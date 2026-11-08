import os
import json
import uuid
from datetime import datetime
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from app.models import SearchParams, SearchResponse, BookingRequest, BookingResponse
from app.services.aggregator import TourAggregatorService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("tour-aggregator")

app = FastAPI(
    title="TourHub Uzbekistan — Поиск и онлайн-бронирование туров",
    version="2.0.0",
    description="Единая поисковая система туров по всем надежным туроператорам Узбекистана"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

service = TourAggregatorService()

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
BOOKINGS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "bookings.json")

if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/", response_class=HTMLResponse)
async def index():
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return "<h1>TourHub API активен</h1>"

@app.get("/api/operators")
async def get_operators():
    """Возвращает список подключенных туроператоров."""
    return service.get_registered_operators()

@app.post("/api/search", response_model=SearchResponse)
async def search_tours(params: SearchParams):
    """
    Выполняет параллельный поиск туров по всем операторам,
    группирует по отелям и возвращает со сравнением цен.
    """
    try:
        return await service.search_all(params)
    except Exception as e:
        logger.error(f"Search endpoint error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/booking-request", response_model=BookingResponse)
async def create_booking_request(req: BookingRequest):
    """
    B2C: Прием заявки от туриста на бронирование выбранного тура.
    """
    booking_id = f"TR-{uuid.uuid4().hex[:6].upper()}"
    record = req.dict()
    record["booking_id"] = booking_id
    record["created_at"] = datetime.now().isoformat()

    logger.info(f"Новая заявка на бронирование [{booking_id}]: {req.client_name} ({req.phone}) -> {req.hotel_name} (${req.price})")

    # Сохраняем в bookings.json
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
        message=f"Спасибо, {req.client_name}! Ваша заявка #{booking_id} принята. Наш менеджер свяжется с вами в течение 10 минут для оформления брони.",
        booking_id=booking_id
    )

@app.get("/api/bookings")
async def get_bookings():
    """Просмотр списка поступивших клиентских заявок."""
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
