# -*- coding: utf-8 -*-
"""
fetch_cpi_israel.py
שולף את מדד המחירים לצרכן (הלמ"ס) ומחשב שינוי חודשי ושינוי שנתי, לצורך
עדכון אוטומטי של weekly_cpi_israel.json (השורה "מדד המחירים לישראל"
בטבלת המאקרו של הסקירה השבועית).

הלמ"ס חסום מ-GitHub Actions (IP בענן, בדיוק כמו ביזפורטל ובנק ישראל)
אבל עובד תקין מהמחשב המקומי - לכן זה מיועד לרוץ מתוך run_daily_local.py
(לא בתוך workflow בענן), וכותב JSON שנקרא בהמשך ע"י fetch_weekly_review.py
(דרך run_weekly_review.py, שכבר יודע לקרוא את הקובץ הזה אם הוא קיים).

עדכון 20/09/2026: ה-endpoint הישן (www.cbs.gov.il/he/Pages/apiDefaultAspx.aspx)
הפסיק לעבוד - הלמ"ס עברו ל-API חדש בדומיין api.cbs.gov.il. תיקון ראשון
עבר לכתובת הנכונה (api.cbs.gov.il/index/data/price) אבל ניחש לא נכון
את מבנה ה-JSON; ריצה אמיתית מהמחשב (20/09, 11:19) חשפה את המבנה
האמיתי, ולפיו נכתב הפרסינג הסופי כאן:

    {
      "month": [
        {
          "code": 120010,
          "name": "Consumer Price Index - General",
          "date": [
            {"year": 2026, "month": 8, "monthDesc": "August",
             "percent": 0.7, "percentYear": 1.5,
             "currBase": {"baseDesc": "Average 2024", "value": 105.8},
             "prevBase": null},
            {"year": 2026, "month": 7, ...},
            ...
          ]
        }
      ]
    }

חשוב: ה-API כבר מחזיר "percent" (שינוי חודשי, באחוזים) ו-"percentYear"
(שינוי שנתי/אינפלציה שנתית, באחוזים) מחושבים מראש לכל רשומה - אז אין
צורך לחשב אותם ידנית מתוך ערכי המדד הגולמיים (currBase.value); זה גם
נמנע מאי-התאמות עגילה/בסיס מול החישוב הרשמי של הלמ"ס.
"""

import datetime
import json
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


def _extract_date_records(data):
    """שולף את רשימת ה-"date" (רשומות חודשיות) מתוך מבנה התגובה
    המאומת: data["month"][0]["date"]. מחזיר [] אם המבנה לא כצפוי,
    כדי שfetch_cpi_series יזרוק שגיאה מפורטת עם התגובה הגולמית
    (ולא ייכשל בצורה עמומה/עם KeyError)."""
    if not isinstance(data, dict):
        return []
    months = data.get("month")
    if not isinstance(months, list) or not months:
        return []
    first = months[0]
    if not isinstance(first, dict):
        return []
    records = first.get("date")
    if not isinstance(records, list):
        return []
    return [r for r in records if isinstance(r, dict)]


def fetch_cpi_series(months_back: int = 6):
    """שולף מה-API של הלמ"ס את {months_back} החודשים האחרונים של המדד
    (כולל percent/percentYear מחושבים מראש ע"י הלמ"ס עצמם). 6 חודשים
    מספיק בהרבה כדי שגם לחודש האחרון וגם לקודם לו יהיה percentYear,
    לצורך ההשוואה "אינפלציה שנתית עלתה/ירדה".
    מחזיר רשימת רשומות ממוינת מהחדש לישן (לפי year,month)."""
    url = f"{CBS_API_URL}?id={ITEM_ID}&format=json&lang=en&last={months_back}"
    resp = requests.get(url, headers=HEADERS, timeout=30)

    if resp.status_code != 200:
        raise RuntimeError(f"status={resp.status_code}, תחילת התגובה: {resp.text[:300]!r}")
    try:
        data = resp.json()
    except ValueError as e:
        raise RuntimeError(
            f"התגובה אינה JSON תקין ({e}) - סטטוס={resp.status_code}, "
            f"אורך גוף התגובה={len(resp.text)}, תחילת התגובה הגולמית: {resp.text[:300]!r}"
        ) from e

    records = _extract_date_records(data)
    records = [r for r in records if r.get("year") and r.get("month") and r.get("percent") is not None]
    if not records:
        raise RuntimeError(
            "ה-API החזיר JSON תקין אך לא נמצאו בו רשומות עם year/month/percent תקינים "
            f"- מבנה התגובה (400 התווים הראשונים): {json.dumps(data, ensure_ascii=False)[:400]!r}"
        )
    records.sort(key=lambda r: (r["year"], r["month"]), reverse=True)
    return records


def compute_cpi_summary(records):
    """מקבל רשימת רשומות (ממוינות מהחדש לישן, כל אחת עם year/month/
    percent/percentYear כמו שה-API מחזיר) ומחזיר (result, error).
    result הוא {"value": "...", "note": "..."} - בדיוק הפורמט
    ש-run_weekly_review.py מצפה לו (שדות value/note בweekly_cpi_israel.json)."""
    if not records:
        return None, "לא התקבלו נתונים מה-API של הלמ\"ס"

    latest = records[0]
    year, month = latest["year"], latest["month"]
    monthly_pct = latest["percent"]
    annual_now = latest.get("percentYear")

    note_parts = [f"מדד {MONTH_NAMES[month - 1]} {year} (למ\"ס)"]

    if annual_now is not None:
        annual_prev = records[1].get("percentYear") if len(records) > 1 else None
        if annual_prev is not None:
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
        records = fetch_cpi_series()
    except Exception as e:
        return None, f"שגיאת רשת מול הלמ\"ס: {e}"
    return compute_cpi_summary(records)


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
