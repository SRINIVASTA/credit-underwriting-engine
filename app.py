import os
import sys
import io
import csv
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- SYSTEM PATH REGISTRATION OVERRIDE ---
app_root_dir = os.path.dirname(os.path.abspath(__file__))
if app_root_dir not in sys.path:
    sys.path.insert(0, app_root_dir)

# Flat margin imports prevent mixed whitespace parsing bugs entirely
from underwriting_core import safe_calculate_metrics
from underwriting_core import map_pricing_matrix
from underwriting_core import evaluate_system_red_flags
from underwriting_core import calculate_pv_amortization
from underwriting_core import calculate_amortization_schedule
from underwriting_core import generate_sanction_memo_pdf
from underwriting_core import fetch_borrower_central_data
from underwriting_core import validate_extended_profile

# --- VIEWPORT PAGE CONFIGURATION MATCHING IMAGE ---
st.set_page_config(page_title="Credit Underwriting Terminal", page_icon="📊", layout="wide")

st.title("🏛️ Commercial Credit Underwriting Dashboard")
st.subheader("Automated Loan Evaluation Engine — Banks & NBFCs (India)")

if "active_profile" not in st.session_state:
    st.session_state.active_profile = {
        "industry": "Pharma", "cibil_score": 750, "recent_enquiries_30_days": 1,
        "net_operating_income": 2200000.0, "annual_debt_service": 1200000.0,
        "tol": 6000000.0, "tnw": 3500000.0, "current_assets": 2500000.0, "current_liabilities": 1800000.0,
        "requested_loan": 6500000.0, "collateral_value": 14000000.0, "loan_term": 7,
        "gst_turnover": 12000000.0, "bank_credits": 12200000.0, "bounces": False,
        "overdrawn_od": False, "frequent_address_changes": False, "large_cash_deposits": False, "litigation_pending": False,
        "pan_ent": True, "gst_ent": True, "biz_ent": True, "br_ent": True, "num_directors": 2, "directors_passed": 2
    }

# --- SIDEBAR INTERFACE ---
st.sidebar.markdown("### 🗂️ Intake Source Selection")
upload_mode = st.sidebar.radio("Data Sourcing Mode", ["Manual Intake / API Core Search", "Direct File Upload Package"])

if upload_mode == "Direct File Upload Package":
    st.sidebar.markdown("---")
    st.sidebar.subheader("📥 Tabular Document Intake")
    uploaded_file = st.sidebar.file_uploader("Upload Borrower Financial Data Profile", type=["csv"])
    
    if uploaded_file is not None:
        try:
            file_bytes = uploaded_file.getvalue()
            text_stream = io.StringIO(file_bytes.decode("utf-8"))
            reader = list(csv.DictReader(text_stream))
            total_rows = len(reader)
            
            if total_rows >= 1:
                st.sidebar.info(f"📋 Multi-Row Batch File Identified: Found {total_rows} Accounts.")
                selected_row_idx = st.sidebar.selectbox(
                    "Select Borrower Record to Load",
                    range(total_rows),
                    format_func=lambda x: f"Row {x+1}: {reader[x].get('industry', 'Record')} (CIBIL: {reader[x].get('cibil_score', 'N/A')})"
                )
                raw_row = reader[selected_row_idx]
                st.session_state.active_profile = validate_extended_profile(raw_row)
                st.sidebar.success(f"✅ Loaded Profile {selected_row_idx+1} Into Engine Context!")
        except Exception:
            st.sidebar.error("Error parsing tabular array layout.")

prof = st.session_state.active_profile

st.sidebar.markdown("---")
st.sidebar.markdown("### 🔑 Enterprise API Search Gateway")
borrower_id = st.sidebar.text_input("Central Borrower Registration ID (PAN / Corporate ID)", placeholder="e.g., BR-95482-X")
if st.sidebar.button("Fetch Central Database"):
    fetched = fetch_borrower_central_data(borrower_id)
    if fetched:
        st.session_state.active_profile = fetched
        st.rerun()

# --- GRID COLUMNS SETUP ---
col1, col2 = st.columns([1.1, 1.2])

