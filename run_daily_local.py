# -*- coding: utf-8 -*-
"""
run_daily_local.py
׳¢׳•׳˜׳£ ׳׳× run_daily_update.py ׳׳”׳¨׳¦׳” ׳׳§׳•׳׳™׳× (׳‘׳׳§׳•׳ ׳‘-GitHub Actions) -
׳›׳™ ׳‘׳™׳–׳₪׳•׳¨׳˜׳/׳‘׳ ׳§ ׳™׳©׳¨׳׳/׳׳"׳¡ ׳—׳•׳¡׳׳™׳ ׳‘׳§׳©׳•׳× ׳׳©׳¨׳×׳™ GitHub (403/timeout),
׳׳‘׳ ׳¢׳•׳‘׳“׳™׳ ׳×׳§׳™׳ ׳׳”׳׳—׳©׳‘ ׳”׳–׳” (׳׳•׳׳× ׳‘׳₪׳•׳¢׳).

׳׳—׳¨׳™ ׳©׳”׳¨׳™׳¦׳” ׳”׳׳§׳•׳׳™׳× ׳׳¡׳×׳™׳™׳׳×, ׳“׳•׳—׳£ ׳׳•׳˜׳•׳׳˜׳™׳× ׳-GitHub ׳׳× ׳”׳§׳‘׳¦׳™׳
׳©׳”׳©׳×׳ ׳• - ׳›׳“׳™ ׳©׳”׳“׳©׳‘׳•׳¨׳“ ׳”׳—׳™ (GitHub Pages) ׳™׳×׳¢׳“׳›׳.

׳׳™׳•׳¢׳“ ׳׳”׳¨׳¦׳” 6 ׳₪׳¢׳׳™׳ ׳‘׳™׳•׳, ׳¨׳׳©׳•׳-׳©׳™׳©׳™, ׳“׳¨׳ Windows Task Scheduler -
׳‘׳“׳™׳•׳§ ׳›׳׳• ׳©׳”-workflow tase-update.yml ׳¢׳©׳” ׳§׳•׳“׳.

׳”׳¢׳¨׳” ׳—׳©׳•׳‘׳” ׳¢׳ ׳”׳×׳ ׳’׳©׳•׳™׳•׳×: ׳׳›׳™׳•׳•׳ ׳©׳”-workflow ׳‘׳¢׳ ׳ (tase-update.yml)
׳׳׳©׳™׳ ׳׳¨׳•׳¥ ׳‘׳׳§׳‘׳™׳ ׳•׳’׳ ׳”׳•׳ ׳“׳•׳—׳£ ׳©׳™׳ ׳•׳™׳™׳ ׳׳׳•׳×׳ ׳§׳‘׳¦׳™׳ ׳‘׳“׳™׳•׳§
(ytm_computed.xlsx, docs/ytm_dashboard.html) - ׳™׳© ׳¡׳™׳›׳•׳™ ׳׳׳™׳×׳™ ׳©׳”-push
׳”׳׳§׳•׳׳™ ׳™׳×׳ ׳’׳© ׳¢׳ ׳©׳™׳ ׳•׳™ ׳©׳›׳‘׳¨ ׳™׳© ׳‘-GitHub. ׳‘׳“׳™׳§׳” ׳‘׳₪׳•׳¢׳ (05/09/2026)
׳”׳¨׳׳×׳” ׳©׳’׳ `git merge -X ours` ׳׳ ׳×׳׳™׳“ "׳–׳•׳›׳”" ׳‘׳§׳•׳‘׳¥ ׳”׳–׳” - ׳›׳ ׳¨׳׳” ׳›׳™
׳›׳ ׳”׳§׳•׳“ ׳”׳׳™׳•׳¦׳¨ ׳™׳•׳©׳‘ ׳‘׳©׳•׳¨׳” ׳׳—׳× ׳׳¨׳•׳›׳” ׳‘׳§׳•׳‘׳¥ ׳”-HTML, ׳•׳–׳” ׳׳‘׳׳‘׳ ׳׳×
׳׳׳’׳•׳¨׳™׳×׳ ׳”-diff ׳©׳ git ׳‘׳¨׳׳× ׳©׳•׳¨׳•׳×. ׳׳›׳ ׳”׳₪׳×׳¨׳•׳ ׳›׳׳ ׳”׳•׳ ׳›׳₪׳•׳:
1. .gitattributes ׳¢׳ merge=ours ׳¢׳ ׳”׳§׳‘׳¦׳™׳ ׳”׳׳׳” (׳™׳¦׳™׳‘ ׳™׳•׳×׳¨ ׳--X ours).
2. ׳׳—׳¨׳™ ׳›׳ merge - ׳‘׳“׳™׳§׳” ׳׳₪׳•׳¨׳©׳× ׳©׳”׳×׳•׳›׳ ׳‘׳₪׳•׳¢׳ ׳×׳•׳׳ ׳׳׳” ׳©׳”׳¨׳™׳¦׳” ׳”׳–׳•
   ׳™׳¦׳¨׳”, ׳•׳׳ ׳׳ - "׳›׳₪׳™׳™׳×" ׳”׳’׳¨׳¡׳” ׳”׳׳§׳•׳׳™׳× ׳¢׳ commit ׳׳×׳§׳. ׳›׳ ׳’׳ ׳׳
   ׳”׳“׳¨׳ ׳”׳¨׳׳©׳•׳ ׳” ׳ ׳›׳©׳׳× ׳׳¡׳™׳‘׳” ׳›׳׳©׳”׳™, ׳™׳© ׳¨׳©׳× ׳‘׳™׳˜׳—׳•׳.

׳‘׳¡׳•׳£ ׳›׳ ׳¨׳™׳¦׳” ׳™׳© ׳’׳ ׳’׳™׳‘׳•׳™ ׳ ׳•׳¡׳£, ׳׳-׳§׳¨׳™׳˜׳™ ׳•׳׳ ׳×׳׳•׳™ ׳‘׳’׳™׳˜, ׳׳×׳™׳§׳™׳™׳×
OneDrive ׳׳§׳•׳׳™׳× (׳¨׳׳” ONEDRIVE_BACKUP_DIR) - ׳¢׳•׳×׳§ ׳׳¨׳׳” (mirror) ׳©׳ ׳›׳
׳”׳×׳™׳§׳™׳™׳” ׳—׳•׳¥ ׳-.git/__pycache__/downloads.

׳©׳׳‘ ׳ ׳•׳¡׳£ (׳©׳׳‘ 2/5) ׳©׳•׳׳£ ׳׳§׳•׳׳™׳× ׳׳‘׳™׳–׳₪׳•׳¨׳˜׳ ׳׳× ׳”׳©׳™׳ ׳•׳™ ׳”׳©׳‘׳•׳¢׳™ ׳©׳ ׳׳“׳“
׳×"׳ ׳‘׳ ׳§׳™׳ (׳¨׳׳” BIZPORTAL_BANKS_INDEX_ID/fetch_banks_index_override) -
׳›׳™ ׳-Yahoo ׳׳™׳ ׳ ׳×׳•׳ ׳™׳ ׳׳׳™׳ ׳™׳ ׳׳˜׳™׳§׳¨ ׳”׳–׳” - ׳•׳›׳•׳×׳‘ ׳׳•׳×׳• ׳-
bizportal_banks_index.json, ׳©׳ ׳§׳¨׳ ׳‘׳”׳׳©׳ ׳¢"׳™ fetch_weekly_review.py
׳“׳¨׳ weekly-review-update.yml ׳‘׳¢׳ ׳.

׳©׳׳‘ ׳ ׳•׳¡׳£ (׳©׳׳‘ 4/6, ׳-20/09/2026) ׳©׳•׳׳£ ׳׳§׳•׳׳™׳× ׳׳”׳׳"׳¡ ׳׳× ׳׳“׳“ ׳”׳׳—׳™׳¨׳™׳
׳׳¦׳¨׳›׳ (׳¨׳׳” fetch_cpi_israel.py) ׳•׳›׳•׳×׳‘ ׳׳•׳×׳• ׳-weekly_cpi_israel.json -
׳¢׳“ ׳¢׳›׳©׳™׳• ׳”׳§׳•׳‘׳¥ ׳”׳–׳” ׳¢׳•׳“׳›׳ ׳¨׳§ ׳™׳“׳ ׳™׳× ׳•׳ ׳©׳׳¨ ׳×׳§׳•׳¢ ׳¢׳ ׳ ׳×׳•׳ ׳™ ׳”׳“׳•׳’׳׳”
׳”׳׳§׳•׳¨׳™׳™׳ ׳׳׳– ׳”׳§׳׳× ׳”׳₪׳¨׳•׳™׳§׳˜, ׳›׳ ׳©׳˜׳‘׳׳× ׳”׳׳׳§׳¨׳• ׳‘׳¡׳§׳™׳¨׳” ׳”׳©׳‘׳•׳¢׳™׳× ׳”׳¦׳™׳’׳” ׳›׳
׳©׳‘׳•׳¢ ׳‘׳“׳™׳•׳§ ׳׳•׳×׳ ׳ ׳×׳•׳ ׳™׳ ׳™׳©׳ ׳™׳.

׳©׳׳‘ ׳ ׳•׳¡׳£ (׳©׳׳‘ 0/6, ׳-02/10/2026): ׳׳₪׳ ׳™ ׳›׳ ׳¨׳™׳¦׳”, ׳‘׳•׳“׳§ ׳”׳׳ ׳™׳© ׳©׳™׳ ׳•׳™׳™׳
׳׳-׳׳—׳•׳™׳‘׳™׳ (uncommitted) ׳‘׳§׳‘׳¦׳™׳ ׳©׳›׳‘׳¨ ׳‘׳׳¢׳§׳‘ git ׳׳׳‘׳“ ׳׳׳” ׳©׳”׳¨׳™׳¦׳” ׳¢׳¦׳׳”
׳׳׳•׳¨׳” ׳׳©׳ ׳•׳× (FILES_TO_PUSH). ׳–׳” ׳‘׳“׳™׳•׳§ ׳׳” ׳©׳’׳¨׳ ׳׳׳¨׳‘׳¢׳” ׳›׳©׳׳•׳ ׳•׳× ׳¨׳¦׳•׳₪׳™׳
׳‘׳™׳•׳ ׳׳—׳“ (16/09/2026): git pull --ff-only ׳ ׳›׳©׳ ׳¢׳ "Your local
changes... would be overwritten by merge", ׳•׳–׳” ׳—׳–׳¨ ׳¢׳ ׳¢׳¦׳׳• ׳‘׳›׳ ׳¨׳™׳¦׳”
׳¢׳“ ׳©׳”׳‘׳¢׳™׳” ׳×׳•׳§׳ ׳” ׳™׳“׳ ׳™׳×. ׳”׳‘׳“׳™׳§׳” ׳”׳–׳• ׳׳ ׳¢׳•׳¦׳¨׳× ׳׳× ׳”׳¨׳™׳¦׳” (׳™׳›׳•׳ ׳׳”׳™׳•׳× ׳’׳
׳©׳™׳ ׳•׳™ ׳׳’׳™׳˜׳™׳׳™ ׳©׳¢׳“׳™׳™׳ ׳׳ ׳”׳’׳™׳¢ ׳–׳׳ ׳•) - ׳¨׳§ ׳׳×׳¨׳™׳¢׳” ׳׳¨׳׳© ׳‘׳׳•׳’, ׳›׳“׳™
׳©׳”׳׳‘׳—׳•׳ ׳™׳”׳™׳” ׳׳™׳™׳“׳™ ׳‘׳׳§׳•׳ ׳׳”׳×׳—׳™׳ ׳"git pull ׳ ׳›׳©׳" ׳”׳׳¢׳•׳¨׳₪׳.

׳¢׳“׳›׳•׳ ׳-28/10/2026: holdings.xlsx (׳§׳•׳‘׳¥ ׳”׳”׳—׳–׳§׳•׳×, ׳©׳׳×׳¢׳“׳›׳ ׳™׳“׳ ׳™׳× ׳¢"׳™
׳—׳) ׳”׳¦׳˜׳¨׳£ ׳-FILES_TO_PUSH ׳•׳-.gitattributes (merge=ours). ׳§׳•׳“׳ ׳׳›׳
׳”׳§׳•׳‘׳¥ ׳”׳–׳” ׳”׳™׳” ׳“׳•׳•׳§׳ ׳”׳“׳•׳’׳׳” ׳”׳§׳׳׳¡׳™׳× ׳׳§׳•׳‘׳¥ "׳׳׳•׳›׳׳" ׳©׳’׳¨׳ ׳׳›׳©׳ ׳”-pull
׳©׳×׳•׳׳¨ ׳׳׳¢׳׳” (16/09/2026) - ׳•׳¢׳“׳›׳•׳ ׳• ׳“׳¨׳© ׳”׳¨׳¦׳” ׳™׳“׳ ׳™׳× ׳ ׳₪׳¨׳“׳×
(update_holdings.bat/update_holdings_and_run.bat). ׳׳¢׳›׳©׳™׳•, ׳›׳ ׳¢׳¨׳™׳›׳”
׳™׳“׳ ׳™׳× ׳-holdings.xlsx (׳‘׳×׳™׳§׳™׳™׳× ׳”׳₪׳¨׳•׳™׳§׳˜ ׳¢׳ ׳”׳׳—׳©׳‘ ׳”׳–׳”) ׳×׳™׳›׳׳ ׳׳•׳˜׳•׳׳˜׳™׳×
׳‘-commit/push ׳©׳ ׳”׳¨׳™׳¦׳” ׳”׳׳×׳•׳–׳׳ ׳× ׳”׳‘׳׳” (׳¢׳“ 6 ׳₪׳¢׳׳™׳ ׳‘׳™׳•׳) - ׳‘׳׳™ ׳¦׳•׳¨׳
׳‘׳”׳¨׳¦׳” ׳™׳“׳ ׳™׳× ׳ ׳₪׳¨׳“׳×, ׳•׳‘׳׳™ ׳©׳”׳§׳•׳‘׳¥ "׳”׳׳׳•׳›׳׳" ׳™׳—׳¡׳•׳ ׳׳× ׳”-pull. ׳”׳¡׳§׳¨׳™׳₪׳˜׳™׳
׳”׳™׳“׳ ׳™׳™׳ ׳¢׳“׳™׳™׳ ׳§׳™׳™׳׳™׳ ׳•׳©׳™׳׳•׳©׳™׳™׳ ׳׳ ׳¨׳•׳¦׳™׳ ׳׳“׳—׳•׳£ ׳©׳™׳ ׳•׳™ ׳׳™׳™׳“׳™׳× ׳‘׳׳™ ׳׳—׳›׳•׳×
׳׳¨׳™׳¦׳” ׳”׳׳×׳•׳–׳׳ ׳× ׳”׳‘׳׳”.

׳¢׳“׳›׳•׳ ׳-01/11/2026 (׳©׳׳‘ 2/7, sync_holdings_from_onedrive): ׳—׳ ׳¢׳•׳¨׳
׳׳× holdings.xlsx ׳׳׳¡׳₪׳¨ ׳׳—׳©׳‘׳™׳ ׳©׳•׳ ׳™׳, ׳׳ ׳¨׳§ ׳-chensurfacepro7 (׳”׳׳—׳©׳‘
׳©׳׳¨׳™׳¥ ׳׳× ׳”׳׳•׳˜׳•׳׳¦׳™׳”) - ׳›׳•׳׳ ׳׳—׳•׳‘׳¨׳™׳ ׳׳׳•׳×׳• ׳—׳©׳‘׳•׳ OneDrive. ׳¢׳¨׳™׳›׳” ׳›׳–׳•
׳ ׳¢׳©׳™׳× ׳™׳©׳™׳¨׳•׳× ׳‘׳×׳•׳ ׳×׳™׳§׳™׳™׳× ׳”׳’׳™׳‘׳•׳™ ׳”׳§׳™׳™׳׳× ׳‘-OneDrive
(ONEDRIVE_BACKUP_DIR/holdings.xlsx), ׳©׳›׳‘׳¨ ׳׳¡׳×׳ ׳›׳¨׳ ׳× ׳׳•׳˜׳•׳׳˜׳™׳× ׳‘׳™׳ ׳›׳
׳”׳׳—׳©׳‘׳™׳ (׳׳ ׳‘׳×׳™׳§׳™׳™׳× ׳”׳₪׳¨׳•׳™׳§׳˜ ׳¢׳¦׳׳” - ׳–׳• ׳§׳™׳™׳׳× ׳¨׳§ ׳¢׳ chensurfacepro7).
׳׳₪׳ ׳™ ׳›׳ ׳¨׳™׳¦׳”, ׳׳ ׳”׳¢׳•׳×׳§ ׳©׳ ׳—׳“׳© ׳™׳•׳×׳¨ ׳׳”׳¢׳•׳×׳§ ׳”׳׳§׳•׳׳™ ׳‘׳×׳™׳§׳™׳™׳× ׳”׳₪׳¨׳•׳™׳§׳˜ -
׳”׳•׳ ׳׳•׳¢׳×׳§ ׳׳›׳׳, ׳›׳ ׳©׳”׳¨׳™׳¦׳” (׳•׳“׳—׳™׳₪׳× holdings.xlsx ׳-GitHub ׳©׳‘׳”׳׳©׳›׳”)
׳×׳׳™׳“ ׳׳×׳‘׳¡׳¡׳× ׳¢׳ ׳”׳¢׳“׳›׳•׳ ׳”׳׳—׳¨׳•׳ ׳׳›׳ ׳׳—׳“ ׳׳”׳׳—׳©׳‘׳™׳. ׳›׳™׳•׳•׳ ׳”׳”׳¢׳×׳§׳” ׳”׳”׳₪׳•׳
(׳₪׳¨׳•׳™׳§׳˜ -> OneDrive) ׳׳׳©׳™׳ ׳׳”׳×׳‘׳¦׳¢ ׳›׳¨׳’׳™׳ ׳‘׳¡׳•׳£ ׳”׳¨׳™׳¦׳” ׳¢"׳™
backup_to_onedrive() ׳”׳§׳™׳™׳, ׳›׳ ׳©׳”׳§׳•׳‘׳¥ ׳ ׳©׳׳¨ ׳׳¡׳•׳ ׳›׳¨׳ ׳‘׳©׳ ׳™ ׳”׳›׳™׳•׳•׳ ׳™׳ ׳‘׳׳™
׳§׳•׳“ ׳›׳₪׳•׳. ׳”׳¢׳¨׳”: ׳׳ ׳©׳ ׳™ ׳׳—׳©׳‘׳™׳ ׳¢׳•׳¨׳›׳™׳ ׳׳× ׳׳•׳×׳• ׳§׳•׳‘׳¥ ׳׳׳© ׳‘׳׳•׳×׳• ׳—׳׳•׳
׳–׳׳ ׳§׳¦׳¨ (׳׳₪׳ ׳™ ׳©׳”-OneDrive sync ׳”׳¡׳₪׳™׳§ ׳׳”׳×׳¢׳“׳›׳) - ׳–׳” ׳¢׳“׳™׳™׳ ׳¡׳™׳›׳•׳ ׳¨׳’׳™׳
׳©׳ ׳§׳•׳‘׳¥ Excel ׳׳©׳•׳×׳£ ׳™׳—׳™׳“, ׳׳ ׳׳©׳”׳• ׳©׳”׳§׳•׳“ ׳”׳–׳” ׳₪׳•׳×׳¨; OneDrive ׳‘׳¢׳¦׳׳•
׳™׳•׳¦׳¨ "׳¢׳•׳×׳§ ׳׳×׳ ׳’׳©" (conflicted copy) ׳׳ ׳–׳” ׳§׳•׳¨׳”.
"""

