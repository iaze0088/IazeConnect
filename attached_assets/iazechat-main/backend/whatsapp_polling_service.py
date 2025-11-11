"""
Serviço de Polling para Evolution API
Busca mensagens a cada 10 segundos de todas as instâncias conectadas
"""
import asyncio
import logging
from datetime import datetime, timezone
import uuid
import httpx
from motor.motor_asyncio import AsyncIOMotorClient
import os

logger = logging.getLogger(__name__)

EVOLUTION_API_URL = os.environ.get('EVOLUTION_API_URL', 'http://151.243.218.223:9000')
EVOLUTION_API_KEY = os.environ.get('EVOLUTION_API_KEY', 'iaze-evolution-2025-secure-key')
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')

class WhatsAppPollingService:
    def __init__(self):
        self.client = AsyncIOMotorClient(MONGO_URL)
        self.db = self.client.support_chat
        self.running = False
        self.http_client = httpx.AsyncClient(timeout=30.0)
        
    async def get_connected_instances(self):
        """Busca todas as instâncias conectadas da Evolution API"""
        try:
            url = f"{EVOLUTION_API_URL}/instance/fetchInstances"
            headers = {"apikey": EVOLUTION_API_KEY}
            
            response = await self.http_client.get(url, headers=headers)
            if response.status_code == 200:
                instances = response.json()
                # Filtra apenas as conectadas
                connected = [inst for inst in instances if inst.get('connectionStatus') == 'open']
                logger.info(f"📱 Instâncias conectadas: {len(connected)}")
                return connected
            else:
                logger.error(f"Erro ao buscar instâncias: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"Erro ao buscar instâncias: {e}")
            return []
    
    async def get_messages_from_instance(self, instance_name: str):
        """Busca mensagens de uma instância específica"""
        try:
            # Busca últimas mensagens (Evolution API v2.1.1)
            url = f"{EVOLUTION_API_URL}/chat/findMessages/{instance_name}"
            headers = {"apikey": EVOLUTION_API_KEY}
            params = {"limit": 50}  # Últimas 50 mensagens
            
            response = await self.http_client.get(url, headers=headers, params=params)
            if response.status_code == 200:
                messages = response.json()
                return messages
            else:
                logger.warning(f"Erro ao buscar mensagens de {instance_name}: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"Erro ao buscar mensagens: {e}")
            return []
    
    async def process_message(self, message: dict, instance_name: str):
        """Processa uma mensagem e cria ticket se necessário"""
        try:
            # Extrai dados da mensagem
            key = message.get('key', {})
            message_info = message.get('message', {})
            from_me = key.get('fromMe', False)
            
            # Ignora mensagens enviadas pelo bot
            if from_me:
                return
            
            # Extrai número do remetente
            remote_jid = key.get('remoteJid', '')
            if not remote_jid or '@g.us' in remote_jid:  # Ignora grupos
                return
                
            phone_number = remote_jid.split('@')[0]
            message_id = key.get('id', '')
            
            # Verifica se já processamos esta mensagem
            existing = await self.db.messages.find_one({"whatsapp_message_id": message_id})
            if existing:
                return  # Já processada
            
            # Extrai texto
            text = ""
            if 'conversation' in message_info:
                text = message_info['conversation']
            elif 'extendedTextMessage' in message_info:
                text = message_info['extendedTextMessage'].get('text', '')
            
            if not text:
                return  # Sem texto
            
            logger.info(f"📨 Nova mensagem de {phone_number}: {text[:30]}...")
            
            # Busca departamento WHATSAPP STARTER
            department = await self.db.departments.find_one({
                "name": "WHATSAPP STARTER",
                "type": "whatsapp"
            })
            
            if not department:
                logger.error("Departamento WHATSAPP STARTER não encontrado!")
                return
            
            # Busca ou cria ticket
            ticket = await self.db.tickets.find_one({
                "whatsapp": phone_number,
                "status": {"$in": ["open", "waiting", "attending"]}
            })
            
            if not ticket:
                # Cria novo ticket
                ticket_id = str(uuid.uuid4())
                ticket = {
                    "id": ticket_id,
                    "whatsapp": phone_number,
                    "status": "open",
                    "department": department["id"],
                    "agent_id": None,
                    "whatsapp_origin": True,
                    "whatsapp_instance": instance_name,
                    "is_whatsapp": True,
                    "ticket_origin": "whatsapp_qr",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
                await self.db.tickets.insert_one(ticket)
                logger.info(f"✅ Ticket criado: {ticket_id}")
            else:
                ticket_id = ticket["id"]
            
            # Salva mensagem
            msg_doc = {
                "id": str(uuid.uuid4()),
                "ticket_id": ticket_id,
                "whatsapp": phone_number,
                "whatsapp_message_id": message_id,
                "message": text,
                "from_type": "client",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            
            await self.db.messages.insert_one(msg_doc)
            logger.info(f"✅ Mensagem salva no ticket {ticket_id}")
            
        except Exception as e:
            logger.error(f"Erro ao processar mensagem: {e}")
    
    async def poll_messages(self):
        """Função principal de polling"""
        logger.info("🔄 Iniciando serviço de polling...")
        
        while self.running:
            try:
                # Busca instâncias conectadas
                instances = await self.get_connected_instances()
                
                for instance in instances:
                    instance_name = instance.get('name')
                    if not instance_name:
                        continue
                    
                    # Busca mensagens da instância
                    messages = await self.get_messages_from_instance(instance_name)
                    
                    # Processa cada mensagem
                    for message in messages:
                        await self.process_message(message, instance_name)
                
            except Exception as e:
                logger.error(f"Erro no polling: {e}")
            
            # Aguarda 10 segundos
            await asyncio.sleep(10)
    
    async def start(self):
        """Inicia o serviço de polling"""
        self.running = True
        await self.poll_messages()
    
    async def stop(self):
        """Para o serviço de polling"""
        self.running = False
        await self.http_client.aclose()
        self.client.close()

# Instância global
polling_service = WhatsAppPollingService()
