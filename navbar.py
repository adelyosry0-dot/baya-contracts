import streamlit as st
from datetime import date

# ==========================================
# قائمة الأقسام
# ==========================================
MENU_ITEMS = [
    ("🏠", "الرئيسية",    "🏠 الرئيسية"),
    ("📝", "عقود البيع",  "📝 منظومة عقود البيع"),
    ("🤝", "القسمة",      "🤝 منظومة القسمة الرضائية"),
    ("📖", "سجل 2",       "📖 سجل 2 خدمات"),
    ("🚨", "المحاضر",     "🚨 سجل المحاضر"),
    ("🧮", "الحاسبات",    "🧮 الحاسبات"),
    ("📂", "الأرشيف",     "📂 أرشيف العقود"),
    ("🖨️", "المستندات",  "🖨️ إدارة المستندات (فردي)"),
    ("🔄", "استرجاع",     "🔄 الاسترجاع من ملف (Backup)"),
    ("⚙️", "الإعدادات",  "⚙️ إعدادات الأمان"),
]

DAYS_AR   = ["الاثنين","الثلاثاء","الأربعاء","الخميس","الجمعة","السبت","الأحد"]
MONTHS_AR = {1:"يناير",2:"فبراير",3:"مارس",4:"أبريل",5:"مايو",6:"يونيو",
             7:"يوليو",8:"أغسطس",9:"سبتمبر",10:"أكتوبر",11:"نوفمبر",12:"ديسمبر"}

# ==========================================
# CSS الشامل (تم إرجاع التوسيط المثالي للمستطيلات)
# ==========================================
NAVBAR_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;800;900&display=swap');

/* إخفاء القائمة العلوية وزر Deploy نهائياً */
[data-testid="stHeader"], header[data-testid="stHeader"], .stApp > header, 
[data-testid="stAppDeployButton"], .stAppDeployButton, [data-testid="stToolbar"] {
    display: none !important;
    visibility: hidden !important;
    opacity: 0 !important;
    height: 0 !important;
}

