@echo off
cd /d "%~dp0"
python restaurant_advanced_filter_gui.py
if errorlevel 1 pause
