#!/usr/bin/env python3
"""Testar ButtonsService"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
import sys
sys.path.append('/app/backend')

from vendas_buttons_service import ButtonsService

async def test():
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.environ.get('DB_NAME', 'support_chat')
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    print("🔌 Conectado ao MongoDB")
    
    buttons_service = ButtonsService(db)
    button_config = await buttons_service.get_config()
    
    print(f"✅ Config carregada:")
    print(f"   Enabled: {button_config.is_enabled}")
    print(f"   Mode: {button_config.mode}")
    print(f"   Buttons: {len(button_config.root_buttons)}")
    
    for btn in button_config.root_buttons:
        print(f"   - {btn.label}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(test())
