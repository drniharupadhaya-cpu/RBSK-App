import streamlit as st
import pandas as pd
import gspread
import json
from fpdf import FPDF
import tempfile
import os

# --- 1. DATABASE CONNECTION ---
def get_spreadsheet():
    creds_dict = json.loads(st.secrets["gcp_service_account"])
    client = gspread.service_account_from_dict(creds_dict)
    sheet_url = "https://docs.google.com/spreadsheets/d/1i5wAkI7k98E80qhHRe6xQOhF4Qj9Z0DH8wjPsQ7gRZc/edit?gid=2111634358#gid=2111634358"
    return client.open_by_url(sheet_url)

# --- 2. DATA LOADING (CACHED) ---
@st.cache_data(ttl=60)
def load_all_data():
    sheet = get_spreadsheet()
    
    df_4d = pd.DataFrame(sheet.worksheet("4d_list").get_all_records()).astype(str)
    df_schools = pd.DataFrame(sheet.worksheet("school_details").get_all_records()).astype(str)
    df_aw = pd.DataFrame(sheet.worksheet("aw_data").get_all_records()).astype(str)
    
    try:
        df_anemia = pd.DataFrame(sheet.worksheet("ANEMIA").get_all_records()).astype(str)
    except:
        df_anemia = pd.DataFrame()
    
    try:
        df_students = pd.DataFrame(sheet.worksheet("students_data").get_all_records()).astype(str)
    except:
        df_students = pd.DataFrame() 

    try:
        df_directory = pd.DataFrame(sheet.worksheet("ALL SCHOOL DETAILS").get_all_records()).astype(str)
    except:
        df_directory = pd.DataFrame()

    # --- NEW: LOAD ANGANWADI MASTER DATA ---
    try:
        df_aw_master = pd.DataFrame(sheet.worksheet("aw new data").get_all_records()).astype(str)
    except:
        df_aw_master = pd.DataFrame()
        
    return df_4d, df_schools, df_aw, df_students, df_anemia, df_directory, df_aw_master

# --- 3. ACTIVATE ---
try:
    spreadsheet = get_spreadsheet() 
    df_4d, df_schools, df_aw, df_students, df_anemia, df_directory, df_aw_master = load_all_data() 
except Exception as e:
    st.error(f"Could not connect to Google Sheets. Error: {e}")
    st.stop()

# --- SIDEBAR ---
st.sidebar.title("🩺 RBSK Menu")
menu = st.sidebar.radio("Go to:", 
    [
        "1. Daily Tour Plan", "2. Child Screening", "3. 4D Defect Registry", 
        "4. Visual Analysis", "5. HBNC Newborn Visit", "6. Success Story Builder",
        "7. Anemia Tracker", "8. School Directory", "9. Anganwadi Directory"
    ]
)

# ... [Modules 1-8 remain unchanged] ...

# ==========================================
# MODULE 9: ANGANWADI DIRECTORY (NEW!)
# ==========================================
if menu == "9. Anganwadi Directory":
    st.title("👶 Digital Anganwadi Directory")
    st.write("View beneficiary counts, mother details, and center demographics.")

    if not df_aw_master.empty:
        # Build dropdown from unique AWC Names
        awc_options = sorted([str(x) for x in df_aw_master['AWC Name'].unique() if str(x) != 'nan' and str(x).strip() != ''])
        selected_awc = st.selectbox("Select an Anganwadi Center:", ["-- Select Center --"] + awc_options)
        
        if selected_awc != "-- Select Center --":
            # Filter the master data for this specific AWC
            aw_filtered = df_aw_master[df_aw_master['AWC Name'] == selected_awc]
            
            st.divider()
            st.subheader(f"🏠 {selected_awc}")
            
            # 1. Big Picture Metrics
            c1, c2, c3 = st.columns(3)
            c1.info(f"**Sector:** {aw_filtered.iloc[0].get('Sector Name', 'N/A')}")
            c2.info(f"**AWC Code:** {aw_filtered.iloc[0].get('AWC Code', 'N/A')}")
            c3.info(f"**District:** {aw_filtered.iloc[0].get('District Name', 'N/A')}")
            
            # 2. Gender Breakdown
            st.markdown("### 📊 Demographics")
            m1, m2, m3 = st.columns(3)
            total_kids = len(aw_filtered)
            boys = len(aw_filtered[aw_filtered['Gender'].str.upper() == 'M'])
            girls = len(aw_filtered[aw_filtered['Gender'].str.upper() == 'F'])
            
            m1.metric("👶 Total Children", total_kids)
            m2.metric("👦 Boys", boys)
            m3.metric("👧 Girls", girls)
            
            # 3. Beneficiary Breakdown Table
            st.markdown("### 📋 Beneficiary List")
            # Select key columns to display for the directory view
            display_cols = ['Beneficiary Name', 'Mother Name', 'DoB', 'Gender', 'Beneficiary Type']
            st.dataframe(aw_filtered[display_cols], use_container_width=True, hide_index=True)
            
            # 4. Nutritional / Health Flags
            with st.expander("🔍 View Nutritional Screening Summary"):
                st.write("Children identified with stunting or wasting at last screening:")
                risk_df = aw_filtered[(aw_filtered['Stunting'] != 'Normal') | (aw_filtered['Wasting'] != 'Normal')]
                if not risk_df.empty:
                    st.warning(f"Found {len(risk_df)} children with nutritional concerns.")
                    st.dataframe(risk_df[['Beneficiary Name', 'Stunting', 'Wasting', 'Underweight']], use_container_width=True)
                else:
                    st.success("All children in this center are at 'Normal' health status!")
    else:
        st.error("⚠️ Could not load data from 'aw new data'. Ensure the tab exists in your Google Sheet.")
