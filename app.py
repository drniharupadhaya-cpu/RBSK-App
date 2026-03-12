import streamlit as st
import pandas as pd
import gspread
import json
from fpdf import FPDF
import tempfile
import os
import time
import plotly.express as px  # <-- NEW: THE GRAPHICS ENGINE!
# ==========================================
# UI DESIGN STUDIO: COLORFUL MODULE BANNERS
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
# ==========================================
# GLOBAL PDF ENGINE (Place this at the Top)
# ==========================================
import os
import urllib.request
from fpdf import FPDF

def generate_refer_card(data):
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.add_page()
    
    # 🌟 MAGIC FONT DOWNLOADER 🌟
    # If the font isn't there, the app downloads it automatically!
    font_path = "gujarati.ttf"
    if not os.path.exists(font_path):
        try:
            url = "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSansGujarati/NotoSansGujarati-Regular.ttf"
            urllib.request.urlretrieve(url, font_path)
        except Exception as e:
            pass # Fallback to English if internet fails

    # Check if font successfully downloaded
    font_exists = os.path.exists(font_path)
    
    if font_exists:
        try:
            pdf.add_font('Gujarati', '', font_path)
            pdf.set_font('Gujarati', '', 12)
            f_gu = 'Gujarati'
            
            # EXACT LABELS FROM YOUR PHYSICAL CARD
            lbl_title1 = "RBSK સંદર્ભ કાર્ડ"
            lbl_title2 = "શાળા આરોગ્ય - રાષ્ટ્રીય બાળ સ્વાસ્થ્ય કાર્યક્રમ"
            lbl_name = "બાળકનું પૂરુ નામ:"
            lbl_gender = "સ્ત્રી / પુરુષ:"
            lbl_dob = "બાળકની જન્મ તારીખ:"
            lbl_age = "ઉંમર:"
            lbl_father = "બાળકના પિતાનું પૂરુ નામ:"
            lbl_mother = "માતાનું નામ:"
            lbl_address = "પૂરુ સરનામું:"
            lbl_village = "ગામ / શહેર:"
            lbl_taluka = "તાલુકો: Visavadar"
            lbl_dist = "જિલ્લો: JUNAGADH"
            lbl_inst = "શાળા / આંગણવાડીનું નામ:"
            lbl_4d = "4D Category:"
            lbl_condition = "પ્રાથમિક તપાસણીની વિગત:"
            lbl_team = "મોબાઈલ હેલ્થ ટીમ નંબર:"
            lbl_date = "પ્રાથમિક તપાસણી કર્યા તારીખ:"
        except:
            font_exists = False

    if not font_exists:
        pdf.set_font('Arial', '', 12)
        f_gu = 'Arial'
        lbl_title1 = "RBSK Refer Card"
        lbl_title2 = "School Health - National Child Health Program"
        lbl_name = "Name:"; lbl_gender = "Gender:"; lbl_dob = "DOB:"
        lbl_age = "Age:"; lbl_father = "Father's Name:"; lbl_mother = "Mother's Name:"
        lbl_address = "Address:"; lbl_village = "Village/City:"
        lbl_taluka = "Taluka: Visavadar"; lbl_dist = "District: JUNAGADH"
        lbl_inst = "School / AWC Name:"; lbl_4d = "4D Category:"
        lbl_condition = "Suspected Condition / Findings:"
        lbl_team = "MHT Team No:"; lbl_date = "Screening Date:"

    # --- DRAW THE EXACT CARD FORMAT ---
    pdf.rect(5, 5, 200, 287) # Outer Border
    
    # Header
    pdf.set_font(f_gu, '', 16)
    pdf.cell(190, 8, lbl_title1, ln=True, align='C')
    pdf.set_font(f_gu, '', 14)
    pdf.cell(190, 8, lbl_title2, ln=True, align='C')
    pdf.ln(5)
    
    # Child & Parent Details
    pdf.set_font(f_gu, '', 11)
    pdf.cell(190, 8, f"{lbl_name} {data.get('Name', '')}", border='B', ln=True)
    
    c_w = 95
    pdf.cell(c_w, 8, f"{lbl_gender} {data.get('Gender', '')}")
    pdf.cell(c_w, 8, f"{lbl_dob} {data.get('DOB', '')}", ln=True)
    
    pdf.cell(c_w, 8, f"{lbl_age} {data.get('Age', '')}")
    pdf.cell(c_w, 8, f"TECHO ID: {data.get('Techo', 'N/A')}", ln=True)
    
    pdf.ln(2)
    pdf.cell(190, 8, f"{lbl_father} {data.get('Father', '')}", ln=True)
    pdf.cell(190, 8, f"{lbl_mother} {data.get('Mother', '')}", ln=True)
    pdf.cell(190, 8, f"{lbl_address} {data.get('Address', '')}", ln=True)
    
    pdf.cell(c_w, 8, f"{lbl_village} {data.get('Village', '')}")
    pdf.cell(c_w, 8, lbl_taluka, ln=True)
    
    pdf.cell(c_w, 8, lbl_dist)
    pdf.cell(c_w, 8, f"{lbl_inst} {data.get('Institution', '')}", ln=True)
    
    # 4D Categories & Condition
    pdf.ln(5)
    pdf.set_font(f_gu, '', 12)
    pdf.cell(190, 8, lbl_4d, ln=True)
    pdf.set_font('Arial', '', 10)
    pdf.cell(190, 8, "[ ] Birth Defect   [ ] Deficiency   [ ] Disease   [ ] Development Delay", ln=True)
    
    pdf.ln(3)
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font(f_gu, '', 12)
    pdf.cell(190, 10, lbl_condition, border=1, ln=True, fill=True)
    pdf.set_font('Arial', '', 11) # Keep medical condition in English
    pdf.multi_cell(190, 10, f"\n {data.get('Condition', 'None')} \n", border=1)
    
    # Signatures & Dates
    pdf.ln(10)
    pdf.set_font(f_gu, '', 11)
    pdf.cell(c_w, 8, f"{lbl_team} 1240315")
    pdf.cell(c_w, 8, f"{lbl_date} {data.get('Date', '')}", ln=True)
    
    pdf.ln(20)
    pdf.set_font('Arial', '', 10)
    pdf.cell(c_w, 8, "_______________________")
    pdf.cell(c_w, 8, "_______________________", ln=True)
    pdf.cell(c_w, 8, "Medical Officer Signature")
    pdf.cell(c_w, 8, "Institute/AWC Stamp", ln=True)
    
    return bytes(pdf.output())
