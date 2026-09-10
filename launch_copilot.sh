#!/usr/bin/env bash
# -------------------------------------------------------------
# NEURAL COPILOT // LINUX & MACOS RUNTIME BOOTLOADER
# -------------------------------------------------------------

echo "[1/2] Checking and initializing Ollama local daemon..."
if ! command -v ollama &> /dev/null; then
    echo "[!] Ollama is not installed or not in PATH. Visit https://ollama.com to install."
    exit 1
fi

# Check if Ollama server is already running on port 11434
if ! curl -s http://localhost:11434 &> /dev/null; then
    echo "[-] Starting Ollama in background..."
    ollama serve >/dev/null 2>&1 &
    sleep 2
fi

echo "[2/2] Launching Neural Command Core Workspace..."
cd "$(dirname "$0")" || exit
python3 assistant_gui.py
