# -*- coding: utf-8 -*-
"""
fetch_index_weights.py
שולף בבקשה אחת את משקל כל מניה במדד ת"א-125 (מתוך עמוד "הרכב מדד" של
ביזפורטל) - להרצה בכל ריצה יומית (חלק מ-run_daily_update.py), לא
כמו fetch_index_composition.py שרץ ידנית פעם ברבעון.

מקור: https://www.bizportal.co.il/capitalmarket/indices/indexcomposition/33333333
טבלת "הרכב מדד" שם: שם הנייר | משקל ב-% | שער | % שינוי | ...
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

TA125_URL = "https://www.bizportal.co.il/capitalmarket/indices/indexcomposition/33333333"

# מזהה שורת טבלה: קישור למניה, ואז המספר הראשון שמופיע אחריו בתוך אותה
# שורה (עמודת "משקל ב-%" - העמודה הראשונה אחרי השם בטבלה).
ROW_PATTERN = re.compile(
    r'<a[^>]+href="https://www\.bizportal\.co\.il/[a-zA-Z]+/quote/generalview/(\d+)"[^>]*>([^<]+)</a>'
    r'(?P<rest>.*?)(?=<a[^>]+quote/generalview|</table>)',
    re.S,
)
NUMBER_PATTERN = re.compile(r'>(-?\d+\.?\d*)<')


def fetch_index125_weights(log_func=print):
    """
    מחזיר dict: sec_id -> {"name": .., "weight_pct": ..} לכל 126 המניות
    במדד ת"א-125. בכישלון מחזיר dict ריק (לא זורק חריגה) - הריצה
    היומית תמשיך כרגיל, רק בלי עדכון משקלים.
    """
    try:
        resp = requests.get(TA125_URL, headers=HEADERS, timeout=20)
    except requests.RequestException as e:
        log_func(f"  ⚠️  משקלי ת\"א-125: שגיאת רשת: {e}")
        return {}

    if resp.status_code != 200:
        log_func(f"  ⚠️  משקלי ת\"א-125: status={resp.status_code}")
        return {}

    weights = {}
    for m in ROW_PATTERN.finditer(resp.text):
        sec_id, name, rest = m.group(1), m.group(2).strip(), m.group("rest")
        num_match = NUMBER_PATTERN.search(rest)
        if not num_match:
            continue
        try:
            weight = float(num_match.group(1))
        except ValueError:
            continue
        if sec_id not in weights:  # השורה הראשונה עם המניה גוברת
            weights[sec_id] = {"name": name, "weight_pct": weight}

    if len(weights) < 100:  # ת"א-125 אמור להכיל 126 מניות - פחות מ-100 מרמז על כישלון פענוח
        log_func(f"  ⚠️  משקלי ת\"א-125: נמצאו רק {len(weights)} מניות (צפוי ~126) - ייתכן שמבנה העמוד השתנה.")
    else:
        log_func(f"✅ נשלפו משקלי {len(weights)} מניות במדד ת\"א-125.")
    return weights


if __name__ == "__main__":
    result = fetch_index125_weights()
    for sid, v in list(result.items())[:10]:
        print(sid, "->", v)
    print(f"... סה\"כ {len(result)} מניות")
