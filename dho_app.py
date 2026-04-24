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
# LOGIN SYSTEM 
# -----------------------------------------
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['user_role'] = None
    st.session_state['taluka_name'] = None

def check_login(user, pwd):
    talukas = ["Junagadh", "Vanthali", "Manavadar", "Keshod", "Mangrol", "Maliya", "Mendarada", "Visavadar", "Bhesan"]
    if user == "DHO_Junagadh" and pwd == "dho@2026":
        st.session_state['logged_in'], st.session_state['user_role'], st.session_state['taluka_name'] = True, "Admin", "District"
        return True
    elif user in talukas and pwd == "rbsk@2026":
        st.session_state['logged_in'], st.session_state['user_role'], st.session_state['taluka_name'] = True, "Taluka", user
        return True
    return False

if not st.session_state['logged_in']:
    st.markdown("<br><br>", unsafe_allow_html=True)
    c_l1, c_l2, c_l3 = st.columns([1, 2, 1])
    with c_l2:
        st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/f/fe/Seal_of_Gujarat.svg/1200px-Seal_of_Gujarat.svg.png", width=80)
        st.markdown('<p class="big-font">DHO RBSK Command Center Login</p>', unsafe_allow_html=True)
        u = st.text_input("Username (Taluka Name or Admin ID)")
        p = st.text_input("Password", type="password")
        if st.button("🔓 Login", use_container_width=True, type="primary"):
            if check_login(u, p): st.rerun()
            else: st.error("Access Denied.")
    st.stop()

# -----------------------------------------
# GOOGLE SHEETS CONNECTION
# -----------------------------------------
scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
raw_secret = st.secrets["gcp_service_account"]
skey = json.loads(raw_secret) if isinstance(raw_secret, str) else dict(raw_secret)
credentials = Credentials.from_service_account_info(skey, scopes=scopes)
client = gspread.authorize(credentials)

# -----------------------------------------
# PHOTO ENGINE
# -----------------------------------------
def process_photo_to_string(uploaded_file):
    if uploaded_file is None: return "No Photo"
    try:
        img = Image.open(uploaded_file)
        img.thumbnail((300, 300)) 
        if img.mode in ("RGBA", "P"): img = img.convert("RGB")
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=70) 
        return f"data:image/jpeg;base64,{base64.b64encode(buffer.getvalue()).decode()}"
    except Exception as e: return f"Error: {e}"

# -----------------------------------------
# DATA MINING ENGINE
# -----------------------------------------
@st.cache_data(ttl=600)
def load_and_mine_defect_data():
    try:
        sheet = client.open("NEW BIRTH DEFECT TOTAL 2025-26 for app")
        conditions = {"Congenital Heart Disease (CHD)": "CHD", "Cleft Lip / Palate": "CLCP", "Club Foot": "CLUB FOOT ", "Congenital Deafness": "DEAFNESS ", "Congenital Cataract": "CATARACT ", "Other Birth Defects": "OTHER BIR"}
        master_list = []
        for c_name, tab_name in conditions.items():
            try:
                ws = sheet.worksheet(tab_name)
                df = pd.DataFrame(ws.get_all_values())
                if df.empty: continue
                header_idx = 0
                for i, row in df.iterrows():
                    if 'NAME' in str(row.values).upper() or 'નામ' in str(row.values):
                        header_idx = i; break
                df.columns = [str(c).strip() for c in df.iloc[header_idx]]
                df = df.iloc[header_idx+1:].copy()
                col_t = next((c for c in df.columns if any(k in c.upper() for k in ['TALUKA', 'તાલુકા'])), None)
                col_n = next((c for c in df.columns if any(k in c.upper() for k in ['NAME', 'નામ'])), None)
                if col_t and col_n:
                    df[col_t] = df[col_t].replace('', pd.NA).ffill()
                    for _, row in df.iterrows():
                        t_raw = str(row[col_t]).strip()
                        n_val = str(row[col_n]).strip()
                        t_val = ''.join([i for i in t_raw if not i.isdigit()]).replace('.', '').strip()
                        if t_val.upper() in ['', 'NAN', 'TOTAL'] or len(n_val) < 2: continue
                        master_list.append({'Taluka': t_val, 'Disease': c_name, 'Child Name': n_val})
            except: pass
        return pd.DataFrame(master_list)
    except Exception as e: return pd.DataFrame()

