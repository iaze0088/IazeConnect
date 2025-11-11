"""
Script para sincronizar instâncias da Evolution API com o banco IAZE
"""
import asyncio
import httpx
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
import os
import uuid

EVOLUTION_API_URL = os.environ.get("EVOLUTION_API_URL", "http://evolution.suporte.help:8080")
EVOLUTION_API_KEY = os.environ.get("EVOLUTION_API_KEY", "iaze-evolution-2025-secure-key")
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "support_chat")

async def sync_instances():
    """Sincronizar instâncias da Evolution API com o banco"""
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    print("🔄 Iniciando sincronização de instâncias...")
    print(f"🔗 Evolution API: {EVOLUTION_API_URL}")
    print(f"📊 Banco: {DB_NAME}")
    print()
    
    try:
        # 1. Buscar instâncias na Evolution API
        async with httpx.AsyncClient(timeout=10.0) as http_client:
            response = await http_client.get(
                f"{EVOLUTION_API_URL}/instance/fetchInstances",
                headers={"apikey": EVOLUTION_API_KEY}
            )
            
            if response.status_code != 200:
                print(f"❌ Erro ao buscar instâncias: {response.status_code}")
                return
            
            evolution_instances = response.json()
            print(f"📱 Encontradas {len(evolution_instances)} instância(s) na Evolution API\n")
            
            # 2. Buscar conexões no banco IAZE
            iaze_connections = await db.whatsapp_connections.find({}, {"_id": 0}).to_list(length=100)
            iaze_instance_names = {conn['instance_name'] for conn in iaze_connections}
            
            print(f"💾 Encontradas {len(iaze_connections)} conexão(ões) no banco IAZE\n")
            
            # 3. Sincronizar
            synced = 0
            for inst in evolution_instances:
                inst_data = inst.get('instance', {})
                inst_name = inst_data.get('instanceName')
                inst_status = inst_data.get('status', 'close')
                inst_api_key = inst_data.get('apikey', EVOLUTION_API_KEY)
                
                if not inst_name:
                    continue
                
                # Verificar connectionState
                state_response = await http_client.get(
                    f"{EVOLUTION_API_URL}/instance/connectionState/{inst_name}",
                    headers={"apikey": EVOLUTION_API_KEY}
                )
                
                state = "disconnected"
                if state_response.status_code == 200:
                    state_data = state_response.json()
                    raw_state = state_data.get('instance', {}).get('state', '').lower()
                    if raw_state == 'open':
                        state = "connected"
                    elif raw_state == 'connecting':
                        state = "connecting"
                    else:
                        state = "disconnected"
                
                # Se não existe no banco, criar
                if inst_name not in iaze_instance_names:
                    print(f"➕ Adicionando '{inst_name}' ao banco IAZE...")
                    
                    # Tentar extrair reseller_id do nome da instância
                    # Formato: resellerid_rotation_timestamp
                    parts = inst_name.split('_')
                    reseller_id = parts[0] if len(parts) > 0 else "admin"
                    
                    # Buscar reseller no banco
                    reseller = await db.resellers.find_one({"username": reseller_id}, {"_id": 0})
                    if not reseller:
                        # Usar admin como fallback
                        reseller_id = "admin"
                        print(f"   ⚠️ Reseller não encontrado, usando 'admin'")
                    else:
                        reseller_id = reseller['id']
                    
                    new_connection = {
                        "id": str(uuid.uuid4()),
                        "reseller_id": reseller_id,
                        "instance_name": inst_name,
                        "phone_number": None,
                        "status": state,
                        "qr_code": None,
                        "api_key": inst_api_key,
                        "max_received_daily": 200,
                        "max_sent_daily": 200,
                        "received_today": 0,
                        "sent_today": 0,
                        "last_reset": datetime.now(timezone.utc).isoformat(),
                        "rotation_order": 1,
                        "is_active_for_rotation": True,
                        "created_at": datetime.now(timezone.utc).isoformat(),
                        "last_activity": datetime.now(timezone.utc).isoformat(),
                        "connection_attempts": 0,
                        "connected": state == "connected",
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    }
                    
                    await db.whatsapp_connections.insert_one(new_connection)
                    print(f"   ✅ Adicionada com status: {state}")
                    synced += 1
                
                else:
                    # Atualizar status se mudou
                    existing = next((c for c in iaze_connections if c['instance_name'] == inst_name), None)
                    if existing and existing.get('status') != state:
                        print(f"🔄 Atualizando '{inst_name}': {existing.get('status')} → {state}")
                        await db.whatsapp_connections.update_one(
                            {"instance_name": inst_name},
                            {
                                "$set": {
                                    "status": state,
                                    "connected": state == "connected",
                                    "last_activity": datetime.now(timezone.utc).isoformat(),
                                    "updated_at": datetime.now(timezone.utc).isoformat()
                                }
                            }
                        )
                        synced += 1
            
            print()
            print(f"✅ Sincronização concluída! {synced} alteração(ões)")
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(sync_instances())
