import asyncio
import httpx
import re
import json
from bs4 import BeautifulSoup
from datetime import datetime
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

async def test():
    url = "https://b2b.selfietravel.kz/search_tour"
    params = {
        "samo_action": "PRICES",
        "TOWNFROMINC": "1853",
        "STATEINC": "50",
        "CHECKIN_BEG": "15.11.2026",
        "CHECKIN_END": "25.11.2026",
        "NIGHTS_FROM": "7",
        "NIGHTS_TILL": "7",
        "ADULT": "2",
        "CHILD": "0",
        "CURRENCY": "2",
        "PRICEPAGE": "1"
    }
    headers = {"User-Agent": "Mozilla/5.0", "X-Requested-With": "XMLHttpRequest"}
    async with httpx.AsyncClient(timeout=20.0, verify=False) as client:
        r = await client.get(url, params=params, headers=headers)
        soup = BeautifulSoup(json.loads(re.search(r'\.ehtml\((".*?")\);', r.text, re.DOTALL).group(1)), "html.parser")
        rows = soup.find_all("tr", class_=lambda c: c and "price_info" in c)
        print(f"Total rows in Selfie: {len(rows)}")
        for i, row in enumerate(rows[:5]):
            arrival_td = row.find("td", class_=lambda c: c and any(k in c for k in ["arrival", "sortie", "checkin", "date"]))
            raw_arrival = arrival_td.get_text(" ", strip=True) if arrival_td else ""
            
            date_match = re.search(r'(\d{2}\.\d{2}\.\d{4})', raw_arrival)
            checkin_date = date_match.group(1) if date_match else ""

            if not checkin_date:
                date_el = row.find(attrs={"data-date": True})
                if date_el and date_el.get("data-date"):
                    checkin_date = date_el.get("data-date").strip()

            if not checkin_date:
                dc = row.get("data-checkin", "")
                if len(dc) == 8 and dc.isdigit():
                    checkin_date = f"{dc[6:8]}.{dc[4:6]}.{dc[0:4]}"

            time_match = re.search(r'(\d{1,2}:\d{2}(?:,\s*\d{1,2}:\d{2})*)', raw_arrival)
            dep_time = time_match.group(1) if time_match else ""

            day_match = re.search(r',\s*([а-яА-Яa-zA-Z]{2})\b', raw_arrival)
            day_of_week = day_match.group(1).lower() if day_match else ""

            if not day_of_week and checkin_date:
                try:
                    dt = datetime.strptime(checkin_date, "%d.%m.%Y")
                    days_ru = ["пн", "вт", "ср", "чт", "пт", "сб", "вс"]
                    day_of_week = days_ru[dt.weekday()]
                except Exception:
                    pass

            print(f"Row {i+1}: checkin_date='{checkin_date}', day='{day_of_week}', time='{dep_time}'")

asyncio.run(test())