# --- 1. GET THE LIVE DATABASE CONNECTION ---
def get_spreadsheet():
    creds_dict = json.loads(st.secrets["gcp_service_account"])
    client = gspread.service_account_from_dict(creds_dict)
    sheet_url = "https://docs.google.com/spreadsheets/d/1i5wAkI7k98E80qhHRe6xQOhF4Qj9Z0DH8wjPsQ7gRZc/edit?gid=2111634358#gid=2111634358"
    return client.open_by_url(sheet_url)

# --- 2. GET THE PURE DATA (WITH SMART AUTO-RETRY) ---
@st.cache_data(ttl=600)
def load_all_data():
    sheet = get_spreadsheet()
    
    def safe_load(tab_name, retries=3):
        for attempt in range(retries):
            try:
                df = pd.DataFrame(sheet.worksheet(tab_name).get_all_records()).astype(str)
                df.columns = df.columns.str.strip() 
                return df
            except Exception as e:
                error_msg = str(e)
                if '429' in error_msg or 'RESOURCE_EXHAUSTED' in error_msg:
                    if attempt < retries - 1:
                        time.sleep(10)
                        continue 
                st.error(f"🚨 FAILED ON TAB '{tab_name}': {e}")
                return pd.DataFrame()

    df_4d = safe_load("4d_list")
    df_schools = safe_load("school_details")
    df_aw = safe_load("aw_data")
    df_anemia = safe_load("ANEMIA")
    df_students = safe_load("students_data")
    df_directory = safe_load("ALL SCHOOL DETAILS")
    df_aw_contacts = safe_load("aw_master_directory")
    df_staff = safe_load("master_staff_directory")
    df_aw_master = safe_load("aw new data")
    df_all_students = safe_load("1240315 ALL STUDENTS NAMES")

    return df_4d, df_schools, df_aw, df_anemia, df_students, df_directory, df_aw_contacts, df_staff, df_aw_master, df_all_students

# --- 3. ACTIVATE BOTH ---
try:
    spreadsheet = get_spreadsheet() 
    df_4d, df_schools, df_aw, df_anemia, df_students, df_directory, df_aw_contacts, df_staff, df_aw_master, df_all_students = load_all_data() 
except Exception as e:
    st.error(f"Could not connect to Google Sheets. Please check your Secret Vault. Error: {e}")
    st.stop()

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("🩺 RBSK Menu")
st.sidebar.write("Dr. Workspace")
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
        "12. Automated State Report" # <-- ADD THIS NEW LINE!
    ]
)

# ... [Modules 1, 2, and 3 remain exactly the same as before] ...

# ==========================================
# MODULE 1: DAILY TOUR PLANNER
# ==========================================
if menu == "1. Daily Tour Plan":
    render_header("Executive Dashboard", "Live team overview and daily screening stats", "📊", "#3b82f6")
    st.write("Plan, edit, and track your medical team's field visits.")

    try:
        planner_sheet = spreadsheet.worksheet("tour_plan")
        df_plan = pd.DataFrame(planner_sheet.get_all_records())
    except:
        st.error("⚠️ Could not find the 'tour_plan' tab.")
        st.stop()

    tab_view, tab_add, tab_edit = st.tabs(["📅 View Schedule", "➕ Plan New Visit", "✏️ Edit / Delete Visit"])

    with tab_view:
        st.subheader("Upcoming Medical Tours")
        if not df_plan.empty:
            df_plan['Date'] = pd.to_datetime(df_plan['Date'])
            df_plan = df_plan.sort_values(by='Date')
            df_plan['Date'] = df_plan['Date'].dt.strftime('%Y-%m-%d')
            st.dataframe(df_plan, width='stretch', hide_index=True)
        else:
            st.info("No upcoming tours planned yet.")

    with tab_add:
        st.subheader("Schedule a New Field Visit")
        with st.form("add_tour_form"):
            col1, col2 = st.columns(2)
            with col1:
                visit_date = st.date_input("Select Date of Visit")
                location = st.text_input("Location / Village Name")
            with col2:
                activity = st.selectbox("Select Activity Type", [
                    "School Screening", "Anganvadi Screening", "Delivery Point Visit", 
                    "HBNC Visit", "Meeting", "Training", "Other"
                ])
            
            submit_plan = st.form_submit_button("💾 Save to Official Planner")

            if submit_plan:
                if location == "":
                    st.error("🚨 Please enter a Location/Village name!")
                else:
                    day_of_week = visit_date.strftime("%A") 
                    planner_sheet.append_row([str(visit_date), day_of_week, location, activity])
                    st.toast("✅ Data Saved Successfully!", icon="🎉")
                    st.success(f"✅ Successfully scheduled: {activity} at {location} on {visit_date}!")
                    st.rerun()

    with tab_edit:
        st.subheader("Modify an Existing Visit")
        if not df_plan.empty:
            df_plan['Select_Label'] = df_plan['Date'].astype(str) + " | " + df_plan['Location'] + " (" + df_plan['Activity'] + ")"
            selected_label = st.selectbox("Select a visit to edit:", df_plan['Select_Label'].tolist())
            selected_idx = df_plan[df_plan['Select_Label'] == selected_label].index[0]
            sheet_row = int(selected_idx) + 2 
            
            with st.form("edit_tour_form"):
                curr_date = pd.to_datetime(df_plan.loc[selected_idx, 'Date']).date()
                curr_loc = str(df_plan.loc[selected_idx, 'Location'])
                curr_act = str(df_plan.loc[selected_idx, 'Activity'])
                
                new_date = st.date_input("Update Date", value=curr_date)
                new_loc = st.text_input("Update Location", value=curr_loc)
                options = ["School Screening", "Anganvadi Screening", "Delivery Point Visit", "HBNC Visit", "Meeting", "Training", "Other"]
                default_idx = options.index(curr_act) if curr_act in options else 0
                new_act = st.selectbox("Update Activity", options, index=default_idx)
                
                st.divider()
                delete_checkbox = st.checkbox("🚨 Delete this visit entirely (Cannot be undone)")
                update_btn = st.form_submit_button("💾 Update / Delete Plan")

                if update_btn:
                    if delete_checkbox:
                        planner_sheet.delete_rows(sheet_row)
                        st.success("✅ The visit was removed from your schedule.")
                        st.rerun()
                    else:
                        new_day = new_date.strftime("%A")
                        planner_sheet.update(range_name=f"A{sheet_row}:D{sheet_row}", values=[[str(new_date), new_day, new_loc, new_act]])
                        st.success(f"✅ Visit updated to: {new_loc} on {new_date}")
                        st.rerun()
        else:
            st.info("No visits available to edit.")

