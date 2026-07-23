# -*- coding: utf-8 -*-
"""
fetch_pe.py
שולף מכפיל רווח (12 חודשים אחרונים) בזמן אמת מביזפורטל, לכל מניה
ישראלית שנמצאת בתיק ההחזקות - לפי מספר ני"ע בלבד (אין צורך בעדכון
ידני של קובץ מכפילים - כל מניה חדשה שתתווסף לתיק נכללת אוטומטית).

נבדק ואומת מול 14/14 מניות אמיתיות בתיק (ראה שיחה) - עובד באופן
עקבי דרך requests רגיל, בלי צורך בדפדפן.
"""

import re
import time

import requests

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "he-IL,he;q=0.9",
}

DELAY_SECONDS = 1.0  # השהיה בין בקשה לבקשה, כדי לא להעמיס על השרת


def fetch_pe_single(sec_id: str):
    """
    מחזיר (pe, error): pe הוא float, המחרוזת "הפסד", או None אם נכשל.
    error הוא None בהצלחה, אחרת תיאור קצר של הכישלון.
    """
    url = f"https://www.bizportal.co.il/realestates/quote/generalview/{sec_id}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
    except requests.RequestException as e:
        return None, f"שגיאת רשת: {e}"

    if resp.status_code != 200:
        return None, f"status={resp.status_code}"

    idx = resp.text.find("מכפיל רווח (12 חודשים אחרונים)")
    if idx == -1:
        idx = resp.text.find("מכפיל רווח")
    if idx == -1:
        return None, "הטקסט 'מכפיל רווח' לא נמצא בעמוד"

    window = resp.text[idx:idx + 400]
    clean = re.sub(r"<[^>]+>", " ", window)
    clean = re.sub(r"&[a-zA-Z#0-9]+;", " ", clean)
    clean = clean.replace("מכפיל רווח (12 חודשים אחרונים)", "").replace("מכפיל רווח", "")

    m = re.search(r"(-?\d+\.\d+|-?\d+|הפסד)", clean)
    if not m:
        return None, "לא נמצא מספר בקטע הרלוונטי"
    val = m.group(1)
    if val == "הפסד":
        return "הפסד", None
    return float(val), None


def fetch_pe_for_securities(sec_ids, log_func=print):
    """
    sec_ids: רשימת מספרי ני"ע (מחרוזות).
    מחזיר dict: sec_id -> מכפיל רווח (float, "הפסד", או None אם נכשל).
    לא זורק חריגה על כישלון בודד - ממשיך לשאר המניות ומדווח בלוג.
    """
    results = {}
    for i, sec_id in enumerate(sec_ids):
        pe, err = fetch_pe_single(sec_id)
        if err:
            log_func(f"  ⚠️  מכפיל רווח - נייר {sec_id}: {err}")
            results[sec_id] = None
        else:
            results[sec_id] = pe
        if i < len(sec_ids) - 1:
            time.sleep(DELAY_SECONDS)
    ok = sum(1 for v in results.values() if v is not None)
    log_func(f"✅ נשלף מכפיל רווח עבור {ok}/{len(sec_ids)} מניות (ביזפורטל).")
    return results


if __name__ == "__main__":
    import sys
    ids = sys.argv[1:] or ["126011"]
    r = fetch_pe_for_securities(ids)
    for sid, pe in r.items():
        print(sid, "->", pe)
