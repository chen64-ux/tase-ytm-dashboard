# -*- coding: utf-8 -*-
"""
fetch_pe.py
שולף מכפיל רווח (12 חודשים אחרונים) בזמן אמת מביזפורטל, לכל מניה
ישראלית שנמצאת בתיק ההחזקות - לפי מספר ני"ע בלבד (אין צורך בעדכון
ידני של קובץ מכפילים - כל מניה חדשה שתתווסף לתיק נכללת אוטומטית).

הערה: נוסה בעבר גם שילוב מכפיל "רבעוני" (מבוסס רווח רבעון אחרון
בלבד, מוכפל ×4) - הוסר, כי השדה הרלוונטי בעמוד ביזפורטל התברר כלא
עקבי (מופיע רק בחלק מהבקשות, ללא תבנית ברורה) ולא ניתן היה לבנות
עליו משהו אמין.
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


def fetch_pe_and_sector(sec_id: str):
    """
    שולפת מאותה בקשה (אותו עמוד generalview) גם את המכפיל וגם את הענף -
    השדה "ענף" מופיע בעמוד כתווית בודדת (לא זוג-מילים, אז אין סיכון
    לשבירה ע"י תג HTML באמצע, כמו שקרה עם "רבעון אחרון").

    מחזירה dict: {"pe": .., "sector": .., "error": ..}
    pe: float, "הפסד", או None. sector: מחרוזת או None.
    """
    url = f"https://www.bizportal.co.il/realestates/quote/generalview/{sec_id}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
    except requests.RequestException as e:
        return {"pe": None, "sector": None, "error": f"שגיאת רשת: {e}"}

    if resp.status_code != 200:
        return {"pe": None, "sector": None, "error": f"status={resp.status_code}"}

    text = resp.text
    errors = []

    idx = text.find("מכפיל רווח (12 חודשים אחרונים)")
    if idx == -1:
        idx = text.find("מכפיל רווח")
    pe = None
    if idx == -1:
        errors.append("מכפיל: לא נמצא בעמוד")
    else:
        window = text[idx:idx + 400]
        clean = re.sub(r"<[^>]+>", " ", window)
        clean = re.sub(r"&[a-zA-Z#0-9]+;", " ", clean)
        clean = clean.replace("מכפיל רווח (12 חודשים אחרונים)", "").replace("מכפיל רווח", "")
        m = re.search(r"(-?\d+\.\d+|-?\d+|הפסד)", clean)
        if not m:
            errors.append("מכפיל: לא נמצא מספר בקטע")
        else:
            pe = m.group(1) if m.group(1) == "הפסד" else float(m.group(1))

    sector = None
    idx2 = text.find("ענף")
    if idx2 == -1:
        errors.append("ענף: לא נמצא בעמוד")
    else:
        window2 = text[idx2:idx2 + 300]
        end_idx = window2.find("מטבע")
        segment = window2[:end_idx] if end_idx != -1 else window2
        clean2 = re.sub(r"<[^>]+>", " ", segment)
        clean2 = re.sub(r"&[a-zA-Z#0-9]+;", " ", clean2)
        clean2 = clean2.replace("ענף", "")
        sector_val = re.sub(r"\s+", " ", clean2).strip()
        sector = sector_val or None
        if not sector:
            errors.append("ענף: לא נמצא ערך")

    return {"pe": pe, "sector": sector, "error": "; ".join(errors) or None}


def fetch_index_weekly_change(index_id: str, log_func=print):
    """
    שולפת את "השינוי השבועי" המוצג ישירות בעמוד המדד בביזפורטל (למשל
    https://www.bizportal.co.il/capitalmarket/indices/generalview/751
    למדד ת"א בנקים) - ביזפורטל כבר מחשב את זה בעצמו, כך שאין צורך
    להשוות מחירים בין שני תאריכים כמו שעושים ל-Yahoo.

    נוסף 19/09/2026: Yahoo Finance מחזיר נתונים דלילים מדי (לפעמים
    נקודת מחיר בודדת בכל השבוע) לטיקר TA-BANKS.TA, מה שגרם ל"שינוי
    שבועי" מוטעה של 0%. ביזפורטל חסום מ-GitHub Actions (כמו בנק
    ישראל/למ"ס) - לכן זה מיועד לרוץ מהמחשב המקומי (run_daily_local.py)
    ולהיכתב לקובץ שנקרא בהמשך ע"י fetch_weekly_review.py בענן.

    מחזיר (pct, error): pct הוא שבר (0.0028 = 0.28%), לא אחוז גולמי -
    כדי להתאים לפורמט של שאר המדדים בסעיף (percent_cols). error הוא
    None בהצלחה.
    """
    url = f"https://www.bizportal.co.il/capitalmarket/indices/generalview/{index_id}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
    except requests.RequestException as e:
        return None, f"שגיאת רשת: {e}"

    if resp.status_code != 200:
        return None, f"status={resp.status_code}"

    text = resp.text
    idx = text.find("שבועי")
    if idx == -1:
        return None, "התווית 'שבועי' לא נמצאה בעמוד"

    window = text[idx:idx + 200]
    clean = re.sub(r"<[^>]+>", " ", window)
    clean = re.sub(r"&[a-zA-Z#0-9]+;", " ", clean)
    clean = clean.replace("שבועי", "", 1)

    m = re.search(r"(-?\d+(?:\.\d+)?)\s*%", clean)
    if not m:
        return None, "לא נמצא ערך אחוז אחרי התווית 'שבועי'"

    pct = float(m.group(1)) / 100.0
    return pct, None


def fetch_pe_for_securities(sec_ids, log_func=print):
    """
    sec_ids: רשימת מספרי ני"ע (מחרוזות).
    מחזיר dict: sec_id -> {"pe": .., "sector": ..}
    pe: float, "הפסד", או None. sector: מחרוזת או None.
    לא זורק חריגה על כישלון בודד - ממשיך לשאר המניות ומדווח בלוג.
    """
    results = {}
    for i, sec_id in enumerate(sec_ids):
        r = fetch_pe_and_sector(sec_id)
        if r["error"]:
            log_func(f"  ⚠️  נייר {sec_id}: {r['error']}")
        results[sec_id] = {"pe": r["pe"], "sector": r["sector"]}
        if i < len(sec_ids) - 1:
            time.sleep(DELAY_SECONDS)
    ok = sum(1 for v in results.values() if v["pe"] is not None)
    ok_sector = sum(1 for v in results.values() if v["sector"] is not None)
    log_func(f"✅ נשלף מכפיל רווח עבור {ok}/{len(sec_ids)} מניות, ענף עבור {ok_sector}/{len(sec_ids)} (ביזפורטל).")
    return results


if __name__ == "__main__":
    import sys
    if "--index" in sys.argv:
        index_id = sys.argv[sys.argv.index("--index") + 1]
        pct, err = fetch_index_weekly_change(index_id)
        print(f"index {index_id} -> pct={pct}, error={err}")
    else:
        ids = sys.argv[1:] or ["126011"]
        r = fetch_pe_for_securities(ids)
        for sid, v in r.items():
            print(sid, "->", v)
