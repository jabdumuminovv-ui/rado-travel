import asyncio
import logging
from typing import List, Dict
from app.models import SearchParams, SearchResponse, HotelGroup, TourItem
from app.connectors.base import BaseTourConnector
from app.connectors.samo import SamoConnector

logger = logging.getLogger(__name__)

class TourAggregatorService:
    def __init__(self):
        self.connectors: List[BaseTourConnector] = []
        self._register_default_connectors()

    def _register_default_connectors(self):
        # 1. Kompas Tour (Узбекистан)
        self.connectors.append(
            SamoConnector(
                operator_id="kompas",
                name="Kompas Tour",
                base_url="https://online.uz.kompastour.com",
                towns_map={
                    "ташкент": "26",
                    "tashkent": "26",
                    "самарканд": "917",
                    "бухара": "913",
                    "фергана": "1819",
                    "ургенч": "2071"
                },
                states_map={
                    "оаэ": "23",
                    "дубай": "23",
                    "турция": "17",
                    "египет": "37",
                    "мальдивы": "40",
                    "таиланд": "28",
                    "шри-ланка": "27",
                    "вьетнам": "32",
                    "маврикий": "86",
                    "сейшелы": "77",
                    "сейшельские острова": "77",
                    "катар": "111",
                    "азербайджан": "61",
                    "малайзия": "12",
                    "индонезия": "11",
                    "бали": "11"
                }
            )
        )
        # 2. EasyBooking Tours
        self.connectors.append(
            SamoConnector(
                operator_id="easybooking",
                name="EasyBooking",
                base_url="https://tours.easybooking.uz",
                towns_map={
                    "ташкент": "1853",
                    "tashkent": "1853",
                    "самарканд": "1949"
                },
                states_map={
                    "оаэ": "13",
                    "дубай": "13",
                    "турция": "9",
                    "египет": "10",
                    "мальдивы": "50",
                    "таиланд": "19",
                    "грузия": "29",
                    "азербайджан": "36",
                    "маврикий": "54",
                    "сейшелы": "78",
                    "малайзия": "41",
                    "индонезия": "69",
                    "бали": "69"
                }
            )
        )
        # 3. Selfie Travel
        self.connectors.append(
            SamoConnector(
                operator_id="selfietravel",
                name="Selfie Travel",
                base_url="https://b2b.selfietravel.kz",
                towns_map={
                    "ташкент": "1853",
                    "tashkent": "1853",
                    "самарканд": "2005"
                },
                states_map={
                    "оаэ": "13",
                    "дубай": "13",
                    "египет": "10",
                    "мальдивы": "50",
                    "катар": "63",
                    "грузия": "29",
                    "азербайджан": "36",
                    "малайзия": "41",
                    "индонезия": "69"
                }
            )
        )
        # 4. Kazunion
        self.connectors.append(
            SamoConnector(
                operator_id="kazunion",
                name="Kazunion",
                base_url="https://online.kazunion.com",
                towns_map={
                    "ташкент": "839",
                    "tashkent": "839",
                    "самарканд": "838"
                },
                states_map={
                    "оаэ": "11",
                    "дубай": "11",
                    "турция": "6",
                    "таиланд": "12",
                    "катар": "95",
                    "китай": "19",
                    "хайнань": "19",
                    "вьетнам": "22",
                    "грузия": "43",
                    "азербайджан": "48"
                }
            )
        )
        # 5. Fly Khiva
        self.connectors.append(
            SamoConnector(
                operator_id="flykhiva",
                name="Fly Khiva",
                base_url="https://b2b.flykhiva.travel",
                towns_map={
                    "ташкент": "1853",
                    "tashkent": "1853",
                    "самарканд": "2478"
                },
                states_map={
                    "египет": "10",
                    "турция": "9",
                    "мальдивы": "50",
                    "таиланд": "19",
                    "грузия": "29",
                    "азербайджан": "36",
                    "оман": "76"
                }
            )
        )
        # 6. Right Flight
        self.connectors.append(
            SamoConnector(
                operator_id="rightflight",
                name="Right Flight",
                base_url="https://online.right-flight.org",
                towns_map={
                    "ташкент": "1853",
                    "tashkent": "1853"
                },
                states_map={
                    "оаэ": "13",
                    "дубай": "13",
                    "турция": "9",
                    "китай": "31",
                    "хайнань": "31"
                }
            )
        )
        # 7. Malva Tour
        self.connectors.append(
            SamoConnector(
                operator_id="malva",
                name="Malva Tour",
                base_url="https://malvatouroperator.uz",
                towns_map={
                    "ташкент": "1853",
                    "tashkent": "1853"
                },
                states_map={
                    "турция": "9",
                    "таиланд": "19",
                    "мальдивы": "50",
                    "малайзия": "41",
                    "индонезия": "69",
                    "бали": "69",
                    "азербайджан": "36",
                    "шри-ланка": "52"
                }
            )
        )
        # 8. Uz-Prestige
        self.connectors.append(
            SamoConnector(
                operator_id="uzprestige",
                name="Uz-Prestige",
                base_url="https://online.uz-prestige.com",
                towns_map={
                    "ташкент": "1853",
                    "tashkent": "1853",
                    "самарканд": "2200"
                },
                states_map={
                    "азербайджан": "36"
                }
            )
        )
        # 9. Crystal Bay
        self.connectors.append(
            SamoConnector(
                operator_id="crystalbay",
                name="Crystal Bay",
                base_url="https://booking-uz.crystalbay.com",
                towns_map={
                    "ташкент": "1853",
                    "tashkent": "1853"
                },
                states_map={
                    "вьетнам": "43",
                    "фукуок": "43"
                }
            )
        )

    def get_registered_operators(self) -> List[Dict[str, str]]:
        return [
            {"id": c.operator_id, "name": c.name, "url": c.base_url}
            for c in self.connectors
        ]

    async def search_all(self, params: SearchParams) -> SearchResponse:
        logger.info(f"Запуск поиска: {params.city_from} -> {params.country} (Оператор: {params.selected_operator}, Сортировка: {params.sort_order})")

        # Выбор туроператоров для запуска
        connectors_to_run = self.connectors
        
        # Если выбран конкретный туроператор в фильтре
        if params.selected_operator and params.selected_operator.lower() not in ["all", "все"]:
            target_id = params.selected_operator.lower()
            connectors_to_run = [c for c in self.connectors if c.operator_id.lower() == target_id or target_id in c.name.lower()]
            if not connectors_to_run:
                # fallback
                connectors_to_run = self.connectors
        elif params.operators:
            op_set = set(o.lower() for o in params.operators)
            connectors_to_run = [c for c in self.connectors if c.operator_id.lower() in op_set or c.name.lower() in op_set]

        tasks = []
        for connector in connectors_to_run:
            tasks.append(self._safe_connector_search(connector, params))

        results_list = await asyncio.gather(*tasks)

        all_tours: List[TourItem] = []
        successful_ops: List[str] = []

        for connector, tours in zip(connectors_to_run, results_list):
            if tours:
                successful_ops.append(connector.name)
                all_tours.extend(tours)

        # Фильтрация по питанию / звездам
        filtered_tours = all_tours
        if params.meal_filter and params.meal_filter.upper() != "ALL":
            mf = params.meal_filter.upper()
            filtered_tours = [t for t in filtered_tours if mf in t.meal_type.upper()]

        if params.stars_filter and params.stars_filter.upper() != "ALL":
            sf = params.stars_filter.upper()
            filtered_tours = [t for t in filtered_tours if sf in t.hotel_stars.upper()]

        # Группировка по отелям
        hotel_groups = self._group_tours_by_hotel(filtered_tours, params.sort_order)

        return SearchResponse(
            total_tours=len(filtered_tours),
            total_hotels=len(hotel_groups),
            operators_queried=[c.name for c in connectors_to_run],
            operators_successful=successful_ops,
            hotels=hotel_groups
        )

    async def _safe_connector_search(self, connector: BaseTourConnector, params: SearchParams) -> List[TourItem]:
        try:
            return await connector.search(params)
        except Exception as e:
            logger.error(f"Ошибка в коннекторе {connector.name}: {e}")
            return []

    def _resolve_hotel_image(self, hotel_name: str, resort: str) -> str:
        h = hotel_name.lower()
        r = resort.lower() if resort else ""
        if "rixos" in h:
            return "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=600&q=80"
        if "atlantis" in h:
            return "https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?auto=format&fit=crop&w=600&q=80"
        if "hilton" in h:
            return "https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=600&q=80"
        if "marriott" in h:
            return "https://images.unsplash.com/photo-1551882547-ff40c63fe5fa?auto=format&fit=crop&w=600&q=80"
        if "albatros" in h:
            return "https://images.unsplash.com/photo-1571003123894-1f0594d2b5d9?auto=format&fit=crop&w=600&q=80"
        if "radisson" in h:
            return "https://images.unsplash.com/photo-1571896349842-33c89424de2d?auto=format&fit=crop&w=600&q=80"
        if "sheraton" in h or "le meridien" in h:
            return "https://images.unsplash.com/photo-1520250497591-112f2f40a3f4?auto=format&fit=crop&w=600&q=80"
        if "дубай" in r or "dubai" in r or "оаэ" in r:
            return "https://images.unsplash.com/photo-1512453979798-5ea266f8880c?auto=format&fit=crop&w=600&q=80"
        if "шарм" in r or "хургада" in r or "египет" in r:
            return "https://images.unsplash.com/photo-1539650116574-8efeb43e2750?auto=format&fit=crop&w=600&q=80"
        if "анталья" in r or "бодрум" in r or "турция" in r:
            return "https://images.unsplash.com/photo-1527838832700-5059252407fa?auto=format&fit=crop&w=600&q=80"
        if "мальдивы" in r or "maldives" in r:
            return "https://images.unsplash.com/photo-1514282401047-d79a71a590e8?auto=format&fit=crop&w=600&q=80"
        if "пхукет" in r or "паттайя" in r or "таиланд" in r:
            return "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=600&q=80"
        return "https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=600&q=80"

    def _group_tours_by_hotel(self, tours: List[TourItem], sort_order: str = "price_asc") -> List[HotelGroup]:
        groups: Dict[str, List[TourItem]] = {}

        for tour in tours:
            name_norm = tour.hotel_name.strip()
            key = name_norm.lower()
            key = key.replace(" hotel", "").replace(" resort", "").replace(" spa", "").strip()

            if key not in groups:
                groups[key] = []
            groups[key].append(tour)

        result_groups: List[HotelGroup] = []
        for _, items in groups.items():
            reverse_sort = (sort_order == "price_desc")
            items_sorted = sorted(items, key=lambda x: x.price, reverse=reverse_sort)
            
            prices = [x.price for x in items_sorted]
            min_p = min(prices)
            max_p = max(prices)

            first = items_sorted[0]
            hotel_img = self._resolve_hotel_image(first.hotel_name, first.resort)
            group = HotelGroup(
                hotel_name=first.hotel_name,
                hotel_stars=first.hotel_stars,
                resort=first.resort,
                min_price=min_p,
                max_price=max_p,
                currency=first.currency,
                variants_count=len(items_sorted),
                image_url=hotel_img,
                tours=items_sorted
            )
            result_groups.append(group)

        if sort_order == "price_desc":
            result_groups.sort(key=lambda x: x.max_price, reverse=True)
        else:
            result_groups.sort(key=lambda x: x.min_price)

        return result_groups
