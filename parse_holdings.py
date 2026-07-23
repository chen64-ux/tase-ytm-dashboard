# -*- coding: utf-8 -*-
"""
parse_holdings.py
קורא קובץ ייצוא "תיק ני\"ע" מהברוקר (xlsx) ומחלץ ממנו את כל האחזקות
לפי סקציות: מניות ישראליות, אג"ח ישראליות, מניות זרות וכו'.

תוקן במיוחד עבור בעיה נפוצה בקבצי ייצוא כאלה: תאים המעוצבים כאחוז
(%) אך מכילים טקסט גולמי (למשל "1.54%") גורמים ל-openpyxl לקרוס
בברירת המחדל. הפונקציה monkey-patches את מנגנון קריאת המספרים כך
שיחזיר את המחרוזת הגולמית במקום לקרוס.
"""

import re


def _patch_openpyxl():
    """מתקן קריסה של openpyxl על תאי אחוז/טקסט לא תקניים."""
    import openpyxl.worksheet._reader as _reader_mod

    _orig_cast_number = _reader_mod._cast_number

    def _safe_cast_number(value):
        try:
            return _orig_cast_number(value)
        except ValueError:
            return value

    _reader_mod._cast_number = _safe_cast_number


_patch_openpyxl()

import openpyxl  # noqa: E402  (חייב לבוא אחרי הפאץ\')


SECTION_HEADERS = {"מניות", "אג״ח", "אג\"ח", "קרנות נאמנות", "מחקי מדד", "נגזרים"}
GROUP_HEADERS = {"ניע ישראלים", "ניע זרים"}

COL_NAME, COL_SEC_ID, COL_SYMBOL, COL_ISIN = 1, 2, 3, 4
COL_QTY, COL_LAST_PRICE, COL_CURRENCY = 5, 6, 7
COL_VALUE_ILS, COL_VALUE_CCY = 16, 17
COL_PCT_PORTFOLIO = 20


def _to_float(v):
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().replace(",", "")
    if not s:
        return None
    s = s.rstrip("%")
    try:
        return float(s)
    except ValueError:
        return None


def parse_holdings(xlsx_path: str) -> dict:
    """
    מחזיר dict: { (group, section): [ {name, sec_id, symbol, isin, qty,
    last_price, currency, value_ils, value_ccy, pct_portfolio}, ... ] }
    לדוגמה: ("ניע ישראלים", "אג״ח") -> רשימת האג"ח הישראליות בתיק.
    """
    wb = openpyxl.load_workbook(xlsx_path, data_only=True)
    ws = wb.active

    result = {}
    current_group = None
    current_section = None

    header_row_idx = None
    for row in ws.iter_rows(values_only=True):
        cells = [c for c in row]
        first_text = next((str(c).strip() for c in cells if c not in (None, "") and str(c).strip()), "")

        if first_text in GROUP_HEADERS:
            current_group = first_text
            current_section = None
            continue
        if first_text in SECTION_HEADERS:
            current_section = first_text
            continue
        if first_text.startswith(":") or 'סה"כ' in first_text or "סה''כ" in first_text:
            continue
        if first_text == "נייר":
            header_row_idx = True
            continue
        if not first_text or current_section is None:
            continue

        # שורת נתונים בפועל
        vals = list(cells)
        while len(vals) <= COL_PCT_PORTFOLIO:
            vals.append(None)

        name = str(vals[COL_NAME]).strip() if vals[COL_NAME] else None
        if not name:
            continue
        sec_id = str(vals[COL_SEC_ID]).strip() if vals[COL_SEC_ID] not in (None, "") else None
        symbol = str(vals[COL_SYMBOL]).strip() if vals[COL_SYMBOL] not in (None, "") else None

        entry = {
            "name": name,
            "sec_id": sec_id,
            "symbol": symbol,
            "isin": str(vals[COL_ISIN]).strip() if vals[COL_ISIN] not in (None, "") else None,
            "qty": _to_float(vals[COL_QTY]),
            "last_price": _to_float(vals[COL_LAST_PRICE]),
            "currency": str(vals[COL_CURRENCY]).strip() if vals[COL_CURRENCY] not in (None, "") else None,
            "value_ils": _to_float(vals[COL_VALUE_ILS]),
            "value_ccy": _to_float(vals[COL_VALUE_CCY]),
            "pct_portfolio": _to_float(vals[COL_PCT_PORTFOLIO]),
        }
        key = (current_group or "ניע ישראלים", current_section)
        result.setdefault(key, []).append(entry)

    return result


if __name__ == "__main__":
    import sys
    import json

    if len(sys.argv) < 2:
        print("שימוש: python3 parse_holdings.py <path_to_holdings.xlsx>")
        sys.exit(1)

    data = parse_holdings(sys.argv[1])
    for (group, section), rows in data.items():
        print(f"\n=== {group} / {section} ({len(rows)} שורות) ===")
        for r in rows:
            print(r)
