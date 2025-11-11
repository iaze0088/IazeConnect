#!/usr/bin/env python3
"""
WebSocket Ping/Pong Test - Specific test for WebSocket functionality
"""

import asyncio
import websockets
import json
import uuid

async def test_websocket_ping_pong():
    """Test WebSocket ping/pong functionality"""
    try:
        # Generate test IDs
        test_user_id = "test_user_" + str(uuid.uuid4())[:8]
        test_session_id = "test_session_" + str(uuid.uuid4())[:8]
        
        # WebSocket URL
        ws_url = f"wss://suporte.help/api/ws/{test_user_id}/{test_session_id}"
        
        print(f"🔌 Conectando ao WebSocket: {ws_url}")
        
        async with websockets.connect(ws_url) as websocket:
            print("✅ Conexão WebSocket estabelecida")
            
            # Send PING
            ping_message = {"type": "ping"}
            await websocket.send(json.dumps(ping_message))
            print("📤 PING enviado")
            
            # Wait for PONG with timeout
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                response_data = json.loads(response)
                
                print(f"📥 Resposta recebida: {response_data}")
                
                if response_data.get("type") == "pong":
                    print("✅ PONG recebido corretamente!")
                    return True
                else:
                    print(f"❌ Resposta inesperada: {response_data}")
                    return False
                    
            except asyncio.TimeoutError:
                print("❌ Timeout - PONG não recebido em 5 segundos")
                return False
                
    except Exception as e:
        print(f"❌ Erro na conexão WebSocket: {e}")
        return False

async def main():
    print("🧪 TESTE WEBSOCKET PING/PONG")
    print("=" * 50)
    
    success = await test_websocket_ping_pong()
    
    print("=" * 50)
    if success:
        print("🎉 TESTE PASSOU: WebSocket ping/pong funcionando!")
    else:
        print("💥 TESTE FALHOU: WebSocket ping/pong não funcionando")

if __name__ == "__main__":
    asyncio.run(main())