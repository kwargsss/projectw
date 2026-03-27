@echo off
chcp 65001 > nul
echo ===================================================
echo   Запуск проекта: Discord Бот + Веб-панель
echo ===================================================

cd /d "%~dp0"

echo [1/3] Запускаем FastAPI Бэкенд...
start "FastAPI Backend" cmd /k "cd backend && uvicorn main:app --reload --port 8000"

echo [2/3] Запускаем Discord Бота...
start "Discord Bot" cmd /k "cd bot && python main.py"

echo [3/3] Запускаем Vue Фронтенд...
start "Vue Frontend" cmd /k "cd frontend && npm run dev"

echo ===================================================
echo Все компоненты запущены в новых окнах!
echo.
echo Бэкенд доступен на:  http://localhost:8000
echo Фронтенд доступен на: http://localhost:5173
echo ===================================================
echo Нажми любую клавишу, чтобы закрыть это главное окно...
pause > nul