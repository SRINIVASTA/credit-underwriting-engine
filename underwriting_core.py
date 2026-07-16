import math
import io
import csv
import json
from fpdf import FPDF

def validate_extended_profile(raw_data):
    """Validates borrower payloads, mapping risk fields from the cheat sheet."""
    def str_to_bool(v):
        if isinstance(v, bool): return v
        return str(v).strip().lower() in ("true", "1", "yes", "t")

    return {
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
        "overdrawn_od": str_to_bool(raw_data.get("overdrawn_od", False)),
        "frequent_address_changes": str_to_bool(raw_data.get("frequent_address_changes", False)),
        "large_cash_deposits": str_to_bool(raw_data.get("large_cash_deposits", False)),
        "litigation_pending": str_to_bool(raw_data.get("litigation_pending", False)),
        "pan_ent": str_to_bool(raw_data.get("pan_ent", False)),
        "gst_ent": str_to_bool(raw_data.get("gst_ent", False)),
        "biz_ent": str_to_bool(raw_data.get("biz_ent", False)),
        "br_ent": str_to_bool(raw_data.get("br_ent", False)),
        "num_directors": int(float(raw_data.get("num_directors", 1))),
        "directors_passed": int(float(raw_data.get("directors_passed", 0)))
    }

def fetch_borrower_central_data(borrower_id): 
    if not borrower_id.strip(): return None 
    return { 
        "industry": "Healthcare", "cibil_score": 775, "recent_enquiries_30_days": 1, 
        "net_operating_income": 2500000, "annual_debt_service": 1100000, 
        "tol": 5500000, "tnw": 4000000, "current_assets": 3200000, "current_liabilities": 1500000, 
        "requested_loan": 7500000, "collateral_value": 16000000, "loan_term": 7, 
        "gst_turnover": 15000000, "bank_credits": 15150000, "bounces": False, 
        "overdrawn_od": False, "frequent_address_changes": False, "large_cash_deposits": False, "litigation_pending": False,
        "pan_ent": True, "gst_ent": True, "biz_ent": True, "br_ent": True, "directors_passed": 2, "num_directors": 2 
    } 

def safe_calculate_metrics(noi, annual_ds, ca, cl, tol, tnw, req_loan, collateral): 
    dscr = round(noi / annual_ds, 2) if annual_ds > 0 else (0.0 if noi <= 0 else 99.9) 
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

def evaluate_system_red_flags(profile, variance_pct):
    flags = []
    if profile["recent_enquiries_30_days"] > 3:
        flags.append("Multiple credit enquiries within a compact 30-day window (High Velocity Risk).")
    if profile["frequent_address_changes"]:
        flags.append("Frequent corporate or director address changes flagged in records.")
    if profile["bounces"]:
        flags.append("Operational account history shows active Cheque or EMI bouncing events.")
    if profile["overdrawn_od"]:
        flags.append("Borrower's Overdraft (OD) account is chronically overdrawn.")
    if profile["large_cash_deposits"]:
        flags.append("Unexplained large cash deposits identified outside trading parameters.")
    if abs(variance_pct) > 10.0:
        flags.append(f"Turnover Mismatch: Bank Credit vs GST variance ({variance_pct:+.2f}%) exceeds parameters.")
    if profile["litigation_pending"]:
        flags.append("Active or pending corporate litigation identified against entity/property.")
    return flags

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
        self.cell(0, 10, "OFFICIAL CREDIT UNDERWRITING SANCTION MEMO", ln=True, align="C") 
        self.set_font("Helvetica", "I", 9) 
        self.cell(0, 5, "Confidential - Internal Bank Risk Committee Vetting Document", ln=True, align="C") 
        self.ln(5) 
        self.line(10, self.get_y(), 200, self.get_y()) 
        self.ln(5) 
    def footer(self): 
        self.set_y(-15) 
        self.set_font("Helvetica", "I", 8) 
        self.cell(0, 10, f"Page {self.page_no()} | System Verification Secured Framework", align="C") 

