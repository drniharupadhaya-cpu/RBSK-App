import streamlit as st
import pandas as pd
import plotly.express as px
import gspread
from google.oauth2.service_account import Credentials
import json

# -----------------------------------------
# PAGE CONFIGURATION
# -----------------------------------------
st.set_page_config(page_title="DHO Command Center | Junagadh", page_icon="📊", layout="wide")

st.markdown("""
    <style>
    .big-font {font-size:26px !important; font-weight: 900; color: #1E3A8A; letter-spacing: 1px;}
    .sub-font {font-size:16px !important; color: #6B7280; margin-bottom: 20px;}
    .kpi-card {background-color: #ffffff; padding: 20px; border-radius: 12px; border-left: 6px solid #3B82F6; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);}
    .kpi-title {color: #6B7280; font-size: 13px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.5px;}
    .kpi-value {color: #111827; font-size: 36px; font-weight: 900;}
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------
# GOOGLE SHEETS CONNECTION
# -----------------------------------------
scopes = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
raw_secret = st.secrets["gcp_service_account"]
if isinstance(raw_secret, str):
    skey = json.loads(raw_secret)
else:
    skey = dict(raw_secret)

credentials = Credentials.from_service_account_info(skey, scopes=scopes)
client = gspread.authorize(credentials)

# -----------------------------------------
# DATA LOADING & MINING FUNCTIONS
# -----------------------------------------
@st.cache_data(ttl=600)
def load_and_mine_defect_data():
    try:
        sheet = client.open("NEW BIRTH DEFECT TOTAL 2025-26")
        
        conditions = {
            "Congenital Heart Disease (CHD)": "CHD",
            "Cleft Lip / Palate": "CLCP",
            "Club Foot": "CLUB FOOT ",
            "Congenital Deafness": "DEAFNESS ",
            "Congenital Cataract": "CATARACT ",
            "Other Birth Defects": "OTHER BIR"
        }
        
        all_children = {}
        master_list = [] # 🚀 NEW: A unified data warehouse for filtering
        
        for condition_name, tab_name in conditions.items():
            try:
                ws = sheet.worksheet(tab_name)
                raw_tab = ws.get_all_values()
                df = pd.DataFrame(raw_tab)
                
                if not df.empty:
                    # Smart Header Detection
                    header_idx = 0
                    for i, row in df.iterrows():
                        if sum(1 for x in row if str(x).strip() != "") > 4:
                            header_idx = i
                            break
                    
                    raw_columns = df.iloc[header_idx].astype(str).tolist()
                    
                    # Deduplicator
                    new_cols = []
                    seen = {}
                    for c in raw_columns:
                        c = c.strip().replace("\n", " ")
                        if c == "": c = "Unnamed"
                        if c in seen:
                            seen[c] += 1
                            new_cols.append(f"{c}_{seen[c]}")
                        else:
                            seen[c] = 0
                            new_cols.append(c)
                            
                    df.columns = new_cols
                    df = df[header_idx+1:].dropna(how='all')
                    all_children[condition_name] = df
                    
                    # 🚀 DATA MINING: Extract Core Metrics for the Master List
                    t_col = next((c for c in df.columns if 'તાલુકા' in c or 'TALUKA' in c.upper()), df.columns[0])
                    n_col = next((c for c in df.columns if 'NAME' in c.upper() or 'નામ' in c), df.columns[2] if len(df.columns)>2 else df.columns[0])
                    p_col = next((c for c in df.columns if 'MO' in c.upper() or 'નંબર' in c or 'CONTACT' in c.upper()), None)
                    
                    for _, row in df.iterrows():
                        taluka_val = str(row[t_col]).strip().upper()
                        if taluka_val in ['', 'NAN', 'NONE']: continue
                        # Clean up Gujarati numbers if present
                        taluka_val = ''.join([i for i in taluka_val if not i.isdigit()]).replace('.', '').strip()
                        
                        master_list.append({
                            'Taluka': taluka_val,
                            'Disease': condition_name,
                            'Child Name': row[n_col],
                            'Contact': row[p_col] if p_col else "N/A"
                        })
            except Exception:
                pass
                
        df_master = pd.DataFrame(master_list)
        return all_children, df_master
    except Exception as e:
        st.error(f"Failed to connect: {e}")
        return {}, pd.DataFrame()

@st.cache_data(ttl=600)
def load_monthly_covered_data(month_tab):
    try:
        sheet = client.open("JUNAGADH DISTRICT COVERED 2025-26")
        ws = sheet.worksheet(month_tab)
        raw_data = ws.get_all_values()
        df_month = pd.DataFrame(raw_data)
        return df_month
    except Exception:
        return pd.DataFrame()

# Load Data
with st.spinner("Mining Data from District Headquarters..."):
    dict_all_children, df_master = load_and_mine_defect_data()

# -----------------------------------------
# SIDEBAR NAVIGATION
# -----------------------------------------
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/f/fe/Seal_of_Gujarat.svg/1200px-Seal_of_Gujarat.svg.png", width=100)
st.sidebar.title("Command Center")
st.sidebar.markdown("---")
menu = st.sidebar.radio("Analytical Modules:", [
    "📊 1. District Burden Analytics", 
    "🚨 2. Triage & Child Search", 
    "📈 3. Deep Monthly Data Mining"
])

# -----------------------------------------
# MODULE 1: DISTRICT BURDEN ANALYTICS
# -----------------------------------------
if menu == "📊 1. District Burden Analytics":
    st.markdown('<p class="big-font">District Birth Defect Analytics</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-font">High-level epidemiological breakdown of all active birth defects.</p>', unsafe_allow_html=True)
    
    if not df_master.empty:
        # Top KPI Cards
        st.write("### 🏥 Total Active Cases by Category")
        disease_counts = df_master['Disease'].value_counts()
        
        cols = st.columns(4)
        count = 0
        for disease, val in disease_counts.items():
            if count > 3: break # Show top 4 for space
            colors = ["#3B82F6", "#EF4444", "#10B981", "#F59E0B"]
            with cols[count]:
                st.markdown(f'<div class="kpi-card" style="border-left-color: {colors[count]};"><div class="kpi-title">{disease}</div><div class="kpi-value" style="color: {colors[count]};">{val}</div></div>', unsafe_allow_html=True)
            count += 1
            
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        # 🚀 THE PIVOT TABLE ALGORITHM
        st.write("### 📍 Taluka-Wise Defect Pivot Table")
        
        # Create a dynamic pivot table
        pivot_df = pd.crosstab(df_master['Taluka'], df_master['Disease'], margins=True, margins_name="Total District")
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.info("Interactive Pivot Matrix")
            # Highlight max values in the pivot table
            st.dataframe(pivot_df.style.background_gradient(cmap='Blues', axis=0), use_container_width=True)
            
        with col2:
            # Let DHO filter the chart
            talukas_list = [t for t in df_master['Taluka'].unique() if 'TOTAL' not in t.upper()]
            selected_t = st.multiselect("Filter Chart by Taluka:", talukas_list, default=talukas_list[:5])
            
            if selected_t:
                chart_df = df_master[df_master['Taluka'].isin(selected_t)]
                fig = px.histogram(chart_df, x="Taluka", color="Disease", barmode="group", 
                                   title="Disease Distribution Comparison",
                                   color_discrete_sequence=px.colors.qualitative.Bold)
                fig.update_layout(yaxis_title="Number of Children", xaxis_title="Taluka", plot_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig, use_container_width=True)

# -----------------------------------------
# MODULE 2: TRIAGE & CHILD SEARCH
# -----------------------------------------
elif menu == "🚨 2. Triage & Child Search":
    st.markdown('<p class="big-font">Master Triage & Search Engine</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-font">Instantly filter the master database to track specific children by region and condition.</p>', unsafe_allow_html=True)
    
    if not df_master.empty:
        col1, col2, col3 = st.columns(3)
        
        # 🚀 DUAL FILTERS
        with col1:
            all_talukas = ["All Talukas"] + sorted(list(df_master['Taluka'].unique()))
            f_taluka = st.selectbox("🌍 Select Taluka", all_talukas)
        with col2:
            all_diseases = ["All Diseases"] + list(df_master['Disease'].unique())
            f_disease = st.selectbox("🦠 Select Disease", all_diseases)
        with col3:
            search_name = st.text_input("🔍 Search by Child's Name (Optional)")
            
        # Apply Filters
        filtered_df = df_master.copy()
        if f_taluka != "All Talukas":
            filtered_df = filtered_df[filtered_df['Taluka'] == f_taluka]
        if f_disease != "All Diseases":
            filtered_df = filtered_df[filtered_df['Disease'] == f_disease]
        if search_name:
            filtered_df = filtered_df[filtered_df['Child Name'].str.contains(search_name, case=False, na=False)]
            
        st.markdown(f"**Found {len(filtered_df)} matches.**")
        
        if not filtered_df.empty:
            st.dataframe(filtered_df.style.set_properties(**{'background-color': '#f8fafc'}), use_container_width=True, hide_index=True)
            
            # Show the FULL details of the selected disease if a specific disease is selected
            if f_disease != "All Diseases":
                st.write(f"### 📋 Full Medical Line List Details for {f_disease} in {f_taluka}")
                full_raw_df = dict_all_children[f_disease]
                
                # Try to filter the raw dataframe by the selected taluka
                t_col_raw = next((c for c in full_raw_df.columns if 'તાલુકા' in c or 'TALUKA' in c.upper()), None)
                if t_col_raw and f_taluka != "All Talukas":
                    # Clean the column for matching
                    filtered_raw = full_raw_df[full_raw_df[t_col_raw].astype(str).str.contains(f_taluka, case=False, na=False)]
                    st.dataframe(filtered_raw, use_container_width=True)
                else:
                    st.dataframe(full_raw_df, use_container_width=True)
        else:
            st.warning("No children match these filters.")

# -----------------------------------------
# MODULE 3: DEEP MONTHLY DATA MINING
# -----------------------------------------
elif menu == "📈 3. Deep Monthly Data Mining":
    st.markdown('<p class="big-font">Deep District Data Mining</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-font">Extract and visualize specific performance metrics from the monthly Excel reports.</p>', unsafe_allow_html=True)
    
    months_available = ["MAR 26", "FEB 26", "JAN 26", "DEC 25", "NOV 25", "OCT 25", "SEP 25", "AUG 25", "JUL 25", "JUN 25", "MAY 25", "APR 25"]
    col1, col2 = st.columns([1, 2])
    with col1:
        selected_month = st.selectbox("📅 Select Reporting Month:", months_available, index=10)
    
    with st.spinner("Mining spreadsheet parameters..."):
        df_monthly = load_monthly_covered_data(selected_month)
        
    if not df_monthly.empty:
        # 🚀 ALGORITHM: Auto-detecting Talukas and Metrics from the complex Excel sheet
        details_col_idx = 1 # We know 'Details' is usually column index 1 (Column B)
        
        # 1. Find all available Metrics
        metrics_list = df_monthly.iloc[3:, details_col_idx].dropna().unique().tolist()
        clean_metrics = [m for m in metrics_list if str(m).strip() != "" and len(str(m)) > 5]
        
        # 2. Find the Taluka Total Columns
        taluka_cols = {}
        # Scan row 1 & 2 to find columns that say "TALUKA JUNAGADH" etc.
        for r_idx in range(0, 3):
            for c_idx, val in enumerate(df_monthly.iloc[r_idx]):
                val_str = str(val).upper().replace('\n', ' ').strip()
                if 'TALUKA' in val_str and 'TOTAL' not in val_str:
                    t_name = val_str.replace('TALUKA', '').strip()
                    taluka_cols[t_name] = c_idx
                    
        with col2:
            if clean_metrics:
                selected_metric = st.selectbox("🎯 Select a Metric to Analyze:", clean_metrics)
            else:
                selected_metric = None
                
        if selected_metric and taluka_cols:
            st.write("---")
            st.write(f"### Comparative Analysis: {selected_metric}")
            
            # 3. Mine the data for the selected metric
            metric_data = []
            
            # Find the row containing this metric
            metric_row = df_monthly[df_monthly.iloc[:, details_col_idx] == selected_metric].iloc[0]
            
            for taluka, col_idx in taluka_cols.items():
                try:
                    val = pd.to_numeric(metric_row.iloc[col_idx], errors='coerce')
                    val = 0 if pd.isna(val) else val
                    metric_data.append({'Taluka': taluka, 'Value': val})
                except:
                    pass
                    
            chart_df = pd.DataFrame(metric_data)
            
            if not chart_df.empty:
                # Layout with Chart and Table
                c1, c2 = st.columns([2, 1])
                with c1:
                    fig = px.bar(chart_df, x='Taluka', y='Value', color='Taluka', 
                                 text_auto=True, title=f"Performance by Taluka ({selected_month})",
                                 color_discrete_sequence=px.colors.qualitative.Pastel)
                    fig.update_layout(showlegend=False, plot_bgcolor="rgba(0,0,0,0)")
                    st.plotly_chart(fig, use_container_width=True)
                with c2:
                    st.dataframe(chart_df.style.background_gradient(cmap='Greens'), hide_index=True, use_container_width=True)
            
        # Optional: Show full raw sheet
        with st.expander("👀 View Raw Monthly Spreadsheet"):
            st.dataframe(df_monthly, use_container_width=True, hide_index=True)
