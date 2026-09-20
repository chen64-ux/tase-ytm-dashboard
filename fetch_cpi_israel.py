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

המקור: אותו API רשמי של הלמ"ס ששימש את fetch_cpi_cbs.py (הסקיל
לעדכון מדד בקובץ אג"ח חברות) - פריט 120010, "מדד המחירים לצרכן -
כללי", בסיס ממוצע 2024=100.
"""

import datetime
import json
import sys

import requests

ITEM_ID = "120010"  # מדד המחירים לצרכן - כללי
CBS_API_URL = (
    "https://www.cbs.gov.il/he/Pages/apiDefaultAspx.aspx"
    "?req=getData&id={item_id}&firstyear={firstyear}&lastyear={lastyear}"
    "&aggs=monthly&base=avg2024&format=json"
)

HEADERS = {
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


def _parse_api_response(data):
    """ממיר תגובת API ל-dict: {(year, month): value}. מטפל בכמה צורות
    JSON אפשריות (כמו fetch_cpi_cbs.py הקיים, שממנו נלקחה הלוגיקה)."""
    cpi = {}
    records = (
        data.get("data") or data.get("Data") or
        data.get("results") or data.get("Results") or []
    )
    if not records and isinstance(data, list):
        records = data
    for rec in records:
        if not isinstance(rec, dict):
            continue
        year = int(rec.get("year") or rec.get("Year") or rec.get("שנה") or 0)
        month = int(rec.get("month") or rec.get("Month") or rec.get("חודש") or 0)
        val = rec.get("value") or rec.get("Value") or rec.get("ערך") or 0
        if year and month and val:
            cpi[(year, month)] = float(val)
    return cpi


def fetch_cpi_series(years_back: int = 3):
    """שולף את סדרת המדד מה-API הרשמי של הלמ"ס, 3 שנים אחורה - מספיק
    כדי לחשב שינוי שנתי גם לחודש האחרון וגם לחודש שלפניו (לצורך
    ההשוואה "אינפלציה שנתית עלתה/ירדה מ-X% ל-Y%")."""
    this_year = datetime.date.today().year
    url = CBS_API_URL.format(item_id=ITEM_ID, firstyear=this_year - years_back, lastyear=this_year)
    resp = requests.get(url, headers=HEADERS, timeout=30)

    # נצפה בפועל (20/09/2026, ריצה ראשונה): הלמ"ס החזיר תגובה שנכשלה על
    # json.loads עם "Expecting value: line 1 column 1 (char 0)" - שגיאה
    # גנרית שלא אומרת אם זה גוף ריק, עמוד HTML/שגיאה, או משהו אחר. כדי
    # לא לנחש שוב בעיוורון (כמו שקרה עם NY Fed/ביזפורטל בעבר) - במקום
    # resp.raise_for_status() +resp.json() ישירים, בודקים סטטוס ידנית
    # ומצרפים את תחילת הגוף הגולמי להודעת השגיאה, כדי שהריצה הבאה תיתן
    # מספיק מידע לאבחון מדויק בלי צורך בעוד סיבוב ניחושים.
    if resp.status_code != 200:
        raise RuntimeError(f"status={resp.status_code}, תחילת התגובה: {resp.text[:300]!r}")
    try:
        data = resp.json()
    except ValueError as e:
        raise RuntimeError(
            f"התגובה אינה JSON תקין ({e}) - סטטוס={resp.status_code}, "
            f"אורך גוף התגובה={len(resp.text)}, תחילת התגובה הגולמית: {resp.text[:300]!r}"
        ) from e
    return _parse_api_response(data)


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
