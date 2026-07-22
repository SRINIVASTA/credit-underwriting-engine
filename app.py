import streamlit as st

# Force Streamlit to completely hide the header bar, deployment buttons, and GitHub icons
st.markdown("""
    <style>
    header[data-testid="stHeader"] {
        visibility: hidden !important;
        display: none !important;
    }
    div[data-testid="stToolbar"] {
        visibility: hidden !important;
        display: none !important;
    }
    footer {
        visibility: hidden !important;
    }
    </style>
    """, unsafe_allow_html=True)

import streamlit as st 
import pandas as pd 
import plotly.graph_objects as go 
import io 
import csv 
import json 
from underwriting_core import ( 
    fetch_borrower_central_data, 
    parse_uploaded_file_stream, 
    safe_calculate_metrics, 
    calculate_pv_amortization, 
    map_pricing_matrix, 
    calculate_amortization_schedule,
    generate_sanction_memo_pdf
) 

# --- STREAMLIT UI VIEWPORTS CONFIGURATION --- 
st.set_page_config(page_title="Credit Underwriting Terminal", page_icon="📊", layout="wide") 
st.title("🏦 Commercial Credit Underwriting Dashboard") 
st.subheader("Automated Loan Evaluation Engine — Banks & NBFCs (India)") 

# --- SIDEBAR INTEGRATED CONTROL DATA PIPELINES --- 
st.sidebar.header("📁 Intake Source Selection") 
upload_mode = st.sidebar.radio("Data Sourcing Mode", ["Manual Intake / API Core Search", "Direct File Upload Package"]) 

active_profile = None 
selected_row_idx = 0  
dynamic_industry_list = ["Pharma", "FMCG", "Healthcare", "Education", "Hospitals", "Trading", "Restaurant", "Textile", "Real Estate", "Startup"]

if upload_mode == "Direct File Upload Package": 
    st.sidebar.markdown("---") 
    st.sidebar.subheader("📄 Financial Statement Upload") 
    uploaded_file = st.sidebar.file_uploader("Upload Borrower Financial Data Profile", type=["json", "csv"]) 
 
    if uploaded_file is not None: 
        try: 
            file_bytes = uploaded_file.getvalue() 
 
            if uploaded_file.name.endswith('.csv'): 
                text_stream = io.StringIO(file_bytes.decode("utf-8")) 
                raw_reader = list(csv.DictReader(text_stream)) 
                
                reader = []
                unique_industries = set()
                for row in raw_reader:
                    cleaned_row = {str(k).strip().lower(): str(v).strip() for k, v in row.items() if k is not None}
                    reader.append(cleaned_row)
                    if cleaned_row.get("industry"):
                        unique_industries.add(cleaned_row.get("industry"))
                
                if unique_industries:
                    dynamic_industry_list = sorted(list(unique_industries))
                
                total_rows = len(reader) 
 
                if total_rows > 0: 
                    st.sidebar.info(f"📊 Multi-Row Batch File Identified: Found {total_rows} Accounts.") 
                    selected_row_idx = st.sidebar.selectbox( 
                        "Select Borrower Record to Load", 
                        range(total_rows), 
                        format_func=lambda x: f"Row {x+1}: {reader[x].get('industry', 'Record')} (CIBIL: {reader[x].get('cibil_score', 'N/A')})" 
                    ) 
 
                    active_row = reader[selected_row_idx] 
 
                    def str_to_bool(v): 
                        return str(v).strip().lower() in ("true", "1", "yes", "t") 
 
                    active_profile = { 
                        "industry": str(active_row.get("industry", "Pharma")), 
                        "cibil_score": int(float(active_row.get("cibil_score", 700))), 
                        "recent_enquiries_30_days": int(float(active_row.get("recent_enquiries_30_days", active_row.get("recent_enq", 0)))), 
                        "net_operating_income": float(active_row.get("net_operating_income", active_row.get("net_operat", 0.0))), 
                        "annual_debt_service": float(active_row.get("annual_debt_service", active_row.get("annual_del", 1.0))), 
                        "tol": float(active_row.get("tol", 0.0)), 
                        "tnw": float(active_row.get("tnw", 1.0)), 
                        "current_assets": float(active_row.get("current_assets", active_row.get("current_as", 0.0))), 
                        "current_liabilities": float(active_row.get("current_liabilities", active_row.get("current_lia", 1.0))), 
                        "requested_loan": float(active_row.get("requested_loan", active_row.get("requested", 0.0))), 
                        "collateral_value": float(active_row.get("collateral_value", active_row.get("collateral_", 0.0))), 
                        "loan_term": int(float(active_row.get("loan_term", 5))), 
                        "gst_turnover": float(active_row.get("gst_turnover", active_row.get("gst_turnov", 0.0))), 
                        "bank_credits": float(active_row.get("bank_credits", active_row.get("bank_cred", 0.0))), 
                        "bounces": str_to_bool(active_row.get("bounces", False)), 
                        "pan_ent": str_to_bool(active_row.get("pan_ent", False)), 
                        "gst_ent": str_to_bool(active_row.get("gst_ent", False)), 
                        "biz_ent": str_to_bool(active_row.get("biz_ent", False)), 
                        "br_ent": str_to_bool(active_row.get("br_ent", False)), 
                        "num_directors": int(float(active_row.get("num_directors", active_row.get("num_direc", 1)))), 
                        "directors_passed": int(float(active_row.get("directors_passed", active_row.get("directors_p", 0)))) 
                    } 
                else: 
                    uploaded_file.seek(0) 
                    active_profile = parse_uploaded_file_stream(uploaded_file) 
            else: 
                uploaded_file.seek(0) 
                active_profile = parse_uploaded_file_stream(uploaded_file) 

            if active_profile: 
                st.sidebar.success("Loaded Profile Successfully!") 
        except Exception as e: 
            st.sidebar.error(f"Error processing batch layout: {str(e)}") 
