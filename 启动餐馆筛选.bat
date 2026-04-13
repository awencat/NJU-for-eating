@echo off
cd /d "%~dp0"
python restaurant_filter_gui.py
if errorlevel 1 pause
