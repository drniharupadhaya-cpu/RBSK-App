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
    .patient-card {background-color: #f1f5f9; padding: 15px; border-radius: 10px; border: 1px solid #cbd5e1;}
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
# PHOTO ENGINE (RESIZE & BASE64)
# -----------------------------------------
def process_photo_to_string(uploaded_file):
    if uploaded_file is None:
        return "No Photo"
    try:
        img = Image.open(uploaded_file)
        img.thumbnail((400, 400)) 
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=75)
        img_str = base64.b64encode(buffer.getvalue()).decode()
        return f"data:image/jpeg;base64,{img_str}"
    except:
        return "Error Processing Photo"

# -----------------------------------------
# DATA LOADING ENGINE
# -----------------------------------------
@st.cache_data(ttl=600)
def load_historic_data():
    try:
        sheet = client.open("NEW BIRTH DEFECT TOTAL 2025-26 for app")
        conditions = {"CHD": "CHD", "CLCP": "CLCP", "CLUB FOOT": "CLUB FOOT ", "DEAFNESS": "DEAFNESS ", "CATARACT": "CATARACT ", "OTHER": "OTHER BIR"}
        master_list = []
        for c_name, tab in conditions.items():
            try:
                df = pd.DataFrame(sheet.worksheet(tab).get_all_values())
                if df.empty: continue
                # Basic cleaning logic for historic data
                df.columns = df.iloc[0]
                df = df[1:]
                for _, row in df.iterrows():
                    master_list.append({'Taluka': str(row.iloc[0]), 'Disease': c_name, 'Child Name': str(row.iloc[2])})
            except: pass
        return pd.DataFrame(master_list)
    except: return pd.DataFrame()

@st.cache_data(ttl=10) # Fresh data for Live Module
def load_live_registrations():
    try:
        sheet = client.open("NEW BIRTH DEFECT TOTAL 2025-26 for app")
        ws = sheet.worksheet("APP_LIVE_REGISTRATIONS")
        data = ws.get_all_values()
        if len(data) < 2: return pd.DataFrame()
        df = pd.DataFrame(data[1:], columns=data[0])
        return df
    except: return pd.DataFrame()

# -----------------------------------------
# SIDEBAR
# -----------------------------------------
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/f/fe/Seal_of_Gujarat.svg/1200px-Seal_of_Gujarat.svg.png", width=100)
st.sidebar.title("Command Center")
menu = st.sidebar.radio("Analytical Modules:", [
    "--- 🚀 LIVE: 2026-27 CYCLE ---",
    "🎯 5. Live Cycle Analytics",
    "➕ 4. New Case Registration",
    "--- 📁 ARCHIVE: 2025-26 ---",
    "📊 1. District Burden Analytics", 
    "🚨 2. Triage & Child Search"
])

# -----------------------------------------
# MODULE 5: LIVE CYCLE ANALYTICS (NEW!)
# -----------------------------------------
if menu == "🎯 5. Live Cycle Analytics":
    st.markdown('<p class="big-font">🎯 Live Cycle Analytics (2026-27)</p>', unsafe_allow_html=True)
    df_live = load_live_registrations()
    
    if df_live.empty:
        st.info("No cases registered in the 2026-27 cycle yet. Go to Module 4 to add your first case!")
    else:
        # KPI ROW
        total = len(df_live)
        completed = len(df_live[df_live['Intervention Status'] == 'COMPLETED'])
        pending = total - completed
        
        k1, k2, k3 = st.columns(3)
        with k1: st.markdown(f'<div class="kpi-card" style="border-left-color: #3B82F6;"><div class="kpi-title">Total 2026-27 Cases</div><div class="kpi-value">{total}</div></div>', unsafe_allow_html=True)
        with k2: st.markdown(f'<div class="kpi-card" style="border-left-color: #10B981;"><div class="kpi-title">Interventions Completed</div><div class="kpi-value">{completed}</div></div>', unsafe_allow_html=True)
        with k3: st.markdown(f'<div class="kpi-card" style="border-left-color: #EF4444;"><div class="kpi-title">Pending / Ongoing</div><div class="kpi-value">{pending}</div></div>', unsafe_allow_html=True)
        
        st.write("---")
        
        # CHARTS
        c1, c2 = st.columns(2)
        with c1:
            fig1 = px.pie(df_live, names='Intervention Status', title="Status Distribution", hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig1, use_container_width=True)
        with c2:
            fig2 = px.bar(df_live['Taluka'].value_counts().reset_index(), x='Taluka', y='count', title="Cases by Taluka", color='Taluka')
            st.plotly_chart(fig2, use_container_width=True)

        st.write("### 🔍 Child Profile Viewer")
        search_child = st.selectbox("Select a Child to view Digital Profile:", ["Select Child"] + list(df_live['Child Name'].unique()))
        
        if search_child != "Select Child":
            child_data = df_live[df_live['Child Name'] == search_child].iloc[0]
            
            p_col1, p_col2 = st.columns([1, 2])
            with p_col1:
                photo_str = child_data['Photo Link']
                if photo_str.startswith("data:image"):
                    st.image(photo_str, caption=f"Photo: {search_child}", use_container_width=True)
                else:
                    st.warning("No photo available for this record.")
            
            with p_col2:
                st.markdown(f"""
                <div class="patient-card">
                    <h4>{child_data['Child Name']} ({child_data['Gender']})</h4>
                    <p><b>Condition:</b> {child_data['Disease']}</p>
                    <p><b>Taluka:</b> {child_data['Taluka']} | <b>DOB:</b> {child_data['DOB']}</p>
                    <p><b>Referral:</b> {child_data['Referral Location']}</p>
                    <p><b>Intervention Status:</b> {child_data['Intervention Status']}</p>
                    <p><b>Next Follow-up:</b> {child_data['Follow-Up Date']}</p>
                    <p><b>Guardian Contact:</b> {child_data['Contact']}</p>
                </div>
                """, unsafe_allow_html=True)

