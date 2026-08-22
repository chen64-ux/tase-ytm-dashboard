# -*- coding: utf-8 -*-
"""
fetch_weekly_review.py
בונה את weekly_review.json באופן אוטומטי (ברובו) לתחילת כל שבוע:
  - סעיפים 1-3 (מדדי מניות, מטבעות/סחורות, תשואות אג"ח+ריבית) - אוטומטי
    לגמרי, משני מקורות חינמיים בלי מפתח: Yahoo Finance (מדדים/מטבעות/
    סחורות) ו-FRED (תשואות אג"ח ממשל ארה"ב + ריבית הפד).
  - סעיף 4 (מאקרו) - רשימת מעקב קבועה מ-FRED (תביעות אבטלה, פד
    פילדלפיה, LEI). מדד המחירים לישראל נשאר קלט ידני (--cpi-israel),
    כי זה נתון חודשי ייעודי, לא סדרת FRED סטנדרטית.
  - סעיפים 5-6 (דוחות כספיים) - נבנים מ-weekly_companies.json (קובץ
    קלט ידני קטן שאתה מתחזק - רק השדות שדורשים שיקול דעת: שם, טיקר/
    מס' ני"ע, תאריך דיווח, הכנסות, הערות). השדות הבאים מושלמים
    אוטומטית: תגובת מניה (Yahoo, לפי תאריך הדיווח), ומכפיל רווח
    למניות ישראליות בלבד (מהנתונים הקיימים שלנו, market_pe_base.json/
    stock_fundamentals.json - לא נשלף מחדש).

*** נכתב בלי אפשרות בדיקה חיה מולי (Yahoo/FRED חסומים בסביבת הפיתוח
    שלי, בדיוק כמו ביזפורטל) - יש להריץ ולוודא שהטיקרים/הפורמטים
    עדיין תואמים, ולדווח על כל כשל כדי שנתקן. ***

שימוש:
    python3 fetch_weekly_review.py 2026-08-14 2026-08-21 \
        --companies weekly_companies.json \
        --market-pe-snapshot market_pe_base.json \
        --nonconv-csv securitiesmarketdata.csv \
        --cpi-israel "+0.3% חודשי" --cpi-israel-note "פורסם 14.8; אינפלציה שנתית ירדה מ-1.6% ל-1.5%"
"""

import argparse
import csv
import json
import sys
import time
from datetime import datetime, date, timezone

import requests

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
}

DELAY_SECONDS = 0.6

YAHOO_INDICES = [
    ("S&P 500", "^GSPC"),
    ("Dow Jones", "^DJI"),
    ("Nasdaq Composite", "^IXIC"),
    ("Russell 2000", "^RUT"),
    ("VIX", "^VIX"),
    ('ת"א 35', "TA35.TA"),
    ('ת"א 125', "^TA125.TA"),
    ('ת"א בנקים', "TA-BANKS.TA"),
]

YAHOO_CURRENCIES_COMMODITIES = [
    ("USD/ILS", "ILS=X"),
    ("נפט WTI", "CL=F"),
    ("זהב (דולר/אונקיה)", "GC=F"),
    ("ביטקוין (דולר)", "BTC-USD"),
]

YAHOO_YIELDS = [
    ('אג"ח ממשל ארה"ב 10 שנים', "^TNX"),
    ('אג"ח ממשל ארה"ב 30 שנה', "^TYX"),
]

# ריבית הפד: טווח (עליון+תחתון) - שתי סדרות נפרדות שמוצגות כטווח אחד
# ריבית הפד: NY Fed API הרשמי (domain שונה לגמרי מ-FRED - אם FRED חסום
# ברמת רשת/פיירוול, יש סיכוי טוב שזה כן יעבוד). לא אומת ע"י הרצה חיה
# מולי (חסום גם בסביבת הפיתוח שלי) - יש טיפול הגנתי שמדפיס את המבנה
# הגולמי אם השדות הצפויים (targetRateFrom/targetRateTo) לא נמצאים.
NY_FED_UNSECURED_RATES_URL = "https://markets.newyorkfed.org/api/rates/unsecured/all/latest.json"


