"""
SOLUÇÃO ROBUSTA: Sincronização automática WhatsApp
- Limpa conexões órfãs
- Sincroniza instâncias Evolution com banco
- Atualiza status em tempo real
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

async def aggressive_sync():
    """Sincronização AGRESSIVA - Limpa tudo e sincroniza"""
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    print("🔥 INICIANDO SINCRONIZAÇÃO ROBUSTA")
    print("=" * 60)
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as http_client:
            # 1. Buscar instâncias na Evolution API
            response = await http_client.get(
                f"{EVOLUTION_API_URL}/instance/fetchInstances",
                headers={"apikey": EVOLUTION_API_KEY}
            )
            
            if response.status_code != 200:
                print(f"❌ Erro ao buscar instâncias: {response.status_code}")
                return
            
            evolution_instances = response.json()
            evolution_instance_names = set()
            
            print(f"\n📱 Instâncias na Evolution API: {len(evolution_instances)}")
            
            # Mapear instâncias Evolution com seus estados
            evolution_map = {}
            for inst in evolution_instances:
                inst_data = inst.get('instance', {})
                inst_name = inst_data.get('instanceName')
                
                if inst_name:
                    evolution_instance_names.add(inst_name)
                    
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
                    
                    evolution_map[inst_name] = {
                        'status': state,
                        'api_key': inst_data.get('apikey', EVOLUTION_API_KEY)
                    }
                    
                    print(f"   ✅ {inst_name}: {state}")
            
            # 2. Buscar conexões no banco IAZE
            iaze_connections = await db.whatsapp_connections.find({}, {"_id": 0}).to_list(length=100)
            iaze_instance_names = {conn['instance_name'] for conn in iaze_connections}
            
            print(f"\n💾 Conexões no banco IAZE: {len(iaze_connections)}")
            
            # 3. LIMPAR conexões órfãs (que não existem mais na Evolution)
            orphaned = iaze_instance_names - evolution_instance_names
            if orphaned:
                print(f"\n🗑️ Removendo {len(orphaned)} conexão(ões) órfã(s):")
                for inst_name in orphaned:
                    print(f"   🗑️ {inst_name}")
                    await db.whatsapp_connections.delete_many({"instance_name": inst_name})
            
            # 4. ADICIONAR instâncias que existem na Evolution mas não no banco
            missing = evolution_instance_names - iaze_instance_names
            if missing:
                print(f"\n➕ Adicionando {len(missing)} instância(s) faltante(s):")
                for inst_name in missing:
                    evo_data = evolution_map.get(inst_name, {})
                    status = evo_data.get('status', 'disconnected')
                    api_key = evo_data.get('api_key', EVOLUTION_API_KEY)
                    
                    print(f"   ➕ {inst_name} ({status})")
                    
                    new_connection = {
                        "id": str(uuid.uuid4()),
                        "reseller_id": "admin",  # Default
                        "instance_name": inst_name,
                        "phone_number": None,
                        "status": status,
                        "qr_code": None,
                        "api_key": api_key,
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
                        "connected": status == "connected",
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    }
                    
                    await db.whatsapp_connections.insert_one(new_connection)
            
            # 5. ATUALIZAR status das conexões existentes
            updated = 0
            for inst_name in evolution_instance_names & iaze_instance_names:
                evo_data = evolution_map.get(inst_name, {})
                new_status = evo_data.get('status', 'disconnected')
                
                # Buscar status atual no banco
                current = next((c for c in iaze_connections if c['instance_name'] == inst_name), None)
                
                if current and current.get('status') != new_status:
                    print(f"\n🔄 Atualizando {inst_name}: {current.get('status')} → {new_status}")
                    
                    await db.whatsapp_connections.update_one(
                        {"instance_name": inst_name},
                        {
                            "$set": {
                                "status": new_status,
                                "connected": new_status == "connected",
                                "last_activity": datetime.now(timezone.utc).isoformat(),
                                "updated_at": datetime.now(timezone.utc).isoformat()
                            }
                        }
                    )
                    updated += 1
            
            print("\n" + "=" * 60)
            print("✅ SINCRONIZAÇÃO CONCLUÍDA")
            print(f"   🗑️ Removidas: {len(orphaned)}")
            print(f"   ➕ Adicionadas: {len(missing)}")
            print(f"   🔄 Atualizadas: {updated}")
            print("=" * 60)
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(aggressive_sync())
