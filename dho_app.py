import streamlit as st
import pandas as pd
import plotly.express as px
import gspread
from google.oauth2.service_account import Credentials
import json
import io
import datetime
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

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
# GOOGLE DRIVE PHOTO UPLOADER
# -----------------------------------------
@st.cache_resource
def get_drive_service():
    # Uses the same credentials you already set up for Google Sheets
    return build('drive', 'v3', credentials=credentials)

def upload_photo_to_drive(uploaded_file, child_name, disease):
    if uploaded_file is None:
        return "No Photo"
    
    try:
        drive_service = get_drive_service()
        
        # 🔴 PASTE YOUR GOOGLE DRIVE FOLDER ID HERE:
        FOLDER_ID = "1yxpJtX_4PV10vC7wrmguuH598fV5vwkU" 
        
        # Create a clean file name
        file_extension = uploaded_file.name.split('.')[-1]
        new_file_name = f"{child_name}_{disease}_{datetime.datetime.now().strftime('%Y%m%d')}.{file_extension}"
        
        file_metadata = {
            'name': new_file_name,
            'parents': [FOLDER_ID]
        }
        
        media = MediaIoBaseUpload(io.BytesIO(uploaded_file.getvalue()), mimetype=uploaded_file.type, resumable=True)
        
        # Upload the file
        file = drive_service.files().create(body=file_metadata, media_body=media, fields='id, webViewLink').execute()
        
        # Make the file viewable to anyone with the link
        drive_service.permissions().create(
            fileId=file.get('id'),
            body={'type': 'anyone', 'role': 'reader'}
        ).execute()
        
        return file.get('webViewLink') # Returns the clickable URL
    except Exception as e:
        st.error(f"Photo Upload Failed: {e}")
        return "Upload Error"

# -----------------------------------------
# DATA MINING ENGINE (BULLETPROOF ACCURACY)
# -----------------------------------------
@st.cache_data(ttl=600)
def load_and_mine_defect_data():
    try:
        # 🚀 Now connects to your newly prepared sheet
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
                    # 1. Find the real header row
                    header_idx = 0
                    for i, row in df.iterrows():
                        row_str = str(row.values).upper()
                        if 'NAME' in row_str or 'નામ' in row_str:
                            header_idx = i
                            break
                    
                    df.columns = [str(c).strip() for c in df.iloc[header_idx]]
                    df = df.iloc[header_idx+1:].copy()
                    
                    # 2. DYNAMIC COLUMN MATCHING (Fixes shifted columns)
                    col_taluka, col_name, col_gender, col_phone = None, None, None, None
                    
                    for col in df.columns:
                        col_upper = col.upper()
                        if any(k in col_upper for k in ['TALUKA', 'તાલુકા']):
                            col_taluka = col
                        elif any(k in col_upper for k in ['NAME', 'નામ']) and col_name is None:
                            col_name = col
                        elif any(k in col_upper for k in ['M/F', 'સ્ત્રી', 'GENDER']):
                            col_gender = col
                        elif any(k in col_upper for k in ['MO. NO', 'કોન્ટેક્ટ', 'CONTACT', 'MOBILE']):
                            col_phone = col
                            
                    if col_taluka and col_name:
                        # 3. FIX MERGED CELLS (Forward Fill)
                        df[col_taluka] = df[col_taluka].replace('', pd.NA).ffill()
                        
                        for _, row in df.iterrows():
                            # Safely extract using the dynamically found column names
                            taluka_raw = str(row[col_taluka]).strip() if pd.notna(row[col_taluka]) else ""
                            name_val = str(row[col_name]).strip() if pd.notna(row[col_name]) else ""
                            gender_val = str(row[col_gender]).strip().upper() if col_gender and pd.notna(row[col_gender]) else "U"
                            phone_val = str(row[col_phone]).strip() if col_phone and pd.notna(row[col_phone]) else "N/A"
                            
                            # Clean up Taluka names
                            taluka_val = ''.join([i for i in taluka_raw if not i.isdigit()]).replace('.', '').strip()
                            
                            # Filter out headers, totals, and empty rows
                            if taluka_val.upper() in ['', 'NAN', 'NONE', 'TALUKA', 'તાલુકા', 'TOTAL', 'ટોટલ']: continue
                            if len(name_val) < 2 or 'NAME' in name_val.upper() or 'નામ' in name_val: continue
                            if phone_val == "": phone_val = "N/A"
                            
                            master_list.append({
                                'Taluka': taluka_val,
                                'Disease': condition_name,
                                'Child Name': name_val,
                                'Gender': gender_val,
                                'Contact': phone_val
                            })
                            
                    all_children[condition_name] = df
                    
            except Exception as e:
                # Silently skip missing tabs
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
        return pd.DataFrame(raw_data)
    except Exception:
        return pd.DataFrame()

