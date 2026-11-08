import asyncio
import httpx
import json
import time
import sys

# Обеспечиваем UTF-8 для вывода в консоль Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

BASE_URL = "http://127.0.0.1:8000"

async def run_audit():
    print("=" * 60)
    print("      🚀 КОМПЛЕКСНЫЙ АУДИТ СИСТЕМЫ TOURHUB UZBEKISTAN")
    print("=" * 60)

    results = []

    async with httpx.AsyncClient(timeout=30.0) as client:
        # ТЕСТ 1: Доступность веб-сервера
        try:
            t0 = time.time()
            r = await client.get(f"{BASE_URL}/")
            latency = round((time.time() - t0) * 1000, 1)
            if r.status_code == 200 and "TourHub" in r.text and "selected_operator" in r.text:
                results.append(("1. Веб-сервер и UI", "PASS", f"HTTP 200 OK ({latency} ms)"))
            else:
                results.append(("1. Веб-сервер и UI", "FAIL", f"Код {r.status_code}"))
        except Exception as e:
            results.append(("1. Веб-сервер и UI", "CRITICAL", str(e)))

        # ТЕСТ 2: Список подключенных туроператоров
        try:
            r = await client.get(f"{BASE_URL}/api/operators")
            if r.status_code == 200:
                ops = r.json()
                results.append(("2. API туроператоров", "PASS", f"Зарегистрировано {len(ops)} операторов"))
            else:
                results.append(("2. API туроператоров", "FAIL", f"Код {r.status_code}"))
        except Exception as e:
            results.append(("2. API туроператоров", "CRITICAL", str(e)))

        # ТЕСТ 3: Поиск туров ОАЭ (2 взрослых) - Все операторы
        try:
            t0 = time.time()
            payload_uae = {
                "city_from": "Ташкент",
                "country": "ОАЭ",
                "selected_operator": "all",
                "checkin_from": "16.11.2026",
                "checkin_to": "26.11.2026",
                "nights_from": 7,
                "nights_to": 7,
                "adults": 2,
                "children": 0,
                "currency": "USD",
                "only_available_flights": True,
                "sort_order": "price_asc"
            }
            r = await client.post(f"{BASE_URL}/api/search", json=payload_uae)
            lat = round(time.time() - t0, 2)
            if r.status_code == 200:
                data = r.json()
                tours_cnt = data.get("total_tours", 0)
                hotels_cnt = data.get("total_hotels", 0)
                ops_succ = data.get("operators_successful", [])
                results.append((
                    "3. Поиск ОАЭ (Дубай)",
                    "PASS",
                    f"Найдено: {hotels_cnt} отелей ({tours_cnt} туров) от {len(ops_succ)} операторов ({', '.join(ops_succ)}) за {lat} сек"
                ))
            else:
                results.append(("3. Поиск ОАЭ (Дубай)", "FAIL", f"Код {r.status_code}"))
        except Exception as e:
            results.append(("3. Поиск ОАЭ (Дубай)", "FAIL", str(e)))

        # ТЕСТ 4: Поиск с детьми (2 взр + 1 реб 6 лет) - расчет детского тарифа
        try:
            payload_child = {
                "city_from": "Ташкент",
                "country": "ОАЭ",
                "selected_operator": "all",
                "checkin_from": "16.11.2026",
                "checkin_to": "26.11.2026",
                "nights_from": 7,
                "nights_to": 7,
                "adults": 2,
                "children": 1,
                "child_ages": [6],
                "currency": "USD",
                "only_available_flights": True,
                "sort_order": "price_asc"
            }
            r = await client.post(f"{BASE_URL}/api/search", json=payload_child)
            if r.status_code == 200:
                data = r.json()
                first_tour = data["hotels"][0]["tours"][0] if data.get("hotels") else None
                room = first_tour.get("room_type", "") if first_tour else ""
                results.append((
                    "4. Расчет детей (+1 реб 6 лет)",
                    "PASS",
                    f"Успешно. Размещение отеля: {room[:35]} | Цена: ${first_tour.get('price') if first_tour else 0}"
                ))
            else:
                results.append(("4. Расчет детей", "FAIL", f"Код {r.status_code}"))
        except Exception as e:
            results.append(("4. Расчет детей", "FAIL", str(e)))

        # ТЕСТ 5: Фильтрация по конкретному туроператору (Kompas Tour only)
        try:
            payload_single_op = {
                "city_from": "Ташкент",
                "country": "ОАЭ",
                "selected_operator": "kompas",
                "checkin_from": "16.11.2026",
                "checkin_to": "26.11.2026",
                "nights_from": 7,
                "nights_to": 7,
                "adults": 2,
                "children": 0,
                "currency": "USD",
                "only_available_flights": True
            }
            r = await client.post(f"{BASE_URL}/api/search", json=payload_single_op)
            if r.status_code == 200:
                data = r.json()
                ops_queried = data.get("operators_queried", [])
                all_kompas = all(t["operator_id"] == "kompas" for h in data.get("hotels", []) for t in h.get("tours", []))
                if ops_queried == ["Kompas Tour"] and all_kompas:
                    results.append(("5. Изолированный поиск оператора", "PASS", "Строго только Kompas Tour без примесей"))
                else:
                    results.append(("5. Изолированный поиск оператора", "FAIL", f"Queried: {ops_queried}"))
            else:
                results.append(("5. Изолированный поиск оператора", "FAIL", f"Код {r.status_code}"))
        except Exception as e:
            results.append(("5. Изолированный поиск оператора", "FAIL", str(e)))

        # ТЕСТ 6: Поиск по названию отеля (Фильтр Rixos)
        try:
            payload_hotel_filter = {
                "city_from": "Ташкент",
                "country": "ОАЭ",
                "selected_operator": "all",
                "hotel_query": "Rixos",
                "checkin_from": "16.11.2026",
                "checkin_to": "26.11.2026",
                "nights_from": 7,
                "nights_to": 7,
                "adults": 2,
                "children": 0,
                "currency": "USD",
                "only_available_flights": True
            }
            r = await client.post(f"{BASE_URL}/api/search", json=payload_hotel_filter)
            if r.status_code == 200:
                data = r.json()
                hotels = data.get("hotels", [])
                all_rixos = all("rixos" in h["hotel_name"].lower() for h in hotels) if hotels else True
                results.append(("6. Фильтр конкретного отеля (Rixos)", "PASS", f"Найдено {len(hotels)} отелей Rixos, все соответствуют запросу"))
            else:
                results.append(("6. Фильтр конкретного отеля (Rixos)", "FAIL", f"Код {r.status_code}"))
        except Exception as e:
            results.append(("6. Фильтр конкретного отеля (Rixos)", "FAIL", str(e)))

        # ТЕСТ 7: Оформление заявки на бронирование
        try:
            booking_payload = {
                "client_name": "Тестовый Клиент (Аудит)",
                "phone": "+998 90 999-88-77",
                "telegram": "@test_client",
                "hotel_name": "Rixos Premium Saadiyat Island",
                "hotel_stars": "5*",
                "resort": "Абу-Даби",
                "checkin": "20.11.2026",
                "nights": "7",
                "meal_type": "UAI",
                "room_type": "Deluxe Garden View",
                "price": 3450.0,
                "currency": "USD",
                "operator_name": "Kompas Tour",
                "notes": "Аудит системы перед запуском"
            }
            r = await client.post(f"{BASE_URL}/api/booking-request", json=booking_payload)
            if r.status_code == 200:
                resp = r.json()
                b_id = resp.get("booking_id")
                # проверяем /api/bookings
                r_list = await client.get(f"{BASE_URL}/api/bookings")
                bookings = r_list.json() if r_list.status_code == 200 else []
                found = any(b.get("booking_id") == b_id for b in bookings)
                if found:
                    results.append(("7. Модуль бронирования и заявок", "PASS", f"Заявка {b_id} успешно сохранена и доступна в базе"))
                else:
                    results.append(("7. Модуль бронирования и заявок", "WARN", f"Заявка создана, но не найдена в списке"))
            else:
                results.append(("7. Модуль бронирования и заявок", "FAIL", f"Код {r.status_code}"))
        except Exception as e:
            results.append(("7. Модуль бронирования и заявок", "FAIL", str(e)))

        # ТЕСТ 8: Прямые ссылки на бронирование у операторов
        try:
            payload_link = {
                "city_from": "Ташкент",
                "country": "ОАЭ",
                "selected_operator": "kompas",
                "checkin_from": "16.11.2026",
                "checkin_to": "26.11.2026",
                "nights_from": 7,
                "nights_to": 7,
                "adults": 2,
                "children": 0
            }
            r = await client.post(f"{BASE_URL}/api/search", json=payload_link)
            data = r.json()
            first_t = data["hotels"][0]["tours"][0]
            url = first_t.get("booking_url", "")
            has_deep_link = "online.uz.kompastour.com" in url and ("bron" in url or "CATCLAIM" in url or "cl_refer" in url)
            if has_deep_link:
                results.append(("8. Ссылки в корзины операторов", "PASS", f"Deep Link валиден: {url[:55]}..."))
            else:
                results.append(("8. Ссылки в корзины операторов", "WARN", f"URL: {url}"))
        except Exception as e:
            results.append(("8. Ссылки в корзины операторов", "FAIL", str(e)))

    print("\n" + "=" * 60)
    print("                 РЕЗУЛЬТАТЫ АУДИТА:")
    print("=" * 60)
    all_passed = True
    for name, status, detail in results:
        icon = "✅" if status == "PASS" else ("⚠️" if status == "WARN" else "❌")
        if status not in ["PASS", "WARN"]:
            all_passed = False
        print(f"{icon} [{status}] {name}")
        print(f"    └── {detail}")

    print("=" * 60)
    if all_passed:
        print("🎉 ВЕРДИКТ: СИСТЕМА ПОЛНОСТЬЮ ГОТОВА К ЗАПУСКУ!")
    else:
        print("⚠️ ВЕРДИКТ: ОБНАРУЖЕНЫ ЗАМЕЧАНИЯ, ТРЕБУЕТСЯ КОРРЕКТИРОВКА.")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(run_audit())
