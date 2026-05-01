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
    df_team_4d = safe_load("Team_4D_Report")
    df_hbnc = safe_load("hbnc_screenings") # 🚀 Added Module 5 to the fast-cache!

    # Return exactly 12 items
    return df_4d, df_anemia, df_directory, df_aw_contacts, df_staff, df_aw_master, df_all_students, df_q_perf, df_q_loc, df_q_demo, df_team_4d, df_hbnc

try:
    spreadsheet = get_spreadsheet() 
    
    # 🔴 THE FIX IS HERE: We unpack exactly 12 variables in the same order they were returned!
    df_4d, df_anemia, df_directory, df_aw_contacts, df_staff, df_aw_master, df_all_students, df_q_perf, df_q_loc, df_q_demo, df_team_4d, df_hbnc = load_all_data() 
    
    # These safe aliases ensure Modules 1, 2, and 3 don't throw NameErrors
    df_aw = df_aw_master
    df_students = df_all_students
    df_schools = df_directory
    
except Exception as e:
    if "429" in str(e) or "Quota exceeded" in str(e):
        st.error("🚦 Whoa there! Google is enforcing a speed limit. Please wait exactly 60 seconds and refresh the page!")
        st.stop()
    else:
        st.error(f"An error occurred while loading data: {e}")
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
elif menu == "1. Daily Tour Plan":
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
                df_tour = pd.DataFrame(data)
                search_word = st.text_input("🔍 Search for a Staff Name, Village, or Date:")
                if search_word:
                    df_tour = df_tour[df_tour.astype(str).apply(lambda col: col.str.contains(search_word, case=False)).any(axis=1)]
                st.dataframe(df_tour, use_container_width=True)
            else:
                st.info("No tour plans have been saved yet!")
                
        st.divider()
        st.markdown("##### ✅ Daily Check-list for MHT-1")
        st.checkbox("Check weighing scale and height tape calibration")
        st.checkbox("Ensure blank referral cards are printed (Backup)")
        st.checkbox("Charge tablet/mobile to 100%")

    with tab_charts:
        import plotly.express as px
        aw_logs, sch_logs, df = get_daily_logs()

        if df.empty:
            st.info("📊 The database is currently empty. Once your team enters screenings in Module 2, the charts will automatically appear here!")
        else:
            st.markdown("#### 📈 District Command Center")
            
            # --- TOP LEVEL DISTRICT METRICS ---
            total_screened = len(df)
            total_aw = len(df[df['Location_Type'] == 'Anganwadi']) if 'Location_Type' in df.columns else 0
            total_sch = len(df[df['Location_Type'] == 'School']) if 'Location_Type' in df.columns else 0
            
            # Smart sniff for Status column
            status_col = next((c for c in df.columns if 'STATUS' in str(c).upper() or 'SAM' in str(c).upper() or 'MAM' in str(c).upper()), None)
            
            if status_col:
                referred_df = df[~df[status_col].astype(str).str.lower().isin(['normal', 'none', '', 'nan', 'healthy', 'false'])]
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
            
            # ==========================================
            # 🚀 NEW: TEAM ANALYTICS ENGINE
            # ==========================================
            st.markdown("#### 👥 Team Performance & Health Demographics")
            
            # Dynamic sniffers for Team and Date columns
            team_col = next((c for c in df.columns if any(k in str(c).upper() for k in ["TEAM", "MHT", "STAFF", "INSTITUTE"])), None)
            date_col = next((c for c in df.columns if any(k in str(c).upper() for k in ["DATE", "SCREENING"])), None)

            if team_col:
                # Create a copy to avoid SettingWithCopyWarning
                df_team = df.copy()
                df_team[team_col] = df_team[team_col].astype(str).str.strip().str.upper()
                
                # 1. HEALTHY VS DISEASED SPLIT (Stacked Bar Chart)
                if status_col:
                    def categorize_health(val):
                        v = str(val).strip().lower()
                        if v in ['normal', 'none', '', 'nan', 'healthy', 'false']: return 'Healthy'
                        return 'Referred/4D Detected'
                    
                    df_team['Health_Category'] = df_team[status_col].apply(categorize_health)
                    health_stats = df_team.groupby([team_col, 'Health_Category']).size().reset_index(name='Child_Count')
                    
                    fig_team_health = px.bar(
                        health_stats, 
                        x=team_col, 
                        y='Child_Count', 
                        color='Health_Category',
                        title="Team-Wise Health Breakdown",
                        color_discrete_map={'Healthy': '#10b981', 'Referred/4D Detected': '#ef4444'},
                        barmode='stack',
                        text='Child_Count'
                    )
                    fig_team_health.update_layout(xaxis_title="Mobile Health Team", yaxis_title="Number of Children")
                    st.plotly_chart(fig_team_health, use_container_width=True)

                # 2. DAILY AVERAGE & TOTALS TABLE
                if date_col:
                    st.markdown("**📊 Team Productivity Matrix**")
                    df_team[date_col] = df_team[date_col].astype(str).str.strip()
                    
                    # Calculate stats
                    team_productivity = df_team.groupby(team_col).agg(
                        Total_Screened=(team_col, 'count'),
                        Unique_Working_Days=(date_col, 'nunique')
                    ).reset_index()
                    
                    # Prevent division by zero
                    team_productivity['Unique_Working_Days'] = team_productivity['Unique_Working_Days'].replace(0, 1)
                    team_productivity['Average_Daily_Screening'] = (team_productivity['Total_Screened'] / team_productivity['Unique_Working_Days']).round(1)
                    
                    # Format for UI
                    team_productivity = team_productivity.rename(columns={
                        team_col: "Mobile Health Team",
                        "Total_Screened": "Total Screened (All Time)",
                        "Unique_Working_Days": "Active Field Days",
                        "Average_Daily_Screening": "Avg. Children/Day"
                    })
                    
                    # Sort by highest average
                    team_productivity = team_productivity.sort_values(by="Avg. Children/Day", ascending=False).reset_index(drop=True)
                    st.dataframe(team_productivity, use_container_width=True, hide_index=True)
            else:
                st.warning("⚠️ Could not detect a 'Team' or 'Institute' column in your data to generate team-wise analytics.")

            st.divider()

            # --- ORIGINAL LOCATION & DISEASE CHARTS ---
            chart_col1, chart_col2 = st.columns(2)

            with chart_col1:
                st.markdown("**Screenings by Location**")
                if 'Location_Type' in df.columns:
                    loc_counts = df['Location_Type'].value_counts().reset_index()
                    loc_counts.columns = ['Location', 'Count']
                    fig_loc = px.pie(loc_counts, values='Count', names='Location', hole=0.4, 
                                     color_discrete_sequence=['#10b981', '#3b82f6'])
                    fig_loc.update_traces(textposition='inside', textinfo='percent+label')
                    st.plotly_chart(fig_loc, use_container_width=True)

            with chart_col2:
                st.markdown("**Referrals by Condition (4D)**")
                # Dynamic sniff for Disease column
                disease_col = next((c for c in referred_df.columns if 'DISEASE' in str(c).upper() or '4D' in str(c).upper()), None)
                
                if not referred_df.empty and disease_col:
                    # Clean up diseases for chart
                    referred_df['Clean_Disease'] = referred_df[disease_col].astype(str).str.strip()
                    disease_counts = referred_df[referred_df['Clean_Disease'] != 'nan']['Clean_Disease'].value_counts().reset_index()
                    disease_counts.columns = ['Condition', 'Cases']
                    
                    # Only show top 10 conditions so chart doesn't look messy
                    disease_counts = disease_counts.head(10)
                    
                    fig_dis = px.bar(disease_counts, x='Cases', y='Condition', orientation='h',
                                     color='Cases', color_continuous_scale='Reds')
                    fig_dis.update_layout(yaxis={'categoryorder':'total ascending'})
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

    # 🚀 THE OFFICIAL WHO GOLD STANDARD ENGINE (Interpolation Method)
    def get_whz_status(gender, height_cm, weight_kg):
        if not height_cm or not weight_kg or height_cm < 45 or height_cm > 120:
            return "Out of bounds"

        # WHO Official Cutoffs [Height in cm: [SAM (-3SD), MAM (-2SD)]]
        who_boys = {
            45.0: [1.9, 2.1], 50.0: [2.4, 2.7], 55.0: [3.4, 3.8], 60.0: [4.4, 4.9],
            65.0: [5.5, 6.0], 70.0: [6.6, 7.1], 75.0: [7.6, 8.2], 80.0: [8.5, 9.2],
            85.0: [9.4, 10.1], 90.0: [10.3, 11.1], 95.0: [11.3, 12.1], 100.0: [12.2, 13.2],
            105.0: [13.3, 14.4], 110.0: [14.4, 15.7], 115.0: [15.6, 17.0], 120.0: [16.8, 18.3]
        }
        
        who_girls = {
            45.0: [1.9, 2.1], 50.0: [2.5, 2.7], 55.0: [3.3, 3.6], 60.0: [4.2, 4.6],
            65.0: [5.2, 5.6], 70.0: [6.3, 6.8], 75.0: [7.3, 7.9], 80.0: [8.2, 8.9],
            85.0: [9.1, 9.8], 90.0: [10.0, 10.8], 95.0: [10.9, 11.8], 100.0: [11.9, 12.9],
            105.0: [13.1, 14.2], 110.0: [14.3, 15.5], 115.0: [15.5, 16.9], 120.0: [16.8, 18.3]
        }

        # Select the correct gender table
        table = who_boys if str(gender).strip().upper().startswith('M') else who_girls

        # Exact Match
        if height_cm in table:
            sam_cutoff, mam_cutoff = table[height_cm]
        else:
            # 🧠 MEDICAL INTERPOLATION MATH: Calculates exact cutoffs for numbers in between
            heights = sorted(table.keys())
            lower_h = max([h for h in heights if h <= height_cm])
            upper_h = min([h for h in heights if h >= height_cm])
            
            lower_sam, lower_mam = table[lower_h]
            upper_sam, upper_mam = table[upper_h]
            
            # Calculate the proportional difference
            ratio = (height_cm - lower_h) / (upper_h - lower_h)
            sam_cutoff = lower_sam + (ratio * (upper_sam - lower_sam))
            mam_cutoff = lower_mam + (ratio * (upper_mam - lower_mam))

        # 🚦 Final Diagnosis
        if weight_kg < sam_cutoff:
            return "SAM"
        elif weight_kg < mam_cutoff:
            return "MAM"
        else:
            return "Normal"

    # 🚀 180-Day Bi-Annual Background Checker
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
    cutoff_date_str = cutoff_date.strftime('%Y-%m-%d')

    # ==========================================
    # 🚀 DUAL TAB INTERFACE (SCREENING & COVERAGE)
    # ==========================================
    tab_screening, tab_coverage = st.tabs(["🩺 1. Child Screening Desktop", "🏫 2. Institution Coverage Engine"])

    with tab_screening:
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
            
            recent_status = {} 
            
            for r in inst_records:
                try:
                    rec_date = datetime.datetime.strptime(r[0], '%Y-%m-%d').date()
                    if rec_date >= cutoff_date:
                        c_name = str(r[2]).strip()
                        status_col = 12 if category == "👶 Anganwadi" else 10
                        status = str(r[status_col]).strip() if len(r) > status_col else ""
                        
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
                        get_recent_screenings.clear() 
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
                
                if name in absent_names:
                    display_str += " 🛑 [ABSENT]"
                    done_list.append(name)
                elif name in screened_names:
                    display_str += " ✅ [SCREENED]"
                    done_list.append(name)
                else:
                    pending_list.append(name)

                child_display[name] = display_str

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
                                # 🛠️ FIX 1: SWAPPED HEIGHT AND WEIGHT HERE!
                                spreadsheet.worksheet("cmtc_referral").append_row([screening_date, selected_inst, new_name, str(new_dob), new_contact, height_val, weight_val, muac_val, final_status, "Pending"])
                            
                            st.toast(f"✅ Successfully registered and screened {new_name}!", icon="🎉")
                            get_recent_screenings.clear() 
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

                            if save_btn:
                                ws = spreadsheet.worksheet(target_sheet)
                                all_recs = ws.get_all_values()
                                
                                row_to_update = None
                                existing_row = []
                                
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
                                                
                                        # 🛠️ FIX 2: SWAPPED HEIGHT AND WEIGHT HERE!
                                        cmtc_data = [str(screening_date), selected_inst, final_child_name, str(dob), merged_contact, merged_h, merged_w, merged_m, merged_status, "Pending"]
                                        
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
                                        # 🛠️ FIX 3: SWAPPED HEIGHT AND WEIGHT HERE!
                                        spreadsheet.worksheet("cmtc_referral").append_row([str(screening_date), selected_inst, final_child_name, str(dob), updated_contact, height_val, weight_val, muac_val, final_status, "Pending"])
                            
                                get_recent_screenings.clear() 
                                import time
                                time.sleep(0.5) 
                                st.rerun()

    # ==========================================
    # 🏫 TAB 2: INSTITUTION COVERAGE ENGINE
    # ==========================================
    with tab_coverage:
        st.subheader("🏫 Real-Time Coverage Tracker")
        st.write("Track real-time screening progress team-wise across your assigned institutions.")
        
        c_col1, c_col2 = st.columns(2)
        with c_col1:
            selected_team = st.selectbox("👥 Select Assigned Team:", ["TEAM-1240315", "TEAM-1240309"])
        with c_col2:
            view_category = st.radio("Select View Category:", ["👶 Anganwadis", "🏫 Schools"], horizontal=True)
            
        @st.cache_data(ttl=300)
        def fetch_master_and_build_coverage(team_id, v_category):
            # 1. Configuration Check
            if v_category == "👶 Anganwadis":
                master_sheet_name = "aw new data"
                inst_cols = ["INSTITUTE", "AWC", "CENTER", "AWC NAME"]
                daily_sheet = "daily_screenings_aw"
                status_idx = 12
            else:
                master_sheet_name = "1240315 ALL STUDENTS NAMES"
                inst_cols = ["INSTITUTION", "SCHOOL"]
                daily_sheet = "daily_screenings_schools"
                status_idx = 10
                
            try:
                master_raw = pd.DataFrame(spreadsheet.worksheet(master_sheet_name).get_all_records())
            except:
                return pd.DataFrame()
                
            # Find the exact columns
            def find_col(df, keys):
                return next((c for c in df.columns if any(k in str(c).upper() for k in keys)), None)
                
            loc_col = find_col(master_raw, inst_cols)
            team_col = find_col(master_raw, ["TEAM"])
            
            # 2. Extract Total Kids (Denominator) filter exactly by the chosen Team!
            if team_col:
                master_raw = master_raw[master_raw[team_col].astype(str).str.strip().str.upper() == team_id.upper()]
                
            master_counts = {}
            if loc_col and not master_raw.empty:
                for _, row in master_raw.iterrows():
                    inst = str(row[loc_col]).strip()
                    if inst and inst not in ['nan', 'None', '']:
                        master_counts[inst] = master_counts.get(inst, 0) + 1
                        
            # 3. Fetch the Daily Logs to see actual Screenings (Numerator)
            daily_stats = {}
            try:
                raw_daily = spreadsheet.worksheet(daily_sheet).get_all_values()
                for r in raw_daily[1:]: 
                    if len(r) > 2:
                        d_date = str(r[0]).strip()
                        
                        # 🚀 180-DAY RULE: Only count screenings that happened in the current semester!
                        if d_date >= cutoff_date_str:
                            d_inst = str(r[1]).strip()
                            d_child = str(r[2]).strip()
                            d_status = str(r[status_idx]).strip() if len(r) > status_idx else "SCREENED"
                            
                            if d_inst not in daily_stats:
                                daily_stats[d_inst] = {'children': {}, 'last_date': ''}
                                
                            daily_stats[d_inst]['children'][d_child] = d_status
                            if d_date > daily_stats[d_inst]['last_date']:
                                daily_stats[d_inst]['last_date'] = d_date
            except:
                pass
                
            # 4. Merge & Compute Progress Math
            coverage_list = []
            for inst, total_reg in master_counts.items():
                stats = daily_stats.get(inst, {'children': {}, 'last_date': 'Not Visited'})
                
                # We don't count absent kids as "Screened". They are pending!
                screened_children = [c for c, s in stats['children'].items() if s != 'ABSENT']
                screened_count = len(screened_children)
                pending_count = max(0, total_reg - screened_count)
                last_visit = stats['last_date']
                
                if screened_count == 0:
                    status_flag = "🔴 Pending"
                elif screened_count >= total_reg:
                    status_flag = "🟢 Completed"
                else:
                    pct = int((screened_count / total_reg) * 100) if total_reg > 0 else 0
                    status_flag = f"🟡 In Progress ({pct}%)"
                    
                coverage_list.append({
                    "Institution Name": inst,
                    "Total Registered": total_reg,
                    "Screened": screened_count,
                    "Pending": pending_count,
                    "Last Visit": last_visit,
                    "Status": status_flag
                })
                
            return pd.DataFrame(coverage_list)
            
        with st.spinner(f"Crunching latest data for {selected_team}..."):
            cov_df = fetch_master_and_build_coverage(selected_team, view_category)
            
        if not cov_df.empty:
            total_inst = len(cov_df)
            completed_inst = len(cov_df[cov_df['Status'] == '🟢 Completed'])
            pending_inst = len(cov_df[cov_df['Status'] == '🔴 Pending'])
            in_prog_inst = len(cov_df[cov_df['Status'].str.startswith('🟡')])
            
            st.markdown("### 📊 Overall Coverage KPIs")
            kpi1, kpi2, kpi3, kpi4 = st.columns(4)
            kpi1.metric("Total Assigned", total_inst)
            kpi2.metric("🟢 100% Completed", completed_inst)
            kpi3.metric("🟡 In Progress", in_prog_inst)
            kpi4.metric("🔴 Unvisited", pending_inst)
            
            st.divider()
            st.markdown("### 📋 The Pending Hit-List")
            
            f_col1, f_col2 = st.columns(2)
            status_filter = f_col1.multiselect("Filter by Status", ["🟢 Completed", "🟡 In Progress", "🔴 Pending"], default=["🟡 In Progress", "🔴 Pending"])
            
            display_df = cov_df.copy()
            if status_filter:
                # Custom filter matching based on emoji tags
                mask = display_df['Status'].apply(lambda x: any(f.split()[0] in x for f in status_filter))
                display_df = display_df[mask]
                
            st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.warning(f"No {view_category} found assigned to {selected_team}. Make sure the master database contains the exact team name.")
   
