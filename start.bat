@echo off
echo ========================================
echo   A股股票分析 — 启动中...
echo ========================================
echo.
cd /d "%~dp0backend"
python -m uvicorn main:app --host 0.0.0.0 --port 8080
pause
