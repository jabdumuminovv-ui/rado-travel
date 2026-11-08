import httpx
from bs4 import BeautifulSoup
import json

targets = [
    ("uzprestige", "https://online.uz-prestige.com"),
    ("flykhiva", "https://b2b.flykhiva.travel"),
    ("rightflight", "https://online.right-flight.org"),
    ("crystalbay", "https://booking-uz.crystalbay.com"),
    ("malva", "https://malvatouroperator.uz")
]

results = {}
for name, base_url in targets:
    try:
        r = httpx.get(f"{base_url}/search_tour", timeout=6.0, verify=False, follow_redirects=True)
        soup = BeautifulSoup(r.text, "html.parser")
        town_sel = soup.find("select", {"name": "TOWNFROMINC"})
        state_sel = soup.find("select", {"name": "STATEINC"})
        
        towns = {}
        if town_sel:
            for opt in town_sel.find_all("option"):
                v = opt.get("value")
                t = opt.get_text(strip=True)
                if v and v != "0":
                    towns[t] = v

        states = {}
        if state_sel:
            for opt in state_sel.find_all("option"):
                v = opt.get("value")
                t = opt.get_text(strip=True)
                if v and v != "0":
                    states[t] = v

        results[name] = {"towns": towns, "states": states}
    except Exception as e:
        results[name] = {"error": str(e)}

with open("scripts/operators_metadata.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print("Saved operators_metadata.json")
