"""
Golden Thread Data Templates
Generates realistic process steps, risks, controls, and compliance requirements for each baseline
"""
import json
from typing import List, Dict, Any


def get_process_steps_template(baseline_id: str) -> List[Dict[str, Any]]:
    """Generate process steps for a baseline based on its type"""
    
    templates = {
        "BL-001": [  # Core Access Management
            {"step_number": 1, "title": "Access Request Initiation", "description": "User submits access request through self-service portal", "responsible_role": "Requester", "objective": "Capture access requirements accurately"},
            {"step_number": 2, "title": "Manager Approval", "description": "Line manager reviews and approves access request", "responsible_role": "Manager", "objective": "Ensure business justification for access"},
            {"step_number": 3, "title": "Access Provisioning", "description": "IT team grants access in target systems", "responsible_role": "System Administrator", "objective": "Implement approved access rights"},
            {"step_number": 4, "title": "Access Verification", "description": "User confirms access is working correctly", "responsible_role": "Requester", "objective": "Validate access implementation"},
            {"step_number": 5, "title": "Access Review", "description": "Periodic review of existing access rights", "responsible_role": "Access Reviewer", "objective": "Maintain access appropriateness"}
        ],
        "BL-002": [  # Segregation of Duties
            {"step_number": 1, "title": "Role Definition", "description": "Define conflicting duties and responsibilities", "responsible_role": "Security Architect", "objective": "Identify SoD conflicts"},
            {"step_number": 2, "title": "Rule Configuration", "description": "Configure SoD rules in access management system", "responsible_role": "System Administrator", "objective": "Implement automated conflict detection"},
            {"step_number": 3, "title": "Conflict Analysis", "description": "Analyze existing access for SoD violations", "responsible_role": "Compliance Officer", "objective": "Identify current conflicts"},
            {"step_number": 4, "title": "Remediation Planning", "description": "Create plan to address identified conflicts", "responsible_role": "Business Owner", "objective": "Resolve SoD violations"},
            {"step_number": 5, "title": "Monitoring", "description": "Ongoing monitoring of SoD compliance", "responsible_role": "Auditor", "objective": "Prevent new conflicts"}
        ],
        "BL-003": [  # Access Certification
            {"step_number": 1, "title": "Certification Campaign Setup", "description": "Define scope and schedule for access review", "responsible_role": "Compliance Manager", "objective": "Plan certification process"},
            {"step_number": 2, "title": "Data Collection", "description": "Gather current access assignments", "responsible_role": "System Administrator", "objective": "Compile access inventory"},
            {"step_number": 3, "title": "Manager Review", "description": "Line managers review team access rights", "responsible_role": "Manager", "objective": "Validate access necessity"},
            {"step_number": 4, "title": "Remediation", "description": "Remove inappropriate access rights", "responsible_role": "System Administrator", "objective": "Implement review decisions"},
            {"step_number": 5, "title": "Evidence Collection", "description": "Document certification results", "responsible_role": "Compliance Officer", "objective": "Maintain audit trail"}
        ],
        "BL-004": [  # Emergency Access
            {"step_number": 1, "title": "Emergency Request", "description": "User requests emergency access", "responsible_role": "Requester", "objective": "Address urgent business need"},
            {"step_number": 2, "title": "Emergency Approval", "description": "Authorized personnel approve emergency access", "responsible_role": "Emergency Approver", "objective": "Validate emergency necessity"},
            {"step_number": 3, "title": "Temporary Access", "description": "Grant time-limited emergency access", "responsible_role": "Security Administrator", "objective": "Provide immediate access"},
            {"step_number": 4, "title": "Access Monitoring", "description": "Monitor emergency access usage", "responsible_role": "Security Analyst", "objective": "Ensure appropriate usage"},
            {"step_number": 5, "title": "Access Revocation", "description": "Remove emergency access after resolution", "responsible_role": "System Administrator", "objective": "Restore normal access state"}
        ]
    }
    
    # Default template for other baselines
    default_template = [
        {"step_number": 1, "title": "Process Initiation", "description": "Initiate the control process", "responsible_role": "Process Owner", "objective": "Start control execution"},
        {"step_number": 2, "title": "Implementation", "description": "Implement control activities", "responsible_role": "Control Owner", "objective": "Execute control procedures"},
        {"step_number": 3, "title": "Review", "description": "Review control effectiveness", "responsible_role": "Reviewer", "objective": "Validate control performance"},
        {"step_number": 4, "title": "Documentation", "description": "Document control results", "responsible_role": "Document Owner", "objective": "Maintain evidence"}
    ]
    
    return templates.get(baseline_id, default_template)


