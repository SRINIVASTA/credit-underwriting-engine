# underwriting_core.py
# Place this file in the exact same directory folder as your app.py

def calculate_score(profile):
    """
    Calculates a basic corporate risk credit score from profile parameters.
    """
    try:
        cibil = int(profile.get("cibil_score", 700))
        enquiries = int(profile.get("recent_enq", 0))
        net_operat = int(profile.get("net_operat", 0))
        tol = int(profile.get("tol", 1)) # avoid division by zero
        
        # Calculate basic score metric components
        base_score = cibil - (enquiries * 15)
        leverage_ratio = net_operat / tol
        
        if leverage_ratio > 2.0:
            base_score += 50
        elif leverage_ratio < 0.8:
            base_score -= 50
            
        return int(max(300, min(900, base_score)))
    except Exception:
        return 650 # Safe mid-tier baseline fallback

def evaluate_risk(score):
    """
    Maps an absolute numerical credit score to a risk assessment category string.
    """
    if score >= 750:
        return "Low Risk (Tier 1 Preferred)"
    elif score >= 650:
        return "Moderate Risk (Tier 2 Standard)"
    else:
        return "High Risk (Tier 3 Escalate)"

def process_financials(profile):
    """
    Calculates operational health indexes like debt-to-equity or liquid current ratio.
    """
    try:
        current_assets = int(profile.get("current_as", 0))
        current_liabilities = int(profile.get("current_lia", 1))
        return round(current_assets / current_liabilities, 2)
    except Exception:
        return 1.0
