"""
Rotas Admin para Configurações do Mercado Pago
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from server import get_current_user, db
from pydantic import BaseModel

router = APIRouter()

class MercadoPagoConfigData(BaseModel):
    access_token: str
    public_key: str
    webhook_secret: str = ""
    enabled: bool = True

@router.get("/admin/mercado-pago/config")
async def get_mercado_pago_config(
    current_user: dict = Depends(get_current_user)
):
    """Obter configurações do Mercado Pago (apenas admin)"""
    if current_user["user_type"] != "admin":
        raise HTTPException(status_code=403, detail="Apenas administradores")
    
    config = await db.mercado_pago_config.find_one({}, {"_id": 0})
    
    return {"config": config}

@router.post("/admin/mercado-pago/config")
async def save_mercado_pago_config(
    data: MercadoPagoConfigData,
    current_user: dict = Depends(get_current_user)
):
    """Salvar configurações do Mercado Pago (apenas admin)"""
    print(f"🔍 DEBUG - current_user: {current_user}")
    print(f"🔍 DEBUG - user_type: {current_user.get('user_type')}")
    
    if current_user.get("user_type") != "admin":
        raise HTTPException(status_code=403, detail=f"Apenas administradores. Tipo atual: {current_user.get('user_type')}")
    
    # Deletar config antiga
    await db.mercado_pago_config.delete_many({})
    
    # Inserir nova (MongoDB adiciona _id automaticamente)
    config_dict = data.dict()
    result = await db.mercado_pago_config.insert_one(config_dict)
    
    # Buscar config salva sem _id
    saved_config = await db.mercado_pago_config.find_one({}, {"_id": 0})
    
    print(f"✅ Mercado Pago config saved successfully")
    
    return {"ok": True, "message": "Configurações salvas com sucesso", "config": saved_config}

@router.post("/admin/mercado-pago/test")
async def test_mercado_pago_connection(
    data: dict,
    current_user: dict = Depends(get_current_user)
):
    """Testar conexão com Mercado Pago"""
    if current_user["user_type"] != "admin":
        raise HTTPException(status_code=403, detail="Apenas administradores")
    
    access_token = data.get("access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail="Access token obrigatório")
    
    try:
        import mercadopago
        sdk = mercadopago.SDK(access_token)
        
        # Testar se o token é válido
        # Não tem endpoint específico de teste, então vamos usar payment search
        result = sdk.payment().search()
        
        if result["status"] == 200:
            return {
                "ok": True,
                "message": "Conexão OK",
                "account_info": {
                    "email": "Conta verificada"
                }
            }
        else:
            raise HTTPException(status_code=400, detail="Token inválido")
            
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao testar: {str(e)}")
