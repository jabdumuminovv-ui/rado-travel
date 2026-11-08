from abc import ABC, abstractmethod
from typing import List, Dict
from app.models import SearchParams, TourItem

class BaseTourConnector(ABC):
    def __init__(self, operator_id: str, name: str, base_url: str):
        self.operator_id = operator_id
        self.name = name
        self.base_url = base_url

    @abstractmethod
    async def search(self, params: SearchParams) -> List[TourItem]:
        """Выполняет поиск туров по параметрам и возвращает список найденных предложений."""
        pass

    @abstractmethod
    def is_city_supported(self, city_name: str) -> bool:
        """Проверяет, поддерживается ли город вылета данным оператором."""
        pass
