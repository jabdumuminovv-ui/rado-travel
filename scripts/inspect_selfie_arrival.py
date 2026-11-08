import asyncio
import httpx
import re
import json
from bs4 import BeautifulSoup
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

async def inspect_selfie():
    url = "https://b2b.selfietravel.kz/search_tour"
    params = {
        "samo_action": "PRICES",
        "TOWNFROMINC": "1853", # Tashkent
        "STATEINC": "50",      # Maldives
        "CHECKIN_BEG": "15.11.2026",
        "CHECKIN_END": "25.11.2026",
        "NIGHTS_FROM": "7",
        "NIGHTS_TILL": "7",
        "ADULT": "2",
        "CHILD": "0",
        "CURRENCY": "2",
        "PRICEPAGE": "1",
        "DYN_SEPARATE": "1"
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "X-Requested-With": "XMLHttpRequest"
    }
    async with httpx.AsyncClient(timeout=20.0, verify=False) as client:
        r = await client.get(url, params=params, headers=headers)
        m = re.search(r'\.ehtml\((".*?")\);', r.text, re.DOTALL)
        if not m:
            print("No ehtml found!")
            return
        html = json.loads(m.group(1))
        soup = BeautifulSoup(html, "html.parser")
        
        # print the table header (th elements)
        headers_th = [th.get_text(strip=True) for th in soup.find_all("th")]
        print("Table TH headers:", headers_th)

        rows = soup.find_all("tr", class_=lambda c: c and "price_info" in c)
        print(f"Found {len(rows)} price_info rows")
        if rows:
            first_row = rows[0]
            print("\nFirst row HTML:")
            print(first_row.prettify()[:1500])
            print("\nAll td classes and contents in first row:")
            for idx, td in enumerate(first_row.find_all("td")):
                print(f"  td[{idx}] class={td.get('class')} text='{td.get_text(' ', strip=True)}'")

asyncio.run(inspect_selfie())
