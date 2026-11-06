import re
from typing import Dict, Any, List

def clean_val(val: str) -> str:
    if not val:
        return ""
    val = re.sub(r"[\s\:\;\|\_]+$", "", val.strip())
    val = re.sub(r"^[\s\:\;\|\_]+", "", val)
    return val.strip()

def extract_aadhaar(text: str, lines: List[str]) -> Dict[str, Any]:
    fields = {}
    
    # 1. Aadhaar Number (12 digits)
    adh_match = re.findall(r"\b[2-9]{1}[0-9]{3}\s+[0-9]{4}\s+[0-9]{4}\b", text)
    if not adh_match:
        adh_match = re.findall(r"\b[2-9]{1}[0-9]{11}\b", text)
        if adh_match:
            raw = adh_match[0]
            fields["Aadhaar Number"] = f"{raw[:4]} {raw[4:8]} {raw[8:]}"
    else:
        fields["Aadhaar Number"] = adh_match[0]
        
    # 2. Gender
    lower = text.lower()
    if "female" in lower:
        fields["Gender"] = "FEMALE"
    elif "male" in lower:
        fields["Gender"] = "MALE"
        
    # 3. DOB / Year of Birth
    dob_match = re.findall(r"(?:dob|d\.o\.b|date of birth|year of birth|birth)\s*[:\-\/]?\s*([0-9]{2}[\/\-][0-9]{2}[\/\-][0-9]{4}|[0-9]{4})", text, re.IGNORECASE)
    if dob_match:
        fields["Date of Birth"] = dob_match[0]
    else:
        date_cand = re.findall(r"\b[0-3]?[0-9][\/\-][0-1]?[0-9][\/\-][12][90][0-9]{2}\b", text)
        if date_cand:
            fields["Date of Birth"] = date_cand[0]

    # 4. Name extraction
    name_found = ""
    for idx, line in enumerate(lines):
        clean = line.strip()
        if re.search(r"enrollment|enrolment", clean, re.IGNORECASE):
            # Often next 1-2 lines contain "To [Name]" or the name
            for j in range(idx + 1, min(idx + 4, len(lines))):
                candidate = re.sub(r"^to\s+", "", lines[j], flags=re.IGNORECASE).strip()
                candidate = re.sub(r"[^a-zA-Z\s\.]", "", candidate).strip()
                if len(candidate) > 3 and not re.search(r"india|government|authority|aadhaar", candidate, re.IGNORECASE):
                    name_found = candidate
                    break
        if name_found:
            break
            
    if not name_found:
        # Search lines above DOB
        for idx, line in enumerate(lines):
            if "dob" in line.lower() or "year of birth" in line.lower():
                if idx > 0:
                    cand = re.sub(r"[^a-zA-Z\s\.]", "", lines[idx - 1]).strip()
                    if len(cand) > 2:
                        name_found = cand
                break
                
    if name_found:
        fields["Full Name"] = name_found

    return fields

def extract_pan(text: str, lines: List[str]) -> Dict[str, Any]:
    fields = {}
    
    # 1. PAN Number
    pan_match = re.findall(r"\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b", text)
    if pan_match:
        fields["PAN Number"] = pan_match[0]
        
    # 2. DOB
    dob_match = re.findall(r"\b[0-3]?[0-9][\/\-][0-1]?[0-9][\/\-][12][90][0-9]{2}\b", text)
    if dob_match:
        fields["Date of Birth"] = dob_match[0]

    # 3. Name & Father's Name
    for idx, line in enumerate(lines):
        if re.search(r"father|father's", line, re.IGNORECASE):
            # Father's name is usually on this line or next line
            val = re.sub(r".*father['s\s]*name\s*[:\-\/]*", "", line, flags=re.IGNORECASE).strip()
            if not val and idx + 1 < len(lines):
                val = lines[idx + 1].strip()
            fields["Father's Name"] = re.sub(r"[^a-zA-Z\s\.]", "", val).strip()
            
            # The holder's name was often right above father's name
            if idx > 0 and "Full Name" not in fields:
                prev = re.sub(r".*name\s*[:\-\/]*", "", lines[idx - 1], flags=re.IGNORECASE).strip()
                if len(prev) > 2 and not re.search(r"department|income|tax|card", prev, re.IGNORECASE):
                    fields["Full Name"] = re.sub(r"[^a-zA-Z\s\.]", "", prev).strip()

    if "Full Name" not in fields:
        # Search for Name label
        for idx, line in enumerate(lines):
            if re.search(r"\bname\b", line, re.IGNORECASE) and not re.search(r"father|department|permanent", line, re.IGNORECASE):
                val = re.sub(r".*name\s*[:\-\/]*", "", line, flags=re.IGNORECASE).strip()
                if not val and idx + 1 < len(lines):
                    val = lines[idx + 1].strip()
                clean = re.sub(r"[^a-zA-Z\s\.]", "", val).strip()
                if len(clean) > 2:
                    fields["Full Name"] = clean
                    break

    return fields

