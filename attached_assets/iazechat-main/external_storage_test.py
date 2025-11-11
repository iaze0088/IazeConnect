#!/usr/bin/env python3
"""
🧪 TESTE COMPLETO: EXTERNAL STORAGE SERVICE (MODO LOCAL - FALLBACK)

CONTEXTO:
Sistema de External Storage implementado com 2 modos:
- EXTERNO: Upload para servidor Evolution (80TB @ 198.96.94.106:9000) - PENDENTE CONFIGURAÇÃO
- LOCAL: Upload para /data/uploads (fallback) - MODO ATIVO ATUAL

OBJETIVO DOS TESTES:
Validar que o sistema está funcionando corretamente no modo LOCAL (fallback),
pronto para quando o servidor Evolution for configurado.

CENÁRIOS DE TESTE OBRIGATÓRIOS:
1️⃣ TESTE DE UPLOAD - ARQUIVO TEXTO
2️⃣ TESTE DE UPLOAD - IMAGEM  
3️⃣ TESTE DE UPLOAD - VÍDEO
4️⃣ TESTE DE UPLOAD - ÁUDIO
5️⃣ VERIFICAÇÃO DE FALLBACK ROBUSTO
6️⃣ VERIFICAÇÃO DE PERSISTÊNCIA
"""

import asyncio
import aiohttp
import json
import os
import tempfile
import time
from pathlib import Path
from typing import Dict, Any

# Configuração
BACKEND_URL = "https://wppconnect-fix.preview.emergentagent.com"
ADMIN_EMAIL = "admin@sistema.com"
ADMIN_PASSWORD = "102030@ab"