def get_risks_template(baseline_id: str) -> List[Dict[str, Any]]:
    """Generate risks for a baseline"""
    
    templates = {
        "BL-001": [  # Core Access Management
            {"risk_id": "R-01", "name": "Unauthorized Access", "description": "Users gain access to systems without proper authorization", "category": "Security", "severity": "High", "related_step_numbers": [1, 2, 3]},
            {"risk_id": "R-02", "name": "Excessive Privileges", "description": "Users have more access rights than required for their role", "category": "Security", "severity": "Medium", "related_step_numbers": [2, 3]},
            {"risk_id": "R-03", "name": "Orphaned Accounts", "description": "Accounts remain active after employee departure", "category": "Security", "severity": "High", "related_step_numbers": [4, 5]},
            {"risk_id": "R-04", "name": "Access Provisioning Errors", "description": "Incorrect access rights granted to users", "category": "Operational", "severity": "Medium", "related_step_numbers": [3, 4]}
        ],
        "BL-002": [  # Segregation of Duties
            {"risk_id": "R-01", "name": "SoD Violations", "description": "Single user can perform conflicting duties", "category": "Compliance", "severity": "High", "related_step_numbers": [1, 2, 3]},
            {"risk_id": "R-02", "name": "Fraud Risk", "description": "Combined access enables fraudulent activities", "category": "Fraud", "severity": "Critical", "related_step_numbers": [3, 4]},
            {"risk_id": "R-03", "name": "Control Override", "description": "SoD controls bypassed for convenience", "category": "Governance", "severity": "Medium", "related_step_numbers": [2, 5]}
        ],
        "BL-003": [  # Access Certification
            {"risk_id": "R-01", "name": "Incomplete Reviews", "description": "Not all access rights are properly reviewed", "category": "Compliance", "severity": "Medium", "related_step_numbers": [2, 3]},
            {"risk_id": "R-02", "name": "Manager Override", "description": "Managers approve inappropriate access", "category": "Governance", "severity": "Medium", "related_step_numbers": [3, 4]},
            {"risk_id": "R-03", "name": "Missing Evidence", "description": "Certification decisions not properly documented", "category": "Audit", "severity": "Low", "related_step_numbers": [4, 5]}
        ],
        "BL-004": [  # Emergency Access
            {"risk_id": "R-01", "name": "Emergency Abuse", "description": "Emergency access used for unauthorized activities", "category": "Security", "severity": "High", "related_step_numbers": [2, 3, 4]},
            {"risk_id": "R-02", "name": "Access Not Revoked", "description": "Emergency access remains active after emergency", "category": "Security", "severity": "Medium", "related_step_numbers": [4, 5]},
            {"risk_id": "R-03", "name": "False Emergency", "description": "Emergency process abused for convenience", "category": "Governance", "severity": "Medium", "related_step_numbers": [1, 2]}
        ]
    }
    
    # Default template for other baselines
    default_template = [
        {"risk_id": "R-01", "name": "Control Failure", "description": "Control activities not performed effectively", "category": "Operational", "severity": "Medium", "related_step_numbers": [2, 3]},
        {"risk_id": "R-02", "name": "Documentation Gaps", "description": "Control evidence not properly maintained", "category": "Audit", "severity": "Low", "related_step_numbers": [3, 4]}
    ]
    
    return templates.get(baseline_id, default_template)


