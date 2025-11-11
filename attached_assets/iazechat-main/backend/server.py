from fastapi import FastAPI, APIRouter, HTTPException, UploadFile, File, WebSocket, WebSocketDisconnect, Depends, Header, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import socket
import logging
import asyncio
from pathlib import Path
from typing import List, Optional, Dict, Set, Tuple, Any
import uuid
from datetime import datetime, timezone, timedelta
import bcrypt
import jwt
import aiofiles
from models import *
from tenant_middleware import detect_tenant, get_current_tenant, apply_tenant_filter, TenantContext, tenant_context as global_tenant_context
from tenant_helpers import get_tenant_filter, get_request_tenant, Tenant
from ai_service import ai_service
import mimetypes
import re

# Logger dedicado para IA (compartilhado com ai_service.py)
ai_logger = logging.getLogger("ai_agent")
ai_logger.setLevel(logging.INFO)

# Se não tiver handlers ainda, adicionar
if not ai_logger.handlers:
    file_handler = logging.FileHandler("/var/log/ai_agent.log")
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    file_handler.setFormatter(formatter)
    ai_logger.addHandler(file_handler)
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    ai_logger.addHandler(console_handler)

# Função auxiliar para detectar formato de Usuário/Senha
def extract_credentials_from_message(text: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Detecta usuário e senha em diferentes formatos:
    - Usuário: 47649510 / usuario: 47649510 / USUARIO: 47649510 / USUÁRIO: 47649510
    - Senha: 59960260 / senha: 59960260 / SENHA: 59960260
    """
    import re
    
    # Padrões para detectar usuário (case-insensitive)
    user_patterns = [
        r'usu[aá]rio\s*:\s*(\S+)',  # Usuário: / usuário: / USUÁRIO:
        r'usuario\s*:\s*(\S+)',      # usuario: / USUARIO:
        r'user\s*:\s*(\S+)',         # user: / USER:
    ]
    
    # Padrões para detectar senha (case-insensitive)
    pass_patterns = [
        r'senha\s*:\s*(\S+)',        # Senha: / senha: / SENHA:
        r'password\s*:\s*(\S+)',     # password: / PASSWORD:
        r'pass\s*:\s*(\S+)',         # pass: / PASS:
    ]
    
    user = None
    password = None
    
    # Tentar extrair usuário
    for pattern in user_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            user = match.group(1).strip()
            break
    
    # Tentar extrair senha
    for pattern in pass_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            password = match.group(1).strip()
            break
    
    return user, password

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Import external storage AFTER loading .env
from external_storage_service import external_storage

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'support_chat')]

# JWT Secret
JWT_SECRET = os.environ.get('JWT_SECRET', 'sua-chave-secreta-super-segura-aqui')

# Inicializar dependências compartilhadas
import dependencies
dependencies.set_db(db)
dependencies.set_secret_key(JWT_SECRET)
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')

# Uploads directory - PERSISTENTE com fallback
try:
    UPLOADS_DIR = Path("/data/uploads")
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    # Testar se consegue escrever
    test_file = UPLOADS_DIR / ".test"
    test_file.touch()
    test_file.unlink()
    print(f"✅ Uploads directory: {UPLOADS_DIR} (persistente)")
except Exception as e:
    # Fallback para diretório local se /data não estiver disponível
    UPLOADS_DIR = ROOT_DIR / "uploads"
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    print(f"⚠️ Using fallback uploads directory: {UPLOADS_DIR}")
    print(f"   Reason: {e}")

app = FastAPI()
api_router = APIRouter(prefix="/api")

# Adicionar db ao app.state para acesso via dependency injection
app.state.db = db


@app.on_event("startup")
async def startup_event():
    """Inicia background tasks ao iniciar o servidor"""
    asyncio.create_task(check_department_timeouts())
    asyncio.create_task(reactivate_ai_after_timeout())
    print("✅ Background tasks iniciadas: timeout de departamentos e reativação de IA")
    
    # Iniciar scheduler de backup automático
    try:
        from backup_scheduler import start_backup_scheduler
        start_backup_scheduler()
        print("✅ Scheduler de backup automático iniciado")
    except Exception as e:
        print(f"❌ Erro ao iniciar scheduler de backup: {e}")
    
    # Iniciar scheduler de limpeza de memória da IA
    try:
        from ai_memory_cleanup_scheduler import ai_memory_cleanup_scheduler
        ai_memory_cleanup_scheduler.start()
        print("✅ Scheduler de limpeza de memória da IA iniciado")
    except Exception as e:
        print(f"❌ Erro ao iniciar scheduler de limpeza de memória: {e}")
    
    # ⚡ DESATIVADO: WhatsApp Polling (conflito com WPPConnect)
    # try:
    #     from whatsapp_polling_service import polling_service
    #     asyncio.create_task(polling_service.start())
    #     print("✅ WhatsApp Polling Service iniciado (verifica mensagens a cada 10s)")
    # except Exception as e:
    #     print(f"❌ Erro ao iniciar WhatsApp Polling: {e}")
    print("⚡ WhatsApp Polling DESATIVADO (usando WPPConnect direto)")
    
    # ⚡ DESATIVADO: Health Monitor estava causando lentidão tentando conectar ao servidor antigo
    # try:
    #     from health_monitor_service import health_monitor
    #     health_monitor.start()
    #     print("✅ Health Monitor Service iniciado (auto-recovery ativo)")
    # except Exception as e:
    #     print(f"❌ Erro ao iniciar Health Monitor: {e}")
    print("⚡ Health Monitor DESATIVADO para melhor performance")


# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.user_sessions: Dict[str, str] = {}  # user_id -> session_id
    
    async def connect(self, websocket: WebSocket, user_id: str, session_id: str):
        await websocket.accept()
        print(f"🔌 [WebSocket CONNECT] user_id: {user_id}, session_id: {session_id}")
        
        # Se já existe outra sessão, desconectar a antiga
        if user_id in self.user_sessions and self.user_sessions[user_id] != session_id:
            print(f"   ⚠️ Nova sessão detectada para {user_id}, desconectando sessão antiga")
            await self.disconnect_user(user_id)
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)
        self.user_sessions[user_id] = session_id
        print(f"   ✅ Total de conexões ativas agora: {len(self.active_connections)}")
    
    async def disconnect_user(self, user_id: str):
        if user_id in self.active_connections:
            for conn in list(self.active_connections[user_id]):
                try:
                    await conn.send_json({"type": "force_logout", "reason": "Nova sessão iniciada"})
                    await conn.close()
                except:
                    pass
            del self.active_connections[user_id]
    
    def disconnect(self, websocket: WebSocket, user_id: str):
        print(f"🔌 [WebSocket DISCONNECT] user_id: {user_id}")
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
                if user_id in self.user_sessions:
                    del self.user_sessions[user_id]
                print(f"   ✅ User {user_id} completamente desconectado")
            print(f"   Total de conexões ativas agora: {len(self.active_connections)}")
    
    async def send_to_user(self, user_id: str, message: dict):
        print(f"📤 [send_to_user] Tentando enviar para user_id: {user_id}")
        print(f"   Active connections: {list(self.active_connections.keys())}")
        
        if user_id in self.active_connections:
            print(f"   ✅ User encontrado! Conexões ativas: {len(self.active_connections[user_id])}")
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                    print(f"   ✅ Mensagem enviada com sucesso via WebSocket para {user_id}")
                except Exception as e:
                    print(f"   ❌ ERRO ao enviar via WebSocket para {user_id}: {e}")
        else:
            print(f"   ⚠️ User {user_id} NÃO está em active_connections!")
    
    async def broadcast_to_agents(self, message: dict):
        agents = await db.agents.find({}, {"id": 1}).to_list(None)
        for agent in agents:
            await self.send_to_user(agent["id"], message)

manager = ConnectionManager()

# Health check endpoint para deploy (SEM autenticação)
health_router = APIRouter(tags=["Health"])

@app.get("/botoes-wa")
async def botoes_wa_page():
    """Página de demonstração dos botões interativos"""
    from fastapi.responses import FileResponse
    return FileResponse("/app/backend/botoes_page.html")

@health_router.get("/health")
async def health_check():
    """Health check endpoint para verificar se o sistema está funcionando"""
    try:
        # Verificar MongoDB
        await db.command('ping')
        return {
            "status": "healthy",
            "service": "backend",
            "mongodb": "connected",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "backend",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


@health_router.get("/storage-status")
async def storage_status():
    """Retorna status do sistema de armazenamento e Health Monitor"""
    try:
        from health_monitor_service import health_monitor
        
        return {
            "current_mode": health_monitor.current_mode or health_monitor.get_current_storage_mode(),
            "external_server": {
                "host": health_monitor.external_host,
                "port": health_monitor.external_port,
                "url": health_monitor.external_url
            },
            "monitor": {
                "is_running": health_monitor.is_running,
                "check_interval": health_monitor.check_interval,
                "consecutive_failures": health_monitor.consecutive_failures,
                "consecutive_successes": health_monitor.consecutive_successes,
                "max_failures": health_monitor.max_failures,
                "last_check": health_monitor.last_check_time.isoformat() if health_monitor.last_check_time else None
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        return {
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

# Helper para enviar mensagem de seleção de departamento
async def send_department_selection(ticket_id: str, client_id: str, reseller_id: Optional[str] = None, ticket_origin: str = "wa_suporte"):
    """Envia mensagem automática pedindo ao cliente para escolher um departamento
    
    Args:
        ticket_id: ID do ticket
        client_id: ID do cliente
        reseller_id: ID do reseller (para isolamento)
        ticket_origin: Origem do ticket ("wa_suporte", "whatsapp_starter", "ia")
    """
    # Buscar departamentos APENAS da origem correspondente
    query = {"origin": ticket_origin}
    if reseller_id:
        query["reseller_id"] = reseller_id
    
    departments = await db.departments.find(query).to_list(None)
    
    if not departments or len(departments) == 0:
        # Sem departamentos configurados para essa origem
        logger.warning(f"⚠️ Nenhum departamento encontrado para origem: {ticket_origin}")
        
        # **IMPORTANTE: Enviar mensagem ao cliente mesmo sem departamentos**
        message = {
            "id": str(uuid.uuid4()),
            "ticket_id": ticket_id,
            "from_type": "system",
            "kind": "text",
            "text": "⚠️ Aguarde um momento. Nosso sistema de atendimento está sendo configurado.",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "reseller_id": reseller_id
        }
        
        await db.messages.insert_one(message)
        
        # Enviar via WebSocket para o cliente (remover _id do MongoDB)
        message_to_send = {k: v for k, v in message.items() if k != '_id'}
        await manager.send_to_user(client_id, {
            "type": "new_message",
            "message": message_to_send
        })
        
        return
    
    logger.info(f"✅ Encontrados {len(departments)} departamentos para origem: {ticket_origin}")
    
    # Criar mensagem com botões
    buttons = []
    for dept in departments:
        buttons.append({
            "id": dept["id"],
            "label": dept["name"],
            "description": dept.get("description", "")
        })
    
    # Criar mensagem no banco
    message = {
        "id": str(uuid.uuid4()),
        "ticket_id": ticket_id,
        "from_type": "system",
        "kind": "department_selection",
        "text": "Você deseja o atendimento para qual área? Clique em uma das opções abaixo:",
        "buttons": buttons,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "reseller_id": reseller_id
    }
    
    await db.messages.insert_one(message)
    
    # Enviar via WebSocket para o cliente (remover _id do MongoDB)
    message_to_send = {k: v for k, v in message.items() if k != '_id'}
    await manager.send_to_user(client_id, {
        "type": "new_message",
        "message": message_to_send
    })
    
    # Marcar timestamp de quando enviou
    await db.tickets.update_one(
        {"id": ticket_id},
        {"$set": {"department_choice_sent_at": datetime.now(timezone.utc).isoformat()}}
    )

async def redirect_to_suporte_department(ticket_id: str, reseller_id: str, ticket_origin: str):
    """
    Redireciona ticket para departamento SUPORTE da mesma origem quando IA falha
    
    Args:
        ticket_id: ID do ticket
        reseller_id: ID do reseller
        ticket_origin: Origem do ticket ("wa_suporte" ou "whatsapp_starter")
    """
    logger.info(f"🔀 Redirecionando ticket {ticket_id} para SUPORTE de origem {ticket_origin}")
    
    # Buscar departamento SUPORTE da mesma origem
    suporte_dept = await db.departments.find_one({
        "reseller_id": reseller_id,
        "origin": ticket_origin,
        "name": {"$regex": "SUPORTE", "$options": "i"}  # Case insensitive
    })
    
    if not suporte_dept:
        logger.warning(f"⚠️ Departamento SUPORTE não encontrado para origem {ticket_origin}")
        logger.info(f"💡 Criando departamento SUPORTE automaticamente...")
        
        # Criar departamento SUPORTE automático
        suporte_dept = {
            "id": str(uuid.uuid4()),
            "reseller_id": reseller_id,
            "name": "SUPORTE",
            "description": f"Suporte técnico - {ticket_origin}",
            "origin": ticket_origin,
            "ai_enabled": False,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.departments.insert_one(suporte_dept)
        logger.info(f"✅ Departamento SUPORTE criado: {suporte_dept['id']}")
    
    # Atualizar ticket
    await db.tickets.update_one(
        {"id": ticket_id},
        {"$set": {
            "department_id": suporte_dept["id"],
            "department_name": suporte_dept["name"],
            "ai_disabled_until": (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    logger.info(f"✅ Ticket redirecionado para departamento SUPORTE ({suporte_dept['name']})")
    
    # Enviar mensagem informando
    message = {
        "id": str(uuid.uuid4()),
        "ticket_id": ticket_id,
        "from_type": "system",
        "kind": "text",
        "text": "⚠️ Redirecionando para atendimento humano...",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "reseller_id": reseller_id
    }
    await db.messages.insert_one(message)
    
    # Notificar cliente via WebSocket (remover _id do MongoDB)
    message_to_send = {k: v for k, v in message.items() if k != '_id'}
    ticket = await db.tickets.find_one({"id": ticket_id})
    if ticket:
        await manager.send_to_user(ticket["client_id"], {
            "type": "new_message",
            "message": message_to_send
        })


async def handle_ai_failure_fallback(ticket: Dict, reason: str, reseller_id: str):
    """
    Transfere ticket para ESPERA quando IA falha (timeout ou erro)
    Roteamento:
    - WhatsApp QR Code → Aba WHATSAPP (verde)
    - Site/Chat/WA Suporte → Aba WA SUPORTE (vermelha)
    """
    try:
        ai_logger.info(f"🚨 AI FAILURE FALLBACK ATIVADO")
        ai_logger.info(f"   Ticket ID: {ticket.get('id')}")
        ai_logger.info(f"   Motivo: {reason}")
        
        # 1. Identificar origem do cliente
        is_whatsapp_qr = (
            ticket.get('whatsapp_origin') == True or 
            ticket.get('whatsapp_instance') is not None or 
            ticket.get('whatsapp_connection_id') is not None or
            ticket.get('is_whatsapp') == True
        )
        
        if is_whatsapp_qr:
            ai_logger.info(f"   📱 Origem: WhatsApp QR Code → Transferindo para aba WHATSAPP")
            target_tab = "WHATSAPP"
        else:
            ai_logger.info(f"   💻 Origem: Site/Chat → Transferindo para aba WA SUPORTE")
            target_tab = "WA_SUPORTE"
        
        # 2. Desativar IA permanentemente (apenas atendente pode reativar)
        now = datetime.now(timezone.utc)
        ai_disabled_until = now + timedelta(hours=24)  # 24 horas (efetivamente permanente até atendente reativar)
        
        await db.tickets.update_one(
            {"id": ticket["id"]},
            {
                "$set": {
                    "status": "open",  # Mover para ESPERA (status 'open' para compatibilidade)
                    "ai_disabled": True,
                    "ai_disabled_until": ai_disabled_until.isoformat(),
                    "ai_disabled_reason": reason,
                    "ai_failure_at": now.isoformat(),
                    "requires_human_attention": True,
                    "updated_at": now.isoformat()
                }
            }
        )
        
        ai_logger.info(f"   ✅ Ticket atualizado: status=open, ai_disabled=True")
        
        # 3. Enviar mensagem ao cliente informando a transferência
        fallback_message_text = (
            "Desculpe, estou com dificuldades para processar sua mensagem no momento. "
            "Já estou transferindo você para um atendente humano que irá te ajudar em breve. "
            "Por favor, aguarde! 🙋‍♂️"
        )
        
        fallback_message = {
            "id": str(uuid.uuid4()),
            "ticket_id": ticket["id"],
            "from_type": "system",
            "from_name": "Sistema",
            "text": fallback_message_text,
            "created_at": now.isoformat(),
            "reseller_id": reseller_id,
            "kind": "text",
            "is_ai_failure_notice": True
        }
        
        await db.messages.insert_one(fallback_message)
        ai_logger.info(f"   ✅ Mensagem de transferência enviada ao cliente")
        
        # 4. Enviar via WebSocket
        message_to_send = {k: v for k, v in fallback_message.items() if k != '_id'}
        await manager.send_to_user(ticket["client_id"], {
            "type": "new_message",
            "message": message_to_send
        })
        
        # 5. Atualizar última mensagem do ticket
        await db.tickets.update_one(
            {"id": ticket["id"]},
            {"$set": {
                "last_message": {
                    "text": fallback_message_text[:100],
                    "from_type": "system",
                    "created_at": fallback_message["created_at"]
                }
            }}
        )
        
        ai_logger.info(f"   🎯 Ticket transferido para {target_tab} - ESPERA")
        ai_logger.info(f"   🔒 IA desativada até atendente reativar manualmente")
        ai_logger.info(f"🟢 AI FAILURE FALLBACK CONCLUÍDO")
        
    except Exception as e:
        ai_logger.error(f"❌ ERRO no fallback da IA: {e}")
        import traceback
        ai_logger.error(traceback.format_exc())

async def process_message_with_ai(ticket: Dict, message_text: str, reseller_id: str):
    """Processa mensagem e gera resposta da IA se houver agente vinculado"""
    ai_logger.info("🟢 " + "="*80)
    ai_logger.info(f"🔍 NOVA MENSAGEM RECEBIDA PARA PROCESSAMENTO IA")
    ai_logger.info(f"📋 Ticket ID: {ticket.get('id')}")
    ai_logger.info(f"👤 Cliente: {ticket.get('client_name', 'N/A')}")
    ai_logger.info(f"🏢 Reseller ID: {reseller_id}")
    ai_logger.info(f"💬 Mensagem: {message_text[:100]}...")
    
    try:
        # 🆕 VERIFICAR CONTROLE GLOBAL/INDIVIDUAL DA IA
        ai_logger.info(f"🔍 Verificando controle de IA...")
        
        # Buscar config global
        if reseller_id:
            config = await db.reseller_configs.find_one({"reseller_id": reseller_id}) or {}
        else:
            config = await db.config.find_one({"id": "config"}) or {}
        
        ai_globally_enabled = config.get("ai_globally_enabled", True)  # Default: ativado
        ai_logger.info(f"   🌍 IA Global: {'ATIVADA' if ai_globally_enabled else 'DESATIVADA'}")
        
        # Verificar controle individual do ticket
        ticket_ai_enabled = ticket.get("ai_enabled")  # null, true ou false
        ticket_ai_manually_controlled = ticket.get("ai_manually_controlled", False)
        
        if ticket_ai_manually_controlled:
            ai_logger.info(f"   🎯 Controle Manual: {'ATIVADA' if ticket_ai_enabled else 'DESATIVADA'}")
        else:
            ai_logger.info(f"   🎯 Controle Manual: Não configurado (segue global)")
        
        # Decidir se IA deve responder
        should_ai_respond = ai_globally_enabled  # Padrão: seguir global
        
        # Controle individual sobrescreve global
        if ticket_ai_manually_controlled:
            should_ai_respond = ticket_ai_enabled
        
        if not should_ai_respond:
            ai_logger.info(f"❌ IA DESATIVADA para este ticket")
            ai_logger.info(f"   Motivo: {'Controle manual' if ticket_ai_manually_controlled else 'Configuração global'}")
            ai_logger.info("🔴 " + "="*80)
            return
        
        ai_logger.info(f"✅ IA ATIVADA - Processando mensagem...")
        
        # Verificar se IA foi desativada manualmente (compatibilidade com código antigo)
        ai_disabled_until = ticket.get("ai_disabled_until")
        if ai_disabled_until:
            try:
                disabled_until = datetime.fromisoformat(ai_disabled_until)
                if datetime.now(timezone.utc) < disabled_until:
                    ai_logger.info(f"❌ IA DESATIVADA TEMPORARIAMENTE para ticket {ticket['id']} até {disabled_until}")
                    ai_logger.info("🔴 " + "="*80)
                    return
                else:
                    ai_logger.info(f"✅ Tempo de desativação expirou, IA pode responder novamente")
            except Exception as e:
                ai_logger.warning(f"⚠️ Erro ao verificar ai_disabled_until: {e}")
        
        # Verificar se o ticket tem departamento
        department_id = ticket.get("department_id")
        ai_logger.info(f"📂 Verificando departamento...")
        ai_logger.info(f"   Department ID: {department_id}")
        
        if not department_id:
            ai_logger.info(f"❌ BLOQUEIO: Ticket {ticket['id']} sem departamento atribuído")
            ai_logger.info(f"💡 Ação necessária: Cliente deve selecionar um departamento")
            ai_logger.info("🔴 " + "="*80)
            return
        
        # Buscar departamento
        ai_logger.info(f"🔎 Buscando departamento no banco de dados...")
        department = await db.departments.find_one({"id": department_id, "reseller_id": reseller_id})
        
        if not department:
            ai_logger.error(f"💥 ERRO: Departamento {department_id} não encontrado no banco!")
            ai_logger.info("🔴 " + "="*80)
            return
        
        ai_logger.info(f"✅ Departamento encontrado:")
        ai_logger.info(f"   Nome: {department.get('name')}")
        ai_logger.info(f"   AI Agent ID: {department.get('ai_agent_id', 'NENHUM')}")
        
        if not department.get("ai_agent_id"):
            ai_logger.info(f"❌ BLOQUEIO: Departamento '{department.get('name')}' sem IA vinculada")
            ai_logger.info(f"💡 Ação necessária: Vincular um agente IA ao departamento")
            ai_logger.info("🔴 " + "="*80)
            return
        
        # Buscar agente IA
        ai_logger.info(f"🔎 Buscando agente IA no banco de dados...")
        ai_agent = await db.ai_agents.find_one({
            "id": department["ai_agent_id"],
            "reseller_id": reseller_id,
            "is_active": True
        })
        
        if not ai_agent:
            ai_logger.error(f"💥 ERRO: Agente IA {department['ai_agent_id']} não encontrado ou inativo!")
            ai_logger.info(f"💡 Ação necessária: Verificar se agente IA existe e está ativo")
            ai_logger.info("🔴 " + "="*80)
            return
        
        ai_logger.info(f"✅ Agente IA encontrado:")
        ai_logger.info(f"   Nome: {ai_agent.get('name')}")
        ai_logger.info(f"   ID: {ai_agent.get('id')}")
        ai_logger.info(f"   Ativo: {ai_agent.get('is_active')}")
        ai_logger.info(f"   Modelo: {ai_agent.get('llm_provider', 'N/A')}/{ai_agent.get('llm_model', 'N/A')}")
        
        # REMOVIDO: Verificação de linked_agents e assigned_agent_id
        # IA responde SEMPRE que o departamento tem IA configurada e ativa
        
        ai_logger.info(f"🎉 TODAS AS VERIFICAÇÕES PASSARAM!")
        ai_logger.info(f"🤖 IA '{ai_agent.get('name', 'Sem nome')}' vai processar QUALQUER mensagem do cliente")
        
        # Buscar histórico de mensagens do ticket (LIMITADO a últimas 10 para evitar Context Window Exceeded)
        ai_logger.info(f"📚 Carregando histórico de mensagens (últimas 10)...")
        all_messages = await db.messages.find({"ticket_id": ticket["id"]}).sort("created_at", -1).limit(10).to_list(10)
        # Reverter ordem (mais antigas primeiro)
        messages = list(reversed(all_messages))
        ai_logger.info(f"   {len(messages)} mensagens carregadas")
        
        # Truncar mensagens muito longas para economizar tokens
        for msg in messages:
            if msg.get("text") and len(msg["text"]) > 500:
                original_len = len(msg["text"])
                msg["text"] = msg["text"][:500] + "..."
                ai_logger.info(f"   ⚠️ Mensagem truncada: {original_len} → 500 caracteres")
        
        # Buscar dados do cliente (para credenciais se permitido)
        ai_logger.info(f"👤 Buscando dados do cliente...")
        client = await db.users.find_one({"id": ticket["client_id"], "reseller_id": reseller_id})
        client_data = {
            "pinned_user": client.get("pinned_user") if client else None,
            "pinned_pass": client.get("pinned_pass") if client else None
        }
        ai_logger.info(f"   Cliente: {client.get('name', 'N/A') if client else 'N/A'}")
        ai_logger.info(f"   Credenciais disponíveis: {bool(client_data['pinned_user'] or client_data['pinned_pass'])}")
        
        # Gerar resposta da IA com TIMEOUT de 2 minutos
        ai_logger.info(f"🚀 Chamando serviço de IA para gerar resposta...")
        ai_logger.info(f"⏱️ Timeout configurado: 120 segundos (2 minutos)")
        
        try:
            # Adicionar timeout de 2 minutos (120 segundos)
            ai_response = await asyncio.wait_for(
                ai_service.generate_response(
                    agent_config=ai_agent,
                    message=message_text,
                    conversation_history=messages,
                    client_data=client_data
                ),
                timeout=120.0  # 2 minutos
            )
            
            if not ai_response:
                ai_logger.error("💥 ERRO: IA não gerou resposta (retornou None)")
                ai_logger.error("💡 Transferindo para atendente humano...")
                await handle_ai_failure_fallback(
                    ticket=ticket,
                    reason="IA retornou resposta vazia",
                    reseller_id=reseller_id
                )
                ai_logger.info("🔴 " + "="*80)
                return
                
        except asyncio.TimeoutError:
            ai_logger.error("⏱️ TIMEOUT: IA não respondeu em 2 minutos")
            ai_logger.error("💡 Transferindo para atendente humano...")
            await handle_ai_failure_fallback(
                ticket=ticket,
                reason="Timeout de 2 minutos - IA não respondeu a tempo",
                reseller_id=reseller_id
            )
            ai_logger.info("🔴 " + "="*80)
            return
            
        except Exception as e:
            ai_logger.error(f"💥 ERRO na chamada da IA: {e}")
            ai_logger.error("💡 Transferindo para atendente humano...")
            import traceback
            ai_logger.error(traceback.format_exc())
            await handle_ai_failure_fallback(
                ticket=ticket,
                reason=f"Erro na IA: {str(e)}",
                reseller_id=reseller_id
            )
            ai_logger.info("🔴 " + "="*80)
            return
        
        # Aguardar tempo de resposta para humanização (response_delay_seconds)
        delay_seconds = ai_agent.get("response_delay_seconds", 3)
        if delay_seconds > 0:
            ai_logger.info(f"⏱️ Aguardando {delay_seconds} segundos para humanizar resposta...")
            await asyncio.sleep(delay_seconds)
        
        # Criar mensagem de resposta da IA
        ai_logger.info(f"💾 Salvando resposta da IA no banco de dados...")
        ai_message = {
            "id": str(uuid.uuid4()),
            "ticket_id": ticket["id"],
            "from_type": "ai",
            "from_name": ai_agent.get("name", "Assistente IA"),
            "text": ai_response,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "reseller_id": reseller_id
        }
        
        await db.messages.insert_one(ai_message)
        ai_logger.info(f"✅ Mensagem da IA salva com sucesso (ID: {ai_message['id']})")
        
        # Atualizar última mensagem do ticket
        await db.tickets.update_one(
            {"id": ticket["id"]},
            {"$set": {
                "last_message": {
                    "text": ai_response[:100],
                    "from_type": "ai",
                    "created_at": ai_message["created_at"]
                },
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        ai_logger.info(f"✅ Ticket atualizado com última mensagem da IA")
        ai_logger.info(f"🎉 PROCESSO COMPLETO! IA respondeu com sucesso")
        ai_logger.info("🟢 " + "="*80)
        
        # Enviar via WebSocket para cliente e atendentes (remover _id do MongoDB)
        ai_logger.info(f"📡 Enviando mensagem via WebSocket...")
        ai_logger.info(f"   Cliente ID: {ticket['client_id']}")
        
        ai_message_to_send = {k: v for k, v in ai_message.items() if k != '_id'}
        await manager.send_to_user(ticket["client_id"], {
            "type": "new_message",
            "message": ai_message_to_send
        })
        ai_logger.info(f"   ✅ Enviado para cliente")
        
        # Enviar para atendentes do departamento
        agents_in_dept = await db.agents.find({
            "reseller_id": reseller_id,
            "departments": department_id
        }).to_list(None)
        
        ai_logger.info(f"   👥 Atendentes no departamento: {len(agents_in_dept)}")
        
        for agent in agents_in_dept:
            await manager.send_to_user(agent["id"], {
                "type": "new_message",
                "message": ai_message_to_send  # ✅ Usar versão sem _id
            })
            ai_logger.info(f"   ✅ Enviado para atendente: {agent.get('name', agent['id'][:10])}")
        
        ai_logger.info(f"📡 Todas mensagens WebSocket enviadas com sucesso!")
        ai_logger.info(f"✅ IA respondeu no ticket {ticket['id']}")
        
    except Exception as e:
        ai_logger.error("💥 " + "="*80)
        ai_logger.error(f"💥 ERRO CRÍTICO ao processar mensagem com IA!")
        ai_logger.error(f"   Tipo: {type(e).__name__}")
        ai_logger.error(f"   Mensagem: {str(e)}")
        import traceback
        ai_logger.error(f"   Traceback:\n{traceback.format_exc()}")
        ai_logger.error("💥 " + "="*80)
        
        # **FALLBACK: Redirecionar para SUPORTE da mesma origem**
        try:
            ticket_origin = ticket.get("ticket_origin", "wa_suporte")
            ai_logger.info(f"🔀 Iniciando fallback: redirecionar para SUPORTE de {ticket_origin}")
            await redirect_to_suporte_department(
                ticket_id=ticket["id"],
                reseller_id=reseller_id,
                ticket_origin=ticket_origin
            )
        except Exception as fallback_error:
            ai_logger.error(f"❌ Erro ao executar fallback: {fallback_error}")

async def call_auto_search(ticket_id: str, whatsapp: str, source: str):
    """
    Chama a busca automática de credenciais
    """
    try:
        import httpx
        
        backend_url = os.environ.get('REACT_APP_BACKEND_URL', 'http://localhost:8001')
        
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                f"{backend_url}/api/auto-search-credentials",
                json={
                    "ticket_id": ticket_id,
                    "whatsapp": whatsapp,
                    "source": source
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Busca automática iniciada: {data}")
            else:
                logger.warning(f"⚠️ Erro na busca automática: {response.status_code}")
                
    except Exception as e:
        logger.error(f"❌ Erro ao chamar busca automática: {e}")

# Background task para verificar timeouts
async def check_department_timeouts():
    """Verifica tickets aguardando escolha de departamento e aplica timeout"""
    while True:
        try:
            await asyncio.sleep(30)  # Verificar a cada 30 segundos
            
            # Buscar tickets aguardando escolha de departamento
            tickets = await db.tickets.find({
                "awaiting_department_choice": True,
                "department_choice_sent_at": {"$exists": True, "$ne": None}
            }).to_list(None)
            
            now = datetime.now(timezone.utc)
            
            for ticket in tickets:
                sent_at = datetime.fromisoformat(ticket["department_choice_sent_at"])
                elapsed = (now - sent_at).total_seconds()
                
                # Buscar timeout do departamento padrão ou usar 120s
                default_dept = await db.departments.find_one({
                    "is_default": True,
                    "reseller_id": ticket.get("reseller_id")
                })
                
                timeout = default_dept.get("timeout_seconds", 120) if default_dept else 120
                
                if elapsed >= timeout:
                    # Timeout! Mover para departamento padrão
                    if default_dept:
                        await db.tickets.update_one(
                            {"id": ticket["id"]},
                            {"$set": {
                                "department_id": default_dept["id"],
                                "awaiting_department_choice": False,
                                "updated_at": datetime.now(timezone.utc).isoformat()
                            }}
                        )
                        
                        # Enviar mensagem de notificação
                        message = {
                            "id": str(uuid.uuid4()),
                            "ticket_id": ticket["id"],
                            "from_type": "system",
                            "kind": "text",
                            "text": f"⏱️ Tempo esgotado. Você foi direcionado automaticamente para: {default_dept['name']}",
                            "created_at": datetime.now(timezone.utc).isoformat(),
                            "reseller_id": ticket.get("reseller_id")
                        }
                        
                        await db.messages.insert_one(message)
                        
                        # Enviar via WebSocket (remover _id do MongoDB)
                        message_to_send = {k: v for k, v in message.items() if k != '_id'}
                        await manager.send_to_user(ticket["client_id"], {
                            "type": "new_message",
                            "message": message_to_send
                        })
        except Exception as e:
            print(f"Error in timeout checker: {e}")

async def reactivate_ai_after_timeout():
    """Verifica tickets com IA desativada e reativa após 1 hora"""
    while True:
        try:
            await asyncio.sleep(60)  # Verificar a cada 60 segundos
            
            # Buscar tickets com IA desativada
            tickets = await db.tickets.find({
                "ai_disabled_until": {"$exists": True, "$ne": None}
            }).to_list(None)
            
            now = datetime.now(timezone.utc)
            
            for ticket in tickets:
                try:
                    disabled_until = datetime.fromisoformat(ticket["ai_disabled_until"])
                    
                    if now >= disabled_until:
                        # Tempo expirou, reativar IA
                        await db.tickets.update_one(
                            {"id": ticket["id"]},
                            {
                                "$unset": {"ai_disabled_until": "", "ai_disabled_by": ""},
                                "$set": {"updated_at": now.isoformat()}
                            }
                        )
                        
                        logger.info(f"✅ IA reativada automaticamente para ticket {ticket['id']}")
                        
                        # Opcional: Enviar mensagem ao atendente informando
                        # (não enviar ao cliente para não poluir conversa)
                        
                except Exception as e:
                    logger.error(f"Erro ao processar ticket {ticket.get('id')}: {e}")
                    
        except Exception as e:
            logger.error(f"Erro na task de reativação de IA: {e}")



# Auth helpers
def create_token(user_id: str, user_type: str, reseller_id: Optional[str] = None) -> str:
    payload = {
        "user_id": user_id,
        "user_type": user_type,
        "reseller_id": reseller_id,
        "exp": datetime.now(timezone.utc) + timedelta(days=365)  # Token válido por 1 ano
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        # Token expirado - não deve acontecer com 365 dias
        logger.error("Token expirado (não deveria acontecer)")
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.InvalidTokenError as e:
        # Token inválido
        logger.error(f"Token inválido: {str(e)}")
        raise HTTPException(status_code=401, detail="Token inválido")
    except Exception as e:
        # Outro erro
        logger.error(f"Erro ao verificar token: {str(e)}")
        raise HTTPException(status_code=401, detail="Erro ao verificar token")

async def get_current_user(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = authorization.split(" ")[1]
    return verify_token(token)

# Validation helpers
def validate_user_password_format(text: str) -> bool:
    """
    Valida se texto está no formato permitido de usuário/senha
    Aceita variações de maiúscula/minúscula, com ou sem acentos, e com texto antes/depois
    
    Exemplos válidos:
    - usuario: xxx senha: xxx
    - Usuário: xxx Senha: xxx
    - esse aqui é seu usuario e senha segue\nUsuario: xxx\nSenha: xxx
    """
    # Padrão flexível que aceita:
    # - usuario/usuário em qualquer capitalização
    # - senha/password em qualquer capitalização
    # - texto antes e depois
    # - quebras de linha
    pattern = r'(usuario|usuário|user)\s*:\s*.+\s+(senha|password)\s*:\s*.+'
    
    # Buscar em qualquer lugar do texto (não apenas no início)
    return bool(re.search(pattern, text, re.IGNORECASE | re.DOTALL))

def has_user_password_keywords(text: str) -> bool:
    """Verifica se tem palavras-chave de usuário/senha"""
    keywords = ['usuario', 'usuário', 'senha', 'password', 'user']
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in keywords)

async def validate_sensitive_data(text: str, config: dict) -> Optional[str]:
    """Valida dados sensíveis baseado na config permitida"""
    text_lower = text.lower()
    allowed_data = config.get('allowed_data', {})
    
    # ✅ PRIORIDADE 1: Verificar se a mensagem exata está na lista de permitidas
    allowed_messages = allowed_data.get('allowed_messages', [])
    for allowed_msg in allowed_messages:
        if allowed_msg.strip().lower() == text.strip().lower():
            # Mensagem permitida explicitamente - NÃO validar
            return None
    
    # Se tem usuário/senha, validar formato
    if has_user_password_keywords(text):
        if not validate_user_password_format(text):
            return "❌ Formato de usuário/senha inválido. Use: 'usuario: XXXX senha: XXXX'"
    
    # CPF check
    cpf_match = re.search(r'\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b', text)
    if cpf_match:
        cpf_found = cpf_match.group()
        allowed_cpfs = allowed_data.get('cpfs', [])
        if cpf_found not in allowed_cpfs:
            return "❌ CPF não autorizado. Cadastre no Admin primeiro."
    
    # Email check
    email_match = re.search(r'[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}', text, re.IGNORECASE)
    if email_match:
        email_found = email_match.group()
        allowed_emails = allowed_data.get('emails', [])
        if email_found.lower() not in [e.lower() for e in allowed_emails]:
            return "❌ Email não autorizado. Cadastre no Admin primeiro."
    
    # Phone/WhatsApp check
    phone_match = re.search(r'\b(\+?55)?\D*\(?\d{2}\)?\D*\d{4,5}\D*\d{4}\b', text)
    if phone_match:
        phone_found = re.sub(r'\D', '', phone_match.group())
        allowed_phones = [re.sub(r'\D', '', p) for p in allowed_data.get('phones', [])]
        if phone_found not in allowed_phones:
            return "❌ Número de telefone não autorizado. Cadastre no Admin primeiro."
    
    # Random key check (chave aleatória PIX)
    if 'chave' in text_lower or 'pix' in text_lower:
        # Check se tem UUID ou chave aleatória
        random_key_match = re.search(r'\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b', text, re.IGNORECASE)
        if random_key_match:
            key_found = random_key_match.group()
            allowed_keys = allowed_data.get('random_keys', [])
            if key_found not in allowed_keys:
                return "❌ Chave aleatória não autorizada. Cadastre no Admin primeiro."
    
    return None

# Auth routes
@api_router.post("/auth/admin/login")
async def admin_login(data: AdminLogin):
    logging.info(f"🔍 Admin login attempt - password received: {data.password[:5]}...")
    
    # Buscar admin no MongoDB (user_type='admin')
    admin_user = await db.users.find_one({"user_type": "admin"})
    
    if not admin_user:
        logging.error("❌ Admin user not found in database")
        raise HTTPException(status_code=401, detail="Admin não encontrado")
    
    logging.info(f"📊 Admin found - email: {admin_user.get('email')}, hash exists: {bool(admin_user.get('pass_hash'))}")
    
    # Verificar senha com bcrypt
    if not bcrypt.checkpw(data.password.encode('utf-8'), admin_user['pass_hash'].encode('utf-8')):
        logging.error(f"❌ Invalid password for admin: {admin_user.get('email', 'unknown')}")
        logging.error(f"❌ Password tried: {data.password}, Hash in DB: {admin_user['pass_hash'][:30]}...")
        raise HTTPException(status_code=401, detail="Senha incorreta")
    
    logging.info(f"✅ Admin login successful: {admin_user.get('email', 'unknown')}")
    
    token = create_token(admin_user['id'], "admin")
    return TokenResponse(
        token=token, 
        user_type="admin", 
        user_data={
            "id": admin_user['id'],
            "reseller_id": admin_user.get('reseller_id'),
            "name": admin_user.get('name', 'Admin'),
            "email": admin_user.get('email', ''),
            "user_type": "admin"
        }
    )

@api_router.get("/test-system")
async def test_system():
    """Página de teste do sistema multi-tenant"""
    from fastapi.responses import HTMLResponse
    
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>TESTE SISTEMA</title>
        <style>
            body { font-family: Arial; max-width: 800px; margin: 50px auto; padding: 20px; }
            .box { background: white; padding: 20px; border: 2px solid #007bff; border-radius: 8px; margin: 20px 0; }
            button { padding: 15px 30px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; }
            button:hover { background: #0056b3; }
            .result { margin-top: 20px; padding: 15px; border-radius: 4px; }
            .success { background: #d4edda; color: #155724; }
            .error { background: #f8d7da; color: #721c24; }
            pre { background: #f5f5f5; padding: 10px; border-radius: 4px; overflow-x: auto; }
        </style>
    </head>
    <body>
        <h1>🔧 TESTE DO SISTEMA MULTI-TENANT</h1>
        
        <div class="box">
            <h2>Teste 1: Login fabioteste</h2>
            <button onclick="testLogin()">🔑 TESTAR LOGIN</button>
            <div id="loginResult"></div>
        </div>
        
        <div class="box">
            <h2>Teste 2: Buscar Tickets</h2>
            <p>Clique em "Testar Login" primeiro para obter o token</p>
            <button onclick="testTickets()">📊 BUSCAR TICKETS</button>
            <div id="ticketsResult"></div>
        </div>

        <script>
            let authToken = null;
            
            async function testLogin() {
                const resultDiv = document.getElementById('loginResult');
                resultDiv.innerHTML = '<div class="result">⏳ Testando login...</div>';
                
                try {
                    const response = await fetch('/api/auth/agent/login', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ login: 'fabioteste', password: '123' })
                    });
                    
                    const data = await response.json();
                    
                    if (response.ok) {
                        authToken = data.token;
                        resultDiv.innerHTML = `
                            <div class="result success">
                                <strong>✅ LOGIN OK!</strong><br><br>
                                <strong>Reseller ID:</strong> ${data.reseller_id || 'None (Admin)'}<br>
                                <strong>User Type:</strong> ${data.user_type}<br>
                                <strong>Token:</strong> ${data.token.substring(0, 50)}...<br><br>
                                Agora clique em "BUSCAR TICKETS" acima!
                            </div>
                        `;
                    } else {
                        resultDiv.innerHTML = `<div class="result error">❌ ERRO: ${data.detail}</div>`;
                    }
                } catch (error) {
                    resultDiv.innerHTML = `<div class="result error">❌ ERRO: ${error.message}</div>`;
                }
            }
            
            async function testTickets() {
                const resultDiv = document.getElementById('ticketsResult');
                
                if (!authToken) {
                    resultDiv.innerHTML = '<div class="result error">❌ Faça o login primeiro!</div>';
                    return;
                }
                
                resultDiv.innerHTML = '<div class="result">⏳ Buscando tickets...</div>';
                
                try {
                    const response = await fetch('/api/tickets', {
                        headers: { 'Authorization': `Bearer ${authToken}` }
                    });
                    
                    const tickets = await response.json();
                    
                    if (tickets.length === 0) {
                        resultDiv.innerHTML = `
                            <div class="result success">
                                <h3>✅ PERFEITO!</h3>
                                <p><strong>Retornou 0 tickets</strong></p>
                                <p>O filtro multi-tenant está funcionando corretamente!</p>
                                <p>fabioteste (revenda braia) não tem tickets.</p>
                            </div>
                        `;
                    } else {
                        const resellerIds = [...new Set(tickets.map(t => t.reseller_id || 'None'))];
                        resultDiv.innerHTML = `
                            <div class="result error">
                                <h3>❌ PROBLEMA DETECTADO!</h3>
                                <p><strong>Retornou ${tickets.length} tickets</strong></p>
                                <p>Deveria retornar 0 tickets!</p>
                                <p><strong>Reseller IDs encontrados:</strong></p>
                                <pre>${JSON.stringify(resellerIds, null, 2)}</pre>
                                <p><strong>Primeiros 3 tickets:</strong></p>
                                <pre>${JSON.stringify(tickets.slice(0, 3), null, 2)}</pre>
                            </div>
                        `;
                    }
                } catch (error) {
                    resultDiv.innerHTML = `<div class="result error">❌ ERRO: ${error.message}</div>`;
                }
            }
        </script>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html_content)

@api_router.post("/auth/agent-login-v2")
async def agent_login_v2(data: AgentLogin, request: Request):
    """Login de atendente/agent - VERSÃO CORRIGIDA"""
    # Procurar em users com user_type='agent' (collection agents NÃO é usada)
    agent = await db.users.find_one({
        "username": data.login,
        "user_type": "agent"
    })
    
    if not agent:
        raise HTTPException(status_code=401, detail="Agent não encontrado")
    
    # Validar senha (pode ser hash ou plain text)
    password_valid = False
    if agent.get("pass_hash"):
        password_valid = bcrypt.checkpw(data.password.encode(), agent["pass_hash"].encode())
    elif agent.get("password"):
        # Se senha não tem hash, comparar diretamente (para testes)
        password_valid = (data.password == agent["password"])
    
    if not password_valid:
        raise HTTPException(status_code=401, detail="Senha incorreta")
    
    if not agent.get("is_active", True):
        raise HTTPException(status_code=403, detail="Conta desativada")
    
    token = create_token(agent["id"], "agent", agent.get("reseller_id"))
    
    return TokenResponse(
        token=token, 
        user_type="agent", 
        user_data={
            "id": agent["id"],
            "name": agent["name"],
            "avatar": agent.get("custom_avatar") or agent.get("avatar", "")
        }, 
        reseller_id=agent.get("reseller_id")
    )

@api_router.post("/auth/agent/login")
async def agent_login(data: AgentLogin, request: Request):
    """Login de atendente/agent - REDIRECIONAR PARA V2"""
    return await agent_login_v2(data, request)

@api_router.post("/auth/client/login")
async def client_login(data: UserLogin, request: Request):
    tenant = get_request_tenant(request)
    reseller_id = tenant.reseller_id
    
    # 🆕 PRIORIDADE: Buscar usuário SEM filtro de tenant primeiro (evita duplicatas)
    user = await db.users.find_one({"whatsapp": data.whatsapp})
    
    # Se não encontrar, buscar com filtro de tenant
    if not user:
        query = {"whatsapp": data.whatsapp}
        if reseller_id:
            query["reseller_id"] = reseller_id
        user = await db.users.find_one(query)
    
    if not user:
        # First time - create user
        if len(data.pin) != 2 or not data.pin.isdigit():
            raise HTTPException(status_code=400, detail="PIN deve ter 2 dígitos")
        
        user_id = str(uuid.uuid4())
        pin_hash = bcrypt.hashpw(data.pin.encode(), bcrypt.gensalt()).decode()
        new_user = {
            "id": user_id,
            "whatsapp": data.whatsapp,
            "pin_hash": pin_hash,
            "display_name": "",
            "avatar": "",
            "custom_avatar": "",
            "gender": "",
            "pinned_user": "",
            "pinned_pass": "",
            "reseller_id": reseller_id,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.users.insert_one(new_user)
        user = new_user
    else:
        # Existing user
        if user.get("pin_hash"):
            if not bcrypt.checkpw(data.pin.encode(), user["pin_hash"].encode()):
                raise HTTPException(status_code=401, detail="PIN incorreto")
        else:
            # Set PIN
            if len(data.pin) != 2 or not data.pin.isdigit():
                raise HTTPException(status_code=400, detail="Crie PIN com 2 dígitos")
            pin_hash = bcrypt.hashpw(data.pin.encode(), bcrypt.gensalt()).decode()
            await db.users.update_one({"id": user["id"]}, {"$set": {"pin_hash": pin_hash}})
            user["pin_hash"] = pin_hash
    
    token = create_token(user["id"], "client", reseller_id)
    return TokenResponse(token=token, user_type="client", user_data={
        "id": user["id"],
        "whatsapp": user["whatsapp"],
        "display_name": user.get("display_name", ""),
        "avatar": user.get("custom_avatar") or user.get("avatar", ""),
        "pinned_user": user.get("pinned_user", ""),
        "pinned_pass": user.get("pinned_pass", "")
    }, reseller_id=reseller_id)

# User routes
@api_router.get("/users/me", response_model=UserMeResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user), response: Response = None):
    # 🆕 Buscar usuário SEM filtro de tenant (consolidado)
    user = await db.users.find_one({"id": current_user["user_id"]})
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    result = {
        "id": user["id"],
        "whatsapp": user["whatsapp"],
        "display_name": user.get("display_name", ""),
        "avatar": user.get("custom_avatar") or user.get("avatar", ""),
        "custom_avatar": user.get("custom_avatar", ""),  # 🆕 Retornar custom_avatar explicitamente
        "user_image": user.get("custom_avatar", ""),  # 🔬 Bypass gateway filter
        "gender": user.get("gender", ""),
        "pinned_user": user.get("pinned_user", ""),
        "pinned_pass": user.get("pinned_pass", "")
    }
    
    print(f"🔍 DEBUG /users/me - custom_avatar in result: {'custom_avatar' in result}")
    print(f"🔍 DEBUG /users/me - custom_avatar value: {result.get('custom_avatar')}")
    print(f"🔍 DEBUG /users/me - result keys: {list(result.keys())}")
    print(f"🔍 DEBUG /users/me - FULL RESULT: {result}")
    
    # 🆕 Adicionar headers para evitar cache
    if response:
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        response.headers["X-Custom-Avatar-Sent"] = "true"  # Header para debug
    
    import json
    print(f"🔍 DEBUG /users/me - JSON SERIALIZADO: {json.dumps(result)}")
    
    return result

@api_router.put("/users/me")
async def update_user(data: dict, current_user: dict = Depends(get_current_user)):
    update_data = {}
    if "display_name" in data:
        update_data["display_name"] = data["display_name"]
    if "avatar" in data:
        update_data["avatar"] = data["avatar"]
    if "custom_avatar" in data:
        update_data["custom_avatar"] = data["custom_avatar"]
    if "gender" in data:
        update_data["gender"] = data["gender"]
    
    if update_data:
        await db.users.update_one({"id": current_user["user_id"]}, {"$set": update_data})
    return {"ok": True}

@api_router.put("/users/me/pin")
async def update_user_pin(data: dict, current_user: dict = Depends(get_current_user)):
    """Atualiza o PIN do usuário atual"""
    pin = data.get("pin", "")
    if not pin or len(pin) != 2 or not pin.isdigit():
        raise HTTPException(status_code=400, detail="PIN deve ter exatamente 2 dígitos")
    
    pin_hash = bcrypt.hashpw(pin.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    await db.users.update_one({"id": current_user["user_id"]}, {"$set": {"pin_hash": pin_hash}})
    return {"ok": True}

@api_router.get("/users/whatsapp-popup-status")
async def check_whatsapp_popup_status(current_user: dict = Depends(get_current_user)):
    """Verifica se deve mostrar o pop-up de confirmação de WhatsApp"""
    user = await db.users.find_one({"id": current_user["user_id"]})
    if not user:
        return {"should_show": False}
    
    # Verificar se já perguntou na última semana (7 dias)
    asked_at = user.get("whatsapp_asked_at")
    if asked_at:
        try:
            asked_date = datetime.fromisoformat(asked_at)
            days_since_asked = (datetime.now(timezone.utc) - asked_date).days
            if days_since_asked < 7:
                return {"should_show": False, "days_until_next": 7 - days_since_asked}
        except:
            pass
    
    # Se nunca perguntou ou passou 1 semana, mostrar popup
    return {"should_show": True}

@api_router.put("/users/me/whatsapp-confirm")
async def confirm_whatsapp(data: dict, current_user: dict = Depends(get_current_user)):
    """Confirma o WhatsApp do usuário atual"""
    whatsapp = data.get("whatsapp", "")
    
    await db.users.update_one(
        {"id": current_user["user_id"]},
        {"$set": {
            "whatsapp_confirmed": whatsapp,
            "whatsapp_asked_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    return {"ok": True}

@api_router.put("/users/me/pin")
async def update_pin(data: dict, current_user: dict = Depends(get_current_user)):
    pin = data.get("pin", "")
    if len(pin) != 2 or not pin.isdigit():
        raise HTTPException(status_code=400, detail="PIN deve ter 2 dígitos")
    
    pin_hash = bcrypt.hashpw(pin.encode(), bcrypt.gensalt()).decode()
    await db.users.update_one({"id": current_user["user_id"]}, {"$set": {"pin_hash": pin_hash}})
    return {"ok": True}

@api_router.get("/users/name-popup-status")
async def check_name_popup_status(current_user: dict = Depends(get_current_user)):
    """Verifica se deve mostrar o pop-up de nome (após primeira mensagem)"""
    user = await db.users.find_one({"id": current_user["user_id"]})
    if not user:
        return {"should_show": False}
    
    # Se já tem nome cadastrado, não mostrar
    if user.get("display_name") and user.get("display_name").strip():
        return {"should_show": False, "has_name": True}
    
    # Se nunca perguntou, mostrar
    if not user.get("name_asked_at"):
        return {"should_show": True, "has_name": False}
    
    return {"should_show": False, "has_name": False}

@api_router.put("/users/me/name")
async def update_user_name(data: dict, current_user: dict = Depends(get_current_user)):
    """Atualiza o nome do usuário"""
    name = data.get("name", "").strip()
    
    # Validação: apenas nomes válidos (letras e espaços)
    if not name:
        raise HTTPException(status_code=400, detail="Nome não pode ser vazio")
    
    if len(name) < 2:
        raise HTTPException(status_code=400, detail="Nome muito curto")
    
    if len(name) > 50:
        raise HTTPException(status_code=400, detail="Nome muito longo")
    
    # Verificar se contém apenas letras, espaços e acentos
    import re
    if not re.match(r'^[A-Za-zÀ-ÿ\s]+$', name):
        raise HTTPException(status_code=400, detail="Nome deve conter apenas letras")
    
    # Verificar se não é uma frase (máximo 3 palavras)
    words = name.split()
    if len(words) > 3:
        raise HTTPException(status_code=400, detail="Digite apenas seu nome (máximo 3 palavras)")
    
    await db.users.update_one(
        {"id": current_user["user_id"]},
        {"$set": {
            "display_name": name,
            "name_asked_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    return {"ok": True, "name": name}

@api_router.post("/users/me/avatar")
async def upload_user_avatar(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    """Upload de foto de perfil do cliente"""
    if not file:
        raise HTTPException(status_code=400, detail="Nenhum arquivo enviado")
    
    # Validar tipo de arquivo
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Apenas imagens são permitidas")
    
    # Upload usando external storage service (automaticamente usa externo ou local)
    try:
        result = await external_storage.upload_file(file)
        
        if result.get('success'):
            url = result['url']
            
            # Atualizar custom_avatar do usuário
            await db.users.update_one(
                {"id": current_user["user_id"]},
                {"$set": {"custom_avatar": url}}
            )
            
            logger.info(f"✅ Avatar atualizado para user {current_user['user_id']}: {url}")
            
            return {"ok": True, "avatar_url": url}
        else:
            raise HTTPException(status_code=500, detail="Upload failed")
    
    except Exception as e:
        logger.error(f"❌ Erro ao fazer upload do avatar: {e}")
        raise HTTPException(status_code=500, detail=f"Erro no upload: {str(e)}")

# Agent routes (admin/reseller)
@api_router.get("/agents")
async def list_agents(request: Request, current_user: dict = Depends(get_current_user)):
    # ISOLAMENTO MULTI-TENANT: Listar agentes da collection users
    query = get_tenant_filter(request, current_user)
    query["user_type"] = "agent"
    
    agents = await db.users.find(query, {"_id": 0, "password": 0, "pass_hash": 0}).to_list(None)
    
    # Garantir que não há ObjectId nos resultados
    import json
    from bson import ObjectId
    
    def clean_objectid(obj):
        """Remove ObjectId recursivamente"""
        if isinstance(obj, dict):
            return {k: clean_objectid(v) for k, v in obj.items() if not isinstance(v, ObjectId)}
        elif isinstance(obj, list):
            return [clean_objectid(item) for item in obj]
        elif isinstance(obj, ObjectId):
            return str(obj)
        return obj
    
    agents = [clean_objectid(agent) for agent in agents]
    return agents


@api_router.get("/agents/me")
async def get_current_agent(current_user: dict = Depends(get_current_user)):
    """Retorna informações do agente logado - USA USERS"""
    if current_user["user_type"] != "agent":
        raise HTTPException(status_code=403, detail="Apenas agentes podem acessar")
    
    agent = await db.users.find_one({"id": current_user["user_id"], "user_type": "agent"})
    if not agent:
        raise HTTPException(status_code=404, detail="Agente não encontrado")
    
    return {
        "id": agent["id"],
        "name": agent.get("name", ""),
        "username": agent.get("username", ""),
        "department_ids": agent.get("department_ids", []),
        "avatar": agent.get("avatar", ""),
        "custom_avatar": agent.get("custom_avatar", "")
    }

@api_router.get("/agents/online-status")
async def get_online_status(request: Request):
    """Verifica status online dos agentes"""
    tenant = get_request_tenant(request)
    reseller_id = tenant.reseller_id
    
    # Verificar se admin ativou modo ausente manualmente
    config_query = {"reseller_id": reseller_id} if reseller_id else {}
    config = await db.reseller_configs.find_one(config_query) if reseller_id else await db.config.find_one({})
    
    if config and config.get("manual_away_mode"):
        return {"online": 0, "status": "away", "manual": True}
    
    # Buscar todos os agentes do reseller que estão conectados via WebSocket
    online_count = 0
    connected_user_ids = list(manager.active_connections.keys())
    
    if connected_user_ids:
        # Buscar usuários conectados que são agentes do reseller
        query = {
            "id": {"$in": connected_user_ids},
            "user_type": "agent"
        }
        if reseller_id:
            query["reseller_id"] = reseller_id
        
        online_agents = await db.users.find(query).to_list(None)
        online_count = len(online_agents)
    
    return {"online": online_count, "status": "online" if online_count > 0 else "offline", "manual": False}

@api_router.post("/agents")
async def create_agent(data: AgentCreate, request: Request, current_user: dict = Depends(get_current_user)):
    """Criar agente - SALVA EM USERS COM ISOLAMENTO MULTI-TENANT E VALIDAÇÕES ANTI-DUPLICATA"""
    # Admin ou Reseller podem criar agentes
    if current_user["user_type"] not in ["admin", "reseller"]:
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    # ISOLAMENTO: Determinar reseller_id correto
    reseller_id = current_user.get("reseller_id")
    
    # VALIDAÇÃO 1: Verificar se username já existe no mesmo tenant
    query = {"username": data.login, "user_type": "agent"}
    if reseller_id:
        query["reseller_id"] = reseller_id
    
    existing = await db.users.find_one(query)
    if existing:
        raise HTTPException(
            status_code=400, 
            detail=f"Username '{data.login}' já está em uso neste revendedor. Escolha outro login."
        )
    
    # VALIDAÇÃO 2: Gerar ID único e verificar se não existe
    max_attempts = 5
    agent_id = None
    for attempt in range(max_attempts):
        temp_id = str(uuid.uuid4())
        existing_id = await db.users.find_one({"id": temp_id})
        if not existing_id:
            agent_id = temp_id
            break
    
    if not agent_id:
        raise HTTPException(
            status_code=500, 
            detail="Erro ao gerar ID único. Tente novamente."
        )
    
    pass_hash = bcrypt.hashpw(data.password.encode(), bcrypt.gensalt()).decode()
    
    agent = {
        "id": agent_id,
        "name": data.name,
        "username": data.login,
        "password": data.password,  # Plain text também para compatibilidade
        "pass_hash": pass_hash,
        "email": f"{data.login}@{reseller_id}.agent.local" if reseller_id else f"{data.login}@agent.local",
        "user_type": "agent",
        "avatar": data.avatar or "",
        "custom_avatar": "",
        "department_ids": data.department_ids if data.department_ids else [],
        "reseller_id": reseller_id,
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    # VALIDAÇÃO 3: Tentar inserir e tratar erro de duplicata
    try:
        await db.users.insert_one(agent)
        logger.info(f"✅ Agente criado: {data.login} (ID: {agent_id}) - Reseller: {reseller_id}")
        return {"ok": True, "id": agent_id}
    except Exception as e:
        if "duplicate key" in str(e).lower() or "11000" in str(e):
            raise HTTPException(
                status_code=400,
                detail="Erro: Este login ou ID já existe. Tente outro."
            )
        raise HTTPException(status_code=500, detail=f"Erro ao criar agente: {str(e)}")

@api_router.put("/agents/{agent_id}")
async def update_agent(agent_id: str, data: dict, request: Request, current_user: dict = Depends(get_current_user)):
    """Atualizar agente - USA USERS COM ISOLAMENTO E ANTI-DUPLICATA"""
    if current_user["user_type"] not in ["admin", "reseller"]:
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    # ISOLAMENTO: Buscar com filtro de tenant
    tenant_filter = get_tenant_filter(request, current_user)
    query = {**tenant_filter, "id": agent_id, "user_type": "agent"}
    
    agent = await db.users.find_one(query)
    if not agent:
        raise HTTPException(status_code=404, detail="Agente não encontrado")
    
    update_data = {}
    
    # VALIDAÇÃO: Se está alterando login, verificar se não existe outro com mesmo login
    if "login" in data and data["login"] != agent.get("username"):
        reseller_id = current_user.get("reseller_id")
        existing_query = {"username": data["login"], "user_type": "agent", "id": {"$ne": agent_id}}
        if reseller_id:
            existing_query["reseller_id"] = reseller_id
        
        existing = await db.users.find_one(existing_query)
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Login '{data['login']}' já está em uso. Escolha outro."
            )
        update_data["username"] = data["login"]
    
    if "name" in data:
        update_data["name"] = data["name"]
    if "password" in data and data["password"]:
        update_data["pass_hash"] = bcrypt.hashpw(data["password"].encode(), bcrypt.gensalt()).decode()
        update_data["password"] = data["password"]
    if "avatar" in data:
        update_data["avatar"] = data["avatar"]
    if "department_ids" in data:
        update_data["department_ids"] = data["department_ids"] if data["department_ids"] else []
    
    try:
        await db.users.update_one(query, {"$set": update_data})
        logger.info(f"✅ Agente atualizado: {agent_id} - Login: {data.get('login', agent.get('username'))}")
        return {"ok": True}
    except Exception as e:
        if "duplicate key" in str(e).lower() or "11000" in str(e):
            raise HTTPException(
                status_code=400,
                detail="Erro: Este login já está em uso."
            )
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar agente: {str(e)}")
    return {"ok": True}

@api_router.delete("/agents/{agent_id}")
async def delete_agent(agent_id: str, request: Request, current_user: dict = Depends(get_current_user)):
    """Deletar agente - USA USERS COM ISOLAMENTO"""
    if current_user["user_type"] not in ["admin", "reseller"]:
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    # ISOLAMENTO: Buscar com filtro de tenant
    tenant_filter = get_tenant_filter(request, current_user)
    query = {**tenant_filter, "id": agent_id, "user_type": "agent"}
    
    agent = await db.users.find_one(query)
    if not agent:
        raise HTTPException(status_code=404, detail="Agente não encontrado")
    
    await db.users.delete_one(query)
    return {"ok": True}

@api_router.post("/users/{user_id}/confirm-whatsapp")
async def confirm_user_whatsapp(user_id: str, data: dict, current_user: dict = Depends(get_current_user)):
    """Salva WhatsApp confirmado pelo cliente"""
    whatsapp_confirmed = data.get("whatsapp", "")
    
    await db.users.update_one(
        {"id": user_id},
        {"$set": {
            "whatsapp_confirmed": whatsapp_confirmed,
            "whatsapp_asked_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    return {"ok": True}

@api_router.get("/users/{user_id}/should-ask-whatsapp")
async def should_ask_whatsapp(user_id: str):
    """Verifica se deve mostrar pop-up de WhatsApp"""
    user = await db.users.find_one({"id": user_id})
    if not user:
        return {"should_ask": False}
    
    # Verificar se já perguntou na última semana
    asked_at = user.get("whatsapp_asked_at")
    if asked_at:
        asked_date = datetime.fromisoformat(asked_at)
        days_since_asked = (datetime.now(timezone.utc) - asked_date).days
        if days_since_asked < 7:
            return {"should_ask": False, "days_until_next": 7 - days_since_asked}
    
    # Se nunca perguntou ou passou 1 semana, perguntar
    return {"should_ask": True}

# Ticket routes
@api_router.get("/tickets")
async def list_tickets(
    status: Optional[str] = None, 
    origin: Optional[str] = None,
    limit: Optional[int] = None,  # ✅ NOVO: Limitar quantidade
    request: Request = None, 
    current_user: dict = Depends(get_current_user)
):
    # ISOLAMENTO MULTI-TENANT: Usar função centralizada
    query = get_tenant_filter(request, current_user)
    
    if status:
        query["status"] = status
    
    # **NOVO: Filtro por origem (ticket_origin)**
    if origin:
        query["ticket_origin"] = origin
    
    # ============================================
    # REGRA ROBUSTA DE ACESSO POR TIPO DE USUÁRIO
    # ============================================
    
    user_type = current_user["user_type"]
    
    # 1. ADMIN: VÊ TUDO (sem filtro adicional)
    if user_type == "admin":
        pass  # Admin vê TODOS os tickets respeitando apenas tenant
    
    # 2. RESELLER: VÊ TUDO da sua revenda (já filtrado pelo tenant)
    elif user_type == "reseller":
        pass  # Reseller vê todos os tickets da revenda dele (já filtrado)
    
    # 3. AGENT: VÊ tickets dos departamentos que ele tem acesso
    elif user_type == "agent":
        agent_id = current_user["user_id"]
        reseller_id = current_user.get("reseller_id")
        
        # Buscar informações do agente
        agent = await db.users.find_one({"id": agent_id, "user_type": "agent"})
        
        if not agent:
            return []
        
        # MÉTODO 1: Verificar se agente tem department_ids (novo sistema)
        agent_dept_ids = agent.get("department_ids", [])
        
        if agent_dept_ids:
            query["$or"] = [
                {"department_id": {"$in": agent_dept_ids}},
                {"department_id": {"$exists": False}},
                {"department_id": None}
            ]
        else:
            # FALLBACK: Buscar departamentos onde o agente está listado (sistema antigo)
            logger.info(f"⚙️ Agente {agent.get('name')} usando fallback (sistema antigo)")
            
            departments = await db.departments.find({
                "reseller_id": reseller_id,
                "$or": [
                    {"agent_ids": []},  # Vazio = todos têm acesso
                    {"agent_ids": {"$exists": False}},  # Não existe = todos têm acesso
                    {"agent_ids": agent_id},  # String direta (bug antigo)
                    {"agent_ids": {"$in": [agent_id]}}  # Array com agente
                ]
            }, {"_id": 0, "id": 1, "name": 1}).to_list(None)
            
            if departments:
                dept_ids = [d["id"] for d in departments]
                logger.info(f"✅ Agente tem acesso a {len(departments)} departamento(s): {[d['name'] for d in departments]}")
                
                query["$or"] = [
                    {"department_id": {"$in": dept_ids}},  # Tickets dos departamentos
                    {"department_id": {"$exists": False}},  # Tickets sem departamento
                    {"department_id": None}  # Tickets com department_id null
                ]
            else:
                # ÚLTIMA TENTATIVA: Se não encontrou nenhum departamento, 
                # permitir ver todos os tickets da revenda (não bloquear)
                logger.warning(f"⚠️ Agente {agent.get('name')} sem departamentos! Liberando acesso total à revenda")
                # Não adiciona filtro adicional, usa apenas o filtro de tenant (reseller_id)
    
    # 4. CLIENT: Vê apenas seus próprios tickets
    elif user_type == "client":
        query["client_id"] = current_user["user_id"]
    
    # Buscar tickets (com limit opcional para performance)
    # ✅ OTIMIZAÇÃO: Se limit fornecido, usar. Senão busca todos.
    max_results = limit if limit else None
    
    # Sort por updated_at descendente (mais recentes primeiro)
    tickets = await db.tickets.find(query, {"_id": 0}).sort("updated_at", -1).to_list(max_results)
    
    logger.info(f"📊 Retornando {len(tickets)} tickets para user_type={user_type} (limit={max_results})")
    
    # ⚡ OTIMIZAÇÃO RADICAL: Enrich em lote usando aggregation
    # Buscar todos os IDs de uma vez
    ticket_ids = [t["id"] for t in tickets]
    client_ids = [t.get("client_id") for t in tickets if t.get("client_id")]
    
    # Buscar unread counts de todos os tickets de uma vez
    unread_pipeline = [
        {"$match": {
            "ticket_id": {"$in": ticket_ids},
            "sender_type": "client",
            "read": {"$ne": True}
        }},
        {"$group": {
            "_id": "$ticket_id",
            "count": {"$sum": 1}
        }}
    ]
    unread_results = {r["_id"]: r["count"] for r in await db.messages.aggregate(unread_pipeline).to_list(None)}
    
    # Buscar todos os clientes de uma vez
    users_map = {}
    if client_ids:
        users_cursor = db.users.find({"id": {"$in": client_ids}})
        async for user in users_cursor:
            users_map[user["id"]] = user
        
        # Se não encontrou em users, buscar em clients
        missing_ids = [cid for cid in client_ids if cid not in users_map]
        if missing_ids:
            clients_cursor = db.clients.find({"id": {"$in": missing_ids}})
            async for client in clients_cursor:
                users_map[client["id"]] = client
    
    # Buscar últimas mensagens de todos os tickets de uma vez
    last_messages_pipeline = [
        {"$match": {"ticket_id": {"$in": ticket_ids}}},
        {"$sort": {"created_at": -1}},
        {"$group": {
            "_id": "$ticket_id",
            "last_message": {"$first": "$$ROOT"}
        }}
    ]
    last_messages = {r["_id"]: r["last_message"] for r in await db.messages.aggregate(last_messages_pipeline).to_list(None)}
    
    # Buscar departments para pegar origin
    dept_ids = [t.get("department_id") for t in tickets if t.get("department_id")]
    departments_map = {}
    if dept_ids:
        depts_cursor = db.departments.find({"id": {"$in": dept_ids}}, {"id": 1, "origin": 1, "name": 1})
        async for dept in depts_cursor:
            departments_map[dept["id"]] = dept
    
    # Enrich tickets com dados em memória (super rápido)
    for ticket in tickets:
        ticket["unread_count"] = unread_results.get(ticket["id"], 0)
        
        # Adicionar department_origin para filtro no frontend
        if ticket.get("department_id"):
            dept = departments_map.get(ticket["department_id"])
            if dept:
                ticket["department_origin"] = dept.get("origin", "wa_suporte")
                ticket["department_name"] = dept.get("name", "")
        
        user = users_map.get(ticket.get("client_id"))
        if user:
            ticket["client_whatsapp"] = user.get("whatsapp") or user.get("phone")
            ticket["client_name"] = user.get("display_name") or user.get("name", "")
            ticket["client_avatar"] = user.get("custom_avatar") or user.get("avatar", "")
        
        last_msg = last_messages.get(ticket["id"])
        if last_msg:
            last_msg.pop("_id", None)
        ticket["last_message"] = last_msg
    
    # Sort: client messages first, then by recent
    tickets.sort(key=lambda t: (
        0 if t.get("last_message") and t.get("last_message", {}).get("from_type") == "client" else 1,
        -(datetime.fromisoformat(t.get("last_message", {}).get("created_at", "2000-01-01T00:00:00+00:00")).timestamp() if t.get("last_message") and t.get("last_message", {}).get("created_at") else 0)
    ))
    
    return tickets

@api_router.post("/tickets/{ticket_id}/mark-read")
async def mark_ticket_as_read(ticket_id: str, current_user: dict = Depends(get_current_user)):
    """Marca ticket como lido (zera contador de não lidas)"""
    if current_user["user_type"] != "agent":
        raise HTTPException(status_code=403, detail="Apenas agentes podem marcar como lido")
    
    await db.tickets.update_one(
        {"id": ticket_id},
        {"$set": {"unread_count": 0}}
    )
    return {"ok": True}

@api_router.put("/tickets/{ticket_id}/toggle-ai")
async def toggle_ticket_ai(ticket_id: str, data: dict, current_user: dict = Depends(get_current_user)):
    """
    Ativa ou desativa IA para um ticket específico
    - enabled: true = forçar IA ativa
    - enabled: false = forçar IA desativada
    - enabled: null = seguir configuração global
    """
    if current_user["user_type"] not in ["agent", "admin"]:
        raise HTTPException(status_code=403, detail="Apenas agentes e admins podem controlar a IA")
    
    enabled = data.get("enabled")  # true, false ou null
    
    ticket = await db.tickets.find_one({"id": ticket_id})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket não encontrado")
    
    # Atualizar ticket
    update_data = {
        "ai_manually_controlled": enabled is not None,  # Flag para indicar controle manual
        "ai_enabled": enabled,  # true, false ou null
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Se desabilitou, limpar ai_disabled_until para não conflitar
    if enabled == False:
        update_data["ai_disabled_until"] = None
    
    await db.tickets.update_one(
        {"id": ticket_id},
        {"$set": update_data}
    )
    
    logger.info(f"🤖 IA toggled para ticket {ticket_id}: enabled={enabled}")
    
    return {
        "ok": True,
        "ticket_id": ticket_id,
        "ai_enabled": enabled,
        "message": "IA ativada" if enabled else "IA desativada" if enabled == False else "IA seguindo configuração global"
    }

@api_router.post("/tickets/{ticket_id}/select-department")
async def select_department(ticket_id: str, data: dict, current_user: dict = Depends(get_current_user)):
    """Cliente seleciona um departamento"""
    department_id = data.get("department_id")
    if not department_id:
        raise HTTPException(status_code=400, detail="department_id é obrigatório")
    
    # Verificar se o departamento existe
    department = await db.departments.find_one({"id": department_id})
    if not department:
        raise HTTPException(status_code=404, detail="Departamento não encontrado")
    
    # Atualizar ticket
    await db.tickets.update_one(
        {"id": ticket_id},
        {"$set": {
            "department_id": department_id,
            "awaiting_department_choice": False,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Criar mensagem de confirmação
    message = {
        "id": str(uuid.uuid4()),
        "ticket_id": ticket_id,
        "from_type": "system",
        "kind": "text",
        "text": f"✅ Você selecionou: {department['name']}. Um atendente irá te responder em breve.",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "reseller_id": current_user.get("reseller_id")
    }
    
    await db.messages.insert_one(message)
    
    # Enviar via WebSocket (remover _id do MongoDB)
    message_to_send = {k: v for k, v in message.items() if k != '_id'}
    ticket = await db.tickets.find_one({"id": ticket_id})
    if ticket:
        await manager.send_to_user(ticket["client_id"], {
            "type": "new_message",
            "message": message_to_send
        })
    
    # TODO: Se departamento tem IA, acionar IA aqui
    
    return {"ok": True}


@api_router.get("/tickets/counts")
async def get_ticket_counts(request: Request, current_user: dict = Depends(get_current_user)):
    # Usar get_tenant_filter para garantir isolamento multi-tenant correto
    tenant_filter = get_tenant_filter(request, current_user)
    
    # EM_ESPERA inclui tanto 'EM_ESPERA' quanto 'open' (para compatibilidade WhatsApp)
    em_espera = await db.tickets.count_documents({
        **tenant_filter, 
        "status": {"$in": ["EM_ESPERA", "open"]}
    })
    atendendo = await db.tickets.count_documents({**tenant_filter, "status": "ATENDENDO"})
    finalizadas = await db.tickets.count_documents({**tenant_filter, "status": "FINALIZADAS"})
    return {
        "EM_ESPERA": em_espera,
        "ATENDENDO": atendendo,
        "FINALIZADAS": finalizadas
    }

@api_router.post("/tickets/{ticket_id}/mark-as-read")
async def mark_as_read(ticket_id: str, current_user: dict = Depends(get_current_user)):
    """Marcar todas as mensagens do ticket como lidas"""
    # Apenas agentes podem marcar como lido
    if current_user["user_type"] != "agent":
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    # Marcar todas as mensagens do cliente como lidas
    result = await db.messages.update_many(
        {
            "ticket_id": ticket_id,
            "sender_type": "client",
            "read": {"$ne": True}
        },
        {
            "$set": {"read": True}
        }
    )
    
    logger.info(f"✅ Marcadas {result.modified_count} mensagens como lidas no ticket {ticket_id[:8]}...")
    
    return {"ok": True, "marked_count": result.modified_count}

@api_router.get("/tickets/{ticket_id}")
async def get_ticket(ticket_id: str, current_user: dict = Depends(get_current_user)):
    ticket = await db.tickets.find_one({"id": ticket_id}, {"_id": 0})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket não encontrado")
    return ticket

@api_router.post("/tickets/{ticket_id}/status")
async def update_ticket_status(ticket_id: str, data: dict, current_user: dict = Depends(get_current_user)):
    if current_user["user_type"] != "agent":
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    status = data.get("status")
    if status not in ["EM_ESPERA", "ATENDENDO", "FINALIZADAS"]:
        raise HTTPException(status_code=400, detail="Status inválido")
    
    await db.tickets.update_one(
        {"id": ticket_id},
        {"$set": {"status": status, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    # Notify client
    ticket = await db.tickets.find_one({"id": ticket_id})
    if ticket:
        await manager.send_to_user(ticket["client_id"], {
            "type": "ticket_status",
            "ticket_id": ticket_id,
            "status": status
        })
    
    return {"ok": True}

@api_router.post("/tickets/{ticket_id}/toggle-ai")
async def toggle_ai_in_ticket(ticket_id: str, data: dict, current_user: dict = Depends(get_current_user)):
    """Ativa/desativa IA em uma conversa específica por 1 hora"""
    if current_user["user_type"] != "agent":
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    ticket = await db.tickets.find_one({"id": ticket_id})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket não encontrado")
    
    # Toggle: se está desativado, reativa. Se está ativo, desativa por 1h
    current_disabled_until = ticket.get("ai_disabled_until")
    
    if current_disabled_until:
        # Se já está desativado, verificar se expirou
        try:
            disabled_until = datetime.fromisoformat(current_disabled_until)
            if datetime.now(timezone.utc) < disabled_until:
                # Ainda desativado, então reativar
                await db.tickets.update_one(
                    {"id": ticket_id},
                    {"$unset": {"ai_disabled_until": ""}, "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}}
                )
                return {"message": "IA reativada", "ai_enabled": True}
        except:
            pass
    
    # Desativar por 1 hora
    disabled_until = datetime.now(timezone.utc) + timedelta(hours=1)
    await db.tickets.update_one(
        {"id": ticket_id},
        {"$set": {
            "ai_disabled_until": disabled_until.isoformat(),
            "ai_disabled_by": current_user["user_id"],
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {"message": "IA desativada por 1 hora", "ai_enabled": False, "disabled_until": disabled_until.isoformat()}

@api_router.put("/tickets/{ticket_id}/assign")
async def assign_ticket_to_agent(ticket_id: str, data: dict, current_user: dict = Depends(get_current_user)):
    """Atribui ticket a um atendente"""
    if current_user["user_type"] != "agent":
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    agent_id = data.get("agent_id", current_user["user_id"])  # Usa ID do usuário atual se não especificado
    
    ticket = await db.tickets.find_one({"id": ticket_id})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket não encontrado")
    
    await db.tickets.update_one(
        {"id": ticket_id},
        {"$set": {
            "assigned_agent_id": agent_id,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {"message": "Ticket atribuído", "assigned_agent_id": agent_id}

# Message routes
@api_router.get("/messages/{ticket_id}")
async def get_messages(ticket_id: str, limit: int = 50, offset: int = 0, current_user: dict = Depends(get_current_user)):
    messages = await db.messages.find(
        {"ticket_id": ticket_id},
        {"_id": 0}
    ).sort("created_at", -1).skip(offset).limit(limit).to_list(None)
    messages.reverse()
    return messages

@api_router.post("/messages")
async def send_message(data: MessageCreate, request: Request, current_user: dict = Depends(get_current_user)):
    # Log para debug
    logger.info(f"📥 POST /messages: from_type={data.from_type}, from_id='{data.from_id}', user_type={current_user.get('user_type')}, user_id={current_user.get('user_id')}")
    
    # Validate sender - APENAS para clientes (admin e atendentes podem enviar por qualquer ID)
    user_type = current_user.get("user_type", "")
    
    # ⚠️ VALIDAÇÃO CRÍTICA: from_id NÃO PODE ESTAR VAZIO
    if data.from_type == "client" and (not data.from_id or data.from_id.strip() == ""):
        logger.error(f"❌ Cliente tentando enviar mensagem sem from_id! user_id do token: {current_user.get('user_id')}")
        # Auto-corrigir usando user_id do token
        data.from_id = current_user.get("user_id")
        logger.info(f"✅ from_id auto-corrigido para: {data.from_id}")
    
    if user_type == "client":
        # Clientes só podem enviar como eles mesmos
        if str(data.from_id) != str(current_user["user_id"]):
            logger.error(f"Client authorization failed: from_id={data.from_id}, user_id={current_user['user_id']}")
            raise HTTPException(status_code=403, detail=f"Não autorizado - ID não corresponde")
    else:
        # Admin e atendentes podem enviar mensagens em nome de qualquer ticket
        logger.info(f"Message from {user_type}: {data.from_id} (logged as {current_user['user_id']})")
    
    # Pegar tenant do request ou do token
    tenant = get_request_tenant(request)
    reseller_id = tenant.reseller_id or current_user.get("reseller_id")
    
    # Get config for validation
    if reseller_id:
        config = await db.reseller_configs.find_one({"reseller_id": reseller_id}) or {}
    else:
        config = await db.config.find_one({"id": "config"}) or {}
    
    # Agent text validation - NEW ENHANCED VALIDATION
    if data.from_type == "agent" and data.kind == "text":
        # Nova validação com dados sensíveis
        error = await validate_sensitive_data(data.text, config)
        if error:
            raise HTTPException(status_code=400, detail=error)
    
    # Create or get ticket
    if data.from_type == "client":
        # Buscar ticket do cliente com filtro de tenant
        query = {"client_id": data.from_id}
        if reseller_id:
            query["reseller_id"] = reseller_id
        
        ticket = await db.tickets.find_one(query)
        if not ticket:
            ticket_id = str(uuid.uuid4())
            
            # **DETECTAR ORIGEM DO TICKET**
            # Padrão: wa_suporte (chat interno)
            ticket_origin = "wa_suporte"
            
            ticket = {
                "id": ticket_id,
                "client_id": data.from_id,
                "status": "open",  # ✅ Status 'open' para compatibilidade (frontend converte para EM_ESPERA)
                "department_id": None,
                "awaiting_department_choice": True,
                "department_choice_sent_at": None,
                "unread_count": 0,
                "reseller_id": reseller_id,
                "ticket_origin": ticket_origin,  # Salvar origem no ticket
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            await db.tickets.insert_one(ticket)
            
            # 🔍 BUSCA AUTOMÁTICA DE NOME DO CLIENTE (DESABILITADA TEMPORARIAMENTE - CAUSA TRAVAMENTO)
            # try:
            #     from client_name_service import auto_fetch_and_save_client_name
            #     
            #     # Verificar se cliente tem nome
            #     client_check = await db.users.find_one({"id": data.from_id})
            #     if not client_check:
            #         client_check = await db.clients.find_one({"id": data.from_id})
            #     
            #     if client_check:
            #         has_name = False
            #         phone = None
            #         collection = "users"
            #         
            #         # Verificar se tem nome e pegar telefone
            #         if "display_name" in client_check:  # users collection
            #             has_name = bool(client_check.get("display_name"))
            #             phone = client_check.get("whatsapp")
            #             collection = "users"
            #         elif "name" in client_check:  # clients collection
            #             has_name = bool(client_check.get("name"))
            #             phone = client_check.get("phone")
            #             collection = "clients"
            #         
            #         # Se não tem nome e tem telefone, buscar automaticamente
            #         if not has_name and phone:
            #             logger.info(f"📝 Cliente sem nome detectado, buscando no Office: {phone}")
            #             asyncio.create_task(
            #                 auto_fetch_and_save_client_name(db, data.from_id, phone, collection)
            #             )
            # except Exception as name_error:
            #     logger.error(f"❌ Erro ao buscar nome do cliente: {name_error}")
            
            # 🔍 BUSCA AUTOMÁTICA DE CREDENCIAIS (WA SUPORTE)
            if ticket_origin == "wa_suporte":
                # Pegar WhatsApp do cliente
                client = await db.clients.find_one({"id": data.from_id})
                if client and client.get("whatsapp"):
                    logger.info(f"🔍 Iniciando busca automática de credenciais para {client['whatsapp']}")
                    
                    # Chamar busca em background
                    import httpx
                    asyncio.create_task(
                        call_auto_search(ticket_id, client["whatsapp"], "wa_suporte_pwa")
                    )
            
            # Enviar mensagem de seleção de departamento (primeira vez)
            # Passa a origem para mostrar apenas departamentos correspondentes
            await send_department_selection(ticket_id, data.from_id, reseller_id, ticket_origin)
        else:
            ticket_id = ticket["id"]
            # Update ticket status to open when client sends and increment unread
            await db.tickets.update_one(
                {"id": ticket_id},
                {
                    "$set": {"status": "open", "updated_at": datetime.now(timezone.utc).isoformat()},  # Status 'open' para compatibilidade
                    "$inc": {"unread_count": 1}  # Incrementar contador de não lidas
                }
            )
            
            # 🔍 BUSCA AUTOMÁTICA DE CREDENCIAIS (WA SUPORTE) - Primeira mensagem do dia
            if ticket.get("ticket_origin") == "wa_suporte":
                client = await db.clients.find_one({"id": data.from_id})
                if client and client.get("whatsapp"):
                    # Verificar se já buscou hoje
                    last_search = ticket.get("credentials_last_search")
                    should_search = True
                    
                    if last_search:
                        try:
                            from datetime import date
                            last_date = datetime.fromisoformat(last_search).date()
                            today = datetime.now(timezone.utc).date()
                            should_search = today > last_date
                        except:
                            pass
                    
                    if should_search:
                        logger.info(f"🔍 Primeira mensagem do dia - Buscando credenciais para {client['whatsapp']}")
                        
                        asyncio.create_task(
                            call_auto_search(ticket_id, client["whatsapp"], "wa_suporte_pwa")
                        )
    else:
        ticket_id = data.ticket_id
        if not ticket_id:
            raise HTTPException(status_code=400, detail="ticket_id é obrigatório para mensagens de agente")
        # When agent sends, reset unread count
        if data.from_type == "agent":
            await db.tickets.update_one(
                {"id": ticket_id},
                {"$set": {"unread_count": 0}}
            )
    
    # 🔑 AUTO-RESPOSTA RÁPIDA - Busca no banco local (0.4ms!)
    if data.from_type == "client" and data.kind == "text":
        from auto_response_service import AutoResponseService
        
        auto_response = AutoResponseService(db)
        
        # Buscar cliente para pegar telefone
        client = await db.users.find_one({"id": data.from_id})
        if not client:
            client = await db.clients.find_one({"id": data.from_id})
        
        client_phone = None
        if client:
            client_phone = client.get("whatsapp") or client.get("phone")
        
        # Verificar se deve responder automaticamente
        auto_resp_data = await auto_response.should_auto_respond(data.text, client_phone)
        
        if auto_resp_data and auto_resp_data.get("auto_response"):
            logger.info(f"🤖 AUTO-RESPOSTA ativada! Tipo: {auto_resp_data['type']}")
            
            # Salvar mensagem do cliente
            client_msg_id = str(uuid.uuid4())
            client_message = {
                "id": client_msg_id,
                "ticket_id": ticket_id if 'ticket_id' in locals() else data.ticket_id,
                "from_type": "client",
                "from_id": data.from_id,
                "to_type": "agent",
                "to_id": None,
                "kind": "text",
                "text": data.text,
                "media_url": None,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db.messages.insert_one(client_message)
            
            # Enviar resposta automática como se fosse o sistema
            bot_msg_id = str(uuid.uuid4())
            bot_message = {
                "id": bot_msg_id,
                "ticket_id": ticket_id if 'ticket_id' in locals() else data.ticket_id,
                "from_type": "agent",
                "from_id": "auto-bot",
                "to_type": "client",
                "to_id": data.from_id,
                "kind": "text",
                "text": auto_resp_data["auto_response"],
                "media_url": None,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "is_auto_response": True
            }
            await db.messages.insert_one(bot_message)
            
            # Enviar via WebSocket
            await manager.send_message(bot_message, ticket_id if 'ticket_id' in locals() else data.ticket_id)
            
            logger.info(f"✅ Auto-resposta enviada com sucesso!")
            
            # Retornar para não processar mais
            return {
                "success": True,
                "message_id": bot_msg_id,
                "auto_response": True
            }
    
    # Wrap text at 20 chars for client
    text = data.text
    if data.from_type == "client" and data.kind == "text":
        text = re.sub(r'(.{20})', r'\1\n', text)
    
    # Detectar se atendente está enviando chave PIX
    message_kind = data.kind
    pix_key = None
    pinned_user = None
    pinned_pass = None
    
    if data.from_type == "agent" and data.kind == "text":
        # Buscar chave PIX configurada
        config_query = {"reseller_id": reseller_id} if reseller_id else {"id": "config"}
        config = await db.reseller_configs.find_one(config_query) or await db.config.find_one({"id": "config"}) or {}
        configured_pix = config.get("pix_key", "")
        
        # Se o texto contém a chave PIX configurada, transformar em mensagem PIX
        if configured_pix and configured_pix in text:
            message_kind = "pix"
            pix_key = configured_pix
            text = f"💰 Clique no botão abaixo para copiar a chave PIX"
        
        # Detectar se está enviando Usuário e Senha no formato flexível
        detected_user, detected_pass = extract_credentials_from_message(text)
        if detected_user and detected_pass:
            pinned_user = detected_user
            pinned_pass = detected_pass
            logger.info(f"✅ Credenciais detectadas automaticamente - User: {pinned_user}, Pass: {pinned_pass}")
            
            # Atualizar cliente com as credenciais
            if data.to_type == "client":
                await db.users.update_one(
                    {"id": data.to_id},
                    {
                        "$set": {
                            "pinned_user": pinned_user,
                            "pinned_pass": pinned_pass,
                            "updated_at": datetime.now(timezone.utc).isoformat()
                        }
                    }
                )
                logger.info(f"✅ Credenciais salvas no cliente {data.to_id}")
    
    # Create message
    message_id = str(uuid.uuid4())
    message = {
        "id": message_id,
        "ticket_id": ticket_id,
        "from_type": data.from_type,
        "from_id": data.from_id,
        "to_type": data.to_type,
        "to_id": data.to_id,
        "kind": message_kind,
        "text": text,
        "pix_key": pix_key,  # Adicionar chave PIX se for mensagem tipo pix
        "file_url": data.file_url or "",
        "reseller_id": reseller_id,
        "read": False if data.from_type == "client" else True,  # Mensagens do cliente começam como não lidas
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.messages.insert_one(message)
    
    # Criar cópia da mensagem SEM _id do MongoDB (ObjectId não é serializável)
    message_to_send = {k: v for k, v in message.items() if k != '_id'}
    
    # Check if system is in away mode and send auto-away message
    if data.from_type == "client" and data.kind == "text":
        # Buscar config do reseller ou config principal
        if reseller_id:
            config = await db.reseller_configs.find_one({"reseller_id": reseller_id})
        else:
            config = await db.config.find_one({"id": "config"})
        
        # ENVIAR MENSAGEM DE AUSÊNCIA SE ATIVADO
        if config and config.get("manual_away_mode"):
            away_message = config.get("away_message", "Estamos ausentes no momento. Por favor, aguarde que retornaremos em breve.")
            
            # Buscar agente do mesmo tenant para enviar mensagem
            agent_query = {}
            if reseller_id:
                agent_query["reseller_id"] = reseller_id
            agents = await db.agents.find(agent_query).to_list(1)
            if agents:
                agent = agents[0]
                away_reply_id = str(uuid.uuid4())
                away_reply = {
                    "id": away_reply_id,
                    "ticket_id": ticket_id,
                    "from_type": "agent",
                    "from_id": agent["id"],
                    "to_type": "client",
                    "to_id": data.from_id,
                    "kind": "text",
                    "text": f"⚠️ {away_message}",
                    "file_url": "",
                    "reseller_id": reseller_id,
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
                await db.messages.insert_one(away_reply)
                # Notify client of away message (remover _id do MongoDB)
                away_reply_to_send = {k: v for k, v in away_reply.items() if k != '_id'}
                await manager.send_to_user(data.from_id, {
                    "type": "message",
                    "message": away_reply_to_send
                })
        
        # Check auto-reply (exact match only)
        if config:
            auto_replies = config.get("auto_reply", [])
            text_lower = text.lower().strip()
            for rule in auto_replies:
                q = rule.get("q", "").lower().strip()
                # EXACT match only
                if q and text_lower == q:
                    # Buscar agente do mesmo tenant
                    agent_query = {}
                    if reseller_id:
                        agent_query["reseller_id"] = reseller_id
                    agents = await db.agents.find(agent_query).to_list(1)
                    if agents:
                        agent = agents[0]
                        reply_id = str(uuid.uuid4())
                        reply = {
                            "id": reply_id,
                            "ticket_id": ticket_id,
                            "from_type": "agent",
                            "from_id": agent["id"],
                            "to_type": "client",
                            "to_id": data.from_id,
                            "kind": "text",
                            "text": rule.get("a", ""),
                            "file_url": "",
                            "reseller_id": reseller_id,
                            "created_at": datetime.now(timezone.utc).isoformat()
                        }
                        await db.messages.insert_one(reply)
                        await db.tickets.update_one(
                            {"id": ticket_id},
                            {"$set": {"status": "ATENDENDO"}}
                        )
                        # Notify client of auto-reply (remover _id do MongoDB)
                        reply_to_send = {k: v for k, v in reply.items() if k != '_id'}
                        await manager.send_to_user(data.from_id, {
                            "type": "message",
                            "message": reply_to_send
                        })
                    break
    
    # Processar com IA se houver agente IA vinculado ao departamento
    ai_logger.info(f"🟡 Verificando se deve chamar IA: from_type={data.from_type}, kind={data.kind}")
    if data.from_type == "client" and data.kind == "text":
        ai_logger.info(f"🟡 Mensagem de cliente detectada! ticket_id={ticket_id}")
        # Buscar ticket atualizado
        ticket = await db.tickets.find_one({"id": ticket_id})
        ai_logger.info(f"🟡 Ticket encontrado: {ticket.get('id') if ticket else 'None'}, department_id={ticket.get('department_id') if ticket else 'None'}")
        if ticket and ticket.get("department_id"):
            ai_logger.info(f"🟡 Chamando process_message_with_ai para ticket {ticket['id']}")
            # Chamar IA de forma assíncrona (não bloqueia resposta)
            asyncio.create_task(process_message_with_ai(ticket, text, reseller_id))
        elif ticket and not ticket.get("department_id"):
            ai_logger.info(f"⚠️ Ticket {ticket['id']} existe mas NÃO TEM department_id definido. IA não será chamada.")
        elif not ticket:
            ai_logger.error(f"💥 Ticket {ticket_id} não encontrado no banco!")
    else:
        ai_logger.info(f"⚪ Mensagem não é de cliente ou não é texto: from_type={data.from_type}, kind={data.kind}")
    
    # Send via WebSocket to recipient
    print(f"💬 [POST /messages] Enviando mensagem:")
    print(f"   from_id: {data.from_id}, from_type: {data.from_type}")
    print(f"   to_id: {data.to_id}, to_type: {data.to_type}")
    print(f"   ticket_id: {ticket_id}")
    
    await manager.send_to_user(data.to_id, {
        "type": "message",
        "message": message_to_send
    })
    
    # Send to sender as well (for real-time update in their own chat)
    await manager.send_to_user(data.from_id, {
        "type": "message",
        "message": message_to_send
    })
    
    # If client sent, notify all agents
    if data.from_type == "client":
        await manager.broadcast_to_agents({
            "type": "message",
            "message": message_to_send
        })
    
    # If agent sent, make sure client receives it
    if data.from_type == "agent":
        await manager.send_to_user(data.to_id, {
            "type": "message",
            "message": message_to_send
        })
        
        # **ENVIAR PARA WHATSAPP SE O TICKET VEIO DO WHATSAPP**
        try:
            ticket_info = await db.tickets.find_one({"id": ticket_id})
            if ticket_info and ticket_info.get("whatsapp_instance"):
                # Ticket veio do WhatsApp, enviar resposta via WhatsApp
                whatsapp_instance = ticket_info.get("whatsapp_instance")
                client_phone = ticket_info.get("client_whatsapp") or ticket_info.get("client_phone")
                
                if whatsapp_instance and client_phone:
                    logger.info(f"📱 Enviando mensagem para WhatsApp: {whatsapp_instance} -> {client_phone}")
                    
                    # Importar serviço WhatsApp
                    from whatsapp_service import WhatsAppService
                    whatsapp_service = WhatsAppService(db)
                    
                    # Enviar mensagem
                    result = await whatsapp_service.send_message(
                        instance_name=whatsapp_instance,
                        to_number=client_phone,
                        message=text
                    )
                    
                    if result.get("success"):
                        logger.info(f"✅ Mensagem enviada via WhatsApp com sucesso!")
                    else:
                        logger.error(f"❌ Erro ao enviar via WhatsApp: {result.get('error')}")
        except Exception as whatsapp_error:
            logger.error(f"❌ Erro ao tentar enviar para WhatsApp: {whatsapp_error}")
        
        # ENVIAR PUSH NOTIFICATION PARA O CLIENTE
        try:
            # Buscar nome do agente
            agent_info = await db.users.find_one({"id": data.from_id})
            agent_name = agent_info.get("name", "Atendente") if agent_info else "Atendente"
            
            # Buscar client_id do ticket
            ticket_info = await db.tickets.find_one({"id": ticket_id})
            if ticket_info:
                client_id = ticket_info.get("client_id")
                
                # Buscar subscriptions ativas do cliente
                subscriptions = await db.push_subscriptions.find({
                    "client_id": client_id,
                    "is_active": True
                }).to_list(length=None)
                
                if subscriptions:
                    # Importar serviço de push
                    from push_notification_service import push_service
                    
                    # Preparar notificação
                    notification_payload = {
                        "title": f"💬 {agent_name}",
                        "body": text[:100] if text else "Enviou uma mensagem",
                        "icon": "/logo192.png",
                        "badge": "/badge72.png",
                        "url": "/",
                        "tag": "iaze-message",
                        "vibrate": [200, 100, 200],
                        "requireInteraction": False,
                        "timestamp": datetime.now(timezone.utc).timestamp() * 1000
                    }
                    
                    # Enviar para todas as subscriptions do cliente
                    for sub in subscriptions:
                        success = await push_service.send_notification(
                            subscription_info=sub["subscription_data"],
                            notification_data=notification_payload
                        )
                        
                        if success:
                            await db.push_subscriptions.update_one(
                                {"id": sub["id"]},
                                {"$set": {"last_used": datetime.now(timezone.utc).isoformat()}}
                            )
                        else:
                            # Desativar subscription que falhou
                            await db.push_subscriptions.update_one(
                                {"id": sub["id"]},
                                {"$set": {"is_active": False}}
                            )
                    
                    logger.info(f"📲 Push notification enviada para cliente {client_id}")
        except Exception as e:
            logger.error(f"❌ Erro ao enviar push notification: {e}")
    
    return {"ok": True, "message_id": message_id}

# Upload route - Com suporte a External Storage
@api_router.post("/upload")
async def upload_file(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    if not file:
        raise HTTPException(status_code=400, detail="Nenhum arquivo enviado")
    
    try:
        # Upload para servidor externo ou local (via external_storage)
        result = await external_storage.upload_file(file)
        
        if result.get('success'):
            # Determinar tipo de arquivo
            mime_type = file.content_type or mimetypes.guess_type(file.filename)[0] or "application/octet-stream"
            kind = "file"
            if mime_type.startswith("image/"):
                kind = "image"
            elif mime_type.startswith("video/"):
                kind = "video"
            elif mime_type.startswith("audio/"):
                kind = "audio"
            
            return {
                "ok": True,
                "url": result['url'],
                "filename": result['filename'],
                "size": result.get('size', 0),
                "kind": kind,
                "external": not result.get('local', False)
            }
        else:
            raise HTTPException(status_code=500, detail="Upload failed")
    
    except Exception as e:
        logger.error(f"❌ Erro crítico no upload: {e}")
        raise HTTPException(status_code=500, detail=f"Erro no upload: {str(e)}")

# Config routes (admin only)
@api_router.get("/config")
async def get_config(request: Request, current_user: dict = Depends(get_current_user)):
    tenant = get_request_tenant(request)
    reseller_id = tenant.reseller_id or current_user.get("reseller_id")
    
    # Se for reseller ou tenant específico, buscar config da revenda
    if reseller_id:
        config = await db.reseller_configs.find_one({"reseller_id": reseller_id}, {"_id": 0})
        if not config:
            config = {
                "id": f"config_{reseller_id}",
                "reseller_id": reseller_id,
                "quick_blocks": [],
                "auto_reply": [],
                "apps": [],
                "pix_key": "",
                "support_avatar": f"{os.environ.get('REACT_APP_BACKEND_URL', '')}/icon-512.png",
                "allowed_data": {"cpfs": [], "emails": [], "phones": [], "random_keys": []},
                "manual_away_mode": False,  # Admin pode ativar modo ausente manualmente
                "api_integration": {"api_url": "", "api_token": "", "api_enabled": False},
                "ai_agent": {
                    "name": "Assistente IA",
                    "personality": "",
                    "instructions": "",
                    "llm_provider": "openai",
                    "llm_model": "gpt-4",
                    "api_key": "",
                    "temperature": 0.7,
                    "max_tokens": 500,
                    "mode": "standby",
                    "active_hours": "24/7",
                    "enabled": False,
                    "can_access_credentials": True,
                    "knowledge_base": ""
                }
            }
            await db.reseller_configs.insert_one(config)
    else:
        # Config principal (admin master)
        config = await db.config.find_one({"id": "config"}, {"_id": 0})
        if not config:
            config = {
                "id": "config",
                "quick_blocks": [],
                "auto_reply": [],
                "apps": [],
                "pix_key": "",
                "support_avatar": f"{os.environ.get('REACT_APP_BACKEND_URL', '')}/icon-512.png",
                "allowed_data": {"cpfs": [], "emails": [], "phones": [], "random_keys": []},
                "api_integration": {"api_url": "", "api_token": "", "api_enabled": False},
                "ai_agent": {
                    "name": "Assistente IA",
                    "personality": "",
                    "instructions": "",
                    "llm_provider": "openai",
                    "llm_model": "gpt-4",
                    "api_key": "",
                    "temperature": 0.7,
                    "max_tokens": 500,
                    "mode": "standby",
                    "active_hours": "24/7",
                    "enabled": False,
                    "can_access_credentials": True,
                    "knowledge_base": ""
                }
            }
            await db.config.insert_one(config)
    
    # Garantir que todos os campos existam (para configs antigas)
    if "pix_key" not in config:
        config["pix_key"] = ""
    if "allowed_data" not in config:
        config["allowed_data"] = {"cpfs": [], "emails": [], "phones": [], "random_keys": []}
    if "api_integration" not in config:
        config["api_integration"] = {"api_url": "", "api_token": "", "api_enabled": False}
    if "ai_agent" not in config:
        config["ai_agent"] = {
            "name": "Assistente IA",
            "personality": "",
            "instructions": "",
            "llm_provider": "openai",
            "llm_model": "gpt-4",
            "temperature": 0.7,
            "max_tokens": 500,
            "mode": "standby",
            "active_hours": "24/7",
            "enabled": False,
            "can_access_credentials": True,
            "knowledge_base": ""
        }
    
    return config

@api_router.put("/config")
async def update_config(data: Dict[str, Any], request: Request, current_user: dict = Depends(get_current_user)):
    """Atualizar configuração - VERSÃO SIMPLIFICADA E ROBUSTA"""
    try:
        # SIMPLIFICADO - ignorar tenant por enquanto
        reseller_id = current_user.get("reseller_id") if current_user.get("user_type") == "reseller" else None
        
        # Admin ou Reseller podem atualizar config
        if current_user["user_type"] not in ["admin", "reseller"]:
            raise HTTPException(status_code=403, detail="Não autorizado")
        
        # Remover campos que não devem ser salvos
        config_data = {k: v for k, v in data.items() if k not in ['_id']}
        
        # FORÇAR id="config" se for admin
        if not reseller_id:
            config_data["id"] = "config"
        
        # Salvar no MongoDB
        if reseller_id:
            await db.reseller_configs.update_one(
                {"reseller_id": reseller_id},
                {"$set": config_data},
                upsert=True
            )
        else:
            # Config principal (admin master) - REPLACE completo
            await db.config.replace_one(
                {"id": "config"},
                config_data,
                upsert=True
            )
        
        return {"ok": True, "message": "Config salva", "saved_fields": list(config_data.keys())[:10]}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro: {str(e)}")

@api_router.post("/config/save")
async def save_config_new(data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    """NOVO ENDPOINT - Salvar configuração completa"""
    if current_user["user_type"] not in ["admin", "reseller"]:
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    reseller_id = current_user.get("reseller_id") if current_user.get("user_type") == "reseller" else None
    config_data = {k: v for k, v in data.items() if k not in ['_id']}
    
    if not reseller_id:
        config_data["id"] = "config"
        await db.config.replace_one({"id": "config"}, config_data, upsert=True)
    else:
        await db.reseller_configs.update_one({"reseller_id": reseller_id}, {"$set": config_data}, upsert=True)
    
    return {"ok": True, "saved": True, "fields": list(config_data.keys())[:15]}

@api_router.post("/config/support-avatar")
async def upload_support_avatar(file: UploadFile = File(...), request: Request = None, current_user: dict = Depends(get_current_user)):
    """Upload de logo/foto do suporte (Admin/Reseller)"""
    tenant = get_request_tenant(request)
    reseller_id = tenant.reseller_id or current_user.get("reseller_id")
    
    # Admin ou Reseller podem fazer upload
    if current_user["user_type"] not in ["admin", "reseller"]:
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    if not file:
        raise HTTPException(status_code=400, detail="Nenhum arquivo enviado")
    
    # Validar tipo de arquivo
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Apenas imagens são permitidas")
    
    # Generate unique filename
    ext = Path(file.filename).suffix or ".jpg"
    filename = f"support_avatar_{reseller_id or 'admin'}{ext}"
    filepath = UPLOADS_DIR / filename
    
    # Save file
    async with aiofiles.open(filepath, 'wb') as f:
        content = await file.read()
        await f.write(content)
    
    # Adicionar timestamp para forçar atualização do cache
    timestamp = int(datetime.now(timezone.utc).timestamp())
    url = f"{os.environ.get('REACT_APP_BACKEND_URL', '')}/api/uploads/{filename}?t={timestamp}"
    
    # Atualizar support_avatar na configuração
    if reseller_id:
        await db.reseller_configs.update_one(
            {"reseller_id": reseller_id},
            {"$set": {"support_avatar": url}},
            upsert=True
        )
    else:
        await db.configs.update_one(
            {"id": "config"},
            {"$set": {"support_avatar": url}},
            upsert=True
        )
    
    return {"ok": True, "avatar_url": url}



@api_router.post("/admin/replicate-config-to-resellers")
async def replicate_config_to_resellers(current_user: dict = Depends(get_current_user)):
    """
    Replica todas as configurações do admin principal para TODAS as revendas
    Apenas admin principal pode usar esta função
    """
    # Verificar se é admin principal
    if current_user["user_type"] != "admin":
        raise HTTPException(status_code=403, detail="Apenas o admin principal pode replicar configurações")
    
    try:
        print("🔄 [REPLICAÇÃO] Iniciando replicação de configurações...")
        
        # 1. Buscar configuração do admin principal
        admin_config = await db.config.find_one({"id": "config"}, {"_id": 0})
        if not admin_config:
            raise HTTPException(status_code=404, detail="Configuração do admin não encontrada")
        
        print(f"✅ [REPLICAÇÃO] Config admin principal encontrada")
        
        # 2. Buscar todas as revendas
        resellers = await db.resellers.find({}, {"_id": 0, "id": 1, "login": 1}).to_list(None)
        total_resellers = len(resellers)
        
        if total_resellers == 0:
            return {"ok": True, "message": "Nenhuma revenda encontrada", "count": 0}
        
        print(f"📋 [REPLICAÇÃO] Encontradas {total_resellers} revendas")
        
        # 3. Configurações a serem replicadas (EXCLUINDO dados manuais)
        config_to_replicate = {
            "support_avatar": admin_config.get("support_avatar"),
            "pix_key": admin_config.get("pix_key", ""),
            "allowed_data": admin_config.get("allowed_data", {"cpfs": [], "emails": [], "phones": [], "random_keys": []}),
            "api_integration": admin_config.get("api_integration", {"api_url": "", "api_token": "", "api_enabled": False}),
            "ai_agent": admin_config.get("ai_agent", {
                "name": "Assistente IA",
                "personality": "",
                "instructions": "",
                "llm_provider": "openai",
                "llm_model": "gpt-4",
                "api_key": "",
                "temperature": 0.7,
                "max_tokens": 500,
                "mode": "standby",
                "active_hours": "24/7",
                "enabled": False,
                "can_access_credentials": True,
                "knowledge_base": ""
            })
        }
        
        # 4. Buscar auto-respostas e tutoriais do admin
        admin_auto_responses = await db.messages.find(
            {"type": "auto_response", "reseller_id": None},
            {"_id": 0}
        ).to_list(None)
        
        admin_tutorials = await db.tutorials.find(
            {"reseller_id": None},
            {"_id": 0}
        ).to_list(None)
        
        admin_iptv_apps = await db.iptv_apps.find(
            {"reseller_id": None},
            {"_id": 0}
        ).to_list(None)
        
        print(f"📦 [REPLICAÇÃO] Auto-respostas: {len(admin_auto_responses)}, Tutoriais: {len(admin_tutorials)}, Apps IPTV: {len(admin_iptv_apps)}")
        
        # 5. Replicar para cada revenda
        replicated_count = 0
        
        for reseller in resellers:
            reseller_id = reseller["id"]
            reseller_login = reseller.get("login", "N/A")
            
            try:
                # 5.1 Atualizar configurações gerais da revenda
                await db.reseller_configs.update_one(
                    {"reseller_id": reseller_id},
                    {"$set": config_to_replicate},
                    upsert=True
                )
                
                # 5.2 Remover auto-respostas antigas da revenda
                await db.messages.delete_many({
                    "type": "auto_response",
                    "reseller_id": reseller_id
                })
                
                # 5.3 Inserir novas auto-respostas (clonar do admin)
                if admin_auto_responses:
                    for msg in admin_auto_responses:
                        new_msg = msg.copy()
                        new_msg["id"] = str(uuid.uuid4())
                        new_msg["reseller_id"] = reseller_id
                        await db.messages.insert_one(new_msg)
                
                # 5.4 Remover tutoriais antigos da revenda
                await db.tutorials.delete_many({"reseller_id": reseller_id})
                
                # 5.5 Inserir novos tutoriais (clonar do admin)
                if admin_tutorials:
                    for tutorial in admin_tutorials:
                        new_tutorial = tutorial.copy()
                        new_tutorial["id"] = str(uuid.uuid4())
                        new_tutorial["reseller_id"] = reseller_id
                        await db.tutorials.insert_one(new_tutorial)
                
                # 5.6 Remover apps IPTV antigos da revenda
                await db.iptv_apps.delete_many({"reseller_id": reseller_id})
                
                # 5.7 Inserir novos apps IPTV (clonar do admin)
                if admin_iptv_apps:
                    for app in admin_iptv_apps:
                        new_app = app.copy()
                        new_app["id"] = str(uuid.uuid4())
                        new_app["reseller_id"] = reseller_id
                        await db.iptv_apps.insert_one(new_app)
                
                replicated_count += 1
                print(f"✅ [REPLICAÇÃO] Configurações replicadas para revenda: {reseller_login} ({replicated_count}/{total_resellers})")
                
            except Exception as e:
                print(f"❌ [REPLICAÇÃO] Erro ao replicar para revenda {reseller_login}: {e}")
                continue
        
        print(f"🎉 [REPLICAÇÃO] Concluído! {replicated_count}/{total_resellers} revendas atualizadas")
        
        return {
            "ok": True,
            "message": f"Configurações replicadas com sucesso para {replicated_count} revendas",
            "total_resellers": total_resellers,
            "replicated_count": replicated_count
        }
        
    except Exception as e:
        print(f"❌ [REPLICAÇÃO] Erro crítico: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao replicar configurações: {str(e)}")




# ====== IPTV Apps Routes ======
@api_router.get("/iptv-apps")
async def get_iptv_apps(request: Request = None, current_user: dict = Depends(get_current_user)):
    """Retorna todos os apps IPTV cadastrados"""
    # ISOLAMENTO MULTI-TENANT: Usar função centralizada
    query = get_tenant_filter(request, current_user)
    
    apps = await db.iptv_apps.find(query, {"_id": 0}).to_list(None)
    return apps

@api_router.post("/iptv-apps")
async def create_iptv_app(data: dict, request: Request = None, current_user: dict = Depends(get_current_user)):
    """Cria um novo app IPTV"""
    if current_user["user_type"] not in ["admin", "reseller"]:
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    # ISOLAMENTO MULTI-TENANT: Determinar reseller_id baseado no contexto
    tenant = get_request_tenant(request)
    user_type = current_user.get("user_type")
    
    # Admin master: usa tenant do request (None se for master domain)
    if user_type == "admin" and tenant.is_master:
        reseller_id = tenant.reseller_id
    else:
        # Reseller: usa reseller_id do token
        reseller_id = current_user.get("reseller_id")
    
    app = {
        "id": str(uuid.uuid4()),
        "name": data["name"],
        "type": data["type"],
        "config_url": data["config_url"],
        "url_template": data["url_template"],
        "fields": data["fields"],
        "instructions": data.get("instructions", ""),
        "reseller_id": reseller_id,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.iptv_apps.insert_one(app)
    return {"ok": True, "app": {k: v for k, v in app.items() if k != '_id'}}

@api_router.put("/iptv-apps/{app_id}")
async def update_iptv_app(app_id: str, data: dict, request: Request = None, current_user: dict = Depends(get_current_user)):
    """Atualiza um app IPTV"""
    if current_user["user_type"] not in ["admin", "reseller"]:
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    # ISOLAMENTO MULTI-TENANT: Usar função centralizada
    tenant_filter = get_tenant_filter(request, current_user)
    
    query = {"id": app_id}
    query.update(tenant_filter)
    
    update_data = {}
    if "name" in data:
        update_data["name"] = data["name"]
    if "config_url" in data:
        update_data["config_url"] = data["config_url"]
    if "url_template" in data:
        update_data["url_template"] = data["url_template"]
    if "fields" in data:
        update_data["fields"] = data["fields"]
    if "instructions" in data:
        update_data["instructions"] = data["instructions"]
    
    result = await db.iptv_apps.update_one(query, {"$set": update_data})
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="App não encontrado")
    
    return {"ok": True}

@api_router.delete("/iptv-apps/{app_id}")
async def delete_iptv_app(app_id: str, request: Request = None, current_user: dict = Depends(get_current_user)):
    """Deleta um app IPTV"""
    if current_user["user_type"] not in ["admin", "reseller"]:
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    # ISOLAMENTO MULTI-TENANT: Usar função centralizada
    tenant_filter = get_tenant_filter(request, current_user)
    
    query = {"id": app_id}
    query.update(tenant_filter)
    
    result = await db.iptv_apps.delete_one(query)
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="App não encontrado")
    
    return {"ok": True}



@api_router.post("/iptv-apps/{app_id}/automate")
async def automate_iptv_config(app_id: str, data: dict, request: Request = None, current_user: dict = Depends(get_current_user)):
    """
    Automatiza a configuração do app IPTV usando sistema robusto com Playwright
    Sistema inteligente com retry, validação, screenshots e fallback para modo manual
    """
    from iptv_automation_service import automate_iptv_app
    
    tenant = get_request_tenant(request)
    reseller_id = tenant.reseller_id or current_user.get("reseller_id")
    
    # Buscar app
    query = {"id": app_id}
    if reseller_id:
        query["reseller_id"] = reseller_id
    
    app = await db.iptv_apps.find_one(query, {"_id": 0})
    if not app:
        raise HTTPException(status_code=404, detail="App não encontrado")
    
    form_data = data.get("form_data", {})
    
    print(f"🤖 [AUTOMAÇÃO ROBUSTA] Iniciando para {app['name']}...")
    print(f"   📋 Form data recebido: {form_data}")
    
    # Executar automação com o novo serviço robusto
    result = await automate_iptv_app(app, form_data)
    
    # Retornar resultado em formato compatível
    if result['success']:
        print(f"   ✅ Automação concluída com sucesso!")
        return {
            "ok": True,
            "success": True,
            "message": result['message'],
            "final_url": result['final_url'],
            "logs": result['logs'],
            "screenshots": result['screenshots'],
            "automation_score": result['automation_score']
        }
    else:
        print(f"   ⚠️ Automação falhou - fallback para modo manual")
        return {
            "ok": False,
            "success": False,
            "error": result.get('error', 'Erro desconhecido'),
            "message": result['message'],
            "logs": result['logs'],
            "screenshots": result['screenshots'],
            "automation_score": result['automation_score']
        }



# Notice routes
@api_router.get("/notices")
async def get_notices(request: Request, current_user: dict = Depends(get_current_user)):
    """
    Obter avisos com isolamento por DOMÍNIO E recipient_type:
    - Admin em domínio master (suporte.help): vê avisos globais + avisos do admin
    - Admin/Agent/Client em domínio de revenda (dominio.revenda): vê avisos dessa revenda + globais
    - Reseller logado: vê avisos da revenda dele (do token) + globais
    - Filtra por recipient_type: ALL, TEAM (agentes), CLIENTS (clientes)
    """
    from tenant_helpers import get_request_tenant
    
    # Determinar tenant pelo DOMÍNIO acessado
    tenant = get_request_tenant(request)
    
    user_type = current_user.get("user_type")
    reseller_id = current_user.get("reseller_id")
    
    # Get notices from last 60 days
    cutoff = datetime.now(timezone.utc) - timedelta(days=60)
    
    query = {"created_at": {"$gte": cutoff.isoformat()}}
    
    # FILTRO POR RECIPIENT_TYPE
    # Admin e Agent veem: ALL e TEAM
    # Client veem: ALL e CLIENTS
    if user_type in ["admin", "agent"]:
        query["recipient_type"] = {"$in": ["all", "team"]}
    elif user_type == "client":
        query["recipient_type"] = {"$in": ["all", "clients"]}
    else:
        # Fallback: apenas ALL
        query["recipient_type"] = "all"
    
    # ISOLAMENTO POR DOMÍNIO:
    # Se está em domínio master (tenant.is_master = True)
    if tenant.is_master:
        # Admin master: vê avisos globais + avisos do admin
        if user_type == "admin":
            query["$or"] = [
                {"target_audience": "all"},
                {"reseller_id": None, "target_audience": "own"}
            ]
        else:
            # Outros usuários no master: apenas avisos globais
            query["target_audience"] = "all"
    
    # Se está em domínio de revenda (tenant.reseller_id existe)
    elif tenant.reseller_id:
        # Qualquer usuário acessando pelo domínio da revenda vê:
        # 1. Avisos globais (target_audience='all')
        # 2. Avisos próprios da revenda do domínio (reseller_id=tenant.reseller_id)
        # 3. Avisos direcionados à revenda (target_reseller_ids contém tenant.reseller_id)
        query["$or"] = [
            {"target_audience": "all"},
            {"reseller_id": tenant.reseller_id, "target_audience": "own"},
            {"target_audience": "specific", "target_reseller_ids": tenant.reseller_id}
        ]
    
    # Se não identificou domínio mas usuário é reseller (fallback pelo token)
    elif user_type == "reseller" and reseller_id:
        query["$or"] = [
            {"target_audience": "all"},
            {"reseller_id": reseller_id, "target_audience": "own"},
            {"target_audience": "specific", "target_reseller_ids": reseller_id}
        ]
    
    # Fallback: apenas avisos globais
    else:
        query["target_audience"] = "all"
    
    notices = await db.notices.find(query, {"_id": 0}).sort("created_at", -1).to_list(None)
    return notices

@api_router.post("/notices")
async def create_notice(data: NoticeCreate, request: Request, current_user: dict = Depends(get_current_user)):
    """Criar aviso - VERSÃO SIMPLIFICADA"""
    try:
        if current_user["user_type"] not in ["admin", "reseller", "agent"]:
            raise HTTPException(status_code=403, detail="Não autorizado")
        
        # Simplificado: usar reseller_id do usuário
        user_type = current_user.get("user_type")
        reseller_id = current_user.get("reseller_id")
        notice_reseller_id = None if user_type == "admin" else reseller_id
        
        # Recipient type
        recipient_type = data.recipient_type.value if hasattr(data.recipient_type, 'value') else str(data.recipient_type)
        
        # Criar aviso
        notice_id = str(uuid.uuid4())
        notice = {
            "id": notice_id,
            "title": data.title,
            "message": data.message,
            "recipient_type": recipient_type,
            "reseller_id": notice_reseller_id,
            "media_url": data.media_url if hasattr(data, 'media_url') else None,
            "media_type": data.media_type if hasattr(data, 'media_type') else 'none',
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.notices.insert_one(notice)
        logger.info(f"✅ Aviso criado: {notice_id} (tipo: {notice['media_type']})")
        
        return {"ok": True, "notice_id": notice_id, "id": notice_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro em create_notice: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao criar aviso: {str(e)}")

@api_router.put("/notices/{notice_id}")
async def update_notice(notice_id: str, data: NoticeCreate, request: Request, current_user: dict = Depends(get_current_user)):
    """
    Atualizar um aviso existente - com isolamento por domínio
    """
    from tenant_helpers import get_request_tenant
    
    if current_user["user_type"] not in ["admin", "reseller"]:
        raise HTTPException(status_code=403, detail="Apenas admin ou revendedores podem editar avisos")
    
    # Determinar tenant pelo DOMÍNIO acessado
    tenant = get_request_tenant(request)
    
    user_type = current_user.get("user_type")
    reseller_id = current_user.get("reseller_id")
    
    # Buscar aviso existente
    notice = await db.notices.find_one({"id": notice_id})
    if not notice:
        raise HTTPException(status_code=404, detail="Aviso não encontrado")
    
    # Verificar permissão baseado no domínio (mesma lógica do delete)
    # Admin no domínio MASTER
    if user_type == "admin" and tenant.is_master:
        # Admin master pode editar avisos globais ou avisos do admin (reseller_id=None)
        if notice.get("reseller_id") is not None:
            raise HTTPException(status_code=403, detail="Você não tem permissão para editar este aviso")
    
    # Admin acessando pelo domínio de uma revenda
    elif user_type == "admin" and tenant.reseller_id:
        # Só pode editar avisos dessa revenda
        if notice.get("reseller_id") != tenant.reseller_id:
            raise HTTPException(status_code=403, detail="Você não tem permissão para editar este aviso")
    
    # Reseller
    else:
        # Só pode editar seus próprios avisos
        if notice.get("reseller_id") != reseller_id:
            raise HTTPException(status_code=403, detail="Você não tem permissão para editar este aviso")
    
    # Atualizar campos
    recipient_type = data.recipient_type.value if hasattr(data.recipient_type, 'value') else str(data.recipient_type)
    
    update_data = {
        "title": data.title,
        "message": data.message,
        "recipient_type": recipient_type,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Atualizar aviso no banco
    await db.notices.update_one({"id": notice_id}, {"$set": update_data})
    
    return {"ok": True, "notice_id": notice_id, "message": "Aviso atualizado com sucesso"}

@api_router.delete("/notices/{notice_id}")
async def delete_notice(notice_id: str, request: Request, current_user: dict = Depends(get_current_user)):
    """Deletar um aviso - com isolamento por domínio"""
    from tenant_helpers import get_request_tenant
    
    if current_user["user_type"] not in ["admin", "reseller"]:
        raise HTTPException(status_code=403, detail="Apenas admin ou revendedores podem deletar avisos")
    
    # Determinar tenant pelo DOMÍNIO acessado
    tenant = get_request_tenant(request)
    
    user_type = current_user.get("user_type")
    reseller_id = current_user.get("reseller_id")
    
    # Buscar aviso
    notice = await db.notices.find_one({"id": notice_id})
    if not notice:
        raise HTTPException(status_code=404, detail="Aviso não encontrado")
    
    # Verificar permissão baseado no domínio
    # Admin no domínio MASTER
    if user_type == "admin" and tenant.is_master:
        # Admin master pode deletar avisos globais ou avisos do admin (reseller_id=None)
        if notice.get("reseller_id") is not None:
            raise HTTPException(status_code=403, detail="Você não tem permissão para deletar este aviso")
    
    # Admin acessando pelo domínio de uma revenda
    elif user_type == "admin" and tenant.reseller_id:
        # Só pode deletar avisos dessa revenda
        if notice.get("reseller_id") != tenant.reseller_id:
            raise HTTPException(status_code=403, detail="Você não tem permissão para deletar este aviso")
    
    # Reseller
    else:
        # Só pode deletar seus próprios avisos
        if notice.get("reseller_id") != reseller_id:
            raise HTTPException(status_code=403, detail="Você não tem permissão para deletar este aviso")
    
    # Deletar aviso
    await db.notices.delete_one({"id": notice_id})
    return {"ok": True, "message": "Aviso deletado com sucesso"}

# Pin credentials (agent only)
@api_router.get("/users/{user_id}/credentials")
async def get_user_credentials(user_id: str, current_user: dict = Depends(get_current_user)):
    """Buscar credenciais fixadas de um cliente específico (apenas para agentes)"""
    if current_user["user_type"] != "agent":
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    return {
        "pinned_user": user.get("pinned_user", ""),
        "pinned_pass": user.get("pinned_pass", "")
    }

@api_router.put("/users/{user_id}/pin-credentials")
async def set_pin_credentials(user_id: str, data: dict, current_user: dict = Depends(get_current_user)):
    if current_user["user_type"] != "agent":
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    await db.users.update_one(
        {"id": user_id},
        {"$set": {
            "pinned_user": data.get("pinned_user", ""),
            "pinned_pass": data.get("pinned_pass", "")
        }}
    )
    
    # Notify client
    await manager.send_to_user(user_id, {
        "type": "credentials_updated",
        "pinned_user": data.get("pinned_user", ""),
        "pinned_pass": data.get("pinned_pass", "")
    })
    
    return {"ok": True}

# Reset PIN (agent only)
@api_router.post("/users/reset-pin")
async def reset_pin(data: dict, current_user: dict = Depends(get_current_user)):
    if current_user["user_type"] != "agent":
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    whatsapp = data.get("whatsapp", "")
    user = await db.users.find_one({"whatsapp": whatsapp})
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    await db.users.update_one({"id": user["id"]}, {"$set": {"pin_hash": ""}})
    return {"ok": True}

# WebSocket endpoint
@api_router.websocket("/ws/{user_id}/{session_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str, session_id: str):
    await manager.connect(websocket, user_id, session_id)
    try:
        while True:
            # Receber mensagem (pode ser ping do keepalive ou outra mensagem)
            data = await websocket.receive_text()
            
            # ⚡ KEEPALIVE: Responder a pings do cliente
            try:
                message = json.loads(data)
                if message.get('type') == 'ping':
                    await websocket.send_text(json.dumps({'type': 'pong'}))
                    print(f"🏓 Pong enviado para user_id: {user_id}")
            except json.JSONDecodeError:
                pass  # Ignorar mensagens que não são JSON
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
    except Exception as e:
        print(f"❌ WebSocket error for user {user_id}: {e}")
        manager.disconnect(websocket, user_id)

# Auto-Responder endpoints (legado - mantido para compatibilidade)
@api_router.get("/config/auto-responses")
async def get_auto_responses(current_user: dict = Depends(get_current_user)):
    config = await db.config.find_one({"id": "auto_responses"}) or {}
    return config.get("responses", [])

@api_router.post("/config/auto-responses")
async def save_auto_responses(data: dict, current_user: dict = Depends(get_current_user)):
    if current_user["user_type"] != "admin":
        raise HTTPException(status_code=403, detail="Apenas admin")
    
    await db.config.update_one(
        {"id": "auto_responses"},
        {"$set": {"responses": data.get("responses", [])}},
        upsert=True
    )
    return {"ok": True}

# ====== NOVO: Auto-Responder Avançado (Multi-mídia + Delays) ======
@api_router.get("/config/auto-responder-sequences")
async def get_auto_responder_sequences(request: Request, current_user: dict = Depends(get_current_user)):
    """Retorna todas as sequências de auto-responder"""
    # ISOLAMENTO MULTI-TENANT: Usar função centralizada
    query = get_tenant_filter(request, current_user)
    
    sequences = await db.auto_responder_sequences.find(
        query,
        {"_id": 0}  # Exclude MongoDB ObjectId
    ).to_list(length=None)
    
    return sequences

@api_router.post("/config/auto-responder-sequences")
async def save_auto_responder_sequences(data: dict, request: Request, current_user: dict = Depends(get_current_user)):
    """Salva/atualiza uma sequência de auto-responder"""
    if current_user["user_type"] not in ["admin", "reseller"]:
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    # ISOLAMENTO MULTI-TENANT: Determinar reseller_id baseado no contexto
    tenant = get_request_tenant(request)
    user_type = current_user.get("user_type")
    
    # Admin master: usa tenant do request (None se for master domain)
    if user_type == "admin" and tenant.is_master:
        reseller_id = tenant.reseller_id
    else:
        # Reseller: usa reseller_id do token
        reseller_id = current_user.get("reseller_id")
    
    sequences = data.get("sequences", [])
    
    # Remove todas as sequências existentes desta revenda
    delete_query = {"reseller_id": reseller_id} if reseller_id else {}
    await db.auto_responder_sequences.delete_many(delete_query)
    
    # Insere novas sequências
    if sequences:
        for seq in sequences:
            seq["reseller_id"] = reseller_id
        await db.auto_responder_sequences.insert_many(sequences)
    
    return {"ok": True, "count": len(sequences)}

@api_router.put("/config/auto-responder-sequences/{sequence_id}")
async def update_auto_responder_sequence(sequence_id: str, data: dict, request: Request, current_user: dict = Depends(get_current_user)):
    """Atualiza uma sequência específica"""
    if current_user["user_type"] not in ["admin", "reseller"]:
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    # ISOLAMENTO MULTI-TENANT: Usar função centralizada
    tenant_filter = get_tenant_filter(request, current_user)
    
    query = {"id": sequence_id}
    query.update(tenant_filter)
    
    # Preparar dados de atualização
    update_data = {}
    if "name" in data:
        update_data["name"] = data["name"]
    if "trigger_keyword" in data:
        update_data["trigger_keyword"] = data["trigger_keyword"]
    if "responses" in data:
        update_data["responses"] = data["responses"]
    if "is_active" in data:
        update_data["is_active"] = data["is_active"]
    
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    result = await db.auto_responder_sequences.update_one(query, {"$set": update_data})
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Sequência não encontrada")
    
    return {"ok": True, "updated": result.modified_count > 0}

@api_router.delete("/config/auto-responder-sequences/{sequence_id}")
async def delete_auto_responder_sequence(sequence_id: str, request: Request, current_user: dict = Depends(get_current_user)):
    """Deleta uma sequência específica"""
    if current_user["user_type"] not in ["admin", "reseller"]:
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    # ISOLAMENTO MULTI-TENANT: Usar função centralizada
    tenant_filter = get_tenant_filter(request, current_user)
    
    query = {"id": sequence_id}
    query.update(tenant_filter)
    
    result = await db.auto_responder_sequences.delete_one(query)
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Sequência não encontrada")
    
    return {"ok": True}

# ====== NOVO: Tutorials Avançado (Multi-mídia + Delays) ======
@api_router.get("/config/tutorials-advanced")
async def get_tutorials_advanced(request: Request, current_user: dict = Depends(get_current_user)):
    """Retorna todos os tutoriais avançados"""
    # ISOLAMENTO MULTI-TENANT: Usar função centralizada
    query = get_tenant_filter(request, current_user)
    
    tutorials = await db.tutorials_advanced.find(
        query,
        {"_id": 0}  # Exclude MongoDB ObjectId
    ).to_list(length=None)
    
    return tutorials

@api_router.post("/config/tutorials-advanced")
async def save_tutorials_advanced(data: dict, request: Request, current_user: dict = Depends(get_current_user)):
    """Salva/atualiza tutoriais avançados"""
    if current_user["user_type"] not in ["admin", "reseller"]:
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    # ISOLAMENTO MULTI-TENANT: Determinar reseller_id baseado no contexto
    tenant = get_request_tenant(request)
    user_type = current_user.get("user_type")
    
    # Admin master: usa tenant do request (None se for master domain)
    if user_type == "admin" and tenant.is_master:
        reseller_id = tenant.reseller_id
    else:
        # Reseller: usa reseller_id do token
        reseller_id = current_user.get("reseller_id")
    
    tutorials = data.get("tutorials", [])
    
    # Remove todos os tutoriais existentes desta revenda
    delete_query = {"reseller_id": reseller_id} if reseller_id else {}
    await db.tutorials_advanced.delete_many(delete_query)
    
    # Insere novos tutoriais
    if tutorials:
        for tutorial in tutorials:
            tutorial["reseller_id"] = reseller_id
        await db.tutorials_advanced.insert_many(tutorials)
    
    return {"ok": True, "count": len(tutorials)}

@api_router.delete("/config/tutorials-advanced/{tutorial_id}")
async def delete_tutorial_advanced(tutorial_id: str, request: Request, current_user: dict = Depends(get_current_user)):
    """Deleta um tutorial específico"""
    if current_user["user_type"] not in ["admin", "reseller"]:
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    # ISOLAMENTO MULTI-TENANT: Usar função centralizada
    tenant_filter = get_tenant_filter(request, current_user)
    
    query = {"id": tutorial_id}
    query.update(tenant_filter)
    
    result = await db.tutorials_advanced.delete_one(query)
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Tutorial não encontrado")
    
    return {"ok": True}

# ====== NOVO: Gestão de Domínios para Revendas ======
@api_router.get("/reseller/me")
async def get_reseller_me(current_user: dict = Depends(get_current_user)):
    """Retorna informações da revenda logada"""
    reseller_id = current_user.get("reseller_id")
    
    if not reseller_id or current_user.get("user_type") != "reseller":
        raise HTTPException(status_code=400, detail="Apenas revendedores podem acessar")
    
    # Buscar informações da revenda
    reseller = await db.resellers.find_one({"id": reseller_id})
    if not reseller:
        raise HTTPException(status_code=404, detail="Revenda não encontrada")
    
    return {
        "id": reseller.get("id"),
        "name": reseller.get("name"),
        "email": reseller.get("email"),
        "first_login": reseller.get("first_login", False),
        "custom_domain": reseller.get("custom_domain", ""),
        "test_domain": reseller.get("test_domain", ""),
        "is_active": reseller.get("is_active", True)
    }

@api_router.post("/resellers/change-password")
async def change_reseller_password(data: dict, current_user: dict = Depends(get_current_user)):
    """Altera a senha da revenda e marca first_login como False"""
    reseller_id = current_user.get("reseller_id")
    
    if not reseller_id or current_user.get("user_type") != "reseller":
        raise HTTPException(status_code=400, detail="Apenas revendedores podem acessar")
    
    new_password = data.get("new_password", "").strip()
    
    if not new_password or len(new_password) < 6:
        raise HTTPException(status_code=400, detail="Senha deve ter no mínimo 6 caracteres")
    
    # Hash da nova senha
    pass_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
    
    # Atualizar senha e marcar first_login como False
    result = await db.resellers.update_one(
        {"id": reseller_id},
        {"$set": {
            "pass_hash": pass_hash,
            "first_login": False,
            "password_changed_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Revenda não encontrada")
    
    logger.info(f"✅ Senha alterada para revenda {reseller_id} (primeiro login concluído)")
    
    return {"ok": True, "message": "Senha alterada com sucesso!"}

@api_router.post("/admin/change-password")
async def change_admin_password(data: dict, current_user: dict = Depends(get_current_user)):
    """Altera a senha do admin"""
    if current_user.get("user_type") != "admin":
        raise HTTPException(status_code=403, detail="Apenas administradores podem acessar")
    
    current_password = data.get("current_password", "").strip()
    new_password = data.get("new_password", "").strip()
    
    if not current_password or not new_password:
        raise HTTPException(status_code=400, detail="Senha atual e nova senha são obrigatórias")
    
    if len(new_password) < 6:
        raise HTTPException(status_code=400, detail="Nova senha deve ter no mínimo 6 caracteres")
    
    # Buscar admin
    admin = await db.users.find_one({"id": current_user["user_id"], "user_type": "admin"})
    if not admin:
        raise HTTPException(status_code=404, detail="Admin não encontrado")
    
    # Verificar senha atual
    if not bcrypt.checkpw(current_password.encode(), admin["password"].encode()):
        raise HTTPException(status_code=401, detail="Senha atual incorreta")
    
    # Hash da nova senha
    new_pass_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
    
    # Atualizar senha
    result = await db.users.update_one(
        {"id": current_user["user_id"], "user_type": "admin"},
        {"$set": {
            "password": new_pass_hash,
            "password_changed_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=500, detail="Erro ao atualizar senha")
    
    logger.info(f"✅ Senha alterada para admin {current_user['user_id']}")
    
    return {"ok": True, "message": "Senha alterada com sucesso!"}

@api_router.get("/reseller/domain-info")
async def get_reseller_domain_info(request: Request, current_user: dict = Depends(get_current_user)):
    """Retorna informações de domínio da revenda"""
    # Use reseller_id from token instead of tenant middleware
    reseller_id = current_user.get("reseller_id")
    
    if not reseller_id or current_user.get("user_type") != "reseller":
        raise HTTPException(status_code=400, detail="Apenas revendedores podem acessar")
    
    # Buscar informações da revenda
    reseller = await db.resellers.find_one({"id": reseller_id})
    if not reseller:
        raise HTTPException(status_code=404, detail="Revenda não encontrada")
    
    # IP do servidor (pegar do ambiente ou hostname)
    server_ip = os.environ.get('SERVER_IP', socket.gethostbyname(socket.gethostname()))
    
    # Domínio de teste
    test_domain = reseller.get('test_domain', f"reseller-{reseller_id[:8]}.preview.emergentagent.com")
    test_domain_active = reseller.get('test_domain_active', True)
    
    return {
        "test_domain": test_domain,
        "test_domain_active": test_domain_active,
        "custom_domain": reseller.get('custom_domain', ''),
        "custom_domain_verified": reseller.get('custom_domain_verified', False),
        "server_ip": server_ip,
        "ssl_enabled": True
    }

@api_router.post("/reseller/update-domain")
async def update_reseller_domain(data: dict, request: Request, current_user: dict = Depends(get_current_user)):
    """Atualiza o domínio personalizado da revenda"""
    # Use reseller_id from token instead of tenant middleware
    reseller_id = current_user.get("reseller_id")
    
    if not reseller_id or current_user.get("user_type") != "reseller":
        raise HTTPException(status_code=400, detail="Apenas revendedores podem atualizar")
    
    custom_domain = data.get('custom_domain', '').strip().lower()
    
    if not custom_domain:
        raise HTTPException(status_code=400, detail="Domínio inválido")
    
    # Atualizar revenda e DESATIVAR domínio de teste
    await db.resellers.update_one(
        {"id": reseller_id},
        {"$set": {
            "custom_domain": custom_domain,
            "custom_domain_verified": False,  # Precisa verificar DNS
            "test_domain_active": False,  # Desativa domínio de teste
            "custom_domain_updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    logger.info(f"✅ Domínio oficial ativado para revenda {reseller_id}: {custom_domain} (domínio de teste desativado)")
    
    return {"ok": True, "message": "Domínio oficial ativado! Domínio de teste desativado. Configure o DNS."}

@api_router.get("/reseller/verify-domain")
async def verify_reseller_domain(request: Request, current_user: dict = Depends(get_current_user)):
    """Verifica se o DNS do domínio personalizado está configurado corretamente"""
    # Use reseller_id from token instead of tenant middleware
    reseller_id = current_user.get("reseller_id")
    
    if not reseller_id or current_user.get("user_type") != "reseller":
        raise HTTPException(status_code=400, detail="Apenas revendedores podem verificar")
    
    reseller = await db.resellers.find_one({"id": reseller_id})
    if not reseller or not reseller.get('custom_domain'):
        raise HTTPException(status_code=400, detail="Nenhum domínio personalizado configurado")
    
    custom_domain = reseller['custom_domain']
    
    # Aqui você implementaria a verificação DNS real
    # Por ora, vamos simular
    try:
        import socket
        # Tentar resolver o domínio
        ip = socket.gethostbyname(custom_domain)
        server_ip = os.environ.get('SERVER_IP', '198.51.100.1')
        
        if ip == server_ip:
            # DNS configurado corretamente
            await db.resellers.update_one(
                {"id": reseller_id},
                {"$set": {
                    "custom_domain_verified": True,
                    "custom_domain_verified_at": datetime.now(timezone.utc).isoformat()
                }}
            )
            return {"verified": True, "message": "Domínio verificado com sucesso!"}
        else:
            return {"verified": False, "message": f"DNS aponta para {ip}, esperado {server_ip}"}
    
    except socket.gaierror:
        return {"verified": False, "message": "Domínio não encontrado. Aguarde propagação DNS."}
    except Exception as e:
        return {"verified": False, "message": f"Erro ao verificar: {str(e)}"}

# Tutoriais endpoints (legado - mantido para compatibilidade)
@api_router.get("/config/tutorials")
async def get_tutorials(current_user: dict = Depends(get_current_user)):
    config = await db.config.find_one({"id": "tutorials"}) or {}
    return config.get("tutorials", [])

@api_router.post("/config/tutorials")
async def save_tutorials(data: dict, current_user: dict = Depends(get_current_user)):
    if current_user["user_type"] != "admin":
        raise HTTPException(status_code=403, detail="Apenas admin")
    
    await db.config.update_one(
        {"id": "tutorials"},
        {"$set": {"tutorials": data.get("tutorials", [])}},
        upsert=True
    )
    return {"ok": True}

# Domain Configuration
@api_router.get("/admin/domain-config")
async def get_domain_config(current_user: dict = Depends(get_current_user)):
    """Obter configuração de domínio"""
    if current_user["user_type"] != "admin":
        raise HTTPException(status_code=403, detail="Apenas admin")
    
    config = await db.config.find_one({"id": "domain_config"}, {"_id": 0})
    
    if not config:
        # Retornar config padrão
        return {
            "config": {
                "mainDomain": "",
                "resellerPath": "/login",
                "agentPath": "/atendente/login",
                "clientPath": "/"
            }
        }
    
    return {"config": config.get("config", {})}

@api_router.post("/admin/domain-config")
async def save_domain_config(data: dict, current_user: dict = Depends(get_current_user)):
    """Salvar configuração de domínio"""
    if current_user["user_type"] != "admin":
        raise HTTPException(status_code=403, detail="Apenas admin")
    
    await db.config.update_one(
        {"id": "domain_config"},
        {"$set": {"config": data}},
        upsert=True
    )
    
    return {"ok": True, "message": "Configuração salva com sucesso"}

# Admin Subscription Management
@api_router.post("/admin/subscriptions/manual-renew")
async def manual_renew_subscription(data: dict, current_user: dict = Depends(get_current_user)):
    """Renovação manual de assinatura pelo admin"""
    if current_user["user_type"] != "admin":
        raise HTTPException(status_code=403, detail="Apenas admin pode renovar manualmente")
    
    reseller_id = data.get("reseller_id")
    plan_type = data.get("plan_type")
    months = data.get("months", 1)
    
    if not reseller_id or not plan_type:
        raise HTTPException(status_code=400, detail="reseller_id e plan_type são obrigatórios")
    
    from subscription_service import SubscriptionService
    subscription_service = SubscriptionService(db)
    
    try:
        subscription = await subscription_service.manual_renew_subscription(reseller_id, plan_type, months)
        return {"ok": True, "subscription": subscription}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@api_router.put("/admin/subscriptions/{reseller_id}/end-date")
async def update_subscription_end_date(reseller_id: str, data: dict, current_user: dict = Depends(get_current_user)):
    """Atualizar data de vencimento da assinatura"""
    if current_user["user_type"] != "admin":
        raise HTTPException(status_code=403, detail="Apenas admin pode editar datas")
    
    new_end_date = data.get("end_date")
    
    if not new_end_date:
        raise HTTPException(status_code=400, detail="end_date é obrigatório")
    
    from subscription_service import SubscriptionService
    subscription_service = SubscriptionService(db)
    
    try:
        subscription = await subscription_service.update_subscription_end_date(reseller_id, new_end_date)
        return {"ok": True, "subscription": subscription}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@api_router.get("/admin/subscriptions")
async def list_all_subscriptions(current_user: dict = Depends(get_current_user)):
    """Listar todas as assinaturas (admin)"""
    if current_user["user_type"] != "admin":
        raise HTTPException(status_code=403, detail="Apenas admin")
    
    from subscription_service import SubscriptionService
    subscription_service = SubscriptionService(db)
    
    subscriptions = await subscription_service.list_all_subscriptions()
    
    # Enriquecer com dados da revenda
    for sub in subscriptions:
        reseller = await db.resellers.find_one({"id": sub["reseller_id"]}, {"_id": 0, "name": 1, "email": 1})
        if reseller:
            sub["reseller_name"] = reseller.get("name", "")
            sub["reseller_email"] = reseller.get("email", "")
    
    return subscriptions

# Endpoints temporários para download dos arquivos de migração
@api_router.get("/migration/backend")
async def download_backend():
    """Download do código backend"""
    file_path = "/app/migration/backend_code.tar.gz"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Backend não encontrado")
    return FileResponse(path=file_path, filename="backend_code.tar.gz", media_type="application/gzip")

@api_router.get("/migration/frontend")
async def download_frontend():
    """Download do código frontend"""
    file_path = "/app/migration/frontend_src.tar.gz"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Frontend não encontrado")
    return FileResponse(path=file_path, filename="frontend_src.tar.gz", media_type="application/gzip")

@api_router.get("/migration/database")
async def download_database():
    """Download do backup do MongoDB"""
    file_path = "/app/migration/mongodb_backup.tar.gz"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Database backup não encontrado")
    return FileResponse(path=file_path, filename="mongodb_backup.tar.gz", media_type="application/gzip")

# Download prompt otimizado
@api_router.get("/download-prompt")
async def download_prompt():
    """Download do prompt IA otimizado"""
    from fastapi.responses import Response, HTMLResponse
    file_path = "/app/PROMPT_IA_FINAL_UTF8.txt"
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return Response(
            content=content,
            media_type="text/plain; charset=utf-8",
            headers={
                "Content-Disposition": "attachment; filename=PROMPT_IA_OPTIMIZED.txt"
            }
        )
    else:
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")

@api_router.get("/view-prompt")
async def view_prompt_page():
    """Página para visualizar e copiar o prompt"""
    from fastapi.responses import HTMLResponse
    file_path = "/app/PROMPT_IA_FINAL_UTF8.txt"
    
    if not os.path.exists(file_path):
        return HTMLResponse(content="<h1>Arquivo não encontrado</h1>", status_code=404)
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Escapar para HTML
    import html
    content_escaped = html.escape(content)
    
    html_page = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Prompt IA Otimizado - Download</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f0f2f5;
        }}
        .container {{
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        .stat-box {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }}
        .stat-box h3 {{
            margin: 0;
            font-size: 14px;
            color: #666;
        }}
        .stat-box p {{
            margin: 5px 0 0 0;
            font-size: 24px;
            font-weight: bold;
            color: #333;
        }}
        .buttons {{
            display: flex;
            gap: 10px;
            margin: 20px 0;
        }}
        .btn {{
            padding: 12px 24px;
            border: none;
            border-radius: 6px;
            font-size: 16px;
            cursor: pointer;
            font-weight: bold;
            transition: all 0.3s;
        }}
        .btn-primary {{
            background: #667eea;
            color: white;
        }}
        .btn-primary:hover {{
            background: #5568d3;
        }}
        .btn-success {{
            background: #28a745;
            color: white;
        }}
        .btn-success:hover {{
            background: #218838;
        }}
        textarea {{
            width: 100%;
            height: 400px;
            padding: 15px;
            border: 2px solid #ddd;
            border-radius: 6px;
            font-family: 'Courier New', monospace;
            font-size: 12px;
            background: #f8f9fa;
        }}
        .alert {{
            padding: 15px;
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
            border-radius: 6px;
            margin: 15px 0;
            display: none;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>✅ Prompt IA Otimizado</h1>
        
        <div class="stats">
            <div class="stat-box">
                <h3>Original</h3>
                <p>744.298</p>
            </div>
            <div class="stat-box">
                <h3>Otimizado</h3>
                <p>393.532</p>
            </div>
            <div class="stat-box">
                <h3>Redução</h3>
                <p>47.1%</p>
            </div>
            <div class="stat-box">
                <h3>Status</h3>
                <p>✅ Pronto</p>
            </div>
        </div>

        <div class="buttons">
            <button class="btn btn-success" onclick="copiar()">📋 Copiar Tudo</button>
            <button class="btn btn-primary" onclick="baixar()">💾 Baixar .TXT</button>
        </div>

        <div id="alert" class="alert">✅ Copiado com sucesso!</div>

        <h3>Conteúdo do Prompt:</h3>
        <textarea id="content" readonly>{content_escaped}</textarea>
    </div>

    <script>
        const conteudo = `{content_escaped}`;
        
        function copiar() {{
            const textarea = document.getElementById('content');
            textarea.select();
            document.execCommand('copy');
            
            const alert = document.getElementById('alert');
            alert.style.display = 'block';
            setTimeout(() => alert.style.display = 'none', 3000);
        }}
        
        function baixar() {{
            const blob = new Blob([conteudo], {{ type: 'text/plain;charset=utf-8' }});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'PROMPT_IA_OPTIMIZED.txt';
            document.body.appendChild(a);
            a.click();
            URL.revokeObjectURL(url);
            document.body.removeChild(a);
        }}
    </script>
</body>
</html>
    """
    
    return HTMLResponse(content=html_page)

app.include_router(api_router)

# Include reseller routes
try:
    from reseller_routes import reseller_router
    app.include_router(reseller_router)
    print("✅ Reseller routes loaded successfully")
except Exception as e:
    print(f"❌ Failed to load reseller routes: {e}")
    import traceback
    traceback.print_exc()

# Include AI agent routes
try:
    from ai_agent_routes import ai_router
    app.include_router(ai_router, prefix="/api")
    print("✅ AI agent routes loaded successfully")
except Exception as e:
    print(f"❌ Failed to load AI agent routes: {e}")
    import traceback
    traceback.print_exc()

# Include WhatsApp routes
# ==================== WHATSAPP TEST ENDPOINT DIRETO ====================
try:
    from whatsapp_routes import router as whatsapp_router
    from whatsapp_webhook_handler import router as webhook_router
    import sys
    print("🔧 Loading WhatsApp routes...", flush=True)
    sys.stdout.flush()
    app.include_router(whatsapp_router, prefix="/api/whatsapp")
    app.include_router(webhook_router, prefix="/api")
    print("✅ WhatsApp routes loaded successfully", flush=True)
    for route in whatsapp_router.routes:
        print(f"   - {route.methods} /api/whatsapp{route.path}", flush=True)
except Exception as e:
    print(f"❌ Failed to load WhatsApp routes: {e}", flush=True)
    import traceback
    traceback.print_exc()

# Push Notification routes
try:
    from push_notification_routes import push_router
    app.include_router(push_router, prefix="/api")
    print("✅ Push notification routes loaded successfully")
except Exception as e:
    print(f"❌ Failed to load push notification routes: {e}")
    import traceback
    traceback.print_exc()

# Payment and Subscription routes
try:
    from payment_routes import router as payment_router
    app.include_router(payment_router, prefix="/api")
    print("✅ Payment routes loaded successfully")
except Exception as e:
    print(f"❌ Failed to load Payment routes: {e}")
    import traceback
    traceback.print_exc()

# Webhook routes
try:
    from webhook_routes import router as webhook_router
    app.include_router(webhook_router, prefix="/api")
    print("✅ Webhook routes loaded successfully")
except Exception as e:
    print(f"❌ Failed to load Webhook routes: {e}")
    import traceback
    traceback.print_exc()

# Admin Payment Config routes
try:
    from admin_payment_routes import router as admin_payment_router
    app.include_router(admin_payment_router, prefix="/api")
    print("✅ Admin Payment routes loaded successfully")
except Exception as e:
    print(f"❌ Failed to load Admin Payment routes: {e}")
    import traceback
    traceback.print_exc()

# Dashboard routes
try:
    from dashboard_routes import router as dashboard_router
    app.include_router(dashboard_router, prefix="/api")
    print("✅ Dashboard routes loaded successfully")
except Exception as e:
    print(f"❌ Failed to load Dashboard routes: {e}")
    import traceback
    traceback.print_exc()

# Vendas routes (Sistema de Vendas CyberTV)
try:
    from vendas_routes_new import router as vendas_router
    app.include_router(vendas_router)
    print("✅ Vendas routes loaded successfully")
except Exception as e:
    print(f"❌ Failed to load Vendas routes: {e}")
    import traceback
    traceback.print_exc()

# Office routes (gestor.my integration)
try:
    from office_routes import router as office_router
    app.include_router(office_router, prefix="/api", tags=['office'])
    print("✅ Office routes loaded successfully")
except Exception as e:
    print(f"❌ Failed to load Office routes: {e}")

# Office Sync routes (sincronização automática de clientes)
try:
    from office_sync_routes import router as office_sync_router
    app.include_router(office_sync_router)
    print("✅ Office Sync routes loaded successfully")
except Exception as e:
    print(f"❌ Failed to load Office Sync routes: {e}")

# Office Credentials routes (gerenciamento de credenciais)
try:
    from office_credentials_routes import router as office_credentials_router
    app.include_router(office_credentials_router)
    print("✅ Office Credentials routes loaded successfully")
except Exception as e:
    print(f"❌ Failed to load Office Credentials routes: {e}")

# Iniciar scheduler de sincronização automática
try:
    from office_sync_service import OfficeSyncService
    from office_sync_scheduler import OfficeSyncScheduler
    
    office_sync_service = OfficeSyncService(db)
    office_sync_scheduler = OfficeSyncScheduler(office_sync_service)
    office_sync_scheduler.start()
    print("✅ Office Sync Scheduler iniciado (sincronização a cada 6 horas)")
except Exception as e:
    print(f"❌ Failed to start Office Sync Scheduler: {e}")

# XUI routes (IPTV integration)
try:
    from xui_routes import router as xui_router
    app.include_router(xui_router)
    print("✅ XUI routes loaded successfully")
except Exception as e:
    print(f"❌ Failed to load XUI routes: {e}")

# Scheduled Messages routes
try:
    from scheduled_messages_routes import router as scheduled_messages_router
    app.include_router(scheduled_messages_router, prefix="/api", tags=['scheduled_messages'])
    print("✅ Scheduled Messages routes loaded successfully")
except Exception as e:
    print(f"❌ Failed to load Scheduled Messages routes: {e}")

# Reminder routes
try:
    from reminder_routes import router as reminder_router
    app.include_router(reminder_router, prefix="/api", tags=['reminders'])
    print("✅ Reminder routes loaded successfully")
except Exception as e:
    print(f"❌ Failed to load Reminder routes: {e}")

# Credential Auto-Search routes
try:
    from credential_auto_search_routes import router as credential_search_router
    app.include_router(credential_search_router, prefix="/api", tags=['credential_search'])
    print("✅ Credential Auto-Search routes loaded successfully")
except Exception as e:
    print(f"❌ Failed to load Credential Auto-Search routes: {e}")
    import traceback
    traceback.print_exc()

# Client Name Auto-Update routes
try:
    from client_name_routes import router as client_name_router
    app.include_router(client_name_router)
    print("✅ Client Name Auto-Update routes loaded successfully")
except Exception as e:
    print(f"❌ Failed to load Client Name routes: {e}")
    import traceback
    traceback.print_exc()

# AI Memory Management routes
try:
    from ai_memory_routes import router as ai_memory_router
    app.include_router(ai_memory_router)
    print("✅ AI Memory Management routes loaded successfully")
except Exception as e:
    print(f"❌ Failed to load AI Memory Management routes: {e}")
    import traceback
    traceback.print_exc()


# Vendas Bot Config routes (Admin)
try:
    from vendas_bot_config_routes import router as vendas_bot_config_router
    app.include_router(vendas_bot_config_router)
    print("✅ Vendas Bot Config routes loaded successfully")
except Exception as e:
    print(f"❌ Failed to load Vendas Bot Config routes: {e}")
    import traceback
    traceback.print_exc()

# Admin Extensions routes (IPTV, WhatsApp Plans, Mercado Pago, etc)
try:
    from admin_extensions_routes import router as admin_extensions_router
    app.include_router(admin_extensions_router, prefix="/api")
    print("✅ Admin Extensions routes loaded successfully")
except Exception as e:
    print(f"❌ Failed to load Admin Extensions routes: {e}")
    import traceback
    traceback.print_exc()


# Vendas Simple Config routes (Admin - WA Site)
try:
    from vendas_simple_config_routes_v2 import router as vendas_simple_config_router
    app.include_router(vendas_simple_config_router)
    print("✅ Vendas Simple Config routes loaded successfully")
except Exception as e:
    print(f"❌ Failed to load Vendas Simple Config routes: {e}")
    import traceback
    traceback.print_exc()

# Correct/Wrong Knowledge Base routes
try:
    from correct_wrong_knowledge import router as correct_wrong_router
    app.include_router(correct_wrong_router)
    print("✅ Correct/Wrong Knowledge routes loaded successfully")
except Exception as e:
    print(f"❌ Failed to load Correct/Wrong Knowledge routes: {e}")
    import traceback
    traceback.print_exc()

# AI Learning routes (Sistema de Aprendizado)
try:
    from ai_learning_routes import router as ai_learning_router
    app.include_router(ai_learning_router)
    print("✅ AI Learning routes loaded successfully")
except Exception as e:
    print(f"❌ Failed to load AI Learning routes: {e}")
    import traceback
    traceback.print_exc()

# Media Processing routes (Áudio, Imagem e Vídeo) - TEMPORARILY DISABLED DUE TO SYNTAX ERROR
# try:
#     from media_routes import router as media_router
#     app.include_router(media_router)
#     print("✅ Media Processing routes loaded successfully")
# except Exception as e:
#     print(f"❌ Failed to load Media Processing routes: {e}")
#     import traceback
#     traceback.print_exc()
print("⚠️ Media Processing routes temporarily disabled")


# Health check route (no prefix needed)
app.include_router(health_router, prefix="/api")
print("✅ Health check endpoint available at /api/health")

# Backup routes
try:
    from backup_routes import router as backup_router
    app.include_router(backup_router, prefix="/api")
    
    # Botões Interativos WA Site
    try:
        from vendas_buttons_routes import router as buttons_router, public_router as buttons_public_router
        app.include_router(buttons_router)
        app.include_router(buttons_public_router)
        print("✅ Vendas Buttons routes loaded successfully")
    except Exception as e:
        print(f"❌ Error loading vendas buttons routes: {e}")
        import traceback
        traceback.print_exc()
    print("✅ Backup routes loaded successfully")
except Exception as e:
    print(f"❌ Failed to load Backup routes: {e}")
    import traceback
    traceback.print_exc()

# Include Simple Download routes
try:
    from simple_download import router as download_router
    app.include_router(download_router, prefix="/api")
    print("✅ Simple download routes loaded successfully")
except Exception as e:
    print(f"⚠️ Simple download routes not loaded: {e}")

# Export routes for syncing to external server
# try:
#     from export_routes import export_router
#     app.include_router(export_router, prefix="/api", tags=['export'])
#     print("✅ Export routes loaded successfully")
# except Exception as e:
#     print(f"❌ Failed to load Export routes: {e}")
#     import traceback
#     traceback.print_exc()


# Custom endpoint for video streaming with Range support

# Upload endpoint for media files
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Upload de arquivo (foto, vídeo, áudio)
    """
    try:
        logger.info(f"📤 Upload recebido: {file.filename} ({file.content_type})")
        
        # Ler arquivo
        file_content = await file.read()
        file_size = len(file_content)
        
        logger.info(f"📦 Tamanho: {file_size} bytes")
        
        # Salvar arquivo usando media_service
        from media_service import save_media_file
        
        media_url = await save_media_file(
            file_content=file_content,
            filename=file.filename,
            content_type=file.content_type
        )
        
        logger.info(f"✅ Mídia salva: {media_url}")
        
        # Determinar tipo de mídia
        kind = 'file'
        if file.content_type:
            if file.content_type.startswith('image/'):
                kind = 'image'
            elif file.content_type.startswith('video/'):
                kind = 'video'
            elif file.content_type.startswith('audio/'):
                kind = 'audio'
        
        return {
            "success": True,
            "url": media_url,
            "kind": kind,
            "filename": file.filename,
            "size": file_size
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao fazer upload: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao fazer upload: {str(e)}")


@app.get("/api/uploads/{filename}")
async def serve_upload(filename: str, request: Request):
    """
    Serve uploaded files with Range request support (required for video playback)
    """
    file_path = UPLOADS_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    # Get file stats
    file_size = file_path.stat().st_size
    mime_type = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
    
    # Check if Range header exists (for video streaming)
    range_header = request.headers.get("range")
    
    if range_header:
        # Parse range header (e.g., "bytes=0-1023")
        range_match = re.match(r"bytes=(\d+)-(\d*)", range_header)
        if range_match:
            start = int(range_match.group(1))
            end = int(range_match.group(2)) if range_match.group(2) else file_size - 1
            end = min(end, file_size - 1)
            
            # Read the requested chunk
            async with aiofiles.open(file_path, 'rb') as f:
                await f.seek(start)
                chunk = await f.read(end - start + 1)
            
            headers = {
                "Content-Range": f"bytes {start}-{end}/{file_size}",
                "Accept-Ranges": "bytes",
                "Content-Length": str(len(chunk)),
                "Content-Type": mime_type,
            }
            
            return StreamingResponse(
                iter([chunk]),
                status_code=206,
                headers=headers,
                media_type=mime_type
            )
    
    # No range request - serve full file
    return FileResponse(
        file_path,
        media_type=mime_type,
        headers={
            "Accept-Ranges": "bytes",
            "Content-Length": str(file_size),
        }
    )

# Fallback: Serve uploads as static files (for non-video files)
# app.mount("/api/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")

# Mount static directory for migration package
app.mount("/static", StaticFiles(directory="/app/backend/static"), name="static")

# Tenant Detection Middleware
class TenantMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Detectar tenant pelo domínio
        tenant_ctx = await detect_tenant(request, db)
        
        # Armazenar no contexto global
        global_tenant_context.reseller_id = tenant_ctx.reseller_id
        global_tenant_context.reseller_data = tenant_ctx.reseller_data
        global_tenant_context.is_master = tenant_ctx.is_master
        
        # Adicionar ao request state para acesso nas rotas
        request.state.tenant = tenant_ctx
        
        response = await call_next(request)
        return response

# TenantMiddleware reabilitado - suporte.help e 151.243.218.223 configurados como master domains
app.add_middleware(TenantMiddleware)

@app.get("/api/debug/tenant")
async def debug_tenant(request: Request):
    from tenant_middleware import get_current_tenant
    tenant_ctx = get_current_tenant()
    
    return {
        "domain": request.headers.get("host", ""),
        "tenant_id": tenant_ctx.reseller_id,
        "is_master": tenant_ctx.is_master,
        "tenant_data": tenant_ctx.reseller_data.get("name") if tenant_ctx.reseller_data else None
    }

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==================== DEBUG WHATSAPP ENDPOINT ====================
# DEPLOYED AT: 2025-11-09 16:40:00 UTC - VERSION 2.0
@app.get("/api/whatsapp-debug")
async def whatsapp_debug_endpoint():
    """Endpoint de debug para WhatsApp - SEM AUTH"""
    import socket
    import os
    return {
        "status": "OK",
        "message": "WhatsApp debug endpoint working! Version 2.0",
        "hostname": socket.gethostname(),
        "pid": os.getpid(),
        "version": "2.0-2025-11-09-16:40",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

# ==================== RECOVERY ENDPOINT ====================
# ENDPOINT TEMPORÁRIO PARA RECUPERAÇÃO DO SERVIDOR EXTERNO
@app.get("/api/recovery/download")
async def download_recovery_files():
    """
    Endpoint temporário para baixar arquivos de recuperação
    """
    import os
    
    # Tentar primeiro o pacote multimodal completo
    multimodal_file = "/tmp/iaze_multimodal_complete.tar.gz"
    recovery_file = "/tmp/iaze_recovery/iaze_recovery_files.tar.gz"
    
    file_to_send = multimodal_file if os.path.exists(multimodal_file) else recovery_file
    
    if not os.path.exists(file_to_send):
        raise HTTPException(status_code=404, detail="Arquivo de recuperação não encontrado")
    
    return FileResponse(
        file_to_send,
        media_type="application/gzip",
        filename="iaze_recovery_files.tar.gz"
    )

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
