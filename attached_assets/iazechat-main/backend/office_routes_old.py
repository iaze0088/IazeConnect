"""
Rotas para gerenciamento de Office (gestor.my)
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import Optional, List
import uuid
from datetime import datetime, timezone
from office_service import office_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Dependency para obter db
async def get_db(request: Request):
    return request.app.state.db

# Modelos
class OfficeCredentials(BaseModel):
    url: str
    username: str
    password: str
    nome: Optional[str] = None  # Nome/descrição das credenciais

class SearchRequest(BaseModel):
    search_term: str  # Usuário ou WhatsApp
    credential_id: Optional[str] = None  # ID da credencial específica (opcional)

class RenovarRequest(BaseModel):
    usuario: str
    dias: int = 30
    credential_id: str

# Rota para cadastrar credenciais do Office
@router.post("/office/credentials")
async def add_office_credentials(
    credentials: OfficeCredentials,
    db=Depends(get_db)
):
    """
    Cadastra novas credenciais do Office
    """
    try:
        # TODO: Adicionar autenticação - apenas admin/revenda pode cadastrar
        
        credential_id = str(uuid.uuid4())
        
        credential_doc = {
            "id": credential_id,
            "url": credentials.url,
            "username": credentials.username,
            "password": credentials.password,
            "nome": credentials.nome or f"Office {credentials.username}",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "active": True
        }
        
        await db.office_credentials.insert_one(credential_doc)
        
        logger.info(f"✅ Credenciais do Office cadastradas: {credential_id}")
        
        return {
            "success": True,
            "credential_id": credential_id,
            "message": "Credenciais cadastradas com sucesso"
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao cadastrar credenciais: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Rota para listar credenciais
@router.get("/office/credentials")
async def list_office_credentials(db=Depends(get_db)):
    """
    Lista todas as credenciais do Office cadastradas
    """
    try:
        credentials = await db.office_credentials.find(
            {"active": True}
        ).to_list(length=None)
        
        # Remover senhas da resposta
        for cred in credentials:
            cred.pop("password", None)
            cred.pop("_id", None)
        
        return {
            "success": True,
            "credentials": credentials
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao listar credenciais: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Rota para deletar credenciais
@router.delete("/office/credentials/{credential_id}")
async def delete_office_credentials(credential_id: str, db=Depends(get_db)):
    """
    Deleta (desativa) credenciais do Office
    """
    try:
        result = await db.office_credentials.update_one(
            {"id": credential_id},
            {"$set": {"active": False}}
        )
        
        if result.modified_count > 0:
            return {
                "success": True,
                "message": "Credenciais removidas com sucesso"
            }
        else:
            raise HTTPException(status_code=404, detail="Credenciais não encontradas")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao deletar credenciais: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Rota para buscar cliente no Office
@router.post("/office/search")
async def search_office_client(
    request: SearchRequest,
    db=Depends(get_db)
):
    """
    Busca dados de um cliente no Office
    """
    try:
        logger.info(f"🔍 Buscando cliente no Office: {request.search_term}")
        
        # Se não especificou credential_id, tentar com todas
        if not request.credential_id:
            credentials_list = await db.office_credentials.find(
                {"active": True}
            ).to_list(length=None)
            
            if not credentials_list:
                raise HTTPException(
                    status_code=400,
                    detail="Nenhuma credencial do Office cadastrada"
                )
            
            # Tentar com cada credencial até encontrar
            for cred in credentials_list:
                result = await office_service.buscar_cliente(
                    {
                        "username": cred["username"],
                        "password": cred["password"]
                    },
                    request.search_term
                )
                
                if result and result.get("success"):
                    # Adicionar informação de qual credencial foi usada
                    result["credential_used"] = {
                        "id": cred["id"],
                        "nome": cred.get("nome", ""),
                        "username": cred["username"]
                    }
                    
                    # Salvar histórico de consulta
                    await db.office_searches.insert_one({
                        "id": str(uuid.uuid4()),
                        "search_term": request.search_term,
                        "credential_id": cred["id"],
                        "result": result,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
                    
                    return result
            
            # Não encontrou em nenhuma credencial
            return {
                "success": False,
                "error": "Cliente não encontrado em nenhum Office cadastrado",
                "search_term": request.search_term
            }
            
        else:
            # Buscar com credencial específica
            cred = await db.office_credentials.find_one({
                "id": request.credential_id,
                "active": True
            })
            
            if not cred:
                raise HTTPException(status_code=404, detail="Credencial não encontrada")
            
            result = await office_service.buscar_cliente(
                {
                    "username": cred["username"],
                    "password": cred["password"]
                },
                request.search_term
            )
            
            # Salvar histórico
            await db.office_searches.insert_one({
                "id": str(uuid.uuid4()),
                "search_term": request.search_term,
                "credential_id": cred["id"],
                "result": result,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            return result
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao buscar cliente no Office: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Rota para renovar cliente
@router.post("/office/renovar")
async def renovar_office_client(
    request: RenovarRequest,
    db=Depends(get_db)
):
    """
    Renova a conta de um cliente no Office
    """
    try:
        logger.info(f"🔄 Renovando cliente: {request.usuario}")
        
        # Buscar credencial
        cred = await db.office_credentials.find_one({
            "id": request.credential_id,
            "active": True
        })
        
        if not cred:
            raise HTTPException(status_code=404, detail="Credencial não encontrada")
        
        # Renovar
        result = await office_service.renovar_cliente(
            {
                "username": cred["username"],
                "password": cred["password"]
            },
            request.usuario,
            request.dias
        )
        
        # Salvar log de renovação
        if result.get("success"):
            await db.office_renovacoes.insert_one({
                "id": str(uuid.uuid4()),
                "usuario": request.usuario,
                "dias": request.dias,
                "credential_id": request.credential_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao renovar cliente: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Rota para histórico de consultas
@router.get("/office/history")
async def get_office_history(db=Depends(get_db), limit: int = 50):
    """
    Retorna histórico de consultas no Office
    """
    try:
        history = await db.office_searches.find().sort(
            "timestamp", -1
        ).limit(limit).to_list(length=limit)
        
        for item in history:
            item.pop("_id", None)
        
        return {
            "success": True,
            "history": history
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao buscar histórico: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    """
    Cadastra novas credenciais do Office
    """
    try:
        # TODO: Adicionar autenticação - apenas admin/revenda pode cadastrar
        
        credential_id = str(uuid.uuid4())
        
        credential_doc = {
            "id": credential_id,
            "url": credentials.url,
            "username": credentials.username,
            "password": credentials.password,
            "nome": credentials.nome or f"Office {credentials.username}",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "active": True
        }
        
        await db.office_credentials.insert_one(credential_doc)
        
        logger.info(f"✅ Credenciais do Office cadastradas: {credential_id}")
        
        return {
            "success": True,
            "credential_id": credential_id,
            "message": "Credenciais cadastradas com sucesso"
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao cadastrar credenciais: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Rota para listar credenciais
@router.get("/office/credentials")
async def list_office_credentials(db=Depends(lambda: None)):
    """
    Lista todas as credenciais do Office cadastradas
    """
    try:
        credentials = await db.office_credentials.find(
            {"active": True}
        ).to_list(length=None)
        
        # Remover senhas da resposta
        for cred in credentials:
            cred.pop("password", None)
            cred.pop("_id", None)
        
        return {
            "success": True,
            "credentials": credentials
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao listar credenciais: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Rota para deletar credenciais
@router.delete("/office/credentials/{credential_id}")
async def delete_office_credentials(credential_id: str, db=Depends(lambda: None)):
    """
    Deleta (desativa) credenciais do Office
    """
    try:
        result = await db.office_credentials.update_one(
            {"id": credential_id},
            {"$set": {"active": False}}
        )
        
        if result.modified_count > 0:
            return {
                "success": True,
                "message": "Credenciais removidas com sucesso"
            }
        else:
            raise HTTPException(status_code=404, detail="Credenciais não encontradas")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao deletar credenciais: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Rota para buscar cliente no Office
@router.post("/office/search")
async def search_office_client(
    request: SearchRequest,
    db=Depends(lambda: None)
):
    """
    Busca dados de um cliente no Office
    """
    try:
        logger.info(f"🔍 Buscando cliente no Office: {request.search_term}")
        
        # Se não especificou credential_id, tentar com todas
        if not request.credential_id:
            credentials_list = await db.office_credentials.find(
                {"active": True}
            ).to_list(length=None)
            
            if not credentials_list:
                raise HTTPException(
                    status_code=400,
                    detail="Nenhuma credencial do Office cadastrada"
                )
            
            # Tentar com cada credencial até encontrar
            for cred in credentials_list:
                result = await office_service.buscar_cliente(
                    {
                        "username": cred["username"],
                        "password": cred["password"]
                    },
                    request.search_term
                )
                
                if result and result.get("success"):
                    # Adicionar informação de qual credencial foi usada
                    result["credential_used"] = {
                        "id": cred["id"],
                        "nome": cred.get("nome", ""),
                        "username": cred["username"]
                    }
                    
                    # Salvar histórico de consulta
                    await db.office_searches.insert_one({
                        "id": str(uuid.uuid4()),
                        "search_term": request.search_term,
                        "credential_id": cred["id"],
                        "result": result,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
                    
                    return result
            
            # Não encontrou em nenhuma credencial
            return {
                "success": False,
                "error": "Cliente não encontrado em nenhum Office cadastrado",
                "search_term": request.search_term
            }
            
        else:
            # Buscar com credencial específica
            cred = await db.office_credentials.find_one({
                "id": request.credential_id,
                "active": True
            })
            
            if not cred:
                raise HTTPException(status_code=404, detail="Credencial não encontrada")
            
            result = await office_service.buscar_cliente(
                {
                    "username": cred["username"],
                    "password": cred["password"]
                },
                request.search_term
            )
            
            # Salvar histórico
            await db.office_searches.insert_one({
                "id": str(uuid.uuid4()),
                "search_term": request.search_term,
                "credential_id": cred["id"],
                "result": result,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            return result
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao buscar cliente no Office: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Rota para renovar cliente
@router.post("/office/renovar")
async def renovar_office_client(
    request: RenovarRequest,
    db=Depends(lambda: None)
):
    """
    Renova a conta de um cliente no Office
    """
    try:
        logger.info(f"🔄 Renovando cliente: {request.usuario}")
        
        # Buscar credencial
        cred = await db.office_credentials.find_one({
            "id": request.credential_id,
            "active": True
        })
        
        if not cred:
            raise HTTPException(status_code=404, detail="Credencial não encontrada")
        
        # Renovar
        result = await office_service.renovar_cliente(
            {
                "username": cred["username"],
                "password": cred["password"]
            },
            request.usuario,
            request.dias
        )
        
        # Salvar log de renovação
        if result.get("success"):
            await db.office_renovacoes.insert_one({
                "id": str(uuid.uuid4()),
                "usuario": request.usuario,
                "dias": request.dias,
                "credential_id": request.credential_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao renovar cliente: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Rota para histórico de consultas
@router.get("/office/history")
async def get_office_history(db=Depends(lambda: None), limit: int = 50):
    """
    Retorna histórico de consultas no Office
    """
    try:
        history = await db.office_searches.find().sort(
            "timestamp", -1
        ).limit(limit).to_list(length=limit)
        
        for item in history:
            item.pop("_id", None)
        
        return {
            "success": True,
            "history": history
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao buscar histórico: {e}")
        raise HTTPException(status_code=500, detail=str(e))
