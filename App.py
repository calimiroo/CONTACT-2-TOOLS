# Merged Streamlit app using Option-1 (TOOL1) and Option-2 (TOOL2) extractors
# Filename: Option-1-2_Merged_Streamlit_App_Headless.py

import streamlit as st
import pandas as pd
import time
import random
import os
import sys
import tempfile
import re
import shutil
from datetime import datetime, timedelta

# Selenium / undetected_chromedriver
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --------------------------- UTILS ---------------------------

def beep():
    try:
        import winsound
        winsound.Beep(1000, 300)
    except Exception:
        pass

def get_shadow_element(driver, selector):
    script = f"""
    function findInShadows(selector) {{
        function search(root) {{
            if (!root) return null;
            const found = root.querySelector(selector);
            if (found) return found;
            const all = root.querySelectorAll('*');
            for (const el of all) {{
                if (el.shadowRoot) {{
                    const result = search(el.shadowRoot);
                    if (result) return result;
                }}
            }}
            return null;
        }}
        return search(document);
    }}
    return findInShadows('{selector}');
    """
    try:
        return driver.execute_script(script)
    except Exception:
        return None

def get_safe_driver():
    """
    تنشئ Driver بآلية تضمن توافق النسخ وتعمل على Linux/Windows
    """
    options = uc.ChromeOptions()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    
    # تحديد مسار المتصفح على سيرفر Streamlit (Linux)
    if sys.platform.startswith('linux'):
        possible_paths = ["/usr/bin/chromium", "/usr/bin/chromium-browser"]
        for path in possible_paths:
            if os.path.exists(path):
                options.binary_location = path
                break

    try:
        # المحاولة الأولى: السماح للمكتبة باكتشاف النسخة تلقائياً
        driver = uc.Chrome(options=options)
    except Exception as e:
        # المحاولة الثانية في حال حدوث خطأ النسخة (مثل الذي ظهر لك):
        # نستخرج رقم النسخة من رسالة الخطأ إذا أمكن ونمررها
        error_msg = str(e)
        version_match = re.search(r"Current browser version is (\d+)", error_msg)
        if version_match:
            ver = int(version_match.group(1))
            driver = uc.Chrome(options=options, version_main=ver)
        else:
            # إذا فشل كل شيء، نحاول التشغيل بدون تحديد نسخة
            driver = uc.Chrome(options=options)
            
    return driver

# --------------------------- EXTRACTORS ---------------------------

def extract_mohre_single(eid, wait_extra=0):
    driver = None
    try:
        driver = get_safe_driver()
        driver.get("https://backoffice.mohre.gov.ae/mohre.complaints.app/freezoneAnonymous2/ComplaintVerification?lang=en")
        time.sleep(random.uniform(4, 7) + wait_extra)

        # استهداف الحقول باستخدام Shadow DOM كما في كودك الأصلي
        eid_input = get_shadow_element(driver, '#IdentityNumber')
        if not eid_input:
            try: eid_input = driver.find_element(By.ID, "EIDA")
            except: pass

        if not eid_input:
            return {"EID": eid, "FullName": "Input Not Found", "MobileNumber": "Input Not Found", "Source": "TOOL1"}

        driver.execute_script(f"arguments[0].value = '{eid}';", eid_input)
        time.sleep(1)

        search_btn = get_shadow_element(driver, '#btnSearchEIDA')
        if search_btn:
            driver.execute_script("arguments[0].click();", search_btn)
            time.sleep(random.uniform(6, 10) + wait_extra)

        # استخراج النتائج
        full_name_el = get_shadow_element(driver, '#FullName')
        name = driver.execute_script("return arguments[0] ? (arguments[0].value || arguments[0].innerText) : 'Not Found';", full_name_el) if full_name_el else 'Not Found'
        
        mobile = 'Not Found'
        unmasked_el = get_shadow_element(driver, '#employeeMobile')
        if unmasked_el:
            mobile = driver.execute_script("return arguments[0].value || arguments[0].innerText || 'Not Found';", unmasked_el)

        return {"EID": eid, "FullName": name, "MobileNumber": mobile, "Source": "TOOL1"}

    except Exception as e:
        return {"EID": eid, "FullName": "Error", "MobileNumber": str(e), "Source": "TOOL1"}
    finally:
        if driver: driver.quit()

