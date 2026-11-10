import os
import json
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
import logging
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from app.models import (
    SearchParams, SearchResponse, BookingRequest, BookingResponse,
    LoginRequest, UserCreateRequest, UserUpdateRequest
)
from app.services.aggregator import TourAggregatorService
from app.services.auth import AuthService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("tour-aggregator")

app = FastAPI(
    title="RaDo Travel — Закрытая поисковая B2B-система туроператоров",
    version="2.1.0",
    description="Единая закрытая система поиска туров по туроператорам для турагентств-абонентов RaDo Travel"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

service = TourAggregatorService()
auth_service = AuthService()

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
BOOKINGS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "bookings.json")

if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Зависимость аутентификации
def get_current_user(
    authorization: Optional[str] = Header(default=None),
    x_auth_token: Optional[str] = Header(default=None)
) -> Dict[str, Any]:
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split("Bearer ", 1)[1].strip()
    elif x_auth_token:
        token = x_auth_token.strip()

    if not token:
        raise HTTPException(
            status_code=401,
            detail="Требуется авторизация в RaDo Travel. Пожалуйста, войдите в систему."
        )

    try:
        user = auth_service.verify_token(token)
        return user
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))

def get_current_admin(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    if user.get("role") != "admin":
        raise HTTPException(
            status_code=403,
            detail="Доступ запрещен. Раздел доступен только главному администратору платформы."
        )
    return user

@app.api_route("/", methods=["GET", "HEAD"], response_class=HTMLResponse)
async def index():
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return "<h1>RaDo Travel API активен</h1>"

# --- ЭНДПОИНТЫ АВТОРИЗАЦИИ ---

@app.post("/api/auth/login")
async def login(req: LoginRequest):
    """Вход в систему турагента или администратора."""
    try:
        result = auth_service.authenticate(req.login, req.password)
        logger.info(f"Успешный вход: {req.login} (Агентство: {result['user']['agency_name']})")
        return result
    except ValueError as e:
        logger.warning(f"Неудачная попытка входа [{req.login}]: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/auth/me")
async def get_me(user: Dict[str, Any] = Depends(get_current_user)):
    """Проверка текущей сессии и статуса подписки."""
    return user

@app.post("/api/auth/logout")
async def logout(
    authorization: Optional[str] = Header(default=None),
    x_auth_token: Optional[str] = Header(default=None)
):
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split("Bearer ", 1)[1].strip()
    elif x_auth_token:
        token = x_auth_token.strip()

    if token:
        auth_service.logout(token)
    return {"success": True, "message": "Вы успешно вышли из системы"}

# --- ЭНДПОИНТЫ АДМИН-ПАНЕЛИ (ТОЛЬКО ДЛЯ АДМИНИСТРАТОРА) ---

@app.get("/api/admin/users")
async def admin_get_users(admin: Dict[str, Any] = Depends(get_current_admin)):
    """Получение списка всех турагентств и статусов подписок."""
    return auth_service.get_all_users()

@app.post("/api/admin/users")
async def admin_create_user(req: UserCreateRequest, admin: Dict[str, Any] = Depends(get_current_admin)):
    """Создание нового турагентства с выбранным тарифом подписки."""
    try:
        new_u = auth_service.create_user(req.dict())
        logger.info(f"Админ создал нового абонента: {req.agency_name} (Логин: {req.login}, Тариф: {req.subscription_plan})")
        return new_u
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/api/admin/users/{user_id}")
async def admin_update_user(user_id: str, req: UserUpdateRequest, admin: Dict[str, Any] = Depends(get_current_admin)):
    """Обновление турагентства (продление подписки, блокировка, смена пароля)."""
    try:
        updated = auth_service.update_user(user_id, req.dict(exclude_unset=True))
        logger.info(f"Админ обновил абонента {user_id}: {req.dict(exclude_unset=True)}")
        return updated
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/api/admin/users/{user_id}")
async def admin_delete_user(user_id: str, admin: Dict[str, Any] = Depends(get_current_admin)):
    """Удаление турагентства."""
    try:
        success = auth_service.delete_user(user_id)
        return {"success": success}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/admin/stats")
async def admin_get_stats(admin: Dict[str, Any] = Depends(get_current_admin)):
    """Статистика подписок и выручки для владельца."""
    return auth_service.get_stats()

# --- ОСНОВНОЙ ФУНКЦИОНАЛ ПОИСКА ТУРОВ (ЗАЩИЩЕН АВТОРИЗАЦИЕЙ) ---

@app.api_route("/api/operators", methods=["GET", "HEAD"])
async def get_operators():
    """Возвращает список подключенных туроператоров."""
    return service.get_registered_operators()

@app.post("/api/search", response_model=SearchResponse)
async def search_tours(
    params: SearchParams,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Выполняет параллельный поиск туров по всем операторам.
    Доступно ТОЛЬКО авторизованным турагентам с активной подпиской.
    """
    try:
        logger.info(f"Запрос поиска от [{user['agency_name']} / {user['login']}]: {params.country} из {params.city_from}")
        return await service.search_all(params)
    except Exception as e:
        logger.error(f"Search endpoint error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/booking-request", response_model=BookingResponse)
async def create_booking_request(req: BookingRequest):
    """
    Прием заявки на бронирование выбранного тура.
    """
    booking_id = f"TR-{uuid.uuid4().hex[:6].upper()}"
    record = req.dict()
    record["booking_id"] = booking_id
    record["created_at"] = datetime.now().isoformat()

    logger.info(f"Новая заявка на бронирование [{booking_id}]: {req.client_name} ({req.phone}) -> {req.hotel_name} (${req.price})")

    try:
        existing = []
        if os.path.exists(BOOKINGS_FILE):
            with open(BOOKINGS_FILE, "r", encoding="utf-8") as f:
                try:
                    existing = json.load(f)
                except Exception:
                    existing = []
        existing.append(record)
        with open(BOOKINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Ошибка сохранения заявки в файл: {e}")

    return BookingResponse(
        success=True,
        message=f"Спасибо, {req.client_name}! Ваша заявка #{booking_id} принята. Менеджер свяжется с вами в течение 10 минут для оформления брони.",
        booking_id=booking_id
    )

@app.get("/api/bookings")
async def get_bookings(user: Dict[str, Any] = Depends(get_current_user)):
    """Просмотр списка поступивших клиентских заявок (только для авторизованных)."""
    if os.path.exists(BOOKINGS_FILE):
        with open(BOOKINGS_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except Exception:
                return []
    return []

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
