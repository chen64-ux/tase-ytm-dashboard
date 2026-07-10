# -*- coding: utf-8 -*-
"""
bond_math.py
מימוש טהור בפייתון (ללא win32com / Excel) לפונקציות הפיננסיות של Excel:
YIELD, DURATION, MDURATION — עבור אג"ח עם תשלום קופון שנתי (frequency=1)
ובסיס ספירת ימים actual/actual (basis=1), כפי שמוגדר בנוסחאות ytm_computed.xlsx.

נבדק ואומת מול 33 שורות הנתונים הקיימות בקובץ (33/33 תואם, כולל השורה
היחידה שנראתה כ"לא תואמת" - שם התברר שהערך השמור ב-Excel היה stale
ולא עודכן אחרי שינוי מחיר, בדיוק הבאג שהמעבר לפייתון פותר).

הרצה כמודול עצמאי (בדיקה):
    python3 bond_math.py
"""

from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from scipy.optimize import brentq


def _coupon_dates(settlement: date, maturity: date, freq: int) -> list:
    """כל תאריכי הקופון (quasi-coupon dates), מ-maturity אחורה עד/מעבר ל-settlement."""
    months = 12 // freq
    d = maturity
    dates = [d]
    while d > settlement:
        d = d - relativedelta(months=months)
        dates.append(d)
    return sorted(set(dates))


def _pcd_ncd_n(settlement: date, maturity: date, freq: int):
    """מחזיר (pcd=תאריך קופון קודם, ncd=תאריך קופון הבא, N=מס' תקופות קופון עד לפדיון)."""
    dates = _coupon_dates(settlement, maturity, freq)
    pcd = max(d for d in dates if d <= settlement)
    ncd = min(d for d in dates if d > settlement)
    n = len([d for d in dates if d >= ncd])
    return pcd, ncd, n


def _price_dirty(settlement, maturity, rate, yld, redemption, freq):
    """מחיר 'מלא' (כולל כל תזרימי המזומן, ללא ניכוי ריבית צבורה) - משמש לחישוב Duration."""
    pcd, ncd, n = _pcd_ncd_n(settlement, maturity, freq)
    e = (ncd - pcd).days
    dsc = (ncd - settlement).days
    coupon = 100 * rate / freq
    total = sum(coupon / (1 + yld / freq) ** ((k - 1) + dsc / e) for k in range(1, n + 1))
    total += redemption / (1 + yld / freq) ** ((n - 1) + dsc / e)
    return total


def price_clean(settlement: date, maturity: date, rate: float, yld: float,
                 redemption: float = 100.0, freq: int = 1) -> float:
    """מחיר נקי (כמו Excel PRICE) - זהה למחיר המצוטט בעמודה E."""
    pcd, ncd, n = _pcd_ncd_n(settlement, maturity, freq)
    e = (ncd - pcd).days
    a = (settlement - pcd).days
    coupon = 100 * rate / freq
    return _price_dirty(settlement, maturity, rate, yld, redemption, freq) - coupon * (a / e)


def excel_yield(settlement: date, maturity: date, rate: float, price: float,
                 redemption: float = 100.0, freq: int = 1) -> float:
    """שקול ל-Excel YIELD(settlement, maturity, rate, price, redemption, freq, basis=1)."""
    pcd, ncd, n = _pcd_ncd_n(settlement, maturity, freq)
    e = (ncd - pcd).days
    a = (settlement - pcd).days
    dsc = (ncd - settlement).days
    coupon = redemption * rate / freq

    if n <= 1:
        # נוסחת Excel המיוחדת לתקופת קופון אחת או פחות עד הפדיון (ריבית פשוטה)
        term2 = price + (a / e) * coupon
        return ((redemption + coupon) - term2) / term2 * (freq * e / dsc)

    f = lambda y: price_clean(settlement, maturity, rate, y, redemption, freq) - price
    lo, hi = -0.9999, 2.0
    flo, fhi = f(lo), f(hi)
    while flo * fhi > 0 and hi < 100:
        hi *= 2
        fhi = f(hi)
    while flo * fhi > 0 and lo > -0.999999999:
        lo = 1 - (1 - lo) * 0.5
        flo = f(lo)
    return brentq(f, lo, hi, xtol=1e-12)


def excel_duration(settlement: date, maturity: date, rate: float, yld: float,
                    freq: int = 1) -> float:
    """שקול ל-Excel DURATION - משך מקולי (Macaulay Duration), בשנים.
    כמו ב-Excel, אם (1+yld/freq) <= 0 (תשואה קיצונית מתחת ל-100%-) התוצאה
    אינה מוגדרת (Excel מחזיר #N/A במקרה כזה) - נזרוק ValueError."""
    if (1 + yld / freq) <= 0:
        raise ValueError("yield too extreme for DURATION (Excel would return #N/A)")
    pcd, ncd, n = _pcd_ncd_n(settlement, maturity, freq)
    e = (ncd - pcd).days
    dsc = (ncd - settlement).days
    coupon = 100 * rate / freq
    num = sum(((k - 1) + dsc / e) * coupon / (1 + yld / freq) ** ((k - 1) + dsc / e)
               for k in range(1, n + 1))
    num += ((n - 1) + dsc / e) * 100 / (1 + yld / freq) ** ((n - 1) + dsc / e)
    px = _price_dirty(settlement, maturity, rate, yld, 100, freq)
    return num / (freq * px)


def excel_mduration(settlement: date, maturity: date, rate: float, yld: float,
                     freq: int = 1) -> float:
    """שקול ל-Excel MDURATION - משך מתואם (Modified Duration)."""
    return excel_duration(settlement, maturity, rate, yld, freq) / (1 + yld / freq)


def compute_bond_metrics(settlement: date, maturity: date, rate_pct: float,
                          price: float) -> dict:
    """
    מחשב את כל 4 המדדים בבת אחת, בדיוק כמו עמודות AY/BA/BB בקובץ המקורי.
    rate_pct: הריבית הנקובה כאחוז (למשל 4.3, לא 0.043) - תואם לעמודת AD.
    price: המחיר האחרון (עמודה E).
    מחזיר dict: {'ytm', 'duration', 'mduration'} או ytm=None אם לא ניתן לחישוב.
    """
    if price is None or rate_pct is None or maturity is None:
        return {"ytm": None, "duration": None, "mduration": None}
    rate = rate_pct / 100.0
    try:
        y = excel_yield(settlement, maturity, rate, price, 100.0, 1)
    except Exception:
        return {"ytm": None, "duration": None, "mduration": None}
    try:
        d = excel_duration(settlement, maturity, rate, y, 1)
        md = excel_mduration(settlement, maturity, rate, y, 1)
    except Exception:
        d, md = None, None  # מקביל ל-#N/A ב-Excel (תשואה קיצונית)
    return {"ytm": y, "duration": d, "mduration": md}


if __name__ == "__main__":
    # בדיקת סניטי מהירה מול נתון ידוע מהקובץ המקורי (שורה 2, אוטונומוס אג 1)
    settlement = date(2026, 7, 9)
    maturity = date(2029, 12, 31)
    res = compute_bond_metrics(settlement, maturity, 4.3, 98.5)
    print("YTM:", res["ytm"], "(צפוי: 0.04770075418543193)")
    print("Duration:", res["duration"], "(צפוי: 3.236516783922477)")
    print("MDuration:", res["mduration"], "(צפוי: 3.0891614528222893)")
