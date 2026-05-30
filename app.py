import streamlit as st
from docxtpl import DocxTemplate
import sqlite3
import pandas as pd
import os
import json
import zipfile
from io import BytesIO
from datetime import date
import inheritance_calc
import register_services
import reports_manager
import home_page

# ==========================================
# 1. إعدادات الصفحة والتصميم CSS
# ==========================================
st.set_page_config(page_title="BAYA Legal Contracts", layout="wide", page_icon="⚖️")

CSS_STYLE = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;800;900&display=swap');

    /* 1. الخط الأساسي والاتجاه */
    .stApp { direction: rtl; text-align: right; }
    html, body, p, label, h1, h2, h3, h4, h5, h6, input, textarea, button, .stMarkdown, .stText {
        font-family: 'Cairo', sans-serif !important;
    }
    i, .material-icons, .material-symbols-rounded, [data-testid="stIconMaterial"], svg {
        font-family: 'Material Symbols Rounded', 'Material Icons', sans-serif !important;
    }
    .stMarkdown p { text-align: right !important; direction: rtl !important; }

    /* 2. إخفاء زوائد Streamlit */
    [data-testid="stHeader"] { background: transparent !important; }
    .stAppDeployButton { display: none !important; visibility: hidden !important; }
    a[href*="github.com"] { display: none !important; visibility: hidden !important; }
    footer { display: none !important; visibility: hidden !important; }
    .viewerBadge_container, [data-testid="stViewerBadge"] { display: none !important; visibility: hidden !important; }
    [data-testid="InputInstructions"] { display: none !important; visibility: hidden !important; }

    /* 3. القائمة الجانبية — theme أخضر داكن */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e3d2f 0%, #163026 60%, #0f2218 100%) !important;
        width: 300px !important; min-width: 300px !important;
        border-left: 1px solid rgba(200,168,76,0.2) !important;
    }
    [data-testid="collapsedControl"] { display: none !important; }
    [data-testid="stSidebarHeader"] button { display: none !important; }
    [data-testid="stSidebarCollapseButton"] { display: none !important; }
    .stApp > header { direction: rtl !important; }

    [data-testid="stSidebar"] div[role="radiogroup"] > label > div:first-child { display: none !important; }
    [data-testid="stSidebar"] div[role="radiogroup"] > label {
        background-color: rgba(255,255,255,0.04);
        padding: 0; min-height: 50px; width: 100%;
        border-radius: 10px; margin-bottom: 8px;
        transition: all 0.25s ease;
        border: 1px solid rgba(200,168,76,0.15);
        cursor: pointer; display: flex; align-items: center; justify-content: center;
    }
    [data-testid="stSidebar"] div[role="radiogroup"] > label p {
        color: rgba(220,240,225,0.85) !important;
        font-size: 14px; margin: 0 !important;
        text-align: center; width: 100%;
        font-weight: 600; white-space: normal !important; padding: 5px;
    }
    [data-testid="stSidebar"] div[role="radiogroup"] > label:hover {
        background-color: rgba(200,168,76,0.12);
        border-color: rgba(200,168,76,0.5);
        transform: translateX(-3px);
    }
    div[role="radiogroup"] > label:has(input:checked) {
        background: linear-gradient(90deg, rgba(200,168,76,0.25), rgba(200,168,76,0.1)) !important;
        border-color: #c9a84c !important;
        border-right: 3px solid #c9a84c !important;
    }
    div[role="radiogroup"] > label:has(input:checked) p {
        color: #e8d5a3 !important; font-weight: 800; font-size: 15px !important;
    }

    /* 4. حقول الإدخال */
    .stTextInput input, .stNumberInput input, .stTextArea textarea {
        transition: all 0.3s ease; border: 1px solid #ccc;
    }
    .stTextInput input:hover, .stNumberInput input:hover, .stTextArea textarea:hover {
        border-color: #c9a84c !important;
        box-shadow: 0 0 8px rgba(201,168,76,0.25) !important;
        background-color: #fdfbf7 !important;
    }
    .stTextInput input:focus, .stNumberInput input:focus, .stTextArea textarea:focus {
        border-color: #2d5a4e !important;
        box-shadow: 0 0 8px rgba(45,90,78,0.25) !important;
    }

    .delete-btn button { background-color: #ffebee !important; color: #cc0000 !important; border: 1px solid #ffcdd2 !important; padding: 2px 10px !important; }
    .delete-btn button:hover { background-color: #ffcdd2 !important; border-color: #cc0000 !important; }

    /* 5. ألوان المتقاسمين */
    div[data-testid="stExpander"]:nth-child(1n) summary { border-right: 5px solid #2d5a4e !important; background-color: #f0f7f4 !important; }
    div[data-testid="stExpander"]:nth-child(2n) summary { border-right: 5px solid #c9a84c !important; background-color: #fdf8ed !important; }
    div[data-testid="stExpander"]:nth-child(3n) summary { border-right: 5px solid #7b9e87 !important; background-color: #f2f7f4 !important; }
    div[data-testid="stExpander"]:nth-child(4n) summary { border-right: 5px solid #a0522d !important; background-color: #faf4ef !important; }
    div[data-testid="stExpander"]:nth-child(5n) summary { border-right: 5px solid #3d7a5e !important; background-color: #eef6f1 !important; }

    /* 6. premium-header بالثيم الجديد */
    .premium-header {
        background: linear-gradient(90deg, #f7f3ee 0%, #ffffff 100%);
        padding: 12px 20px; border-right: 5px solid #c9a84c; border-radius: 0;
        margin-top: 15px; margin-bottom: 20px;
        color: #1e3d2f !important; font-weight: 800; font-size: 22px;
        display: block !important; text-align: right !important; direction: rtl !important; width: 100% !important;
        transition: transform 0.3s ease; position: relative; overflow: hidden;
    }
    .premium-header::before {
        content: ''; position: absolute; top: 0; right: 0; width: 100%; height: 100%;
        background: linear-gradient(90deg, transparent, rgba(201,168,76,0.07), transparent);
        background-size: 200% auto; animation: goldShimmer2 4s linear infinite;
    }
    .premium-header:hover { transform: translateX(-3px); }

    .info-header {
        background-color: #eef6f1; padding: 10px 15px;
        border-right: 4px solid #2d5a4e; border-radius: 5px;
        color: #1e3d2f !important; font-weight: 600;
        margin-bottom: 15px; margin-top: 15px; transition: all 0.3s ease;
        display: block !important; text-align: right !important; direction: rtl !important; width: 100% !important;
    }
    .info-header:hover { background-color: #ddf0e6; transform: translateX(-2px); }

    /* 7. أنيميشن تسجيل الدخول */
    @keyframes comeFromLeft {
        0%   { transform: translateX(-200px) rotate(-30deg) scale(0.5); opacity: 0; filter: blur(8px); }
        60%  { transform: translateX(15px) rotate(3deg) scale(1.05); opacity: 1; filter: blur(0); }
        80%  { transform: translateX(-6px) rotate(-1deg) scale(0.98); }
        100% { transform: translateX(0) rotate(0) scale(1); opacity: 1; filter: blur(0); }
    }
    @keyframes comeFromTop {
        0%   { transform: translateY(-200px) scale(0.4) rotate(20deg); opacity: 0; filter: blur(10px); }
        55%  { transform: translateY(12px) scale(1.08) rotate(-2deg); opacity: 1; filter: blur(0); }
        75%  { transform: translateY(-5px) scale(0.97) rotate(1deg); }
        100% { transform: translateY(0) scale(1) rotate(0); opacity: 1; }
    }
    @keyframes comeFromBottom {
        0%   { transform: translateY(200px) scale(0.4) rotate(-20deg); opacity: 0; filter: blur(10px); }
        55%  { transform: translateY(-12px) scale(1.08) rotate(2deg); opacity: 1; filter: blur(0); }
        75%  { transform: translateY(5px) scale(0.97) rotate(-1deg); }
        100% { transform: translateY(0) scale(1) rotate(0); opacity: 1; }
    }
    @keyframes comeFromRight {
        0%   { transform: translateX(200px) rotate(30deg) scale(0.5); opacity: 0; filter: blur(8px); }
        60%  { transform: translateX(-15px) rotate(-3deg) scale(1.05); opacity: 1; filter: blur(0); }
        80%  { transform: translateX(6px) rotate(1deg) scale(0.98); }
        100% { transform: translateX(0) rotate(0) scale(1); opacity: 1; filter: blur(0); }
    }
    @keyframes goldShimmer2 { 0% { background-position: -200% center; } 100% { background-position: 200% center; } }
    @keyframes goldShimmer  { 0% { background-position: -200% center; } 100% { background-position: 200% center; } }
    @keyframes goldenPulseRing {
        0%   { box-shadow: 0 0 0 0 rgba(201,168,76,0.6), 0 10px 40px rgba(0,0,0,0.4); }
        50%  { box-shadow: 0 0 0 18px rgba(201,168,76,0), 0 10px 40px rgba(0,0,0,0.4); }
        100% { box-shadow: 0 0 0 0 rgba(201,168,76,0), 0 10px 40px rgba(0,0,0,0.4); }
    }
    @keyframes scaleBalance {
        0%,100% { transform: rotate(0deg) scale(1); }
        20%  { transform: rotate(-12deg) scale(1.1); }
        40%  { transform: rotate(10deg) scale(1.05); }
        60%  { transform: rotate(-6deg) scale(1.08); }
        80%  { transform: rotate(4deg) scale(1.02); }
    }
    @keyframes drawLine { 0% { width: 0%; opacity: 0; } 60% { opacity: 1; } 100% { width: 80%; opacity: 1; } }
    @keyframes fadeInScale {
        0%   { opacity: 0; transform: translateY(20px) scale(0.92); filter: blur(4px); }
        60%  { opacity: 1; filter: blur(0); }
        100% { opacity: 1; transform: translateY(0) scale(1); filter: blur(0); }
    }
    @keyframes floatingWave { 0%,100% { transform: translateY(0px) rotate(0deg); } 30% { transform: translateY(-8px) rotate(-2deg); } 70% { transform: translateY(-4px) rotate(1deg); } }
    @keyframes gradientShift { 0% { background-position: 0% 50%; } 50% { background-position: 100% 50%; } 100% { background-position: 0% 50%; } }
    @keyframes spinSlow { from{transform:rotate(0deg)} to{transform:rotate(360deg)} }

    .letter-b { animation: comeFromLeft 1.1s cubic-bezier(0.34,1.56,0.64,1) forwards; display: inline-block; animation-delay: 0.1s; opacity: 0; }
    .letter-a1 { animation: comeFromTop 1.1s cubic-bezier(0.34,1.56,0.64,1) forwards; display: inline-block; animation-delay: 0.25s; opacity: 0; }
    .letter-y  { animation: comeFromBottom 1.1s cubic-bezier(0.34,1.56,0.64,1) forwards; display: inline-block; animation-delay: 0.4s; opacity: 0; }
    .letter-a2 { animation: comeFromRight 1.1s cubic-bezier(0.34,1.56,0.64,1) forwards; display: inline-block; animation-delay: 0.55s; opacity: 0; }
    .letter-b, .letter-a1, .letter-y, .letter-a2 {
        background: linear-gradient(90deg, #c9a84c 30%, #f0d98a 50%, #c9a84c 70%);
        background-size: 200% auto; -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
        animation: comeFromLeft 1.1s cubic-bezier(0.34,1.56,0.64,1) forwards, goldShimmer 3s linear 1.8s infinite;
    }
    .letter-a1 { animation: comeFromTop 1.1s cubic-bezier(0.34,1.56,0.64,1) forwards, goldShimmer 3s linear 2s infinite; }
    .letter-y  { animation: comeFromBottom 1.1s cubic-bezier(0.34,1.56,0.64,1) forwards, goldShimmer 3s linear 2.2s infinite; }
    .letter-a2 { animation: comeFromRight 1.1s cubic-bezier(0.34,1.56,0.64,1) forwards, goldShimmer 3s linear 2.4s infinite; }

    .fade-in-scale { animation: fadeInScale 0.9s cubic-bezier(0.22,1,0.36,1) forwards; display: inline-block; opacity: 0; }
    .continuous-wave { animation: floatingWave 4s ease-in-out infinite; display: inline-block; }
    .balance-icon { animation: fadeInScale 0.8s ease-out forwards, scaleBalance 6s ease-in-out 2s infinite; display: inline-block; opacity: 0; }
    .login-box-pulse { animation: goldenPulseRing 2.5s ease-out infinite; }
    .gold-line { display: block; height: 2px; background: linear-gradient(90deg, transparent, #c9a84c, #f0d98a, #c9a84c, transparent); border-radius: 2px; margin: 10px auto; animation: drawLine 1.5s cubic-bezier(0.22,1,0.36,1) 1.2s forwards; width: 0%; opacity: 0; }
    .login-animated-bg { background: linear-gradient(-45deg, #0d2318, #1e3d2f, #163026, #0a1f14, #1a3828); background-size: 400% 400%; animation: gradientShift 8s ease infinite; }

    .stFormSubmitButton button, [data-testid="stFormSubmitButton"] button { position: relative; overflow: hidden; transition: all 0.4s cubic-bezier(0.22,1,0.36,1) !important; }
    .stFormSubmitButton button::after, [data-testid="stFormSubmitButton"] button::after {
        content: ''; position: absolute; top: -50%; left: -75%; width: 50%; height: 200%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
        transform: skewX(-20deg); animation: shimmerBtn 3s ease-in-out 2s infinite;
    }
    @keyframes shimmerBtn { 0%{left:-75%;opacity:0} 10%{opacity:1} 50%{left:125%;opacity:1} 51%,100%{left:125%;opacity:0} }

    /* 8. الموبايل */
    @media (max-width: 768px) {
        [data-testid="stSidebar"] { width: 260px !important; min-width: 260px !important; max-width: 85vw !important; }
        .premium-header { font-size: 18px !important; padding: 10px 12px !important; }
    }
    .block-container { padding-top: 1.5rem !important; margin-top: 0 !important; }
    [data-testid="stAppViewContainer"] > .main { padding-top: 0rem !important; }
    [data-testid="stHeader"] { height: 3rem !important; min-height: 3rem !important; background: transparent !important; }

    /* 9. مربعات الحاسبة */
    .calc-result-container { display: flex; justify-content: center; gap: 15px; margin-top: 15px; margin-bottom: 20px; direction: ltr; }
    .calc-box { background-color: #ffffff; border: 2px solid #2d5a4e; border-radius: 12px; width: 70px; display: flex; flex-direction: column; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.08); }
    .calc-top { background-color: #2d5a4e; color: #c9a84c; font-weight: 900; font-size: 22px; text-align: center; padding: 5px 0; }
    .calc-bottom { color: #1e3d2f; font-weight: 800; font-size: 20px; text-align: center; padding: 10px 0; background-color: #f7f3ee; }
</style>
"""
st.markdown(CSS_STYLE, unsafe_allow_html=True)

# ==========================================
# 2. إنشاء الفولدرات والدوال المساعدة
# ==========================================
folders_to_create = [
    os.path.join("templates", "sale"),
    os.path.join("templates", "kesma_main"),
    os.path.join("templates", "kesma_indiv")
]
for folder in folders_to_create:
    if not os.path.exists(folder): os.makedirs(folder)

def get_age_from_id(nat_id):
    if nat_id and len(nat_id) == 14 and nat_id.isdigit():
        century_code = int(nat_id[0])
        if century_code == 2: year = 1900 + int(nat_id[1:3])
        elif century_code == 3: year = 2000 + int(nat_id[1:3])
        else: return ""
        month = int(nat_id[3:5])
        day = int(nat_id[5:7])
        try:
            birth_date = date(year, month, day)
            today = date.today()
            age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
            return str(age)
        except ValueError: return ""
    return ""

def tafqeet_area(f, k, s):
    def num_to_word(n, unit_name):
        units = ["", "واحد", "اثنان", "ثلاثة", "أربعة", "خمسة", "ستة", "سبعة", "ثمانية", "تسعة", "عشرة"]
        teens = ["", "أحد عشر", "اثنا عشر", "ثلاثة عشر", "أربعة عشر", "خمسة عشر", "ستة عشر", "سبعة عشر", "ثمانية عشر", "تسعة عشر"]
        tens = ["", "عشرة", "عشرون", "ثلاثون", "أربعون", "خمسون", "ستون", "سبعون", "ثمانون", "تسعون"]
        
        # تحويل الرقم إلى كلمات
        if n <= 10: word = units[n]
        elif 11 <= n <= 19: word = teens[n-10]
        else:
            t = n // 10
            u = n % 10
            if u == 0: word = tens[t]
            elif u == 1: word = f"واحد و{tens[t]}"
            elif u == 2: word = f"اثنان و{tens[t]}"
            else: word = f"{units[u]} و{tens[t]}"
        
        # ربط الكلمة بالتمييز الصحيح (فدان، قيراط، سهم)
        if unit_name == 'f':
            if n == 1: return "فدان واحد"
            if n == 2: return "فدانان"
            if 3 <= n <= 10: return f"{word} أفدنة"
            return f"{word} فداناً"
        elif unit_name == 'k':
            if n == 1: return "قيراط واحد"
            if n == 2: return "قيراطان"
            if 3 <= n <= 10: return f"{word} قراريط"
            return f"{word} قيراطاً"
        elif unit_name == 's':
            if n == 1: return "سهم واحد"
            if n == 2: return "سهمان"
            if 3 <= n <= 10: return f"{word} أسهم"
            return f"{word} سهماً"
        return ""

    parts = []
    f_int = int(float(f))
    k_int = int(float(k))
    s_val = float(s)
    s_int = int(s_val)
    s_frac = s_val - s_int

    # معالجة الفدان
    if f_int > 0:
        parts.append(num_to_word(f_int, 'f'))
        
    # معالجة القيراط
    if k_int > 0:
        parts.append(num_to_word(k_int, 'k'))
        
    # معالجة السهم والكسور (نصف، ربع)
    if s_int > 0 or s_frac > 0:
        if s_int > 0:
            s_str = num_to_word(s_int, 's')
            if s_frac == 0.5: s_str += " ونصف"
            elif s_frac == 0.25: s_str += " وربع"
            elif s_frac == 0.75: s_str += " وثلاثة أرباع"
            parts.append(s_str)
        else:
            # لو المساحة كسور فقط بدون أسهم صحيحة
            if s_frac == 0.5: parts.append("نصف سهم")
            elif s_frac == 0.25: parts.append("ربع سهم")
            elif s_frac == 0.75: parts.append("ثلاثة أرباع سهم")
            else: parts.append(f"{s_frac} سهم") 

    if not parts:
        return "صفر"
    
    return " و ".join(parts) + " فقط لا غير"

def init_db():
    conn = sqlite3.connect('contracts_database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS archive (id INTEGER PRIMARY KEY AUTOINCREMENT, contract_date TEXT, seller_name TEXT, buyer_name TEXT, raw_data TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT, password TEXT)''')
    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO users (username, password) VALUES ('admin', '12345')")
    conn.commit(); conn.close()

def save_to_db(date_val, seller, buyer, raw_json):
    conn = sqlite3.connect('contracts_database.db')
    c = conn.cursor()
    c.execute('INSERT INTO archive (contract_date, seller_name, buyer_name, raw_data) VALUES (?, ?, ?, ?)', (date_val, seller, buyer, raw_json))
    conn.commit(); conn.close()

def update_in_db(record_id, date_val, seller, buyer, raw_json):
    conn = sqlite3.connect('contracts_database.db')
    c = conn.cursor()
    c.execute('UPDATE archive SET contract_date=?, seller_name=?, buyer_name=?, raw_data=? WHERE id=?', (date_val, seller, buyer, raw_json, record_id))
    conn.commit(); conn.close()

def delete_from_db(record_id):
    conn = sqlite3.connect('contracts_database.db')
    c = conn.cursor()
    c.execute('DELETE FROM archive WHERE id=?', (record_id,))
    conn.commit(); conn.close()

def check_login(username, password):
    conn = sqlite3.connect('contracts_database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    user = c.fetchone()
    conn.close()
    return user is not None

def update_credentials(new_user, new_pass):
    conn = sqlite3.connect('contracts_database.db')
    c = conn.cursor()
    c.execute("UPDATE users SET username=?, password=? WHERE id=1", (new_user, new_pass))
    conn.commit(); conn.close()

init_db()

def format_sahm(s): return int(s) if s == int(s) else s

def parse_date_safe(d_val):
    if not d_val: return date.today()
    try: return date.fromisoformat(d_val)
    except: return date.today()

def format_custom_date(iso_str, mode="full"):
    if not iso_str: return ""
    try:
        d = date.fromisoformat(iso_str)
        if mode == "my": 
            return f"{d.month}/{d.year}" 
        if mode == "short": 
            return f"{d.day}/{d.month}/{d.year}"
            
        days_ar = ["الاثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت", "الأحد"]
        day_name = days_ar[d.weekday()]
        return f"{day_name} الموافق {d.day}/{d.month}/{d.year}"
    except: 
        return iso_str

def shorten_name(full_name, limit=3):
    if not full_name: return ""
    clean = full_name.replace("/", " ").replace("\\", " ").strip()
    words = clean.split()
    if "ورثة" in words or "المرحوم" in words:
        return " ".join(words[:limit+2])
    return " ".join(words[:limit])

# ==========================================
# 3. بوابة الدخول (Login Gate & Animation)
# ==========================================
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

LOGIN_HTML = """
<div class='login-box-pulse' style='text-align:center;padding:45px 35px;border-radius:20px;overflow:hidden;position:relative;border:1px solid rgba(201,168,76,0.25);'>
    <div class='login-animated-bg' style='position:absolute;top:0;left:0;width:100%;height:100%;border-radius:20px;z-index:0;'></div>
    <div style='position:absolute;top:-40px;right:-30px;width:160px;height:160px;border-radius:50%;border:1px solid rgba(201,168,76,0.08);animation:spinSlow 30s linear infinite;z-index:0;'></div>
    <div style='position:absolute;bottom:-50px;left:-20px;width:200px;height:200px;border-radius:50%;border:1px solid rgba(201,168,76,0.06);animation:spinSlow 45s linear infinite reverse;z-index:0;'></div>
    <div style='position:relative;z-index:1;'>
        <div class='balance-icon' style='font-size:70px;margin-bottom:8px;animation-delay:0.1s;filter:drop-shadow(0 0 18px rgba(201,168,76,0.5));'>⚖️</div>
        <div style="direction:ltr;display:flex;justify-content:center;align-items:center;flex-direction:column;gap:4px;margin-bottom:4px;">
            <div style="font-size:62px;font-weight:900;display:flex;gap:3px;letter-spacing:2px;justify-content:center;width:100%;">
                <span class='letter-b' style='animation-delay:0.2s;'>B</span>
                <span class='letter-a1' style='animation-delay:0.4s;'>A</span>
                <span class='letter-y' style='animation-delay:0.6s;'>Y</span>
                <span class='letter-a2' style='animation-delay:0.8s;'>A</span>
            </div>
            <span class='fade-in-scale continuous-wave' style='color:rgba(220,245,230,0.9);font-size:26px;font-weight:300;animation-delay:1.2s;letter-spacing:5px;display:block;'>Legal</span>
        </div>
        <span class='gold-line'></span>
        <h3 class='fade-in-scale' style='color:rgba(220,245,230,0.95);margin-top:18px;font-weight:600;font-size:17px;animation-delay:1.5s;'>الجمعية التعاونية الزراعية بالناصرية</h3>
        <p class='fade-in-scale' style='color:rgba(180,220,200,0.75);margin-top:8px;font-size:13px;animation-delay:1.7s;'>✦ تم التصميم بواسطة عادل جمعة ✦</p>
    </div>
</div><br>
"""

if not st.session_state.logged_in:
    st.markdown("<div style='height: 2vh;'></div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(LOGIN_HTML, unsafe_allow_html=True)
        with st.form("login_form"):
            username_input = st.text_input("👤 اسم المستخدم (أو رقم الهاتف)")
            password_input = st.text_input("🔑 كلمة المرور", type="password")
            submit_login = st.form_submit_button("تسجيل الدخول 🔓", use_container_width=True)
            if submit_login:
                if check_login(username_input, password_input):
                    st.session_state.logged_in = True
                    st.rerun()
                else:
                    st.error("❌ بيانات الدخول غير صحيحة، يرجى المحاولة مرة أخرى.")
    st.stop()

# ==========================================
# 4. إدارة حالة البيانات الافتراضية
# ==========================================
today_iso = date.today().isoformat()

def get_empty_sale():
    return {
        "doc_type": "sale", 
        "sellers": [{"name": "", "id": "", "address": "", "id_date": today_iso, "job": "", "age": ""}], 
        "buyers": [{"name": "", "id": "", "address": "", "id_date": today_iso, "job": "", "age": ""}], 
        "lands": [{"f": 0, "k": 0, "s": 0.0, "hod": "", "n": "", "s_bound": "", "e": "", "w": ""}],
        "is_heirs_s": False, "moraث_s": "", "s_morath_case_num": "", "s_morath_year": "", "s_morath_date": today_iso, "s_hayaza_no": "", "s_total_f": 0, "s_total_k": 0, "s_total_s": 0.0, "ayloula": "",
        "is_heirs_b": False, "moraث_b": "", "b_morath_case_num": "", "b_morath_year": "", "b_morath_date": today_iso, "b_hayaza_no": "", "b_total_f": 0, "b_total_k": 0, "b_total_s": 0.0, 
        "sell_f": 0, "sell_k": 0, "sell_s": 0.0, "sell_txt": "", "price_num": "", "price_txt": "", 
        "has_penalty": True, "penalty_num": "", "penalty_txt": "", "c_date": today_iso, "t_date": today_iso
    }

def get_empty_kesma():
    return {
        "doc_type": "kesma", "moraث": "", "hayaza_no": "", "morath_case_num": "", "morath_year": "", "morath_date": today_iso, "c_date": today_iso, "total_f": 0, "total_k": 0, "total_s": 0.0,
        "main_lands": [{"f": 0, "k": 0, "s": 0.0, "hod": "", "n": "", "s_bound": "", "e": "", "w": ""}],
        "partitioners": [{"name": "", "nat_id": "", "nat_id_date": today_iso, "address": "", "job": "", "age": "", "hayaza_no": "", "prev_f": 0, "prev_k": 0, "prev_s": 0.0, "total_f": 0, "total_k": 0, "total_s": 0.0, "total_txt": "", "lands": [{"f": 0, "k": 0, "s": 0.0, "hod": "", "n": "", "s_bound": "", "e": "", "w": ""}]}]
    }

def reset_form():
    st.session_state.sale_data = get_empty_sale()
    st.session_state.kesma_data = get_empty_kesma()
    st.session_state.current_archive_id = None
    st.session_state.loaded_doc_type = None
    if 'zip_data' in st.session_state: del st.session_state['zip_data']

if 'sale_data' not in st.session_state: reset_form()

def load_from_archive(record_id, json_str):
    loaded_data = json.loads(json_str)
    doc_type = loaded_data.get("doc_type")
    if not doc_type:
        if "partitioners" in loaded_data or "moraث" in loaded_data: doc_type = "kesma"; loaded_data["doc_type"] = "kesma"
        else: doc_type = "sale"; loaded_data["doc_type"] = "sale"
    if doc_type == "sale":
        for key in ["sellers", "buyers"]:
            if loaded_data.get(key) and isinstance(loaded_data[key][0], str):
                loaded_data[key] = [{"name": n, "id": "", "address": "", "id_date": today_iso, "job": "", "age": ""} for n in loaded_data[key]]
    st.session_state.current_archive_id = record_id
    st.session_state.loaded_doc_type = doc_type  
    if 'zip_data' in st.session_state: del st.session_state['zip_data']
    if doc_type == "kesma": st.session_state.kesma_data = loaded_data; st.session_state.active_menu = "🤝 منظومة القسمة الرضائية"
    else: st.session_state.sale_data = loaded_data; st.session_state.active_menu = "📝 منظومة عقود البيع"

# ==========================================
# 5. دوال تجهيز وبناء الوثائق
# ==========================================
def process_kesma_lands(lands, total_f, total_k, total_s):
    if not lands: return []
    processed = []
    ordinals = ["الأولى", "الثانية", "الثالثة", "الرابعة", "الخامسة", "السادسة", "السابعة", "الثامنة", "التاسعة", "العاشرة"]
    for idx, l in enumerate(lands):
        f_val, k_val, s_val = l.get("f",0), l.get("k",0), l.get("s",0.0)
        if len(lands) == 1 and f_val == 0 and k_val == 0 and s_val == 0:
            f_val, k_val, s_val = total_f, total_k, total_s
            
        if len(lands) == 1: plot_title = "قطعة أرض زراعية"
        else:
            ord_word = ordinals[idx] if idx < len(ordinals) else str(idx + 1)
            plot_title = f"القطعة {ord_word}"
            
        processed.append({
            "f": f_val, "k": k_val, "s": format_sahm(s_val), 
            "hod": l.get("hod",""), "n": l.get("n",""), "s_bound": l.get("s_bound",""), 
            "e": l.get("e",""), "w": l.get("w",""), 
            "اسم_القطعة": plot_title
        })
    return processed

def process_lands(lands, sell_f, sell_k, sell_s):
    if not lands: return []
    processed = []
    ordinals = ["الأولى", "الثانية", "الثالثة", "الرابعة", "الخامسة"]
    for idx, l in enumerate(lands):
        f_val, k_val, s_val = l.get("f",0), l.get("k",0), l.get("s",0.0)
        if len(lands) == 1 and f_val == 0 and k_val == 0 and s_val == 0:
            f_val, k_val, s_val = sell_f, sell_k, sell_s
        plot_title = "قطعة أرض زراعية" if len(lands) == 1 else f"القطعة {ordinals[idx] if idx < len(ordinals) else str(idx + 1)}"
        processed.append({
            "f": f_val, "k": k_val, "s": format_sahm(s_val), 
            "hod": l.get("hod",""), "n": l.get("n",""), "s_bound": l.get("s_bound",""), 
            "e": l.get("e",""), "w": l.get("w",""), "اسم_القطعة": plot_title
        })
    return processed

def build_sale_context(fd):
    final_seller = f"ورثة المرحوم / {fd['moraث_s']}" if fd.get("is_heirs_s") else (fd["sellers"][0]['name'] if fd["sellers"] else "")
    final_buyer = f"ورثة المرحوم / {fd['moraث_b']}" if fd.get("is_heirs_b") else (fd["buyers"][0]['name'] if fd["buyers"] else "")
    formatted_sellers = []
    for s in fd["sellers"]:
        s_copy = s.copy()
        s_copy["id_date"] = format_custom_date(s.get("id_date"), "my")
        formatted_sellers.append(s_copy)
    formatted_buyers = []
    for b in fd["buyers"]:
        b_copy = b.copy()
        b_copy["id_date"] = format_custom_date(b.get("id_date"), "my")
        formatted_buyers.append(b_copy)
    s1 = fd["sellers"][0] if fd["sellers"] else {}
    b1 = fd["buyers"][0] if fd["buyers"] else {}
    
    return {
        "sellers": formatted_sellers, "buyers": formatted_buyers,
        "اسم_البائع": final_seller, "رقم_بطاقة_البائع": s1.get("id", ""), "عنوان_البائع": s1.get("address", ""), "مهنة_البائع": s1.get("job", ""), "سن_البائع": s1.get("age", ""), "تاريخ_إصدار_بطاقة_البائع": format_custom_date(s1.get("id_date"), "my"),
        "اسم_المشتري": final_buyer, "رقم_بطاقة_المشتري": b1.get("id", ""), "عنوان_المشتري": b1.get("address", ""), "مهنة_المشتري": b1.get("job", ""), "سن_المشتري": b1.get("age", ""), "تاريخ_إصدار_بطاقة_المشتري": format_custom_date(b1.get("id_date"), "my"),
        "طريقة_أيلولة_الملكية": fd.get("ayloula", ""), "lands": process_lands(fd.get("lands", []), fd.get("sell_f",0), fd.get("sell_k",0), fd.get("sell_s",0.0)),
        "رقم_قضية_وراثة_البائع": fd.get("s_morath_case_num", ""), "سنة_قضية_وراثة_البائع": fd.get("s_morath_year", ""), "تاريخ_جلسة_وراثة_البائع": format_custom_date(fd.get("s_morath_date"), "full"),
        "رقم_قضية_وراثة_المشتري": fd.get("b_morath_case_num", ""), "سنة_قضية_وراثة_المشتري": fd.get("b_morath_year", ""), "تاريخ_جلسة_وراثة_المشتري": format_custom_date(fd.get("b_morath_date"), "full"),
        "الثمن_أرقام": fd.get("price_num", ""), "الثمن_حروف": fd.get("price_txt", ""), "يوجد_شرط_جزائي": fd.get("has_penalty", True), "الشرط_الجزائي_أرقام": fd.get("penalty_num", ""), "الشرط_الجزائي_حروف": fd.get("penalty_txt", ""),
        "تاريخ_العقد": format_custom_date(fd.get("c_date"), "full"), "تاريخ_العقد_رقمي": format_custom_date(fd.get("c_date"), "short"), 
        "تاريخ_اليوم": format_custom_date(fd.get("t_date"), "full"),
        "مساحة_البيع_فدان": fd.get("sell_f",0), "مساحة_البيع_قيراط": fd.get("sell_k",0), "مساحة_البيع_سهم": format_sahm(fd.get("sell_s",0.0)), "مساحة_البيع_حروف": fd.get("sell_txt", ""), 
        "رقم_حيازة_البائع": fd.get("s_hayaza_no", ""), "إجمالي_فدان_البائع": fd.get("s_total_f",0), "إجمالي_قيراط_البائع": fd.get("s_total_k",0), "إجمالي_سهم_البائع": format_sahm(fd.get("s_total_s",0.0)),
        "رقم_حيازة_المشتري": fd.get("b_hayaza_no", ""), "إجمالي_فدان_المشتري": fd.get("b_total_f",0), "إجمالي_قيراط_المشتري": fd.get("b_total_k",0), "إجمالي_سهم_المشتري": format_sahm(fd.get("b_total_s",0.0)),
        "is_heirs_s": fd.get("is_heirs_s", False), "is_heirs_b": fd.get("is_heirs_b", False)
    }

def generate_sale_zip(fd):
    context = build_sale_context(fd)
    zip_buffer = BytesIO()
    sale_folder = os.path.join("templates", "sale")
    seller_name = shorten_name(context.get("اسم_البائع", "بائع"))
    buyer_name = shorten_name(context.get("اسم_المشتري", "مشتري"))
    if not seller_name: seller_name = "بائع"
    if not buyer_name: buyer_name = "مشتري"

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        backup_str = json.dumps(fd, ensure_ascii=False, indent=4)
        zip_file.writestr("backup_data.json", backup_str)
        if os.path.exists(sale_folder):
            files = [f for f in os.listdir(sale_folder) if f.endswith('.docx') and not f.startswith('~')]
            for file_name in files:
                try:
                    doc = DocxTemplate(os.path.join(sale_folder, file_name))
                    doc.render(context)
                    doc_buffer = BytesIO()
                    doc.save(doc_buffer)
                    name_only, ext = os.path.splitext(file_name)
                    new_file_name = f"{name_only}_{buyer_name}_مشتراه_من_{seller_name}{ext}"
                    zip_file.writestr(new_file_name, doc_buffer.getvalue())
                except Exception as e: st.error(f"خطأ في قالب البيع {file_name}: {e}")
    return zip_buffer.getvalue()

def generate_kesma_zip(kd):
    zip_buffer = BytesIO()
    main_folder = os.path.join("templates", "kesma_main")
    indiv_folder = os.path.join("templates", "kesma_indiv")
    mora_name = shorten_name(kd.get("moraث", "المورث"))
    all_heirs = []
    main_partitioners = []
    
    for p in kd["partitioners"]:
        if not p.get("name"): continue
        all_heirs.append({"اسم_المتقاسم": p["name"], "رقم_قومي": p["nat_id"], "عنوان": p["address"]})
        if p.get("total_f", 0) > 0 or p.get("total_k", 0) > 0 or float(p.get("total_s", 0)) > 0:
            main_partitioners.append({
                "اسم_المتقاسم": p["name"], "رقم_قومي": p["nat_id"], "عنوان": p["address"],
                "إجمالي_فدان": p["total_f"], "إجمالي_قيراط": p["total_k"], "إجمالي_سهم": format_sahm(p["total_s"]),
                "lands": process_kesma_lands(p.get("lands", []), p.get("total_f",0), p.get("total_k",0), p.get("total_s",0.0))
            })
            
    main_context = {
        "اسم_المورث": mora_name, "رقم_حيازة_المورث": kd.get("hayaza_no", ""), 
        "تاريخ_العقد": format_custom_date(kd.get("c_date"), "full"), "تاريخ_العقد_رقمي": format_custom_date(kd.get("c_date"), "short"),
        "رقم_قضية_الوراثة": kd.get("morath_case_num", ""), "سنة_قضية_الوراثة": kd.get("morath_year", ""), 
        "تاريخ_جلسة_الوراثة": format_custom_date(kd.get("morath_date"), "full"),
        "إجمالي_التركة_فدان": kd.get("total_f",0), "إجمالي_التركة_قيراط": kd.get("total_k",0), "إجمالي_التركة_سهم": format_sahm(kd.get("total_s",0.0)),
        "main_lands": process_kesma_lands(kd.get("main_lands", []), kd.get("total_f",0), kd.get("total_k",0), kd.get("total_s",0.0)),
        "كل_الورثة": all_heirs, "المتقاسمين": main_partitioners
    }
    
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        backup_str = json.dumps(kd, ensure_ascii=False, indent=4)
        zip_file.writestr("backup_data.json", backup_str)
        if os.path.exists(main_folder):
            for file_name in [f for f in os.listdir(main_folder) if f.endswith('.docx') and not f.startswith('~')]:
                try:
                    doc = DocxTemplate(os.path.join(main_folder, file_name))
                    doc.render(main_context)
                    doc_buffer = BytesIO()
                    doc.save(doc_buffer)
                    zip_file.writestr(f"عقد_مجمع_ورثة_{mora_name}_{file_name}", doc_buffer.getvalue())
                except Exception as e: st.error(f"خطأ في القالب المجمع {file_name}: {e}")
                
        if os.path.exists(indiv_folder):
            indiv_files = [f for f in os.listdir(indiv_folder) if f.endswith('.docx') and not f.startswith('~')]
            for p in kd["partitioners"]:
                if not p.get("name") or (p.get("total_f", 0) == 0 and p.get("total_k", 0) == 0 and p.get("total_s", 0) == 0): continue
                indiv_context = {
                    **main_context,
                    "اسم_المتقاسم": p.get("name",""), "رقم_قومي_المتقاسم": p.get("nat_id",""), "عنوان_المتقاسم": p.get("address",""), "مهنة_المتقاسم": p.get("job",""), "سن_المتقاسم": p.get("age", ""),
                    "تاريخ_إصدار_بطاقة_المتقاسم": format_custom_date(p.get("nat_id_date"), "my"),
                    "رقم_حيازة_المتقاسم": p.get("hayaza_no", ""), "إجمالي_فدان_المتقاسم": p.get("prev_f", 0), "إجمالي_قيراط_المتقاسم": p.get("prev_k", 0), "إجمالي_سهم_المتقاسم": format_sahm(p.get("prev_s", 0.0)),
                    "مساحة_الاختصاص_فدان": p.get("total_f",0), "مساحة_الاختصاص_قيراط": p.get("total_k",0), "مساحة_الاختصاص_سهم": format_sahm(p.get("total_s",0.0)),
                    "مساحة_الاختصاص_حروف": p.get("total_txt", ""),
                    "lands": process_kesma_lands(p.get("lands", []), p.get("total_f",0), p.get("total_k",0), p.get("total_s",0.0))
                }
                for file_name in indiv_files:
                    try:
                        doc = DocxTemplate(os.path.join(indiv_folder, file_name))
                        doc.render(indiv_context)
                        doc_buffer = BytesIO()
                        doc.save(doc_buffer)
                        clean_name = shorten_name(p.get('name', 'مجهول'), limit=3)
                        zip_file.writestr(f"مستندات_{clean_name}/{clean_name}_{file_name}", doc_buffer.getvalue())
                    except Exception as e: st.error(f"خطأ في القالب الفردي {file_name}: {e}")
    return zip_buffer.getvalue()

# ==========================================
# 6. القائمة الجانبية (Sidebar) مع الأنيميشن
# ==========================================
SIDEBAR_HTML = """
<div style='text-align:center;padding:20px 16px 18px;border-bottom:1px solid rgba(201,168,76,0.15);margin-bottom:16px;position:relative;overflow:hidden;'>
    <div style='position:absolute;top:-30px;right:-30px;width:100px;height:100px;border-radius:50%;border:1px solid rgba(201,168,76,0.08);animation:spinSlow 25s linear infinite;'></div>
    <div style='position:relative;z-index:1;'>
        <div class='continuous-wave' style='font-size:44px;margin-bottom:4px;filter:drop-shadow(0 0 12px rgba(201,168,76,0.4));'>⚖️</div>
        <div style='direction:ltr;display:flex;justify-content:center;align-items:baseline;gap:4px;'>
            <div style='font-size:30px;font-weight:900;display:flex;gap:1px;letter-spacing:1px;'>
                <span class='letter-b'>B</span>
                <span class='letter-a1'>A</span>
                <span class='letter-y'>Y</span>
                <span class='letter-a2'>A</span>
            </div>
            <span class='fade-in-scale' style='font-size:14px;font-weight:600;color:#c9a84c;letter-spacing:2px;'>Legal</span>
        </div>
        <div style='height:1px;background:linear-gradient(90deg,transparent,rgba(201,168,76,0.4),transparent);margin:8px auto;width:80%;'></div>
        <div style='font-size:10px;color:rgba(200,230,210,0.5);letter-spacing:2px;'>N A S R I Y A</div>
    </div>
</div>
"""
st.sidebar.markdown(SIDEBAR_HTML, unsafe_allow_html=True)

menu = ["🏠 الرئيسية", "📝 منظومة عقود البيع", "🤝 منظومة القسمة الرضائية", "📖 سجل 2 خدمات", "🚨 سجل المحاضر", "🧮 حاسبة الأراضي", "⚖️ حاسبة المواريث", "📂 أرشيف العقود", "🖨️ إدارة المستندات (فردي)", "🔄 الاسترجاع من ملف (Backup)", "⚙️ إعدادات الأمان"]

if "active_menu" not in st.session_state:
    st.session_state.active_menu = "🏠 الرئيسية"
    
choice = st.sidebar.radio("", menu, key="active_menu")

st.sidebar.markdown("""
<div style='margin-top:8px;padding-top:12px;border-top:1px solid rgba(201,168,76,0.15);'></div>
""", unsafe_allow_html=True)
if st.sidebar.button("🚪 تسجيل الخروج", type="primary", use_container_width=True):
    st.session_state.logged_in = False
    st.rerun()
st.sidebar.markdown("""
<div style='text-align:center;margin-top:12px;font-size:9px;color:rgba(200,220,210,0.35);letter-spacing:1px;'>
BAYA Legal · Nasriya
</div>
""", unsafe_allow_html=True)

# ==========================================
# 7. واجهات البرنامج الرئيسية
# ==========================================
if choice == "🏠 الرئيسية":
    home_page.show_page()

elif choice == "🔄 الاسترجاع من ملف (Backup)":
    st.title("🔄 استرجاع معاملة مفقودة من ملف الطوارئ")
    st.info("💡 طريقة الاستخدام: قم بفك الضغط عن ملف الـ ZIP الخاص بالمعاملة القديمة، وارفع ملف `backup_data.json` الموجود بداخله هنا لاستعادة كافة البيانات فوراً.")
    uploaded_file = st.file_uploader("اختر ملف النسخة الاحتياطية (backup_data.json)", type=['json'])
    if uploaded_file is not None:
        try:
            file_content = uploaded_file.read().decode("utf-8")
            loaded_data = json.loads(file_content)
            doc_type = loaded_data.get("doc_type")
            if not doc_type: doc_type = "kesma" if "partitioners" in loaded_data or "moraث" in loaded_data else "sale"
            st.success(f"✅ تم قراءة الملف بنجاح. نوع المعاملة: {'عقد بيع' if doc_type == 'sale' else 'قسمة رضائية'}")
            if st.button("🚀 استرجاع البيانات والانتقال للتعديل", type="primary", use_container_width=True):
                st.session_state.current_archive_id = None 
                st.session_state.loaded_doc_type = doc_type
                if doc_type == "kesma": st.session_state.kesma_data = loaded_data; st.session_state.active_menu = "🤝 منظومة القسمة الرضائية"
                else: st.session_state.sale_data = loaded_data; st.session_state.active_menu = "📝 منظومة عقود البيع"
                st.rerun()
        except Exception as e: st.error(f"❌ حدث خطأ في قراءة الملف: تأكد أنه ملف backup_data.json سليم.")

elif choice == "🧮 حاسبة الأراضي":
    spacer1, main_col, spacer2 = st.columns([1, 2, 1])
    with main_col:
        st.markdown("<h3 style='text-align: center; color: #1a2c42;'>🧮 حاسبة مساحات الأراضي</h3>", unsafe_allow_html=True)
        st.markdown("---")
        calc_op = st.radio("نوع العملية:", ["➕ جمع", "➖ طرح"], horizontal=True)
        st.markdown("<b>🌾 المساحة الأولى:</b>", unsafe_allow_html=True)
        c_s1, c_k1, c_f1 = st.columns(3)
        with c_f1: val_f1 = st.number_input("فدان", min_value=0, step=1, key="cf1")
        with c_k1: val_k1 = st.number_input("قيراط", min_value=0, max_value=23, step=1, key="ck1")
        with c_s1: val_s1 = st.number_input("سهم", min_value=0.0, max_value=23.99, step=0.5, key="cs1")
        st.markdown("<b>🌾 المساحة الثانية:</b>", unsafe_allow_html=True)
        c_s2, c_k2, c_f2 = st.columns(3)
        with c_f2: val_f2 = st.number_input("فدان", min_value=0, step=1, key="cf2")
        with c_k2: val_k2 = st.number_input("قيراط", min_value=0, max_value=23, step=1, key="ck2")
        with c_s2: val_s2 = st.number_input("سهم", min_value=0.0, max_value=23.99, step=0.5, key="cs2")
        st.write("")
        if st.button("🧮 احسب الناتج", use_container_width=True, type="primary"):
            tot1 = (val_f1 * 24 * 24) + (val_k1 * 24) + val_s1
            tot2 = (val_f2 * 24 * 24) + (val_k2 * 24) + val_s2
            res = tot1 + tot2 if "جمع" in calc_op else tot1 - tot2
            if res < 0: st.error("⚠️ المساحة المطروحة أكبر من المساحة الأساسية!")
            else:
                f_res = int(res // (24 * 24))
                k_res = int((res % (24 * 24)) // 24)
                s_res = format_sahm(round(res % 24, 2))
                st.markdown("<div style='text-align: center; color: green; font-weight: bold;'>النتيجة الصافية</div>", unsafe_allow_html=True)
                st.markdown(f"""
                <div class="calc-result-container">
                    <div class="calc-box"><div class="calc-top">ف</div><div class="calc-bottom">{f_res}</div></div>
                    <div class="calc-box"><div class="calc-top">ط</div><div class="calc-bottom">{k_res}</div></div>
                    <div class="calc-box"><div class="calc-top">س</div><div class="calc-bottom">{s_res}</div></div>
                </div>
                """, unsafe_allow_html=True)

elif choice == "⚖️ حاسبة المواريث":
    spacer1, main_col, spacer2 = st.columns([1, 2, 1])
    with main_col:
        st.markdown("<h3 style='text-align: center; color: #1a2c42;'>⚖️ حاسبة المواريث</h3>", unsafe_allow_html=True)
        st.markdown("---")
        st.markdown("<b>🌾 مساحة التركة:</b>", unsafe_allow_html=True)
        c_s, c_k, c_f = st.columns(3)
        with c_f: area_f = st.number_input("فدان ", min_value=0, step=1, key="ih_f")
        with c_k: area_k = st.number_input("قيراط ", min_value=0, max_value=23, step=1, key="ih_k")
        with c_s: area_s = st.number_input("سهم ", min_value=0.0, max_value=23.99, step=0.01, format="%.2f", key="ih_s")
        st.markdown("<b>👥 بيانات الورثة:</b>", unsafe_allow_html=True)
        w_c1, w_c2, w_c3 = st.columns(3)
        with w_c1: has_wife = st.checkbox("يوجد زوجة")
        with w_c2: has_father = st.checkbox("يوجد أب")
        with w_c3: has_mother = st.checkbox("يوجد أم")
        c_c1, c_c2 = st.columns(2)
        with c_c1: sons_count = st.number_input("عدد الأبناء (الذكور)", min_value=0, step=1)
        with c_c2: daugh_count = st.number_input("عدد البنات", min_value=0, step=1)
        st.write("")
        if st.button("⚖️ تقسيم التركة", type="primary", use_container_width=True):
            if area_f == 0 and area_k == 0 and area_s == 0: st.error("⚠️ يرجى إدخال مساحة التركة أولاً.")
            elif not (has_wife or has_father or has_mother or sons_count > 0 or daugh_count > 0): st.error("⚠️ يرجى تحديد الورثة.")
            else:
                results = inheritance_calc.calculate_shares(area_f, area_k, area_s, has_wife, has_father, has_mother, sons_count, daugh_count)
                st.markdown("---")
                names_ar = {'wife': 'نصيب الزوجة', 'father': 'نصيب الأب', 'mother': 'نصيب الأم', 'son': 'نصيب الابن الواحد', 'daughter': 'نصيب البنت الواحدة'}
                for key, data in results.items():
                    if key in names_ar:
                        st.markdown(f"<div style='text-align: center; color: #1a2c42; font-weight: bold; margin-top: 10px;'>{names_ar[key]}</div>", unsafe_allow_html=True)
                        st.markdown(f"""
                        <div class="calc-result-container">
                            <div class="calc-box"><div class="calc-top">ف</div><div class="calc-bottom">{data['f']}</div></div>
                            <div class="calc-box"><div class="calc-top">ط</div><div class="calc-bottom">{data['q']}</div></div>
                            <div class="calc-box"><div class="calc-top">س</div><div class="calc-bottom">{data['s']}</div></div>
                        </div>
                        """, unsafe_allow_html=True)

elif choice == "📝 منظومة عقود البيع":
    if st.session_state.current_archive_id is not None and st.session_state.get('loaded_doc_type') != 'sale': st.session_state.current_archive_id = None
    col_title, col_btn = st.columns([3, 1])
    with col_title: st.title("📄 بيانات عقد البيع")
    with col_btn:
        st.write("") 
        if st.button("🆕 معاملة جديدة", type="secondary", use_container_width=True): reset_form(); st.rerun()

    fd = st.session_state.sale_data
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="premium-header">👥 الطرف الأول (البائع)</div>', unsafe_allow_html=True)
        fd["is_heirs_s"] = st.checkbox("الطرف الأول ورثة؟", value=fd.get("is_heirs_s", False))
        if fd["is_heirs_s"]: 
            fd["moraث_s"] = st.text_input("اسم المورث", value=fd.get("moraث_s", ""))
            wc1, wc2, wc3 = st.columns(3)
            with wc1: fd["s_morath_case_num"] = st.text_input("رقم قضية الوراثة", value=fd.get("s_morath_case_num", ""))
            with wc2: fd["s_morath_year"] = st.text_input("لسنة", value=fd.get("s_morath_year", ""))
            with wc3: fd["s_morath_date"] = st.date_input("تاريخ جلسة الحكم", value=parse_date_safe(fd.get("s_morath_date")), key="s_m_date").isoformat()
        for i, s in enumerate(fd["sellers"]):
            with st.expander(f"👤 بيانات البائع رقم {i+1}: {s.get('name','')}", expanded=True):
                s["name"] = st.text_input(f"الاسم", value=s.get("name", ""), key=f"s_name_{i}")
                c1, c2 = st.columns(2)
                with c1: s["id"] = st.text_input(f"الرقم القومي", value=s.get("id", ""), key=f"s_id_{i}")
                with c2: s["job"] = st.text_input(f"المهنة", value=s.get("job", ""), key=f"s_job_{i}")
                calc_s_age = get_age_from_id(s.get("id", ""))
                c3, c4 = st.columns(2)
                with c3: s["age"] = st.text_input("السن", value=calc_s_age if calc_s_age else s.get("age", ""), key=f"s_age_{i}")
                with c4: s["id_date"] = st.date_input("تاريخ إصدار البطاقة", value=parse_date_safe(s.get("id_date")), key=f"s_date_{i}").isoformat()
                s["address"] = st.text_input(f"العنوان", value=s.get("address", ""), key=f"s_addr_{i}")
                if len(fd["sellers"]) > 1:
                    st.markdown("<div class='delete-btn'>", unsafe_allow_html=True)
                    if st.button(f"🗑️ حذف البائع {i+1}", key=f"del_s_{i}", use_container_width=True): fd["sellers"].pop(i); st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)
        if st.button("➕ أضف بائع آخر", use_container_width=True): fd["sellers"].append({"name": "", "id": "", "address": "", "id_date": today_iso, "job": "", "age": ""}); st.rerun()
        fd["ayloula"] = st.text_area("طريقة أيلولة الملكية للبائع", value=fd.get("ayloula", ""))
        st.markdown('<div class="info-header">🌾 بيانات الحيازة الإجمالية للبائع</div>', unsafe_allow_html=True)
        fd["s_hayaza_no"] = st.text_input("رقم حيازة البائع", value=fd.get("s_hayaza_no", ""))
        hc_s, hc_k, hc_f = st.columns(3)
        with hc_s: fd["s_total_s"] = st.number_input("سهم إجمالي", min_value=0.0, max_value=23.99, step=0.5, value=float(fd.get("s_total_s",0.0)), key="st_s")
        with hc_k: fd["s_total_k"] = st.number_input("قيراط إجمالي", min_value=0, max_value=23, step=1, value=int(fd.get("s_total_k",0)), key="st_k")
        with hc_f: fd["s_total_f"] = st.number_input("فدان إجمالي", min_value=0, step=1, value=int(fd.get("s_total_f",0)), key="st_f")

    with col2:
        st.markdown('<div class="premium-header">👥 الطرف الثاني (المشتري)</div>', unsafe_allow_html=True)
        fd["is_heirs_b"] = st.checkbox("الطرف الثاني ورثة؟", value=fd.get("is_heirs_b", False))
        if fd["is_heirs_b"]: 
            fd["moraث_b"] = st.text_input("اسم مورث الطرف الثاني", value=fd.get("moraث_b", ""))
            wc1, wc2, wc3 = st.columns(3)
            with wc1: fd["b_morath_case_num"] = st.text_input("رقم قضية الوراثة", value=fd.get("b_morath_case_num", ""), key="b_mc")
            with wc2: fd["b_morath_year"] = st.text_input("لسنة", value=fd.get("b_morath_year", ""), key="b_my")
            with wc3: fd["b_morath_date"] = st.date_input("تاريخ جلسة الحكم", value=parse_date_safe(fd.get("b_morath_date")), key="b_m_date").isoformat()
        for i, b in enumerate(fd["buyers"]):
            with st.expander(f"👤 بيانات المشتري رقم {i+1}: {b.get('name','')}", expanded=True):
                b["name"] = st.text_input(f"الاسم ", value=b.get("name", ""), key=f"b_name_{i}")
                c5, c6 = st.columns(2)
                with c5: b["id"] = st.text_input(f"الرقم القومي ", value=b.get("id", ""), key=f"b_id_{i}")
                with c6: b["job"] = st.text_input(f"المهنة ", value=b.get("job", ""), key=f"b_job_{i}")
                calc_b_age = get_age_from_id(b.get("id", ""))
                c7, c8 = st.columns(2)
                with c7: b["age"] = st.text_input("السن", value=calc_b_age if calc_b_age else b.get("age", ""), key=f"b_age_{i}")
                with c8: b["id_date"] = st.date_input("تاريخ الإصدار ", value=parse_date_safe(b.get("id_date")), key=f"b_date_{i}").isoformat()
                b["address"] = st.text_input(f"العنوان ", value=b.get("address", ""), key=f"b_addr_{i}")
                if len(fd["buyers"]) > 1:
                    st.markdown("<div class='delete-btn'>", unsafe_allow_html=True)
                    if st.button(f"🗑️ حذف المشتري {i+1}", key=f"del_b_{i}", use_container_width=True): fd["buyers"].pop(i); st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)
        if st.button("➕ أضف مشتري آخر", use_container_width=True): fd["buyers"].append({"name": "", "id": "", "address": "", "id_date": today_iso, "job": "", "age": ""}); st.rerun()
        st.markdown('<div class="info-header">🌾 بيانات الحيازة السابقة للمشتري (إن وجد)</div>', unsafe_allow_html=True)
        fd["b_hayaza_no"] = st.text_input("رقم حيازة المشتري", value=fd.get("b_hayaza_no", ""))
        bhc_s, bhc_k, bhc_f = st.columns(3)
        with bhc_s: fd["b_total_s"] = st.number_input("سهم ", min_value=0.0, max_value=23.99, step=0.5, value=float(fd.get("b_total_s",0.0)), key="bt_s")
        with bhc_k: fd["b_total_k"] = st.number_input("قيراط ", min_value=0, max_value=23, step=1, value=int(fd.get("b_total_k",0)), key="bt_k")
        with bhc_f: fd["b_total_f"] = st.number_input("فدان ", min_value=0, step=1, value=int(fd.get("b_total_f",0)), key="bt_f")

    st.markdown("---")
    st.markdown('<div class="premium-header">🌾 بيانات المساحة والحدود المبيعة</div>', unsafe_allow_html=True)
    sc_txt, sc_s, sc_k, sc_f = st.columns([3, 1, 1, 1])
    
    # تفقيط مساحة البيع تلقائياً
    auto_sell_txt = tafqeet_area(fd.get("sell_f",0), fd.get("sell_k",0), fd.get("sell_s",0.0))
    
    with sc_txt: fd["sell_txt"] = st.text_input("المساحة بالحروف", value=auto_sell_txt)
    with sc_s: fd["sell_s"] = st.number_input("سهم البيع", min_value=0.0, max_value=23.99, step=0.5, value=float(fd.get("sell_s",0.0)))
    with sc_k: fd["sell_k"] = st.number_input("قيراط البيع", min_value=0, max_value=23, step=1, value=int(fd.get("sell_k",0)))
    with sc_f: fd["sell_f"] = st.number_input("فدان البيع", min_value=0, step=1, value=int(fd.get("sell_f",0)))

    for i, l in enumerate(fd["lands"]):
        col_lbl, col_del = st.columns([5, 1])
        with col_lbl: st.markdown(f'<div style="text-align:right; font-weight:bold; margin-top:10px;">📍 القطعة رقم {i+1}:</div>', unsafe_allow_html=True)
        with col_del:
            if len(fd["lands"]) > 1:
                st.markdown("<div class='delete-btn'>", unsafe_allow_html=True)
                if st.button("❌ حذف القطعة", key=f"del_sell_land_{i}", use_container_width=True): fd["lands"].pop(i); st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
        lc_hod, lc_s, lc_k, lc_f = st.columns([3,1,1,1])
        with lc_hod: l['hod'] = st.text_input("الحوض", value=l.get('hod',""), key=f"lh_{i}")
        with lc_s: l['s'] = st.number_input("سهم", min_value=0.0, max_value=23.99, step=0.5, value=float(l.get('s',0.0)), key=f"ls_{i}")
        with lc_k: l['k'] = st.number_input("قيراط", min_value=0, max_value=23, step=1, value=int(l.get('k',0)), key=f"lk_{i}")
        with lc_f: l['f'] = st.number_input("فدان", min_value=0, step=1, value=int(l.get('f',0)), key=f"lf_{i}")
        bc1, bc2, bc3, bc4 = st.columns(4)
        with bc1: l['n'] = st.text_input("الحد البحري", value=l.get('n',""), key=f"ln_{i}")
        with bc2: l['s_bound'] = st.text_input("الحد القبلي", value=l.get('s_bound',""), key=f"lsb_{i}")
        with bc3: l['e'] = st.text_input("الحد الشرقي", value=l.get('e',""), key=f"le_{i}")
        with bc4: l['w'] = st.text_input("الحد الغربي", value=l.get('w',""), key=f"lw_{i}")
        st.write("---")
    if st.button("➕ أضف قطعة أرض أخرى", use_container_width=True): fd["lands"].append({"f": 0, "k": 0, "s": 0.0, "hod": "", "n": "", "s_bound": "", "e": "", "w": ""}); st.rerun()

    st.markdown('<div class="premium-header">💰 التواريخ والمبالغ</div>', unsafe_allow_html=True)
    tc1, tc2, tc3, tc4 = st.columns(4)
    with tc1: fd["price_num"] = st.text_input("الثمن (أرقام)", value=fd.get("price_num", ""))
    with tc2: fd["price_txt"] = st.text_input("الثمن (حروف)", value=fd.get("price_txt", ""))
    with tc3: fd["c_date"] = st.date_input("تاريخ العقد", value=parse_date_safe(fd.get("c_date")), key="c_date_picker").isoformat()
    with tc4: fd["t_date"] = st.date_input("تاريخ اليوم", value=parse_date_safe(fd.get("t_date")), key="t_date_picker").isoformat()

    st.write("---")
    fd["has_penalty"] = st.checkbox("⚖️ إضافة بند الشرط الجزائي للعقد", value=fd.get("has_penalty", True))
    if fd["has_penalty"]:
        pc1, pc2 = st.columns(2)
        with pc1: fd["penalty_num"] = st.text_input("الشرط الجزائي (أرقام)", value=fd.get("penalty_num", ""))
        with pc2: fd["penalty_txt"] = st.text_input("الشرط الجزائي (حروف)", value=fd.get("penalty_txt", ""))
    else: fd["penalty_num"] = ""; fd["penalty_txt"] = ""

    st.markdown("---")
    st.markdown('<div class="premium-header">⚙️ حفظ واستخراج ملفات البيع</div>', unsafe_allow_html=True)
    raw_json = json.dumps(fd, ensure_ascii=False)
    
    context = build_sale_context(fd)
    prev_seller = shorten_name(context.get("اسم_البائع", "بائع"))
    if not prev_seller: prev_seller = "بائع"
    prev_buyer = shorten_name(context.get("اسم_المشتري", "مشتري"))
    if not prev_buyer: prev_buyer = "مشتري"

    if st.session_state.current_archive_id is None:
        if st.button("💾 حفظ معاملة البيع واستخراج الملفات (ZIP)", type="primary", use_container_width=True):
            save_to_db(fd["c_date"], f"[بيع] {prev_seller}", prev_buyer, raw_json)
            st.session_state.zip_data = generate_sale_zip(fd)
            st.success("✅ تم الحفظ بنجاح وتجهيز الملفات! يمكنك التحميل الآن.")
    else:
        st.info("⚠️ أنت تقوم بتعديل معاملة (بيع) مسترجعة من الأرشيف.")
        if st.button("🔄 تحديث المعاملة واستخراج الملفات الجديدة (ZIP)", type="primary", use_container_width=True):
            update_in_db(st.session_state.current_archive_id, fd["c_date"], f"[بيع] {prev_seller}", prev_buyer, raw_json)
            st.session_state.zip_data = generate_sale_zip(fd)
            st.success("✅ تم التحديث بنجاح وتجهيز الملفات الجديدة!")

    if 'zip_data' in st.session_state:
        st.download_button("📥 تحميل جميع مستندات البيع (ملف ZIP)", data=st.session_state.zip_data, file_name=f"عقد_بيع_{prev_buyer}_مشتراه_من_{prev_seller}.zip", mime="application/zip", type="secondary", use_container_width=True)

elif choice == "🤝 منظومة القسمة الرضائية":
    if st.session_state.current_archive_id is not None and st.session_state.get('loaded_doc_type') != 'kesma': st.session_state.current_archive_id = None
    col_title, col_btn = st.columns([3, 1])
    with col_title: st.title("🤝 بيانات شرط القسمة الرضائي")
    with col_btn:
        st.write("") 
        if st.button("🆕 معاملة جديدة", type="secondary", use_container_width=True): reset_form(); st.rerun()
        
    kd = st.session_state.kesma_data
    if "main_lands" not in kd: kd["main_lands"] = [{"f": 0, "k": 0, "s": 0.0, "hod": "", "n": "", "s_bound": "", "e": "", "w": ""}]
    
    st.markdown("---")
    # جعل قسم المورث بالكامل داخل expander كبير مطوي تلقائياً لراحة العين
    moraث_display_name = kd.get("moraث", "") or "(لم يحدد بعد)"
    with st.expander(f"👨‍🦳 بيانات المورث والتركة وإعلام الوراثة | المورث الحالي: {moraث_display_name}", expanded=False):
        c1, c2, c3 = st.columns(3)
        with c1: kd["moraث"] = st.text_input("اسم المورث", value=kd.get("moraث", ""))
        with c2: kd["hayaza_no"] = st.text_input("رقم حيازة المورث", value=kd.get("hayaza_no", ""))
        with c3: kd["c_date"] = st.date_input("تاريخ شرط القسمة", value=parse_date_safe(kd.get("c_date")), key="k_date_picker").isoformat()
            
        w1, w2, w3 = st.columns(3)
        with w1: kd["morath_case_num"] = st.text_input("رقم قضية الوراثة", value=kd.get("morath_case_num", ""))
        with w2: kd["morath_year"] = st.text_input("لسنة", value=kd.get("morath_year", ""))
        with w3: kd["morath_date"] = st.date_input("تاريخ جلسة الوراثة", value=parse_date_safe(kd.get("morath_date")), key="m_date_picker").isoformat()
            
        st.markdown('<div style="text-align:right; font-weight:bold;">إجمالي التركة:</div>', unsafe_allow_html=True)
        c4, c5, c6 = st.columns(3)
        with c4: kd["total_s"] = st.number_input("إجمالي التركة (سهم)", min_value=0.0, max_value=23.99, step=0.5, value=float(kd.get("total_s",0.0)))
        with c5: kd["total_k"] = st.number_input("إجمالي التركة (قيراط)", min_value=0, max_value=23, step=1, value=int(kd.get("total_k",0)))
        with c6: kd["total_f"] = st.number_input("إجمالي التركة (فدان)", min_value=0, step=1, value=int(kd.get("total_f",0)))

        st.markdown('<div style="text-align:right; font-weight:bold; margin-top:10px;">📍 تفاصيل قطع أراضي المورث (قبل القسمة):</div>', unsafe_allow_html=True)
        for ml_idx, ml in enumerate(kd["main_lands"]):
            col_lbl, col_del = st.columns([5, 1])
            with col_lbl: st.markdown(f'<div style="text-align:right; font-weight:bold; margin-top:10px;">القطعة {ml_idx+1}:</div>', unsafe_allow_html=True)
            with col_del:
                if len(kd["main_lands"]) > 1:
                    st.markdown("<div class='delete-btn'>", unsafe_allow_html=True)
                    if st.button("❌ حذف القطعة", key=f"del_main_land_{ml_idx}", use_container_width=True): kd["main_lands"].pop(ml_idx); st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)
            l_hod, l_s, l_k, l_f = st.columns([3,1,1,1])
            with l_hod: ml["hod"] = st.text_input("الحوض", value=ml.get("hod",""), key=f"mlh_{ml_idx}")
            with l_s: ml["s"] = st.number_input("سهم", min_value=0.0, max_value=23.99, step=0.5, value=float(ml.get("s",0.0)), key=f"mls_{ml_idx}")
            with l_k: ml["k"] = st.number_input("قيراط", min_value=0, max_value=23, step=1, value=int(ml.get("k",0)), key=f"mlk_{ml_idx}")
            with l_f: ml["f"] = st.number_input("فدان", min_value=0, step=1, value=int(ml.get("f",0)), key=f"mlf_{ml_idx}")
            b1, b2, b3, b4 = st.columns(4)
            with b1: ml["n"] = st.text_input("الحد البحري", value=ml.get("n",""), key=f"mln_{ml_idx}")
            with b2: ml["s_bound"] = st.text_input("الحد القبلي", value=ml.get("s_bound",""), key=f"mlsb_{ml_idx}")
            with b3: ml["e"] = st.text_input("الحد الشرقي", value=ml.get("e",""), key=f"mle_{ml_idx}")
            with b4: ml["w"] = st.text_input("الحد الغربي", value=ml.get("w",""), key=f"mlw_{ml_idx}")
            st.write("---")
        if st.button("➕ إضافة قطعة أرض أخرى للمورث", use_container_width=True): kd["main_lands"].append({"f": 0, "k": 0, "s": 0.0, "hod": "", "n": "", "s_bound": "", "e": "", "w": ""}); st.rerun()

    st.markdown("---")
    # ---------------------------
    # حساب الإجمالي الحي للمساحات الموزعة والتحقق
    # ---------------------------
    # الجمع بيتم من مساحات الاختصاص فقط (total_f, total_k, total_s)
    total_part_sahm = sum((p.get("total_f", 0)*24*24) + (p.get("total_k", 0)*24) + float(p.get("total_s", 0.0)) for p in kd["partitioners"])
    total_inh_sahm = (kd.get("total_f", 0)*24*24) + (kd.get("total_k", 0)*24) + float(kd.get("total_s", 0.0))

    calc_f = int(total_part_sahm // (24*24))
    calc_k = int((total_part_sahm % (24*24)) // 24)
    calc_s = format_sahm(round(total_part_sahm % 24, 2))

    # تصميم العرض في 3 مربعات (ف - ط - س)
    st.markdown(f'''
    <div class="premium-header" style="display: flex !important; justify-content: space-between !important; align-items: center; padding: 8px 20px;">
        <span style="font-size: 20px;">👥 بيانات المتقاسمين (الورثة)</span>
        <div style="display: flex; align-items: center; gap: 15px;">
            <span style="font-size: 15px; color: #1a2c42; font-weight: 800;">إجمالي المساحة الموزعة حالياً:</span>
            <div class="calc-result-container" style="margin: 0 !important; gap: 8px; direction: ltr;">
                <div class="calc-box" style="width: 45px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <div class="calc-top" style="font-size: 14px; padding: 2px 0;">ف</div>
                    <div class="calc-bottom" style="font-size: 16px; padding: 4px 0;">{calc_f}</div>
                </div>
                <div class="calc-box" style="width: 45px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <div class="calc-top" style="font-size: 14px; padding: 2px 0;">ط</div>
                    <div class="calc-bottom" style="font-size: 16px; padding: 4px 0;">{calc_k}</div>
                </div>
                <div class="calc-box" style="width: 45px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <div class="calc-top" style="font-size: 14px; padding: 2px 0;">س</div>
                    <div class="calc-bottom" style="font-size: 16px; padding: 4px 0;">{calc_s}</div>
                </div>
            </div>
        </div>
    </div>
    ''', unsafe_allow_html=True)
    
    # رسائل التحقق (Validation)
    if total_inh_sahm > 0:
        diff = total_inh_sahm - total_part_sahm
        if abs(diff) < 0.01:
            st.success("✅ تطابق ممتاز: المساحات الموزعة مطابقة تماماً لإجمالي التركة.")
        elif diff > 0:
            st.warning(f"⚠️ انتبه: هناك مساحة متبقية لم توزع بعد! (الفرق: {format_sahm(round(diff,2))} سهم)")
        else:
            st.error(f"❌ تحذير أحمر: المساحة الموزعة تخطت التركة الأساسية! (المساحة الزائدة: {format_sahm(round(abs(diff),2))} سهم)")

    # ---------------------------
    # إعدادات الحدود السريعة
    # ---------------------------
    st.markdown('<div class="info-header">📌 إعدادات الحدود السريعة للقطع الجديدة</div>', unsafe_allow_html=True)
    use_fixed_bounds = st.checkbox("تثبيت حدود افتراضية لأي قطعة يتم إضافتها؟", key="use_fb")
    if use_fixed_bounds:
        fb_c1, fb_c2, fb_c3, fb_c4 = st.columns(4)
        with fb_c1: default_n = st.text_input("الحد البحري الموحد", key="def_n")
        with fb_c2: default_s_bound = st.text_input("الحد القبلي الموحد", key="def_s")
        with fb_c3: default_e = st.text_input("الحد الشرقي الموحد", key="def_e")
        with fb_c4: default_w = st.text_input("الحد الغربي الموحد", key="def_w")
    else:
        default_n = default_s_bound = default_e = default_w = ""

    # ---------------------------
    # عرض الورثة مع الألوان والتفقيط
    # ---------------------------
    colors = ["🔵", "🟢", "🟠", "🟣", "🟤", "🔴", "🟡"]
    for p_idx, p in enumerate(kd["partitioners"]):
        color_icon = colors[p_idx % len(colors)]
        with st.expander(f"{color_icon} المتقاسم رقم {p_idx+1}: {p.get('name', '') or '(بدون اسم)'}", expanded=False):
            col_p_title, col_p_del = st.columns([5, 1])
            with col_p_del:
                if len(kd["partitioners"]) > 1:
                    st.markdown("<div class='delete-btn'>", unsafe_allow_html=True)
                    if st.button("❌ حذف الوريث", key=f"del_part_btn_{p_idx}", use_container_width=True): kd["partitioners"].pop(p_idx); st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)
            p_c1, p_c2 = st.columns(2)
            with p_c1: p["name"] = st.text_input("اسم المتقاسم", value=p.get("name",""), key=f"pk_name_{p_idx}")
            with p_c2: p["nat_id"] = st.text_input("الرقم القومي", value=p.get("nat_id",""), key=f"pk_id_{p_idx}")
            p_c3, p_c4, p_c5 = st.columns(3)
            with p_c3: p["job"] = st.text_input("المهنة", value=p.get("job",""), key=f"pk_job_{p_idx}")
            calc_age = get_age_from_id(p.get("nat_id",""))
            with p_c4: p["age"] = st.text_input("السن "+" "*p_idx, value=calc_age if calc_age else p.get("age",""))
            with p_c5: p["nat_id_date"] = st.date_input("تاريخ البطاقة", value=parse_date_safe(p.get("nat_id_date")), key=f"pk_date_{p_idx}").isoformat()
            p["address"] = st.text_input("العنوان", value=p.get("address",""), key=f"pk_add_{p_idx}")
            
            st.markdown('<div class="info-header">🌾 بيانات الحيازة السابقة للمتقاسم (إن وجد)</div>', unsafe_allow_html=True)
            p["hayaza_no"] = st.text_input("رقم الحيازة للمتقاسم", value=p.get("hayaza_no", ""), key=f"ph_no_{p_idx}")
            h1, h2, h3 = st.columns(3)
            with h1: p["prev_s"] = st.number_input("سهم سابق", min_value=0.0, max_value=23.99, step=0.5, value=float(p.get("prev_s",0.0)), key=f"ph_s_{p_idx}")
            with h2: p["prev_k"] = st.number_input("قيراط سابق", min_value=0, max_value=23, step=1, value=int(p.get("prev_k",0)), key=f"ph_k_{p_idx}")
            with h3: p["prev_f"] = st.number_input("فدان سابق", min_value=0, step=1, value=int(p.get("prev_f",0)), key=f"ph_f_{p_idx}")
            
            st.markdown('<div class="info-header" style="background-color: #d1e7dd; border-right-color: #0f5132; color: #0f5132 !important;">✔️ مساحة اختصاص المتقاسم الإجمالية في القسمة</div>', unsafe_allow_html=True)
            a1, a2, a3 = st.columns(3)
            with a1: p["total_s"] = st.number_input("سهم اختصاص", min_value=0.0, max_value=23.99, step=0.5, value=float(p.get("total_s",0.0)), key=f"pt_s_{p_idx}")
            with a2: p["total_k"] = st.number_input("قيراط اختصاص", min_value=0, max_value=23, step=1, value=int(p.get("total_k",0)), key=f"pt_k_{p_idx}")
            with a3: p["total_f"] = st.number_input("فدان اختصاص", min_value=0, step=1, value=int(p.get("total_f",0)), key=f"pt_f_{p_idx}")
            
            # التفقيط الآلي يقرأ من المدخلات ويجهز القيمة للـ text_input
            auto_p_txt = tafqeet_area(p.get("total_f",0), p.get("total_k",0), p.get("total_s",0.0))
            p["total_txt"] = st.text_input("المساحة الإجمالية بالحروف (مكتوبة آلياً ويمكنك تعديلها)", value=auto_p_txt, key=f"pt_txt_{p_idx}")
            
            st.markdown('<div style="text-align:right; font-weight:bold; margin-top:10px;">📍 تفاصيل القطع المخصصة لهذا المتقاسم:</div>', unsafe_allow_html=True)
            for l_idx, l in enumerate(p["lands"]):
                col_lbl, col_del = st.columns([5, 1])
                with col_lbl: st.markdown(f'<div style="text-align:right; font-weight:bold; margin-top:10px;">القطعة {l_idx+1}:</div>', unsafe_allow_html=True)
                with col_del:
                    if len(p["lands"]) > 1:
                        st.markdown("<div class='delete-btn'>", unsafe_allow_html=True)
                        if st.button("❌ حذف القطعة", key=f"del_part_land_{p_idx}_{l_idx}", use_container_width=True): p["lands"].pop(l_idx); st.rerun()
                        st.markdown("</div>", unsafe_allow_html=True)
                l_hod, l_s, l_k, l_f = st.columns([3,1,1,1])
                with l_hod: l["hod"] = st.text_input("الحوض", value=l.get("hod",""), key=f"plh_{p_idx}_{l_idx}")
                with l_s: l["s"] = st.number_input("سهم", min_value=0.0, max_value=23.99, step=0.5, value=float(l.get("s",0.0)), key=f"pls_{p_idx}_{l_idx}")
                with l_k: l["k"] = st.number_input("قيراط", min_value=0, max_value=23, step=1, value=int(l.get("k",0)), key=f"plk_{p_idx}_{l_idx}")
                with l_f: l["f"] = st.number_input("فدان", min_value=0, step=1, value=int(l.get("f",0)), key=f"plf_{p_idx}_{l_idx}")
                b1, b2, b3, b4 = st.columns(4)
                with b1: l["n"] = st.text_input("الحد البحري", value=l.get("n",""), key=f"pln_{p_idx}_{l_idx}")
                with b2: l["s_bound"] = st.text_input("الحد القبلي", value=l.get("s_bound",""), key=f"pls_b_{p_idx}_{l_idx}")
                with b3: l["e"] = st.text_input("الحد الشرقي", value=l.get("e",""), key=f"ple_{p_idx}_{l_idx}")
                with b4: l["w"] = st.text_input("الحد الغربي", value=l.get("w",""), key=f"plw_{p_idx}_{l_idx}")
                st.write("---")
            if st.button(f"➕ إضافة قطعة أخرى لـ {p.get('name','') or 'هذا المتقاسم'}", key=f"add_l_{p_idx}", use_container_width=True): 
                # تطبيق الحدود الموحدة بشكل آلي هنا
                p["lands"].append({"f": 0, "k": 0, "s": 0.0, "hod": "", "n": default_n, "s_bound": default_s_bound, "e": default_e, "w": default_w})
                st.rerun()

    if st.button("➕ إضافة متقاسم جديد (وريث آخر)", type="secondary", use_container_width=True):
        kd["partitioners"].append({"name": "", "nat_id": "", "nat_id_date": today_iso, "address": "", "job": "", "age": "", "hayaza_no": "", "prev_f": 0, "prev_k": 0, "prev_s": 0.0, "total_f": 0, "total_k": 0, "total_s": 0.0, "total_txt": "", "lands": [{"f": 0, "k": 0, "s": 0.0, "hod": "", "n": default_n, "s_bound": default_s_bound, "e": default_e, "w": default_w}]})
        st.rerun()

    st.markdown("---")
    st.markdown('<div class="premium-header">⚙️ حفظ واستخراج ملفات القسمة</div>', unsafe_allow_html=True)
    raw_json = json.dumps(kd, ensure_ascii=False)
    mora_name = shorten_name(kd.get("moraث", "المورث"))
    
    if st.session_state.current_archive_id is None:
        if st.button("💾 حفظ معاملة القسمة واستخراج كل الملفات (مجمع وفردي)", type="primary", use_container_width=True):
            save_to_db(kd["c_date"], f"[قسمة] ورثة {mora_name}", f"عدد المتقاسمين: {len(kd['partitioners'])}", raw_json)
            st.session_state.zip_data = generate_kesma_zip(kd)
            st.success("✅ تم الحفظ بنجاح وتجهيز الملفات! يمكنك التحميل الآن.")
    else:
        st.info("⚠️ أنت تقوم بتعديل معاملة (قسمة) مسترجعة من الأرشيف.")
        if st.button("🔄 تحديث معاملة القسمة واستخراج الملفات الجديدة", type="primary", use_container_width=True):
            update_in_db(st.session_state.current_archive_id, kd["c_date"], f"[قسمة] ورثة {mora_name}", f"عدد المتقاسمين: {len(kd['partitioners'])}", raw_json)
            st.session_state.zip_data = generate_kesma_zip(kd)
            st.success("✅ تم التحديث بنجاح وتجهيز الملفات الجديدة!")

    if 'zip_data' in st.session_state:
        st.download_button("📥 تحميل جميع مستندات القسمة (ملف ZIP)", data=st.session_state.zip_data, file_name=f"ملف_قسمة_ورثة_{mora_name}.zip", mime="application/zip", type="secondary", use_container_width=True)

elif choice == "📂 أرشيف العقود":
    st.title("📂 أرشيف المعاملات المسجلة")
    search_query = st.text_input("🔍 بحث باسم البائع / المورث...")
    st.markdown("---")
    conn = sqlite3.connect('contracts_database.db')
    df = pd.read_sql_query("SELECT id, contract_date, seller_name, buyer_name, raw_data FROM archive ORDER BY id DESC", conn)
    conn.close()
    if search_query: df = df[(df['seller_name'].str.contains(search_query, na=False)) | (df['buyer_name'].str.contains(search_query, na=False))]
    if df.empty: st.info("لا توجد معاملات محفوظة مطابقة للبحث.")
    else:
        for index, row in df.iterrows():
            with st.expander(f"📄 {row['seller_name']} | بتاريخ: {format_custom_date(row['contract_date'])}"):
                st.write(f"**تفاصيل إضافية:** {row['buyer_name']}")
                col_btn_edit, col_btn_del = st.columns(2)
                with col_btn_edit: st.button(f"✏️ استرجاع وتعديل", key=f"edit_{row['id']}", on_click=load_from_archive, args=(row['id'], row['raw_data']), use_container_width=True)
                with col_btn_del:
                    if st.button(f"🗑️ حذف نهائي", key=f"del_arc_{row['id']}", type="primary", use_container_width=True): delete_from_db(row['id']); st.rerun()

elif choice == "🖨️ إدارة المستندات (فردي)":
    st.title("🖨️ طباعة واستخراج المستندات الفردية")
    st.info("💡 ملاحظة: ملفات القسمة يتم استخراجها آلياً دفعة واحدة من صفحة القسمة. هذه الصفحة مخصصة لاستخراج ملف واحد من قوالب (البيع).")
    sale_folder = os.path.join("templates", "sale")
    if os.path.exists(sale_folder):
        files = [f for f in os.listdir(sale_folder) if f.endswith('.docx') and not f.startswith('~')]
        if files:
            selected_file = st.selectbox("اختر المستند المراد طباعته:", files)
            if st.button("⚙️ معالجة وتجهيز المستند المحدد", type="primary", use_container_width=True):
                context = build_sale_context(st.session_state.sale_data)
                try:
                    doc = DocxTemplate(os.path.join(sale_folder, selected_file))
                    doc.render(context)
                    buf = BytesIO()
                    doc.save(buf)
                    st.session_state.ready_file_name = selected_file
                    st.session_state.ready_file_data = buf.getvalue()
                    st.success(f"✅ تم تجهيز المستند ({selected_file}) بنجاح!")
                except Exception as e: st.error(f"حدث خطأ: {e}")
            if 'ready_file_data' in st.session_state and st.session_state.get('ready_file_name') == selected_file:
                context = build_sale_context(st.session_state.sale_data)
                s_name = shorten_name(context.get("اسم_البائع", "بائع"))
                if not s_name: s_name = "بائع"
                b_name = shorten_name(context.get("اسم_المشتري", "مشتري"))
                if not b_name: b_name = "مشتري"
                name_only, ext = os.path.splitext(selected_file)
                indiv_file_name = f"{name_only}_{b_name}_مشتراه_من_{s_name}{ext}"
                c_a, c_b = st.columns(2)
                with c_a: st.download_button(f"📥 تحميل (Word)", data=st.session_state.ready_file_data, file_name=indiv_file_name, use_container_width=True)
                with c_b: st.components.v1.html("""<button onclick="window.print()" style="background-color:#1a2c42;color:white;border:none;padding:10px 20px;font-family:'Cairo';border-radius:5px;cursor:pointer;width:100%;">🖨️ طباعة المستند</button>""", height=50)

elif choice == "⚙️ إعدادات الأمان":
    st.title("⚙️ تغيير بيانات الدخول الخاصة بالبرنامج")
    st.info("💡 يمكنك كتابة رقم هاتفك أو أي اسم تفضله في خانة 'اسم المستخدم'.")
    with st.form("security_settings_form"):
        new_username = st.text_input("اسم المستخدم الجديد (أو رقم التليفون)")
        new_password = st.text_input("كلمة المرور الجديدة", type="password")
        confirm_password = st.text_input("تأكيد كلمة المرور", type="password")
        submit_update = st.form_submit_button("حفظ التعديلات 💾", use_container_width=True)
        if submit_update:
            if not new_username or not new_password: st.error("⚠️ يرجى إدخال البيانات الجديدة.")
            elif new_password != confirm_password: st.error("❌ كلمة المرور غير متطابقة!")
            else:
                update_credentials(new_username, new_password)
                st.success(f"✅ تم تحديث بيانات الدخول بنجاح! اسم المستخدم الجديد هو: {new_username}")

elif choice == "📖 سجل 2 خدمات":
    register_services.show_page()

elif choice == "🚨 سجل المحاضر":
    reports_manager.show_page()
