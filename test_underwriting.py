import pytest 
from underwriting_core import safe_calculate_metrics, map_pricing_matrix, calculate_pv_amortization 

def test_financial_metrics_math(): 
    noi, annual_ds, ca, cl, tol, tnw, req_loan, collateral = 2500000, 1100000, 3200000, 1500000, 5500000, 4000000, 7500000, 16000000 
    dscr, cr_ratio, tol_tnw, ltv = safe_calculate_metrics(noi, annual_ds, ca, cl, tol, tnw, req_loan, collateral) 
    assert dscr == 2.27 
    assert cr_ratio == 2.13 
    assert tol_tnw == 1.38 
    assert ltv == 46.88 

def test_zero_collateral_edge_case(): 
    dscr, cr_ratio, tol_tnw, ltv = safe_calculate_metrics(2000000, 1000000, 1000000, 500000, 3000000, 1000000, 500000, 0) 
    assert ltv == 0.0 
    assert dscr == 2.0 

def test_risk_based_pricing_matrix(): 
    rate, max_ltv, min_dscr, tier_name, tier_type = map_pricing_matrix(90, 8.50) 
    assert tier_name == "Elite (Low Risk)" 
    assert rate == 9.75 
    rate, max_ltv, min_dscr, tier_name, tier_type = map_pricing_matrix(45, 8.50) 
    assert tier_name == "Decline (Critical Risk)" 
    assert rate == 0.0 

def test_annuity_present_value_math(): 
    pv = calculate_pv_amortization(100000, 0, 5)
    assert pv == 500000 
