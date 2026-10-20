# -*- coding: utf-8 -*-
"""
compute_ta125_weekly.py
תנודות שבועיות של מניות ת"א-125, מתוך הצילומים היומיים ש-collect_ta125_daily.py
צבר ב-data/.

שיטת החישוב: תשואה שבועית = ריבית דריבית של "שינוי (%)" היומי של כל יום מסחר
בשבוע:  R = Π(1 + chg_d/100) − 1.
"שינוי (%)" של הבורסה מחושב מול שער בסיס מותאם (מקדם אקס), ולכן ביום אקס דיבידנד
הירידה המכנית של השער לא נספרת כהפסד. (הפער מתשואה כוללת מדויקת קטן: בערך
תשואת הדיבידנד כפול תנועת אותו יום.)

תרומה למדד = משקל תחילת שבוע × תשואה שבועית (buy & hold).
משקל: אם יש data/ta125_weights.csv (ביזפורטל) - הצילום האחרון ≤ תחילת התקופה;
אחרת חלק משווי השוק מתוך אוניברסום ת"א-125 (קירוב - לא משקל Free-float).

פלט: שני סעיפים בפורמט weekly_review.json:
  7. ת"א 125 - תנודות שבועיות בניירות הערך
  8. ת"א 125 - סיכום לפי ענף

שימוש:
    python compute_ta125_weekly.py --start 2026-10-10 --end 2026-10-17 --out ta125_weekly.json --csv-out ta125_weekly.csv
    python compute_ta125_weekly.py --start ... --end ... --merge-into weekly_review.json
התקופה היא (start, end] - יום ההתחלה עצמו לא נכלל (זה סגירת השבוע הקודם).
"""

import argparse
import csv
import datetime
import json
import pathlib
import sys
from collections import defaultdict

REPO_DIR = pathlib.Path(__file__).parent
SECTION_PREFIXES = ("7.", "8.")
STOCK_TITLE = '7. ת"א 125 - תנודות שבועיות בניירות הערך'
SECTOR_TITLE = '8. ת"א 125 - סיכום לפי ענף'
PRIOR_DAYS_MIN = 10          # מינימום ימי מסחר היסטוריים להשוואת מחזור
PRIOR_WINDOW_DAYS = 28


def _f(v):
    try:
        return float(v) if v not in ("", None) else None
    except ValueError:
        return None


def load_daily(data_dir, since):
    """כל השורות מקבצי החודש עם date >= since. מחזיר list של dict."""
    rows = []
    for p in sorted(pathlib.Path(data_dir).glob("equity_daily_*.csv")):
        with open(p, encoding="utf-8", newline="") as f:
            for r in csv.DictReader(f):
                if r["date"] >= since.isoformat():
                    rows.append(r)
    return rows


def load_universe(path):
    """sec_id -> (name, sector) למניות ת"א-125."""
    d = json.load(open(path, encoding="utf-8"))
    out = {}
    for k, v in d.items():
        out[str(k).lstrip("0")] = (v.get("name", ""), v.get("sector") or "אחר")
    return out


