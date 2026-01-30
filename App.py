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

# --------------------------- MOCK EXTRACTORS (Links Only) ---------------------------
# نظرًا لقيود الأمان على المواقع الحكومية، لا يمكن استخراج البيانات تلقائيًا.
# نستخدم دوال تُنشئ روابط مباشرة للمستخدم لفتحها يدويًا.

def extract_mohre_single(eid, headless=True, lang_force=True, wait_extra=0):
    """
    دالة لاستخراج معلومات من MOHRE.
    نظرًا لقيود الأمان، نُنشئ رابطًا مباشرًا فقط.
    """
    # إنشاء رابط يحتوي على EID مُدخل
    base_url = "https://backoffice.mohre.gov.ae/mohre.complaints.app/freezoneAnonymous2/ComplaintVerification?lang=en"
    # ملاحظة: لا يمكن تمرير EID في الرابط مباشرة، يجب أن يُدخله المستخدم على الصفحة
    return {
        "EID": eid,
        "FullName": "Manual Verification Required",
        "MobileNumber": "Not Available",
        "Source": "TOOL1-LINK",
        "Verification_Link": base_url  # الرابط الرسمي
    }

def extract_dcd_single(eid, headless=True, wait_extra=0):
    """
    دالة لاستخراج معلومات من DCD.
    نستخدم رابطًا وهميًا كمثال. قم بتعديله.
    """
    # مثال على رابط DCD (يجب تعديله إلى الرابط الصحيح)
    base_url = "https://dcdigitalservices.dubaichamber.com/?lang=en"
    return {
        "EID": eid,
        "FullName": "Manual Verification Required",
        "MobileNumber": "Not Available",
        "Email": "Not Available",
        "Source": "TOOL2-LINK",
        "Verification_Link": base_url
    }

# --------------------------- STREAMLIT APP ---------------------------

st.set_page_config(page_title="HAMADA TRACING - Manual Verification", layout="wide")
st.title("HAMADA TRACING (Manual Verification)")

# --- auth ---
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    with st.form('login'):
        st.subheader('Protected Access')
        pwd = st.text_input('Password', type='password')
        if st.form_submit_button('Login'):
            if pwd == 'Hamada':
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error('Wrong password')
    st.stop()

# --- app controls ---
col_top = st.columns([2,1])
with col_top[0]:
    extractor_mode = st.selectbox(
        'Extractor Mode',
        ['Both (TOOL1 + TOOL2)', 'TOOL1 only', 'TOOL2 only'],
        index=1  # TOOL1 only default
    )
with col_top[1]:
    wait_multiplier = st.slider('Delay multiplier', 0.0, 5.0, 0.5, 0.1)

def run_extractors_on_eid(eid):
    results = []
    if extractor_mode in ['Both (TOOL1 + TOOL2)', 'TOOL1 only']:
        res1 = extract_mohre_single(eid, headless=True, wait_extra=wait_multiplier)
        if res1:
            results.append(res1)
    if extractor_mode in ['Both (TOOL1 + TOOL2)', 'TOOL2 only']:
        res2 = extract_dcd_single(eid, headless=True, wait_extra=wait_multiplier)
        if res2:
            results.append(res2)
    return results

# ---------- SINGLE SEARCH ----------
tab1, tab2 = st.tabs(['Single EID Search', 'Batch (Upload Excel)'])

with tab1:
    st.subheader('Single Emirates ID lookup')
    c1, c2 = st.columns([3,1])
    eid_input = c1.text_input('Enter Emirates ID (only digits)')
    if c2.button('Get Links'):
        if not eid_input or not str(eid_input).strip():
            st.warning('Enter a valid Emirates ID')
        else:
            with st.spinner('Preparing links...'):
                start = time.time()
                aggregated = run_extractors_on_eid(str(eid_input).strip())
                if not aggregated:
                    st.error('No links generated.')
                else:
                    df = pd.DataFrame(aggregated)
                    st.write('Verification Links:')
                    for _, row in df.iterrows():
                        st.write(f"**{row['Source']} Link:**")
                        st.link_button("🔗 Open Verification Page", row['Verification_Link'], type="secondary")
                    
                    # لا يمكن تحميل CSV مع معلومات فارغة، نعرض الجدول فقط
                    st.dataframe(df)
                    # beep() # لا حاجة للصوت هنا
                    st.success(f'Links ready in {int(time.time()-start)}s')

