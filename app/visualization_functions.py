"""
Visualization computation functions for dashboard, fit-gap, standardization, benchmark, and risk heatmap
"""
import json
from typing import List, Optional, Dict, Any

# Region definitions
DEFAULT_REGIONS = [
    {"code": "EMEA", "name": "Europe, Middle East & Africa", "markets": ["GB", "DE", "FR"]},
    {"code": "APAC", "name": "Asia-Pacific", "markets": ["JP", "CN", "IN", "AU"]},
    {"code": "AMER", "name": "Americas", "markets": ["US", "CA"]},
    {"code": "LATAM", "name": "Latin America", "markets": ["BR"]},
]


def get_market_variations_with_details(cur, baseline_id: str, region: Optional[str], markets: Optional[str]) -> List[Dict[str, Any]]:
    """Get market variations with all related details"""
    query = "SELECT * FROM market_variations WHERE baseline_id = ?"
    params = [baseline_id]
    
    if region:
        # Filter by region
        region_markets = []
        for r in DEFAULT_REGIONS:
            if r["code"] == region:
                region_markets = r["markets"]
                break
        if region_markets:
            query += " AND market_code IN ({})".format(",".join(["?" for _ in region_markets]))
            params.extend(region_markets)
    
    if markets:
        # Filter by specific markets
        market_list = [m.strip() for m in markets.split(",")]
        if region:
            query += " AND market_code IN ({})".format(",".join(["?" for _ in market_list]))
        else:
            query += " AND market_code IN ({})".format(",".join(["?" for _ in market_list]))
        params.extend(market_list)
    
    cur.execute(query, params)
    variations = []
    
    for row in cur.fetchall():
        variation = dict(row)
        variation_id = variation['id']
        
        # Parse notes JSON
        if variation.get('notes'):
            try:
                variation['notes'] = json.loads(variation['notes'])
            except:
                variation['notes'] = {"default": "Notes unavailable"}
        
        # Get step overrides
        cur.execute("SELECT * FROM market_step_overrides WHERE variation_id = ? ORDER BY step_number", (variation_id,))
        variation['overrides'] = [dict(row) for row in cur.fetchall()]
        
        # Get additional steps
        cur.execute("SELECT * FROM market_additional_steps WHERE variation_id = ? ORDER BY step_number", (variation_id,))
        additional_steps = []
        for step in cur.fetchall():
            step_dict = dict(step)
            if step_dict.get('title'):
                step_dict['title'] = json.loads(step_dict['title'])
            if step_dict.get('description'):
                step_dict['description'] = json.loads(step_dict['description'])
            additional_steps.append(step_dict)
        variation['additional_steps'] = additional_steps
        
        # Get removed steps
        cur.execute("SELECT step_number FROM market_removed_steps WHERE variation_id = ? ORDER BY step_number", (variation_id,))
        variation['removed_step_numbers'] = [row[0] for row in cur.fetchall()]
        
        # Get additional risks
        cur.execute("SELECT * FROM market_additional_risks WHERE variation_id = ? ORDER BY id", (variation_id,))
        additional_risks = []
        for risk in cur.fetchall():
            risk_dict = dict(risk)
            if risk_dict.get('mitigating_controls'):
                risk_dict['mitigating_controls'] = json.loads(risk_dict['mitigating_controls'])
            additional_risks.append(risk_dict)
        variation['additional_risks'] = additional_risks
        
        variations.append(variation)
    
    return variations


