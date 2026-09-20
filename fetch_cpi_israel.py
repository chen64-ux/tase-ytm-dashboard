# -*- coding: utf-8 -*-
"""
fetch_cpi_israel.py
שולף את מדד המחירים לצרכן (הלמ"ס) ומחשב שינוי חודשי ושינוי שנתי, לצורך
עדכון אוטומטי של weekly_cpi_israel.json (השורה "מדד המחירים לישראל"
בטבלת המאקרו של הסקירה השבועית) - עד 20/09/2026 הקובץ הזה עודכן רק
ידנית ונשאר עם נתוני הדוגמה המקוריים מאז הקמת הפרויקט, בלי שאף אחד
שם לב (הטבלה בדשבורד המשיכה להציג את אותם נתונים ישנים בכל שבוע).

הלמ"ס חסום מ-GitHub Actions (IP בענן, בדיוק כמו ביזפורטל ובנק ישראל)
אבל עובד תקין מהמחשב המקומי - לכן זה מיועד לרוץ מתוך run_daily_local.py
(לא בתוך workflow בענן), וכותב JSON שנקרא בהמשך ע"י fetch_weekly_review.py
(דרך run_weekly_review.py, שכבר יודע לקרוא את הקובץ הזה אם הוא קיים).

עדכון 20/09/2026: ה-endpoint הישן ששימש כאן (וגם את הסקיל fetch_cpi_cbs.py
הקיים) - www.cbs.gov.il/he/Pages/apiDefaultAspx.aspx - הפסיק לעבוד: הוא
עדיין מחזיר HTTP 200, אבל עם עמוד HTML קטן שמפנה בג'אווהסקריפט
(function go2cbs) לדף הבית, ולא JSON אמיתי. הלמ"ס עברו ל-API חדש בדומיין
api.cbs.gov.il (מתועד בעמוד cbs.gov.il/en/Pages/Api-interface.aspx),
עם endpoint ייעודי לנתוני מדדים: /index/data/price?id=<קוד>&format=json
&lang=en&last=<מס' תקופות אחרונות>. פריט 120010 ("מדד המחירים לצרכן -
כללי") נשאר אותו קוד גם ב-API החדש.

הערה חשובה: לא הצלחתי לאמת ישירות את שמות השדות המדויקים בתגובת ה-JSON
של ה-API החדש (גם הסביבה ששימשה לכתיבת הקוד הזה חסומה מ-cbs.gov.il/
api.cbs.gov.il, בדיוק כמו GitHub Actions - למ"ס חוסמים לפי IP ישראלי
בלבד לפי התיעוד הרשמי). לכן הפרסינג למטה (_find_index_records/
_extract_year_month/_extract_value) כללי וסובלני: הוא מחפש ברשימות
שבתגובה כל רשימה של רשומות (dict) שיש לה גם שדה שנה/תקופה וגם שדה ערך,
בלי תלות בשם מדויק של השדה - כדי לתת סיכוי טוב להצליח גם אם ניחשתי לא
מדויק. אם זה עדיין ייכשל בריצה האמיתית (מהמחשב בישראל) - ה-RuntimeError
כולל את תחילת ה-JSON הגולמי בפועל, בדיוק כמו שקרה עם ה-endpoint הישן,
כדי שהריצה הבאה תיתן מספיק מידע לתיקון מדויק בלי עוד סיבוב ניחושים.
"""

import datetime
import json
import re
import sys

import requests

ITEM_ID = "120010"  # מדד המחירים לצרכן - כללי
CBS_API_URL = "https://api.cbs.gov.il/index/data/price"

HEADERS = {
    # הלמ"ס חוסמים לפי התיעוד user-agent-ים גנריים/של בוטים - חשוב
    # להישאר עם UA שנראה כמו דפדפן אמיתי.
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.cbs.gov.il/",
}

MONTH_NAMES = [
    "ינואר", "פברואר", "מרס", "אפריל", "מאי", "יוני",
    "יולי", "אוגוסט", "ספטמבר", "אוקטובר", "נובמבר", "דצמבר",
]

