import asyncio
from app.models import SearchParams
from app.services.aggregator import TourAggregatorService

async def main():
    service = TourAggregatorService()
    
    # Тест поиска Rixos в Египте (в точности как на скриншотах)
    params = SearchParams(
        city_from="Ташкент",
        country="Египет",
        hotel_query="rixos",
        checkin_from="12.11.2026",
        checkin_to="26.11.2026",
        nights_from=7,
        nights_to=7,
        adults=2,
        children=0,
        currency="USD",
        only_available_flights=False
    )
    
    print("Запуск поиска Rixos в Египте:")
    resp = await service.search_all(params)
    print(f"Всего найдено туров: {resp.total_tours}, отелей: {resp.total_hotels}")
    print(f"Операторы: {resp.operators_successful}")
    
    for h in resp.hotels[:3]:
        print(f"\n[ОТЕЛЬ] {h.hotel_name} ({h.hotel_stars}, курорт: {h.resort}) - от ${h.min_price} ({h.variants_count} вылетов)")
        for t in h.tours[:3]:
            status = "НЕТ МЕСТ" if t.is_red_row else "ЕСТЬ МЕСТА"
            print(f"   * [{t.checkin} {t.departure_time}] | {t.meal_type} | {t.room_type} | ${t.price} | {status}")

if __name__ == "__main__":
    asyncio.run(main())
