"""
Script para testar atualização de nomes de clientes
"""
import asyncio
import httpx

BACKEND_URL = "http://localhost:8001"

async def main():
    async with httpx.AsyncClient(timeout=300.0) as client:
        print("=" * 60)
        print("🔍 TESTANDO SISTEMA DE ATUALIZAÇÃO DE NOMES")
        print("=" * 60)
        
        # 1. Verificar status atual
        print("\n📊 1. Verificando status atual...")
        response = await client.get(f"{BACKEND_URL}/api/client-names/status")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status obtido com sucesso!")
            print(f"\n📈 USERS:")
            print(f"   Total: {data['users']['total']}")
            print(f"   Com nome: {data['users']['with_name']}")
            print(f"   Sem nome: {data['users']['without_name']}")
            print(f"   Completo: {data['users']['percentage_complete']}%")
            
            print(f"\n📈 CLIENTS:")
            print(f"   Total: {data['clients']['total']}")
            print(f"   Com nome: {data['clients']['with_name']}")
            print(f"   Sem nome: {data['clients']['without_name']}")
            print(f"   Completo: {data['clients']['percentage_complete']}%")
            
            print(f"\n📈 TOTAL GERAL:")
            print(f"   Todos: {data['total']['all_clients']}")
            print(f"   Com nome: {data['total']['with_name']}")
            print(f"   Sem nome: {data['total']['without_name']}")
        else:
            print(f"❌ Erro ao verificar status: {response.status_code}")
            return
        
        # 2. Perguntar se quer atualizar
        if data['total']['without_name'] == 0:
            print("\n✅ Todos os clientes já têm nome! Nada a fazer.")
            return
        
        print(f"\n🤔 Deseja atualizar {data['total']['without_name']} clientes sem nome?")
        resposta = input("   Digite 'sim' para confirmar: ")
        
        if resposta.lower() != 'sim':
            print("❌ Operação cancelada")
            return
        
        # 3. Iniciar atualização
        print(f"\n🚀 3. Iniciando atualização em background...")
        response = await client.post(f"{BACKEND_URL}/api/client-names/update-all")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ {data['message']}")
            print(f"   Users: {data['total_users']}")
            print(f"   Clients: {data['total_clients']}")
            print(f"   Total: {data['total']}")
            print(f"\n⏳ Aguarde alguns minutos e verifique o status novamente...")
        else:
            print(f"❌ Erro ao iniciar atualização: {response.status_code}")
            print(response.text)

if __name__ == "__main__":
    asyncio.run(main())
