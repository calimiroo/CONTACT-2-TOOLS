# Merged Streamlit app using Option-1 (TOOL1) and Option-2 (TOOL2) extractors
# Filename: Option-1-2_Merged_Streamlit_App_Headless.py
# Usage: pip install -r requirements.txt
# Run: streamlit run Option-1-2_Merged_Streamlit_App_Headless.py
import streamlit as st
import pandas as pd
import time
import random
import os
import sys
import tempfile
import re
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
        print("\a")
def get_chrome_version():
    try:
        if sys.platform == 'win32':
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Google\Chrome\BLBeacon")
            version, _ = winreg.QueryValueEx(key, "version")
            return int(version.split('.')[0])
    except Exception:
        pass
    return None
class RobustChrome(uc.Chrome):
    def __del__(self):
        try:
            self.quit()
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
# --------------------------- EXTRACTORS ---------------------------
def extract_mohre_single(eid, headless=True, lang_force=True, wait_extra=0):
    options = uc.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--lang=en-US')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-software-rasterizer')
    options.add_experimental_option('prefs', {'intl.accept_languages': 'en-US,en'})
    # version = get_chrome_version()  # Commented out for cloud compatibility; undetected_chromedriver will auto-detect
    version = None
    driver = None
    try:
        driver = RobustChrome(options=options, version_main=version)
        driver.get("https://backoffice.mohre.gov.ae/mohre.complaints.app/freezoneAnonymous2/ComplaintVerification?lang=en")
        time.sleep(random.uniform(3, 6) + wait_extra)
        # try to click English
        try:
            lang_btn = None
            try:
                lang_btn = driver.find_element(By.XPATH, "//a[contains(text(), 'English')]")
            except:
                try:
                    lang_btn = driver.find_element(By.XPATH, "//span[contains(text(), 'English')]")
                except:
                    pass
            if lang_btn and lang_btn.is_displayed():
                driver.execute_script("arguments[0].click();", lang_btn)
                time.sleep(1)
        except:
            pass
        # select employee if necessary
        try:
            emp_btn = driver.find_element(By.ID, "employeeLink")
            driver.execute_script("arguments[0].click();", emp_btn)
            time.sleep(1)
        except:
            pass
        # fill EID
        eid_input = get_shadow_element(driver, '#IdentityNumber')
        if not eid_input:
            try:
                eid_input = driver.find_element(By.ID, "EIDA")
            except:
                eid_input = None
        if not eid_input:
            return {"EID": eid, "FullName": "Input Not Found", "MobileNumber": "Input Not Found"}
        driver.execute_script("arguments[0].value = '';", eid_input)
        driver.execute_script(f"arguments[0].value = '{eid}';", eid_input)
        time.sleep(0.5)
        search_btn = get_shadow_element(driver, '#btnSearchEIDA')
        if not search_btn:
            try:
                search_btn = driver.find_element(By.ID, "workderUid")
            except:
                search_btn = None
        if not search_btn:
            return {"EID": eid, "FullName": "Search Button Not Found", "MobileNumber": "Search Button Not Found"}
        driver.execute_script("arguments[0].click();", search_btn)
        time.sleep(random.uniform(6, 10) + wait_extra)
        full_name_el = get_shadow_element(driver, '#FullName')
        if not full_name_el:
            try:
                full_name_el = driver.find_element(By.ID, "CallerName")
            except:
                full_name_el = None
        name = 'Not Found'
        try:
            if full_name_el:
                name = driver.execute_script("return arguments[0] ? (arguments[0].value || arguments[0].innerText) : 'Not Found';", full_name_el)
        except:
            name = 'Not Found'
        if lang_force and re.search(r'[\u0600-\u06FF]', name or ''):
            try:
                driver.execute_script("window.location.href = window.location.href.split('?')[0] + '?lang=en';")
                time.sleep(2)
                full_name_el = get_shadow_element(driver, '#FullName')
                if full_name_el:
                    name = driver.execute_script("return arguments[0] ? (arguments[0].value || arguments[0].innerText) : 'Not Found';", full_name_el)
            except:
                pass
        mobile = 'Not Found'
        try:
            unmasked_el = get_shadow_element(driver, '#employeeMobile')
            if not unmasked_el:
                try:
                    unmasked_el = driver.find_element(By.ID, "employeeMobile")
                except:
                    unmasked_el = None
            if unmasked_el:
                mobile = driver.execute_script("return arguments[0].value || arguments[0].innerText || 'Not Found';", unmasked_el)
            else:
                visible_mobile_el = get_shadow_element(driver, '#MobileNumber')
                if visible_mobile_el:
                    mobile = driver.execute_script("return arguments[0].getAttribute('title') || arguments[0].value || arguments[0].innerText || 'Not Found';", visible_mobile_el)
        except:
            mobile = 'Not Found'
        return {"EID": eid, "FullName": name or 'Not Found', "MobileNumber": mobile or 'Not Found', "Source": "TOOL1"}
    except Exception as e:
        return {"EID": eid, "FullName": "Error", "MobileNumber": str(e), "Source": "TOOL1"}
    finally:
        try:
            if driver:
                driver.quit()
        except:
            pass
