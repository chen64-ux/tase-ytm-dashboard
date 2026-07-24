# -*- coding: utf-8 -*-
"""
fetch_pe.py
שולף מכפיל רווח (TTM ורבעוני) בזמן אמת מביזפורטל, לכל מניה ישראלית -
לפי מספר ני"ע בלבד.
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


def _extract_after(text, label_variants, pattern=r"(-?[\d,]+\.?\d*|הפסד)", window_size=400):
    """מוצא את הטקסט אחרי אחת מתוויות label_variants, מנקה תגי HTML, ומחלץ מספר."""
    idx = -1
    for label in label_variants:
        idx = text.find(label)
        if idx != -1:
            break
    if idx == -1:
        return None, "לא נמצא בעמוד"
    window = text[idx:idx + window_size]
    clean = re.sub(r"<[^>]+>", " ", window)
    clean = re.sub(r"&[a-zA-Z#0-9]+;", " ", clean)
    for label in label_variants:
        clean = clean.replace(label, "")
    m = re.search(pattern, clean)
    if not m:
        return None, "לא נמצא מספר בקטע"
    val = m.group(1)
    if val == "הפסד":
        return "הפסד", None
    return float(val.replace(",", "")), None


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

    return _extract_after(resp.text, ["מכפיל רווח (12 חודשים אחרונים)", "מכפיל רווח"])


def fetch_pe_full(sec_id: str):
    """
    שולפת מאותו עמוד (בקשה אחת בלבד) גם את המכפיל TTM (12 חודשים אחרונים)
    וגם את הרווח הרבעוני האחרון (מתוך "רבעון אחרון" - התווית הקצרה, כי
    "רווח לפי דו\"ח אחרון" ו"(רבעון אחרון)" הם שני אלמנטי HTML נפרדים
    בעמוד עם תג ביניהם, אז לא ניתן לחפש אותם כמחרוזת רציפה אחת)
    ו"שווי שוק (אלפי ₪)", ומחשבת מכפיל רבעוני מוכפל = שווי שוק / (רווח
    רבעוני × 4).

    מחזירה dict: {"pe_ttm": .., "pe_quarterly": .., "error": ..}
    pe_ttm / pe_quarterly: float, "הפסד", או None.
    """
    url = f"https://www.bizportal.co.il/realestates/quote/generalview/{sec_id}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
    except requests.RequestException as e:
        return {"pe_ttm": None, "pe_quarterly": None, "error": f"שגיאת רשת: {e}"}

    if resp.status_code != 200:
        return {"pe_ttm": None, "pe_quarterly": None, "error": f"status={resp.status_code}"}

    text = resp.text
    errors = []

    pe_ttm, err = _extract_after(text, ["מכפיל רווח (12 חודשים אחרונים)", "מכפיל רווח"])
    if err:
        errors.append(f"מכפיל TTM: {err}")

    q_profit, err_q = _extract_after(text, ["רבעון אחרון"])
    mcap, err_m = _extract_after(text, ["שווי שוק (אלפי ₪)"])

    pe_quarterly = None
    if isinstance(q_profit, (int, float)) and isinstance(mcap, (int, float)):
        if q_profit > 0:
            pe_quarterly = mcap / (q_profit * 4)
        elif q_profit < 0:
            pe_quarterly = "הפסד"
    elif err_q or err_m:
        errors.append(f"רווח רבעוני/שווי שוק: {err_q or err_m}")

    return {"pe_ttm": pe_ttm, "pe_quarterly": pe_quarterly, "error": "; ".join(errors) or None}


def fetch_pe_for_securities(sec_ids, log_func=print):
    """
    sec_ids: רשימת מספרי ני"ע (מחרוזות).
    מחזיר dict: sec_id -> {"pe_ttm": .., "pe_quarterly": ..} (כל אחד: float,
    "הפסד", או None). לא זורק חריגה על כישלון בודד - ממשיך לשאר המניות
    ומדווח בלוג.
    """
    results = {}
    for i, sec_id in enumerate(sec_ids):
        r = fetch_pe_full(sec_id)
        if r["error"]:
            log_func(f"  ⚠️  מכפיל רווח - נייר {sec_id}: {r['error']}")
        results[sec_id] = {"pe_ttm": r["pe_ttm"], "pe_quarterly": r["pe_quarterly"]}
        if i < len(sec_ids) - 1:
            time.sleep(DELAY_SECONDS)
    ok = sum(1 for v in results.values() if v["pe_ttm"] is not None)
    log_func(f"✅ נשלף מכפיל רווח (TTM + רבעוני) עבור {ok}/{len(sec_ids)} מניות (ביזפורטל).")
    return results


if __name__ == "__main__":
    import sys
    ids = sys.argv[1:] or ["126011"]
    r = fetch_pe_for_securities(ids)
    for sid, v in r.items():
        print(sid, "->", v)