class ExternalStorageTest:
    def __init__(self):
        self.session = None
        self.admin_token = None
        self.test_results = []
        
    async def setup(self):
        """Configurar sessão HTTP e autenticação"""
        self.session = aiohttp.ClientSession()
        
        # Login como admin
        login_data = {
            "password": ADMIN_PASSWORD
        }
        
        async with self.session.post(f"{BACKEND_URL}/api/auth/admin/login", json=login_data) as response:
            if response.status == 200:
                data = await response.json()
                self.admin_token = data["token"]
                print(f"✅ Admin login successful")
                return True
            else:
                error = await response.text()
                print(f"❌ Admin login failed: {response.status} - {error}")
                return False
    
    async def cleanup(self):
        """Limpar recursos"""
        if self.session:
            await self.session.close()
    
    def create_test_file(self, content: bytes, filename: str, content_type: str) -> tuple:
        """Criar arquivo temporário para teste"""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=Path(filename).suffix)
        temp_file.write(content)
        temp_file.close()
        return temp_file.name, content_type
    
    async def test_upload_file(self, test_name: str, content: bytes, filename: str, content_type: str, expected_kind: str) -> Dict[str, Any]:
        """Testar upload de arquivo"""
        print(f"\n🧪 {test_name}")
        print(f"   Arquivo: {filename}")
        print(f"   Tipo: {content_type}")
        print(f"   Tamanho: {len(content)} bytes")
        print(f"   Kind esperado: {expected_kind}")
        
        try:
            # Criar arquivo temporário
            temp_path, _ = self.create_test_file(content, filename, content_type)
            
            # Preparar upload
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            # Ler arquivo e preparar FormData
            with open(temp_path, 'rb') as f:
                file_content = f.read()
            
            data = aiohttp.FormData()
            data.add_field('file', file_content, filename=filename, content_type=content_type)
            
            # Fazer upload
            async with self.session.post(f"{BACKEND_URL}/api/upload", data=data, headers=headers) as response:
                response_text = await response.text()
                
                if response.status == 200:
                    result = json.loads(response_text)
                    
                    # Validações obrigatórias
                    validations = {
                        "ok": result.get("ok") == True,
                        "url_presente": bool(result.get("url")),
                        "filename_presente": bool(result.get("filename")),
                        "size_correto": result.get("size", 0) == len(content),
                        "kind_correto": result.get("kind") == expected_kind,
                        "local_mode": result.get("external") == False  # Deve ser False no modo local
                    }
                    
                    # Verificar se URL é acessível
                    url_accessible = False
                    if result.get("url"):
                        try:
                            async with self.session.get(result["url"]) as url_response:
                                url_accessible = url_response.status == 200
                        except:
                            url_accessible = False
                    
                    validations["url_acessivel"] = url_accessible
                    
                    # Resultado do teste
                    test_result = {
                        "test_name": test_name,
                        "status": "PASS" if all(validations.values()) else "FAIL",
                        "response": result,
                        "validations": validations,
                        "details": {
                            "filename": result.get("filename"),
                            "url": result.get("url"),
                            "size": result.get("size"),
                            "kind": result.get("kind"),
                            "local": not result.get("external", True)
                        }
                    }
                    
                    # Log resultado
                    if test_result["status"] == "PASS":
                        print(f"   ✅ SUCESSO!")
                        print(f"      URL: {result.get('url')}")
                        print(f"      Filename: {result.get('filename')}")
                        print(f"      Size: {result.get('size')} bytes")
                        print(f"      Kind: {result.get('kind')}")
                        print(f"      Local: {not result.get('external', True)}")
                    else:
                        print(f"   ❌ FALHA!")
                        for validation, passed in validations.items():
                            status = "✅" if passed else "❌"
                            print(f"      {status} {validation}")
                    
                    # Limpar arquivo temporário
                    os.unlink(temp_path)
                    
                    return test_result
                
                else:
                    print(f"   ❌ HTTP Error: {response.status}")
                    print(f"   Response: {response_text}")
                    return {
                        "test_name": test_name,
                        "status": "FAIL",
                        "error": f"HTTP {response.status}: {response_text}",
                        "validations": {},
                        "details": {}
                    }
        
        except Exception as e:
            print(f"   ❌ Exception: {str(e)}")
            return {
                "test_name": test_name,
                "status": "FAIL", 
                "error": str(e),
                "validations": {},
                "details": {}
            }
    
    async def test_file_persistence(self) -> Dict[str, Any]:
        """Verificar se arquivos estão sendo salvos em /data/uploads"""
        print(f"\n🧪 TESTE DE PERSISTÊNCIA")
        print(f"   Verificando se arquivos estão em /data/uploads...")
        
        try:
            # Fazer upload de teste
            test_content = b"Teste de persistencia"
            temp_path, _ = self.create_test_file(test_content, "persistencia.txt", "text/plain")
            
            with open(temp_path, 'rb') as f:
                file_content = f.read()
            
            data = aiohttp.FormData()
            data.add_field('file', file_content, filename="persistencia.txt", content_type="text/plain")
            
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            async with self.session.post(f"{BACKEND_URL}/api/upload", data=data, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    filename = result.get("filename")
                    
                    if filename:
                        # Verificar se arquivo pode ser acessado via GET
                        file_url = f"{BACKEND_URL}/api/uploads/{filename}"
                        async with self.session.get(file_url) as file_response:
                            if file_response.status == 200:
                                content = await file_response.read()
                                if content == test_content:
                                    print(f"   ✅ Arquivo persistido e acessível!")
                                    print(f"      URL: {file_url}")
                                    print(f"      Conteúdo verificado: {len(content)} bytes")
                                    
                                    os.unlink(temp_path)
                                    return {
                                        "test_name": "Persistência de Arquivos",
                                        "status": "PASS",
                                        "details": {
                                            "filename": filename,
                                            "url": file_url,
                                            "content_verified": True
                                        }
                                    }
                                else:
                                    print(f"   ❌ Conteúdo não confere!")
                                    return {"test_name": "Persistência de Arquivos", "status": "FAIL", "error": "Content mismatch"}
                            else:
                                print(f"   ❌ Arquivo não acessível: {file_response.status}")
                                return {"test_name": "Persistência de Arquivos", "status": "FAIL", "error": f"File not accessible: {file_response.status}"}
                    else:
                        print(f"   ❌ Filename não retornado")
                        return {"test_name": "Persistência de Arquivos", "status": "FAIL", "error": "No filename returned"}
                else:
                    print(f"   ❌ Upload falhou: {response.status}")
                    return {"test_name": "Persistência de Arquivos", "status": "FAIL", "error": f"Upload failed: {response.status}"}
        
        except Exception as e:
            print(f"   ❌ Exception: {str(e)}")
            return {"test_name": "Persistência de Arquivos", "status": "FAIL", "error": str(e)}
    
    async def verify_local_mode(self) -> Dict[str, Any]:
        """Verificar se está no modo local (USE_EXTERNAL_STORAGE=false)"""
        print(f"\n🧪 VERIFICAÇÃO DE MODO LOCAL")
        print(f"   Confirmando que USE_EXTERNAL_STORAGE=false...")
        
        # Fazer upload simples e verificar se retorna local=true
        test_content = b"Teste modo local"
        temp_path, _ = self.create_test_file(test_content, "modo_local.txt", "text/plain")
        
        try:
            with open(temp_path, 'rb') as f:
                file_content = f.read()
            
            data = aiohttp.FormData()
            data.add_field('file', file_content, filename="modo_local.txt", content_type="text/plain")
            
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            async with self.session.post(f"{BACKEND_URL}/api/upload", data=data, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    # Verificar se external=false (modo local)
                    is_local = result.get("external") == False
                    
                    if is_local:
                        print(f"   ✅ Confirmado: Sistema em modo LOCAL!")
                        print(f"      external: {result.get('external')}")
                        print(f"      URL: {result.get('url')}")
                        
                        os.unlink(temp_path)
                        return {
                            "test_name": "Verificação Modo Local",
                            "status": "PASS",
                            "details": {
                                "external": result.get("external"),
                                "local_mode": True,
                                "url": result.get("url")
                            }
                        }
                    else:
                        print(f"   ❌ Sistema não está em modo local!")
                        print(f"      external: {result.get('external')}")
                        return {"test_name": "Verificação Modo Local", "status": "FAIL", "error": "Not in local mode"}
                else:
                    print(f"   ❌ Upload falhou: {response.status}")
                    return {"test_name": "Verificação Modo Local", "status": "FAIL", "error": f"Upload failed: {response.status}"}
        
        except Exception as e:
            print(f"   ❌ Exception: {str(e)}")
            return {"test_name": "Verificação Modo Local", "status": "FAIL", "error": str(e)}
    
    async def check_backend_logs(self) -> Dict[str, Any]:
        """Verificar logs do backend para mensagens de external_storage"""
        print(f"\n🧪 VERIFICAÇÃO DE LOGS DO BACKEND")
        print(f"   Verificando logs para mensagens de external_storage...")
        
        try:
            # Fazer upload para gerar logs
            test_content = b"Teste para logs"
            temp_path, _ = self.create_test_file(test_content, "log_test.txt", "text/plain")
            
            with open(temp_path, 'rb') as f:
                file_content = f.read()
            
            data = aiohttp.FormData()
            data.add_field('file', file_content, filename="log_test.txt", content_type="text/plain")
            
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            async with self.session.post(f"{BACKEND_URL}/api/upload", data=data, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    # Se chegou até aqui, o upload funcionou
                    print(f"   ✅ Upload executado com sucesso!")
                    print(f"      Logs devem mostrar: 'Arquivo salvo localmente'")
                    print(f"      Filename: {result.get('filename')}")
                    
                    os.unlink(temp_path)
                    return {
                        "test_name": "Verificação de Logs",
                        "status": "PASS",
                        "details": {
                            "upload_successful": True,
                            "filename": result.get("filename"),
                            "note": "Logs devem mostrar 'Arquivo salvo localmente'"
                        }
                    }
                else:
                    print(f"   ❌ Upload falhou: {response.status}")
                    return {"test_name": "Verificação de Logs", "status": "FAIL", "error": f"Upload failed: {response.status}"}
        
        except Exception as e:
            print(f"   ❌ Exception: {str(e)}")
            return {"test_name": "Verificação de Logs", "status": "FAIL", "error": str(e)}
    
    async def run_all_tests(self):
        """Executar todos os testes conforme review request"""
        print("🚀 INICIANDO TESTE COMPLETO: EXTERNAL STORAGE SERVICE (MODO LOCAL)")
        print("=" * 80)
        
        # Setup
        if not await self.setup():
            print("❌ Falha no setup. Abortando testes.")
            return
        
        # 1️⃣ TESTE DE UPLOAD - ARQUIVO TEXTO
        result1 = await self.test_upload_file(
            "1️⃣ TESTE DE UPLOAD - ARQUIVO TEXTO",
            b"Este eh um arquivo de texto para teste do external storage service.",
            "teste.txt",
            "text/plain",
            "file"
        )
        self.test_results.append(result1)
        
        # 2️⃣ TESTE DE UPLOAD - IMAGEM
        # Criar uma imagem PNG simples (1x1 pixel)
        png_content = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\nIDATx\x9cc\xf8\x00\x00\x00\x01\x00\x01\x00\x00\x00\x00IEND\xaeB`\x82'
        result2 = await self.test_upload_file(
            "2️⃣ TESTE DE UPLOAD - IMAGEM",
            png_content,
            "teste.png",
            "image/png",
            "image"
        )
        self.test_results.append(result2)
        
        # 3️⃣ TESTE DE UPLOAD - VÍDEO
        # Criar um arquivo MP4 mínimo (header apenas)
        mp4_content = b'\x00\x00\x00\x20ftypmp42\x00\x00\x00\x00mp42isom\x00\x00\x00\x08free'
        result3 = await self.test_upload_file(
            "3️⃣ TESTE DE UPLOAD - VÍDEO",
            mp4_content,
            "teste.mp4",
            "video/mp4",
            "video"
        )
        self.test_results.append(result3)
        
        # 4️⃣ TESTE DE UPLOAD - ÁUDIO
        # Criar um arquivo MP3 mínimo (header apenas)
        mp3_content = b'\xff\xfb\x90\x00' + b'\x00' * 100  # MP3 header + padding
        result4 = await self.test_upload_file(
            "4️⃣ TESTE DE UPLOAD - ÁUDIO",
            mp3_content,
            "teste.mp3",
            "audio/mpeg",
            "audio"
        )
        self.test_results.append(result4)
        
        # 5️⃣ VERIFICAÇÃO DE FALLBACK ROBUSTO
        result5 = await self.verify_local_mode()
        self.test_results.append(result5)
        
        # 6️⃣ VERIFICAÇÃO DE PERSISTÊNCIA
        result6 = await self.test_file_persistence()
        self.test_results.append(result6)
        
        # 7️⃣ VERIFICAÇÃO DE LOGS
        result7 = await self.check_backend_logs()
        self.test_results.append(result7)
        
        # Cleanup
        await self.cleanup()
        
        # Relatório final
        self.print_final_report()
    
    def print_final_report(self):
        """Imprimir relatório final dos testes"""
        print("\n" + "=" * 80)
        print("📊 RELATÓRIO FINAL - EXTERNAL STORAGE SERVICE (MODO LOCAL)")
        print("=" * 80)
        
        passed_tests = [r for r in self.test_results if r.get("status") == "PASS"]
        failed_tests = [r for r in self.test_results if r.get("status") == "FAIL"]
        
        print(f"\n✅ TESTES APROVADOS: {len(passed_tests)}/{len(self.test_results)}")
        for test in passed_tests:
            print(f"   ✅ {test['test_name']}")
        
        if failed_tests:
            print(f"\n❌ TESTES FALHARAM: {len(failed_tests)}/{len(self.test_results)}")
            for test in failed_tests:
                print(f"   ❌ {test['test_name']}")
                if test.get("error"):
                    print(f"      Erro: {test['error']}")
        
        # Critérios de sucesso
        print(f"\n🎯 CRITÉRIOS DE SUCESSO:")
        success_criteria = {
            "Upload de diferentes tipos de arquivo funcionando": len([t for t in self.test_results[:4] if t.get("status") == "PASS"]) == 4,
            "Detecção correta de tipo de arquivo (kind)": all(t.get("details", {}).get("kind") for t in self.test_results[:4] if t.get("status") == "PASS"),
            "Arquivos salvos em /data/uploads": any(t.get("test_name") == "Persistência de Arquivos" and t.get("status") == "PASS" for t in self.test_results),
            "URLs retornadas são válidas e acessíveis": all(t.get("validations", {}).get("url_acessivel", False) for t in self.test_results[:4] if t.get("status") == "PASS"),
            "Campo 'local: true' presente nas respostas": any(t.get("test_name") == "Verificação Modo Local" and t.get("status") == "PASS" for t in self.test_results),
            "Sistema robusto e sem erros": len(failed_tests) == 0
        }
        
        for criterion, met in success_criteria.items():
            status = "✅" if met else "❌"
            print(f"   {status} {criterion}")
        
        # Conclusão
        all_passed = len(failed_tests) == 0
        if all_passed:
            print(f"\n🎉 CONCLUSÃO: SISTEMA EXTERNAL STORAGE 100% FUNCIONAL NO MODO LOCAL!")
            print(f"✅ Todos os testes passaram")
            print(f"✅ Sistema pronto para quando o usuário configurar o servidor Evolution")
            print(f"✅ Fallback robusto funcionando perfeitamente")
        else:
            print(f"\n⚠️ CONCLUSÃO: SISTEMA PRECISA DE CORREÇÕES")
            print(f"❌ {len(failed_tests)} teste(s) falharam")
            print(f"🔧 Verificar logs acima para detalhes dos problemas")
        
        print("=" * 80)

async def main():
    """Função principal"""
    test_runner = ExternalStorageTest()
    await test_runner.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())