# ==========================================
# MODULE 2: EMR SCREENING (WITH WHO Z-SCORE & MUAC AUTOPILOT)
# ==========================================
elif menu == "2. Child Screening":
    render_header("Child Screening & EMR", "Record vitals and auto-calculate SAM/MAM", "🩺", "#10b981")

    # --- CLINICAL MATH ENGINE: WHO WEIGHT-FOR-HEIGHT REFERENCE ---
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

    category = st.radio("Select Visit Type:", ["🏫 Schools", "👶 Anganwadi"], horizontal=True)
    st.divider()

    if category == "👶 Anganwadi":
        if not df_aw.empty:
            raw_list = df_aw['AWC Name'].dropna().unique().tolist()
            actual_institutes = sorted([str(i).strip() for i in raw_list if str(i).strip() != ''])
            inst_display = {name: f"{idx+1}. {name}" for idx, name in enumerate(actual_institutes)}
            
            selected_inst = st.selectbox(
                "Select Anganwadi Center:", 
                options=["-- Select --"] + actual_institutes,
                format_func=lambda x: inst_display.get(x, x)
            )
            if selected_inst != "-- Select --":
                filtered_children = df_aw[df_aw['AWC Name'] == selected_inst]
                actual_children = [str(c).strip() for c in filtered_children['Beneficiary Name'].tolist() if str(c).strip() != '']
        else:
            st.error("No Anganwadi data found.")
            selected_inst = "-- Select --"
            
    else: 
        if not df_students.empty:
            raw_list = df_students['School'].dropna().unique().tolist()
            actual_institutes = sorted([str(i).strip() for i in raw_list if str(i).strip() != ''])
            inst_display = {name: f"{idx+1}. {name}" for idx, name in enumerate(actual_institutes)}
            
            selected_inst = st.selectbox(
                "Select School:", 
                options=["-- Select --"] + actual_institutes,
                format_func=lambda x: inst_display.get(x, x)
            )
            if selected_inst != "-- Select --":
                filtered_children = df_students[df_students['School'] == selected_inst]
                actual_children = [str(c).strip() for c in filtered_children['StudentName'].tolist() if str(c).strip() != '']
        else:
            st.error("No School Student data found.")
            selected_inst = "-- Select --"

    if selected_inst != "-- Select --":
        child_display = {name: f"{idx+1}. {name}" for idx, name in enumerate(actual_children)}
        
        selected_child = st.selectbox(
            f"Select Child enrolled in {selected_inst}:", 
            options=["-- Select Child --", "➕ Register New Child"] + actual_children,
            format_func=lambda x: child_display.get(x, x)
        )
        
        if selected_child != "-- Select Child --":
            if selected_child == "➕ Register New Child":
                st.subheader("🆕 Register New Child")
                new_child_name = st.text_input("Enter Child's Full Name")
                col_n1, col_n2, col_n3 = st.columns(3)
                with col_n1: dob = st.date_input("Date of Birth")
                with col_n2: gender = st.selectbox("Gender", ["M", "F"])
                with col_n3: parent = st.text_input("Parent's Name")
                existing_contact = ""
                final_child_name = new_child_name
            else:
                st.subheader("👤 Child Profile & History")
                final_child_name = selected_child
                if category == "👶 Anganwadi":
                    child_info = filtered_children[filtered_children['Beneficiary Name'] == selected_child].iloc[0]
                    dob = child_info.get('DoB', 'N/A')
                    gender = child_info.get('Gender', 'N/A')
                    parent = child_info.get('Mother Name', 'N/A')
                    existing_contact = "" 
                    hist_h = child_info.get('Height', 'N/A')
                    hist_w = child_info.get('Weight', 'N/A')
                    hist_wasting = child_info.get('Wasting', 'N/A')
                    hist_disease = child_info.get('4d', 'None')
                    hist_hb = "N/A" 
                else:
                    child_info = filtered_children[filtered_children['StudentName'] == selected_child].iloc[0]
                    dob = child_info.get('DOB', 'N/A')
                    gender = child_info.get('Gender', 'N/A')
                    parent = child_info.get('FatherName', 'N/A')
                    contact_val = child_info.get('CONTACT NUMBER', '')
                    existing_contact = str(contact_val) if str(contact_val) != "nan" else ""
                    hist_h = child_info.get('HEIGHT', 'N/A')
                    hist_w = child_info.get('WEIGHT', 'N/A')
                    hist_wasting = "N/A"
                    hist_disease = child_info.get('4D', 'None')
                    hist_hb = child_info.get('Hb', 'N/A')

                cols = st.columns(3)
                cols[0].info(f"**DOB:** {dob}")
                cols[1].info(f"**Gender:** {gender}")
                cols[2].info(f"**Parent:** {parent}")

                st.markdown("##### 🕰️ Last Recorded Vitals (Baseline)")
                hist_cols = st.columns(4)
                hist_cols[0].metric(label="Previous Height", value=f"{hist_h} cm" if str(hist_h) != "nan" else "N/A")
                hist_cols[1].metric(label="Previous Weight", value=f"{hist_w} kg" if str(hist_w) != "nan" else "N/A")
                if category == "👶 Anganwadi":
                    hist_cols[2].metric(label="Previous Status", value=str(hist_wasting) if str(hist_wasting) != "nan" else "N/A")
                else:
                    hist_cols[2].metric(label="Previous Hb", value=f"{hist_hb} %" if str(hist_hb) != "nan" else "N/A")
                hist_cols[3].metric(label="Previous 4D", value=str(hist_disease) if str(hist_disease) != "nan" else "None")

            st.divider()
            st.subheader("🩺 Enter New Screening Vitals")
            with st.form("vitals_form"):
                screening_date = st.date_input("Date of Screening")
                c_col1, c_col2 = st.columns(2)
                
                # QoL UPGRADE: 10 Digits Max
                with c_col1: updated_contact = st.text_input("📞 Contact Number", value=existing_contact, max_chars=10, placeholder="10-digit mobile number")
                with c_col2: techo_id = st.text_input("🆔 Techo ID") if category == "👶 Anganwadi" else "N/A"

                v_col1, v_col2, v_col3, v_col4 = st.columns(4)
                
                # QoL UPGRADE: Clean text boxes without "0.00"
                with v_col1: height_str = st.text_input("Height (cm)", placeholder="e.g. 95.5")
                with v_col2: weight_str = st.text_input("Weight (kg)", placeholder="e.g. 14.2")
                with v_col3:
                    if category == "👶 Anganwadi":
                        muac_str = st.text_input("MUAC (cm)", placeholder="e.g. 12.5")
                    else:
                        muac_str = "0"
                        st.text_input("MUAC (cm)", value="Not required", disabled=True)
                with v_col4: hb_str = st.text_input("Hb %", placeholder="e.g. 11.0")

                disease = st.text_input("🦠 Disease Identified (4D)", placeholder="Type 'None' or describe...")
                save_btn = st.form_submit_button("💾 Save Screening Data")

            # --- ACTION BLOCK PROPERLY ALIGNED ---
            if save_btn:
                # QoL UPGRADE: Strict 10-Digit Check
                if updated_contact and len(updated_contact.strip()) != 10:
                    st.error("⚠️ Please enter a valid 10-digit contact number before saving.")
                else:
                    # Math Translator
                    def safe_float(val):
                        try: return float(val)
                        except: return 0.0

                    height_val = safe_float(height_str)
                    weight_val = safe_float(weight_str)
                    muac_val = safe_float(muac_str)
                    hb_val = safe_float(hb_str)

                    # 1. THE AUTOMATIC SAM/MAM CALCULATOR
                    final_status = "Normal"
                    if category == "👶 Anganwadi":
                        try:
                            h_m = height_val / 100
                            bmi = weight_val / (h_m * h_m) if h_m > 0 else 0
                            
                            if (muac_val > 0 and muac_val < 11.5) or (bmi > 0 and bmi < 13.0):
                                final_status = "SAM"
                            elif (muac_val >= 11.5 and muac_val < 12.5) or (bmi >= 13.0 and bmi < 14.5):
                                final_status = "MAM"
                        except:
                            final_status = "Error in Calculation"

                    # 2. SAVE TO GOOGLE SHEETS
                    try:
                        if category == "👶 Anganwadi":
                            ws = spreadsheet.worksheet("daily_screenings_aw")
                            new_row = [str(screening_date), selected_inst, final_child_name, str(dob), str(gender), height_val, weight_val, muac_val, hb_val, disease, updated_contact, techo_id, final_status]
                            ws.append_row(new_row)
                            st.success(f"✅ Saved to AWC Log! Status: {final_status}")
                            if final_status == "SAM":
                                st.error("🚨 CRITICAL: Child identified as SAM. Refer to CMTC immediately.")
                        else:
                            ws = spreadsheet.worksheet("daily_screenings_schools")
                            new_row = [str(screening_date), selected_inst, final_child_name, str(dob), str(gender), height_val, weight_val, hb_val, disease, updated_contact]
                            ws.append_row(new_row)
                            st.success(f"✅ Saved to School Log!")

                        st.cache_data.clear()

                    except Exception as e:
                        st.error(f"Failed to connect to Google Sheets: {e}")
