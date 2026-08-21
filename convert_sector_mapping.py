# -*- coding: utf-8 -*-
"""
convert_sector_mapping.py
קורא את הסיווג הענפי הידני שלך מתוך indexcomponents.xlsx (לשונית
"indexcomponents", עמודות: A=שם, C=ענף, E=מס' ני"ע) ושומר כ-
sector_mapping.json - קובץ שהריצה היומית קוראת (לא נשלף אוטומטית,
כי הסיווג הזה ידני - יש להריץ את הסקריפט הזה מחדש ולהעלות את הקובץ
כל פעם שאתה מעדכן את הסיווג הענפי בקובץ המקור.

שימוש:
    python3 convert_sector_mapping.py indexcomponents.xlsx
"""

import json
import sys

import openpyxl


def convert(path):
    wb = openpyxl.load_workbook(path, data_only=True)
    ws = wb["indexcomponents"]

    mapping = {}
    # שורה 3 היא כותרות (שם | סימול | ענף | מכפיל רווח | מס' ני"ע | ...),
    # הנתונים מתחילים משורה 4.
    for row in ws.iter_rows(min_row=4, values_only=True):
        name, sector, sec_id = row[0], row[2], row[4]
        if not sec_id or not sector:
            continue
        mapping[str(sec_id).strip()] = {"name": str(name).strip() if name else None,
                                         "sector": str(sector).strip()}
    return mapping


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("שימוש: python3 convert_sector_mapping.py indexcomponents.xlsx")
        sys.exit(1)

    mapping = convert(sys.argv[1])
    with open("sector_mapping.json", "w", encoding="utf-8") as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)

    sectors_found = sorted(set(v["sector"] for v in mapping.values()))
    print(f"✅ הומרו {len(mapping)} ניירות, {len(sectors_found)} ענפים שונים.")
    print("ענפים:", ", ".join(sectors_found))
    print("נשמר ל-sector_mapping.json")
