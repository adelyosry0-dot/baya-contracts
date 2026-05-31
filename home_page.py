import streamlit as st
import sqlite3
from datetime import date

DAYS_AR = ["الاثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت", "الأحد"]
MONTHS_AR = {1:"يناير",2:"فبراير",3:"مارس",4:"أبريل",5:"مايو",6:"يونيو",
             7:"يوليو",8:"أغسطس",9:"سبتمبر",10:"أكتوبر",11:"نوفمبر",12:"ديسمبر"}
MONTHS_SHORT = {1:"يناير",2:"فبراير",3:"مارس",4:"أبريل",5:"مايو",6:"يونيو",
                7:"يوليو",8:"أغسطس",9:"سبتمبر",10:"أكتوبر",11:"نوفمبر",12:"ديسمبر"}

def get_stats():
    try:
        conn = sqlite3.connect('contracts_database.db')
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM archive WHERE seller_name NOT LIKE '[قسمة]%'")
        sales = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM archive WHERE seller_name LIKE '[قسمة]%'")
        kesma = c.fetchone()[0]
        month_start = str(today.year) + "-" + str(today.month).zfill(2) + "-01"
        c.execute("SELECT COUNT(*) FROM archive WHERE contract_date >= ?", (month_start,))
        this_month = c.fetchone()[0]
        total = sales + kesma
        conn.close()
        sales_pct = round((sales / total) * 100) if total > 0 else 79
        kesma_pct = 100 - sales_pct
        return sales, kesma, total, this_month, sales_pct, kesma_pct
    except:
        return 0, 0, 0, 0, 79, 21

def get_recent(limit=3):
    try:
        conn = sqlite3.connect('contracts_database.db')
        c = conn.cursor()
        c.execute("SELECT contract_date, seller_name, buyer_name FROM archive ORDER BY id DESC LIMIT ?", (limit,))
        rows = c.fetchall()
        conn.close()
        return rows
    except:
        return []

def get_monthly_counts():
    try:
        conn = sqlite3.connect('contracts_database.db')
        c = conn.cursor()
        today = date.today()
        months = []
        for i in range(5, -1, -1):
            m = today.month - i
            y = today.year
            while m <= 0:
                m += 12
                y -= 1
            months.append((y, m))
        counts = []
        for y, m in months:
            start = str(y) + "-" + str(m).zfill(2) + "-01"
            nm = m + 1
            ny = y
            if nm > 12:
                nm = 1
                ny += 1
            end = str(ny) + "-" + str(nm).zfill(2) + "-01"
            c.execute("SELECT COUNT(*) FROM archive WHERE contract_date >= ? AND contract_date < ?", (start, end))
            counts.append(c.fetchone()[0])
        conn.close()
        return counts, months
    except:
        return [3, 5, 2, 6, 4, 7], [(2025,12),(2026,1),(2026,2),(2026,3),(2026,4),(2026,5)]

def show_page():
    sales, kesma, total, this_month, sales_pct, kesma_pct = get_stats()
    recent = get_recent(3)
    monthly_counts, monthly_labels = get_monthly_counts()

    today = date.today()

    max_c = max(monthly_counts) if max(monthly_counts) > 0 else 1
    bar_heights = [max(8, int((cnt / max_c) * 64)) for cnt in monthly_counts]
    bar_classes = ["hi"] * 5 + ["top"]

    # ---- بناء الأعمدة البيانية ----
    bars_html = ""
    for i in range(len(bar_heights)):
        h   = bar_heights[i]
        cls = bar_classes[i]
        lbl = monthly_labels[i]
        short = MONTHS_SHORT[lbl[1]][:3]
        delay = 0.5 + i * 0.05
        bars_html = (bars_html
            + '<div class="bc_h">'
            + '<div class="bfill_h ' + cls + '" style="height:' + str(h) + 'px;animation-delay:' + str(delay) + 's"></div>'
            + '<div class="bml_h">' + short + '</div>'
            + '</div>')

    # ---- بناء آخر المعاملات ----
    recent_html = ""
    icons_list = ["📝", "🤝", "📋"]
    tags_list  = [("tg","بيع"), ("tb","قسمة"), ("tw","بيع")]

    for i, row in enumerate(recent[:3]):
        date_str = row[0]
        seller   = row[1]
        is_kesma = "[قسمة]" in seller
        icon     = "🤝" if is_kesma else icons_list[i % 3]
        tag_cls  = "tb" if is_kesma else tags_list[i % 3][0]
        tag_lbl  = "قسمة" if is_kesma else tags_list[i % 3][1]
        bg       = "bg-a" if is_kesma else "bg-g"
        clean    = seller.replace("[قسمة]","").replace("[بيع]","").strip()
        if len(clean) > 18:
            clean = clean[:18] + "..."
        recent_html = (recent_html
            + '<div class="ritem_h">'
            + '<div class="ri-dot_h ' + bg + '">' + icon + '</div>'
            + '<div class="ri-info_h">'
            + '<div class="ri-name_h">' + clean + '</div>'
            + '<div class="ri-time_h">' + date_str + '</div>'
            + '</div>'
            + '<div class="ri-tag_h ' + tag_cls + '">' + tag_lbl + '</div>'
            + '</div>')

    if not recent_html:
        recent_html = '<div class="ritem_h"><div class="ri-info_h"><div class="ri-name_h" style="color:#a89880">لا توجد معاملات بعد</div></div></div>'

    # ---- إرسال CSS ----
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800;900&display=swap');
@keyframes fadeUp_h{from{opacity:0;transform:translateY(22px)}to{opacity:1;transform:translateY(0)}}
@keyframes barUp_h{from{transform:scaleY(0)}to{transform:scaleY(1)}}
@keyframes slideRight_h{from{width:0}to{width:var(--pw)}}
@keyframes dotPulse_h{0%,100%{opacity:0.4;transform:scale(1)}50%{opacity:1;transform:scale(1.4)}}

