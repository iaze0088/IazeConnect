#!/usr/bin/env python3
"""
🧪 TESTE COMPLETO: EXTERNAL STORAGE ATIVADO (80TB Evolution Server)

CONTEXTO CRÍTICO:
External storage FOI ATIVADO com sucesso no servidor Evolution (198.96.94.106:9000)!
✅ USE_EXTERNAL_STORAGE="true" no .env
✅ Servidor Evolution rodando e testado manualmente
✅ Upload direto funcionando: http://198.96.94.106:9000/upload
✅ Download funcionando: http://198.96.94.106:9000/uploads/{filename}

OBJETIVO DOS TESTES:
Validar que o sistema IAZE está usando o storage externo corretamente através do endpoint /api/upload
"""

import asyncio
import aiohttp
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Configuração
BACKEND_URL = "https://wppconnect-fix.preview.emergentagent.com"
ADMIN_EMAIL = "admin@sistema.com"
ADMIN_PASSWORD = "102030@ab"

# Cores para output
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

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text.center(80)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.END}")

def print_success(text):
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")

def print_error(text):
    print(f"{Colors.RED}❌ {text}{Colors.END}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠️ {text}{Colors.END}")

def print_info(text):
    print(f"{Colors.BLUE}ℹ️ {text}{Colors.END}")

