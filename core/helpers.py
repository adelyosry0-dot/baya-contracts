from datetime import date

def get_age_from_id(nat_id):
    if not nat_id: return ""
    nat_id = str(nat_id).strip()
    if len(nat_id) == 14 and nat_id.isdigit():
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
        
        if n <= 10: word = units[n]
        elif 11 <= n <= 19: word = teens[n-10]
        else:
            t = n // 10
            u = n % 10
            if u == 0: word = tens[t]
            elif u == 1: word = f"واحد و{tens[t]}"
            elif u == 2: word = f"اثنان و{tens[t]}"
            else: word = f"{units[u]} و{tens[t]}"
        
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

    if f_int > 0: parts.append(num_to_word(f_int, 'f'))
    if k_int > 0: parts.append(num_to_word(k_int, 'k'))
    if s_int > 0 or s_frac > 0:
        if s_int > 0:
            s_str = num_to_word(s_int, 's')
            if s_frac == 0.5: s_str += " ونصف"
            elif s_frac == 0.25: s_str += " وربع"
            elif s_frac == 0.75: s_str += " وثلاثة أرباع"
            parts.append(s_str)
        else:
            if s_frac == 0.5: parts.append("نصف سهم")
            elif s_frac == 0.25: parts.append("ربع سهم")
            elif s_frac == 0.75: parts.append("ثلاثة أرباع سهم")
            else: parts.append(f"{s_frac} سهم") 

    if not parts: return "صفر"
    return " و ".join(parts) + " فقط لا غير"

def tafqeet_money(amount_str):
    if not amount_str: return ""
    try:
        clean_str = str(amount_str).replace(',', '').replace(' ', '')
        num = int(float(clean_str))
        if num <= 0: return ""
        
        units = ["", "واحد", "اثنان", "ثلاثة", "أربعة", "خمسة", "ستة", "سبعة", "ثمانية", "تسعة"]
        teens = ["عشرة", "أحد عشر", "اثنا عشر", "ثلاثة عشر", "أربعة عشر", "خمسة عشر", "ستة عشر", "سبعة عشر", "ثمانية عشر", "تسعة عشر"]
        tens = ["", "عشرة", "عشرون", "ثلاثون", "أربعون", "خمسون", "ستون", "سبعون", "ثمانون", "تسعون"]
        hundreds = ["", "مائة", "مائتان", "ثلاثمائة", "أربعمائة", "خمسمائة", "ستمائة", "سبعمائة", "ثمانمائة", "تسعمائة"]

        def convert_group(n):
            if n == 0: return ""
            h = n // 100
            rest = n % 100
            res = []
            if h > 0: res.append(hundreds[h])
            if rest > 0:
                if rest < 10: res.append(units[rest])
                elif rest < 20: res.append(teens[rest - 10])
                else:
                    t = rest // 10
                    u = rest % 10
                    if u > 0: res.append(units[u] + " و" + tens[t])
                    else: res.append(tens[t])
            return " و ".join(res)

        parts = []
        m = num // 1000000
        rest = num % 1000000
        th = rest // 1000
        u = rest % 1000

        if m > 0:
            if m == 1: parts.append("مليون")
            elif m == 2: parts.append("مليونان")
            elif 3 <= m <= 10: parts.append(convert_group(m) + " ملايين")
            else: parts.append(convert_group(m) + " مليون")

        if th > 0:
            if th == 1: parts.append("ألف")
            elif th == 2: parts.append("ألفان")
            elif 3 <= th <= 10: parts.append(convert_group(th) + " آلاف")
            else: parts.append(convert_group(th) + " ألف")

        if u > 0: parts.append(convert_group(u))

        final_text = " و ".join(parts).replace(" و  و ", " و ").replace("  ", " ").strip()
        return f"{final_text} جنيهاً مصرياً لا غير"
    except: return ""

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
        if mode == "short": return f"{d.day}/{d.month}/{d.year}"
        days_ar = ["الاثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت", "الأحد"]
        day_name = days_ar[d.weekday()]
        return f"{day_name} الموافق {d.day}/{d.month}/{d.year}"
    except: return iso_str

def shorten_name(full_name, limit=3):
    if not full_name: return ""
    clean = full_name.replace("/", " ").replace("\\", " ").strip()
    words = clean.split()
    if "ورثة" in words or "المرحوم" in words: return " ".join(words[:limit+2])
    return " ".join(words[:limit])