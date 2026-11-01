# -*- coding: utf-8 -*-
"""
collect_ta125_daily.py
איסוף יומי של נתוני המניות בבורסה *אחרי סגירת המסחר* (לא לפני 19:00 שעון
ישראל), ושמירה מצטברת לקבצים חודשיים ב-data/equity_daily_YYYY-MM.csv.
משמש את compute_ta125_weekly.py לחישוב תשואה שבועית כריבית דריבית של
השינוי היומי (ראה שם).

מקור: ייצוא נתוני המסחר של הבורסה (אותו API כמו run_daily_update.py).
השורות נשמרות כפי שהן, ובעיקר "שינוי (%)" - שבורסת תל אביב מחשבת מול שער
בסיס *מותאם* (ביום אקס דיבידנד שער הבסיס מוכפל ב"מקדם אקס"), ולכן ירידת
השער בגלל הדיבידנד לא מופיעה כהפסד.

כללי בטיחות:
  * לא רץ לפני 19:00 שעון ישראל (אלא עם --force).
  * נשמר רק אם תאריך "נכון ל-" בקובץ שווה להיום (ישראל) - כך ימי שישי/
    חגים/ימים ללא מסחר נדלגים אוטומטית, בלי לוח שנה ידני.
  * אידמפוטנטי: ריצה חוזרת באותו יום לא משכפלת שורות.
  * דילוג מחזיר קוד 0 (ה-workflow נשאר ירוק); רק כשל אמיתי מחזיר 1.

שימוש:
    python collect_ta125_daily.py                 # ריצה רגילה (workflow)
    python collect_ta125_daily.py --weights-only  # מקומי: משקלי ת"א-125 (ביזפורטל)
    python collect_ta125_daily.py --force         # לעקוף שעה/תאריך (בדיקות)
    python collect_ta125_daily.py --csv-file X.csv --now 2026-09-04T19:30 --force
"""

import argparse
import csv
import datetime
import io
import pathlib
import re
import sys
import time

REPO_DIR = pathlib.Path(__file__).parent
DATA_DIR = REPO_DIR / "data"
WEIGHTS_PATH = DATA_DIR / "ta125_weights.csv"

MAIN_PAGE_URL = "https://market.tase.co.il/he/market_data/securities/data/all"
API_URL = "https://api.tase.co.il/api/export/securitiesmarketdata"
HEADERS = {
    "Accept": "text/csv",
    "Accept-Language": "he-IL",
    "Content-Type": "application/json;charset=UTF-8",
    "Origin": "https://market.tase.co.il",
    "Referer": "https://market.tase.co.il/",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36"
    ),
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site",
}
PAYLOAD = {
    "FilterData": {"dType": 1, "TotalRec": 1, "pageNum": 1, "cl1": "0", "lang": "0"},
    "isAdd": False,
}

# שדות הקובץ היומי: (שם בקובץ, אפשרויות כותרת בקובץ הבורסה)
SOURCE_COLUMNS = {
    "name": ["שם"],
    "sec_id": ["מס' ני''ע", "מס' ני\"ע"],
    "sec_type": ["סוג ני''ע", "סוג ני\"ע"],
    "last": ["שער אחרון (באגורות)"],
    "chg": ["שינוי (%)"],
    "base": ["שער בסיס"],
    "turnover": ["מחזור (באלפי ש''ח)", "מחזור (באלפי ש\"ח)"],
    "ex_type": ["סוג האקס"],
    "ex_coef": ["מקדם אקס"],
    "mcap": ["שווי שוק (אלפי ש''ח)", "שווי שוק (אלפי ש\"ח)"],
    "trades": ["מספר עסקאות"],
}
OUT_FIELDS = ["date", "sec_id", "name", "last", "chg", "base", "turnover",
              "ex_type", "ex_coef", "mcap", "trades"]
MIN_STOCK_ROWS = 300          # בבורסה כ-530 מניות; פחות מזה = קובץ חלקי/שבור
STOCK_TYPES = ("מניות", "יחידת השתתפות")  # יהש (נאוויטס, ניו-מד, ישראמקו, רציו) נכללות
TRADING_CLOSED_HOUR = 19      # לא לאסוף לפני השעה הזו (שעון ישראל)


def _il_now():
    """השעה בישראל. אם אין tzdata (Windows) - נופלים ל-UTC+3 עם אזהרה."""
    try:
        from zoneinfo import ZoneInfo
        return datetime.datetime.now(ZoneInfo("Asia/Jerusalem")).replace(tzinfo=None)
    except Exception:
        print("⚠️  zoneinfo/tzdata לא זמין (pip install tzdata) - מניח UTC+3.")
        return (datetime.datetime.now(datetime.timezone.utc)
                + datetime.timedelta(hours=3)).replace(tzinfo=None)


