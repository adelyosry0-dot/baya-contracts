import streamlit as st
from docxtpl import DocxTemplate
import sqlite3
import pandas as pd
import os
import json
import zipfile
from io import BytesIO
from datetime import date, timedelta

import inheritance_calc
import register_services
import reports_manager
import home_page
import navbar
from core.helpers import get_age_from_id, tafqeet_area, tafqeet_money, format_sahm, parse_date_safe, format_custom_date, shorten_name
from core.database import init_db, save_to_db, update_in_db, delete_from_db, check_login, update_credentials

# ==========================================
# 1. إعدادات الصفحة والتصميم CSS
# ==========================================
st.set_page_config(page_title="BAYA Legal Contracts", layout="wide", page_icon="⚖️")

CSS_STYLE = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;800;900&display=swap');

    .stApp { direction: rtl; text-align: right; }
    html, body, p, label, h1, h2, h3, h4, h5, h6, input, textarea, button, .stMarkdown, .stText {
        font-family: 'Cairo', sans-serif !important;
    }
    .stMarkdown p { text-align: right !important; direction: rtl !important; }

    div[data-testid="InputInstructions"] {
        display: none !important;
    }

    @keyframes comeFromLeft  { 0%{transform:translateX(-200px) rotate(-30deg) scale(0.5);opacity:0;filter:blur(8px)} 60%{transform:translateX(15px) rotate(3deg) scale(1.05);opacity:1;filter:blur(0)} 100%{transform:translateX(0) rotate(0) scale(1);opacity:1} }
    @keyframes comeFromTop   { 0%{transform:translateY(-200px) scale(0.4) rotate(20deg);opacity:0;filter:blur(10px)} 55%{transform:translateY(12px) scale(1.08) rotate(-2deg);opacity:1;filter:blur(0)} 100%{transform:translateY(0) scale(1) rotate(0);opacity:1} }
    @keyframes comeFromBottom{ 0%{transform:translateY(200px) scale(0.4) rotate(-20deg);opacity:0;filter:blur(10px)} 55%{transform:translateY(-12px) scale(1.08) rotate(2deg);opacity:1;filter:blur(0)} 100%{transform:translateY(0) scale(1) rotate(0);opacity:1} }
    @keyframes comeFromRight { 0%{transform:translateX(200px) rotate(30deg) scale(0.5);opacity:0;filter:blur(8px)} 60%{transform:translateX(-15px) rotate(-3deg) scale(1.05);opacity:1;filter:blur(0)} 100%{transform:translateX(0) rotate(0) scale(1);opacity:1} }
    @keyframes goldShimmer   { 0%{background-position:-200% center} 100%{background-position:200% center} }
    @keyframes gradientShift { 0%{background-position:0% 50%} 50%{background-position:100% 50%} 100%{background-position:0% 50%} }
    @keyframes shimmerBtn    { 0%{left:-75%;opacity:0} 10%{opacity:1} 50%{left:125%;opacity:1} 51%,100%{left:125%;opacity:0} }

    .letter-b,.letter-a1,.letter-y,.letter-a2 {
        background:linear-gradient(90deg,#c9a84c 30%,#f0d98a 50%,#c9a84c 70%);
        background-size:200% auto; -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text;
    }
    .letter-b  { animation:comeFromLeft   1.1s cubic-bezier(0.34,1.56,0.64,1) forwards,goldShimmer 3s linear 1.8s infinite; display:inline-block; opacity:0; animation-delay:0.2s; }
    .letter-a1 { animation:comeFromTop    1.1s cubic-bezier(0.34,1.56,0.64,1) forwards,goldShimmer 3s linear 2.0s infinite; display:inline-block; opacity:0; animation-delay:0.4s; }
    .letter-y  { animation:comeFromBottom 1.1s cubic-bezier(0.34,1.56,0.64,1) forwards,goldShimmer 3s linear 2.2s infinite; display:inline-block; opacity:0; animation-delay:0.6s; }
    .letter-a2 { animation:comeFromRight  1.1s cubic-bezier(0.34,1.56,0.64,1) forwards,goldShimmer 3s linear 2.4s infinite; display:inline-block; opacity:0; animation-delay:0.8s; }
    .login-animated-bg { background:linear-gradient(-45deg,#0d2318,#1e3d2f,#163026,#0a1f14,#1a3828); background-size:400% 400%; animation:gradientShift 8s ease infinite; }
    .stFormSubmitButton button { position:relative; overflow:hidden; transition:all 0.4s cubic-bezier(0.22,1,0.36,1) !important; }
    .stFormSubmitButton button::after { content:''; position:absolute; top:-50%; left:-75%; width:50%; height:200%; background:linear-gradient(90deg,transparent,rgba(255,255,255,0.3),transparent); transform:skewX(-20deg); animation:shimmerBtn 3s ease-in-out 2s infinite; }

    .stTextInput input:hover,.stNumberInput input:hover,.stTextArea textarea:hover {
        border-color:#c9a84c !important; box-shadow:0 0 8px rgba(201,168,76,0.25) !important; background-color:#fdfbf7 !important;
    }
    .stTextInput input:focus,.stNumberInput input:focus,.stTextArea textarea:focus {
        border-color:#2d5a4e !important; box-shadow:0 0 8px rgba(45,90,78,0.25) !important;
    }
    .delete-btn button { background-color:#ffebee !important; color:#cc0000 !important; border:1px solid #ffcdd2 !important; }
    .delete-btn button:hover { background-color:#ffcdd2 !important; border-color:#cc0000 !important; }

    .premium-header { background:linear-gradient(90deg,#f7f3ee 0%,#ffffff 100%); padding:12px 20px; border-right:5px solid #c9a84c; margin:15px 0 20px; color:#1e3d2f !important; font-weight:800; font-size:22px; display:block !important; text-align:right !important; direction:rtl !important; width:100% !important; transition:transform 0.3s ease; position:relative; overflow:hidden; }
    .premium-header:hover { transform:translateX(-3px); }
    .info-header { background-color:#eef6f1; padding:10px 15px; border-right:4px solid #2d5a4e; border-radius:5px; color:#1e3d2f !important; font-weight:600; margin:15px 0; transition:all 0.3s ease; display:block !important; text-align:right !important; direction:rtl !important; width:100% !important; }
    .info-header:hover { background-color:#ddf0e6; transform:translateX(-2px); }

    div[data-testid="stExpander"]:nth-child(1n) summary { border-right:5px solid #2d5a4e !important; background-color:#f0f7f4 !important; }
    div[data-testid="stExpander"]:nth-child(2n) summary { border-right:5px solid #c9a84c !important; background-color:#fdf8ed !important; }
    div[data-testid="stExpander"]:nth-child(3n) summary { border-right:5px solid #7b9e87 !important; background-color:#f2f7f4 !important; }
    div[data-testid="stExpander"]:nth-child(4n) summary { border-right:5px solid #a0522d !important; background-color:#faf4ef !important; }

    .calc-result-container { display:flex; justify-content:center; gap:15px; margin:15px 0 20px; direction:ltr; }
    .calc-box { background:#fff; border:2px solid #2d5a4e; border-radius:12px; width:70px; display:flex; flex-direction:column; overflow:hidden; box-shadow:0 4px 6px rgba(0,0,0,0.08); }
    .calc-top { background:#2d5a4e; color:#c9a84c; font-weight:900; font-size:22px; text-align:center; padding:5px 0; }
    .calc-bottom { color:#1e3d2f; font-weight:800; font-size:20px; text-align:center; padding:10px 0; background:#f7f3ee; }
    
    .main-card {
        background-color: #ffffff; border-radius: 12px; padding: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border: 1px solid #e0e0e0; transition: all 0.3s ease-in-out; text-align: center; height: 100%;
    }
    .main-card:hover { transform: translateY(-5px); box-shadow: 0 10px 15px rgba(201,168,76,0.2); border-color: #c9a84c; }
    .main-card h3 { color: #1e3d2f !important; font-weight: bold; font-size: 18px; margin-bottom: 5px;}
    .main-card p { color: #666 !important; font-size: 13px; margin:0;}

    .stat-box {
        background-color: #f4f8f6; border-radius: 10px; padding: 15px; text-align: center;
        border: 1px solid #d1e7dd; transition: transform 0.2s ease;
    }
    .stat-box:hover { transform: scale(1.03); }
    .stat-box h2 { color: #2d5a4e !important; margin: 0; font-size: 32px; font-weight: 900;}
    .stat-box p { color: #555 !important; margin: 0; font-size: 14px; font-weight: bold;}

    .badge-sale {
        background-color: #d1e7dd; color: #0f5132 !important; padding: 4px 10px; border-radius: 6px;
        font-weight: 900; font-size: 12px; border: 1px solid #badbcc; display: inline-block;
    }
    .badge-kesma {
        background-color: #fff3cd; color: #856404 !important; padding: 4px 10px; border-radius: 6px;
        font-weight: 900; font-size: 12px; border: 1px solid #ffeeba; display: inline-block;
    }
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

init_db()

# ==========================================
# 3. بوابة الدخول (Login Gate)
# ==========================================
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown("""
<style>
.stApp { background: radial-gradient(circle at center, #163026 0%, #0a1f14 100%) !important; }
.block-container { padding-top: 3rem !important; } 
[data-testid="stForm"] {
    background: rgba(255, 255, 255, 0.03) !important;
    backdrop-filter: blur(15px) !important; -webkit-backdrop-filter: blur(15px) !important;
    border: 1px solid rgba(201, 168, 76, 0.2) !important;
    border-radius: 20px !important; padding: 40px 30px !important;
    box-shadow: 0 20px 50px rgba(0,0,0,0.5), inset 0 0 20px rgba(201,168,76,0.05) !important;
}
[data-testid="stForm"] label { color: rgba(220,240,230,0.9) !important; font-weight: bold !important; font-family: 'Cairo' !important; }
[data-testid="stForm"] input { background: rgba(0, 0, 0, 0.3) !important; border: 1px solid rgba(201, 168, 76, 0.3) !important; color: #fff !important; border-radius: 8px !important; text-align: right !important; }
[data-testid="stFormSubmitButton"] button {
    background: linear-gradient(90deg, #c9a84c, #f0d98a, #c9a84c) !important;
    background-size: 200% auto !important; border: none !important; color: #0a1f14 !important;
    font-weight: 900 !important; font-size: 16px !important; border-radius: 8px !important;
    margin-top: 15px !important; box-shadow: 0 0 20px rgba(201,168,76,0.4) !important; transition: 0.5s !important;
}
</style>
""", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.2, 1]) 
    with col2:
        with st.form("login_form"):
            st.markdown("""
<div style="text-align:center; margin-bottom: 25px;">
<div style="font-size:60px; filter:drop-shadow(0 0 15px rgba(201,168,76,0.6)); margin-bottom:5px;">⚖️</div>
<div style="font-size:48px; font-weight:900; letter-spacing:4px; display:flex; justify-content:center; gap:3px; margin-bottom:10px; direction:ltr;">
<span class="letter-b">B</span><span class="letter-a1">A</span><span class="letter-y">Y</span><span class="letter-a2">A</span>
</div>
<div style="color:#e0e0e0; font-size:15px; font-weight:bold;">الجمعية التعاونية الزراعية بالناصرية</div>
<hr style="border-color: rgba(201,168,76,0.2); margin-top:15px; margin-bottom:10px;">
</div>
""", unsafe_allow_html=True)
            
            username_input = st.text_input("👤 اسم المستخدم (أو رقم الهاتف)")
            password_input = st.text_input("🔑 كلمة المرور", type="password")
            submit_login = st.form_submit_button("تسجيل الدخول 🔓", use_container_width=True)
            
            if submit_login:
                if check_login(username_input, password_input):
                    st.session_state.logged_in = True
                    st.rerun()
                else: st.error("❌ بيانات الدخول غير صحيحة، يرجى المحاولة مرة أخرى.")
    st.stop()

# ==========================================
# 4. إدارة حالة البيانات الافتراضية والمسح
# ==========================================
today_iso = date.today().isoformat()

def get_empty_sale():
    return {
        "doc_type": "sale", 
        "sellers": [{"name": "", "id": "", "address": "", "id_date": today_iso, "job": "", "age": ""}], 
        "buyers": [{"name": "", "id": "", "address": "", "id_date": today_iso, "job": "", "age": ""}], 
        "lands": [{"f": 0, "k": 0, "s": 0.0, "hod": "", "n": "", "s_bound": "", "e": "", "w": ""}],
        "is_heirs_s": False, "moraث_s": "", "s_heirs_address": "", "s_morath_case_num": "", "s_morath_year": "", "s_morath_date": today_iso, "s_hayaza_no": "", "s_total_f": 0, "s_total_k": 0, "s_total_s": 0.0, "ayloula": "",
        "is_heirs_b": False, "moraث_b": "", "b_heirs_address": "", "b_morath_case_num": "", "b_morath_year": "", "b_morath_date": today_iso, "b_hayaza_no": "", "b_total_f": 0, "b_total_k": 0, "b_total_s": 0.0, 
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
    safe_keys = ['logged_in', 'active_menu', 'dark_mode', '_navbar_radio']
    saved_state = {k: st.session_state[k] for k in safe_keys if k in st.session_state}
    
    st.session_state.clear()
    
    for k, v in saved_state.items():
        st.session_state[k] = v
        
    st.session_state.sale_data = get_empty_sale()
    st.session_state.kesma_data = get_empty_kesma()
    st.session_state.current_archive_id = None
    st.session_state.loaded_doc_type = None

if 'sale_data' not in st.session_state:
    st.session_state.sale_data = get_empty_sale()
if 'kesma_data' not in st.session_state:
    st.session_state.kesma_data = get_empty_kesma()
if 'current_archive_id' not in st.session_state:
    st.session_state.current_archive_id = None
if 'loaded_doc_type' not in st.session_state:
    st.session_state.loaded_doc_type = None
def load_from_archive(record_id, json_str):
    loaded_data = json.loads(json_str)
    doc_type = loaded_data.get("doc_type")
    if not doc_type:
        if "partitioners" in loaded_data or "moraث" in loaded_data: doc_type = "kesma"; loaded_data["doc_type"] = "kesma"
        else: doc_type = "sale"; loaded_data["doc_type"] = "sale"
        
    safe_keys = ['logged_in', 'active_menu', 'dark_mode', '_navbar_radio']
    saved_state = {k: st.session_state[k] for k in safe_keys if k in st.session_state}
    
    st.session_state.clear()
    
    for k, v in saved_state.items():
        st.session_state[k] = v

    # السطرين الجداد لتأمين الذاكرة قبل وضع البيانات
    st.session_state.sale_data = get_empty_sale()
    st.session_state.kesma_data = get_empty_kesma()

    if doc_type == "sale":
        for key in ["sellers", "buyers"]:
            if loaded_data.get(key) and isinstance(loaded_data[key][0], str):
                loaded_data[key] = [{"name": n, "id": "", "address": "", "id_date": today_iso, "job": "", "age": ""} for n in loaded_data[key]]
                
    st.session_state.current_archive_id = record_id
    st.session_state.loaded_doc_type = doc_type  
    
    if doc_type == "kesma": 
        st.session_state.kesma_data = loaded_data
        st.session_state.active_menu = "🤝 منظومة القسمة الرضائية"
        if "_navbar_radio" in st.session_state: st.session_state["_navbar_radio"] = "🤝 قسمة"
    else: 
        st.session_state.sale_data = loaded_data
        st.session_state.active_menu = "📝 منظومة عقود البيع"
        if "_navbar_radio" in st.session_state: st.session_state["_navbar_radio"] = "📝 بيع"

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
        else: plot_title = f"القطعة {ordinals[idx] if idx < len(ordinals) else str(idx + 1)}"
        processed.append({
            "f": f_val, "k": k_val, "s": format_sahm(s_val), 
            "hod": l.get("hod",""), "n": l.get("n",""), "s_bound": l.get("s_bound",""), 
            "e": l.get("e",""), "w": l.get("w",""), "اسم_القطعة": plot_title
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
        ordinal_word = ordinals[idx] if idx < len(ordinals) else str(idx + 1)
        processed.append({
            "f": f_val, "k": k_val, "s": format_sahm(s_val), 
            "hod": l.get("hod",""), "n": l.get("n",""), "s_bound": l.get("s_bound",""), 
            "e": l.get("e",""), "w": l.get("w",""), "اسم_القطعة": plot_title,
            "ترتيب": ordinal_word
        })
    return processed

def build_sale_context(fd):
    s1 = fd["sellers"][0] if fd.get("sellers") else {}
    b1 = fd["buyers"][0] if fd.get("buyers") else {}

    # تجهيز البائع
    if fd.get("is_heirs_s"):
        sellers_names = " - ".join([s.get('name', '') for s in fd.get("sellers", []) if s.get('name', '')])
        sellers_ids = " - ".join([s.get('id', '') for s in fd.get("sellers", []) if s.get('id', '')])
        moraث_s = fd.get("moraث_s", "")
        
        # الاسم العادي اللي هيظهر في باقي القوالب
        final_seller = f"ورثة المرحوم / {moraث_s}"
        final_s_address = fd.get("s_heirs_address", "")
        final_s_id = sellers_ids
        
        # صيغة الاستجواب المخصصة في حالة الورثة
        dibaga_seller = f"نحن ورثة المرحوم / {moraث_s} وأسماؤنا: ({sellers_names}) ومقيمون {final_s_address}"
    else:
        final_seller = s1.get('name', '')
        final_s_address = s1.get('address', '')
        final_s_id = s1.get('id', '')
        
        # صيغة الاستجواب المخصصة في حالة الفردي
        s_age = s1.get('age', '')
        s_job = s1.get('job', '')
        dibaga_seller = f"اسمي / {final_seller} – {s_age} عام – {s_job} – ويقيم {final_s_address}"

    # تجهيز المشتري
    if fd.get("is_heirs_b"):
        buyers_names = " - ".join([b.get('name', '') for b in fd.get("buyers", []) if b.get('name', '')])
        buyers_ids = " - ".join([b.get('id', '') for b in fd.get("buyers", []) if b.get('id', '')])
        moraث_b = fd.get("moraث_b", "")
        
        # الاسم العادي
        final_buyer = f"ورثة المرحوم / {moraث_b}"
        final_b_address = fd.get("b_heirs_address", "")
        final_b_id = buyers_ids
        
        # صيغة الاستجواب المخصصة في حالة الورثة
        dibaga_buyer = f"نحن ورثة المرحوم / {moraث_b} وأسماؤنا: ({buyers_names}) ومقيمون {final_b_address}"
    else:
        final_buyer = b1.get('name', '')
        final_b_address = b1.get('address', '')
        final_b_id = b1.get('id', '')
        
        # صيغة الاستجواب المخصصة في حالة الفردي
        b_age = b1.get('age', '')
        b_job = b1.get('job', '')
        dibaga_buyer = f"اسمي / {final_buyer} – {b_age} عام – {b_job} – ويقيم {final_b_address}"

    formatted_sellers = []
    for s in fd.get("sellers", []):
        s_copy = s.copy()
        s_copy["id_date"] = format_custom_date(s.get("id_date"), "my")
        formatted_sellers.append(s_copy)
        
    formatted_buyers = []
    for b in fd.get("buyers", []):
        b_copy = b.copy()
        b_copy["id_date"] = format_custom_date(b.get("id_date"), "my")
        formatted_buyers.append(b_copy)
        
    return {
        "sellers": formatted_sellers, "buyers": formatted_buyers,
        "moraث_s": fd.get("moraث_s", ""),
        "moraث_b": fd.get("moraث_b", ""),
        
        "اسم_البائع": final_seller, 
        "ديباجة_استجواب_البائع": dibaga_seller,
        "رقم_بطاقة_البائع": final_s_id, 
        "عنوان_البائع": final_s_address, 
        "مهنة_البائع": s1.get("job", ""), 
        "سن_البائع": s1.get("age", ""), 
        "تاريخ_إصدار_بطاقة_البائع": format_custom_date(s1.get("id_date"), "my"),
        
        "اسم_المشتري": final_buyer, 
        "ديباجة_استجواب_المشتري": dibaga_buyer,
        "رقم_بطاقة_المشتري": final_b_id, 
        "عنوان_المشتري": final_b_address, 
        "مهنة_المشتري": b1.get("job", ""), 
        "سن_المشتري": b1.get("age", ""), 
        "تاريخ_إصدار_بطاقة_المشتري": format_custom_date(b1.get("id_date"), "my"),
        
        "طريقة_أيلولة_الملكية": fd.get("ayloula", ""), "lands": process_lands(fd.get("lands", []), fd.get("sell_f",0), fd.get("sell_k",0), fd.get("sell_s",0.0)),
        "رقم_قضية_وراثة_البائع": fd.get("s_morath_case_num", ""), "سنة_قضية_وراثة_البائع": fd.get("s_morath_year", ""), "تاريخ_جلسة_وراثة_البائع": format_custom_date(fd.get("s_morath_date"), "full"),
        "رقم_قضية_وراثة_المشتري": fd.get("b_morath_case_num", ""), "سنة_قضية_وراثة_المشتري": fd.get("b_morath_year", ""), "تاريخ_جلسة_وراثة_المشتري": format_custom_date(fd.get("b_morath_date"), "full"),
        "الثمن_أرقام": fd.get("price_num", ""), "الثمن_حروف": fd.get("price_txt", ""), "يوجد_شرط_جزائي": fd.get("has_penalty", True), "الشرط_الجزائي_أرقام": fd.get("penalty_num", ""), "الشرط_الجزائي_حروف": fd.get("penalty_txt", ""),
        "تاريخ_العقد": format_custom_date(fd.get("c_date"), "full"), "تاريخ_العقد_رقمي": format_custom_date(fd.get("c_date"), "short"), 
        "تاريخ_اليوم": format_custom_date(fd.get("c_date"), "full"),
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
# 6. الشريط العلوي وإدارة التوجيه
# ==========================================
choice = navbar.show()

if choice == "🏠 الرئيسية":
    home_page.show_page()

elif choice == "🔄 الاسترجاع من ملف (Backup)":
    st.markdown("<h2 style='text-align: right; color: #1e3d2f; margin-top: -30px;'>🔄 استرجاع معاملة مفقودة</h2>", unsafe_allow_html=True)
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
                if doc_type == "kesma": 
                    st.session_state.kesma_data = loaded_data
                    st.session_state.active_menu = "🤝 منظومة القسمة الرضائية"
                else: 
                    st.session_state.sale_data = loaded_data
                    st.session_state.active_menu = "📝 منظومة عقود البيع"
                st.rerun()
        except Exception as e: st.error(f"❌ حدث خطأ في قراءة الملف: تأكد أنه ملف backup_data.json سليم.")

elif choice == "🧮 الحاسبات":
    _t1, _t2 = st.tabs(["🌾 حاسبة الأراضي المتقدمة", "⚖️ حاسبة المواريث"])
    with _t1:
        spacer1, main_col, spacer2 = st.columns([1, 3, 1])
        with main_col:
            st.markdown("<h4 style='text-align:center;color:#2d5a4e;margin-top:12px'>🌾 حاسبة المساحات المتعددة</h4>", unsafe_allow_html=True)
            st.markdown("---")
            
            c_op, c_num = st.columns(2)
            with c_op: calc_op = st.selectbox("نوع العملية:", ["➕ جمع مساحات", "➖ طرح مساحات"])
            with c_num: num_areas = st.number_input("عدد المساحات المراد حسابها:", min_value=2, max_value=10, value=2, step=1)
            
            st.markdown("---")
            total_sahms = 0
            
            for i in range(num_areas):
                st.markdown(f"<b>🌾 المساحة رقم {i+1}:</b>", unsafe_allow_html=True)
                c_s, c_k, c_f = st.columns(3)
                with c_f: f_val = st.number_input("فدان", min_value=0, step=1, key=f"cf_{i}")
                with c_k: k_val = st.number_input("قيراط", min_value=0, step=1, key=f"ck_{i}")
                with c_s: s_val = st.number_input("سهم", min_value=0.0, step=0.5, key=f"cs_{i}")
                
                current_sahms = (f_val * 24 * 24) + (k_val * 24) + s_val
                
                if "جمع" in calc_op:
                    total_sahms += current_sahms
                else:
                    if i == 0: total_sahms = current_sahms
                    else: total_sahms -= current_sahms
            
            st.write("")
            if st.button("🧮 احسب الناتج النهائي", use_container_width=True, type="primary"):
                if total_sahms < 0: st.error("⚠️ خطأ: المساحة المطروحة أكبر من المساحة الأساسية الأولى!")
                else:
                    f_res = int(total_sahms // (24 * 24))
                    k_res = int((total_sahms % (24 * 24)) // 24)
                    s_res = format_sahm(round(total_sahms % 24, 2))
                    st.markdown("<div style='text-align:center;color:#2d5a4e;font-weight:bold;'>صافي المساحة (آلياً)</div>", unsafe_allow_html=True)
                    st.markdown(f"""
                    <div class="calc-result-container">
                        <div class="calc-box"><div class="calc-top">ف</div><div class="calc-bottom">{f_res}</div></div>
                        <div class="calc-box"><div class="calc-top">ط</div><div class="calc-bottom">{k_res}</div></div>
                        <div class="calc-box"><div class="calc-top">س</div><div class="calc-bottom">{s_res}</div></div>
                    </div>
                    """, unsafe_allow_html=True)
    
    with _t2:
        spacer1, main_col, spacer2 = st.columns([1, 2, 1])
        with main_col:
            st.markdown("<h4 style='text-align:center;color:#2d5a4e;margin-top:12px'>⚖️ حاسبة المواريث</h4>", unsafe_allow_html=True)
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
                            st.markdown("<div style='text-align:center;color:#2d5a4e;font-weight:bold;margin-top:10px;'>" + names_ar[key] + "</div>", unsafe_allow_html=True)
                            st.markdown(f"""
                            <div class="calc-result-container">
                                <div class="calc-box"><div class="calc-top">ف</div><div class="calc-bottom">{data['f']}</div></div>
                                <div class="calc-box"><div class="calc-top">ط</div><div class="calc-bottom">{data['q']}</div></div>
                                <div class="calc-box"><div class="calc-top">س</div><div class="calc-bottom">{data['s']}</div></div>
                            </div>
                            """, unsafe_allow_html=True)
    
elif choice == "📝 منظومة عقود البيع":
    if st.session_state.current_archive_id is not None and st.session_state.get('loaded_doc_type') != 'sale': st.session_state.current_archive_id = None
    
    st.markdown("<h2 style='text-align: right; color: #1e3d2f; margin-top: -30px;'>📄 بيانات عقد البيع</h2>", unsafe_allow_html=True)
    st.markdown("---")

    fd = st.session_state.sale_data
    
    st.markdown('<div class="premium-header">📅 تاريخ تحرير العقد</div>', unsafe_allow_html=True)
    d_col1, d_col2 = st.columns([4, 1])
    with d_col1:
        fd["c_date"] = st.date_input("اختر تاريخ العقد (اضغط لتغييره من لوحة النوتة المنسدلة آلياً)", value=parse_date_safe(fd.get("c_date")), min_value=date(date.today().year - 30, 1, 1), key="c_date_picker_top").isoformat()
        fd["t_date"] = fd["c_date"]
    with d_col2:
        st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
        if st.button("🗑️ مسح الخانات لمعاملة جديدة", type="secondary", use_container_width=True): 
            reset_form()
            st.rerun()

    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="premium-header">👥 الطرف الأول (البائع)</div>', unsafe_allow_html=True)
        fd["is_heirs_s"] = st.checkbox("الطرف الأول ورثة؟", value=fd.get("is_heirs_s", False))
        if fd["is_heirs_s"]: 
            fd["moraث_s"] = st.text_input("اسم المورث", value=fd.get("moraث_s", ""))
            fd["s_heirs_address"] = st.text_input("عنوان إقامة الورثة المجمع", value=fd.get("s_heirs_address", ""))
            wc1, wc2, wc3 = st.columns(3)
            with wc1: fd["s_morath_case_num"] = st.text_input("رقم قضية الوراثة", value=fd.get("s_morath_case_num", ""))
            with wc2: fd["s_morath_year"] = st.text_input("لسنة", value=fd.get("s_morath_year", ""))
            with wc3: fd["s_morath_date"] = st.date_input("تاريخ جلسة الحكم", value=parse_date_safe(fd.get("s_morath_date")), key="s_m_date").isoformat()
        for i, s in enumerate(fd["sellers"]):
            with st.expander(f"👤 بيانات البائع رقم {i+1}: {s.get('name','')}", expanded=True):
                s["name"] = st.text_input(f"الاسم", value=s.get("name", ""), key=f"s_name_{i}")
                c1, c2 = st.columns(2)
                with c1: 
                    s["id"] = st.text_input(f"الرقم القومي", value=s.get("id", ""), key=f"s_id_{i}")
                    calc_s_age = get_age_from_id(s["id"])
                    if calc_s_age and s.get("_last_id") != s["id"]:
                        st.session_state[f"s_age_{i}"] = calc_s_age
                        s["age"] = calc_s_age
                        s["_last_id"] = s["id"]
                with c2: s["job"] = st.text_input(f"المهنة", value=s.get("job", ""), key=f"s_job_{i}")
                
                c3, c4 = st.columns(2)
                with c3: s["age"] = st.text_input("السن", value=s.get("age", ""), key=f"s_age_{i}")
                
                curr_s = s.get("id_date", "")
                try: 
                    d_val = date(int(curr_s[:4]), int(curr_s[5:7]), 1) if len(curr_s) == 7 else parse_date_safe(curr_s)
                except: 
                    d_val = date.today()
                with c4: 
                    s_picker = st.date_input("تاريخ إصدار البطاقة (اختر أي يوم)", value=d_val, min_value=date(1990, 1, 1), key=f"s_date_{i}")
                    s["id_date"] = f"{s_picker.year}/{s_picker.month:02d}"
                    
                s["address"] = st.text_input(f"العنوان", value=s.get("address", ""), key=f"s_addr_{i}")
                if len(fd["sellers"]) > 1:
                    st.markdown("<div class='delete-btn'>", unsafe_allow_html=True)
                    if st.button(f"🗑️ حذف البائع {i+1}", key=f"del_s_{i}", use_container_width=True): fd["sellers"].pop(i); st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)
        if st.button("➕ أضف بائع آخر", use_container_width=True): fd["sellers"].append({"name": "", "id": "", "address": "", "id_date": today_iso, "job": "", "age": ""}); st.rerun()
        fd["ayloula"] = st.text_area("طريقة أيلولة الملكية (إذا كان ورثة: اكتب كيف آلت الأرض للمورث المرحوم)", value=fd.get("ayloula", ""))
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
            fd["b_heirs_address"] = st.text_input("عنوان إقامة الورثة المجمع", value=fd.get("b_heirs_address", ""))
            wc1, wc2, wc3 = st.columns(3)
            with wc1: fd["b_morath_case_num"] = st.text_input("رقم قضية الوراثة", value=fd.get("b_morath_case_num", ""), key="b_mc")
            with wc2: fd["b_morath_year"] = st.text_input("لسنة", value=fd.get("b_morath_year", ""), key="b_my")
            with wc3: fd["b_morath_date"] = st.date_input("تاريخ جلسة الحكم", value=parse_date_safe(fd.get("b_morath_date")), key="b_m_date").isoformat()
        for i, b in enumerate(fd["buyers"]):
            with st.expander(f"👤 بيانات المشتري رقم {i+1}: {b.get('name','')}", expanded=True):
                b["name"] = st.text_input(f"الاسم ", value=b.get("name", ""), key=f"b_name_{i}")
                c5, c6 = st.columns(2)
                with c5: 
                    b["id"] = st.text_input(f"الرقم القومي ", value=b.get("id", ""), key=f"b_id_{i}")
                    calc_b_age = get_age_from_id(b["id"])
                    if calc_b_age and b.get("_last_id") != b["id"]:
                        st.session_state[f"b_age_{i}"] = calc_b_age
                        b["age"] = calc_b_age
                        b["_last_id"] = b["id"]
                with c6: b["job"] = st.text_input(f"المهنة ", value=b.get("job", ""), key=f"b_job_{i}")
                
                c7, c8 = st.columns(2)
                with c7: b["age"] = st.text_input("السن", value=b.get("age", ""), key=f"b_age_{i}")
                
                curr_b = b.get("id_date", "")
                try: 
                    d_val = date(int(curr_b[:4]), int(curr_b[5:7]), 1) if len(curr_b) == 7 else parse_date_safe(curr_b)
                except: 
                    d_val = date.today()
                with c8: 
                    b_picker = st.date_input("تاريخ الإصدار (اختر أي يوم)", value=d_val, min_value=date(1990, 1, 1), key=f"b_date_{i}")
                    b["id_date"] = f"{b_picker.year}/{b_picker.month:02d}"
                    
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

    st.markdown('<div class="premium-header">💰 المبالغ والشرط الجزائي التفصيلي</div>', unsafe_allow_html=True)
    tc1, tc2 = st.columns(2)
    with tc1: 
        fd["price_num"] = st.text_input("الثمن (أرقام)", value=fd.get("price_num", ""))
        auto_price_money_txt = tafqeet_money(fd["price_num"])
    with tc2: 
        curr_p_txt = auto_price_money_txt if fd["price_num"] else fd.get("price_txt", "")
        fd["price_txt"] = st.text_input("الثمن (حروف - يتفقط تلقائياً ويمكنك تعديله)", value=curr_p_txt)

    st.write("---")
    fd["has_penalty"] = st.checkbox("⚖️ إضافة بند الشرط الجزائي للعقد", value=fd.get("has_penalty", True))
    if fd["has_penalty"]:
        pc1, pc2 = st.columns(2)
        with pc1: 
            fd["penalty_num"] = st.text_input("الشرط الجزائي (أرقام)", value=fd.get("penalty_num", ""))
            auto_penalty_money_txt = tafqeet_money(fd["penalty_num"])
        with pc2: 
            curr_pen_txt = auto_penalty_money_txt if fd["penalty_num"] else fd.get("penalty_txt", "")
            fd["penalty_txt"] = st.text_input("الشرط الجزائي (حروف - يتفقط تلقائياً)", value=curr_pen_txt)
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
    
    st.markdown("<h2 style='text-align: right; color: #1e3d2f; margin-top: -30px;'>🤝 بيانات شرط القسمة الرضائي</h2>", unsafe_allow_html=True)
    st.markdown("---")
        
    kd = st.session_state.kesma_data
    if "main_lands" not in kd: kd["main_lands"] = [{"f": 0, "k": 0, "s": 0.0, "hod": "", "n": "", "s_bound": "", "e": "", "w": ""}]
    
    st.markdown('<div class="premium-header">📅 تاريخ تحرير عقد القسمة</div>', unsafe_allow_html=True)
    d_col1, d_col2 = st.columns([4, 1])
    with d_col1:
        kd["c_date"] = st.date_input("اختر تاريخ عقد القسمة (اضغط لتغييره من لوحة النوتة المنسدلة)", value=parse_date_safe(kd.get("c_date")), min_value=date(date.today().year - 30, 1, 1), key="k_date_picker_top").isoformat()
    with d_col2:
        st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
        if st.button("🗑️ مسح الخانات لمعاملة جديدة", type="secondary", use_container_width=True): 
            reset_form()
            st.rerun()

    moraث_display_name = kd.get("moraث", "") or "(لم يحدد بعد)"
    with st.expander(f"👨‍🦳 بيانات المورث والتركة وإعلام الوراثة | المورث الحالي: {moraث_display_name}", expanded=False):
        c1, c2 = st.columns(2)
        with c1: kd["moraث"] = st.text_input("اسم المورث", value=kd.get("moraث", ""))
        with c2: kd["hayaza_no"] = st.text_input("رقم حيازة المورث", value=kd.get("hayaza_no", ""))
            
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
    total_part_sahm = sum((p.get("total_f", 0)*24*24) + (p.get("total_k", 0)*24) + float(p.get("total_s", 0.0)) for p in kd["partitioners"])
    total_inh_sahm = (kd.get("total_f", 0)*24*24) + (kd.get("total_k", 0)*24) + float(kd.get("total_s", 0.0))

    calc_f = int(total_part_sahm // (24*24))
    calc_k = int((total_part_sahm % (24*24)) // 24)
    calc_s = format_sahm(round(total_part_sahm % 24, 2))

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
    
    if total_inh_sahm > 0:
        diff = total_inh_sahm - total_part_sahm
        if abs(diff) < 0.01:
            st.success("✅ تطابق ممتاز: المساحات الموزعة مطابقة تماماً لإجمالي التركة.")
        elif diff > 0:
            st.warning(f"⚠️ انتبه: هناك مساحة متبقية لم توزع بعد! (الفرق: {format_sahm(round(diff,2))} سهم)")
        else:
            st.error(f"❌ تحذير أحمر: المساحة الموزعة تخطت التركة الأساسية! (المساحة الزائدة: {format_sahm(round(abs(diff),2))} سهم)")

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
            with p_c2: 
                p["nat_id"] = st.text_input("الرقم القومي", value=p.get("nat_id",""), key=f"pk_id_{p_idx}")
                calc_age = get_age_from_id(p["nat_id"])
                if calc_age and p.get("_last_id") != p["nat_id"]:
                    st.session_state[f"pk_age_{p_idx}"] = calc_age
                    p["age"] = calc_age
                    p["_last_id"] = p["nat_id"]
                    
            p_c3, p_c4, p_c5 = st.columns(3)
            with p_c3: p["job"] = st.text_input("المهنة", value=p.get("job",""), key=f"pk_job_{p_idx}")
            with p_c4: p["age"] = st.text_input("السن", value=p.get("age",""), key=f"pk_age_{p_idx}")
            
            curr_p = p.get("nat_id_date", "")
            try: 
                d_val = date(int(curr_p[:4]), int(curr_p[5:7]), 1) if len(curr_p) == 7 else parse_date_safe(curr_p)
            except: 
                d_val = date.today()
            with p_c5: 
                p_picker = st.date_input("تاريخ البطاقة (اختر أي يوم)", value=d_val, min_value=date(1990, 1, 1), key=f"pk_date_{p_idx}")
                p["nat_id_date"] = f"{p_picker.year}/{p_picker.month:02d}"
                
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
    st.markdown("<h2 style='text-align: right; color: #1e3d2f; margin-top: -30px;'>📂 أرشيف المعاملات المسجلة</h2>", unsafe_allow_html=True)
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
    st.markdown("<h2 style='text-align: right; color: #1e3d2f; margin-top: -30px;'>🖨️ طباعة واستخراج المستندات الفردية</h2>", unsafe_allow_html=True)
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
    st.markdown("<h2 style='text-align: right; color: #1e3d2f; margin-top: -30px;'>⚙️ تغيير بيانات الدخول الخاصة بالبرنامج</h2>", unsafe_allow_html=True)
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