import math 
import json 
import io 
import csv 
import requests 
from fpdf import FPDF 

def parse_uploaded_file_stream(uploaded_file): 
    """ 
    Decodes uploaded files, supporting BOTH horizontal multi-column CSVs 
    and structured JSON data payloads with robust string-cleaning protections. 
    """ 
    if uploaded_file is None: 
        return None 
    try: 
        file_bytes = uploaded_file.read() 
        raw_data = {} 
        if uploaded_file.name.endswith('.csv'): 
            text_stream = io.StringIO(file_bytes.decode("utf-8")) 
            reader = csv.DictReader(text_stream) 
            for row in reader: 
                raw_data = {str(k).strip(): str(v).strip() for k, v in row.items() if k is not None} 
                break 
        elif uploaded_file.name.endswith('.json'): 
            raw_data = json.loads(file_bytes.decode("utf-8")) 
        else: 
            return None 

        def str_to_bool(v): 
            if isinstance(v, bool): return v 
            return str(v).strip().lower() in ("true", "1", "yes", "t") 
        
        validated_profile = { 
            "industry": str(raw_data.get("industry", "Pharma")), 
            "cibil_score": int(float(raw_data.get("cibil_score", 700))), 
            "recent_enquiries_30_days": int(float(raw_data.get("recent_enquiries_30_days", 0))), 
            "net_operating_income": float(raw_data.get("net_operating_income", 0.0)), 
            "annual_debt_service": float(raw_data.get("annual_debt_service", 1.0)), 
            "tol": float(raw_data.get("tol", 0.0)), 
            "tnw": float(raw_data.get("tnw", 1.0)), 
            "current_assets": float(raw_data.get("current_assets", 0.0)), 
            "current_liabilities": float(raw_data.get("current_liabilities", 1.0)), 
            "requested_loan": float(raw_data.get("requested_loan", 0.0)), 
            "collateral_value": float(raw_data.get("collateral_value", 0.0)), 
            "loan_term": int(float(raw_data.get("loan_term", 5))), 
            "gst_turnover": float(raw_data.get("gst_turnover", 0.0)), 
            "bank_credits": float(raw_data.get("bank_credits", 0.0)), 
            "bounces": str_to_bool(raw_data.get("bounces", False)), 
            "pan_ent": str_to_bool(raw_data.get("pan_ent", False)), 
            "gst_ent": str_to_bool(raw_data.get("gst_ent", False)), 
            "biz_ent": str_to_bool(raw_data.get("biz_ent", False)), 
            "br_ent": str_to_bool(raw_data.get("br_ent", False)), 
            "num_directors": int(float(raw_data.get("num_directors", 1))), 
            "directors_passed": int(float(raw_data.get("directors_passed", 0))) 
        } 
        return validated_profile 
    except Exception: 
        return None 

def fetch_borrower_central_data(borrower_id): 
    if not borrower_id.strip(): return None 
    mock_endpoint_url = "https://typicode.com" 
    try: 
        response = requests.get(mock_endpoint_url, timeout=5.0) 
        if response.status_code == 200: 
            return { 
                "industry": "Healthcare", "cibil_score": 775, "recent_enquiries_30_days": 1, 
                "net_operating_income": 2500000, "annual_debt_service": 1100000, 
                "tol": 5500000, "tnw": 4000000, "current_assets": 3200000, "current_liabilities": 1500000, 
                "requested_loan": 7500000, "collateral_value": 16000000, "loan_term": 7, 
                "gst_turnover": 15000000, "bank_credits": 15150000, "bounces": False, 
                "pan_ent": True, "gst_ent": True, "biz_ent": True, "br_ent": True, "directors_passed": 2, 
                "num_directors": 2 
            } 
        return None 
    except requests.exceptions.RequestException: return None 

def safe_calculate_metrics(noi, annual_ds, ca, cl, tol, tnw, req_loan, collateral): 
    dscr = round(noi / annual_ds, 2) if annual_ds > 0 else (0.0 if noi <= 0 else 99.9) 
    if noi < 0 and annual_ds == 0: dscr = -99.9 
    cr_ratio = round(ca / cl, 2) if cl > 0 else 99.9 
    tol_tnw = round(tol / tnw, 2) if tnw > 0 else (0.0 if tol == 0 else 99.9) 
    ltv = round((req_loan / collateral) * 100, 2) if collateral > 0 else 0.0 
    return dscr, cr_ratio, tol_tnw, ltv 

def calculate_pv_amortization(annual_pmt, annual_rate, years): 
    r = (annual_rate / 100) 
    if r <= 0: return annual_pmt * years 
    return annual_pmt * ((1 - math.pow(1 + r, -years)) / r) 

def map_pricing_matrix(risk_score, base_mclr): 
    if risk_score >= 85: return (base_mclr + 1.25), 65.0, 1.25, "Elite (Low Risk)", "success" 
    elif risk_score >= 65: return (base_mclr + 2.50), 60.0, 1.35, "Standard (Moderate Risk)", "info" 
    elif risk_score >= 50: return (base_mclr + 4.50), 45.0, 1.50, "Subprime (High Risk)", "warning" 
    else: return 0.0, 0.0, 0.0, "Decline (Critical Risk)", "error" 

def calculate_amortization_schedule(final_sanction, final_rate, loan_term): 
    r_rate = final_rate / 100 
    annual_pmt = final_sanction * (r_rate * math.pow(1 + r_rate, loan_term)) / (math.pow(1 + r_rate, loan_term) - 1) if r_rate > 0 else final_sanction / loan_term 
    balance, total_int_paid = final_sanction, 0 
    years, balances, cumulative_interest = ["Year 0"], [balance], [0.0] 
    for year in range(1, loan_term + 1): 
        interest_paid = balance * r_rate 
        balance = max(0.0, balance - (annual_pmt - interest_paid)) 
        total_int_paid += interest_paid 
        years.append(f"Year {year}")
        balances.append(balance) 
        cumulative_interest.append(total_int_paid) 
    return years, balances, cumulative_interest 