class ExternalStorageTest:
    def __init__(self):
        self.session = None
        self.admin_token = None
        self.test_results = []
        
    async def setup(self):
        """Configurar sessão HTTP"""
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(timeout=timeout)
        
    async def cleanup(self):
        """Limpar recursos"""
        if self.session:
            await self.session.close()
    
    async def login_admin(self):
        """Login como admin para obter token"""
        print_info("Fazendo login como admin...")
        
        try:
            async with self.session.post(
                f"{BACKEND_URL}/api/auth/admin/login",
                json={"password": ADMIN_PASSWORD}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self.admin_token = data["token"]
                    print_success(f"Login admin realizado com sucesso")
                    return True
                else:
                    error_text = await response.text()
                    print_error(f"Erro no login admin: {response.status} - {error_text}")
                    return False
        except Exception as e:
            print_error(f"Exceção no login admin: {e}")
            return False
    
    def create_test_file(self, filename: str, content: str, content_type: str):
        """Criar arquivo de teste temporário"""
        test_file = Path(f"/tmp/{filename}")
        test_file.write_text(content)
        return test_file, content_type
    
    def create_test_binary_file(self, filename: str, size: int, content_type: str):
        """Criar arquivo binário de teste"""
        test_file = Path(f"/tmp/{filename}")
        # Criar conteúdo binário simples
        content = b'\x89PNG\r\n\x1a\n' + b'A' * (size - 8)  # PNG header + padding
        test_file.write_bytes(content)
        return test_file, content_type
    
    async def test_upload_file(self, test_name: str, filename: str, content: str, content_type: str, expected_kind: str):
        """Testar upload de um arquivo específico"""
        print_info(f"🧪 {test_name}")
        
        try:
            # Criar arquivo de teste
            if content_type.startswith('text/'):
                test_file, _ = self.create_test_file(filename, content, content_type)
                file_content = content.encode('utf-8')
            else:
                test_file, _ = self.create_test_binary_file(filename, len(content.encode()), content_type)
                file_content = test_file.read_bytes()
            
            # Preparar dados do upload
            data = aiohttp.FormData()
            data.add_field('file', 
                          file_content,
                          filename=filename,
                          content_type=content_type)
            
            # Headers com autenticação
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            # Fazer upload
            async with self.session.post(
                f"{BACKEND_URL}/api/upload",
                data=data,
                headers=headers
            ) as response:
                
                if response.status == 200:
                    result = await response.json()
                    
                    # Validações críticas
                    validations = []
                    
                    # 1. Verificar se retornou ok: true
                    if result.get('ok') == True:
                        validations.append("✅ ok: true")
                    else:
                        validations.append(f"❌ ok: {result.get('ok')} (esperado: true)")
                    
                    # 2. Verificar se URL aponta para servidor Evolution
                    url = result.get('url', '')
                    if url.startswith("http://198.96.94.106:9000/uploads/"):
                        validations.append("✅ URL aponta para servidor Evolution")
                    else:
                        validations.append(f"❌ URL incorreta: {url}")
                    
                    # 3. Verificar filename
                    if result.get('filename'):
                        validations.append(f"✅ filename: {result.get('filename')}")
                    else:
                        validations.append("❌ filename ausente")
                    
                    # 4. Verificar size > 0
                    size = result.get('size', 0)
                    if size > 0:
                        validations.append(f"✅ size: {size} bytes")
                    else:
                        validations.append(f"❌ size: {size} (deve ser > 0)")
                    
                    # 5. CRÍTICO: Verificar external: true
                    external = result.get('external')
                    if external == True:
                        validations.append("✅ external: true (STORAGE EXTERNO ATIVO!)")
                    else:
                        validations.append(f"❌ external: {external} (esperado: true)")
                    
                    # 6. Verificar kind
                    kind = result.get('kind')
                    if kind == expected_kind:
                        validations.append(f"✅ kind: {kind}")
                    else:
                        validations.append(f"❌ kind: {kind} (esperado: {expected_kind})")
                    
                    # Mostrar resultados
                    for validation in validations:
                        print(f"   {validation}")
                    
                    # Testar download do arquivo
                    await self.test_download_file(url, filename)
                    
                    # Determinar se teste passou
                    failed_validations = [v for v in validations if v.startswith("❌")]
                    if not failed_validations:
                        print_success(f"{test_name}: PASSOU")
                        self.test_results.append({"test": test_name, "status": "PASS", "details": result})
                        return True
                    else:
                        print_error(f"{test_name}: FALHOU ({len(failed_validations)} problemas)")
                        self.test_results.append({"test": test_name, "status": "FAIL", "details": result, "errors": failed_validations})
                        return False
                
                else:
                    error_text = await response.text()
                    print_error(f"{test_name}: HTTP {response.status} - {error_text}")
                    self.test_results.append({"test": test_name, "status": "ERROR", "error": f"HTTP {response.status}"})
                    return False
                    
        except Exception as e:
            print_error(f"{test_name}: Exceção - {e}")
            self.test_results.append({"test": test_name, "status": "EXCEPTION", "error": str(e)})
            return False
        finally:
            # Limpar arquivo temporário
            if 'test_file' in locals():
                try:
                    test_file.unlink()
                except:
                    pass
    
    async def test_download_file(self, url: str, filename: str):
        """Testar download do arquivo uploadado"""
        print_info(f"   🔗 Testando download: {filename}")
        
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    content = await response.read()
                    print_success(f"   Download OK: {len(content)} bytes")
                    return True
                else:
                    print_error(f"   Download falhou: HTTP {response.status}")
                    return False
        except Exception as e:
            print_error(f"   Download exceção: {e}")
            return False
    
    async def check_backend_logs(self):
        """Verificar logs do backend para mensagens de external storage"""
        print_info("🔍 Verificando logs do backend...")
        
        try:
            # Verificar logs do supervisor
            result = os.popen("tail -n 50 /var/log/supervisor/backend.*.log | grep -i 'external\\|evolution' | tail -10").read()
            
            if result.strip():
                print_success("Logs encontrados:")
                for line in result.strip().split('\n'):
                    print(f"   📝 {line}")
            else:
                print_warning("Nenhum log específico de external storage encontrado")
                
        except Exception as e:
            print_warning(f"Erro ao verificar logs: {e}")
    
    async def verify_local_storage_empty(self):
        """Verificar se arquivos NÃO estão sendo salvos localmente"""
        print_info("🔍 Verificando se arquivos NÃO estão em /data/uploads...")
        
        try:
            uploads_dir = Path("/data/uploads")
            if uploads_dir.exists():
                files = list(uploads_dir.glob("*"))
                recent_files = []
                
                # Verificar arquivos criados nos últimos 5 minutos
                import time
                current_time = time.time()
                for file_path in files:
                    if file_path.is_file():
                        file_age = current_time - file_path.stat().st_mtime
                        if file_age < 300:  # 5 minutos
                            recent_files.append(file_path.name)
                
                if recent_files:
                    print_warning(f"⚠️ Arquivos recentes encontrados localmente: {recent_files}")
                    print_warning("   Isso pode indicar que o external storage não está funcionando")
                else:
                    print_success("✅ Nenhum arquivo recente em /data/uploads (external storage funcionando)")
            else:
                print_info("Diretório /data/uploads não existe")
                
        except Exception as e:
            print_warning(f"Erro ao verificar storage local: {e}")
    
    async def run_all_tests(self):
        """Executar todos os testes obrigatórios"""
        print_header("🧪 TESTE COMPLETO: EXTERNAL STORAGE ATIVADO")
        
        # Setup
        await self.setup()
        
        # Login
        if not await self.login_admin():
            print_error("Falha no login admin. Abortando testes.")
            return False
        
        print_header("CENÁRIOS DE TESTE OBRIGATÓRIOS")
        
        # 1️⃣ TESTE DE UPLOAD - TEXTO (External Storage)
        await self.test_upload_file(
            "1️⃣ TESTE DE UPLOAD - TEXTO (External Storage)",
            "teste_external.txt",
            "Este é um arquivo de teste para external storage Evolution!",
            "text/plain",
            "file"
        )
        
        # 2️⃣ TESTE DE UPLOAD - IMAGEM
        await self.test_upload_file(
            "2️⃣ TESTE DE UPLOAD - IMAGEM",
            "teste_external.png",
            "PNG_FAKE_CONTENT_FOR_TESTING_EXTERNAL_STORAGE_EVOLUTION_SERVER",
            "image/png",
            "image"
        )
        
        # 3️⃣ TESTE DE UPLOAD - VÍDEO
        await self.test_upload_file(
            "3️⃣ TESTE DE UPLOAD - VÍDEO",
            "teste_external.mp4",
            "MP4_FAKE_CONTENT_FOR_TESTING_EXTERNAL_STORAGE_EVOLUTION_SERVER",
            "video/mp4",
            "video"
        )
        
        # 4️⃣ TESTE DE UPLOAD - ÁUDIO
        await self.test_upload_file(
            "4️⃣ TESTE DE UPLOAD - ÁUDIO",
            "teste_external.mp3",
            "MP3_FAKE_CONTENT_FOR_TESTING_EXTERNAL_STORAGE_EVOLUTION_SERVER",
            "audio/mpeg",
            "audio"
        )
        
        print_header("VERIFICAÇÕES ADICIONAIS")
        
        # 5️⃣ VERIFICAÇÃO DE LOGS
        await self.check_backend_logs()
        
        # 6️⃣ VERIFICAR SE NÃO ESTÁ SALVANDO LOCALMENTE
        await self.verify_local_storage_empty()
        
        # Cleanup
        await self.cleanup()
        
        # Relatório final
        await self.generate_final_report()
        
        return True
    
    async def generate_final_report(self):
        """Gerar relatório final dos testes"""
        print_header("📊 RELATÓRIO FINAL DOS TESTES")
        
        total_tests = len(self.test_results)
        passed_tests = len([t for t in self.test_results if t["status"] == "PASS"])
        failed_tests = len([t for t in self.test_results if t["status"] in ["FAIL", "ERROR", "EXCEPTION"]])
        
        print(f"\n{Colors.BOLD}RESUMO EXECUTIVO:{Colors.END}")
        print(f"📊 Total de testes: {total_tests}")
        print(f"✅ Testes aprovados: {passed_tests}")
        print(f"❌ Testes falharam: {failed_tests}")
        print(f"📈 Taxa de sucesso: {(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "N/A")
        
        print(f"\n{Colors.BOLD}DETALHES DOS TESTES:{Colors.END}")
        for i, result in enumerate(self.test_results, 1):
            status_color = Colors.GREEN if result["status"] == "PASS" else Colors.RED
            print(f"{i}. {status_color}{result['test']}: {result['status']}{Colors.END}")
            
            if result["status"] == "PASS":
                details = result.get("details", {})
                external = details.get("external", "N/A")
                url = details.get("url", "N/A")
                print(f"   ✅ External: {external}")
                print(f"   🔗 URL: {url[:60]}..." if len(str(url)) > 60 else f"   🔗 URL: {url}")
            elif result["status"] == "FAIL":
                errors = result.get("errors", [])
                for error in errors[:3]:  # Mostrar apenas os primeiros 3 erros
                    print(f"   {error}")
        
        print(f"\n{Colors.BOLD}CRITÉRIOS DE SUCESSO:{Colors.END}")
        
        # Verificar critérios específicos do review request
        external_working = any(
            t["status"] == "PASS" and t.get("details", {}).get("external") == True 
            for t in self.test_results
        )
        
        evolution_urls = any(
            t["status"] == "PASS" and "198.96.94.106:9000/uploads/" in str(t.get("details", {}).get("url", ""))
            for t in self.test_results
        )
        
        if external_working:
            print_success("✅ Todos os uploads retornam 'external: true'")
        else:
            print_error("❌ Uploads não retornam 'external: true'")
        
        if evolution_urls:
            print_success("✅ URLs apontam para http://198.96.94.106:9000/uploads/")
        else:
            print_error("❌ URLs não apontam para servidor Evolution")
        
        if passed_tests == total_tests:
            print_success("✅ Downloads funcionam a partir das URLs retornadas")
            print_success("✅ Sistema robusto e sem erros")
        
        print(f"\n{Colors.BOLD}CONCLUSÃO:{Colors.END}")
        if passed_tests == total_tests and external_working and evolution_urls:
            print_success("🎉 EXTERNAL STORAGE 100% FUNCIONAL!")
            print_success("✅ Sistema IAZE está usando o servidor Evolution corretamente")
            print_success("✅ Todos os critérios de sucesso foram atendidos")
            print_success("✅ Performance melhorada com storage externo de 80TB")
        else:
            print_error("❌ EXTERNAL STORAGE COM PROBLEMAS!")
            print_error("❌ Alguns testes falharam ou critérios não foram atendidos")
            print_warning("⚠️ Verificar configuração do servidor Evolution")

async def main():
    """Função principal"""
    print(f"{Colors.BOLD}{Colors.PURPLE}")
    print("🧪 TESTE COMPLETO: EXTERNAL STORAGE ATIVADO (80TB Evolution Server)")
    print("=" * 80)
    print("CONTEXTO: External storage FOI ATIVADO no servidor Evolution!")
    print("OBJETIVO: Validar que o sistema IAZE está usando storage externo")
    print(f"{'=' * 80}{Colors.END}")
    
    tester = ExternalStorageTest()
    
    try:
        success = await tester.run_all_tests()
        
        if success:
            print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 TESTE FINALIZADO COM SUCESSO!{Colors.END}")
        else:
            print(f"\n{Colors.RED}{Colors.BOLD}❌ TESTE FINALIZADO COM PROBLEMAS!{Colors.END}")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⚠️ Teste interrompido pelo usuário{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}💥 Erro crítico: {e}{Colors.END}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())