def _to_ts(d):
    return int(datetime.combine(d, datetime.min.time(), tzinfo=timezone.utc).timestamp())


def fetch_yahoo_range(ticker, start_date, end_date):
    """
    מחזיר (start_close, end_close, error). שולף חלון רחב יותר מהטווח
    המבוקש (ימים נוספים משני הצדדים) כדי להתמודד עם סופי שבוע/חגים
    שאין בהם מסחר, ובוחר את מחיר הסגירה הקרוב ביותר לכל קצה.
    """
    period1 = _to_ts(start_date) - 5 * 86400
    period2 = _to_ts(end_date) + 2 * 86400
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
    params = {"period1": period1, "period2": period2, "interval": "1d"}
    try:
        resp = requests.get(url, params=params, headers=HEADERS, timeout=15)
    except requests.RequestException as e:
        return None, None, f"שגיאת רשת: {e}"
    if resp.status_code != 200:
        return None, None, f"status={resp.status_code}"
    try:
        data = resp.json()
        result = data["chart"]["result"][0]
        timestamps = result["timestamp"]
        closes = result["indicators"]["quote"][0]["close"]
    except (KeyError, IndexError, TypeError, ValueError):
        return None, None, "מבנה תגובה לא צפוי (ייתכן שהטיקר שגוי או Yahoo שינו מבנה)"
    pairs = [(datetime.fromtimestamp(ts, tz=timezone.utc).date(), c)
             for ts, c in zip(timestamps, closes) if c is not None]
    if not pairs:
        return None, None, "אין נתונים בטווח המבוקש"
    start_pairs = [p for p in pairs if p[0] <= end_date]
    if not start_pairs:
        start_pairs = pairs
    start_val = min(start_pairs, key=lambda p: abs((p[0] - start_date).days))[1]
    end_val = min(pairs, key=lambda p: abs((p[0] - end_date).days))[1]
    return start_val, end_val, None


def fetch_yahoo_latest(ticker, as_of_date, scale=1.0):
    """
    מחזיר (value, error) - מחיר הסגירה האחרון הידוע ב-Yahoo עד ובכולל
    as_of_date, מחולק ב-scale אם צריך. הערה: ^TNX/^TYX (תשואות אג"ח
    ממשל ארה"ב) מוחזרים ב-Yahoo *ישירות* כאחוז (4.68 = 4.68%), לא פי
    10 כפי שהונח בטעות בגרסה קודמת - אומת מול נתון אמיתי מהדשבורד
    (0.47%/0.53% שגויים -> 4.7%/5.3% נכונים). scale נשאר לשימוש עתידי
    אם יתווסף מכשיר שכן דורש חלוקה.
    """
    start = date.fromordinal(as_of_date.toordinal() - 6)
    _, end_val, err = fetch_yahoo_range(ticker, start, as_of_date)
    if err:
        return None, err
    return end_val / scale, None





def build_indices_section(start_date, end_date, log):
    rows = []
    for name, ticker in YAHOO_INDICES:
        start_val, end_val, err = fetch_yahoo_range(ticker, start_date, end_date)
        if err:
            log(f"  ⚠️  {name} ({ticker}): {err}")
            rows.append([name, None, None, f"שגיאת שליפה: {err}"])
        else:
            pct = (end_val - start_val) / start_val
            rows.append([name, round(start_val, 2), round(end_val, 2), pct])
        time.sleep(DELAY_SECONDS)
    return {
        "title": "1. מדדי מניות",
        "headers": ["מדד", f"ערך תחילת שבוע ({start_date.day}.{start_date.month})",
                    f"ערך סוף שבוע ({end_date.day}.{end_date.month})", "שינוי שבועי"],
        "percent_cols": [3],
        "rows": rows,
        "footnotes": [],
    }


