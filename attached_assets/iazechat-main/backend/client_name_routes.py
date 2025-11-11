"""
Rotas para gerenciar nomes de clientes
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Optional
import logging

from client_name_service import auto_fetch_and_save_client_name

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/client-names", tags=["client-names"])


def get_db():
    """Dependency para obter database"""
    from server import db
    return db


@router.post("/update-all")
async def update_all_client_names(
    background_tasks: BackgroundTasks,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Atualizar nomes de TODOS os clientes sem nome
    Busca no Office pelo telefone e salva no banco
    
    Executa em background para não bloquear
    """
    try:
        # Buscar clientes sem nome na coleção users
        users_without_name = await db.users.find({
            "$or": [
                {"display_name": ""},
                {"display_name": {"$exists": False}}
            ],
            "whatsapp": {"$exists": True, "$ne": ""}
        }).to_list(length=None)
        
        # Buscar clientes sem nome na coleção clients
        clients_without_name = await db.clients.find({
            "$or": [
                {"name": ""},
                {"name": {"$exists": False}}
            ],
            "phone": {"$exists": True, "$ne": ""}
        }).to_list(length=None)
        
        total_users = len(users_without_name)
        total_clients = len(clients_without_name)
        total = total_users + total_clients
        
        logger.info(f"📊 Encontrados {total} clientes sem nome ({total_users} users, {total_clients} clients)")
        
        if total == 0:
            return {
                "success": True,
                "message": "Todos os clientes já têm nome!",
                "updated": 0,
                "total": 0
            }
        
        # Executar atualização em background
        background_tasks.add_task(
            process_clients_update,
            db,
            users_without_name,
            clients_without_name
        )
        
        return {
            "success": True,
            "message": f"Atualização iniciada em background para {total} clientes",
            "total_users": total_users,
            "total_clients": total_clients,
            "total": total
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao iniciar atualização de nomes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update-single/{client_id}")
async def update_single_client_name(
    client_id: str,
    collection: Optional[str] = "users",
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Atualizar nome de um único cliente
    """
    try:
        # Buscar cliente
        if collection == "users":
            client = await db.users.find_one({"id": client_id})
            phone_field = "whatsapp"
        else:
            client = await db.clients.find_one({"id": client_id})
            phone_field = "phone"
        
        if not client:
            raise HTTPException(status_code=404, detail="Cliente não encontrado")
        
        phone = client.get(phone_field)
        if not phone:
            raise HTTPException(status_code=400, detail="Cliente sem telefone cadastrado")
        
        # Buscar e salvar nome
        nome = await auto_fetch_and_save_client_name(db, client_id, phone, collection)
        
        if nome:
            return {
                "success": True,
                "message": f"Nome atualizado: {nome}",
                "name": nome
            }
        else:
            return {
                "success": False,
                "message": "Nome não encontrado no Office",
                "name": None
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao atualizar nome do cliente: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_names_status(db: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Verificar quantos clientes estão sem nome
    """
    try:
        # Users
        total_users = await db.users.count_documents({})
        users_without_name = await db.users.count_documents({
            "$or": [
                {"display_name": ""},
                {"display_name": {"$exists": False}}
            ]
        })
        users_with_name = total_users - users_without_name
        
        # Clients
        total_clients = await db.clients.count_documents({})
        clients_without_name = await db.clients.count_documents({
            "$or": [
                {"name": ""},
                {"name": {"$exists": False}}
            ]
        })
        clients_with_name = total_clients - clients_without_name
        
        return {
            "users": {
                "total": total_users,
                "with_name": users_with_name,
                "without_name": users_without_name,
                "percentage_complete": round((users_with_name / total_users * 100) if total_users > 0 else 0, 2)
            },
            "clients": {
                "total": total_clients,
                "with_name": clients_with_name,
                "without_name": clients_without_name,
                "percentage_complete": round((clients_with_name / total_clients * 100) if total_clients > 0 else 0, 2)
            },
            "total": {
                "all_clients": total_users + total_clients,
                "with_name": users_with_name + clients_with_name,
                "without_name": users_without_name + clients_without_name
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao verificar status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def process_clients_update(db, users_list, clients_list):
    """
    Processa atualização de clientes em background
    """
    logger.info(f"🚀 Iniciando atualização em background de {len(users_list) + len(clients_list)} clientes")
    
    updated_count = 0
    failed_count = 0
    
    # Processar users
    for user in users_list:
        try:
            phone = user.get("whatsapp")
            if phone:
                nome = await auto_fetch_and_save_client_name(db, user["id"], phone, "users")
                if nome:
                    updated_count += 1
                else:
                    failed_count += 1
        except Exception as e:
            logger.error(f"❌ Erro ao processar user {user.get('id')}: {e}")
            failed_count += 1
    
    # Processar clients
    for client in clients_list:
        try:
            phone = client.get("phone")
            if phone:
                nome = await auto_fetch_and_save_client_name(db, client["id"], phone, "clients")
                if nome:
                    updated_count += 1
                else:
                    failed_count += 1
        except Exception as e:
            logger.error(f"❌ Erro ao processar client {client.get('id')}: {e}")
            failed_count += 1
    
    logger.info(f"✅ Atualização concluída: {updated_count} atualizados, {failed_count} falharam")
