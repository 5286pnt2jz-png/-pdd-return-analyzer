@echo off
chcp 65001 >nul
title PDD Agent Auto Start

cd /d "%~dp0"

:: Add to startup
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "PDDAgent" /t REG_SZ /d "\"%~dp0start.bat\"" /f >nul 2>&1

echo 已添加开机自启
echo 如需取消，运行 stop_autostart.bat
pause
