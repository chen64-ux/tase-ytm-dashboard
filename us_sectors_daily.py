# -*- coding: utf-8 -*-
"""
us_sectors_daily.py
תשואה יומית ושבועית מתגלגלת (7 ימים) של 11 סקטורי ה-S&P 500, דרך קרנות הסקטורים של SPDR
(Yahoo Finance, אותו API שבו משתמשת הסקירה השבועית), ושילוב כסעיף 9 ב-weekly_review.json.

הגדרות:
  * הבסיס הוא שער הסגירה של *יום המסחר האחרון שהסתיים* (היום הקודם) - לא של היום.
    ברירת מחדל: ברים עם תאריך של היום (שעון ניו יורק) מוחרגים, כי כשהריצה בערב
    בישראל וול סטריט עדיין פתוחה וה"סגירה" של היום היא מחיר ביניים.
    (--include-today מבטל את ההחרגה, למשל לריצה אחרי הסגירה.)
  * תשואה יומית  = סגירת E מול סגירת יום המסחר הקודם לו. E = יום המסחר האחרון שהסתיים.
  * תשואה 7 ימים = סגירת E מול הסגירה האחרונה בתאריך <= E פחות 7 ימים קלנדריים
    (חלון מתגלגל, כולל יום E; אותה הגדרה כמו סעיפים 7-8 של ת"א-125).
  * המחיר: adjusted close של Yahoo (תשואה כוללת, מנטרל דיבידנדים); אם חסר - close.
  * ההשוואה: מול SPY (קרן ה-S&P 500, אותה שיטת חישוב).

שימוש:
    python us_sectors_daily.py --merge-into weekly_review.json
    python us_sectors_daily.py --out us_sectors.json            # בלי מיזוג
    python us_sectors_daily.py --fixture-dir DIR --today 2026-10-22   # בדיקות (קובצי JSON של Yahoo)
קוד יציאה 0 גם כש-Yahoo לא זמין (לא עוצר את הסקירה); 1 רק על שגיאת שימוש/קובץ.
"""

import argparse
import datetime
import json
import pathlib
import sys
import time

SECTION_PREFIX = "9."
SECTION_TITLE = '9. סקטורי ארה"ב - תשואה יומית ו-7 ימים'
BENCH = ("S&P 500 (SPY)", "SPY")
SECTORS = [
    ("טכנולוגיה", "XLK"), ("פיננסים", "XLF"), ("בריאות", "XLV"), ("אנרגיה", "XLE"),
    ("צריכה מחזורית", "XLY"), ("צריכה בסיסית", "XLP"), ("תעשייה", "XLI"),
    ("חומרים", "XLB"), ("נדל\"ן", "XLRE"), ("שירותי תקשורת", "XLC"), ("תשתיות", "XLU"),
]
MIN_OK_SECTORS = 8     # פחות מזה = כשל שליפה, לא מעדכנים את הסעיף
WINDOW_DAYS = 7
HEADERS = {"User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36"),
           "Accept": "application/json"}


def _ny_today():
    try:
        from zoneinfo import ZoneInfo
        return datetime.datetime.now(ZoneInfo("America/New_York")).date()
    except Exception:  # noqa: BLE001 - אין tzdata: ניו יורק ~ UTC-5/-4, נשתמש ב-UTC-5 (שמרני)
        print("⚠️  tzdata לא זמין - מניח UTC-5 לתאריך ניו יורק.")
        return (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=5)).date()


def parse_chart(data):
    """תגובת Yahoo chart -> {date: price} (adjclose אם יש, אחרת close). זורק ValueError על מבנה לא צפוי."""
    try:
        res = data["chart"]["result"][0]
        ts = res["timestamp"]
        close = res["indicators"]["quote"][0]["close"]
        adj = (res["indicators"].get("adjclose") or [{}])[0].get("adjclose") or close
    except (KeyError, IndexError, TypeError) as e:
        raise ValueError(f"מבנה תגובה לא צפוי: {e!r}") from e
    try:
        from zoneinfo import ZoneInfo
        tz = ZoneInfo("America/New_York")
    except Exception:  # noqa: BLE001
        tz = datetime.timezone(datetime.timedelta(hours=-5))
    out = {}
    for t, a, c in zip(ts, adj, close):
        p = a if a is not None else c
        if p is None:
            continue
        d = datetime.datetime.fromtimestamp(t, tz=datetime.timezone.utc).astimezone(tz).date()
        out[d] = float(p)
    return out


def fetch_prices(ticker, fixture_dir=None, retries=3):
    if fixture_dir:
        return parse_chart(json.load(open(pathlib.Path(fixture_dir) / f"{ticker}.json", encoding="utf-8")))
    import requests
    last = None
    for i in range(1, retries + 1):
        try:
            r = requests.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}",
                             params={"range": "2mo", "interval": "1d", "events": "div,split"},
                             headers=HEADERS, timeout=20)
            if r.status_code == 200:
                return parse_chart(r.json())
            last = f"status={r.status_code}"
        except Exception as e:  # noqa: BLE001
            last = repr(e)
        if i < retries:
            time.sleep(3 * i)
    raise RuntimeError(last)