@st.cache_data(ttl=600)
def load_monthly_covered_data(month_tab):
    try:
        ws = client.open("JUNAGADH DISTRICT COVERED 2025-26").worksheet(month_tab)
        return pd.DataFrame(ws.get_all_values())
    except: return pd.DataFrame()

@st.cache_data(ttl=5)
def load_live_app_data():
    try:
        ws = client.open("NEW BIRTH DEFECT TOTAL 2025-26 for app").worksheet("APP_LIVE_REGISTRATIONS")
        data = ws.get_all_values()
        if len(data) < 1: return pd.DataFrame()
        df = pd.DataFrame(data)
        df.columns = ["Timestamp", "Taluka", "Condition", "Child Name", "Gender", "DOB", "Contact", "Screening Date", "Team Number", "Institution", "Referral Location", "Status", "Follow-up", "PhotoData"]
        return df
    except: return pd.DataFrame()

# Initial Data Load
df_master = load_and_mine_defect_data()

# -----------------------------------------
# SIDEBAR
# -----------------------------------------
st.sidebar.markdown(f"👤 **User:** {st.session_state['taluka_name']}")
if st.sidebar.button("Logout"):
    st.session_state['logged_in'] = False
    st.rerun()

st.sidebar.markdown("---")
menu = st.sidebar.radio("Command Center Modules:", [
    "--- 📁 ARCHIVE: 2025-26 ---",
    "📊 1. District Burden Analytics", 
    "🚨 2. Triage & Child Search", 
    "📈 3. Deep Monthly Data Mining",
    "--- 🚀 LIVE: 2026-27 CYCLE ---",
    "➕ 4. New Case Registration",
    "🎯 5. Live Cycle Analytics"
])

# -----------------------------------------
# MODULE 1 & 2 ARCHIVE
# -----------------------------------------
if menu == "📊 1. District Burden Analytics":
    st.markdown('<p class="big-font">District Archive Analytics</p>', unsafe_allow_html=True)
    if not df_master.empty:
        f1, f2 = st.columns(2)
        with f1:
            all_t = sorted(list(df_master['Taluka'].unique()))
            def_t = [st.session_state['taluka_name']] if st.session_state['user_role'] == "Taluka" and st.session_state['taluka_name'] in all_t else all_t
            sel_t = st.multiselect("Talukas:", all_t, default=def_t)
        with f2:
            all_d = sorted(list(df_master['Disease'].unique()))
            sel_d = st.multiselect("Diseases:", all_d, default=all_d)
        
        fil_df = df_master[(df_master['Taluka'].isin(sel_t)) & (df_master['Disease'].isin(sel_d))]
        st.write("### 🏥 Total Burden")
        c_counts = fil_df['Disease'].value_counts()
        cols = st.columns(4)
        for i, (disease, val) in enumerate(c_counts.items()):
            if i > 3: break
            with cols[i]: st.markdown(f'<div class="kpi-card"><div class="kpi-title">{disease}</div><div class="kpi-value">{val}</div></div>', unsafe_allow_html=True)
        st.dataframe(pd.crosstab(fil_df['Taluka'], fil_df['Disease'], margins=True), use_container_width=True)

