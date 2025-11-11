#!/usr/bin/env python3
"""
Script de teste para External Storage
Testa upload local e externo (Evolution API)
"""
import asyncio
import aiohttp
import sys
import os
from pathlib import Path
import io

# Adicionar backend ao path
sys.path.insert(0, '/app/backend')

BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'http://localhost:8001')
EXTERNAL_HOST = os.environ.get('EXTERNAL_STORAGE_HOST', '198.96.94.106')
EXTERNAL_PORT = os.environ.get('EXTERNAL_STORAGE_PORT', '9000')

print("=" * 80)
print("🧪 TESTE DE EXTERNAL STORAGE")
print("=" * 80)
print()

async def test_external_health():
    """Testa se servidor Evolution está online"""
    print("1️⃣ TESTANDO SERVIDOR EVOLUTION...")
    print(f"   URL: http://{EXTERNAL_HOST}:{EXTERNAL_PORT}/health")
    
    try:
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(f"http://{EXTERNAL_HOST}:{EXTERNAL_PORT}/health") as response:
                if response.status == 200:
                    text = await response.text()
                    print(f"   ✅ Servidor Evolution ONLINE: {text.strip()}")
                    return True
                else:
                    print(f"   ❌ Servidor retornou status {response.status}")
                    return False
    except Exception as e:
        print(f"   ❌ Servidor Evolution OFFLINE: {e}")
        return False

async def test_local_upload():
    """Testa upload local (via backend)"""
    print()
    print("2️⃣ TESTANDO UPLOAD LOCAL (VIA BACKEND)...")
    print(f"   URL: {BACKEND_URL}/api/upload")
    
    try:
        # Login como admin para obter token
        admin_password = os.environ.get('ADMIN_PASSWORD', '102030@ab')
        timeout = aiohttp.ClientTimeout(total=30)
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            # Login
            login_data = {"email": "admin@sistema.com", "password": admin_password}
            async with session.post(f"{BACKEND_URL}/api/auth/admin/login", json=login_data) as response:
                if response.status != 200:
                    print(f"   ❌ Falha no login: {response.status}")
                    text = await response.text()
                    print(f"      {text}")
                    return False
                
                data = await response.json()
                token = data.get('access_token')
                print(f"   ✅ Login bem sucedido")
            
            # Upload arquivo de teste
            test_content = b"Test file for external storage - LOCAL"
            data = aiohttp.FormData()
            data.add_field('file',
                          test_content,
                          filename='test_local.txt',
                          content_type='text/plain')
            
            headers = {'Authorization': f'Bearer {token}'}
            async with session.post(f"{BACKEND_URL}/api/upload", data=data, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"   ✅ Upload local bem sucedido!")
                    print(f"      Filename: {result.get('filename')}")
                    print(f"      URL: {result.get('url')}")
                    print(f"      Size: {result.get('size')} bytes")
                    print(f"      Kind: {result.get('kind')}")
                    print(f"      External: {result.get('external', False)}")
                    return True
                else:
                    print(f"   ❌ Upload falhou: {response.status}")
                    text = await response.text()
                    print(f"      {text}")
                    return False
    
    except Exception as e:
        print(f"   ❌ Erro no teste de upload local: {e}")
        return False

async def test_external_upload():
    """Testa upload direto para Evolution API"""
    print()
    print("3️⃣ TESTANDO UPLOAD DIRETO PARA EVOLUTION...")
    print(f"   URL: http://{EXTERNAL_HOST}:{EXTERNAL_PORT}/upload")
    
    try:
        test_content = b"Test file for external storage - EXTERNAL"
        data = aiohttp.FormData()
        data.add_field('file',
                      test_content,
                      filename='test_external.txt',
                      content_type='text/plain')
        
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(f"http://{EXTERNAL_HOST}:{EXTERNAL_PORT}/upload", data=data) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"   ✅ Upload externo bem sucedido!")
                    print(f"      Filename: {result.get('filename')}")
                    print(f"      URL: {result.get('url')}")
                    print(f"      Size: {result.get('size')} bytes")
                    
                    # Tentar acessar arquivo
                    file_url = result.get('url')
                    if file_url:
                        print(f"   📥 Testando download do arquivo...")
                        async with session.get(file_url) as dl_response:
                            if dl_response.status == 200:
                                content = await dl_response.read()
                                print(f"      ✅ Arquivo acessível! ({len(content)} bytes)")
                            else:
                                print(f"      ❌ Arquivo não acessível: {dl_response.status}")
                    
                    return True
                else:
                    print(f"   ❌ Upload falhou: {response.status}")
                    text = await response.text()
                    print(f"      {text}")
                    return False
    
    except Exception as e:
        print(f"   ❌ Erro no teste de upload externo: {e}")
        return False

async def test_env_config():
    """Mostra configuração atual"""
    print()
    print("4️⃣ CONFIGURAÇÃO ATUAL...")
    
    use_external = os.environ.get('USE_EXTERNAL_STORAGE', 'false')
    print(f"   USE_EXTERNAL_STORAGE: {use_external}")
    print(f"   EXTERNAL_STORAGE_HOST: {EXTERNAL_HOST}")
    print(f"   EXTERNAL_STORAGE_PORT: {EXTERNAL_PORT}")
    print(f"   BACKEND_URL: {BACKEND_URL}")
    
    if use_external.lower() == 'true':
        print()
        print("   ⚡ MODO EXTERNO ATIVADO")
        print("   Arquivos serão salvos no servidor Evolution (80TB)")
    else:
        print()
        print("   📁 MODO LOCAL ATIVADO")
        print("   Arquivos serão salvos em /data/uploads (fallback)")

async def main():
    """Executa todos os testes"""
    
    # Configuração
    await test_env_config()
    
    # Teste 1: Health check Evolution
    evolution_online = await test_external_health()
    
    # Teste 2: Upload local (sempre funciona)
    local_ok = await test_local_upload()
    
    # Teste 3: Upload externo (só se Evolution estiver online)
    external_ok = False
    if evolution_online:
        external_ok = await test_external_upload()
    else:
        print()
        print("3️⃣ TESTANDO UPLOAD DIRETO PARA EVOLUTION...")
        print("   ⏭️ Pulando (servidor offline)")
    
    # Resumo
    print()
    print("=" * 80)
    print("📊 RESUMO DOS TESTES")
    print("=" * 80)
    print(f"1. Servidor Evolution: {'✅ ONLINE' if evolution_online else '❌ OFFLINE'}")
    print(f"2. Upload Local:       {'✅ OK' if local_ok else '❌ FALHOU'}")
    print(f"3. Upload Externo:     {'✅ OK' if external_ok else '❌ FALHOU / PULADO'}")
    print()
    
    if not evolution_online:
        print("💡 PRÓXIMOS PASSOS:")
        print()
        print("   Para ativar storage externo, execute no servidor Evolution:")
        print()
        print("   1. ssh root@198.96.94.106")
        print("   2. bash < /app/setup_evolution_storage_remote.sh")
        print("   3. Teste: curl http://198.96.94.106:9000/health")
        print()
        print("   Depois edite /app/backend/.env:")
        print("   USE_EXTERNAL_STORAGE=\"true\"")
        print()
        print("   E reinicie o backend:")
        print("   sudo supervisorctl restart backend")
        print()
    elif external_ok:
        print("🎉 TUDO FUNCIONANDO!")
        print()
        print("   Para ativar storage externo permanentemente:")
        print("   1. Edite /app/backend/.env")
        print("   2. USE_EXTERNAL_STORAGE=\"true\"")
        print("   3. sudo supervisorctl restart backend")
        print()
    
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())
