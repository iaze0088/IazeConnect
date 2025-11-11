#!/bin/bash
export PYTHONUNBUFFERED=1
export MONGO_URL="mongodb://localhost:27017"
export EVOLUTION_API_URL="http://evolution.suporte.help:8080"
export EVOLUTION_API_KEY="iaze-evolution-2025-secure-key"
export DB_NAME="support_chat"

/root/.venv/bin/python /app/backend/whatsapp_polling.py
