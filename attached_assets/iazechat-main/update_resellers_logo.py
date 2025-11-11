"""
Script para atualizar todas as revendas com a foto padrão
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os

MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DEFAULT_LOGO = "https://customer-assets.emergentagent.com/job_535f0fc0-1515-4938-9910-2bc0af524212/artifacts/qwn9iyvo_image.png"

async def update_all_resellers():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client['support_db']
    
    # Atualizar todas as revendas com a foto padrão
    result = await db.resellers.update_many(
        {},
        {"$set": {"client_logo_url": DEFAULT_LOGO}}
    )
    
    print(f"✅ {result.modified_count} revendas atualizadas com a foto padrão!")
    print(f"   Logo: {DEFAULT_LOGO}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(update_all_resellers())
