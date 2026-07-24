#!/usr/bin/env python3
"""
עדכון דשבורד ה-YTM (ytm_dashboard.html) מקובץ Excel מחושב (ytm_computed.xlsx).

שימוש:
    python build_dashboard.py <path_to_ytm_computed.xlsx> [--template <path_to_previous_dashboard.html>]
                                                           [--usd-rate <RATE>] [--usd-date <DD/MM/YYYY>]
                                                           [--out <output_path>]

אם לא מסופק --template, נעשה שימוש בתבנית השמורה ב-assets/dashboard_template.html.
אם לא מסופקים --usd-rate/--usd-date, נשמר השער הקודם מהתבנית (ללא שינוי).
"""
import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

import openpyxl
import requests

from parse_holdings import parse_holdings
from fetch_pe import fetch_pe_for_securities
from fetch_bonds import fetch_bizportal_bonds

# 0-based column indices (A=0, B=1, ... AC=28, AY=50, etc.)
COL = {
    "name": 0,          # A  שם
    "sec_id": 2,        # C  מס' ני"ע
    "price": 4,         # E  שער אחרון (באגורות)
    "atzmat": 28,       # AC הצמדה
    "interest": 29,     # AD ריבית
    "maturity": 30,     # AE מועד פדיון
    "stock_name": 31,   # AF מניית המרה
    "conv_qty": 34,     # AI כמות אג"ח למניה אחת
    "stock_price": 35,  # AJ שער מנית המרה
    "conv_mat": 36,     # AK מועד המרה סופי
    "usd_issue_date": 38,  # AM תאריך מדד/מט"ח יסודי
    "ytm": 50,          # AY תשואה לפדיון
    "premium": 51,      # AZ פרמיית המרה
    "duration": 52,     # BA Duration
    "mod_dur": 53,      # BB Modified Duration
    "time_conv": 54,    # BC טווח לפדיון עד להמרה סופית
    "sensitivity": 55,  # BD רגישות
}


def fmt_date(v):
    if v is None or v == "":
        return None
    if hasattr(v, "strftime"):
        return v.strftime("%d/%m/%Y")
    return str(v)


def cell(row, key):
    idx = COL[key]
    v = row[idx].value if idx < len(row) else None
    if isinstance(v, str) and v.startswith("#"):
        return None  # Excel error value (#N/A, #DIV/0!, #NUM!, ...)
    return v


def read_bonds(xlsx_path):
    wb = openpyxl.load_workbook(xlsx_path, data_only=True)
    ws = wb["Sheet1"]
    bonds = []
    for row in ws.iter_rows(min_row=2):
        name = cell(row, "name")
        if not name:
            continue
        sec_id = cell(row, "sec_id")
        bonds.append({
            "sec_id": str(sec_id) if sec_id is not None else None,
            "name": name,
            "price": cell(row, "price"),
            "atzmat": cell(row, "atzmat"),
            "interest": cell(row, "interest"),
            "maturity": fmt_date(cell(row, "maturity")) or "",
            "stock_name": cell(row, "stock_name") or "",
            "conv_qty": cell(row, "conv_qty"),
            "stock_price": cell(row, "stock_price"),
            "conv_mat": fmt_date(cell(row, "conv_mat")) or "",
            "conv_price": None,
            "ytm": cell(row, "ytm"),
            "premium": cell(row, "premium"),
            "duration": cell(row, "duration"),
            "mod_dur": cell(row, "mod_dur"),
            "time_conv": cell(row, "time_conv"),
            "sensitivity": cell(row, "sensitivity"),
            "_usd_issue_date_raw": fmt_date(cell(row, "usd_issue_date")),
        })
    return bonds


def extract_template_raw(template_html):
    m = re.search(r"const RAW = (\[.*?\]);", template_html, re.S)
    if not m:
        raise RuntimeError("לא נמצא מערך RAW בתבנית")
    raw = json.loads(m.group(1))
    usd_rate_m = re.search(r"const USD_CURRENT_RATE = ([\d.]+);", template_html)
    usd_date_m = re.search(r'const USD_CURRENT_DATE = "([^"]+)";', template_html)
    usd_rate = float(usd_rate_m.group(1)) if usd_rate_m else None
    usd_date = usd_date_m.group(1) if usd_date_m else None
    return raw, usd_rate, usd_date


