import httpx
from bs4 import BeautifulSoup
import json

targets = [
    ("uzprestige", "https://online.uz-prestige.com"),
    ("flykhiva", "https://b2b.flykhiva.travel"),
    ("rightflight", "https://online.right-flight.org"),
    ("centrum", "https://online.centrum-holidays.com"),
    ("crystalbay", "https://booking-uz.crystalbay.com"),
    ("malva", "https://malvatouroperator.uz")
]

for name, base_url in targets:
    print(f"\n--- Testing {name} ({base_url}) ---")
    # try search_tour
    try:
        r = httpx.get(f"{base_url}/search_tour", timeout=6.0, verify=False, follow_redirects=True)
        print(f"search_tour status: {r.status_code}")
        soup = BeautifulSoup(r.text, "html.parser")
        town_sel = soup.find("select", {"name": "TOWNFROMINC"}) or soup.find("select", id=lambda x: x and "town" in x.lower())
        if town_sel:
            options = {opt.get_text(strip=True): opt.get("value") for opt in town_sel.find_all("option")}
            print(f"Towns found ({len(options)}): {list(options.items())[:5]}")
        else:
            print("No town select found on search_tour")
    except Exception as e:
        print(f"Error {name}: {e}")