/* مؤشر التحميل */
[data-testid="stStatusWidget"] {
    position: fixed !important; bottom: 30px !important; left: 30px !important;
    top: auto !important; right: auto !important;
    background: rgba(13, 35, 24, 0.95) !important; backdrop-filter: blur(10px) !important;
    border-radius: 12px !important; border: 1px solid rgba(201,168,76,0.5) !important;
    box-shadow: 0 8px 20px rgba(0,0,0,0.3) !important; z-index: 999999 !important;
}
[data-testid="stStatusWidget"] * { color: #f0d98a !important; }

/* محاذاة النصوص */
.stMarkdown, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4, .stMarkdown h5, .stMarkdown p, label {
    text-align: right !important; direction: rtl !important;
}
.hero-brand-name, .hero-brand-sub, .hero-date-box, .hero-stat-n { direction: ltr !important; }

/* مساحة المحتوى الكلية لتوسيع الإحصائيات لأعلى */
.block-container { 
    max-width: 1150px !important; margin: 0 auto !important; padding-top: 8rem !important; 
} 

/* ==============================================
   الشريط الأخضر الثابت (توسيط الأقسام بالمسطرة أفقياً ورأسياً)
   ============================================== */
div[data-testid="stRadio"]:has(div[aria-label="navbar_radio"]) {
    position: fixed !important; top: 0 !important; left: 0 !important; right: 0 !important;
    z-index: 999990 !important;
    background: linear-gradient(135deg, #0a1f14 0%, #1e3d2f 50%, #0d2318 100%) !important;
    padding: 0 !important; /* بدون حواف لضمان التوسيط الدقيق */
    box-shadow: 0 4px 25px rgba(0,0,0,0.4) !important;
    border-bottom: 2px solid rgba(201,168,76,0.6) !important;
    height: 95px !important; /* ارتفاع ثابت لمركزة العناصر داخله */
    display: flex !important; align-items: center !important; justify-content: center !important;
}

div[data-testid="stRadio"]:has(div[aria-label="navbar_radio"]) > label { display: none !important; }

/* حاوية الأقسام في منتصف الشريط تماماً */
div[data-testid="stRadio"]:has(div[aria-label="navbar_radio"]) > div[role="radiogroup"] {
    display: flex !important; flex-direction: row !important;
    justify-content: center !important; 
    align-items: center !important;
    flex-wrap: wrap !important;
    gap: 12px !important; 
    direction: rtl !important;
    width: 100% !important;
    padding: 0 !important; margin: 0 auto !important;
}
div[data-testid="stRadio"]:has(div[aria-label="navbar_radio"]) > div[role="radiogroup"] > label > div:first-child { display: none !important; }

/* تصميم الأقسام (زجاجي شفاف) */
div[data-testid="stRadio"]:has(div[aria-label="navbar_radio"]) > div[role="radiogroup"] > label {
    flex: 0 0 auto !important; width: auto !important;
    background: rgba(255, 255, 255, 0.08) !important; 
    backdrop-filter: blur(12px) !important; -webkit-backdrop-filter: blur(12px) !important;
    border: 1px solid rgba(255, 255, 255, 0.2) !important;
    border-radius: 10px !important; padding: 10px 18px !important;
    cursor: pointer !important; transition: all 0.3s cubic-bezier(0.22, 1, 0.36, 1) !important; 
    margin: 0 !important;
    display: inline-flex !important; align-items: center !important; justify-content: center !important;
}
div[data-testid="stRadio"]:has(div[aria-label="navbar_radio"]) > div[role="radiogroup"] > label p {
    color: rgba(255,255,255,0.85) !important; font-size: 14px !important; font-weight: 600 !important; font-family: 'Cairo' !important; margin: 0 !important;
    transition: all 0.3s !important;
}
div[data-testid="stRadio"]:has(div[aria-label="navbar_radio"]) > div[role="radiogroup"] > label:hover { 
    transform: translateY(-5px) !important; 
    box-shadow: 0 8px 18px rgba(0,0,0,0.3) !important; 
    background: rgba(201, 168, 76, 0.2) !important; 
    border-color: rgba(201, 168, 76, 0.6) !important; 
}
div[data-testid="stRadio"]:has(div[aria-label="navbar_radio"]) > div[role="radiogroup"] > label:hover p { color: #f0d98a !important; }

/* القسم النشط */
div[data-testid="stRadio"]:has(div[aria-label="navbar_radio"]) > div[role="radiogroup"] > label:has(input:checked) {
    background: linear-gradient(90deg, #c9a84c, #f0d98a) !important; 
    border-color: #f0d98a !important; 
    box-shadow: 0 4px 15px rgba(201,168,76,0.4) !important; 
    transform: translateY(-2px) !important;
}
div[data-testid="stRadio"]:has(div[aria-label="navbar_radio"]) > div[role="radiogroup"] > label:has(input:checked) p { 
    color: #1a3328 !important; font-weight: 900 !important; 
}

/* =========================================
   تثبيت الأزرار الجانبية (المظهر والخروج)
   ========================================= */
/* حاوية زر الخروج */
div[data-testid="stVerticalBlock"] > div:has(#logout-marker) + div {
    position: fixed !important;
    top: 26px !important;
    left: 20px !important;
    z-index: 999999 !important;
    width: auto !important;
}
div[data-testid="stVerticalBlock"] > div:has(#logout-marker) + div button {
    background: rgba(220, 53, 69, 0.15) !important;
    backdrop-filter: blur(12px) !important;
    -webkit-backdrop-filter: blur(12px) !important;
    border: 1px solid rgba(220, 53, 69, 0.3) !important;
    border-radius: 10px !important;
    height: 42px !important;
    padding: 0 15px !important;
    transition: all 0.3s ease !important;
}
div[data-testid="stVerticalBlock"] > div:has(#logout-marker) + div button p {
    color: #ffadad !important;
    font-weight: bold !important;
    font-family: 'Cairo', sans-serif !important;
    margin: 0 !important;
}
div[data-testid="stVerticalBlock"] > div:has(#logout-marker) + div button:hover {
    background: rgba(220, 53, 69, 0.3) !important;
    transform: translateY(-3px) !important;
    border-color: rgba(220, 53, 69, 0.5) !important;
}

/* حاوية زر المظهر */
div[data-testid="stVerticalBlock"] > div:has(#theme-marker) + div {
    position: fixed !important;
    top: 26px !important;
    left: 120px !important; 
    z-index: 999999 !important;
    width: auto !important;
}
div[data-testid="stVerticalBlock"] > div:has(#theme-marker) + div button {
    background: rgba(255, 255, 255, 0.08) !important;
    backdrop-filter: blur(12px) !important;
    -webkit-backdrop-filter: blur(12px) !important;
    border: 1px solid rgba(255, 255, 255, 0.2) !important;
    border-radius: 10px !important;
    height: 42px !important;
    padding: 0 15px !important;
    transition: all 0.3s ease !important;
}
div[data-testid="stVerticalBlock"] > div:has(#theme-marker) + div button p {
    color: #fff !important;
    font-weight: bold !important;
    font-family: 'Cairo', sans-serif !important;
    margin: 0 !important;
}
div[data-testid="stVerticalBlock"] > div:has(#theme-marker) + div button:hover {
    background: rgba(255, 255, 255, 0.2) !important;
    transform: translateY(-3px) !important;
    border-color: rgba(255, 255, 255, 0.4) !important;
}

/* اللوجو على اليمين */
.nav-logo-box {
    position: fixed; top: 32px; right: 30px; z-index: 999999 !important; 
    display: flex; align-items: center; gap: 8px; direction: ltr; pointer-events: none;
}
.nav-logo-box .icon { font-size: 28px; }
.nav-logo-box .text {
    font-size: 24px; font-weight: 900; letter-spacing: 2px; font-family: 'Cairo';
    background: linear-gradient(90deg,#c9a84c,#f0d98a,#c9a84c);
    background-size: 200% auto; -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}

/* ==============================================
   الأنيميشن الخاص بالمستطيل الرئيسي
   ============================================== */
@keyframes fadeInScale {
    0% { opacity: 0; transform: translateY(20px) scale(0.95); filter: blur(4px); }
    100% { opacity: 1; transform: translateY(0) scale(1); filter: blur(0); }
}
.fade-in-scale {
    animation: fadeInScale 0.6s cubic-bezier(0.22, 1, 0.36, 1) forwards;
}

/* المستطيل العريض للرئيسية */
.hero-banner {
    display: flex; flex-direction: row; justify-content: space-between; align-items: center;
    background: #ffffff; 
    padding: 35px 30px 20px 30px !important; 
    border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.06);
    border: 1px solid rgba(201,168,76,0.3); border-bottom: 4px solid #c9a84c; 
    margin-top: -15px !important; 
    margin-bottom: 30px; direction: rtl; width: 100%; flex-wrap: wrap; gap: 20px;
}
.hb-right { display: flex; flex-direction: column; align-items: flex-start; }
.hb-middle { display: flex; gap: 15px; flex-grow: 1; justify-content: center; }
.hb-left { flex-shrink: 0; }
.hero-brand-name { font-size: 36px; font-weight: 900; color: #2d5a4e; letter-spacing: 3px; line-height: 1; direction: ltr; }
.hero-brand-sub { font-size: 10px; color: #a09585; letter-spacing: 5px; direction: ltr; margin-top: 5px; font-weight: 700; }
.hero-live-badge { display: inline-flex; align-items: center; gap: 6px; background: #eef6f1; border: 1px solid #c9e8d3; border-radius: 20px; padding: 4px 12px; font-size: 11px; color: #2d5a4e; font-weight: bold; margin-bottom: 12px; }
.hero-live-dot { width: 8px; height: 8px; border-radius: 50%; background: #28a745; }
.hero-date-box { text-align: center; direction: ltr; background: #fdfbf7; padding: 10px 25px; border-radius: 12px; border: 1px solid #eee; }
.hero-date-num { font-size: 34px; font-weight: 900; color: #c9a84c; line-height: 1; }
.hero-date-txt { font-size: 11px; color: #666; margin-top: 4px; font-weight: bold; }
.hero-stat-box { background: #f8f9fa; border: 1px solid #e9ecef; border-radius: 10px; padding: 12px 18px; text-align: center; min-width: 100px; }
.hero-stat-n { font-size: 24px; font-weight: 900; color: #2d5a4e; line-height: 1; }
.hero-stat-n.gr { color: #c9a84c; }
.hero-stat-l { font-size: 10px; color: #6c757d; margin-top: 5px; font-weight: 800; }

@media (max-width:1450px) { 
    .nav-logo-box { display: none; } 
}
</style>
"""

# ==========================================
# CSS الوضع الداكن 
# ==========================================
DARK_MODE_CSS = """
<style>
.stApp, .block-container { background-color: #121418 !important; color: #e0e0e0 !important; }
h1, h2, h3, h4, span, label { color: #f0f2f6 !important; }
p:not(div[data-testid="stRadio"] p):not(button p) { color: #d0d4dc !important; }
.hero-banner, .hero-stat-box, .hero-date-box, div[data-testid="stExpander"] > div { background: #1e2128 !important; border-color: #333945 !important; }
.hero-stat-n { color: #7ecba1 !important; }
.hero-stat-l { color: #a0aab5 !important; }
.hero-brand-name { color: #7ecba1 !important; }
div[data-testid="stVerticalBlock"] > div { background-color: transparent !important; }
.stTextInput input, .stNumberInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] { background-color: #2a2e37 !important; color: #ffffff !important; border-color: #4b5263 !important; }
.stTextInput input:focus, .stNumberInput input:focus, .stTextArea textarea:focus { border-color: #7ecba1 !important; box-shadow: 0 0 8px rgba(126, 203, 161, 0.4) !important; }
table th { background: #262a33 !important; color: #c9a84c !important; border-color: #3d4452 !important; }
table td { color: #d0d4dc !important; border-color: #3d4452 !important; background-color: #1e2128 !important;}
tr:hover td { background-color: #2a2e37 !important; }
.calc-top { background: #262a33 !important; color: #c9a84c !important; }
.calc-bottom { background: #1e2128 !important; color: #f0f2f6 !important; }
.calc-box { border-color: #4b5263 !important; }
</style>
"""

def _get_stats():
    try:
        import sqlite3
        conn = sqlite3.connect('contracts_database.db')
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM archive WHERE seller_name NOT LIKE '[قسمة]%'")
        sales = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM archive WHERE seller_name LIKE '[قسمة]%'")
        kesma = c.fetchone()[0]
        today = date.today()
        m_start = str(today.year)+"-"+str(today.month).zfill(2)+"-01"
        c.execute("SELECT COUNT(*) FROM archive WHERE contract_date >= ?", (m_start,))
        this_month = c.fetchone()[0]
        conn.close()
        return sales, kesma, sales+kesma, this_month
    except:
        return 0, 0, 0, 0

def show(default="🏠 الرئيسية"):
    st.markdown(NAVBAR_CSS, unsafe_allow_html=True)
    
    if 'dark_mode' not in st.session_state:
        st.session_state.dark_mode = False
    
    if st.session_state.dark_mode:
        st.markdown(DARK_MODE_CSS, unsafe_allow_html=True)

    if "active_menu" not in st.session_state:
        st.session_state.active_menu = default

    # ==================================
    # أزرار (الخروج والمظهر) المستقلة
    # ==================================
    st.markdown('<div id="logout-marker" style="display:none;"></div>', unsafe_allow_html=True)
    if st.button("🚪 خروج"):
        st.session_state.logged_in = False
        st.rerun() 
        
    st.markdown('<div id="theme-marker" style="display:none;"></div>', unsafe_allow_html=True)
    theme_lbl = "☀️ فاتح" if st.session_state.dark_mode else "🌗 المظهر"
    if st.button(theme_lbl):
        st.session_state.dark_mode = not st.session_state.dark_mode
        st.rerun()

    # قائمة الأقسام العادية
    labels = [icon+" "+label for icon,label,key in MENU_ITEMS]
    keys   = [key for icon,label,key in MENU_ITEMS]
    
    current_key = st.session_state.get("active_menu", default)
    try:    current_idx = keys.index(current_key)
    except: current_idx = 0

    st.markdown("""
        <div class="nav-logo-box">
            <span class="icon">⚖️</span>
            <span class="text">BAYA</span>
        </div>
    """, unsafe_allow_html=True)

    selected_label = st.radio(
        "navbar_radio",
        labels,
        index=current_idx,
        key="_navbar_radio",
        horizontal=True,
        label_visibility="collapsed"
    )

    selected_idx = labels.index(selected_label)
    new_key = keys[selected_idx]
    
    if new_key != st.session_state.get("active_menu"):
        st.session_state.active_menu = new_key
        st.rerun()

    if st.session_state.active_menu == "🏠 الرئيسية":
        sales, kesma, total, this_month = _get_stats()
        today     = date.today()
        day_name  = DAYS_AR[today.weekday()]
        month_name= MONTHS_AR[today.month]

        st.markdown(f"""
        <div class="hero-banner fade-in-scale">
        <div class="hb-right">
        <div class="hero-live-badge"><div class="hero-live-dot"></div> النظام نشط</div>
        <div class="hero-brand-name">BAYA <span style="color:#c9a84c;">LEGAL</span></div>
        <div class="hero-brand-sub">N A S R I Y A  ·  A G R I C U L T U R E</div>
        </div>
        <div class="hb-middle hero-stats">
        <div class="hero-stat-box"><div class="hero-stat-n">{sales}</div><div class="hero-stat-l">عقود بيع</div></div>
        <div class="hero-stat-box"><div class="hero-stat-n gr">{kesma}</div><div class="hero-stat-l">قسمات</div></div>
        <div class="hero-stat-box"><div class="hero-stat-n">{total}</div><div class="hero-stat-l">إجمالي المعاملات</div></div>
        <div class="hero-stat-box"><div class="hero-stat-n gr">{this_month}</div><div class="hero-stat-l">نشاط هذا الشهر</div></div>
        </div>
        <div class="hb-left hero-date-box">
        <div class="hero-date-num">{today.day}</div>
        <div class="hero-date-txt">{month_name} {today.year}</div>
        <div class="hero-date-txt">{day_name}</div>
        </div>
        </div>
        """, unsafe_allow_html=True)

    return st.session_state.active_menu