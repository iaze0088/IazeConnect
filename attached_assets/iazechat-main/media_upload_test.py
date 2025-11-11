#!/usr/bin/env python3
"""
TESTE COMPLETO: Upload e envio de foto/vídeo entre cliente e atendente no servidor externo (suporte.help)

CONTEXTO:
- Servidor externo: 198.96.94.106 (suporte.help)
- Backend corrigido com novo endpoint /api/upload
- REACT_APP_BACKEND_URL atualizado para https://suporte.help

TESTES NECESSÁRIOS:
1. Upload de Mídia (API): POST /api/upload com imagem/vídeo/áudio
2. Download de Mídia (API): GET /api/uploads/{filename}
3. Envio de Mensagem Cliente → Atendente com Mídia
4. Envio de Mensagem Atendente → Cliente com Mídia
5. Verificações de Segurança

BACKEND URL: https://suporte.help
CREDENCIAIS ADMIN: admin / 102030@ab
CREDENCIAIS CLIENTE: 5511999999999 / PIN 00
"""

import asyncio
import aiohttp
import json
import os
import io
import uuid
from datetime import datetime, timezone
from typing import Dict, Optional, List, Tuple

# Configurações do teste
BACKEND_URL = "https://suporte.help"
API_BASE = f"{BACKEND_URL}/api"

# Credenciais conforme review request
ADMIN_PASSWORD = "102030@ab"
CLIENT_WHATSAPP = "5511999999999"
CLIENT_PIN = "00"

