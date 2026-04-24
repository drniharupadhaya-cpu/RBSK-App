import streamlit as st
import pandas as pd
import plotly.express as px
import gspread
from google.oauth2.service_account import Credentials
import json
import io
import base64
import datetime
from PIL import Image

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
    .patient-card {background-color: #f8fafc; padding: 20px; border-radius: 15px; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);}
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
# PRISTINE PHOTO ENGINE (NO-DRIVE / NO-QUOTA)
# -----------------------------------------
def process_photo_to_string(uploaded_file):
    """Resizes, compresses, and converts photo to a Base64 string for Sheet storage."""
    if uploaded_file is None:
        return "No Photo"
    
    try:
        img = Image.open(uploaded_file)
        img.thumbnail((300, 300)) 
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=70) 
        img_str = base64.b64encode(buffer.getvalue()).decode()
        return f"data:image/jpeg;base64,{img_str}"
    except Exception as e:
        return f"Error: {e}"

# -----------------------------------------
# DATA MINING ENGINE (HISTORIC DATA)
# -----------------------------------------
@st.cache_data(ttl=600)
def load_and_mine_defect_data():
    try:
        sheet = client.open("NEW BIRTH DEFECT TOTAL 2025-26 for app")
        conditions = {
            "Congenital Heart Disease (CHD)": "CHD",
            "Cleft Lip / Palate": "CLCP",
            "Club Foot": "CLUB FOOT ",
            "Congenital Deafness": "DEAFNESS ",
            "Congenital Cataract": "CATARACT ",
            "Other Birth Defects": "OTHER BIR"
        }
        all_children = {}
        master_list = []
        for condition_name, tab_name in conditions.items():
            try:
                ws = sheet.worksheet(tab_name)
                raw_tab = ws.get_all_values()
                df = pd.DataFrame(raw_tab)
                if not df.empty:
                    header_idx = 0
                    for i, row in df.iterrows():
                        row_str = str(row.values).upper()
                        if 'NAME' in row_str or 'નામ' in row_str:
                            header_idx = i
                            break
                    df.columns = [str(c).strip() for c in df.iloc[header_idx]]
                    df = df.iloc[header_idx+1:].copy()
                    col_taluka, col_name, col_gender, col_phone = None, None, None, None
                    for col in df.columns:
                        col_upper = col.upper()
                        if any(k in col_upper for k in ['TALUKA', 'તાલુકા']): col_taluka = col
                        elif any(k in col_upper for k in ['NAME', 'નામ']) and col_name is None: col_name = col
                        elif any(k in col_upper for k in ['M/F', 'સ્ત્રી', 'GENDER']): col_gender = col
                        elif any(k in col_upper for k in ['MO. NO', 'કોન્ટેક્ટ', 'CONTACT', 'MOBILE']): col_phone = col
                    if col_taluka and col_name:
                        df[col_taluka] = df[col_taluka].replace('', pd.NA).ffill()
                        for _, row in df.iterrows():
                            taluka_raw = str(row[col_taluka]).strip() if pd.notna(row[col_taluka]) else ""
                            name_val = str(row[col_name]).strip() if pd.notna(row[col_name]) else ""
                            gender_val = str(row[col_gender]).strip().upper() if col_gender and pd.notna(row[col_gender]) else "U"
                            phone_val = str(row[col_phone]).strip() if col_phone and pd.notna(row[col_phone]) else "N/A"
                            taluka_val = ''.join([i for i in taluka_raw if not i.isdigit()]).replace('.', '').strip()
                            if taluka_val.upper() in ['', 'NAN', 'NONE', 'TALUKA', 'તાલુકા', 'TOTAL', 'ટોટલ']: continue
                            if len(name_val) < 2 or 'NAME' in name_val.upper() or 'નામ' in name_val: continue
                            master_list.append({'Taluka': taluka_val, 'Disease': condition_name, 'Child Name': name_val, 'Gender': gender_val, 'Contact': phone_val})
                    all_children[condition_name] = df
            except: pass
        return all_children, pd.DataFrame(master_list)
    except Exception as e:
        st.error(f"Failed to connect: {e}")
        return {}, pd.DataFrame()