import datetime
import json
import os
import pathlib
import shutil
import subprocess
import sys
import traceback

import fetch_cpi_israel
import fetch_pe

# ׳›׳©-Task Scheduler ׳׳¨׳™׳¥ ׳׳× ׳”׳¡׳§׳¨׳™׳₪׳˜ (׳׳׳ ׳—׳׳•׳ ׳§׳•׳ ׳¡׳•׳׳”), ׳”-stdout
# ׳׳₪׳¢׳׳™׳ ׳׳ ׳×׳•׳׳ ׳‘-UTF-8 (׳¢׳‘׳¨׳™׳×/׳׳™׳׳•׳’'׳™׳) ׳•-print() ׳¨׳’׳™׳ ׳™׳›׳•׳ ׳׳§׳¨׳•׳¡
# ׳¢׳ UnicodeEncodeError - ׳•׳–׳” ׳§׳•׳¨׳¡ ׳‘׳©׳§׳˜ ׳׳₪׳ ׳™ ׳©׳׳₪׳™׳׳• ׳׳’׳™׳¢׳™׳ ׳׳”׳¨׳¦׳×
# run_daily_update.py, ׳‘׳׳™ ׳©׳•׳ ׳¢׳§׳‘׳•׳× ׳‘׳©׳•׳ ׳׳•׳’. ׳׳›׳ ׳§׳•׳“׳ ׳›׳ ׳“׳•׳׳’׳™׳
# ׳©׳”-stdout/stderr ׳×׳׳™׳“ ׳™׳¢׳‘׳“׳• ׳‘-UTF-8, ׳’׳ ׳׳ ׳׳©׳”׳• ׳׳ ׳ ׳™׳×׳ ׳׳”׳¦׳’׳”.
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

