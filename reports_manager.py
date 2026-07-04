import streamlit as st
import sqlite3
import pandas as pd
import os
from register_services import normalize_arabic_name, generate_print_html

def init_db():
    conn = sqlite3.connect('contracts_database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS reports 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  report_no TEXT, name TEXT, normalized_name TEXT, 
                  report_date TEXT, notes TEXT)''')
    conn.commit()
    conn.close()

def sync_reports_to_csv():
    if not os.path.exists("templates"): os.makedirs("templates")
    conn = sqlite3.connect('contracts_database.db')
    df = pd.read_sql_query("SELECT id as 'م', report_no as 'رقم المحضر', name as 'اسم المخالف', report_date as 'التاريخ', notes as 'ملاحظات' FROM reports", conn)
    df.to_csv('templates/سجل_المحاضر_محدث_تلقائيا.csv', index=False, encoding='utf-8-sig')
    conn.close()

def show_page():
    init_db()
    st.markdown("<h2 style='text-align: center; color: #1a2c35;'>🚨 سجل المحاضر والتشريعات (متزامن مع الإكسيل)</h2>", unsafe_allow_html=True)
    st.markdown("---")

    # ==========================================
    # 1. نظام القوالب والاستيراد (يدعم Excel و CSV)
    # ==========================================
    with st.expander("📥 إدارة البيانات والاستيراد من إكسيل"):
        col_temp, col_up = st.columns(2)
        with col_temp:
            df_template = pd.DataFrame(columns=["رقم المحضر", "اسم المخالف", "التاريخ", "ملاحظات"])
            st.download_button("⬇️ تحميل قالب المحاضر فارغ", data=df_template.to_csv(index=False).encode('utf-8-sig'), file_name="قالب_سجل_المحاضر.csv", mime="text/csv", use_container_width=True)
        with col_up:
            uploaded_file = st.file_uploader("📤 ارفع قالب المحاضر بعد ملئه", type=['csv', 'xlsx'])
            if uploaded_file is not None:
                if st.button("🚀 سحب المحاضر للقاعدة", type="primary", use_container_width=True):
                    try:
                        if uploaded_file.name.endswith('.csv'):
                            df = pd.read_csv(uploaded_file)
                        else:
                            df = pd.read_excel(uploaded_file)
                            
                        conn = sqlite3.connect('contracts_database.db')
                        c = conn.cursor()
                        for index, row in df.iterrows():
                            name_val = str(row.get('اسم المخالف', ''))
                            if name_val and name_val.strip() != "nan":
                                c.execute('''INSERT INTO reports (report_no, name, normalized_name, report_date, notes) VALUES (?, ?, ?, ?, ?)''', 
                                          (str(row.get('رقم المحضر', '')), name_val, normalize_arabic_name(name_val), str(row.get('التاريخ', '')), str(row.get('ملاحظات', ''))))
                        conn.commit(); conn.close()
                        sync_reports_to_csv()
                        st.success("✅ تم الحفظ وتحديث شيت الإكسيل التلقائي بنجاح!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ حدث خطأ أثناء القراءة: {e}")

    # ==========================================
    # 2. طباعة السجل
    # ==========================================
    st.markdown("### 🖨️ طباعة سجل المحاضر")
    c_year, c_btn = st.columns([2, 1])
    with c_year: print_year = st.text_input("السنة الزراعية / العام للمحاضر:", value="2025/2026")
    with c_btn:
        st.write("")
        conn = sqlite3.connect('contracts_database.db')
        df_print = pd.read_sql_query("SELECT id as 'م', report_no as 'رقم المحضر', name as 'اسم المخالف', report_date as 'التاريخ', notes as 'ملاحظات' FROM reports", conn)
        conn.close()
        if not df_print.empty:
            html_bytes = generate_print_html(df_print, print_year, "سجل قيد المحاضر والتشريعات")
            st.download_button("🖨️ تحميل السجل للطباعة", data=html_bytes, file_name="سجل_المحاضر_للطباعة.html", mime="text/html", type="primary", use_container_width=True)
        else:
            st.button("🖨️ تحميل السجل للطباعة", disabled=True, use_container_width=True)

    st.markdown("---")

    # ==========================================
    # 3. البحث والإضافة والحذف
    # ==========================================
    search_query = st.text_input("🔍 ابحث باسم المخالف...")
    conn = sqlite3.connect('contracts_database.db')
    if search_query:
        norm_query = normalize_arabic_name(search_query)
        df_search = pd.read_sql_query(f"SELECT id as 'م', report_no as 'رقم المحضر', name as 'اسم المخالف', report_date as 'التاريخ', notes as 'ملاحظات' FROM reports WHERE normalized_name LIKE '%{norm_query}%'", conn)
        if not df_search.empty: st.dataframe(df_search, use_container_width=True, hide_index=True)
        else: st.warning("⚠️ لا توجد نتائج.")

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        with st.expander("➕ إضافة محضر يدوياً"):
            with st.form("add_rep_form", clear_on_submit=True):
                r_no = st.text_input("رقم المحضر")
                r_name = st.text_input("اسم المخالف")
                r_date = st.text_input("التاريخ")
                r_notes = st.text_area("ملاحظات")
                if st.form_submit_button("💾 إضافة"):
                    if r_name:
                        c = conn.cursor()
                        c.execute('''INSERT INTO reports (report_no, name, normalized_name, report_date, notes) VALUES (?, ?, ?, ?, ?)''', (r_no, r_name, normalize_arabic_name(r_name), r_date, r_notes))
                        conn.commit()
                        sync_reports_to_csv()
                        st.success("✅ تم الإضافة وتحديث الإكسيل!"); st.rerun()

    with col2:
        with st.expander("🗑️ حذف محضر"):
            del_id = st.number_input("رقم (م) للحذف", min_value=1, step=1, key="del_rep")
            if st.button("❌ حذف نهائي"):
                c = conn.cursor()
                c.execute("DELETE FROM reports WHERE id=?", (del_id,))
                conn.commit()
                sync_reports_to_csv()
                st.success("✅ تم الحذف وتحديث الإكسيل!"); st.rerun()
    conn.close()