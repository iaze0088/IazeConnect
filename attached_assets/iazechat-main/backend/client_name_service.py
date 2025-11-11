"""
Serviço para buscar e atualizar nomes de clientes automaticamente
Busca no gestor.my pelo telefone e atualiza o nome no banco
"""
import logging
from typing import Optional, Dict

logger = logging.getLogger(__name__)


async def fetch_client_name_from_office(phone: str, office_credentials: list, office_service) -> Optional[str]:
    """
    Busca o nome do cliente no gestor.my pelo telefone
    
    Args:
        phone: Número de telefone do cliente
        office_credentials: Lista de credenciais do Office
        office_service: Serviço do Office (Playwright)
        
    Returns:
        Nome do cliente ou None se não encontrado
    """
    try:
        logger.info(f"🔍 Buscando nome do cliente para telefone: {phone}")
        
        if not office_credentials:
            logger.warning("⚠️ Nenhuma credencial Office cadastrada")
            return None
        
        # Usar primeira credencial ativa
        credential = office_credentials[0]
        
        # Preparar credenciais no formato esperado
        creds_dict = {
            "username": credential["username"],
            "password": credential["password"]
        }
        
        # Fazer login e buscar cliente
        result = await office_service.buscar_cliente(creds_dict, phone)
        
        if result.get("success") and result.get("cliente"):
            cliente = result["cliente"]
            nome = cliente.get("nome") or cliente.get("name") or cliente.get("username")
            
            if nome:
                logger.info(f"✅ Nome encontrado: {nome}")
                return nome
            else:
                logger.warning(f"⚠️ Cliente encontrado mas sem nome: {phone}")
                return None
        else:
            logger.warning(f"⚠️ Cliente não encontrado no Office: {phone}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Erro ao buscar nome do cliente: {e}")
        import traceback
        traceback.print_exc()
        return None


async def update_client_name(db, client_id: str, name: str, collection_name: str = "users"):
    """
    Atualiza o nome do cliente no banco de dados
    
    Args:
        db: Database connection
        client_id: ID do cliente
        name: Nome a ser salvo
        collection_name: Nome da coleção (users ou clients)
    """
    try:
        if collection_name == "users":
            await db.users.update_one(
                {"id": client_id},
                {"$set": {"display_name": name}}
            )
        else:  # clients
            await db.clients.update_one(
                {"id": client_id},
                {"$set": {"name": name}}
            )
        
        logger.info(f"✅ Nome atualizado no banco: {name} (collection: {collection_name})")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro ao atualizar nome no banco: {e}")
        return False


async def auto_fetch_and_save_client_name(db, client_id: str, phone: str, collection_name: str = "users"):
    """
    Busca automaticamente o nome do cliente no Office e salva no banco
    
    Args:
        db: Database connection
        client_id: ID do cliente
        phone: Telefone do cliente
        collection_name: Nome da coleção (users ou clients)
        
    Returns:
        Nome encontrado ou None
    """
    try:
        # Buscar credenciais Office
        office_credentials = await db.office_credentials.find(
            {"active": True}
        ).to_list(length=None)
        
        if not office_credentials:
            logger.warning("⚠️ Nenhuma credencial Office para buscar nome")
            return None
        
        # Importar serviço do Office
        from office_service_playwright import office_service_playwright
        
        # Buscar nome
        nome = await fetch_client_name_from_office(phone, office_credentials, office_service_playwright)
        
        if nome:
            # Salvar no banco
            await update_client_name(db, client_id, nome, collection_name)
            return nome
        
        return None
        
    except Exception as e:
        logger.error(f"❌ Erro ao buscar e salvar nome do cliente: {e}")
        import traceback
        traceback.print_exc()
        return None