_PERIOD_KEY_HINTS = ("period", "date", "tkufa", "תקופה", "תאריך")
_VALUE_KEY_EXACT = ("value", "currentvalue", "indexvalue", "ervach", "arach")
_INDEX_KEY_EXACT = ("index", "arach", "ervach")


def _find_index_records(data):
    """מחפש רקורסיבית בתוך ה-JSON (רשימות/dict-ים מקוננים) רשימה של
    רשומות שנראית כמו נתוני מדד: לכל רשומה יש גם שדה שדומה לשנה/תקופה
    וגם שדה שדומה לערך. לא מניח מראש את שמות השדות המדויקים."""
    found = []

    def looks_like_records(lst):
        if not lst or not all(isinstance(x, dict) for x in lst):
            return False
        keys_lower = [k.lower() for k in lst[0].keys()]
        has_value = any(
            ("value" in k and "id" not in k) or k in _INDEX_KEY_EXACT
            for k in keys_lower
        )
        has_period = any(
            "year" in k or "month" in k or "period" in k or "date" in k or "tkufa" in k
            for k in keys_lower
        )
        return has_value and has_period

    def walk(o):
        if isinstance(o, list):
            if looks_like_records(o):
                found.append(o)
            for item in o:
                walk(item)
        elif isinstance(o, dict):
            for v in o.values():
                walk(v)

    walk(data)
    found.sort(key=len, reverse=True)
    return found[0] if found else None


def _extract_year_month(rec):
    keys_lower = {k: k.lower() for k in rec.keys()}
    year = month = None
    for k, kl in keys_lower.items():
        if year is None and ("year" in kl or kl == "shana"):
            try:
                year = int(float(rec[k]))
            except (TypeError, ValueError):
                pass
        if month is None and (
            kl == "month" or kl == "chodesh" or (kl.startswith("month") and "name" not in kl)
        ):
            try:
                month = int(float(rec[k]))
            except (TypeError, ValueError):
                pass
    if year and month:
        return year, month

    for k, kl in keys_lower.items():
        if any(hint in kl for hint in _PERIOD_KEY_HINTS):
            s = str(rec[k])
            m = re.match(r"^(\d{4})[-/]?[Mm]?(\d{1,2})$", s)
            if m:
                return int(m.group(1)), int(m.group(2))
            m = re.match(r"^(\d{1,2})[-/](\d{4})$", s)
            if m:
                return int(m.group(2)), int(m.group(1))
    return None, None


def _extract_value(rec):
    keys_lower = {k: k.lower() for k in rec.keys()}
    for k, kl in keys_lower.items():
        if kl in _VALUE_KEY_EXACT:
            try:
                return float(rec[k])
            except (TypeError, ValueError):
                pass
    for k, kl in keys_lower.items():
        if "value" in kl and "id" not in kl:
            try:
                return float(rec[k])
            except (TypeError, ValueError):
                pass
    for k, kl in keys_lower.items():
        if kl in _INDEX_KEY_EXACT or ("index" in kl and "id" not in kl and "name" not in kl):
            try:
                return float(rec[k])
            except (TypeError, ValueError):
                pass
    return None


def _parse_api_response(data):
    """ממיר תגובת JSON מה-API של הלמ"ס ל-dict: {(year, month): value}."""
    records = _find_index_records(data)
    if not records:
        return {}
    cpi = {}
    for rec in records:
        if not isinstance(rec, dict):
            continue
        year, month = _extract_year_month(rec)
        val = _extract_value(rec)
        if year and month and val:
            cpi[(year, month)] = val
    return cpi


