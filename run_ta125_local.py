# -*- coding: utf-8 -*-
"""
run_ta125_local.py
הרצה מקומית (Windows Task Scheduler) של עדכוני התשואות היומיות/7-ימים מתגלגלות בדשבורד:

    python run_ta125_local.py ta125   # אחרי 19:00: איסוף ת"א-125 + משקלים + סעיפים 7-8 + דשבורד
    python run_ta125_local.py us      # 05:00: סקטורי ארה"ב (סעיף 9) + דשבורד

כל ריצה: git pull -> עבודה -> commit של הקבצים הרלוונטיים בלבד -> push.
הקבצים שלא קשורים (bat, לוגים, שינויים מקומיים אחרים) לא נכללים ב-commit.
פלט ללוג: ta125_local_log.txt (לא נכנס ל-git).
פרמטרים נוספים אחרי שם המשימה מועברים לאוסף (בדיקות), למשל: ta125 --csv-file X.csv --now 2026-10-16T19:30
"""

import datetime
import os
import pathlib
import subprocess
import sys

REPO = pathlib.Path(__file__).parent
LOG = REPO / "ta125_local_log.txt"
PY = sys.executable
DASH_FILES = ["weekly_review.json", "docs/ytm_dashboard.html"]
MAX_ATTEMPTS = 3


def log(msg):
    line = f"[{datetime.datetime.now():%Y-%m-%d %H:%M:%S}] {msg}"
    try:
        print(line)
    except Exception:  # noqa: BLE001 - אין קונסולה / קידוד לא תומך (Task Scheduler)
        pass
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def sh(args, show=True):
    env = {**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}  # עברית/אימוג'י בפלט של סקריפטי-הבן
    r = subprocess.run(args, cwd=str(REPO), capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
    if show:
        for ln in (r.stdout or "").splitlines():
            log("  " + ln)
        for ln in (r.stderr or "").splitlines():
            log("  (stderr) " + ln)
    return r


def changed(paths):
    r = sh(["git", "status", "--porcelain", "--"] + paths, show=False)
    return bool(r.stdout.strip())


def commit_push(paths, message):
    """commit של paths בלבד + push (עם pull --rebase וניסיון חוזר). True אם עבר/אין מה לדחוף."""
    if not changed(paths):
        log("אין שינוי ב-" + ", ".join(paths))
        return True
    sh(["git", "add", "--"] + paths)
    r = sh(["git", "commit", "-m", message, "--"] + paths)
    if r.returncode != 0:
        log("❌ commit נכשל")
        return False
    for i in range(MAX_ATTEMPTS):
        if sh(["git", "push"]).returncode == 0:
            log("✅ push עבר")
            return True
        log(f"push נדחה (ניסיון {i + 1}) - pull --rebase...")
        if sh(["git", "pull", "--rebase", "--autostash"]).returncode != 0:
            sh(["git", "rebase", "--abort"])
            return False
    return False


def regenerate_and_push(steps, message):
    """מייצר מחדש את סעיפי הסקירה והדשבורד ודוחף. אם ה-push נדחה - מבטל רק את ה-commit
    ואת שני הקבצים שנוצרו, מושך את הגרסה העדכנית ומייצר שוב (בלי לגעת בשאר הקבצים)."""
    for attempt in range(1, MAX_ATTEMPTS + 1):
        for name, args in steps:
            r = sh([PY] + args)
            if r.returncode != 0:
                log(f"⚠️  {name} נכשל (קוד {r.returncode}) - ממשיך")
        r = sh([PY, "build_dashboard.py", "ytm_computed.xlsx", "--template", "docs/ytm_dashboard.html",
                "--out", "docs/ytm_dashboard.html", "--weekly-review", "weekly_review.json"], show=False)
        if r.returncode != 0:
            log("❌ build_dashboard נכשל:\n" + (r.stderr or r.stdout)[-500:])
            return False
        if not changed(DASH_FILES):
            log("אין שינוי בדשבורד.")
            return True
        sh(["git", "add", "--"] + DASH_FILES)
        sh(["git", "commit", "-m", message, "--"] + DASH_FILES)
        if sh(["git", "push"]).returncode == 0:
            log("✅ הדשבורד נדחף")
            return True
        log(f"push נדחה (ניסיון {attempt}) - מושך את הגרסה העדכנית ומייצר מחדש...")
        sh(["git", "reset", "--mixed", "HEAD~1"])
        sh(["git", "checkout", "--"] + DASH_FILES)
        if sh(["git", "pull", "--rebase", "--autostash"]).returncode != 0:
            sh(["git", "rebase", "--abort"])
            return False
    log("❌ push נכשל אחרי כל הניסיונות")
    return False


def main(argv):
    if not argv or argv[0] not in ("ta125", "us"):
        print(__doc__)
        return 2
    job, extra = argv[0], argv[1:]
    log(f"--- התחלה: {job} ---")
    if sh(["git", "pull", "--rebase", "--autostash"]).returncode != 0:
        sh(["git", "rebase", "--abort"])
        log("❌ git pull נכשל - עוצר")
        return 1

    today = datetime.date.today().isoformat()
    if job == "ta125":
        r = sh([PY, "collect_ta125_daily.py", "--with-weights"] + extra)
        if r.returncode != 0:
            log("❌ האיסוף נכשל - עוצר")
            return 1
        if not commit_push(["data"], f"TA125 daily snapshot (local) {today}"):
            return 1
        steps = [("חישוב ת\"א-125", ["compute_ta125_weekly.py", "--merge-into", "weekly_review.json"])]
    else:
        steps = [("סקטורי ארה\"ב", ["us_sectors_daily.py", "--merge-into", "weekly_review.json"])]

    ok = regenerate_and_push(steps, f"{'TA125 rolling 7-day' if job == 'ta125' else 'US sectors'} update (local) {today}")
    log("--- הסתיים " + ("בהצלחה ---" if ok else "עם כשל ---"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
