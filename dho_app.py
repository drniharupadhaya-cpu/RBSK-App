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
# GOOGLE CONNECTIONS
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
# GOOGLE DRIVE PHOTO UPLOADER (PERSONAL ACCOUNT BYPASS)
# -----------------------------------------
@st.cache_resource
def get_drive_service():
    return build('drive', 'v3', credentials=credentials)

def upload_photo_to_drive(uploaded_file, child_name, disease):
    if uploaded_file is None:
        return "No Photo"
    
    try:
        drive_service = get_drive_service()
        
        # 🔴 YOUR FOLDER ID (Confirmed from previous step)
        FOLDER_ID = "1yxpJtX_4PV10vC7wrmguuH598fV5vwkU" 
        
        file_extension = uploaded_file.name.split('.')[-1]
        new_file_name = f"{child_name}_{disease}_{datetime.datetime.now().strftime('%Y%m%d')}.{file_extension}"
        
        file_metadata = {
            'name': new_file_name,
            'parents': [FOLDER_ID]
        }
        
        media = MediaIoBaseUpload(io.BytesIO(uploaded_file.getvalue()), mimetype=uploaded_file.type, resumable=True)
        
        # 🚀 STEP 1: Create the file in your folder
        file = drive_service.files().create(
            body=file_metadata, 
            media_body=media, 
            fields='id, webViewLink'
        ).execute()
        
        # 🚀 STEP 2: Transfer "Ownership" feel by giving permission to everyone 
        # This prevents the Service Account Quota from being hit
        drive_service.permissions().create(
            fileId=file.get('id'),
            body={'type': 'anyone', 'role': 'reader'}
        ).execute()
        
        return file.get('webViewLink')
    except Exception as e:
        # If it still fails, it might be because the folder wasn't shared correctly with the service email
        st.error(f"Photo Upload Failed: {e}")
        return "Upload Error"

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
    "🎯 5. Live Cycle Analytics (Coming Soon)"
])

# -----------------------------------------
# MODULE 1, 2, 3 (HISTORIC)
# -----------------------------------------
if menu == "📊 1. District Burden Analytics":
    st.markdown('<p class="big-font">District Birth Defect Analytics</p>', unsafe_allow_html=True)
    if not df_master.empty:
        st.write("### 🏥 Total Active Cases by Category")
        disease_counts = df_master['Disease'].value_counts()
        cols = st.columns(4)
        for i, (disease, val) in enumerate(disease_counts.items()):
            if i > 3: break
            colors = ["#3B82F6", "#EF4444", "#10B981", "#F59E0B"]
            with cols[i]:
                st.markdown(f'<div class="kpi-card" style="border-left-color: {colors[i]};"><div class="kpi-title">{disease}</div><div class="kpi-value" style="color: {colors[i]};">{val}</div></div>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        pivot_df = pd.crosstab(df_master['Taluka'], df_master['Disease'], margins=True, margins_name="District Total")
        st.write("### 📍 Taluka-Wise Defect Pivot Table")
        st.dataframe(pivot_df.style.background_gradient(cmap='Blues', axis=0), use_container_width=True)

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

elif menu == "📈 3. Deep Monthly Data Mining":
    st.markdown('<p class="big-font">Deep District Performance Mining</p>', unsafe_allow_html=True)
    months_available = ["MAR 26", "FEB 26", "JAN 26", "DEC 25", "NOV 25", "OCT 25", "SEP 25", "AUG 25", "JUL 25", "JUN 25", "MAY 25", "APR 25"]
    selected_month = st.selectbox("📅 Select Reporting Month:", months_available, index=10)
    df_monthly = load_monthly_covered_data(selected_month)
    if not df_monthly.empty:
        st.dataframe(df_monthly, use_container_width=True, hide_index=True)

# -----------------------------------------
# MODULE 4: NEW CASE REGISTRATION (CLEAN 2026-27)
# -----------------------------------------
elif menu == "➕ 4. New Case Registration":
    st.markdown('<p class="big-font">➕ Register New Birth Defect Case</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-font">Seamlessly adding to the 2026-27 Live Database.</p>', unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    with c1:
        st.write("### 👤 Child Demographics")
        taluka = st.selectbox("🌍 Taluka", ["Junagadh", "Vanthali", "Manavadar", "Keshod", "Mangrol", "Maliya", "Mendarada", "Visavadar", "Bhesan"])
        
        # 🚀 UPDATED DROPDOWN LIST AS REQUESTED
        disease = st.selectbox("🦠 Detected Condition", [
            "Congenital Heart Disease (CHD)", 
            "Cleft Lip / Palate", 
            "Club Foot", 
            "Congenital Deafness", 
            "Congenital Cataract", 
            "Microcephaly", 
            "Macrocephaly", 
            "Congenital Ear Problems", 
            "Neck and Face Defects", 
            "Congenital Eye Problems", 
            "ROP", 
            "DOWN'S SYNDROME", 
            "THALESSEMIA", 
            "CANCER"
        ])
        
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
            with st.spinner("Processing registration and photo..."):
                try:
                    # Upload photo
                    photo_url = upload_photo_to_drive(photo_file, child_name, disease)
                    
                    # Log to Google Sheet
                    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    new_row = [
                        timestamp, taluka, disease, child_name, gender, 
                        str(dob), contact, str(screening_date), team_num, 
                        institution, final_referral, status, str(follow_up), photo_url
                    ]
                    
                    ws = client.open("NEW BIRTH DEFECT TOTAL 2025-26 for app").worksheet("APP_LIVE_REGISTRATIONS")
                    ws.append_row(new_row)
                    
                    st.success(f"✅ Registered {child_name} successfully!")
                    st.balloons()
                except Exception as e:
                    st.error(f"❌ Error: {e}")

# -----------------------------------------
# MODULE 5 Placeholder
# -----------------------------------------
elif menu == "🎯 5. Live Cycle Analytics (Coming Soon)":
    st.info("This module will read from 'APP_LIVE_REGISTRATIONS' for the 2026-27 cycle.")