# Load Data
with st.spinner("Mining highly accurate data from District Headquarters..."):
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
    "🎯 5. Live Cycle Analytics (Coming Soon)"
])

# -----------------------------------------
# MODULE 1: DISTRICT BURDEN ANALYTICS
# -----------------------------------------
if menu == "📊 1. District Burden Analytics":
    st.markdown('<p class="big-font">District Birth Defect Analytics</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-font">Calculated instantly from live Master Line Lists for 100% accuracy.</p>', unsafe_allow_html=True)
    
    if not df_master.empty:
        # Top KPI Cards
        st.write("### 🏥 Total Active Cases by Category")
        disease_counts = df_master['Disease'].value_counts()
        
        cols = st.columns(4)
        count = 0
        for disease, val in disease_counts.items():
            if count > 3: break 
            colors = ["#3B82F6", "#EF4444", "#10B981", "#F59E0B"]
            with cols[count]:
                st.markdown(f'<div class="kpi-card" style="border-left-color: {colors[count]};"><div class="kpi-title">{disease}</div><div class="kpi-value" style="color: {colors[count]};">{val}</div></div>', unsafe_allow_html=True)
            count += 1
            
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        # INTERACTIVE PIVOT MATRIX
        st.write("### 📍 Taluka-Wise Defect Pivot Table")
        
        pivot_df = pd.crosstab(df_master['Taluka'], df_master['Disease'], margins=True, margins_name="District Total")
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.info("Live Master Matrix")
            st.dataframe(pivot_df.style.background_gradient(cmap='Blues', axis=0), use_container_width=True)
            
        with col2:
            valid_talukas = sorted([t for t in df_master['Taluka'].unique() if t != 'District Total'])
            selected_t = st.multiselect("Filter Chart by Taluka:", valid_talukas, default=valid_talukas[:5] if len(valid_talukas)>5 else valid_talukas)
            
            if selected_t:
                chart_df = df_master[df_master['Taluka'].isin(selected_t)]
                fig = px.histogram(chart_df, x="Taluka", color="Disease", barmode="group", 
                                   title="Disease Distribution Comparison",
                                   color_discrete_sequence=px.colors.qualitative.Bold)
                fig.update_layout(yaxis_title="Total Children", xaxis_title="Taluka", plot_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig, use_container_width=True)

# -----------------------------------------
# MODULE 2: TRIAGE & CHILD SEARCH
# -----------------------------------------
elif menu == "🚨 2. Triage & Child Search":
    st.markdown('<p class="big-font">Master Triage & Search Engine</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-font">Search the verified Master List combining all condition datasets.</p>', unsafe_allow_html=True)
    
    if not df_master.empty:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            all_talukas = ["All Talukas"] + sorted(list(df_master['Taluka'].unique()))
            f_taluka = st.selectbox("🌍 Select Taluka", all_talukas)
        with col2:
            all_diseases = ["All Diseases"] + list(df_master['Disease'].unique())
            f_disease = st.selectbox("🦠 Select Disease", all_diseases)
        with col3:
            search_name = st.text_input("🔍 Search by Child's Name")
            
        filtered_df = df_master.copy()
        if f_taluka != "All Talukas":
            filtered_df = filtered_df[filtered_df['Taluka'] == f_taluka]
        if f_disease != "All Diseases":
            filtered_df = filtered_df[filtered_df['Disease'] == f_disease]
        if search_name:
            filtered_df = filtered_df[filtered_df['Child Name'].str.contains(search_name, case=False, na=False)]
            
        st.markdown(f"**🟢 Found {len(filtered_df)} Verified Matches**")
        
        if not filtered_df.empty:
            st.dataframe(filtered_df.style.set_properties(**{'background-color': '#f8fafc'}), use_container_width=True, hide_index=True)
        else:
            st.warning("No children match these filters.")

