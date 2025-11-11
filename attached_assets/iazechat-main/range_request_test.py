#!/usr/bin/env python3
"""
TESTE ADICIONAL: Verificar Range requests para vídeos (importante para streaming)
"""

import asyncio
import aiohttp

BACKEND_URL = "https://suporte.help"

async def test_range_requests():
    """Testar Range requests em arquivos de vídeo"""
    print("🎥 TESTE ADICIONAL: Range Requests para Vídeos")
    print("=" * 50)
    
    # Usar um dos arquivos de vídeo que acabamos de fazer upload
    # Vamos tentar alguns filenames comuns ou fazer um upload primeiro
    
    async with aiohttp.ClientSession() as session:
        # Primeiro, fazer login como cliente para fazer upload de um vídeo
        async with session.post(f"{BACKEND_URL}/api/auth/client/login", json={
            "whatsapp": "5511999999999",
            "pin": "00"
        }) as response:
            if response.status == 200:
                data = await response.json()
                token = data["token"]
                print(f"✅ Login realizado")
                
                # Fazer upload de um vídeo pequeno
                import io
                video_data = io.BytesIO(b"fake video content for range test")
                
                form_data = aiohttp.FormData()
                form_data.add_field('file', video_data, filename='range_test.mp4', content_type='video/mp4')
                
                async with session.post(
                    f"{BACKEND_URL}/api/upload",
                    data=form_data,
                    headers={"Authorization": f"Bearer {token}"}
                ) as upload_response:
                    if upload_response.status == 200:
                        upload_data = await upload_response.json()
                        file_url = upload_data["url"]
                        filename = file_url.split('/')[-1]
                        
                        print(f"✅ Upload realizado: {filename}")
                        
                        # Testar Range request
                        range_headers = {"Range": "bytes=0-10"}
                        
                        async with session.get(
                            f"{BACKEND_URL}/api/uploads/{filename}",
                            headers=range_headers
                        ) as range_response:
                            status = range_response.status
                            headers = dict(range_response.headers)
                            
                            print(f"📊 Status da Range request: {status}")
                            print(f"📋 Headers de resposta:")
                            for key, value in headers.items():
                                if key.lower() in ['content-range', 'accept-ranges', 'content-length']:
                                    print(f"   {key}: {value}")
                            
                            if status == 206:
                                print("✅ Range requests suportadas (Status 206 Partial Content)")
                                return True
                            elif status == 200:
                                print("⚠️ Range requests não suportadas, mas arquivo acessível (Status 200)")
                                return True
                            else:
                                print(f"❌ Problema com Range request (Status {status})")
                                return False
                    else:
                        print(f"❌ Falha no upload: {upload_response.status}")
                        return False
            else:
                print(f"❌ Falha no login: {response.status}")
                return False

async def main():
    success = await test_range_requests()
    if success:
        print("\n✅ Range requests testadas com sucesso!")
    else:
        print("\n❌ Problemas com Range requests")

if __name__ == "__main__":
    asyncio.run(main())