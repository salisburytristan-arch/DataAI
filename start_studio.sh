#!/bin/bash

# ArcticCodex Studio - Linux/Mac Startup Script

echo "╔══════════════════════════════════════════════════════╗"
echo "║       ArcticCodex Studio - Full Chat System         ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "[*] Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate venv
echo "[*] Activating virtual environment..."
source venv/bin/activate

# Set environment variables
export PYTHONPATH="$(pwd)"
export AC_EMBEDDINGS=1
export AC_EMBEDDINGS_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Create vault directory
mkdir -p vault

# Check if vault is empty
chunks=$(find vault -type f | wc -l)
if [ "$chunks" -lt 10 ]; then
    echo ""
    echo "[!] Vault appears empty. Seed with documents? (y/n)"
    read -r response
    if [ "$response" = "y" ]; then
        echo "[*] Seeding vault from documents..."
        python run_studio.py seed --vault ./vault
        echo ""
    fi
fi

# Start Studio Server
echo ""
echo "[✓] Starting ArcticCodex Studio Server..."
echo "[*] Vault: $(pwd)/vault"
echo "[*] Chat: http://localhost:8000"
echo "[*] Press Ctrl+C to stop"
echo ""

python -m packages.studio.src.studio_server_fly \
    --host 0.0.0.0 \
    --port 8000 \
    --vault ./vault \
    --embeddings on

echo ""
echo "[*] Studio server stopped"
