# AI-Powered Endpoints Documentation

## Overview
Three new AI-powered endpoints that enhance the Control Design Assessment system with advanced LLM capabilities, rate limiting, and structured output guarantees.

## 🔧 Configuration

### Environment Variables
```bash
# Required: At least one LLM provider API key
OPENAI_API_KEY=sk-your-openai-key-here
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here

# Optional: LLM provider preference
LLM_PROVIDER=openai  # or "anthropic"
```

### Dependencies
```bash
pip install slowapi==0.1.9  # Rate limiting
# Already included: openai, anthropic, fastapi, pydantic
```

## 🚀 Endpoints

### 1. POST /api/ai/prefill - Form Pre-filling

**Purpose**: Pre-fills form fields for creating Global Baselines or Local Variations from analysis results.

#### Request
```json
{
  "mode": "baseline",
  "analysis": {
    "process_steps": [...],
    "risks": [...],
    "summary": "Analysis results..."
  },
  "context": "Country: Germany, Region: DACH, Interviewee: Tax Manager"
}
```

#### Response (Baseline Mode)
```json
{
  "baseline_name": "Tax Compliance Process Control",
  "baseline_description": "Standardized tax compliance workflow with automated validation",
  "version": "1.0"
}
```

#### Response (Variation Mode)
```json
{
  "notes": "German market requires additional VAT validation steps and local tax authority integration",
  "additional_steps": [
    {
      "title": "German VAT Validation",
      "description": "Validate VAT numbers against German Federal Central Tax Office",
      "responsible_role": "Tax Specialist",
      "is_mandatory": true
    }
  ],
  "additional_risks": [
    {
      "description": "GDPR compliance risk for customer data processing",
      "severity": "high",
      "mitigating_controls": "Data minimization and consent management"
    }
  ],
  "suggested_overrides": [
    {
      "step_keyword": "approval",
      "field": "responsible_role",
      "value": "German Tax Manager",
      "reason": "Local regulatory requirement for tax-specific approval"
    }
  ]
}
```

#### Use Cases
- **Baseline Creation**: Auto-generate names and descriptions from analysis
- **Market Variations**: Identify local deviations and additional requirements
- **Form Automation**: Reduce manual data entry for control creation

---

### 2. POST /api/ai/triage - Security Triage

**Purpose**: Performs AI-powered security triage analysis on detected anomalies.

#### Request
```json
{
  "anomaly": {
    "type": "Data Exfiltration",
    "severity": "high",
    "details": "Unauthorized access attempt to export sensitive financial data",
    "affected_controls": ["FIN-001", "FIN-003"],
    "timestamp": "2024-01-15T10:30:00Z"
  },
  "context": "Detected during quarterly audit process"
}
```

#### Response
```json
{
  "classification": "Insider Threat - Data Theft",
  "confidence": 0.85,
  "risk_score": 78,
  "summary": "High-confidence insider threat attempt targeting financial data export. Requires immediate investigation and access revocation.",
  "recommended_actions": [
    "Immediately revoke user access",
    "Initiate forensic investigation",
    "Review recent access logs",
    "Notify compliance team"
  ],
  "affected_systems": ["Financial System", "ERP", "Data Warehouse"],
  "ioc_indicators": [
    "Unusual data export patterns",
    "After-hours access attempts",
    "Multiple failed login attempts"
  ],
  "regulatory_impact": "Potential SOX violation - requires disclosure if material impact confirmed"
}
```

#### Use Cases
- **Security Operations**: Automated triage of security alerts
- **Compliance**: Regulatory impact assessment
- **Incident Response**: Prioritization and recommended actions

---

### 3. POST /api/ai/analyze-source - Enhanced Source Analysis

**Purpose**: Extract structured GRC data from interview transcripts or documents with enhanced AI capabilities.

#### Request
```json
{
  "text": "Interviewer: Can you describe your approval process?\nInterviewee: Well, usually I just send an email to my manager and they approve it...",
  "language": "en",
  "context": "Country: Brazil, Department: Finance, Interviewee: Finance Manager"
}
```

#### Response
```json
{
  "process_steps": [
    {
      "step_number": 1,
      "title": "Submit Approval Request",
      "description": "Employee sends approval request via email",
      "responsible_role": "Employee",
      "is_mandatory": true
    },
    {
      "step_number": 2,
      "title": "Manager Review",
      "description": "Manager reviews and approves request",
      "responsible_role": "Manager",
      "is_mandatory": true
    }
  ],
  "risks": [
    {
      "description": "Lack of formal approval trail",
      "severity": "medium",
      "mitigating_controls": ["Implement formal approval system"],
      "related_step_numbers": [1, 2]
    }
  ],
  "controls": [
    {
      "name": "Email Approval Control",
      "description": "Manager approval via email",
      "control_type": "preventive",
      "frequency": "per_transaction",
      "risk_ids": ["risk_001"]
    }
  ],
  "inefficiencies": [
    "No centralized tracking of approvals",
    "Email-based process creates audit trail gaps",
    "No escalation process for delayed approvals"
  ],
  "compliance_observations": [
    "Process may not meet audit requirements for formal approval documentation",
    "SOX compliance risk due to lack of formal approval records"
  ],
  "metadata": {
    "interviewee_role": "Finance Manager",
    "department": "Finance",
    "region": "Brazil",
    "confidence_score": 0.87
  }
}
```

