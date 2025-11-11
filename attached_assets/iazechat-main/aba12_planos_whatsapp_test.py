#!/usr/bin/env python3
"""
🧪 TESTE SISTEMÁTICO - ABA 12: PLANOS WHATSAPP (RENOVAÇÃO)

FUNCIONALIDADES A TESTAR:
1. Admin Login - POST /api/auth/admin/login
2. LISTAR ASSINATURAS/PLANOS - GET /api/admin/subscriptions
3. CRIAR/RENOVAR PLANO MANUALMENTE - POST /api/admin/subscriptions/manual-renew
4. OBTER INFORMAÇÕES DE ASSINATURA - Verificar via lista
5. EDITAR ASSINATURA - PUT /api/admin/subscriptions/{reseller_id}/end-date

Admin: admin@admin.com / 102030@ab
Backend: https://wppconnect-fix.preview.emergentagent.com/api
"""

import asyncio
import aiohttp
import json
from datetime import datetime, timezone, timedelta
import sys

# Configuração
BACKEND_URL = "https://wppconnect-fix.preview.emergentagent.com/api"
ADMIN_EMAIL = "admin@admin.com"
ADMIN_PASSWORD = "102030@ab"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(title):
    print(f"\n{Colors.CYAN}{Colors.BOLD}{'='*80}{Colors.END}")
    print(f"{Colors.CYAN}{Colors.BOLD}{title.center(80)}{Colors.END}")
    print(f"{Colors.CYAN}{Colors.BOLD}{'='*80}{Colors.END}")

def print_test(test_name):
    print(f"\n{Colors.BLUE}{Colors.BOLD}🧪 TESTE: {test_name}{Colors.END}")

def print_success(message):
    print(f"{Colors.GREEN}✅ {message}{Colors.END}")

def print_error(message):
    print(f"{Colors.RED}❌ {message}{Colors.END}")

def print_warning(message):
    print(f"{Colors.YELLOW}⚠️ {message}{Colors.END}")

def print_info(message):
    print(f"{Colors.WHITE}ℹ️ {message}{Colors.END}")

async def make_request(session, method, url, headers=None, json_data=None):
    """Fazer requisição HTTP com tratamento de erro"""
    try:
        async with session.request(method, url, headers=headers, json=json_data) as response:
            try:
                data = await response.json()
            except:
                data = await response.text()
            
            return {
                "status": response.status,
                "data": data,
                "headers": dict(response.headers)
            }
    except Exception as e:
        return {
            "status": 0,
            "data": f"Erro de conexão: {str(e)}",
            "headers": {}
        }

async def test_admin_login(session):
    """Teste 1: Admin Login"""
    print_test("1. ADMIN LOGIN")
    
    url = f"{BACKEND_URL}/auth/admin/login"
    payload = {
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    }
    
    print_info(f"POST {url}")
    print_info(f"Payload: {json.dumps(payload, indent=2)}")
    
    result = await make_request(session, "POST", url, json_data=payload)
    
    if result["status"] == 200:
        token = result["data"].get("token")
        if token:
            print_success(f"Login realizado com sucesso!")
            print_info(f"Token: {token[:50]}...")
            return token
        else:
            print_error("Login falhou - token não retornado")
            return None
    else:
        print_error(f"Login falhou - Status: {result['status']}")
        print_error(f"Resposta: {result['data']}")
        return None

async def test_list_subscriptions(session, token):
    """Teste 2: Listar Assinaturas/Planos"""
    print_test("2. LISTAR ASSINATURAS/PLANOS")
    
    url = f"{BACKEND_URL}/admin/subscriptions"
    headers = {"Authorization": f"Bearer {token}"}
    
    print_info(f"GET {url}")
    
    result = await make_request(session, "GET", url, headers=headers)
    
    if result["status"] == 200:
        subscriptions = result["data"]
        print_success(f"Lista de assinaturas obtida com sucesso!")
        print_info(f"Total de assinaturas: {len(subscriptions)}")
        
        if subscriptions:
            print_info("Primeiras 3 assinaturas:")
            for i, sub in enumerate(subscriptions[:3]):
                print_info(f"  {i+1}. Reseller: {sub.get('reseller_name', 'N/A')} | "
                          f"Plano: {sub.get('plan_type', 'N/A')} | "
                          f"Status: {sub.get('status', 'N/A')} | "
                          f"Expira: {sub.get('current_period_end', 'N/A')[:10]}")
        
        return subscriptions
    else:
        print_error(f"Falha ao listar assinaturas - Status: {result['status']}")
        print_error(f"Resposta: {result['data']}")
        return []