class SanctionMemoPDF(FPDF): 
    def header(self): 
        self.set_font("Helvetica", "B", 14) 
        self.cell(0, 10, "OFFICIAL CREDIT UNDERWRITING SANCTION MEMO", border=False, ln=True, align="C") 
        self.set_font("Helvetica", "I", 9) 
        self.cell(0, 5, "Confidential - Internal Bank Risk Committee Vetting Document", border=False, ln=True, align="C") 
        self.ln(5) 
        self.line(10, self.get_y(), 200, self.get_y()) 
        self.ln(5) 
        
    def footer(self): 
        self.set_y(-15) 
        self.set_font("Helvetica", "I", 8) 
        self.cell(0, 10, f"Page {self.page_no()} | System Verification Secured Framework", align="C") 

def generate_sanction_memo_pdf(meta_data, metrics_data, scoring_data, results_data): 
    """Compiles structured parameters into a valid PDF binary byte stream without encoding failures.""" 
    pdf = SanctionMemoPDF() 
    pdf.add_page() 
 
    # 1. Executive Summary Profile Banner 
    pdf.set_font("Helvetica", "B", 12) 
    pdf.cell(0, 8, "1. EXECUTIVE LOAN PROFILE SUMMARY", ln=True) 
    pdf.set_font("Helvetica", "", 10) 
    pdf.cell(95, 6, f"Target Industry Sector: {str(meta_data['industry'])}") 
    pdf.cell(95, 6, f"Evaluated Scoring Grade: {str(scoring_data['score'])} / 100 Points", ln=True) 
    pdf.cell(95, 6, f"Risk Tier Assigned: {str(results_data['tier_name'])}") 
    pdf.cell(95, 6, f"KYC Compliance Track: {'PASSED' if meta_data['kyc_cleared'] else 'FAILED - HOLD'}", ln=True) 
    pdf.ln(5) 

    # 2. Risk Metrics Table Ingestion Block 
    pdf.set_font("Helvetica", "B", 12) 
    pdf.cell(0, 8, "2. UNDERWRITING ANALYSIS FACTOR BREAKDOWN", ln=True) 
    pdf.set_font("Helvetica", "B", 10) 
 
    # Draw Table Headers 
    pdf.cell(65, 7, "Underwriting Parameter", border=1) 
    pdf.cell(40, 7, "Observed Value", border=1) 
    pdf.cell(40, 7, "Bank Benchmarks", border=1) 
    pdf.cell(45, 7, "Status", border=1, ln=True) 
 
    pdf.set_font("Helvetica", "", 10) 
    metrics_rows = [ 
        ("Debt Service Cover (DSCR)", f"{metrics_data['dscr']}x", ">= 1.25x", "Pass" if metrics_data['dscr'] >= 1.25 else "Fail"), 
        ("Current Ratio Liquidity", f"{metrics_data['cr_ratio']}x", ">= 1.20x", "Pass" if metrics_data['cr_ratio'] >= 1.20 else "Fail"), 
        ("Structural Capital Leverage", f"{metrics_data['tol_tnw']}x", "<= 3.00x", "Pass" if metrics_data['tol_tnw'] <= 3.00 else "Fail"), 
        ("Loan To Value Ratio", f"{metrics_data['ltv']}%", "<= 60.0%", "Pass" if metrics_data['ltv'] <= 60.0 else "Fail"), 
    ] 
 
    for row in metrics_rows: 
        pdf.cell(65, 7, str(row[0]), border=1) 
        pdf.cell(40, 7, str(row[1]), border=1) 
        pdf.cell(40, 7, str(row[2]), border=1) 
        pdf.cell(45, 7, str(row[3]), border=1, ln=True) 

    pdf.ln(5) 
    
    # 3. Final Portfolio Allocation Resolutions 
    pdf.set_font("Helvetica", "B", 12) 
    pdf.cell(0, 8, "3. COMMITTEE DISBURSEMENT RESOLUTION", ln=True) 
    pdf.set_font("Helvetica", "", 10) 
    pdf.cell(0, 6, f"Requested Facility Amount: INR {results_data['req_loan']:,.2f}", ln=True) 
    pdf.cell(0, 6, f"Calculated Cash-Flow Ceiling Cap: INR {results_data['cash_flow_cap']:,.2f}", ln=True) 
    pdf.cell(0, 6, f"Calculated Collateral Cover Cap: INR {results_data['asset_cap']:,.2f}", ln=True) 
 
    pdf.set_font("Helvetica", "B", 11) 
    pdf.ln(2) 
    pdf.cell(0, 8, f"FINAL APPROVED POLICY SANCTION OFFER: INR {results_data['final_sanction']:,.2f}", ln=True) 
    pdf.cell(0, 8, f"RISK BASED PRICING YIELD APPLIED (APR): {round(results_data['final_rate'], 2)}%", ln=True) 
 
    # 4. Warnings and Red Flags Section 
    if scoring_data["flags"]: 
        pdf.ln(3) 
        pdf.set_font("Helvetica", "B", 12) 
        pdf.cell(0, 8, "4. CRITICAL OPERATIONAL WARNING NOTES / FLAGS", ln=True) 
        pdf.set_font("Helvetica", "I", 9) 
        for flag in scoring_data["flags"]: 
            pdf.cell(0, 6, f"- {str(flag)}", ln=True) 
 
    return bytes(pdf.output()) 
