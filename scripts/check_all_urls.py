import httpx
from bs4 import BeautifulSoup

urls = [
    ('Centrum Holidays', 'https://online.centrum-holidays.com/'),
    ('Crystal Bay', 'https://booking-uz.crystalbay.com/'),
    ('Uz-Prestige', 'https://online.uz-prestige.com/'),
    ('Fly Khiva', 'https://b2b.flykhiva.travel/'),
    ('Right Flight', 'https://online.right-flight.org/'),
    ('Delux Tur', 'https://b2bdeluxtur.com/'),
    ('Malva Tour', 'https://malvatouroperator.uz/'),
    ('Enjoy Fly', 'https://b2b.enjoyfly.uz/'),
    ('Mir Jahon', 'https://online.mir-jahon.uz/'),
    ('Atlas Aviatour', 'https://atlasaviatour.uz/'),
    ('Velikolepniy Vek', 'https://velikolepniy-vek.com/'),
    ('Pegas', 'https://uz.pegast.asia/'),
]

for name, url in urls:
    try:
        r = httpx.get(url, timeout=6.0, follow_redirects=True, verify=False)
        soup = BeautifulSoup(r.text, 'html.parser')
        title = soup.title.string.strip() if soup.title else 'No title'
        is_samo = 'samo' in r.text.lower() or 'search_tour' in r.text.lower()
        is_master = 'megatec' in r.text.lower() or 'mastertour' in r.text.lower()
        print(f"{name} ({url}) -> Status {r.status_code} | Samo: {is_samo} | MasterTour: {is_master} | Title: {title[:40]}")
    except Exception as e:
        print(f"{name} ({url}) -> Error: {e}")
