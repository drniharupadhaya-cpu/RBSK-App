import streamlit as st
import pandas as pd
from datetime import date, datetime
import gspread
import json
from fpdf import FPDF
import tempfile
import os
import time
import datetime
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
import plotly.express as px
import numpy as np # Added globally for maximum speed

# ==========================================
# MASTER DATA ENGINE (Optimized for Speed & Multiple Users)
# ==========================================
@st.cache_data(ttl=600)
def get_daily_logs():
    """Fetches daily screenings ONCE and shares it with Modules 1, 3, and 12."""
    try:
        aw = pd.DataFrame(spreadsheet.worksheet("daily_screenings_aw").get_all_records())
        sch = pd.DataFrame(spreadsheet.worksheet("daily_screenings_schools").get_all_records())
        
        if not aw.empty: aw['Location_Type'] = 'Anganwadi'
        if not sch.empty: sch['Location_Type'] = 'School'
        
        return aw, sch, pd.concat([aw, sch], ignore_index=True)
    except:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

def get_age(dob_str):
    try:
        birth = pd.to_datetime(dob_str, dayfirst=True)
        today = datetime.date.today()
        age_years = today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
        
        if age_years < 1:
            months = (today.year - birth.year) * 12 + today.month - birth.month
            return f"{months} Months"
        return f"{age_years} Years"
    except:
        return "N/A"

# ==========================================
# UI DESIGN STUDIO & SECURITY
# ==========================================
def render_header(title, subtitle, icon, bg_color):
    """Creates a beautiful, colorful graphic banner for each module."""
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, {bg_color} 0%, #2b323c 100%); 
                padding: 25px; 
                border-radius: 15px; 
                box-shadow: 0 4px 6px rgba(0,0,0,0.1); 
                margin-bottom: 25px;
                border-left: 8px solid white;">
        <h1 style="color: white; margin: 0; font-size: 32px;">
            <span style="font-size: 40px; margin-right: 15px;">{icon}</span>{title}
        </h1>
        <p style="color: #e2e8f0; font-size: 18px; margin-top: 8px; margin-bottom: 0;">{subtitle}</p>
    </div>
    """, unsafe_allow_html=True)

def check_password():
    if "password_correct" not in st.session_state:
        st.markdown("<br><br>", unsafe_allow_html=True)
        render_header("RBSK Secure Access", "Please enter credentials to continue", "🔒", "#1e293b")
        
        pwd = st.text_input("Enter Password", type="password")
        if st.button("Login"):
            if pwd == st.secrets["password"]:
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("🚫 Incorrect Password.")
        return False
    return True

if not check_password():
    st.stop()

# ==========================================
# GLOBAL PDF ENGINE: OFFICIAL RBSK FORMAT
# ==========================================
def generate_refer_card(data):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    def draw_text(x, y, text, size=11, bold=False, color=colors.black):
        c.setFillColor(color)
        c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
        c.drawString(x, y, str(text))

    # Outer Frame
    c.setStrokeColor(colors.HexColor("#1e3a8a"))
    c.setLineWidth(3)
    c.roundRect(20, 20, width - 40, height - 40, 10, stroke=1, fill=0)
    c.setLineWidth(1)

    # Header
    c.setFillColor(colors.HexColor("#10b981"))
    c.roundRect(20, height - 80, width - 40, 60, 10, stroke=0, fill=1)
    c.rect(20, height - 80, width - 40, 30, stroke=0, fill=1) 
    
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width / 2.0, height - 45, "RBSK - REFERRAL CARD (NATIONAL CHILD HEALTH PROGRAM)")
    c.setFont("Helvetica", 11)
    c.drawCentredString(width / 2.0, height - 65, "District Panchayat, Junagadh - Health Branch")

    # Demographics
    start_y = height - 100
    c.setFillColor(colors.HexColor("#f8fafc"))
    c.setStrokeColor(colors.HexColor("#cbd5e1"))
    c.roundRect(30, start_y - 105, width - 60, 95, 6, stroke=1, fill=1)
    
    draw_text(40, start_y - 20, "📋 PATIENT DEMOGRAPHICS", 12, bold=True, color=colors.HexColor("#1e3a8a"))
    draw_text(40, start_y - 45, f"Child's Name: {data.get('Name', '')}", 12, bold=True)
    draw_text(350, start_y - 45, f"Gender: {data.get('Gender', '')}")
    draw_text(40, start_y - 70, f"Date of Birth: {data.get('DOB', '')}")
    draw_text(180, start_y - 70, f"Age: {data.get('Age', 'N/A')}")
    draw_text(350, start_y - 70, f"Contact: {data.get('Contact_Num', '')}")
    draw_text(40, start_y - 95, f"Father's Name: {data.get('Parent_Name', '')}")
    draw_text(350, start_y - 95, f"Mother's Name: {data.get('Mother', '')}")

    # Location
    loc_y = start_y - 120
    c.setFillColor(colors.HexColor("#f8fafc"))
    c.roundRect(30, loc_y - 75, width - 60, 65, 6, stroke=1, fill=1)
    
    draw_text(40, loc_y - 20, "🏫 LOCATION & INSTITUTION", 12, bold=True, color=colors.HexColor("#1e3a8a"))
    draw_text(40, loc_y - 45, f"Village / City: {data.get('Village', '')}")
    draw_text(350, loc_y - 45, "Taluka: VISAVADAR")
    draw_text(40, loc_y - 65, f"Institution: {data.get('Institution', '')}")
    draw_text(350, loc_y - 65, f"Status: {data.get('School_Status', '')}")

    # Clinical
    clin_y = loc_y - 90
    c.setFillColor(colors.HexColor("#fef2f2"))
    c.setStrokeColor(colors.HexColor("#fca5a5"))
    c.roundRect(30, clin_y - 125, width - 60, 115, 6, stroke=1, fill=1)
    
    draw_text(40, clin_y - 20, "🩺 CLINICAL SCREENING & REFERRAL", 12, bold=True, color=colors.HexColor("#b91c1c"))
    draw_text(40, clin_y - 45, f"Screening Date: {data.get('Date', '')}")
    draw_text(40, clin_y - 70, "Medical Condition Identified (4D):", 11, bold=True)
    draw_text(240, clin_y - 70, f"{data.get('Clinical_Findings', '')}", 12, color=colors.HexColor("#b91c1c"))
    draw_text(40, clin_y - 95, "Primary Treatment Given:")
    draw_text(240, clin_y - 95, f"{data.get('Treatment_Given', '')}")
    draw_text(40, clin_y - 115, "Referred To (Hospital):", 11, bold=True)
    draw_text(240, clin_y - 115, f"{data.get('Referred_To', '')}", 12, bold=True)

    # Stamp & Signature
    stamp_y = clin_y - 220
    stamp_x = 120
    
    c.setStrokeColor(colors.HexColor("#1e3a8a"))
    c.setLineWidth(2)
    c.circle(stamp_x, stamp_y, 45, stroke=1, fill=0)
    c.circle(stamp_x, stamp_y, 40, stroke=1, fill=0)
    
    c.setFillColor(colors.HexColor("#1e3a8a"))
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(stamp_x, stamp_y + 10, "RBSK MO")
    c.drawCentredString(stamp_x, stamp_y - 5, "VISAVADAR")
    c.setFont("Helvetica", 8)
    c.drawCentredString(stamp_x, stamp_y - 20, "Official Seal")
    
    sign_path = "sign.jpg"
    if os.path.exists(sign_path):
        c.drawImage(sign_path, 360, stamp_y - 10, width=90, height=60, preserveAspectRatio=True, mask='auto')
    else:
        draw_text(370, stamp_y + 10, "(Signature Image Missing)", 9, color=colors.red)

    c.setFillColor(colors.black)
    c.setStrokeColor(colors.black)
    c.setLineWidth(1)
    c.line(340, stamp_y - 15, 520, stamp_y - 15)
    
    draw_text(340, stamp_y - 30, f"Medical Officer: {data.get('MO_Name', '')}", 11, bold=True)
    draw_text(340, stamp_y - 45, "Mobile Health Team (MHT-1)")

    c.save()
    buffer.seek(0)
    return buffer.getvalue()

# ==========================================
# DATABASE CONNECTION (Zero-Lag Optimized)
# ==========================================
# 🚀 THE FIX: This keeps the Google Connection "awake" in the server's background for 30 minutes!
@st.cache_resource(ttl=1800)
def get_spreadsheet():
    creds_dict = json.loads(st.secrets["gcp_service_account"])
    client = gspread.service_account_from_dict(creds_dict)
    sheet_url = "https://docs.google.com/spreadsheets/d/1i5wAkI7k98E80qhHRe6xQOhF4Qj9Z0DH8wjPsQ7gRZc/edit?gid=2111634358#gid=2111634358"
    return client.open_by_url(sheet_url)

@st.cache_data(ttl=600)
def load_all_data():
    sheet = get_spreadsheet()
    def safe_load(tab_name, retries=3):
        for attempt in range(retries):
            try:
                df = pd.DataFrame(sheet.worksheet(tab_name).get_all_records()).astype(str)
                df.columns = df.columns.str.strip() 
                
                time.sleep(1.5)  # 🚦 Keeps Google from blocking us during initial boot!
                
                return df
            except Exception as e:
                error_msg = str(e)
                if '429' in error_msg or 'RESOURCE_EXHAUSTED' in error_msg:
                    if attempt < retries - 1:
                        time.sleep(5) 
                        continue 
                st.error(f"🚨 FAILED ON TAB '{tab_name}': {e}")
                return pd.DataFrame()

    df_4d = safe_load("4d_list")
    df_anemia = safe_load("ANEMIA")
    df_directory = safe_load("ALL SCHOOL DETAILS")
    df_aw_contacts = safe_load("aw_master_directory")
    df_staff = safe_load("master_staff_directory")
    df_aw_master = safe_load("aw new data")
    df_all_students = safe_load("1240315 ALL STUDENTS NAMES")
    df_q_perf = safe_load("Q_Performance")
    df_q_loc = safe_load("Q_Location_4D")
    df_q_demo = safe_load("Q_Demo_4D")
    df_hbnc = safe_load("hbnc_screenings") # 🚀 Added Module 5 to the fast-cache!

    return df_4d, df_anemia, df_directory, df_aw_contacts, df_staff, df_aw_master, df_all_students, df_q_perf, df_q_loc, df_q_demo, df_hbnc

try:
    spreadsheet = get_spreadsheet() 
    df_4d, df_anemia, df_directory, df_aw_contacts, df_staff, df_aw_master, df_all_students, df_q_perf, df_q_loc, df_q_demo, df_hbnc = load_all_data() 
    
    df_aw = df_aw_master
    df_students = df_all_students
    df_schools = df_directory
    
except Exception as e:
    if "429" in str(e) or "Quota exceeded" in str(e):
        st.error("🚦 Whoa there! Google is enforcing a speed limit. Please wait exactly 60 seconds and refresh the page!")
        st.stop()

# ==========================================
# 🌍 DISTRICT COMMAND: TEAM UNIFICATION ENGINE
# ==========================================
st.sidebar.header("🌍 District Command")

team_options = ["TEAM-1240315", "TEAM-1240309", "District Admin (All Teams)"]
selected_team = st.sidebar.selectbox("🏥 Select Active Team:", team_options)
st.sidebar.divider()

if selected_team != "District Admin (All Teams)":
    try:
        team_col_aw = [c for c in df_aw.columns if 'team' in str(c).strip().lower()][0]
        team_col_stu = [c for c in df_students.columns if 'team' in str(c).strip().lower()][0]
        team_col_sch = [c for c in df_schools.columns if 'team' in str(c).strip().lower()][0]

        df_aw = df_aw[df_aw[team_col_aw].astype(str).str.strip().str.upper() == selected_team]
        df_students = df_students[df_students[team_col_stu].astype(str).str.strip().str.upper() == selected_team]
        df_schools = df_schools[df_schools[team_col_sch].astype(str).str.strip().str.upper() == selected_team]
        
    except IndexError:
        st.sidebar.error("⚠️ Could not find the 'TEAM' column in one of the master sheets. Please check your Google Sheet headers!")

@st.cache_data(ttl=600)
def get_today_stats():
    try:
        today_str = str(datetime.date.today())
        aw_df, sch_df, _ = get_daily_logs()
        
        def count_today(df):
            if df.empty: return 0
            date_col = next((c for c in df.columns if 'date' in str(c).lower()), None)
            if not date_col: return 0
            return len(df[df[date_col].astype(str).str.contains(today_str)])
            
        return count_today(aw_df) + count_today(sch_df)
    except:
        return 0

# ==========================================
# SIDEBAR NAVIGATION
# ==========================================
st.sidebar.markdown("### 🏛️ RBSK Team Portal")
st.sidebar.write("Team: Visavadar MHT-1240315")
st.sidebar.divider()
st.sidebar.title("🩺 RBSK Menu")
st.sidebar.write("Dr. Workspace")

today_total = get_today_stats()

st.sidebar.markdown(f"""
<div style="background-color: #1e293b; padding: 15px; border-radius: 10px; border-left: 5px solid #10b981; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
    <p style="margin: 0; color: #94a3b8; font-size: 14px; text-transform: uppercase; letter-spacing: 1px;">📅 Screened Today</p>
    <h2 style="margin: 5px 0 0 0; color: #ffffff; font-size: 28px;">
        {today_total} <span style="font-size: 14px; color: #10b981; font-weight: normal;">Children</span>
    </h2>
