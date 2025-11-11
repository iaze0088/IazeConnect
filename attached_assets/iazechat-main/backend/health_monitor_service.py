"""
Serviço de Monitoramento Automático e Auto-Recuperação
- Verifica saúde do servidor externo periodicamente
- Faz fallback automático para armazenamento local em caso de falha
- Tenta reconectar automaticamente quando servidor voltar
- Logs detalhados de todas as ações
"""
import asyncio
import aiohttp
import logging
import os
import time
from datetime import datetime, timezone
from typing import Optional

# Configurar logger
logger = logging.getLogger("health_monitor")
logger.setLevel(logging.INFO)

# Handler para arquivo
file_handler = logging.FileHandler("/var/log/health_monitor.log")
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Handler para console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)


class HealthMonitorService:
    """Serviço de monitoramento de saúde e auto-recuperação"""
    
    def __init__(self):
        self.external_host = os.getenv('EXTERNAL_STORAGE_HOST', '198.96.94.106')
        self.external_port = os.getenv('EXTERNAL_STORAGE_PORT', '9000')
        self.check_interval = int(os.getenv('HEALTH_CHECK_INTERVAL', '60'))  # Segundos
        self.timeout = int(os.getenv('HEALTH_CHECK_TIMEOUT', '5'))  # Segundos
        self.max_failures = int(os.getenv('HEALTH_MAX_FAILURES', '3'))  # Tentativas antes de fallback
        
        self.external_url = f"http://{self.external_host}:{self.external_port}/health"
        self.current_mode = None  # 'external' ou 'local'
        self.consecutive_failures = 0
        self.consecutive_successes = 0
        self.last_check_time = None
        self.is_running = False
        
        logger.info("="*80)
        logger.info("🏥 Health Monitor Service Inicializado")
        logger.info(f"   External Server: {self.external_host}:{self.external_port}")
        logger.info(f"   Check Interval: {self.check_interval}s")
        logger.info(f"   Timeout: {self.timeout}s")
        logger.info(f"   Max Failures: {self.max_failures}")
        logger.info("="*80)
    
    async def check_external_storage_health(self) -> bool:
        """
        Verifica saúde do servidor externo
        Returns: True se saudável, False se com problemas
        """
        try:
            start_time = time.time()
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.external_url,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    elapsed_time = time.time() - start_time
                    
                    if response.status == 200:
                        # Servidor respondeu OK
                        logger.info(f"✅ External Storage: HEALTHY (response time: {elapsed_time:.2f}s)")
                        return True
                    else:
                        # Servidor respondeu mas com erro
                        logger.warning(f"⚠️ External Storage: UNHEALTHY (status: {response.status})")
                        return False
                        
        except asyncio.TimeoutError:
            elapsed_time = time.time() - start_time
            logger.error(f"⏱️ External Storage: TIMEOUT (timeout após {elapsed_time:.2f}s)")
            return False
            
        except aiohttp.ClientError as e:
            logger.error(f"❌ External Storage: CONNECTION ERROR ({str(e)})")
            return False
            
        except Exception as e:
            logger.error(f"💥 External Storage: UNKNOWN ERROR ({type(e).__name__}: {str(e)})")
            return False
    
    def get_current_storage_mode(self) -> str:
        """Lê o modo atual de storage do .env"""
        env_path = "/app/backend/.env"
        try:
            with open(env_path, 'r') as f:
                for line in f:
                    if line.startswith('USE_EXTERNAL_STORAGE='):
                        value = line.split('=')[1].strip().strip('"').lower()
                        return 'external' if value == 'true' else 'local'
        except Exception as e:
            logger.error(f"Erro ao ler .env: {e}")
        
        return 'local'  # Default
    
    def switch_to_local_storage(self) -> bool:
        """Troca para armazenamento local"""
        env_path = "/app/backend/.env"
        
        try:
            # Ler arquivo
            with open(env_path, 'r') as f:
                lines = f.readlines()
            
            # Atualizar linha
            new_lines = []
            updated = False
            for line in lines:
                if line.startswith('USE_EXTERNAL_STORAGE='):
                    new_lines.append('USE_EXTERNAL_STORAGE="false"\n')
                    updated = True
                else:
                    new_lines.append(line)
            
            if updated:
                # Escrever de volta
                with open(env_path, 'w') as f:
                    f.writelines(new_lines)
                
                # Atualizar variável de ambiente
                os.environ['USE_EXTERNAL_STORAGE'] = 'false'
                
                logger.info("🔄 FALLBACK: Trocado para ARMAZENAMENTO LOCAL")
                logger.info("   Arquivos agora serão salvos em /data/uploads")
                self.current_mode = 'local'
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Erro ao trocar para local storage: {e}")
            return False
    
    def switch_to_external_storage(self) -> bool:
        """Troca para armazenamento externo"""
        env_path = "/app/backend/.env"
        
        try:
            # Ler arquivo
            with open(env_path, 'r') as f:
                lines = f.readlines()
            
            # Atualizar linha
            new_lines = []
            updated = False
            for line in lines:
                if line.startswith('USE_EXTERNAL_STORAGE='):
                    new_lines.append('USE_EXTERNAL_STORAGE="true"\n')
                    updated = True
                else:
                    new_lines.append(line)
            
            if updated:
                # Escrever de volta
                with open(env_path, 'w') as f:
                    f.writelines(new_lines)
                
                # Atualizar variável de ambiente
                os.environ['USE_EXTERNAL_STORAGE'] = 'true'
                
                logger.info("🔄 RECOVERY: Trocado para ARMAZENAMENTO EXTERNO")
                logger.info(f"   Arquivos agora serão salvos em {self.external_host}:{self.external_port}")
                self.current_mode = 'external'
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Erro ao trocar para external storage: {e}")
            return False
    
    async def monitor_loop(self):
        """Loop principal de monitoramento"""
        logger.info("🚀 Health Monitor Loop INICIADO")
        self.is_running = True
        
        # Detectar modo inicial
        self.current_mode = self.get_current_storage_mode()
        logger.info(f"📊 Modo inicial: {self.current_mode.upper()}")
        
        while self.is_running:
            try:
                self.last_check_time = datetime.now(timezone.utc)
                
                # Verificar saúde do servidor externo
                is_healthy = await self.check_external_storage_health()
                
                if is_healthy:
                    self.consecutive_failures = 0
                    self.consecutive_successes += 1
                    
                    # Se estamos em modo local e servidor voltou, tentar reconectar
                    if self.current_mode == 'local' and self.consecutive_successes >= 3:
                        logger.info("🎉 Servidor externo RECUPERADO e ESTÁVEL!")
                        logger.info(f"   ({self.consecutive_successes} checks consecutivos OK)")
                        logger.info("🔄 Iniciando AUTO-RECOVERY para external storage...")
                        
                        if self.switch_to_external_storage():
                            logger.info("✅ AUTO-RECOVERY COMPLETO")
                            self.consecutive_successes = 0
                        else:
                            logger.error("❌ AUTO-RECOVERY FALHOU")
                
                else:
                    self.consecutive_successes = 0
                    self.consecutive_failures += 1
                    
                    logger.warning(f"⚠️ Falha {self.consecutive_failures}/{self.max_failures}")
                    
                    # Se atingiu máximo de falhas, fazer fallback
                    if self.consecutive_failures >= self.max_failures and self.current_mode == 'external':
                        logger.error("🚨 SERVIDOR EXTERNO INDISPONÍVEL!")
                        logger.error(f"   {self.max_failures} tentativas falharam consecutivamente")
                        logger.info("🔄 Iniciando AUTO-FALLBACK para local storage...")
                        
                        if self.switch_to_local_storage():
                            logger.info("✅ AUTO-FALLBACK COMPLETO")
                            logger.info("   Sistema continuará funcionando com armazenamento local")
                            self.consecutive_failures = 0
                        else:
                            logger.error("❌ AUTO-FALLBACK FALHOU")
                
                # Log de status a cada 10 checks
                if self.consecutive_successes > 0 and self.consecutive_successes % 10 == 0:
                    logger.info(f"📊 Status: {self.current_mode.upper()} - {self.consecutive_successes} checks OK consecutivos")
                
                # Aguardar próximo check
                await asyncio.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"💥 Erro no monitor loop: {type(e).__name__}: {str(e)}")
                await asyncio.sleep(self.check_interval)
    
    def start(self):
        """Inicia o serviço de monitoramento em background"""
        asyncio.create_task(self.monitor_loop())
        logger.info("✅ Health Monitor Service ATIVO")
    
    def stop(self):
        """Para o serviço de monitoramento"""
        self.is_running = False
        logger.info("🛑 Health Monitor Service PARADO")


# Instância global do serviço
health_monitor = HealthMonitorService()