def extract_driving_license(text: str, lines: List[str]) -> Dict[str, Any]:
    fields = {}
    
    # DL number
    dl_match = re.findall(r"\b[A-Z]{2}[0-9]{2}[0-9A-Z]{11,15}\b", text)
    if not dl_match:
        dl_match = re.findall(r"\b[A-Z]{2}[-\s]?[0-9]{2}[-\s]?[0-9]{11,15}\b", text)
    if dl_match:
        fields["License Number"] = dl_match[0].replace("\n", "").strip()

    # Dates
    dates = re.findall(r"\b[0-3]?[0-9][\/\-][0-1]?[0-9][\/\-][12][90][0-9]{2}\b", text)
    if dates:
        fields["Date of Issue / DOB"] = dates[0]
        if len(dates) > 1:
            fields["Valid Till / Expiry"] = dates[-1]

    # State / Authority
    state_match = re.findall(r"(maharashtra|delhi|karnataka|tamil nadu|uttar pradesh|rajasthan|gujarat|kerala|punjab|haryana)", text, re.IGNORECASE)
    if state_match:
        fields["State Authority"] = state_match[0].title()

    # Name
    for idx, line in enumerate(lines):
        if re.search(r"\bname\b", line, re.IGNORECASE) and not re.search(r"licence|union|authority", line, re.IGNORECASE):
            val = re.sub(r".*name\s*[:\-\/]*", "", line, flags=re.IGNORECASE).strip()
            if not val and idx + 1 < len(lines):
                val = lines[idx + 1].strip()
            clean = re.sub(r"[^a-zA-Z\s\.]", "", val).strip()
            if len(clean) > 2:
                fields["Full Name"] = clean
                break

    return fields

def extract_voter_id(text: str, lines: List[str]) -> Dict[str, Any]:
    fields = {}
    
    # EPIC number
    epic_match = re.findall(r"\b[A-Z]{3}[0-9]{7}\b", text)
    if epic_match:
        fields["EPIC / Voter Card No"] = epic_match[0]

    # Name
    for idx, line in enumerate(lines):
        if re.search(r"elector'?s?\s*name", line, re.IGNORECASE):
            val = re.sub(r".*name\s*[:\-\/]*", "", line, flags=re.IGNORECASE).strip()
            if not val and idx + 1 < len(lines):
                val = lines[idx + 1].strip()
            clean = re.sub(r"[^a-zA-Z\s\.]", "", val).strip()
            if len(clean) > 2:
                fields["Elector Name"] = clean
                break

    # Father/Spouse
    for idx, line in enumerate(lines):
        if re.search(r"father'?s?\s*name|husband'?s?\s*name", line, re.IGNORECASE):
            val = re.sub(r".*name\s*[:\-\/]*", "", line, flags=re.IGNORECASE).strip()
            if not val and idx + 1 < len(lines):
                val = lines[idx + 1].strip()
            clean = re.sub(r"[^a-zA-Z\s\.]", "", val).strip()
            if len(clean) > 2:
                fields["Relation Name"] = clean
                break

    # Gender
    if "female" in text.lower():
        fields["Gender"] = "FEMALE"
    elif "male" in text.lower():
        fields["Gender"] = "MALE"

    return fields

