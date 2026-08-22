# -*- coding: utf-8 -*-
"""
run_weekly_review.py
עוטף את fetch_weekly_review.py ומחבר את התוצאה לדשבורד - מיועד להרצה
פעם בשבוע (workflow נפרד, לא חלק מהריצה היומית) דרך
.github/workflows/weekly-review-update.yml.

טווח השבוע מחושב אוטומטית: 7 הימים האחרונים עד היום (כולל).

קבצי קלט ידניים (ב-repo root, כולם אופציונליים - אם חסרים, החלק
המתאים בסקירה פשוט יהיה ריק/לא יופיע):
  - weekly_companies.json   (דוחות כספיים - ראה weekly_companies_example.json)
  - weekly_macro.json       (פריטי מאקרו נוספים - ראה weekly_macro_example.json)
  - weekly_cpi_israel.json  ({"value": "...", "note": "..."})
"""

import datetime
import json
import pathlib
import subprocess
import sys

_REPO_DIR = pathlib.Path(__file__).parent
XLSX_PATH = str(_REPO_DIR / "ytm_computed.xlsx")
DASHBOARD_PATH = str(_REPO_DIR / "docs" / "ytm_dashboard.html")
BUILD_DASHBOARD_SCRIPT = _REPO_DIR / "build_dashboard.py"
FETCH_WEEKLY_REVIEW_SCRIPT = _REPO_DIR / "fetch_weekly_review.py"
MARKET_PE_SNAPSHOT_PATH = _REPO_DIR / "market_pe_base.json"

WEEKLY_COMPANIES_PATH = _REPO_DIR / "weekly_companies.json"
WEEKLY_MACRO_PATH = _REPO_DIR / "weekly_macro.json"
WEEKLY_CPI_ISRAEL_PATH = _REPO_DIR / "weekly_cpi_israel.json"
WEEKLY_REVIEW_JSON_PATH = _REPO_DIR / "weekly_review.json"

LOG_PATH = _REPO_DIR / "weekly_review_log.txt"


def log(msg):
    line = f"[{datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(line)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def main():
    log("--- ריצה שבועית התחילה ---")

    end_date = datetime.date.today()
    start_date = end_date - datetime.timedelta(days=7)

    cmd = [
        sys.executable, str(FETCH_WEEKLY_REVIEW_SCRIPT),
        start_date.isoformat(), end_date.isoformat(),
    ]
    if WEEKLY_COMPANIES_PATH.exists():
        cmd += ["--companies", str(WEEKLY_COMPANIES_PATH)]
    else:
        log(f"ℹ️  לא נמצא {WEEKLY_COMPANIES_PATH.name} - סעיפי דוחות כספיים לא ייבנו השבוע.")
    if MARKET_PE_SNAPSHOT_PATH.exists():
        cmd += ["--market-pe-snapshot", str(MARKET_PE_SNAPSHOT_PATH)]
    if WEEKLY_MACRO_PATH.exists():
        cmd += ["--macro-file", str(WEEKLY_MACRO_PATH)]
    if WEEKLY_CPI_ISRAEL_PATH.exists():
        try:
            with open(WEEKLY_CPI_ISRAEL_PATH, encoding="utf-8") as f:
                cpi = json.load(f)
            if cpi.get("value"):
                cmd += ["--cpi-israel", cpi["value"]]
            if cpi.get("note"):
                cmd += ["--cpi-israel-note", cpi["note"]]
        except (json.JSONDecodeError, AttributeError) as e:
            log(f"⚠️  שגיאה בקריאת {WEEKLY_CPI_ISRAEL_PATH.name}: {e}")
    else:
        log(f"ℹ️  לא נמצא {WEEKLY_CPI_ISRAEL_PATH.name} - מדד המחירים לישראל לא יופיע השבוע.")

    log(f"מריץ את fetch_weekly_review.py לטווח {start_date} - {end_date}...")
    result = subprocess.run(cmd, cwd=str(_REPO_DIR), capture_output=True, text=True)
    for line in result.stdout.splitlines():
        log(line)
    for line in result.stderr.splitlines():
        log(f"  (stderr) {line}")
    if result.returncode != 0:
        log(f"❌ fetch_weekly_review.py נכשל (קוד יציאה {result.returncode}) - עוצר.")
        sys.exit(1)

    if not WEEKLY_REVIEW_JSON_PATH.exists():
        log("❌ weekly_review.json לא נוצר - עוצר.")
        sys.exit(1)

    log("מחבר את weekly_review.json לדשבורד...")
    build_cmd = [
        sys.executable, str(BUILD_DASHBOARD_SCRIPT), XLSX_PATH,
        "--template", DASHBOARD_PATH, "--out", DASHBOARD_PATH,
        "--weekly-review", str(WEEKLY_REVIEW_JSON_PATH),
    ]
    build_result = subprocess.run(build_cmd, cwd=str(_REPO_DIR), capture_output=True, text=True)
    for line in build_result.stdout.splitlines():
        log(line)
    for line in build_result.stderr.splitlines():
        log(f"  (stderr) {line}")
    if build_result.returncode != 0:
        log(f"❌ build_dashboard.py נכשל (קוד יציאה {build_result.returncode}) - עוצר.")
        sys.exit(1)

    log("--- ריצה שבועית הסתיימה בהצלחה ---")


if __name__ == "__main__":
    main()