else: 
    st.sidebar.markdown("---") 
    st.sidebar.subheader("🔑 Enterprise API Search Gateway") 
    borrower_id_input = st.sidebar.text_input("Central Borrower Registration ID (PAN / Corporate ID)", placeholder="e.g., BR-99482-X") 
    active_profile = fetch_borrower_central_data(borrower_id_input) 
    if active_profile: 
        st.sidebar.success(f"Linked File Account via API: {borrower_id_input}") 

if not active_profile:
    active_profile = {"industry": "Pharma", "cibil_score": 750, "recent_enquiries_30_days": 1, "net_operating_income": 2200000.0, "annual_debt_service": 1200000.0, "tol": 6000000.0, "tnw": 3500000.0, "current_assets": 2500000.0, "current_liabilities": 1800000.0, "requested_loan": 6500000.0, "collateral_value": 14000000.0, "loan_term": 7, "gst_turnover": 12000000.0, "bank_credits": 12200000.0, "bounces": False, "pan_ent": True, "gst_ent": True, "biz_ent": True, "br_ent": True, "num_directors": 2, "directors_passed": 2}
# --- LAYOUT VIEWPORTS SETUP ---
col1, col2 = st.columns([1, 1.2]) 

with col1: 
    st.header("📋 Borrower & Entity Intake") 
    
    # CHEAT SHEET INTEGRATION: The 5 Cs of Credit Qualitative Scoring Matrix
    with st.expander("🛡️ Part 1.5: The 5 Cs of Credit Evaluation", expanded=True):
        st.markdown("**Qualitative Assessment Framework**")
        character_grade = st.slider("Management Character & Track Record", 1, 10, value=7, key=f"char_idx_{selected_row_idx}")
        conditions_grade = st.slider("Business Conditions & Industry Outlook", 1, 10, value=7, key=f"cond_idx_{selected_row_idx}")
        
    with st.expander("🔑 Part 1: Corporate Registration & KYC", expanded=True): 
        current_ind = active_profile["industry"]
        if current_ind not in dynamic_industry_list:
            dynamic_industry_list.append(current_ind)
            dynamic_industry_list = sorted(dynamic_industry_list)
            
        default_ind_idx = dynamic_industry_list.index(current_ind)
        industry = st.selectbox("Industry Classification", dynamic_industry_list, index=default_ind_idx, key=f"ind_sel_idx_{selected_row_idx}") 
        
        c1, c2 = st.columns(2) 
        with c1: 
            pan_ent = st.checkbox("Entity PAN Verified", value=active_profile["pan_ent"], key=f"pan_chk_idx_{selected_row_idx}") 
            gst_ent = st.checkbox("GST Registration Active", value=active_profile["gst_ent"], key=f"gst_chk_idx_{selected_row_idx}") 
        with c2: 
            biz_ent = st.checkbox("Udyam/Shop Act Provided", value=active_profile["biz_ent"], key=f"biz_chk_idx_{selected_row_idx}") 
            br_ent = st.checkbox("Board Resolution Present", value=active_profile["br_ent"], key=f"br_chk_idx_{selected_row_idx}") 
 
        num_directors = st.number_input("Number of Corporate Directors", min_value=1, max_value=10, value=int(active_profile["num_directors"]), key=f"num_dir_idx_{selected_row_idx}") 
        p_pass_dir = int(active_profile["directors_passed"]) 
        safe_passed_val = min(p_pass_dir, int(num_directors)) 
        directors_passed = st.number_input("Verified Cleared Directors (PAN + Aadhaar Passes)", min_value=0, max_value=int(num_directors), value=safe_passed_val, key=f"pass_dir_idx_{selected_row_idx}") 
        
    with st.expander("📊 Part 2: Financial Statements & Bureau Checks", expanded=True): 
        cibil = st.slider("CIBIL Bureau Score", 300, 900, value=int(active_profile["cibil_score"]), key=f"cibil_slider_idx_{selected_row_idx}") 
        enquiries = st.number_input("Bureau Enquiries (Last 30 Days)", min_value=0, max_value=15, value=int(active_profile["recent_enquiries_30_days"]), key=f"enq_num_idx_{selected_row_idx}") 
 
        noi = st.number_input("Net Operating Income (Annual INR)", value=float(active_profile["net_operating_income"]), step=50000.0, key=f"noi_num_idx_{selected_row_idx}") 
        annual_debt_service = st.number_input("Current Annual Debt Service (INR)", min_value=0.0, value=float(active_profile["annual_debt_service"]), step=50000.0, key=f"ads_num_idx_{selected_row_idx}") 
        tol = st.number_input("Total Outside Liabilities (TOL INR)", min_value=0.0, value=float(active_profile["tol"]), step=100000.0, key=f"tol_num_idx_{selected_row_idx}") 
        tnw = st.number_input("Tangible Net Worth (TNW INR)", value=float(active_profile["tnw"]), step=100000.0, key=f"tnw_num_idx_{selected_row_idx}") 
        ca = st.number_input("Current Assets (INR)", min_value=0.0, value=float(active_profile["current_assets"]), step=50000.0, key=f"ca_num_idx_{selected_row_idx}") 

    with st.expander("💼 Part 3: Loan Proposal Structure", expanded=True): 
        cl = st.number_input("Current Liabilities (INR)", min_value=0.0, value=float(active_profile["current_liabilities"]), step=50000.0, key=f"cl_num_idx_{selected_row_idx}") 
        req_loan = st.number_input("Requested Term Loan Facility (INR)", min_value=0.0, value=float(active_profile["requested_loan"]), step=100000.0, key=f"req_num_idx_{selected_row_idx}") 
        collateral = st.number_input("Appraised Collateral Market Value (INR)", min_value=0.0, value=float(active_profile["collateral_value"]), step=100000.0, key=f"col_num_idx_{selected_row_idx}") 
        loan_term = st.slider("Loan Tenure (Years)", 1, 10, value=int(active_profile["loan_term"]), key=f"term_slide_idx_{selected_row_idx}") 
        base_mclr = st.number_input("Bank Benchmark Base Rate (MCLR %)", min_value=0.0, max_value=20.0, value=8.50, step=0.1, key=f"mclr_num_idx_{selected_row_idx}") 
 
        st.markdown("**Tax & Banking Consistency Checks**") 
        gst_turnover = st.number_input("Annual Sales Declared in GST (INR)", min_value=0.0, value=float(active_profile["gst_turnover"]), step=100000.0, key=f"gst_turn_idx_{selected_row_idx}") 
        bank_credits = st.number_input("Total Operational Banking Credits (INR)", min_value=0.0, value=float(active_profile["bank_credits"]), step=100000.0, key=f"bank_cred_idx_{selected_row_idx}") 
        bounces = st.checkbox("Any Cheque / EMI Bounces in Last 12 Months?", value=active_profile["bounces"], key=f"bounce_chk_idx_{selected_row_idx}") 
        
        # CHEAT SHEET INTEGRATION: Behavioral Red Flags Panel
        st.markdown("**🚨 Behavioral Red Flags Panel (Vetting Audit)**")
        litigation_flag = st.checkbox("Any Active Litigation on Property / Promoters?", value=False, key=f"lit_chk_{selected_row_idx}")
        circular_flag = st.checkbox("Suspected Circular Transaction / Loop Banking Entries?", value=False, key=f"circ_chk_{selected_row_idx}")
 
        if gst_turnover > 0: 
            variance_amt = bank_credits - gst_turnover 
            variance_pct = (variance_amt / gst_turnover) * 100 
            if abs(variance_pct) > 10.0: 
                st.error(f"⚠️ Turnover Mismatch Detected: {variance_pct:+.2f}%") 
            else: 
                st.success(f"✅ Turnover Reconciled: {variance_pct:+.2f}%") 
        else: 
            variance_pct = 0.0 