def extract_dcd_single(eid, headless=True, wait_extra=0):
    options = uc.ChromeOptions()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-software-rasterizer')
    temp_dir = tempfile.mkdtemp()
    options.add_argument(f'--user-data-dir={temp_dir}')
    options.add_argument('--lang=en-US')
    options.add_experimental_option('prefs', {'intl.accept_languages': 'en-US,en'})
    # version = get_chrome_version()  # Commented out for cloud compatibility
    version = None
    driver = None
    try:
        driver = RobustChrome(options=options, version_main=version)
        driver.get("https://dcdigitalservices.dubaichamber.com/?lang=en")
        WebDriverWait(driver, 20).until(EC.url_contains("authenticationendpoint"))
        time.sleep(random.uniform(2, 4) + wait_extra)
        try:
            sign_up_xpath = '//a[contains(text(), "Sign Up") or contains(text(), "Register") or contains(text(), "Create Account") or contains(text(), "Don\'t have an account") or contains(@id, "signUp")] | //button[contains(text(), "Sign Up") or contains(text(), "Register") or contains(text(), "Create Account") or contains(text(), "Don\'t have an account") or contains(@id, "signUp")]'
            sign_up_link = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, sign_up_xpath)))
            driver.execute_script("arguments[0].click();", sign_up_link)
            time.sleep(random.uniform(3, 6) + wait_extra)
        except Exception as e:
            return {"EID": eid, "FullName": "Sign Up Not Found", "MobileNumber": "Sign Up Not Found", "Source": "TOOL2"}
        try:
            continue_btn_xpath = '//button[contains(text(), "Continue with email") or contains(text(), "Continue with Email") or contains(text(), "email/emiratesId") or contains(text(), "Email/Emirates ID") or contains(text(), "Basic") or contains(@id, "basicAuthenticator")]' 
            continue_btn = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, continue_btn_xpath)))
            driver.execute_script("arguments[0].click();", continue_btn)
            time.sleep(random.uniform(3, 6) + wait_extra)
        except Exception:
            pass
        try:
            uae_resident_select = WebDriverWait(driver, 8).until(EC.presence_of_element_located((By.ID, "uaeResident")))
            driver.execute_script("arguments[0].value = 'yes';", uae_resident_select)
            driver.execute_script("arguments[0].dispatchEvent(new Event('change'));", uae_resident_select)
            time.sleep(1)
        except:
            pass
        try:
            eid_input = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, "emiratesId")))
            driver.execute_script("arguments[0].value = '';", eid_input)
            driver.execute_script(f"arguments[0].value = '{eid}';", eid_input)
            time.sleep(0.5)
            driver.execute_script("arguments[0].blur();", eid_input)
            eid_input.send_keys(Keys.TAB)
            time.sleep(random.uniform(4, 8) + wait_extra)
            def is_first_name_present(drv):
                try:
                    el = drv.find_element(By.ID, "firstNameUserInput")
                    value = el.get_attribute("value")
                    return bool(value and value != '')
                except:
                    return False
            try:
                WebDriverWait(driver, 30).until(is_first_name_present)
            except:
                return {"EID": eid, "FullName": "Timeout/Not Found", "MobileNumber": "Timeout/Not Found", "Source": "TOOL2"}
            def get_value_by_id(id_str):
                try:
                    el = driver.find_element(By.ID, id_str)
                    value = el.get_attribute("value") or el.text or 'Not Found'
                    return value
                except:
                    return 'Not Found'
            first_name = get_value_by_id("firstNameUserInput")
            last_name = get_value_by_id("lastNameUserInput")
            full_name = f"{first_name} {last_name}".strip() if first_name != 'Not Found' else 'Not Found'
            email = get_value_by_id("usernameUserInput")
            mobile = get_value_by_id("mobileNumber")
            return {
                "EID": eid,
                "FullName": full_name or 'Not Found',
                "MobileNumber": mobile or 'Not Found',
                "Email": email or 'Not Found',
                "Source": "TOOL2"
            }
        except Exception as e:
            return {"EID": eid, "FullName": "Error", "MobileNumber": str(e), "Source": "TOOL2"}
    except Exception as e:
        return {"EID": eid, "FullName": "Critical Error", "MobileNumber": str(e), "Source": "TOOL2"}
    finally:
        try:
            if driver:
                driver.quit()
        except:
            pass
