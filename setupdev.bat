@echo off
echo =================================================
echo   ProctorAI Setup Script — aumne.ai Internship
echo =================================================
echo.

:: ─── Backend Setup ──────────────────────────────────────────────────────────
echo [1/4] Setting up Python virtual environment...
cd backend
python -m venv env
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.10+
    pause
    exit /b 1
)

echo [2/4] Installing backend dependencies...
call env\Scripts\activate
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: pip install failed. Check requirements.txt
    pause
    exit /b 1
)

echo [3/4] Running database migrations...
alembic upgrade head
if errorlevel 1 (
    echo ERROR: Alembic migration failed.
    pause
    exit /b 1
)

echo [3b] Seeding initial test data...
sqlite3 proctoring.db < seed_data.sql 2>nul || echo (sqlite3 not in PATH — skipping seed, data will be empty)

cd ..

:: ─── Frontend Setup ─────────────────────────────────────────────────────────
echo [4/4] Installing frontend dependencies...
cd frontend
npm install
if errorlevel 1 (
    echo ERROR: npm install failed. Is Node.js installed?
    pause
    exit /b 1
)
cd ..

echo.
echo =================================================
echo   Setup complete! Run runapplication.bat to start
echo =================================================
pause