# ׳׳“׳“ ׳×"׳ ׳‘׳ ׳§׳™׳ ׳‘-Yahoo (TA-BANKS.TA) ׳׳—׳–׳™׳¨ ׳ ׳×׳•׳ ׳™׳ ׳“׳׳™׳׳™׳ ׳׳“׳™ (׳¨׳׳”
# fetch_weekly_review.py, ׳×׳•׳§׳ 19/09/2026) - ׳ ׳©׳׳£ ׳›׳׳ ׳׳§׳•׳׳™׳× ׳׳‘׳™׳–׳₪׳•׳¨׳˜׳
# (׳¢׳׳•׳“ index_id=751) ׳•׳ ׳›׳×׳‘ ׳׳§׳•׳‘׳¥ ׳§׳˜׳, ׳›׳“׳™ ׳©fetch_weekly_review.py
# ׳‘׳¢׳ ׳ (weekly-review-update.yml) ׳™׳•׳›׳ ׳׳”׳©׳×׳׳© ׳‘׳• ׳›-override ׳›׳©Yahoo
# ׳ ׳›׳©׳ ׳׳¡׳₪׳§ ׳ ׳×׳•׳ ׳׳׳™׳. ׳׳ ׳§׳¨׳™׳˜׳™: ׳›׳©׳ ׳›׳׳ ׳¨׳§ ׳ ׳¨׳©׳ ׳׳™׳•׳׳.
BIZPORTAL_BANKS_INDEX_ID = "751"
BANKS_INDEX_OVERRIDE_PATH = _REPO_DIR / "bizportal_banks_index.json"

# ׳׳“׳“ ׳”׳׳—׳™׳¨׳™׳ ׳׳¦׳¨׳›׳ (׳”׳׳"׳¡) - ׳ ׳©׳׳£ ׳›׳׳ ׳׳§׳•׳׳™׳× (׳—׳¡׳•׳ ׳-GitHub Actions,
# ׳›׳׳• ׳‘׳™׳–׳₪׳•׳¨׳˜׳ ׳•׳‘׳ ׳§ ׳™׳©׳¨׳׳ - ׳¨׳׳” fetch_cpi_israel.py) ׳•׳ ׳›׳×׳‘ ׳׳§׳•׳‘׳¥
# ׳”׳™׳“׳ ׳™ ׳©run_weekly_review.py ׳›׳‘׳¨ ׳™׳•׳“׳¢ ׳׳§׳¨׳•׳. ׳¢׳“ 20/09/2026 ׳”׳§׳•׳‘׳¥ ׳”׳–׳”
# ׳¢׳•׳“׳›׳ ׳¨׳§ ׳‘׳™׳“ ׳•׳ ׳©׳׳¨ ׳¢׳ ׳ ׳×׳•׳ ׳™ ׳”׳“׳•׳’׳׳” ׳”׳׳§׳•׳¨׳™׳™׳ ׳׳׳ ׳©׳™׳ ׳•׳™.
WEEKLY_CPI_ISRAEL_PATH = _REPO_DIR / "weekly_cpi_israel.json"

# ׳§׳•׳‘׳¥ ׳”׳”׳—׳–׳§׳•׳× ׳‘׳×׳™׳§׳™׳™׳× ׳”׳₪׳¨׳•׳™׳§׳˜ ׳¢׳¦׳׳” (׳–׳” ׳׳” ׳©-run_daily_update.py
# ׳§׳•׳¨׳ ׳‘׳₪׳•׳¢׳, ׳•׳–׳” ׳׳” ׳©׳ ׳“׳—׳£ ׳-GitHub ׳›׳—׳׳§ ׳-FILES_TO_PUSH).
HOLDINGS_XLSX_PATH = _REPO_DIR / "holdings.xlsx"

# ׳”׳§׳‘׳¦׳™׳ ׳©׳ ׳“׳—׳₪׳™׳ ׳‘׳¡׳•׳£ ׳›׳ ׳¨׳™׳¦׳”. ׳¨׳•׳‘׳ ׳ ׳•׳¦׳¨׳™׳ ׳׳•׳˜׳•׳׳˜׳™׳× ׳¢"׳™
# run_daily_update.py; bizportal_banks_index.json ׳•-weekly_cpi_israel.json
# ׳ ׳›׳×׳‘׳™׳ ׳•׳ ׳“׳—׳₪׳™׳ ׳›׳׳ ׳™׳©׳™׳¨׳•׳× (׳׳ ׳¢"׳™ run_daily_update.py), ׳׳‘׳ ׳–׳”
# ׳¢׳“׳™׳™׳ ׳”׳׳§׳•׳ ׳”׳ ׳›׳•׳ ׳›׳“׳™ ׳©׳™׳™׳›׳׳׳• ׳‘׳׳•׳×׳• commit. holdings.xlsx ׳”׳•׳ ׳”׳™׳—׳™׳“
# ׳©׳ ׳¢׳¨׳ ׳™׳“׳ ׳™׳× (׳¢"׳™ ׳—׳, ׳׳ ׳¢"׳™ ׳§׳•׳“) - ׳”׳•׳ ׳›׳׳ ׳›׳“׳™ ׳©׳¢׳¨׳™׳›׳” ׳™׳“׳ ׳™׳× ׳×׳™׳›׳׳
# ׳׳•׳˜׳•׳׳˜׳™׳× ׳‘׳¨׳™׳¦׳” ׳”׳׳×׳•׳–׳׳ ׳× ׳”׳‘׳׳”, ׳‘׳׳§׳•׳ ׳׳“׳¨׳•׳© ׳”׳¨׳¦׳” ׳ ׳₪׳¨׳“׳×
# (update_holdings.bat) ׳•׳‘׳׳§׳•׳ ׳׳”׳™׳©׳׳¨ "׳׳׳•׳›׳׳" ׳•׳—׳•׳¡׳ pull (׳¨׳׳”
# docstring, 16/09/2026). market_pe_base.json / sector_mapping.json
# ׳•׳›׳•' ׳¢׳“׳™׳™׳ ׳׳ ׳›׳׳ - ׳׳׳” ׳׳×׳¢׳“׳›׳ ׳™׳ ׳‘׳×׳”׳׳™׳›׳™׳ ׳ ׳₪׳¨׳“׳™׳ ׳׳©׳׳”׳.
FILES_TO_PUSH = [
    "ytm_computed.xlsx",
    "docs/ytm_dashboard.html",
    "run_log.txt",
    "bizportal_banks_index.json",
    "weekly_cpi_israel.json",
    "holdings.xlsx",
]