</div>
""", unsafe_allow_html=True)

menu = st.sidebar.radio("Go to:", 
    [
        "1. Daily Tour Plan", 
        "2. Child Screening", 
        "3. 4D Defect Registry", 
        "4. Visual Analysis", 
        "5. HBNC Newborn Visit", 
        "6. Success Story Builder",
        "7. Anemia Tracker",
        "8. School Directory",
        "9. Anganwadi Directory",
        "10. Staff Directory",
        "11. Annual FY Planner",
        "12. Automated State Report",
        "13. Offline Batch Sync",
        "14. TECHO Entry Queue",
        "15. Clinical & IFA Tracker",
    ])

st.sidebar.markdown("---")
if st.sidebar.button("🔓 Logout"):
    for key in st.session_state.keys():
        del st.session_state[key]
    st.rerun()

# ==========================================
# MODULE 1: THE EXECUTIVE DASHBOARD & TOUR PLAN
# ==========================================
if menu == "1. Daily Tour Plan":
    render_header("Executive Dashboard", "Live team overview and daily screening stats", "📊", "#3b82f6")

    tab_tour, tab_charts = st.tabs(["📅 Daily Tour Plan", "📈 Executive Analytics"])

    with tab_tour:
        st.markdown("#### 🗺️ Manage Daily Tour Plan")
        
        with st.form("add_tour_form"):
            st.write("**📌 Enter Today's Target Locations**")
            c1, c2 = st.columns(2)
            with c1:
                staff_name = st.selectbox("select staff name", ["Dr. Nihar", "Dr. Sushmita", "Dr.Shruti", "Shobhaben", "Rinkalben", "Vaishaliben"])
                tour_date = st.date_input("Tour Date")
                tour_village = st.text_input("Village/City Name")
            with c2:
                tour_school = st.text_input("Target School (Optional)")
                tour_awc = st.text_input("Target Anganwadi (Optional)")
                tour_activity = st.text_input("field activity (Optional)")
            
            submit_tour = st.form_submit_button("💾 Save Tour Plan")
            
            if submit_tour:
                try:
                    tour_sheet = spreadsheet.worksheet("tour_plans")
                    date_str = tour_date.strftime("%d-%m-%Y")
                    tour_sheet.append_row([staff_name, date_str, tour_village, tour_school, tour_awc])
                    st.toast(f"✅ Tour Plan for {tour_village} saved!", icon="🎉")
                except Exception as e:
                    st.error(f"❌ Could not save! Error: {e}")

        st.write("---")
        st.subheader("📅 Live Tour Plan Preview")

        if st.button("🔄 Refresh Table"):
            try:
                tour_sheet = spreadsheet.worksheet("tour_plans")
                st.session_state.tour_data = tour_sheet.get_all_records()
            except Exception as e:
                st.error(f"❌ Could not load the table. Error: {e}")

        if "tour_data" in st.session_state:
            data = st.session_state.tour_data
            if data:
                df = pd.DataFrame(data)
                search_word = st.text_input("🔍 Search for a Staff Name, Village, or Date:")
                if search_word:
                    df = df[df.astype(str).apply(lambda col: col.str.contains(search_word, case=False)).any(axis=1)]
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No tour plans have been saved yet!")
                
        st.divider()
        st.markdown("##### ✅ Daily Check-list for MHT-1")
        st.checkbox("Check weighing scale and height tape calibration")
        st.checkbox("Ensure blank referral cards are printed (Backup)")
        st.checkbox("Charge tablet/mobile to 100%")

    with tab_charts:
        aw_logs, sch_logs, df = get_daily_logs()

        if df.empty:
            st.info("📊 The database is currently empty. Once your team enters screenings in Module 2, the charts will automatically appear here!")
        else:
            st.markdown("#### 📈 District Command Center")
            
            total_screened = len(df)
            total_aw = len(df[df['Location_Type'] == 'Anganwadi']) if 'Location_Type' in df.columns else 0
            total_sch = len(df[df['Location_Type'] == 'School']) if 'Location_Type' in df.columns else 0
            
            if 'Status' in df.columns:
                referred_df = df[~df['Status'].astype(str).str.lower().isin(['normal', 'none', '', 'nan'])]
                total_referred = len(referred_df)
            else:
                referred_df = pd.DataFrame()
                total_referred = 0

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total Screened", total_screened)
            c2.metric("Anganwadi", total_aw)
            c3.metric("School", total_sch)
            c4.metric("🚨 Referrals", total_referred, delta="Requires Action", delta_color="inverse")

            st.divider()
            chart_col1, chart_col2 = st.columns(2)

            with chart_col1:
                st.markdown("**Screenings by Location**")
                if 'Location_Type' in df.columns:
                    loc_counts = df['Location_Type'].value_counts().reset_index()
                    loc_counts.columns = ['Location', 'Count']
                    fig_loc = px.pie(loc_counts, values='Count', names='Location', hole=0.4, 
                                     color_discrete_sequence=['#10b981', '#3b82f6'])
                    st.plotly_chart(fig_loc, use_container_width=True)

            with chart_col2:
                st.markdown("**Referrals by Condition (4D)**")
                if not referred_df.empty and 'Disease' in referred_df.columns:
                    disease_counts = referred_df['Disease'].value_counts().reset_index()
                    disease_counts.columns = ['Condition', 'Cases']
                    fig_dis = px.bar(disease_counts, x='Cases', y='Condition', orientation='h',
                                     color='Cases', color_continuous_scale='Reds')
                    st.plotly_chart(fig_dis, use_container_width=True)
                else:
                    st.info("No referral conditions to map yet. Great job MHT-1!")

# ==========================================
# MODULE 2: EMR SCREENING (180-Day Roster & Manual Sync)
# ==========================================
elif menu == "2. Child Screening":
    render_header("Child Screening & EMR", "Record vitals and auto-calculate SAM/MAM", "🩺", "#10b981")

    # 🚀 NEW: The Manual Override Sync Button!
    if st.button("🔄 Sync & Refresh Roster"):
        try: get_recent_screenings.clear()
        except: st.cache_data.clear()
        st.toast("Roster synchronized with Master Database!", icon="✅")
        import time
        time.sleep(0.5)
        st.rerun()

    # 🚀 BULLETPROOF NUMBER FIX
    def safe_float(val):
        if not val: return 0.0
        clean_str = ''.join(c for c in str(val).replace(',', '.') if c.isdigit() or c == '.')
        try: return float(clean_str) if clean_str else 0.0
        except: return 0.0

    def get_whz_status(gender, height_cm, weight_kg):
        who_table = {
            65: [5.9, 6.4, 5.5, 6.0], 70: [6.8, 7.4, 6.4, 7.0],
            75: [7.6, 8.3, 7.3, 8.0], 80: [8.5, 9.2, 8.2, 9.0],
            85: [9.3, 10.1, 9.1, 9.9], 90: [10.2, 11.1, 10.0, 10.9],
            95: [11.2, 12.1, 10.9, 11.9], 100: [12.2, 13.3, 11.9, 13.0],
            105: [13.3, 14.5, 13.0, 14.3], 110: [14.4, 15.8, 14.1, 15.6],
            115: [15.5, 17.1, 15.3, 17.0], 120: [16.6, 18.4, 16.5, 18.4]
        }
        if height_cm < 65 or height_cm > 120:
            return "Out of bounds"
        closest_h = min(who_table.keys(), key=lambda k: abs(k - height_cm))
        refs = who_table[closest_h]
        if str(gender).upper().startswith('M'):
            sam_cutoff, mam_cutoff = refs[0], refs[1]
        else:
            sam_cutoff, mam_cutoff = refs[2], refs[3]
        if weight_kg < sam_cutoff: return "SAM"
        elif weight_kg < mam_cutoff: return "MAM"
        else: return "Normal"

    # 🚀 NEW: 180-Day Bi-Annual Background Checker
    @st.cache_data(ttl=60)
    def get_recent_screenings(sheet_name, inst_name):
        try:
            records = spreadsheet.worksheet(sheet_name).get_all_values()
            return [r for r in records if len(r) > 2 and r[1] == inst_name]
        except: return []

    import datetime
    today_date = datetime.date.today()
    today_string = today_date.strftime('%Y-%m-%d')
    cutoff_date = today_date - datetime.timedelta(days=180) # The 6-Month Mark!

    category = st.radio("Select Visit Type:", ["🏫 Schools", "👶 Anganwadi"], horizontal=True)
    st.divider()

    selected_inst = "-- Select --"
    if category == "👶 Anganwadi":
        if not df_aw.empty:
            raw_list = df_aw['AWC Name'].dropna().unique().tolist()
            actual_institutes = sorted([str(i).strip() for i in raw_list if str(i).strip() != ''])
            inst_display = {name: f"{idx+1}. {name}" for idx, name in enumerate(actual_institutes)}
            selected_inst = st.selectbox("Select Anganwadi Center:", options=["-- Select --"] + actual_institutes, format_func=lambda x: inst_display.get(x, x))
            if selected_inst != "-- Select --":
                filtered_children = df_aw[df_aw['AWC Name'] == selected_inst]
                actual_children = [str(c).strip() for c in filtered_children['Beneficiary Name'].tolist() if str(c).strip() != '']
        else:
            st.error("No Anganwadi data found.")
    else: 
        if not df_students.empty:
            raw_list = df_students['School'].dropna().unique().tolist()
            actual_institutes = sorted([str(i).strip() for i in raw_list if str(i).strip() != ''])
            inst_display = {name: f"{idx+1}. {name}" for idx, name in enumerate(actual_institutes)}
            selected_inst = st.selectbox("Select School:", options=["-- Select --"] + actual_institutes, format_func=lambda x: inst_display.get(x, x))
            
            if selected_inst != "-- Select --":
                filtered_children = df_students[df_students['School'] == selected_inst].copy()
                class_column = next((col for col in filtered_children.columns if any(w in str(col).lower() for w in ['class', 'std', 'grade', 'ધોરણ'])), None)
                
                if class_column:
                    filtered_children['_sort_val'] = filtered_children[class_column].astype(str).str.extract(r'(\d+)', expand=False).astype(float).fillna(999)
                    filtered_children = filtered_children.sort_values(by=['_sort_val', 'StudentName'])
                else:
                    filtered_children = filtered_children.sort_values(by=['StudentName'])
                
                actual_children = [str(c).strip() for c in filtered_children['StudentName'].tolist() if str(c).strip() != '']
        else:
            st.error("No School Student data found.")

    if selected_inst != "-- Select --":
        class_column = None
        if category != "👶 Anganwadi":
            for col in filtered_children.columns:
                if any(w in str(col).lower() for w in ['class', 'std', 'grade', 'ધોરણ']):
                    class_column = col; break

        # 🚀 180-DAY ROSTER LOGIC: Scan the last 6 months to see who is already done!
        target_sheet = "daily_screenings_aw" if category == "👶 Anganwadi" else "daily_screenings_schools"
        inst_records = get_recent_screenings(target_sheet, selected_inst)
        
        recent_status = {} # Keeps track of the most recent status for each child
        
        for r in inst_records:
            try:
                rec_date = datetime.datetime.strptime(r[0], '%Y-%m-%d').date()
                if rec_date >= cutoff_date:
                    c_name = str(r[2]).strip()
                    status_col = 12 if category == "👶 Anganwadi" else 10
                    status = str(r[status_col]).strip() if len(r) > status_col else ""
                    
                    # Updates dictionary (Google Sheets appending means the latest record overwrites older ones here)
                    recent_status[c_name] = "ABSENT" if status == "ABSENT" else "SCREENED"
            except:
                pass
                
        screened_names = [name for name, stat in recent_status.items() if stat == "SCREENED"]
        absent_names = [name for name, stat in recent_status.items() if stat == "ABSENT"]

        with st.expander("🚀 Bulk Absentee Entry"):
            st.write("Mark multiple children as absent instantly.")
            pending_only = [n for n in actual_children if n not in screened_names and n not in absent_names]
            absent_selection = st.multiselect("Select Absent Children:", pending_only)
            
            bulk_date = st.date_input("Date of Absence", key="bulk_abs_date")
            if st.button("📤 Mark All Selected as Absent"):
                if absent_selection:
                    ws_bulk = spreadsheet.worksheet(target_sheet)
                    rows_to_push = []
                    for name in absent_selection:
                        match = filtered_children[filtered_children['Beneficiary Name' if category=="👶 Anganwadi" else 'StudentName'].str.strip() == name].iloc[0]
                        
                        bulk_class = ""
                        if category != "👶 Anganwadi" and class_column:
                            bulk_class = str(match.get(class_column, ''))
                            if bulk_class.endswith('.0'): bulk_class = bulk_class[:-2]
                            if bulk_class == 'nan': bulk_class = ""

                        if category == "👶 Anganwadi":
                            rows_to_push.append([str(bulk_date), selected_inst, name, str(match.get('DoB','')), str(match.get('Gender','')), 0, 0, 0, 0, "None", "", str(match.get('TechoID','')), "ABSENT", "Pending", bulk_class])
                        else:
                            rows_to_push.append([str(bulk_date), selected_inst, name, str(match.get('DOB','')), str(match.get('Gender','')), 0, 0, 0, "None", str(match.get('CONTACT NUMBER','')), "ABSENT", "Pending", bulk_class])
                    ws_bulk.append_rows(rows_to_push)
                    st.toast("Bulk absences recorded!", icon="✅")
                    get_recent_screenings.clear() # Clear cache to instantly update tags
                    import time
                    time.sleep(0.5)
                    st.rerun()
        
        child_display = {}
        pending_list = []
        done_list = []
        
        for idx, name in enumerate(actual_children):
            display_str = f"{idx+1}. {name}"
            if category != "👶 Anganwadi" and class_column:
                student_row = filtered_children[filtered_children['StudentName'].astype(str).str.strip() == name]
                if not student_row.empty:
                    raw_class = str(student_row.iloc[0][class_column]).strip()
                    display_str += f" [Class: {raw_class[:-2] if raw_class.endswith('.0') else raw_class}]"
            
            # Apply Visual Tags based on 180-day history
            if name in absent_names:
                display_str += " 🛑 [ABSENT]"
                done_list.append(name)
            elif name in screened_names:
                display_str += " ✅ [SCREENED]"
                done_list.append(name)
            else:
                pending_list.append(name)

            child_display[name] = display_str

        # Smart Sort: Pending kids top, Finished kids bottom!
        sorted_actual_children = pending_list + done_list

        selected_child = st.selectbox(f"Select Child:", options=["-- Select Child --", "➕ Register New Child"] + sorted_actual_children, format_func=lambda x: child_display.get(x, x))
        
        if selected_child != "-- Select Child --":
            if selected_child == "➕ Register New Child":
                st.subheader("🆕 Register & Screen New Child")
                st.info("Fill out the details below to add a new walk-in or enrolled child and record their first screening.")
                
                with st.form("new_child_form", clear_on_submit=True):
                    c1, c2 = st.columns(2)
                    with c1: new_name = st.text_input("Child Full Name *")
                    with c2: new_dob = st.date_input("Date of Birth")
                    
                    c3, c4 = st.columns(2)
                    with c3: new_gender = st.selectbox("Gender *", ["M", "F"])
                    with c4: new_parent = st.text_input("Parent's Name")
                    
                    c5, c6, c7 = st.columns(3)
                    with c5: new_contact = st.text_input("📞 Contact Number", max_chars=10)
                    with c6: new_class = st.text_input("🏫 Class / Std")
                    if category == "👶 Anganwadi":
                        with c7: new_techo = st.text_input("🆔 Techo ID (Optional)")
                    else:
                        new_techo = "N/A"
                    
                    st.divider()
                    st.markdown("##### 🩺 Today's Vitals")
                    v1, v2, v3, v4 = st.columns(4)
                    with v1: h_str = st.text_input("Height (cm) *")
                    with v2: w_str = st.text_input("Weight (kg) *")
                    with v3: m_str = st.text_input("MUAC (cm)") if category == "👶 Anganwadi" else "0"
                    with v4: hb_str = st.text_input("Hb %")
                    
                    disease = st.text_input("🦠 Disease Identified (4D)", value="None")
                    save_new = st.form_submit_button("💾 Save New Child & Screening")
                    
                if save_new:
                    if not new_name or not h_str or not w_str:
                        st.error("⚠️ Name, Height, and Weight are mandatory fields!")
                    else:
                        screening_date = today_string
                        height_val = safe_float(h_str)
                        weight_val = safe_float(w_str)
                        muac_val = safe_float(m_str)
                        hb_val = safe_float(hb_str)
                        
                        final_status = get_whz_status(new_gender, height_val, weight_val) if category == "👶 Anganwadi" else "Normal"
                        
                        ws = spreadsheet.worksheet(target_sheet)
                        
                        if category == "👶 Anganwadi":
                            new_row = [screening_date, selected_inst, new_name, str(new_dob), new_gender, height_val, weight_val, muac_val, hb_val, disease, new_contact, new_techo, final_status, "Pending", new_class]
                        else:
                            new_row = [screening_date, selected_inst, new_name, str(new_dob), new_gender, height_val, weight_val, hb_val, disease, new_contact, "Online Entry", "Pending", new_class]
                            
                        ws.append_row(new_row)
                        
                        if category == "👶 Anganwadi" and final_status in ["SAM", "MAM"]:
                            spreadsheet.worksheet("cmtc_referral").append_row([screening_date, selected_inst, new_name, str(new_dob), new_contact, weight_val, height_val, muac_val, final_status, "Pending"])
                        
                        st.toast(f"✅ Successfully registered and screened {new_name}!", icon="🎉")
                        get_recent_screenings.clear() # Clear cache to instantly update tags
                        import time
                        time.sleep(0.5)
                        st.rerun()

            else:
                st.subheader("👤 Child Profile & History")
                final_child_name = selected_child
                
                name_col = 'Beneficiary Name' if category == "👶 Anganwadi" else 'StudentName'
                matched_rows = filtered_children[filtered_children[name_col].astype(str).str.strip() == selected_child]
                
                existing_class = ""
                if not matched_rows.empty:
                    match = matched_rows.iloc[0]
                    dob = match.get('DoB' if category == "👶 Anganwadi" else 'DOB', 'N/A')
                    gender = match.get('Gender', 'N/A')
                    parent = match.get('Mother Name' if category == "👶 Anganwadi" else 'FatherName', 'N/A')
                    
                    hist_h = match.get('Height' if category=="👶 Anganwadi" else 'HEIGHT', 'N/A')
                    hist_w = match.get('Weight' if category=="👶 Anganwadi" else 'WEIGHT', 'N/A')
                    hist_disease = match.get('4d' if category=="👶 Anganwadi" else '4D', 'None')
                    hist_hb = match.get('Hb', 'N/A')
                    contact_val = match.get('CONTACT NUMBER', '')
                    existing_contact = str(contact_val) if str(contact_val) != "nan" else ""

                    if category != "👶 Anganwadi" and class_column:
                        existing_class = str(match.get(class_column, ''))
                        if existing_class.endswith('.0'): existing_class = existing_class[:-2]
                        if existing_class == 'nan': existing_class = ""

                    p_col1, p_col2, p_col3 = st.columns(3)
                    with p_col1: st.info(f"**DOB:** {dob}")
                    with p_col2: st.info(f"**Gender:** {gender}")
                    with p_col3: st.info(f"**Parent:** {parent}")

                    st.markdown("##### 🕰️ Last Recorded Vitals (Baseline)")
                    h_cols = st.columns(4)
                    h_cols[0].metric("Prev Height", f"{hist_h} cm")
                    h_cols[1].metric("Prev Weight", f"{hist_w} kg")
                    h_cols[2].metric("Prev Hb", f"{hist_hb} %" if category != "👶 Anganwadi" else "N/A")
                    h_cols[3].metric("Prev 4D", str(hist_disease))

                    st.divider()

                    is_absent = st.checkbox(f"🚨 Mark {selected_child} as ABSENT today", key=f"emr_single_abs_{str(selected_child).replace(' ', '_')}")
                    
                    if is_absent:
                        if st.button("🚩 Confirm Single Absence"):
                            try:
                                ws = spreadsheet.worksheet(target_sheet)
                                if category == "👶 Anganwadi":
                                    row = [today_string, selected_inst, final_child_name, str(dob), str(gender), 0, 0, 0, 0, "None", existing_contact, str(match.get('TechoID','')), "ABSENT", "Pending", existing_class]
                                else:
                                    row = [today_string, selected_inst, final_child_name, str(dob), str(gender), 0, 0, 0, "None", existing_contact, "ABSENT", "Pending", existing_class]
                                ws.append_row(row)
                                st.toast("Recorded absence!", icon="✅")
                                get_recent_screenings.clear() 
                                import time
                                time.sleep(0.5) 
                                st.rerun()
                            except Exception as e: st.error(f"Error: {e}")

                    if not is_absent:
                        st.divider()
                        st.subheader("🩺 Enter New Screening Vitals")
                        
                        safe_key = str(selected_child).replace(" ", "_")
                        with st.form(f"vitals_form_{safe_key}", clear_on_submit=True):
                            screening_date = st.date_input("Date of Screening")
                            
                            sc1, sc2, sc3 = st.columns(3)
                            with sc1: updated_contact = st.text_input("📞 Contact Number", value=existing_contact, max_chars=10)
                            with sc2: updated_class = st.text_input("🏫 Class / Std", value=existing_class)
                            with sc3: techo_id = st.text_input("🆔 Techo ID") if category == "👶 Anganwadi" else "N/A"
                            
                            v1, v2, v3, v4 = st.columns(4)
                            with v1: h_str = st.text_input("Height (cm)")
                            with v2: w_str = st.text_input("Weight (kg)")
                            with v3: m_str = st.text_input("MUAC (cm)") if category == "👶 Anganwadi" else "0"
                            with v4: hb_str = st.text_input("Hb %")
                            disease = st.text_input("🦠 Disease Identified (4D)", value="None")
                            save_btn = st.form_submit_button("💾 Save Screening Data")

                        # 🚀 SMART MERGE ENGINE (Continues to look only at TODAY's date to prevent historical overwrite!)
                        if save_btn:
                            ws = spreadsheet.worksheet(target_sheet)
                            all_recs = ws.get_all_values()
                            
                            row_to_update = None
                            existing_row = []
                            
                            # 1. FIND THE EXISTING ROW FOR TODAY ONLY
                            for idx, r in enumerate(all_recs):
                                if len(r) > 2 and r[0] == str(screening_date) and str(r[2]).strip() == final_child_name.strip():
                                    row_to_update = idx + 1
                                    existing_row = r + [""] * 15  
                                    break

                            has_new_h = str(h_str).strip() != ""
                            has_new_w = str(w_str).strip() != ""
                            has_new_m = str(m_str).strip() != "" if category == "👶 Anganwadi" else False
                            has_new_hb = str(hb_str).strip() != ""
                            has_new_disease = str(disease).strip().lower() not in ["", "none"]

                            if row_to_update:
                                merged_h = safe_float(h_str) if has_new_h else safe_float(existing_row[5])
                                merged_w = safe_float(w_str) if has_new_w else safe_float(existing_row[6])
                                
                                if category == "👶 Anganwadi":
                                    merged_m = safe_float(m_str) if has_new_m else safe_float(existing_row[7])
                                    merged_hb = safe_float(hb_str) if has_new_hb else safe_float(existing_row[8])
                                    merged_disease = disease if has_new_disease else (existing_row[9] if str(existing_row[9]).strip() != "" else "None")
                                    merged_contact = updated_contact if str(updated_contact).strip() != "" else existing_row[10]
                                    merged_techo = techo_id if str(techo_id).strip() not in ["", "N/A"] else existing_row[11]
                                    
                                    merged_status = get_whz_status(gender, merged_h, merged_w)
                                    merged_class = updated_class if str(updated_class).strip() != "" else existing_row[14]
                                    
                                    new_row = [str(screening_date), selected_inst, final_child_name, str(dob), str(gender), merged_h, merged_w, merged_m, merged_hb, merged_disease, merged_contact, merged_techo, merged_status, "Pending", merged_class]
                                else:
                                    merged_hb = safe_float(hb_str) if has_new_hb else safe_float(existing_row[7])
                                    merged_disease = disease if has_new_disease else (existing_row[8] if str(existing_row[8]).strip() != "" else "None")
                                    merged_contact = updated_contact if str(updated_contact).strip() != "" else existing_row[9]
                                    merged_class = updated_class if str(updated_class).strip() != "" else existing_row[12]
                                    
                                    new_row = [str(screening_date), selected_inst, final_child_name, str(dob), str(gender), merged_h, merged_w, merged_hb, merged_disease, merged_contact, "Online Entry", "Pending", merged_class]
                                    
                                ws.update(range_name=f"A{row_to_update}", values=[new_row])
                                st.toast(f"✅ Safely merged records for {final_child_name}!", icon="🤝")
                                
                                if category == "👶 Anganwadi" and merged_status in ["SAM", "MAM"]:
                                    cmtc_ws = spreadsheet.worksheet("cmtc_referral")
                                    cmtc_recs = cmtc_ws.get_all_values()
                                    cmtc_row = None
                                    for i, r in enumerate(cmtc_recs):
                                        if len(r) > 2 and r[0] == str(screening_date) and str(r[2]).strip() == final_child_name.strip():
                                            cmtc_row = i + 1; break
                                            
                                    cmtc_data = [str(screening_date), selected_inst, final_child_name, str(dob), merged_contact, merged_w, merged_h, merged_m, merged_status, "Pending"]
                                    
                                    if cmtc_row:
                                        cmtc_ws.update(range_name=f"A{cmtc_row}", values=[cmtc_data]) 
                                    else:
                                        cmtc_ws.append_row(cmtc_data) 
                                    
                            else:
                                height_val = safe_float(h_str)
                                weight_val = safe_float(w_str)
                                muac_val = safe_float(m_str)
                                hb_val = safe_float(hb_str)
                                final_status = get_whz_status(gender, height_val, weight_val) if category == "👶 Anganwadi" else "Normal"
                                
                                if category == "👶 Anganwadi":
                                    new_row = [str(screening_date), selected_inst, final_child_name, str(dob), str(gender), height_val, weight_val, muac_val, hb_val, disease, updated_contact, techo_id, final_status, "Pending", updated_class]
                                else:
                                    new_row = [str(screening_date), selected_inst, final_child_name, str(dob), str(gender), height_val, weight_val, hb_val, disease, updated_contact, "Online Entry", "Pending", updated_class]

                                ws.append_row(new_row) 
                                st.toast(f"✅ New screening saved for {final_child_name}!", icon="🎉")
                                
                                if category == "👶 Anganwadi" and final_status in ["SAM", "MAM"]:
                                    spreadsheet.worksheet("cmtc_referral").append_row([str(screening_date), selected_inst, final_child_name, str(dob), updated_contact, weight_val, height_val, muac_val, final_status, "Pending"])
                            
                            get_recent_screenings.clear() 
                            import time
                            time.sleep(0.5) 
                            st.rerun()
# ==========================================
# MODULE 3: 4D DEFECT REGISTRY & CASE MANAGEMENT (Emoji-Anchor Edition)
# ==========================================
elif menu == "3. 4D Defect Registry":
    render_header("4D Defect Command Center", "Track live referrals, manage 5-year case history, and generate official print cards", "📋", "#8b5cf6")

    if st.button("🔄 Sync & Refresh Data"):
        try: get_daily_logs.clear()
        except: st.cache_data.clear()
        st.toast("Database refreshed!", icon="✅")
        time.sleep(0.5)
        st.rerun()

    aw_logs, sch_logs, df_combined = get_daily_logs()
    all_defects = []

    def is_real_defect(val):
        v = str(val).strip().lower()
        return v not in ['', 'nan', 'none', 'no', 'null', 'na', 'n/a', 'false', 'normal', '-', 'absent', 'out of bounds']

    # 🚀 VECTORIZED SPEED UPGRADE
    for df_type, df in [("Anganwadi", aw_logs), ("School", sch_logs)]:
        if not df.empty:
            df.columns = [str(c).strip() for c in df.columns]
            
            disease_col = next((c for c in df.columns if c.lower() in ['disease', 'diseases', '4d']), None)
            status_col = next((c for c in df.columns if c.lower() in ['status', 'sam', 'mam']), None)
            
            mask = pd.Series(False, index=df.index)
            if disease_col: mask = mask | df[disease_col].apply(is_real_defect)
            if status_col: mask = mask | df[status_col].apply(is_real_defect)
            
            sick_kids = df[mask]
            
            for _, row in sick_kids.iterrows():
                d_val = str(row[disease_col]).strip() if disease_col else ""
                s_val = str(row[status_col]).strip() if status_col else ""
                
                condition_parts = []
                if is_real_defect(s_val): condition_parts.append(s_val)
                if is_real_defect(d_val): condition_parts.append(d_val)
                
                def get_val(search_terms, fallback="Unknown"):
                    for col in df.columns:
                        if any(term in col.lower() for term in search_terms): return str(row[col])
                    return fallback

                all_defects.append({
                    "Date": get_val(['date', 'screening']),
                    "Name": get_val(['name', 'beneficiary', 'student']),
                    "Institution": get_val(['inst', 'school', 'awc']),
                    "Condition": " + ".join(condition_parts),
                    "Contact": get_val(['contact', 'mobile', 'phone', 'techo']),
                    "Gender": get_val(['gender', 'sex'], "N/A"),
                    "DOB": get_val(['dob', 'birth'], "N/A"),
                    "Father": get_val(['father', 'parent', 'mother'], "N/A"),
                    "Type": df_type
                })

    import datetime
    today = datetime.date.today()
    today_ts = pd.Timestamp(today) 
    
    if not df_4d.empty:
        df_4d.columns = df_4d.columns.str.strip()
        df_working = df_4d.copy()
        df_working['Parsed_Next_Date'] = pd.to_datetime(df_working.get('Next Follow-Up Date', ''), errors='coerce', dayfirst=True)
    else:
        df_working = pd.DataFrame()

    tab_action, tab_logger, tab_live, tab_card, tab_master = st.tabs([
        "🚨 1. Action Desk", 
        "📞 2. Follow-Up Logger", 
        "🌍 3. Live Daily Registry", 
        "🪪 4. Refer Card Print", 
        "🗄️ 5. Master Database"
    ])

    with tab_action:
        st.subheader("🎯 Today's Action Desk")
        st.write("Historical 4D cases that need immediate follow-up.")

        if not df_working.empty:
            overdue_mask = (df_working['Parsed_Next_Date'] <= today_ts) & (df_working.get('Current Status', '').astype(str).str.upper() != 'CURED/RESOLVED')
            df_action = df_working[overdue_mask].copy()
            
            unscheduled_mask = df_working['Parsed_Next_Date'].isna() & (df_working.get('Current Status', '').astype(str).str.upper() != 'CURED/RESOLVED')
            df_new = df_working[unscheduled_mask].copy()

            col1, col2 = st.columns(2)
            col1.metric("🔴 Urgent / Overdue Follow-ups", len(df_action))
            col2.metric("🟡 Unscheduled / Needs Assessment", len(df_new))

            st.divider()
            if not df_action.empty:
                st.error(f"🚨 **{len(df_action)} Children require immediate contact!**")
                cols_to_show = [c for c in ['NAME', 'VILLAGE', '4D', 'MOBILE NO', 'Current Status', 'Next Follow-Up Date'] if c in df_action.columns]
                st.dataframe(df_action[cols_to_show], use_container_width=True, hide_index=True)
            else:
                st.success("🎉 No overdue follow-ups! You are completely caught up.")

            if not df_new.empty:
                st.warning(f"⚠️ **{len(df_new)} Children have no follow-up date scheduled.**")
                cols_to_show2 = [c for c in ['NAME', 'VILLAGE', '4D', 'SCREENING DATE', 'AW/SCHOOL NAME'] if c in df_new.columns]
                st.dataframe(df_new[cols_to_show2], use_container_width=True, hide_index=True)
        else:
            st.warning("⚠️ No historical data found in the '4d_list' tab.")

    with tab_logger:
        st.subheader("📞 Log a Follow-Up Contact")
        
        if not df_working.empty:
            active_kids = df_working[df_working.get('Current Status', '').astype(str).str.upper() != 'CURED/RESOLVED']
            
            if not active_kids.empty:
                kid_options = []
                for _, r in active_kids.iterrows():
                    # 🚀 EMOJI ANCHOR FIX: Bulletproof string building!
                    kid_options.append(f"{r.get('NAME', 'Unknown')} 🩺 {r.get('4D', 'Unknown')} 📍 {r.get('VILLAGE', 'Unknown')} 📞 Ph: {r.get('MOBILE NO', 'N/A')}")
                
                selected_kid_str = st.selectbox("Select Child for Follow-up:", ["-- Select --"] + sorted(kid_options))

                if selected_kid_str != "-- Select --":
                    # 🚀 EMOJI ANCHOR PARSING: It will never get confused by parenthesis again!
                    exact_name = selected_kid_str.split(" 🩺 ")[0].strip()
                    exact_disease = selected_kid_str.split(" 🩺 ")[1].split(" 📍 ")[0].strip()
                    
                    matched_rows = df_working[
                        (df_working['NAME'].astype(str).str.strip() == exact_name) & 
                        (df_working['4D'].astype(str).str.strip() == exact_disease)
                    ]
                    
                    if not matched_rows.empty:
                        target_row = matched_rows.iloc[0]
                        st.info(f"**Current Status:** {target_row.get('Current Status', 'None')} | **Last Scheduled:** {target_row.get('Next Follow-Up Date', 'None')}")

                        with st.form("followup_form"):
                            st.write("### Update Case File")
                            f_col1, f_col2 = st.columns(2)
                            with f_col1: contact_method = st.radio("Contact Method:", ["📞 Telephonic", "🏠 Physical Visit"], horizontal=True)
                            with f_col2: new_status = st.selectbox("New Case Status:", ["Pending Assessment", "Under Treatment", "Referred to CHC", "Surgery Scheduled", "Cured/Resolved"], index=1)
                            
                            remarks = st.text_input("Doctor/Staff Remarks & Advice given today:")
                            new_date = st.date_input("Schedule NEXT Follow-Up Date (Leave as today if Cured)")
                            submit_followup = st.form_submit_button("💾 Save to Master Database")

                        if submit_followup:
                            try:
                                ws_4d = spreadsheet.worksheet("4d_list")
                                all_recs = ws_4d.get_all_values()
                                headers = all_recs[0]
                                
                                status_idx = headers.index("Current Status") if "Current Status" in headers else None
                                date_idx = headers.index("Next Follow-Up Date") if "Next Follow-Up Date" in headers else None
                                remarks_idx = headers.index("Remarks") if "Remarks" in headers else None
                                
                                if status_idx is None or date_idx is None:
                                    st.error("⚠️ Ensure your Google Sheet has exact columns named 'Current Status' and 'Next Follow-Up Date'")
                                    st.stop()

                                row_to_update = None
                                for i, r in enumerate(all_recs):
                                    if len(r) > headers.index("NAME") and str(r[headers.index("NAME")]).strip() == exact_name and str(r[headers.index("4D")]).strip() == exact_disease:
                                        row_to_update = i + 1; break
                                
                                if row_to_update:
                                    ws_4d.update_cell(row_to_update, status_idx + 1, new_status)
                                    final_date = "" if new_status == "Cured/Resolved" else str(new_date)
                                    ws_4d.update_cell(row_to_update, date_idx + 1, final_date)
                                    if remarks_idx is not None:
                                        ws_4d.update_cell(row_to_update, remarks_idx + 1, f"[{today}] {contact_method}: {remarks}")

                                    st.toast(f"✅ Successfully updated Case File for {exact_name}!", icon="🎉")
                                    st.cache_data.clear()
                                    time.sleep(0.5)
                                    st.rerun()
                                else:
                                    st.error("Could not find this specific child in the Google Sheet.")
                            except Exception as e: st.error(f"Error saving to Google Sheets: {e}")
                            
                    else:
                        st.error(f"⚠️ Could not find the exact record for '{exact_name}'. The database might have hidden formatting issues.")
            else:
                st.success("No active cases found! Everyone is cured.")

    with tab_live:
        st.subheader("🌍 Today's Screened Defects")
        if all_defects:
            df_display = pd.DataFrame(all_defects)
            c1, c2 = st.columns(2)
            c1.metric("Total Referrals Today", len(all_defects))
            c2.info("💡 Pro-tip: You can call parents using the 'Contact' column on mobile.")
            st.dataframe(df_display[['Date', 'Name', 'Institution', 'Condition', 'Contact']], use_container_width=True, hide_index=True)
        else:
            st.info("Registry empty. Start screening in Module 2!")

    with tab_card:
        st.subheader("🪪 Print Official Refer Cards")
        if all_defects:
            # 🚀 NEW FEATURE: Extract unique institutions for the filter
            unique_institutions = sorted(list(set([str(d['Institution']).strip() for d in all_defects if str(d['Institution']).strip() != ""])))
            
            # Institution Filter UI
            selected_inst = st.selectbox("🏢 Filter by Institution (Optional):", ["All Institutions"] + unique_institutions)
            
            # Filter the defects list based on selection
            filtered_defects = all_defects
            if selected_inst != "All Institutions":
                filtered_defects = [d for d in all_defects if str(d['Institution']).strip() == selected_inst]
                
            if not filtered_defects:
                st.warning(f"No children found in {selected_inst}.")
            else:
                display_names = {f"{d['Name']} ({d['Institution']})": d['Name'] for d in filtered_defects}
                sel_display = st.selectbox("Select Child for Refer Card:", ["-- Select --"] + list(display_names.keys()))
                
                if sel_display != "-- Select --":
                    actual_name = display_names[sel_display]
                    p_data = next(item for item in filtered_defects if item["Name"] == actual_name)
                    p_data['Age'] = get_age(p_data.get('DOB', ''))
                    
                    st.markdown(f"### 🪪 Preparing Card for: **{actual_name}**")
                    st.info(f"**Child Age:** {p_data['Age']} | **Condition:** {p_data.get('Condition', 'Unknown')}")
                    
                    with st.form("refer_card_print_form"):
                        st.write("### 📝 Doctor's Clinical Referral Details")
                        
                        c1, c2, c3 = st.columns(3)
                        with c1: p_data['Parent_Name'] = st.text_input("Father's Name", value=p_data.get('Father', ''))
                        with c2: p_data['Mother'] = st.text_input("Mother's Name", placeholder="Enter Mother's Name")
                        with c3: p_data['Contact_Num'] = st.text_input("Contact Number", value=p_data.get('Contact', ''), max_chars=10)
                        
                        c4, c5 = st.columns(2)
                        with c4: p_data['Village'] = st.text_input("Village / City", value=p_data.get('Institution', ''))
                        with c5: p_data['School_Status'] = st.selectbox("Child Status", ["School Going", "Not School Going", "Anganwadi"])
                        
                        st.divider()
                        
                        p_data['Clinical_Findings'] = st.text_area("Medical Condition / 4D", value=p_data.get('Condition', ''))
                        
                        c6, c7 = st.columns(2)
                        with c6: p_data['Treatment_Given'] = st.text_input("Primary Treatment Given", value="Counselling and Referral")
                        with c7: p_data['Referred_To'] = st.text_input("Referred To (Hospital)", value="CIVIL HOSPITAL JUNAGADH")
                        
                        c8, c9 = st.columns(2)
                        with c8: p_data['MO_Name'] = st.text_input("Medical Officer Name", value="Dr. NIHAR UPADHYAY")
                        with c9: p_data['Date'] = st.date_input("Official Referral Date")
                            
                        prepare_pdf = st.form_submit_button("🖨️ Generate Official Card & Stamp")
                    
                    if prepare_pdf:
                        pdf_bytes = generate_refer_card(p_data) 
                        st.success(f"✅ PDF Prepared for {actual_name}!")
                        
                        import base64
                        b64 = base64.b64encode(pdf_bytes).decode()
                        
                        html_button = f'''
                            <a href="data:application/pdf;base64,{b64}" download="Refer_{actual_name}.pdf" target="_blank" 
                               style="display: inline-block; padding: 12px 24px; background-color: #3b82f6; color: white; 
                               text-decoration: none; border-radius: 8px; font-weight: bold; text-align: center; width: 100%;">
                               📄 Tap Here to View / Download PDF
                            </a>
                        '''
                        st.markdown(html_button, unsafe_allow_html=True)
                        st.caption("💡 **Mobile Users:** The PDF will open safely in a new window. When you are done, simply close the PDF to return to the app!")                
        
        else:
            st.warning("No children found in daily registry to generate a card. Screen children in Module 2 first.")

    with tab_master:
        st.subheader("🗄️ Search the Historical Database (2021-Present)")
        
        if not df_working.empty:
            search_query = st.text_input("🔍 Search by Name, Village, or Disease:")
            if search_query:
                mask = np.column_stack([df_4d[col].astype(str).str.contains(search_query, case=False, na=False) for col in df_4d.columns])
                df_display = df_4d.loc[mask.any(axis=1)]
            else:
                df_display = df_4d
                
            st.write(f"Showing **{len(df_display)}** records.")
            st.dataframe(df_display, use_container_width=True)
            
            csv_4d = df_display.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="⬇️ Download Filtered Report (CSV)",
                data=csv_4d,
                file_name=f"4D_Master_Report_{today}.csv",
                mime="text/csv"
            )
# ==========================================
# MODULE 4: VISUAL ANALYSIS
# ==========================================
elif menu == "4. Visual Analysis":
    render_header("Visual Analytics", "Quarterly Zero-Lag Performance & Epidemiological Mapping", "🗺️", "#f97316")
    st.write("Welcome to the Zero-Lag Command Center. This dashboard processes your Quarterly State Reports for maximum speed and deep insights.")

    tab_coverage, tab_hotspot, tab_radar = st.tabs([
        "🎯 Coverage & Velocity Matrix", "📍 Disease Hotspot Mapper", "🧬 Epidemiological Radar"
    ])

    with tab_coverage:
        st.subheader("Village-Wise Screening Coverage")
        st.write("Identifies which villages have the largest gap between registered children and actual screenings.")
        
        if not df_q_perf.empty and 'Location Name' in df_q_perf.columns:
            perf_df = df_q_perf.copy()
            
            cols_to_clean = ['Registered Children', 'AWC Screened In First Half', 'Registered Students', 'Students Screened']
            for col in cols_to_clean:
                if col in perf_df.columns:
                    perf_df[col] = pd.to_numeric(perf_df[col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)

            perf_df['Total Registered'] = perf_df.get('Registered Children', 0) + perf_df.get('Registered Students', 0)
            perf_df['Total Screened'] = perf_df.get('AWC Screened In First Half', 0) + perf_df.get('Students Screened', 0)

            perf_df = perf_df[perf_df['Location Name'].str.strip() != '']
            perf_df = perf_df.sort_values('Total Registered', ascending=False).head(20) 

            fig_cov = px.bar(perf_df, x='Location Name', y=['Total Screened', 'Total Registered'],
                             barmode='group', title="Screened vs Registered (Top 20 Villages by Population)",
                             labels={'value': 'Number of Children', 'variable': 'Category'},
                             color_discrete_map={'Total Screened': '#10b981', 'Total Registered': '#3b82f6'})
            st.plotly_chart(fig_cov, use_container_width=True)
        else:
            st.warning("⚠️ Waiting for valid data in the 'Q_Performance' tab.")

    with tab_hotspot:
        st.subheader("Geographical Disease Hotspots")
        st.write("Select a specific disease to instantly see which villages have the highest case counts.")
        
        if not df_q_loc.empty and 'Location Name' in df_q_loc.columns:
            loc_df = df_q_loc.copy()
            
            exclude_cols = ['Sr. No.', 'Parent Location', 'Location Name', 'Total Number of Registered Children', 'Total No of Children Screened']
            disease_cols = [c for c in loc_df.columns if c not in exclude_cols and 'Total' not in c]

            selected_disease = st.selectbox("🦠 Select Disease to Map:", sorted(disease_cols))

            if selected_disease:
                loc_df[selected_disease] = pd.to_numeric(loc_df[selected_disease].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
                loc_df = loc_df[loc_df['Location Name'].str.strip() != '']

                hotspot_data = loc_df[['Location Name', selected_disease]].sort_values(selected_disease, ascending=False).head(15)

                if hotspot_data[selected_disease].sum() > 0:
                    fig_hot = px.bar(hotspot_data, x=selected_disease, y='Location Name', orientation='h',
                                     title=f"🚨 Top 15 Villages for: {selected_disease}",
                                     color=selected_disease, color_continuous_scale='Reds')
                    fig_hot.update_layout(yaxis={'categoryorder':'total ascending'})
                    st.plotly_chart(fig_hot, use_container_width=True)
                else:
                    st.success(f"✅ Incredible! Zero reported cases of **{selected_disease}** across all villages!")
        else:
            st.warning("⚠️ Waiting for valid data in the 'Q_Location_4D' tab.")

    with tab_radar:
        st.subheader("Demographic Disease Radar (Age & Gender)")
        st.write("Analyze how specific defects impact different age brackets and genders.")
        
        if not df_q_demo.empty and 'Defects' in df_q_demo.columns:
            demo_df = df_q_demo.copy()
            demo_df = demo_df[~demo_df['Defects'].astype(str).str.contains('Total', na=False, case=False)]

            selected_demo_disease = st.selectbox("🧬 Select Disease to Analyze:", sorted(demo_df['Defects'].unique()))

            if selected_demo_disease:
                disease_data = demo_df[demo_df['Defects'] == selected_demo_disease].iloc[0]

                age_groups = ['Below 6 weeks', 'Below 3 Years', '3 Years to 6 Years', '6 Years to 18 Years']
                radar_data = []

                for age in age_groups:
                    m_val = 0
                    f_val = 0
                    for c in demo_df.columns:
                        if 'Male' in c and age in c: m_val = pd.to_numeric(str(disease_data[c]).replace(',', ''), errors='coerce')
                        if 'Female' in c and age in c: f_val = pd.to_numeric(str(disease_data[c]).replace(',', ''), errors='coerce')

                    m_val = m_val if pd.notna(m_val) else 0
                    f_val = f_val if pd.notna(f_val) else 0

                    radar_data.append({'Age Group': age, 'Gender': 'Boys 👦', 'Cases': m_val})
                    radar_data.append({'Age Group': age, 'Gender': 'Girls 👧', 'Cases': f_val})

                radar_df = pd.DataFrame(radar_data)

                if radar_df['Cases'].sum() > 0:
                    fig_rad = px.bar(radar_df, x='Age Group', y='Cases', color='Gender', barmode='group',
                                     title=f"Demographic Breakdown: {selected_demo_disease}",
                                     color_discrete_map={'Boys 👦': '#3b82f6', 'Girls 👧': '#ec4899'})
                    st.plotly_chart(fig_rad, use_container_width=True)
                else:
                    st.success(f"✅ No demographic cases found for **{selected_demo_disease}**!")
        else:
            st.warning("⚠️ Waiting for valid data in the 'Q_Demo_4D' tab.")

# ==========================================
# MODULE 5: HBNC NEWBORN VISIT (Zero-Lag Micro-Cache)
# ==========================================
elif menu == "5. HBNC Newborn Visit":
    render_header("HBNC Newborn Visit", "Track physical visits and telephonic Techo consultations", "👶", "#f472b6")
    
    @st.cache_data(ttl=600)
    def get_hbnc_logs():
        try: return pd.DataFrame(spreadsheet.worksheet("hbnc_screenings").get_all_records())
        except: return pd.DataFrame()
        
    df_hbnc_live = get_hbnc_logs()

    tab_physical, tab_telephonic = st.tabs(["🏠 1. Physical Field Visits", "📞 2. Telephonic Techo Queue"])
    
    # --- TAB 1: PHYSICAL FIELD VISITS (UNTOUCHED AS PER REQUEST) ---
    with tab_physical:
        st.subheader("📝 Log Physical Visit")
        with st.form("hbnc_form", clear_on_submit=True):
            st.markdown("#### 👶 Details")
            c1, c2, c3 = st.columns(3)
            with c1: visit_date = st.date_input("Date of Visit")
            with c2: child_name = st.text_input("Child's Name *")
            with c3: techo_id = st.text_input("Techo ID")
                
            c4, c5, c6 = st.columns(3)
            with c4: parent_name = st.text_input("Parent's Name *")
            with c5: contact_number = st.text_input("Contact Number", max_chars=10)
            with c6: village_name = st.text_input("Village Name") 

            st.divider()
            st.markdown("#### 🏥 Birth History")
            b1, b2, b3, b4 = st.columns(4)
            with b1: dob = st.date_input("Date of Birth")
            with b2: birth_weight = st.number_input("Birth Weight (kg)", min_value=0.0, step=0.1)
            with b3: delivery_type = st.selectbox("Delivery Type", ["Normal Delivery (ND)", "C-Section (LSCS)", "Instrumental"])
            with b4: delivery_point = st.selectbox("Delivery Point", ["Vatsalya Hospital", "SDH Visavadar", "Jay Ambe Hospital", "Junagadh Civil Hospital", "CHC/PHC", "Home Delivery", "Other Private Hospital"])

            st.divider()
            disease = st.text_input("🦠 Disease / Defect Identified?", placeholder="e.g., Cleft lip, None")
            observations = st.text_area("📝 Clinical Observations", height=100)

            if st.form_submit_button("💾 Save HBNC Record"):
                if child_name == "" or parent_name == "":
                    st.error("🚨 Enter Child and Parent Name.")
                else:
                    try:
                        spreadsheet.worksheet("hbnc_screenings").append_row([str(visit_date), child_name, parent_name, contact_number, str(dob), birth_weight, delivery_type, delivery_point, techo_id, disease, observations, village_name])
                        st.toast(f"✅ Recorded Visit for {child_name}.", icon="🎉")
                        get_hbnc_logs.clear() 
                        import time
                        time.sleep(0.5)
                        st.rerun()
                    except Exception as e:
                        st.error(f"⚠️ Error: Could not find 'hbnc_screenings' tab. {e}")
                        
        st.divider()
        st.subheader("📋 Recent Physical HBNC Records")
        try:
            if not df_hbnc_live.empty:
                st.dataframe(df_hbnc_live, use_container_width=True)
                csv_hbnc = df_hbnc_live.to_csv(index=False).encode('utf-8-sig')
                st.download_button(label="⬇️ Download Physical Visit Data", data=csv_hbnc, file_name=f"HBNC_Physical_Visits.csv", mime="text/csv")
            else:
                st.info("No physical visit data found yet.")
        except Exception as e:
            st.warning(f"⚠️ Could not load physical data table. Reason: {e}")

    # --- TAB 2: TELEPHONIC TECHO QUEUE (REVAMPED) ---
    with tab_telephonic:
        st.subheader("📞 Techo Consultation Queue")
        st.info("Directly managing call list from 'hbnc_telephonic' master sheet. No upload needed.")
        
        try:
            # 1. Fetch data from the persistent sheet
            tele_sheet = spreadsheet.worksheet("hbnc_telephonic")
            raw_tele_data = tele_sheet.get_all_records()
            
            if raw_tele_data:
                df_tele = pd.DataFrame(raw_tele_data)
                
                # 🚀 THE SANITIZER (Prevents JSON NaN Errors)
                df_tele = df_tele.fillna("")
                df_tele = df_tele.replace(['nan', 'NaN', 'NaT', 'None'], "")

               # ✂️ THE UPDATED TECHO LOCATION TRIMMER (Extracts Last Two Levels)
                if "Location" in df_tele.columns:
                    # Splits at '>', takes the last two elements ([-2:]), strips spaces, and joins them back
                    df_tele["Location"] = df_tele["Location"].astype(str).apply(
                        lambda x: " > ".join([p.strip() for p in x.split('>')[-2:]]) if '>' in x else x.strip()
                    )

                # 2. Ensure all required columns exist (Safety Check)
                required_cols = ["Child Name", "Techo ID", "Contact Number", "Location", "Gender", "Date of Birth", "Call Status", "Staff Remarks"]

                # Ensure Status and Remarks columns exist
                if "Call Status" not in df_tele.columns: df_tele["Call Status"] = "Pending"
                if "Staff Remarks" not in df_tele.columns: df_tele["Staff Remarks"] = ""

                st.write(f"Showing **{len(df_tele)}** children in the Techo Call Queue.")
                
                # 2. THE DATA EDITOR (Module 15 Style)
                status_options = ["Pending", "Completed ✅", "Not Reachable 📵", "Call Later ⏳", "Switched Off", "Wrong Number"]
                
                # Lock original Techo columns, only allow editing Status and Remarks
                # Modify these strings to match your actual Google Sheet headers exactly
                read_only_cols = [col for col in df_tele.columns if col not in ["Call Status", "Staff Remarks"]]

                updated_tele_df = st.data_editor(
                    df_tele,
                    column_config={
                        "Call Status": st.column_config.SelectboxColumn("Call Outcome", options=status_options, width="medium"),
                        "Staff Remarks": st.column_config.TextColumn("Call Notes/Remarks", width="large"),
                    },
                    disabled=read_only_cols,
                    hide_index=True,
                    use_container_width=True
                )

                # 3. THE BULK SAVE BUTTON
                if st.button("💾 Save All Call Outcomes", type="primary"):
                    with st.spinner("Cleaning and syncing call logs..."):
                        final_tele_df = updated_tele_df.copy()
                        
                        # Add a "Last Updated" timestamp to every row
                        import datetime
                        final_tele_df['Last Update'] = datetime.date.today().strftime("%Y-%m-%d")
                        
                        # Vacuum cleanup for JSON compatibility
                        final_tele_df = final_tele_df.astype(str).replace(['nan', 'NaN', 'None'], "")
                        
                        # Overwrite sheet
                        data_to_push = [final_tele_df.columns.values.tolist()] + final_tele_df.values.tolist()
                        tele_sheet.update(data_to_push)
                        
                        st.toast("Call log successfully updated!", icon="📞")
                        import time
                        time.sleep(1)
                        st.rerun()
            else:
                st.warning("⚠️ The 'hbnc_telephonic' sheet is empty. Please paste the Techo names into the Google Sheet first.")
                
        except Exception as e:
            st.error(f"❌ Telephonic Module Error: {e}")
            st.info("💡 Ensure you have a tab named 'hbnc_telephonic' in your Master Google Sheet.")
# ==========================================
# MODULE 6: SUCCESS STORY BUILDER
# ==========================================
elif menu == "6. Success Story Builder":
    render_header("Success Story Builder", "Generate digital, photo-integrated success reports.", "🌟", "#e11d48")
    
    with st.form("success_story_form"):
        st.subheader("👤 1. Child Details")
        c1, c2, c3 = st.columns(3)
        name = c1.text_input("Child Name")
        age = c2.text_input("Age (e.g., 3 Years)")
        gender = c3.selectbox("Gender", ["Male", "Female"])
        location = st.text_input("Village & Anganwadi / School Name")
        
        st.divider()
        
        st.subheader("🚨 2. The Discovery (Before Intervention)")
        col_b1, col_b2 = st.columns([2, 1])
        with col_b1:
            date_before = st.date_input("Date of Initial Screening")
            diagnosis = st.text_input("Initial Diagnosis (e.g., SAM, Severe Anemia)")
            b1, b2, b3, b4 = st.columns(4)
            w_before = b1.number_input("Weight (kg)", value=0.0, key="w1")
            h_before = b2.number_input("Height (cm)", value=0.0, key="h1")
            m_before = b3.number_input("MUAC (cm)", value=0.0, key="m1")
            hb_before = b4.number_input("Hb (g/dL)", value=0.0, key="hb1")
        with col_b2:
            img_before = st.file_uploader("Upload 'Before' Photo", type=["jpg", "jpeg", "png"], key="img_b")
            
        st.divider()
            
        st.subheader("⚕️ 3. The Intervention")
        referred_to = st.text_input("Referred To (e.g., CMTC Junagadh, District Hospital)")
        treatment = st.text_area("Key Treatments Given (e.g., F-100 diet, Blood Transfusion)", height=100)
        days_care = st.text_input("Duration of Care (e.g., 14 Days)")
        
        st.divider()
        
        st.subheader("✅ 4. The Triumph (Current Status)")
        col_a1, col_a2 = st.columns([2, 1])
        with col_a1:
            date_after = st.date_input("Date of Discharge / Follow-up")
            status = st.text_input("Current Health Status (e.g., Recovered, Healthy)")
            a1, a2, a3, a4 = st.columns(4)
            w_after = a1.number_input("Weight (kg)", value=0.0, key="w2")
            h_after = a2.number_input("Height (cm)", value=0.0, key="h2")
            m_after = a3.number_input("MUAC (cm)", value=0.0, key="m2")
            hb_after = a4.number_input("Hb (g/dL)", value=0.0, key="hb2")
        with col_a2:
            img_after = st.file_uploader("Upload 'After' Photo", type=["jpg", "jpeg", "png"], key="img_a")
            
        st.divider()
        
        st.subheader("📝 5. Medical Officer's Narrative")
        narrative = st.text_area("Write the human story here. How did the parents react? How did the child transform?", height=150)
        
        submit_btn = st.form_submit_button("🎨 Generate Digital Success Story PDF", use_container_width=True)

    if submit_btn:
        if not name or not location:
            st.error("⚠️ Please enter at least the Child's Name and Location.")
        else:
            with st.spinner("Painting the Digital Success Story..."):
                from fpdf import FPDF
                from PIL import Image
                import tempfile
                
                def save_temp_img(upload):
                    if upload is not None:
                        img = Image.open(upload)
                        if img.mode != 'RGB': img = img.convert('RGB')
                        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
                        img.save(temp_file.name)
                        return temp_file.name
                    return None

                path_before = save_temp_img(img_before)
                path_after = save_temp_img(img_after)

                try:
                    pdf = FPDF(orientation="P", unit="mm", format="A4")
                    pdf.add_page()
                    pdf.set_auto_page_break(auto=False)

                    pdf.set_fill_color(41, 128, 185)
                    pdf.rect(0, 0, 210, 35, 'F')
                    pdf.set_text_color(255, 255, 255)
                    pdf.set_font("Helvetica", "B", 22)
                    pdf.set_xy(10, 8)
                    pdf.cell(190, 10, "FROM SURVIVAL TO HEALTHY SURVIVAL", ln=True, align="C")
                    pdf.set_font("Helvetica", "", 12)
                    pdf.cell(190, 8, f"A Journey to Health: {name} ({age}, {gender})", ln=True, align="C")
                    pdf.cell(190, 8, f"Location: {location}", ln=True, align="C")

                    pdf.set_fill_color(253, 237, 236)
                    pdf.rect(10, 45, 190, 55, 'F')
                    pdf.set_text_color(192, 57, 43)
                    pdf.set_font("Helvetica", "B", 14)
                    pdf.set_xy(15, 50)
                    pdf.cell(90, 8, "1. THE DISCOVERY", ln=True)
                    
                    pdf.set_text_color(0, 0, 0)
                    pdf.set_font("Helvetica", "", 11)
                    pdf.set_xy(15, 60)
                    pdf.multi_cell(100, 6, f"Date: {date_before}\nDiagnosis: {diagnosis}\nWeight: {w_before} kg   |   Height: {h_before} cm\nMUAC: {m_before} cm   |   Hb: {hb_before} g/dL")
                    
                    if path_before:
                        pdf.image(path_before, x=130, y=50, w=60, h=45)

                    pdf.set_fill_color(235, 245, 251)
                    pdf.rect(10, 105, 190, 45, 'F')
                    pdf.set_text_color(41, 128, 185)
                    pdf.set_font("Helvetica", "B", 14)
                    pdf.set_xy(15, 110)
                    pdf.cell(190, 8, "2. THE INTERVENTION", ln=True)
                    
                    pdf.set_text_color(0, 0, 0)
                    pdf.set_font("Helvetica", "", 11)
                    pdf.set_xy(15, 120)
                    pdf.multi_cell(180, 6, f"Referred To: {referred_to}\nDuration of Care: {days_care}\nTreatment Provided: {treatment}")

                    pdf.set_fill_color(234, 250, 234)
                    pdf.rect(10, 155, 190, 55, 'F')
                    pdf.set_text_color(39, 174, 96)
                    pdf.set_font("Helvetica", "B", 14)
                    pdf.set_xy(15, 160)
                    pdf.cell(90, 8, "3. THE TRIUMPH", ln=True)
                    
                    pdf.set_text_color(0, 0, 0)
                    pdf.set_font("Helvetica", "", 11)
                    pdf.set_xy(15, 170)
                    pdf.multi_cell(100, 6, f"Date: {date_after}\nStatus: {status}\nWeight: {w_after} kg   |   Height: {h_after} cm\nMUAC: {m_after} cm   |   Hb: {hb_after} g/dL")
                    
                    if path_after:
                        pdf.image(path_after, x=130, y=160, w=60, h=45)

                    pdf.set_text_color(0, 0, 0)
                    pdf.set_font("Helvetica", "I", 12)
                    pdf.set_xy(15, 220)
                    pdf.multi_cell(180, 6, f"\"{narrative}\"")

                    pdf.set_font("Helvetica", "B", 10)
                    pdf.set_xy(15, 275)
                    pdf.cell(80, 5, "DR. NIHAR UPADHYAY", ln=True)
                    pdf.set_xy(15, 280)
                    pdf.cell(80, 5, f"Medical Officer", ln=True)

                    pdf.set_xy(115, 275)
                    pdf.cell(80, 5, "DR. ALPESH BHESANIYA", ln=True, align="R")
                    pdf.set_xy(115, 280)
                    pdf.cell(80, 5, "TALUKA HEALTH OFFICER", ln=True, align="R")

                    pdf_bytes = bytes(pdf.output())
                    st.success("✅ Success Story Generated Flawlessly!")
                    
                    import base64
                    b64 = base64.b64encode(pdf_bytes).decode()
                    html_button = f'''
                        <a href="data:application/pdf;base64,{b64}" download="Success_Story_{name}.pdf" target="_blank" 
                           style="display: inline-block; padding: 14px 24px; background-color: #e11d48; color: white; 
                           text-decoration: none; border-radius: 8px; font-weight: bold; text-align: center; width: 100%;">
                           📄 Tap Here to View / Download Success Story PDF
                        </a>
                    '''
                    st.markdown(html_button, unsafe_allow_html=True)
                    
                except Exception as e:
                    st.error(f"⚠️ An error occurred while painting the PDF: {e}")

# ==========================================
# MODULE 7: ANEMIA TRACKER
# ==========================================
elif menu == "7. Anemia Tracker":
    render_header("T3 camps and taluka Anemia statistics", "easily enter T3 camp data and analyze", "📅", "#f59e0b")
    st.write("Track Hemoglobin levels and analyze historical trends.")

    tab_dash, tab_entry = st.tabs(["📈 Interactive Dashboard", "➕ Enter New Camp Data"])

    with tab_dash:
        if not df_anemia.empty:
            df_anemia['HB LEVEL'] = pd.to_numeric(df_anemia['HB LEVEL'], errors='coerce')
            df_anemia['CAMP DATE'] = pd.to_datetime(df_anemia['CAMP DATE'], errors='coerce')
            clean_df = df_anemia.dropna(subset=['HB LEVEL'])

            st.markdown("### 🔍 Filter Your Data")
            f_col1, f_col2 = st.columns(2)
            phc_list = ["All"] + sorted([str(x) for x in clean_df['PHC/CHC/UPHC'].unique() if str(x) != 'nan'])
            village_list = ["All"] + sorted([str(x) for x in clean_df['VILLAGE'].unique() if str(x) != 'nan'])

            with f_col1: selected_phc = st.selectbox("🏥 Filter by PHC/CHC/UPHC:", phc_list)
            with f_col2: selected_village = st.selectbox("🏘️ Filter by Village:", village_list)

            filtered_df = clean_df.copy()
            if selected_phc != "All": filtered_df = filtered_df[filtered_df['PHC/CHC/UPHC'].astype(str) == selected_phc]
            if selected_village != "All": filtered_df = filtered_df[filtered_df['VILLAGE'].astype(str) == selected_village]

            st.divider()

            st.markdown(f"### 📊 Key Metrics (Showing: {len(filtered_df)} patients)")
            m1, m2, m3 = st.columns(3)
            m1.metric("Total Screened", len(filtered_df))
            severe_cases = len(filtered_df[filtered_df['SEVERITY'].astype(str).str.strip().str.upper() == 'SEVERE'])
            m2.metric("Severe Cases", severe_cases)
            avg_hb = filtered_df['HB LEVEL'].mean()
            m3.metric("Average Hb Level", f"{avg_hb:.1f} g/dL" if pd.notna(avg_hb) else "N/A")

            st.divider()
            
            st.markdown("### 📈 Analytics & Trends")
            st.write("**Average Hemoglobin Levels Over Time (Camp Dates)**")
            
            if not filtered_df.empty and not filtered_df['CAMP DATE'].isnull().all():
                trend_df = filtered_df.dropna(subset=['CAMP DATE'])
                trend_df = trend_df.groupby('CAMP DATE')['HB LEVEL'].mean().reset_index()
                trend_df = trend_df.sort_values('CAMP DATE')
                trend_df.set_index('CAMP DATE', inplace=True)
                st.line_chart(trend_df, y='HB LEVEL', color="#1f77b4")
            else:
                st.info("Not enough valid date data to show trends.")

            col_chart1, col_chart2 = st.columns(2)
            with col_chart1:
                st.write("**Severity Breakdown**")
                sev_counts = filtered_df['SEVERITY'].value_counts()
                st.bar_chart(sev_counts, color="#FF4B4B")
                
            with col_chart2:
                st.write("**Cases by Village/Location**")
                village_counts = filtered_df['VILLAGE'].value_counts().head(10)
                st.bar_chart(village_counts)
            
        else:
            st.info("No data available in the ANEMIA sheet yet.")

    with tab_entry:
        st.subheader("Log New Anemia Screening")
        with st.form("anemia_form"):
            a_col1, a_col2 = st.columns(2)
            with a_col1:
                facility = st.text_input("PHC / CHC / UPHC")
                camp_date = st.date_input("Camp Date")
                village = st.text_input("Village Location")
            with a_col2:
                child_name = st.text_input("Child's Name")
                dob = st.date_input("Date of Birth")
                gender = st.selectbox("Gender", ["M", "F"])

            st.markdown("---")
            st.write("**Clinical Results**")
            hb_level = st.number_input("Hemoglobin (Hb) Level (g/dL)", min_value=0.0, max_value=25.0, step=0.1)

            submit_anemia = st.form_submit_button("💾 Save & Auto-Categorize")

            if submit_anemia:
                if facility == "" or child_name == "":
                    st.error("🚨 Please fill in both the Facility and Child Name.")
                elif hb_level == 0.0:
                    st.error("🚨 Please enter a valid Hb level greater than 0.")
                else:
                    if hb_level < 8.0:
                        calculated_severity = "Severe"
                    elif 8.0 <= hb_level <= 10.9:
                        calculated_severity = "Moderate"
                    elif 11.0 <= hb_level <= 11.4:
                        calculated_severity = "Mild"
                    else:
                        calculated_severity = "Normal"

                    try:
                        anemia_sheet = spreadsheet.worksheet("ANEMIA")
                        row_data = [
                            facility, str(camp_date), village, child_name, 
                            str(dob), gender, hb_level, calculated_severity
                        ]
                        anemia_sheet.append_row(row_data)
                        
                        st.toast("✅ Anemia Record Saved!", icon="🩸")
                        st.success(f"✅ Saved **{child_name}**! With an Hb of {hb_level}, they were automatically categorized as: **{calculated_severity}**.")
                    except Exception as e:
                        st.error(f"⚠️ Error: Could not find the 'ANEMIA' tab. Detail: {e}")

# ==========================================
# MODULE 8: SCHOOL DIRECTORY
# ==========================================
elif menu == "8. School Directory":
    render_header("Master School Data Management", "Get all info about schools", "🗄️", "#4f46e5")
    st.write("Instantly look up school demographics, principals, and class sizes.")

    if not df_directory.empty:
        school_options = sorted([str(x) for x in df_directory['School'].unique() if str(x) != 'nan' and str(x).strip() != ''])
        selected_school = st.selectbox("Select a School to view its ID Card:", ["-- Select a School --"] + school_options)
        
        if selected_school != "-- Select a School --":
            s_data = df_directory[df_directory['School'] == selected_school].iloc[0]
            st.divider()
            
            st.subheader(f"📍 {selected_school}")
            c1, c2, c3 = st.columns(3)
            c1.info(f"**Type:** {s_data.get('PRIMARY/HIGH SCHOOL', 'N/A')}")
            c2.info(f"**Category:** {s_data.get('GOVT/PRIVATE', 'N/A')}")
            c3.info(f"**PHC:** {s_data.get('PHC', 'N/A')}")
            
            st.markdown("### 👨‍🏫 Administrative Contact")
            st.success(f"**Principal:** {s_data.get('PRINCIPAL NAME', 'N/A')} | 📞 **Phone:** {s_data.get('PRINCIPAL CONTACT NUMBER', 'N/A')}")
            
            st.markdown("### 📊 Overall Student Strength")
            m1, m2, m3 = st.columns(3)
            m1.metric("👦 Total Boys", s_data.get('TOTAL BOYS', '0'))
            m2.metric("👧 Total Girls", s_data.get('TOTAL GIRLS', '0'))
            m3.metric("🏫 Grand Total", s_data.get('TOTAL', '0'))
            
            st.markdown("### 📋 Class-by-Class Breakdown")
            class_prefixes = ['BV', 'CLS1', 'CLS2', 'CLS3', 'CLS4', 'CLS5', 'CLS6', 'CLS7', 'CLS8', 'CLS9', 'CLS10', 'CLS11', 'CLS12']
            class_names = ['Bal Vatika', 'Class 1', 'Class 2', 'Class 3', 'Class 4', 'Class 5', 'Class 6', 'Class 7', 'Class 8', 'Class 9', 'Class 10', 'Class 11', 'Class 12']
            breakdown_list = []
            
            for prefix, readable_name in zip(class_prefixes, class_names):
                total_val = str(s_data.get(f'Total_{prefix}', '0')).strip()
                if total_val not in ['0', '0.0', 'nan', '', 'None']:
                    breakdown_list.append({
                        "Standard": readable_name,
                        "Boys": str(s_data.get(f'{prefix}_B', '0')),
                        "Girls": str(s_data.get(f'{prefix}_G', '0')),
                        "Transgender": str(s_data.get(f'{prefix}_TG', '0')),
                        "Total Students": total_val
                    })
            
            if breakdown_list:
                df_breakdown = pd.DataFrame(breakdown_list)
                st.dataframe(df_breakdown, use_container_width=True, hide_index=True)
            else:
                st.warning("No student demographic data is currently available for this school.")
    else:
        st.error("⚠️ Could not load data from the 'ALL SCHOOL DETAILS' tab.")

# ==========================================
# MODULE 9: ANGANWADI DIRECTORY 
# ==========================================
elif menu == "9. Anganwadi Directory":
    render_header("Anganvadi Information", "All Anganvadi details at your fingertips", "⚙️", "#64748b")
    st.write("Instantly look up Anganwadi Workers, their contact numbers, and live enrollment data.")

    # 🚀 NEW: Sleek Tabbed Interface!
    tab_search, tab_summary = st.tabs(["🔍 Directory Search", "📊 Master Summary Table"])

    with tab_search:
        if not df_aw_contacts.empty:
            awc_col = df_aw_contacts.columns[0] 
            for col in df_aw_contacts.columns:
                if 'AWC' in col.upper() or 'NAME' in col.upper():
                    awc_col = col
                    break
                    
            aw_summary = {}
            if not df_aw.empty and 'AWC Name' in df_aw.columns:
                aw_summary = df_aw['AWC Name'].value_counts().to_dict()

            def format_awc_dropdown(awc_name):
                if awc_name == "-- Select Center --":
                    return awc_name
                count = aw_summary.get(awc_name, 0)
                return f"{awc_name}  👶 ({count} Enrolled)"
                    
            awc_options = sorted([str(x) for x in df_aw_contacts[awc_col].unique() if str(x) != 'nan' and str(x).strip() != ''])
            
            selected_awc = st.selectbox("Select an Anganwadi Center:", ["-- Select Center --"] + awc_options, format_func=format_awc_dropdown)
            
            if selected_awc != "-- Select Center --":
                contact_info = df_aw_contacts[df_aw_contacts[awc_col] == selected_awc].iloc[0]
                
                st.divider()
                st.subheader(f"🏠 {selected_awc}")
                
                if not df_aw.empty and 'AWC Name' in df_aw.columns:
                    aw_data = df_aw[df_aw['AWC Name'] == selected_awc]
                    total_kids = len(aw_data)
                    
                    gender_col = next((c for c in aw_data.columns if str(c).lower() == 'gender'), None)
                    if gender_col:
                        boys = len(aw_data[aw_data[gender_col].astype(str).str.upper().str.startswith('M')])
                        girls = len(aw_data[aw_data[gender_col].astype(str).str.upper().str.startswith('F')])
                    else:
                        boys, girls = 0, 0
                    
                    st.markdown("#### 📊 Live Enrollment Summary")
                    c1, c2, c3 = st.columns(3)
                    c1.metric("👶 Total Children", total_kids)
                    c2.metric("👦 Boys", boys)
                    c3.metric("👧 Girls", girls)
                    st.write("---")
                
                st.markdown("#### 📞 Contact Information")
                for col in df_aw_contacts.columns:
                    if col != awc_col:  
                        val = str(contact_info[col]).strip()
                        if val not in ['', 'nan', 'None']:
                            st.success(f"**{col}:** {val}")
                            
        else:
            st.error("⚠️ Could not load data from the 'aw_master_directory' tab. Please ensure the tab is spelled exactly right in your Google Sheet.")

    with tab_summary:
        st.subheader("📈 Master Enrollment Summary")
        st.write("A complete numerical breakdown of all Anganwadi centers dynamically generated from your Master Database.")
        
        if not df_aw.empty and 'AWC Name' in df_aw.columns:
            summary_data = []
            gender_col = next((c for c in df_aw.columns if str(c).lower() == 'gender'), None)
            
            # Loop through every unique Anganwadi and count the children!
            for awc in df_aw['AWC Name'].dropna().unique():
                aw_data = df_aw[df_aw['AWC Name'] == awc]
                total = len(aw_data)
                
                if gender_col:
                    boys = len(aw_data[aw_data[gender_col].astype(str).str.upper().str.startswith('M')])
                    girls = len(aw_data[aw_data[gender_col].astype(str).str.upper().str.startswith('F')])
                else:
                    boys, girls = 0, 0
                    
                summary_data.append({
                    "Anganwadi Center": str(awc).strip(),
                    "Total Children": total,
                    "👦 Boys": boys,
                    "👧 Girls": girls
                })
            
            if summary_data:
                summary_df = pd.DataFrame(summary_data).sort_values(by="Anganwadi Center")
                
                # Calculate Grand Totals for the header
                total_all = summary_df['Total Children'].sum()
                total_boys = summary_df['👦 Boys'].sum()
                total_girls = summary_df['👧 Girls'].sum()
                
                st.info(f"🏆 **Grand Total Block Enrollment:** {total_all} Children ({total_boys} Boys | {total_girls} Girls)")
                
                import datetime
                csv_summary = summary_df.to_csv(index=False).encode('utf-8-sig')
                st.download_button(
                    label="⬇️ Download Master Summary (CSV)",
                    data=csv_summary,
                    file_name=f"Anganwadi_Master_Summary_{datetime.date.today()}.csv",
                    mime="text/csv"
                )
                
                st.dataframe(summary_df, use_container_width=True, hide_index=True)
        else:
            st.info("⚠️ No enrollment data available in the master database to generate a summary.")

# ==========================================
# MODULE 10: STAFF DIRECTORY
# ==========================================
elif menu == "10. Staff Directory":
    render_header("All staff data", "Reach out to anyone and Communicate", "🆘", "#ec4899")
    st.write("Filter by Headquarter or Designation to find your team members instantly.")

    if not df_staff.empty:
        desig_col = None
        hq_col = None
        for col in df_staff.columns:
            col_upper = col.upper()
            if "DESIGNATION" in col_upper or "ROLE" in col_upper or "POST" in col_upper:
                desig_col = col
            if "HEADQUARTER" in col_upper or "HQ" in col_upper or "BLOCK" in col_upper:
                hq_col = col

        f_col1, f_col2, f_col3 = st.columns(3)
        with f_col1:
            search_query = st.text_input("🔍 Search by Name:")
        with f_col2:
            if hq_col:
                hqs = ["All"] + sorted([str(x) for x in df_staff[hq_col].unique() if str(x).strip() not in ['', 'nan']])
                selected_hq = st.selectbox("📍 Filter by Headquarter:", hqs)
            else: selected_hq = "All"
        with f_col3:
            if desig_col:
                roles = ["All"] + sorted([str(x) for x in df_staff[desig_col].unique() if str(x).strip() not in ['', 'nan']])
                selected_role = st.selectbox("⚕️ Filter by Designation:", roles)
            else: selected_role = "All"

        filtered_staff = df_staff.copy()
        if search_query:
            name_col = df_staff.columns[0]
            for col in df_staff.columns:
                if "NAME" in col.upper():
                    name_col = col
                    break
            mask = filtered_staff[name_col].astype(str).str.contains(search_query, case=False, na=False)
            filtered_staff = filtered_staff[mask]

        if hq_col and selected_hq != "All": filtered_staff = filtered_staff[filtered_staff[hq_col] == selected_hq]
        if desig_col and selected_role != "All": filtered_staff = filtered_staff[filtered_staff[desig_col] == selected_role]

        st.divider()

        if not filtered_staff.empty:
            st.write(f"**Showing {len(filtered_staff)} staff member(s):**")
            display_df = filtered_staff.replace('nan', '').fillna('')
            st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.warning("No staff members found matching your filters.")
    else:
        st.error("⚠️ Could not load data from the 'master_staff_directory' tab.")

# ==========================================
# MODULE 11: ANNUAL FY PLANNER
# ==========================================
elif menu == "11. Annual FY Planner":
    render_header("Roadmap of whole year in advance!", "Plan your work together!", "🏥", "#e11d48")
    st.write("Annual roadmap, campaign timelines, and real-time workload calculations.")

    tab_timeline, tab_calculator, tab_monthly = st.tabs([
        "📊 Interactive Master Timeline", "🧮 Workload & Resource Calculator", "📋 Monthly Target Focus"
    ])

    with tab_timeline:
        st.subheader("RBSK Annual Campaign Roadmap (Apr 2026 - Mar 2027)")
        st.write("Hover over the blocks to see specific dates and campaign details.")
        
        schedule_data = [
            {"Task": "AWC Cycle 1", "Start": "2026-04-01", "Finish": "2026-09-30", "Category": "Anganwadi"},
            {"Task": "AWC Cycle 2", "Start": "2026-10-01", "Finish": "2027-02-28", "Category": "Anganwadi"},
            {"Task": "School Summer Vacations", "Start": "2026-04-15", "Finish": "2026-06-10", "Category": "Vacations/Exams"},
            {"Task": "Diwali Vacations", "Start": "2026-10-20", "Finish": "2026-11-10", "Category": "Vacations/Exams"},
            {"Task": "HBNC & Delivery Points Focus", "Start": "2026-04-01", "Finish": "2026-06-15", "Category": "Special Focus"},
            {"Task": "MR Vaccine Campaign (Schools)", "Start": "2026-06-15", "Finish": "2026-08-31", "Category": "Special Focus"},
            {"Task": "School Main Screening Phase", "Start": "2026-11-11", "Finish": "2027-02-28", "Category": "Schools"},
            {"Task": "Buffer & Mop-up Month", "Start": "2027-03-01", "Finish": "2027-03-31", "Category": "Buffer"}
        ]
        
        df_schedule = pd.DataFrame(schedule_data)
        
        fig_gantt = px.timeline(
            df_schedule, x_start="Start", x_end="Finish", y="Task", color="Category",
            color_discrete_map={
                "Anganwadi": "#2ca02c", "Schools": "#1f77b4", 
                "Vacations/Exams": "#7f7f7f", "Special Focus": "#ff7f0e", "Buffer": "#d62728"
            }
        )
        fig_gantt.update_yaxes(autorange="reversed") 
        st.plotly_chart(fig_gantt, use_container_width=True)

    with tab_calculator:
        st.subheader("⚙️ Target Feasibility Calculator")
        st.write("Calculates exact working days available in FY 2026-27 and compares it to your caseload.")
        
        if not df_aw_master.empty and not df_all_students.empty:
            total_awc_kids = len(df_aw_master)
            total_school_kids = len(df_all_students)
            total_screenings_target = (total_awc_kids * 2) + total_school_kids
            
            fy_dates = pd.date_range(start="2026-04-01", end="2027-03-31")
            total_days_in_fy = len(fy_dates)
            sundays = (fy_dates.weekday == 6).sum()
            saturdays = (fy_dates.weekday == 5).sum()
            
            st.markdown("### 1. Available Time (FY 26-27)")
            c1, c2, c3 = st.columns(3)
            public_holidays = c1.number_input("Public Holidays (Weekdays)", min_value=0, max_value=40, value=18)
            
            saturday_loss = saturdays * 0.5
            available_working_days = total_days_in_fy - sundays - public_holidays - saturday_loss
            
            c2.metric("Total Days in FY", total_days_in_fy)
            c3.metric("Net Working Days Available", f"{available_working_days:g}")
            
            st.markdown("### 2. Team Capacity (1 MHT = 4 Members)")
            c4, c5 = st.columns(2)
            with c4:
                daily_target = st.slider("Target Screenings per day (for your team)", min_value=40, max_value=120, value=70, step=5)
            with c5:
                st.info("🧑‍⚕️ **Team Size:** 1 Dedicated Mobile Health Team")
                active_teams = 1 
            
            daily_district_capacity = daily_target * active_teams
            working_days_needed = total_screenings_target / daily_district_capacity if daily_district_capacity > 0 else 0
            
            st.divider()
            st.markdown("### 📊 The Final Verdict")
            
            m1, m2, m3 = st.columns(3)
            m1.metric("Total Screenings Required", f"{total_screenings_target:,}")
            m2.metric("Working Days Needed", f"{working_days_needed:.1f}")
            
            margin = available_working_days - working_days_needed
            m3.metric("Buffer Days (+/-)", f"{margin:.1f}")
            
            if margin >= 30:
                st.success(f"✅ **HIGHLY FEASIBLE:** Your team needs {working_days_needed:.1f} days. You have {available_working_days:g} days available. You will easily finish with a comfortable {margin:.1f} day buffer!")
            elif margin >= 0:
                st.warning(f"⚠️ **TIGHT SCHEDULE:** Your team needs {working_days_needed:.1f} days. You have {available_working_days:g} days available. You will finish, but there is very little room for sick days or delays.")
            else:
                st.error(f"🚨 **MATHEMATICALLY IMPOSSIBLE:** You need {working_days_needed:.1f} days, but only have {available_working_days:g} working days. You MUST increase your daily average above {daily_target} kids/day.")
        else:
            st.warning("⚠️ Cannot calculate. Ensure 'aw new data' and '1240315 ALL STUDENTS NAMES' are loaded.")

    with tab_monthly:
        st.subheader("📋 Team Focus by Month")
        
        with st.expander("🌸 April - May 2026 (Exams & Summer Vacation)"):
            st.write("- **Schools:** CLOSED (Exams and Vacations).")
            st.write("- **AWC Focus:** Launch AWC Cycle 1.")
            st.write("- **Special Tasks:** Heavy focus on Delivery Point screening and HBNC (Newborn) visits.")
            
        with st.expander("☀️ June - August 2026 (MR Campaign)"):
            st.write("- **Schools:** REOPENED. Priority shifted to MR Vaccine Campaigns.")
            st.write("- **AWC Focus:** Continue AWC Cycle 1 seamlessly alongside MR tracking.")
            
        with st.expander("🍂 September 2026 (Mid-Year Deadline)"):
            st.write("- **AWC Focus:** CRITICAL - Finish 100% of AWC Cycle 1.")
            st.write("- **Schools:** Preparation for main screening phase post-MR campaign.")
            
        with st.expander("🪔 October - November 2026 (Diwali Shift)"):
            st.write("- **Schools:** Paused during Diwali holidays. Resume heavy screening mid-November.")
            st.write("- **AWC Focus:** Launch AWC Cycle 2 immediately after Diwali.")
            
        with st.expander("❄️ December 2026 - February 2027 (The Final Push)"):
            st.write("- **Schools:** Full speed school screenings.")
            st.write("- **AWC Focus:** Full speed AWC Cycle 2.")
            st.write("- **Goal:** Achieve 95%+ completion by Feb 28 to avoid year-end rush.")
            
        with st.expander("🌼 March 2027 (Mop-Up & Reporting)"):
            st.write("- **Field Work:** Mop-up rounds for absent children only.")
            st.write("- **Admin:** Success story generation, data entry, and final state-level reporting.")

# ==========================================
# MODULE 12: AUTOMATED STATE REPORTING & SCOREBOARD
# ==========================================
elif menu == "12. Automated State Report":
    render_header("Automatic Report Generator", "Get real-time reports", "📅", "#f59e0b")
    st.write("Generate official Form III exports and track your team's annual targets.")

    tab_form3, tab_scoreboard = st.tabs(["📄 Form III (Govt Export)", "🎯 Live Scoreboard (Target vs. Achievement)"])

    df_aw_daily, df_sch_daily, df_combined = get_daily_logs()

    if not df_aw_daily.empty or not df_sch_daily.empty:
        if not df_aw_daily.empty: df_aw_daily['Source'] = 'Anganwadi'
        if not df_sch_daily.empty: df_sch_daily['Source'] = 'School'
        
        df_combined = pd.concat([df_aw_daily, df_sch_daily], ignore_index=True)
        
        def find_col(df, keywords):
            for col in df.columns:
                if any(k.lower() in str(col).lower() for k in keywords): return col
            return None

        date_col = find_col(df_combined, ['date of screening', 'screening date', 'date'])
        dob_col = find_col(df_combined, ['dob', 'date of birth'])
        gender_col = find_col(df_combined, ['gender', 'sex'])
        disease_col = find_col(df_combined, ['disease', '4d', 'defect'])
        status_col = find_col(df_combined, ['status', 'sam', 'mam'])
        # Necessary for the Scoreboard Backtracking
        inst_col_daily = find_col(df_combined, ['inst', 'school', 'center', 'awc'])

        if date_col and dob_col:
            df_combined[date_col] = df_combined[date_col].astype(str).str.strip()
            df_combined[dob_col] = df_combined[dob_col].astype(str).str.strip()
            
            df_combined[date_col] = df_combined[date_col].str.replace('/', '-').str.replace('.', '-', regex=False)
            df_combined[dob_col] = df_combined[dob_col].str.replace('/', '-').str.replace('.', '-', regex=False)
            
            df_combined[date_col] = pd.to_datetime(df_combined[date_col], dayfirst=True, errors='coerce')
            df_combined[dob_col] = pd.to_datetime(df_combined[dob_col], dayfirst=True, errors='coerce')
            
            df_combined = df_combined.dropna(subset=[date_col])

    # ==========================================
    # 📄 TAB 1: FORM III (ORIGINAL CODE - UNTOUCHED)
    # ==========================================
    with tab_form3:
        if not df_combined.empty and date_col and dob_col:
            st.write("### 🗓️ Report Timeframe")
            
            col_y, col_m = st.columns(2)
            with col_y:
                selected_year = st.selectbox("📅 Select Year", ["2024", "2025", "2026", "2027"], index=2)
            with col_m:
                months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
                import datetime
                current_month_index = datetime.datetime.now().month - 1
                selected_month = st.selectbox("🗓️ Select Month", months, index=current_month_index)
            
            st.divider()

            month_num = months.index(selected_month) + 1
            report_df = df_combined[
                (df_combined[date_col].dt.year == int(selected_year)) & 
                (df_combined[date_col].dt.month == month_num)
            ].copy()

            if report_df.empty:
                st.info(f"No screenings found for {selected_month} {selected_year}.")
            else:
                child_name_cols = [c for c in report_df.columns if any(k in str(c).lower() for k in ['name', 'child', 'student', 'beneficiary'])]
                if child_name_cols:
                    report_df['Official_Child_Name'] = report_df[child_name_cols[0]]
                    for col in child_name_cols[1:]:
                        report_df['Official_Child_Name'] = report_df['Official_Child_Name'].combine_first(report_df[col])
                else:
                    report_df['Official_Child_Name'] = "Unknown"

                inst_name_cols = [c for c in report_df.columns if any(k in str(c).lower() for k in ['inst', 'school', 'awc', 'center', 'aw name'])]
                if inst_name_cols:
                    report_df['Official_Institution'] = report_df[inst_name_cols[0]]
                    for col in inst_name_cols[1:]:
                        report_df['Official_Institution'] = report_df['Official_Institution'].combine_first(report_df[col])
                else:
                    report_df['Official_Institution'] = "Unknown"

                report_df['Age_Years'] = (report_df[date_col] - report_df[dob_col]).dt.days / 365.25
                
                def bucket_age(age):
                    if pd.isna(age): return "Unknown"
                    if age <= 3.0: return "0-3 Years"
                    elif age <= 6.0: return "3-6 Years"
                    else: return "6-18 Years"
                
                report_df['Govt_Age_Bucket'] = report_df['Age_Years'].apply(bucket_age)
                
                if gender_col:
                    report_df['Clean_Gender'] = report_df[gender_col].astype(str).str.upper().str[0]
                else:
                    report_df['Clean_Gender'] = "U"

                st.markdown(f"### 📊 Official Form III Output: **{selected_month} {selected_year}**")
                st.write(f"Total Children Screened this month: **{len(report_df)}**")

                col_0_3, col_3_6, col_6_18 = st.columns(3)
                
                def render_bucket_stats(bucket_name, column_ui):
                    bucket_data = report_df[report_df['Govt_Age_Bucket'] == bucket_name]
                    boys = len(bucket_data[bucket_data['Clean_Gender'] == 'M'])
                    girls = len(bucket_data[bucket_data['Clean_Gender'] == 'F'])
                    
                    with column_ui:
                        st.info(f"**{bucket_name}**")
                        st.metric("Total", len(bucket_data))
                        st.write(f"👦 Boys: **{boys}**")
                        st.write(f"👧 Girls: **{girls}**")
                
                render_bucket_stats("0-3 Years", col_0_3)
                render_bucket_stats("3-6 Years", col_3_6)
                render_bucket_stats("6-18 Years", col_6_18)

                unknown_count = len(report_df[report_df['Govt_Age_Bucket'] == 'Unknown'])
                if unknown_count > 0:
                    st.warning(f"⚠️ **DATA ALERT:** There are **{unknown_count} children** with a missing or invalid Date of Birth. They cannot be sorted into the age buckets.")

                st.divider()
                st.markdown("### 🚨 Disease & Malnutrition Referrals")
                
                m1, m2 = st.columns(2)
                with m1:
                    st.write("**Nutritional Triage**")
                    if status_col:
                        sam_count = len(report_df[report_df[status_col].astype(str).str.upper() == 'SAM'])
                        mam_count = len(report_df[report_df[status_col].astype(str).str.upper() == 'MAM'])
                        st.error(f"🔴 SAM Cases: **{sam_count}**")
                        st.warning(f"🟡 MAM Cases: **{mam_count}**")
                    else:
                        st.write("No nutrition status column found.")
                        
                with m2:
                    st.write("**4D Conditions Found**")
                    if disease_col:
                        def is_real_disease(val):
                            clean = str(val).strip().lower()
                            return clean not in ['', 'nan', 'none', 'no', 'null', 'na', 'false']
                            
                        diseases = report_df[report_df[disease_col].apply(is_real_disease)]
                        if not diseases.empty:
                            disease_counts = diseases[disease_col].value_counts().reset_index()
                            disease_counts.columns = ['Condition', 'Count']
                            st.dataframe(disease_counts, use_container_width=True, hide_index=True)
                        else:
                            st.success("No 4D diseases logged this month!")
                            
                st.divider()
                st.markdown("### 📥 Download Cleaned Report")
                
                export_df = pd.DataFrame()
                export_df['Screening Date'] = report_df[date_col].dt.strftime('%d-%m-%Y')
                export_df['Source'] = report_df['Source']
                export_df['Institution'] = report_df['Official_Institution'] 
                export_df['Child Name'] = report_df['Official_Child_Name']    
                export_df['DOB'] = report_df[dob_col].dt.strftime('%d-%m-%Y')
                export_df['Calculated Age (Yrs)'] = report_df['Age_Years'].round(2)
                export_df['Govt Age Bucket'] = report_df['Govt_Age_Bucket']
                export_df['Gender'] = report_df['Clean_Gender']
                
                if status_col: export_df['Nutrition (SAM/MAM)'] = report_df[status_col]
                if disease_col: export_df['4D Condition Found'] = report_df[disease_col]

                with st.expander("👁️ Preview Streamlined CSV Data"):
                    st.dataframe(export_df, use_container_width=True, hide_index=True)

                csv = export_df.to_csv(index=False).encode('utf-8-sig')
                st.download_button(
                    label=f"⬇️ Download Streamlined {selected_month} Data (CSV)",
                    data=csv,
                    file_name=f"RBSK_Form_III_{selected_month}_{selected_year}.csv",
                    mime="text/csv",
                )
        else:
            st.info("No valid daily screening data found yet to generate Form III. Start screening in Module 2!")

    # ==========================================
    # 🎯 TAB 2: LIVE SCOREBOARD (RE-CODED WITH BACKTRACKING + AUTO-TARGET)
    # ==========================================
    with tab_scoreboard:
        st.subheader("🏆 Team-wise Performance Scoreboard")
        st.markdown("**Block:** Visavadar | **District:** Junagadh")

        try:
            with st.spinner("Calculating Targets and Backtracking Achievements..."):
                # 1. FETCH MASTER PLAN TO BUILD THE "BACKTRACKING MAP"
                master_aw = pd.DataFrame(spreadsheet.worksheet("aw new data").get_all_records())
                master_sch = pd.DataFrame(spreadsheet.worksheet("1240315 ALL STUDENTS NAMES").get_all_records())

                # Search for correct columns in Master Sheets
                def find_m_col(df, keys):
                    return next((c for c in df.columns if any(k in str(c).upper() for k in keys)), None)

                aw_loc_key = find_m_col(master_aw, ["INSTITUTE", "AWC", "CENTER"])
                aw_team_key = find_m_col(master_aw, ["TEAM"])
                sch_loc_key = find_m_col(master_sch, ["INSTITUTION", "SCHOOL"])
                sch_team_key = find_m_col(master_sch, ["TEAM"])

                # Create the Lookup Dictionary
                team_lookup = {}
                if aw_loc_key and aw_team_key:
                    team_lookup.update(dict(zip(master_aw[aw_loc_key].astype(str).str.strip(), master_aw[aw_team_key].astype(str).str.strip())))
                if sch_loc_key and sch_team_key:
                    team_lookup.update(dict(zip(master_sch[sch_loc_key].astype(str).str.strip(), master_sch[sch_team_key].astype(str).str.strip())))

                # Calculate Targets
                targets = {}
                for t_id in ["TEAM-1240315", "TEAM-1240309"]:
                    count = 0
                    if aw_team_key: count += len(master_aw[master_aw[aw_team_key].astype(str).str.strip() == t_id])
                    if sch_team_key: count += len(master_sch[master_sch[sch_team_key].astype(str).str.strip() == t_id])
                    targets[t_id] = count

            # 2. RENDER PERFORMANCE FOR BOTH TEAMS
            if not df_combined.empty and inst_col_daily:
                # The Magic: Map daily rows to Teams via Institute Name
                df_combined['Mapped_Team'] = df_combined[inst_col_daily].astype(str).str.strip().map(team_lookup)
                
                for t_id in ["TEAM-1240315", "TEAM-1240309"]:
                    t_target = targets.get(t_id, 0)
                    t_achieved = len(df_combined[df_combined['Mapped_Team'] == t_id])
                    t_pct = (t_achieved / t_target * 100) if t_target > 0 else 0

                    st.markdown(f"#### 🏥 Team: {t_id}")
                    sc1, sc2, sc3 = st.columns(3)
                    sc1.metric("Annual Target", f"{t_target:,}")
                    sc2.metric("Total Achieved", f"{t_achieved:,}", delta=f"{t_achieved - t_target} Remaining")
                    sc3.metric("Achievement %", f"{t_pct:.2f}%")
                    
                    st.progress(min(t_pct / 100.0, 1.0))
                    st.divider()

                # KEEPING YOUR ORIGINAL BREAKDOWN FEATURE
                st.markdown("### 🏢 Screening Breakdown by Source")
                source_counts = df_combined['Source'].value_counts().reset_index()
                source_counts.columns = ['Location Type', 'Children Screened']
                st.dataframe(source_counts, use_container_width=True, hide_index=True)
            else:
                st.info("No screenings logged yet. Your scoreboard will update automatically.")

        except Exception as e:
            st.error(f"❌ Scoreboard Error: {e}")
# ==========================================
# MODULE 13: OFFLINE BATCH SYNC
# ==========================================
elif menu == "13. Offline Batch Sync":
    render_header("Offline Batch Sync", "Upload field data collected without internet", "📡", "#8b5cf6")
    st.write("When you lose signal in the field, collect data on the Offline CSV Template. Once you have internet again, upload the file here to instantly sync all children to the Master Database.")

    tab_template, tab_upload = st.tabs(["📥 1. Download Blank Template", "📤 2. Upload & Sync Data"])

    with tab_template:
        st.subheader("Get the Offline Template")
        st.write("Download this blank CSV file to your phone or tablet before heading into areas with no internet. You can open and edit this file in any spreadsheet app (like Excel or Google Sheets offline).")
        
        template_cols = ["Location Type (Anganwadi or School)", "Screening Date (DD-MM-YYYY)", "Location Name", "Child Name", "DOB (DD-MM-YYYY)", "Gender", "Height (cm)", "Weight (kg)", "MUAC (cm - AW only)", "Hemoglobin", "Disease or 4D", "Contact Number"]
        df_template = pd.DataFrame(columns=template_cols)
        
        csv_template = df_template.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="⬇️ Download Offline Template (CSV)",
            data=csv_template,
            file_name='MHT_Offline_Template.csv',
            mime='text/csv',
        )

    with tab_upload:
        st.subheader("Sync Field Data")
        uploaded_file = st.file_uploader("Upload your filled Offline Template (CSV format)", type=["csv"])

        if uploaded_file is not None:
            try:
                df_offline = pd.read_csv(uploaded_file, encoding='utf-8-sig')
                df_offline.columns = df_offline.columns.str.strip()
                
                st.write(f"📊 Found **{len(df_offline)}** records ready to sync.")
                st.dataframe(df_offline) 

                if st.button("🚀 Sync All to Master Database"):
                    with st.spinner("Processing calculations and syncing in batches... Please wait."):
                        aw_rows_to_add = []
                        sch_rows_to_add = []
                        cmtc_rows_to_add = []

                        for index, row in df_offline.iterrows():
                            loc_col = [c for c in df_offline.columns if 'type' in c.lower()][0]
                            loc_type = str(row[loc_col]).strip().lower()
                            
                            raw_date = str(row.get("Screening Date (DD-MM-YYYY)", "")).strip()
                            try:
                                s_date = pd.to_datetime(raw_date, dayfirst=True).strftime('%Y-%m-%d')
                            except:
                                s_date = raw_date 
                                
                            inst = str(row.get("Location Name", "")).strip()
                            name = str(row.get("Child Name", "")).strip()
                            dob = str(row.get("DOB (DD-MM-YYYY)", "")).strip()
                            gender = str(row.get("Gender", "")).strip()
                            
                            height = pd.to_numeric(row.get("Height (cm)", 0), errors='coerce')
                            weight = pd.to_numeric(row.get("Weight (kg)", 0), errors='coerce')
                            muac = pd.to_numeric(row.get("MUAC (cm - AW only)", 0), errors='coerce')
                            hb = pd.to_numeric(row.get("Hemoglobin", 0), errors='coerce')
                            
                            raw_disease = str(row.get("Disease or 4D", "")).strip()
                            contact = str(row.get("Contact Number", "")).strip()

                            height = 0.0 if pd.isna(height) else height
                            weight = 0.0 if pd.isna(weight) else weight
                            muac = 0.0 if pd.isna(muac) else muac
                            hb = 0.0 if pd.isna(hb) else hb
                            
                            if raw_disease.lower() in ['nan', '', 'none', 'na', 'null']:
                                disease = "None"
                            else:
                                disease = raw_disease
                                
                            contact = "" if contact.lower() in ['nan', ''] else contact

                            if "ang" in loc_type or "aw" in loc_type:
                                final_status = "Normal"
                                try:
                                    h_m = height / 100
                                    bmi = weight / (h_m * h_m) if h_m > 0 else 0
                                    if (muac > 0 and muac < 11.5) or (bmi > 0 and bmi < 13.0): final_status = "SAM"
                                    elif (muac >= 11.5 and muac < 12.5) or (bmi >= 13.0 and bmi < 14.5): final_status = "MAM"
                                except: final_status = "Error"

                                aw_rows_to_add.append([s_date, inst, name, dob, gender, height, weight, muac, hb, disease, contact, "Offline Sync", final_status, "Pending"])
                                
                                if final_status in ["SAM", "MAM"]:
                                    cmtc_rows_to_add.append([s_date, inst, name, dob, contact, weight, height, muac, final_status, "Pending"])

                            elif "sch" in loc_type:
                                sch_rows_to_add.append([s_date, inst, name, dob, gender, height, weight, hb, disease, contact, "Offline Sync", "Pending"])

                        if aw_rows_to_add: spreadsheet.worksheet("daily_screenings_aw").append_rows(aw_rows_to_add)
                        if sch_rows_to_add: spreadsheet.worksheet("daily_screenings_schools").append_rows(sch_rows_to_add)
                        if cmtc_rows_to_add: spreadsheet.worksheet("cmtc_referral").append_rows(cmtc_rows_to_add)

                        st.cache_data.clear() 
                        
                        st.toast(f"✅ Synced {len(aw_rows_to_add)} AWC & {len(sch_rows_to_add)} School records!", icon="🎉")
                        if cmtc_rows_to_add:
                            st.toast(f"🏥 Auto-forwarded {len(cmtc_rows_to_add)} cases to CMTC!", icon="🚑")
                        
                        time.sleep(0.5)
                        st.rerun()

            except Exception as e:
                st.error(f"⚠️ Error reading file. Please ensure you are using the exact template. Detail: {e}")

# ==========================================
# MODULE 14: 💻 TECHO PORTAL ENTRY QUEUE (Multi-Tier + Phonetic + Full UI)
# ==========================================
elif menu == "14. TECHO Entry Queue":  
    import difflib
    import time
    import gspread
    
    st.header("💻 TECHO Portal Pending Queue")
    st.info("⚡ Auto-Sync Engine: Select your location first, then upload your TECHO export file to match and clear!")

    # 🚀 THE FIX: MEMORY CACHE TO STOP READ ERRORS
    @st.cache_data(ttl=600)
    def get_techo_queue_data(sheet_name):
        try:
            return spreadsheet.worksheet(sheet_name).get_all_records()
        except:
            return []

    queue_type = st.radio("Select which queue to work on:", ["👶 Anganwadi Queue", "🏫 School Queue"])
    
    if queue_type == "👶 Anganwadi Queue":
        target_sheet_name = "daily_screenings_aw"
        name_col = "Child Name"  
        inst_col = "Institute"   
    else:
        target_sheet_name = "daily_screenings_schools"
        name_col = "Student Name" 
        inst_col = "Institution"     

    st.write("---")
    
    try:
        active_sheet = spreadsheet.worksheet(target_sheet_name) # Keep this open for writing
        data = get_techo_queue_data(target_sheet_name) # 🚀 Pulls from memory, NOT Google!
        
        if data:
            df = pd.DataFrame(data)
            
            if 'TECHO_Status' not in df.columns:
                st.error(f"❌ Please add the 'TECHO_Status' column to the {target_sheet_name} sheet!")
            elif name_col not in df.columns:
                st.error(f"❌ Could not find the '{name_col}' column in your Google Sheet!")
            else:
                pending_df = df[df['TECHO_Status'] == 'Pending'].copy()
                
                if pending_df.empty:
                    st.success(f"🎉 Awesome! The {queue_type} is completely empty!")
                else:
                    st.subheader("🎯 Step 1: Select Location / Team")
                    available_locations = sorted(pending_df[inst_col].dropna().astype(str).unique().tolist()) if inst_col in df.columns else ["All"]
                    selected_location = st.selectbox(f"Filter queue by {inst_col}:", ["-- Select Location --"] + available_locations)
                    
                    if selected_location != "-- Select Location --":
                        loc_pending_df = pending_df[pending_df[inst_col].astype(str) == selected_location].copy()
                        
                        if loc_pending_df.empty:
                            st.success(f"🎉 All entries for {selected_location} are completely done!")
                        else:
                            st.write("---")
                            st.subheader("⚡ Step 2: Choose Data Entry Method")
                            tab_auto, tab_manual = st.tabs(["🚀 Auto-Sync (TECHO File)", "✍️ Manual Multi-Select"])
                            
                            # ==========================================
                            # 🚀 TAB 1: AUTO-SYNC
                            # ==========================================
                            with tab_auto:
                                st.info(f"Upload the TECHO export file for **{selected_location}** to automatically match and clear children.")
                                techo_file = st.file_uploader("📥 Upload TECHO Export (Excel/CSV)", type=["csv", "xlsx", "xls"], key="techo_upload")
                                
                                if techo_file is not None:
                                    def gujarati_to_english(text):
                                        if not text or pd.isna(text): return ""
                                        char_map = {
                                            'અ': 'A', 'આ': 'A', 'ઇ': 'I', 'ઈ': 'I', 'ઉ': 'U', 'ઊ': 'U', 'એ': 'E', 'ઐ': 'AI', 'ઓ': 'O', 'ઔ': 'AU',
                                            'ક': 'K', 'ખ': 'KH', 'ગ': 'G', 'ઘ': 'GH', 'ચ': 'CH', 'છ': 'CH', 'જ': 'J', 'ઝ': 'Z', 'ટ': 'T', 'ઠ': 'TH',
                                            'ડ': 'D', 'ઢ': 'DH', 'ણ': 'N', 'ત': 'T', 'થ': 'TH', 'દ': 'D', 'ધ': 'DH', 'ન': 'N', 'પ': 'P', 'ફ': 'F',
                                            'બ': 'B', 'ભ': 'BH', 'મ': 'M', 'ય': 'Y', 'ર': 'R', 'લ': 'L', 'વ': 'V', 'શ': 'SH', 'ષ': 'SH', 'સ': 'S',
                                            'હ': 'H', 'ળ': 'L', 'ક્ષ': 'KSH', 'જ્ઞ': 'GN', 'ા': 'A', 'િ': 'I', 'ી': 'I', 'ુ': 'U', 'ૂ': 'U', 'ે': 'E', 'ૈ': 'AI', 'ો': 'O', 'ૌ': 'AU', 'ં': 'N'
                                        }
                                        clean_guj = str(text).split('/')[0].strip()
                                        return "".join([char_map.get(c, "") for c in clean_guj])

                                    def normalize_date(val):
                                        try: return pd.to_datetime(str(val).strip().replace('-', '/'), dayfirst=True).strftime('%Y-%m-%d')
                                        except: return ""

                                    if techo_file.name.endswith('.csv'): techo_df = pd.read_csv(techo_file)
                                    else: techo_df = pd.read_excel(techo_file)

                                    if 'Member Name' in techo_df.columns and 'Date Of Birth' in techo_df.columns:
                                        techo_df['Clean_DOB'] = techo_df['Date Of Birth'].apply(normalize_date)
                                        techo_df['Trans_Name'] = techo_df['Member Name'].apply(gujarati_to_english)
                                        
                                        emr_dob_col = next((c for c in df.columns if str(c).lower() in ['dob', 'date of birth']), None)
                                        
                                        matched_emr_indices = []
                                        matched_techo_indices = []
                                        match_display_data = []

                                        for idx, emr_row in loc_pending_df.iterrows():
                                            emr_name_full = str(emr_row[name_col])
                                            emr_name_clean = emr_name_full.split('/')[0].strip().upper()
                                            emr_dob = normalize_date(emr_row[emr_dob_col]) if emr_dob_col else ""
                                            
                                            potentials = techo_df[techo_df['Clean_DOB'] == emr_dob]
                                            best_score, best_row, best_t_idx = 0, None, None

                                            for t_idx, t_row in potentials.iterrows():
                                                if t_idx in matched_techo_indices: continue
                                                score = difflib.SequenceMatcher(None, emr_name_clean, t_row['Trans_Name']).ratio()
                                                if score > best_score:
                                                    best_score, best_row, best_t_idx = score, t_row, t_idx

                                            if best_score > 0.6:
                                                matched_emr_indices.append(idx)
                                                matched_techo_indices.append(best_t_idx)
                                                
                                                row_data = {
                                                    "Match Quality": f"{int(best_score*100)}%",
                                                    "✅ TECHO Name (Gujarati)": best_row['Member Name'],
                                                }
                                                for col_name in loc_pending_df.columns:
                                                    if col_name not in ['TECHO_Status', '_sort_val']:
                                                        row_data[f"📋 EMR: {col_name}"] = emr_row[col_name]
                                                match_display_data.append(row_data)

                                        emr_only_df = loc_pending_df.drop(index=matched_emr_indices)
                                        techo_only_df = techo_df.drop(index=matched_techo_indices)

                                        st.markdown("#### ⚙️ Sync Results")
                                        sync_t1, sync_t2, sync_t3 = st.tabs([
                                            f"✅ Perfect Matches ({len(match_display_data)})", 
                                            f"⚠️ Missing in TECHO ({len(emr_only_df)})", 
                                            f"🛑 Extra in TECHO ({len(techo_only_df)})"
                                        ])

                                        with sync_t1:
                                            if match_display_data:
                                                st.success(f"Found {len(match_display_data)} matches triangulated by Phonetic Matching!")
                                                match_df = pd.DataFrame(match_display_data)
                                                
                                                sort_key = f"📋 EMR: {name_col}"
                                                if sort_key in match_df.columns: match_df = match_df.sort_values(by=sort_key)
                                                
                                                match_df.insert(0, "✅ Select", True)
                                                edited_match_df = st.data_editor(
                                                    match_df, hide_index=True, use_container_width=True,
                                                    disabled=[col for col in match_df.columns if col != "✅ Select"]
                                                )
                                                
                                                selected_matches = edited_match_df[edited_match_df["✅ Select"] == True][f"📋 EMR: {name_col}"].tolist()
                                                
                                                if st.button(f"🚀 Mark Selected ({len(selected_matches)}) Matches as 'Done'", type="primary"):
                                                    with st.spinner("Batch updating Google Sheets (1 Write Call)..."):
                                                        status_idx = df.columns.get_loc('TECHO_Status') + 1
                                                        cells_to_update = []
                                                        
                                                        for c_name in selected_matches:
                                                            matching_rows = df.index[df[name_col].astype(str) == str(c_name)].tolist()
                                                            for row_idx in matching_rows:
                                                                cells_to_update.append(gspread.Cell(row=row_idx + 2, col=status_idx, value="Done"))
                                                        
                                                        if cells_to_update:
                                                            active_sheet.update_cells(cells_to_update)
                                                            
                                                        st.toast(f"✅ Successfully synced {len(selected_matches)} records!", icon="🎉")
                                                        get_techo_queue_data.clear() # 🚀 CLEAR MEMORY SO IT REFRESHES
                                                        time.sleep(1)
                                                        st.rerun()
                                            else:
                                                st.info("No matches found. Ensure your TECHO export contains the same children and DOBs.")

                                        with sync_t2:
                                            st.warning("These children are pending in your EMR but weren't found in the TECHO file.")
                                            if not emr_only_df.empty:
                                                disp_emr = emr_only_df.drop(columns=['TECHO_Status', '_sort_val'], errors='ignore').sort_values(by=name_col)
                                                st.dataframe(disp_emr, use_container_width=True)

                                        with sync_t3:
                                            st.error("These children are pending in TECHO, but are NOT in your EMR pending queue.")
                                            if not techo_only_df.empty:
                                                disp_techo = techo_only_df.drop(columns=['Trans_Name', 'Clean_DOB'], errors='ignore').sort_values(by='Member Name')
                                                st.dataframe(disp_techo, use_container_width=True)
                                    else:
                                        st.error("❌ The uploaded file is missing 'Member Name' or 'Date Of Birth' columns.")

                            # ==========================================
                            # ✍️ TAB 2: MANUAL MULTI-SELECT
                            # ==========================================
                            with tab_manual:
                                st.write(f"### 📋 Pending Entries for {selected_location} ({len(loc_pending_df)} Children)")
                                
                                display_manual_df = loc_pending_df.drop(columns=['TECHO_Status', '_sort_val'], errors='ignore').sort_values(by=name_col)
                                st.dataframe(display_manual_df, use_container_width=True)
                                
                                st.write("---")
                                children_to_update = st.multiselect(f"Select multiple children to mark as 'Done':", display_manual_df[name_col].tolist())
                                
                                if st.button(f"🚀 Mark Selected ({len(children_to_update)}) as 'Done'"):
                                    if children_to_update:
                                        with st.spinner("Batch updating Google Sheets (1 Write Call)..."):
                                            status_idx = df.columns.get_loc('TECHO_Status') + 1
                                            cells_to_update = []
                                            
                                            for c_name in children_to_update:
                                                matching_rows = df.index[df[name_col].astype(str) == str(c_name)].tolist()
                                                for row_idx in matching_rows:
                                                    cells_to_update.append(gspread.Cell(row=row_idx + 2, col=status_idx, value="Done"))
                                            
                                            if cells_to_update:
                                                active_sheet.update_cells(cells_to_update)
                                                
                                            st.toast(f"✅ {len(children_to_update)} Statuses updated!", icon="🎉")
                                            get_techo_queue_data.clear() # 🚀 CLEAR MEMORY SO IT REFRESHES
                                            time.sleep(1)
                                            st.rerun()
                                    else:
                                        st.warning("Please select at least one child.")
        else:
            st.info(f"The {target_sheet_name} sheet is currently empty.")
            
    except Exception as e:
        st.error(f"❌ Connection Error: {e}")
# ==========================================
# MODULE 15: 🏥 CLINICAL FOLLOW-UP & IFA STOCK TRACKER
# ==========================================
elif menu == "15. Clinical & IFA Tracker":
    import gspread # Needed for specific error catching
    
    render_header("Clinical Operations", "Referrals & Inventory Management", "🏥", "#0ea5e9")
    
    # --- CACHING FUNCTIONS (Memorizes data for 10 minutes) ---
    @st.cache_data(ttl=600)
    def get_master_lists():
        try:
            aw_df = pd.DataFrame(spreadsheet.worksheet("aw new data").get_all_records())
            sch_df = pd.DataFrame(spreadsheet.worksheet("1240315 ALL STUDENTS NAMES").get_all_records())
            return aw_df, sch_df
        except: return pd.DataFrame(), pd.DataFrame()

    @st.cache_data(ttl=600)
    def get_cmtc_data():
        try: return spreadsheet.worksheet("cmtc_referral").get_all_records()
        except: return []

    @st.cache_data(ttl=600)
    def get_ifa_data():
        try: return pd.DataFrame(spreadsheet.worksheet("ifa_inventory").get_all_records())
        except: return pd.DataFrame()

    tab_cmtc, tab_ifa = st.tabs(["🔴 CMTC Follow-up (SAM/MAM)", "💊 IFA Stock Tracker (Syrups/Tablets)"])

    # --- 0. FETCH INSTITUTE LISTS (FROM MEMORY) ---
    master_aw_data, master_sch_data = get_master_lists()

    def get_inst_list(df, keywords):
        col = next((c for c in df.columns if any(k in str(c).upper() for k in keywords)), None)
        return sorted(df[col].astype(str).unique().tolist()) if col else []

    aw_list = get_inst_list(master_aw_data, ["INSTITUTE", "AWC", "CENTER"])
    school_list = get_inst_list(master_sch_data, ["INSTITUTION", "SCHOOL"])

    # --- 1. CMTC FOLLOW-UP ---
    with tab_cmtc:
        st.subheader("📝 SAM/MAM Treatment Progress")
        
        try:
            raw_data = get_cmtc_data() 
            
            if raw_data:
                ref_data = pd.DataFrame(raw_data)
                ref_data = ref_data.fillna("").astype(str).replace(['nan', 'NaN', 'NaT', 'None'], "")

                for col in ["Current Status", "Admission Date", "Follow-up Remarks"]:
                    if col not in ref_data.columns:
                        ref_data[col] = "Pending" if col == "Current Status" else ""

                ref_data['Admission Date'] = pd.to_datetime(
                    ref_data['Admission Date'].astype(str).str.replace('/', '-'), 
                    dayfirst=True, errors='coerce'
                ).dt.date

                status_list = ["Pending", "Counselled", "Admitted", "Discharged", "Recovered", "LAMA/Refused"]
                read_only_cols = ["Child Name", "Institute", "DOB", "Gender", "Referral Date"]
                
                updated_ref_df = st.data_editor(
                    ref_data,
                    column_config={
                        "Current Status": st.column_config.SelectboxColumn("Status", options=status_list, width="medium"),
                        "Admission Date": st.column_config.DateColumn("Adm Date"),
                        "Follow-up Remarks": st.column_config.TextColumn("Remarks", width="large"),
                    },
                    disabled=read_only_cols,
                    hide_index=True,
                    use_container_width=True
                )

                if st.button("💾 Save Follow-up Progress", type="primary"):
                    with st.spinner("Scrubbing data and updating Google Sheets..."):
                        final_df = updated_ref_df.copy()
                        
                        if "Admission Date" in final_df.columns:
                            final_df['Admission Date'] = final_df['Admission Date'].apply(
                                lambda x: x.strftime('%d-%m-%Y') if pd.notnull(x) and hasattr(x, 'strftime') else x
                            )

                        # THE ULTIMATE NAN KILLER
                        raw_data_list = final_df.values.tolist()
                        cleaned_list = []
                        for row in raw_data_list:
                            clean_row = []
                            for cell in row:
                                if pd.isna(cell): clean_row.append("")
                                else:
                                    str_cell = str(cell).strip()
                                    clean_row.append("" if str_cell.lower() in ['nan', 'nat', 'none', '<na>'] else str_cell)
                            cleaned_list.append(clean_row)

                        data_to_save = [final_df.columns.values.tolist()] + cleaned_list
                        
                        spreadsheet.worksheet("cmtc_referral").update(data_to_save)
                        get_cmtc_data.clear() 
                        
                        st.toast("Referral status updated successfully!", icon="✅")
                        import time
                        time.sleep(1)
                        st.rerun()
            else:
                st.success("🎉 No SAM/MAM referrals currently pending!")
        
        except Exception as e:
            st.error(f"CMTC Logic Error: {e}")

    # --- 2. IFA STOCK TRACKER ---
    with tab_ifa:
        st.subheader("💊 IFA Inventory Control")
        ifa_level = st.radio("Select Level:", ["👶 Anganwadi (Syrups)", "🏫 School (Tablets)"], horizontal=True)
        current_options = aw_list if "Anganwadi" in ifa_level else school_list

        try:
            # 🚀 THE FIX: SMART SHEET CONNECTION
            try: 
                inventory_sheet = spreadsheet.worksheet("ifa_inventory")
            except gspread.exceptions.WorksheetNotFound: 
                # ONLY create it if Google explicitly confirms it does not exist
                inventory_sheet = spreadsheet.add_worksheet(title="ifa_inventory", rows="1000", cols="10")
                inventory_sheet.append_row(["Timestamp", "Level", "Institute Name", "Stock Quantity", "Expiry Date", "Status"])
            except Exception as conn_err:
                st.warning(f"Temporary connection glitch: {conn_err}. Retrying usually fixes this.")
                st.stop()

            with st.form("ifa_stock_form", clear_on_submit=True):
                st.write("### 📝 Log Stock Audit")
                c1, c2 = st.columns(2)
                with c1:
                    selected_inst = st.selectbox("Select Institute Name:", ["-- Select --"] + current_options)
                    stock_qty = st.number_input("Current Stock (Units)", min_value=0)
                with c2:
                    expiry_date = st.date_input("Batch Expiry Date")
                    stock_status = st.selectbox("Stock Status:", ["Sufficient", "Low (<25%)", "Critical (<10%)", "Stock Out"])

                if st.form_submit_button("🚀 Submit Inventory Report"):
                    if selected_inst != "-- Select --":
                        import datetime
                        new_entry = [
                            datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                            ifa_level, selected_inst, stock_qty, str(expiry_date), stock_status
                        ]
                        inventory_sheet.append_row(new_entry)
                        get_ifa_data.clear() 
                        st.success(f"Stock record for {selected_inst} saved!")
                    else:
                        st.warning("Please select a valid Institute Name.")

            st.divider()
            st.write("### 📊 Recent Inventory Updates")
            all_inv = get_ifa_data().fillna("") 
            if not all_inv.empty:
                filtered_inv = all_inv[all_inv['Level'] == ifa_level].tail(10)
                st.dataframe(filtered_inv.iloc[::-1], use_container_width=True, hide_index=True)

        except Exception as e:
            st.error(f"Inventory Error: {e}")