with col1:
    st.header("📋 Borrower & Entity Intake")
    
    with st.expander("📝 Part 1: Corporate Registration & KYC", expanded=True):
        industry_list = ["Pharma", "FMCG", "Healthcare", "Textile", "Real Estate", "Startup"]
        default_idx = industry_list.index(prof["industry"]) if prof["industry"] in industry_list else 0
        industry = st.selectbox("Industry Classification", industry_list, index=default_idx)
        
        c1, c2 = st.columns(2)
        with c1:
            pan_ent = st.checkbox("Entity PAN Verified", value=prof["pan_ent"])
            gst_ent = st.checkbox("GST Registration Active", value=prof["gst_ent"])
        with c2:
            biz_ent = st.checkbox("Udyam/Shop Act Provided", value=prof["biz_ent"])
            br_ent = st.checkbox("Board Resolution Present", value=prof["br_ent"])
            
        c3, c4 = st.columns(2)
        with c3:
            num_directors = st.number_input("Number of Corporate Directors", min_value=1, value=prof["num_directors"])
        with c4:
            directors_passed = st.number_input("Verified Cleared Directors Passes", min_value=0, value=prof["directors_passed"])

    with st.expander("📊 Part 2: Financial Statements & Bureau Checks", expanded=True):
        cibil = st.slider("CIBIL Bureau Score", 300, 900, value=prof["cibil_score"])
        enquiries = st.number_input("Bureau Enquiries (Last 30 Days)", min_value=0, value=prof["recent_enquiries_30_days"])
        noi = st.number_input("Net Operating Income (Annual INR)", value=prof["net_operating_income"], step=50000.0)
        annual_debt_service = st.number_input("Current Annual Debt Service (INR)", value=prof["annual_debt_service"], step=50000.0)
        tol = st.number_input("Total Outside Liabilities (TOL INR)", value=prof["tol"], step=100000.0)
        tnw = st.number_input("Tangible Net Worth (TNW INR)", value=prof["tnw"], step=100000.0)
        ca = st.number_input("Current Assets (INR)", value=prof["current_assets"], step=50000.0)
        cl = st.number_input("Current Liabilities (INR)", value=prof["current_liabilities"], step=50000.0)

    with st.expander("📈 Part 3: Loan Proposal Structure", expanded=True):
        req_loan = st.number_input("Requested Term Loan Facility (INR)", value=prof["requested_loan"], step=100000.0)
        collateral = st.number_input("Appraised Collateral Market Value (INR)", value=prof["collateral_value"], step=100000.0)
        loan_term = st.slider("Loan Tenure (Years)", 1, 10, value=prof["loan_term"])
        base_mclr = st.number_input("Bank Benchmark Base Rate (MCLR %)", value=prof.get("base_mclr", 8.50), step=0.1)
        
        st.markdown("**Tax & Banking Consistency Checks**")
        gst_turnover = st.number_input("Annual Sales Declared in GST (INR)", value=prof["gst_turnover"], step=100000.0)
        bank_credits = st.number_input("Total Operational Banking Credits (INR)", value=prof["bank_credits"], step=100000.0)

        variance_pct = ((bank_credits - gst_turnover) / gst_turnover * 100) if gst_turnover > 0 else 0.0
        if abs(variance_pct) > 10.0:
            st.error(f"⚠️ Turnover Mismatch Detected: {variance_pct:+.2f}%")
        else:
            st.success(f"✅ Turnover Reconciled: {variance_pct:+.2f}%")
