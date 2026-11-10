from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class SearchParams(BaseModel):
    city_from: str = Field(default="Ташкент", description="Город вылета (Ташкент, Самарканд и др.)")
    country: str = Field(default="ОАЭ", description="Страна назначения")
    selected_operator: Optional[str] = Field(default="all", description="Конкретный туроператор (all, kompas, easybooking, etc.)")
    hotel_query: Optional[str] = Field(default=None, description="Поиск по названию отеля (Rixos, Albatros и др.)")
    checkin_from: str = Field(..., description="Дата заезда С (DD.MM.YYYY)")
    checkin_to: str = Field(..., description="Дата заезда ПО (DD.MM.YYYY)")
    nights_from: int = Field(default=7, ge=1, le=30)
    nights_to: int = Field(default=7, ge=1, le=30)
    adults: int = Field(default=2, ge=1, le=6)
    children: int = Field(default=0, ge=0, le=4)
    child_ages: List[int] = Field(default=[], description="Возраста детей (например [6] или [4, 9])")
    currency: str = Field(default="USD", description="USD, EUR, UZS")
    only_available_flights: bool = Field(default=False, description="Только с местами на рейсы")
    meal_filter: Optional[str] = Field(default=None, description="UAI, AI, BB, HB, FB, RO")
    stars_filter: Optional[str] = Field(default=None, description="5*, 4*, 3*")
    sort_order: str = Field(default="price_asc", description="price_asc или price_desc")
    operators: Optional[List[str]] = Field(default=None, description="Список выбранных операторов")

class TourItem(BaseModel):
    operator_id: str
    operator_name: str
    tour_name: str
    checkin: str
    departure_time: Optional[str] = ""
    day_of_week: Optional[str] = ""
    nights: str
    hotel_name: str
    hotel_stars: str
    resort: str
    meal_type: str
    room_type: str
    price: float
    currency: str
    price_formatted: str
    booking_url: str
    flight_info: Optional[str] = "Включен (прямой рейс)"
    flight_to_status: Optional[str] = "Y"
    flight_back_status: Optional[str] = "Y"
    is_available: bool = True
    is_red_row: bool = False
    image_url: Optional[str] = None

class HotelGroup(BaseModel):
    hotel_name: str
    hotel_stars: str
    resort: str
    min_price: float
    max_price: float
    currency: str
    variants_count: int
    image_url: Optional[str] = None
    tours: List[TourItem]

class SearchResponse(BaseModel):
    total_tours: int
    total_hotels: int
    operators_queried: List[str]
    operators_successful: List[str]
    hotels: List[HotelGroup]

class BookingRequest(BaseModel):
    client_name: str
    phone: str
    telegram: Optional[str] = None
    hotel_name: str
    hotel_stars: Optional[str] = None
    resort: Optional[str] = None
    checkin: str
    nights: str
    meal_type: str
    room_type: str
    price: float
    currency: str = "USD"
    operator_name: Optional[str] = None
    notes: Optional[str] = None

class BookingResponse(BaseModel):
    success: bool
    message: str
    booking_id: str

class LoginRequest(BaseModel):
    login: str
    password: str

class UserCreateRequest(BaseModel):
    agency_name: str
    manager_name: Optional[str] = ""
    login: str
    password: str
    phone: Optional[str] = ""
    telegram: Optional[str] = ""
    role: str = "user"
    subscription_plan: str = "monthly"
    price_paid: float = 0.0
    notes: Optional[str] = ""

class UserUpdateRequest(BaseModel):
    agency_name: Optional[str] = None
    manager_name: Optional[str] = None
    password: Optional[str] = None
    phone: Optional[str] = None
    telegram: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    subscription_plan: Optional[str] = None
    extend_days: Optional[int] = None
    price_paid: Optional[float] = None
    notes: Optional[str] = None