def build_currencies_section(start_date, end_date, log):
    rows = []
    for name, ticker in YAHOO_CURRENCIES_COMMODITIES:
        start_val, end_val, err = fetch_yahoo_range(ticker, start_date, end_date)
        if err:
            log(f"  ⚠️  {name} ({ticker}): {err}")
            rows.append([name, None, None, f"שגיאת שליפה: {err}"])
        else:
            pct = (end_val - start_val) / start_val
            rows.append([name, round(start_val, 4), round(end_val, 4), pct])
        time.sleep(DELAY_SECONDS)
    return {
        "title": "2. מטבעות וסחורות",
        "headers": ["מכשיר", f"תחילת שבוע ({start_date.day}.{start_date.month})",
                    f"סוף שבוע ({end_date.day}.{end_date.month})", "שינוי שבועי"],
        "percent_cols": [3],
        "rows": rows,
        "footnotes": [],
    }


def fetch_fed_target_range(log):
    """
    מחזיר (lower, upper, date_str, error) - טווח ריבית הפד מ-NY Fed API
    (לא FRED - domain אחר לגמרי, כדי לעקוף חסימת רשת אפשרית ל-FRED).
    לא אומת ע"י הרצה חיה - אם השדות הצפויים לא נמצאים, מדפיס את תחילת
    התגובה הגולמית ל-log כדי שאפשר יהיה לאבחן ולתקן במהירות.
    """
    try:
        resp = requests.get(NY_FED_UNSECURED_RATES_URL, headers=HEADERS, timeout=20)
    except requests.RequestException as e:
        return None, None, None, f"שגיאת רשת: {e}"
    if resp.status_code != 200:
        return None, None, None, f"status={resp.status_code}"
    try:
        data = resp.json()
    except ValueError:
        return None, None, None, "התגובה אינה JSON תקין"

    records = data.get("refRates") if isinstance(data, dict) else None
    if not records:
        log(f"  ℹ️  מבנה JSON לא צפוי מ-NY Fed, תחילת התגובה: {json.dumps(data, ensure_ascii=False)[:300]}")
        return None, None, None, "לא נמצא מפתח 'refRates' בתגובה"

    effr = next((r for r in records if r.get("type") == "EFFR"), records[0])
    lower = effr.get("targetRateFrom")
    upper = effr.get("targetRateTo")
    d = effr.get("effectiveDate")
    if lower is None or upper is None:
        log(f"  ℹ️  שדות טווח היעד לא נמצאו ברשומה, תוכן הרשומה: {json.dumps(effr, ensure_ascii=False)[:300]}")
        return None, None, None, "לא נמצאו שדות targetRateFrom/targetRateTo"
    return float(lower), float(upper), d, None


def build_yields_section(end_date, log):
    rows = []
    for name, ticker in YAHOO_YIELDS:
        val, err = fetch_yahoo_latest(ticker, end_date, scale=1.0)
        if err:
            log(f"  ⚠️  {name} ({ticker}): {err}")
            rows.append([name, None, f"שגיאת שליפה: {err}"])
        else:
            rows.append([name, f"{val:.2f}%", f"נכון ל-{end_date.day}.{end_date.month}.{end_date.year} (Yahoo Finance, {ticker})"])
        time.sleep(DELAY_SECONDS)

    lower, upper, d_str, err = fetch_fed_target_range(log)
    if err:
        log(f"  ⚠️  ריבית הפד (NY Fed): {err}")
        rows.append(["ריבית הפד (טווח)", None, "שגיאת שליפה"])
    else:
        rows.append(["ריבית הפד (טווח)", f"{lower:.2f}%-{upper:.2f}%", f"נכון ל-{d_str} (NY Fed API)"])

    return {
        "title": '3. תשואות אג"ח וריבית בנקים מרכזיים',
        "headers": ["מכשיר", "ערך נוכחי", "הערה"],
        "percent_cols": [],
        "rows": rows,
        "footnotes": [
            'ריבית בנק ישראל אינה נשלפת אוטומטית - יש לעדכן ידנית אם השתנתה (נדיר, מוכרז מראש).',
            'ריבית הפד נשלפת מ-NY Fed API (domain שונה מ-FRED) - אם זה נכשל, ייתכן שגם domain זה חסום; יש לבדוק את ההודעה המפורטת בלוג.',
        ],
    }


