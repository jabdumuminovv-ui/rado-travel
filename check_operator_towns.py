import urllib.request
import ssl
import re
import json

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

headers = {'User-Agent': 'Mozilla/5.0'}

targets = {
    'EasyBooking': 'https://tours.easybooking.uz/search_tour',
    'SelfieTravel': 'https://b2b.selfietravel.kz/search_tour',
    'Kazunion': 'https://online.kazunion.com/search_tour',
    'CentrumHolidays': 'https://online.centrum-holidays.com/search_tour'
}

towns_by_op = {}

for name, url in targets.items():
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=10) as r:
            html = r.read().decode('utf-8', errors='ignore')
            match = re.search(r'<select[^>]*name=["\']TOWNFROMINC["\'][^>]*>(.*?)</select>', html, re.DOTALL | re.I)
            if match:
                options = re.findall(r'<option[^>]*value=["\']([^"\']*)["\'][^>]*>(.*?)</option>', match.group(1))
                towns_by_op[name] = {re.sub(r'<[^>]+>', '', t).strip(): v for v, t in options}
            else:
                towns_by_op[name] = "TOWNFROMINC not found"
    except Exception as e:
        towns_by_op[name] = f"Error: {e}"

with open(r'C:\Users\farru\.gemini\antigravity\scratch\tour-aggregator\operator_towns.json', 'w', encoding='utf-8') as f:
    json.dump(towns_by_op, f, ensure_ascii=False, indent=2)

print("Saved operator_towns.json")
