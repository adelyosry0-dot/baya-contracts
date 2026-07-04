import streamlit as st
import sqlite3
import pandas as pd
import re
import os
from datetime import date

# ==========================================
# 1. القوائم المرجعية
# ==========================================
BASINS_LIST = ["شكري حبيب", "حوض نيازي", "حوض نشأت", "حوض رشيد بهنا", "حوض الزياتين", "حوض الحريري", "حوض 14", "حوض 13", "حوض 12"]

SEASONS_OPTS = ["", "بساتين", "خضر صيفي", "محاصيل حقلية صيفي", "خضر شتوي", "محاصيل شتوية", "أخرى (كتابة يدوية)"]

CROP_MAPPINGS = {
    "بساتين": ["البرتقال", "المانجو", "الجوافة", "النخيل", "الموز", "التفاح", "الخوخ", "المشمش", "البرقوق", "الكمثرى", "القشطة", "الباباظ", "التوت"],
    "خضر صيفي": ["الطماطم", "الخيار", "الكوسة", "الباذنجان", "الفلفل", "البامية", "الملوخية", "الفاصوليا الخضراء", "اللوبيا", "البطيخ", "الكانتالوب والشهد (الشمام)", "البطاطا الحلوة", "الروكا"],
    "محاصيل حقلية صيفي": ["الأرز", "الذرة الشامية", "الذرة الرفيعة", "القطن", "قصب السكر", "فول الصويا", "السمسم", "عباد الشمس", "الفول السوداني", "الذرة السكرية", "الدخن", "البرسيم الحجازي"],
    "خضر شتوي": ["البطاطس", "البصل", "الثوم", "البسلة", "السبانخ", "الخس", "الكرنب", "القرنبيط", "البروكلي", "الجزر", "الفجل", "الجرجير", "السلق", "اللفت", "القلقاس", "الكرفس", "الخبيزة", "البقدونس", "الكزبرة", "الشبت"],
    "محاصيل شتوية": ["القمح", "الشعير", "البرسيم المسقاوي", "الفول البلدي", "بنجر السكر", "الكتان", "الحمص", "العدس", "الحلبة", "الترمس"]
}

# ==========================================
# 2. دوال المعالجة والبحث الذكي وتوحيد الأسماء
# ==========================================
def normalize_arabic_name(name):
    if pd.isna(name) or not name: return ""
    name = str(name).strip()
    name = re.sub(r'[أإآ]', 'ا', name)
    name = name.replace('ى', 'ي').replace('ة', 'ه')
    name = name.replace('عبد ', 'عبد').replace('ابو ', 'ابو')
    name = re.sub(r'\s+', ' ', name)
    return name

def generate_smart_name(name):
    norm = normalize_arabic_name(name)
    words = norm.split()
    return " ".join(words[:4]) if len(words) >= 4 else norm

def unify_crop_name(c):
    if not c: return ""
    c_str = str(c).strip()
    if 'جواف' in c_str: return 'الجوافة'
    if 'مانج' in c_str: return 'المانجو'
    if 'برتقال' in c_str: return 'البرتقال'
    
    c_norm = normalize_arabic_name(c_str)
    c_no_al = c_norm[2:] if c_norm.startswith('ال') else c_norm
    for cat, crops in CROP_MAPPINGS.items():
        for std_crop in crops:
            std_norm = normalize_arabic_name(std_crop)
            std_no_al = std_norm[2:] if std_norm.startswith('ال') else std_norm
            if c_no_al == std_no_al or c_norm == std_norm:
                return std_crop
    return c_str

def safe_num(val, is_float=False):
    if pd.isna(val): return 0.0 if is_float else 0
    val_str = str(val).strip()
    if val_str in ['-', 'ــ', '—', '_', '', 'nan', 'None']: return 0.0 if is_float else 0
    try: return float(val_str) if is_float else int(float(val_str))
    except ValueError: return 0.0 if is_float else 0

def fmt_s(val):
    try: return f"{float(val):.2f}".rstrip('0').rstrip('.')
    except: return "0"