def get_controls_template(baseline_id: str) -> List[Dict[str, Any]]:
    """Generate controls for a baseline"""
    
    templates = {
        "BL-001": [  # Core Access Management
            {"control_id": "MC-01", "name": "Manager Approval", "description": "All access requests require manager approval", "control_type": "Manual", "risk_ids": ["R-01", "R-02"], "frequency": "Per Request"},
            {"control_id": "AC-01", "name": "Automated Provisioning", "description": "System automatically grants approved access", "control_type": "Automated", "risk_ids": ["R-01", "R-04"], "frequency": "Real-time"},
            {"control_id": "ITGC-01", "name": "Access Logging", "description": "All access changes are logged and monitored", "control_type": "ITGC", "risk_ids": ["R-01", "R-02", "R-04"], "frequency": "Continuous"},
            {"control_id": "MC-02", "name": "Periodic Review", "description": "Quarterly review of all access rights", "control_type": "Manual", "risk_ids": ["R-02", "R-03"], "frequency": "Quarterly"},
            {"control_id": "AC-02", "name": "Automated Termination", "description": "System automatically disables terminated employee accounts", "control_type": "Automated", "risk_ids": ["R-03"], "frequency": "Real-time"}
        ],
        "BL-002": [  # Segregation of Duties
            {"control_id": "AC-01", "name": "SoD Rule Engine", "description": "Automated detection of SoD conflicts", "control_type": "Automated", "risk_ids": ["R-01", "R-02"], "frequency": "Real-time"},
            {"control_id": "MC-01", "name": "Exception Review", "description": "Manual review of SoD exceptions", "control_type": "Manual", "risk_ids": ["R-01", "R-03"], "frequency": "Monthly"},
            {"control_id": "ITGC-01", "name": "Configuration Control", "description": "Control over SoD rule configuration changes", "control_type": "ITGC", "risk_ids": ["R-01", "R-03"], "frequency": "Per Change"},
            {"control_id": "MC-02", "name": "Management Sign-off", "description": "Management approval for SoD exceptions", "control_type": "Manual", "risk_ids": ["R-02"], "frequency": "Per Exception"}
        ],
        "BL-003": [  # Access Certification
            {"control_id": "MC-01", "name": "Manager Certification", "description": "Managers certify team access rights", "control_type": "Manual", "risk_ids": ["R-01", "R-02"], "frequency": "Quarterly"},
            {"control_id": "AC-01", "name": "Automated Reminders", "description": "System sends certification reminders", "control_type": "Automated", "risk_ids": ["R-01"], "frequency": "Per Campaign"},
            {"control_id": "ITGC-01", "name": "Audit Trail", "description": "Complete audit trail of certification activities", "control_type": "ITGC", "risk_ids": ["R-02", "R-03"], "frequency": "Continuous"},
            {"control_id": "MC-02", "name": "Evidence Review", "description": "Audit review of certification evidence", "control_type": "Manual", "risk_ids": ["R-03"], "frequency": "Annually"}
        ],
        "BL-004": [  # Emergency Access
            {"control_id": "MC-01", "name": "Emergency Approval", "description": "Two-person approval for emergency access", "control_type": "Manual", "risk_ids": ["R-01", "R-03"], "frequency": "Per Request"},
            {"control_id": "AC-01", "name": "Time-Bound Access", "description": "System automatically expires emergency access", "control_type": "Automated", "risk_ids": ["R-02"], "frequency": "Real-time"},
            {"control_id": "ITGC-01", "name": "Usage Monitoring", "description": "Real-time monitoring of emergency access usage", "control_type": "ITGC", "risk_ids": ["R-01"], "frequency": "Continuous"},
            {"control_id": "MC-02", "name": "Post-Incident Review", "description": "Review emergency access after each incident", "control_type": "Manual", "risk_ids": ["R-01", "R-02"], "frequency": "Per Incident"}
        ]
    }
    
    # Default template for other baselines
    default_template = [
        {"control_id": "MC-01", "name": "Manual Review", "description": "Manual review of control activities", "control_type": "Manual", "risk_ids": ["R-01"], "frequency": "Monthly"},
        {"control_id": "AC-01", "name": "Automated Check", "description": "Automated validation of control requirements", "control_type": "Automated", "risk_ids": ["R-01", "R-02"], "frequency": "Daily"},
        {"control_id": "ITGC-01", "name": "System Logging", "description": "Comprehensive logging of system activities", "control_type": "ITGC", "risk_ids": ["R-02"], "frequency": "Continuous"}
    ]
    
    return templates.get(baseline_id, default_template)


