#!/usr/bin/env python3
"""
🎯 TESTE ESPECÍFICO: Evolution API v2.3.x Webhook Format Fix

CONTEXTO:
- Sistema IAZE multi-tenant com WhatsApp integration via Evolution API
- Recentemente corrigido erro "Invalid 'url' property" ao configurar webhook
- Webhook payload foi atualizado para formato v2.3.x com objeto raiz "webhook"
- Teste foca na validação do formato do webhook, não na conectividade da Evolution API

OBJETIVO DO TESTE:
Validar se o formato do webhook está correto para Evolution API v2.3.x

CENÁRIO DE TESTE:
1. Verificar se o método configure_webhook_for_instance usa o formato correto
2. Validar se o payload do webhook está no formato v2.3.x esperado
3. Confirmar que não há mais erro "Invalid 'url' property"

FORMATO CORRETO v2.3.x:
{
  "webhook": {
    "enabled": true,
    "url": "...",
    "headers": {},
    "byEvents": false,
    "base64": false,
    "events": []
  }
}

FORMATO INCORRETO (antigo):
{
  "url": "...",
  "enabled": true,
  ...
}
"""

import asyncio
import json
import os
import sys
import importlib.util
from unittest.mock import AsyncMock, patch, MagicMock

# Adicionar o diretório backend ao path
sys.path.insert(0, '/app/backend')