def extract_passport(text: str, lines: List[str]) -> Dict[str, Any]:
    fields = {}
    
    # Passport Number
    p_num = re.findall(r"\b[A-Z]{1}[0-9]{7}\b", text)
    if p_num:
        fields["Passport Number"] = p_num[0]

    fields["Country / Issuing Authority"] = "Republic of India"
    fields["Nationality"] = "INDIAN"

    # MRZ Parsing (P<IND...)
    mrz = re.findall(r"P<IND([A-Z<]+)", text)
    if mrz:
        raw_mrz = mrz[0].replace("\n", "").strip()
        parts = [p for p in raw_mrz.split("<") if p]
        if len(parts) >= 2:
            fields["Surname"] = parts[0]
            fields["Given Name"] = " ".join(parts[1:])
        elif len(parts) == 1:
            fields["Given Name"] = parts[0]

    return fields

def extract_salary_slip(text: str, lines: List[str]) -> Dict[str, Any]:
    fields = {}
    
    # Pay Period
    period = re.findall(r"(?:salary\s*slip\s*for|payslip\s*for|month)\s*[:\-]?\s*([a-zA-Z]{3,9}\s*[0-9]{4})", text, re.IGNORECASE)
    if period:
        fields["Pay Period"] = period[0].strip()

    # Net Pay
    net = re.findall(r"(?:net\s*pay|net\s*salary|take\s*home)\s*[:\-]?\s*(?:rs\.?|inr)?\s*([0-9,]+(?:\.[0-9]{2})?)", text, re.IGNORECASE)
    if net:
        fields["Net Pay"] = f"INR {net[0]}"
    else:
        # Amount in words or standalone numbers
        num_cands = re.findall(r"\b[1-9][0-9]{4,6}\b", text)
        if num_cands:
            fields["Net Pay (Approx)"] = f"INR {num_cands[-1]}"

    # Company Name
    if len(lines) > 0:
        cname = lines[0].strip()
        if len(cname) > 3 and not re.search(r"salary|payslip|slip", cname, re.IGNORECASE):
            fields["Company / Employer"] = cname

    return fields

def extract_form16(text: str, lines: List[str]) -> Dict[str, Any]:
    fields = {}
    
    # Assessment Year
    ay = re.findall(r"(?:assessment\s*year|ay)\s*[:\-]?\s*([0-9]{4}\s*[\-\/]?\s*[0-9]{2,4})", text, re.IGNORECASE)
    if ay:
        fields["Assessment Year"] = ay[0].strip()

    # Certificate No
    cert = re.findall(r"certificate\s*no\.?\s*[:\-]?\s*([a-zA-Z0-9]+)", text, re.IGNORECASE)
    if cert:
        fields["Certificate No"] = cert[0].strip()

    # PAN of Employee
    pans = re.findall(r"\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b", text)
    if pans:
        fields["Employee PAN"] = pans[0]
        if len(pans) > 1:
            fields["Employer / Deductor TAN/PAN"] = pans[1]

    # TAN
    tans = re.findall(r"\b[A-Z]{4}[0-9]{5}[A-Z]{1}\b", text)
    if tans:
        fields["Deductor TAN"] = tans[0]

    return fields

def extract_bank_statement(text: str, lines: List[str]) -> Dict[str, Any]:
    fields = {}
    
    # Bank Name
    for bname in ["State Bank of India", "HDFC Bank", "ICICI Bank", "Axis Bank", "Punjab National Bank", "Bank of Baroda", "Kotak Mahindra Bank", "Canara Bank"]:
        if bname.lower() in text.lower():
            fields["Bank Name"] = bname
            break

    # Account Number
    ac_match = re.findall(r"(?:account\s*no|a\/c\s*no|ac\s*no|accountnumber)\.?\s*[:\-]?\s*([0-9Xx\*\-]{8,18})", text, re.IGNORECASE)
    if ac_match:
        fields["Account Number"] = ac_match[0].strip()

    # IFSC
    ifsc = re.findall(r"\b[A-Z]{4}0[A-Z0-9]{6}\b", text)
    if ifsc:
        fields["IFSC Code"] = ifsc[0]

    # Statement Sections detected
    sections = []
    if "accountholderdetails" in text.lower() or "account holder" in text.lower():
        sections.append("Account Holder Details")
    if "accountstatement" in text.lower() or "statement" in text.lower():
        sections.append("Transaction Ledger")
    if "accountbalance" in text.lower() or "total balance" in text.lower():
        sections.append("Balance Summary")
    if sections:
        fields["Statement Sections"] = ", ".join(sections)

    # Dates
    dates = re.findall(r"\b[0-3]?[0-9][\/\-][0-1]?[0-9][\/\-][12][90][0-9]{2}\b", text)
    if dates:
        fields["Statement Date / Period"] = " - ".join(dates[:2])

    return fields