.hw-body{padding:16px 14px 0;background:#f7f3ee}
.sec-label_h{font-size:10px;font-weight:700;color:#8a7d6e;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:10px;display:flex;align-items:center;gap:6px}
.sec-label_h::before{content:'';width:16px;height:2px;background:#c9a84c;border-radius:2px}
.sec-label_h::after{content:'';flex:1;height:1px;background:#e5ddd4}
.nav-grid_h{display:grid;grid-template-columns:repeat(3,1fr);gap:9px;margin-bottom:14px}
.ncard_h{background:#fff;border-radius:14px;border:1.5px solid #ede7de;padding:15px 10px 13px;cursor:default;text-align:center;transition:all 0.25s cubic-bezier(0.22,1,0.36,1);position:relative;overflow:hidden}
.ncard_h::before{content:'';position:absolute;top:0;left:0;right:0;height:3px;transform:scaleX(0);transform-origin:right;transition:transform 0.3s ease}
.ncard_h:hover::before{transform:scaleX(1)}
.ncard_h.green::before{background:#2d5a4e}.ncard_h.amber::before{background:#c9a84c}
.ncard_h.terr::before{background:#a0522d}.ncard_h.sage::before{background:#7b9e87}
.ncard_h.warm::before{background:#c4804a}.ncard_h.muted::before{background:#8b7355}
.ncard_h:hover{border-color:#c9a84c;transform:translateY(-3px);box-shadow:0 6px 20px rgba(0,0,0,0.08)}
.nc-icon_h{width:44px;height:44px;border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:21px;margin:0 auto 9px}
.bg-g{background:#e8f2ed}.bg-a{background:#fdf5e3}.bg-t{background:#f5ece6}
.bg-s{background:#eef4f0}.bg-w{background:#faeee4}.bg-m{background:#f2ede6}
.nc-title_h{font-size:13px;font-weight:700;color:#2c2416;line-height:1.3}
.nc-sub_h{font-size:10px;color:#a89880;margin-top:2px}
.lower_h{display:grid;grid-template-columns:5fr 4fr;gap:10px;margin-bottom:14px}
.chart-box_h{background:#fff;border-radius:14px;border:1.5px solid #ede7de;padding:14px}
.chart-head_h{display:flex;justify-content:space-between;align-items:center;margin-bottom:12px}
.ch-title_h{font-size:11px;font-weight:700;color:#6b5e50;letter-spacing:0.5px}
.ch-leg{display:flex;gap:8px}
.ld{display:flex;align-items:center;gap:3px;font-size:9px;color:#a89880}
.ld span{width:7px;height:7px;border-radius:2px}
.ld-g{background:#2d5a4e}.ld-a{background:#c9a84c}
.bars-area_h{display:flex;align-items:flex-end;gap:6px;height:68px}
.bc_h{flex:1;display:flex;flex-direction:column;align-items:center;gap:3px}
.bfill_h{width:100%;border-radius:4px 4px 0 0;background:#ddd6cc;transform-origin:bottom;animation:barUp_h 0.8s cubic-bezier(0.22,1,0.36,1) both}
.bfill_h.hi{background:#2d5a4e}.bfill_h.top{background:#c9a84c}
.bml_h{font-size:8px;color:#b5a898}
.recent-box_h{background:#fff;border-radius:14px;border:1.5px solid #ede7de;padding:14px}
.rb-title_h{font-size:11px;font-weight:700;color:#6b5e50;letter-spacing:0.5px;margin-bottom:10px}
.ritem_h{display:flex;align-items:center;gap:9px;padding:8px 0;border-bottom:1px solid #f5f0ea}
.ritem_h:last-child{border-bottom:none;padding-bottom:0}
.ri-dot_h{width:32px;height:32px;border-radius:9px;display:flex;align-items:center;justify-content:center;font-size:14px;flex-shrink:0}
.ri-info_h{flex:1;min-width:0}
.ri-name_h{font-size:11px;font-weight:700;color:#2c2416;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.ri-time_h{font-size:9px;color:#b5a898;margin-top:1px}
.ri-tag_h{font-size:9px;padding:2px 6px;border-radius:6px;font-weight:700;flex-shrink:0}
.tg{background:#e8f2ed;color:#1a3d31}.tb{background:#fdf5e3;color:#6b4c00}.tw{background:#f5ece6;color:#6b2e10}
.prog-sect{background:#fff;border-radius:14px;border:1.5px solid #ede7de;padding:14px;margin-bottom:14px}
.prog-title_h{font-size:11px;font-weight:700;color:#6b5e50;letter-spacing:0.5px;margin-bottom:12px}
.prog-row_h{display:flex;align-items:center;gap:10px;margin-bottom:10px}
.prog-row_h:last-child{margin-bottom:0}
.prog-icon_h{font-size:14px;width:26px;text-align:center;flex-shrink:0}
.prog-label_h{font-size:11px;font-weight:600;color:#4a3d30;width:90px;flex-shrink:0}
.prog-bar-bg_h{flex:1;height:8px;background:#f0ebe4;border-radius:4px;overflow:hidden}
.prog-bar-fill_h{height:100%;border-radius:4px;animation:slideRight_h 1s cubic-bezier(0.22,1,0.36,1) both}
.pf-green{background:#2d5a4e;animation-delay:0.5s}
.pf-amber{background:#c9a84c;animation-delay:0.6s}
.prog-val_h{font-size:11px;font-weight:700;color:#6b5e50;width:32px;text-align:left;direction:ltr;flex-shrink:0}
</style>
""", unsafe_allow_html=True)

    # Hero منقول لـ navbar.py

    # ---- Body: بطاقات الأقسام ----
    st.markdown(
        '<div class="hw-body">'
        '<div class="sec-label_h" style="margin-top:4px">الأقسام الرئيسية</div>'
        '<div class="nav-grid_h">'
        '<div class="ncard_h green"><div class="nc-icon_h bg-g">&#x1F4DD;</div><div class="nc-title_h">عقود البيع</div><div class="nc-sub_h">إنشاء وإدارة</div></div>'
        '<div class="ncard_h amber"><div class="nc-icon_h bg-a">&#x1F91D;</div><div class="nc-title_h">القسمة الرضائية</div><div class="nc-sub_h">توزيع الميراث</div></div>'
        '<div class="ncard_h terr"><div class="nc-icon_h bg-t">&#x1F4C2;</div><div class="nc-title_h">الأرشيف</div><div class="nc-sub_h">المعاملات</div></div>'
        '<div class="ncard_h sage"><div class="nc-icon_h bg-s">&#x1F33E;</div><div class="nc-title_h">حاسبة الأراضي</div><div class="nc-sub_h">فدان . قيراط</div></div>'
        '<div class="ncard_h warm"><div class="nc-icon_h bg-w">&#x2696;&#xFE0F;</div><div class="nc-title_h">المواريث</div><div class="nc-sub_h">توزيع التركات</div></div>'
        '<div class="ncard_h muted"><div class="nc-icon_h bg-m">&#x1F6A8;</div><div class="nc-title_h">سجل المحاضر</div><div class="nc-sub_h">متابعة</div></div>'
        '</div>',
        unsafe_allow_html=True
    )

    # ---- Chart + Recent ----
    st.markdown(
        '<div class="lower_h">'
        '<div class="chart-box_h">'
        '<div class="chart-head_h">'
        '<div class="ch-title_h">نشاط آخر 6 أشهر</div>'
        '<div class="ch-leg">'
        '<div class="ld"><span class="ld-g"></span>عقود</div>'
        '<div class="ld"><span class="ld-a"></span>الشهر الحالي</div>'
        '</div></div>'
        '<div class="bars-area_h">' + bars_html + '</div>'
        '</div>'
        '<div class="recent-box_h">'
        '<div class="rb-title_h">آخر المعاملات</div>'
        + recent_html +
        '</div>'
        '</div>',
        unsafe_allow_html=True
    )

    # ---- Progress Bars ----
    st.markdown(
        '<div class="prog-sect">'
        '<div class="prog-title_h">نسبة أنواع المعاملات</div>'
        '<div class="prog-row_h">'
        '<div class="prog-icon_h">&#x1F4DD;</div>'
        '<div class="prog-label_h">عقود بيع</div>'
        '<div class="prog-bar-bg_h"><div class="prog-bar-fill_h pf-green" style="width:' + str(sales_pct) + '%"></div></div>'
        '<div class="prog-val_h">' + str(sales_pct) + '%</div>'
        '</div>'
        '<div class="prog-row_h">'
        '<div class="prog-icon_h">&#x1F91D;</div>'
        '<div class="prog-label_h">قسمات</div>'
        '<div class="prog-bar-bg_h"><div class="prog-bar-fill_h pf-amber" style="width:' + str(kesma_pct) + '%"></div></div>'
        '<div class="prog-val_h">' + str(kesma_pct) + '%</div>'
        '</div>'
        '</div>'
        '</div>'   
        '</div>',
        unsafe_allow_html=True
    )
