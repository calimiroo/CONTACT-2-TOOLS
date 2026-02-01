import streamlit as st
import pandas as pd
import time
from datetime import datetime, timedelta

# --------------------------- UTILS ---------------------------

def beep():
    try:
        import winsound
        winsound.Beep(1000, 300)
    except Exception:
        print("\a")

def format_time(seconds):
    seconds = int(seconds)
    return f"{seconds // 3600:02d}:{(seconds % 3600) // 60:02d}:{seconds % 60:02d}"

# --------------------------- MOCK EXTRACTORS (Links Only) ---------------------------
# نظرًا لقيود الأمان على المواقع الحكومية، لا يمكن استخراج البيانات تلقائيًا.
# نستخدم دوال تُنشئ روابط مباشرة للمستخدم لفتحها يدويًا.

def extract_mohre_single_manual(eid, headless=True, lang_force=True, wait_extra=0):
    """
    دالة لاستخراج معلومات من MOHRE.
    نظرًا لقيود الأمان، نُنشئ رابطًا مباشرًا فقط.
    """
    base_url = "https://backoffice.mohre.gov.ae/mohre.complaints.app/freezoneAnonymous2/ComplaintVerification?lang=en"
    return {
        "EID": eid,
        "FullName": "Manual Verification Required",
        "MobileNumber": "Not Available",
        "Source": "TOOL1-LINK",
        "Verification_Link": base_url
    }

def extract_dcd_single_manual(eid, headless=True, wait_extra=0):
    """
    دالة لاستخراج معلومات من DCD.
    نستخدم رابطًا وهميًا كمثال. قم بتعديله.
    """
    base_url = "https://dcdigitalservices.dubaichamber.com/?lang=en"
    return {
        "EID": eid,
        "FullName": "Manual Verification Required",
        "MobileNumber": "Not Available",
        "Email": "Not Available",
        "Source": "TOOL2-LINK",
        "Verification_Link": base_url
    }

# --------------------------- SESSION STATE MANAGEMENT ---------------------------

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'batch_results' not in st.session_state:
    st.session_state.batch_results = []
if 'current_index' not in st.session_state:
    st.session_state.current_index = 0
if 'found_counter' not in st.session_state:
    st.session_state.found_counter = 0
if 'accumulated_time' not in st.session_state:
    st.session_state.accumulated_time = 0.0
if 'single_res' not in st.session_state:
    st.session_state.single_res = None
if 'run_state' not in st.session_state:
    st.session_state.run_state = 'idle'

# --------------------------- LOGIN LOGIC ---------------------------

if not st.session_state.authenticated:
    with st.form("login_form"):
        pwd_input = st.text_input("Enter Password", type="password")
        if st.form_submit_button("Login"):
            if pwd_input == "Hamada": # يمكنك تغيير "Hamada" إلى "Bilkish" إذا كنت تستخدمها
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Incorrect Password.")
    st.stop()

# --------------------------- COLOR STYLING FOR DATAFRAME (Optional) ---------------------------

def color_status(val):
    if val == 'Found': 
        return 'background-color: #90EE90'
    if val == 'Not Found': 
        return 'background-color: #FFCCCB'
    if val == 'Link Generated':
        return 'background-color: #ADD8E6'  # Light blue for manual links
    return 'background-color: #FFA500'

# --------------------------- MAIN APP UI ---------------------------

st.set_page_config(page_title="HAMADA TRACING - Manual Verification", layout="wide")
st.title("HAMADA TRACING (Manual Verification)")

# --- Tabs for MOHRE/DCD ---
tab1, tab2 = st.tabs(["MOHRE/DCD EID Lookup", "Batch Processing"])

# --- MOHRE/DCD Tab ---
with tab1:
    st.subheader("🔍 MOHRE/DCD Emirates ID Lookup")
    c1_m, c2_m = st.columns([2,1])
    eid_input = c1_m.text_input('Enter Emirates ID (only digits)')
    extractor_mode = c2_m.selectbox(
        'Extractor Mode',
        ['Both (TOOL1 + TOOL2)', 'TOOL1 only', 'TOOL2 only'],
        index=1  # TOOL1 only default
    )

    if c2_m.button('Get Links'):
        if not eid_input or not str(eid_input).strip():
            st.warning('Enter a valid Emirates ID')
        else:
            with st.spinner('Generating links...'):
                start = time.time()
                results = []
                if extractor_mode in ['Both (TOOL1 + TOOL2)', 'TOOL1 only']:
                    res1 = extract_mohre_single_manual(str(eid_input).strip())
                    results.append(res1)
                if extractor_mode in ['Both (TOOL1 + TOOL2)', 'TOOL2 only']:
                    res2 = extract_dcd_single_manual(str(eid_input).strip())
                    results.append(res2)
                
                if not results:
                    st.error('No links generated.')
                else:
                    df = pd.DataFrame(results)
                    st.write('Verification Links:')
                    for _, row in df.iterrows():
                        st.write(f"**{row['Source']} Link:**")
                        st.link_button("🔗 Open Verification Page", row['Verification_Link'], type="secondary")
                    
                    st.dataframe(df.style.applymap(color_status, subset=['Source']))
                    st.success(f'Links ready in {int(time.time()-start)}s')

# --- Batch Processing Tab ---
with tab2:
    st.subheader("📊 MOHRE/DCD Excel Batch Upload")
    uploaded_mohre = st.file_uploader('Upload .xlsx or .csv file for MOHRE/DCD', type=['xlsx', 'csv'])

    if uploaded_mohre:
        try:
            if uploaded_mohre.name.lower().endswith('.csv'):
                df_in = pd.read_csv(uploaded_mohre, dtype=str)
            else:
                df_in = pd.read_excel(uploaded_mohre, dtype=str)

            possible_cols = [c for c in df_in.columns if c.lower() in ['eid', 'emirates id', 'emiratesid', 'id']]
            if not possible_cols:
                st.warning("Couldn't find an EID column automatically. Please map the column below.")
                col_map = st.selectbox('Map EID column', options=['--select--'] + list(df_in.columns.tolist()), key="mohre_col_map")
                if col_map and col_map != '--select--':
                    eid_series = df_in[col_map].astype(str).str.strip()
                else:
                    st.stop()
            else:
                eid_series = df_in[possible_cols[0]].astype(str).str.strip()

            eids = eid_series.dropna().unique().tolist()
            st.write(f'Total unique EIDs: {len(eids)}')

            if st.button("Generate All MOHRE/DCD Links", key="gen_mohre_batch"):
                st.success("🔗 Generated MOHRE/DCD Links:")
                for i, eid in enumerate(eids, 1):
                    if len(eid) == 15 and eid.isdigit():
                        st.write(f"{i}. [MOHRE - {eid}]({extract_mohre_single_manual(eid)['Verification_Link']})")
                        st.write(f"{i}. [DCD - {eid}]({extract_dcd_single_manual(eid)['Verification_Link']})")
                    else:
                        st.write(f"{i}. ❌ Invalid EID: `{eid}`")
                        
        except Exception as e:
            st.error(f'Error reading file: {e}')