def compute_returns(prices, last_day, window_days=WINDOW_DAYS):
    """prices {date: p} כבר מסוננים (<= last_day). מחזיר dict או None אם אין מספיק נתונים."""
    days = sorted(d for d in prices if d <= last_day)
    if len(days) < 2 or days[-1] != last_day:
        return None
    prev = days[-2]
    base_cut = last_day - datetime.timedelta(days=window_days)
    base_days = [d for d in days if d <= base_cut]
    if not base_days:
        return None
    base = base_days[-1]
    return {"daily": prices[last_day] / prices[prev] - 1, "prev": prev,
            "weekly": prices[last_day] / prices[base] - 1, "base": base}


def build_section(results, bench, last_day, skipped_today, failed):
    rows = []
    ok = [(n, t, r) for n, t, r in results if r]
    ok.sort(key=lambda x: x[2]["weekly"], reverse=True)
    for name, tk, r in ok:
        rows.append([name, tk, r["daily"], r["daily"] - bench["daily"],
                     r["weekly"], r["weekly"] - bench["weekly"]])
    rows.append([BENCH[0], BENCH[1], bench["daily"], None, bench["weekly"], None])
    foot = [
        f"שער סגירה של יום המסחר האחרון שהסתיים ({last_day:%d.%m.%Y}); "
        + ("שער היום הנוכחי (שעוד לא נסגר) לא נכלל. " if skipped_today else "")
        + f"תשואה יומית = מול סגירת {bench['prev']:%d.%m.%Y}; "
        f"תשואה 7 ימים = חלון מתגלגל מול סגירת {bench['base']:%d.%m.%Y} (7 ימים קלנדריים אחורה, כולל יום הסגירה).",
        "מקור: Yahoo Finance, קרנות הסקטורים SPDR (תשואה כוללת - adjusted close, דיבידנדים מנוטרלים). "
        "ממוין לפי תשואת 7 הימים; \"מול\" = הפרש מנקודות האחוז מול SPY.",
    ]
    if failed:
        foot.append("⚠️ לא נשלפו: " + ", ".join(failed))
    return {"title": f"{SECTION_TITLE} (עד {last_day:%d.%m.%Y})",
            "headers": ["סקטור", "קרן", "תשואה יומית", "מול S&P 500 (יומי)", "תשואה 7 ימים", "מול S&P 500 (7 ימים)"],
            "percent_cols": [2, 3, 4, 5], "rows": rows, "footnotes": foot}


def merge_into(path, section):
    p = pathlib.Path(path)
    d = json.load(open(p, encoding="utf-8"))
    secs = [s for s in d.get("sections", []) if not s.get("title", "").startswith(SECTION_PREFIX)]
    d["sections"] = secs + [section]
    tmp = p.with_suffix(".tmp")
    json.dump(d, open(tmp, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    tmp.replace(p)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--merge-into", help="weekly_review.json - מחליף סעיף 9")
    ap.add_argument("--out", help="כתיבת הסעיף לקובץ JSON")
    ap.add_argument("--include-today", action="store_true", help="כולל את בר התאריך של היום (ניו יורק)")
    ap.add_argument("--today", help="לדריסת התאריך בניו יורק, YYYY-MM-DD (בדיקות)")
    ap.add_argument("--fixture-dir", help="תיקיית קובצי JSON של Yahoo (בדיקות), שם קובץ = TICKER.json")
    a = ap.parse_args(argv)

    today = datetime.date.fromisoformat(a.today) if a.today else _ny_today()
    cutoff = today if a.include_today else today - datetime.timedelta(days=1)

    prices, failed = {}, []
    for name, tk in SECTORS + [BENCH]:
        try:
            prices[tk] = fetch_prices(tk, a.fixture_dir)
        except Exception as e:  # noqa: BLE001
            failed.append(f"{tk} ({e})")
            print(f"⚠️  {tk}: {e}")

    if BENCH[1] not in prices:
        print("❌ SPY לא נשלף - אין בסיס השוואה, הסעיף לא עודכן.")
        return 0
    spy_days = [d for d in prices[BENCH[1]] if d <= cutoff]
    if not spy_days:
        print("❌ אין נתוני SPY עד תאריך החיתוך - הסעיף לא עודכן.")
        return 0
    last_day = max(spy_days)
    skipped_today = (not a.include_today) and any(d >= today for d in prices[BENCH[1]])

    bench = compute_returns({d: p for d, p in prices[BENCH[1]].items() if d <= cutoff}, last_day)
    if not bench:
        print("❌ אין מספיק היסטוריה ל-SPY - הסעיף לא עודכן.")
        return 0
    results = []
    for name, tk in SECTORS:
        r = compute_returns({d: p for d, p in prices.get(tk, {}).items() if d <= cutoff}, last_day) if tk in prices else None
        if tk in prices and not r:
            failed.append(f"{tk} (אין נתון ל-{last_day})")
        results.append((name, tk, r))
    n_ok = sum(1 for _, _, r in results if r)
    if n_ok < MIN_OK_SECTORS:
        print(f"❌ רק {n_ok} סקטורים נשלפו (נדרשים {MIN_OK_SECTORS}) - הסעיף לא עודכן.")
        return 0

    section = build_section(results, bench, last_day, skipped_today, failed)
    print(f"✅ {n_ok}/11 סקטורים, יום סגירה אחרון {last_day}, SPY יומי {bench['daily']:+.2%}, 7 ימים {bench['weekly']:+.2%}")
    if a.out:
        json.dump(section, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    if a.merge_into:
        merge_into(a.merge_into, section)
        print(f"✅ סעיף 9 עודכן ב-{a.merge_into}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