# ׳׳¡׳˜׳¨׳˜׳’׳™׳™׳× ׳׳™׳–׳•׳’ ׳׳›׳ ׳§׳•׳‘׳¥: "ours" = ׳‘׳”׳×׳ ׳’׳©׳•׳×, ׳”׳’׳¨׳¡׳” ׳׳”׳¨׳™׳¦׳” ׳”׳׳§׳•׳׳™׳×
# ׳”׳–׳• ׳×׳׳™׳“ ׳׳ ׳¦׳—׳× - ׳ ׳›׳•׳ ׳׳§׳‘׳¦׳™׳ ׳©׳ ׳•׳¦׳¨׳™׳ ׳׳—׳“׳© ׳›׳ ׳¨׳™׳¦׳” (ytm_computed.xlsx,
# ׳”׳“׳©׳‘׳•׳¨׳“), ׳•׳’׳ ׳-holdings.xlsx: ׳׳׳¨׳•׳× ׳©׳—׳ ׳¢׳•׳¨׳ ׳׳•׳×׳• ׳׳׳¡׳₪׳¨ ׳׳—׳©׳‘׳™׳
# (׳¨׳׳” sync_holdings_from_onedrive), ׳׳™ ׳©׳‘׳׳׳× ׳׳‘׳¦׳¢ git commit ׳׳§׳•׳‘׳¥
# ׳”׳–׳” ׳–׳” ׳×׳׳™׳“ chensurfacepro7 ׳‘׳׳‘׳“, ׳׳—׳¨׳™ ׳©׳›׳‘׳¨ ׳¡׳™׳ ׳›׳¨׳ ׳׳¢׳¦׳׳• ׳׳× ׳”׳’׳¨׳¡׳”
# ׳”׳¢׳“׳›׳ ׳™׳× ׳‘׳™׳•׳×׳¨ ׳-OneDrive - ׳›׳ ׳©׳’׳ ׳›׳׳, ׳׳‘׳—׳™׳ ׳× git, ׳™׳© ׳‘׳₪׳•׳¢׳ "׳¦׳“"
# ׳™׳—׳™׳“ ׳©׳׳‘׳¦׳¢ ׳׳× ׳”-commit, ׳•׳”׳’׳¨׳¡׳” ׳”׳׳—׳¨׳•׳ ׳” ׳©׳ ׳©׳׳¨׳” ׳”׳™׳ ׳×׳׳™׳“ ׳”׳ ׳›׳•׳ ׳”.
# run_log.txt ׳׳§׳‘׳ "union" (׳׳׳—׳“ ׳©׳•׳¨׳•׳×, ׳׳ ׳‘׳•׳—׳¨ ׳¦׳“) ׳›׳™ ׳”׳•׳ ׳§׳•׳‘׳¥ ׳©׳¨׳§
# ׳׳×׳•׳•׳¡׳£ ׳׳׳™׳• ׳׳©׳ ׳™ ׳”׳׳§׳•׳¨׳•׳× (׳”׳׳—׳©׳‘ ׳”׳׳§׳•׳׳™ ׳•׳”-workflow ׳‘׳¢׳ ׳).
GITATTRIBUTES_LINES = [
    "ytm_computed.xlsx merge=ours",
    "docs/ytm_dashboard.html merge=ours",
    "run_log.txt merge=union",
    "holdings.xlsx merge=ours",
]

# ׳’׳™׳‘׳•׳™ ׳ ׳•׳¡׳£ (׳׳ git) ׳׳×׳™׳§׳™׳™׳× OneDrive ׳©׳›׳‘׳¨ ׳׳¡׳•׳ ׳›׳¨׳ ׳× ׳‘׳׳—׳©׳‘ ׳”׳–׳” - ׳׳
# ׳×׳—׳׳™׳£ ׳-GitHub (׳©׳”׳•׳ ׳”-source of truth ׳•׳׳׳©׳™׳ ׳׳”׳™׳•׳× ׳׳ ׳’׳ ׳•׳ ׳”-push
# ׳”׳¢׳™׳§׳¨׳™), ׳׳׳ ׳¨׳©׳× ׳‘׳™׳˜׳—׳•׳ ׳¢׳¦׳׳׳™׳× ׳©׳׳ ׳×׳׳•׳™׳” ׳‘׳’׳™׳˜ ׳‘׳›׳׳. .git ׳¢׳¦׳׳• ׳׳
# ׳׳’׳•׳‘׳” ׳›׳׳ (׳”׳•׳ ׳›׳‘׳¨ ׳׳’׳•׳‘׳” ׳“׳¨׳ GitHub, ׳•׳¡׳ ׳›׳¨׳•׳ OneDrive ׳¢׳ ׳×׳™׳§׳™׳™׳×
# .git ׳₪׳¢׳™׳׳” ׳¢׳׳•׳ ׳׳”׳×׳ ׳’׳© ׳¢׳ ׳›׳×׳™׳‘׳•׳× git ׳•׳׳’׳¨׳•׳ ׳׳©׳—׳™׳×׳•׳×).
ONEDRIVE_BACKUP_DIR = pathlib.Path(r"C:\Users\micha\OneDrive\tase-ytm-dashboard-backup")
ONEDRIVE_BACKUP_EXCLUDE_DIRS = [".git", "__pycache__", "downloads"]

# ׳¢׳•׳×׳§ ׳”-holdings.xlsx ׳‘׳×׳™׳§׳™׳™׳× ׳”׳’׳™׳‘׳•׳™ ׳‘-OneDrive - ׳׳׳– 01/11/2026 ׳”׳•׳
# ׳׳ ׳¨׳§ ׳™׳¢׳“ ׳’׳™׳‘׳•׳™ ׳׳׳ ׳’׳ ׳׳§׳•׳¨ ׳§׳׳˜ ׳׳₪׳©׳¨׳™: ׳—׳ ׳¢׳•׳¨׳ ׳׳× ׳”׳§׳•׳‘׳¥ ׳׳׳¡׳₪׳¨
# ׳׳—׳©׳‘׳™׳ ׳©׳׳—׳•׳‘׳¨׳™׳ ׳׳׳•׳×׳• ׳—׳©׳‘׳•׳ OneDrive, ׳•׳׳ ׳¨׳§ ׳-chensurfacepro7
# (׳¨׳׳” sync_holdings_from_onedrive).
ONEDRIVE_HOLDINGS_PATH = ONEDRIVE_BACKUP_DIR / "holdings.xlsx"


