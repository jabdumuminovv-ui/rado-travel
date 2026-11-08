import re
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional
import httpx
from bs4 import BeautifulSoup
from app.connectors.base import BaseTourConnector
from app.models import SearchParams, TourItem

logger = logging.getLogger(__name__)

class SamoConnector(BaseTourConnector):
    """
    Универсальный коннектор к туроператорам на платформе SAMO-Soft.
    Поддерживает расчет цен с детьми и их возрастом, поиск отелей по названию,
    статусы мест на рейсах и прямые ссылки на бронирование.
    """
    def __init__(
        self,
        operator_id: str,
        name: str,
        base_url: str,
        towns_map: Optional[Dict[str, str]] = None,
        states_map: Optional[Dict[str, str]] = None
    ):
        super().__init__(operator_id, name, base_url.rstrip('/'))
        self.towns_map = {k.lower(): str(v) for k, v in (towns_map or {}).items()}
        self.states_map = {k.lower(): str(v) for k, v in (states_map or {}).items()}
        self.currency_map = {
            "USD": "2",
            "EUR": "3",
            "UZS": "10",
            "KZT": "1"
        }
        self._hotel_cache: Dict[str, List[Dict]] = {}

    def is_city_supported(self, city_name: str) -> bool:
        return city_name.strip().lower() in self.towns_map

    async def _get_hotel_ids_by_name(self, town_id: str, state_id: str, query: str) -> List[str]:
        cache_key = f"{town_id}_{state_id}"
        hotels = self._hotel_cache.get(cache_key)

        if hotels is None:
            url = f"{self.base_url}/search_tour"
            params = {
                "samo_action": "STATEINC",
                "TOWNFROMINC": town_id,
                "STATEINC": state_id
            }
            try:
                async with httpx.AsyncClient(timeout=15.0, verify=False) as client:
                    resp = await client.get(url, params=params)
                    if resp.status_code == 200:
                        m = re.search(r'samo\.hotelDynamic\s*=\s*(\[.*?\]);', resp.text, re.DOTALL)
                        if m:
                            hotels = json.loads(m.group(1))
                            self._hotel_cache[cache_key] = hotels
            except Exception as e:
                logger.warning(f"[{self.name}] Ошибка получения hotelDynamic: {e}")
                hotels = []

        if not hotels:
            return []

        q = query.strip().lower()
        matched_ids = []
        for h in hotels:
            h_name = h.get("name", "").lower()
            if q in h_name:
                matched_ids.append(str(h["id"]))

        return matched_ids

    async def search(self, params: SearchParams) -> List[TourItem]:
        city_key = params.city_from.strip().lower()
        town_id = self.towns_map.get(city_key)
        if not town_id:
            return []

        country_key = params.country.strip().lower()
        state_id = self.states_map.get(country_key)
        if not state_id:
            for name, sid in self.states_map.items():
                if name in country_key or country_key in name:
                    state_id = sid
                    break
        if not state_id:
            return []

        currency_id = self.currency_map.get(params.currency.upper(), "2")

        query_params = {
            "samo_action": "PRICES",
            "TOWNFROMINC": town_id,
            "STATEINC": state_id,
            "CHECKIN_BEG": params.checkin_from,
            "CHECKIN_END": params.checkin_to,
            "NIGHTS_FROM": str(params.nights_from),
            "NIGHTS_TILL": str(params.nights_to),
            "ADULT": str(params.adults),
            "CHILD": str(params.children),
            "CURRENCY": currency_id,
            "PRICEPAGE": "1",
            "DYN_SEPARATE": "1"
        }

        # Возраста детей (AGE1, AGE2, AGE3)
        if params.children > 0 and params.child_ages:
            for i in range(1, 4):
                age = params.child_ages[i-1] if i <= len(params.child_ages) else 0
                query_params[f"AGE{i}"] = str(age)
        else:
            query_params["AGE1"] = "0"
            query_params["AGE2"] = "0"
            query_params["AGE3"] = "0"

        # Фильтр "Только с местами на рейс"
        if params.only_available_flights:
            query_params["FREIGHT"] = "1"

        # Фильтр по названию отеля (Rixos, Albatros и др.)
        if params.hotel_query and params.hotel_query.strip():
            hotel_ids = await self._get_hotel_ids_by_name(town_id, state_id, params.hotel_query)
            if hotel_ids:
                query_params["HOTELS"] = ",".join(hotel_ids[:50])
                query_params["HOTELS_SEL"] = "1"
                logger.info(f"[{self.name}] Применен фильтр по {len(hotel_ids)} отелям: '{params.hotel_query}'")

        url = f"{self.base_url}/search_tour"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "X-Requested-With": "XMLHttpRequest",
            "Accept": "*/*"
        }

        logger.info(f"[{self.name}] Поиск: {params.city_from} -> {params.country} ({params.checkin_from}-{params.checkin_to}) Взр:{params.adults}, Дет:{params.children}")

        try:
            async with httpx.AsyncClient(timeout=25.0, verify=False) as client:
                resp = await client.get(url, params=query_params, headers=headers)
                if resp.status_code != 200:
                    return []
                content = resp.text
        except Exception as e:
            logger.error(f"[{self.name}] Ошибка сети: {e}")
            return []

        return self._parse_samo_response(content, currency_id, params.currency)

    def _parse_samo_response(self, text: str, currency_id: str, currency_symbol: str) -> List[TourItem]:
        match = re.search(r'\.ehtml\((".*?")\);', text, re.DOTALL)
        if not match:
            return []

        try:
            html = json.loads(match.group(1))
        except Exception:
            return []

        soup = BeautifulSoup(html, "html.parser")
        rows = soup.find_all("tr", class_=lambda c: c and "price_info" in c)

        tours: List[TourItem] = []

        for row in rows:
            try:
                row_classes = row.get("class", [])
                is_red_row = "red_row" in row_classes

                cat_claim = row.get("data-cat-claim", "")
                hotel_name_attr = row.get("data-hotel-name", "").strip()

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

                tour_td = row.find("td", class_="tour")
                tour_name = tour_td.get_text(" ", strip=True) if tour_td else ""

                nights = row.get("data-nights") or row.get("data-hnights")
                if not nights:
                    nights_td = row.find("td", class_=lambda c: c and any(k in c for k in ["tour-nights", "nights"]))
                    nights = nights_td.get_text(strip=True) if nights_td else "7"

                hotel_td = row.find("td", class_=lambda c: c and "link-hotel" in c)
                hotel_text = hotel_td.get_text(" ", strip=True) if hotel_td else hotel_name_attr

                stars_match = re.search(r'(\d\*|5\*\s*DELUXE|HV-\d|Boutique|Apartment)', hotel_text, re.I)
                hotel_stars = stars_match.group(1) if stars_match else "5*"

                resort_match = re.search(r'\((.*?)\)', hotel_text)
                resort = resort_match.group(1).strip() if resort_match else ""

                clean_hotel_name = re.sub(r'[\(\[].*?[\)\]]', '', hotel_text)
                clean_hotel_name = re.sub(r'\d\*|5\*\s*DELUXE|HV-\d|Boutique|Apartment', '', clean_hotel_name, flags=re.I).strip().strip(',')

                if not clean_hotel_name and hotel_name_attr:
                    clean_hotel_name = hotel_name_attr

                meal_td = row.find("td", class_=lambda c: c and "hotel-meals" in c)
                meal_type = meal_td.get_text(strip=True) if meal_td else ""
                if not meal_type:
                    tds = row.find_all("td")
                    if len(tds) > 6:
                        cand_meal = tds[6].get_text(strip=True)
                        if cand_meal in ["AI", "UAI", "BB", "HB", "FB", "RO"]:
                            meal_type = cand_meal
                if not meal_type:
                    meal_type = "AI"

                room_td = row.find("td", class_=lambda c: c and "hotel-room" in c)
                room_type = room_td.get_text(" / ", strip=True) if room_td else ""
                if not room_type:
                    tds = row.find_all("td")
                    if len(tds) > 7:
                        cand_room = tds[7].get_text(" / ", strip=True)
                        if cand_room:
                            room_type = cand_room
                if not room_type:
                    room_type = "Standard Room"

                price_span = row.find("span", class_=lambda c: c and "price" in c)
                price_num = 0.0
                price_formatted = "0"
                if price_span:
                    num_str = price_span.get("data-cat-price") or price_span.get("data-converted-price-number")
                    if num_str:
                        try:
                            price_num = float(num_str)
                        except ValueError:
                            pass
                    price_formatted = price_span.get_text(strip=True)

                if price_num <= 0:
                    continue

                transport_td = row.find("td", class_=lambda c: c and "transport" in c)
                flight_info = "Прямой чартер"
                to_status = "Y"
                back_status = "Y"

                if transport_td:
                    name_el = transport_td.find("span", class_="name")
                    if name_el:
                        flight_info = name_el.get_text(strip=True)
                    
                    place_r = transport_td.find("span", class_=lambda c: c and "fr_place_r" in c)
                    place_l = transport_td.find("span", class_=lambda c: c and "fr_place_l" in c)

                    if place_r:
                        classes_r = place_r.get("class", [])
                        for s in ["Y", "M", "F", "N", "R"]:
                            if s in classes_r:
                                to_status = s
                                break

                    if place_l:
                        classes_l = place_l.get("class", [])
                        for s in ["Y", "M", "F", "N", "R"]:
                            if s in classes_l:
                                back_status = s
                                break

                is_available = (to_status not in ["F", "N"]) and (back_status not in ["F", "N"]) and not is_red_row

                if cat_claim:
                    booking_url = f"{self.base_url}/bron?CATCLAIM={cat_claim}&CURRENCY={currency_id}"
                else:
                    booking_url = f"{self.base_url}/search_tour"

                item = TourItem(
                    operator_id=self.operator_id,
                    operator_name=self.name,
                    tour_name=tour_name,
                    checkin=checkin_date,
                    departure_time=dep_time,
                    day_of_week=day_of_week,
                    nights=nights,
                    hotel_name=clean_hotel_name,
                    hotel_stars=hotel_stars,
                    resort=resort,
                    meal_type=meal_type,
                    room_type=room_type,
                    price=price_num,
                    currency=currency_symbol,
                    price_formatted=price_formatted,
                    booking_url=booking_url,
                    flight_info=flight_info,
                    flight_to_status=to_status,
                    flight_back_status=back_status,
                    is_available=is_available,
                    is_red_row=is_red_row
                )
                tours.append(item)
            except Exception as e:
                logger.error(f"Ошибка парсинга строки: {e}")
                continue

        logger.info(f"[{self.name}] Найдено {len(tours)} туров")
        return tours
