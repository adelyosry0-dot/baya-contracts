import streamlit as st
from docxtpl import DocxTemplate
import sqlite3
import pandas as pd
import os
import json
import zipfile
from io import BytesIO
from datetime import date

# ==========================================
# 1. إعدادات الصفحة والتصميم CSS المطور
# ==========================================
st.set_page_config(page_title="BAYA Legal Contracts", layout="wide", page_icon="⚖️")

CSS_STYLE = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;800;900&display=swap');
    
    .stApp { direction: rtl; text-align: right; }
    html, body, p, label, h1, h2, h3, h4, h5, h6, input, textarea, button, .stMarkdown, .stText {
        font-family: 'Cairo', sans-serif !important;
    }

    /* إخفاء زوائد Streamlit */
    [data-testid="stHeader"] { background: transparent !important; height: 0rem !important; }
    .stAppDeployButton, a[href*="github.com"], footer, .viewerBadge_container, [data-testid="stViewerBadge"], [data-testid="InputInstructions"] { 
        display: none !important; visibility: hidden !important; 
    }

    /* تصميم القائمة الجانبية */
    [data-testid="stSidebar"] { 
        background-color: #1a2c42 !important; 
        width: 340px !important; 
        min-width: 340px !important;
    }

    /* زر الطي الجديد - يظهر دائماً في اليمين */
    #sidebar-toggle-btn {
        position: fixed;
        top: 15px;
        right: 15px;
        z-index: 9999999;
        background-color: #d4af37;
        color: #1a2c42;
        border: 2px solid #1a2c42;
        border-radius: 8px;
        padding: 8px 15px;
        font-size: 22px;
        font-weight: 900;
        cursor: pointer;
        box-shadow: 0 4px 15px rgba(0,0,0,0.4);
        transition: all 0.3s ease;
    }
    #sidebar-toggle-btn:hover { background-color: #ffffff; transform: scale(1.1); }

    /* تحسينات التصميم العام */
    .premium-header {
        background: linear-gradient(135deg, #fdfbf7 0%, #fffef9 100%); padding: 12px 20px; border-right: 5px solid #d4af37; border-radius: 8px;
        margin-top: 15px; margin-bottom: 20px; box-shadow: 0 4px 15px rgba(212,175,55,0.15); color: #1a2c42 !important; font-weight: 800; font-size: 22px;
    }
    .info-header { background-color: #e8f0fe; padding: 10px 15px; border-right: 4px solid #1a2c42; border-radius: 5px; color: #1a2c42 !important; font-weight: 600; margin-bottom: 15px; }
    
    /* أنيميشن BAYA */
    @keyframes comeFromLeft { 0% { transform: translateX(-200px); opacity: 0; } 100% { transform: translateX(0); opacity: 1; } }
    @keyframes goldShimmer { 0% { background-position: -200% center; } 100% { background-position: 200% center; } }
    .letter-b, .letter-a1, .letter-y, .letter-a2 {
        display: inline-block; background: linear-gradient(90deg, #d4af37 30%, #fff8dc 50%, #d4af37 70%);
        background-size: 200% auto; -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        animation: comeFromLeft 1s ease forwards, goldShimmer 3s linear infinite;
    }
</style>
"""
st.markdown(CSS_STYLE, unsafe_allow_html=True)

# سكريبت التحكم في الزر (يعمل قبل وبعد تسجيل الدخول)
SIDEBAR_TOGGLE_JS = """
<script>
(function() {
    function addToggleBtn() {
        if (document.getElementById('sidebar-toggle-btn')) return;
        var btn = document.createElement('button');
        btn.id = 'sidebar-toggle-btn';
        btn.innerHTML = '☰ القائمة'; 
        btn.onclick = function() {
            var closeBtn = document.querySelector('[data-testid="stSidebarHeader"] button');
            var openBtn = document.querySelector('[data-testid="collapsedControl"]');
            if (openBtn) { openBtn.click(); } 
            else if (closeBtn) { closeBtn.click(); }
        };
        document.body.appendChild(btn);
    }
    setTimeout(addToggleBtn, 500);
    setInterval(function() { if (!document.getElementById('sidebar-toggle-btn')) addToggleBtn(); }, 1000);
})();
</script>
"""
st.markdown(SIDEBAR_TOGGLE_JS, unsafe_allow_html=True)

# ==========================================
# 2. إنشاء الفولدرات والدوال المساعدة
# ==========================================
folders_to_create = [os.path.join("templates", "sale"), os.path.join("templates", "kesma_main"), os.path.join("templates", "kesma_indiv")]
for folder in folders_to_create:
    if not os.path.exists(folder): os.makedirs(folder)

def get_age_from_id(nat_id):
    if nat_id and len(nat_id) == 14 and nat_id.isdigit():
        century_code = int(nat_id[0])
        year = (1900 if century_code == 2 else 2000) + int(nat_id[1:3])
        month, day = int(nat_id[3:5]), int(nat_id[5:7])
        try:
            birth_date = date(year, month, day)
            today = date.today()
            return str(today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day)))
        except: return ""
    return ""

def init_db():
    conn = sqlite3.connect('contracts_database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS archive (id INTEGER PRIMARY KEY AUTOINCREMENT, contract_date TEXT, seller_name TEXT, buyer_name TEXT, raw_data TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT, password TEXT)''')
    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0] == 0: c.execute("INSERT INTO users (username, password) VALUES ('admin', '12345')")
    conn.commit(); conn.close()

def save_to_db(date_val, seller, buyer, raw_json):
    conn = sqlite3.connect('contracts_database.db'); c = conn.cursor()
    c.execute('INSERT INTO archive (contract_date, seller_name, buyer_name, raw_data) VALUES (?, ?, ?, ?)', (date_val, seller, buyer, raw_json))
    conn.commit(); conn.close()

def update_in_db(record_id, date_val, seller, buyer, raw_json):
    conn = sqlite3.connect('contracts_database.db'); c = conn.cursor()
    c.execute('UPDATE archive SET contract_date=?, seller_name=?, buyer_name=?, raw_data=? WHERE id=?', (date_val, seller, buyer, raw_json, record_id))
    conn.commit(); conn.close()

def delete_from_db(record_id):
    conn = sqlite3.connect('contracts_database.db'); c = conn.cursor()
    c.execute('DELETE FROM archive WHERE id=?', (record_id,))
    conn.commit(); conn.close()

def check_login(username, password):
    conn = sqlite3.connect('contracts_database.db'); c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    user = c.fetchone(); conn.close()
    return user is not None

def update_credentials(new_user, new_pass):
    conn = sqlite3.connect('contracts_database.db'); c = conn.cursor()
    c.execute("UPDATE users SET username=?, password=? WHERE id=1", (new_user, new_pass))
    conn.commit(); conn.close()

def format_sahm(s): return int(s) if s == int(s) else s
def parse_date_safe(d_val):
    if not d_val: return date.today()
    try: return date.fromisoformat(d_val)
    except: return date.today()

def format_custom_date(iso_str, mode="full"):
    if not iso_str: return ""
    try:
        d = date.fromisoformat(iso_str)
        if mode == "my": return f"{d.month}/{d.year}" 
        days_ar = ["الاثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت", "الأحد"]
        return f"{days_ar[d.weekday()]} الموافق {d.day}/{d.month}/{d.year}"
    except: return iso_str

init_db()

# ==========================================
# 3. بوابة الدخول (Login Gate)
# ==========================================
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""<div style='text-align: center; background-color: #1a2c42; padding: 40px; border-radius: 20px; border: 2px solid #d4af37;'>
            <div style='font-size: 60px;'>⚖️</div>
            <div style="font-size: 50px; font-weight: 900; direction: ltr;">
                <span class='letter-b'>B</span><span class='letter-a1'>A</span><span class='letter-y'>Y</span><span class='letter-a2'>A</span>
            </div>
            <h3 style='color: white;'>الجمعية التعاونية الزراعية بالناصرية</h3>
        </div><br>""", unsafe_allow_html=True)
        with st.form("login_form"):
            u = st.text_input("👤 اسم المستخدم")
            p = st.text_input("🔑 كلمة المرور", type="password")
            if st.form_submit_button("تسجيل الدخول 🔓", use_container_width=True):
                if check_login(u, p): st.session_state.logged_in = True; st.rerun()
                else: st.error("❌ بيانات الدخول غير صحيحة")
    st.stop()

# ==========================================
# 4. إدارة الحالة والبيانات الافتراضية
# ==========================================
today_iso = date.today().isoformat()

def get_empty_sale():
    return {
        "doc_type": "sale", "sellers": [{"name": "", "id": "", "address": "", "id_date": today_iso, "job": "", "age": ""}], 
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
    st.session_state.sale_data = get_empty_sale(); st.session_state.kesma_data = get_empty_kesma()
    st.session_state.current_archive_id = None; st.session_state.loaded_doc_type = None
    if 'zip_data' in st.session_state: del st.session_state['zip_data']

if 'sale_data' not in st.session_state: reset_form()

def load_from_archive(record_id, json_str):
    loaded_data = json.loads(json_str); doc_type = loaded_data.get("doc_type")
    if not doc_type: doc_type = "kesma" if "partitioners" in loaded_data else "sale"
    st.session_state.current_archive_id = record_id; st.session_state.loaded_doc_type = doc_type  
    if doc_type == "kesma": st.session_state.kesma_data = loaded_data; st.session_state.active_menu = "🤝 منظومة القسمة الرضائية"
    else: st.session_state.sale_data = loaded_data; st.session_state.active_menu = "📝 منظومة عقود البيع"

# ==========================================
# 5. دوال بناء الوثائق (Sale & Kesma)
# ==========================================
def process_lands(lands, total_f, total_k, total_s):
    processed = []
    ordinals = ["الأولى", "الثانية", "الثالثة", "الرابعة", "الخامسة", "السادسة", "السابعة", "الثامنة", "التاسعة", "العاشرة"]
    for idx, l in enumerate(lands):
        f_val, k_val, s_val = l.get("f",0), l.get("k",0), l.get("s",0.0)
        ord_word = ordinals[idx] if idx < len(ordinals) else str(idx + 1)
        processed.append({"f": f_val, "k": k_val, "s": format_sahm(s_val), "hod": l.get("hod",""), "n": l.get("n",""), "s_bound": l.get("s_bound",""), "e": l.get("e",""), "w": l.get("w",""), "ترتيب": ord_word})
    return processed

def build_sale_context(fd):
    final_seller = f"ورثة المرحوم / {fd['moraث_s']}" if fd.get("is_heirs_s") else (fd["sellers"][0]['name'] if fd["sellers"] else "")
    final_buyer = f"ورثة المرحوم / {fd['moraث_b']}" if fd.get("is_heirs_b") else (fd["buyers"][0]['name'] if fd["buyers"] else "")
    s1 = fd["sellers"][0] if fd["sellers"] else {}; b1 = fd["buyers"][0] if fd["buyers"] else {}
    return {
        "sellers": fd["sellers"], "buyers": fd["buyers"], "اسم_البائع": final_seller, "اسم_المشتري": final_buyer,
        "طريقة_أيلولة_الملكية": fd.get("ayloula", ""), "lands": process_lands(fd.get("lands", []), fd.get("sell_f",0), fd.get("sell_k",0), fd.get("sell_s",0.0)),
        "الثمن_أرقام": fd.get("price_num", ""), "الثمن_حروف": fd.get("price_txt", ""), "تاريخ_العقد": format_custom_date(fd.get("c_date")),
        "مساحة_البيع_فدان": fd.get("sell_f",0), "مساحة_البيع_قيراط": fd.get("sell_k",0), "مساحة_البيع_سهم": format_sahm(fd.get("sell_s",0.0)), "مساحة_البيع_حروف": fd.get("sell_txt", ""),
        "رقم_حيازة_البائع": fd.get("s_hayaza_no", ""), "رقم_حيازة_المشتري": fd.get("b_hayaza_no", ""),
        "الشرط_الجزائي_أرقام": fd.get("penalty_num", ""), "الشرط_الجزائي_حروف": fd.get("penalty_txt", "")
    }

def generate_sale_zip(fd):
    context = build_sale_context(fd); zip_buffer = BytesIO(); sale_folder = os.path.join("templates", "sale")
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr("backup_data.json", json.dumps(fd, ensure_ascii=False, indent=4))
        if os.path.exists(sale_folder):
            for file_name in [f for f in os.listdir(sale_folder) if f.endswith('.docx')]:
                doc = DocxTemplate(os.path.join(sale_folder, file_name)); doc.render(context)
                doc_buf = BytesIO(); doc.save(doc_buf); zip_file.writestr(f"عقد_{file_name}", doc_buf.getvalue())
    return zip_buffer.getvalue()

def generate_kesma_zip(kd):
    zip_buffer = BytesIO(); main_folder = os.path.join("templates", "kesma_main"); indiv_folder = os.path.join("templates", "kesma_indiv")
    mora_name = kd.get("moraث", "المورث")
    main_context = {
        "اسم_المورث": mora_name, "تاريخ_العقد": format_custom_date(kd.get("c_date")),
        "إجمالي_التركة_فدان": kd.get("total_f",0), "إجمالي_التركة_قيراط": kd.get("total_k",0), "إجمالي_التركة_سهم": format_sahm(kd.get("total_s",0.0)),
        "main_lands": process_lands(kd.get("main_lands", []), kd.get("total_f",0), kd.get("total_k",0), kd.get("total_s",0.0))
    }
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr("backup_data.json", json.dumps(kd, ensure_ascii=False, indent=4))
        if os.path.exists(main_folder):
            for file_name in [f for f in os.listdir(main_folder) if f.endswith('.docx')]:
                doc = DocxTemplate(os.path.join(main_folder, file_name)); doc.render(main_context)
                doc_buf = BytesIO(); doc.save(doc_buf); zip_file.writestr(f"مجمع_{file_name}", doc_buf.getvalue())
        if os.path.exists(indiv_folder):
            for p in kd["partitioners"]:
                if not p.get("name"): continue
                indiv_ctx = {**main_context, "اسم_المتقاسم": p["name"], "مساحة_الاختصاص_فدان": p["total_f"], "lands": process_lands(p.get("lands", []), p["total_f"], p["total_k"], p["total_s"])}
                for file_name in [f for f in os.listdir(indiv_folder) if f.endswith('.docx')]:
                    doc = DocxTemplate(os.path.join(indiv_folder, file_name)); doc.render(indiv_ctx)
                    doc_buf = BytesIO(); doc.save(doc_buf); zip_file.writestr(f"{p['name']}_{file_name}", doc_buf.getvalue())
    return zip_buffer.getvalue()

# ==========================================
# 6. القائمة الجانبية (Sidebar)
# ==========================================
st.sidebar.markdown("""<div style='text-align: center; color: white;'>
    <div style='font-size: 50px;'>⚖️</div>
    <h2 style='margin-bottom:0;'>BAYA Legal</h2>
    <p style='color: #d4af37;'>الجمعية التعاونية بالناصرية</p>
</div><hr>""", unsafe_allow_html=True)

menu = ["📝 منظومة عقود البيع", "🤝 منظومة القسمة الرضائية", "🧮 حاسبة الأراضي", "📂 أرشيف العقود", "🔄 استرجاع النسخة الاحتياطية", "⚙️ إعدادات الأمان"]
if 'active_menu' not in st.session_state: st.session_state.active_menu = menu[0]
choice = st.sidebar.radio("اختر الوظيفة:", menu, key="active_menu")

if st.sidebar.button("🚪 تسجيل الخروج", use_container_width=True):
    st.session_state.logged_in = False; st.rerun()

# ==========================================
# 7. واجهات البرنامج الرئيسية
# ==========================================

if choice == "🧮 حاسبة الأراضي":
    st.title("🧮 حاسبة مساحات الأراضي")
    calc_op = st.radio("نوع العملية:", ["➕ جمع", "➖ طرح"], horizontal=True)
    c1, c2, c3 = st.columns(3); f1 = c1.number_input("فدان 1", 0); k1 = c2.number_input("قيراط 1", 0, 23); s1 = c3.number_input("سهم 1", 0.0, 23.9)
    c4, c5, c6 = st.columns(3); f2 = c4.number_input("فدان 2", 0); k2 = c5.number_input("قيراط 2", 0, 23); s2 = c6.number_input("سهم 2", 0.0, 23.9)
    if st.button("احسب الآن", type="primary"):
        t1 = (f1*24*24) + (k1*24) + s1; t2 = (f2*24*24) + (k2*24) + s2
        res = t1 + t2 if "جمع" in calc_op else t1 - t2
        if res < 0: st.error("المساحة المطروحة أكبر!")
        else: st.success(f"الناتج: {int(res//576)} فدان، {int((res%576)//24)} قيراط، {round(res%24, 2)} سهم")

elif choice == "📝 منظومة عقود البيع":
    st.title("📄 بيانات عقد البيع")
    fd = st.session_state.sale_data
    if st.button("🆕 معاملة جديدة"): reset_form(); st.rerun()
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="premium-header">👥 البائع</div>', unsafe_allow_html=True)
        fd["is_heirs_s"] = st.checkbox("البائع ورثة؟", fd.get("is_heirs_s"))
        if fd["is_heirs_s"]: fd["moraث_s"] = st.text_input("اسم المورث", fd.get("moraث_s"))
        for i, s in enumerate(fd["sellers"]):
            s["name"] = st.text_input(f"اسم البائع {i+1}", s.get("name"), key=f"sn_{i}")
    with col2:
        st.markdown('<div class="premium-header">👥 المشتري</div>', unsafe_allow_html=True)
        for i, b in enumerate(fd["buyers"]):
            b["name"] = st.text_input(f"اسم المشتري {i+1}", b.get("name"), key=f"bn_{i}")
            
    st.markdown('<div class="premium-header">🌾 مساحة البيع والحدود</div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns([3,1,1,1])
    fd["sell_txt"] = c1.text_input("المساحة بالحروف", fd.get("sell_txt"))
    fd["sell_f"] = c4.number_input("فدان", 0, value=fd.get("sell_f",0))
    
    if st.button("💾 حفظ واستخراج ZIP", type="primary", use_container_width=True):
        save_to_db(fd["c_date"], f"بيع: {fd['sellers'][0]['name']}", fd['buyers'][0]['name'], json.dumps(fd, ensure_ascii=False))
        st.session_state.zip_data = generate_sale_zip(fd); st.success("تم التجهيز!")
    
    if 'zip_data' in st.session_state:
        st.download_button("📥 تحميل الملفات", st.session_state.zip_data, "sale_docs.zip", "application/zip", use_container_width=True)

elif choice == "🤝 منظومة القسمة الرضائية":
    st.title("🤝 شرط القسمة الرضائي")
    kd = st.session_state.kesma_data
    kd["moraث"] = st.text_input("اسم المورث", kd.get("moraث"))
    # ... (باقي كود القسمة الرضائية بنفس المنطق) ...
    if st.button("💾 حفظ واستخراج ملفات القسمة", type="primary"):
        st.session_state.zip_data = generate_kesma_zip(kd); st.success("جاهز للتحميل!")

elif choice == "📂 أرشيف العقود":
    st.title("📂 أرشيف المعاملات")
    conn = sqlite3.connect('contracts_database.db'); df = pd.read_sql_query("SELECT id, contract_date, seller_name, buyer_name, raw_data FROM archive ORDER BY id DESC", conn); conn.close()
    for idx, row in df.iterrows():
        with st.expander(f"📄 {row['seller_name']} ⬅️ {row['buyer_name']}"):
            if st.button(f"✏️ تعديل المعاملة {row['id']}"): load_from_archive(row['id'], row['raw_data']); st.rerun()

elif choice == "⚙️ إعدادات الأمان":
    st.title("⚙️ تغيير كلمة المرور")
    with st.form("security"):
        u = st.text_input("اسم المستخدم الجديد"); p = st.text_input("كلمة المرور الجديدة", type="password")
        if st.form_submit_button("حفظ"): update_credentials(u, p); st.success("تم التحديث")
