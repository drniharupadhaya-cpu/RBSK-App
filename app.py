import streamlit as st
import pandas as pd
import gspread
import json
from fpdf import FPDF
import tempfile
import os

# --- 1. GET THE LIVE DATABASE CONNECTION ---
def get_spreadsheet():
    creds_dict = json.loads(st.secrets["gcp_service_account"])
    client = gspread.service_account_from_dict(creds_dict)
    sheet_url = "https://docs.google.com/spreadsheets/d/1i5wAkI7k98E80qhHRe6xQOhF4Qj9Z0DH8wjPsQ7gRZc/edit?gid=2111634358#gid=2111634358"
    return client.open_by_url(sheet_url)

import time # <-- Make sure this is at the very top of your file with the other imports!

# --- 2. GET THE PURE DATA (WITH SMART AUTO-RETRY) ---
@st.cache_data(ttl=600)
def load_all_data():
    sheet = get_spreadsheet()
    
    # SMART LOADER: If Google yells "Slow down!" (Error 429), it waits and tries again!
    def safe_load(tab_name, retries=3):
        for attempt in range(retries):
            try:
                df = pd.DataFrame(sheet.worksheet(tab_name).get_all_records()).astype(str)
                df.columns = df.columns.str.strip() # Destroys hidden spaces
                return df
            except Exception as e:
                error_msg = str(e)
                if '429' in error_msg or 'RESOURCE_EXHAUSTED' in error_msg:
                    if attempt < retries - 1:
                        # Wait 10 seconds and try again
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
        "10. Staff Directory"
    ]
)