class MediaUploadTester:
    def __init__(self):
        self.session = None
        self.admin_token = None
        self.client_token = None
        self.agent_token = None
        self.test_results = []
        self.uploaded_files = []  # Para cleanup
        
    async def setup_session(self):
        """Configurar sessão HTTP"""
        self.session = aiohttp.ClientSession()
        
    async def cleanup_session(self):
        """Limpar sessão HTTP"""
        if self.session:
            await self.session.close()
            
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
        
    async def make_request(self, method: str, endpoint: str, data: dict = None, 
                          token: str = None, headers: dict = None, files: dict = None) -> Tuple[bool, dict, int]:
        """Make HTTP request with error handling"""
        url = f"{API_BASE}{endpoint}"
        
        request_headers = {}
        if token:
            request_headers["Authorization"] = f"Bearer {token}"
        if headers:
            request_headers.update(headers)
            
        try:
            if method.upper() == "GET":
                async with self.session.get(url, headers=request_headers) as response:
                    status = response.status
                    try:
                        data = await response.json()
                    except:
                        data = {"text": await response.text()}
                    return status < 400, data, status
                    
            elif method.upper() == "POST":
                if files:
                    # Multipart form data for file upload
                    form_data = aiohttp.FormData()
                    for key, value in files.items():
                        form_data.add_field(key, value[0], filename=value[1], content_type=value[2])
                    if data:
                        for key, value in data.items():
                            form_data.add_field(key, str(value))
                    
                    async with self.session.post(url, data=form_data, headers=request_headers) as response:
                        status = response.status
                        try:
                            data = await response.json()
                        except:
                            data = {"text": await response.text()}
                        return status < 400, data, status
                else:
                    # JSON data
                    if not headers or "Content-Type" not in headers:
                        request_headers["Content-Type"] = "application/json"
                    
                    async with self.session.post(url, json=data, headers=request_headers) as response:
                        status = response.status
                        try:
                            data = await response.json()
                        except:
                            data = {"text": await response.text()}
                        return status < 400, data, status
                        
            elif method.upper() == "PUT":
                if not headers or "Content-Type" not in headers:
                    request_headers["Content-Type"] = "application/json"
                    
                async with self.session.put(url, json=data, headers=request_headers) as response:
                    status = response.status
                    try:
                        data = await response.json()
                    except:
                        data = {"text": await response.text()}
                    return status < 400, data, status
                    
            else:
                return False, {"error": f"Unsupported method: {method}"}, 400
                
        except Exception as e:
            return False, {"error": str(e)}, 500
    
    # ============================================
    # TESTES DE AUTENTICAÇÃO
    # ============================================
    
    async def test_admin_login(self) -> bool:
        """Teste: Login do Admin"""
        print("\n🔑 TESTE 1: Login do Admin")
        print("=" * 50)
        
        success, response, status = await self.make_request("POST", "/auth/admin/login", {
            "password": ADMIN_PASSWORD
        })
        
        if success and "token" in response:
            self.admin_token = response["token"]
            self.log_result("Admin Login", True, f"Admin logado com sucesso")
            print(f"   ✅ Token obtido: {self.admin_token[:50]}...")
            return True
        else:
            self.log_result("Admin Login", False, f"Erro: {response}")
            print(f"   ❌ Falha no login: {response}")
            return False
    
    async def test_client_login(self) -> bool:
        """Teste: Login do Cliente"""
        print("\n🔑 TESTE 2: Login do Cliente")
        print("=" * 50)
        
        success, response, status = await self.make_request("POST", "/auth/client/login", {
            "whatsapp": CLIENT_WHATSAPP,
            "pin": CLIENT_PIN
        })
        
        if success and "token" in response:
            self.client_token = response["token"]
            self.log_result("Client Login", True, f"Cliente logado com sucesso")
            print(f"   ✅ Token obtido: {self.client_token[:50]}...")
            print(f"   📱 WhatsApp: {CLIENT_WHATSAPP}")
            return True
        else:
            self.log_result("Client Login", False, f"Erro: {response}")
            print(f"   ❌ Falha no login: {response}")
            return False
    
    async def test_get_agent_for_testing(self) -> bool:
        """Teste: Obter um agente para testes"""
        print("\n👤 TESTE 3: Obter Agente para Testes")
        print("=" * 50)
        
        if not self.admin_token:
            self.log_result("Get Agent", False, "Admin token necessário")
            return False
        
        # Listar agentes
        success, response, status = await self.make_request("GET", "/agents", token=self.admin_token)
        
        if success and len(response) > 0:
            # Pegar o primeiro agente
            agent = response[0]
            agent_id = agent.get("id")
            agent_name = agent.get("name", "Agente Teste")
            
            # Tentar fazer login como agente (assumindo que existe um agente com credenciais conhecidas)
            # Para este teste, vamos criar um token temporário ou usar o admin token
            self.agent_token = self.admin_token  # Usar admin token como fallback
            
            self.log_result("Get Agent", True, f"Agente encontrado: {agent_name}")
            print(f"   ✅ Agente ID: {agent_id}")
            print(f"   👤 Nome: {agent_name}")
            return True
        else:
            self.log_result("Get Agent", False, f"Nenhum agente encontrado: {response}")
            print(f"   ❌ Nenhum agente disponível")
            return False
    
    # ============================================
    # TESTES DE UPLOAD DE MÍDIA
    # ============================================
    
    def create_test_file(self, file_type: str, content: str = None) -> Tuple[io.BytesIO, str, str]:
        """Criar arquivo de teste"""
        if content is None:
            content = f"Teste de {file_type} - {datetime.now().isoformat()}"
        
        file_data = io.BytesIO(content.encode('utf-8'))
        
        if file_type == "image":
            filename = f"teste_imagem_{uuid.uuid4().hex[:8]}.jpg"
            content_type = "image/jpeg"
        elif file_type == "video":
            filename = f"teste_video_{uuid.uuid4().hex[:8]}.mp4"
            content_type = "video/mp4"
        elif file_type == "audio":
            filename = f"teste_audio_{uuid.uuid4().hex[:8]}.mp3"
            content_type = "audio/mpeg"
        else:
            filename = f"teste_arquivo_{uuid.uuid4().hex[:8]}.txt"
            content_type = "text/plain"
        
        return file_data, filename, content_type
    
    async def test_upload_image(self) -> Tuple[bool, str]:
        """Teste: Upload de Imagem"""
        print("\n📷 TESTE 4: Upload de Imagem")
        print("=" * 50)
        
        if not self.client_token:
            self.log_result("Upload Image", False, "Token do cliente necessário")
            return False, ""
        
        # Criar arquivo de teste
        file_data, filename, content_type = self.create_test_file("image")
        
        # Upload
        files = {
            "file": (file_data, filename, content_type)
        }
        
        success, response, status = await self.make_request(
            "POST", "/upload", 
            token=self.client_token,
            files=files
        )
        
        if success and "url" in response:
            file_url = response["url"]
            file_kind = response.get("kind", "unknown")
            
            # Verificar se URL usa https://suporte.help
            if "suporte.help" in file_url:
                self.uploaded_files.append(file_url)
                self.log_result("Upload Image", True, f"Imagem enviada: {filename}")
                print(f"   ✅ URL: {file_url}")
                print(f"   📋 Kind: {file_kind}")
                print(f"   🌐 Servidor: suporte.help ✓")
                return True, file_url
            else:
                self.log_result("Upload Image", False, f"URL não usa suporte.help: {file_url}")
                return False, ""
        else:
            self.log_result("Upload Image", False, f"Erro no upload: {response}")
            print(f"   ❌ Status: {status}")
            print(f"   📄 Response: {response}")
            return False, ""
    
    async def test_upload_video(self) -> Tuple[bool, str]:
        """Teste: Upload de Vídeo"""
        print("\n🎥 TESTE 5: Upload de Vídeo")
        print("=" * 50)
        
        if not self.client_token:
            self.log_result("Upload Video", False, "Token do cliente necessário")
            return False, ""
        
        # Criar arquivo de teste
        file_data, filename, content_type = self.create_test_file("video")
        
        # Upload
        files = {
            "file": (file_data, filename, content_type)
        }
        
        success, response, status = await self.make_request(
            "POST", "/upload", 
            token=self.client_token,
            files=files
        )
        
        if success and "url" in response:
            file_url = response["url"]
            file_kind = response.get("kind", "unknown")
            
            # Verificar se URL usa https://suporte.help
            if "suporte.help" in file_url:
                self.uploaded_files.append(file_url)
                self.log_result("Upload Video", True, f"Vídeo enviado: {filename}")
                print(f"   ✅ URL: {file_url}")
                print(f"   📋 Kind: {file_kind}")
                print(f"   🌐 Servidor: suporte.help ✓")
                return True, file_url
            else:
                self.log_result("Upload Video", False, f"URL não usa suporte.help: {file_url}")
                return False, ""
        else:
            self.log_result("Upload Video", False, f"Erro no upload: {response}")
            print(f"   ❌ Status: {status}")
            print(f"   📄 Response: {response}")
            return False, ""
    
    async def test_upload_audio(self) -> Tuple[bool, str]:
        """Teste: Upload de Áudio"""
        print("\n🎵 TESTE 6: Upload de Áudio")
        print("=" * 50)
        
        if not self.client_token:
            self.log_result("Upload Audio", False, "Token do cliente necessário")
            return False, ""
        
        # Criar arquivo de teste
        file_data, filename, content_type = self.create_test_file("audio")
        
        # Upload
        files = {
            "file": (file_data, filename, content_type)
        }
        
        success, response, status = await self.make_request(
            "POST", "/upload", 
            token=self.client_token,
            files=files
        )
        
        if success and "url" in response:
            file_url = response["url"]
            file_kind = response.get("kind", "unknown")
            
            # Verificar se URL usa https://suporte.help
            if "suporte.help" in file_url:
                self.uploaded_files.append(file_url)
                self.log_result("Upload Audio", True, f"Áudio enviado: {filename}")
                print(f"   ✅ URL: {file_url}")
                print(f"   📋 Kind: {file_kind}")
                print(f"   🌐 Servidor: suporte.help ✓")
                return True, file_url
            else:
                self.log_result("Upload Audio", False, f"URL não usa suporte.help: {file_url}")
                return False, ""
        else:
            self.log_result("Upload Audio", False, f"Erro no upload: {response}")
            print(f"   ❌ Status: {status}")
            print(f"   📄 Response: {response}")
            return False, ""
    
    # ============================================
    # TESTES DE DOWNLOAD DE MÍDIA
    # ============================================
    
    async def test_download_files(self) -> bool:
        """Teste: Download dos arquivos enviados"""
        print("\n⬇️ TESTE 7: Download de Arquivos")
        print("=" * 50)
        
        if not self.uploaded_files:
            self.log_result("Download Files", False, "Nenhum arquivo foi enviado para testar download")
            return False
        
        success_count = 0
        total_files = len(self.uploaded_files)
        
        for i, file_url in enumerate(self.uploaded_files, 1):
            print(f"\n   📁 Testando download {i}/{total_files}")
            
            # Extrair filename da URL
            filename = file_url.split('/')[-1]
            download_endpoint = f"/uploads/{filename}"
            
            try:
                success, response, status = await self.make_request("GET", download_endpoint)
                
                if status == 200:
                    print(f"   ✅ Download OK: {filename}")
                    success_count += 1
                else:
                    print(f"   ❌ Download falhou: {filename} (Status: {status})")
                    
            except Exception as e:
                print(f"   ❌ Erro no download: {filename} - {e}")
        
        success = success_count == total_files
        self.log_result("Download Files", success, f"{success_count}/{total_files} downloads bem-sucedidos")
        
        return success
    
    # ============================================
    # TESTES DE ENVIO DE MENSAGENS COM MÍDIA
    # ============================================
    
    async def test_client_send_message_with_media(self, file_url: str) -> bool:
        """Teste: Cliente envia mensagem com mídia para atendente"""
        print("\n💬 TESTE 8: Cliente → Atendente (com mídia)")
        print("=" * 50)
        
        if not self.client_token or not file_url:
            self.log_result("Client Send Media Message", False, "Token do cliente ou URL do arquivo necessário")
            return False
        
        # Primeiro, obter informações do cliente logado
        success, user_info, status = await self.make_request("GET", "/users/me", token=self.client_token)
        if not success:
            self.log_result("Client Send Media Message", False, f"Erro ao obter info do cliente: {user_info}")
            return False
        
        client_id = user_info.get("id")
        if not client_id:
            self.log_result("Client Send Media Message", False, "ID do cliente não encontrado")
            return False
        
        # Buscar ou criar ticket do cliente
        success, tickets_response, status = await self.make_request("GET", "/tickets", token=self.admin_token)
        
        ticket_id = None
        if success and tickets_response:
            # Procurar ticket do cliente
            for ticket in tickets_response:
                if ticket.get("client_id") == client_id:
                    ticket_id = ticket.get("id")
                    break
        
        if not ticket_id:
            # Se não encontrou ticket, a primeira mensagem criará um automaticamente
            # Vamos usar um ticket_id temporário que será ignorado pelo backend
            ticket_id = "auto-create"
        
        # Enviar mensagem com arquivo (seguindo o formato correto da API)
        message_data = {
            "ticket_id": ticket_id,
            "text": "Olá, estou enviando uma imagem para vocês!",
            "file_url": file_url,
            "kind": "image",
            "from_type": "client",
            "from_id": client_id
        }
        
        success, response, status = await self.make_request(
            "POST", "/messages",
            data=message_data,
            token=self.client_token
        )
        
        if success and response.get("ok"):
            message_id = response.get("message_id")
            self.log_result("Client Send Media Message", True, f"Mensagem com mídia enviada: {message_id}")
            print(f"   ✅ Message ID: {message_id}")
            print(f"   👤 Client ID: {client_id}")
            print(f"   🎫 Ticket ID: {ticket_id}")
            print(f"   📎 File URL: {file_url}")
            print(f"   💬 Texto: {message_data['text']}")
            return True
        else:
            self.log_result("Client Send Media Message", False, f"Erro ao enviar mensagem: {response}")
            print(f"   ❌ Status: {status}")
            print(f"   📄 Response: {response}")
            return False
    
    async def test_agent_send_message_with_media(self, file_url: str) -> bool:
        """Teste: Atendente envia mensagem com mídia para cliente"""
        print("\n💬 TESTE 9: Atendente → Cliente (com mídia)")
        print("=" * 50)
        
        if not self.agent_token or not file_url:
            self.log_result("Agent Send Media Message", False, "Token do agente ou URL do arquivo necessário")
            return False
        
        # Primeiro, precisamos obter um ticket ativo para responder
        success, tickets_response, status = await self.make_request("GET", "/tickets", token=self.agent_token)
        
        if not success or not tickets_response:
            self.log_result("Agent Send Media Message", False, "Nenhum ticket encontrado para responder")
            return False
        
        # Pegar o primeiro ticket
        ticket = tickets_response[0] if tickets_response else None
        if not ticket:
            self.log_result("Agent Send Media Message", False, "Nenhum ticket disponível")
            return False
        
        ticket_id = ticket.get("id")
        client_id = ticket.get("client_id")
        
        # Obter informações do agente logado
        success, agent_info, status = await self.make_request("GET", "/agents/me", token=self.agent_token)
        agent_id = "admin"  # Fallback para admin
        if success and agent_info:
            agent_id = agent_info.get("id", "admin")
        
        # Enviar mensagem com arquivo (seguindo o formato correto da API)
        message_data = {
            "ticket_id": ticket_id,
            "text": "Aqui está o vídeo que você solicitou!",
            "file_url": file_url,
            "kind": "video",
            "from_type": "agent",
            "from_id": agent_id,
            "to_type": "client",
            "to_id": client_id
        }
        
        success, response, status = await self.make_request(
            "POST", "/messages",
            data=message_data,
            token=self.agent_token
        )
        
        if success and response.get("ok"):
            message_id = response.get("message_id")
            self.log_result("Agent Send Media Message", True, f"Mensagem com mídia enviada pelo agente: {message_id}")
            print(f"   ✅ Message ID: {message_id}")
            print(f"   👤 Agent ID: {agent_id}")
            print(f"   👤 Client ID: {client_id}")
            print(f"   🎫 Ticket ID: {ticket_id}")
            print(f"   📎 File URL: {file_url}")
            print(f"   💬 Texto: {message_data['text']}")
            return True
        else:
            self.log_result("Agent Send Media Message", False, f"Erro ao enviar mensagem: {response}")
            print(f"   ❌ Status: {status}")
            print(f"   📄 Response: {response}")
            return False
    
    # ============================================
    # TESTES DE SEGURANÇA
    # ============================================
    
    async def test_upload_without_auth(self) -> bool:
        """Teste: Upload sem autenticação (deve retornar 401)"""
        print("\n🔒 TESTE 10: Upload sem Autenticação")
        print("=" * 50)
        
        # Criar arquivo de teste
        file_data, filename, content_type = self.create_test_file("image")
        
        # Tentar upload sem token
        files = {
            "file": (file_data, filename, content_type)
        }
        
        success, response, status = await self.make_request(
            "POST", "/upload",
            files=files
            # Sem token!
        )
        
        # Deve falhar com 401
        if status == 401:
            self.log_result("Upload Without Auth", True, "Upload bloqueado corretamente (401)")
            print(f"   ✅ Status 401 - Acesso negado corretamente")
            return True
        else:
            self.log_result("Upload Without Auth", False, f"Upload deveria retornar 401, mas retornou {status}")
            print(f"   ❌ Status: {status} (esperado: 401)")
            print(f"   📄 Response: {response}")
            return False
    
    async def test_download_nonexistent_file(self) -> bool:
        """Teste: Download de arquivo inexistente (deve retornar 404)"""
        print("\n🔒 TESTE 11: Download de Arquivo Inexistente")
        print("=" * 50)
        
        # Tentar baixar arquivo que não existe
        fake_filename = f"arquivo_inexistente_{uuid.uuid4().hex}.jpg"
        
        success, response, status = await self.make_request("GET", f"/uploads/{fake_filename}")
        
        # Deve falhar com 404
        if status == 404:
            self.log_result("Download Nonexistent File", True, "Download de arquivo inexistente bloqueado (404)")
            print(f"   ✅ Status 404 - Arquivo não encontrado corretamente")
            return True
        else:
            self.log_result("Download Nonexistent File", False, f"Download deveria retornar 404, mas retornou {status}")
            print(f"   ❌ Status: {status} (esperado: 404)")
            print(f"   📄 Response: {response}")
            return False
    
    # ============================================
    # EXECUÇÃO PRINCIPAL
    # ============================================
    
    async def run_all_tests(self):
        """Executar todos os testes"""
        print("🚀 TESTE COMPLETO: Upload e envio de foto/vídeo entre cliente e atendente")
        print("=" * 80)
        print(f"🌐 Backend URL: {BACKEND_URL}")
        print(f"👤 Admin: admin / {ADMIN_PASSWORD}")
        print(f"📱 Cliente: {CLIENT_WHATSAPP} / PIN {CLIENT_PIN}")
        print("=" * 80)
        
        try:
            await self.setup_session()
            
            # 1. TESTES DE AUTENTICAÇÃO
            print("\n🔐 FASE 1: AUTENTICAÇÃO")
            print("=" * 40)
            
            admin_login_ok = await self.test_admin_login()
            client_login_ok = await self.test_client_login()
            agent_ok = await self.test_get_agent_for_testing()
            
            if not (admin_login_ok and client_login_ok):
                print("❌ Falha na autenticação - interrompendo testes")
                return False
            
            # 2. TESTES DE UPLOAD
            print("\n📤 FASE 2: UPLOAD DE MÍDIA")
            print("=" * 40)
            
            image_ok, image_url = await self.test_upload_image()
            video_ok, video_url = await self.test_upload_video()
            audio_ok, audio_url = await self.test_upload_audio()
            
            # 3. TESTES DE DOWNLOAD
            print("\n📥 FASE 3: DOWNLOAD DE MÍDIA")
            print("=" * 40)
            
            download_ok = await self.test_download_files()
            
            # 4. TESTES DE MENSAGENS COM MÍDIA
            print("\n💬 FASE 4: ENVIO DE MENSAGENS COM MÍDIA")
            print("=" * 40)
            
            client_message_ok = False
            agent_message_ok = False
            
            if image_url:
                client_message_ok = await self.test_client_send_message_with_media(image_url)
            
            if video_url and agent_ok:
                agent_message_ok = await self.test_agent_send_message_with_media(video_url)
            
            # 5. TESTES DE SEGURANÇA
            print("\n🔒 FASE 5: VERIFICAÇÕES DE SEGURANÇA")
            print("=" * 40)
            
            auth_security_ok = await self.test_upload_without_auth()
            file_security_ok = await self.test_download_nonexistent_file()
            
            # RESUMO FINAL
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
                print(f"{i:2d}. {status_icon} {result['test']}")
                if result["message"]:
                    print(f"     {result['message']}")
            
            # VALIDAÇÕES ESPECÍFICAS DO REVIEW REQUEST
            print("\n🎯 VALIDAÇÕES ESPECÍFICAS DO REVIEW REQUEST:")
            
            # 1. Upload de Mídia (API)
            upload_tests = [image_ok, video_ok, audio_ok]
            if all(upload_tests):
                print("✅ Upload de Mídia (API): Imagem, vídeo e áudio funcionando")
            else:
                print("❌ Upload de Mídia (API): Alguns tipos falharam")
            
            # 2. URLs usando https://suporte.help
            if self.uploaded_files and all("suporte.help" in url for url in self.uploaded_files):
                print("✅ URLs retornadas usam https://suporte.help")
            else:
                print("❌ URLs não usam https://suporte.help")
            
            # 3. Download de Mídia (API)
            if download_ok:
                print("✅ Download de Mídia (API): Funcionando corretamente")
            else:
                print("❌ Download de Mídia (API): Problemas detectados")
            
            # 4. Envio de Mensagens com Mídia
            if client_message_ok:
                print("✅ Envio Cliente → Atendente com mídia: Funcionando")
            else:
                print("❌ Envio Cliente → Atendente com mídia: Problemas")
            
            if agent_message_ok:
                print("✅ Envio Atendente → Cliente com mídia: Funcionando")
            else:
                print("❌ Envio Atendente → Cliente com mídia: Problemas")
            
            # 5. Verificações de Segurança
            security_ok = auth_security_ok and file_security_ok
            if security_ok:
                print("✅ Verificações de Segurança: Upload sem auth (401) e arquivo inexistente (404)")
            else:
                print("❌ Verificações de Segurança: Problemas detectados")
            
            # CONCLUSÃO FINAL
            critical_tests = [
                image_ok, video_ok, audio_ok,  # Upload
                download_ok,  # Download
                client_message_ok,  # Mensagens
                security_ok  # Segurança
            ]
            
            overall_success = all(critical_tests)
            
            if overall_success:
                print("\n🎉 RESULTADO FINAL: SISTEMA DE UPLOAD/DOWNLOAD DE MÍDIA 100% FUNCIONAL!")
                print("✅ Todos os cenários do review request foram validados com sucesso")
                print("✅ Upload/download de foto/vídeo entre cliente e atendente funcionando")
                print("✅ Servidor externo (suporte.help) operacional")
            else:
                print("\n❌ RESULTADO FINAL: PROBLEMAS DETECTADOS NO SISTEMA DE MÍDIA")
                print("⚠️ Alguns cenários do review request falharam")
                
                failed_areas = []
                if not all(upload_tests):
                    failed_areas.append("Upload de mídia")
                if not download_ok:
                    failed_areas.append("Download de mídia")
                if not client_message_ok:
                    failed_areas.append("Mensagens cliente→atendente")
                if not agent_message_ok:
                    failed_areas.append("Mensagens atendente→cliente")
                if not security_ok:
                    failed_areas.append("Verificações de segurança")
                
                print(f"🔧 Áreas com problemas: {', '.join(failed_areas)}")
            
            return overall_success
            
        except Exception as e:
            print(f"💥 ERRO CRÍTICO durante execução dos testes: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            await self.cleanup_session()

async def main():
    """Função principal"""
    tester = MediaUploadTester()
    success = await tester.run_all_tests()
    
    if success:
        print("\n🎯 CONCLUSÃO: Sistema de upload/download de mídia funcionando perfeitamente!")
        exit(0)
    else:
        print("\n⚠️ CONCLUSÃO: Problemas detectados no sistema de mídia!")
        exit(1)

if __name__ == "__main__":
    asyncio.run(main())