import streamlit as st
import pandas as pd
import time
import os
import sys
import re
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By

def get_safe_driver():
    # إنشاء كائن خيارات جديد في كل مرة لتجنب خطأ "cannot reuse"
    options = uc.ChromeOptions()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    # تحديد مسار المتصفح في سيرفر Streamlit
    if sys.platform.startswith('linux'):
        options.binary_location = "/usr/bin/chromium"

    try:
        # محاولة التشغيل التلقائي
        driver = uc.Chrome(options=options)
    except Exception as e:
        # حل مشكلة اختلاف النسخ (Mismatch) عبر استخراج النسخة من رسالة الخطأ
        error_msg = str(e)
        version_match = re.search(r"Current browser version is (\d+)", error_msg)
        if version_match:
            ver = int(version_match.group(1))
            driver = uc.Chrome(options=options, version_main=ver)
        else:
            raise e
    return driver

# استخدم get_safe_driver() داخل دوال البحث الخاصة بك
