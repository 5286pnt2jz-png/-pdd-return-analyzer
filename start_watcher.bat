@echo off
echo ========================================
echo   PDD 工具箱 Watcher 启动器
echo ========================================
echo.
echo 正在启动Watcher服务...
echo 启动后可随时通过扩展启动Agent
echo.
cd /d "%~dp0"
start /b python watcher.py
timeout /t 2 >nul
echo Watcher已启动! 端口: 8766
echo.
echo 按任意键关闭此窗口...
pause >nul
