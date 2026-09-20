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

הערה חשובה על התנגשויות: מכיוון שה-workflow בענן (tase-update.yml)
ממשיך לרוץ במקביל וגם הוא דוחף שינויים לאותם קבצים בדיוק
(ytm_computed.xlsx, docs/ytm_dashboard.html) - יש סיכוי אמיתי שה-push
המקומי יתנגש עם שינוי שכבר יש ב-GitHub. בדיקה בפועל (05/09/2026)
הראתה שגם `git merge -X ours` לא תמיד "זוכה" בקובץ הזה - כנראה כי
כל הקוד המיוצר יושב בשורה אחת ארוכה בקובץ ה-HTML, וזה מבלבל את
אלגוריתם ה-diff של git ברמת שורות. לכן הפתרון כאן הוא כפול:
1. .gitattributes עם merge=ours על הקבצים האלה (יציב יותר מ--X ours).
2. אחרי כל merge - בדיקה מפורשת שהתוכן בפועל תואם למה שהריצה הזו
   יצרה, ואם לא - "כפיית" הגרסה המקומית עם commit מתקן. כך גם אם
   הדרך הראשונה נכשלת מסיבה כלשהי, יש רשת ביטחון.

בסוף כל ריצה יש גם גיבוי נוסף, לא-קריטי ולא תלוי בגיט, לתיקיית
OneDrive מקומית (ראה ONEDRIVE_BACKUP_DIR) - עותק מראה (mirror) של כל
התיקייה חוץ מ-.git/__pycache__/downloads.

שלב נוסף (שלב 2/5) שולף מקומית מביזפורטל את השינוי השבועי של מדד
ת"א בנקים (ראה BIZPORTAL_BANKS_INDEX_ID/fetch_banks_index_override) -
כי ל-Yahoo אין נתונים אמינים לטיקר הזה - וכותב אותו ל-
bizportal_banks_index.json, שנקרא בהמשך ע"י fetch_weekly_review.py
דרך weekly-review-update.yml בענן.

שלב נוסף (שלב 3/5, מ-20/09/2026) שולף מקומית מהלמ"ס את מדד המחירים
לצרכן (ראה fetch_cpi_israel.py) וכותב אותו ל-weekly_cpi_israel.json -
עד עכשיו הקובץ הזה עודכן רק ידנית ונשאר תקוע עם נתוני הדוגמה
המקוריים מאז הקמת הפרויקט, כך שטבלת המאקרו בסקירה השבועית הציגה כל
שבוע בדיוק אותם נתונים ישנים.
"""

import datetime
import json
import os
import pathlib
import subprocess
import sys
import traceback

import fetch_cpi_israel
import fetch_pe

# כש-Task Scheduler מריץ את הסקריפט (ללא חלון קונסולה), ה-stdout
# לפעמים לא תומך ב-UTF-8 (עברית/אימוג'ים) ו-print() רגיל יכול לקרוס
# עם UnicodeEncodeError - וזה קורס בשקט לפני שאפילו מגיעים להרצת
# run_daily_update.py, בלי שום עקבות בשום לוג. לכן קודם כל דואגים
# שה-stdout/stderr תמיד יעבדו ב-UTF-8, גם אם משהו לא ניתן להצגה.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

_REPO_DIR = pathlib.Path(__file__).parent
RUN_DAILY_UPDATE_SCRIPT = _REPO_DIR / "run_daily_update.py"
WRAPPER_LOG_PATH = _REPO_DIR / "run_daily_local_log.txt"
GITATTRIBUTES_PATH = _REPO_DIR / ".gitattributes"
GIT_BRANCH = "main"

# מדד ת"א בנקים ב-Yahoo (TA-BANKS.TA) מחזיר נתונים דלילים מדי (ראה
# fetch_weekly_review.py, תוקן 19/09/2026) - נשלף כאן מקומית מביזפורטל
# (עמוד index_id=751) ונכתב לקובץ קטן, כדי שfetch_weekly_review.py
# בענן (weekly-review-update.yml) יוכל להשתמש בו כ-override כשYahoo
# נכשל לספק נתון אמין. לא קריטי: כשל כאן רק נרשם ליומן.
BIZPORTAL_BANKS_INDEX_ID = "751"
BANKS_INDEX_OVERRIDE_PATH = _REPO_DIR / "bizportal_banks_index.json"

# מדד המחירים לצרכן (הלמ"ס) - נשלף כאן מקומית (חסום מ-GitHub Actions,
# כמו ביזפורטל ובנק ישראל - ראה fetch_cpi_israel.py) ונכתב לקובץ
# הידני שrun_weekly_review.py כבר יודע לקרוא. עד 20/09/2026 הקובץ הזה
# עודכן רק ביד ונשאר עם נתוני הדוגמה המקוריים ללא שינוי.
WEEKLY_CPI_ISRAEL_PATH = _REPO_DIR / "weekly_cpi_israel.json"

# הקבצים שריצת run_daily_update.py משנה בפועל - רק אלה נדחפים.
# holdings.xlsx / market_pe_base.json / sector_mapping.json וכו' לא
# נגעים כאן - אלה מתעדכנים בתהליכים נפרדים משלהם. bizportal_banks_index.json
# ו-weekly_cpi_israel.json נכתבים ונדחפים כאן ישירות (לא ע"י
# run_daily_update.py), אבל זה עדיין המקום הנכון כדי שייכללו באותו commit.
FILES_TO_PUSH = [
    "ytm_computed.xlsx",
    "docs/ytm_dashboard.html",
    "run_log.txt",
    "bizportal_banks_index.json",
    "weekly_cpi_israel.json",
]

# קבצים שנוצרים אוטומטית מחדש בכל ריצה (לא נערכים ידנית) - בהתנגשות
# מול הענן, הגרסה מהריצה האחרונה תמיד מנצחת. run_log.txt מקבל
# "union" (מאחד שורות, לא בוחר צד) כי הוא קובץ שרק מתווסף אליו.
GITATTRIBUTES_LINES = [
    "ytm_computed.xlsx merge=ours",
    "docs/ytm_dashboard.html merge=ours",
    "run_log.txt merge=union",
]

# גיבוי נוסף (לא git) לתיקיית OneDrive שכבר מסונכרנת במחשב הזה - לא
# תחליף ל-GitHub (שהוא ה-source of truth וממשיך להיות מנגנון ה-push
# העיקרי), אלא רשת ביטחון עצמאית שלא תלויה בגיט בכלל. .git עצמו לא
# מגובה כאן (הוא כבר מגובה דרך GitHub, וסנכרון OneDrive על תיקיית
# .git פעילה עלול להתנגש עם כתיבות git ולגרום לשחיתות).
ONEDRIVE_BACKUP_DIR = pathlib.Path(r"C:\Users\chen\OneDrive\tase-ytm-dashboard-backup")
ONEDRIVE_BACKUP_EXCLUDE_DIRS = [".git", "__pycache__", "downloads"]


def log_wrapper_event(text: str) -> None:
    """כותב שורת אבחון לקובץ ייעודי - כדי שכשל (או פרטי דיבוג) לא
    ייעלמו בשקט בריצה מתוזמנת שאף אחד לא צופה בה."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(WRAPPER_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {text}\n")
    except Exception:
        pass


