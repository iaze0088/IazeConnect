"""
Sistema de Botões Interativos para WA Site
Permite criar menus hierárquicos com botões clicáveis
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from fastapi import HTTPException
import uuid

class Button(BaseModel):
    """Modelo de botão individual"""
    id: str
    label: str  # Texto do botão (ex: "SUPORTE", "TESTE GRÁTIS")
    response_text: str  # Mensagem enviada quando botão é clicado
    sub_buttons: List['Button'] = []  # Botões filhos (hierarquia)
    action_type: str = "message"  # "message", "redirect", "ai", "create_user"
    is_active: bool = True
    # 🆕 Campos de mídia
    media_url: Optional[str] = None  # URL da foto/vídeo
    media_type: Optional[str] = None  # "image" ou "video"
    # 🆕 Campo de redirecionamento
    redirect_url: Optional[str] = None  # URL para abrir ao clicar (ex: WhatsApp, site)
    # 🆕 Configuração de API para criação de usuário
    api_url: Optional[str] = None  # URL da API para criar usuário
    api_method: Optional[str] = "POST"  # Método HTTP (POST, GET)
    api_headers: Optional[dict] = None  # Headers customizados
    # 🆕 Personalização visual do botão
    pulse: Optional[bool] = False  # Botão pulsante (animação)
    color: Optional[str] = "green"  # Cor: "green", "blue", "red"
    
    class Config:
        extra = "ignore"  # Ignorar campos extras que não estão no modelo

class ButtonConfig(BaseModel):
    """Configuração do sistema de botões"""
    status: int = 3  # 🔧 1=button, 2=ia, 3=hybrid
    welcome_message: str = "Por favor, selecione uma das opções abaixo:"
    root_buttons: List[Button] = []
    is_enabled: bool = True
    # 🆕 Personalização do bot
    bot_name: Optional[str] = "Assistente Virtual"  # Nome do bot
    bot_avatar_url: Optional[str] = None  # URL da foto de perfil

class ButtonsService:
    """Serviço para gerenciar botões interativos"""
    
    def __init__(self, db):
        self.db = db
    
    async def get_config(self, reseller_id: Optional[str] = None) -> ButtonConfig:
        """Obter configuração de botões"""
        collection = self.db.reseller_configs if reseller_id else self.db.config
        query = {"reseller_id": reseller_id} if reseller_id else {"id": "config"}
        
        config = await collection.find_one(query)
        if not config or "button_config" not in config:
            return ButtonConfig()
        
        return ButtonConfig(**config["button_config"])
    
    async def save_config(self, button_config: ButtonConfig, reseller_id: Optional[str] = None):
        """Salvar configuração de botões"""
        collection = self.db.reseller_configs if reseller_id else self.db.config
        query = {"reseller_id": reseller_id} if reseller_id else {"id": "config"}
        
        # Garantir que o documento tem o campo de identificação
        update_data = {"button_config": button_config.dict()}
        if not reseller_id:
            update_data["id"] = "config"
        else:
            update_data["reseller_id"] = reseller_id
        
        await collection.update_one(
            query,
            {"$set": update_data},
            upsert=True
        )
    
    async def get_buttons_for_user(self, session_id: str, reseller_id: Optional[str] = None) -> List[Button]:
        """Obter botões para exibir ao usuário baseado no contexto da sessão"""
        config = await self.get_config(reseller_id)
        
        if not config.is_enabled or config.status == 2:  # 2 = apenas IA
            return []
        
        # Verificar se usuário está em algum sub-menu
        session = await self.db.vendas_sessions.find_one({"session_id": session_id})
        if session and "button_path" in session:
            # Usuário está em sub-menu, retornar botões filhos
            return self._get_buttons_by_path(config.root_buttons, session["button_path"])
        
        # Retornar botões raiz
        return config.root_buttons
    
    def _get_buttons_by_path(self, buttons: List[Button], path: List[str]) -> List[Button]:
        """Navegar hierarquia de botões usando path"""
        current_buttons = buttons
        for button_id in path:
            found = next((b for b in current_buttons if b.id == button_id), None)
            if found:
                current_buttons = found.sub_buttons
            else:
                break
        return current_buttons
    
    async def handle_button_click(
        self, 
        session_id: str, 
        button_id: str, 
        reseller_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Processar clique em botão"""
        config = await self.get_config(reseller_id)
        
        # Buscar o botão clicado
        session = await self.db.vendas_sessions.find_one({"session_id": session_id})
        current_path = session.get("button_path", []) if session else []
        
        current_buttons = self._get_buttons_by_path(config.root_buttons, current_path)
        clicked_button = next((b for b in current_buttons if b.id == button_id), None)
        
        if not clicked_button:
            raise HTTPException(status_code=404, detail="Botão não encontrado")
        
        # Atualizar path da sessão
        new_path = current_path + [button_id]
        await self.db.vendas_sessions.update_one(
            {"session_id": session_id},
            {"$set": {"button_path": new_path}},
            upsert=True
        )
        
        # Retornar resposta (incluindo mídia)
        result = {
            "response_text": clicked_button.response_text,
            "has_sub_buttons": len(clicked_button.sub_buttons) > 0,
            "sub_buttons": clicked_button.sub_buttons if clicked_button.sub_buttons else [],
            "action_type": clicked_button.action_type,
            "media_url": clicked_button.media_url,
            "media_type": clicked_button.media_type
        }
        
        return result
    
    async def reset_session(self, session_id: str):
        """Resetar sessão para voltar ao menu principal"""
        await self.db.vendas_sessions.update_one(
            {"session_id": session_id},
            {"$set": {"button_path": []}},
            upsert=True
        )
    
    def create_default_buttons(self) -> ButtonConfig:
        """Criar botões padrão de exemplo"""
        return ButtonConfig(
            mode="button",
            welcome_message="Olá! Como posso ajudar você hoje? Selecione uma opção:",
            root_buttons=[
                Button(
                    id=str(uuid.uuid4()),
                    label="📞 SUPORTE",
                    response_text="Você será atendido por nossa equipe de suporte em breve.",
                    action_type="message",
                    sub_buttons=[]
                ),
                Button(
                    id=str(uuid.uuid4()),
                    label="🎁 TESTE GRÁTIS",
                    response_text="Ótimo! Vamos configurar seu teste grátis. Por favor, informe:",
                    action_type="message",
                    sub_buttons=[
                        Button(
                            id=str(uuid.uuid4()),
                            label="📱 Como funciona?",
                            response_text="Nosso teste grátis dura 24 horas e você tem acesso completo!",
                            action_type="message"
                        ),
                        Button(
                            id=str(uuid.uuid4()),
                            label="✅ Quero o teste!",
                            response_text="Perfeito! Me informe seu CPF para gerar o teste.",
                            action_type="message"
                        )
                    ]
                ),
                Button(
                    id=str(uuid.uuid4()),
                    label="💼 SEJA REVENDEDOR",
                    response_text="Excelente escolha! Nossas condições de revenda são:",
                    action_type="message",
                    sub_buttons=[
                        Button(
                            id=str(uuid.uuid4()),
                            label="💰 Valores",
                            response_text="Planos de revenda a partir de R$ 50/mês com margem de lucro de 40%!",
                            action_type="message"
                        ),
                        Button(
                            id=str(uuid.uuid4()),
                            label="📋 Como começar",
                            response_text="Para começar, você precisa escolher um plano e fazer o cadastro.",
                            action_type="message"
                        )
                    ]
                )
            ],
            is_enabled=True
        )

# Permitir referências recursivas
Button.model_rebuild()