# ==========================================
# MODULE 3: 4D DEFECT REGISTRY
# ==========================================
elif menu == "3. 4D Defect Registry":
    render_header("4D Defect Command Center", "Track referrals and generate official print cards", "📋", "#8b5cf6")

    # --- 1. THE DATA LOADER WITH FORCE REFRESH ---
    @st.cache_data(ttl=600) # Cache for 10 mins by default
    def get_live_defects():
        try:
            aw_logs = pd.DataFrame(spreadsheet.worksheet("daily_screenings_aw").get_all_records())
            sch_logs = pd.DataFrame(spreadsheet.worksheet("daily_screenings_schools").get_all_records())
            return aw_logs, sch_logs
        except:
            return pd.DataFrame(), pd.DataFrame()

    # Manual Sync Button
    if st.button("🔄 Sync with Google Sheets"):
        st.cache_data.clear()
        st.success("Data refreshed! Fetching latest entries...")
        st.rerun()

    aw_logs, sch_logs = get_live_defects()
    all_defects = []

    def is_real_defect(val):
        """Returns True if the value looks like a defect or malnutrition."""
        v = str(val).strip().lower()
        # It's a defect if it's NOT empty, NOT normal, and NOT "none"
        return v not in ['', 'nan', 'none', 'no', 'null', 'na', 'false', 'normal', '-']

    # Process logs (Universal Scanner)
    for df_type, df in [("Anganwadi", aw_logs), ("School", sch_logs)]:
        if not df.empty:
            # Clean up the column names just in case they have hidden spaces
            df.columns = [str(c).strip() for c in df.columns]
            
            for _, row in df.iterrows():
                # 1. SMART DISEASE DETECTION
                d_val = str(row.get('Disease', row.get('Diseases', row.get('4d', '')))).strip()
                s_val = str(row.get('Status', '')).strip()
                
                if is_real_defect(s_val) or is_real_defect(d_val):
                    condition_parts = []
                    if is_real_defect(s_val): condition_parts.append(s_val)
                    if is_real_defect(d_val): condition_parts.append(d_val)
                    
                    # 2. UNIVERSAL COLUMN PICKER (Looks for Name/Inst anywhere in the first few columns)
                    def get_val(search_terms, fallback="Unknown"):
                        for col in df.columns:
                            if any(term in col.lower() for term in search_terms):
                                return str(row[col])
                        return fallback

                    name = get_val(['name', 'beneficiary', 'student'])
                    inst = get_val(['inst', 'school', 'awc'])
                    date = get_val(['date', 'screening'])
                    
                    all_defects.append({
                        "Date": date,
                        "Name": name,
                        "Institution": inst,
                        "Condition": " + ".join(condition_parts),
                        "Gender": get_val(['gender', 'sex'], "N/A"),
                        "DOB": get_val(['dob', 'birth'], "N/A"),
                        "Father": get_val(['father', 'parent', 'mother'], "N/A"),
                        "Techo": get_val(['techo', 'id', 'contact'], "N/A"),
                        "Type": df_type
                    })
    tab_reg, tab_card = st.tabs(["🌍 Live Defect Registry", "🪪 Refer Card Generator"])

    with tab_reg:
        if all_defects:
            st.success(f"Found {len(all_defects)} children requiring follow-up.")
            st.dataframe(pd.DataFrame(all_defects)[['Date', 'Name', 'Institution', 'Condition']], use_container_width=True, hide_index=True)
        else:
            st.info("Registry empty. Start screening in Module 2!")

    with tab_card:
        if all_defects:
            names = [d['Name'] for d in all_defects]
            sel = st.selectbox("Select Child for Refer Card:", ["-- Select --"] + names)
            
            if sel != "-- Select --":
                p_data = next(item for item in all_defects if item["Name"] == sel)
                
                with st.form("refer_card_print_form"):
                    p_data['Mother'] = st.text_input("Mother's Name")
                    p_data['Address'] = st.text_input("Address", value=p_data['Institution'])
                    p_data['Date'] = st.date_input("Referral Date")
                    prepare_pdf = st.form_submit_button("Prepare PDF for Printing")
                
                if prepare_pdf:
                    # 1. Generate the PDF
                    pdf_output = generate_refer_card(p_data)
                    
                    # 2. Convert to raw bytes specifically for Streamlit
                    pdf_bytes = bytes(pdf_output)
                    
                    st.success(f"✅ PDF Prepared for {sel}!")
                    
                    # 3. The Button
                    st.download_button(
                        label="⬇️ Download Official Refer Card", 
                        data=pdf_bytes, 
                        file_name=f"Refer_{sel}.pdf", 
                        mime="application/pdf"
                    )
        else:
            st.warning("No children found in registry to generate a card.")