def log_wrapper_failure(exc: BaseException) -> None:
    log_wrapper_event("run_daily_local.py נכשל:\n" + traceback.format_exc())


def run_git(args, check=False):
    """מריץ פקודת git, לוכד stdout/stderr (כדי שיהיה מה לאבחן אם
    זה נכשל), ומחזיר את ה-CompletedProcess."""
    result = subprocess.run(
        ["git"] + args,
        cwd=str(_REPO_DIR),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        log_wrapper_event(
            f"git {' '.join(args)} -> קוד יציאה {result.returncode}\n"
            f"--- stdout ---\n{result.stdout}\n--- stderr ---\n{result.stderr}"
        )
    if check and result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} נכשל (קוד יציאה {result.returncode})")
    return result


def step(msg):
    print(f"\n=== {msg} ===")


def ensure_git_merge_config():
    """חד-פעמי ואידמפוטנטי: רושם את ה-driver 'ours' בהגדרות git
    המקומיות (לא ניתן להגדיר את זה רק דרך .gitattributes), ומוודא
    שהקובץ .gitattributes עצמו קיים וב-git עם השורות הנדרשות. אם היה
    צריך ליצור/לעדכן אותו - עושה לכך commit+push קטן ונפרד."""
    run_git(["config", "merge.ours.driver", "true"])

    existing = GITATTRIBUTES_PATH.read_text(encoding="utf-8") if GITATTRIBUTES_PATH.exists() else ""
    missing = [line for line in GITATTRIBUTES_LINES if line not in existing]
    if not missing:
        return

    with open(GITATTRIBUTES_PATH, "a", encoding="utf-8") as f:
        if existing and not existing.endswith("\n"):
            f.write("\n")
        for line in missing:
            f.write(line + "\n")

    run_git(["add", ".gitattributes"], check=True)
    commit = run_git(["commit", "-m", "Configure merge strategy for auto-generated files"])
    if commit.returncode == 0:
        push = run_git(["push"])
        if push.returncode != 0:
            log_wrapper_event("push של .gitattributes נכשל - ינסה שוב בריצה הבאה (לא קריטי).")


