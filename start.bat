@echo off
chcp 65001 >nul
cd /d "%~dp0"
title 考研政治刷题掌上宝

echo 正在启动考研政治刷题掌上宝...
echo.

python run.py
if errorlevel 1 pause
