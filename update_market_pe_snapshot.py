# -*- coding: utf-8 -*-
"""
update_market_pe_snapshot.py
עטיפה סביב fetch_market_pe_snapshot.py להרצה מתוזמנת (לא ידנית) -
פעם בחודש/רבעון. מוצאת את קובץ ה-CSV האחרון שהורד ע"י run_daily_update.py
(בתיקיית downloads/), מריצה איתו את fetch_market_pe_snapshot.py,
ואז דוחפת את market_pe_base.json המעודכן ל-GitHub.

משך הריצה: כ-10-15 דקות (500+ בקשות לביזפורטל, בהשהיה של שנייה בין
בקשה לבקשה). מיועד לרוץ בנפרד מהריצות היומיות הרגילות (לא באותו
חלון זמן), כדי לא להכפיל עומס/זמן ריצה ולא להתנגש עם ה-push היומי.

שימוש (ב-Task Scheduler, פעם בחודש):
    python update_market_pe_snapshot.py
"""

import datetime
import pathlib
import subprocess
import sys

_REPO_DIR = pathlib.Path(__file__).parent
DOWNLOADS_DIR = _REPO_DIR / "downloads"
LOG_PATH = _REPO_DIR / "update_market_pe_snapshot_log.txt"


def log(msg: str) -> None:
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def find_latest_csv():
    csvs = sorted(DOWNLOADS_DIR.glob("tase_securities_*.csv"))
    return csvs[-1] if csvs else None


def run_git(args, check: bool = False):
    result = subprocess.run(
        ["git"] + args,
        cwd=str(_REPO_DIR),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        log(f"git {' '.join(args)} -> שגיאה: {result.stderr.strip()}")
    if check and result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} נכשל")
    return result


def main() -> None:
    log("=== מתחיל רענון רבעוני של מכפילי כל מניות הבורסה ===")

    csv_path = find_latest_csv()
    if csv_path is None:
        log(
            "❌ לא נמצא קובץ CSV בתיקיית downloads - יש להריץ קודם ריצה "
            "יומית רגילה (run_daily_local.py), או להעביר קובץ ידנית לשם."
        )
        sys.exit(1)
    log(f"משתמש בקובץ CSV: {csv_path.name}")

    pull = run_git(["pull", "--ff-only"])
    if pull.returncode != 0:
        log("⚠️  git pull נכשל - ממשיך עם הקובץ המקומי; ה-push בסוף עשוי לדרוש טיפול ידני.")

    log("מריץ את fetch_market_pe_snapshot.py (זה ייקח כ-10-15 דקות)...")
    result = subprocess.run(
        [sys.executable, str(_REPO_DIR / "fetch_market_pe_snapshot.py"), str(csv_path)],
        cwd=str(_REPO_DIR),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.stdout:
        print(result.stdout)
    if result.returncode != 0:
        log(f"❌ fetch_market_pe_snapshot.py נכשל: {result.stderr.strip()}")
        sys.exit(1)
    log("✅ fetch_market_pe_snapshot.py הסתיים בהצלחה.")

    run_git(["add", "market_pe_base.json"], check=True)
    diff = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=str(_REPO_DIR))
    if diff.returncode == 0:
        log("אין שינוי ב-market_pe_base.json לעומת הגרסה הקודמת - לא נדרש commit.")
        return

    commit_msg = f"Quarterly refresh of market P/E snapshot ({datetime.date.today().isoformat()})"
    run_git(["commit", "-m", commit_msg], check=True)

    push = run_git(["push"])
    if push.returncode != 0:
        log("⚠️  push נדחה - מנסה fetch+merge...")
        run_git(["fetch", "origin"], check=True)
        merge = run_git(["merge", "--no-edit", "origin/main"])
        if merge.returncode != 0:
            log("❌ merge נכשל - נדרש טיפול ידני (git status / git diff).")
            sys.exit(1)
        push2 = run_git(["push"])
        if push2.returncode != 0:
            log("❌ push שני נכשל - נדרש טיפול ידני.")
            sys.exit(1)

    log("✅ market_pe_base.json נדחף ל-GitHub בהצלחה.")
    log("=== רענון רבעוני הושלם ===")


if __name__ == "__main__":
    main()