@st.cache_data(ttl=600)
def load_monthly_covered_data(month_tab):
    try:
        sheet = client.open("JUNAGADH DISTRICT COVERED 2025-26")
        ws = sheet.worksheet(month_tab)
        return pd.DataFrame(ws.get_all_values())
    except: return pd.DataFrame()

@st.cache_data(ttl=5)
def load_live_app_data():
    try:
        sheet = client.open("NEW BIRTH DEFECT TOTAL 2025-26 for app")
        ws = sheet.worksheet("APP_LIVE_REGISTRATIONS")
        data = ws.get_all_values()
        if len(data) < 1:
            return pd.DataFrame()
        df = pd.DataFrame(data)
        df.columns = ["Timestamp", "Taluka", "Condition", "Child Name", "Gender", "DOB", "Contact", "Screening Date", "Team Number", "Institution", "Referral Location", "Status", "Follow-up", "PhotoData"]
        return df
    except:
        return pd.DataFrame()

# Load Data
with st.spinner("Mining highly accurate data..."):
    dict_all_children, df_master = load_and_mine_defect_data()

# -----------------------------------------
# SIDEBAR NAVIGATION
# -----------------------------------------
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/f/fe/Seal_of_Gujarat.svg/1200px-Seal_of_Gujarat.svg.png", width=100)
st.sidebar.title("Command Center")
st.sidebar.markdown("---")
menu = st.sidebar.radio("Analytical Modules:", [
    "--- 📁 ARCHIVE: 2025-26 ---",
    "📊 1. District Burden Analytics", 
    "🚨 2. Triage & Child Search", 
    "📈 3. Deep Monthly Data Mining",
    "--- 🚀 LIVE: 2026-27 CYCLE ---",
    "➕ 4. New Case Registration",
    "🎯 5. Live Cycle Analytics"
])