def get_compliance_template(baseline_id: str) -> List[Dict[str, Any]]:
    """Generate compliance requirements for a baseline"""
    
    templates = {
        "BL-001": [  # Core Access Management
            {"regulation": "SOX 404", "requirement_text": "Access controls must prevent unauthorized access to financial systems", "applicable_regions": ["US", "Global"]},
            {"regulation": "PCI DSS", "requirement_text": "Unique user identification and access control mechanisms must be implemented", "applicable_regions": ["US", "EU", "APAC"]},
            {"regulation": "GDPR", "requirement_text": "Access to personal data must be controlled and logged", "applicable_regions": ["EU", "UK"]},
            {"regulation": "ISO 27001", "requirement_text": "Information access control procedures must be documented and implemented", "applicable_regions": ["Global"]},
            {"regulation": "NIST 800-53", "requirement_text": "System access must be authorized and managed according to principle of least privilege", "applicable_regions": ["US", "Global"]}
        ],
        "BL-002": [  # Segregation of Duties
            {"regulation": "SOX 404", "requirement_text": "Duties must be segregated to prevent fraud and errors", "applicable_regions": ["US", "Global"]},
            {"regulation": "PCI DSS", "requirement_text": "Separation of duties must be maintained for cardholder data environment", "applicable_regions": ["US", "EU", "APAC"]},
            {"regulation": "ISO 27001", "requirement_text": "Conflicting duties and responsibilities must be segregated", "applicable_regions": ["Global"]},
            {"regulation": "COSO", "requirement_text": "Segregation of duties is a key component of internal control", "applicable_regions": ["Global"]}
        ],
        "BL-003": [  # Access Certification
            {"regulation": "SOX 404", "requirement_text": "Management must certify effectiveness of internal controls", "applicable_regions": ["US", "Global"]},
            {"regulation": "ISO 27001", "requirement_text": "Access rights must be reviewed at regular intervals", "applicable_regions": ["Global"]},
            {"regulation": "NIST 800-53", "requirement_text": "System access must be periodically reviewed and re-authorized", "applicable_regions": ["US", "Global"]},
            {"regulation": "HIPAA", "requirement_text": "Access to electronic PHI must be reviewed and authorized", "applicable_regions": ["US"]}
        ],
        "BL-004": [  # Emergency Access
            {"regulation": "SOX 404", "requirement_text": "Emergency access must be controlled and documented", "applicable_regions": ["US", "Global"]},
            {"regulation": "PCI DSS", "requirement_text": "Emergency access procedures must be documented and tested", "applicable_regions": ["US", "EU", "APAC"]},
            {"regulation": "ISO 27001", "requirement_text": "Procedures for emergency situations must be established", "applicable_regions": ["Global"]},
            {"regulation": "NIST 800-53", "requirement_text": "Emergency access must be time-limited and monitored", "applicable_regions": ["US", "Global"]}
        ]
    }
    
    # Default template for other baselines
    default_template = [
        {"regulation": "SOX 404", "requirement_text": "Internal controls must be documented and effective", "applicable_regions": ["US", "Global"]},
        {"regulation": "ISO 27001", "requirement_text": "Control objectives must be established and monitored", "applicable_regions": ["Global"]},
        {"regulation": "NIST 800-53", "requirement_text": "Security controls must be implemented and reviewed", "applicable_regions": ["US", "Global"]}
    ]
    
    return templates.get(baseline_id, default_template)