# ==========================================
# 3. تهيئة قاعدة البيانات
# ==========================================
def init_db():
    conn = sqlite3.connect('contracts_database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS services_reg 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  hayaza_no TEXT, hayaza_manzoma TEXT DEFAULT '', national_id TEXT DEFAULT '',
                  name TEXT, normalized_name TEXT, smart_name TEXT, 
                  f INTEGER DEFAULT 0, q INTEGER DEFAULT 0, s REAL DEFAULT 0, hod TEXT DEFAULT '')''')

    c.execute('''CREATE TABLE IF NOT EXISTS farmer_crops 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  hayaza_no TEXT, season TEXT, crop_name TEXT, crop_type TEXT DEFAULT 'محصول',
                  f INTEGER DEFAULT 0, q INTEGER DEFAULT 0, s REAL DEFAULT 0)''')
    try: c.execute("ALTER TABLE services_reg ADD COLUMN rep_name TEXT DEFAULT ''")
    except sqlite3.OperationalError: pass
    conn.commit()
    conn.close()

@st.cache_data
def convert_df_to_csv(df):
    return df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')

# ==========================================
# 4. بناء واجهات الطباعة والتصميم (بدون f-string للهروب من الأخطاء)
# ==========================================
def build_pivot_data(raw_data, main_crops=None):
    records = {}
    found_crops = set()
    for r in raw_data:
        name, hod, h_no, crop, f, q, s = r
        unified_crop = unify_crop_name(crop)
        if h_no not in records: records[h_no] = {'الاسم': name, 'الحوض': hod, 'رقم الحيازة': h_no}
        if unified_crop not in records[h_no]: records[h_no][unified_crop] = {'f': 0, 'q': 0, 's': 0.0}
        records[h_no][unified_crop]['f'] += int(f)
        records[h_no][unified_crop]['q'] += int(q)
        records[h_no][unified_crop]['s'] += float(s)
        found_crops.add(unified_crop)
        
    ordered_crops = []
    if main_crops:
        for mc in main_crops:
            for c in found_crops:
                if mc in c and c not in ordered_crops: ordered_crops.append(c)
        for c in found_crops:
            if c not in ordered_crops: ordered_crops.append(c)
    else: ordered_crops = list(found_crops)
    return records, ordered_crops

def generate_multi_header_html(records, ordered_crops, title):
    if not records: return "<h3>لا توجد بيانات</h3>".encode('utf-8')
    thead = "<tr><th rowspan='2' style='min-width:150px;'>الاسم</th><th rowspan='2'>الحيازة</th><th rowspan='2'>الحوض</th>"
    for c in ordered_crops: thead += f"<th colspan='3'>{c}</th>"
    thead += "</tr><tr>"
    for c in ordered_crops: thead += "<th>س</th><th>ط</th><th>ف</th>"
    thead += "</tr>"
    tbody = ""
    for h_no, data in records.items():
        tbody += "<tr>"
        tbody += f"<td>{data['الاسم']}</td><td>{h_no}</td><td>{data['الحوض']}</td>"
        for c in ordered_crops:
            if c in data: tbody += f"<td>{fmt_s(data[c]['s'])}</td><td>{data[c]['q']}</td><td>{data[c]['f']}</td>"
            else: tbody += "<td></td><td></td><td></td>"
        tbody += "</tr>"
        
    html = (
        '<!DOCTYPE html>\n<html dir="rtl" lang="ar"><head><meta charset="UTF-8"><title>' + str(title) + '</title>\n'
        '<style>\n@import url("https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap");\n'
        'body { font-family:"Cairo",sans-serif; background:#fff; color:#000; padding:20px; direction:rtl; }\n'
        'table { width:100%; border-collapse:collapse; margin-top:15px; font-size:13px; text-align:center; page-break-inside: auto; }\n'
        'tr { page-break-inside: avoid; page-break-after: auto; }\n'
        'th,td { border:1px solid #000; padding:6px; font-weight:bold; }\n'
        'th { background:#2d5a4e; color:#c9a84c; -webkit-print-color-adjust: exact; print-color-adjust: exact; }\n'
        'h2 { text-align:center; color:#2d5a4e; margin-bottom: 10px; }\n'
        '.btn { display:block; width:200px; margin:0 auto 15px; padding:10px; background:#2d5a4e; color:#fff; text-align:center; cursor:pointer; border:none; font-size:16px; border-radius:5px; font-family:"Cairo"; }\n'
        '@media print { \n    .btn { display:none !important; } \n    @page { size: A4 landscape; margin: 0; }\n    body { padding: 15mm; }\n}\n'
        '</style></head><body>\n<button class="btn" onclick="window.print()">🖨️ طباعة المستند الحالي</button>\n'
        '<h2>' + str(title) + '</h2>\n<table><thead>' + thead + '</thead><tbody>' + tbody + '</tbody></table>\n</body></html>'
    )
    return html.encode('utf-8')

def generate_scrollable_multi_header_table(records, ordered_crops):
    if not records: return "<div style='text-align:center; padding:20px;'>لا توجد بيانات لعرضها</div>"
    thead = "<tr><th rowspan='2' style='padding: 12px; border: 1px solid #3d6b5e; min-width:150px;'>الاسم</th><th rowspan='2' style='padding: 12px; border: 1px solid #3d6b5e;'>الحيازة</th><th rowspan='2' style='padding: 12px; border: 1px solid #3d6b5e;'>الحوض</th>"
    for c in ordered_crops: thead += f"<th colspan='3' style='padding: 12px; border: 1px solid #3d6b5e; text-align:center;'>{c}</th>"
    thead += "</tr><tr>"
    for c in ordered_crops: thead += "<th style='padding: 8px; border: 1px solid #3d6b5e; text-align:center;'>س</th><th style='padding: 8px; border: 1px solid #3d6b5e; text-align:center;'>ط</th><th style='padding: 8px; border: 1px solid #3d6b5e; text-align:center;'>ف</th>"
    thead += "</tr>"
    tbody = ""
    for h_no, data in records.items():
        tbody += "<tr style='background-color:#fff; transition:0.2s;' onmouseover=\"this.style.backgroundColor='#eef6f1'\" onmouseout=\"this.style.backgroundColor='#fff'\">"
        tbody += f"<td style='padding:10px; border:1px solid #ddd; color:#222;'>{data['الاسم']}</td><td style='padding:10px; border:1px solid #ddd; color:#222;'>{h_no}</td><td style='padding:10px; border:1px solid #ddd; color:#222;'>{data['الحوض']}</td>"
        for c in ordered_crops:
            if c in data: tbody += f"<td style='padding:10px; border:1px solid #ddd; color:#222;'>{fmt_s(data[c]['s'])}</td><td style='padding:10px; border:1px solid #ddd; color:#222;'>{data[c]['q']}</td><td style='padding:10px; border:1px solid #ddd; color:#222;'>{data[c]['f']}</td>"
            else: tbody += "<td style='padding:10px; border:1px solid #ddd; color:#222;'></td><td style='padding:10px; border:1px solid #ddd; color:#222;'></td><td style='padding:10px; border:1px solid #ddd; color:#222;'></td>"
        tbody += "</tr>"
    return f"""<div style="max-height: 500px; overflow-y: auto; overflow-x: auto; border: 1px solid #ddd; border-radius: 8px; direction: rtl; margin-bottom: 20px;"><table style="width: 100%; border-collapse: collapse; text-align: center; font-family: 'Cairo', sans-serif; font-size: 15px;"><thead style="position: sticky; top: 0; background-color: #2d5a4e; color: #c9a84c; z-index: 2; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">{thead}</thead><tbody>{tbody}</tbody></table></div>"""

def get_area_box_html(f, q, s):
    return f"""<div style="display:inline-flex; gap:8px; direction:rtl;">
<div style="border:1px solid #2d5a4e; border-radius:6px; padding:2px 12px; text-align:center; background:#fff; min-width:40px; box-shadow:0 1px 3px rgba(0,0,0,0.1);"><span style="font-size:11px; color:#555; display:block; border-bottom:1px solid #eee; margin-bottom:2px;">سهم</span><strong style="font-size:16px; color:#2d5a4e;">{fmt_s(s)}</strong></div>
<div style="border:1px solid #2d5a4e; border-radius:6px; padding:2px 12px; text-align:center; background:#fff; min-width:40px; box-shadow:0 1px 3px rgba(0,0,0,0.1);"><span style="font-size:11px; color:#555; display:block; border-bottom:1px solid #eee; margin-bottom:2px;">قيراط</span><strong style="font-size:16px; color:#2d5a4e;">{int(q)}</strong></div>
<div style="border:1px solid #2d5a4e; border-radius:6px; padding:2px 12px; text-align:center; background:#fff; min-width:40px; box-shadow:0 1px 3px rgba(0,0,0,0.1);"><span style="font-size:11px; color:#555; display:block; border-bottom:1px solid #eee; margin-bottom:2px;">فدان</span><strong style="font-size:16px; color:#2d5a4e;">{int(f)}</strong></div>
</div>"""

def generate_scrollable_styled_table(df):
    html = """<div style="max-height: 500px; overflow-y: auto; overflow-x: auto; border: 1px solid #ddd; border-radius: 8px; direction: rtl; margin-bottom: 20px;"><table style="width: 100%; border-collapse: collapse; text-align: center; font-family: 'Cairo', sans-serif; font-size: 15px;"><thead style="position: sticky; top: 0; background-color: #2d5a4e; color: #c9a84c; z-index: 2; box-shadow: 0 2px 5px rgba(0,0,0,0.1);"><tr>"""
    for col in df.columns: html += f"<th style='padding: 12px; border: 1px solid #3d6b5e;'>{col}</th>"
    html += "</tr></thead><tbody>"
    for i, row in df.iterrows():
        bg_color = "#f9f9f9" if i % 2 == 0 else "#ffffff"
        html += f"<tr style='background-color: {bg_color}; transition: background-color 0.2s;' onmouseover=\"this.style.backgroundColor='#eef6f1'\" onmouseout=\"this.style.backgroundColor='{bg_color}'\">"
        for col in df.columns:
            val = row[col]
            if pd.isna(val) or val == "None" or str(val).strip() == "": val = "—"
            html += f"<td style='padding: 10px; border: 1px solid #ddd; color: #222;'>{val}</td>"
        html += "</tr>"
    html += "</tbody></table></div>"
    return html

def generate_print_html(df, title):
    rows = ""
    for idx, row in df.iterrows():
        rows += "<tr>"
        for col in df.columns:
            val = row[col]
            rows += f"<td>{val if val != '' and val is not None else ''}</td>"
        rows += "</tr>"
    headers = ''.join([f'<th>{col}</th>' for col in df.columns])
    html = (
        '<!DOCTYPE html><html dir="rtl" lang="ar"><head><meta charset="UTF-8"><title>' + str(title) + '</title>'
        '<style>@import url("https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap"); '
        'body { font-family:"Cairo",sans-serif; background:#fff; color:#000; padding:20px; direction:rtl; } '
        'table { width:100%; border-collapse:collapse; margin-top:15px; font-size:13px; text-align:center; } '
        'th,td { border:1px solid #000; padding:6px; font-weight:bold; } '
        'th { background:#2d5a4e; color:#c9a84c; -webkit-print-color-adjust: exact; print-color-adjust: exact; } '
        'h2 { text-align:center; color:#2d5a4e; margin-bottom: 10px; } '
        '.btn { display:block; width:200px; margin:0 auto 15px; padding:10px; background:#2d5a4e; color:#fff; text-align:center; cursor:pointer; border:none; font-size:16px; border-radius:5px; font-family:"Cairo"; } '
        '@media print { .btn { display:none !important; } @page { size: A4 portrait; margin: 0; } body { padding: 15mm; } }'
        '</style></head><body><button class="btn" onclick="window.print()">🖨️ طباعة المستند الحالي</button>'
        '<h2>' + str(title) + '</h2><table><thead><tr>' + headers + '</tr></thead><tbody>' + rows + '</tbody></table></body></html>'
    )
    return html.encode('utf-8')

# ==========================================
# 5. جسم الصفحة الرئيسي
# ==========================================
def show_page():
    init_db()
    if 'edit_id' not in st.session_state: st.session_state['edit_id'] = None

    st.markdown("<h2 style='text-align: right; color: #2d5a4e; margin-top: -35px;'>🌾 منظومة الإدارة الزراعية الشاملة</h2>", unsafe_allow_html=True)
    st.markdown("---")

    tab_comprehensive, tab_sijil2, tab_orchards, tab_crops = st.tabs([
        "🔍 الملف الشامل (الكارت)", 
        "📖 قاعدة بيانات (سجل 2 خدمات)",
        "🌳 منظومة البساتين والأشجار", 
        "🌾 المحاصيل والخضروات"
    ])

    with tab_comprehensive:
        st.markdown("### 🪪 الاستعلام السريع والملفات التعريفية")
        c_search1, c_search2 = st.columns([3, 1])
        with c_search1: search_input = st.text_input("🔍 ابحث برقم الحيازة أو اسم الحائز الحالي\u200B:")
        with c_search2:
            st.markdown("<div style='margin-top:28px;'></div>", unsafe_allow_html=True)
            search_btn = st.button("🚀 تشغيل البحث الكلي", use_container_width=True, type="primary")

        if search_input:
            conn = sqlite3.connect('contracts_database.db')
            c = conn.cursor()
            c.execute("SELECT * FROM services_reg")
            all_db_farmers = c.fetchall()
            c.execute("PRAGMA table_info(services_reg)")
            cols_map = {col[1]: i for i, col in enumerate(c.fetchall())}
            s_norm = normalize_arabic_name(search_input)
            s_parts = s_norm.split()
            
            farmers = []
            for r in all_db_farmers:
                h_no = str(r[cols_map['hayaza_no']])
                db_name_raw = str(r[cols_map['name']])
                db_name = normalize_arabic_name(db_name_raw)
                
                # جلب اسم مفوض الورثة ومعالجته للبحث
                rep_name_raw = str(r[cols_map.get('rep_name', '')] if 'rep_name' in cols_map else "")
                db_rep_name = normalize_arabic_name(rep_name_raw)
                
                # البحث في الحيازة، اسم الحائز الأساسي، أو اسم المفوض
                if (search_input == h_no) or (s_norm in db_name) or all(p in db_name for p in s_parts) or (db_rep_name and (s_norm in db_rep_name or all(p in db_rep_name for p in s_parts))):
                    farmers.append(r)
            
            if not farmers: st.warning("⚠️ لم يتم العثور على أي حائز يطابق هذا البحث في سجل 2 خدمات.")
            else:
                for f_row in farmers:
                    f_id = f_row[cols_map['id']]
                    h_no = f_row[cols_map['hayaza_no']]
                    h_manz = f_row[cols_map.get('hayaza_manzoma', '') or ''] or "—"
                    f_name = f_row[cols_map['name']]
                    f_nid = f_row[cols_map.get('national_id', '') or ''] or "—"
                    f_hod = f_row[cols_map.get('hod', '') or ''] or "—"
                    rep_name = f_row[cols_map.get('rep_name', '')] if 'rep_name' in cols_map else ""
                    
                    tot_f = int(f_row[cols_map.get('f', 0)] or 0)
                    tot_q = int(f_row[cols_map.get('q', 0)] or 0)
                    tot_s = float(f_row[cols_map.get('s', 0)] or 0)

                    is_heir = str(f_name).strip().startswith("و") or "ورثة" in str(f_name) or "ورثه" in str(f_name)

                    c.execute("SELECT id, season, crop_name, crop_type, f, q, s FROM farmer_crops WHERE hayaza_no=?", (h_no,))
                    all_items = c.fetchall()
                    
                    basateen_items = [item for item in all_items if item[1] == 'بساتين']
                    crop_items = [item for item in all_items if item[1] != 'بساتين']

                    total_sijil_sahms = (tot_f * 24 * 24) + (tot_q * 24) + tot_s
                    total_planted_sahms = sum((item[4]*24*24) + (item[5]*24) + float(item[6]) for item in all_items)
                    diff_sahms = total_sijil_sahms - total_planted_sahms
                    
                    audit_msg = ""
                    if total_sijil_sahms == 0 and total_planted_sahms == 0: audit_msg = "<span style='color:gray; font-weight:bold;'>⚪ الحيازة مصفّرة بالكامل ولا يوجد زراعات.</span>"
                    elif diff_sahms == 0: audit_msg = "<span style='color:green; font-weight:bold;'>🟢 الحيازة منزرعة بالكامل (تطابق المساحات).</span>"
                    elif diff_sahms > 0:
                        df_f = int(diff_sahms // (24 * 24))
                        df_q = int((diff_sahms % (24 * 24)) // 24)
                        df_s = fmt_s(round(diff_sahms % 24, 2))
                        audit_msg = f"<span style='color:#b8860b; font-weight:bold;'>🟡 يوجد مساحة غير منزرعة (فضاء): {df_f}ف و {df_q}ط و {df_s}س</span>"
                    else:
                        ov_sahms = abs(diff_sahms)
                        ov_f = int(ov_sahms // (24 * 24))
                        ov_q = int((ov_sahms % (24 * 24)) // 24)
                        ov_s = fmt_s(round(ov_sahms % 24, 2))
                        audit_msg = f"<span style='color:red; font-weight:bold;'>🔴 تنبيه: مساحة المحاصيل أكبر من الحيازة الكلية بزيادة: {ov_f}ف و {ov_q}ط و {ov_s}س!</span>"

                    rows_html = ""
                    if not basateen_items and not crop_items:
                        rows_html = "<tr><td colspan='4' style='text-align:center; padding:15px; color:#888;'>لا توجد زراعات مسجلة لهذا الحائز حتى الآن</td></tr>"
                    else:
                        for b in basateen_items: rows_html += f"<tr><td style='padding:10px; border:1px solid #ddd; text-align:right; font-weight:bold;'>🌳 {unify_crop_name(b[2])}</td><td style='padding:6px; border:1px solid #ddd; text-align:center;'><div style='background:#f4f6f9; border:1px solid #ccc; border-radius:4px;'>{fmt_s(b[6])}</div></td><td style='padding:6px; border:1px solid #ddd; text-align:center;'><div style='background:#f4f6f9; border:1px solid #ccc; border-radius:4px;'>{int(b[5])}</div></td><td style='padding:6px; border:1px solid #ddd; text-align:center;'><div style='background:#f4f6f9; border:1px solid #ccc; border-radius:4px;'>{int(b[4])}</div></td></tr>"
                        for cr in crop_items: rows_html += f"<tr><td style='padding:10px; border:1px solid #ddd; text-align:right; font-weight:bold;'>🌾 {unify_crop_name(cr[2])} ({cr[1]})</td><td style='padding:6px; border:1px solid #ddd; text-align:center;'><div style='background:#f4f6f9; border:1px solid #ccc; border-radius:4px;'>{fmt_s(cr[6])}</div></td><td style='padding:6px; border:1px solid #ddd; text-align:center;'><div style='background:#f4f6f9; border:1px solid #ccc; border-radius:4px;'>{int(cr[5])}</div></td><td style='padding:6px; border:1px solid #ddd; text-align:center;'><div style='background:#f4f6f9; border:1px solid #ccc; border-radius:4px;'>{int(cr[4])}</div></td></tr>"

                    rep_html = f'<div style="flex:1; text-align:center; border-left:1px solid #ddd;"><span style="color:#666; font-size:13px;">مفوض الورثة</span><br><strong style="font-size:16px; color:#2d5a4e;">{rep_name if rep_name else "—"}</strong></div>' if is_heir else ""

                    card_full_html = (
                        '<div style="width:100%; border:2px solid #2d5a4e; border-radius:12px; overflow:hidden; direction:rtl; text-align:right; font-family:\'Cairo\', sans-serif; background:#fff; box-shadow:0 4px 12px rgba(0,0,0,0.15); margin-bottom:20px; -webkit-user-select: text; user-select: text;">'
                        '<div style="background:#2d5a4e; color:#fff; padding:15px 20px; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px;">'
                        f'<div style="font-size:24px; font-weight:900; color:#c9a84c;">👤 {f_name}</div>'
                        '<div style="display:flex; gap:12px;">'
                        f'<div style="background:rgba(255,255,255,0.1); border:1px solid #c9a84c; padding:4px 15px; border-radius:6px; text-align:center;"><span style="display:block; font-size:11px; color:#ccc;">رقم المنظومة المرجعي</span><strong style="font-size:16px; color:#fff;">{h_manz}</strong></div>'
                        f'<div style="background:#c9a84c; padding:4px 15px; border-radius:6px; text-align:center; color:#2d5a4e;"><span style="display:block; font-size:11px; font-weight:bold;">رقم سجل 2</span><strong style="font-size:16px; font-weight:900;">{h_no}</strong></div>'
                        '</div></div>'
                        '<div style="display:flex; justify-content:space-between; align-items:center; background:#f7f3ee; padding:15px 20px; border-bottom:1px solid #eee; flex-wrap:wrap; gap:15px;">'
                        f'<div style="flex:1.2; text-align:center; border-left:1px solid #ddd;"><span style="color:#666; font-size:13px;">الرقم القومي {"(للمفوض)" if is_heir else ""}</span><br><strong style="font-size:20px; color:#2d5a4e; font-weight:bold; letter-spacing:0.5px;">{f_nid}</strong></div>'
                        f'{rep_html}'
                        f'<div style="flex:0.8; text-align:center; border-left:1px solid #ddd;"><span style="color:#666; font-size:13px;">الحوض الرئيسي</span><br><strong style="font-size:16px; color:#2d5a4e;">{f_hod}</strong></div>'
                        f'<div style="flex:1.5; display:flex; flex-direction:column; align-items:center; justify-content:center;"><span style="font-weight:bold; color:#2d5a4e; font-size:13px; margin-bottom:5px;">📐 المساحة الكلية (سجل 2):</span>{get_area_box_html(tot_f, tot_q, tot_s)}</div>'
                        '</div>'
                        '<div style="padding:20px; background:#fff;"><h4 style="margin-top:0; color:#2d5a4e; margin-bottom:12px; font-size:15px;">🌱 التفاصيل الزراعية (المحاصيل والبساتين الحالية):</h4>'
                        '<table style="width:100%; border-collapse:collapse; font-family:\'Cairo\', sans-serif;"><thead><tr style="background:#2d5a4e; color:#c9a84c;">'
                        '<th style="padding:10px; border:1px solid #ddd; text-align:right; font-size:13px;">نوع الزراعة (المحاصيل / الشجر)</th>'
                        '<th style="padding:10px; border:1px solid #ddd; text-align:center; width:80px; font-size:13px;">سهم</th>'
                        '<th style="padding:10px; border:1px solid #ddd; text-align:center; width:80px; font-size:13px;">قيراط</th>'
                        '<th style="padding:10px; border:1px solid #ddd; text-align:center; width:80px; font-size:13px;">فدان</th>'
                        f'</tr></thead><tbody>{rows_html}</tbody></table></div>'
                        f'<div style="padding:10px 20px; background:#f9f9f9; text-align:center; border-top:1px solid #eee; font-size:14px;">{audit_msg}</div></div>'
                    )
                    
                    st.markdown(card_full_html, unsafe_allow_html=True)
                    col_print, col_gap, col_edit = st.columns([1, 0.2, 1])
                    
                    with col_print:
                        print_file = (
                            '<!DOCTYPE html><html dir="rtl" lang="ar"><head><meta charset="UTF-8"><title>كارت الحائز - ' + str(f_name) + '</title>'
                            '<style>@import url("https://fonts.googleapis.com/css2?family=Cairo:wght@400;700;900&display=swap"); '
                            'body { font-family:"Cairo",sans-serif; background:#fff; margin:0; padding:20px; -webkit-print-color-adjust: exact; print-color-adjust: exact; } '
                            '@media print { @page { size: A4 portrait; margin: 15mm; } button { display: none !important; } }</style></head>'
                            '<body><button onclick="window.print()" style="display:block; margin:0 auto 20px auto; padding:10px 20px; font-family:\'Cairo\'; font-size:16px; background:#2d5a4e; color:#fff; border:none; border-radius:5px; cursor:pointer;">🖨️ اضغط هنا لطباعة الكارت الفوري</button>'
                            + card_full_html + '</body></html>'
                        ).encode('utf-8')
                        st.download_button("🖨️ تحميل نسخة الطباعة (A4)", data=print_file, file_name=f"كارت_الطباعة_{h_no}.html", mime="text/html", use_container_width=True)
                    
                    with col_edit:
                        if st.button("⚙️ إدارة وتعديل الملف الشامل", key=f"tgl_{h_no}", type="primary", use_container_width=True):
                            st.session_state['edit_id'] = None if st.session_state['edit_id'] == str(f_id) else str(f_id)
                            st.session_state[f'add_count_{f_id}'] = 1 
                            st.rerun()

                    if st.session_state['edit_id'] == str(f_id):
                        if f'add_count_{f_id}' not in st.session_state: st.session_state[f'add_count_{f_id}'] = 1
                        with st.container():
                            st.markdown(f"""<div style="padding:20px; background:#f4f6f9; border:2px solid #c9a84c; border-radius:12px; direction:rtl; text-align:right; margin-top:15px;">
                            <h3 style="color:#2d5a4e; margin-top:0; border-bottom:2px solid #c9a84c; padding-bottom:10px;">🛠️ لوحة تحكم الحائز: {f_name}</h3>""", unsafe_allow_html=True)
                            
                            total_planted_live = 0.0

                            st.markdown("##### 📝 1. البيانات الأساسية:")
                            if is_heir:
                                c_b1, c_b2, c_rep = st.columns(3)
                                with c_b1: edit_name = st.text_input("اسم الحائز (الورثة)\u200B", value=f_name)
                                with c_rep: edit_rep = st.text_input("اسم مفوض الورثة\u200B", value=rep_name)
                                with c_b2: edit_nid = st.text_input("الرقم القومي للمفوض\u200B", value=f_nid)
                            else:
                                c_b1, c_b2 = st.columns([2, 1])
                                with c_b1: edit_name = st.text_input("اسم الحائز بالكامل\u200B", value=f_name)
                                with c_b2: edit_nid = st.text_input("الرقم القومي\u200B", value=f_nid)
                                edit_rep = ""

                            c_b4, c_b5 = st.columns(2)
                            with c_b4: edit_h_no = st.text_input("رقم الحيازة (سجل 2)\u200B", value=h_no)
                            with c_b5: edit_h_manz = st.text_input("رقم المنظومة المرجعي\u200B", value=h_manz)
                            
                            c_b6, _ = st.columns([1, 1])
                            with c_b6: 
                                hod_options = [""] + BASINS_LIST + ["أخرى (كتابة يدوية)"]
                                current_hod = f_hod.strip()
                                if current_hod and current_hod not in hod_options and current_hod != "nan": hod_options.insert(1, current_hod)
                                hod_idx = hod_options.index(current_hod) if current_hod in hod_options else 0
                                edit_hod_sel = st.selectbox("الحوض الرئيسي\u200B", hod_options, index=hod_idx)
                                edit_hod = st.text_input("اكتب اسم الحوض يدوياً\u200B", value="") if edit_hod_sel == "أخرى (كتابة يدوية)" else edit_hod_sel

                            st.markdown("##### 📐 2. المساحة الكلية (بسجل 2):")
                            col_s, col_q, col_f = st.columns(3)
                            with col_s: edit_s = st.number_input("سهم كلي\u200B", min_value=0.0, value=float(tot_s))
                            with col_q: edit_q = st.number_input("قيراط كلي\u200B", min_value=0, max_value=23, value=tot_q)
                            with col_f: edit_f = st.number_input("فدان كلي\u200B", min_value=0, value=tot_f)
                            
                            st.markdown("##### 🌱 3. تعديل الزراعات الحالية:")
                            crop_edits = {}
                            if not all_items: st.info("لا توجد زراعات مسجلة لهذا الحائز. يمكنك إضافتها من القسم التالي.")
                            else:
                                for crp in all_items:
                                    c_id, c_season, c_name_db, _, c_f, c_q, c_s = crp
                                    icon = "🌳" if c_season == "بساتين" else "🌾"
                                    st.markdown(f"<div style='background:#e9ecef; padding:5px 10px; border-radius:5px; margin-top:10px; border-right:3px solid #2d5a4e;'>{icon} <b>{unify_crop_name(c_name_db)}</b> ({c_season}) <span style='font-size:12px; color:red;'>(للحذف اجعل المساحات صفر)</span></div>", unsafe_allow_html=True)
                                    cs, cq, cf = st.columns(3)
                                    with cs: new_cs = st.number_input("سهم\u200B", min_value=0.0, value=float(c_s), key=f"s_{c_id}")
                                    with cq: new_cq = st.number_input("قيراط\u200B", min_value=0, max_value=23, value=int(c_q), key=f"q_{c_id}")
                                    with cf: new_cf = st.number_input("فدان\u200B", min_value=0, value=int(c_f), key=f"f_{c_id}")
                                    crop_edits[c_id] = (new_cf, new_cq, new_cs)
                                    total_planted_live += (new_cf * 24 * 24) + (new_cq * 24) + new_cs

                            st.markdown("##### ➕ 4. إضافة زراعات جديدة:")
                            new_crops_data = []
                            for i in range(st.session_state[f'add_count_{f_id}']):
                                c_ns, c_nq, c_nf, c_name, c_season = st.columns([1, 1, 1, 3, 2])
                                with c_season: new_season = st.selectbox(f"الموسم / النوع\u200B", SEASONS_OPTS, key=f"nseason_{f_id}_{i}")
                                with c_name: 
                                    if new_season and new_season != "أخرى (كتابة يدوية)":
                                        crop_opts = [""] + CROP_MAPPINGS.get(new_season, []) + ["أخرى (كتابة يدوية)"]
                                        sel_crop = st.selectbox(f"اسم المحصول أو الشجرة\u200B", crop_opts, key=f"nname_sel_{f_id}_{i}")
                                        new_crop_name = st.text_input("اكتب اسم المحصول\u200B", key=f"nname_txt_{f_id}_{i}") if sel_crop == "أخرى (كتابة يدوية)" else sel_crop
                                    elif new_season == "أخرى (كتابة يدوية)":
                                        new_crop_name = st.text_input("اكتب اسم المحصول\u200B", key=f"nname_txt2_{f_id}_{i}")
                                    else:
                                        st.selectbox(f"اسم المحصول أو الشجرة\u200B", [""], key=f"nname_dis_{f_id}_{i}", disabled=True)
                                        new_crop_name = ""
                                with c_ns: new_s_add = st.number_input("سهم\u200B", min_value=0.0, key=f"ns2_{f_id}_{i}")
                                with c_nq: new_q_add = st.number_input("قيراط\u200B", min_value=0, max_value=23, key=f"nq_{f_id}_{i}")
                                with c_nf: new_f_add = st.number_input("فدان\u200B", min_value=0, key=f"nf_{f_id}_{i}")
                                new_crops_data.append((new_season, new_crop_name, new_f_add, new_q_add, new_s_add))
                                total_planted_live += (new_f_add * 24 * 24) + (new_q_add * 24) + new_s_add

                            st.write("---")
                            total_sijil_live = (edit_f * 24 * 24) + (edit_q * 24) + edit_s
                            diff_live = total_sijil_live - total_planted_live
                            
                            st.markdown("##### ⚖️ الموقف الحي للمساحة (أثناء التعديل):")
                            if total_sijil_live == 0 and total_planted_live == 0:
                                st.info("⚪ الحيازة مصفرة بالكامل.")
                            elif diff_live == 0:
                                st.success("🟢 المساحة مطابقة تماماً! لا يوجد زيادة أو عجز.")
                            elif diff_live > 0:
                                df_f = int(diff_live // (24 * 24))
                                df_q = int((diff_live % (24 * 24)) // 24)
                                df_s = fmt_s(round(diff_live % 24, 2))
                                st.warning(f"🟡 متبقي للحائز (فضاء بدون زراعة): {df_f} فدان و {df_q} قيراط و {df_s} سهم")
                            else:
                                ov = abs(diff_live)
                                ov_f = int(ov // (24 * 24))
                                ov_q = int((ov % (24 * 24)) // 24)
                                ov_s = fmt_s(round(ov % 24, 2))
                                st.error(f"🔴 احذر! لقد تخطيت المساحة الكلية بزيادة قدرها: {ov_f} فدان و {ov_q} قيراط و {ov_s} سهم")

                            st.write("")
                            b_cn, b_del, b_add_row, b_sv = st.columns([1, 1, 1.5, 2])
                            with b_cn: cancel_btn = st.button("❌ إلغاء", use_container_width=True, key=f"btn_cancel_{f_id}")
                            with b_del: delete_btn = st.button("🗑️ حذف الحائز", use_container_width=True, key=f"btn_del_{f_id}")
                            with b_add_row: add_more_btn = st.button("➕ إضافة زراعة أخرى", use_container_width=True, key=f"btn_add_{f_id}")
                            with b_sv: save_btn = st.button("💾 حفظ وتحديث كل البيانات", type="primary", use_container_width=True, key=f"btn_save_{f_id}")

                            if delete_btn:
                                c.execute("DELETE FROM services_reg WHERE id=?", (f_id,))
                                c.execute("DELETE FROM farmer_crops WHERE hayaza_no=?", (h_no,))
                                conn.commit()
                                st.session_state['edit_id'] = None
                                st.success("🗑️ تم حذف الحائز وكل زراعاته نهائياً!")
                                st.rerun()

                            if add_more_btn:
                                st.session_state[f'add_count_{f_id}'] += 1
                                st.rerun()

                            if save_btn:
                                c.execute("UPDATE services_reg SET hayaza_no=?, hayaza_manzoma=?, name=?, normalized_name=?, smart_name=?, national_id=?, f=?, q=?, s=?, hod=?, rep_name=? WHERE id=?", 
                                          (edit_h_no, edit_h_manz, edit_name, normalize_arabic_name(edit_name), generate_smart_name(edit_name), edit_nid, edit_f, edit_q, edit_s, edit_hod, edit_rep, f_id))
                                
                                if edit_h_no != h_no: c.execute("UPDATE farmer_crops SET hayaza_no=? WHERE hayaza_no=?", (edit_h_no, h_no))
                                
                                for cid, (nf, nq, ns) in crop_edits.items():
                                    if nf == 0 and nq == 0 and ns == 0.0: c.execute("DELETE FROM farmer_crops WHERE id=?", (cid,))
                                    else: c.execute("UPDATE farmer_crops SET f=?, q=?, s=? WHERE id=?", (nf, nq, ns, cid))
                                        
                                for season_val, name_val, nf_add, nq_add, ns_add in new_crops_data:
                                    if season_val and name_val and (nf_add > 0 or nq_add > 0 or ns_add > 0):
                                        db_season, db_type = "أخرى", "محصول"
                                        if season_val == "بساتين": db_season, db_type = "بساتين", "بساتين"
                                        elif "صيفي" in season_val: db_season, db_type = "صيفي", "خضار" if "خضر" in season_val else "محصول"
                                        elif "شتوي" in season_val: db_season, db_type = "شتوي", "خضار" if "خضر" in season_val else "محصول"
                                        c.execute("INSERT INTO farmer_crops (hayaza_no, season, crop_name, crop_type, f, q, s) VALUES (?, ?, ?, ?, ?, ?, ?)", (edit_h_no, db_season, name_val, db_type, nf_add, nq_add, ns_add))

                                conn.commit()
                                st.session_state['edit_id'] = None
                                st.success("✅ تم الحفظ الشامل بنجاح!")
                                st.rerun()
                                
                            if cancel_btn:
                                st.session_state['edit_id'] = None
                                st.rerun()
                            st.markdown("</div>", unsafe_allow_html=True)
            conn.close()

    # ====================================================
    # التبويب الثاني: قاعدة بيانات سجل 2 خدمات
    # ====================================================
    with tab_sijil2:
        st.markdown("### 📖 قاعدة البيانات المركزية والاستيراد الشامل")
        
        conn = sqlite3.connect('contracts_database.db')
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM services_reg WHERE hayaza_no GLOB '[0-9]*'")
        total_h_count = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM services_reg WHERE hayaza_no GLOB '[0-9]*' AND f=0 AND q=0 AND s=0")
        zero_h_count = c.fetchone()[0]
        active_h_count = total_h_count - zero_h_count
        
        st.markdown(f'''
        <div style="display:flex; justify-content:space-around; background:#fff; padding:15px; border-radius:12px; margin-bottom:15px; border:2px solid #2d5a4e; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
            <div style="text-align:center;"><span style="font-size:28px; font-weight:900; color:#1a2c42;">{total_h_count}</span><br><span style="color:#666; font-weight:bold;">إجمالي الحيازات الكلي</span></div>
            <div style="text-align:center; border-right: 1px solid #ddd; padding-right: 20px;"><span style="font-size:28px; font-weight:900; color:#28a745;">{active_h_count}</span><br><span style="color:#666; font-weight:bold;">حيازات فعلية (قائمة)</span></div>
            <div style="text-align:center; border-right: 1px solid #ddd; padding-right: 20px;"><span style="font-size:28px; font-weight:900; color:#dc3545;">{zero_h_count}</span><br><span style="color:#666; font-weight:bold;">حيازات ملغاة (مُصفرة)</span></div>
        </div>
        ''', unsafe_allow_html=True)

        with st.expander("📥 الاستيراد الشامل الذكي (من الشيت المجمع Master Final)", expanded=True):
            st.info("💡 ارفع الشيت المجمع (Master_Final.xlsx) هنا. البرنامج هيقسّم الأساسيات في سجل 2 ومحاصيل الجوافة والبرتقال والمانجو في البساتين تلقائياً.")
            up_master_file = st.file_uploader("اختر الشيت المجمع لرفعه:", type=['csv', 'xlsx'], key="up_master")
            if up_master_file and st.button("🚀 بدء الاستيراد الشامل والتوزيع", type="primary"):
                try:
                    df_up = pd.read_csv(up_master_file) if up_master_file.name.endswith('.csv') else pd.read_excel(up_master_file)
                    df_up.columns = df_up.columns.str.strip()
                    ok_c, crops_c, missing_counter = 0, 0, 0
                    
                    for _, row in df_up.iterrows():
                        n_v = str(row.get('الاسم', '')).strip()
                        h_base = str(row.get('رقم الحيازة', '')).replace('.0','').strip()
                        if not n_v: continue
                        if not h_base or "غير موجود" in h_base or "غير محدد" in h_base:
                            missing_counter += 1
                            h_v = f"غير مدرج ({missing_counter})"
                        else: h_v = h_base

                        nid = str(row.get('الرقم القومي', '')).replace('.0','').strip()
                        hmz = str(row.get('رقم المنظومة', '')).replace('.0','').strip()
                        hod = str(row.get('الحوض', '')).strip()
                        sf = safe_num(row.get('فدان كلي', 0))
                        sq = safe_num(row.get('قيراط كلي', 0))
                        ss = safe_num(row.get('سهم كلي', 0.0), True)
                        
                        c.execute("INSERT INTO services_reg (hayaza_no, hayaza_manzoma, national_id, name, normalized_name, smart_name, f, q, s, hod) VALUES (?,?,?,?,?,?,?,?,?,?)",
                                  (h_v, hmz, nid, n_v, normalize_arabic_name(n_v), generate_smart_name(n_v), sf, sq, ss, hod))
                        ok_c += 1

                        crops_to_check = [('جوافه', 'الجوافة'), ('برتقال', 'البرتقال'), ('مانجو', 'المانجو')]
                        for col_base, db_name in crops_to_check:
                            cf = safe_num(row.get(f'فدان {col_base}', 0))
                            cq = safe_num(row.get(f'قيراط {col_base}', 0))
                            cs = safe_num(row.get(f'سهم {col_base}', 0.0), True)
                            if cf > 0 or cq > 0 or cs > 0:
                                c.execute("INSERT INTO farmer_crops (hayaza_no, season, crop_name, crop_type, f, q, s) VALUES (?, 'بساتين', ?, 'بساتين', ?, ?, ?)", (h_v, db_name, cf, cq, cs))
                                crops_c += 1

                    conn.commit()
                    st.success(f"✅ تمت العملية بنجاح! تم استيراد {ok_c} حائز أساسي، وتوزيع {crops_c} مساحة بساتين.")
                    st.rerun()
                except Exception as e: st.error(f"خطأ في الاستيراد: {e}")

        with st.expander("➕ إضافة حائز جديد لسجل 2 (رقم تلقائي)", expanded=False):
            c.execute("SELECT MAX(CAST(hayaza_no AS INTEGER)) FROM services_reg WHERE hayaza_no GLOB '[0-9]*'")
            max_h = c.fetchone()[0]
            next_h = str((max_h or 0) + 1)
            
            c1, c2, c3 = st.columns(3)
            with c1: new_f_name = st.text_input("الاسم بالكامل*", key="new_fn")
            with c2: new_h_no = st.text_input("رقم الحيازة (سجل 2)*", value=next_h, key="new_hn")
            with c3: new_nid = st.text_input("الرقم القومي", key="new_nid")
            
            c4, c5 = st.columns(2)
            with c4: 
                new_hod_sel = st.selectbox("الحوض الرئيسي", [""] + BASINS_LIST + ["أخرى (كتابة يدوية)"], key="new_hod_sel")
                new_hod = st.text_input("اكتب اسم الحوض يدوياً", key="new_hod_txt") if new_hod_sel == "أخرى (كتابة يدوية)" else new_hod_sel
            with c5: new_manz = st.text_input("رقم المنظومة", key="new_manz")
            
            st.markdown("###### 📐 المساحة الكلية للحائز الجديد:")
            col_s, col_q, col_f = st.columns(3)
            with col_s: new_s = st.number_input("سهم كلي", min_value=0.0, key="new_s")
            with col_q: new_q = st.number_input("قيراط كلي", min_value=0, max_value=23, key="new_q")
            with col_f: new_f = st.number_input("فدان كلي", min_value=0, key="new_f")
            
            if st.button("💾 حفظ الحائز الجديد", type="primary", use_container_width=True):
                if new_f_name and new_h_no:
                    c.execute("SELECT id FROM services_reg WHERE hayaza_no=?", (new_h_no,))
                    if c.fetchone(): st.error("⚠️ رقم الحيازة مسجل مسبقاً، برجاء اختيار رقم آخر.")
                    else:
                        c.execute("INSERT INTO services_reg (hayaza_no, hayaza_manzoma, national_id, name, normalized_name, smart_name, f, q, s, hod) VALUES (?,?,?,?,?,?,?,?,?,?)",
                                  (new_h_no, new_manz, new_nid, new_f_name, normalize_arabic_name(new_f_name), generate_smart_name(new_f_name), new_f, new_q, new_s, new_hod))
                        conn.commit()
                        st.success(f"✅ تم إضافة الحائز '{new_f_name}' برقم حيازة {new_h_no} بنجاح!")
                else: st.error("⚠️ برجاء كتابة الاسم ورقم الحيازة.")

        st.markdown("---")
        filter_opt = st.selectbox("📌 عرض التقرير حسب الحالة:", ["الكل (عرض جميع الحيازات)", "الحيازات الفعلية (القائمة) فقط", "الحيازات الملغاة (المُصفرة) فقط"])
        
        base_query = "SELECT name as 'الاسم', national_id as 'الرقم القومي', hod as 'الحوض', s as 'سهم', q as 'قيراط', f as 'فدان' FROM services_reg"
        conditions = ["hayaza_no GLOB '[0-9]*'"]
        if filter_opt == "الحيازات الفعلية (القائمة) فقط": conditions.append("(f>0 OR q>0 OR s>0)")
        elif filter_opt == "الحيازات الملغاة (المُصفرة) فقط": conditions.append("(f=0 AND q=0 AND s=0)")
            
        base_query += " WHERE " + " AND ".join(conditions) + " ORDER BY CAST(hayaza_no AS INTEGER) ASC"
        df_sijil = pd.read_sql_query(base_query, conn)
        conn.close()
        
        if not df_sijil.empty:
            df_sijil['سهم'] = df_sijil['سهم'].apply(fmt_s)
            st.download_button("🖨️ طباعة التقرير المعروض", data=generate_print_html(df_sijil, f"قاعدة بيانات سجل 2 خدمات - {filter_opt}"), file_name="تقرير_سجل_2.html", mime="text/html", key="print_sijil_all")
            st.write("")
            st.markdown(generate_scrollable_styled_table(df_sijil), unsafe_allow_html=True)

    # ====================================================
    # التبويب الثالث: منظومة البساتين والأشجار
    # ====================================================
    with tab_orchards:
        st.markdown("### 🌳 إدارة وحصر مساحات أشجار البساتين")
        c_srch_o, c_hod_o = st.columns(2)
        with c_srch_o: search_orch = st.text_input("بحث بالاسم أو رقم الحيازة:", key="s_orch")
        with c_hod_o: hod_orch = st.selectbox("فلترة بالحوض:", ["الكل"] + BASINS_LIST, key="hod_orch_sel")

        conn = sqlite3.connect('contracts_database.db')
        c = conn.cursor()
        c.execute("SELECT s.name, s.hod, s.hayaza_no, c.crop_name, c.f, c.q, c.s FROM farmer_crops c JOIN services_reg s ON c.hayaza_no = s.hayaza_no WHERE c.season = 'بساتين' ORDER BY CAST(s.hayaza_no AS INTEGER) ASC")
        orchard_data = c.fetchall()
        conn.close()
        
        filtered_orch = []
        s_norm_o = normalize_arabic_name(search_orch) if search_orch else ""
        for r in orchard_data:
            name, hod, h_no, crop, f, q, s = r
            if hod_orch != "الكل":
                n_db = normalize_arabic_name(str(hod).replace("حوض", "").replace("-", ""))
                n_sel = normalize_arabic_name(hod_orch.replace("حوض", "").replace("-", ""))
                if not (n_db == n_sel or n_db in n_sel or n_sel in n_db): continue
            if s_norm_o and not (search_orch == str(h_no) or s_norm_o in normalize_arabic_name(name)): continue
            filtered_orch.append(r)
            
        records_orch, ordered_crops_orch = build_pivot_data(filtered_orch, main_crops=["الجوافة", "البرتقال", "المانجو"])
        if records_orch:
            st.download_button("🖨️ طباعة سجل أشجار البساتين", data=generate_multi_header_html(records_orch, ordered_crops_orch, "سجل منظومة أشجار البساتين"), file_name="سجل_البساتين.html", mime="text/html", key="print_orch_all")
            st.write("")
            st.markdown(generate_scrollable_multi_header_table(records_orch, ordered_crops_orch), unsafe_allow_html=True)
        else: st.warning("لم يتم العثور على نتائج مطابقة في البساتين.")

    # ====================================================
    # التبويب الرابع: المحاصيل والخضروات الزراعية
    # ====================================================
    with tab_crops:
        st.markdown("### 🌾 إدارة ومراجعة مساحات المحاصيل والخضروات")
        with st.expander("📥 استيراد كشف المحاصيل والخضروات", expanded=True):
            st.info("💡 يمكنك إدخال (رقم الحيازة) لتأكيد الربط للأسماء المتكررة. إذا تُرك فارغاً سيربط بالاسم الموجود في سجل 2.")
            empty_crops_df = pd.DataFrame(columns=['رقم الحيازة (اختياري)', 'الاسم', 'الموسم', 'النوع', 'اسم المحصول_الخضار', 'فدان', 'قيراط', 'سهم'])
            st.download_button("📥 تحميل قالب إدخال المحاصيل", data=convert_df_to_csv(empty_crops_df), file_name="قالب_إدخال_المحاصيل.csv", mime="text/csv")
            
            st.markdown("---")
            up_crop_file = st.file_uploader("اختر شيت المحاصيل لرفعه:", type=['csv', 'xlsx'], key="up_crp_fl")
            if up_crop_file and st.button("🚀 بدء استيراد وربط المحاصيل", type="primary"):
                try:
                    df_up = pd.read_csv(up_crop_file) if up_crop_file.name.endswith('.csv') else pd.read_excel(up_crop_file)
                    df_up.columns = df_up.columns.str.strip()
                    conn = sqlite3.connect('contracts_database.db')
                    c = conn.cursor()
                    ok_c, skip_c, not_found_cr = 0, 0, []
                    
                    for _, row in df_up.iterrows():
                        f_name = str(row.get('الاسم', '')).strip()
                        h_no_excel = str(row.get('رقم الحيازة (اختياري)', '')).replace('.0', '').strip()
                        c_season = str(row.get('الموسم', 'صيفي')).strip()
                        c_type = str(row.get('النوع', 'محصول')).strip()
                        c_name = str(row.get('اسم المحصول_الخضار', '')).strip()
                        
                        if not f_name and not h_no_excel: continue
                        if not c_name or c_name == 'nan': continue
                        
                        if h_no_excel and h_no_excel != 'nan': h_v = h_no_excel
                        else:
                            norm_n = normalize_arabic_name(f_name)
                            smart_n = generate_smart_name(f_name)
                            c.execute("SELECT hayaza_no FROM services_reg WHERE normalized_name=? OR smart_name=? OR name=?", (norm_n, smart_n, f_name))
                            res = c.fetchone()
                            h_v = res[0] if res else None
                            
                        if not h_v:
                            not_found_cr.append(f_name)
                            continue
                        
                        sf = safe_num(row.get('فدان', 0))
                        sq = safe_num(row.get('قيراط', 0))
                        ss = safe_num(row.get('سهم', 0.0), True)
                        
                        c.execute("SELECT id FROM farmer_crops WHERE hayaza_no=? AND season=? AND crop_name=?", (h_v, c_season, c_name))
                        if not c.fetchone():
                            c.execute("INSERT INTO farmer_crops (hayaza_no, season, crop_name, crop_type, f, q, s) VALUES (?, ?, ?, ?, ?, ?, ?)", (h_v, c_season, c_name, c_type, sf, sq, ss))
                            ok_c += 1
                        else: skip_c += 1
                    conn.commit()
                    conn.close()
                    st.success(f"✅ تم ربط واستيراد {ok_c} محصول، وتجاهل {skip_c} مكرر.")
                    if not_found_cr: st.error(f"⚠️ هذه الأسماء غير موجودة في سجل 2: {', '.join(not_found_cr)}")
                    st.rerun()
                except Exception as e: st.error(f"خطأ: {e}")

        c_srch_c, c_hod_c = st.columns(2)
        with c_srch_c: search_crop = st.text_input("بحث بالاسم أو رقم الحيازة:", key="s_crp")
        with c_hod_c: hod_crop = st.selectbox("فلترة بالحوض:", ["الكل"] + BASINS_LIST, key="hod_crp_sel")

        conn = sqlite3.connect('contracts_database.db')
        c = conn.cursor()
        c.execute("SELECT s.name, s.hod, s.hayaza_no, c.crop_name, c.f, c.q, c.s FROM farmer_crops c JOIN services_reg s ON c.hayaza_no = s.hayaza_no WHERE c.season != 'بساتين' ORDER BY CAST(s.hayaza_no AS INTEGER) ASC")
        crops_data = c.fetchall()
        conn.close()
        
        filtered_crp = []
        s_norm_c = normalize_arabic_name(search_crop) if search_crop else ""
        for r in crops_data:
            name, hod, h_no, crop, f, q, s = r
            if hod_crop != "الكل":
                n_db = normalize_arabic_name(str(hod).replace("حوض", "").replace("-", ""))
                n_sel = normalize_arabic_name(hod_crop.replace("حوض", "").replace("-", ""))
                if not (n_db == n_sel or n_db in n_sel or n_sel in n_db): continue
            if s_norm_c and not (search_crop == str(h_no) or s_norm_c in normalize_arabic_name(name)): continue
            filtered_crp.append(r)
            
        records_crp, ordered_crops_crp = build_pivot_data(filtered_crp, main_crops=["القمح", "الذرة", "الأرز", "البرسيم"])
        if records_crp:
            st.download_button("🖨️ طباعة سجل المحاصيل الشامل", data=generate_multi_header_html(records_crp, ordered_crops_crp, "سجل المحاصيل والخضروات"), file_name="سجل_المحاصيل.html", mime="text/html", key="print_crops_all")
            st.write("")
            st.markdown(generate_scrollable_multi_header_table(records_crp, ordered_crops_crp), unsafe_allow_html=True)
        else: st.warning("لم يتم العثور على نتائج مطابقة في المحاصيل.")

if __name__ == "__main__":
    show_page()