import asyncio
import httpx
import re
import json
from bs4 import BeautifulSoup
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

async def test_both():
    # 1. Selfie
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
    async with httpx.AsyncClient(timeout=15.0, verify=False) as client:
        r = await client.get(url, params=params, headers=headers)
        m = re.search(r'\.ehtml\((".*?")\);', r.text, re.DOTALL)
        if m:
            soup = BeautifulSoup(json.loads(m.group(1)), "html.parser")
            row = soup.find("tr", class_=lambda c: c and "price_info" in c)
            if row:
                print("Selfie Travel row data attributes:", {k: v for k, v in row.attrs.items() if k.startswith("data-")})
                sortie = row.find("td", class_=lambda c: c and ("sortie" in c or "arrival" in c))
                print("Selfie Travel sortie td:", repr(sortie.prettify() if sortie else None))
                transport = row.find("td", class_=lambda c: c and "transport" in c)
                print("Selfie Travel transport td:", repr(transport.prettify() if transport else None))

    # 2. Kompas
    url2 = "https://online.uz.kompastour.com/search_tour"
    params2 = {
        "samo_action": "PRICES",
        "TOWNFROMINC": "26",
        "STATEINC": "23",
        "CHECKIN_BEG": "15.11.2026",
        "CHECKIN_END": "25.11.2026",
        "NIGHTS_FROM": "7",
        "NIGHTS_TILL": "7",
        "ADULT": "2",
        "CHILD": "0",
        "CURRENCY": "2",
        "PRICEPAGE": "1"
    }
    async with httpx.AsyncClient(timeout=15.0, verify=False) as client:
        r2 = await client.get(url2, params=params2, headers=headers)
        m2 = re.search(r'\.ehtml\((".*?")\);', r2.text, re.DOTALL)
        if m2:
            soup2 = BeautifulSoup(json.loads(m2.group(1)), "html.parser")
            row2 = soup2.find("tr", class_=lambda c: c and "price_info" in c)
            if row2:
                print("\nKompas row data attributes:", {k: v for k, v in row2.attrs.items() if k.startswith("data-")})
                sortie2 = row2.find("td", class_=lambda c: c and ("sortie" in c or "arrival" in c))
                print("Kompas sortie/arrival td:", repr(sortie2.prettify() if sortie2 else None))

asyncio.run(test_both())