def extract_cheque(text: str, lines: List[str]) -> Dict[str, Any]:
    fields = {}
    
    # Bank Name
    for bname in ["State Bank of India", "HDFC Bank", "ICICI Bank", "Axis Bank", "Punjab National Bank", "Bank of Baroda", "Canara Bank"]:
        if bname.lower() in text.lower():
            fields["Bank Name"] = bname
            break

    # IFSC Code
    ifsc = re.findall(r"\b[A-Z]{4}0[A-Z0-9]{6}\b", text)
    if ifsc:
        fields["IFSC Code"] = ifsc[0]

    # Payee
    payee = re.findall(r"pay\s+([a-zA-Z\s\.\&]+?)(?:\s+or\s+bearer|\s+rupees|\n|$)", text, re.IGNORECASE)
    if payee:
        cand = payee[0].strip()
        if len(cand) > 2:
            fields["Payee Name"] = cand

    # Amount
    amount = re.findall(r"(?:₹|rs\.?|inr)?\s*([0-9,]+(?:\.[0-9]{2})?)\s*\/\-", text, re.IGNORECASE)
    if amount:
        fields["Cheque Amount"] = f"INR {amount[0]}"

    return fields

def extract_utility_bill(text: str, lines: List[str]) -> Dict[str, Any]:
    fields = {}
    
    # Provider
    if "water authority" in text.lower():
        fields["Utility Provider"] = "Kerala Water Authority"
    elif "electricity" in text.lower() or "power" in text.lower():
        fields["Utility Provider"] = "Electricity Distribution Co."

    # Bill Number
    bill_no = re.findall(r"(?:bill\s*no|bill\s*number|consumer\s*id)\s*[:\-]?\s*([0-9A-Za-z]+)", text, re.IGNORECASE)
    if bill_no:
        fields["Bill / Consumer No"] = bill_no[0]

    # Dates
    due_date = re.findall(r"(?:due\s*date|payment\s*by)\s*[:\-]?\s*([0-3]?[0-9][\/\-][0-1]?[0-9][\/\-][12][90][0-9]{2}|[0-3]?[0-9]-[a-zA-Z]{3}-[0-9]{4})", text, re.IGNORECASE)
    if due_date:
        fields["Due Date"] = due_date[0]

    return fields

EXTRACTOR_ROUTER = {
    "aadhar": extract_aadhaar,
    "pan": extract_pan,
    "driver": extract_driving_license,
    "voter": extract_voter_id,
    "passport": extract_passport,
    "salary": extract_salary_slip,
    "form16": extract_form16,
    "bank": extract_bank_statement,
    "cheque": extract_cheque,
    "bill": extract_utility_bill
}

def extract_document_fields(doc_type: str, text: str, lines: List[str] = None) -> Dict[str, Any]:
    """Extracts typed structured attributes based on classified document category."""
    if lines is None:
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        
    fn = EXTRACTOR_ROUTER.get(doc_type)
    if fn:
        try:
            return fn(text, lines)
        except Exception as e:
            return {"Extraction Note": f"Parsed with generic pattern: {str(e)}"}
            
    # Generic fallback
    generic = {}
    dates = re.findall(r"\b[0-3]?[0-9][\/\-][0-1]?[0-9][\/\-][12][90][0-9]{2}\b", text)
    if dates:
        generic["Detected Dates"] = ", ".join(dates[:2])
    return generic