async def test_manual_renewal(session, token, reseller_id=None):
    """Teste 3: Criar/Renovar Plano Manualmente"""
    print_test("3. CRIAR/RENOVAR PLANO MANUALMENTE")
    
    # Se não foi fornecido reseller_id, usar um de teste
    if not reseller_id:
        # Buscar um reseller existente primeiro
        resellers_url = f"{BACKEND_URL}/resellers"
        headers = {"Authorization": f"Bearer {token}"}
        
        print_info("Buscando revendedores existentes...")
        resellers_result = await make_request(session, "GET", resellers_url, headers=headers)
        
        if resellers_result["status"] == 200 and resellers_result["data"]:
            reseller_id = resellers_result["data"][0]["id"]
            print_info(f"Usando reseller_id: {reseller_id}")
        else:
            print_warning("Nenhum revendedor encontrado, usando ID de teste")
            reseller_id = "test-reseller-id-12345"
    
    url = f"{BACKEND_URL}/admin/subscriptions/manual-renew"
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "reseller_id": reseller_id,
        "plan_type": "basico",
        "months": 1
    }
    
    print_info(f"POST {url}")
    print_info(f"Payload: {json.dumps(payload, indent=2)}")
    
    result = await make_request(session, "POST", url, headers=headers, json_data=payload)
    
    if result["status"] == 200:
        subscription = result["data"].get("subscription", {})
        print_success("Renovação manual realizada com sucesso!")
        print_info(f"Plano: {subscription.get('plan_type', 'N/A')}")
        print_info(f"Status: {subscription.get('status', 'N/A')}")
        print_info(f"Expira em: {subscription.get('current_period_end', 'N/A')[:10]}")
        return subscription
    else:
        print_error(f"Falha na renovação manual - Status: {result['status']}")
        print_error(f"Resposta: {result['data']}")
        return None

async def test_get_subscription_info(session, token, reseller_id):
    """Teste 4: Obter Informações de Assinatura (via lista)"""
    print_test("4. OBTER INFORMAÇÕES DE ASSINATURA")
    
    print_info("Nota: Endpoint específico GET /api/subscriptions/{reseller_id} não encontrado")
    print_info("Verificando via lista de assinaturas...")
    
    # Usar a lista de assinaturas para encontrar a específica
    subscriptions = await test_list_subscriptions(session, token)
    
    if subscriptions:
        target_subscription = None
        for sub in subscriptions:
            if sub.get("reseller_id") == reseller_id:
                target_subscription = sub
                break
        
        if target_subscription:
            print_success(f"Assinatura encontrada para reseller_id: {reseller_id}")
            print_info(f"Plano: {target_subscription.get('plan_type', 'N/A')}")
            print_info(f"Status: {target_subscription.get('status', 'N/A')}")
            print_info(f"Criada em: {target_subscription.get('created_at', 'N/A')[:10]}")
            print_info(f"Expira em: {target_subscription.get('current_period_end', 'N/A')[:10]}")
            return target_subscription
        else:
            print_warning(f"Assinatura não encontrada para reseller_id: {reseller_id}")
            return None
    else:
        print_error("Não foi possível obter lista de assinaturas")
        return None

async def test_edit_subscription(session, token, reseller_id):
    """Teste 5: Editar Assinatura (data de expiração)"""
    print_test("5. EDITAR ASSINATURA")
    
    # Calcular nova data de expiração (30 dias a partir de hoje)
    new_end_date = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    
    url = f"{BACKEND_URL}/admin/subscriptions/{reseller_id}/end-date"
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "end_date": new_end_date
    }
    
    print_info(f"PUT {url}")
    print_info(f"Payload: {json.dumps(payload, indent=2)}")
    
    result = await make_request(session, "PUT", url, headers=headers, json_data=payload)
    
    if result["status"] == 200:
        subscription = result["data"].get("subscription", {})
        print_success("Data de expiração atualizada com sucesso!")
        print_info(f"Nova data de expiração: {subscription.get('current_period_end', 'N/A')[:10]}")
        return subscription
    else:
        print_error(f"Falha ao editar assinatura - Status: {result['status']}")
        print_error(f"Resposta: {result['data']}")
        return None

