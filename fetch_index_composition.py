# -*- coding: utf-8 -*-
"""
fetch_index_composition.py
שולף את הרכב מדדי ת"א 35, ת"א 90, ות"א SME60 (הידוע גם כ"ת"א יתר 60")
מביזפורטל - 3 בקשות בלבד (לא בקשה למניה), ושומר מיפוי sec_id -> שם
המדד ל-index_tiers.json.

*** להריץ ידנית, פעם ברבעון בערך (או אחרי עדכון הרכב מדדים רבעוני
    של הבורסה) - לא חלק מהריצה היומית האוטומטית! ***

שימוש:
    python3 fetch_index_composition.py
"""

import json
import re

import requests

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "he-IL,he;q=0.9",
}

# סדר חשוב: אם מניה כלשהי מופיעה (לא אמור לקרות, אבל ליתר ביטחון)
# ביותר ממדד אחד, המדד הגבוה יותר (35 לפני 90 לפני יתר 60) גובר.
TIER_INDICES = [
    ("ת\"א 35", "https://www.bizportal.co.il/capitalmarket/indices/indexcomposition/33343333"),
    ("ת\"א 90", "https://www.bizportal.co.il/capitalmarket/indices/indexcomposition/33363333"),
    ("ת\"א יתר 60", "https://www.bizportal.co.il/capitalmarket/indices/indexcomposition/33403333"),
]

# מדדי ענף רשמיים של הבורסה (לא מדדים תמטיים כמו ESG/דיבידנד) - סדר
# לא משנה, אמורים להיות בלעדיים זה מזה ברובם.
SECTOR_INDICES = [
    ("בנקים", "https://www.bizportal.co.il/capitalmarket/indices/indexcomposition/13"),
    ("ביטוח ושירותים פיננסיים", "https://www.bizportal.co.il/capitalmarket/indices/indexcomposition/527"),
    ("חברות השקעה ואחזקות", "https://www.bizportal.co.il/capitalmarket/indices/indexcomposition/117"),
    ("נדל\"ן ובינוי", "https://www.bizportal.co.il/realestates/indices/indexcomposition/61"),
    ("חברות תעשיה", "https://www.bizportal.co.il/capitalmarket/indices/indexcomposition/73"),
    ("כימיה גומי ופלסטיק", "https://www.bizportal.co.il/capitalmarket/indices/indexcomposition/97"),
    ("מסחר ושירותים", "https://www.bizportal.co.il/capitalmarket/indices/indexcomposition/41"),
    ("חיפושי נפט וגז", "https://www.bizportal.co.il/gazandoil/indices/indexcomposition/127"),
    ("טכנולוגיה", "https://www.bizportal.co.il/capitalmarket/indices/indexcomposition/525"),
    ("ביומד", "https://www.bizportal.co.il/biomed/indices/indexcomposition/521"),
]

LINK_PATTERN = re.compile(
    r'<a[^>]+href="https://www\.bizportal\.co\.il/[a-zA-Z]+/quote/generalview/(\d+)"[^>]*>([^<]+)</a>'
)


def fetch_index_members(url):
    """מחזיר dict: sec_id -> name, לכל המניות בעמוד הרכב המדד."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
    except requests.RequestException as e:
        print(f"  ⚠️  שגיאת רשת: {e}")
        return {}
    if resp.status_code != 200:
        print(f"  ⚠️  status={resp.status_code}")
        return {}
    members = {}
    for sec_id, name in LINK_PATTERN.findall(resp.text):
        members[sec_id] = name.strip()
    return members


def main():
    tiers = {}  # sec_id -> (name, tier_name)
    for tier_name, url in TIER_INDICES:
        print(f"שולף הרכב {tier_name}...")
        members = fetch_index_members(url)
        print(f"  נמצאו {len(members)} מניות.")
        for sec_id, name in members.items():
            if sec_id not in tiers:  # מדד גבוה יותר (שהופיע קודם) גובר
                tiers[sec_id] = (name, tier_name)

    sectors = {}
    for sector_name, url in SECTOR_INDICES:
        print(f"שולף הרכב ענף '{sector_name}'...")
        members = fetch_index_members(url)
        print(f"  נמצאו {len(members)} מניות.")
        for sec_id, name in members.items():
            if sec_id not in sectors:  # אם מניה מופיעה בכמה מדדי ענף, הראשון גובר
                sectors[sec_id] = {"name": name, "sector": sector_name}

    all_ids = set(tiers) | set(sectors)
    combined = {}
    for sec_id in all_ids:
        tier_name_val = tiers.get(sec_id, (None, "שאר המניות"))[1]
        name = (tiers.get(sec_id) or (None,))[0] or (sectors.get(sec_id) or {}).get("name")
        combined[sec_id] = {
            "name": name,
            "tier": tier_name_val,
            "sector": (sectors.get(sec_id) or {}).get("sector"),
        }

    out = {"_meta": {"note": "מיפוי sec_id -> מדד (ת\"א 35/90/יתר 60) וענף. יש לרענן כל רבעון בערך."}}
    out.update(combined)

    with open("index_tiers.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    tier_counts, sector_counts = {}, {}
    for v in combined.values():
        tier_counts[v["tier"]] = tier_counts.get(v["tier"], 0) + 1
        if v["sector"]:
            sector_counts[v["sector"]] = sector_counts.get(v["sector"], 0) + 1
    print(f"\n✅ הושלם. סה\"כ {len(combined)} מניות מסווגות.")
    print(f"לפי מדד: {tier_counts}")
    print(f"לפי ענף: {sector_counts}")
    print("נשמר ל-index_tiers.json")


if __name__ == "__main__":
    main()
