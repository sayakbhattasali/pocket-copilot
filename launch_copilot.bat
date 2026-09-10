@echo off
title POCKET COPILOT // ENGINE BOOT
echo [1/2] Initializing Ollama local runtime...
start "" /B ollama serve >nul 2>&1
timeout /t 2 /nobreak >nul

echo [2/2] Launching Pocket Copilot...
cd /d "%~dp0"
python assistant_gui.py
