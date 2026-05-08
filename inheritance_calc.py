# inheritance_calc.py
from fractions import Fraction

def format_area(total_sahm):
    """تحويل إجمالي الأسهم إلى فدان وقيراط وسهم"""
    faddan = int(total_sahm // 576)
    remainder = total_sahm % 576
    qirat = int(remainder // 24)
    sahm = round(remainder % 24, 2)
    return faddan, qirat, sahm

def calculate_shares(faddan, qirat, sahm, has_wife, has_father, has_mother, sons_count, daughters_count):
    """حساب المواريث للحالة الأساسية (زوجة، أب، أم، أبناء، بنات)"""
    # 1. تحويل كل المساحة لأسهم
    total_sahms = float((faddan * 576) + (qirat * 24) + sahm)
    
    shares = {}
    remaining_fraction = Fraction(1, 1) # التركة كاملة = 1
    has_children = (sons_count > 0 or daughters_count > 0)
    
    # 2. حساب أصحاب الفروض
    if has_wife:
        wife_share = Fraction(1, 8) if has_children else Fraction(1, 4)
        shares['wife'] = wife_share
        remaining_fraction -= wife_share
        
    if has_father:
        father_share = Fraction(1, 6) if has_children else Fraction(0, 1) # مبسطة، الأب له أحوال أخرى بالتعصيب
        shares['father'] = father_share
        remaining_fraction -= father_share
        
    if has_mother:
        mother_share = Fraction(1, 6) if has_children else Fraction(1, 3) # مبسطة (الثلث أو السدس)
        shares['mother'] = mother_share
        remaining_fraction -= mother_share

    # 3. حساب العصبة (الأبناء والبنات)
    if has_children:
        total_parts = (sons_count * 2) + daughters_count
        if total_parts > 0:
            part_value = remaining_fraction / total_parts
            if sons_count > 0:
                shares['son'] = part_value * 2
            if daughters_count > 0:
                shares['daughter'] = part_value

    # 4. تحويل الكسور لمساحات فعلية
    results = {}
    for heir, fraction in shares.items():
        heir_sahms = total_sahms * float(fraction)
        f, q, s = format_area(heir_sahms)
        results[heir] = {"f": f, "q": q, "s": s, "total_sahms": heir_sahms}
        
    return results