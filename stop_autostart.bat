@echo off
chcp 65001 >nul
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "PDDAgent" /f >nul 2>&1
echo 已取消开机自启
pause
