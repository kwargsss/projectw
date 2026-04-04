@echo off
title Запуск проекта
chcp 65001 > nul

echo =========================================
echo Запуск микросервисов проекта...
echo =========================================

cd /d "%~dp0"

echo [1/4] Запуск сервера Lavalink...
start "Lavalink Server" cmd /k "cd lavalink && title Lavalink && java -jar Lavalink.jar"

timeout /t 5 /nobreak >nul

echo [2/4] Запускаем FastAPI Бэкенд
start "FastAPI Backend" cmd /k "cd backend && uvicorn main:app --reload --port 8000"

echo [3/4] Запускаем Discord Бота
start "Discord Bot" cmd /k "cd bot && python main.py"

echo [4/4] Запускаем Vue Фронтенд
start "Vue Frontend" cmd /k "cd frontend && npm run dev"

echo =========================================
echo Все сервисы успешно запущены!
echo Откроется 4 отдельных окна консоли.
echo =========================================

echo Нажми любую клавишу, чтобы закрыть это главное окно
pause > nul