def generate_sanction_memo_pdf(meta_data, metrics_data, scoring_data, results_data, qualitative_5cs=None): 
    pdf = SanctionMemoPDF() 
    pdf.add_page() 
 
    pdf.set_font("Helvetica", "B", 12) 
    pdf.cell(0, 8, "1. EXECUTIVE LOAN PROFILE SUMMARY", ln=True) 
    pdf.set_font("Helvetica", "", 10) 
    pdf.cell(95, 6, f"Target Industry Sector: {str(meta_data['industry'])}") 
    pdf.cell(95, 6, f"Evaluated Scoring Grade: {str(scoring_data['score'])} / 100 Points", ln=True) 
    pdf.cell(95, 6, f"Risk Tier Assigned: {str(results_data['tier_name'])}") 
    pdf.cell(95, 6, f"KYC Compliance Track: {'PASSED' if meta_data['kyc_cleared'] else 'FAILED'}", ln=True) 
    pdf.ln(5) 

    pdf.set_font("Helvetica", "B", 12) 
    pdf.cell(0, 8, "2. UNDERWRITING ANALYSIS FACTOR BREAKDOWN", ln=True) 
    pdf.set_font("Helvetica", "B", 10) 
    pdf.cell(65, 7, "Parameter", border=1) 
    pdf.cell(40, 7, "Observed", border=1) 
    pdf.cell(40, 7, "Benchmark", border=1) 
    pdf.cell(45, 7, "Status", border=1, ln=True) 
 
    pdf.set_font("Helvetica", "", 10) 
    rows = [
        ("DSCR", f"{metrics_data['dscr']}x", ">= 1.25x", "Pass" if metrics_data['dscr'] >= 1.25 else "Fail"),
        ("Current Ratio", f"{metrics_data['cr_ratio']}x", ">= 1.20x", "Pass" if metrics_data['cr_ratio'] >= 1.20 else "Fail"),
        ("TOL / TNW", f"{metrics_data['tol_tnw']}x", "<= 3.00x", "Pass" if metrics_data['tol_tnw'] <= 3.00 else "Fail"),
        ("LTV Ratio", f"{metrics_data['ltv']}%", "<= 60.0%", "Pass" if metrics_data['ltv'] <= 60.0 else "Fail")
    ]
    for r in rows:
        pdf.cell(65, 7, r[0], border=1)
        pdf.cell(40, 7, r[1], border=1)
        pdf.cell(40, 7, r[2], border=1)
        pdf.cell(45, 7, r[3], border=1, ln=True)
    pdf.ln(5)

    if qualitative_5cs:
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "3. QUALITATIVE ASSESSMENT (THE 5 Cs OF CREDIT)", ln=True)
        pdf.ln(2)
        for label, key in [("Character", "character"), ("Capacity", "capacity"), ("Capital", "capital"), ("Collateral", "collateral"), ("Conditions", "conditions")]:
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(0, 5, f"• {label}:", ln=True)
            pdf.set_font("Helvetica", "", 9)
            text_narrative = qualitative_5cs.get(key, "").strip() or "No qualitative notes recorded."
            pdf.multi_cell(0, 5, text_narrative)
            pdf.ln(2)
        pdf.ln(3)

    pdf.set_font("Helvetica", "B", 12) 
    pdf.cell(0, 8, "4. COMMITTEE DISBURSEMENT RESOLUTION", ln=True) 
    pdf.set_font("Helvetica", "", 10) 
    pdf.cell(0, 6, f"Requested Facility Amount: INR {results_data['req_loan']:,.2f}", ln=True) 
    pdf.cell(0, 6, f"FINAL APPROVED SANCTION OFFER: INR {results_data['final_sanction']:,.2f}", ln=True) 
    pdf.cell(0, 8, f"RISK BASED PRICING APR: {round(results_data['final_rate'], 2)}%", ln=True) 
 
    if scoring_data["flags"]: 
        pdf.ln(3) 
        pdf.set_font("Helvetica", "B", 12) 
        pdf.cell(0, 8, "5. CRITICAL OPERATIONAL WARNING NOTES / FLAGS", ln=True) 
        pdf.set_font("Helvetica", "I", 9) 
        for flag in scoring_data["flags"]: 
            pdf.cell(0, 6, f"- {str(flag)}", ln=True) 
 
    return bytes(pdf.output())