# -----------------------------------------
# MODULE 3: DEEP MONTHLY DATA MINING
# -----------------------------------------
elif menu == "📈 3. Deep Monthly Data Mining":
    st.markdown('<p class="big-font">Deep District Performance Mining</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-font">Dynamically extracts KPIs from complex monthly MHT sheets.</p>', unsafe_allow_html=True)
    
    months_available = ["MAR 26", "FEB 26", "JAN 26", "DEC 25", "NOV 25", "OCT 25", "SEP 25", "AUG 25", "JUL 25", "JUN 25", "MAY 25", "APR 25"]
    col1, col2 = st.columns([1, 2])
    with col1:
        selected_month = st.selectbox("📅 Select Reporting Month:", months_available, index=10)
    
    with st.spinner(f"Mining complex headers for {selected_month}..."):
        df_monthly = load_monthly_covered_data(selected_month)
        
    if not df_monthly.empty:
        # 🚀 ALGORITHM: Auto-Locate exactly where the Taluka Total Columns are
        taluka_cols = {}
        for r_idx in range(0, 4):  # Scan the first 4 rows to find 'TALUKA'
            for c_idx, val in enumerate(df_monthly.iloc[r_idx]):
                val_str = str(val).upper().replace('\n', ' ').strip()
                # Ignore District Total, just grab specific Talukas
                if 'TALUKA' in val_str and 'TOTAL' not in val_str and c_idx > 1:
                    t_name = val_str.replace('TALUKA', '').strip()
                    if t_name not in taluka_cols:
                        taluka_cols[t_name] = c_idx
                        
        # 🚀 ALGORITHM: Auto-Extract Clean Metrics (Column 1)
        clean_metrics = []
        for r_idx in range(3, len(df_monthly)):
            metric_val = str(df_monthly.iloc[r_idx, 1]).strip()
            if len(metric_val) > 5 and metric_val not in clean_metrics:
                clean_metrics.append(metric_val)
                    
        with col2:
            if clean_metrics:
                selected_metric = st.selectbox("🎯 Select a Performance Metric:", clean_metrics)
            else:
                selected_metric = None
                
        if selected_metric and taluka_cols:
            st.write("---")
            st.write(f"### Comparative Analysis: {selected_metric}")
            
            # Find the exact row for this metric
            metric_data = []
            for r_idx in range(3, len(df_monthly)):
                if str(df_monthly.iloc[r_idx, 1]).strip() == selected_metric:
                    for taluka, col_idx in taluka_cols.items():
                        raw_val = df_monthly.iloc[r_idx, col_idx]
                        val = pd.to_numeric(raw_val, errors='coerce')
                        metric_data.append({'Taluka': taluka, 'Value': 0 if pd.isna(val) else val})
                    break # Stop once found
                    
            chart_df = pd.DataFrame(metric_data)
            
            if not chart_df.empty:
                c1, c2 = st.columns([2, 1])
                with c1:
                    fig = px.bar(chart_df, x='Taluka', y='Value', color='Taluka', 
                                 text_auto=True, title=f"Metric Volume by Taluka ({selected_month})")
                    fig.update_layout(showlegend=False, plot_bgcolor="rgba(0,0,0,0)")
                    st.plotly_chart(fig, use_container_width=True)
                with c2:
                    st.dataframe(chart_df.style.background_gradient(cmap='Greens'), hide_index=True, use_container_width=True)

        with st.expander("👀 View Raw Excel Data Sheet"):
            st.dataframe(df_monthly, use_container_width=True, hide_index=True)