def compute_dashboard_data(baseline: Dict[str, Any], variations: List[Dict[str, Any]], region: Optional[str], markets: Optional[str]) -> Dict[str, Any]:
    """Compute comprehensive dashboard data"""
    # Summary statistics
    total_markets = len(variations)
    total_overrides = sum(len(v.get('overrides', [])) for v in variations)
    total_additional_steps = sum(len(v.get('additional_steps', [])) for v in variations)
    total_additional_risks = sum(len(v.get('additional_risks', [])) for v in variations)
    
    # Region aggregation
    region_data = {}
    for variation in variations:
        market_code = variation['market_code']
        market_region = None
        for r in DEFAULT_REGIONS:
            if market_code in r['markets']:
                market_region = r['code']
                break
        
        if market_region:
            if market_region not in region_data:
                region_data[market_region] = {
                    'name': next(r['name'] for r in DEFAULT_REGIONS if r['code'] == market_region),
                    'markets': [],
                    'total_overrides': 0,
                    'total_additional_steps': 0,
                    'total_additional_risks': 0,
                    'avg_fit_score': 0
                }
            
            region_data[market_region]['markets'].append(market_code)
            region_data[market_region]['total_overrides'] += len(variation.get('overrides', []))
            region_data[market_region]['total_additional_steps'] += len(variation.get('additional_steps', []))
            region_data[market_region]['total_additional_risks'] += len(variation.get('additional_risks', []))
    
    # Calculate fit scores (simplified)
    for region_code, data in region_data.items():
        if data['markets']:
            data['avg_fit_score'] = max(0, 100 - (data['total_overrides'] / len(data['markets']) * 10))
    
    return {
        'baseline': baseline,
        'summary': {
            'total_markets': total_markets,
            'total_overrides': total_overrides,
            'total_additional_steps': total_additional_steps,
            'total_additional_risks': total_additional_risks,
            'avg_overrides_per_market': total_overrides / total_markets if total_markets > 0 else 0
        },
        'regions': region_data,
        'markets': [
            {
                'code': v['market_code'],
                'name': v['market_name'],
                'overrides_count': len(v.get('overrides', [])),
                'additional_steps_count': len(v.get('additional_steps', [])),
                'additional_risks_count': len(v.get('additional_risks', [])),
                'fit_score': max(0, 100 - len(v.get('overrides', [])) * 5)
            }
            for v in variations
        ]
    }


def compute_fit_gap_data(baseline: Dict[str, Any], variations: List[Dict[str, Any]], region: Optional[str], markets: Optional[str]) -> Dict[str, Any]:
    """Compute fit-gap analysis data"""
    market_scores = []
    
    for variation in variations:
        # Calculate fit score based on deviations
        overrides_count = len(variation.get('overrides', []))
        additional_steps_count = len(variation.get('additional_steps', []))
        removed_steps_count = len(variation.get('removed_step_numbers', []))
        
        # Fit score: 100 - (overrides * 5 + additional_steps * 3 + removed_steps * 10)
        fit_score = max(0, 100 - (overrides_count * 5 + additional_steps_count * 3 + removed_steps_count * 10))
        
        # Determine market region
        market_region = None
        for r in DEFAULT_REGIONS:
            if variation['market_code'] in r['markets']:
                market_region = r['code']
                break
        
        market_scores.append({
            'market_code': variation['market_code'],
            'market_name': variation['market_name'],
            'region': market_region,
            'fit_score': fit_score,
            'deviations': {
                'overrides': overrides_count,
                'additional_steps': additional_steps_count,
                'removed_steps': removed_steps_count
            }
        })
    
    # Sort by fit score
    market_scores.sort(key=lambda x: x['fit_score'], reverse=True)
    
    # Region aggregation
    region_scores = {}
    for score in market_scores:
        region = score['region']
        if region not in region_scores:
            region_scores[region] = {'scores': [], 'avg_score': 0}
        region_scores[region]['scores'].append(score['fit_score'])
    
    for region, data in region_scores.items():
        data['avg_score'] = sum(data['scores']) / len(data['scores'])
        data['market_count'] = len(data['scores'])
    
    return {
        'baseline': baseline,
        'market_scores': market_scores,
        'region_scores': region_scores,
        'overall_avg_score': sum(s['fit_score'] for s in market_scores) / len(market_scores) if market_scores else 0
    }