def load_weights(data_dir, start):
    """משקלי ביזפורטל: הצילום האחרון עם date <= start. מחזיר (date, {sec_id: pct}) או (None, {})."""
    p = pathlib.Path(data_dir) / "ta125_weights.csv"
    if not p.exists():
        return None, {}
    by_date = defaultdict(dict)
    with open(p, encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            w = _f(r.get("weight_pct"))
            if w is not None and r["date"] <= start.isoformat():
                by_date[r["date"]][r["sec_id"].lstrip("0")] = w
    if not by_date:
        return None, {}
    d = max(by_date)
    return d, by_date[d]


def expected_trading_days(start, end):
    """ימי ב'-ו' בתקופה (בורסת ת"א נסחרת ב'-ו' מינואר 2026). חגים לא מטופלים - רק אזהרה."""
    d, out = start + datetime.timedelta(days=1), []
    while d <= end:
        if d.weekday() < 5:
            out.append(d.isoformat())
        d += datetime.timedelta(days=1)
    return out


def find_reported_index_return(review_path):
    """שינוי שבועי מדווח של ת"א 125 מסעיף 1 ב-weekly_review.json (אם קיים)."""
    try:
        d = json.load(open(review_path, encoding="utf-8"))
        for s in d.get("sections", []):
            if s.get("title", "").startswith("1."):
                for row in s["rows"]:
                    if str(row[0]).replace("״", '"').strip() == 'ת"א 125':
                        return float(row[-1])
    except Exception:  # noqa: BLE001
        pass
    return None


def compute(start, end, data_dir, universe, index_return=None):
    since = start - datetime.timedelta(days=PRIOR_WINDOW_DAYS + 7)
    rows = load_daily(data_dir, since)
    s_iso, e_iso = start.isoformat(), end.isoformat()
    in_win = [r for r in rows if s_iso < r["date"] <= e_iso and r["sec_id"] in universe]
    if not in_win:
        raise SystemExit(f"❌ אין נתונים יומיים בתקופה ({start}, {end}] ב-{data_dir}")

    win_dates = sorted({r["date"] for r in in_win})
    warnings = []
    missing_wd = [d for d in expected_trading_days(start, end) if d not in win_dates]
    if missing_wd:
        warnings.append("ימי מסחר (ב'-ו') שחסרים בצבירה: " + ", ".join(missing_wd)
                        + " (חגים תקינים; אחרת - התשואה מתחת לתחתית)")

    per = defaultdict(lambda: {"f": 1.0, "n": 0, "turn": 0.0, "ex": [], "last_end": None})
    for r in sorted(in_win, key=lambda x: x["date"]):
        p = per[r["sec_id"]]
        chg = _f(r["chg"])
        if chg is not None:
            p["f"] *= 1 + chg / 100
            p["n"] += 1
        p["turn"] += _f(r["turnover"]) or 0.0
        p["last_end"] = _f(r["last"]) or p["last_end"]
        if r.get("ex_type") or (_f(r.get("ex_coef")) not in (None, 1.0)):
            p["ex"].append(r["date"])

    # שער ותחילת שבוע, מחזור היסטורי, שווי שוק ל-fallback של משקלים
    prior = [r for r in rows if r["date"] <= s_iso and r["sec_id"] in universe]
    prior_dates = sorted({r["date"] for r in prior if r["date"] > (start - datetime.timedelta(days=PRIOR_WINDOW_DAYS)).isoformat()})
    last_prior_date = max((r["date"] for r in prior), default=None)
    start_last, start_mcap, prior_turn = {}, {}, defaultdict(float)
    for r in prior:
        if r["date"] == last_prior_date:
            start_last[r["sec_id"]] = _f(r["last"])
            start_mcap[r["sec_id"]] = _f(r["mcap"])
        if r["date"] in prior_dates:
            prior_turn[r["sec_id"]] += _f(r["turnover"]) or 0.0

    w_date, w_pct = load_weights(data_dir, start)
    if w_pct:
        weights = {k: v / 100 for k, v in w_pct.items() if k in universe}
        weight_src = f"משקלי ת\"א-125 (ביזפורטל) מתאריך {w_date}"
    else:
        # fallback: שווי שוק; אם אין צילום לפני התקופה - צילום היום הראשון בתקופה
        mc = {k: v for k, v in start_mcap.items() if v}
        src_date = last_prior_date
        if not mc:
            first = win_dates[0]
            mc = {r["sec_id"]: _f(r["mcap"]) for r in in_win if r["date"] == first and _f(r["mcap"])}
            src_date = first
            warnings.append("אין צילום לפני תחילת התקופה - המשקלים לפי שווי שוק של היום הראשון בתקופה")
        tot = sum(mc.values()) or 1
        weights = {k: v / tot for k, v in mc.items()}
        weight_src = (f"קירוב: חלקה בשווי השוק של 126 מניות האוניברסום ({src_date}) - "
                      "לא משקל Free-float רשמי; להפעלת משקלים רשמיים: collect_ta125_daily.py --weights-only")

    stocks = []
    for sid, p in per.items():
        name, sector = universe[sid]
        R = p["f"] - 1 if p["n"] else None
        stocks.append({"sec_id": sid, "name": name, "sector": sector, "R": R, "n": p["n"],
                       "w0": weights.get(sid, 0.0), "turn": p["turn"], "ex": p["ex"],
                       "last_end": p["last_end"], "last_start": start_last.get(sid)})
    wsum = sum(s["w0"] for s in stocks if s["R"] is not None) or 1.0
    for s in stocks:
        s["contrib"] = (s["w0"] / wsum * s["R"]) if s["R"] is not None else None
    proxy = sum(s["contrib"] for s in stocks if s["contrib"] is not None)
    bench = index_return if index_return is not None else proxy
    bench_label = ("מדד ת\"א 125 המדווח" if index_return is not None else "קירוב המדד (סכום תרומות)")

    n_days = len(win_dates)
    n_prior = len(prior_dates)
    for s in stocks:
        s["rel"] = (s["R"] - bench) if s["R"] is not None else None
        pt = prior_turn.get(s["sec_id"], 0.0)
        s["turn_vs"] = None
        if n_prior >= PRIOR_DAYS_MIN and pt > 0 and n_days:
            s["turn_vs"] = (s["turn"] / n_days) / (pt / n_prior) - 1
        notes = []
        if s["n"] < n_days:
            notes.append(f"חסרים {n_days - s['n']} ימים")
        if s["ex"]:
            txt = "אקס " + ", ".join(d[8:] + "/" + d[5:7] for d in s["ex"])
            if s["last_start"] and s["last_end"]:
                naive = s["last_end"] / s["last_start"] - 1
                txt += f" (סגירה מול סגירה: {naive:+.1%})"
            notes.append(txt)
        s["notes"] = "; ".join(notes)
    return stocks, proxy, bench, bench_label, weight_src, win_dates, n_prior, warnings


def build_sections(stocks, proxy, bench, bench_label, weight_src, win_dates, n_prior, warnings, start, end):
    ok = sorted([s for s in stocks if s["R"] is not None], key=lambda s: s["R"], reverse=True)
    rows = [[s["name"], s["sector"], s["R"], s["rel"], s["contrib"],
             round(s["turn"] / 1000, 1), s["turn_vs"], s["notes"]] for s in ok]
    foot = [
        "תשואה שבועית = ריבית דריבית של השינוי היומי (שער סגירה מול שער בסיס מותאם); ביום אקס דיבידנד הירידה בשער בגלל הדיבידנד אינה נספרת כהפסד.",
        f"תקופה: {win_dates[0]} עד {win_dates[-1]} ({len(win_dates)} ימי מסחר). מול המדד = תשואה פחות {bench_label} ({bench:+.2%}). קירוב המדד מסכום תרומות: {proxy:+.2%}.",
        f"תרומה = משקל תחילת שבוע × תשואה. מקור משקלים: {weight_src}.",
        "מחזור שבועי במיליוני ש\"ח; \"מחזור מול ממוצע\" = ממוצע יומי השבוע מול ממוצע יומי ב-4 השבועות הקודמים"
        + ("" if n_prior >= PRIOR_DAYS_MIN else " (לא מחושב - אין עדיין מספיק היסטוריה)") + ".",
    ] + [f"⚠️ {w}" for w in warnings]
    sec1 = {"title": STOCK_TITLE,
            "headers": ["נייר", "ענף", "תשואה שבועית", "מול המדד", "תרומה למדד",
                        "מחזור שבועי (מ' ש\"ח)", "מחזור מול ממוצע", "הערות"],
            "percent_cols": [2, 3, 4, 6], "rows": rows, "footnotes": foot}

    by_sec = defaultdict(list)
    for s in ok:
        by_sec[s["sector"]].append(s)
    srows = []
    for sec, lst in by_sec.items():
        w = sum(x["w0"] for x in lst)
        ret = sum(x["w0"] * x["R"] for x in lst) / w if w else sum(x["R"] for x in lst) / len(lst)
        up = sum(1 for x in lst if x["R"] > 0)
        down = sum(1 for x in lst if x["R"] < 0)
        srows.append([sec, ret, sum(x["contrib"] for x in lst), len(lst), up, down, up / len(lst)])
    srows.sort(key=lambda r: r[1], reverse=True)
    sec2 = {"title": SECTOR_TITLE,
            "headers": ["ענף", "תשואה (משוקללת)", "תרומה למדד", "מניות", "עלו", "ירדו", "רוחב (% שעלו)"],
            "percent_cols": [1, 2, 6], "rows": srows,
            "footnotes": ["תשואת ענף = ממוצע משוקלל במשקלי תחילת שבוע של מניות הענף.",
                          f"מניות ללא נתון תשואה נשמטו: {sum(1 for s in stocks if s['R'] is None)}."]}
    return [sec1, sec2]


def merge_into(path, sections):
    p = pathlib.Path(path)
    d = json.load(open(p, encoding="utf-8"))
    secs = [s for s in d.get("sections", []) if not s.get("title", "").startswith(SECTION_PREFIXES)]
    # שומר סדר: סעיפים 7-8 אחרי 1-4 ולפני כל סעיף אחר שמספרו גבוה (אם קיים)
    d["sections"] = secs + sections
    tmp = p.with_suffix(".tmp")
    json.dump(d, open(tmp, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    tmp.replace(p)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--start", required=True, help="YYYY-MM-DD, סגירת השבוע הקודם (לא נכלל)")
    ap.add_argument("--end", required=True, help="YYYY-MM-DD, סוף התקופה (נכלל)")
    ap.add_argument("--data-dir", default=str(REPO_DIR / "data"))
    ap.add_argument("--universe", default=str(REPO_DIR / "sector_mapping.json"))
    ap.add_argument("--out", help="כתיבת הסעיפים לקובץ JSON")
    ap.add_argument("--csv-out", help="טבלה מלאה ל-CSV (לאקסל)")
    ap.add_argument("--merge-into", help="weekly_review.json - מחליף סעיפים 7-8")
    ap.add_argument("--index-return", type=float, help="תשואת ת\"א 125 המדווחת (שבר, למשל 0.0423)")
    a = ap.parse_args(argv)

    start, end = datetime.date.fromisoformat(a.start), datetime.date.fromisoformat(a.end)
    idx = a.index_return
    if idx is None and a.merge_into:
        idx = find_reported_index_return(a.merge_into)
    universe = load_universe(a.universe)
    res = compute(start, end, a.data_dir, universe, idx)
    stocks, proxy, bench, bench_label, weight_src, win_dates, n_prior, warnings = res
    sections = build_sections(*res, start, end)

    for w in warnings:
        print("⚠️ ", w)
    print(f"✅ {len(stocks)} מניות, {len(win_dates)} ימים, קירוב מדד {proxy:+.2%}, בסיס השוואה {bench:+.2%} ({bench_label})")
    if a.out:
        json.dump(sections, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    if a.csv_out:
        with open(a.csv_out, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f)
            w.writerow(sections[0]["headers"])
            w.writerows(sections[0]["rows"])
    if a.merge_into:
        merge_into(a.merge_into, sections)
        print(f"✅ סעיפים 7-8 עודכנו ב-{a.merge_into}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
