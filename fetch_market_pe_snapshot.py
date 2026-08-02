# -*- coding: utf-8 -*-
"""
fetch_market_pe_snapshot.py
שולף מכפיל רווח (12 חודשים אחרונים) מביזפורטל עבור **כל** המניות
הנסחרות בבורסה (לפי קובץ ה-CSV היומי), ושומר "תמונת מצב" ל-
market_pe_base.json - כולל המחיר בזמן השליפה, כדי שהתהליך היומי
יוכל לגלגל את המכפיל קדימה לפי שינוי מחיר, בלי לשלוף מחדש כל יום.

*** להריץ ידנית, פעם ברבעון (או אחרי דוחות כספיים) - לא חלק מהריצה
    היומית האוטומטית! עם 500+ מניות זה לוקח כ-10-15 דקות. ***

שימוש:
    python3 fetch_market_pe_snapshot.py <path_to_securitiesmarketdata.csv>
"""

import csv
import json
import sys
from datetime import datetime

from fetch_pe import fetch_pe_single, DELAY_SECONDS
import time


def read_all_stocks(csv_path):
    """מחזיר dict: sec_id -> {name, price} עבור כל המניות בקובץ ה-CSV."""
    COL_NAME, COL_SEC_ID, COL_TYPE, COL_PRICE = 0, 2, 3, 4
    DATA_START = 3
    with open(csv_path, encoding="utf-8-sig") as f:
        rows = list(csv.reader(f))
    out = {}
    for row in rows[DATA_START:]:
        if len(row) <= COL_PRICE:
            continue
        if row[COL_TYPE].strip() != "מניות":
            continue
        sec_id = row[COL_SEC_ID].strip()
        name = row[COL_NAME].strip()
        price_s = row[COL_PRICE].strip()
        if not sec_id or not name or not price_s:
            continue
        try:
            price = float(price_s)
        except ValueError:
            continue
        out[sec_id] = {"name": name, "price": price}
    return out


def main():
    if len(sys.argv) < 2:
        print("שימוש: python3 fetch_market_pe_snapshot.py <path_to_securitiesmarketdata.csv>")
        sys.exit(1)

    stocks = read_all_stocks(sys.argv[1])
    print(f"נמצאו {len(stocks)} מניות בקובץ. מתחיל שליפה (זה ייקח כ-{len(stocks)} שניות)...")

    snapshot = {}
    ok, failed = 0, 0
    for i, (sec_id, info) in enumerate(stocks.items()):
        pe, err = fetch_pe_single(sec_id)
        if err:
            failed += 1
        else:
            ok += 1
            snapshot[sec_id] = {
                "name": info["name"],
                "pe_base": pe,
                "price_base": info["price"],
            }
        if (i + 1) % 25 == 0:
            print(f"  ...{i + 1}/{len(stocks)} ({ok} הצליחו, {failed} נכשלו)")
        if i < len(stocks) - 1:
            time.sleep(DELAY_SECONDS)

    out = {
        "_meta": {
            "snapshot_date": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "source": "bizportal.co.il",
            "note": "מכפיל בסיס לכל מניות הבורסה. יש לרענן קובץ זה מחדש (הרצה ידנית) כל רבעון בערך.",
        }
    }
    out.update(snapshot)

    with open("market_pe_base.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"\n✅ הושלם: {ok} הצליחו, {failed} נכשלו. נשמר ל-market_pe_base.json")


if __name__ == "__main__":
    main()