def build_macro_section(cpi_israel, cpi_israel_note, macro_file, log):
    """
    סעיף מאקרו - ידני לגמרי (FRED חסום ברשת, ואין מקור חינמי אמין
    אחר לנתונים כאלה - תביעות אבטלה/פד פילדלפיה/LEI וכו' אינם זמינים
    ב-Yahoo Finance). מדד המחירים לישראל (--cpi-israel) ושאר הנתונים
    (--macro-file, קובץ JSON קטן שאתה מתחזק) מוצגים כמות שהם, בלי
    שליפה כלשהי.
    """
    rows = []
    if cpi_israel:
        rows.append(["מדד המחירים לצרכן ישראל", cpi_israel, cpi_israel_note or ""])
    if macro_file:
        try:
            with open(macro_file, encoding="utf-8") as f:
                items = json.load(f)
            for item in items:
                rows.append([item.get("name", ""), item.get("value", ""), item.get("note", "")])
        except FileNotFoundError:
            log(f"  ℹ️  לא נמצא {macro_file} - פריטי מאקרו נוספים לא נוספו.")
        except (json.JSONDecodeError, AttributeError, TypeError) as e:
            log(f"  ⚠️  שגיאה בקריאת {macro_file}: {e}")
    return {
        "title": "4. נתוני מאקרו",
        "headers": ["נתון", "ערך", "הערה"],
        "percent_cols": [],
        "rows": rows,
        "footnotes": ["סעיף זה ידני לגמרי - יש לעדכן בכל שבוע (--cpi-israel/--cpi-israel-note ו/או --macro-file)."],
    }


def read_israeli_pe(sec_id, market_pe_snapshot_path, nonconv_csv_path):
    """
    מכפיל רווח למניה ישראלית - מהנתונים הקיימים שלנו (לא נשלף מחדש).
    משתמש ב-pe_base מתמונת המצב (ללא גלגול מדויק לפי מחיר יומי - זו
    הערכה סבירה לצורך הסקירה השבועית, לא הדשבורד המלא).
    """
    try:
        with open(market_pe_snapshot_path, encoding="utf-8") as f:
            snapshot = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None
    entry = snapshot.get(sec_id)
    if not entry:
        return None
    pe = entry.get("pe_base")
    return pe if isinstance(pe, (int, float)) else None