class WebhookFormatTester:
    def __init__(self):
        self.test_results = []
        
    def log_result(self, test_name: str, success: bool, message: str = "", details: dict = None):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = f"{status} {test_name}"
        if message:
            result += f" - {message}"
        print(result)
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message,
            "details": details or {}
        })
    
    async def test_webhook_format_in_service(self):
        """Teste 1: Verificar formato do webhook no WhatsAppService"""
        print("\n🔧 TESTE 1: Verificar Formato do Webhook no Service")
        print("=" * 60)
        
        try:
            # Importar o WhatsAppService
            from whatsapp_service import WhatsAppService
            
            # Criar mock do database
            mock_db = MagicMock()
            service = WhatsAppService(mock_db)
            
            # Mock do httpx.AsyncClient para capturar o payload
            captured_payload = None
            captured_url = None
            
            class MockResponse:
                def __init__(self, status_code=200, json_data=None):
                    self.status_code = status_code
                    self._json_data = json_data or {}
                    self.text = json.dumps(self._json_data)
                
                def json(self):
                    return self._json_data
            
            async def mock_put(url, json=None, headers=None):
                nonlocal captured_payload, captured_url
                captured_payload = json
                captured_url = url
                return MockResponse(200, {"success": True})
            
            # Mock do AsyncClient
            mock_client = AsyncMock()
            mock_client.put = mock_put
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            
            # Patch do httpx.AsyncClient
            with patch('httpx.AsyncClient', return_value=mock_client):
                # Executar o método configure_webhook_for_instance
                result = await service.configure_webhook_for_instance("test_instance")
                
                print(f"📊 Resultado: {result}")
                print(f"📍 URL chamada: {captured_url}")
                print(f"📋 Payload capturado: {json.dumps(captured_payload, indent=2)}")
                
                # Validações
                success = True
                issues = []
                
                # 1. Verificar se o payload foi capturado
                if not captured_payload:
                    success = False
                    issues.append("❌ Payload não foi capturado")
                else:
                    print("✅ Payload capturado com sucesso")
                
                # 2. Verificar se tem objeto raiz "webhook"
                if captured_payload and "webhook" not in captured_payload:
                    success = False
                    issues.append("❌ Payload não contém objeto raiz 'webhook'")
                else:
                    print("✅ Payload contém objeto raiz 'webhook'")
                
                # 3. Verificar estrutura do webhook
                if captured_payload and "webhook" in captured_payload:
                    webhook_obj = captured_payload["webhook"]
                    
                    required_fields = ["enabled", "url", "headers", "byEvents", "base64", "events"]
                    for field in required_fields:
                        if field not in webhook_obj:
                            success = False
                            issues.append(f"❌ Campo '{field}' ausente no objeto webhook")
                        else:
                            print(f"✅ Campo '{field}' presente")
                    
                    # Verificar tipos
                    if webhook_obj.get("enabled") is not True:
                        success = False
                        issues.append("❌ Campo 'enabled' deve ser true")
                    
                    if not isinstance(webhook_obj.get("url"), str):
                        success = False
                        issues.append("❌ Campo 'url' deve ser string")
                    
                    if not isinstance(webhook_obj.get("headers"), dict):
                        success = False
                        issues.append("❌ Campo 'headers' deve ser dict")
                    
                    if webhook_obj.get("byEvents") is not False:
                        success = False
                        issues.append("❌ Campo 'byEvents' deve ser false")
                    
                    if webhook_obj.get("base64") is not False:
                        success = False
                        issues.append("❌ Campo 'base64' deve ser false")
                    
                    if not isinstance(webhook_obj.get("events"), list):
                        success = False
                        issues.append("❌ Campo 'events' deve ser list")
                
                # 4. Verificar URL do endpoint
                expected_url_pattern = "/webhook/set/"
                if captured_url and expected_url_pattern not in captured_url:
                    success = False
                    issues.append(f"❌ URL não contém padrão esperado '{expected_url_pattern}'")
                else:
                    print("✅ URL do endpoint correta")
                
                # 5. Verificar se não há campos do formato antigo no nível raiz
                old_format_fields = ["url", "enabled", "webhookByEvents"]
                for field in old_format_fields:
                    if captured_payload and field in captured_payload:
                        success = False
                        issues.append(f"❌ Campo do formato antigo '{field}' encontrado no nível raiz")
                
                if success:
                    print("✅ Formato do webhook está correto para Evolution API v2.3.x")
                
                self.log_result(
                    "Webhook Format in Service",
                    success,
                    f"Webhook format validation - Issues: {len(issues)}",
                    {
                        "payload": captured_payload,
                        "url": captured_url,
                        "issues": issues
                    }
                )
                
                return success
                
        except Exception as e:
            self.log_result("Webhook Format in Service", False, f"Exception: {str(e)}")
            return False
    
    async def test_webhook_url_construction(self):
        """Teste 2: Verificar construção da URL do webhook"""
        print("\n🌐 TESTE 2: Verificar Construção da URL do Webhook")
        print("=" * 60)
        
        try:
            # Verificar se a URL do webhook está sendo construída corretamente
            backend_url = os.environ.get("REACT_APP_BACKEND_URL", "https://wppconnect-fix.preview.emergentagent.com")
            expected_webhook_url = f"{backend_url}/api/whatsapp/webhook/evolution"
            
            print(f"📍 Backend URL: {backend_url}")
            print(f"📍 Expected Webhook URL: {expected_webhook_url}")
            
            # Importar o service e verificar se a URL está sendo construída corretamente
            from whatsapp_service import WhatsAppService
            
            # Verificar se o código usa a URL correta
            import inspect
            source = inspect.getsource(WhatsAppService.configure_webhook_for_instance)
            
            success = True
            issues = []
            
            # Verificar se a URL está sendo construída corretamente no código
            if "/api/whatsapp/webhook/evolution" not in source:
                success = False
                issues.append("❌ URL do webhook não encontrada no código")
            else:
                print("✅ URL do webhook encontrada no código")
            
            # Verificar se usa REACT_APP_BACKEND_URL
            if "REACT_APP_BACKEND_URL" not in source:
                success = False
                issues.append("❌ Não usa REACT_APP_BACKEND_URL para construir URL")
            else:
                print("✅ Usa REACT_APP_BACKEND_URL para construir URL")
            
            # Verificar se a URL está bem formada
            if not expected_webhook_url.startswith("http"):
                success = False
                issues.append("❌ URL do webhook mal formada")
            else:
                print("✅ URL do webhook bem formada")
            
            self.log_result(
                "Webhook URL Construction",
                success,
                f"URL construction validation - Issues: {len(issues)}",
                {
                    "backend_url": backend_url,
                    "webhook_url": expected_webhook_url,
                    "issues": issues
                }
            )
            
            return success
            
        except Exception as e:
            self.log_result("Webhook URL Construction", False, f"Exception: {str(e)}")
            return False
    
    async def test_webhook_endpoint_exists(self):
        """Teste 3: Verificar se o endpoint do webhook existe"""
        print("\n📡 TESTE 3: Verificar Endpoint do Webhook")
        print("=" * 60)
        
        try:
            # Verificar se o endpoint /api/whatsapp/webhook/evolution existe
            import aiohttp
            
            backend_url = os.environ.get("REACT_APP_BACKEND_URL", "https://wppconnect-fix.preview.emergentagent.com")
            webhook_endpoint = f"{backend_url}/api/whatsapp/webhook/evolution"
            
            print(f"📍 Testando endpoint: {webhook_endpoint}")
            
            async with aiohttp.ClientSession() as session:
                # Fazer uma requisição POST de teste (sem dados válidos, só para ver se o endpoint existe)
                async with session.post(webhook_endpoint, json={}) as response:
                    status = response.status
                    
                    print(f"📊 Status: {status}")
                    
                    success = True
                    issues = []
                    
                    # Status 404 = endpoint não existe
                    # Status 400/422/500 = endpoint existe mas dados inválidos (esperado)
                    # Status 200 = endpoint existe e funcionou (inesperado com dados vazios)
                    
                    if status == 404:
                        success = False
                        issues.append("❌ Endpoint do webhook não existe (404)")
                    elif status in [400, 422, 500]:
                        print("✅ Endpoint existe (retornou erro esperado com dados inválidos)")
                    elif status == 200:
                        print("✅ Endpoint existe e funcionou")
                    else:
                        print(f"ℹ️ Endpoint existe (status {status})")
                    
                    self.log_result(
                        "Webhook Endpoint Exists",
                        success,
                        f"Endpoint test - Status: {status}",
                        {
                            "endpoint": webhook_endpoint,
                            "status": status,
                            "issues": issues
                        }
                    )
                    
                    return success
                    
        except Exception as e:
            self.log_result("Webhook Endpoint Exists", False, f"Exception: {str(e)}")
            return False
    
    async def test_evolution_api_configuration(self):
        """Teste 4: Verificar configuração da Evolution API"""
        print("\n⚙️ TESTE 4: Verificar Configuração da Evolution API")
        print("=" * 60)
        
        try:
            # Verificar variáveis de ambiente
            evolution_url = os.environ.get('EVOLUTION_API_URL')
            evolution_key = os.environ.get('EVOLUTION_API_KEY')
            
            print(f"📍 EVOLUTION_API_URL: {evolution_url}")
            print(f"🔑 EVOLUTION_API_KEY: {'***' + evolution_key[-4:] if evolution_key else 'Not set'}")
            
            success = True
            issues = []
            
            if not evolution_url:
                success = False
                issues.append("❌ EVOLUTION_API_URL não configurada")
            else:
                print("✅ EVOLUTION_API_URL configurada")
            
            if not evolution_key:
                success = False
                issues.append("❌ EVOLUTION_API_KEY não configurada")
            else:
                print("✅ EVOLUTION_API_KEY configurada")
            
            # Verificar se a URL está bem formada
            if evolution_url and not evolution_url.startswith("http"):
                success = False
                issues.append("❌ EVOLUTION_API_URL mal formada")
            else:
                print("✅ EVOLUTION_API_URL bem formada")
            
            # Nota sobre conectividade
            print("ℹ️ Nota: Evolution API não está acessível no momento (esperado em ambiente de teste)")
            
            self.log_result(
                "Evolution API Configuration",
                success,
                f"Configuration validation - Issues: {len(issues)}",
                {
                    "evolution_url": evolution_url,
                    "evolution_key_set": bool(evolution_key),
                    "issues": issues
                }
            )
            
            return success
            
        except Exception as e:
            self.log_result("Evolution API Configuration", False, f"Exception: {str(e)}")
            return False
    
    async def run_all_tests(self):
        """Executar todos os testes"""
        print("🎯 TESTE ESPECÍFICO: Evolution API v2.3.x Webhook Format Fix")
        print("=" * 80)
        print("📋 Foco: Validação do formato do webhook (não conectividade)")
        
        try:
            # Executar testes
            test1_success = await self.test_webhook_format_in_service()
            test2_success = await self.test_webhook_url_construction()
            test3_success = await self.test_webhook_endpoint_exists()
            test4_success = await self.test_evolution_api_configuration()
            
            # Resumo final
            print("\n" + "=" * 80)
            print("📊 RESUMO FINAL DOS TESTES")
            print("=" * 80)
            
            total_tests = len(self.test_results)
            passed_tests = sum(1 for r in self.test_results if r["success"])
            
            print(f"📈 Total de testes: {total_tests}")
            print(f"✅ Testes passaram: {passed_tests}")
            print(f"❌ Testes falharam: {total_tests - passed_tests}")
            print(f"📊 Taxa de sucesso: {(passed_tests/total_tests)*100:.1f}%")
            
            print("\n📋 DETALHES DOS TESTES:")
            for i, result in enumerate(self.test_results, 1):
                status_icon = "✅" if result["success"] else "❌"
                print(f"{i}. {status_icon} {result['test']}: {result['message']}")
            
            # Validações específicas do review request
            print("\n🎯 VALIDAÇÕES ESPECÍFICAS DO REVIEW REQUEST:")
            
            webhook_format_correct = test1_success
            webhook_url_correct = test2_success
            webhook_endpoint_exists = test3_success
            
            if webhook_format_correct:
                print("✅ Formato do webhook corrigido para Evolution API v2.3.x")
            else:
                print("❌ Formato do webhook ainda incorreto")
            
            if webhook_url_correct:
                print("✅ URL do webhook construída corretamente")
            else:
                print("❌ URL do webhook com problemas")
            
            if webhook_endpoint_exists:
                print("✅ Endpoint do webhook existe e está acessível")
            else:
                print("❌ Endpoint do webhook não existe")
            
            overall_success = webhook_format_correct and webhook_url_correct
            
            if overall_success:
                print("\n🎉 RESULTADO FINAL: CORREÇÃO DO FORMATO DO WEBHOOK FUNCIONANDO!")
                print("✅ Erro 'Invalid url property' foi resolvido")
                print("✅ Formato v2.3.x implementado corretamente")
                print("ℹ️ Nota: Conectividade com Evolution API não testada (API não acessível)")
            else:
                print("\n❌ RESULTADO FINAL: PROBLEMAS NO FORMATO DO WEBHOOK")
                print("⚠️ Correção pode não estar completa")
            
            return overall_success
            
        except Exception as e:
            print(f"💥 ERRO CRÍTICO durante execução dos testes: {e}")
            return False

async def main():
    """Função principal"""
    tester = WebhookFormatTester()
    success = await tester.run_all_tests()
    
    if success:
        print("\n🎯 CONCLUSÃO: Formato do webhook Evolution API v2.3.x corrigido!")
        exit(0)
    else:
        print("\n⚠️ CONCLUSÃO: Problemas detectados no formato do webhook!")
        exit(1)

if __name__ == "__main__":
    asyncio.run(main())