#### Use Cases
- **Process Discovery**: Extract structured processes from interviews
- **Risk Identification**: Identify implicit risks from conversational cues
- **Compliance Analysis**: Flag regulatory alignment issues

---

### 4. GET /api/ai/status - Service Status

**Purpose**: Check AI service status and configuration.

#### Response
```json
{
  "service": "AI-Powered GRC Endpoints",
  "status": "healthy",
  "llm_provider": "openai",
  "openai_configured": true,
  "anthropic_configured": false,
  "rate_limit": "10 requests per minute per IP",
  "endpoints": {
    "prefill": "POST /api/ai/prefill",
    "triage": "POST /api/ai/triage",
    "analyze-source": "POST /api/ai/analyze-source",
    "status": "GET /api/ai/status"
  }
}
```

---

## 🛡️ Security & Rate Limiting

### Rate Limiting
- **Limit**: 10 requests per minute per IP address
- **Implementation**: SlowAPI middleware
- **Response**: 429 status code with retry information

### Input Validation
- **Required Fields**: Validated for each endpoint
- **Content Length**: Minimum/maximum text limits
- **Language Support**: Limited to supported languages
- **Data Types**: Strong typing with Pydantic models

### Error Handling
```json
{
  "detail": "Failed to generate form prefill: LLM API rate limit exceeded"
}
```

### Audit Trail
- **Logging**: All AI calls logged with endpoint and metadata
- **Request Tracking**: Request IDs for troubleshooting
- **Performance Metrics**: Response time monitoring

---

## 🔧 LLM Provider Support

### OpenAI Integration
```python
# Uses structured output mode
response_format={"type": "json_object"}
# Models: gpt-4, gpt-4-turbo, gpt-3.5-turbo
```

### Anthropic Integration
```python
# Uses system messages and JSON parsing
# Models: claude-3-opus, claude-3-sonnet, claude-3-haiku
```

### Provider Selection
```python
# Controlled by LLM_PROVIDER environment variable
# Fallback to OpenAI if Anthropic not configured
```

---

## 📊 Performance & Monitoring

### Response Times
- **Target**: < 5 seconds for most requests
- **Complex Analysis**: Up to 30 seconds for large documents
- **Timeout**: 60 seconds maximum

### Monitoring
```bash
# Check service status
curl https://your-app.onrender.com/api/ai/status

# Monitor logs for AI calls
grep "AI endpoint called" application.log
```

### Cost Management
- **Token Usage**: Monitored per endpoint
- **Rate Limiting**: Prevents cost spikes
- **Provider Selection**: Choose cost-effective model

---

## 🎯 Best Practices

### For Form Pre-filling
- Provide complete analysis results
- Include context about market/region
- Validate generated fields before use

### For Security Triage
- Include detailed anomaly information
- Provide context about detection circumstances
- Review recommended actions for applicability

### For Source Analysis
- Clean text of sensitive information
- Provide accurate language identification
- Include relevant context about interview setting

### General
- Handle rate limit errors gracefully
- Implement retry logic with exponential backoff
- Monitor API costs and usage patterns
- Validate AI outputs before critical use

---

## 🚀 Integration Examples

### Frontend Integration
```javascript
// Form prefilling
const prefillResponse = await fetch('/api/ai/prefill', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    mode: 'variation',
    analysis: analysisData,
    context: 'Market: Germany, Department: Finance'
  })
});

// Security triage
const triageResponse = await fetch('/api/ai/triage', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    anomaly: securityEvent,
    context: 'Detected during routine monitoring'
  })
});
```

### Error Handling
```javascript
try {
  const result = await callAIEndpoint(data);
  return result;
} catch (error) {
  if (error.status === 429) {
    // Rate limited - wait and retry
    await new Promise(resolve => setTimeout(resolve, 60000));
    return callAIEndpoint(data);
  }
  throw error;
}
```

---

## 🔍 Troubleshooting

### Common Issues

1. **"LLM API key not configured"**
   - Set OPENAI_API_KEY or ANTHROPIC_API_KEY environment variable
   - Check Render environment variables

2. **"Rate limit exceeded"**
   - Wait before retrying
   - Implement exponential backoff
   - Consider upgrading API plan

3. **"Invalid JSON response"**
   - Check LLM model compatibility
   - Verify prompt formatting
   - Review system prompts

4. **"Text too short" error**
   - Ensure minimum 100 characters for source analysis
   - Provide more context in requests

### Debug Mode
```python
# Enable debug logging
import logging
logging.getLogger('app.services.llm_service').setLevel(logging.DEBUG)
```

These AI endpoints provide enterprise-grade GRC automation with structured outputs, rate limiting, and comprehensive error handling for production use.
