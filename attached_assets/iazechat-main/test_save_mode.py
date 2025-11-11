#!/usr/bin/env python3
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os

async def test_save_mode():
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.environ.get('DB_NAME', 'support_chat')
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    print("🔌 Testando salvar modo 'button'...")
    
    # Buscar config atual
    config_doc = await db.config.find_one({"id": "config"})
    print(f"Config atual: {config_doc}")
    
    # Atualizar modo
    mode = "button"
    if config_doc and "button_config" in config_doc:
        button_config = config_doc["button_config"]
        button_config["mode"] = mode
        button_config["is_enabled"] = True
    else:
        button_config = {
            "mode": mode,
            "is_enabled": True,
            "welcome_message": "Olá!",
            "root_buttons": []
        }
    
    result = await db.config.update_one(
        {"id": "config"},
        {
            "$set": {
                "id": "config",
                "button_config": button_config
            }
        },
        upsert=True
    )
    
    print(f"✅ Update result: matched={result.matched_count}, modified={result.modified_count}, upserted={result.upserted_id}")
    
    # Verificar
    config_doc2 = await db.config.find_one({"id": "config"})
    if config_doc2:
        print(f"✅ Mode salvo: {config_doc2.get('button_config', {}).get('mode')}")
    else:
        print("❌ Config não encontrada!")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(test_save_mode())