def compute_standardization_data(baseline: Dict[str, Any], variations: List[Dict[str, Any]], region: Optional[str], markets: Optional[str]) -> Dict[str, Any]:
    """Compute standardization heatmap data"""
    # Get all unique steps across all variations
    all_steps = set()
    step_data = {}
    
    for variation in variations:
        # Track which steps are modified, added, or removed
        for override in variation.get('overrides', []):
            step_key = f"step_{override['step_number']}"
            all_steps.add(step_key)
            if step_key not in step_data:
                step_data[step_key] = {'step_number': override['step_number'], 'title': f"Step {override['step_number']}"}
        
        for step in variation.get('additional_steps', []):
            step_key = f"additional_{step['step_number']}"
            all_steps.add(step_key)
            if step_key not in step_data:
                title = step['title'].get('default', f"Additional Step {step['step_number']}")
                step_data[step_key] = {'step_number': step['step_number'], 'title': title, 'is_additional': True}
        
        for step_num in variation.get('removed_step_numbers', []):
            step_key = f"step_{step_num}"
            all_steps.add(step_key)
            if step_key not in step_data:
                step_data[step_key] = {'step_number': step_num, 'title': f"Step {step_num}"}
    
    # Build heatmap matrix
    heatmap_data = []
    markets = [v['market_code'] for v in variations]
    
    for step_key in sorted(all_steps):
        step_info = step_data[step_key]
        row = {
            'step_number': step_info['step_number'],
            'title': step_info['title'],
            'is_additional': step_info.get('is_additional', False),
            'market_status': {}
        }
        
        for variation in variations:
            market_code = variation['market_code']
            status = 'adopted'  # Default status
            
            # Check if step is overridden
            for override in variation.get('overrides', []):
                if override['step_number'] == step_info['step_number']:
                    status = 'modified'
                    break
            
            # Check if step is removed
            if step_info['step_number'] in variation.get('removed_step_numbers', []):
                status = 'removed'
            
            # Check if this is an additional step
            if step_info.get('is_additional'):
                for step in variation.get('additional_steps', []):
                    if step['step_number'] == step_info['step_number']:
                        status = 'additional'
                        break
            
            row['market_status'][market_code] = status
        
        heatmap_data.append(row)
    
    return {
        'baseline': baseline,
        'markets': markets,
        'heatmap_data': heatmap_data,
        'status_counts': {
            'adopted': sum(1 for row in heatmap_data for status in row['market_status'].values() if status == 'adopted'),
            'modified': sum(1 for row in heatmap_data for status in row['market_status'].values() if status == 'modified'),
            'removed': sum(1 for row in heatmap_data for status in row['market_status'].values() if status == 'removed'),
            'additional': sum(1 for row in heatmap_data for status in row['market_status'].values() if status == 'additional')
        }
    }


def compute_benchmark_data(baseline: Dict[str, Any], variations: List[Dict[str, Any]], region: Optional[str], markets: Optional[str]) -> Dict[str, Any]:
    """Compute benchmark radar chart data"""
    # Define benchmark dimensions
    dimensions = [
        'Process Coverage',
        'Risk Mitigation', 
        'Automation Level',
        'Compliance Adherence',
        'Control Maturity',
        'Documentation Quality'
    ]
    
    # Calculate scores for each market
    market_benchmarks = []
    
    for variation in variations:
        scores = {}
        
        # Process Coverage (based on additional steps vs removed steps)
        additional_steps = len(variation.get('additional_steps', []))
        removed_steps = len(variation.get('removed_step_numbers', []))
        scores['Process Coverage'] = min(100, max(0, 50 + additional_steps * 10 - removed_steps * 15))
        
        # Risk Mitigation (based on additional risks)
        additional_risks = len(variation.get('additional_risks', []))
        scores['Risk Mitigation'] = min(100, max(0, 80 - additional_risks * 5))
        
        # Automation Level (based on overrides mentioning automated systems)
        automation_overrides = sum(1 for override in variation.get('overrides', []) 
                                 if 'automated' in override.get('value', '').lower() or 'automated' in override.get('reason', '').lower())
        scores['Automation Level'] = min(100, max(0, 30 + automation_overrides * 20))
        
        # Compliance Adherence (based on regulatory reasons in overrides)
        compliance_overrides = sum(1 for override in variation.get('overrides', []) 
                                if any(reg in override.get('reason', '').lower() 
                                      for reg in ['sox', 'gdpr', 'lgpd', 'hipaa', 'pci', 'basel']))
        scores['Compliance Adherence'] = min(100, max(0, 40 + compliance_overrides * 15))
        
        # Control Maturity (based on overall variation complexity)
        total_changes = len(variation.get('overrides', [])) + len(variation.get('additional_steps', []))
        scores['Control Maturity'] = min(100, max(0, 70 - total_changes * 3))
        
        # Documentation Quality (based on notes quality)
        has_notes = bool(variation.get('notes'))
        scores['Documentation Quality'] = 80 if has_notes else 60
        
        market_benchmarks.append({
            'market_code': variation['market_code'],
            'market_name': variation['market_name'],
            'scores': scores,
            'overall_score': sum(scores.values()) / len(scores)
        })
    
    # Calculate global benchmark (average of all markets)
    global_benchmark = {}
    for dimension in dimensions:
        global_benchmark[dimension] = sum(m['scores'][dimension] for m in market_benchmarks) / len(market_benchmarks) if market_benchmarks else 50
    
    global_benchmark['overall_score'] = sum(global_benchmark.values()) / len(global_benchmark)
    
    return {
        'baseline': baseline,
        'dimensions': dimensions,
        'global_benchmark': global_benchmark,
        'market_benchmarks': market_benchmarks,
        'region_benchmarks': {}  # Could be implemented if needed
    }