def _norm(s):
    return re.sub(r"\s+", " ", (s or "").strip())


def _num(s):
    """מחרוזת -> float, או None אם ריק/לא תקין."""
    s = _norm(s).replace(",", "").replace("%", "")
    if s in ("", "-", "--", "N/A"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def download_csv_bytes(retries=3, delay=20):
    import requests
    last_err = None
    for attempt in range(1, retries + 1):
        try:
            session = requests.Session()
            session.get(MAIN_PAGE_URL, headers={"User-Agent": HEADERS["User-Agent"]}, timeout=30)
            resp = session.post(API_URL, headers=HEADERS, json=PAYLOAD, timeout=60)
            if resp.status_code == 200 and "text/csv" in resp.headers.get("Content-Type", ""):
                return resp.content
            last_err = f"status={resp.status_code} body={resp.text[:200]!r}"
        except Exception as e:  # noqa: BLE001 - רשת, נתעד ונחזור על הניסיון
            last_err = repr(e)
        print(f"⚠️  ניסיון הורדה {attempt}/{retries} נכשל: {last_err}")
        if attempt < retries:
            time.sleep(delay)
    raise RuntimeError(f"הורדת ה-CSV נכשלה: {last_err}")


def parse_tase_csv(raw):
    """
    מחזיר (as_of_date, rows) - rows רק של מניות, כל שורה dict לפי OUT_FIELDS
    (בלי date). הכותרות נמצאות לפי שם (לא לפי אינדקס) כדי לעמוד בשינוי סדר עמודות.
    """
    text = raw.decode("utf-8-sig") if isinstance(raw, (bytes, bytearray)) else raw
    table = list(csv.reader(io.StringIO(text)))

    as_of = None
    for row in table[:5]:
        m = re.search(r"(\d{2})/(\d{2})/(\d{4})", " ".join(row))
        if m:
            as_of = datetime.date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
            break
    if as_of is None:
        raise ValueError("לא נמצא תאריך 'נכון ל-' בראש הקובץ")

    header_idx = None
    for i, row in enumerate(table[:10]):
        if any(_norm(c) in SOURCE_COLUMNS["sec_id"] for c in row):
            header_idx = i
            break
    if header_idx is None:
        raise ValueError("לא נמצאה שורת כותרות (מס' ני''ע)")
    header = [_norm(c) for c in table[header_idx]]

    col = {}
    for key, options in SOURCE_COLUMNS.items():
        for opt in options:
            if _norm(opt) in header:
                col[key] = header.index(_norm(opt))
                break
    missing = [k for k in ("name", "sec_id", "sec_type", "last", "chg", "base", "turnover") if k not in col]
    if missing:
        raise ValueError(f"עמודות חסרות בקובץ הבורסה: {missing}")

    def get(row, key):
        i = col.get(key)
        return row[i] if i is not None and i < len(row) else ""

    out = []
    for row in table[header_idx + 1:]:
        if len(row) <= col["sec_id"]:
            continue
        if _norm(get(row, "sec_type")) not in STOCK_TYPES:
            continue
        sec_id = _norm(get(row, "sec_id")).lstrip("0")
        if not sec_id:
            continue
        out.append({
            "sec_id": sec_id,
            "name": _norm(get(row, "name")),
            "last": _num(get(row, "last")),
            "chg": _num(get(row, "chg")),
            "base": _num(get(row, "base")),
            "turnover": _num(get(row, "turnover")),
            "ex_type": _norm(get(row, "ex_type")),
            "ex_coef": _num(get(row, "ex_coef")),
            "mcap": _num(get(row, "mcap")),
            "trades": _num(get(row, "trades")),
        })
    return as_of, out


def month_file(d):
    return DATA_DIR / f"equity_daily_{d:%Y-%m}.csv"


def _read_rows(path):
    if not path.exists():
        return []
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _write_rows(path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    tmp.replace(path)


def _fmt(v):
    return "" if v is None else (repr(v) if isinstance(v, float) else v)


def store_day(as_of, rows, force=False):
    """שומר את היום בקובץ החודש. מחזיר True אם נכתב, False אם כבר קיים (ובלי force)."""
    path = month_file(as_of)
    existing = _read_rows(path)
    iso = as_of.isoformat()
    already = any(r["date"] == iso for r in existing)
    if already and not force:
        return False
    kept = [r for r in existing if r["date"] != iso]
    new = [{"date": iso, **{k: _fmt(r[k]) for k in OUT_FIELDS if k != "date"}} for r in rows]
    _write_rows(path, kept + new, OUT_FIELDS)
    return True


def collect_weights(as_of):
    """משקלי ת"א-125 מביזפורטל - חסום מ-GitHub, לכן רץ מקומית (--weights-only).
    לא קריטי: בכישלון מחזיר False בלי לזרוק."""
    try:
        sys.path.insert(0, str(REPO_DIR))
        from fetch_index_weights import fetch_index125_weights
        weights = fetch_index125_weights(log_func=print)
    except Exception as e:  # noqa: BLE001
        print(f"⚠️  שליפת משקלים נכשלה: {e!r}")
        return False
    if not weights or len(weights) < 100:
        print("⚠️  משקלים חסרים/חלקיים - לא נשמר.")
        return False
    fields = ["date", "sec_id", "name", "weight_pct"]
    iso = as_of.isoformat()
    kept = [r for r in _read_rows(WEIGHTS_PATH) if r["date"] != iso]
    new = [{"date": iso, "sec_id": str(k).lstrip("0"), "name": v.get("name", ""),
            "weight_pct": v.get("weight_pct")} for k, v in weights.items()]
    _write_rows(WEIGHTS_PATH, kept + new, fields)
    print(f"✅ נשמרו משקלי {len(new)} מניות לתאריך {iso}.")
    return True


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--force", action="store_true", help="לעקוף בדיקת שעה/תאריך וכתיבה חוזרת")
    ap.add_argument("--weights-only", action="store_true", help="רק משקלי ת\"א-125 (מקומי)")
    ap.add_argument("--with-weights", action="store_true", help="נסה גם משקלים אחרי האיסוף")
    ap.add_argument("--min-hour", type=int, default=TRADING_CLOSED_HOUR)
    ap.add_argument("--csv-file", help="קובץ CSV מקומי במקום הורדה (בדיקות)")
    ap.add_argument("--now", help="לדריסת השעה בישראל, ISO (בדיקות), למשל 2026-09-04T19:30")
    args = ap.parse_args(argv)

    now = datetime.datetime.fromisoformat(args.now) if args.now else _il_now()
    print(f"שעה בישראל: {now:%Y-%m-%d %H:%M}")

    try:
        raw = open(args.csv_file, "rb").read() if args.csv_file else download_csv_bytes()
        as_of, rows = parse_tase_csv(raw)
    except Exception as e:  # noqa: BLE001
        print(f"❌ {e}")
        return 1

    print(f"נכון ל-{as_of:%d/%m/%Y}, נמצאו {len(rows)} מניות.")
    # נתוני היום נחשבים סופיים רק אחרי 19:00 (מסחר פעיל = מחירי ביניים). נתוני יום קודם תמיד סופיים,
    # ולכן ריצה מאוחרת (מחשב שהיה כבוי ב-19:15, GitHub שאיחר) משלימה את היום החסר, וריצה ביום
    # ללא מסחר פשוט מוצאת שהיום כבר נשמר.
    if not args.force and as_of >= now.date() and now.hour < args.min_hour:
        print(f"⏭️  הקובץ נכון להיום ({as_of}) אך השעה לפני {args.min_hour}:00 - המסחר עוד לא הסתיים, דילוג.")
        return 0
    if not args.force and as_of > now.date():
        print(f"⏭️  תאריך הקובץ ({as_of}) אחרי היום - לא שומר.")
        return 0

    if args.weights_only:
        return 0 if collect_weights(as_of) else 1

    if len(rows) < MIN_STOCK_ROWS:
        print(f"❌ רק {len(rows)} מניות (צפוי 500+) - לא שומר קובץ חלקי.")
        return 1

    bad_chg = sum(1 for r in rows if r["chg"] is None)
    if bad_chg > len(rows) * 0.5:
        print(f"❌ ל-{bad_chg} מניות אין 'שינוי (%)' - נראה שהנתונים לא סופיים. לא שומר.")
        return 1

    if store_day(as_of, rows, force=args.force):
        print(f"✅ נשמרו {len(rows)} שורות ל-{month_file(as_of).name} ({as_of}).")
    else:
        print(f"ℹ️  {as_of} כבר נשמר - אין שינוי.")

    if args.with_weights:
        collect_weights(as_of)
    return 0


if __name__ == "__main__":
    sys.exit(main())