# ==========================================
# MODULE 4: THE LIVING DASHBOARD (NEW!)
# ==========================================
elif menu == "4. Visual Analysis":
    render_header("Visual Analytics", "Geographical mapping and health trends", "🗺️", "#f97316")
    st.write("Living, breathing visual analytics of your entire RBSK program.")

    # Helper function for defect checking
    def has_defect(val):
        clean_val = str(val).strip().lower()
        return clean_val not in ['', 'nan', 'none', 'no', 'null', 'na', 'false']

    tab_funnel, tab_treemap, tab_velocity, tab_pyramid = st.tabs([
        "🎯 Coverage Funnel", "🗺️ Hotspot Treemap", "⏱️ Screening Velocity", "⚖️ Demographic Pyramid"
    ])

    # --- TAB 1: THE ROI FUNNEL ---
    with tab_funnel:
        st.subheader("RBSK Program Funnel")
        st.write("Tracking the pipeline from total enrollment to successful surgical treatment.")
        
        # Calculate numbers dynamically
        target_pop = len(df_aw_master) + len(df_all_students)
        
        aw_4d_col = next((col for col in df_aw_master.columns if col.lower() == '4d'), None)
        sch_4d_col = next((col for col in df_all_students.columns if col.lower() == '4d'), None)
        sch_dis_col = next((col for col in df_all_students.columns if col.lower() == 'disabilityname'), None)
        
        identified_4d = 0
        if aw_4d_col and not df_aw_master.empty:
            identified_4d += len(df_aw_master[df_aw_master[aw_4d_col].apply(has_defect)])
        if not df_all_students.empty:
            sch_mask = pd.Series(False, index=df_all_students.index)
            if sch_4d_col: sch_mask = sch_mask | df_all_students[sch_4d_col].apply(has_defect)
            if sch_dis_col: sch_mask = sch_mask | df_all_students[sch_dis_col].apply(has_defect)
            identified_4d += len(df_all_students[sch_mask])
            
        treated_cases = len(df_4d) if not df_4d.empty else 0
        
        funnel_data = dict(
            Stage=["1. Target Population", "2. Identified 4D Cases", "3. Successfully Treated"],
            Count=[target_pop, identified_4d, treated_cases]
        )
        
        # 
        fig_funnel = px.funnel(funnel_data, x='Count', y='Stage', color='Stage',
                               color_discrete_sequence=['#1f77b4', '#ff7f0e', '#2ca02c'])
        st.plotly_chart(fig_funnel, use_container_width=True)


    # --- TAB 2: HEALTH HOTSPOT TREEMAP ---
    with tab_treemap:
        st.subheader("Anemia Hotspots by Region")
        st.write("Click on a PHC block to zoom into specific high-risk villages.")
        
        if not df_anemia.empty:
            tree_df = df_anemia.copy()
            # Clean columns for the map
            tree_df = tree_df.dropna(subset=['PHC/CHC/UPHC', 'VILLAGE', 'SEVERITY'])
            tree_df = tree_df[tree_df['PHC/CHC/UPHC'].astype(str).str.strip() != 'nan']
            tree_df['District'] = "Main District" # Root node
            
            # 
            fig_tree = px.treemap(
                tree_df, 
                path=['District', 'PHC/CHC/UPHC', 'VILLAGE', 'SEVERITY'],
                color='SEVERITY',
                color_discrete_map={
                    'Normal': '#2ca02c', 'Mild': '#fdb863', 
                    'Moderate': '#e66101', 'Severe': '#b2182b', 'nan': '#808080'
                }
            )
            fig_tree.update_traces(root_color="lightgrey")
            fig_tree.update_layout(margin=dict(t=10, l=10, r=10, b=10))
            st.plotly_chart(fig_tree, use_container_width=True)
        else:
            st.info("Not enough data in the ANEMIA sheet to build the Hotspot Treemap.")


    # --- TAB 3: SCREENING VELOCITY ---
    with tab_velocity:
        st.subheader("Screening Velocity (The District Pulse)")
        st.write("Tracking your team's momentum and daily medical camp output.")
        
        if not df_anemia.empty and 'CAMP DATE' in df_anemia.columns:
            trend_df = df_anemia.copy()
            trend_df['CAMP DATE'] = pd.to_datetime(trend_df['CAMP DATE'], errors='coerce')
            trend_df = trend_df.dropna(subset=['CAMP DATE'])
            
            # Count how many kids were screened on each date
            daily_counts = trend_df.groupby('CAMP DATE').size().reset_index(name='Children Screened')
            daily_counts = daily_counts.sort_values('CAMP DATE')
            
            fig_line = px.line(daily_counts, x='CAMP DATE', y='Children Screened', markers=True,
                               title="Daily Anemia Screenings Over Time")
            fig_line.update_traces(line_color='#d62728', line_width=3)
            st.plotly_chart(fig_line, use_container_width=True)
        else:
            st.info("Need more 'CAMP DATE' data in the ANEMIA sheet to calculate velocity.")


    # --- TAB 4: DEMOGRAPHIC PYRAMID ---
    with tab_pyramid:
        st.subheader("Demographic Disease Pyramid")
        st.write("Analyzing Nutritional Status (Stunting/Wasting) by Gender in Anganwadis.")
        
        if not df_aw_master.empty and 'Gender' in df_aw_master.columns:
            pyr_df = df_aw_master.copy()
            
            # Create a simple "Age Group" proxy based on Beneficiary Type
            if 'Beneficiary Type' in pyr_df.columns:
                pyr_df['Category'] = pyr_df['Beneficiary Type']
            else:
                pyr_df['Category'] = "General Enrollment"
                
            # Filter down to children with nutritional risks
            risk_df = pyr_df[
                (pyr_df['Stunting'].astype(str).str.lower() != 'normal') | 
                (pyr_df['Wasting'].astype(str).str.lower() != 'normal')
            ]
            
            if not risk_df.empty:
                # Group by Category and Gender
                pyramid_data = risk_df.groupby(['Category', 'Gender']).size().reset_index(name='Count')
                
                # Make Male numbers negative so they draw on the left side of the pyramid!
                def adjust_count(row):
                    if str(row['Gender']).upper().startswith('M'): return -row['Count']
                    return row['Count']
                    
                pyramid_data['Pyramid_Count'] = pyramid_data.apply(adjust_count, axis=1)
                
                # 



                fig_pyr = px.bar(pyramid_data, y='Category', x='Pyramid_Count', color='Gender', 
                                 orientation='h', title="Children with Nutritional Risks (Boys vs Girls)",
                                 color_discrete_map={'M': '#1f77b4', 'F': '#e377c2', 'Male': '#1f77b4', 'Female': '#e377c2'})
                
                fig_pyr.update_layout(barmode='relative', xaxis_title="Count (Boys Left | Girls Right)")
                st.plotly_chart(fig_pyr, use_container_width=True)
            else:
                st.success("No widespread nutritional risks identified to build the pyramid!")
        else:
            st.info("Missing 'Gender' column in Anganwadi data.")