def compute_risk_heatmap_data(baseline: Dict[str, Any], variations: List[Dict[str, Any]], region: Optional[str], markets: Optional[str]) -> Dict[str, Any]:
    """Compute risk heatmap data"""
    risk_data = []
    
    for variation in variations:
        additional_risks = variation.get('additional_risks', [])
        
        # Count risks by severity
        severity_counts = {'low': 0, 'medium': 0, 'high': 0, 'critical': 0}
        weighted_score = 0
        
        for risk in additional_risks:
            severity = risk.get('severity', 'medium').lower()
            if severity in severity_counts:
                severity_counts[severity] += 1
            
            # Weighted score calculation
            weights = {'low': 1, 'medium': 3, 'high': 7, 'critical': 10}
            weighted_score += weights.get(severity, 3)
        
        # Determine market region
        market_region = None
        for r in DEFAULT_REGIONS:
            if variation['market_code'] in r['markets']:
                market_region = r['code']
                break
        
        risk_data.append({
            'market_code': variation['market_code'],
            'market_name': variation['market_name'],
            'region': market_region,
            'total_risks': len(additional_risks),
            'severity_counts': severity_counts,
            'weighted_score': weighted_score,
            'risk_level': 'Low' if weighted_score < 10 else 'Medium' if weighted_score < 25 else 'High' if weighted_score < 50 else 'Critical'
        })
    
    # Aggregate by region
    region_risks = {}
    for risk in risk_data:
        region = risk['region']
        if region not in region_risks:
            region_risks[region] = {
                'total_risks': 0,
                'severity_counts': {'low': 0, 'medium': 0, 'high': 0, 'critical': 0},
                'weighted_score': 0,
                'markets': []
            }
        
        region_risks[region]['total_risks'] += risk['total_risks']
        region_risks[region]['markets'].append(risk['market_code'])
        for severity, count in risk['severity_counts'].items():
            region_risks[region]['severity_counts'][severity] += count
        region_risks[region]['weighted_score'] += risk['weighted_score']
    
    # Calculate region averages
    for region, data in region_risks.items():
        if data['markets']:
            data['avg_weighted_score'] = data['weighted_score'] / len(data['markets'])
            data['avg_risks_per_market'] = data['total_risks'] / len(data['markets'])
    
    return {
        'baseline': baseline,
        'market_risks': risk_data,
        'region_risks': region_risks,
        'severity_distribution': {
            'low': sum(r['severity_counts']['low'] for r in risk_data),
            'medium': sum(r['severity_counts']['medium'] for r in risk_data),
            'high': sum(r['severity_counts']['high'] for r in risk_data),
            'critical': sum(r['severity_counts']['critical'] for r in risk_data)
        }
    }