def extract_dcd_single(eid, wait_extra=0):
    driver = None
    try:
        driver = get_safe_driver()
        driver.get("https://dcdigitalservices.dubaichamber.com/?lang=en")
        time.sleep(random.uniform(5, 8) + wait_extra)

        # محاكاة خطوات التسجيل للوصول لبيانات الهوية
        sign_up_xpath = '//a[contains(text(), "Sign Up") or contains(@id, "signUp")]'
        sign_up_link = WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.XPATH, sign_up_xpath)))
        driver.execute_script("arguments[0].click();", sign_up_link)
        time.sleep(5)

        eid_input = WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "emiratesId")))
        driver.execute_script(f"arguments[0].value = '{eid}';", eid_input)
        eid_input.send_keys(Keys.TAB)
        time.sleep(8 + wait_extra)

        first_name = driver.find_element(By.ID, "firstNameUserInput").get_attribute("value")
        last_name = driver.find_element(By.ID, "lastNameUserInput").get_attribute("value")
        mobile = driver.find_element(By.ID, "mobileNumber").get_attribute("value")

        return {
            "EID": eid,
            "FullName": f"{first_name} {last_name}".strip(),
            "MobileNumber": mobile,
            "Source": "TOOL2"
        }
    except Exception as e:
        return {"EID": eid, "FullName": "Error", "MobileNumber": str(e), "Source": "TOOL2"}
    finally:
        if driver: driver.quit()

# --------------------------- STREAMLIT UI ---------------------------

st.set_page_config(page_title="HAMADA TRACING - Unified", layout="wide")
st.title("HAMADA TRACING")

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    with st.form('login'):
        pwd = st.text_input('Password', type='password')
        if st.form_submit_button('Login'):
            if pwd == 'Hamada':
                st.session_state.authenticated = True
                st.rerun()
            else: st.error('Wrong password')
    st.stop()

extractor_mode = st.selectbox('Extractor Mode', ['Both', 'TOOL1 only', 'TOOL2 only'], index=1)
wait_multiplier = st.slider('Wait Multiplier', 0.0, 5.0, 1.0)

tab1, tab2 = st.tabs(['Single Search', 'Batch Upload'])

with tab1:
    eid_in = st.text_input('Emirates ID')
    if st.button('Search Now'):
        with st.spinner('Extracting...'):
            results = []
            if extractor_mode in ['Both', 'TOOL1 only']:
                results.append(extract_mohre_single(eid_in, wait_multiplier))
            if extractor_mode in ['Both', 'TOOL2 only']:
                results.append(extract_dcd_single(eid_in, wait_multiplier))
            st.table(pd.DataFrame(results))

with tab2:
    uploaded = st.file_uploader('Upload Excel/CSV', type=['xlsx', 'csv'])
    if uploaded:
        df_in = pd.read_excel(uploaded) if uploaded.name.endswith('xlsx') else pd.read_csv(uploaded)
        eids = df_in.iloc[:, 0].dropna().tolist() # يفترض العمود الأول هو EID
        
        if st.button('Start Batch'):
            results_batch = []
            progress = st.progress(0)
            for i, eid in enumerate(eids):
                res = extract_mohre_single(str(eid), wait_multiplier) if 'TOOL1' in extractor_mode or 'Both' in extractor_mode else extract_dcd_single(str(eid), wait_multiplier)
                results_batch.append(res)
                progress.progress((i+1)/len(eids))
                st.dataframe(pd.DataFrame(results_batch))
            
            st.download_button('Download Result', pd.DataFrame(results_batch).to_csv(index=False), 'results.csv')