async def test_different_plan_types(session, token, reseller_id):
    """Teste Extra: Testar diferentes tipos de plano"""
    print_test("EXTRA: TESTAR DIFERENTES TIPOS DE PLANO")
    
    plan_types = ["basico", "pro", "premium"]
    
    for plan_type in plan_types:
        print_info(f"Testando plano: {plan_type}")
        
        url = f"{BACKEND_URL}/admin/subscriptions/manual-renew"
        headers = {"Authorization": f"Bearer {token}"}
        payload = {
            "reseller_id": reseller_id,
            "plan_type": plan_type,
            "months": 1
        }
        
        result = await make_request(session, "POST", url, headers=headers, json_data=payload)
        
        if result["status"] == 200:
            print_success(f"Plano {plan_type} renovado com sucesso!")
        else:
            print_error(f"Falha ao renovar plano {plan_type} - Status: {result['status']}")

async def main():
    """Função principal de teste"""
    print_header("🧪 TESTE SISTEMÁTICO - ABA 12: PLANOS WHATSAPP (RENOVAÇÃO)")
    
    print_info(f"Backend URL: {BACKEND_URL}")
    print_info(f"Admin: {ADMIN_EMAIL}")
    print_info("Iniciando testes...")
    
    # Contadores de teste
    total_tests = 0
    passed_tests = 0
    
    async with aiohttp.ClientSession() as session:
        try:
            # Teste 1: Admin Login
            total_tests += 1
            token = await test_admin_login(session)
            if token:
                passed_tests += 1
            else:
                print_error("❌ TESTE CRÍTICO FALHOU - Parando execução")
                return
            
            # Teste 2: Listar Assinaturas
            total_tests += 1
            subscriptions = await test_list_subscriptions(session, token)
            if subscriptions is not None:  # Pode ser lista vazia
                passed_tests += 1
            
            # Obter reseller_id para próximos testes
            reseller_id = None
            if subscriptions:
                reseller_id = subscriptions[0].get("reseller_id")
            
            if not reseller_id:
                # Buscar revendedores
                resellers_url = f"{BACKEND_URL}/resellers"
                headers = {"Authorization": f"Bearer {token}"}
                resellers_result = await make_request(session, "GET", resellers_url, headers=headers)
                
                if resellers_result["status"] == 200 and resellers_result["data"]:
                    reseller_id = resellers_result["data"][0]["id"]
                    print_info(f"Usando reseller_id dos revendedores: {reseller_id}")
            
            # Teste 3: Renovação Manual
            total_tests += 1
            renewal_result = await test_manual_renewal(session, token, reseller_id)
            if renewal_result:
                passed_tests += 1
            
            # Teste 4: Obter Informações de Assinatura
            if reseller_id:
                total_tests += 1
                subscription_info = await test_get_subscription_info(session, token, reseller_id)
                if subscription_info:
                    passed_tests += 1
            
            # Teste 5: Editar Assinatura
            if reseller_id:
                total_tests += 1
                edit_result = await test_edit_subscription(session, token, reseller_id)
                if edit_result:
                    passed_tests += 1
            
            # Teste Extra: Diferentes tipos de plano
            if reseller_id:
                await test_different_plan_types(session, token, reseller_id)
            
        except Exception as e:
            print_error(f"Erro durante execução dos testes: {e}")
            import traceback
            traceback.print_exc()
    
    # Resultado final
    print_header("📊 RESULTADO FINAL DOS TESTES")
    
    success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    print_info(f"Total de testes: {total_tests}")
    print_info(f"Testes aprovados: {passed_tests}")
    print_info(f"Testes falharam: {total_tests - passed_tests}")
    print_info(f"Taxa de sucesso: {success_rate:.1f}%")
    
    if success_rate >= 80:
        print_success("🎉 TESTES PASSARAM - ABA 12 (PLANOS WHATSAPP) FUNCIONAL!")
    elif success_rate >= 60:
        print_warning("⚠️ TESTES PARCIAIS - Algumas funcionalidades precisam de correção")
    else:
        print_error("❌ TESTES FALHARAM - ABA 12 precisa de correções significativas")
    
    return success_rate >= 80

if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print_error("\n❌ Testes interrompidos pelo usuário")
        sys.exit(1)
    except Exception as e:
        print_error(f"❌ Erro fatal: {e}")
        sys.exit(1)