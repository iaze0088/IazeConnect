#!/usr/bin/env python3
"""
Script de monitoramento forçado de conexões WhatsApp
Monitora o WPPConnect e atualiza o banco diretamente quando detectar conexão
"""

import requests
import time
import sys
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio

# Configurações
WPPCONNECT_URL = "http://151.243.218.223:21465"
MONGODB_URL = "mongodb://localhost:27017/support_chat"
CHECK_INTERVAL = 3  # segundos

async def monitor_connections():
    """Monitora conexões WhatsApp e força atualização"""
    
    # Conectar ao MongoDB
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client.support_chat
    
    print("🔍 MONITOR DE CONEXÕES WHATSAPP ATIVO")
    print("=" * 50)
    print(f"WPPConnect: {WPPCONNECT_URL}")
    print(f"MongoDB: {MONGODB_URL}")
    print(f"Intervalo: {CHECK_INTERVAL}s")
    print("=" * 50)
    print()
    
    iteration = 0
    
    while True:
        try:
            iteration += 1
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            # Buscar todas as conexões do banco
            connections = await db.whatsapp_connections.find({}).to_list(length=100)
            
            if not connections:
                print(f"[{timestamp}] Nenhuma conexão no banco. Aguardando...")
                await asyncio.sleep(CHECK_INTERVAL)
                continue
            
            for conn in connections:
                instance_name = conn.get("instance_name")
                conn_token = conn.get("token")
                conn_id = conn.get("id")
                current_status = conn.get("status", "unknown")
                
                if not instance_name or not conn_token:
                    continue
                
                # Verificar status no WPPConnect
                try:
                    url = f"{WPPCONNECT_URL}/api/{instance_name}:{conn_token}/status-session"
                    response = requests.get(url, timeout=5)
                    
                    if response.status_code == 200:
                        data = response.json()
                        wpp_status = data.get("status", "").upper()
                        
                        print(f"[{timestamp}] {instance_name[:20]:20s} | DB: {current_status:12s} | WPP: {wpp_status:12s}", end="")
                        
                        # Se WPPConnect diz CONNECTED mas banco não está conectado
                        if wpp_status == "CONNECTED" and current_status != "connected":
                            print(" → 🔧 FORÇANDO ATUALIZAÇÃO...")
                            
                            # Atualizar DIRETAMENTE no banco
                            result = await db.whatsapp_connections.update_one(
                                {"id": conn_id},
                                {
                                    "$set": {
                                        "status": "connected",
                                        "connected": True,
                                        "qr_code": None,  # Remover QR code
                                        "updated_at": datetime.utcnow().isoformat()
                                    }
                                }
                            )
                            
                            if result.modified_count > 0:
                                print(f"                                        ✅ CONEXÃO ATIVADA: {instance_name}")
                                print(f"                                        🎉 STATUS ATUALIZADO NO BANCO!")
                                print(f"                                        📱 RECARREGUE O DASHBOARD (F5)")
                            else:
                                print(f"                                        ⚠️  Falha ao atualizar")
                        
                        # Se WPPConnect diz CLOSED mas banco diz conectado
                        elif wpp_status == "CLOSED" and current_status == "connected":
                            print(" → ❌ Desconectado")
                            await db.whatsapp_connections.update_one(
                                {"id": conn_id},
                                {
                                    "$set": {
                                        "status": "disconnected",
                                        "connected": False,
                                        "updated_at": datetime.utcnow().isoformat()
                                    }
                                }
                            )
                        else:
                            print()  # Nova linha
                    
                except requests.exceptions.RequestException as e:
                    print(f"[{timestamp}] {instance_name[:20]:20s} | Erro ao verificar: {str(e)[:30]}")
                
                await asyncio.sleep(0.5)  # Pequeno delay entre conexões
            
            # Linha em branco a cada 10 iterações para facilitar leitura
            if iteration % 10 == 0:
                print()
            
            await asyncio.sleep(CHECK_INTERVAL)
            
        except Exception as e:
            print(f"❌ Erro no monitor: {e}")
            await asyncio.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    print("\n🚀 Iniciando monitor de conexões WhatsApp...")
    print("⚠️  Mantenha este script rodando em background")
    print("⚠️  Pressione CTRL+C para parar\n")
    
    try:
        asyncio.run(monitor_connections())
    except KeyboardInterrupt:
        print("\n\n⏹️  Monitor parado pelo usuário")
        sys.exit(0)