# ... [Modules 5 through 10 remain exactly the same as before] ...

# ==========================================
# MODULE 5: HBNC NEWBORN VISIT
# ==========================================
elif menu == "5. HBNC Newborn Visit":
    render_header("Record HBNC visits", "Record HBNC and Delivery point visits easily", "📝", "#14b8a6")
    with st.form("hbnc_form"):
        st.markdown("#### 👶 Details")
        c1, c2, c3 = st.columns(3)
        with c1: visit_date = st.date_input("Date of Visit")
        with c2: child_name = st.text_input("Child's Name")
        with c3: techo_id = st.text_input("Techo ID")
            
        c4, c5 = st.columns(2)
        with c4: parent_name = st.text_input("Parent's Name")
        with c5: contact_number = st.text_input("Contact Number")

        st.divider()
        st.markdown("#### 🏥 Birth History")
        b1, b2, b3, b4 = st.columns(4)
        with b1: dob = st.date_input("Date of Birth")
        with b2: birth_weight = st.number_input("Birth Weight (kg)", min_value=0.0, step=0.1)
        with b3: delivery_type = st.selectbox("Delivery Type", ["Normal Delivery (ND)", "C-Section (LSCS)", "Instrumental"])
        with b4: delivery_point = st.selectbox("Delivery Point", ["Vatsalya Hospital", "SDH Visavadar", "Jay Ambe Hospital", "CHC/PHC", "Home Delivery", "Other Private Hospital"])

        st.divider()
        disease = st.text_input("🦠 Disease / Defect Identified?", placeholder="e.g., Cleft lip, None")
        observations = st.text_area("📝 Clinical Observations", height=100)

        if st.form_submit_button("💾 Save HBNC Record"):
            if child_name == "" or parent_name == "":
                st.error("🚨 Enter Child and Parent Name.")
            else:
                try:
                    spreadsheet.worksheet("hbnc_screenings").append_row([str(visit_date), child_name, parent_name, contact_number, str(dob), birth_weight, delivery_type, delivery_point, techo_id, disease, observations])
                    st.success(f"✅ Recorded Visit for {child_name}.")
                except Exception as e:
                    st.error(f"⚠️ Error: Could not find 'hbnc_screenings' tab. {e}")