elif menu == "🚨 2. Triage & Child Search":
    st.markdown('<p class="big-font">Master Search Engine</p>', unsafe_allow_html=True)
    if not df_master.empty:
        col1, col2, col3 = st.columns(3)
        with col1: f_t = st.selectbox("Taluka:", ["All"] + sorted(list(df_master['Taluka'].unique())))
        with col2: f_d = st.selectbox("Disease:", ["All"] + list(df_master['Disease'].unique()))
        with col3: s_n = st.text_input("Name:")
        fdf = df_master.copy()
        if f_t != "All": fdf = fdf[fdf['Taluka'] == f_t]
        if f_d != "All": fdf = fdf[fdf['Disease'] == f_d]
        if s_n: fdf = fdf[fdf['Child Name'].str.contains(s_n, case=False, na=False)]
        st.dataframe(fdf, use_container_width=True, hide_index=True)

elif menu == "📈 3. Deep Monthly Data Mining":
    st.markdown('<p class="big-font">Deep Monthly Performance Mining</p>', unsafe_allow_html=True)
    months = ["MAR 26", "FEB 26", "JAN 26", "DEC 25", "NOV 25", "OCT 25", "SEP 25", "AUG 25", "JUL 25", "JUN 25", "MAY 25", "APR 25"]
    c1, c2 = st.columns(2)
    with c1: sel_m = st.selectbox("Month:", months, index=10)
    df_m = load_monthly_covered_data(sel_m)
    if not df_m.empty:
        # Find Taluka columns automatically
        t_cols = {str(df_m.iloc[0, i]).strip().upper().replace('TALUKA','').strip(): i for i in range(2, len(df_m.columns)) if 'TALUKA' in str(df_m.iloc[0,i]).upper()}
        metrics = [str(df_m.iloc[r, 1]).strip() for r in range(3, len(df_m)) if len(str(df_m.iloc[r,1]).strip()) > 5]
        with c2: sel_met = st.selectbox("Metric:", metrics)
        
        st.write("### 📍 Performance Filter")
        all_found_tals = list(t_cols.keys())
        def_t = [st.session_state['taluka_name'].upper()] if st.session_state['user_role'] == "Taluka" and st.session_state['taluka_name'].upper() in all_found_tals else all_found_tals
        sel_tals = st.multiselect("Compare Talukas:", all_found_tals, default=def_t)
        
        res = []
        for r in range(3, len(df_m)):
            if str(df_m.iloc[r,1]).strip() == sel_met:
                for t, idx in t_cols.items():
                    if t in sel_tals: res.append({'Taluka': t, 'Val': pd.to_numeric(df_m.iloc[r, idx], errors='coerce')})
        if res: st.plotly_chart(px.bar(pd.DataFrame(res), x='Taluka', y='Val', color='Taluka', text_auto=True), use_container_width=True)

