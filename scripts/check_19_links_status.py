import httpx
import asyncio
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

urls = [
    ("Kompas Tour", "https://online.uz.kompastour.com/cl_refer"),
    ("Centrum Holidays", "https://online.centrum-holidays.com/"),
    ("Pegas Touristik", "https://uz.pegast.asia/"),
    ("Delux Tur", "https://b2bdeluxtur.com/"),
    ("Izel Booking", "https://www.izelbooking.com/"),
    ("RateHawk", "https://www.ratehawk.com/"),
    ("Atlas Aviatour", "https://atlasaviatour.uz/"),
    ("Enjoy Fly", "https://b2b.enjoyfly.uz/"),
    ("Mir Jahon", "https://online.mir-jahon.uz/"),
    ("Crystal Bay", "https://booking-uz.crystalbay.com/"),
    ("Uz-Prestige", "https://online.uz-prestige.com/"),
    ("Fly Khiva", "https://b2b.flykhiva.travel/"),
    ("Right Flight", "https://online.right-flight.org/"),
    ("Velikolepniy Vek", "https://velikolepniy-vek.com/"),
    ("EasyBooking", "https://tours.easybooking.uz/cl_refer"),
    ("Selfie Travel", "https://b2b.selfietravel.kz/"),
    ("Kazunion", "https://online.kazunion.com/"),
    ("Malva Tour", "https://malvatouroperator.uz/"),
    ("Asialuxe Travel", "https://b2b.asialuxe.uz/")
]

async def check_all():
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"}
    async with httpx.AsyncClient(timeout=8.0, verify=False, follow_redirects=True) as client:
        for name, url in urls:
            try:
                r = await client.get(url, headers=headers)
                print(f"[{r.status_code}] {name:18} | URL: {url}")
            except Exception as e:
                print(f"[ERR] {name:18} | Ошибка подключения: {e}")

asyncio.run(check_all())
