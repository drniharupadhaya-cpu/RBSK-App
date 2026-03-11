import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
from fpdf import FPDF
import tempfile
import os

@st.cache_data(ttl=60)
def load_all_data():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = json.loads(st.secrets["gcp_service_account"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    sheet_url = "https://docs.google.com/spreadsheets/d/1i5wAkI7k98E80qhHRe6xQOhF4Qj9Z0DH8wjPsQ7gRZc/edit?gid=2111634358#gid=2111634358"
    spreadsheet = client.open_by_url(sheet_url)
    
    df_4d = pd.DataFrame(spreadsheet.worksheet("4d_list").get_all_records()).astype(str)
    df_schools = pd.DataFrame(spreadsheet.worksheet("school_details").get_all_records()).astype(str)
    df_aw = pd.DataFrame(spreadsheet.worksheet("aw_data").get_all_records()).astype(str)
    
    try:
        df_students = pd.DataFrame(spreadsheet.worksheet("students_data").get_all_records()).astype(str)
    except:
        df_students = pd.DataFrame() 
        
    return df_4d, df_schools, df_aw, df_students, spreadsheet

# Actually load the data into the app!
try:
    df_4d, df_schools, df_aw, df_students, spreadsheet = load_all_data()
except Exception as e:
    st.error(f"Could not connect to Google Sheets. Please check your Secret Vault. Error: {e}")
    st.stop()

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("🩺 RBSK Menu")
st.sidebar.write("Dr. Workspace")
menu = st.sidebar.radio("Go to:", 
    ["1. Daily Tour Plan", "2. Child Screening", "3. 4D Defect Registry", "4. Visual Analysis", "5. HBNC Newborn Visit", "6. Success Story Builder"]
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

    # --- TAB 1: VIEWING THE SCHEDULE ---
    with tab_view:
        st.subheader("Upcoming Medical Tours")
        if not df_plan.empty:
            df_plan['Date'] = pd.to_datetime(df_plan['Date'])
            df_plan = df_plan.sort_values(by='Date')
            df_plan['Date'] = df_plan['Date'].dt.strftime('%Y-%m-%d')
            st.dataframe(df_plan, width='stretch', hide_index=True)
        else:
            st.info("No upcoming tours planned yet.")

    # --- TAB 2: ADDING A NEW VISIT ---
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

    # --- TAB 3: EDIT OR DELETE A VISIT ---
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
                        st.toast("✅ Visit Deleted Successfully!", icon="🗑️")
                        st.success("✅ The visit was removed from your schedule.")
                        st.rerun()
                    else:
                        new_day = new_date.strftime("%A")
                        planner_sheet.update(range_name=f"A{sheet_row}:D{sheet_row}", values=[[str(new_date), new_day, new_loc, new_act]])
                        
                        st.toast("✅ Update Saved Successfully!", icon="✨")
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
                with col_n1:
                    dob = st.date_input("Date of Birth")
                with col_n2:
                    gender = st.selectbox("Gender", ["M", "F"])
                with col_n3:
                    parent = st.text_input("Parent's Name")
                
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
                with c_col1:
                    updated_contact = st.text_input("📞 Contact Number", value=existing_contact, placeholder="Enter 10-digit number")
                with c_col2:
                    if category == "👶 Anganwadi":
                        techo_id = st.text_input("🆔 Techo ID", placeholder="Enter Techo ID here")
                    else:
                        techo_id = "N/A"

                v_col1, v_col2, v_col3, v_col4 = st.columns(4)
                with v_col1:
                    height = st.number_input("Height (cm)", min_value=0.0, step=0.5)
                with v_col2:
                    weight = st.number_input("Weight (kg)", min_value=0.0, step=0.1)
                with v_col3:
                    if category == "👶 Anganwadi":
                        muac = st.number_input("MUAC (cm)", min_value=0.0, step=0.1)
                    else:
                        muac = "N/A"
                        st.text_input("MUAC (cm)", value="Not required for Schools", disabled=True)
                with v_col4:
                    hb = st.number_input("Hemoglobin (Hb %)", min_value=0.0, step=0.1)

                disease = st.text_input("🦠 Disease / Defect Identified (4D)", placeholder="Type 'None' or describe the defect...")

                save_btn = st.form_submit_button("💾 Save Screening Data")

                if save_btn:
                    if final_child_name == "":
                        st.error("🚨 Please enter a name for the child.")
                    elif height == 0 or weight == 0:
                        st.error("🚨 Height and Weight cannot be 0.")
                    else:
                        try:
                            if category == "👶 Anganwadi":
                                target_sheet = spreadsheet.worksheet("daily_screenings_aw")
                                row_to_save = [str(screening_date), selected_inst, final_child_name, str(dob), str(gender), height, weight, muac, hb, disease, updated_contact, techo_id]
                            else:
                                target_sheet = spreadsheet.worksheet("daily_screenings_schools")
                                row_to_save = [str(screening_date), selected_inst, final_child_name, str(dob), str(gender), height, weight, hb, disease, updated_contact]
                            
                            target_sheet.append_row(row_to_save)
                            
                            st.toast("✅ Vitals Saved to Cloud!", icon="🏥")
                            st.success(f"✅ Successfully recorded screening for {final_child_name} in {category} Database!")
                        except Exception as e:
                            st.error(f"⚠️ Error saving data: Please ensure your tabs are named 'daily_screenings_aw' and 'daily_screenings_schools'. Error details: {e}")

# ==========================================
# MODULE 3: 4D DEFECT REGISTRY
# ==========================================
elif menu == "3. 4D Defect Registry":
    st.title("🔍 4D Defect Registry & Search")
    search_term = st.text_input("Search for a child by Name, Village, or Defect:")

    if search_term:
        mask = df_4d.astype(str).apply(lambda x: x.str.contains(search_term, case=False)).any(axis=1)
        filtered_df = df_4d[mask]
        st.dataframe(filtered_df, use_container_width=True)
        st.success(f"Found {len(filtered_df)} matching records.")
    else:
        st.dataframe(df_4d, use_container_width=True)

# ==========================================
# MODULE 4: VISUAL ANALYSIS
# ==========================================
elif menu == "4. Visual Analysis":
    st.title("📊 Interactive Data Analysis")
    st.write("Live breakdown of your field data.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Total Students by School")
        if not df_schools.empty and 'School' in df_schools.columns and 'TOTAL' in df_schools.columns:
            df_schools['TOTAL'] = pd.to_numeric(df_schools['TOTAL'], errors='coerce').fillna(0)
            
            top_schools = df_schools.sort_values(by='TOTAL', ascending=False).head(10)
            st.bar_chart(data=top_schools, x='School', y='TOTAL')
            
    with col2:
        st.subheader("Gender Distribution (Anganwadis)")
        if not df_aw.empty and 'Gender' in df_aw.columns:
            gender_counts = df_aw['Gender'].value_counts()
            st.bar_chart(gender_counts)

# ==========================================
# MODULE 5: HBNC NEWBORN VISIT
# ==========================================
elif menu == "5. HBNC Newborn Visit":
    st.title("🍼 HBNC Neonatal Visit Interface")
    st.write("Record critical Home Based Newborn Care observations.")

    with st.form("hbnc_form"):
        st.markdown("#### 👶 Newborn & Parent Details")
        c1, c2, c3 = st.columns(3)
        with c1:
            visit_date = st.date_input("📅 Date of Home Visit")
        with c2:
            child_name = st.text_input("Child's Name", placeholder="e.g., Baby of Ashaben")
        with c3:
            techo_id = st.text_input("🆔 Techo ID")
            
        c4, c5 = st.columns(2)
        with c4:
            parent_name = st.text_input("Mother/Father's Name")
        with c5:
            contact_number = st.text_input("📞 Contact Number")

        st.divider()

        st.markdown("#### 🏥 Birth History")
        b1, b2, b3, b4 = st.columns(4)
        with b1:
            dob = st.date_input("🎂 Date of Birth")
        with b2:
            birth_weight = st.number_input("⚖️ Birth Weight (kg)", min_value=0.0, step=0.1)
        with b3:
            delivery_type = st.selectbox("🩸 Delivery Type", ["Normal Delivery (ND)", "C-Section (LSCS)", "Instrumental"])
        with b4:
            delivery_point = st.selectbox("📍 Delivery Point", [
                "Vatsalya Hospital", "SDH Visavadar", "Jay Ambe Hospital", 
                "CHC/PHC", "Home Delivery", "Other Private Hospital"
            ])

        st.divider()

        st.markdown("#### 🩺 Clinical Examination & Observations")
        
        disease = st.text_input("🦠 Any Disease / Defect Identified?", placeholder="e.g., Cleft lip, suspected CHD, None")
        
        observations = st.text_area(
            "📝 Current Clinical Observations", 
            placeholder="Describe the baby's condition (e.g., Breastfeeding well, mild jaundice, cord stump clean and dry, active cry...)",
            height=100
        )

        submit_hbnc = st.form_submit_button("💾 Save HBNC Record to Cloud")

        if submit_hbnc:
            if child_name == "" or parent_name == "":
                st.error("🚨 Please enter both the Child's Name and Parent's Name.")
            elif birth_weight < 1.0:
                st.warning("⚠️ Warning: Birth weight is unusually low. Please double-check.")
            else:
                try:
                    hbnc_sheet = spreadsheet.worksheet("hbnc_screenings")
                    
                    row_data = [
                        str(visit_date), child_name, parent_name, contact_number, 
                        str(dob), birth_weight, delivery_type, delivery_point, 
                        techo_id, disease, observations
                    ]
                    
                    hbnc_sheet.append_row(row_data)
                    
                    st.toast("✅ HBNC Record Saved!", icon="🍼")
                    st.success(f"✅ Successfully recorded the Home Visit for {child_name}.")
                except Exception as e:
                    st.error(f"⚠️ Error: Could not find 'hbnc_screenings' tab. Please create it in Google Sheets! Detail: {e}")

# ==========================================
# MODULE 6: SUCCESS STORY BUILDER
# ==========================================
elif menu == "6. Success Story Builder":
    st.title("🌟 Success Story Generator")
    st.write("Create official PDF reports for children successfully treated under RBSK.")
    st.info(f"🔍 X-RAY: Total patients found: {len(df_4d)}")
    st.info(f"🔍 X-RAY: Exact columns found: {list(df_4d.columns)}")
    st.dataframe(df_4d)

    if not df_4d.empty:
        df_4d.columns = df_4d.columns.astype(str).str.strip().str.upper()
        
        if 'NAME' in df_4d.columns and '4D' in df_4d.columns and 'VILLAGE' in df_4d.columns:
            
            df_4d['Select_Label'] = df_4d['NAME'].astype(str) + " (" + df_4d['4D'].astype(str) + ") - " + df_4d['VILLAGE'].astype(str)

