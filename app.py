# app.py
import pandas as pd
import streamlit as st
import io

# Securely import functions from our separate underwriting_core.py file
from underwriting_core import (
    calculate_score,
    evaluate_risk,
    process_financials
)

# Initialize Streamlit application container layouts
st.set_page_config(
    page_title="Credit Underwriting Engine",
    page_icon="📊",
    layout="wide"
)

# Re-initialize internal profile mock database for lookup selections
@st.cache_data
def get_mock_database():
    columns = [
        "Industry", "cibil_score", "recent_enq", "net_operat", "annual_del", "tol", 
        "tnw", "current_as", "current_lia", "requested", "collateral_", "loan_term", 
        "gst_turnov", "bank_cred", "bounces", "pan_ent", "gst_ent", "biz_ent", 
        "br_ent", "num_direc", "directors_passed"
    ]
    data = [
        ["Pharma", 780, 1, 4200000, 1500000, 8000000, 7500000, 5500000, 2000000, 12000000, 25000000, 5, 24000000, 24500000, False, True, True, True, True, 3, 3],
        ["FMCG", 745, 2, 3500000, 1200000, 6500000, 4800000, 4100000, 1900000, 9000000, 15000000, 4, 18500000, 18100000, False, True, True, True, True, 2, 2],
        ["Healthcare", 775, 1, 2500000, 1100000, 5500000, 4000000, 3200000, 1500000, 7500000, 16000000, 7, 15000000, 15150000, False, True, True, True, True, 2, 2],
        ["Education", 760, 0, 1800000, 600000, 3000000, 4200000, 2200000, 900000, 5500000, 11000000, 7, 10000000, 10200000, False, True, True, True, True, 2, 2],
        ["Hospitals", 790, 1, 6800000, 2400000, 13000000, 11000000, 8500000, 3500000, 20000000, 45000000, 8, 42000000, 42500000, False, True, True, True, True, 4, 4],
        ["Trading/Distributors", 710, 4, 5000000, 2200000, 11000000, 5000000, 6500000, 4000000, 14000000, 18000000, 3, 32000000, 31500000, True, True, True, True, False, 3, 2],
        ["Restaurant/Hospitality", 685, 3, 1600000, 850000, 3800000, 2200000, 1800000, 1100000, 4000000, 6000000, 4, 9500000, 9200000, False, True, True, True, True, 2, 1],
        ["Textile/Garments", 725, 2, 2900000, 1300000, 6000000, 3900000, 3400000, 1700000, 8000000, 12000000, 5, 16000000, 16200000, False, True, True, True, True, 2, 2],
        ["Real Estate/Const.", 695, 5, 8500000, 3800000, 19000000, 12000000, 14000000, 8200000, 25000000, 40000000, 5, 45000000, 43800000, True, True, False, True, True, 3, 2],
        ["Startup", 730, 3, 1200000, 450000, 2000000, 3000000, 1500000, 700000, 6000000, 4000000, 3, 5000000, 5500000, False, True, True, True, True, 2, 2]
    ]
    return pd.DataFrame(data, columns=columns)

db_df = get_mock_database()

st.title("📊 Enterprise Credit Underwriting Engine")
st.markdown("Automated risk verification portal and financial appraisal module.")

# Selection Sidebar Processing Navigation Elements
app_mode = st.sidebar.radio("Select Processing Mode", ["Upload Mode (CSV)", "Database Profile Lookup"])

active_profile = None
unique_session_key = "default_session"

# Handle Mode Parsing Infrastructure 
if app_mode == "Upload Mode (CSV)":
    st.subheader("📁 Upload Customer Credit Sheet")
    uploaded_file = st.file_uploader("Drop client risk parameters (.csv format)", type=["csv"])
    
    if uploaded_file is not None:
        try:
            uploaded_df = pd.read_csv(uploaded_file)
            if not uploaded_df.empty:
                # Target primary profile row matrix from uploaded document
                active_profile = uploaded_df.iloc[0].to_dict()
                unique_session_key = f"uploaded_{uploaded_file.name}_{len(uploaded_df)}"
                st.success(f"Successfully processed profile: **{active_profile.get('Industry', 'Unknown')}**")
        except Exception as e:
            st.error(f"Error reading dataset parsing columns: {str(e)}")
