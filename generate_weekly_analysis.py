# -*- coding: utf-8 -*-
"""
generate_weekly_analysis.py
מפעיל את Claude (דרך ה-API של Anthropic, עם כלי חיפוש אינטרנט) כדי
לחקור ולכתוב ניתוח שבועי אנליטי - אירועים/מגמות של השבוע שחלף,
מניות וסקטורים בולטים בישראל ובארה"ב, ומבט קדימה לשבוע הבא.

*** עלות: זו קריאת API בתשלום (טוקנים + חיפושי אינטרנט) - לא חינמי
    כמו שאר הסקריפטים בפרויקט. עלות משוערת לריצה: כמה סנטים עד
    כדולר בודד, תלוי בהיקף החיפושים שהמודל בוחר לבצע. ***

מפתח ה-API: **אף פעם לא בקובץ הזה, ולא ב-repo** (הוא ציבורי ב-GitHub).
נקרא אך ורק ממשתנה סביבה בשם ANTHROPIC_API_KEY:
  - בריצה מקומית (Windows): משתני סביבה של המשתמש -> New -> שם
    ANTHROPIC_API_KEY, ערך המפתח (מ-console.anthropic.com -> API Keys).
    לא ב-cmd/PowerShell (זה נשמר בהיסטוריית הפקודות) - דרך ה-GUI:
    Win -> "environment variables" -> "Edit environment variables for
    your account".
  - בריצה ב-GitHub Actions: Settings -> Secrets and variables ->
    Actions -> New repository secret, בשם ANTHROPIC_API_KEY. ה-workflow
    מעביר אותו כ-secret מוצפן, לא כטקסט גלוי בקובץ ה-yml.

אם המשתנה לא מוגדר, הסקריפט נכשל עם הודעה ברורה (ולא כותב shell
כלשהו) - כך שריצה שבועית שבה עדיין לא הוגדר מפתח פשוט מדלגת על
הניתוח האנליטי (run_weekly_review.py תופס את זה ומדלג בעדינות), בלי
לחסום את שאר הסקירה השבועית (הטבלאות האוטומטיות).

שימוש:
    python generate_weekly_analysis.py 2026-09-04 2026-09-11
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime

import requests

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

MODEL = "claude-sonnet-5"
API_URL = "https://api.anthropic.com/v1/messages"

PROMPT_TEMPLATE = """כתוב ניתוח שבועי אנליטי לשוק ההון עבור השבוע {start_date} עד {end_date}.

חובה להשתמש בכלי החיפוש כדי לוודא שהמידע עדכני ומדויק לגבי השבוע הספציפי הזה - אל
תסתמך על ידע כללי/ישן בלבד. חפש בנפרד על: מדדי מניות מרכזיים (ת"א, S&P500, נאסד"ק),
אירועי מאקרו/ריבית מהשבוע, ומניות/סקטורים בולטים בישראל ובארה"ב.

כלול חמישה חלקים, כל אחד 2-5 משפטים בעברית, בסגנון תמציתי ואנליטי (לא רק תיאור
יבש של מספרים - גם הסבר "למה" ומה המשמעות):

1. summary - תמצית מנהלים: הנושא/האירוע המרכזי שהוביל את השבוע
2. past_week_events - אירועים ומגמות מרכזיות בשווקים ובמאקרו השבוע (ישראל וארה"ב/עולם)
3. notable_stocks_il - מניות וסקטורים בולטים בבורסת תל אביב השבוע, עם הסבר קצר לסיבה
4. notable_stocks_us - מניות וסקטורים בולטים בארה"ב השבוע, עם הסבר קצר לסיבה
5. outlook_next_week - אירועים/נתונים כלכליים צפויים בשבוע הבא שכדאי לעקוב אחריהם

השב אך ורק ב-JSON תקני בפורמט הבא, בלי שום טקסט, כותרת, או ```json לפני/אחרי:
{{"summary": "...", "past_week_events": "...", "notable_stocks_il": "...", "notable_stocks_us": "...", "outlook_next_week": "..."}}
"""


def extract_final_text(content_blocks):
    """מחלץ את הטקסט הסופי מהתגובה - יכולה להכיל בלוקים מעורבים (טקסט +
    חיפושים) כשמשתמשים בכלי web_search."""
    texts = [b["text"] for b in content_blocks if b.get("type") == "text"]
    if not texts:
        raise RuntimeError("לא נמצא טקסט בתגובת ה-API")
    return texts[-1]


def parse_json_response(raw_text):
    cleaned = re.sub(r"^```json\s*|\s*```$", "", raw_text.strip())
    return json.loads(cleaned)


def generate(start_date: str, end_date: str) -> dict:
    if not ANTHROPIC_API_KEY:
        raise RuntimeError(
            "משתנה הסביבה ANTHROPIC_API_KEY לא מוגדר - ראה ההסבר בראש הקובץ "
            "(אין ולא יהיה מפתח שמור בקובץ הזה או ב-repo, כי הוא ציבורי)."
        )

    prompt = PROMPT_TEMPLATE.format(start_date=start_date, end_date=end_date)

    resp = requests.post(
        API_URL,
        headers={
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": MODEL,
            "max_tokens": 4000,
            "tools": [{"type": "web_search_20250305", "name": "web_search"}],
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=180,
    )

    if resp.status_code != 200:
        raise RuntimeError(f"קריאת ה-API נכשלה: status={resp.status_code}, {resp.text[:500]}")

    data = resp.json()
    raw_text = extract_final_text(data.get("content", []))
    result = parse_json_response(raw_text)

    required_keys = ["summary", "past_week_events", "notable_stocks_il", "notable_stocks_us", "outlook_next_week"]
    missing = [k for k in required_keys if k not in result]
    if missing:
        raise RuntimeError(f"חסרים שדות בתשובת ה-API: {missing}")

    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("start_date", help="YYYY-MM-DD")
    ap.add_argument("end_date", help="YYYY-MM-DD")
    args = ap.parse_args()

    print(f"מבקש מ-Claude לחקור ולכתוב ניתוח לשבוע {args.start_date} - {args.end_date}...")
    print("(זה עשוי לקחת דקה-שתיים, בגלל החיפושים)")

    result = generate(args.start_date, args.end_date)

    with open("weekly_analysis.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print("\n✅ נשמר ל-weekly_analysis.json:")
    for k, v in result.items():
        print(f"\n--- {k} ---")
        print(v)


if __name__ == "__main__":
    main()