def pull_latest_before_run():
    """מושך מ-GitHub לפני שמתחילים - כדי לצמצם (לא לחסל לגמרי, יש
    עדיין חלון זמן) את הסיכוי להתנגשות בסוף הריצה. לא קריטי אם זה
    נכשל (למשל אין רשת רגעית) - ממשיכים בכל מקרה."""
    result = run_git(["pull", "--ff-only"])
    if result.returncode != 0:
        print("⚠️  git pull בתחילת הריצה לא הצליח (ממשיכים בכל זאת).")


def run_daily_update():
    # capture_output=True: בלעדיו, אם run_daily_update.py קורס עוד לפני
    # שהוא מצליח לפתוח את run_log.txt (למשל PermissionError חד-פעמי -
    # קרה בפועל ב-07/09/2026), ה-traceback האמיתי הולך ל-stderr של
    # תהליך שרץ בלי חלון קונסולה (Task Scheduler) - כלומר נעלם לגמרי,
    # ונשארת רק הודעת "קוד יציאה 1" הגנרית בלי שום מידע לאבחון.
    # PYTHONIOENCODING: הגנה כפולה בנוסף ל-sys.stdout.reconfigure() שכבר
    # קיים בתוך run_daily_update.py עצמו - קובעת את קידוד ברירת המחדל
    # של ה-stdout/stderr של התהליך הבן עוד לפני שהוא בכלל מתחיל לרוץ.
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    result = subprocess.run(
        [sys.executable, str(RUN_DAILY_UPDATE_SCRIPT)],
        cwd=str(_REPO_DIR),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )
    if result.returncode != 0:
        log_wrapper_event(
            f"run_daily_update.py נכשל (קוד יציאה {result.returncode})\n"
            f"--- stdout ---\n{result.stdout}\n--- stderr ---\n{result.stderr}"
        )
        raise RuntimeError(f"run_daily_update.py נכשל (קוד יציאה {result.returncode})")


def git_commit_and_push() -> bool:
    run_git(["add"] + FILES_TO_PUSH, check=True)

    diff = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=str(_REPO_DIR))
    if diff.returncode == 0:
        print("אין שינוי לעומת מה שכבר ב-GitHub.")
        return False

    run_git(["commit", "-m", "Daily local update (bizportal/BOI blocked from GitHub)"], check=True)
    our_commit = run_git(["rev-parse", "HEAD"], check=True).stdout.strip()

    push = run_git(["push"])
    if push.returncode == 0:
        print("✅ נדחף ל-GitHub בהצלחה.")
        return True

    print(
        "⚠️  git push נכשל - כנראה שה-workflow בענן דחף באותו זמן שינוי לאותם קבצים "
        "(ytm_computed.xlsx / הדשבורד). מנסה לאחד אוטומטית עם הגרסה מהריצה הזו..."
    )

    run_git(["fetch", "origin"], check=True)
    merge = run_git(["merge", "--no-edit", f"origin/{GIT_BRANCH}"])
    if merge.returncode != 0:
        run_git(["merge", "--abort"])
        raise RuntimeError("git merge נכשל - נדרשת בדיקה ידנית (git status במחשב)")

    # ביטחון כפול: לא סומכים רק על .gitattributes/merge=ours - בודקים
    # בפועל שהקבצים המיוצרים אוטומטית עדיין תואמים למה שהריצה הזו
    # יצרה, ואם המיזוג בכל זאת "בחר" בטעות בגרסה מהענן - כופים את
    # הגרסה המקומית ומוסיפים commit מתקן.
    run_git(["checkout", our_commit, "--"] + FILES_TO_PUSH, check=True)
    run_git(["add"] + FILES_TO_PUSH, check=True)
    fixup_diff = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=str(_REPO_DIR))
    if fixup_diff.returncode != 0:
        run_git(["commit", "-m", "Ensure local run's generated files win after merge"], check=True)
        log_wrapper_event("המיזוג האוטומטי לא שמר על הגרסה המקומית - תוקן עם commit נוסף.")

    push2 = run_git(["push"])
    if push2.returncode != 0:
        raise RuntimeError("git push נכשל גם אחרי merge אוטומטי - נדרשת בדיקה ידנית")

    print("✅ נדחף ל-GitHub בהצלחה (אחרי איחוד אוטומטי עם השינוי שהיה בענן).")
    return True