# ==========================================
# MODULE 6: SUCCESS STORY BUILDER
# ==========================================
elif menu == "6. Success Story Builder":
    render_header("Success Story Builder", "Create success stories instantly", "🏥", "#e11d48")
    if not df_4d.empty:
        df_4d.columns = df_4d.columns.astype(str).str.strip().str.upper()
        if 'NAME' in df_4d.columns and '4D' in df_4d.columns and 'VILLAGE' in df_4d.columns:
            df_4d['Select_Label'] = df_4d['NAME'].astype(str) + " (" + df_4d['4D'].astype(str) + ") - " + df_4d['VILLAGE'].astype(str)
            selected_label = st.selectbox("Select Treated Child from 4D Registry:", ["-- Select --"] + df_4d['Select_Label'].tolist())
            
            if selected_label != "-- Select --":
                child_data = df_4d[df_4d['Select_Label'] == selected_label].iloc[0]
                with st.form("success_story_form"):
                    st.subheader("📝 Treatment Summary")
                    col1, col2 = st.columns(2)
                    with col1:
                        treatment_place = st.text_input("Treatment Center")
                        surgery_date = st.date_input("Date of Treatment")
                    with col2:
                        doctor_notes = st.text_area("Doctor's Narrative", height=100)
                    
                    st.subheader("📸 Upload Photos")
                    col3, col4 = st.columns(2)
                    with col3: img_before = st.file_uploader("Upload 'Before' Photo", type=["jpg", "jpeg", "png"])
                    with col4: img_after = st.file_uploader("Upload 'After' Photo", type=["jpg", "jpeg", "png"])
                    
                    if st.form_submit_button("📄 Prepare Official PDF Report"):
                        if treatment_place == "" or doctor_notes == "":
                            st.error("🚨 Fill in Treatment Center and Narrative.")
                        else:
                            with st.spinner("Generating PDF..."):
                                pdf = FPDF()
                                pdf.add_page()
                                pdf.set_auto_page_break(auto=True, margin=15)
                                pdf.set_font("Arial", "B", 16)
                                pdf.cell(200, 10, txt="RBSK SUCCESS STORY REPORT", ln=True, align='C')
                                pdf.ln(10)
                                pdf.set_font("Arial", "B", 12)
                                pdf.cell(200, 10, txt="PATIENT DETAILS", ln=True, align='L')
                                pdf.set_font("Arial", "", 12)
                                pdf.cell(200, 8, txt=f"Name: {child_data['NAME']}", ln=True)
                                pdf.cell(200, 8, txt=f"Village: {child_data['VILLAGE']}", ln=True)
                                pdf.cell(200, 8, txt=f"Identified Defect: {child_data['4D']}", ln=True)
                                mob = child_data.get('MOBILE NO', child_data.get('MOBILE', 'N/A'))
                                pdf.cell(200, 8, txt=f"Mobile Number: {mob}", ln=True)
                                pdf.ln(5)
                                pdf.set_font("Arial", "B", 12)
                                pdf.cell(200, 10, txt="TREATMENT SUMMARY", ln=True, align='L')
                                pdf.set_font("Arial", "", 12)
                                pdf.cell(200, 8, txt=f"Treated At: {treatment_place}", ln=True)
                                pdf.cell(200, 8, txt=f"Treatment Date: {surgery_date}", ln=True)
                                pdf.multi_cell(0, 8, txt=f"Doctor's Narrative:\n{doctor_notes}")
                                pdf.ln(10)
                                
                                if img_before or img_after:
                                    pdf.set_font("Arial", "B", 12)
                                    pdf.cell(200, 10, txt="CLINICAL PHOTOGRAPHS", ln=True, align='L')
                                    if img_before:
                                        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_b:
                                            tmp_b.write(img_before.read())
                                            tmp_b_name = tmp_b.name
                                        pdf.image(tmp_b_name, x=20, w=70)
                                        os.remove(tmp_b_name) 
                                    if img_after:
                                        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_a:
                                            tmp_a.write(img_after.read())
                                            tmp_a_name = tmp_a.name
                                        pdf.image(tmp_a_name, x=110, w=70) 
                                        os.remove(tmp_a_name) 
                                
                                pdf_output = pdf.output(dest="S").encode("latin-1")
                                st.success("✅ PDF Generated Successfully!")
                                st.download_button(label="⬇️ Download PDF Report", data=pdf_output, file_name=f"Success_Story_{child_data['NAME']}.pdf", mime="application/pdf")
        else:
            st.error("⚠️ Headers in 4d_list must be 'NAME', 'VILLAGE', and '4D'.")
    else:
        st.warning("No 4D Defect records found.")

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
    st.write("Instantly look up Anganwadi Workers and their contact numbers.")

    if not df_aw_contacts.empty:
        awc_col = df_aw_contacts.columns[0] 
        for col in df_aw_contacts.columns:
            if 'AWC' in col.upper() or 'NAME' in col.upper():
                awc_col = col
                break
                
        awc_options = sorted([str(x) for x in df_aw_contacts[awc_col].unique() if str(x) != 'nan' and str(x).strip() != ''])
        selected_awc = st.selectbox("Select an Anganwadi Center:", ["-- Select Center --"] + awc_options)
        
        if selected_awc != "-- Select Center --":
            contact_info = df_aw_contacts[df_aw_contacts[awc_col] == selected_awc].iloc[0]
            
            st.divider()
            st.subheader(f"🏠 {selected_awc}")
            
            for col in df_aw_contacts.columns:
                if col != awc_col:  
                    val = str(contact_info[col]).strip()
                    if val not in ['', 'nan', 'None']:
                        st.success(f"**{col}:** {val}")
                        
    else:
        st.error("⚠️ Could not load data from the 'aw_master_directory' tab. Please ensure the tab is spelled exactly right in your Google Sheet.")

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
# MODULE 11: ANNUAL FY PLANNER (2026-2027)
# ==========================================
elif menu == "11. Annual FY Planner":
    render_header("Roadmap of whole year in advance!", "Plan your work together!", "🏥", "#e11d48")
    st.write("Annual roadmap, campaign timelines, and real-time workload calculations.")

    tab_timeline, tab_calculator, tab_monthly = st.tabs([
        "📊 Interactive Master Timeline", "🧮 Workload & Resource Calculator", "📋 Monthly Target Focus"
    ])

    # --- TAB 1: GANTT CHART TIMELINE ---
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


    # --- TAB 2: TRUE CALENDAR WORKLOAD CALCULATOR ---
    with tab_calculator:
        st.subheader("⚙️ Target Feasibility Calculator")
        st.write("Calculates exact working days available in FY 2026-27 and compares it to your caseload.")
        
        if not df_aw_master.empty and not df_all_students.empty:
            total_awc_kids = len(df_aw_master)
            total_school_kids = len(df_all_students)
            total_screenings_target = (total_awc_kids * 2) + total_school_kids
            
            # --- TRUE CALENDAR MATH (Apr 1, 2026 - Mar 31, 2027) ---
            fy_dates = pd.date_range(start="2026-04-01", end="2027-03-31")
            total_days_in_fy = len(fy_dates) # 365
            sundays = (fy_dates.weekday == 6).sum() # 52
            saturdays = (fy_dates.weekday == 5).sum() # 52
            
            st.markdown("### 1. Available Time (FY 26-27)")
            c1, c2, c3 = st.columns(3)
            public_holidays = c1.number_input("Public Holidays (Weekdays)", min_value=0, max_value=40, value=18)
            
            # 52 half-Saturdays equals exactly 26 full working days lost.
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
                active_teams = 1 # Hardcoded strictly to your single 4-person team
            
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


    # --- TAB 3: MONTHLY BREAKDOWN ---
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

    @st.cache_data(ttl=60)
    def load_daily_screenings():
        try:
            aw = pd.DataFrame(spreadsheet.worksheet("daily_screenings_aw").get_all_records())
            sch = pd.DataFrame(spreadsheet.worksheet("daily_screenings_schools").get_all_records())
            return aw, sch
        except Exception as e:
            st.error(f"Could not load daily screenings. Ensure tabs 'daily_screenings_aw' and 'daily_screenings_schools' exist. {e}")
            return pd.DataFrame(), pd.DataFrame()

    df_aw_daily, df_sch_daily = load_daily_screenings()
    df_combined = pd.DataFrame()

    if not df_aw_daily.empty or not df_sch_daily.empty:
        if not df_aw_daily.empty: df_aw_daily['Source'] = 'Anganwadi'
        if not df_sch_daily.empty: df_sch_daily['Source'] = 'School'
        
        df_combined = pd.concat([df_aw_daily, df_sch_daily], ignore_index=True)
        
        def find_col(df, keywords):
            for col in df.columns:
                if any(k.lower() in col.lower() for k in keywords): return col
            return None

        date_col = find_col(df_combined, ['date of screening', 'screening date', 'date'])
        dob_col = find_col(df_combined, ['dob', 'date of birth'])
        gender_col = find_col(df_combined, ['gender', 'sex'])
        disease_col = find_col(df_combined, ['disease', '4d', 'defect'])
        status_col = find_col(df_combined, ['status', 'sam', 'mam'])
        name_col = find_col(df_combined, ['name', 'child', 'student', 'beneficiary'])
        inst_col = find_col(df_combined, ['inst', 'school', 'awc', 'center'])

        if date_col and dob_col:
            df_combined[date_col] = pd.to_datetime(df_combined[date_col], errors='coerce')
            df_combined[dob_col] = pd.to_datetime(df_combined[dob_col], errors='coerce')
            df_combined = df_combined.dropna(subset=[date_col])
            df_combined['Month_Year'] = df_combined[date_col].dt.strftime('%B %Y')

    # --- TAB 1: FORM III EXPORT (IRONED OUT) ---
    with tab_form3:
        if not df_combined.empty and date_col and dob_col:
            available_months = df_combined['Month_Year'].dropna().unique().tolist()
            if not available_months:
                st.warning("No valid dates found in the screening logs.")
            else:
                c1, c2 = st.columns(2)
                selected_month = c1.selectbox("📅 Select Reporting Month:", available_months)
                
                report_df = df_combined[df_combined['Month_Year'] == selected_month].copy()
                
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

                st.divider()
                st.markdown(f"### 📊 Official Form III Output: **{selected_month}**")
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

                st.divider()
                st.markdown("### 🚨 Disease & Malnutrition Referrals (Current Month)")
                
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
                export_df['Institution'] = report_df[inst_col] if inst_col else "Unknown"
                export_df['Child Name'] = report_df[name_col] if name_col else "Unknown"
                export_df['DOB'] = report_df[dob_col].dt.strftime('%d-%m-%Y')
                export_df['Calculated Age (Yrs)'] = report_df['Age_Years'].round(2)
                export_df['Govt Age Bucket'] = report_df['Govt_Age_Bucket']
                export_df['Gender'] = report_df['Clean_Gender']
                
                if status_col: export_df['Nutrition (SAM/MAM)'] = report_df[status_col]
                if disease_col: export_df['4D Condition Found'] = report_df[disease_col]

                with st.expander("👁️ Preview Streamlined CSV Data"):
                    st.dataframe(export_df, use_container_width=True, hide_index=True)

                csv = export_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="⬇️ Download Streamlined Monthly Data (CSV)",
                    data=csv,
                    file_name=f"RBSK_MPR_Cleaned_{selected_month}.csv",
                    mime="text/csv",
                )
        else:
            st.info("No valid daily screening data found yet to generate Form III. Start screening in Module 2!")

    # --- TAB 2: LIVE SCOREBOARD (DR. NIHAR) ---
    with tab_scoreboard:
        st.subheader("🏆 Live Performance Scoreboard")
        st.markdown("**Team:** Dr. Nihar (MHT-1240315) | **Block:** Visavadar")
        
        # Hardcoded Target for Dr. Nihar based on TEAMIDVISE.csv
        annual_target = 12794
        
        if not df_combined.empty:
            total_achieved = len(df_combined)
            
            # Calculate Percentage
            achievement_pct = (total_achieved / annual_target) * 100
            
            # Prevent progress bar from breaking if you somehow go over 100%
            progress_bar_val = min(achievement_pct / 100.0, 1.0)
            
            st.markdown("### 📈 FY Cumulative Progress")
            
            # The big metrics
            s1, s2, s3 = st.columns(3)
            s1.metric("Annual Target", f"{annual_target:,}")
            s2.metric("Total Achieved", f"{total_achieved:,}", delta="Children Screened")
            s3.metric("Achievement %", f"{achievement_pct:.2f}%")
            
            # The Visual Progress Bar
            st.progress(progress_bar_val)
            
            st.divider()
            
            # Quick breakdown of WHERE the screenings happened
            st.markdown("### 🏢 Screening Breakdown by Source")
            source_counts = df_combined['Source'].value_counts().reset_index()
            source_counts.columns = ['Location Type', 'Children Screened']
            st.dataframe(source_counts, use_container_width=True, hide_index=True)
            
        else:
            st.info("No screening data logged yet. Your scoreboard will update as soon as you save your first screening!")

































