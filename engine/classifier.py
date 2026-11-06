import re
from typing import Dict, Any, List

DOCUMENT_PROFILES = {
    "aadhar": {
        "title": "Aadhaar Card",
        "icon": "shield-check",
        "color": "emerald",
        "keywords": [
            ("aadhaar", 40),
            ("uidai", 40),
            ("uniqueidentificationauthority", 45),
            ("unique identification authority", 45),
            ("government of india", 20),
            ("governmentofindia", 20),
            ("enrollment no", 25),
            ("enrollmentno", 25),
            ("mera aadhaar", 30),
            ("my aadhaar", 25),
            ("dob", 15),
            ("year of birth", 20),
        ],
        "regex": [
            (r"\b[2-9]{1}[0-9]{3}\s+[0-9]{4}\s+[0-9]{4}\b", 45),
            (r"\b[2-9]{1}[0-9]{11}\b", 35)
        ]
    },
    "pan": {
        "title": "PAN Card",
        "icon": "credit-card",
        "color": "indigo",
        "keywords": [
            ("incometaxdepartment", 45),
            ("incometax department", 45),
            ("income tax department", 45),
            ("permanentaccountnumber", 45),
            ("permanent account number", 45),
            ("govt. of india", 20),
            ("govtofindia", 20),
            ("father's name", 20),
            ("fathersname", 20),
        ],
        "regex": [
            (r"\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b", 50)
        ],
        "negative_keywords": [("form no. 16", -40), ("form16", -40), ("salary slip", -45), ("salaryslip", -45), ("water authority", -45)]
    },
    "driver": {
        "title": "Driving License",
        "icon": "car",
        "color": "amber",
        "keywords": [
            ("motordrivinglicence", 50),
            ("motordrivinglicense", 50),
            ("drivinglicence", 45),
            ("driving licence", 45),
            ("drivinglicense", 45),
            ("driving license", 45),
            ("unionofindia", 20),
            ("transportdepartment", 30),
            ("licensingauthority", 30),
            ("valid till", 25),
            ("validtill", 25),
            ("date of issue", 20),
            ("dateofissue", 20),
        ],
        "regex": [
            (r"\b[A-Z]{2}[0-9]{2}[0-9A-Z\s]{11,15}\b", 35)
        ]
    },
    "voter": {
        "title": "Voter ID Card",
        "icon": "vote",
        "color": "purple",
        "keywords": [
            ("electioncommissionofindia", 50),
            ("election commission of india", 50),
            ("electorphotoidentitycard", 50),
            ("elector photo identity card", 50),
            ("elector's name", 35),
            ("electorsname", 35),
            ("elector", 25),
            ("vidhansabha", 25),
            ("epic", 30),
        ],
        "regex": [
            (r"\b[A-Z]{3}[0-9]{7}\b", 40)
        ]
    },
    "passport": {
        "title": "Passport",
        "icon": "globe",
        "color": "blue",
        "keywords": [
            ("republicofindia", 45),
            ("republic of india", 45),
            ("passport", 45),
            ("passoire", 35),
            ("presidentoftherepublic", 40),
            ("president of the republic", 40),
            ("given name", 25),
            ("surname", 25),
            ("nationality", 25),
            ("type p", 30),
        ],
        "regex": [
            (r"\b[A-Z]{1}[0-9]{7}\b", 30),
            (r"P<IND[A-Z<]+", 50)
        ]
    },
    "salary": {
        "title": "Salary Slip / Payslip",
        "icon": "banknote",
        "color": "teal",
        "keywords": [
            ("salaryslip", 50),
            ("salary slip", 50),
            ("payslip", 50),
            ("basicsalary", 35),
            ("basic salary", 35),
            ("gross salary", 35),
            ("grosssalary", 35),
            ("net pay", 35),
            ("netpay", 35),
            ("earnings", 25),
            ("deductions", 25),
            ("provident fund", 25),
            ("epf", 25),
            ("hra", 20),
            ("conveyance", 20),
            ("designation", 20),
        ],
        "regex": [
            (r"salary\s*slip\s*for\s+[a-z]{3,9}\s+[0-9]{4}", 45)
        ]
    },
    "form16": {
        "title": "Form 16 (TDS Certificate)",
        "icon": "file-check",
        "color": "rose",
        "keywords": [
            ("form no. 16", 50),
            ("form no.16", 50),
            ("formno.16", 50),
            ("form 16", 45),
            ("section 203", 35),
            ("traces", 35),
            ("tdsreconciliation", 35),
            ("tds reconciliation", 35),
            ("centralized processing cell", 35),
            ("centralizedprocessingcell", 35),
            ("assessment year", 30),
            ("assessmentyear", 30),
            ("tax deducted at source", 30),
            ("tanofthedeductor", 30),
            ("tan of the deductor", 30),
        ],
        "regex": [
            (r"form\s*no\.?\s*16", 45)
        ]
    },
    "bank": {
        "title": "Bank Statement",
        "icon": "building-2",
        "color": "cyan",
        "keywords": [
            ("bankstatement", 50),
            ("bank statement", 50),
            ("accountholderdetails", 45),
            ("statement of account", 45),
            ("accountholdername", 35),
            ("account holder", 30),
            ("account number", 25),
            ("accountnumber", 25),
            ("accountdetails", 35),
            ("opening balance", 30),
            ("closing balance", 30),
            ("withdrawal", 25),
            ("deposit", 25),
            ("transaction date", 25),
        ],
        "regex": [
            (r"statement\s*period", 30),
            (r"bank\s*statement", 45)
        ],
        "negative_keywords": [("salary slip", -25), ("salaryslip", -25)]
    },
    "cheque": {
        "title": "Bank Cheque",
        "icon": "receipt",
        "color": "amber",
        "keywords": [
            ("payee", 30),
            ("pay to", 30),
            ("rupees", 30),
            ("a/c payee", 40),
            ("acpayee", 40),
            ("cheque", 35),
            ("state bank", 25),
            ("statebank", 25),
            ("ifccode", 25),
            ("ifsc", 20),
            ("not over", 25),
        ],
        "regex": [
            (r"\b[0-9]{6}\b\s+[:\d]{9,}", 40),
            (r"pay\s+[\w\s]+\s+or\s+bearer", 45)
        ],
        "negative_keywords": [("bankstatement", -40), ("bank statement", -40), ("accountholderdetails", -40), ("salary slip", -40)]
    },
    "bill": {
        "title": "Utility Bill",
        "icon": "zap",
        "color": "orange",
        "keywords": [
            ("water authority", 45),
            ("waterauthority", 45),
            ("electricity bill", 45),
            ("electricitybill", 45),
            ("water supply", 40),
            ("watersupply", 40),
            ("disconnection notice", 40),
            ("disconnectionnotice", 40),
            ("consumer id", 35),
            ("consumerid", 35),
            ("bill number", 30),
            ("billnumber", 30),
            ("due date", 25),
            ("duedate", 25),
            ("meter no", 30),
            ("power distribution", 40),
            ("total amount due", 30)
        ],
        "regex": [
            (r"due\s*date\s*without\s*fine", 40),
            (r"disconnection\s*notice", 40)
        ]
    }
}