# ==========================================
# MODULE 3: 4D DEFECT REGISTRY & CASE MANAGEMENT
# ==========================================
elif menu == "3. 4D Defect Registry":
    render_header("4D Defect Command Center", "Clinical Registry & Enhanced Refer Card Generator", "📋", "#8b5cf6")

    # 🔄 SYNC BUTTON
    if st.button("🔄 Sync & Refresh Database"):
        try: get_daily_logs.clear()
        except: st.cache_data.clear()
        st.toast("Database refreshed!", icon="✅")
        import time
        time.sleep(0.5)
        st.rerun()

    # --- 1. DATA PRE-PROCESSING ---
    team_lookup = {}
    if not df_aw.empty:
        aw_loc_key = next((c for c in df_aw.columns if any(k in str(c).upper() for k in ["INSTITUTE", "AWC", "CENTER", "AWC NAME"])), None)
        aw_team_key = next((c for c in df_aw.columns if "TEAM" in str(c).upper()), None)
        if aw_loc_key and aw_team_key:
            team_lookup.update(dict(zip(df_aw[aw_loc_key].astype(str).str.strip(), df_aw[aw_team_key].astype(str).str.strip())))
            
    if not df_directory.empty:
        sch_loc_key = next((c for c in df_directory.columns if any(k in str(c).upper() for k in ["INSTITUTION", "SCHOOL"])), None)
        sch_team_key = next((c for c in df_directory.columns if "TEAM" in str(c).upper()), None)
        if sch_loc_key and sch_team_key:
            team_lookup.update(dict(zip(df_directory[sch_loc_key].astype(str).str.strip(), df_directory[sch_team_key].astype(str).str.strip())))

    def get_anemia_status(hb_val):
        try:
            clean_hb = ''.join(c for c in str(hb_val) if c.isdigit() or c == '.')
            hb = float(clean_hb)
            if hb <= 0: return "" 
            if hb < 7.0: return "🔴 Severe Anemia"
            elif 7.0 <= hb <= 9.9: return "🟡 Moderate Anemia"
            elif 10.0 <= hb <= 10.9: return "🔵 Mild Anemia"
            else: return "Normal"
        except: return ""

    def get_val_from_row(row, cols, search_terms, default="N/A"):
        for c in cols:
            if any(term in c.lower() for term in search_terms):
                val = str(row[c]).strip()
                return val if val.lower() not in ['nan', ''] else default
        return default

    aw_logs, sch_logs, _ = get_daily_logs()

    def is_significant(val):
        v = str(val).strip().lower()
        return v not in ['', 'nan', 'none', 'no', 'null', 'na', 'n/a', 'false', 'normal', '-', 'absent']

    all_live_defects = []
    for source_type, df in [("Anganwadi", aw_logs), ("School", sch_logs)]:
        if not df.empty:
            d_col = next((c for c in df.columns if c.lower() in ['disease', 'diseases', '4d']), None)
            s_col = next((c for c in df.columns if c.lower() in ['status', 'sam', 'mam']), None)
            hb_col = next((c for c in df.columns if c.lower() in ['hb', 'hemoglobin']), None)
            inst_col = next((c for c in df.columns if any(k in c.lower() for k in ['inst', 'school', 'awc', 'anganwadi', 'center'])), None)
            gender_col = next((c for c in df.columns if any(k in c.lower() for k in ['gender', 'sex'])), None)
            
            for _, row in df.iterrows():
                hb_val = row[hb_col] if hb_col else 0
                anemia_status = get_anemia_status(hb_val)
                has_disease = is_significant(row[d_col]) if d_col else False
                has_status = is_significant(row[s_col]) if s_col else False
                has_anemia = anemia_status != "" and "Normal" not in anemia_status
                
                if has_disease or has_status or has_anemia:
                    inst_name = str(row[inst_col]).strip() if inst_col else "Unknown"
                    raw_g = str(row[gender_col]).upper() if gender_col else "U"
                    clean_g = "Male" if raw_g.startswith('M') else "Female" if raw_g.startswith('F') else "Unknown"
                    
                    cond_list = []
                    if has_disease: cond_list.append(str(row[d_col]))
                    if has_status: cond_list.append(str(row[s_col]))
                    if has_anemia: cond_list.append(anemia_status)

                    all_live_defects.append({
                        "Date": str(row.get('Date', row.get('Screening Date', 'Unknown'))),
                        "Name": str(row.get('Child Name', row.get('Student Name', 'Unknown'))),
                        "Institution": inst_name,
                        "Team": team_lookup.get(inst_name, "Unassigned"),
                        "Gender": clean_g,
                        "Condition": " + ".join(cond_list),
                        "Contact": str(row.get('Contact', row.get('Mobile No', 'N/A'))),
                        "DOB": str(row.get('DOB', 'N/A')),
                        "Father": str(row.get('Father', row.get('Parent Name', 'N/A'))),
                        "Height": get_val_from_row(row, df.columns, ['height', 'ht', 'ઊંચાઈ']),
                        "Weight": get_val_from_row(row, df.columns, ['weight', 'wt', 'વજન']),
                        "MUAC": get_val_from_row(row, df.columns, ['muac']) if source_type == "Anganwadi" else "N/A",
                        "Hb": str(hb_val) if hb_val != 0 else "N/A",
                        "Class": get_val_from_row(row, df.columns, ['class', 'std', 'standard', 'ધોરણ']) if source_type == "School" else "N/A",
                        "Type": source_type
                    })

    # --- 2. PREP HISTORICAL DATA (For Tabs 1 & 2) ---
    df_hist = pd.DataFrame()
    hist_team_options = []
    
    if not df_4d.empty:
        df_hist = df_4d.copy()
        df_hist.columns = df_hist.columns.str.strip()
        
        for req_col in ['Current Status', 'Next Follow-Up Date', 'Remarks']:
            if req_col not in df_hist.columns:
                df_hist[req_col] = ''
                
        t_col = next((c for c in df_hist.columns if 'TEAM' in c.upper()), None)
        if t_col:
            hist_team_options = sorted([str(x).strip() for x in df_hist[t_col].unique() if str(x).strip() and str(x).lower() not in ['nan', 'none']])

    # --- 3. TABBED INTERFACE ---
    tab_action, tab_logger, tab_live, tab_card = st.tabs([
        "🚨 1. Action Desk", "📞 2. Follow-Up Logger", "🌍 3. Live Daily Registry", "🪪 4. Refer Card Print"
    ])

    # 🚨 TAB 1: ACTION DESK
    with tab_action:
        st.subheader("🎯 Full Action Desk (Pending Cases)")
        a_f1, a_f2 = st.columns(2)
        with a_f1: a_team = st.selectbox("👤 Filter by Team:", ["-- All --"] + hist_team_options, key="act_team")
        with a_f2: a_gen = st.selectbox("⚖️ Filter by Gender:", ["-- All --", "Male", "Female"], key="act_gen")

        if not df_hist.empty:
            df_act = df_hist.copy()
            
            if a_team != "-- All --" and t_col:
                df_act = df_act[df_act[t_col].astype(str).str.upper().str.strip() == a_team.upper()]
            if a_gen != "-- All --":
                g_col = next((c for c in df_act.columns if any(k in c.upper() for k in ['GENDER', 'SEX'])), None)
                if g_col: df_act = df_act[df_act[g_col].astype(str).str.upper().str.startswith(a_gen[0])]
            
            df_act['Parsed_Next_Date'] = pd.to_datetime(df_act.get('Next Follow-Up Date', ''), errors='coerce', dayfirst=True)
            import datetime
            today_ts = pd.Timestamp(datetime.date.today())
            
            full_action_list = df_act[
                (df_act['Current Status'].astype(str).str.upper() != 'CURED/RESOLVED') & 
                ((df_act['Parsed_Next_Date'] <= today_ts) | (df_act['Parsed_Next_Date'].isna()))
            ]
            
            st.write(f"Showing **{len(full_action_list)}** total children requiring follow-up.")
            st.dataframe(full_action_list[['NAME', 'VILLAGE', '4D', 'Current Status', 'Next Follow-Up Date']], 
                         use_container_width=True, hide_index=True)
        else: st.info("Historical data is empty.")

    # 📞 TAB 2: FOLLOW-UP LOGGER
    with tab_logger:
        st.subheader("📞 Interactive Case Logger")
        st.write("Double-click any cell below to edit! Edits will not save or reload the app until you click the save button.")
        
        l_f1, l_f2 = st.columns(2)
        with l_f1: l_team = st.selectbox("👤 Filter by Team:", ["-- All --"] + hist_team_options, key="log_team")
        with l_f2: l_gen = st.selectbox("⚖️ Filter by Gender:", ["-- All --", "Male", "Female"], key="log_gen")

        if not df_hist.empty:
            df_log_pool = df_hist.copy()
            
            if l_team != "-- All --" and t_col: 
                df_log_pool = df_log_pool[df_log_pool[t_col].astype(str).str.upper().str.strip() == l_team.upper()]
            if l_gen != "-- All --":
                g_col = next((c for c in df_log_pool.columns if any(k in c.upper() for k in ['GENDER', 'SEX'])), None)
                if g_col: df_log_pool = df_log_pool[df_log_pool[g_col].astype(str).str.upper().str.startswith(l_gen[0])]
            
            df_log_pool = df_log_pool.reset_index(drop=True)
            
            if not df_log_pool.empty:
                df_log_pool['Next Follow-Up Date'] = pd.to_datetime(df_log_pool['Next Follow-Up Date'], errors='coerce', dayfirst=True).dt.date
                
                editable_columns = ["Current Status", "Next Follow-Up Date", "Remarks"]
                disabled_columns = [c for c in df_log_pool.columns if c not in editable_columns]
                
                with st.form("logger_editor_form"):
                    edited_df = st.data_editor(
                        df_log_pool,
                        disabled=disabled_columns,
                        use_container_width=True,
                        hide_index=True,
                        key="interactive_logger",
                        column_config={
                            "Next Follow-Up Date": st.column_config.DateColumn(
                                "Next Follow-Up Date",
                                help="Select the next follow-up date",
                                format="DD/MM/YYYY",
                                step=1,
                            ),
                            "Current Status": st.column_config.SelectboxColumn(
                                "Current Status",
                                options=["Under Treatment", "Referred to CHC", "Surgery Scheduled", "Cured/Resolved"]
                            )
                        }
                    )
                    
                    submit_edits = st.form_submit_button("💾 Save All Changes to Master Sheet", type="primary")
                    
                    if submit_edits:
                        changes = []
                        for i in range(len(df_log_pool)):
                            old_stat = str(df_log_pool.loc[i, 'Current Status']).strip()
                            new_stat = str(edited_df.loc[i, 'Current Status']).strip()
                            old_date = str(df_log_pool.loc[i, 'Next Follow-Up Date']).strip()
                            new_date = str(edited_df.loc[i, 'Next Follow-Up Date']).strip()
                            old_rem = str(df_log_pool.loc[i, 'Remarks']).strip()
                            new_rem = str(edited_df.loc[i, 'Remarks']).strip()
                            
                            if old_stat != new_stat or old_date != new_date or old_rem != new_rem:
                                save_date = new_date if new_date not in ['NaT', 'None', ''] else ''
                                changes.append({
                                    'name': str(edited_df.loc[i, 'NAME']).strip(),
                                    '4d': str(edited_df.loc[i, '4D']).strip(),
                                    'status': new_stat if new_stat != 'nan' else '',
                                    'date': save_date,
                                    'remarks': new_rem if new_rem != 'nan' else ''
                                })
                        
                        if changes:
                            try:
                                with st.spinner("Saving changes to Google Sheets..."):
                                    ws = spreadsheet.worksheet("4d_list")
                                    all_v = ws.get_all_values()
                                    heads = all_v[0]
                                    
                                    n_idx = heads.index("NAME")
                                    d_idx = heads.index("4D")
                                    s_idx = heads.index("Current Status") if "Current Status" in heads else None
                                    dt_idx = heads.index("Next Follow-Up Date") if "Next Follow-Up Date" in heads else None
                                    r_idx = heads.index("Remarks") if "Remarks" in heads else None
                                    
                                    for ch in changes:
                                        for i, row in enumerate(all_v):
                                            if i > 0 and str(row[n_idx]).strip() == ch['name'] and str(row[d_idx]).strip() == ch['4d']:
                                                if s_idx is not None: ws.update_cell(i+1, s_idx+1, ch['status'])
                                                if dt_idx is not None: ws.update_cell(i+1, dt_idx+1, ch['date'])
                                                if r_idx is not None: ws.update_cell(i+1, r_idx+1, ch['remarks'])
                                                break
                                    st.success(f"Successfully updated {len(changes)} child(ren)!")
                                    st.cache_data.clear()
                                    import time
                                    time.sleep(0.5)
                                    st.rerun()
                            except Exception as e:
                                st.error(f"Error saving to sheet: {e}")
                        else:
                            st.info("No edits detected. Nothing to save.")
            else:
                st.success("No children found for this specific filter.")
        else:
            st.info("Historical data is empty.")

    # 🌍 TAB 3: LIVE REGISTRY
    with tab_live:
        st.subheader("🌍 Live Daily Defect Registry")
        r_f1, r_f2 = st.columns(2)
        
        df_live_base = pd.DataFrame(all_live_defects)
        
        if not df_live_base.empty:
            inst_options = sorted(list(df_live_base['Institution'].unique()))
            with r_f1: r_inst = st.selectbox("🏢 Institution:", ["-- All --"] + inst_options, key="reg_inst")
            with r_f2: r_gen = st.selectbox("⚖️ Gender:", ["-- All --", "Male", "Female"], key="reg_gen_live")
            
            df_live_filtered = df_live_base.copy()
            if r_inst != "-- All --": df_live_filtered = df_live_filtered[df_live_filtered['Institution'] == r_inst]
            if r_gen != "-- All --": df_live_filtered = df_live_filtered[df_live_filtered['Gender'] == r_gen]
            
            st.write(f"Showing **{len(df_live_filtered)}** defects screened today.")
            st.dataframe(df_live_filtered[['Date', 'Name', 'Institution', 'Condition', 'Contact', 'Gender']], 
                         use_container_width=True, hide_index=True)
        else: st.info("No defects screened today.")

    # 🪪 TAB 4: REFER CARD PRINT
    with tab_card:
        st.subheader("🪪 Official Refer Card Center")
        df_card_base = pd.DataFrame(all_live_defects)
        
        if not df_card_base.empty:
            c_f1, c_f2 = st.columns(2)
            inst_list_card = sorted(list(df_card_base['Institution'].unique()))
            with c_f1: sel_inst_card = st.selectbox("🏢 Institution:", ["-- All --"] + inst_list_card, key="card_inst")
            with c_f2: c_gen_card = st.selectbox("⚖️ Gender:", ["-- All --", "Male", "Female"], key="card_gen")

            df_card_filtered = df_card_base.copy()
            if sel_inst_card != "-- All --": df_card_filtered = df_card_filtered[df_card_filtered['Institution'] == sel_inst_card]
            if c_gen_card != "-- All --": df_card_filtered = df_card_filtered[df_card_filtered['Gender'] == c_gen_card]

            display_map = {f"{r['Name']} ({r['Institution']})": r for _, r in df_card_filtered.iterrows()}
            sel_c = st.selectbox("Select Child to Print:", ["-- Select --"] + sorted(list(display_map.keys())))
            
            if sel_c != "-- Select --":
                p = display_map[sel_c]
                
                with st.form("print_refer_final"):
                    st.write(f"### 📋 Auto-Filled Screening Details for {p['Name']}")
                    st.caption("Data is pulled directly from the screening sheet. Please verify and add remarks.")
                    
                    r1_1, r1_2, r1_3 = st.columns(3)
                    with r1_1: st.text_input("Screening Date", value=p['Date'], disabled=True)
                    with r1_2: st.text_input("Institution", value=p['Institution'], disabled=True)
                    with r1_3: st.text_input("Gender", value=p['Gender'], disabled=True)
                    
                    r2_1, r2_2, r2_3 = st.columns(3)
                    with r2_1: st.text_input("DOB", value=p['DOB'], disabled=True)
                    with r2_2: st.text_input("Father Name", value=p['Father'], disabled=True)
                    with r2_3: st.text_input("Contact", value=p['Contact'], disabled=True)
                    
                    r3_1, r3_2, r3_3 = st.columns(3)
                    with r3_1: st.text_input("Height (cm)", value=p.get('Height', 'N/A'), disabled=True)
                    with r3_2: st.text_input("Weight (kg)", value=p.get('Weight', 'N/A'), disabled=True)
                    with r3_3: st.text_input("Hb (g/dL)", value=p.get('Hb', 'N/A'), disabled=True)
                    
                    r4_1, r4_2 = st.columns(2)
                    with r4_1: st.text_input("MUAC (Anganwadi)", value=p.get('MUAC', 'N/A'), disabled=True)
                    with r4_2: st.text_input("Class (School)", value=p.get('Class', 'N/A'), disabled=True)
                    
                    st.text_area("Diseases / Conditions Found", value=p['Condition'], disabled=True)
                    
                    st.divider()
                    st.write("### ✍️ Team Actions")
                    
                    action_c1, action_c2 = st.columns(2)
                    with action_c1:
                        team_remarks = st.text_area("Doctor / Team Remarks (Editable)", placeholder="Add any specific clinical advice or notes here...")
                    with action_c2:
                        refer_options = ["DEIC", "CMTC", "SDH", "PHC", "GATHANI HOSPITAL", "JAY AMBE CHAPARDA HOSPITAL"]
                        selected_refer_to = st.selectbox("Referred To (Editable)", refer_options)
                    
                    if st.form_submit_button("🖨️ Generate Professional PDF Refer Card"):
                        
                        def generate_enhanced_refer_card(data):
                            try:
                                from fpdf import FPDF
                                import os
                                pdf = FPDF()
                                pdf.add_page()
                                
                                # Header
                                pdf.set_font("Arial", 'B', 16)
                                pdf.cell(0, 10, "RASHTRIYA BAL SWASTHYA KARYAKRAM (RBSK)", ln=True, align='C')
                                pdf.set_font("Arial", 'B', 12)
                                pdf.cell(0, 10, "Official Clinical Referral & Case Management Card", ln=True, align='C')
                                pdf.ln(5)
                                
                                def add_row(col1, val1, col2, val2):
                                    pdf.set_font("Arial", 'B', 10)
                                    pdf.cell(40, 8, col1, border=1)
                                    pdf.set_font("Arial", '', 10)
                                    pdf.cell(55, 8, str(val1), border=1)
                                    pdf.set_font("Arial", 'B', 10)
                                    pdf.cell(40, 8, col2, border=1)
                                    pdf.set_font("Arial", '', 10)
                                    pdf.cell(55, 8, str(val2), border=1, ln=True)

                                # Section 1. Demographics
                                pdf.set_fill_color(220, 230, 245)
                                pdf.set_font("Arial", 'B', 11)
                                pdf.cell(0, 8, " 1. Child Demographics & Details", border=1, fill=True, ln=True)
                                add_row("Name:", data.get('Name', 'N/A'), "Gender:", data.get('Gender', 'N/A'))
                                add_row("DOB / Age:", f"{data.get('DOB', 'N/A')} ({get_age(data.get('DOB', ''))})", "Father Name:", data.get('Father', 'N/A'))
                                add_row("Institution:", data.get('Institution', 'N/A'), "Contact No:", data.get('Contact', 'N/A'))
                                add_row("Screening Date:", data.get('Date', 'N/A'), "Class / Team:", f"{data.get('Class', 'N/A')} / {data.get('Team', 'N/A')}")
                                pdf.ln(5)

                                # Section 2. Vitals
                                pdf.set_font("Arial", 'B', 11)
                                pdf.cell(0, 8, " 2. Screening Vitals & Anthropometry", border=1, fill=True, ln=True)
                                add_row("Height (cm):", data.get('Height', 'N/A'), "Weight (kg):", data.get('Weight', 'N/A'))
                                add_row("Hemoglobin (Hb):", data.get('Hb', 'N/A'), "MUAC (AW):", data.get('MUAC', 'N/A'))
                                pdf.ln(5)

                                # Section 3. Clinical
                                pdf.set_font("Arial", 'B', 11)
                                pdf.cell(0, 8, " 3. Clinical Diagnosis & Team Remarks", border=1, fill=True, ln=True)
                                pdf.set_font("Arial", 'B', 10)
                                pdf.cell(40, 14, "Conditions / 4D:", border=1)
                                pdf.set_font("Arial", '', 10)
                                pdf.multi_cell(150, 14, str(data.get('Condition', 'N/A')), border=1)
                                
                                pdf.set_font("Arial", 'B', 10)
                                pdf.cell(40, 14, "Team Remarks:", border=1)
                                pdf.set_font("Arial", '', 10)
                                pdf.multi_cell(150, 14, str(team_remarks if team_remarks else 'No remarks provided.'), border=1)
                                pdf.ln(5)

                                # Section 4. Referral Action
                                pdf.set_font("Arial", 'B', 11)
                                pdf.cell(0, 8, " 4. Referral Action", border=1, fill=True, ln=True)
                                add_row("Referred To:", selected_refer_to, "Medical Officer:", "Dr. NIHAR UPADHYAY")
                                
                                # 🚀 RE-INTEGRATED: Signature and Seal
                                pdf.ln(10)
                                y_pos = pdf.get_y()
                                
                                seal_path = "SEAL.jpeg" 
                                sign_path = "sign.jpg"
                                
                                if os.path.exists(seal_path):
                                    try:
                                        pdf.image(seal_path, x=30, y=y_pos, w=25)
                                    except Exception as e:
                                        st.warning(f"⚠️ Found {seal_path} but couldn't load it: {e}")
                                else:
                                    st.warning(f"⚠️ Could not find {seal_path} in the app directory.")

                                if os.path.exists(sign_path):
                                    try:
                                        pdf.image(sign_path, x=150, y=y_pos, w=30)
                                    except Exception as e:
                                        st.warning(f"⚠️ Found {sign_path} but couldn't load it: {e}")
                                else:
                                    st.warning(f"⚠️ Could not find {sign_path} in the app directory.")
                                
                                pdf.set_y(y_pos + 25)
                                pdf.set_font("Arial", 'B', 10)
                                pdf.cell(80, 5, "Official Seal", align='C')
                                pdf.cell(110, 5, "Medical Officer Signature", align='R', ln=True)

                                # Footer
                                pdf.ln(10)
                                pdf.set_font("Arial", 'I', 9)
                                pdf.cell(0, 10, "Authorized by RBSK Health Department. Generated Electronically.", align='C')

                                pdf_out = pdf.output()
                                if type(pdf_out) == str:
                                    return pdf_out.encode('latin1')
                                else:
                                    return bytes(pdf_out)
                                    
                            except Exception as e:
                                st.error(f"Error generating PDF: {e}")
                                return b""

                        pdf_b = generate_enhanced_refer_card(p)
                        if pdf_b:
                            import base64
                            b64 = base64.b64encode(pdf_b).decode()
                            st.markdown(f'<a href="data:application/pdf;base64,{b64}" download="Refer_{p["Name"]}.pdf" style="display:block;padding:12px;background:#2563eb;color:white;text-align:center;font-weight:bold;border-radius:6px;text-decoration:none;">📄 Click Here to Download PDF Referral Card</a>', unsafe_allow_html=True)
        else: st.warning("No children available to print cards matching current filters.")
