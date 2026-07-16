import math
from fpdf import FPDF

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

def generate_sanction_memo_pdf(meta_data, metrics_data, scoring_data, results_data, qualitative_5cs=None): 
    """
    Compiles banking metrics, user qualitative parameters, and operational 
    red flags directly into a standardized downloadable PDF binary stream.
    """
    pdf = SanctionMemoPDF() 
    pdf.add_page() 
 
    # --- 1. EXECUTIVE LOAN PROFILE SUMMARY ---
    pdf.set_font("Helvetica", "B", 12) 
    pdf.cell(0, 8, "1. EXECUTIVE LOAN PROFILE SUMMARY", ln=True) 
    pdf.set_font("Helvetica", "", 10) 
    pdf.cell(95, 6, f"Target Industry Sector: {str(meta_data.get('industry', 'N/A'))}") 
    pdf.cell(95, 6, f"Evaluated Scoring Grade: {str(scoring_data.get('score', 0))} / 100 Points", ln=True) 
    pdf.cell(95, 6, f"Risk Tier Assigned: {str(results_data.get('tier_name', 'N/A'))}") 
    pdf.cell(95, 6, f"KYC Compliance Track: {'PASSED' if meta_data.get('kyc_cleared', False) else 'FAILED - HOLD'}", ln=True) 
    pdf.ln(5) 

    # --- 2. UNDERWRITING ANALYSIS FACTOR BREAKDOWN ---
    pdf.set_font("Helvetica", "B", 12) 
    pdf.cell(0, 8, "2. UNDERWRITING ANALYSIS FACTOR BREAKDOWN", ln=True) 
    pdf.set_font("Helvetica", "B", 10) 
 
    pdf.cell(65, 7, "Underwriting Parameter", border=1) 
    pdf.cell(40, 7, "Observed Value", border=1) 
    pdf.cell(40, 7, "Bank Benchmarks", border=1) 
    pdf.cell(45, 7, "Status", border=1, ln=True) 
 
    pdf.set_font("Helvetica", "", 10) 
    metrics_rows = [
        ("Debt Service Cover (DSCR)", f"{metrics_data.get('dscr', 0)}x", ">= 1.25x", "Pass" if metrics_data.get('dscr', 0) >= 1.25 else "Fail"),
        ("Current Ratio Liquidity", f"{metrics_data.get('cr_ratio', 0)}x", ">= 1.20x", "Pass" if metrics_data.get('cr_ratio', 0) >= 1.20 else "Fail"),
        ("Structural Capital Leverage", f"{metrics_data.get('tol_tnw', 0)}x", "<= 3.00x", "Pass" if metrics_data.get('tol_tnw', 0) <= 3.00 else "Fail"),
        ("Loan To Value Ratio", f"{metrics_data.get('ltv', 0)}%", "<= 60.0%", "Pass" if metrics_data.get('ltv', 0) <= 60.0 else "Fail")
    ]
 
    for row in metrics_rows: 
        pdf.cell(65, 7, str(row[0]), border=1) 
        pdf.cell(40, 7, str(row[1]), border=1) 
        pdf.cell(40, 7, str(row[2]), border=1) 
        pdf.cell(45, 7, str(row[3]), border=1, ln=True) 
    pdf.ln(5)

    # --- 3. QUALITATIVE ASSESSMENT Framework (THE 5 Cs) ---
    if qualitative_5cs:
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "3. QUALITATIVE ASSESSMENT (THE 5 Cs OF CREDIT)", ln=True)
        pdf.ln(2)
        for label, key in [("Character", "character"), ("Capacity", "capacity"), ("Capital", "capital"), ("Collateral", "collateral"), ("Conditions", "conditions")]:
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(0, 5, f"• {label}:", ln=True)
            pdf.set_font("Helvetica", "", 9)
            text_narrative = qualitative_5cs.get(key, "").strip() or "No observations recorded."
            pdf.multi_cell(0, 5, text_narrative)
            pdf.ln(2)
        pdf.ln(3)

    # --- 4. COMMITTEE DISBURSEMENT RESOLUTION --- 
    pdf.set_font("Helvetica", "B", 12) 
    pdf.cell(0, 8, "4. COMMITTEE DISBURSEMENT RESOLUTION", ln=True) 
    pdf.set_font("Helvetica", "", 10) 
    pdf.cell(0, 6, f"Requested Facility Amount: INR {float(results_data.get('req_loan', 0)):,.2f}", ln=True) 
    pdf.cell(0, 6, f"Calculated Cash-Flow Ceiling Cap: INR {float(results_data.get('cash_flow_cap', 0)):,.2f}", ln=True) 
    pdf.cell(0, 6, f"Calculated Collateral Cover Cap: INR {float(results_data.get('asset_cap', 0)):,.2f}", ln=True) 
 
    pdf.set_font("Helvetica", "B", 11) 
    pdf.ln(2) 
    pdf.cell(0, 8, f"FINAL APPROVED POLICY SANCTION OFFER: INR {float(results_data.get('final_sanction', 0)):,.2f}", ln=True) 
    pdf.cell(0, 8, f"RISK BASED PRICING YIELD APPLIED (APR): {round(float(results_data.get('final_rate', 0)), 2)}%", ln=True) 
 
    # --- 5. CRITICAL WARNINGS AND FLAGS --- 
    if scoring_data.get("flags"): 
        pdf.ln(3) 
        pdf.set_font("Helvetica", "B", 12) 
        pdf.cell(0, 8, "5. CRITICAL OPERATIONAL WARNING NOTES / FLAGS", ln=True) 
        pdf.set_font("Helvetica", "I", 9) 
        for flag in scoring_data["flags"]: 
            pdf.cell(0, 6, f"- {str(flag)}", ln=True) 
 
    return bytes(pdf.output())