# -----------------------------------------
# MODULE 4: REGISTRATION
# -----------------------------------------
elif menu == "➕ 4. New Case Registration":
    st.markdown('<p class="big-font">➕ Register New Birth Defect Case (2026-27)</p>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        taluka = st.selectbox("🌍 Taluka", ["Junagadh", "Vanthali", "Manavadar", "Keshod", "Mangrol", "Maliya", "Mendarada", "Visavadar", "Bhesan"])
        disease = st.selectbox("🦠 Detected Condition", ["Congenital Heart Disease (CHD)", "Cleft Lip / Palate", "Club Foot", "Congenital Deafness", "Congenital Cataract", "Microcephaly", "Macrocephaly", "Congenital Ear Problems", "Neck and Face Defects", "Congenital Eye Problems", "ROP", "DOWN'S SYNDROME", "THALESSEMIA", "CANCER"])
        child_name = st.text_input("📝 Child's Full Name")
        gender = st.selectbox("⚧️ Gender", ["Male", "Female"])
        dob = st.date_input("🎂 Date of Birth", min_value=datetime.date(2008, 1, 1))
        contact = st.text_input("📱 Guardian Contact Number")
    with c2:
        screening_date = st.date_input("🗓️ Screening Date", value=datetime.date.today())
        team_num = st.text_input("🚑 Team Number")
        inst = st.selectbox("🏫 Institution", ["AWC", "School", "PHC"])
        ref = st.selectbox("🏥 Referral", ["DEIC", "SDH", "U.N. MEHTA", "AHMEDABAD CIVIL", "RAJKOT CIVIL", "OTHER"])
        status = st.selectbox("🚦 Status", ["PENDING", "WAITING FOR APPROVAL", "ON TREATMENT", "COMPLETED"])
        f_up = st.date_input("⏰ Follow-up Date")
    
    photo_file = st.file_uploader("Upload Photo", type=['jpg', 'png', 'jpeg'])
    
    if st.button("🚀 Submit Registration"):
        if child_name and contact:
            with st.spinner("Processing..."):
                photo_data = process_photo_to_string(photo_file)
                row = [str(datetime.datetime.now()), taluka, disease, child_name, gender, str(dob), contact, str(screening_date), team_num, inst, ref, status, str(f_up), photo_data]
                ws = client.open("NEW BIRTH DEFECT TOTAL 2025-26 for app").worksheet("APP_LIVE_REGISTRATIONS")
                ws.append_row(row)
                st.success("Registration Successful!")
                st.balloons()

# -----------------------------------------
# HISTORIC MODULES
# -----------------------------------------
elif menu == "📊 1. District Burden Analytics":
    df_h = load_historic_data()
    st.markdown('<p class="big-font">District Burden Analytics (Archive)</p>', unsafe_allow_html=True)
    if not df_h.empty:
        st.dataframe(df_h, use_container_width=True)

elif menu == "🚨 2. Triage & Child Search":
    df_h = load_historic_data()
    st.markdown('<p class="big-font">Historic Search Engine</p>', unsafe_allow_html=True)
    if not df_h.empty:
        search = st.text_input("Search Name:")
        st.dataframe(df_h[df_h['Child Name'].str.contains(search, case=False, na=False)])