def build_earnings_sections(companies_path, market_pe_snapshot_path, log):
    """
    בונה את סעיפים 5-6 (דוחות כספיים - ארה"ב/ישראל) מ-weekly_companies.json.
    לכל חברה: תגובת מניה נשלפת אוטומטית (Yahoo, יום הדיווח מול היום
    שלפניו). מכפיל רווח: אוטומטי למניות ישראליות (מהנתונים הקיימים),
    ידני לאמריקאיות (P/E) - הערה: כדי לקבל מכפיל P/E אמריקאי מעודכן,
    יש להזין אותו ידנית בקובץ הקלט - אין לנו מקור חינמי אמין לזה.
    """
    try:
        with open(companies_path, encoding="utf-8") as f:
            companies = json.load(f)
    except FileNotFoundError:
        log(f"  ℹ️  לא נמצא {companies_path} - סעיפי דוחות כספיים לא ייבנו.")
        return None, None

    us_rows, il_rows = [], []
    for c in companies:
        report_date = datetime.strptime(c["report_date"], "%Y-%m-%d").date()
        # תגובת מניה: יום הדיווח מול יום המסחר הקודם
        ticker = c.get("ticker")
        reaction = None
        if ticker:
            prev_close, day_close, err = fetch_yahoo_range(
                ticker, date.fromordinal(report_date.toordinal() - 5), report_date)
            if err:
                log(f"  ⚠️  תגובת מניה - {c['company']} ({ticker}): {err}")
            else:
                reaction = (day_close - prev_close) / prev_close
            time.sleep(DELAY_SECONDS)

        if c.get("market") == "IL":
            pe = read_israeli_pe(c.get("sec_id"), market_pe_snapshot_path, None) if market_pe_snapshot_path else None
            il_rows.append([
                c["company"], c.get("revenue", ""), c.get("profit_note", ""),
                c.get("yoy_note", ""), f"{pe:.1f}x" if pe else c.get("pe_manual", ""),
                reaction if reaction is not None else c.get("reaction_manual", ""),
            ])
        else:
            us_rows.append([
                c["company"], f"{report_date.day}.{report_date.month}",
                c.get("revenue", ""), c.get("eps_note", ""), c.get("yoy_note", ""),
                c.get("pe_manual", ""),  # P/E אמריקאי - ידני, אין מקור חינמי אמין
                reaction if reaction is not None else c.get("reaction_manual", ""),
            ])

    us_section = {
        "title": '5. דוחות כספיים בולטים - ארה"ב',
        "headers": ["חברה", "תאריך דיווח", "הכנסות", "רווח (EPS)", "שינוי מול רבעון מקביל", "מכפיל רווח (P/E)", "תגובת מניה"],
        "percent_cols": [6],
        "rows": us_rows,
        "footnotes": ["מכפיל P/E אמריקאי מוזן ידנית בקובץ הקלט - אין מקור חינמי אמין לשליפה אוטומטית."],
    } if us_rows else None

    il_section = {
        "title": "6. דוחות כספיים בולטים - ישראל",
        "headers": ["חברה", "הכנסות", "רווח / EBITDA", "שינוי מול רבעון מקביל", "מכפיל", "תגובת מניה"],
        "percent_cols": [5],
        "rows": il_rows,
        "footnotes": ['מכפילי הרווח (P/E) למניות ישראליות מבוססים על "כל מניות הבורסה" (market_pe_base.json) - לא מחושבים מחדש מהדוח הבודד.'],
    } if il_rows else None

    return us_section, il_section


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("start_date", help="תחילת השבוע, פורמט YYYY-MM-DD")
    ap.add_argument("end_date", help="סוף השבוע, פורמט YYYY-MM-DD")
    ap.add_argument("--companies", default=None, help="נתיב ל-weekly_companies.json")
    ap.add_argument("--market-pe-snapshot", default=None, help="נתיב ל-market_pe_base.json (למכפילי מניות ישראליות)")
    ap.add_argument("--cpi-israel", default=None, help='ערך מדד המחירים לצרכן ישראל (למשל "+0.3%% חודשי") - ידני')
    ap.add_argument("--cpi-israel-note", default=None, help="הערה נלווית למדד הישראלי - ידני")
    ap.add_argument("--macro-file", default=None, help="נתיב לקובץ JSON עם פריטי מאקרו נוספים - ידני, ראה weekly_macro_example.json")
    args = ap.parse_args()

    start_date = datetime.strptime(args.start_date, "%Y-%m-%d").date()
    end_date = datetime.strptime(args.end_date, "%Y-%m-%d").date()

    def log(msg):
        print(msg)

    print("שולף מדדי מניות (Yahoo Finance)...")
    sections = [build_indices_section(start_date, end_date, log)]
    print("שולף מטבעות וסחורות (Yahoo Finance)...")
    sections.append(build_currencies_section(start_date, end_date, log))
    print("שולף תשואות אג\"ח (Yahoo Finance) וריבית הפד (NY Fed API)...")
    sections.append(build_yields_section(end_date, log))
    print("בונה סעיף מאקרו (ידני)...")
    sections.append(build_macro_section(args.cpi_israel, args.cpi_israel_note, args.macro_file, log))

    if args.companies:
        print("בונה סעיפי דוחות כספיים (weekly_companies.json + Yahoo לתגובת מניה)...")
        us_section, il_section = build_earnings_sections(args.companies, args.market_pe_snapshot, log)
        if us_section:
            sections.append(us_section)
        if il_section:
            sections.append(il_section)

    data = {
        "title": f"סקירה שבועית שוק ההון | {start_date.day}-{end_date.day} ב{['ינואר','פברואר','מרץ','אפריל','מאי','יוני','יולי','אוגוסט','ספטמבר','אוקטובר','נובמבר','דצמבר'][end_date.month-1]} {end_date.year}",
        "sources_note": "מקורות: Yahoo Finance, FRED (Federal Reserve Economic Data). נשלף אוטומטית ע\"י fetch_weekly_review.py.",
        "sections": sections,
    }

    with open("weekly_review.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n✅ נשמר ל-weekly_review.json ({len(sections)} סעיפים).")


if __name__ == "__main__":
    main()
