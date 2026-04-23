@echo off
echo =================================================
echo   ProctorAI — Starting Application
echo =================================================
echo.

:: ─── Start Backend in a new window ──────────────────────────────────────────
echo [1/2] Starting FastAPI backend on http://localhost:8000 ...
start "ProctorAI Backend" cmd /k "cd backend && call env\Scripts\activate && python main.py"

:: Give the backend a moment to start
timeout /t 3 /nobreak >nul

:: ─── Start Frontend in a new window ─────────────────────────────────────────
echo [2/2] Starting React frontend on http://localhost:3000 ...
start "ProctorAI Frontend" cmd /k "cd frontend && npm start"

echo.
echo =================================================
echo   Application running!
echo   Backend  → http://localhost:8000
echo   Swagger  → http://localhost:8000/docs
echo   Frontend → http://localhost:3000
echo =================================================
echo.
echo Press any key to open the app in your browser...
pause >nul
start http://localhost:3000