def build_usd_cache(prev_raw):
    """sec_id -> (usd_rate_issue, usd_rate_issue_date) מהדשבורד הקודם"""
    cache = {}
    for r in prev_raw:
        if r.get("atzmat") == "דולר" and r.get("usd_rate_issue") is not None:
            cache[r["sec_id"]] = (r["usd_rate_issue"], r.get("usd_rate_issue_date"))
    return cache


CBS_CPI_API_URL = (
    "https://www.cbs.gov.il/he/Pages/apiDefaultAspx.aspx"
    "?req=getData&id=120010&firstyear=2000&lastyear={year}"
    "&aggs=monthly&base=avg2024&format=json"
)
CBS_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.cbs.gov.il/",
}


def fetch_cpi_series():
    """
    שולף את מדד המחירים לצרכן (120010) מהלמ"ס דרך api.cbs.gov.il, ומשרשר
    בין בסיסי מדד שונים (הלמ"ס מחליפה בסיס מדד בערך כל שנתיים - למשל "2020
    ממוצע" -> "2022 ממוצע" -> "2024 ממוצע") לכדי סדרה אחת אחידה.
    מחזיר dict {(year, month): value}, מתואם לבסיס הנוכחי (האחרון בסדרה),
    או {} בכשלון.

    שיטת השרשור: השדה "percent" בכל רשומה הוא אחוז השינוי החודשי, שהלמ"ס
    מפרסמת ברציפות גם דרך מעברי בסיס (הוא לא "מתאפס" יחד עם רמת המדד) -
    לכן ניתן "לשרשר אחורה" מהחודש העדכני ביותר: value(m-1) = value(m) /
    (1 + percent(m)/100). כך מתקבלת סדרה עקבית לחלוטין, ללא תלות בהצלחת
    מציאת מקדם שרשור רשמי, וללא בעיית אי-התאמת בסיסים.
    """
    session = requests.Session()
    try:
        session.get("https://www.cbs.gov.il/he/", headers=CBS_HEADERS, timeout=20)
    except Exception:
        pass  # אם החימום נכשל, עדיין ננסה את ה-API ישירות

    data = None
    last_error = None
    for page_size in (1000, 500, 200, 100):
        url = f"https://api.cbs.gov.il/index/data/price?id=120010&format=json&download=false&last={page_size}&PageSize={page_size}"
        try:
            resp = session.get(url, headers=CBS_HEADERS, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            break
        except Exception as e:
            last_error = e
            continue

    if data is None:
        print(f"⚠️  שליפת מדד המחירים לצרכן מהלמ\"ס נכשלה ({last_error}) - "
              f"לא בוצעה התאמת אינפלציה לאג\"ח צמודות מדד בטבלת הלא-להמרה.", file=sys.stderr)
        return {}

    try:
        records = data["month"][0]["date"]
    except Exception as e:
        print(f"⚠️  מבנה תגובה לא צפוי מהלמ\"ס ({e}) - "
              f"לא בוצעה התאמת אינפלציה לאג\"ח צמודות מדד בטבלת הלא-להמרה.", file=sys.stderr)
        return {}

    records = sorted(records, key=lambda r: (r["year"], r["month"]))
    if not records:
        return {}
    print(f"ℹ️  התקבלו {len(records)} חודשי מדד מהלמ\"ס, מ-{records[0]['month']}/{records[0]['year']} "
          f"עד {records[-1]['month']}/{records[-1]['year']}.", file=sys.stderr)

    latest = records[-1]
    latest_val = (latest.get("currBase") or {}).get("value")
    if latest_val is None:
        return {}

    cpi = {(latest["year"], latest["month"]): latest_val}
    broken_links = 0
    for i in range(len(records) - 1, 0, -1):
        later, earlier = records[i], records[i - 1]
        # רציפות: החודש ה"מוקדם" חייב להיות בדיוק חודש אחד לפני ה"מאוחר"
        later_ym = later["year"] * 12 + later["month"]
        earlier_ym = earlier["year"] * 12 + earlier["month"]
        if later_ym - earlier_ym != 1:
            broken_links += 1
            continue
        pct = later.get("percent")
        later_val = cpi.get((later["year"], later["month"]))
        if pct is None or later_val is None:
            broken_links += 1
            continue
        cpi[(earlier["year"], earlier["month"])] = later_val / (1 + pct / 100)

    if broken_links:
        print(f"ℹ️  {broken_links} קישורים בסדרת המדד לא היו רציפים (חוסר בנתון חודשי) - "
              f"ייתכן שאג\"ח ישנות במיוחד לא יקבלו התאמת אינפלציה.", file=sys.stderr)

    return cpi


def read_non_conv_bonds(csv_path):
    """
    קורא אג"ח שאינן ניתנות להמרה (קונצרניות, ממשלתיות, מק"מ) מתוך קובץ ה-CSV
    הגולמי שמורד מהבורסה (market.tase.co.il/.../data/all export).
    מחזיר רשימת dict-ים: sec_id, name, type, price, interest, ytm, maturity,
    atzmat, linkage_base_date, cpi_ratio.

    עבור אג"ח צמודות מדד (atzmat == "מדד המחירים לצרכן"): cpi_ratio הוא היחס
    בין המדד הידוע האחרון לבין מדד הבסיס (לפי חודש ההנפקה, מעמודת "תאריך
    מדד/מט"ח יסודי") - שני הערכים נשלפים מאותה טבלת למ"ס (בסיס ממוצע 2024=100)
    כדי למנוע חוסר-התאמת בסיסים. משמש להתאמת ערך הפדיון (Face) בחישוב ה-YTM
    בצד הלקוח, במקום 100 קבוע.
    """
    import csv as csv_module

    TYPE_MAP = {
        "איגרות חוב": "corp",
        "אג''ח ממשלתיות": "gov",
        "מק''מ": "makam",
    }
    COL_NAME, COL_SEC_ID, COL_TYPE, COL_PRICE = 0, 2, 3, 4
    COL_INTEREST, COL_MATURITY, COL_YTM = 29, 30, 46
    COL_ATZMAT, COL_LINKAGE_BASE_DATE = 28, 38
    DATA_START = 3

    with open(csv_path, encoding="utf-8-sig") as f:
        rows = list(csv_module.reader(f))

    out = []
    for row in rows[DATA_START:]:
        if len(row) <= COL_YTM:
            continue
        raw_type = row[COL_TYPE].strip()
        bond_type = TYPE_MAP.get(raw_type)
        if bond_type is None:
            continue  # מניות, כתבי אופציה, יחידות השתתפות, אג"ח להמרה - לא רלוונטי כאן

        sec_id = row[COL_SEC_ID].strip()
        name = row[COL_NAME].strip()
        if not sec_id or not name:
            continue

        price = None
        if row[COL_PRICE].strip():
            try:
                price = float(row[COL_PRICE].strip())
            except ValueError:
                pass

        ytm = None
        if row[COL_YTM].strip():
            try:
                ytm = float(row[COL_YTM].strip())
            except ValueError:
                pass

        interest = None
        if row[COL_INTEREST].strip():
            try:
                interest = float(row[COL_INTEREST].strip())
            except ValueError:
                pass

        maturity = row[COL_MATURITY].strip() or None
        atzmat = row[COL_ATZMAT].strip() or None
        linkage_base_date = (
            row[COL_LINKAGE_BASE_DATE].strip()
            if len(row) > COL_LINKAGE_BASE_DATE else ""
        ) or None

        out.append({
            "sec_id": sec_id,
            "name": name,
            "type": bond_type,
            "price": price,
            "interest": interest,
            "ytm": ytm,
            "maturity": maturity,
            "atzmat": atzmat,
            "linkage_base_date": linkage_base_date,
            "cpi_ratio": None,
        })

    cpi_linked = [b for b in out if b["atzmat"] == "מדד המחירים לצרכן" and b["linkage_base_date"]]
    if cpi_linked:
        cpi_series = fetch_cpi_series()
        if cpi_series:
            latest_index = cpi_series[max(cpi_series.keys())]
            missing = []
            for b in cpi_linked:
                try:
                    d, m, y = b["linkage_base_date"].split("/")
                    base_index = cpi_series.get((int(y), int(m)))
                except Exception:
                    base_index = None
                if base_index:
                    b["cpi_ratio"] = latest_index / base_index
                else:
                    missing.append(b["name"])
            if missing:
                print(f"⚠️  לא נמצא מדד בסיס עבור {len(missing)} אג\"ח צמודות מדד "
                      f"(חודש הבסיס חסר בטבלת הלמ\"ס): {missing[:5]}", file=sys.stderr)

    return out


def read_warrants(csv_path):
    """
    קורא כתבי אופציה מתוך קובץ ה-CSV הגולמי שמורד מהבורסה. מחזיר רשימת
    dict-ים: sec_id, name, price, strike_base, strike_current,
    strike_linkage, last_exercise_date, ratio, stock_name, stock_price.
    כל השדות זמינים ישירות ב-CSV - אין צורך במעקב ידני, בדיוק כמו
    read_non_conv_bonds.
    """
    import csv as csv_module

    WARRANT_TYPE = "כתבי אופציה"
    COL_NAME, COL_SEC_ID, COL_TYPE, COL_PRICE = 0, 2, 3, 4
    COL_STRIKE_BASE, COL_STRIKE_CURRENT, COL_STRIKE_LINKAGE = 39, 40, 41
    COL_LAST_EXERCISE_DATE, COL_RATIO, COL_STOCK_NAME, COL_STOCK_PRICE = 42, 43, 44, 45
    DATA_START = 3

    def to_float(s):
        s = (s or "").strip()
        if not s:
            return None
        try:
            return float(s)
        except ValueError:
            return None

    with open(csv_path, encoding="utf-8-sig") as f:
        rows = list(csv_module.reader(f))

    out = []
    for row in rows[DATA_START:]:
        if len(row) <= COL_STOCK_PRICE:
            continue
        if row[COL_TYPE].strip() != WARRANT_TYPE:
            continue
        sec_id = row[COL_SEC_ID].strip()
        name = row[COL_NAME].strip()
        if not sec_id or not name:
            continue
        out.append({
            "sec_id": sec_id,
            "name": name,
            "price": to_float(row[COL_PRICE]),
            "strike_base": to_float(row[COL_STRIKE_BASE]),
            "strike_current": to_float(row[COL_STRIKE_CURRENT]),
            "strike_linkage": row[COL_STRIKE_LINKAGE].strip() or None,
            "last_exercise_date": row[COL_LAST_EXERCISE_DATE].strip() or None,
            "ratio": to_float(row[COL_RATIO]),
            "stock_name": row[COL_STOCK_NAME].strip() or None,
            "stock_price": to_float(row[COL_STOCK_PRICE]),
        })
    return out


def read_stock_prices(csv_path):
    """מחזיר dict: sec_id -> מחיר אחרון (אגורות), עבור כל המניות בקובץ ה-CSV היומי."""
    import csv as csv_module

    COL_SEC_ID, COL_TYPE, COL_PRICE = 2, 3, 4
    DATA_START = 3

    with open(csv_path, encoding="utf-8-sig") as f:
        rows = list(csv_module.reader(f))

    out = {}
    for row in rows[DATA_START:]:
        if len(row) <= COL_PRICE:
            continue
        if row[COL_TYPE].strip() != "מניות":
            continue
        sec_id = row[COL_SEC_ID].strip()
        price_s = row[COL_PRICE].strip()
        if not sec_id or not price_s:
            continue
        try:
            out[sec_id] = float(price_s)
        except ValueError:
            continue
    return out


def read_stock_market_caps(csv_path):
    """מחזיר dict: sec_id -> שווי שוק (אלפי ש"ח), ישירות מעמודה 19 בקובץ ה-CSV היומי."""
    import csv as csv_module

    COL_SEC_ID, COL_TYPE, COL_MCAP = 2, 3, 19
    DATA_START = 3

    with open(csv_path, encoding="utf-8-sig") as f:
        rows = list(csv_module.reader(f))

    out = {}
    for row in rows[DATA_START:]:
        if len(row) <= COL_MCAP:
            continue
        if row[COL_TYPE].strip() != "מניות":
            continue
        sec_id = row[COL_SEC_ID].strip()
        mcap_s = row[COL_MCAP].strip()
        if not sec_id or not mcap_s:
            continue
        try:
            out[sec_id] = float(mcap_s)
        except ValueError:
            continue
    return out


def read_stock_fundamentals(json_path):
    """קורא את קובץ נתוני היסוד (מכפילים) שנשמר מדוח 'מבט עומק' תקופתי."""
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)
    data.pop("_meta", None)
    return data


