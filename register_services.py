import streamlit as st
import sqlite3
import pandas as pd
import re
import os

def normalize_arabic_name(name):
    if pd.isna(name) or not name: return ""
    name = str(name).strip()
    name = re.sub(r'[أإآ]', 'ا', name)
    name = name.replace('ى', 'ي').replace('ة', 'ه')
    return name

# فلتر ذكي لتحويل الشُرط والمسافات الفاضية إلى أرقام (أصفار)
def safe_num(val, is_float=False):
    if pd.isna(val): return 0.0 if is_float else 0
    val_str = str(val).strip()
    # لو القيمة عبارة عن شرطة أو فاضية نرجع صفر
    if val_str in ['-', 'ــ', '—', '_', '']: return 0.0 if is_float else 0
    try:
        return float(val_str) if is_float else int(float(val_str))
    except ValueError:
        return 0.0 if is_float else 0

def init_db():
    conn = sqlite3.connect('contracts_database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS services_reg 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  hayaza_no TEXT, name TEXT, normalized_name TEXT, 
                  f INTEGER, q INTEGER, s REAL, hod TEXT)''')
    conn.commit()
    conn.close()

def sync_to_csv():
    if not os.path.exists("templates"): os.makedirs("templates")
    try:
        conn = sqlite3.connect('contracts_database.db')
        df = pd.read_sql_query("SELECT hayaza_no as 'رقم الحيازة', name as 'الاسم', f as 'فدان', q as 'قيراط', s as 'سهم', hod as 'الحوض' FROM services_reg ORDER BY CAST(hayaza_no AS INTEGER) ASC", conn)
        df.to_csv('templates/سجل_2_خدمات_محدث_تلقائيا.csv', index=False, encoding='utf-8-sig')
        conn.close()
    except PermissionError:
        st.warning("⚠️ تم الحفظ في البرنامج، ولكن الإكسيل التلقائي مفتوح حالياً على جهازك، يرجى إغلاقه ليتحدث في المرة القادمة.")
    except Exception as e:
        pass

def generate_print_html(df, year_text, title):
    rows = ""
    for idx, row in df.iterrows():
        rows += "<tr>"
        rows += f"<td>{idx + 1}</td>" 
        for col in df.columns: 
            rows += f"<td>{row[col]}</td>"
        rows += "</tr>"
        
    html = f"""<!DOCTYPE html>
    <html dir="rtl" lang="ar">
    <head>
        <meta charset="UTF-8">
        <title>طباعة {title}</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
            body {{ font-family: 'Cairo', sans-serif; background: #fff; color: #000; font-size: 16px; padding: 20px; }}
            @page {{ margin: 15mm; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
            th, td {{ border: 1px solid #000; padding: 8px; text-align: center; }}
            th {{ background-color: #f4f4f4; font-weight: bold; }}
            thead {{ display: table-header-group; }}
            tr {{ page-break-inside: avoid; }}
            h2 {{ text-align: center; margin-bottom: 5px; }}
            .print-btn {{ display: block; width: 250px; margin: 0 auto 20px auto; padding: 12px; background: #1a2c42; color: #fff; text-align: center; cursor: pointer; border: none; font-size: 18px; border-radius: 5px; font-family: 'Cairo'; font-weight: bold; }}
            @media print {{ .print-btn {{ display: none; }} }}
        </style>
    </head>
    <body>
        <button class="print-btn" onclick="window.print()">🖨️ اضغط هنا لطباعة السجل</button>
        <h2>{title} {year_text}</h2>
        <table>
            <thead>
                <tr>
                    <th>م</th>
                    {''.join([f'<th>{c}</th>' for c in df.columns])}
                </tr>
            </thead>
            <tbody>{rows}</tbody>
        </table>
    </body>
    </html>"""
    return html.encode('utf-8')

def show_page():
    st.markdown("""
    <style>
        .block-container { max-width: 1000px !important; padding-top: 2rem !important; margin: 0 auto; }
        .stTabs [data-baseweb="tab-list"] { gap: 24px; }
        .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; background-color: #f8f9fa; border-radius: 4px 4px 0px 0px; gap: 1px; padding-top: 10px; padding-bottom: 10px; }
        .stTabs [aria-selected="true"] { background-color: #1a2c42 !important; color: white !important; font-weight: bold !important; }
    </style>
    """, unsafe_allow_html=True)

    init_db()
    st.markdown("<h2 style='text-align: center; color: #1a2c42;'>📖 سجل 2 خدمات (إدارة شاملة)</h2>", unsafe_allow_html=True)
    st.markdown("---")

    # ==========================================
    # 1. البحث وعرض قاعدة البيانات
    # ==========================================
    st.markdown("### 🔍 بحث وقاعدة بيانات السجل")
    search_query = st.text_input("ابحث بالاسم عن حائز...")
    conn = sqlite3.connect('contracts_database.db')
    
    if search_query:
        norm_query = normalize_arabic_name(search_query)
        df_search = pd.read_sql_query(f"SELECT hayaza_no as 'رقم الحيازة', name as 'الاسم', f as 'فدان', q as 'قيراط', s as 'سهم', hod as 'الحوض' FROM services_reg WHERE normalized_name LIKE '%{norm_query}%' ORDER BY CAST(hayaza_no AS INTEGER) ASC", conn)
    else:
        df_search = pd.read_sql_query("SELECT hayaza_no as 'رقم الحيازة', name as 'الاسم', f as 'فدان', q as 'قيراط', s as 'سهم', hod as 'الحوض' FROM services_reg ORDER BY CAST(hayaza_no AS INTEGER) ASC", conn)
        
    if not df_search.empty: 
        df_search.index = df_search.index + 1
        st.dataframe(df_search, use_container_width=True)
    else: 
        st.warning("⚠️ لا توجد نتائج.")
    conn.close()

    st.markdown("---")

    # ==========================================
    # 2. إدارة الحائزين
    # ==========================================
    st.markdown("### ⚙️ لوحة إدارة الحائزين")
    tab1, tab2, tab3 = st.tabs(["➕ إضافة حائز جديد", "✏️ تعديل بيانات حائز", "🗑️ حذف حائز"])
    
    with tab1:
        with st.form("add_form", clear_on_submit=True):
            new_hayaza = st.text_input("رقم الحيازة")
            new_name = st.text_input("الاسم")
            c_f, c_q, c_s = st.columns(3)
            with c_f: new_f = st.number_input("فدان", min_value=0, step=1)
            with c_q: new_q = st.number_input("قيراط", min_value=0, max_value=23, step=1)
            with c_s: new_s = st.number_input("سهم", min_value=0.0, max_value=23.99, step=0.5)
            new_hod = st.text_input("الحوض")
            if st.form_submit_button("💾 حفظ", type="primary"):
                if new_name and new_hayaza:
                    conn = sqlite3.connect('contracts_database.db')
                    c = conn.cursor()
                    c.execute('''INSERT INTO services_reg (hayaza_no, name, normalized_name, f, q, s, hod) VALUES (?, ?, ?, ?, ?, ?, ?)''', (new_hayaza, new_name, normalize_arabic_name(new_name), new_f, new_q, new_s, new_hod))
                    conn.commit(); conn.close()
                    sync_to_csv()
                    st.success("✅ تمت الإضافة بنجاح!"); st.rerun()
                else:
                    st.warning("⚠️ يرجى إدخال رقم الحيازة والاسم على الأقل.")

    with tab2:
        edit_target = st.text_input("🔍 أدخل رقم الحيازة للتعديل:", key="edit_search")
        if edit_target:
            conn = sqlite3.connect('contracts_database.db')
            c = conn.cursor()
            c.execute("SELECT * FROM services_reg WHERE hayaza_no=?", (edit_target,))
            res = c.fetchone()
            if res:
                with st.form("edit_form"):
                    e_h = st.text_input("رقم الحيازة", value=res[1])
                    e_n = st.text_input("الاسم", value=res[2])
                    ec_f, ec_q, ec_s = st.columns(3)
                    with ec_f: e_f = st.number_input("فدان", min_value=0, step=1, value=int(res[4]))
                    with ec_q: e_q = st.number_input("قيراط", min_value=0, max_value=23, step=1, value=int(res[5]))
                    with ec_s: e_s = st.number_input("سهم", min_value=0.0, max_value=23.99, step=0.5, value=float(res[6]))
                    e_hod = st.text_input("الحوض", value=res[7])
                    
                    if st.form_submit_button("💾 حفظ التعديلات", type="primary"):
                        c.execute("UPDATE services_reg SET hayaza_no=?, name=?, normalized_name=?, f=?, q=?, s=?, hod=? WHERE id=?", (e_h, e_n, normalize_arabic_name(e_n), e_f, e_q, e_s, e_hod, res[0]))
                        conn.commit(); conn.close()
                        sync_to_csv()
                        st.success("✅ تم التحديث بنجاح!"); st.rerun()
            else:
                st.warning("⚠️ لم يتم العثور على حائز بهذا الرقم.")
                conn.close()

    with tab3:
        del_target = st.text_input("🔍 أدخل رقم الحيازة المراد حذفه:")
        if del_target:
            conn = sqlite3.connect('contracts_database.db')
            c = conn.cursor()
            c.execute("SELECT * FROM services_reg WHERE hayaza_no=?", (del_target,))
            res_del = c.fetchone()
            if res_del:
                st.error(f"هل أنت متأكد من حذف الحائز: {res_del[2]}؟")
                if st.button("❌ نعم، تأكيد الحذف", type="primary"):
                    c.execute("DELETE FROM services_reg WHERE id=?", (res_del[0],))
                    conn.commit(); conn.close()
                    sync_to_csv()
                    st.success("✅ تم الحذف بنجاح!"); st.rerun()
            else:
                st.info("اكتب رقم حيازة صحيح لظهور زر الحذف.")
                conn.close()
            
    st.markdown("---")

    # ==========================================
    # 3. طباعة السجل
    # ==========================================
    st.markdown("### 🖨️ طباعة السجل بالكامل")
    c_year, c_btn = st.columns([2, 1])
    with c_year: print_year = st.text_input("السنة الزراعية / العام:", value="2025/2026")
    with c_btn:
        st.write("")
        conn = sqlite3.connect('contracts_database.db')
        df_print = pd.read_sql_query("SELECT hayaza_no as 'رقم الحيازة', name as 'الاسم', f as 'فدان', q as 'قيراط', s as 'سهم', hod as 'الحوض' FROM services_reg ORDER BY CAST(hayaza_no AS INTEGER) ASC", conn)
        conn.close()
        if not df_print.empty:
            html_bytes = generate_print_html(df_print, print_year, "سجل 2 خدمات زراعة حصر حيازي")
            st.download_button("🖨️ تحميل السجل للطباعة", data=html_bytes, file_name="سجل_2_خدمات_للطباعة.html", mime="text/html", type="primary", use_container_width=True)
        else:
            st.button("🖨️ تحميل السجل للطباعة", disabled=True, use_container_width=True)

    st.markdown("---")

    # ==========================================
    # 4. الاستيراد من الإكسيل (مع الفلتر الذكي للشرط)
    # ==========================================
    with st.expander("📥 الاستيراد من إكسيل (CSV / XLSX)"):
        col_temp, col_up = st.columns(2)
        with col_temp:
            df_template = pd.DataFrame(columns=["رقم الحيازة", "الاسم", "فدان", "قيراط", "سهم", "الحوض"])
            st.download_button("⬇️ تحميل قالب إكسيل فارغ", data=df_template.to_csv(index=False).encode('utf-8-sig'), file_name="قالب_سجل_2_خدمات.csv", mime="text/csv", use_container_width=True)
        with col_up:
            uploaded_file = st.file_uploader("📤 ارفع شيت الإكسيل", type=['csv', 'xlsx'])
            if uploaded_file is not None:
                if st.button("🚀 بدء سحب البيانات", type="primary", use_container_width=True):
                    try:
                        if uploaded_file.name.endswith('.csv'): df = pd.read_csv(uploaded_file)
                        else: df = pd.read_excel(uploaded_file)
                        
                        df.columns = df.columns.str.strip()
                            
                        conn = sqlite3.connect('contracts_database.db')
                        c = conn.cursor()
                        success_count = 0
                        
                        for index, row in df.iterrows():
                            name_val = str(row.get('الاسم', ''))
                            hayaza_val = str(row.get('رقم الحيازة', row.get('رقم', row.get('م', '')))).replace('.0', '')
                            
                            # تطبيق الفلتر الذكي على الأرقام
                            safe_f = safe_num(row.get('فدان', 0))
                            safe_q = safe_num(row.get('قيراط', 0))
                            safe_s = safe_num(row.get('سهم', 0.0), is_float=True)
                            
                            if name_val and name_val.strip() != "nan":
                                c.execute('''INSERT INTO services_reg (hayaza_no, name, normalized_name, f, q, s, hod) VALUES (?, ?, ?, ?, ?, ?, ?)''', 
                                          (hayaza_val, name_val, normalize_arabic_name(name_val), 
                                           safe_f, safe_q, safe_s, str(row.get('الحوض', ''))))
                                success_count += 1
                                
                        conn.commit(); conn.close()
                        sync_to_csv()
                        
                        if success_count > 0:
                            st.success(f"✅ تم استيراد {success_count} اسم بنجاح متضمنة الشُرَط!")
                            st.rerun()
                        else:
                            st.warning("⚠️ الملف تم قراءته، ولكن تأكد من وجود عمود باسم 'الاسم'.")
                            
                    except Exception as e:
                        if "openpyxl" in str(e):
                            st.error("❌ بايثون يحتاج أداة قراءة الإكسيل. افتح الـ Terminal واكتب: pip install openpyxl")
                        else:
                            st.error(f"❌ حدث خطأ أثناء القراءة: {e}")