# -----------------------------------------
# MODULE 4: NEW CASE REGISTRATION (LIVE 2026-27)
# -----------------------------------------
elif menu == "➕ 4. New Case Registration":
    st.markdown('<p class="big-font">➕ Register New Birth Defect Case</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-font">Data entered here will be saved securely to the 2026-27 Live Database.</p>', unsafe_allow_html=True)
    
    # We use a standard layout (not st.form) so the dynamic "Other" box pops up instantly
    c1, c2 = st.columns(2)
    
    with c1:
        st.write("### 👤 Child Demographics")
        taluka = st.selectbox("🌍 Taluka", ["Junagadh", "Vanthali", "Manavadar", "Keshod", "Mangrol", "Maliya", "Mendarada", "Visavadar", "Bhesan"])
        disease = st.selectbox("🦠 Detected Condition (4D)", ["Congenital Heart Disease (CHD)", "Cleft Lip / Palate", "Club Foot", "Congenital Deafness", "Congenital Cataract", "Other Birth Defects"])
        child_name = st.text_input("📝 Child's Full Name")
        gender = st.selectbox("⚧️ Gender", ["Male", "Female"])
        dob = st.date_input("🎂 Date of Birth", min_value=datetime.date(2008, 1, 1), max_value=datetime.date.today())
        contact = st.text_input("📱 Guardian Contact Number", max_chars=10)
        
    with c2:
        st.write("### 🏥 Clinical & Referral Details")
        screening_date = st.date_input("🗓️ Date of Screening", value=datetime.date.today())
        team_num = st.text_input("🚑 Team Number (e.g., 1240315)")
        institution = st.selectbox("🏫 Institution Type", ["AWC (Anganwadi)", "School", "Delivery Point / PHC"])
        
        # Dynamic Referral Logic
        referral_base = st.selectbox("🏥 Referral Location", [
            "DEIC", "SDH", "U.N. MEHTA", "AHMEDABAD CIVIL", "RAJKOT CIVIL", 
            "OTHER PRIVATE HOSPITAL", "OTHER TRUST HOSPITAL", "OTHER NGO", "OTHER (Type Manually)"
        ])
        
        if "OTHER" in referral_base:
            referral_exact = st.text_input("⚠️ Please specify the exact Hospital/NGO Name:")
            final_referral = f"{referral_base} - {referral_exact}"
        else:
            final_referral = referral_base
            
        status = st.selectbox("🚦 Intervention Status", ["PENDING", "WAITING FOR APPROVAL", "ON TREATMENT", "COMPLETED", "REFUSAL", "MIGRATION", "DEATH"])
        follow_up = st.date_input("⏰ Next Follow-Up Date")

    st.write("### 📸 Clinical Evidence")
    photo_file = st.file_uploader("Upload Child's Photo (JPG/PNG)", type=['jpg', 'jpeg', 'png'])

    st.markdown("---")
    
    if st.button("🚀 Submit to Live Database", use_container_width=True, type="primary"):
        if child_name.strip() == "" or contact.strip() == "":
            st.error("⚠️ Child Name and Contact Number are required!")
        else:
            with st.spinner("Encrypting and uploading data to Google Cloud..."):
                try:
                    # 1. Upload Photo to Drive
                    photo_url = upload_photo_to_drive(photo_file, child_name, disease)
                    
                    # 2. Prepare Data Row
                    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    new_row = [
                        timestamp, taluka, disease, child_name, gender, 
                        str(dob), contact, str(screening_date), team_num, 
                        institution, final_referral, status, str(follow_up), photo_url
                    ]
                    
                    # 3. Push to Google Sheets
                    sheet = client.open("NEW BIRTH DEFECT TOTAL 2025-26 for app")
                    ws = sheet.worksheet("APP_LIVE_REGISTRATIONS")
                    ws.append_row(new_row)
                    
                    st.success(f"✅ Successfully registered {child_name} into the 2026-27 Database!")
                    st.balloons()
                    
                except Exception as e:
                    st.error(f"❌ Database Error: {e}")

# -----------------------------------------
# MODULE 5 Placeholder
# -----------------------------------------
elif menu == "🎯 5. Live Cycle Analytics (Coming Soon)":
    st.markdown('<p class="big-font">🎯 Live Cycle Analytics (2026-27)</p>', unsafe_allow_html=True)
    st.info("This module is currently being built! It will read exclusively from the new 'APP_LIVE_REGISTRATIONS' sheet.")