def read_market_pe_snapshot(json_path):
    """קורא את תמונת המצב הרבעונית (מכפיל בסיס לכל השוק)."""
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)
    data.pop("_meta", None)
    return data


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("xlsx_path")
    ap.add_argument("--template", default=None,
                     help="דשבורד קודם לשימוש כתבנית (ברירת מחדל: assets/dashboard_template.html)")
    ap.add_argument("--usd-rate", type=float, default=None, help="שער דולר/שקל נוכחי (בנק ישראל)")
    ap.add_argument("--usd-date", default=None, help="תאריך שער הדולר, בפורמט DD/MM/YYYY")
    ap.add_argument("--gov-curve", default=None,
                     help='עקום תשואות ממשלתי כ-JSON, לדוגמה \'[{"t":0.25,"y":3.42},{"t":1,"y":3.32}]\'')
    ap.add_argument("--nonconv-csv", default=None,
                     help="נתיב לקובץ ה-CSV הגולמי מהבורסה (לעדכון טבלת אג\"ח שאינן ניתנות להמרה)")
    ap.add_argument("--holdings-xlsx", default=None,
                     help="נתיב לקובץ ייצוא תיק ני\"ע מהברוקר (לעדכון לשוניות ההחזקות)")
    ap.add_argument("--stock-fundamentals", default=None,
                     help="נתיב ל-stock_fundamentals.json (מכפילי רווח/הון בסיסיים לגלגול יומי)")
    ap.add_argument("--market-pe-snapshot", default=None,
                     help="נתיב ל-market_pe_base.json (תמונת מצב רבעונית של מכפיל רווח לכל השוק, לטאב 'כל מניות הבורסה')")
    ap.add_argument("--out", default=None, help="נתיב לקובץ הפלט")
    args = ap.parse_args()

    skill_dir = Path(__file__).resolve().parent.parent
    template_path = Path(args.template) if args.template else skill_dir / "assets" / "dashboard_template.html"
    template_html = template_path.read_text(encoding="utf-8")

    prev_raw, prev_usd_rate, prev_usd_date = extract_template_raw(template_html)
    usd_cache = build_usd_cache(prev_raw)

    usd_rate = args.usd_rate if args.usd_rate is not None else prev_usd_rate
    usd_date = args.usd_date if args.usd_date is not None else prev_usd_date
    if args.usd_rate is None:
        print(f"⚠️  לא סופק --usd-rate — נשמר השער הקודם ({prev_usd_rate} מ-{prev_usd_date}) ללא עדכון. "
              f"יש לשלוף שער יציג עדכני מבנק ישראל ולהעביר --usd-rate/--usd-date.", file=sys.stderr)
    if args.gov_curve is None:
        print("⚠️  לא סופק --gov-curve — נשמר עקום התשואות הממשלתי הקודם בתבנית ללא עדכון. "
              "יש לשלוף עקום עדכני ולהעביר --gov-curve.", file=sys.stderr)

    bonds = read_bonds(args.xlsx_path)

    missing_usd = []
    for b in bonds:
        if b["atzmat"] == "דולר":
            cached = usd_cache.get(b["sec_id"])
            if cached and cached[0] is not None:
                b["usd_rate_issue"] = cached[0]
                b["usd_rate_issue_date"] = cached[1] or b.pop("_usd_issue_date_raw", None)
            else:
                b["usd_rate_issue_date"] = b.get("_usd_issue_date_raw")
                print(f"⚠️  אג\"ח דולרי חדש ללא שער בסיס בהנפקה: {b['name']} (sec_id={b['sec_id']}). "
                      f"יש להזין שער דולר/שקל ליום ההנפקה ({b['usd_rate_issue_date']}) ידנית.",
                      file=sys.stderr)
                missing_usd.append(b["name"])
            b["usd_rate_current"] = usd_rate
        b.pop("_usd_issue_date_raw", None)

    raw_json = json.dumps(bonds, ensure_ascii=False)

    new_html = re.sub(r"const RAW = \[.*?\];", f"const RAW = {raw_json};", template_html, count=1, flags=re.S)
    new_html = re.sub(r"const USD_CURRENT_RATE = [\d.]+;", f"const USD_CURRENT_RATE = {usd_rate};", new_html)
    new_html = re.sub(r'const USD_CURRENT_DATE = "[^"]+";', f'const USD_CURRENT_DATE = "{usd_date}";', new_html)
    if args.gov_curve:
        curve = json.loads(args.gov_curve)
        curve_js = "[" + ", ".join(f'{{t:{p["t"]}, y:{p["y"]}}}' for p in curve) + "]"
        new_html = re.sub(r"let GOV_CURVE = \[.*?\];", f"let GOV_CURVE = {curve_js};", new_html, count=1, flags=re.S)

    if args.nonconv_csv:
        non_conv = read_non_conv_bonds(args.nonconv_csv)
        non_conv_json = json.dumps(non_conv, ensure_ascii=False)
        new_html = re.sub(
            r"const NON_CONV_BONDS = \[.*?\];",
            f"const NON_CONV_BONDS = {non_conv_json};",
            new_html, count=1, flags=re.S,
        )
        print(f"✅ עודכנו {len(non_conv)} אג\"ח שאינן ניתנות להמרה (טאב נפרד).")

        bizportal_bonds = fetch_bizportal_bonds(log_func=print)
        bizportal_json = json.dumps(bizportal_bonds, ensure_ascii=False)
        new_html = re.sub(
            r"const BIZPORTAL_BONDS = \{.*?\};",
            f"const BIZPORTAL_BONDS = {bizportal_json};",
            new_html, count=1, flags=re.S,
        )

        warrants = read_warrants(args.nonconv_csv)
        warrants_json = json.dumps(warrants, ensure_ascii=False)
        new_html = re.sub(
            r"const WARRANTS = \[.*?\];",
            f"const WARRANTS = {warrants_json};",
            new_html, count=1, flags=re.S,
        )
        print(f"✅ עודכנו {len(warrants)} כתבי אופציה (טאב נפרד).")
    else:
        print("⚠️  לא סופק --nonconv-csv - טבלת האג\"ח שאינן ניתנות להמרה לא עודכנה.", file=sys.stderr)

    if args.holdings_xlsx:
        holdings = parse_holdings(args.holdings_xlsx)
        bonds_holdings = holdings.get(("ניע ישראלים", "אג״ח"), []) or holdings.get(("ניע ישראלים", 'אג"ח'), [])
        stocks_holdings = holdings.get(("ניע ישראלים", "מניות"), []) + holdings.get(("ניע זרים", "מניות"), [])

        bonds_json = json.dumps(bonds_holdings, ensure_ascii=False)
        new_html = re.sub(r"const HOLDINGS_BONDS = \[.*?\];", f"const HOLDINGS_BONDS = {bonds_json};",
                           new_html, count=1, flags=re.S)
        stocks_json = json.dumps(stocks_holdings, ensure_ascii=False)
        new_html = re.sub(r"const HOLDINGS_STOCKS = \[.*?\];", f"const HOLDINGS_STOCKS = {stocks_json};",
                           new_html, count=1, flags=re.S)
        print(f"✅ עודכן תיק החזקות: {len(bonds_holdings)} אג\"ח, {len(stocks_holdings)} מניות.")

        israeli_stock_ids = [s["sec_id"] for s in stocks_holdings if s.get("currency") == "₪" and s.get("sec_id")]
        if israeli_stock_ids:
            stock_pe_live = fetch_pe_for_securities(israeli_stock_ids, log_func=print)
            pe_json = json.dumps(stock_pe_live, ensure_ascii=False)
            new_html = re.sub(r"const STOCK_PE_LIVE = \{.*?\};", f"const STOCK_PE_LIVE = {pe_json};",
                               new_html, count=1, flags=re.S)

        if args.stock_fundamentals:
            fundamentals = read_stock_fundamentals(args.stock_fundamentals)
            fundamentals_json = json.dumps(fundamentals, ensure_ascii=False)
            new_html = re.sub(r"const STOCK_FUNDAMENTALS = \{.*?\};",
                               f"const STOCK_FUNDAMENTALS = {fundamentals_json};",
                               new_html, count=1, flags=re.S)
            print(f"✅ נטענו נתוני יסוד (סקטור/שווי שוק) עבור {len(fundamentals)} מניות.")
        else:
            print("⚠️  לא סופק --stock-fundamentals - סקטור/שווי שוק בתיק ההחזקות לא יעודכנו.", file=sys.stderr)

        if args.nonconv_csv:
            stock_prices = read_stock_prices(args.nonconv_csv)
            prices_json = json.dumps(stock_prices, ensure_ascii=False)
            new_html = re.sub(r"const STOCK_PRICES = \{.*?\};", f"const STOCK_PRICES = {prices_json};",
                               new_html, count=1, flags=re.S)
            print(f"✅ עודכנו מחירי {len(stock_prices)} מניות (לגלגול מכפילים).")

            holdings_mcaps = read_stock_market_caps(args.nonconv_csv)
            mcaps_json = json.dumps(holdings_mcaps, ensure_ascii=False)
            new_html = re.sub(r"const STOCK_MARKET_CAPS = \{.*?\};", f"const STOCK_MARKET_CAPS = {mcaps_json};",
                               new_html, count=1, flags=re.S)

    # טאב "כל מניות הבורסה" - עצמאי, לא תלוי בקובץ ההחזקות. דורש --nonconv-csv
    # (למחירים עדכניים) ו---market-pe-snapshot (תמונת מצב רבעונית ממביזפורטל).
    if args.nonconv_csv and args.market_pe_snapshot:
        all_prices = read_stock_prices(args.nonconv_csv)
        all_mcaps = read_stock_market_caps(args.nonconv_csv)
        market_base = read_market_pe_snapshot(args.market_pe_snapshot)
        all_stocks = []
        for sec_id, base in market_base.items():
            cur_price = all_prices.get(sec_id)
            base_price = base.get("price_base")
            pe_base = base.get("pe_base")
            roll_factor = None
            if base_price and cur_price is not None:
                roll_factor = cur_price / base_price
            pe_rolled = pe_base * roll_factor if (isinstance(pe_base, (int, float)) and roll_factor is not None) else None
            all_stocks.append({
                "sec_id": sec_id,
                "name": base.get("name"),
                "price": cur_price if cur_price is not None else base_price,
                "pe": pe_rolled if pe_rolled is not None else (pe_base if pe_base == "הפסד" else None),
                "market_cap": all_mcaps.get(sec_id),  # ישירות מה-CSV היומי - מדויק, לא מגולגל
            })
        all_stocks_json = json.dumps(all_stocks, ensure_ascii=False)
        new_html = re.sub(r"const ALL_STOCKS = \[.*?\];", f"const ALL_STOCKS = {all_stocks_json};",
                           new_html, count=1, flags=re.S)
        snapshot_date = None
        with open(args.market_pe_snapshot, encoding="utf-8") as f:
            snapshot_date = json.load(f).get("_meta", {}).get("snapshot_date")
        new_html = re.sub(r'const MARKET_PE_SNAPSHOT_DATE = ".*?";',
                           f'const MARKET_PE_SNAPSHOT_DATE = "{snapshot_date or ""}";',
                           new_html, count=1)
        print(f"✅ עודכן טאב 'כל מניות הבורסה': {len(all_stocks)} מניות (תמונת מצב מ-{snapshot_date}).")
    elif args.market_pe_snapshot:
        print("⚠️  סופק --market-pe-snapshot אבל לא --nonconv-csv - טאב 'כל מניות הבורסה' לא עודכן.", file=sys.stderr)

    out_path = Path(args.out) if args.out else Path("ytm_dashboard.html")
    out_path.write_text(new_html, encoding="utf-8")

    # עדכון התבנית השמורה בסקיל, כדי שהמטמון של שערי דולר בהנפקה יישמר לפעם הבאה
    template_path.write_text(new_html, encoding="utf-8")

    print(f"✅ נוצר: {out_path} ({len(bonds)} אג\"ח)")
    if missing_usd:
        print(f"⚠️  {len(missing_usd)} אג\"ח דולריים חדשים דורשים הזנת שער בסיס ידנית: {', '.join(missing_usd)}")


if __name__ == "__main__":
    main()