# --------------------------- STREAMLIT APP ---------------------------
st.set_page_config(page_title="HAMADA TRACING - Unified", layout="wide")
st.title("HAMADA TRACING")
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
    # TOOL1 only as default
    extractor_mode = st.selectbox(
        'Extractor Mode',
        ['Both (TOOL1 + TOOL2)', 'TOOL1 only', 'TOOL2 only'],
        index=1  # index=1 makes TOOL1 only the default
    )
with col_top[1]:
    wait_multiplier = st.slider('Delay multiplier (speed vs reliability)', 0.0, 5.0, 0.5, 0.1)
# helper to run chosen extractors
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
    if c2.button('Search'):
        if not eid_input or not str(eid_input).strip():
            st.warning('Enter a valid Emirates ID')
        else:
            with st.spinner('Running extractors...'):
                start = time.time()
                aggregated = run_extractors_on_eid(str(eid_input).strip())
                if not aggregated:
                    st.error('No results found or both extractors failed.')
                else:
                    df = pd.DataFrame(aggregated)
                    st.write('Live results:')
                    st.dataframe(df)
                    st.download_button('Download results (CSV)', df.to_csv(index=False).encode('utf-8'), file_name=f'result_{eid_input}.csv')
                    beep()
                    st.success(f'Finished in {int(time.time()-start)}s')
# ---------- BATCH PROCESSING ----------
with tab2:
    st.subheader('Batch Excel upload - one column with header "EID" or "Emirates Id"')
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
        # find column
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
        # dedupe and cleanup
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
        live_table = st.empty()
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
                        if r.get('FullName') and r.get('FullName') not in ['Not Found', 'Error', 'Timeout/Not Found', 'Input Not Found']:
                            successes += 1
                else:
                    st.session_state.batch_results.append({
                        "EID": eid,
                        "FullName": 'Not Found',
                        'MobileNumber': 'Not Found',
                        'Source': 'None'
                    })
            except Exception as e:
                st.session_state.batch_results.append({
                    "EID": eid,
                    "FullName": 'Error',
                    'MobileNumber': str(e),
                    'Source': 'Exception'
                })
            elapsed = int(time.time() - start)
            progress_bar.progress((idx + 1) / total)
            live_df = pd.DataFrame(st.session_state.batch_results)
            live_table.dataframe(live_df, use_container_width=True)
            time.sleep(0.2)
        if st.session_state.run_state == 'running' and len(st.session_state.batch_results) >= total:
            st.success(f'Batch finished. Found: {successes} / {total}. Total time: {str(timedelta(seconds=int(time.time()-st.session_state.start_time_ref)))}')
            result_df = pd.DataFrame(st.session_state.batch_results)
            st.download_button('Download full results (CSV)', result_df.to_csv(index=False).encode('utf-8'), file_name='batch_results.csv')
            beep()