def fetch_cpi_series(months_back: int = 40):
    """שולף את סדרת המדד מה-API של הלמ"ס, כ-40 חודשים אחורה - מספיק כדי
    לחשב שינוי שנתי גם לחודש האחרון וגם לחודש שלפניו (לצורך ההשוואה
    "אינפלציה שנתית עלתה/ירדה מ-X% ל-Y%"), עם מרווח ביטחון."""
    url = f"{CBS_API_URL}?id={ITEM_ID}&format=json&lang=en&last={months_back}"
    resp = requests.get(url, headers=HEADERS, timeout=30)

    # אותה גישה שכבר הוכיחה את עצמה עם ה-endpoint הישן (חשפה בדיוק את
    # עמוד ה-HTML שהחזיר במקום JSON): לא לנחש בעיוורון למה json.loads
    # נכשל - לצרף תמיד סטטוס + תחילת הגוף הגולמי להודעת השגיאה.
    if resp.status_code != 200:
        raise RuntimeError(f"status={resp.status_code}, תחילת התגובה: {resp.text[:300]!r}")
    try:
        data = resp.json()
    except ValueError as e:
        raise RuntimeError(
            f"התגובה אינה JSON תקין ({e}) - סטטוס={resp.status_code}, "
            f"אורך גוף התגובה={len(resp.text)}, תחילת התגובה הגולמית: {resp.text[:300]!r}"
        ) from e

    cpi = _parse_api_response(data)
    if not cpi:
        raise RuntimeError(
            "ה-API החזיר JSON תקין אך לא זוהתה בו רשימת רשומות מדד "
            "(שדות שנה/תקופה+ערך) - ייתכן ששמות השדות שונים ממה שצפינו. "
            f"מבנה התגובה (400 התווים הראשונים): {json.dumps(data, ensure_ascii=False)[:400]!r}"
        )
    return cpi


def compute_cpi_summary(cpi: dict):
    """מקבל dict {(year, month): value} ומחזיר (result, error).
    result הוא {"value": "...", "note": "..."} - בדיוק הפורמט
    ש-run_weekly_review.py מצפה לו (שדות value/note בweekly_cpi_israel.json)."""
    if not cpi:
        return None, "לא התקבלו נתונים מה-API של הלמ\"ס"

    latest_key = max(cpi.keys())
    latest_year, latest_month = latest_key
    prev_key = (latest_year, latest_month - 1) if latest_month > 1 else (latest_year - 1, 12)

    if prev_key not in cpi:
        return None, f"חסר נתון לחודש הקודם ({prev_key[1]}/{prev_key[0]}) - לא ניתן לחשב שינוי חודשי"

    monthly_pct = (cpi[latest_key] / cpi[prev_key] - 1) * 100

    note_parts = [f"מדד {MONTH_NAMES[latest_month - 1]} {latest_year} (למ\"ס)"]

    latest_yoy_key = (latest_year - 1, latest_month)
    prev_yoy_key = (prev_key[0] - 1, prev_key[1])
    if latest_yoy_key in cpi:
        annual_now = (cpi[latest_key] / cpi[latest_yoy_key] - 1) * 100
        if prev_yoy_key in cpi:
            annual_prev = (cpi[prev_key] / cpi[prev_yoy_key] - 1) * 100
            if annual_now > annual_prev + 0.05:
                direction = "עלתה"
            elif annual_now < annual_prev - 0.05:
                direction = "ירדה"
            else:
                direction = "נותרה יציבה סביב"
            note_parts.append(f"אינפלציה שנתית {direction} מ-{annual_prev:.1f}% ל-{annual_now:.1f}%")
        else:
            note_parts.append(f"אינפלציה שנתית: {annual_now:.1f}%")

    result = {
        "value": f"{monthly_pct:+.1f}% חודשי",
        "note": "; ".join(note_parts),
    }
    return result, None


def fetch_and_summarize():
    """עוטף fetch_cpi_series + compute_cpi_summary עם טיפול בחריגות רשת,
    כדי שrun_daily_local.py יוכל לקרוא לזה בבטחה בלי try/except משלו.
    מחזיר (result_or_None, error_or_None) - אף פעם לא זורק חריגה."""
    try:
        cpi = fetch_cpi_series()
    except Exception as e:
        return None, f"שגיאת רשת מול הלמ\"ס: {e}"
    return compute_cpi_summary(cpi)


def main():
    out_path = sys.argv[1] if len(sys.argv) > 1 else "weekly_cpi_israel.json"
    result, err = fetch_and_summarize()
    if err:
        print(f"⚠️  עדכון מדד המחירים לצרכן נכשל: {err}")
        sys.exit(1)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"✅ מדד המחירים לצרכן (למ\"ס): {result['value']} - {result['note']}")


if __name__ == "__main__":
    main()
