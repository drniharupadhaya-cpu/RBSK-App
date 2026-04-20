import streamlit as st
import pandas as pd
import plotly.express as px
import gspread
from google.oauth2.service_account import Credentials

# -----------------------------------------
# PAGE CONFIGURATION
# -----------------------------------------
st.set_page_config(page_title="DHO Command Center | Junagadh", page_icon="🏥", layout="wide")

st.markdown("""
    <style>
    .big-font {font-size:24px !important; font-weight: bold; color: #1E3A8A;}
    .kpi-card {background-color: #F3F4F6; padding: 20px; border-radius: 10px; border-left: 5px solid #3B82F6; box-shadow: 2px 2px 5px rgba(0,0,0,0.1);}
    .kpi-title {color: #6B7280; font-size: 14px; font-weight: bold; text-transform: uppercase;}
    .kpi-value {color: #111827; font-size: 32px; font-weight: 900;}
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------
# GOOGLE SHEETS CONNECTION
# -----------------------------------------
import json

scopes = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# Pull the secret from Streamlit
raw_secret = st.secrets["gcp_service_account"]

# 🚀 BULLETPROOF FIX: Safely translate the secret whether it's a String or a Dictionary
if isinstance(raw_secret, str):
    skey = json.loads(raw_secret)
else:
    skey = dict(raw_secret)

credentials = Credentials.from_service_account_info(skey, scopes=scopes)
client = gspread.authorize(credentials)

# -----------------------------------------
# DATA LOADING FUNCTION (Caches for 10 mins for speed)
# -----------------------------------------
@st.cache_data(ttl=600)
def load_all_defect_data():
    try:
        sheet = client.open("NEW BIRTH DEFECT TOTAL 2025-26 (1).xlsx")
        
        # 1. Load Executive Summary
        summary_ws = sheet.worksheet("SUMMRY SHEET report")
        df_summary = pd.DataFrame(summary_ws.get_all_records())
        
        # 2. Load ALL Disease Line Lists
        conditions = {
            "Congenital Heart Disease (CHD)": "CHD",
            "Cleft Lip / Palate": "CLCP",
            "Club Foot": "CLUB FOOT ",
            "Congenital Deafness": "DEAFNESS ",
            "Congenital Cataract": "CATARACT ",
            "Other Birth Defects": "OTHER BIR"
        }
        
        all_children = {}
        for condition_name, tab_name in conditions.items():
            try:
                ws = sheet.worksheet(tab_name)
                df = pd.DataFrame(ws.get_all_records())
                # Clean up empty rows
                df = df.dropna(how='all')
                all_children[condition_name] = df
            except Exception as e:
                st.warning(f"Could not load tab: {tab_name}. Error: {e}")
                
        return df_summary, all_children
    except Exception as e:
        st.error(f"Failed to connect to Birth Defect Sheet: {e}")
        return pd.DataFrame(), {}

@st.cache_data(ttl=600)
def load_monthly_covered_data(month_tab):
    try:
        sheet = client.open("JUNAGADH DISTRICT COVERED 2025-26 (1).xlsx")
        ws = sheet.worksheet(month_tab)
        # Fetching all values as a raw list of lists to handle the complex formatting
        raw_data = ws.get_all_values()
        df_month = pd.DataFrame(raw_data)
        return df_month
    except Exception as e:
        st.error(f"Failed to load {month_tab} from District Covered Sheet: {e}")
        return pd.DataFrame()

# Load initial data
with st.spinner("Fetching Live Data from District Headquarters..."):
    df_defect_summary, dict_all_children = load_all_defect_data()

# -----------------------------------------
# SIDEBAR NAVIGATION
# -----------------------------------------
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/f/fe/Seal_of_Gujarat.svg/1200px-Seal_of_Gujarat.svg.png", width=100)
st.sidebar.title("DHO Command Center")
st.sidebar.markdown("---")
menu = st.sidebar.radio("Select Module:", [
    "📊 Executive Snapshot", 
    "🚨 Critical Triage Tracker", 
    "👥 Monthly District Reports"
])

# -----------------------------------------
# MODULE 1: EXECUTIVE SNAPSHOT
# -----------------------------------------
if menu == "📊 Executive Snapshot":
    st.markdown('<p class="big-font">District Executive Snapshot: Junagadh</p>', unsafe_allow_html=True)
    st.markdown("Live aggregate data of Birth Defects across the district.")
    
    if not df_defect_summary.empty:
        # Standardize column names dynamically just in case
        cols = df_defect_summary.columns
        taluka_col = cols[1] if len(cols) > 1 else 'Taluka'
        total_col = cols[-1] # The last column is usually the Total Birth Defects
        
        # Calculate high-level KPIs based on the raw summary sheet
        # Assuming last row is the "JUNAGADH DIST." totals
        totals_row = df_defect_summary.iloc[-2] if "JUNAGADH DIST" in str(df_defect_summary.iloc[-2].values) else df_defect_summary.iloc[-1]
        
        try:
            total_defects = int(totals_row[total_col])
        except:
            total_defects = "N/A"

        st.write("### District Wide Birth Defect Burden (2025-26)")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f'<div class="kpi-card"><div class="kpi-title">Total Defects Identified</div><div class="kpi-value">{total_defects}</div></div>', unsafe_allow_html=True)
        with col2:
            st.markdown(f'<div class="kpi-card" style="border-left-color: #EF4444;"><div class="kpi-title">Severe CHD Cases</div><div class="kpi-value" style="color: #EF4444;">{totals_row.get("Cong. Heart Disease", "N/A")}</div></div>', unsafe_allow_html=True)
        with col3:
            st.markdown(f'<div class="kpi-card" style="border-left-color: #F59E0B;"><div class="kpi-title">Cleft Lip / Palate</div><div class="kpi-value" style="color: #F59E0B;">{totals_row.get("Cleft Lip & Palate", "N/A")}</div></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        
        st.write("#### Raw Summary Data (Live from Google Sheets)")
        st.dataframe(df_defect_summary, use_container_width=True)
    else:
        st.warning("No summary data found.")

# -----------------------------------------
# MODULE 2: CRITICAL TRIAGE TRACKER (ALL DISEASES)
# -----------------------------------------
elif menu == "🚨 Critical Triage Tracker":
    st.markdown('<p class="big-font">Master Children Line List & Triage</p>', unsafe_allow_html=True)
    st.markdown("View all children registered across all disease categories.")
    
    # Create dropdown for all conditions
    options = ["Show All Children (Combined)"] + list(dict_all_children.keys())
    selected_condition = st.selectbox("Filter by Condition:", options)
    
    st.write(f"### Displaying: {selected_condition}")
    
    if selected_condition == "Show All Children (Combined)":
        # Simply display each dataframe one after the other in expandable tabs
        for condition, df in dict_all_children.items():
            if not df.empty and len(df) > 2: # Skip completely empty sheets
                with st.expander(f"📌 {condition} ({len(df)} records)", expanded=False):
                    st.dataframe(df, use_container_width=True)
    else:
        # Display the specific selected condition
        df_selected = dict_all_children.get(selected_condition, pd.DataFrame())
        if not df_selected.empty:
            st.dataframe(df_selected, use_container_width=True)
            st.success(f"Successfully loaded {len(df_selected)} rows for {selected_condition}.")
        else:
            st.warning(f"No data found in the {selected_condition} tab.")

# -----------------------------------------
# MODULE 3: MONTHLY DISTRICT REPORTS
# -----------------------------------------
elif menu == "👥 Monthly District Reports":
    st.markdown('<p class="big-font">Live District Covered Reports</p>', unsafe_allow_html=True)
    st.markdown("Pulling full monthly performance data directly from the MHT Teams' Google Sheet.")
    
    # You can add more months here as they get added to your Google Sheet!
    months_available = [
        "MAR 26", "FEB 26", "JAN 26", "DEC 25", "NOV 25", 
        "OCT 25", "SEP 25", "AUG 25", "JUL 25", "JUN 25", "MAY 25", "APR 25"
    ]
    
    selected_month = st.selectbox("Select Reporting Month:", months_available, index=10) # Defaults to MAY 25
    
    with st.spinner(f"Loading complete data for {selected_month}..."):
        df_monthly = load_monthly_covered_data(selected_month)
        
    if not df_monthly.empty:
        st.write(f"### Full Data Sheet: {selected_month}")
        st.info("💡 You can scroll left/right and up/down to view all Teams and Talukas.")
        
        # Displaying raw data without indices for a cleaner look
        st.dataframe(df_monthly, use_container_width=True, hide_index=True)
    else:
        st.warning(f"No data found for {selected_month}. Check if the tab name exactly matches in Google Sheets.")
