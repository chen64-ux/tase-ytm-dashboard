# -*- coding: utf-8 -*-
"""
run_daily_local.py
עוטף את run_daily_update.py להרצה מקומית (במקום ב-GitHub Actions) -
כי ביזפורטל/בנק ישראל/למ"ס חוסמים בקשות משרתי GitHub (403/timeout),
אבל עובדים תקין מהמחשב הזה (אומת בפועל).

אחרי שהריצה המקומית מסתיימת, דוחף אוטומטית ל-GitHub את הקבצים
שהשתנו - כדי שהדשבורד החי (GitHub Pages) יתעדכן.

מיועד להרצה 6 פעמים ביום, ראשון-שישי, דרך Windows Task Scheduler -
בדיוק כמו שה-workflow tase-update.yml עשה קודם.
"""

import pathlib
import subprocess
import sys

_REPO_DIR = pathlib.Path(__file__).parent
RUN_DAILY_UPDATE_SCRIPT = _REPO_DIR / "run_daily_update.py"

# הקבצים שריצת run_daily_update.py משנה בפועל - רק אלה נדחפים.
# holdings.xlsx / market_pe_base.json / sector_mapping.json וכו' לא
# נגעים כאן - אלה מתעדכנים בתהליכים נפרדים משלהם.
FILES_TO_PUSH = ["ytm_computed.xlsx", "docs/ytm_dashboard.html", "run_log.txt"]


def step(msg):
    print(f"\n=== {msg} ===")


def run_daily_update():
    result = subprocess.run([sys.executable, str(RUN_DAILY_UPDATE_SCRIPT)], cwd=str(_REPO_DIR))
    if result.returncode != 0:
        raise RuntimeError(f"run_daily_update.py נכשל (קוד יציאה {result.returncode})")


def git_commit_and_push() -> bool:
    subprocess.run(["git", "add"] + FILES_TO_PUSH, cwd=str(_REPO_DIR), check=True)

    diff = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=str(_REPO_DIR))
    if diff.returncode == 0:
        print("אין שינוי לעומת מה שכבר ב-GitHub.")
        return False

    subprocess.run(
        ["git", "commit", "-m", "Daily local update (bizportal/BOI blocked from GitHub)"],
        cwd=str(_REPO_DIR), check=True,
    )
    subprocess.run(["git", "push"], cwd=str(_REPO_DIR), check=True)
    print("✅ נדחף ל-GitHub בהצלחה.")
    return True


def main():
    step("שלב 1/2: מריץ את run_daily_update.py המקומי")
    run_daily_update()

    step("שלב 2/2: דוחף את התוצאה ל-GitHub")
    git_commit_and_push()

    print("\n🎉 הריצה היומית המקומית הושלמה.")


if __name__ == "__main__":
    main()