def log_wrapper_event(text: str) -> None:
    """׳›׳•׳×׳‘ ׳©׳•׳¨׳× ׳׳‘׳—׳•׳ ׳׳§׳•׳‘׳¥ ׳™׳™׳¢׳•׳“׳™ - ׳›׳“׳™ ׳©׳›׳©׳ (׳׳• ׳₪׳¨׳˜׳™ ׳“׳™׳‘׳•׳’) ׳׳
    ׳™׳™׳¢׳׳׳• ׳‘׳©׳§׳˜ ׳‘׳¨׳™׳¦׳” ׳׳×׳•׳–׳׳ ׳× ׳©׳׳£ ׳׳—׳“ ׳׳ ׳¦׳•׳₪׳” ׳‘׳”."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(WRAPPER_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {text}\n")
    except Exception:
        pass


def log_wrapper_failure(exc: BaseException) -> None:
    log_wrapper_event("run_daily_local.py ׳ ׳›׳©׳:\n" + traceback.format_exc())


def run_git(args, check=False):
    """׳׳¨׳™׳¥ ׳₪׳§׳•׳“׳× git, ׳׳•׳›׳“ stdout/stderr (׳›׳“׳™ ׳©׳™׳”׳™׳” ׳׳” ׳׳׳‘׳—׳ ׳׳
    ׳–׳” ׳ ׳›׳©׳), ׳•׳׳—׳–׳™׳¨ ׳׳× ׳”-CompletedProcess."""
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
            f"git {' '.join(args)} -> ׳§׳•׳“ ׳™׳¦׳™׳׳” {result.returncode}\n"
            f"--- stdout ---\n{result.stdout}\n--- stderr ---\n{result.stderr}"
        )
    if check and result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} ׳ ׳›׳©׳ (׳§׳•׳“ ׳™׳¦׳™׳׳” {result.returncode})")
    return result


def step(msg):
    print(f"\n=== {msg} ===")


def check_uncommitted_tracked_changes() -> None:
    """׳‘׳•׳“׳§ ׳׳ ׳™׳© ׳©׳™׳ ׳•׳™׳™׳ ׳׳-׳׳—׳•׳™׳‘׳™׳ (uncommitted) ׳‘׳§׳‘׳¦׳™׳ ׳©׳›׳‘׳¨ ׳‘׳׳¢׳§׳‘
    git, ׳׳׳‘׳“ ׳׳׳” ׳©׳”׳¨׳™׳¦׳” ׳”׳–׳• ׳¢׳¦׳׳” ׳׳׳•׳¨׳” ׳׳©׳ ׳•׳× (FILES_TO_PUSH - ׳׳׳–
    28/10/2026 ׳›׳•׳׳ ׳’׳ ׳׳× holdings.xlsx). ׳–׳” ׳‘׳“׳™׳•׳§ ׳׳” ׳©׳’׳¨׳ ׳‘׳¢׳‘׳¨
    (16/09/2026, ׳׳₪׳ ׳™ ׳©-holdings.xlsx ׳”׳¦׳˜׳¨׳£ ׳-FILES_TO_PUSH) ׳׳›׳׳”
    ׳›׳©׳׳•׳ ׳•׳× ׳¨׳¦׳•׳₪׳™׳ ׳‘׳׳•׳×׳• ׳™׳•׳ ׳›׳™ git pull --ff-only ׳ ׳›׳©׳ ׳¢׳ "Your
    local changes... would be overwritten by merge". ׳¢׳“׳™׳™׳ ׳¨׳׳•׳•׳ ׳˜׳™
    ׳׳›׳ ׳§׳•׳‘׳¥ ׳׳—׳¨ ׳©׳‘׳׳¢׳§׳‘ git ׳•׳ ׳¢׳¨׳ ׳™׳“׳ ׳™׳× ׳׳—׳•׳¥ ׳׳×׳”׳׳™׳ ׳”׳–׳”. ׳׳ ׳¢׳•׳¦׳¨ ׳׳×
    ׳”׳¨׳™׳¦׳” (׳™׳›׳•׳ ׳׳”׳™׳•׳× ׳’׳ ׳©׳™׳ ׳•׳™ ׳׳’׳™׳˜׳™׳׳™ ׳©׳¢׳“׳™׳™׳ ׳׳ ׳”׳’׳™׳¢ ׳–׳׳ ׳•) - ׳¨׳§
    ׳׳×׳¨׳™׳¢ ׳׳¨׳׳© ׳‘׳׳•׳’, ׳›׳“׳™ ׳©׳”׳׳‘׳—׳•׳ ׳™׳”׳™׳” ׳׳™׳™׳“׳™ ׳׳ ׳”-pull/push ׳‘׳”׳׳©׳
    ׳”׳¨׳™׳¦׳” ׳”׳–׳• ׳™׳™׳›׳©׳, ׳‘׳׳§׳•׳ ׳׳”׳×׳—׳™׳ ׳׳”׳•׳“׳¢׳× git ׳”׳׳¢׳•׳¨׳₪׳׳×."""
    result = run_git(["status", "--porcelain"])
    if result.returncode != 0:
        return

    files_to_push_normalized = {f.replace("\\", "/") for f in FILES_TO_PUSH}
    dirty_files = []
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        status_code, filename = line[:2], line[3:].strip()
        if status_code.strip() == "??":  # ׳§׳•׳‘׳¥ ׳׳-׳‘׳׳¢׳§׳‘ ׳‘׳›׳׳ - ׳׳ ׳¨׳׳•׳•׳ ׳˜׳™ ׳›׳׳
            continue
        if filename.replace("\\", "/") in files_to_push_normalized:
            continue
        dirty_files.append(filename)

    if not dirty_files:
        return

    files_list = ", ".join(dirty_files)
    log_wrapper_event(
        "ג ן¸  ׳ ׳׳¦׳׳• ׳©׳™׳ ׳•׳™׳™׳ ׳׳-׳׳—׳•׳™׳‘׳™׳ (uncommitted) ׳‘׳§׳‘׳¦׳™׳ ׳”׳‘׳׳™׳ ׳©׳›׳‘׳¨ ׳‘׳׳¢׳§׳‘ git, "
        f"׳׳₪׳ ׳™ ׳×׳—׳™׳׳× ׳”׳¨׳™׳¦׳”: {files_list} - ׳׳ ׳”-pull/push ׳‘׳”׳׳©׳ ׳”׳¨׳™׳¦׳” ׳”׳–׳• ׳™׳™׳›׳©׳, "
        "׳–׳• ׳›׳ ׳¨׳׳” ׳”׳¡׳™׳‘׳” (׳‘׳“׳™׳•׳§ ׳›׳׳• ׳©׳§׳¨׳” ׳¢׳ holdings.xlsx ׳׳₪׳ ׳™ ׳©׳”׳¦׳˜׳¨׳£ ׳-FILES_TO_PUSH, 16/09/2026). "
        "׳׳×׳™׳§׳•׳: ׳‘׳¦׳¢׳™ commit+push ׳™׳“׳ ׳™ ׳׳§׳•׳‘׳¥, ׳׳• commit/stash, ׳׳₪׳ ׳™ ׳©׳”׳¨׳™׳¦׳” ׳”׳‘׳׳” ׳׳×׳•׳–׳׳ ׳×."
    )
    print(f"ג ן¸  ׳©׳™׳ ׳•׳™׳™׳ ׳׳-׳׳—׳•׳™׳‘׳™׳ ׳‘׳§׳‘׳¦׳™׳ ׳©׳‘׳׳¢׳§׳‘ git (׳¨׳׳• run_daily_local_log.txt): {files_list}")


def ensure_git_merge_config():
    """׳—׳“-׳₪׳¢׳׳™ ׳•׳׳™׳“׳׳₪׳•׳˜׳ ׳˜׳™: ׳¨׳•׳©׳ ׳׳× ׳”-driver 'ours' ׳‘׳”׳’׳“׳¨׳•׳× git
    ׳”׳׳§׳•׳׳™׳•׳× (׳׳ ׳ ׳™׳×׳ ׳׳”׳’׳“׳™׳¨ ׳׳× ׳–׳” ׳¨׳§ ׳“׳¨׳ .gitattributes), ׳•׳׳•׳•׳“׳
    ׳©׳”׳§׳•׳‘׳¥ .gitattributes ׳¢׳¦׳׳• ׳§׳™׳™׳ ׳•׳‘-git ׳¢׳ ׳”׳©׳•׳¨׳•׳× ׳”׳ ׳“׳¨׳©׳•׳×. ׳׳ ׳”׳™׳”
    ׳¦׳¨׳™׳ ׳׳™׳¦׳•׳¨/׳׳¢׳“׳›׳ ׳׳•׳×׳• - ׳¢׳•׳©׳” ׳׳›׳ commit+push ׳§׳˜׳ ׳•׳ ׳₪׳¨׳“."""
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
            log_wrapper_event("push ׳©׳ .gitattributes ׳ ׳›׳©׳ - ׳™׳ ׳¡׳” ׳©׳•׳‘ ׳‘׳¨׳™׳¦׳” ׳”׳‘׳׳” (׳׳ ׳§׳¨׳™׳˜׳™).")


def pull_latest_before_run():
    """׳׳•׳©׳ ׳-GitHub ׳׳₪׳ ׳™ ׳©׳׳×׳—׳™׳׳™׳ - ׳›׳“׳™ ׳׳¦׳׳¦׳ (׳׳ ׳׳—׳¡׳ ׳׳’׳׳¨׳™, ׳™׳©
    ׳¢׳“׳™׳™׳ ׳—׳׳•׳ ׳–׳׳) ׳׳× ׳”׳¡׳™׳›׳•׳™ ׳׳”׳×׳ ׳’׳©׳•׳× ׳‘׳¡׳•׳£ ׳”׳¨׳™׳¦׳”. ׳׳ ׳§׳¨׳™׳˜׳™ ׳׳ ׳–׳”
    ׳ ׳›׳©׳ (׳׳׳©׳ ׳׳™׳ ׳¨׳©׳× ׳¨׳’׳¢׳™׳×) - ׳׳׳©׳™׳›׳™׳ ׳‘׳›׳ ׳׳§׳¨׳”."""
    result = run_git(["pull", "--ff-only"])
    if result.returncode != 0:
        print("ג ן¸  git pull ׳‘׳×׳—׳™׳׳× ׳”׳¨׳™׳¦׳” ׳׳ ׳”׳¦׳׳™׳— (׳׳׳©׳™׳›׳™׳ ׳‘׳›׳ ׳–׳׳×).")


def run_daily_update():
    # capture_output=True: ׳‘׳׳¢׳“׳™׳•, ׳׳ run_daily_update.py ׳§׳•׳¨׳¡ ׳¢׳•׳“ ׳׳₪׳ ׳™
    # ׳©׳”׳•׳ ׳׳¦׳׳™׳— ׳׳₪׳×׳•׳— ׳׳× run_log.txt (׳׳׳©׳ PermissionError ׳—׳“-׳₪׳¢׳׳™ -
    # ׳§׳¨׳” ׳‘׳₪׳•׳¢׳ ׳‘-07/09/2026), ׳”-traceback ׳”׳׳׳™׳×׳™ ׳”׳•׳׳ ׳-stderr ׳©׳
    # ׳×׳”׳׳™׳ ׳©׳¨׳¥ ׳‘׳׳™ ׳—׳׳•׳ ׳§׳•׳ ׳¡׳•׳׳” (Task Scheduler) - ׳›׳׳•׳׳¨ ׳ ׳¢׳׳ ׳׳’׳׳¨׳™,
    # ׳•׳ ׳©׳׳¨׳× ׳¨׳§ ׳”׳•׳“׳¢׳× "׳§׳•׳“ ׳™׳¦׳™׳׳” 1" ׳”׳’׳ ׳¨׳™׳× ׳‘׳׳™ ׳©׳•׳ ׳׳™׳“׳¢ ׳׳׳‘׳—׳•׳.
    # PYTHONIOENCODING: ׳”׳’׳ ׳” ׳›׳₪׳•׳׳” ׳‘׳ ׳•׳¡׳£ ׳-sys.stdout.reconfigure() ׳©׳›׳‘׳¨
    # ׳§׳™׳™׳ ׳‘׳×׳•׳ run_daily_update.py ׳¢׳¦׳׳• - ׳§׳•׳‘׳¢׳× ׳׳× ׳§׳™׳“׳•׳“ ׳‘׳¨׳™׳¨׳× ׳”׳׳—׳“׳
    # ׳©׳ ׳”-stdout/stderr ׳©׳ ׳”׳×׳”׳׳™׳ ׳”׳‘׳ ׳¢׳•׳“ ׳׳₪׳ ׳™ ׳©׳”׳•׳ ׳‘׳›׳׳ ׳׳×׳—׳™׳ ׳׳¨׳•׳¥.
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
            f"run_daily_update.py ׳ ׳›׳©׳ (׳§׳•׳“ ׳™׳¦׳™׳׳” {result.returncode})\n"
            f"--- stdout ---\n{result.stdout}\n--- stderr ---\n{result.stderr}"
        )
        raise RuntimeError(f"run_daily_update.py ׳ ׳›׳©׳ (׳§׳•׳“ ׳™׳¦׳™׳׳” {result.returncode})")


def git_commit_and_push() -> bool:
    run_git(["add"] + FILES_TO_PUSH, check=True)

    diff = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=str(_REPO_DIR))
    if diff.returncode == 0:
        print("׳׳™׳ ׳©׳™׳ ׳•׳™ ׳׳¢׳•׳׳× ׳׳” ׳©׳›׳‘׳¨ ׳‘-GitHub.")
        return False

    run_git(["commit", "-m", "Daily local update (bizportal/BOI blocked from GitHub)"], check=True)
    our_commit = run_git(["rev-parse", "HEAD"], check=True).stdout.strip()

    push = run_git(["push"])
    if push.returncode == 0:
        print("ג… ׳ ׳“׳—׳£ ׳-GitHub ׳‘׳”׳¦׳׳—׳”.")
        return True

    print(
        "ג ן¸  git push ׳ ׳›׳©׳ - ׳›׳ ׳¨׳׳” ׳©׳”-workflow ׳‘׳¢׳ ׳ ׳“׳—׳£ ׳‘׳׳•׳×׳• ׳–׳׳ ׳©׳™׳ ׳•׳™ ׳׳׳•׳×׳ ׳§׳‘׳¦׳™׳ "
        "(ytm_computed.xlsx / ׳”׳“׳©׳‘׳•׳¨׳“). ׳׳ ׳¡׳” ׳׳׳—׳“ ׳׳•׳˜׳•׳׳˜׳™׳× ׳¢׳ ׳”׳’׳¨׳¡׳” ׳׳”׳¨׳™׳¦׳” ׳”׳–׳•..."
    )

    run_git(["fetch", "origin"], check=True)
    merge = run_git(["merge", "--no-edit", f"origin/{GIT_BRANCH}"])
    if merge.returncode != 0:
        run_git(["merge", "--abort"])
        raise RuntimeError("git merge ׳ ׳›׳©׳ - ׳ ׳“׳¨׳©׳× ׳‘׳“׳™׳§׳” ׳™׳“׳ ׳™׳× (git status ׳‘׳׳—׳©׳‘)")

    # ׳‘׳™׳˜׳—׳•׳ ׳›׳₪׳•׳: ׳׳ ׳¡׳•׳׳›׳™׳ ׳¨׳§ ׳¢׳ .gitattributes/merge=ours - ׳‘׳•׳“׳§׳™׳
    # ׳‘׳₪׳•׳¢׳ ׳©׳”׳§׳‘׳¦׳™׳ ׳”׳׳™׳•׳¦׳¨׳™׳ ׳׳•׳˜׳•׳׳˜׳™׳× ׳¢׳“׳™׳™׳ ׳×׳•׳׳׳™׳ ׳׳׳” ׳©׳”׳¨׳™׳¦׳” ׳”׳–׳•
    # ׳™׳¦׳¨׳”, ׳•׳׳ ׳”׳׳™׳–׳•׳’ ׳‘׳›׳ ׳–׳׳× "׳‘׳—׳¨" ׳‘׳˜׳¢׳•׳× ׳‘׳’׳¨׳¡׳” ׳׳”׳¢׳ ׳ - ׳›׳•׳₪׳™׳ ׳׳×
    # ׳”׳’׳¨׳¡׳” ׳”׳׳§׳•׳׳™׳× ׳•׳׳•׳¡׳™׳₪׳™׳ commit ׳׳×׳§׳.
    run_git(["checkout", our_commit, "--"] + FILES_TO_PUSH, check=True)
    run_git(["add"] + FILES_TO_PUSH, check=True)
    fixup_diff = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=str(_REPO_DIR))
    if fixup_diff.returncode != 0:
        run_git(["commit", "-m", "Ensure local run's generated files win after merge"], check=True)
        log_wrapper_event("׳”׳׳™׳–׳•׳’ ׳”׳׳•׳˜׳•׳׳˜׳™ ׳׳ ׳©׳׳¨ ׳¢׳ ׳”׳’׳¨׳¡׳” ׳”׳׳§׳•׳׳™׳× - ׳×׳•׳§׳ ׳¢׳ commit ׳ ׳•׳¡׳£.")

    push2 = run_git(["push"])
    if push2.returncode != 0:
        raise RuntimeError("git push ׳ ׳›׳©׳ ׳’׳ ׳׳—׳¨׳™ merge ׳׳•׳˜׳•׳׳˜׳™ - ׳ ׳“׳¨׳©׳× ׳‘׳“׳™׳§׳” ׳™׳“׳ ׳™׳×")

    print("ג… ׳ ׳“׳—׳£ ׳-GitHub ׳‘׳”׳¦׳׳—׳” (׳׳—׳¨׳™ ׳׳™׳—׳•׳“ ׳׳•׳˜׳•׳׳˜׳™ ׳¢׳ ׳”׳©׳™׳ ׳•׳™ ׳©׳”׳™׳” ׳‘׳¢׳ ׳).")
    return True


def fetch_banks_index_override() -> None:
    """׳©׳•׳׳£ ׳׳× ׳”׳©׳™׳ ׳•׳™ ׳”׳©׳‘׳•׳¢׳™ ׳©׳ ׳׳“׳“ ׳×"׳ ׳‘׳ ׳§׳™׳ ׳׳‘׳™׳–׳₪׳•׳¨׳˜׳ (׳¢׳•׳‘׳“ ׳¨׳§
    ׳׳”׳׳—׳©׳‘ ׳”׳׳§׳•׳׳™ - ׳—׳¡׳•׳ ׳-GitHub Actions) ׳•׳›׳•׳×׳‘ ׳׳•׳×׳• ׳-
    bizportal_banks_index.json. ׳׳ ׳§׳¨׳™׳˜׳™: ׳›׳©׳ ׳›׳׳ ׳¨׳§ ׳ ׳¨׳©׳ ׳׳™׳•׳׳,
    ׳•׳׳ ׳”׳§׳•׳‘׳¥ ׳›׳‘׳¨ ׳§׳™׳™׳ ׳׳¨׳™׳¦׳” ׳§׳•׳“׳׳× ׳”׳•׳ ׳₪׳©׳•׳˜ ׳ ׳©׳׳¨ ׳›׳׳• ׳©׳”׳•׳."""
    pct, err = fetch_pe.fetch_index_weekly_change(BIZPORTAL_BANKS_INDEX_ID)
    if err:
        log_wrapper_event(f"ג ן¸  ׳©׳׳™׳₪׳× ׳׳“׳“ ׳×\"׳ ׳‘׳ ׳§׳™׳ ׳׳‘׳™׳–׳₪׳•׳¨׳˜׳ ׳ ׳›׳©׳׳”: {err}")
        return
    data = {
        "pct": pct,
        "as_of": datetime.date.today().isoformat(),
        "source": f"bizportal index {BIZPORTAL_BANKS_INDEX_ID}",
    }
    with open(BANKS_INDEX_OVERRIDE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"ג… ׳׳“׳“ ׳×\"׳ ׳‘׳ ׳§׳™׳ (׳‘׳™׳–׳₪׳•׳¨׳˜׳): {pct * 100:+.2f}% ׳©׳‘׳•׳¢׳™.")


def update_weekly_cpi_israel() -> None:
    """׳©׳•׳׳£ ׳׳”׳׳"׳¡ (׳¢׳•׳‘׳“ ׳¨׳§ ׳׳”׳׳—׳©׳‘ ׳”׳׳§׳•׳׳™ - ׳—׳¡׳•׳ ׳-GitHub Actions) ׳׳×
    ׳”׳©׳™׳ ׳•׳™ ׳”׳—׳•׳“׳©׳™/׳©׳ ׳×׳™ ׳”׳¢׳“׳›׳ ׳™ ׳©׳ ׳׳“׳“ ׳”׳׳—׳™׳¨׳™׳ ׳׳¦׳¨׳›׳, ׳•׳›׳•׳×׳‘ ׳׳•׳×׳• ׳-
    weekly_cpi_israel.json - ׳¢׳“ ׳¢׳›׳©׳™׳• ׳”׳§׳•׳‘׳¥ ׳”׳–׳” ׳¢׳•׳“׳›׳ ׳¨׳§ ׳™׳“׳ ׳™׳× ׳•׳ ׳©׳׳¨
    ׳×׳§׳•׳¢ ׳¢׳ ׳ ׳×׳•׳ ׳™ ׳”׳“׳•׳’׳׳” ׳”׳׳§׳•׳¨׳™׳™׳. ׳׳ ׳§׳¨׳™׳˜׳™: ׳›׳©׳ ׳›׳׳ ׳¨׳§ ׳ ׳¨׳©׳ ׳׳™׳•׳׳,
    ׳•׳׳ ׳”׳§׳•׳‘׳¥ ׳›׳‘׳¨ ׳§׳™׳™׳ ׳׳¨׳™׳¦׳” ׳§׳•׳“׳׳× ׳”׳•׳ ׳₪׳©׳•׳˜ ׳ ׳©׳׳¨ ׳›׳׳• ׳©׳”׳•׳."""
    result, err = fetch_cpi_israel.fetch_and_summarize()
    if err:
        log_wrapper_event(f"ג ן¸  ׳¢׳“׳›׳•׳ ׳׳“׳“ ׳”׳׳—׳™׳¨׳™׳ ׳׳¦׳¨׳›׳ (׳׳\"׳¡) ׳ ׳›׳©׳: {err}")
        return
    with open(WEEKLY_CPI_ISRAEL_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"ג… ׳׳“׳“ ׳”׳׳—׳™׳¨׳™׳ ׳׳¦׳¨׳›׳ (׳׳\"׳¡): {result['value']} - {result['note']}")


def sync_holdings_from_onedrive() -> None:
    """׳׳׳₪׳©׳¨׳× ׳׳¢׳¨׳•׳ ׳׳× holdings.xlsx ׳׳׳¡׳₪׳¨ ׳׳—׳©׳‘׳™׳: ׳׳ ׳”׳¢׳•׳×׳§ ׳‘׳×׳™׳§׳™׳™׳×
    ׳”׳’׳™׳‘׳•׳™ ׳‘-OneDrive (׳©׳׳¡׳×׳ ׳›׳¨׳ ׳× ׳׳•׳˜׳•׳׳˜׳™׳× ׳‘׳™׳ ׳›׳ ׳”׳׳—׳©׳‘׳™׳ ׳”׳׳—׳•׳‘׳¨׳™׳
    ׳׳׳•׳×׳• ׳—׳©׳‘׳•׳ OneDrive) ׳—׳“׳© ׳™׳•׳×׳¨ ׳׳”׳¢׳•׳×׳§ ׳”׳׳§׳•׳׳™ ׳›׳׳ ׳‘׳×׳™׳§׳™׳™׳×
    ׳”׳₪׳¨׳•׳™׳§׳˜ - ׳׳¢׳×׳™׳§׳™׳ ׳׳•׳×׳• ׳׳›׳׳, ׳›׳“׳™ ׳©׳”׳¨׳™׳¦׳” ׳”׳–׳• (׳•׳“׳—׳™׳₪׳× holdings.xlsx
    ׳-GitHub ׳©׳‘׳”׳׳©׳›׳”, ׳“׳¨׳ FILES_TO_PUSH) ׳×׳×׳‘׳¡׳¡ ׳¢׳ ׳”׳¢׳“׳›׳•׳ ׳©׳ ׳¢׳¨׳
    ׳‘׳׳—׳©׳‘ ׳”׳׳—׳¨. ׳׳ ׳”׳¢׳•׳×׳§ ׳”׳׳§׳•׳׳™ ׳—׳“׳© ׳™׳•׳×׳¨ ׳׳• ׳–׳”׳” (׳׳׳©׳ ׳ ׳¢׳¨׳ ׳›׳׳
    ׳™׳©׳™׳¨׳•׳×, ׳׳• ׳‘-update_holdings.bat) - ׳׳ ׳ ׳•׳’׳¢׳™׳ ׳‘׳•; ׳”׳•׳ ׳׳׳™׳׳
    ׳™׳¡׳•׳ ׳›׳¨׳ ׳‘׳—׳–׳¨׳” ׳-OneDrive ׳‘׳¡׳•׳£ ׳”׳¨׳™׳¦׳” ׳¢"׳™ backup_to_onedrive(),
    ׳›׳ ׳©׳׳™׳ ׳¦׳•׳¨׳ "׳׳“׳—׳•׳£" ׳’׳ ׳‘׳›׳™׳•׳•׳ ׳”׳–׳” ׳›׳׳. ׳¡׳£ ׳©׳ 5 ׳©׳ ׳™׳•׳× ׳‘׳”׳©׳•׳•׳׳×
    ׳”׳–׳׳ ׳™׳ - ׳›׳“׳™ ׳׳ "׳׳§׳₪׳•׳¥" ׳‘׳’׳׳ ׳¨׳¢׳© ׳§׳˜׳ ׳‘׳–׳׳ ׳™ ׳§׳‘׳¦׳™׳ ׳‘׳™׳ ׳©׳™׳¨׳•׳×׳™
    ׳¡׳ ׳›׳¨׳•׳/׳“׳™׳¡׳§׳™׳ ׳©׳•׳ ׳™׳. ׳׳ ׳§׳¨׳™׳˜׳™: ׳›׳©׳ ׳׳• ׳”׳¢׳“׳¨ ׳×׳™׳§׳™׳™׳×/׳§׳•׳‘׳¥ OneDrive
    ׳¨׳§ ׳ ׳¨׳©׳׳™׳ ׳׳™׳•׳׳ ׳•׳׳ ׳׳₪׳™׳׳™׳ ׳׳× ׳©׳׳¨ ׳”׳¨׳™׳¦׳” - ׳׳׳©׳™׳›׳™׳ ׳₪׳©׳•׳˜ ׳¢׳
    ׳”׳¢׳•׳×׳§ ׳”׳׳§׳•׳׳™ ׳”׳§׳™׳™׳."""
    if not ONEDRIVE_BACKUP_DIR.exists():
        log_wrapper_event(
            f"ג ן¸  ׳×׳™׳§׳™׳™׳× ׳”-OneDrive {ONEDRIVE_BACKUP_DIR} ׳׳ ׳ ׳׳¦׳׳” - ׳׳“׳׳’ ׳¢׳ ׳¡׳ ׳›׳¨׳•׳ holdings.xlsx ׳׳׳ ׳”."
        )
        return
    if not ONEDRIVE_HOLDINGS_PATH.exists():
        return  # ׳׳™׳ ׳©׳ ׳¢׳“׳™׳™׳ ׳¢׳•׳×׳§ (׳׳׳©׳ ׳׳₪׳ ׳™ ׳”׳¨׳™׳¦׳” ׳”׳¨׳׳©׳•׳ ׳” ׳׳—׳¨׳™ ׳”׳₪׳¢׳׳× ׳”׳₪׳™׳¦'׳¨) - ׳׳ ׳—׳¨׳™׳’.

    if not HOLDINGS_XLSX_PATH.exists():
        shutil.copy2(ONEDRIVE_HOLDINGS_PATH, HOLDINGS_XLSX_PATH)
        print("ג… holdings.xlsx ׳׳ ׳”׳™׳” ׳§׳™׳™׳ ׳׳§׳•׳׳™׳× - ׳”׳•׳¢׳×׳§ ׳-OneDrive.")
        log_wrapper_event("holdings.xlsx ׳”׳•׳¢׳×׳§ ׳-OneDrive (׳׳ ׳”׳™׳” ׳§׳™׳™׳ ׳׳§׳•׳׳™׳×).")
        return

    onedrive_mtime = ONEDRIVE_HOLDINGS_PATH.stat().st_mtime
    local_mtime = HOLDINGS_XLSX_PATH.stat().st_mtime
    if onedrive_mtime > local_mtime + 5:
        shutil.copy2(ONEDRIVE_HOLDINGS_PATH, HOLDINGS_XLSX_PATH)
        print("ג… holdings.xlsx ׳¢׳•׳“׳›׳ ׳׳׳—׳©׳‘ ׳׳—׳¨ (OneDrive) - ׳”׳•׳¢׳×׳§ ׳׳›׳׳ ׳׳₪׳ ׳™ ׳”׳¨׳™׳¦׳”.")
        log_wrapper_event("holdings.xlsx ׳¡׳•׳ ׳›׳¨׳ ׳-OneDrive (׳”׳¢׳•׳×׳§ ׳©׳ ׳”׳™׳” ׳—׳“׳© ׳™׳•׳×׳¨ ׳׳”׳׳§׳•׳׳™).")


def backup_to_onedrive() -> None:
    """׳׳¨׳׳” (mirror) ׳׳× ׳›׳ ׳×׳™׳§׳™׳™׳× ׳”׳₪׳¨׳•׳™׳§׳˜ ׳׳×׳™׳§׳™׳™׳× ׳”׳’׳™׳‘׳•׳™ ׳‘-OneDrive,
    ׳—׳•׳¥ ׳-.git/__pycache__/downloads. ׳׳ ׳§׳¨׳™׳˜׳™: ׳›׳©׳ ׳›׳׳ ׳¨׳§ ׳ ׳¨׳©׳ ׳׳™׳•׳׳
    ׳•׳׳ ׳׳₪׳™׳ ׳׳× ׳©׳׳¨ ׳”׳¨׳™׳¦׳” - ׳–׳” ׳©׳›׳‘׳× ׳’׳™׳‘׳•׳™ ׳ ׳•׳¡׳₪׳×, ׳׳ ׳”׳₪׳™׳™׳₪׳׳™׳™׳ ׳”׳¢׳™׳§׳¨׳™."""
    if not ONEDRIVE_BACKUP_DIR.exists():
        log_wrapper_event(
            f"ג ן¸  ׳×׳™׳§׳™׳™׳× ׳”׳’׳™׳‘׳•׳™ {ONEDRIVE_BACKUP_DIR} ׳׳ ׳ ׳׳¦׳׳” - ׳׳“׳׳’ ׳¢׳ ׳’׳™׳‘׳•׳™ ׳”-OneDrive."
        )
        return

    args = ["robocopy", str(_REPO_DIR), str(ONEDRIVE_BACKUP_DIR), "/MIR"]
    for d in ONEDRIVE_BACKUP_EXCLUDE_DIRS:
        args += ["/XD", str(_REPO_DIR / d)]
    args += ["/R:1", "/W:1", "/NFL", "/NDL", "/NP"]

    result = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace")
    # robocopy: 0-7 = ׳”׳¦׳׳—׳” (׳¡׳•׳’׳™ ׳©׳™׳ ׳•׳™ ׳©׳•׳ ׳™׳), 8+ = ׳›׳©׳ ׳׳׳™׳×׳™.
    if result.returncode >= 8:
        log_wrapper_event(
            f"ג ן¸  ׳’׳™׳‘׳•׳™ ׳-OneDrive ׳ ׳›׳©׳ (robocopy ׳§׳•׳“ ׳™׳¦׳™׳׳” {result.returncode})\n"
            f"--- stdout ---\n{result.stdout}\n--- stderr ---\n{result.stderr}"
        )
    else:
        print(f"ג… ׳’׳•׳‘׳” ׳-OneDrive ׳‘׳”׳¦׳׳—׳” (robocopy ׳§׳•׳“ ׳™׳¦׳™׳׳” {result.returncode}).")


def main():
    ensure_git_merge_config()

    step("׳©׳׳‘ 0/7: ׳‘׳•׳“׳§ ׳©׳™׳ ׳•׳™׳™׳ ׳׳§׳•׳׳™׳™׳ ׳׳-׳׳—׳•׳™׳‘׳™׳ ׳‘׳§׳‘׳¦׳™׳ ׳©׳‘׳׳¢׳§׳‘ git")
    try:
        check_uncommitted_tracked_changes()
    except Exception as exc:
        log_wrapper_event(f"ג ן¸  ׳‘׳“׳™׳§׳× ׳©׳™׳ ׳•׳™׳™׳ ׳׳-׳׳—׳•׳™׳‘׳™׳ ׳ ׳›׳©׳׳” ׳¢׳ ׳—׳¨׳™׳’׳”: {exc}")

    step("׳©׳׳‘ 1/7: ׳׳•׳©׳ ׳¢׳“׳›׳•׳ ׳™׳ ׳׳—׳¨׳•׳ ׳™׳ ׳-GitHub")
    pull_latest_before_run()

    step("׳©׳׳‘ 2/7: ׳׳¡׳ ׳›׳¨׳ ׳׳× holdings.xlsx ׳-OneDrive (׳׳ ׳¢׳•׳“׳›׳ ׳׳׳—׳©׳‘ ׳׳—׳¨)")
    try:
        sync_holdings_from_onedrive()
    except Exception as exc:
        log_wrapper_event(f"ג ן¸  ׳¡׳ ׳›׳¨׳•׳ holdings.xlsx ׳-OneDrive ׳ ׳›׳©׳ ׳¢׳ ׳—׳¨׳™׳’׳”: {exc}")

    step("׳©׳׳‘ 3/7: ׳׳¨׳™׳¥ ׳׳× run_daily_update.py ׳”׳׳§׳•׳׳™")
    run_daily_update()

    step("׳©׳׳‘ 4/7: ׳©׳•׳׳£ ׳׳“׳“ ׳×\"׳ ׳‘׳ ׳§׳™׳ ׳׳‘׳™׳–׳₪׳•׳¨׳˜׳ (׳¢׳‘׳•׳¨ ׳”׳¡׳§׳™׳¨׳” ׳”׳©׳‘׳•׳¢׳™׳×)")
    try:
        fetch_banks_index_override()
    except Exception as exc:
        log_wrapper_event(f"ג ן¸  ׳©׳׳™׳₪׳× ׳׳“׳“ ׳×\"׳ ׳‘׳ ׳§׳™׳ ׳ ׳›׳©׳׳” ׳¢׳ ׳—׳¨׳™׳’׳”: {exc}")

    step("׳©׳׳‘ 5/7: ׳׳¢׳“׳›׳ ׳׳“׳“ ׳”׳׳—׳™׳¨׳™׳ ׳׳¦׳¨׳›׳ ׳׳”׳׳\"׳¡ (׳¢׳‘׳•׳¨ ׳”׳¡׳§׳™׳¨׳” ׳”׳©׳‘׳•׳¢׳™׳×)")
    try:
        update_weekly_cpi_israel()
    except Exception as exc:
        log_wrapper_event(f"ג ן¸  ׳¢׳“׳›׳•׳ ׳׳“׳“ ׳”׳׳—׳™׳¨׳™׳ ׳׳¦׳¨׳›׳ ׳ ׳›׳©׳ ׳¢׳ ׳—׳¨׳™׳’׳”: {exc}")

    step("׳©׳׳‘ 6/7: ׳“׳•׳—׳£ ׳׳× ׳”׳×׳•׳¦׳׳” ׳-GitHub")
    git_commit_and_push()

    step("׳©׳׳‘ 7/7: ׳׳’׳‘׳” ׳-OneDrive")
    try:
        backup_to_onedrive()
    except Exception as exc:
        log_wrapper_event(f"ג ן¸  ׳’׳™׳‘׳•׳™ ׳-OneDrive ׳ ׳›׳©׳ ׳¢׳ ׳—׳¨׳™׳’׳”: {exc}")

    print("\nנ‰ ׳”׳¨׳™׳¦׳” ׳”׳™׳•׳׳™׳× ׳”׳׳§׳•׳׳™׳× ׳”׳•׳©׳׳׳”.")


if __name__ == "__main__":
    try:
        main()
    except BaseException as exc:
        log_wrapper_failure(exc)
        raise

