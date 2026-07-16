import math 
import json 
import io 
import csv 
import requests 

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
    """
    Calculates primary credit metrics and financial covenants including
    DSCR, Current Ratio, TOL/TNW, LTV Cover, and FOIR.
    """
    dscr = round(noi / annual_ds, 2) if annual_ds > 0 else (0.0 if noi <= 0 else 99.9) 
    if noi < 0 and annual_ds == 0: dscr = -99.9 
    cr_ratio = round(ca / cl, 2) if cl > 0 else 99.9 
    tol_tnw = round(tol / tnw, 2) if tnw > 0 else (0.0 if tol == 0 else 99.9) 
    ltv = round((req_loan / collateral) * 100, 2) if collateral > 0 else 0.0 
    
    # CHEAT SHEET INTEGRATION: Fixed Obligation to Income Ratio (FOIR) calculation
    # Employs annual debt obligations relative to historical net business income
    foir = round((annual_ds / noi) * 100, 2) if noi > 0 else 0.0
    
    return dscr, cr_ratio, tol_tnw, ltv, foir 

def calculate_pv_amortization(annual_pmt, annual_rate, years): 
    r = (annual_rate / 100) 
    if r <= 0: return annual_pmt * years 
    return annual_pmt * ((1 - math.pow(1 + r, -years)) / r) 

def map_pricing_matrix(risk_score, base_mclr, industry_classification="Pharma"): 
    """
    Assigns loan grade pricing tiers based on total scorecard risk weightings.
    Applies standard MCLR premium spreads along with Cheat Sheet defined 
    Industry Matrix risk loading penalties for sector specific vulnerabilities.
    """
    # Baseline Scorecard Grade Assignments
    if risk_score >= 85: 
        final_rate, max_ltv, min_dscr, tier_name, tier_type = (base_mclr + 1.25), 65.0, 1.25, "Elite (Low Risk)", "success" 
    elif risk_score >= 65: 
        final_rate, max_ltv, min_dscr, tier_name, tier_type = (base_mclr + 2.50), 60.0, 1.35, "Standard (Moderate Risk)", "info" 
    elif risk_score >= 50: 
        final_rate, max_ltv, min_dscr, tier_name, tier_type = (base_mclr + 4.50), 45.0, 1.50, "Subprime (High Risk)", "warning" 
    else: 
        return 0.0, 0.0, 0.0, "Decline (Critical Risk)", "error" 
        
    # CHEAT SHEET INDUSTRY RISK MATRIX PREMIUM LOADING:
    # Captures High Risk sector classifications (Real Estate / Construction / Startups)
    # and automatically appends a +1.50% yield premium penalty to secure portfolio risk.
    high_risk_sectors = ["real estate", "real estate/const.", "construction", "startup", "startups/new business"]
    if str(industry_classification).strip().lower() in high_risk_sectors:
        final_rate += 1.50
        tier_name += " [High-Risk Sector Spread Applied]"
        
    return final_rate, max_ltv, min_dscr, tier_name, tier_type 

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