# ---------- BATCH PROCESSING ----------
with tab2:
    st.subheader('Batch Excel upload')
    uploaded = st.file_uploader('Upload .xlsx or .csv file', type=['xlsx', 'csv'])

    if uploaded:
        try:
            if uploaded.name.lower().endswith('.csv'):
                df_in = pd.read_csv(uploaded, dtype=str)
            else:
                df_in = pd.read_excel(uploaded, dtype=str)
        except Exception as e:
            st.error(f'Error reading file: {e}')
            st.stop()

        possible_cols = [c for c in df_in.columns if c.lower() in ['eid', 'emirates id', 'emiratesid', 'id']]
        if not possible_cols:
            st.warning("Couldn't find an EID column automatically. Please map the column below.")
            col_map = st.selectbox('Map EID column', options=['--select--'] + list(df_in.columns.tolist()))
            if col_map and col_map != '--select--':
                eid_series = df_in[col_map].astype(str).str.strip()
            else:
                st.stop()
        else:
            eid_series = df_in[possible_cols[0]].astype(str).str.strip()

        eids = eid_series.dropna().unique().tolist()
        st.write(f'Total unique EIDs: {len(eids)}')

        if 'batch_results' not in st.session_state:
            st.session_state.batch_results = []
        if 'run_state' not in st.session_state:
            st.session_state.run_state = 'stopped'
        if 'start_time_ref' not in st.session_state:
            st.session_state.start_time_ref = None

        col_a, col_b, col_c = st.columns(3)
        if col_a.button('▶️ Start / Resume'):
            st.session_state.run_state = 'running'
            if st.session_state.start_time_ref is None:
                st.session_state.start_time_ref = time.time()
        if col_b.button('⏸️ Pause'):
            st.session_state.run_state = 'paused'
        if col_c.button('⏹️ Stop & Reset'):
            st.session_state.run_state = 'stopped'
            st.session_state.batch_results = []
            st.session_state.start_time_ref = None
            st.rerun()

        progress_bar = st.progress(0)
        status_text = st.empty()
        # live_table = st.empty() # لا نعرض جدول حي في الدفعة لتسريع العملية

        total = len(eids)
        successes = 0
        for idx, eid in enumerate(eids):
            while st.session_state.run_state == 'paused':
                status_text.warning('Paused...')
                time.sleep(1)
            if st.session_state.run_state == 'stopped':
                break
            if idx < len(st.session_state.batch_results):
                progress_bar.progress((idx + 1) / total)
                status_text.info(f"Skipping {idx+1}/{total} - already processed")
                continue

            status_text.info(f'Processing {idx+1}/{total}: {eid}')
            start = time.time()
            try:
                res_list = run_extractors_on_eid(eid)
                if res_list:
                    for r in res_list:
                        st.session_state.batch_results.append(r)
                        # لا يمكن التحقق من "Found" لأن المعلومات غير متاحة تلقائيًا
                        # نعتبر كلها "Processed"
                        successes += 1
                else:
                    st.session_state.batch_results.append({
                        "EID": eid,
                        "FullName": 'No Link Generated',
                        'MobileNumber': 'N/A',
                        'Source': 'None',
                        'Verification_Link': 'N/A'
                    })
            except Exception as e:
                st.session_state.batch_results.append({
                    "EID": eid,
                    "FullName": 'Error',
                    'MobileNumber': str(e),
                    'Source': 'Exception',
                    'Verification_Link': 'N/A'
                })

            elapsed = int(time.time() - start)
            progress_bar.progress((idx + 1) / total)
            # live_table.dataframe(pd.DataFrame(st.session_state.batch_results), use_container_width=True)
            time.sleep(0.2)

        if st.session_state.run_state == 'running' and len(st.session_state.batch_results) >= total:
            st.success(f'Batch finished. Processed: {successes} EIDs. Total time: {str(timedelta(seconds=int(time.time()-st.session_state.start_time_ref)))}')
            result_df = pd.DataFrame(st.session_state.batch_results)
            st.dataframe(result_df)
            st.download_button('Download full results (CSV)', result_df.to_csv(index=False).encode('utf-8'), file_name='batch_verification_links.csv')
            beep()