# -----------------------------------------
# MODULE 1: DISTRICT BURDEN ANALYTICS
# -----------------------------------------
if menu == "📊 1. District Burden Analytics":
    st.markdown('<p class="big-font">District Birth Defect Analytics</p>', unsafe_allow_html=True)
    
    if not df_master.empty:
        # --- ADDED FILTERS ---
        st.write("### 🔍 Global Archive Filters")
        f_col1, f_col2 = st.columns(2)
        with f_col1:
            all_talukas = sorted(list(df_master['Taluka'].unique()))
            sel_talukas = st.multiselect("Filter by Taluka:", all_talukas, default=all_talukas)
        with f_col2:
            all_diseases = sorted(list(df_master['Disease'].unique()))
            sel_diseases = st.multiselect("Filter by Disease:", all_diseases, default=all_diseases)
        
        filtered_df = df_master[(df_master['Taluka'].isin(sel_talukas)) & (df_master['Disease'].isin(sel_diseases))]
        
        st.write("### 🏥 Active Cases by Category")
        disease_counts = filtered_df['Disease'].value_counts()
        cols = st.columns(4)
        for i, (disease, val) in enumerate(disease_counts.items()):
            if i > 3: break
            colors = ["#3B82F6", "#EF4444", "#10B981", "#F59E0B"]
            with cols[i]:
                st.markdown(f'<div class="kpi-card" style="border-left-color: {colors[i]};"><div class="kpi-title">{disease}</div><div class="kpi-value" style="color: {colors[i]};">{val}</div></div>', unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        pivot_df = pd.crosstab(filtered_df['Taluka'], filtered_df['Disease'], margins=True, margins_name="Total")
        st.write("### 📍 Taluka-Wise Defect Pivot Table")
        st.dataframe(pivot_df.style.background_gradient(cmap='Blues', axis=0), use_container_width=True)

# -----------------------------------------
# MODULE 2: TRIAGE & CHILD SEARCH
# -----------------------------------------
elif menu == "🚨 2. Triage & Child Search":
    st.markdown('<p class="big-font">Master Triage & Search Engine</p>', unsafe_allow_html=True)
    if not df_master.empty:
        col1, col2, col3 = st.columns(3)
        with col1: f_taluka = st.selectbox("🌍 Select Taluka", ["All Talukas"] + sorted(list(df_master['Taluka'].unique())))
        with col2: f_disease = st.selectbox("🦠 Select Disease", ["All Diseases"] + list(df_master['Disease'].unique()))
        with col3: search_name = st.text_input("🔍 Search by Child's Name")
        
        filtered_df = df_master.copy()
        if f_taluka != "All Talukas": filtered_df = filtered_df[filtered_df['Taluka'] == f_taluka]
        if f_disease != "All Diseases": filtered_df = filtered_df[filtered_df['Disease'] == f_disease]
        if search_name: filtered_df = filtered_df[filtered_df['Child Name'].str.contains(search_name, case=False, na=False)]
        
        st.dataframe(filtered_df, use_container_width=True, hide_index=True)

# -----------------------------------------
# MODULE 3: DEEP MONTHLY DATA MINING
# -----------------------------------------
elif menu == "📈 3. Deep Monthly Data Mining":
    st.markdown('<p class="big-font">Deep District Performance Mining</p>', unsafe_allow_html=True)
    months_available = ["MAR 26", "FEB 26", "JAN 26", "DEC 25", "NOV 25", "OCT 25", "SEP 25", "AUG 25", "JUL 25", "JUN 25", "MAY 25", "APR 25"]
    
    col_sel1, col_sel2 = st.columns(2)
    with col_sel1:
        selected_month = st.selectbox("📅 Select Reporting Month:", months_available, index=10)
    
    df_monthly = load_monthly_covered_data(selected_month)
    
    if not df_monthly.empty:
        # --- DYNAMIC MINING LOGIC ---
        taluka_cols = {}
        for r_idx in range(0, 4):
            for c_idx, val in enumerate(df_monthly.iloc[r_idx]):
                val_str = str(val).upper().replace('\n', ' ').strip()
                if 'TALUKA' in val_str and 'TOTAL' not in val_str and c_idx > 1:
                    t_name = val_str.replace('TALUKA', '').strip()
                    if t_name not in taluka_cols: taluka_cols[t_name] = c_idx
        
        clean_metrics = []
        for r_idx in range(3, len(df_monthly)):
            metric_val = str(df_monthly.iloc[r_idx, 1]).strip()
            if len(metric_val) > 5 and metric_val not in clean_metrics:
                clean_metrics.append(metric_val)
        
        with col_sel2:
            selected_metric = st.selectbox("🎯 Select Performance Metric (Disease/Metric):", clean_metrics if clean_metrics else ["None"])
        
        # --- ADDED TALUKA FILTER FOR CHART ---
        st.write("---")
        st.write("### 📍 Comparative Analysis Filter")
        all_found_talukas = list(taluka_cols.keys())
        sel_mining_talukas = st.multiselect("Filter Chart by Specific Talukas:", all_found_talukas, default=all_found_talukas)

        if selected_metric != "None":
            metric_data = []
            for r_idx in range(3, len(df_monthly)):
                if str(df_monthly.iloc[r_idx, 1]).strip() == selected_metric:
                    for taluka, col_idx in taluka_cols.items():
                        if taluka in sel_mining_talukas:
                            raw_val = df_monthly.iloc[r_idx, col_idx]
                            val = pd.to_numeric(raw_val, errors='coerce')
                            metric_data.append({'Taluka': taluka, 'Value': 0 if pd.isna(val) else val})
                    break
            
            chart_df = pd.DataFrame(metric_data)
            if not chart_df.empty:
                fig = px.bar(chart_df, x='Taluka', y='Value', color='Taluka', title=f"{selected_metric} Overview", text_auto=True)
                st.plotly_chart(fig, use_container_width=True)

        with st.expander("👀 View Raw Monthly Data Table"):
            st.dataframe(df_monthly, use_container_width=True, hide_index=True)

# -----------------------------------------
# MODULE 4: NEW CASE REGISTRATION
# -----------------------------------------
elif menu == "➕ 4. New Case Registration":
    st.markdown('<p class="big-font">➕ Register New Birth Defect Case (2026-27)</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-font">Secured Internal Database: No Quota Errors, No Storage Gaps.</p>', unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    with c1:
        st.write("### 👤 Child Demographics")
        taluka = st.selectbox("🌍 Taluka", ["Junagadh", "Vanthali", "Manavadar", "Keshod", "Mangrol", "Maliya", "Mendarada", "Visavadar", "Bhesan"])
        disease = st.selectbox("🦠 Detected Condition", ["Congenital Heart Disease (CHD)", "Cleft Lip / Palate", "Club Foot", "Congenital Deafness", "Congenital Cataract", "Microcephaly", "Macrocephaly", "Congenital Ear Problems", "Neck and Face Defects", "Congenital Eye Problems", "ROP", "DOWN'S SYNDROME", "THALESSEMIA", "CANCER"])
        child_name = st.text_input("📝 Child's Full Name")
        gender = st.selectbox("⚧️ Gender", ["Male", "Female"])
        dob = st.date_input("🎂 Date of Birth", min_value=datetime.date(2008, 1, 1), max_value=datetime.date.today())
        contact = st.text_input("📱 Guardian Contact Number", max_chars=10)
        
    with c2:
        st.write("### 🏥 Clinical & Referral Details")
        screening_date = st.date_input("🗓️ Date of Screening", value=datetime.date.today())
        team_num = st.text_input("🚑 Team Number (e.g., 1240315)")
        institution = st.selectbox("🏫 Institution Type", ["AWC (Anganwadi)", "School", "PHC / Delivery Point"])
        referral_base = st.selectbox("🏥 Referral Location", ["DEIC", "SDH", "U.N. MEHTA", "AHMEDABAD CIVIL", "RAJKOT CIVIL", "OTHER PRIVATE HOSPITAL", "OTHER TRUST HOSPITAL", "OTHER NGO", "OTHER (Type Manually)"])
        
        if "OTHER" in referral_base:
            referral_exact = st.text_input("⚠️ Specify Hospital Name:")
            final_referral = f"{referral_base} - {referral_exact}"
        else: final_referral = referral_base
            
        status = st.selectbox("🚦 Intervention Status", ["PENDING", "WAITING FOR APPROVAL", "ON TREATMENT", "COMPLETED", "REFUSAL", "MIGRATION", "DEATH"])
        follow_up = st.date_input("⏰ Next Follow-Up Date")

    st.write("### 📸 Clinical Evidence")
    photo_file = st.file_uploader("Upload Child's Photo (JPG/PNG)", type=['jpg', 'jpeg', 'png'])

    if st.button("🚀 Submit to Live Database", use_container_width=True, type="primary"):
        if child_name.strip() == "" or contact.strip() == "":
            st.error("⚠️ Child Name and Contact are required!")
        else:
            with st.spinner("Processing registration and optimizing photo..."):
                try:
                    photo_data = process_photo_to_string(photo_file)
                    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    new_row = [timestamp, taluka, disease, child_name, gender, str(dob), contact, str(screening_date), team_num, institution, final_referral, status, str(follow_up), photo_data]
                    ws = client.open("NEW BIRTH DEFECT TOTAL 2025-26 for app").worksheet("APP_LIVE_REGISTRATIONS")
                    ws.append_row(new_row)
                    st.success(f"✅ Successfully registered {child_name} into 2026-27 cycle!")
                    st.balloons()
                except Exception as e: st.error(f"❌ Error: {e}")

# -----------------------------------------
# MODULE 5: LIVE CYCLE ANALYTICS
# -----------------------------------------
elif menu == "🎯 5. Live Cycle Analytics":
    st.markdown('<p class="big-font">🎯 Live Cycle Analytics (2026-27)</p>', unsafe_allow_html=True)
    df_live = load_live_app_data()

    if df_live.empty:
        st.warning("No data found in the 2026-27 Database.")
    else:
        # --- ADDED TOP FILTERS FOR MODULE 5 ---
        st.write("### 🔍 Global Live Filters")
        fl_col1, fl_col2 = st.columns(2)
        with fl_col1:
            l_talukas = ["All Talukas"] + sorted(list(df_live['Taluka'].unique()))
            sel_l_taluka = st.selectbox("Filter Dashboard by Taluka:", l_talukas)
        with fl_col2:
            l_conditions = ["All Conditions"] + sorted(list(df_live['Condition'].unique()))
            sel_l_cond = st.selectbox("Filter Dashboard by Condition:", l_conditions)

        # Apply Filters to the dataframe
        df_filtered_live = df_live.copy()
        if sel_l_taluka != "All Talukas":
            df_filtered_live = df_filtered_live[df_filtered_live['Taluka'] == sel_l_taluka]
        if sel_l_cond != "All Conditions":
            df_filtered_live = df_filtered_live[df_filtered_live['Condition'] == sel_l_cond]

        # KPIs
        t1, t2, t3 = st.columns(3)
        total_l = len(df_filtered_live)
        done_l = len(df_filtered_live[df_filtered_live['Status'] == 'COMPLETED'])
        pending_l = total_l - done_l
        
        with t1: st.markdown(f'<div class="kpi-card" style="border-left-color: #3B82F6;"><div class="kpi-title">Total Registered</div><div class="kpi-value">{total_l}</div></div>', unsafe_allow_html=True)
        with t2: st.markdown(f'<div class="kpi-card" style="border-left-color: #10B981;"><div class="kpi-title">Interventions Done</div><div class="kpi-value">{done_l}</div></div>', unsafe_allow_html=True)
        with t3: st.markdown(f'<div class="kpi-card" style="border-left-color: #EF4444;"><div class="kpi-title">Total Pending</div><div class="kpi-value">{pending_l}</div></div>', unsafe_allow_html=True)

        st.write("---")
        
        # CHARTS
        c1, c2 = st.columns(2)
        with c1:
            fig_p = px.pie(df_filtered_live, names='Status', title="Live Intervention Status", hole=0.4)
            st.plotly_chart(fig_p, use_container_width=True)
        with c2:
            fig_b = px.bar(df_filtered_live['Taluka'].value_counts().reset_index(), x='Taluka', y='count', title="Cases by Taluka", color='Taluka')
            st.plotly_chart(fig_b, use_container_width=True)

        # --- ADDED LIVE CASE LEDGER TABLE ---
        st.write("### 📜 2026-27 Registered Case Ledger")
        st.dataframe(df_filtered_live.drop(columns=['PhotoData']), use_container_width=True, hide_index=True)

        # DIGITAL PROFILE VIEWER (Updated to follow filters)
        st.write("### 🔍 Search & View Digital Child Profile")
        search_list = sorted(df_filtered_live['Child Name'].unique())
        selected_child = st.selectbox("Select Child (Filter applied):", ["-- Select Child --"] + search_list)

        if selected_child != "-- Select Child --":
            child_row = df_filtered_live[df_filtered_live['Child Name'] == selected_child].iloc[0]
            p1, p2 = st.columns([1, 2])
            with p1:
                photo_str = str(child_row['PhotoData'])
                if photo_str.startswith("data:image"): st.image(photo_str, use_container_width=True)
                else: st.info("No photo available.")
            with p2:
                st.markdown(f"""
                <div class="patient-card">
                    <h3>{child_row['Child Name']}</h3>
                    <p><b>Condition:</b> {child_row['Condition']} | <b>Taluka:</b> {child_row['Taluka']}</p>
                    <p><b>Mobile:</b> {child_row['Contact']} | <b>DOB:</b> {child_row['DOB']}</p>
                    <p><b>Status:</b> <span style='color:red;'>{child_row['Status']}</span></p>
                    <p><b>Referral:</b> {child_row['Referral Location']}</p>
                    <p><b>Follow-up:</b> {child_row['Follow-up']}</p>
                </div>
                """, unsafe_allow_html=True)