# -----------------------------------------
# MODULE 4: NEW REGISTRATION (ROLE LOCKED)
# -----------------------------------------
elif menu == "➕ 4. New Case Registration":
    st.markdown('<p class="big-font">➕ New Registration (2026-27)</p>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        t_list = ["Junagadh", "Vanthali", "Manavadar", "Keshod", "Mangrol", "Maliya", "Mendarada", "Visavadar", "Bhesan"]
        if st.session_state['user_role'] == "Taluka": t_sel = st.selectbox("🌍 Taluka", [st.session_state['taluka_name']], disabled=True)
        else: t_sel = st.selectbox("🌍 Taluka", t_list)
        dis = st.selectbox("🦠 Condition", ["CHD", "Cleft Lip", "Club Foot", "Deafness", "Cataract", "Microcephaly", "Macrocephaly", "Ear Defects", "Neck Defects", "Eye Defects", "ROP", "DOWN'S", "THALESSEMIA", "CANCER"])
        nam = st.text_input("📝 Full Name")
        gen = st.selectbox("⚧️ Gender", ["Male", "Female"])
        dob = st.date_input("🎂 DOB")
        mob = st.text_input("📱 Contact", max_chars=10)
    with c2:
        scr = st.date_input("🗓️ Screening Date")
        tm = st.text_input("🚑 Team #")
        ins = st.selectbox("🏫 Inst.", ["AWC", "School", "PHC"])
        ref = st.selectbox("🏥 Referral", ["DEIC", "SDH", "U.N. MEHTA", "AHMEDABAD CIVIL", "RAJKOT CIVIL", "OTHER"])
        sta = st.selectbox("🚦 Status", ["PENDING", "ON TREATMENT", "COMPLETED", "DEATH"])
        fup = st.date_input("⏰ Follow-up")
    p_f = st.file_uploader("📸 Photo", type=['jpg', 'png', 'jpeg'])
    if st.button("🚀 Submit"):
        if nam and mob:
            p_str = process_photo_to_string(p_f)
            row = [str(datetime.datetime.now()), t_sel, dis, nam, gen, str(dob), mob, str(scr), tm, ins, ref, sta, str(fup), p_str]
            client.open("NEW BIRTH DEFECT TOTAL 2025-26 for app").worksheet("APP_LIVE_REGISTRATIONS").append_row(row)
            st.success("Registration Successful!"); st.balloons()

# -----------------------------------------
# MODULE 5: LIVE ANALYTICS (WITH FILTERS & LEDGER)
# -----------------------------------------
elif menu == "🎯 5. Live Cycle Analytics":
    st.markdown('<p class="big-font">🎯 Live Analytics (2026-27)</p>', unsafe_allow_html=True)
    df_l = load_live_app_data()
    if df_l.empty: st.warning("Database empty.")
    else:
        # Filters
        f1, f2 = st.columns(2)
        with f1:
            l_t = sorted(list(df_l['Taluka'].unique()))
            def_l_idx = l_t.index(st.session_state['taluka_name']) if st.session_state['user_role'] == "Taluka" and st.session_state['taluka_name'] in l_t else 0
            sel_lt = st.selectbox("Dashboard Taluka:", ["All"] + l_t, index=def_l_idx if st.session_state['user_role'] == "Taluka" else 0)
        with f2: sel_lc = st.selectbox("Dashboard Condition:", ["All"] + sorted(list(df_l['Condition'].unique())))
        
        ldf = df_l.copy()
        if sel_lt != "All": ldf = ldf[ldf['Taluka'] == sel_lt]
        if sel_lc != "All": ldf = ldf[ldf['Condition'] == sel_lc]
        
        k1, k2, k3 = st.columns(3)
        with k1: st.markdown(f'<div class="kpi-card"><div class="kpi-title">Registered</div><div class="kpi-value">{len(ldf)}</div></div>', unsafe_allow_html=True)
        with k2: st.markdown(f'<div class="kpi-card"><div class="kpi-title">Completed</div><div class="kpi-value">{len(ldf[ldf["Status"]=="COMPLETED"])}</div></div>', unsafe_allow_html=True)
        with k3: st.markdown(f'<div class="kpi-card"><div class="kpi-title">Pending</div><div class="kpi-value">{len(ldf[ldf["Status"]!="COMPLETED"])}</div></div>', unsafe_allow_html=True)

        st.write("### 📜 Live Ledger")
        st.dataframe(ldf.drop(columns=['PhotoData']), use_container_width=True, hide_index=True)

        st.write("### 🔍 Child Profile Viewer")
        sel_c = st.selectbox("Select Child (Filtered):", ["--Select--"] + sorted(ldf['Child Name'].unique()))
        if sel_c != "--Select--":
            r = ldf[ldf['Child Name'] == sel_c].iloc[0]
            p1, p2 = st.columns([1, 2])
            with p1: 
                if str(r['PhotoData']).startswith("data:image"): st.image(r['PhotoData'], use_container_width=True)
                else: st.info("No Photo.")
            with p2: st.markdown(f'<div class="patient-card"><b>Condition:</b> {r["Condition"]}<br><b>Status:</b> {r["Status"]}<br><b>Taluka:</b> {r["Taluka"]}</div>', unsafe_allow_html=True)