# ==========================================
# MODULE 4: VISUAL ANALYSIS
# ==========================================
elif menu == "4. Visual Analysis":
    import plotly.express as px
    import plotly.graph_objects as go
    import numpy as np
    import pandas as pd
    
    render_header("Visual Analytics", "Quarterly Zero-Lag Performance & Epidemiological Mapping", "🗺️", "#f97316")
    st.write("Welcome to the Zero-Lag Command Center. This dashboard processes your Quarterly State Reports for maximum speed and deep insights.")

    tab_coverage, tab_hotspot, tab_radar, tab_team = st.tabs([
        "🎯 Coverage & Velocity Matrix", "📍 Disease Hotspot Mapper", "🧬 Epidemiological Radar", "👥 Team Performance Matrix"
    ])

    # 🎯 TAB 1: COVERAGE
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
            st.warning("⚠️ Waiting for valid data in the 'Q_Performance' sheet.")

    # 📍 TAB 2: HOTSPOT
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
            st.warning("⚠️ Waiting for valid data in the 'Q_Location_4D' sheet.")

    # 🧬 TAB 3: RADAR
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
            st.warning("⚠️ Waiting for valid data in the 'Q_Demo_4D' sheet.")

    # 👥 TAB 4: TEAM PERFORMANCE MATRIX
    with tab_team:
        st.subheader("👥 Operational Workforce & Team Performance Matrix")
        st.write("Track productivity, efficiency, and clinical detection quality across all specific RBSK Teams.")

        if not df_team_4d.empty:
            df_t = df_team_4d.copy()
            
            # Clean data: Remove TOTAL rows so graphs aren't skewed
            df_t = df_t[~df_t['Team ID'].astype(str).str.contains("TOTAL", case=False, na=False)]
            
            # Convert all necessary columns to numeric
            num_cols = [
                'Total No. of Children (AWC)', 'Screened (AWC)', 'SCREENING PERCENTAGE',
                'Defect at birth (AWC)', 'Deficiencies (AWC)', 'Diseases (AWC)', 'Developmental Delay (AWC)', 'TOTAL 4D ANGANVADI',
                'Total No. of Children (School)', 'Screened (School)', 'Defect at birth (School)', 
                'Deficiencies (School)', 'Diseases (School)', 'Developmental Delay (School)', 'TOAL 4D SCHOOL'
            ]
            for c in num_cols:
                if c in df_t.columns:
                    df_t[c] = pd.to_numeric(df_t[c].astype(str).str.replace(',', ''), errors='coerce').fillna(0)

            # --- Calculate Globals for Teams ---
            df_t['Combined Registered'] = df_t.get('Total No. of Children (AWC)', 0) + df_t.get('Total No. of Children (School)', 0)
            df_t['Combined Screened'] = df_t.get('Screened (AWC)', 0) + df_t.get('Screened (School)', 0)
            df_t['Combined Screening %'] = np.where(df_t['Combined Registered'] > 0, (df_t['Combined Screened'] / df_t['Combined Registered']) * 100, 0)
            
            df_t['Combined 4D Found'] = df_t.get('TOTAL 4D ANGANVADI', 0) + df_t.get('TOAL 4D SCHOOL', 0)
            df_t['Combined Detection %'] = np.where(df_t['Combined Screened'] > 0, (df_t['Combined 4D Found'] / df_t['Combined Screened']) * 100, 0)
            
            df_t['School Screening %'] = np.where(df_t.get('Total No. of Children (School)', 0) > 0, (df_t.get('Screened (School)', 0) / df_t.get('Total No. of Children (School)', 0)) * 100, 0)

            # 1. 📊 RAW DATA TABLE
            st.markdown("### 📋 Team Raw Data Table")
            st.dataframe(df_t, use_container_width=True, hide_index=True)
            st.divider()

            # 2. 🏆 The Screening Leaderboard (Bar + Line)
            st.markdown("### 🏆 Overall Screening Leaderboard")
            fig_lead = go.Figure()
            fig_lead.add_trace(go.Bar(x=df_t['Team ID'], y=df_t['Combined Registered'], name='Total Registered', marker_color='#93c5fd'))
            fig_lead.add_trace(go.Bar(x=df_t['Team ID'], y=df_t['Combined Screened'], name='Total Screened', marker_color='#3b82f6'))
            fig_lead.add_trace(go.Scatter(x=df_t['Team ID'], y=df_t['Combined Screening %'], name='Screening %', yaxis='y2', line=dict(color='#ef4444', width=3), mode='lines+markers'))
            
            fig_lead.update_layout(
                title="Registered vs. Screened with Overall Percentage",
                barmode='group',
                yaxis=dict(title='Number of Children'),
                yaxis2=dict(title='Screening Percentage (%)', overlaying='y', side='right', range=[0, 100]),
                hovermode='x unified'
            )
            st.plotly_chart(fig_lead, use_container_width=True)

            # 3. 🧬 The 4D Clinical Breakdown (Stacked Bar)
            st.markdown("### 🧬 4D Clinical Profile by Team")
            df_t['Total Defects'] = df_t.get('Defect at birth (AWC)', 0) + df_t.get('Defect at birth (School)', 0)
            df_t['Total Deficiencies'] = df_t.get('Deficiencies (AWC)', 0) + df_t.get('Deficiencies (School)', 0)
            df_t['Total Diseases'] = df_t.get('Diseases (AWC)', 0) + df_t.get('Diseases (School)', 0)
            df_t['Total Delays'] = df_t.get('Developmental Delay (AWC)', 0) + df_t.get('Developmental Delay (School)', 0)

            fig_stack = go.Figure(data=[
                go.Bar(name='Defects at Birth', x=df_t['Team ID'], y=df_t['Total Defects'], marker_color='#f87171'),
                go.Bar(name='Deficiencies', x=df_t['Team ID'], y=df_t['Total Deficiencies'], marker_color='#fbbf24'),
                go.Bar(name='Diseases', x=df_t['Team ID'], y=df_t['Total Diseases'], marker_color='#34d399'),
                go.Bar(name='Delays', x=df_t['Team ID'], y=df_t['Total Delays'], marker_color='#a78bfa')
            ])
            fig_stack.update_layout(barmode='stack', title="Total 4D Conditions Found per Team")
            st.plotly_chart(fig_stack, use_container_width=True)

            c1, c2 = st.columns(2)
            
            # 4. 🏫 AWC vs. School Focus (Grouped Bar)
            with c1:
                st.markdown("### 🏫 Operational Focus: AWC vs School")
                fig_focus = go.Figure(data=[
                    go.Bar(name='AWC Screening %', x=df_t['Team ID'], y=df_t.get('SCREENING PERCENTAGE', 0), marker_color='#f472b6'),
                    go.Bar(name='School Screening %', x=df_t['Team ID'], y=df_t['School Screening %'], marker_color='#60a5fa')
                ])
                fig_focus.update_layout(barmode='group', title="Screening Percentage Comparison", yaxis=dict(range=[0, 100]))
                st.plotly_chart(fig_focus, use_container_width=True)

            # 5. 🎯 The "Quality vs. Quantity" Scatter Matrix
            with c2:
                st.markdown("### 🎯 Efficiency Matrix: Quality vs. Quantity")
                fig_scatter = px.scatter(df_t, x='Combined Screening %', y='Combined Detection %', 
                                         text='Team ID', size='Combined Screened', color='Combined Detection %',
                                         title="Screening Velocity vs. Detection Rate",
                                         labels={'Combined Screening %': 'Quantity (Screening %)', 'Combined Detection %': 'Quality (Detection %)'},
                                         color_continuous_scale='Viridis')
                fig_scatter.update_traces(textposition='top center')
                fig_scatter.update_layout(xaxis=dict(range=[-5, 105]))
                st.plotly_chart(fig_scatter, use_container_width=True)

        else:
            st.warning("⚠️ Could not locate the 'Team_4D_Report' sheet. Make sure you spelled the sheet name exactly as 'Team_4D_Report' in Google Sheets!")

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
    
    # --- TAB 1: PHYSICAL FIELD VISITS ---
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
            b1, b2, b3, b4, b5 = st.columns(5)
            with b1: dob = st.date_input("Date of Birth")
            with b2: gender = st.selectbox("Gender", ["Male", "Female"])
            with b3: birth_weight = st.number_input("Birth Weight (kg)", min_value=0.0, step=0.1)
            with b4: delivery_type = st.selectbox("Delivery Type", ["Normal Delivery (ND)", "C-Section (LSCS)", "Instrumental"])
            with b5: delivery_point = st.selectbox("Delivery Point", ["Vatsalya Hospital", "SDH Visavadar", "Jay Ambe Hospital", "Junagadh Civil Hospital", "CHC/PHC", "Home Delivery", "Other Private Hospital"])

            st.divider()
            disease = st.text_input("🦠 Disease / Defect Identified?", placeholder="e.g., Cleft lip, None")
            observations = st.text_area("📝 Clinical Observations", height=100)

            if st.form_submit_button("💾 Save HBNC Record"):
                if child_name == "" or parent_name == "":
                    st.error("🚨 Enter Child and Parent Name.")
                else:
                    try:
                        # FIX: Reordered list so gender goes to the end column as per your sheet update
                        spreadsheet.worksheet("hbnc_screenings").append_row([
                            str(visit_date), 
                            child_name, 
                            parent_name, 
                            contact_number, 
                            str(dob), 
                            birth_weight, 
                            delivery_type, 
                            delivery_point, 
                            techo_id, 
                            disease, 
                            observations, 
                            village_name,
                            gender # Gender moved to the end
                        ])
                        st.toast(f"✅ Recorded Visit for {child_name}.", icon="🎉")
                        get_hbnc_logs.clear() 
                        import time
                        time.sleep(0.5)
                        st.rerun()
                    except Exception as e:
                        st.error(f"⚠️ Error: Could not find 'hbnc_screenings' tab. {e}")
                        
        st.divider()
        st.subheader("📋 Recent Physical HBNC Records & Analytics")
        try:
            if not df_hbnc_live.empty:
                
                # ==========================================
                # 🚀 NEW: HOSPITAL-WISE DEMOGRAPHICS TABLE
                # ==========================================
                if all(col in df_hbnc_live.columns for col in ["Delivery Point", "Gender", "Delivery Type"]):
                    st.markdown("##### 🏥 Hospital-wise Demographics & Delivery Analysis")
                    
                    # Group by Delivery Point and calculate metrics
                    hbnc_stats = df_hbnc_live.groupby("Delivery Point").apply(
                        lambda x: pd.Series({
                            "Total Deliveries": len(x),
                            "Male 👦": (x["Gender"].astype(str).str.strip().str.title() == "Male").sum(),
                            "Female 👧": (x["Gender"].astype(str).str.strip().str.title() == "Female").sum(),
                            "Normal (ND) 🟢": x["Delivery Type"].astype(str).str.contains("Normal", case=False, na=False).sum(),
                            "C-Section (LSCS) 🔴": x["Delivery Type"].astype(str).str.contains("C-Section|LSCS", case=False, na=False).sum()
                        })
                    ).reset_index()
                    
                    # Sort to show highest deliveries first
                    hbnc_stats = hbnc_stats.sort_values("Total Deliveries", ascending=False).reset_index(drop=True)
                    
                    # Display the analytical table
                    st.dataframe(hbnc_stats, use_container_width=True, hide_index=True)
                    st.divider()
                # ==========================================

                # --- ADDED FILTERS ---
                st.markdown("##### 🔍 View Detailed Records")
                f1, f2, f3 = st.columns(3)
                
                if "Delivery Type" in df_hbnc_live.columns:
                    with f1: filter_del_type = st.selectbox("Filter by Delivery Type", ["All"] + list(df_hbnc_live["Delivery Type"].unique()))
                else: filter_del_type = "All"
                
                if "Delivery Point" in df_hbnc_live.columns:
                    with f2: filter_del_point = st.selectbox("Filter by Delivery Point", ["All"] + list(df_hbnc_live["Delivery Point"].unique()))
                else: filter_del_point = "All"
                
                if "Gender" in df_hbnc_live.columns:
                    with f3: filter_gender = st.selectbox("Filter by Gender", ["All"] + list(df_hbnc_live["Gender"].unique()))
                else: filter_gender = "All"

                # Apply Filters
                filtered_hbnc = df_hbnc_live.copy()
                if filter_del_type != "All":
                    filtered_hbnc = filtered_hbnc[filtered_hbnc["Delivery Type"] == filter_del_type]
                if filter_del_point != "All":
                    filtered_hbnc = filtered_hbnc[filtered_hbnc["Delivery Point"] == filter_del_point]
                if filter_gender != "All":
                    filtered_hbnc = filtered_hbnc[filtered_hbnc["Gender"] == filter_gender]

                st.dataframe(filtered_hbnc, use_container_width=True)
                csv_hbnc = filtered_hbnc.to_csv(index=False).encode('utf-8-sig')
                st.download_button(label="⬇️ Download Physical Visit Data", data=csv_hbnc, file_name=f"HBNC_Physical_Visits.csv", mime="text/csv")
            else:
                st.info("No physical visit data found yet.")
        except Exception as e:
            st.warning(f"⚠️ Could not load physical data table. Reason: {e}")

    # --- TAB 2: TELEPHONIC TECHO QUEUE (UNTOUCHED) ---
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

    # 🚀 NEW: Tabbed Interface for Schools!
    tab_search, tab_summary = st.tabs(["🔍 School ID Search", "📊 PHC Analytics & Matrix"])

    with tab_search:
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

    with tab_summary:
        st.subheader("📈 Master PHC & School Summary")
        st.write("A complete infrastructure and demographic breakdown of all schools across your PHCs.")
        
        if not df_directory.empty:
            # PHC Filter UI
            phc_col = 'PHC'
            if phc_col in df_directory.columns:
                phc_list = sorted([str(x) for x in df_directory[phc_col].unique() if str(x).strip() not in ['', 'nan', 'None']])
                selected_phc = st.selectbox("🎯 Filter by PHC:", ["All PHCs"] + phc_list)
                
                if selected_phc != "All PHCs":
                    filtered_school_df = df_directory[df_directory[phc_col].astype(str).str.strip() == selected_phc]
                else:
                    filtered_school_df = df_directory
            else:
                filtered_school_df = df_directory
                st.warning("⚠️ PHC column could not be identified.")

            # Safe integer converter for math
            def safe_int(val):
                try:
                    clean_str = ''.join(c for c in str(val).replace(',', '.') if c.isdigit() or c == '.')
                    return int(float(clean_str)) if clean_str else 0
                except: 
                    return 0

            # --- TOP LEVEL ANALYTICS ---
            total_schools = len(filtered_school_df)
            
            # Government vs Private Breakdown
            cat_series = filtered_school_df.get('GOVT/PRIVATE', pd.Series(dtype=str)).astype(str).str.upper()
            govt_count = len(filtered_school_df[cat_series.str.contains('GOVT|GOVERNMENT', na=False)])
            pvt_count = len(filtered_school_df[cat_series.str.contains('PRIV|SELF|GRANT', na=False)])
            
            # Primary vs High School Breakdown
            type_series = filtered_school_df.get('PRIMARY/HIGH SCHOOL', pd.Series(dtype=str)).astype(str).str.upper()
            primary_count = len(filtered_school_df[type_series.str.contains('PRI|LOWER', na=False)])
            high_count = len(filtered_school_df[type_series.str.contains('HIGH|SEC|UPPER', na=False)])

            # Total Students Demographic
            grand_total = sum(safe_int(x) for x in filtered_school_df.get('TOTAL', []))
            grand_boys = sum(safe_int(x) for x in filtered_school_df.get('TOTAL BOYS', []))
            grand_girls = sum(safe_int(x) for x in filtered_school_df.get('TOTAL GIRLS', []))

            st.divider()
            st.markdown(f"### 🏆 Metrics for: {selected_phc}")
            
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("🏫 Total Schools", total_schools)
            m2.metric("👩‍🎓 Total Students", grand_total)
            m3.metric("👦 Boys", grand_boys)
            m4.metric("👧 Girls", grand_girls)

            st.markdown("#### 🏛️ School Infrastructure & Category")
            i1, i2, i3, i4 = st.columns(4)
            i1.metric("🏛️ Government Schools", govt_count)
            i2.metric("🏢 Private Schools", pvt_count)
            i3.metric("🎒 Primary Schools", primary_count)
            i4.metric("🎓 High Schools", high_count)

            st.divider()
            st.markdown("#### 📚 Detailed Standard-Wise & Gender-Wise Matrix")

            # --- DETAILED MATRIX GENERATION ---
            summary_data = []
            class_prefixes = ['BV', 'CLS1', 'CLS2', 'CLS3', 'CLS4', 'CLS5', 'CLS6', 'CLS7', 'CLS8', 'CLS9', 'CLS10', 'CLS11', 'CLS12']
            class_names = ['Bal Vatika', 'Class 1', 'Class 2', 'Class 3', 'Class 4', 'Class 5', 'Class 6', 'Class 7', 'Class 8', 'Class 9', 'Class 10', 'Class 11', 'Class 12']

            for _, row in filtered_school_df.iterrows():
                row_data = {
                    "PHC": str(row.get('PHC', 'N/A')).strip(),
                    "School Name": str(row.get('School', 'N/A')).strip(),
                    "Category": str(row.get('GOVT/PRIVATE', 'N/A')).strip(),
                    "Type": str(row.get('PRIMARY/HIGH SCHOOL', 'N/A')).strip(),
                    "Total Boys": safe_int(row.get('TOTAL BOYS', 0)),
                    "Total Girls": safe_int(row.get('TOTAL GIRLS', 0)),
                    "Total Students": safe_int(row.get('TOTAL', 0))
                }
                
                # Append gender-wise breakdown for EVERY standard!
                for prefix, name in zip(class_prefixes, class_names):
                    row_data[f"{name} (Boys)"] = safe_int(row.get(f'{prefix}_B', 0))
                    row_data[f"{name} (Girls)"] = safe_int(row.get(f'{prefix}_G', 0))
                    row_data[f"{name} (Total)"] = safe_int(row.get(f'Total_{prefix}', 0))
                    
                summary_data.append(row_data)

            if summary_data:
                summary_df = pd.DataFrame(summary_data).sort_values(by=["PHC", "School Name"])
                
                # 🚀 NEW: Generate and Append Total Row
                total_row = {}
                for col in summary_df.columns:
                    if col == "PHC":
                        total_row[col] = "🏆 GRAND TOTAL"
                    elif col in ["School Name", "Category", "Type"]:
                        total_row[col] = "-"
                    else:
                        total_row[col] = summary_df[col].sum()
                
                # Safely append the total row to the bottom
                summary_df = pd.concat([summary_df, pd.DataFrame([total_row])], ignore_index=True)
                
                import datetime
                csv_summary = summary_df.to_csv(index=False).encode('utf-8-sig')
                st.download_button(
                    label="⬇️ Download School Matrix Summary (CSV)",
                    data=csv_summary,
                    file_name=f"School_Matrix_Summary_{datetime.date.today()}.csv",
                    mime="text/csv"
                )
                
                st.dataframe(summary_df, use_container_width=True, hide_index=True)
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
                    aw_data = df_aw[df_aw['AWC Name'] == selected_awc].copy()
                    total_kids = len(aw_data)
                    
                    gender_col = next((c for c in aw_data.columns if str(c).lower() == 'gender'), None)
                    if gender_col:
                        is_M = aw_data[gender_col].astype(str).str.upper().str.startswith('M')
                        is_F = aw_data[gender_col].astype(str).str.upper().str.startswith('F')
                        boys = len(aw_data[is_M])
                        girls = len(aw_data[is_F])
                    else:
                        is_M = pd.Series([False]*len(aw_data), index=aw_data.index)
                        is_F = pd.Series([False]*len(aw_data), index=aw_data.index)
                        boys, girls = 0, 0

                    # 1. Broad Age Groups (From Beneficiary Type)
                    beneficiary_col = None
                    for col in aw_data.columns:
                        if 'beneficiary type' in str(col).lower():
                            beneficiary_col = col
                            break
                    if not beneficiary_col and len(aw_data.columns) >= 9:
                        beneficiary_col = aw_data.columns[8] # Fallback to Column I

                    if beneficiary_col:
                        is_0_6m = aw_data[beneficiary_col].astype(str).str.strip().str.lower() == 'children_0m_6m'
                        is_6m_3y = aw_data[beneficiary_col].astype(str).str.strip().str.lower() == 'children_6m_3y'
                        is_3y_6y = aw_data[beneficiary_col].astype(str).str.strip().str.lower() == 'children_3y_6y'
                        
                        age_0_6m_M, age_0_6m_F, age_0_6m_T = len(aw_data[is_0_6m & is_M]), len(aw_data[is_0_6m & is_F]), len(aw_data[is_0_6m])
                        age_6m_3y_M, age_6m_3y_F, age_6m_3y_T = len(aw_data[is_6m_3y & is_M]), len(aw_data[is_6m_3y & is_F]), len(aw_data[is_6m_3y])
                        age_3y_6y_M, age_3y_6y_F, age_3y_6y_T = len(aw_data[is_3y_6y & is_M]), len(aw_data[is_3y_6y & is_F]), len(aw_data[is_3y_6y])
                    else:
                        age_0_6m_M = age_0_6m_F = age_0_6m_T = 0
                        age_6m_3y_M = age_6m_3y_F = age_6m_3y_T = 0
                        age_3y_6y_M = age_3y_6y_F = age_3y_6y_T = 0

                    # 🚀 2. NEW SPECIFIC 5-6 YEARS (From DoB)
                    dob_col = next((c for c in aw_data.columns if 'dob' in str(c).lower() or 'date of birth' in str(c).lower()), None)
                    if not dob_col and len(aw_data.columns) >= 11:
                        dob_col = aw_data.columns[10] # Column K
                        
                    if dob_col:
                        dobs = pd.to_datetime(aw_data[dob_col], errors='coerce', dayfirst=True)
                        age_years = (pd.Timestamp.now() - dobs).dt.days / 365.25
                        is_5_to_6 = (age_years >= 5) & (age_years < 6)
                        
                        age_5_6y_M = len(aw_data[is_5_to_6 & is_M])
                        age_5_6y_F = len(aw_data[is_5_to_6 & is_F])
                        age_5_6y_T = len(aw_data[is_5_to_6])
                    else:
                        age_5_6y_M = age_5_6y_F = age_5_6y_T = 0
                    
                    st.markdown("#### 📊 Live Enrollment Summary")
                    c1, c2, c3 = st.columns(3)
                    c1.metric("👶 Total Children", total_kids)
                    c2.metric("👦 Boys", boys)
                    c3.metric("👧 Girls", girls)

                    # 🚀 NEW: 2x2 Grid for Age Matrix to fit the 5-6 Years elegantly
                    st.markdown("#### 🎂 Age & Gender Matrix")
                    a1, a2 = st.columns(2)
                    with a1:
                        st.info(f"**🍼 0 to 6 Months: {age_0_6m_T}**\n\n👦 Boys: **{age_0_6m_M}** | 👧 Girls: **{age_0_6m_F}**")
                        st.info(f"**🧒 3 to 6 Years: {age_3y_6y_T}**\n\n👦 Boys: **{age_3y_6y_M}** | 👧 Girls: **{age_3y_6y_F}**")
                    with a2:
                        st.info(f"**👶 6M to 3 Years: {age_6m_3y_T}**\n\n👦 Boys: **{age_6m_3y_M}** | 👧 Girls: **{age_6m_3y_F}**")
                        st.success(f"**🎓 5 to 6 Years (Specific): {age_5_6y_T}**\n\n👦 Boys: **{age_5_6y_M}** | 👧 Girls: **{age_5_6y_F}**")

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
            
            sector_col = None
            for col in df_aw.columns:
                if 'sector' in str(col).lower():
                    sector_col = col
                    break
            if not sector_col and len(df_aw.columns) >= 5:
                sector_col = df_aw.columns[4]

            beneficiary_col = None
            for col in df_aw.columns:
                if 'beneficiary type' in str(col).lower():
                    beneficiary_col = col
                    break
            if not beneficiary_col and len(df_aw.columns) >= 9:
                beneficiary_col = df_aw.columns[8]
                
            # Locate DoB column for entire dataframe
            dob_col = next((c for c in df_aw.columns if 'dob' in str(c).lower() or 'date of birth' in str(c).lower()), None)
            if not dob_col and len(df_aw.columns) >= 11:
                dob_col = df_aw.columns[10]

            selected_sector = "All Sectors"
            if sector_col:
                sector_list = sorted([str(x) for x in df_aw[sector_col].unique() if str(x).strip() not in ['', 'nan', 'None']])
                selected_sector = st.selectbox("🎯 Filter by Sector:", ["All Sectors"] + sector_list)
                
                if selected_sector != "All Sectors":
                    filtered_aw_df = df_aw[df_aw[sector_col].astype(str).str.strip() == selected_sector].copy()
                else:
                    filtered_aw_df = df_aw.copy()
            else:
                filtered_aw_df = df_aw.copy()
                st.warning("⚠️ Sector column (Column E) could not be identified.")
                
            # Pre-calculate age in years for speed
            if dob_col:
                dobs = pd.to_datetime(filtered_aw_df[dob_col], errors='coerce', dayfirst=True)
                filtered_aw_df['_age_years'] = (pd.Timestamp.now() - dobs).dt.days / 365.25
            else:
                filtered_aw_df['_age_years'] = -1

            summary_data = []
            gender_col = next((c for c in filtered_aw_df.columns if str(c).lower() == 'gender'), None)
            
            for awc in filtered_aw_df['AWC Name'].dropna().unique():
                aw_data = filtered_aw_df[filtered_aw_df['AWC Name'] == awc]
                total = len(aw_data)
                
                if gender_col:
                    is_M = aw_data[gender_col].astype(str).str.upper().str.startswith('M')
                    is_F = aw_data[gender_col].astype(str).str.upper().str.startswith('F')
                    boys = len(aw_data[is_M])
                    girls = len(aw_data[is_F])
                else:
                    is_M = pd.Series([False]*len(aw_data), index=aw_data.index)
                    is_F = pd.Series([False]*len(aw_data), index=aw_data.index)
                    boys, girls = 0, 0

                # 1. Beneficiary Type Breakdown
                if beneficiary_col:
                    is_0_6m = aw_data[beneficiary_col].astype(str).str.strip().str.lower() == 'children_0m_6m'
                    is_6m_3y = aw_data[beneficiary_col].astype(str).str.strip().str.lower() == 'children_6m_3y'
                    is_3y_6y = aw_data[beneficiary_col].astype(str).str.strip().str.lower() == 'children_3y_6y'
                    
                    age_0_6m_M, age_0_6m_F, age_0_6m_T = len(aw_data[is_0_6m & is_M]), len(aw_data[is_0_6m & is_F]), len(aw_data[is_0_6m])
                    age_6m_3y_M, age_6m_3y_F, age_6m_3y_T = len(aw_data[is_6m_3y & is_M]), len(aw_data[is_6m_3y & is_F]), len(aw_data[is_6m_3y])
                    age_3y_6y_M, age_3y_6y_F, age_3y_6y_T = len(aw_data[is_3y_6y & is_M]), len(aw_data[is_3y_6y & is_F]), len(aw_data[is_3y_6y])
                else:
                    age_0_6m_M = age_0_6m_F = age_0_6m_T = 0
                    age_6m_3y_M = age_6m_3y_F = age_6m_3y_T = 0
                    age_3y_6y_M = age_3y_6y_F = age_3y_6y_T = 0
                    
                # 2. Specific 5-6 Years Breakdown
                is_5_to_6 = (aw_data['_age_years'] >= 5) & (aw_data['_age_years'] < 6)
                age_5_6y_M = len(aw_data[is_5_to_6 & is_M])
                age_5_6y_F = len(aw_data[is_5_to_6 & is_F])
                age_5_6y_T = len(aw_data[is_5_to_6])
                
                awc_sector = aw_data[sector_col].iloc[0] if sector_col and not aw_data.empty else "N/A"
                
                summary_data.append({
                    "Sector": str(awc_sector).strip(),
                    "Anganwadi Center": str(awc).strip(),
                    "Total Children": total,
                    "👦 Boys": boys,
                    "👧 Girls": girls,
                    "🍼 0-6m (Boys)": age_0_6m_M,
                    "🍼 0-6m (Girls)": age_0_6m_F,
                    "🍼 0-6m (Total)": age_0_6m_T,
                    "👶 6m-3y (Boys)": age_6m_3y_M,
                    "👶 6m-3y (Girls)": age_6m_3y_F,
                    "👶 6m-3y (Total)": age_6m_3y_T,
                    "🧒 3-6y (Boys)": age_3y_6y_M,
                    "🧒 3-6y (Girls)": age_3y_6y_F,
                    "🧒 3-6y (Total)": age_3y_6y_T,
                    "🎓 5-6y (Boys)": age_5_6y_M,
                    "🎓 5-6y (Girls)": age_5_6y_F,
                    "🎓 5-6y (Total)": age_5_6y_T
                })
            
            if summary_data:
                summary_df = pd.DataFrame(summary_data).sort_values(by=["Sector", "Anganwadi Center"])
                
                total_all = summary_df['Total Children'].sum()
                total_boys = summary_df['👦 Boys'].sum()
                total_girls = summary_df['👧 Girls'].sum()
                total_awcs = summary_df['Anganwadi Center'].nunique()
                
                t_0_6m_M, t_0_6m_F, t_0_6m_T = summary_df['🍼 0-6m (Boys)'].sum(), summary_df['🍼 0-6m (Girls)'].sum(), summary_df['🍼 0-6m (Total)'].sum()
                t_6m_3y_M, t_6m_3y_F, t_6m_3y_T = summary_df['👶 6m-3y (Boys)'].sum(), summary_df['👶 6m-3y (Girls)'].sum(), summary_df['👶 6m-3y (Total)'].sum()
                t_3y_6y_M, t_3y_6y_F, t_3y_6y_T = summary_df['🧒 3-6y (Boys)'].sum(), summary_df['🧒 3-6y (Girls)'].sum(), summary_df['🧒 3-6y (Total)'].sum()
                t_5_6y_M, t_5_6y_F, t_5_6y_T = summary_df['🎓 5-6y (Boys)'].sum(), summary_df['🎓 5-6y (Girls)'].sum(), summary_df['🎓 5-6y (Total)'].sum()
                
                st.divider()
                st.markdown(f"### 🏆 Master Metrics for: {selected_sector}")
                
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("🏠 Anganwadis", total_awcs)
                m2.metric("👶 Total Children", total_all)
                m3.metric("👦 Boys", total_boys)
                m4.metric("👧 Girls", total_girls)

                st.markdown("#### 🎂 Age & Gender Matrix")
                a1, a2 = st.columns(2)
                with a1:
                    st.info(f"**🍼 0 to 6 Months: {t_0_6m_T}**\n\n👦 Boys: **{t_0_6m_M}** | 👧 Girls: **{t_0_6m_F}**")
                    st.info(f"**🧒 3 to 6 Years: {t_3y_6y_T}**\n\n👦 Boys: **{t_3y_6y_M}** | 👧 Girls: **{t_3y_6y_F}**")
                with a2:
                    st.info(f"**👶 6M to 3 Years: {t_6m_3y_T}**\n\n👦 Boys: **{t_6m_3y_M}** | 👧 Girls: **{t_6m_3y_F}**")
                    st.success(f"**🎓 5 to 6 Years: {t_5_6y_T}**\n\n👦 Boys: **{t_5_6y_M}** | 👧 Girls: **{t_5_6y_F}**")
                
                st.divider()
                
                import datetime
                csv_summary = summary_df.to_csv(index=False).encode('utf-8-sig')
                st.download_button(
                    label="⬇️ Download Sector Summary Matrix (CSV)",
                    data=csv_summary,
                    file_name=f"Anganwadi_Matrix_Summary_{datetime.date.today()}.csv",
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

    # 🚀 Force Refresh Button for the Command Center
    col_btn1, col_btn2 = st.columns([8, 2])
    with col_btn2:
        if st.button("🔄 Force Sync Latest Data"):
            st.cache_data.clear()
            st.toast("Data synchronized with live Google Sheets!", icon="✅")
            import time
            time.sleep(0.5)
            st.rerun()

    tab_form3, tab_scoreboard = st.tabs(["📄 Form III (Govt Export)", "🎯 Live Scoreboard (Target vs. Achievement)"])

    # 🚀 Fetch Master Mapping globally so both tabs run lightning fast!
    with st.spinner("Synchronizing Master Team Databases..."):
        try:
            master_aw = pd.DataFrame(spreadsheet.worksheet("aw new data").get_all_records())
            master_sch = pd.DataFrame(spreadsheet.worksheet("1240315 ALL STUDENTS NAMES").get_all_records())
        except:
            master_aw = pd.DataFrame()
            master_sch = pd.DataFrame()

        def find_m_col(df, keys):
            return next((c for c in df.columns if any(k in str(c).upper() for k in keys)), None)

        # 🧹 THE FIX: GHOST ROW PURGER 🧹
        # This explicitly deletes empty rows from Google Sheets so they aren't counted in your target!
        if not master_aw.empty:
            aw_name_col = find_m_col(master_aw, ["NAME", "CHILD", "STUDENT"])
            if aw_name_col:
                master_aw = master_aw[master_aw[aw_name_col].astype(str).str.strip() != '']
                
        if not master_sch.empty:
            sch_name_col = find_m_col(master_sch, ["NAME", "CHILD", "STUDENT"])
            if sch_name_col:
                master_sch = master_sch[master_sch[sch_name_col].astype(str).str.strip() != '']

        # Now map the clean data
        aw_loc_key = find_m_col(master_aw, ["INSTITUTE", "AWC", "CENTER", "AWC NAME"])
        aw_team_key = find_m_col(master_aw, ["TEAM"])
        aw_gender_key = find_m_col(master_aw, ["GENDER", "SEX"])
        aw_beneficiary_key = find_m_col(master_aw, ["BENEFICIARY TYPE"])

        sch_loc_key = find_m_col(master_sch, ["INSTITUTION", "SCHOOL"])
        sch_team_key = find_m_col(master_sch, ["TEAM"])
        sch_gender_key = find_m_col(master_sch, ["GENDER", "SEX"])

        team_lookup = {}
        if aw_loc_key and aw_team_key:
            team_lookup.update(dict(zip(master_aw[aw_loc_key].astype(str).str.strip(), master_aw[aw_team_key].astype(str).str.strip())))
        if sch_loc_key and sch_team_key:
            team_lookup.update(dict(zip(master_sch[sch_loc_key].astype(str).str.strip(), master_sch[sch_team_key].astype(str).str.strip())))

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
        
        inst_name_cols = [c for c in df_combined.columns if any(k in str(c).lower() for k in ['inst', 'school', 'awc', 'center', 'aw name', 'anganwadi'])]
        if inst_name_cols:
            df_combined['Official_Institution'] = df_combined[inst_name_cols[0]]
            for col in inst_name_cols[1:]:
                df_combined['Official_Institution'] = df_combined['Official_Institution'].combine_first(df_combined[col])
        else:
            df_combined['Official_Institution'] = "Unknown"

        # 🚀 Map Teams Globally
        df_combined['Mapped_Team'] = df_combined['Official_Institution'].astype(str).str.strip().map(team_lookup).fillna("Unassigned")

        if date_col and dob_col:
            df_combined[date_col] = df_combined[date_col].astype(str).str.strip()
            df_combined[dob_col] = df_combined[dob_col].astype(str).str.strip()
            
            df_combined[date_col] = df_combined[date_col].str.replace('/', '-').str.replace('.', '-', regex=False)
            df_combined[dob_col] = df_combined[dob_col].str.replace('/', '-').str.replace('.', '-', regex=False)
            
            df_combined[date_col] = pd.to_datetime(df_combined[date_col], dayfirst=True, format='mixed', errors='coerce')
            df_combined[dob_col] = pd.to_datetime(df_combined[dob_col], dayfirst=True, format='mixed', errors='coerce')
            
            df_combined = df_combined.dropna(subset=[date_col])

    # ==========================================
    # 📄 TAB 1: FORM III (TEAM-WISE)
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

                report_df['Age_Years'] = (report_df[date_col] - report_df[dob_col]).dt.days / 365.25
                
                def bucket_age(age):
                    if pd.isna(age): return "Unknown"
                    if age <= 3.0: return "0-3 Years"
                    if age <= 6.0: return "3-6 Years"
                    else: return "6-18 Years"
                
                report_df['Govt_Age_Bucket'] = report_df['Age_Years'].apply(bucket_age)
                
                if gender_col:
                    report_df['Clean_Gender'] = report_df[gender_col].astype(str).str.upper().str[0]
                else:
                    report_df['Clean_Gender'] = "U"

                st.markdown(f"## 📊 Official Form III Output: **{selected_month} {selected_year}**")
                st.write(f"Total Children Screened (Entire Block): **{len(report_df)}**")

                unknown_count = len(report_df[report_df['Govt_Age_Bucket'] == 'Unknown'])
                if unknown_count > 0:
                    st.warning(f"⚠️ **DATA ALERT:** There are **{unknown_count} children** with a missing or invalid Date of Birth. They cannot be sorted into the age buckets.")

                st.divider()

                teams_to_show = ["TEAM-1240315", "TEAM-1240309", "Unassigned"]
                
                for team in teams_to_show:
                    team_df = report_df[report_df['Mapped_Team'] == team]
                    if team_df.empty and team == "Unassigned":
                        continue # Hide Unassigned if empty
                        
                    st.markdown(f"### 🏥 {team}")
                    st.write(f"Total Screened by this team: **{len(team_df)}**")

                    col_0_3, col_3_6, col_6_18 = st.columns(3)
                    
                    def render_team_bucket(bucket_name, column_ui, t_df):
                        b_data = t_df[t_df['Govt_Age_Bucket'] == bucket_name]
                        boys = len(b_data[b_data['Clean_Gender'] == 'M'])
                        girls = len(b_data[b_data['Clean_Gender'] == 'F'])
                        with column_ui:
                            st.info(f"**{bucket_name}**")
                            st.metric("Total", len(b_data))
                            st.write(f"👦 Boys: **{boys}**")
                            st.write(f"👧 Girls: **{girls}**")
                    
                    render_team_bucket("0-3 Years", col_0_3, team_df)
                    render_team_bucket("3-6 Years", col_3_6, team_df)
                    render_team_bucket("6-18 Years", col_6_18, team_df)

                    m1, m2 = st.columns(2)
                    with m1:
                        st.write("**Nutritional Triage**")
                        if status_col:
                            sam_count = len(team_df[team_df[status_col].astype(str).str.upper() == 'SAM'])
                            mam_count = len(team_df[team_df[status_col].astype(str).str.upper() == 'MAM'])
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
                                
                            t_diseases = team_df[team_df[disease_col].apply(is_real_disease)]
                            if not t_diseases.empty:
                                d_counts = t_diseases.groupby([disease_col, 'Govt_Age_Bucket', 'Clean_Gender']).size().reset_index(name='Count')
                                d_counts.columns = ['Condition', 'Age Group', 'Gender', 'Count']
                                d_counts['Gender'] = d_counts['Gender'].map({'M': 'Boys', 'F': 'Girls', 'U': 'Unknown'}).fillna('Unknown')
                                st.dataframe(d_counts, use_container_width=True, hide_index=True)
                            else:
                                st.success("No 4D diseases logged by this team!")
                                
                    st.divider()

                st.markdown("### 📥 Download Cleaned Report")
                
                export_df = pd.DataFrame()
                export_df['Screening Date'] = report_df[date_col].dt.strftime('%d-%m-%Y')
                export_df['Assigned Team'] = report_df['Mapped_Team'] 
                export_df['Source'] = report_df['Source']
                export_df['Institution'] = report_df['Official_Institution'] 
                export_df['Child Name'] = report_df['Official_Child_Name']   
                export_df['DOB'] = report_df[dob_col].dt.strftime('%d-%m-%Y')
                export_df['Calculated Age (Yrs)'] = report_df['Age_Years'].round(2)
                export_df['Govt Age Bucket'] = report_df['Govt_Age_Bucket']
                export_df['Gender'] = report_df['Clean_Gender']
                
                def get_merged_col(df, keywords):
                    matched_cols = [c for c in df.columns if any(k in str(c).lower() for k in keywords)]
                    if not matched_cols: return None
                    merged = df[matched_cols[0]]
                    for c in matched_cols[1:]:
                        merged = merged.combine_first(df[c])
                    return merged

                ht_data = get_merged_col(report_df, ['height', 'ht', 'ઊંચાઈ'])
                wt_data = get_merged_col(report_df, ['weight', 'wt', 'વજન'])
                hb_data = get_merged_col(report_df, ['hb', 'hemoglobin'])
                muac_data = get_merged_col(report_df, ['muac'])

                if ht_data is not None: export_df['Height'] = ht_data
                if wt_data is not None: export_df['Weight'] = wt_data
                if hb_data is not None: export_df['Hb (School)'] = hb_data
                if muac_data is not None: export_df['MUAC (AW)'] = muac_data
                
                if status_col: export_df['Nutrition (SAM/MAM)'] = report_df[status_col]
                if disease_col: export_df['4D Condition Found'] = report_df[disease_col]

                with st.expander("👁️ Preview Streamlined CSV Data"):
                    unique_institutions = sorted(list(set([str(i).strip() for i in export_df['Institution'].dropna() if str(i).strip() != ""])))
                    selected_inst = st.selectbox("🏢 Filter by Institution (Optional):", ["All Institutions"] + unique_institutions, key="preview_filter")
                    
                    preview_df = export_df.copy()
                    if selected_inst != "All Institutions":
                        preview_df = preview_df[preview_df['Institution'].astype(str).str.strip() == selected_inst]
                        
                    st.dataframe(preview_df, use_container_width=True, hide_index=True)

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
    # 🎯 TAB 2: LIVE SCOREBOARD (MASTER TALUKA + GRANULAR MATRIX)
    # ==========================================
    with tab_scoreboard:
        st.subheader("🏆 Team-wise Performance Command Center")
        st.markdown("**Block:** Visavadar | **District:** Junagadh")

        try:
            with st.spinner("Calculating Taluka Matrix, Cycles, and Achievements..."):
                
                if not df_combined.empty and date_col:
                    df_combined['Screening_Month'] = df_combined[date_col].dt.month
                    df_combined['Cycle'] = df_combined['Screening_Month'].apply(lambda m: 'Cycle 1' if 4 <= m <= 9 else 'Cycle 2')
                    
                    if dob_col:
                        df_combined['_age'] = (df_combined[date_col] - df_combined[dob_col]).dt.days / 365.25
                    else:
                        df_combined['_age'] = 10.0 
                        
                    if gender_col:
                        df_combined['_g'] = df_combined[gender_col].astype(str).str.upper().str[0]
                    else:
                        df_combined['_g'] = 'U'

                stats = {}
                team_ids = ["TEAM-1240315", "TEAM-1240309"]

                for t_id in team_ids:
                    stats[t_id] = {
                        "tgt_aw_base": 0, "tgt_sch_base": 0,
                        "tgt_aw_0_6m_M": 0, "tgt_aw_0_6m_F": 0,
                        "tgt_aw_6m_3y_M": 0, "tgt_aw_6m_3y_F": 0,
                        "tgt_aw_3_6y_M": 0, "tgt_aw_3_6y_F": 0,
                        "tgt_sch_M": 0, "tgt_sch_F": 0,
                        
                        "ach_c1_aw": 0, "ach_c2_aw": 0, "ach_sch": 0,
                        "ach_aw_0_6m_M": 0, "ach_aw_0_6m_F": 0,
                        "ach_aw_6m_3y_M": 0, "ach_aw_6m_3y_F": 0,
                        "ach_aw_3_6y_M": 0, "ach_aw_3_6y_F": 0,
                        "ach_sch_M": 0, "ach_sch_F": 0
                    }
                    
                    if aw_team_key:
                        t_aw_df = master_aw[master_aw[aw_team_key].astype(str).str.strip() == t_id].copy()
                        stats[t_id]["tgt_aw_base"] = len(t_aw_df)
                        
                        if aw_gender_key and aw_beneficiary_key:
                            is_M = t_aw_df[aw_gender_key].astype(str).str.upper().str.startswith('M')
                            is_F = t_aw_df[aw_gender_key].astype(str).str.upper().str.startswith('F')
                            b_type = t_aw_df[aw_beneficiary_key].astype(str).str.lower().str.strip()
                            
                            stats[t_id]["tgt_aw_0_6m_M"] = len(t_aw_df[(b_type == 'children_0m_6m') & is_M]) * 2
                            stats[t_id]["tgt_aw_0_6m_F"] = len(t_aw_df[(b_type == 'children_0m_6m') & is_F]) * 2
                            stats[t_id]["tgt_aw_6m_3y_M"] = len(t_aw_df[(b_type == 'children_6m_3y') & is_M]) * 2
                            stats[t_id]["tgt_aw_6m_3y_F"] = len(t_aw_df[(b_type == 'children_6m_3y') & is_F]) * 2
                            stats[t_id]["tgt_aw_3_6y_M"] = len(t_aw_df[(b_type == 'children_3y_6y') & is_M]) * 2
                            stats[t_id]["tgt_aw_3_6y_F"] = len(t_aw_df[(b_type == 'children_3y_6y') & is_F]) * 2

                    if sch_team_key:
                        t_sch_df = master_sch[master_sch[sch_team_key].astype(str).str.strip() == t_id].copy()
                        stats[t_id]["tgt_sch_base"] = len(t_sch_df)
                        
                        if sch_gender_key:
                            stats[t_id]["tgt_sch_M"] = len(t_sch_df[t_sch_df[sch_gender_key].astype(str).str.upper().str.startswith('M')])
                            stats[t_id]["tgt_sch_F"] = len(t_sch_df[t_sch_df[sch_gender_key].astype(str).str.upper().str.startswith('F')])

                    if not df_combined.empty and date_col:
                        t_daily = df_combined[df_combined['Mapped_Team'] == t_id].copy()
                        
                        t_aw_daily = t_daily[t_daily['Source'] == 'Anganwadi']
                        stats[t_id]["ach_c1_aw"] = len(t_aw_daily[t_aw_daily['Cycle'] == 'Cycle 1'])
                        stats[t_id]["ach_c2_aw"] = len(t_aw_daily[t_aw_daily['Cycle'] == 'Cycle 2'])
                        
                        stats[t_id]["ach_aw_0_6m_M"] = len(t_aw_daily[(t_aw_daily['_age'] <= 0.5) & (t_aw_daily['_g'] == 'M')])
                        stats[t_id]["ach_aw_0_6m_F"] = len(t_aw_daily[(t_aw_daily['_age'] <= 0.5) & (t_aw_daily['_g'] == 'F')])
                        stats[t_id]["ach_aw_6m_3y_M"] = len(t_aw_daily[(t_aw_daily['_age'] > 0.5) & (t_aw_daily['_age'] <= 3.0) & (t_aw_daily['_g'] == 'M')])
                        stats[t_id]["ach_aw_6m_3y_F"] = len(t_aw_daily[(t_aw_daily['_age'] > 0.5) & (t_aw_daily['_age'] <= 3.0) & (t_aw_daily['_g'] == 'F')])
                        stats[t_id]["ach_aw_3_6y_M"] = len(t_aw_daily[(t_aw_daily['_age'] > 3.0) & (t_aw_daily['_age'] <= 6.0) & (t_aw_daily['_g'] == 'M')])
                        stats[t_id]["ach_aw_3_6y_F"] = len(t_aw_daily[(t_aw_daily['_age'] > 3.0) & (t_aw_daily['_age'] <= 6.0) & (t_aw_daily['_g'] == 'F')])

                        t_sch_daily = t_daily[(t_daily['Source'] == 'School') & (t_daily[date_col] >= '2026-03-01')]
                        stats[t_id]["ach_sch"] = len(t_sch_daily)
                        stats[t_id]["ach_sch_M"] = len(t_sch_daily[t_sch_daily['_g'] == 'M'])
                        stats[t_id]["ach_sch_F"] = len(t_sch_daily[t_sch_daily['_g'] == 'F'])

                taluka = {k: sum(stats[t][k] for t in team_ids) for k in stats[team_ids[0]].keys()}
                
                def render_dashboard(title, data, is_taluka=False):
                    total_annual_target = (data["tgt_aw_base"] * 2) + data["tgt_sch_base"]
                    total_achieved = data["ach_c1_aw"] + data["ach_c2_aw"] + data["ach_sch"]
                    overall_pct = (total_achieved / total_annual_target * 100) if total_annual_target > 0 else 0
                    
                    if is_taluka:
                        st.markdown(f"## 🌟 {title}")
                    else:
                        st.divider()
                        st.markdown(f"### 🚀 {title}")

                    sc1, sc2, sc3 = st.columns(3)
                    sc1.metric("Grand Annual Target", f"{total_annual_target:,}", help=f"AW ({data['tgt_aw_base']} x 2) + Sch ({data['tgt_sch_base']})")
                    sc2.metric("Total Achieved", f"{total_achieved:,}", delta=f"{total_achieved - total_annual_target} Remaining")
                    sc3.metric("Overall Completion", f"{overall_pct:.2f}%")
                    st.progress(min(overall_pct / 100.0, 1.0))

                    s1, s2, s3 = st.columns(3)
                    s1.info(f"**🏫 Schools (1x Cycle)**\n\nTarget: **{data['tgt_sch_base']}**\n\nAchieved: **{data['ach_sch']}**")
                    s2.success(f"**👶 AW (Cycle 1: Apr-Sep)**\n\nTarget: **{data['tgt_aw_base']}**\n\nAchieved: **{data['ach_c1_aw']}**")
                    s3.warning(f"**👶 AW (Cycle 2: Oct-Mar)**\n\nTarget: **{data['tgt_aw_base']}**\n\nAchieved: **{data['ach_c2_aw']}**")

                    with st.expander(f"📊 View Age & Gender Matrix for {title}"):
                        matrix_data = [
                            {"Metric": "🍼 AW: 0 - 6 Months (Boys)", "Annual Target": data["tgt_aw_0_6m_M"], "Achieved": data["ach_aw_0_6m_M"]},
                            {"Metric": "🍼 AW: 0 - 6 Months (Girls)", "Annual Target": data["tgt_aw_0_6m_F"], "Achieved": data["ach_aw_0_6m_F"]},
                            {"Metric": "👶 AW: 6M - 3 Years (Boys)", "Annual Target": data["tgt_aw_6m_3y_M"], "Achieved": data["ach_aw_6m_3y_M"]},
                            {"Metric": "👶 AW: 6M - 3 Years (Girls)", "Annual Target": data["tgt_aw_6m_3y_F"], "Achieved": data["ach_aw_6m_3y_F"]},
                            {"Metric": "🧒 AW: 3 - 6 Years (Boys)", "Annual Target": data["tgt_aw_3_6y_M"], "Achieved": data["ach_aw_3_6y_M"]},
                            {"Metric": "🧒 AW: 3 - 6 Years (Girls)", "Annual Target": data["tgt_aw_3_6y_F"], "Achieved": data["ach_aw_3_6y_F"]},
                            {"Metric": "🎓 Schools: 6 - 18 Years (Boys)", "Annual Target": data["tgt_sch_M"], "Achieved": data["ach_sch_M"]},
                            {"Metric": "🎓 Schools: 6 - 18 Years (Girls)", "Annual Target": data["tgt_sch_F"], "Achieved": data["ach_sch_F"]}
                        ]
                        
                        df_matrix = pd.DataFrame(matrix_data)
                        df_matrix['% Completed'] = (df_matrix['Achieved'] / df_matrix['Annual Target'] * 100).fillna(0).round(1).astype(str) + "%"
                        st.dataframe(df_matrix, use_container_width=True, hide_index=True)

                render_dashboard("TALUKA GRAND SUMMARY (ALL TEAMS)", taluka, is_taluka=True)
                for t_id in team_ids:
                    render_dashboard(f"Team: {t_id}", stats[t_id])

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
