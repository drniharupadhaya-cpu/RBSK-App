import streamlit as st
import pandas as pd
import plotly.express as px

# -----------------------------------------
# PAGE CONFIGURATION
# -----------------------------------------
st.set_page_config(page_title="DHO Command Center | Junagadh", page_icon="🏥", layout="wide")

# Custom CSS for a premium Executive Look
st.markdown("""
    <style>
    .big-font {font-size:24px !important; font-weight: bold; color: #1E3A8A;}
    .kpi-card {background-color: #F3F4F6; padding: 20px; border-radius: 10px; border-left: 5px solid #3B82F6; box-shadow: 2px 2px 5px rgba(0,0,0,0.1);}
    .kpi-title {color: #6B7280; font-size: 14px; font-weight: bold; text-transform: uppercase;}
    .kpi-value {color: #111827; font-size: 32px; font-weight: 900;}
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------
# DATA LOADING FUNCTION (Hook to your Live Sheets)
# -----------------------------------------
@st.cache_data(ttl=600) # Caches data for 10 mins so it's super fast for the DHO
def load_live_data():
    # INSTRUCTIONS: Replace these mock dataframes with your actual Google Sheets fetch code.
    # e.g., df_summary = conn.read("NEW BIRTH DEFECT TOTAL 2025-26", worksheet="SUMMRY SHEET report")
    
    # 1. Mocking the 'SUMMRY SHEET report' for Birth Defects
    defect_summary = pd.DataFrame({
        'Taluka': ['JUNAGADH', 'VANTHALI', 'MANAVADAR', 'KESHOD', 'MANGROL', 'MALIYA', 'MENDARADA', 'VISAVADAR', 'BHESAN'],
        'Reported': [12, 8, 15, 25, 34, 21, 11, 18, 7],
        'On Treatment': [10, 7, 13, 22, 30, 19, 9, 13, 4],
        'Pending / Waiting': [1, 1, 1, 2, 1, 1, 0, 0, 0]
    })
    
    # 2. Mocking the CHD (Heart Disease) Line List
    chd_linelist = pd.DataFrame({
        'Taluka': ['JUNAGADH', 'BHESAN', 'KESHOD'],
        'Child Name': ['NIHARIKA VISHAL', 'VAGHELA MISHA', 'JODHANI VED'],
        'Gender': ['F', 'F', 'M'],
        'Contact': ['9537127461', '9586569498', '7984874875'],
        'Referral Status': ['Pending', 'Operated', 'Pending'],
        'Reason for Delay': ['Awaiting Funds', '-', 'Parents Refused']
    })
    
    return defect_summary, chd_linelist

df_defect_summary, df_chd = load_live_data()

# -----------------------------------------
# SIDEBAR NAVIGATION
# -----------------------------------------
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/f/fe/Seal_of_Gujarat.svg/1200px-Seal_of_Gujarat.svg.png", width=100)
st.sidebar.title("DHO Command Center")
st.sidebar.markdown("---")
menu = st.sidebar.radio("Select Module:", [
    "📊 Executive Snapshot", 
    "🚨 Critical Triage Tracker", 
    "👥 Team Accountability"
])

# -----------------------------------------
# MODULE 1: EXECUTIVE SNAPSHOT
# -----------------------------------------
if menu == "📊 Executive Snapshot":
    st.markdown('<p class="big-font">District Executive Snapshot: Junagadh</p>', unsafe_allow_html=True)
    st.markdown("Live aggregate data of all RBSK operations across the district.")
    
    st.write("### Birth Defect KPIs (Current Year)")
    col1, col2, col3, col4 = st.columns(4)
    
    # Calculate KPIs
    total_reported = df_defect_summary['Reported'].sum()
    total_treated = df_defect_summary['On Treatment'].sum()
    total_pending = df_defect_summary['Pending / Waiting'].sum()
    treatment_rate = round((total_treated / total_reported) * 100, 1) if total_reported > 0 else 0
    
    with col1:
        st.markdown(f'<div class="kpi-card"><div class="kpi-title">Total Defects Reported</div><div class="kpi-value">{total_reported}</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="kpi-card" style="border-left-color: #10B981;"><div class="kpi-title">On Treatment / Operated</div><div class="kpi-value" style="color: #10B981;">{total_treated}</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="kpi-card" style="border-left-color: #EF4444;"><div class="kpi-title">Pending / Waiting</div><div class="kpi-value" style="color: #EF4444;">{total_pending}</div></div>', unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div class="kpi-card" style="border-left-color: #F59E0B;"><div class="kpi-title">Treatment Conversion</div><div class="kpi-value" style="color: #F59E0B;">{treatment_rate}%</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    # Graphs
    colA, colB = st.columns(2)
    with colA:
        st.write("#### Taluka-wise Defect Burden")
        fig1 = px.bar(df_defect_summary, x='Taluka', y='Reported', color='Taluka', text_auto=True)
        fig1.update_layout(showlegend=False, margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig1, use_container_width=True)
        
    with colB:
        st.write("#### Treatment Status Distribution")
        fig2 = px.pie(names=['On Treatment', 'Pending'], values=[total_treated, total_pending], hole=0.4, color_discrete_sequence=['#10B981', '#EF4444'])
        fig2.update_layout(margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig2, use_container_width=True)

# -----------------------------------------
# MODULE 2: CRITICAL TRIAGE TRACKER
# -----------------------------------------
elif menu == "🚨 Critical Triage Tracker":
    st.markdown('<p class="big-font">Critical Surgery & Referral Tracker</p>', unsafe_allow_html=True)
    st.markdown("Filter and track severe cases (e.g., Congenital Heart Disease, Cleft Lip) requiring immediate surgical intervention.")
    
    # Filters
    col1, col2 = st.columns([1, 2])
    with col1:
        condition_filter = st.selectbox("Select Condition", ["Congenital Heart Disease (CHD)", "Cleft Lip / Palate", "Club Foot"])
    with col2:
        status_filter = st.selectbox("Treatment Status", ["All", "Pending", "Operated"])
    
    st.write(f"### Live Action Board: {condition_filter}")
    
    # Apply Filters
    df_filtered = df_chd.copy()
    if status_filter != "All":
        df_filtered = df_filtered[df_filtered['Referral Status'] == status_filter]
        
    # Style the dataframe to highlight pending cases
    def highlight_pending(val):
        color = '#ffebee' if val == 'Pending' else '#e8f5e9' if val == 'Operated' else ''
        return f'background-color: {color}'
    
    st.dataframe(
        df_filtered.style.map(highlight_pending, subset=['Referral Status']),
        use_container_width=True,
        hide_index=True
    )
    
    if status_filter == "Pending":
        st.warning(f"⚠️ There are {len(df_filtered)} critical children currently waiting for surgery. Please check the 'Reason for Delay' column.")

# -----------------------------------------
# MODULE 3: TEAM ACCOUNTABILITY
# -----------------------------------------
elif menu == "👥 Team Accountability":
    st.markdown('<p class="big-font">MHT Performance & Accountability</p>', unsafe_allow_html=True)
    st.markdown("Track exactly how many children each Mobile Health Team is screening month-by-month.")
    
    month = st.selectbox("Select Reporting Month", ["APR 2025", "MAY 2025", "JUN 2025"])
    
    st.info(f"Displaying performance data for {month}. (Connect this to your 'JUNAGADH DISTRICT COVERED' monthly tabs).")
    
    # Mock data representing the "JUNAGADH DISTRICT COVERED" sheets
    team_data = pd.DataFrame({
        'Taluka': ['JUNAGADH', 'JUNAGADH', 'KESHOD', 'KESHOD', 'MANGROL'],
        'Team ID': ['MHT-1240278', 'MHT-1240279', 'MHT-1240288', 'MHT-1240291', 'MHT-1240308'],
        'Target Screenings': [1500, 1500, 1200, 1200, 2000],
        'Actual Screened': [1450, 1100, 1250, 800, 1900]
    })
    
    team_data['Achievement %'] = round((team_data['Actual Screened'] / team_data['Target Screenings']) * 100, 1)
    
    # Highlight underperforming teams
    st.write("#### Monthly Team Leaderboard")
    st.dataframe(
        team_data.style.background_gradient(subset=['Achievement %'], cmap='RdYlGn', vmin=50, vmax=100),
        use_container_width=True,
        hide_index=True
    )
