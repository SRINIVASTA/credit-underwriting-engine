import pytest
from underwriting_core import safe_calculate_metrics, generate_sanction_memo_pdf, map_pricing_matrix

def test_financial_metrics_math(): 
    dscr, cr_ratio, tol_tnw, ltv = safe_calculate_metrics(2500000, 1100000, 3200000, 1500000, 5500000, 4000000, 7500000, 16000000) 
    assert dscr == pytest.approx(2.27, abs=1e-2) 
    assert cr_ratio == pytest.approx(2.13, abs=1e-2) 
    assert tol_tnw == pytest.approx(1.38, abs=1e-2) 
    assert ltv == pytest.approx(46.88, abs=1e-2) 

def test_zero_collateral_edge_case(): 
    dscr, cr_ratio, tol_tnw, ltv = safe_calculate_metrics(2000000, 1000000, 1000000, 500000, 3000000, 1000000, 500000, 0) 
    assert ltv == 0.0 
    assert dscr == 2.0

def test_risk_based_pricing_matrix():
    rate, max_ltv, min_dscr, tier_name, tier_type = map_pricing_matrix(90, 8.50)
    assert tier_name == "Elite (Low Risk)"
    assert rate == 9.75

def test_pdf_multi_cell_paragraph_overflow_protection():
    meta = {"industry": "Pharma", "kyc_cleared": True}
    metrics = {"dscr": 1.5, "cr_ratio": 1.2, "tol_tnw": 2.0, "ltv": 50.0}
    scoring = {"score": 75, "flags": []}
    results = {"req_loan": 500000, "cash_flow_cap": 600000, "asset_cap": 700000, "final_sanction": 500000, "final_rate": 10.5, "tier_name": "Standard"}
    extreme_qualitative = {
        "character": "Flawless baseline corporate parameters checking indicators. " * 50,
        "capacity": "Adequate capital generation streams documented.",
        "capital": "High historical partner skin in the game.",
        "collateral": "Property valuation verified clear.",
        "conditions": "Standard parameters map well against current regional segment trends."
    }
    pdf_bytes = generate_sanction_memo_pdf(meta, metrics, scoring, results, qualitative_5cs=extreme_qualitative)
    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes.startswith(b"%PDF")