def classify_text(text: str) -> Dict[str, Any]:
    """
    Analyzes OCR or embedded text and returns the best matching document type
    with confidence percentage, matched signals, and document metadata.
    """
    clean_lower = text.lower()
    clean_nospace = re.sub(r"\s+", "", clean_lower)
    scores = {}
    signals_matched = {}

    for doc_type, profile in DOCUMENT_PROFILES.items():
        score = 0
        matches = []
        
        # Keyword checks (both in raw lower text and no-space lower text)
        for kw, weight in profile.get("keywords", []):
            kw_clean = kw.lower()
            if kw_clean in clean_lower or kw_clean in clean_nospace:
                score += weight
                matches.append(kw)
                
        # Regex checks
        for pattern, weight in profile.get("regex", []):
            found = re.findall(pattern, text, re.IGNORECASE)
            if found:
                score += weight
                snippet = found[0] if isinstance(found[0], str) else found[0][0]
                matches.append(f"Pattern match: {str(snippet)[:25].strip()}")
                
        # Negative penalties
        for neg_kw, penalty in profile.get("negative_keywords", []):
            neg_clean = neg_kw.lower()
            if neg_clean in clean_lower or neg_clean in clean_nospace:
                score += penalty
                
        if score > 0:
            scores[doc_type] = max(0, score)
            signals_matched[doc_type] = matches

    if not scores:
        return {
            "type": "unknown",
            "title": "Unclassified Document",
            "confidence": 0,
            "badge_color": "slate",
            "icon": "help-circle",
            "signals": [],
            "all_scores": {}
        }

    # Normalize best score to confidence percentage (capped at 99%)
    best_type = max(scores, key=scores.get)
    raw_score = scores[best_type]
    confidence = min(99, max(45, int((raw_score / 75.0) * 100)))

    profile = DOCUMENT_PROFILES[best_type]
    return {
        "type": best_type,
        "title": profile["title"],
        "confidence": confidence,
        "badge_color": profile["color"],
        "icon": profile["icon"],
        "signals": signals_matched.get(best_type, []),
        "all_scores": scores
    }