# --- COL 2 PIPELINE ANALYSIS RENDER ENGINE --- 
with col2: 
    st.header("📈 Risk Analysis & System Output") 
    if collateral == 0: st.error("🚨 CRITICAL METRIC ALERT: Collateral asset valued at zero.") 
    if tnw <= 0: st.error("⚠️ SYSTEM BALANCE NOTICE: Tangible Net Worth is zero or negative.") 
    if noi <= 0: st.error("🛑 UNDERWRITING HALT: Operating income is negative or zero.") 
    
    # CORRECTED PACKAGING: Passes qualitative grades from sliders and unpacks all 6 structural parameters cleanly
    dscr, cr_ratio, tol_tnw, ltv, foir, qualitative_modifier = safe_calculate_metrics(
        noi, annual_debt_service, ca, cl, tol, tnw, req_loan, collateral, character_grade, conditions_grade
    ) 
    
    gst_penalty = 10 if (gst_turnover > 0 and abs(variance_pct) > 10.0) else 0
    enq_penalty = 5 if enquiries > 3 else 0
    
    # Dynamic point modifiers driven completely by your sheet's risk frameworks
    qualitative_penalty = abs(qualitative_modifier)
    fraud_penalty = 20 if (litigation_flag or circular_flag) else 0

    fin_score = max(0, (40 if dscr >= 1.50 else (32 if dscr >= 1.25 else (20 if dscr >= 1.10 else 0))) - gst_penalty) 
    bureau_score = max(0, (30 if cibil >= 750 else (24 if cibil >= 700 else (15 if cibil >= 650 else 0))) - enq_penalty) 
    leverage_score = 15 if tol_tnw <= 2.00 and tnw > 0 else (11 if tol_tnw <= 3.00 and tnw > 0 else (6 if tol_tnw <= 4.50 and tnw > 0 else 0)) 
    asset_score = 15 if ltv <= 50.0 and collateral > 0 else (12 if ltv <= 60.0 and collateral > 0 else (7 if ltv <= 75.0 and collateral > 0 else 0)) 
    
    score = max(0, fin_score + bureau_score + leverage_score + asset_score - qualitative_penalty - fraud_penalty) 
    
    # ... rest of your Block 3 code remains completely identical
    
    # Maps pricing and dynamically loads the +1.50% yield premium penalty for Real Estate / Construction / Startups
    final_rate, max_ltv, min_dscr, tier_name, tier_type = map_pricing_matrix(score, base_mclr, industry) 
    kyc_cleared = pan_ent and gst_ent and biz_ent and br_ent and (directors_passed == num_directors) 
    
    flags = [] 
    if enquiries > 3: flags.append("Multiple credit enquiries within a 30-day window.") 
    if bounces: flags.append("Operational account notes active Cheque/EMI bouncing history.") 
    if gst_turnover > 0 and abs(variance_pct) > 10.0: 
        flags.append(f"Reconciliation Mismatch: Bank Credit vs GST filing variance ({variance_pct:+.2f}%) exceeds baseline parameters.") 
    if foir > 50.0:
        flags.append(f"High Leverage Threat: Fixed Obligation ratio ({foir}%) crosses target thresholds.")
    if litigation_flag:
        flags.append("CRITICAL FRAUD HOLD: Active promoter or real-estate property litigation notes discovered.")
    if circular_flag:
        flags.append("AUDIT WARNING: Shell ledger routing or circular circular-banking indicators triggered.")
        
    if flags: 
        st.warning("⚠️ Critical Warnings Triggered") 
        for flag in flags: st.markdown(f"- {flag}") 
    else: 
        st.success("✅ Behavioral Records Clear: No Operational Red Flags Detected") 

    st.subheader("📊 100-Point Internal Risk Scorecard") 
    score_df = pd.DataFrame({ 
        "Risk Factor Module": ["Cash Flow (DSCR)", "Bureau History (CIBIL)", "Capital Structure (TOL/TNW)", "Collateral Cover (LTV)"], 
        "Observed Metrics": [f"DSCR: {dscr}x (FOIR: {foir}%)", f"Score: {cibil}", f"Leverage: {tol_tnw}x", f"Ratio: {ltv}%"], 
        "Points Allowed": [f"{fin_score} / 40", f"{bureau_score} / 30", f"{leverage_score} / 15", f"{asset_score} / 15"] 
    }) 
    st.table(score_df) 
    
    st.subheader("💡 Smart Loan Sizing & Risk-Based Pricing") 
    # CHEAT SHEET SAFEGUARD RULES GATE: Rejects if points total < 50, operating cash flow is zero, or bureau CIBIL drops < 650
    if score < 50 or noi <= 0 or cibil < 650: 
        st.error(f"❌ APPLICATION REJECTED OUTRIGHT — Total Scorecard Grade: {score}/100 (CIBIL / Scorecard Rule Safety Decline Applied)") 
    else: 
        max_annual_ds = noi / min_dscr 
        cash_flow_cap = calculate_pv_amortization(max_annual_ds, final_rate, loan_term) 
        asset_cap = collateral * (max_ltv / 100.0) if collateral > 0 else 0.0 
        max_eligible_loan = min(cash_flow_cap, asset_cap) if collateral > 0 else cash_flow_cap 
        final_sanction = min(max_eligible_loan, req_loan) 
        
        st.success(f"✅ UNDERWRITING APPLICATION APPROVED — Total Scorecard Grade: {score}/100")

        if not kyc_cleared:
            st.warning("⚠️ Operational Advisory Notice: Mismatches or gaps in entity filing paperwork / director verification count are currently active.")

        st.metric(label="Calculated Internal Risk Grade Score", value=f"{score} / 100 Points") 
        st.info(f"📋 Risk Profile Tier Assignment: {tier_name}")
        
        m1, m2 = st.columns(2) 
        with m1: 
            st.metric(label="Risk-Based Pricing Applied (APR)", value=f"{round(final_rate, 2)}%") 
            st.metric(label="Cash-Flow Borrowing Limit (DSCR Cap)", value=f"₹{cash_flow_cap:,.2f}") 
        with m2: 
            st.metric(label="Maximum Portfolio Eligible Offer", value=f"₹{max_eligible_loan:,.2f}") 
            st.metric(label="Collateral Asset Capacity (LTV Cap)", value=f"₹{asset_cap:,.2f}") 
            
        st.markdown("---") 
        st.metric(label="📄 FINAL APPROVED SANCTION AMOUNT", value=f"₹{final_sanction:,.2f}") 
        
        # --- EXECUTING THE COMPILATION DOWNLOAD BLOCK --- 
        st.sidebar.markdown("---") 
        st.sidebar.subheader("📥 Export Sanction Package") 
        meta_pkg = {"industry": industry, "kyc_cleared": kyc_cleared} 
        metrics_pkg = {"dscr": dscr, "cr_ratio": cr_ratio, "tol_tnw": tol_tnw, "ltv": ltv} 
        scoring_pkg = {"score": score, "flags": flags} 
        results_pkg = {"req_loan": req_loan, "cash_flow_cap": cash_flow_cap, "asset_cap": asset_cap, "final_sanction": final_sanction, "final_rate": final_rate, "tier_name": tier_name} 
 
        try: 
            pdf_bytes = generate_sanction_memo_pdf(meta_pkg, metrics_pkg, scoring_pkg, results_pkg) 
            st.sidebar.download_button(label="📄 Download Official Sanction PDF", data=pdf_bytes, file_name="Sanction_Memo_Draft.pdf", mime="application/pdf", key=f"pdf_btn_idx_{selected_row_idx}") 
        except Exception: 
            st.sidebar.error("Could not pre-compile download module bundle.") 
            
        # --- PLOTLY DATA VISUALIZATION ENGINE --- 
        st.markdown("---") 
        st.subheader("📊 Interactive Portfolio Plots (Plotly Express Engine)") 
        categories = ["Requested Facility", "Cash Flow Ceiling", "Collateral Ceiling", "Final Approved Sanction"] 
        amounts = [req_loan, cash_flow_cap, asset_cap, final_sanction] 
 
        fig_bars = go.Figure(go.Bar(x=amounts, y=categories, orientation='h', marker=dict(color=['#636EFA', '#EF553B', '#00CC96', '#AB63FA']))) 
        fig_bars.update_layout(title="Loan Proposal vs Underwriting Exposure Ceilings", xaxis_title="Amount (INR)", yaxis_title="Evaluation Segment", height=350, margin=dict(l=20, r=20, t=40, b=20)) 
        st.plotly_chart(fig_bars, use_container_width=True, key=f"bar_chart_idx_{selected_row_idx}") 
        
        years, balances, cumulative_interest = calculate_amortization_schedule(final_sanction, final_rate, loan_term) 
        fig_line = go.Figure() 
        fig_line.add_trace(go.Scatter(x=years, y=balances, mode='lines+markers', name='Principal Outstanding', line=dict(color='#EF553B', width=3))) 
        fig_line.add_trace(go.Scatter(x=years, y=cumulative_interest, mode='lines+markers', name='Cumulative Interest Paid', line=dict(color='#636EFA', width=3, dash='dash'))) 
        fig_line.update_layout(title=f"{loan_term}-Year Runway Loan Amortization Track", xaxis_title="Loan Timeline Milestone", yaxis_title="Capital Balance (INR)", legend=dict(yanchor="top", y=0.99, xanchor="right", x=0.99), height=380, margin=dict(l=20, r=20, t=40, b=20)) 
        st.plotly_chart(fig_line, use_container_width=True, key=f"line_chart_idx_{selected_row_idx}") 