else:
    st.subheader("🔍 Select Internal Database Profile")
    selected_ind = st.selectbox("Select Target Enterprise Client", db_df["Industry"].tolist())
    matched_row = db_df[db_df["Industry"] == selected_ind]
    if not matched_row.empty:
        active_profile = matched_row.iloc[0].to_dict()
        unique_session_key = f"db_{selected_ind}"

st.divider()
st.subheader("📋 Active Risk Assessment Profile")

if active_profile is not None:
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.text_input("Target Corporate Segment / Industry", value=str(active_profile.get("Industry", "General")), disabled=True)
        cibil = st.number_input("CIBIL Bureau Score", min_value=300, max_value=900, value=int(active_profile.get("cibil_score", 700)))
        recent_enq = st.number_input("Recent Bureau Enquiries (Last 30 Days)", min_value=0, value=int(active_profile.get("recent_enq", 0)))
        
    with col2:
        # Step A: Safely structure clean scalar variables for maximum evaluation ceilings
        try:
            num_directors = int(active_profile.get("num_direc", 1))
        except (ValueError, TypeError):
            num_directors = 1
        max_directors = max(1, num_directors)

        # Step B: Secure historical value validation data
        if "directors_passed" in active_profile:
            try:
                profile_passed = int(active_profile["directors_passed"])
            except (ValueError, TypeError):
                profile_passed = max_directors
        else:
            profile_passed = max_directors

        # Step C: MATH BOUNDARY ENFORCEMENT ENGINE
        safe_value = min(profile_passed, max_directors)
        safe_value = max(0, safe_value)

        # Input Widgets featuring dynamic validation caches
        num_directors_input = st.number_input(
            "Total Onboarded Directors", 
            min_value=1, 
            value=max_directors,
            key=f"total_dir_{unique_session_key}"
        )
        
        # --- PREVENT StreamlitValueAboveMaxError ENGINE CRASH ---
        directors_passed = st.number_input(
            "Verified Cleared Directors (PAN + Aadhaar Passes)", 
            min_value=0, 
            max_value=int(num_directors_input), 
            value=min(safe_value, int(num_directors_input)),
            key=f"dir_passed_{unique_session_key}" 
        )

    with col3:
        requested_loan = st.number_input("Requested Credit Capacity", min_value=0, value=int(active_profile.get("requested", 100000)))
        collateral_val = st.number_input("Valued Collateral Assets", min_value=0, value=int(active_profile.get("collateral_", 0)))

    # Metrics Display Interface Module
    st.markdown("### 🔑 Financial Liquidity & Solvency Ratios")
    f_col1, f_col2, f_col3 = st.columns(3)
    with f_col1:
        st.metric("Net Operational Revenue", f"₹{int(active_profile.get('net_operat', 0)):,}")
        st.metric("Total Outstanding Liabilities (TOL)", f"₹{int(active_profile.get('tol', 0)):,}")
    with f_col2:
        st.metric("Annual Deliverable Flow", f"₹{int(active_profile.get('annual_del', 0)):,}")
        st.metric("Total Net Worth (TNW)", f"₹{int(active_profile.get('tnw', 0)):,}")
    with f_col3:
        st.metric("Current Assets", f"₹{int(active_profile.get('current_as', 0)):,}")
        st.metric("Current Liabilities", f"₹{int(active_profile.get('current_lia', 0)):,}")

    # Process metrics using backend functions imported from underwriting_core
    st.markdown("### ⚡ Core Underwriting Engine Output")
    try:
        calculated_score_val = calculate_score(active_profile)
        risk_evaluation_status = evaluate_risk(calculated_score_val)
        current_ratio = process_financials(active_profile)
        
        st.success(f"📋 **Engine Core Scoring:** {calculated_score_val} | **Risk Status:** {risk_evaluation_status} | **Current Asset Ratio:** {current_ratio}")
    except Exception as calculation_error:
        st.warning(f"⚠️ Internal script scoring fallback active. Core module error: {str(calculation_error)}")
else:
    st.info("💡 Please upload a customer CSV file or choose an operational profile from the database option in the sidebar to activate engine components.")