# ... [Modules 1 and 2 remain exactly the same as before] ...
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
# MODULE 3: 4D DEFECT COMMAND CENTER (BULLETPROOF FIX)
# ==========================================
elif menu == "3. 4D Defect Registry":
    st.title("🔍 4D Defect Command Center")
    st.write("Live filtering for high-risk regions, schools, and Anganwadis.")

    def has_defect(val):
        clean_val = str(val).strip().lower()
        return clean_val not in ['', 'nan', 'none', 'no', 'null', 'na', 'false']

    if not df_aw_master.empty and not df_all_students.empty:
        
        # --- DYNAMIC COLUMN HUNTER ---
        # Instead of hardcoding '4d', this automatically finds the column whether it's '4d', '4D', or '4d '
        sch_4d_col = next((col for col in df_all_students.columns if col.lower() == '4d'), None)
        sch_dis_col = next((col for col in df_all_students.columns if col.lower() == 'disabilityname'), None)
        aw_4d_col = next((col for col in df_aw_master.columns if col.lower() == '4d'), None)

        tab_loc, tab_inst = st.tabs(["🌍 Search by Village / Sector", "🏫 Search by Specific Institution"])
        
        with tab_loc:
            aw_locs = df_aw_master['Sector Name'].unique().tolist()
            sch_locs = df_all_students['Village'].unique().tolist()
            all_locs = sorted(list(set([str(x).strip() for x in aw_locs + sch_locs if str(x).strip() not in ['nan', '']])))
            
            selected_loc = st.selectbox("Select a Village or Sector:", ["-- Select --"] + all_locs)
            
            if selected_loc != "-- Select --":
                aw_loc_df = df_aw_master[df_aw_master['Sector Name'].astype(str).str.strip() == selected_loc]
                sch_loc_df = df_all_students[df_all_students['Village'].astype(str).str.strip() == selected_loc]
                
                # Check Anganwadi defects safely
                aw_defects = pd.DataFrame()
                if aw_4d_col:
                    aw_defects = aw_loc_df[aw_loc_df[aw_4d_col].apply(has_defect)]
                
                # Check School defects safely
                sch_mask = pd.Series(False, index=sch_loc_df.index)
                if sch_4d_col:
                    sch_mask = sch_mask | sch_loc_df[sch_4d_col].apply(has_defect)
                if sch_dis_col:
                    sch_mask = sch_mask | sch_loc_df[sch_dis_col].apply(has_defect)
                    
                sch_defects = sch_loc_df[sch_mask]
                
                st.markdown(f"### 📊 Health Overview: {selected_loc}")
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("👶 Total AWC Kids", len(aw_loc_df))
                c2.metric("🏫 Total School Kids", len(sch_loc_df))
                c3.metric("🚨 AWC 4D Cases", len(aw_defects))
                c4.metric("🚨 School 4D Cases", len(sch_defects))
                
                st.divider()
                st.markdown("### 📋 Identified 4D Patients")
                
                if not aw_defects.empty:
                    st.write("👶 **Anganwadi Cases**")
                    aw_display = aw_defects[['AWC Name', 'Beneficiary Name', aw_4d_col]].rename(
                        columns={'AWC Name': 'Institution', 'Beneficiary Name': 'Child Name', aw_4d_col: 'Recorded Defect'}
                    )
                    st.dataframe(aw_display, use_container_width=True, hide_index=True)
                else:
                    st.info("👶 No 4D conditions recorded in the Anganwadis for this location.")
                    
                if not sch_defects.empty:
                    st.write("🏫 **School Cases**")
                    
                    def combine_sch_defects(row):
                        d1 = str(row.get(sch_4d_col, '')).strip() if sch_4d_col else ''
                        d2 = str(row.get(sch_dis_col, '')).strip() if sch_dis_col else ''
                        if has_defect(d1) and has_defect(d2) and d1 != d2: return f"{d1} | {d2}"
                        if has_defect(d1): return d1
                        if has_defect(d2): return d2
                        return "Unknown"
                        
                    sch_display = sch_defects[['School', 'StudentName']].copy()
                    sch_display['Recorded Defect'] = sch_defects.apply(combine_sch_defects, axis=1)
                    sch_display = sch_display.rename(columns={'School': 'Institution', 'StudentName': 'Child Name'})
                    st.dataframe(sch_display, use_container_width=True, hide_index=True)
                else:
                    st.info("🏫 No 4D conditions recorded in the Schools for this location.")

        with tab_inst:
            aw_insts = df_aw_master['AWC Name'].unique().tolist()
            sch_insts = df_all_students['School'].unique().tolist()
            all_insts = sorted(list(set([str(x).strip() for x in aw_insts + sch_insts if str(x).strip() not in ['nan', '']])))
            
            selected_inst = st.selectbox("Search for a specific School or AWC:", ["-- Select --"] + all_insts)
            
            if selected_inst != "-- Select --":
                is_aw = selected_inst in aw_insts
                
                if is_aw:
                    inst_df = df_aw_master[df_aw_master['AWC Name'].astype(str).str.strip() == selected_inst]
                    defects_df = pd.DataFrame()
                    if aw_4d_col:
                        defects_df = inst_df[inst_df[aw_4d_col].apply(has_defect)]
                    
                    st.markdown(f"### 📊 Data for: {selected_inst}")
                    m1, m2 = st.columns(2)
                    m1.metric("Total Enrolled Children", len(inst_df))
                    m2.metric("Identified 4D Cases", len(defects_df))
                    
                    if not defects_df.empty:
                        st.write("**📋 Patient List**")
                        display_df = defects_df[['Beneficiary Name', aw_4d_col]].rename(columns={'Beneficiary Name': 'Child Name', aw_4d_col: 'Recorded Defect'})
                        st.dataframe(display_df, use_container_width=True, hide_index=True)
                    else:
                        st.success("✅ No 4D cases recorded in this institution!")
                        
                else:
                    inst_df = df_all_students[df_all_students['School'].astype(str).str.strip() == selected_inst]
                    
                    sch_mask = pd.Series(False, index=inst_df.index)
                    if sch_4d_col:
                        sch_mask = sch_mask | inst_df[sch_4d_col].apply(has_defect)
                    if sch_dis_col:
                        sch_mask = sch_mask | inst_df[sch_dis_col].apply(has_defect)
                        
                    defects_df = inst_df[sch_mask]
                    
                    st.markdown(f"### 📊 Data for: {selected_inst}")
                    m1, m2 = st.columns(2)
                    m1.metric("Total Enrolled Students", len(inst_df))
                    m2.metric("Identified 4D Cases", len(defects_df))
                    
                    if not defects_df.empty:
                        st.write("**📋 Patient List**")
                        
                        display_df = defects_df[['StudentName']].copy()
                        display_df['Recorded Defect'] = defects_df.apply(
                            lambda r: f"{r.get(sch_4d_col,'')} | {r.get(sch_dis_col,'')}".strip(' |'), axis=1
                        )
                        display_df = display_df.rename(columns={'StudentName': 'Child Name'})
                        st.dataframe(display_df, use_container_width=True, hide_index=True)
                    else:
                        st.success("✅ No 4D cases recorded in this institution!")
    else:
        st.warning("⚠️ Could not load data from 'aw new data' or '1240315 ALL STUDENTS NAMES'. Please check your sheet names.")

# ... [Modules 4 through 10 remain exactly the same as before] ...

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
# MODULE 7: ANEMIA TRACKER
# ==========================================
elif menu == "7. Anemia Tracker":
    st.title("🩸 Anemia Camp & Analytics Dashboard")
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
    st.title("🏫 Digital School Directory")
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
    st.title("👶 Anganwadi Contact Directory")
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
    st.title("👨‍⚕️ Master Staff Directory")
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

