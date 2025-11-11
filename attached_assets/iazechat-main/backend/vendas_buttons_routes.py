"""
Rotas da API para sistema de botões interativos
"""
from fastapi import APIRouter, HTTPException, Depends, File, UploadFile
from typing import Optional, Dict, Any
from vendas_buttons_service import ButtonsService, ButtonConfig, Button
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
import os
import shutil
import uuid
from pathlib import Path

router = APIRouter(prefix="/api/admin/vendas-bot/buttons", tags=["vendas-buttons"])

# MongoDB
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'support_chat')
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

buttons_service = ButtonsService(db)

# Sem auth por enquanto - TODO: adicionar depois
def no_auth():
    return {"user_type": "admin", "reseller_id": None}

@router.get("/config")
async def get_button_config(current_user: dict = Depends(no_auth)):
    """Obter configuração de botões"""
    reseller_id = current_user.get("reseller_id") if current_user.get("user_type") == "reseller" else None
    config = await buttons_service.get_config(reseller_id)
    return config.dict()

@router.post("/config")
async def save_button_config(
    config: ButtonConfig, 
    current_user: dict = Depends(no_auth)
):
    """Salvar configuração de botões"""
    reseller_id = current_user.get("reseller_id") if current_user.get("user_type") == "reseller" else None
    await buttons_service.save_config(config, reseller_id)
    return {"ok": True, "message": "Configuração de botões salva com sucesso"}

@router.post("/create-default")
async def create_default_config(current_user: dict = Depends(no_auth)):
    """Criar configuração padrão de botões"""
    default_config = buttons_service.create_default_buttons()
    reseller_id = current_user.get("reseller_id") if current_user.get("user_type") == "reseller" else None
    await buttons_service.save_config(default_config, reseller_id)
    return {"ok": True, "config": default_config.dict()}

@router.post("/add-button")
async def add_button(
    button: Button,
    parent_id: Optional[str] = None,
    current_user: dict = Depends(no_auth)
):
    """Adicionar novo botão (raiz ou filho)"""
    reseller_id = current_user.get("reseller_id") if current_user.get("user_type") == "reseller" else None
    config = await buttons_service.get_config(reseller_id)
    
    if parent_id:
        # Adicionar como filho
        def add_to_parent(buttons, target_id, new_button):
            for btn in buttons:
                if btn.id == target_id:
                    btn.sub_buttons.append(new_button)
                    return True
                if btn.sub_buttons:
                    if add_to_parent(btn.sub_buttons, target_id, new_button):
                        return True
            return False
        
        if not add_to_parent(config.root_buttons, parent_id, button):
            raise HTTPException(status_code=404, detail="Botão pai não encontrado")
    else:
        # Adicionar como botão raiz
        config.root_buttons.append(button)
    
    await buttons_service.save_config(config, reseller_id)
    return {"ok": True, "message": "Botão adicionado"}

@router.delete("/button/{button_id}")
async def delete_button(
    button_id: str,
    current_user: dict = Depends(no_auth)
):
    """Deletar botão"""
    reseller_id = current_user.get("reseller_id") if current_user.get("user_type") == "reseller" else None
    config = await buttons_service.get_config(reseller_id)
    
    def remove_button(buttons, target_id):
        for i, btn in enumerate(buttons):
            if btn.id == target_id:
                buttons.pop(i)
                return True
            if btn.sub_buttons:
                if remove_button(btn.sub_buttons, target_id):
                    return True
        return False
    
    if not remove_button(config.root_buttons, button_id):
        raise HTTPException(status_code=404, detail="Botão não encontrado")
    
    await buttons_service.save_config(config, reseller_id)
    return {"ok": True, "message": "Botão removido"}

@router.put("/mode")
async def update_mode(
    mode: str,
    current_user: dict = Depends(no_auth)
):
    """Atualizar modo (button, ia, hibrido)"""
    if mode not in ["button", "ia", "hibrido"]:
        raise HTTPException(status_code=400, detail="Modo inválido")
    
    reseller_id = current_user.get("reseller_id") if current_user.get("user_type") == "reseller" else None
    config = await buttons_service.get_config(reseller_id)
    config.operation_mode = mode
    await buttons_service.save_config(config, reseller_id)
    return {"ok": True, "operation_mode": mode}

# Rotas públicas para interação do cliente
public_router = APIRouter(prefix="/api/vendas/buttons", tags=["vendas-buttons-public"])

@public_router.get("/{session_id}")
async def get_buttons_for_session(session_id: str):
    """Obter botões disponíveis para uma sessão"""
    config = await buttons_service.get_config()
    
    if not config.is_enabled:
        return {"buttons": [], "message": "Sistema de botões desabilitado"}
    
    if config.operation_mode == "ia":
        return {"buttons": [], "message": "Modo IA ativo", "use_ai": True}
    
    buttons = await buttons_service.get_buttons_for_user(session_id)
    return {
        "welcome_message": config.welcome_message,
        "buttons": [b.dict() for b in buttons],
        "operation_mode": config.operation_mode
    }

@public_router.post("/{session_id}/click")
async def handle_button_click_endpoint(session_id: str, data: Dict[str, str]):
    """Processar clique em botão"""
    button_id = data.get("button_id")
    if not button_id:
        raise HTTPException(status_code=400, detail="button_id é obrigatório")
    
    result = await buttons_service.handle_button_click(session_id, button_id)
    return result

