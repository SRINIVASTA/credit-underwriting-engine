import pandas as pd
import streamlit as st
import io

# Preserve your exact original application backend imports
from underwriting_core import (
    calculate_score,
    evaluate_risk,
    process_financials
)

# Set your page layout
st.set_page_config(
    page_title="Credit Underwriting Engine",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Enterprise Credit Underwriting Engine")
st.markdown("Automated risk verification portal and financial appraisal module.")

# 1. SIDEBAR CONTROLS & MULTI-ROW CSV UPLOADER
app_mode = st.sidebar.radio("Select Processing Mode", ["Upload Mode (CSV)", "Database Profile Lookup"])

active_profile = None
unique_session_key = "default_session"

if app_mode == "Upload Mode (CSV)":
    st.subheader("📁 Upload Customer Credit Sheet")
    uploaded_file = st.file_uploader("Drop client risk parameters (.csv format)", type=["csv"])
    
    if uploaded_file is not None:
        try:
            uploaded_df = pd.read_csv(uploaded_file)
            if not uploaded_df.empty:
                # NEW: If CSV has multiple rows, let the user select which company/report to analyze
                if len(uploaded_df) > 1 and "Industry" in uploaded_df.columns:
                    selected_row_industry = st.selectbox(
                        "Select a client report from the uploaded file:", 
                        uploaded_df["Industry"].tolist(),
                        key="uploaded_csv_row_selector"
                    )
                    # Filter data to the chosen row
                    matched_row = uploaded_df[uploaded_df["Industry"] == selected_row_industry]
                    active_profile = matched_row.iloc[0].to_dict()
                else:
                    # Fallback to the first row if it's a single-row file
                    active_profile = uploaded_df.iloc[0].to_dict()
                
                # Dynamic key changes whenever a different company is selected to wipe widget memory
                current_industry = active_profile.get('Industry', 'Unknown')
                unique_session_key = f"uploaded_{uploaded_file.name}_{current_industry}"
                st.success(f"Active Report: **{current_industry}**")
        except Exception as e:
            st.error(f"Error parsing uploaded file: {str(e)}")
else:
    # (Your original internal database selection logic goes here)
    st.subheader("🔍 Select Internal Database Profile")
    # Placeholder for your database setup:
    db_industries = ["Pharma", "FMCG", "Healthcare", "Education"] 
    selected_ind = st.selectbox("Select Target Enterprise Client", db_industries)
    unique_session_key = f"db_{selected_ind}"
    # active_profile = your_database_fetch_logic(selected_ind)

st.divider()

# 2. RUNNING THE RISK PROFILE AND FIXING THE WIDGET BUG
if active_profile is not None:
    
    # Extract structural variables from your active dataset
    num_directors = active_profile.get("num_direc", 1)
    
    # --- SAFE MATH ENGINE FOR LINE 55 CRASH ---
    # 1. Safely establish your upper limit
    max_value_limit = int(num_directors)
    
    # 2. Get incoming raw value from dataset profile
    profile_passed_val = active_profile.get("directors_passed", max_value_limit)
    
    # 3. Force the layout value to remain within limits (min/max bounding check)
    safe_starting_value = min(int(profile_passed_val), max_value_limit)
    safe_starting_value = max(0, safe_starting_value)
    
    # --- YOUR ORIGINAL LINE 55 (UPDATED) ---
    directors_passed = st.number_input(
        "Verified Cleared Directors (PAN + Aadhaar Passes)", 
        min_value=0, 
        max_value=max_value_limit, 
        value=safe_starting_value,
        key=f"dir_passed_widget_{unique_session_key}" # Unique key resets cache per row change
    )
    # ----------------------------------------

    # 3. VISUALIZATIONS SECTION
    st.markdown("### 📈 Risk Evaluation & Financial Metrics")
    
    # Run your original backend module calculations
    try:
        calculated_score_val = calculate_score(active_profile)
        risk_evaluation_status = evaluate_risk(calculated_score_val)
        current_ratio = process_financials(active_profile)
        
        # Display Visual Layout Cards
        metric_col1, metric_col2, metric_col3 = st.columns(3)
        with metric_col1:
            st.metric(label="Risk Assessment Score", value=str(calculated_score_val))
        with metric_col2:
            st.metric(label="Classification Status", value=str(risk_evaluation_status))
        with metric_col3:
            st.metric(label="Current Liquidity Ratio", value=f"{current_ratio}x")
            
        # Optional: Render simple visual gauge chart via standard native charts
        chart_data = pd.DataFrame({
            "Metrics": ["Current Score", "Target Safety Baseline"],
            "Values": [calculated_score_val, 700]
        })
        st.bar_chart(data=chart_data, x="Metrics", y="Values")
        
    except Exception as calculation_error:
        st.warning(f"⚠️ Financial engine computation warning: {str(calculation_error)}")

else:
    st.info("💡 Please upload a customer CSV file or choose an operational profile to activate dashboard analytics.")
