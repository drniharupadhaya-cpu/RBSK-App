import streamlit as st
import pandas as pd
import gspread
import json
from fpdf import FPDF
import tempfile
import os

# --- 1. GET THE LIVE DATABASE CONNECTION (DO NOT CACHE THIS!) ---
def get_spreadsheet():
    creds_dict = json.loads(st.secrets["gcp_service_account"])
    client = gspread.service_account_from_dict(creds_dict)
    sheet_url = "https://docs.google.com/spreadsheets/d/1i5wAkI7k98E80qhHRe6xQOhF4Qj9Z0DH8wjPsQ7gRZc/edit?gid=2111634358#gid=2111634358"
    return client.open_by_url(sheet_url)

# --- 2. GET THE PURE DATA (CACHE THIS FOR SPEED) ---
@st.cache_data(ttl=60)
def load_all_data():
    sheet = get_spreadsheet()
    
    df_4d = pd.DataFrame(sheet.worksheet("4d_list").get_all_records()).astype(str)
    df_schools = pd.DataFrame(sheet.worksheet("school_details").get_all_records()).astype(str)
    df_aw = pd.DataFrame(sheet.worksheet("aw_data").get_all_records()).astype(str)
    
    try:
        df_anemia = pd.DataFrame(sheet.worksheet("ANEMIA").get_all_records()).astype(str)
    except:
        df_anemia = pd.DataFrame()
    
    try:
        df_students = pd.DataFrame(sheet.worksheet("students_data").get_all_records()).astype(str)
    except:
        df_students = pd.DataFrame() 

    # --- NEW: LOAD SCHOOL DIRECTORY DATA ---
    try:
        df_directory = pd.DataFrame(sheet.worksheet("ALL SCHOOL DETAILS").get_all_records()).astype(str)
    except:
        df_directory = pd.DataFrame()
        
    return df_4d, df_schools, df_aw, df_students, df_anemia, df_directory

# --- 3. ACTIVATE BOTH ---
try:
    spreadsheet = get_spreadsheet() 
    df_4d, df_schools, df_aw, df_students, df_anemia, df_directory = load_all_data() 
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
        "8. School Directory"  # <-- NEW MENU ITEM!
        "9. Anganwadi Directory"
    ]
)