@public_router.post("/{session_id}/reset")
async def reset_session_endpoint(session_id: str):
    """Resetar sessão para menu principal"""
    result = await buttons_service.reset_session(session_id)
    return {"ok": True, "message": "Sessão resetada"}

@router.post("/create-user")
async def create_user_via_api(
    request: dict,
    current_user: dict = Depends(no_auth)
):
    """
    Criar usuário via API externa configurada no botão
    Sistema de controle: 1 teste por número de WhatsApp
    """
    try:
        import requests
        
        button_id = request.get('button_id')
        user_data = request.get('user_data')  # {name, whatsapp, pin}
        whatsapp = user_data.get('whatsapp')
        
        # 🔒 VERIFICAR SE JÁ EXISTE TESTE ATIVO PARA ESTE NÚMERO
        existing_test = await db.vendas_credentials.find_one({
            "whatsapp": whatsapp,
            "test_status": "active"  # Teste ativo (não pagou ainda)
        })
        
        if existing_test:
            # ❌ Já tem teste ativo - retornar credenciais existentes
            return {
                "ok": False,
                "already_exists": True,
                "message": "Você já possui um teste ativo!",
                "credentials": {
                    "whatsapp": existing_test.get('whatsapp'),
                    "name": existing_test.get('name'),
                    "pin": existing_test.get('pin'),
                    "generated_user": existing_test.get('generated_user'),
                    "generated_password": existing_test.get('generated_password'),
                    "panel_name": existing_test.get('panel_name'),
                    "created_at": existing_test.get('created_at')
                }
            }
        
        # ✅ Não tem teste ativo - criar novo usuário
        
        # Buscar configuração do botão
        buttons_service = ButtonsService(db)
        button_config = await buttons_service.get_config()
        
        # Encontrar botão específico
        def find_button(buttons, btn_id):
            for btn in buttons:
                if btn.id == btn_id:
                    return btn
                if btn.sub_buttons:
                    found = find_button(btn.sub_buttons, btn_id)
                    if found:
                        return found
            return None
        
        button = find_button(button_config.root_buttons, button_id)
        
        if not button or not button.api_url:
            raise HTTPException(status_code=400, detail="Botão não configurado para criar usuário")
        
        # Fazer requisição para API externa
        headers = button.api_headers or {'Content-Type': 'application/json'}
        
        api_response = requests.request(
            method=button.api_method,
            url=button.api_url,
            json=user_data,
            headers=headers,
            timeout=30
        )
        
        if api_response.status_code >= 400:
            raise HTTPException(
                status_code=api_response.status_code,
                detail=f"Erro na API externa: {api_response.text}"
            )
        
        # Salvar credenciais do cliente no banco com status de teste
        credentials = {
            "whatsapp": user_data.get('whatsapp'),
            "name": user_data.get('name'),
            "pin": user_data.get('pin'),
            "generated_user": api_response.json().get('username') or api_response.json().get('user'),
            "generated_password": api_response.json().get('password') or api_response.json().get('senha'),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "panel_name": button.label,
            "test_status": "active",  # 🔒 Teste ativo (bloqueado para novo teste)
            "payment_status": "pending"  # Pagamento pendente
        }
        
        # Inserir credenciais
        await db.vendas_credentials.insert_one(credentials)
        
        return {
            "ok": True,
            "already_exists": False,
            "credentials": credentials,
            "api_response": api_response.json()
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/mark-payment")
async def mark_payment_done(
    request: dict,
    current_user: dict = Depends(no_auth)
):
    """
    Marcar pagamento como realizado e liberar número para novos testes
    """
    try:
        whatsapp = request.get('whatsapp')
        
        if not whatsapp:
            raise HTTPException(status_code=400, detail="WhatsApp não informado")
        
        # Atualizar status para pagamento realizado
        result = await db.vendas_credentials.update_one(
            {"whatsapp": whatsapp, "test_status": "active"},
            {"$set": {
                "test_status": "completed",
                "payment_status": "paid",
                "payment_date": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Nenhum teste ativo encontrado")
        
        return {
            "ok": True,
            "message": "Pagamento registrado! Você pode criar novos testes agora."
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload-media")
async def upload_button_media(
    file: UploadFile = File(...),
    current_user: dict = Depends(no_auth)
):
    """
    Upload de foto/vídeo para botões
    Aceita: JPG, PNG, GIF, MP4, MOV
    """
    # Validar tipo de arquivo
    allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.mp4', '.mov', '.avi'}
    file_ext = Path(file.filename).suffix.lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"Tipo de arquivo não permitido. Use: {', '.join(allowed_extensions)}"
        )
    
    # Determinar tipo de mídia
    media_type = "image" if file_ext in {'.jpg', '.jpeg', '.png', '.gif'} else "video"
    
    # Criar diretório de uploads se não existir
    upload_dir = Path("/var/www/iaze/uploads/buttons")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Gerar nome único
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = upload_dir / unique_filename
    
    # Salvar arquivo
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Retornar URL pública
    media_url = f"/uploads/buttons/{unique_filename}"
    
    return {
        "ok": True,
        "media_url": media_url,
        "media_type": media_type,
        "filename": file.filename
    }