def fetch_banks_index_override() -> None:
    """שולף את השינוי השבועי של מדד ת"א בנקים מביזפורטל (עובד רק
    מהמחשב המקומי - חסום מ-GitHub Actions) וכותב אותו ל-
    bizportal_banks_index.json. לא קריטי: כשל כאן רק נרשם ליומן,
    ואם הקובץ כבר קיים מריצה קודמת הוא פשוט נשאר כמו שהוא."""
    pct, err = fetch_pe.fetch_index_weekly_change(BIZPORTAL_BANKS_INDEX_ID)
    if err:
        log_wrapper_event(f"⚠️  שליפת מדד ת\"א בנקים מביזפורטל נכשלה: {err}")
        return
    data = {
        "pct": pct,
        "as_of": datetime.date.today().isoformat(),
        "source": f"bizportal index {BIZPORTAL_BANKS_INDEX_ID}",
    }
    with open(BANKS_INDEX_OVERRIDE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ מדד ת\"א בנקים (ביזפורטל): {pct * 100:+.2f}% שבועי.")


def update_weekly_cpi_israel() -> None:
    """שולף מהלמ"ס (עובד רק מהמחשב המקומי - חסום מ-GitHub Actions) את
    השינוי החודשי/שנתי העדכני של מדד המחירים לצרכן, וכותב אותו ל-
    weekly_cpi_israel.json - עד עכשיו הקובץ הזה עודכן רק ידנית ונשאר
    תקוע עם נתוני הדוגמה המקוריים. לא קריטי: כשל כאן רק נרשם ליומן,
    ואם הקובץ כבר קיים מריצה קודמת הוא פשוט נשאר כמו שהוא."""
    result, err = fetch_cpi_israel.fetch_and_summarize()
    if err:
        log_wrapper_event(f"⚠️  עדכון מדד המחירים לצרכן (למ\"ס) נכשל: {err}")
        return
    with open(WEEKLY_CPI_ISRAEL_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"✅ מדד המחירים לצרכן (למ\"ס): {result['value']} - {result['note']}")


def backup_to_onedrive() -> None:
    """מראה (mirror) את כל תיקיית הפרויקט לתיקיית הגיבוי ב-OneDrive,
    חוץ מ-.git/__pycache__/downloads. לא קריטי: כשל כאן רק נרשם ליומן
    ולא מפיל את שאר הריצה - זה שכבת גיבוי נוספת, לא הפייפליין העיקרי."""
    if not ONEDRIVE_BACKUP_DIR.exists():
        log_wrapper_event(
            f"⚠️  תיקיית הגיבוי {ONEDRIVE_BACKUP_DIR} לא נמצאה - מדלג על גיבוי ה-OneDrive."
        )
        return

    args = ["robocopy", str(_REPO_DIR), str(ONEDRIVE_BACKUP_DIR), "/MIR"]
    for d in ONEDRIVE_BACKUP_EXCLUDE_DIRS:
        args += ["/XD", str(_REPO_DIR / d)]
    args += ["/R:1", "/W:1", "/NFL", "/NDL", "/NP"]

    result = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace")
    # robocopy: 0-7 = הצלחה (סוגי שינוי שונים), 8+ = כשל אמיתי.
    if result.returncode >= 8:
        log_wrapper_event(
            f"⚠️  גיבוי ל-OneDrive נכשל (robocopy קוד יציאה {result.returncode})\n"
            f"--- stdout ---\n{result.stdout}\n--- stderr ---\n{result.stderr}"
        )
    else:
        print(f"✅ גובה ל-OneDrive בהצלחה (robocopy קוד יציאה {result.returncode}).")


def main():
    ensure_git_merge_config()

    step("שלב 0/5: מושך עדכונים אחרונים מ-GitHub")
    pull_latest_before_run()

    step("שלב 1/5: מריץ את run_daily_update.py המקומי")
    run_daily_update()

    step("שלב 2/5: שולף מדד ת\"א בנקים מביזפורטל (עבור הסקירה השבועית)")
    try:
        fetch_banks_index_override()
    except Exception as exc:
        log_wrapper_event(f"⚠️  שליפת מדד ת\"א בנקים נכשלה עם חריגה: {exc}")

    step("שלב 3/5: מעדכן מדד המחירים לצרכן מהלמ\"ס (עבור הסקירה השבועית)")
    try:
        update_weekly_cpi_israel()
    except Exception as exc:
        log_wrapper_event(f"⚠️  עדכון מדד המחירים לצרכן נכשל עם חריגה: {exc}")

    step("שלב 4/5: דוחף את התוצאה ל-GitHub")
    git_commit_and_push()

    step("שלב 5/5: מגבה ל-OneDrive")
    try:
        backup_to_onedrive()
    except Exception as exc:
        log_wrapper_event(f"⚠️  גיבוי ל-OneDrive נכשל עם חריגה: {exc}")

    print("\n🎉 הריצה היומית המקומית הושלמה.")


if __name__ == "__main__":
    try:
        main()
    except BaseException as exc:
        log_wrapper_failure(exc)
        raise