# ==========================================
# MODULE 1: DAILY TOUR PLANNER
# ==========================================
if menu == "1. Daily Tour Plan":
    st.title("📅 Official Advance Tour Planner")
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
# MODULE 2: EMR SCREENING WITH HISTORY
# ==========================================
elif menu == "2. Child Screening":
    st.title("📝 EMR Screening Form")
    st.write("View historical data and enter new vitals.")

    category = st.radio("Select Visit Type:", ["🏫 Schools", "👶 Anganwadi"], horizontal=True)
    st.divider()

    if category == "👶 Anganwadi":
        if not df_aw.empty:
            institute_list = df_aw['AWC Name'].dropna().unique().tolist()
            selected_inst = st.selectbox("Select Anganwadi Center:", ["-- Select --"] + institute_list)
            if selected_inst != "-- Select --":
                filtered_children = df_aw[df_aw['AWC Name'] == selected_inst]
                child_names = filtered_children['Beneficiary Name'].tolist()
        else:
            st.error("No Anganwadi data found.")
            selected_inst = "-- Select --"
            
    else: 
        if not df_students.empty:
            institute_list = df_students['School'].dropna().unique().tolist()
            selected_inst = st.selectbox("Select School:", ["-- Select --"] + institute_list)
            if selected_inst != "-- Select --":
                filtered_children = df_students[df_students['School'] == selected_inst]
                child_names = filtered_children['StudentName'].tolist()
        else:
            st.error("No School Student data found.")
            selected_inst = "-- Select --"

    if selected_inst != "-- Select --":
        selected_child = st.selectbox(
            f"Select Child enrolled in {selected_inst}:", 
            ["-- Select Child --", "➕ Register New Child"] + child_names
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
                with c_col1: updated_contact = st.text_input("📞 Contact Number", value=existing_contact)
                with c_col2: techo_id = st.text_input("🆔 Techo ID") if category == "👶 Anganwadi" else "N/A"

                v_col1, v_col2, v_col3, v_col4 = st.columns(4)
                with v_col1: height = st.number_input("Height (cm)", min_value=0.0, step=0.5)
                with v_col2: weight = st.number_input("Weight (kg)", min_value=0.0, step=0.1)
                with v_col3:
                    if category == "👶 Anganwadi":
                        muac = st.number_input("MUAC (cm)", min_value=0.0, step=0.1)
                    else:
                        muac = "N/A"
                        st.text_input("MUAC (cm)", value="Not required", disabled=True)
                with v_col4: hb = st.number_input("Hb %", min_value=0.0, step=0.1)

                disease = st.text_input("🦠 Disease Identified (4D)", placeholder="Type 'None' or describe...")
                save_btn = st.form_submit_button("💾 Save Screening Data")

                if save_btn:
                    if final_child_name == "" or height == 0 or weight == 0:
                        st.error("🚨 Please fill out Name, Height, and Weight.")
                    else:
                        try:
                            if category == "👶 Anganwadi":
                                target_sheet = spreadsheet.worksheet("daily_screenings_aw")
                                target_sheet.append_row([str(screening_date), selected_inst, final_child_name, str(dob), str(gender), height, weight, muac, hb, disease, updated_contact, techo_id])
                            else:
                                target_sheet = spreadsheet.worksheet("daily_screenings_schools")
                                target_sheet.append_row([str(screening_date), selected_inst, final_child_name, str(dob), str(gender), height, weight, hb, disease, updated_contact])
                            
                            st.success(f"✅ Successfully recorded screening for {final_child_name}!")
                        except Exception as e:
                            st.error(f"⚠️ Error saving data: {e}")

# ==========================================
# MODULE 3: 4D DEFECT REGISTRY
# ==========================================
elif menu == "3. 4D Defect Registry":
    st.title("🔍 4D Defect Registry & Search")
    search_term = st.text_input("Search for a child by Name, Village, or Defect:")

    if search_term:
        mask = df_4d.astype(str).apply(lambda x: x.str.contains(search_term, case=False)).any(axis=1)
        st.dataframe(df_4d[mask], use_container_width=True)
    else:
        st.dataframe(df_4d, use_container_width=True)

# ==========================================
# MODULE 4: VISUAL ANALYSIS
# ==========================================
elif menu == "4. Visual Analysis":
    st.title("📊 Interactive Data Analysis")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Total Students by School")
        if not df_schools.empty and 'School' in df_schools.columns and 'TOTAL' in df_schools.columns:
            df_schools['TOTAL'] = pd.to_numeric(df_schools['TOTAL'], errors='coerce').fillna(0)
            st.bar_chart(data=df_schools.sort_values(by='TOTAL', ascending=False).head(10), x='School', y='TOTAL')
    with col2:
        st.subheader("Gender Distribution (Anganwadis)")
        if not df_aw.empty and 'Gender' in df_aw.columns:
            st.bar_chart(df_aw['Gender'].value_counts())

# ==========================================
# MODULE 5: HBNC NEWBORN VISIT
# ==========================================
elif menu == "5. HBNC Newborn Visit":
    st.title("🍼 HBNC Neonatal Visit")
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
    st.title("🌟 Success Story Generator")
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
# MODULE 7: ANEMIA TRACKER (LEVEL 2 UPGRADE!)
# ==========================================
elif menu == "7. Anemia Tracker":
    st.title("🩸 Anemia Camp & Analytics Dashboard")
    st.write("Track Hemoglobin levels and analyze historical trends.")

    tab_dash, tab_entry = st.tabs(["📈 Interactive Dashboard", "➕ Enter New Camp Data"])

    # --- TAB 1: THE LEVEL 2 DASHBOARD ---
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

    # --- TAB 2: THE ENTRY PORTAL ---
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
# MODULE 8: SCHOOL DIRECTORY (NEW!)
# ==========================================
elif menu == "8. School Directory":
    st.title("🏫 Digital School Directory")
    st.write("Instantly look up school demographics, principals, and class sizes.")

    if not df_directory.empty:
        # 1. Build the dropdown menu
        school_options = sorted([str(x) for x in df_directory['School'].unique() if str(x) != 'nan' and str(x).strip() != ''])
        selected_school = st.selectbox("Select a School to view its ID Card:", ["-- Select a School --"] + school_options)
        
        if selected_school != "-- Select a School --":
            # Find the specific school's row
            s_data = df_directory[df_directory['School'] == selected_school].iloc[0]
            
            st.divider()
            
            # 2. Top Information Cards
            st.subheader(f"📍 {selected_school}")
            c1, c2, c3 = st.columns(3)
            c1.info(f"**Type:** {s_data.get('PRIMARY/HIGH SCHOOL', 'N/A')}")
            c2.info(f"**Category:** {s_data.get('GOVT/PRIVATE', 'N/A')}")
            c3.info(f"**PHC:** {s_data.get('PHC', 'N/A')}")
            
            # 3. Contact Info
            st.markdown("### 👨‍🏫 Administrative Contact")
            st.success(f"**Principal:** {s_data.get('PRINCIPAL NAME', 'N/A')} | 📞 **Phone:** {s_data.get('PRINCIPAL CONTACT NUMBER', 'N/A')}")
            
            # 4. Overall Strength
            st.markdown("### 📊 Overall Student Strength")
            m1, m2, m3 = st.columns(3)
            m1.metric("👦 Total Boys", s_data.get('TOTAL BOYS', '0'))
            m2.metric("👧 Total Girls", s_data.get('TOTAL GIRLS', '0'))
            m3.metric("🏫 Grand Total", s_data.get('TOTAL', '0'))
            
            # 5. The Class Breakdown Table
            st.markdown("### 📋 Class-by-Class Breakdown")
            
            # We map your exact Google Sheet prefixes to human-readable names
            class_prefixes = ['BV', 'CLS1', 'CLS2', 'CLS3', 'CLS4', 'CLS5', 'CLS6', 'CLS7', 'CLS8', 'CLS9', 'CLS10', 'CLS11', 'CLS12']
            class_names = ['Bal Vatika', 'Class 1', 'Class 2', 'Class 3', 'Class 4', 'Class 5', 'Class 6', 'Class 7', 'Class 8', 'Class 9', 'Class 10', 'Class 11', 'Class 12']
            
            breakdown_list = []
            
            # Loop through every class prefix and pull the Boys, Girls, Transgender, and Total
            for prefix, readable_name in zip(class_prefixes, class_names):
                total_val = str(s_data.get(f'Total_{prefix}', '0')).strip()
                
                # MAGIC: Only add this class to the table if the Total is greater than 0!
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
        st.error("⚠️ Could not load data from the 'ALL SCHOOL DETAILS' tab. Please ensure the tab is spelled exactly right in your Google Sheet.")
        # ==========================================
# MODULE 9: ANGANWADI DIRECTORY (CONTACTS + DEMOGRAPHICS)
# ==========================================
if menu == "9. Anganwadi Directory":
    st.title("👶 Digital Anganwadi Directory")
    st.write("Look up AWC Worker contacts and student demographics.")

    if not df_aw_contacts.empty:
        # Use AWC Name column from your directory sheet
        awc_options = sorted([str(x) for x in df_aw_contacts['AWC Name'].unique() if str(x) != 'nan' and str(x).strip() != ''])
        selected_awc = st.selectbox("Select an Anganwadi Center:", ["-- Select Center --"] + awc_options)
        
        if selected_awc != "-- Select Center --":
            # 1. Pull Contact Info from aw_master_directory
            contact_info = df_aw_contacts[df_aw_contacts['AWC Name'] == selected_awc].iloc[0]
            
            st.divider()
            st.subheader(f"🏠 {selected_awc}")
            
            c1, c2 = st.columns(2)
            with c1:
                st.success(f"👩‍🏫 **Worker:** {contact_info.get('Worker Name', 'N/A')}")
            with c2:
                st.success(f"📞 **Contact:** {contact_info.get('Worker Contact', 'N/A')}")
            
            # 2. Pull Demographics from aw new data
            if not df_aw_master.empty:
                aw_filtered = df_aw_master[df_aw_master['AWC Name'] == selected_awc]
                
                if not aw_filtered.empty:
                    st.markdown("### 📊 Demographics")
                    m1, m2, m3 = st.columns(3)
                    total_kids = len(aw_filtered)
                    boys = len(aw_filtered[aw_filtered['Gender'].str.upper().str.startswith('M')])
                    girls = len(aw_filtered[aw_filtered['Gender'].str.upper().str.startswith('F')])
                    
                    m1.metric("👶 Total Children", total_kids)
                    m2.metric("👦 Boys", boys)
                    m3.metric("👧 Girls", girls)
                    
                    st.markdown("### 📋 Beneficiary List")
                    display_cols = ['Beneficiary Name', 'Mother Name', 'DoB', 'Gender']
                    st.dataframe(aw_filtered[display_cols], use_container_width=True, hide_index=True)
                else:
                    st.info("No beneficiary data found for this center in 'aw new data'.")
            
            # 3. Quick Info from Directory
            with st.expander("📍 Center Details"):
                st.write(f"**Sector:** {contact_info.get('Sector', 'N/A')}")
                st.write(f"**AWC Code:** {contact_info.get('AWC Code', 'N/A')}")
                st.write(f"**Building Type:** {contact_info.get('Building', 'N/A')}")

    else:
        st.error("⚠️ Could not load 'aw_master_directory'. Check your sheet tab name!")

