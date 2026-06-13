@echo off
chcp 65001 >nul
title PDD Agent Server

echo ==========================================
echo   PDD Agent 服务启动中...
echo ==========================================
echo.

cd /d "%~dp0"

:: Check Python
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] 未找到 Python，请先安装 Python 3.8+
    pause
    exit /b 1
)

:: Check dependencies
echo [1/3] 检查依赖...
python -c "import pandas" >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] 安装 pandas...
    python -m pip install pandas -q
)

:: Start server
echo [2/3] 启动服务...
echo [3/3] 服务已启动!
echo.
echo ==========================================
echo   服务地址:
echo   首页下载: http://127.0.0.1:8765
echo   退货分析: http://127.0.0.1:8765/return_analysis
echo   API状态:  http://127.0.0.1:8765/api/status
echo ==========================================
echo.
echo 按 Ctrl+C 停止服务
echo.

python main.py --port 8765

pause
