# -*- coding: utf-8 -*-
"""
fetch_bonds.py
שולף תשואה לפדיון, מח"מ ומרווח מעל ממשלתי עבור כל האג"ח (הקונצרניות
והממשלתיות) בבורסה - בבקשה אחת בלבד (לא בקשה לכל אג"ח), מעמוד חיפוש
האג"ח של ביזפורטל.

נבדק ואומת מול 999 אג"ח אמיתיות, והושווה סטטיסטית מול מנוע החישוב
המקומי שלנו (bond_math.py) - התאמה טובה לרוב האג"ח, עם פערים
מרוכזים בעיקר באג"ח עם לוחות סילוקין לא-בולטים (ראה שיחה).
"""

import re

import requests

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "he-IL,he;q=0.9",
}

BONDS_SEARCH_URL = "https://www.bizportal.co.il/bonds/search"


def _to_float(v):
    if v is None or v in ("", "--"):
        return None
    try:
        return float(v.replace(",", ""))
    except ValueError:
        return None


def fetch_bizportal_bonds(log_func=print):
    """
    מחזיר dict: sec_id -> {name, price, ytm_gross, duration, spread}.
    בקשה אחת בלבד לכל השוק. לא זורק חריגה אם הבקשה נכשלת - מחזיר
    dict ריק ומדווח בלוג, כדי שהריצה היומית תמשיך עם החישוב המקומי
    כגיבוי לכל האג"ח.
    """
    try:
        resp = requests.get(BONDS_SEARCH_URL, headers=HEADERS, timeout=30)
    except requests.RequestException as e:
        log_func(f"⚠️  שליפת אג\"ח מביזפורטל נכשלה (שגיאת רשת: {e}) - ישמש חישוב מקומי לכל האג\"ח.")
        return {}

    if resp.status_code != 200:
        log_func(f"⚠️  שליפת אג\"ח מביזפורטל נכשלה (status={resp.status_code}) - ישמש חישוב מקומי לכל האג\"ח.")
        return {}

    html = resp.text
    results = {}
    rows = re.split(r'<tr class="MarketCode1"', html)[1:]
    for row in rows:
        m_id = re.search(r'data-filter-paperid="(\d+)"', row)
        m_name = re.search(r'data-filter-papername="([^"]*)"', row)
        if not m_id:
            continue
        tds = re.findall(r"<td[^>]*>(.*?)</td>", row, re.S)

        def clean(i):
            if i >= len(tds):
                return None
            t = re.sub(r"<[^>]+>", "", tds[i]).strip()
            return t or None

        results[m_id.group(1)] = {
            "name": m_name.group(1) if m_name else clean(0),
            "price": _to_float(clean(1)),
            "ytm_gross": _to_float(clean(5)),
            "duration": _to_float(clean(6)),
            "spread": _to_float(clean(7)),
        }

    if not results:
        log_func("⚠️  לא נמצאו נתוני אג\"ח בעמוד ביזפורטל (מבנה העמוד אולי השתנה) - ישמש חישוב מקומי לכל האג\"ח.")
    else:
        log_func(f"✅ נשלפו נתוני {len(results)} אג\"ח מביזפורטל (בקשה אחת).")
    return results


if __name__ == "__main__":
    import json
    import sys

    data = fetch_bizportal_bonds()
    print(f"סה\"כ: {len(data)}")
    if len(sys.argv) > 1:
        with open(sys.argv[1], "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"נשמר ל-{sys.argv[1]}")
