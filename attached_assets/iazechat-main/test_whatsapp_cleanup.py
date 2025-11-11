#!/usr/bin/env python3
"""
Script de teste para validar a limpeza de instâncias WhatsApp
"""
import requests
import json
import time

# Configurações
BACKEND_URL = "https://wppconnect-fix.preview.emergentagent.com/api"
EVOLUTION_API_URL = "http://45.157.157.69:8080"
EVOLUTION_API_KEY = "B4F8E9A2C5D7F1E3A9B6C8D2E5F7A1B3"

# Credenciais de teste
TEST_RESELLER_EMAIL = "fabio@gmail.com"
TEST_RESELLER_PASSWORD = "102030ab"

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def test_login():
    print_section("TESTE 1: Login como Reseller")
    
    response = requests.post(
        f"{BACKEND_URL}/resellers/login",
        json={
            "email": TEST_RESELLER_EMAIL,
            "password": TEST_RESELLER_PASSWORD
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Login bem-sucedido!")
        print(f"   Token: {data['token'][:50]}...")
        print(f"   Reseller ID: {data.get('reseller_id', 'N/A')}")
        return data['token'], data.get('reseller_id')
    else:
        print(f"❌ Erro no login: {response.status_code}")
        print(f"   Response: {response.text}")
        return None, None

def check_evolution_instances():
    print_section("VERIFICAÇÃO: Instâncias na Evolution API")
    
    try:
        response = requests.get(
            f"{EVOLUTION_API_URL}/instance/fetchInstances",
            headers={"apikey": EVOLUTION_API_KEY},
            timeout=10
        )
        
        if response.status_code == 200:
            instances = response.json()
            print(f"✅ Evolution API respondeu")
            print(f"   Total de instâncias: {len(instances)}")
            
            if instances:
                print("\n   Instâncias encontradas:")
                for inst in instances:
                    inst_name = inst.get("instance", {}).get("instanceName", "N/A")
                    inst_status = inst.get("instance", {}).get("status", "N/A")
                    print(f"   - {inst_name} (status: {inst_status})")
            else:
                print("   📝 Nenhuma instância encontrada (limpo)")
            
            return instances
        else:
            print(f"❌ Evolution API erro: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Erro ao acessar Evolution API: {e}")
        return None

def check_db_connections(token):
    print_section("VERIFICAÇÃO: Conexões no Banco de Dados")
    
    response = requests.get(
        f"{BACKEND_URL}/whatsapp/connections",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        connections = response.json()
        print(f"✅ Banco de dados respondeu")
        print(f"   Total de conexões: {len(connections)}")
        
        if connections:
            print("\n   Conexões encontradas:")
            for conn in connections:
                print(f"   - ID: {conn['id']}")
                print(f"     Instance: {conn.get('instance_name', 'N/A')}")
                print(f"     Status: {conn.get('status', 'N/A')}")
                print(f"     Reseller: {conn.get('reseller_id', 'N/A')}")
        else:
            print("   📝 Nenhuma conexão encontrada (limpo)")
        
        return connections
    else:
        print(f"❌ Erro ao buscar conexões: {response.status_code}")
        print(f"   Response: {response.text}")
        return None

def test_cleanup_all(token):
    print_section("TESTE 2: Limpar TODAS as Instâncias")
    
    if not input("\n⚠️  Isso vai DELETAR todas as instâncias. Continuar? (s/n): ").lower().startswith('s'):
        print("❌ Teste cancelado pelo usuário")
        return False
    
    response = requests.post(
        f"{BACKEND_URL}/whatsapp/cleanup-all",
        json={},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Limpeza executada com sucesso!")
        print(f"   Deletadas da Evolution API: {data.get('deleted_from_evolution', 0)}")
        print(f"   Deletadas do banco de dados: {data.get('deleted_from_db', 0)}")
        
        errors = data.get('errors', [])
        if errors:
            print(f"\n   ⚠️ Erros encontrados:")
            for err in errors:
                print(f"   - {err}")
        
        return True
    else:
        print(f"❌ Erro ao limpar: {response.status_code}")
        print(f"   Response: {response.text}")
        return False

def test_create_connection(token, reseller_id):
    print_section("TESTE 3: Criar Nova Conexão")
    
    response = requests.post(
        f"{BACKEND_URL}/whatsapp/connections",
        json={
            "reseller_id": reseller_id,
            "max_received_daily": 200,
            "max_sent_daily": 200
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Conexão criada com sucesso!")
        print(f"   ID: {data.get('id', 'N/A')}")
        print(f"   Instance: {data.get('instance_name', 'N/A')}")
        print(f"   Status: {data.get('status', 'N/A')}")
        return data
    else:
        print(f"❌ Erro ao criar conexão: {response.status_code}")
        print(f"   Response: {response.text}")
        return None

def test_delete_connection(token, connection_id):
    print_section("TESTE 4: Deletar Conexão Individual")
    
    response = requests.delete(
        f"{BACKEND_URL}/whatsapp/connections/{connection_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        print(f"✅ Conexão deletada com sucesso!")
        return True
    else:
        print(f"❌ Erro ao deletar: {response.status_code}")
        print(f"   Response: {response.text}")
        return False

def main():
    print("\n🔧 TESTE DE LIMPEZA DE INSTÂNCIAS WHATSAPP")
    print("=" * 60)
    print("Este script vai testar:")
    print("1. Login como reseller")
    print("2. Verificar instâncias existentes")
    print("3. Limpar todas as instâncias")
    print("4. Criar nova conexão")
    print("5. Deletar conexão criada")
    print("6. Verificar limpeza final")
    print("=" * 60)
    
    # Teste 1: Login
    token, reseller_id = test_login()
    if not token:
        print("\n❌ FALHA: Não foi possível fazer login")
        return
    
    # Verificação inicial
    print("\n📊 ESTADO INICIAL:")
    check_evolution_instances()
    check_db_connections(token)
    
    # Teste 2: Cleanup completo
    if test_cleanup_all(token):
        print("\n⏳ Aguardando 3 segundos para estabilizar...")
        time.sleep(3)
        
        print("\n📊 ESTADO APÓS LIMPEZA:")
        check_evolution_instances()
        check_db_connections(token)
    
    # Teste 3: Criar nova conexão
    print("\n")
    if input("Deseja testar criação de conexão? (s/n): ").lower().startswith('s'):
        connection = test_create_connection(token, reseller_id)
        
        if connection:
            print("\n⏳ Aguardando 2 segundos...")
            time.sleep(2)
            
            print("\n📊 ESTADO APÓS CRIAÇÃO:")
            check_evolution_instances()
            check_db_connections(token)
            
            # Teste 4: Deletar conexão
            print("\n")
            if input("Deseja deletar a conexão criada? (s/n): ").lower().startswith('s'):
                if test_delete_connection(token, connection['id']):
                    print("\n⏳ Aguardando 2 segundos...")
                    time.sleep(2)
                    
                    print("\n📊 ESTADO FINAL:")
                    check_evolution_instances()
                    check_db_connections(token)
    
    print("\n" + "="*60)
    print("  ✅ TESTES CONCLUÍDOS!")
    print("="*60 + "\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Testes interrompidos pelo usuário")
    except Exception as e:
        print(f"\n\n❌ Erro durante os testes: {e}")
        import traceback
        traceback.print_exc()
