import pandas as pd
import streamlit as st
import io

# Set page configuration
st.set_page_config(
    page_title="Credit Underwriting Engine",
    page_icon="📊",
    layout="wide"
)

# ---------------------------------------------------------
# 1. LOAD REFERENCE / ENGINE MOCK DATASETS
# ---------------------------------------------------------
# This replicates the 10 reference profiles we built previously
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

# ---------------------------------------------------------
# 2. APPLICATION HEADER & CONTROLS
# ---------------------------------------------------------
st.title("📊 Enterprise Credit Underwriting Engine")
st.markdown("Automated risk verification portal and financial appraisal module.")

# Mode selection sidebar toggle
app_mode = st.sidebar.radio("Select Processing Mode", ["Upload Mode (CSV)", "Database Profile Lookup"])

active_profile = None
unique_session_key = "default_session"

# ---------------------------------------------------------
# 3. MODE LOGIC: HANDLE UPLOADS OR PROFILES
# ---------------------------------------------------------
if app_mode == "Upload Mode (CSV)":
    st.subheader("📁 Upload Customer Credit Sheet")
    uploaded_file = st.file_uploader("Drop client risk parameters (.csv format)", type=["csv"])
    
    if uploaded_file is not None:
        try:
            uploaded_df = pd.read_csv(uploaded_file)
            if not uploaded_df.empty:
                # Map the first row of data as our active running underwriting profile
                active_profile = uploaded_df.iloc[0].to_dict()
                # Create a specific token unique to this file instance to destroy stuck widget states
                unique_session_key = f"uploaded_{uploaded_file.name}_{len(uploaded_df)}"
                st.success(f"Successfully processed profile: **{active_profile.get('Industry', 'Unknown')}**")
        except Exception as e:
            st.error(f"Error reading dataset parsing columns: {str(e)}")

else:
    st.subheader("🔍 Select Internal Database Profile")
    selected_ind = st.selectbox("Select Target Enterprise Client", db_df["Industry"].tolist())
    
    # Filter row to construct profile dictionary
    matched_row = db_df[db_df["Industry"] == selected_ind]
    if not matched_row.empty:
        active_profile = matched_row.iloc[0].to_dict()
        unique_session_key = f"db_{selected_ind}"

# ---------------------------------------------------------
# 4. APP UNDERWRITING RUNTIME (LINE 55 BUG FIX INCLUDED)
# ---------------------------------------------------------
st.divider()
st.subheader("📋 Active Risk Assessment Profile")

if active_profile is not None:
    # Setup safe columnar structural layouts
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.text_input("Target Corporate Segment / Industry", value=str(active_profile.get("Industry", "General")), disabled=True)
        cibil = st.number_input("CIBIL Bureau Score", min_value=300, max_value=900, value=int(active_profile.get("cibil_score", 700)))
        recent_enq = st.number_input("Recent Bureau Enquiries (Last 30 Days)", min_value=0, value=int(active_profile.get("recent_enq", 0)))
        
    with col2:
        # Step A: Parse absolute maximum boundary to prevent validation limits crash
        try:
            num_directors = int(active_profile.get("num_direc", 1))
        except (ValueError, TypeError):
            num_directors = 1
            
        max_directors = max(1, num_directors) # Guarantees minimum ceiling is at least 1

        # Step B: Securely look up profile history or use default 
        if "directors_passed" in active_profile:
            try:
                profile_passed = int(active_profile["directors_passed"])
            except (ValueError, TypeError):
                profile_passed = max_directors
        else:
            profile_passed = max_directors

        # Step C: MATH CONSTRAINT BOUNDING ENGINE (Guarantees value is NEVER > max_value)
        safe_value = min(profile_passed, max_directors)
        safe_value = max(0, safe_value) # Ensures it remains >= min_value=0

        # Primary Input Configuration Widgets
        num_directors_input = st.number_input(
            "Total Onboarded Directors", 
            min_value=1, 
            value=max_directors,
            key=f"total_dir_{unique_session_key}"
        )
        
        # --- FIXED LINE 55 CRASH FIX ---
        directors_passed = st.number_input(
            "Verified Cleared Directors (PAN + Aadhaar Passes)", 
            min_value=0, 
            max_value=int(num_directors_input), 
            value=min(safe_value, int(num_directors_input)),
            key=f"dir_passed_{unique_session_key}" # Dynamic dynamic layout cache eviction key
        )
        # -------------------------------

    with col3:
        requested_loan = st.number_input("Requested Credit Capacity", min_value=0, value=int(active_profile.get("requested", 100000)))
        collateral_val = st.number_input("Valued Collateral Assets", min_value=0, value=int(active_profile.get("collateral_", 0)))

    # Financial Exposure Review Sections 
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

    # Process and evaluate simple loan viability checks
    st.markdown("### ⚡ Automate Underwriting Evaluation Status")
    
    # Calculate simple Coverage LTV
    ltv = (requested_loan / collateral_val) * 100 if collateral_val > 0 else 100
    
    if cibil >= 750 and directors_passed == num_directors_input and ltv <= 75:
        st.success(f"✅ **RECOMMENDED FOR APPROVAL** | LTV: {ltv:.1f}% | Verification Clean")
    elif cibil >= 680 and directors_passed >= (num_directors_input / 2):
        st.warning(f"⚠️ **CONDITIONAL REVIEW REQUIRED** | LTV: {ltv:.1f}% | Manual risk override needed due to mid-tier credentials.")
    else:
        st.error(f"❌ **AUTOMATED ESCALATION REJECTION** | High risk criteria match or verification failure.")

else:
    st.info("💡 Please upload a customer CSV file or choose an operational profile from the database option in the sidebar to activate engine components.")