with col2:
    st.header("⚡ Risk Analysis & System Output")
    dscr, cr_ratio, tol_tnw, ltv = safe_calculate_metrics(noi, annual_debt_service, ca, cl, tol, tnw, req_loan, collateral)
    
    # 🤖 100% AUTOMATED TRANSACTIONS CHECKPOINTS:
    current_state = {
        "recent_enquiries_30_days": enquiries,
        "frequent_address_changes": prof.get("frequent_address_changes", False),
        "bounces": prof.get("bounces", False),
        "overdrawn_od": prof.get("overdrawn_od", False),
        "large_cash_deposits": prof.get("large_cash_deposits", False),
        "litigation_pending": prof.get("litigation_pending", False)
    }
    
    flags = evaluate_system_red_flags(current_state, variance_pct)
    if flags:
        st.error("⚠️ Automated Red Flags Detected by Engine")
        for flag in flags: st.markdown(f"- {flag}")
    else:
        st.success("✅ Machine Screening Confirmed Clear: No Operational Red Flags Detected")

    # --- SCORECARD SECTION ---
    st.markdown("### 📊 100-Point Internal Risk Scorecard")
    fin_score = 40 if dscr >= 1.50 else (32 if dscr >= 1.25 else 0)
    bureau_score = 30 if cibil >= 750 else (20 if cibil >= 650 else 0)
    leverage_score = 15 if tol_tnw <= 2.00 else 11
    asset_score = 15 if ltv <= 50.0 else 12
    score = fin_score + bureau_score + leverage_score + asset_score

    score_df = pd.DataFrame({
        "Risk Factor Module": ["Cash Flow (DSCR)", "Bureau History (CIBIL)", "Capital Structure (TOL/TNW)", "Collateral Cover (LTV)"],
        "Observed Metrics": [f"DSCR: {dscr}x", f"Score: {cibil}", f"Leverage: {tol_tnw}x", f"Ratio: {ltv}%"],
        "Points Allowed": [f"{fin_score} / 40", f"{bureau_score} / 30", f"{leverage_score} / 15", f"{asset_score} / 15"]
    })
    st.table(score_df)

    # --- LOAN SIZING SECTION ---
    st.markdown("### 💰 Smart Loan Sizing & Risk-Based Pricing")
    st.metric(label="Calculated Internal Risk Grade Score", value=f"{score} / 100 Points")
    
    final_rate, max_ltv, min_dscr, tier_name, tier_type = map_pricing_matrix(score, base_mclr)
    
    max_annual_ds = noi / min_dscr if min_dscr > 0 else noi
    cash_flow_cap = calculate_pv_amortization(max_annual_ds, final_rate, loan_term)
    asset_cap = collateral * (max_ltv / 100.0) if collateral > 0 else 0.0
    max_eligible_loan = min(cash_flow_cap, asset_cap) if collateral > 0 else cash_flow_cap
    final_sanction = min(max_eligible_loan, req_loan) if (score >= 50 and not prof.get("litigation_pending", False)) else 0.0

    m1, m2 = st.columns(2)
    with m1:
        st.metric(label="Risk-Based Pricing Applied (APR)", value=f"{round(final_rate, 2)}%")
        st.metric(label="Cash-Flow Borrowing Limit (DSCR Cap)", value=f"₹{cash_flow_cap:,.2f}")
    with m2:
        st.metric(label="Maximum Portfolio Eligible Offer", value=f"₹{max_eligible_loan:,.2f}")
        st.metric(label="Collateral Asset Capacity (LTV Cap)", value=f"₹{asset_cap:,.2f}")

    st.markdown(f"#### 📑 FINAL APPROVED SANCTION AMOUNT: **₹{final_sanction:,.2f}**")

    # --- 5 Cs MODULE ---
    st.markdown("---")
    st.markdown("### 🔍 Part 5: The 5 Cs of Credit Qualitative Module")
    c_char = st.text_area("1. Character (Integrity)", placeholder="Reputation record...")
    c_cap = st.text_area("2. Capacity (Repayment)", value=f"DSCR computed at {dscr}x.")
    c_cap_struct = st.text_area("3. Capital (Leverage)", value=f"Leverage structure sits at {tol_tnw}x.")
    c_coll = st.text_area("4. Collateral (Coverage)", value=f"Calculated LTV set at {ltv}%.")
    c_cond = st.text_area("5. Conditions (Outlook)", value=f"Sector: '{industry}'.")

    # --- SIDEBAR EXPORT PACKAGE HOOK ---
    try:
        meta_p = {"industry": industry, "kyc_cleared": pan_ent and gst_ent}
        metrics_p = {"dscr": dscr, "cr_ratio": cr_ratio, "tol_tnw": tol_tnw, "ltv": ltv}
        scoring_p = {"score": score, "flags": flags}
        results_p = {"req_loan": req_loan, "cash_flow_cap": cash_flow_cap, "asset_cap": asset_cap, "final_sanction": final_sanction, "final_rate": final_rate, "tier_name": tier_name}
        qual_p = {"character": c_char, "capacity": c_cap, "capital": c_cap_struct, "collateral": c_coll, "conditions": c_cond}
        
        pdf_bytes = generate_sanction_memo_pdf(meta_p, metrics_p, scoring_p, results_p, qualitative_5cs=qual_p)
        st.sidebar.download_button(label="📥 Download Official Sanction PDF", data=pdf_bytes, file_name="Sanction_Memo_Draft.pdf", mime="application/pdf")
    except Exception:
        pass

# --- WIDE FORM PORTFOLIO PLOTS (OUTSIDE OF COLUMNS FOR FULL WIDTH) ---
st.markdown("---")
st.markdown("### 📊 Interactive Portfolio Plots (Plotly Express Engine)")

categories = ["Requested Facility", "Cash Flow Ceiling", "Collateral Ceiling", "Final Approved Sanction"]
amounts = [req_loan, cash_flow_cap, asset_cap, final_sanction]

fig_bars = go.Figure(go.Bar(x=amounts, y=categories, orientation='h', marker=dict(color=['#636EFA', '#EF553B', '#00CC96', '#AB63FA'])))
fig_bars.update_layout(title="Loan Proposal vs Underwriting Exposure Ceilings", xaxis_title="Amount (INR)", yaxis_title="Evaluation Segment", height=320, margin=dict(l=20, r=20, t=40, b=20))
st.plotly_chart(fig_bars, use_container_width=True)

years, balances, cumulative_interest = calculate_amortization_schedule(final_sanction, final_rate, loan_term)
fig_line = go.Figure()
fig_line.add_trace(go.Scatter(x=years, y=balances, mode='lines+markers', name='Principal Outstanding', line=dict(color='#EF553B', width=3)))
fig_line.add_trace(go.Scatter(x=years, y=cumulative_interest, mode='lines+markers', name='Cumulative Interest Paid', line=dict(color='#636EFA', width=3, dash='dash')))
fig_line.update_layout(title=f"{loan_term}-Year Runway Loan Amortization Track", xaxis_title="Loan Timeline Milestone", yaxis_title="Capital Balance (INR)", height=350, margin=dict(l=20, r=20, t=40, b=20))
st.plotly_chart(fig_line, use_container_width=True)
