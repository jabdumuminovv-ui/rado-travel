@echo off
cd /d "%~dp0"
chcp 65001 > nul
echo ========================================================
echo   TourHub Travel — Агрегатор туров Узбекистана (B2C)
echo   Запуск локального веб-сервера...
echo ========================================================
echo.

if not exist ".venv\Scripts\python.exe" (
    echo [1/2] Создание виртуального окружения...
    python -m venv .venv
    echo [2/2] Установка зависимостей...
    .venv\Scripts\pip install -r requirements.txt
)

echo Сервер запускается по адресу: http://127.0.0.1:8000
echo Для остановки нажмите Ctrl+C.
echo.

.venv\Scripts\uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
pause
