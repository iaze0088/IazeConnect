"""
Dependências compartilhadas para evitar circular imports
"""
from fastapi import Depends, HTTPException, Header
from typing import Optional
import jwt
import os

# Variáveis globais que serão definidas pelo server.py
db = None
SECRET_KEY = None

def set_db(database):
    """Define a instância do banco de dados"""
    global db
    db = database

def set_secret_key(key):
    """Define a chave secreta para JWT"""
    global SECRET_KEY
    SECRET_KEY = key

async def get_current_user(authorization: Optional[str] = Header(None)):
    """
    Dependência para obter o usuário atual a partir do token JWT
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Token não fornecido")
    
    try:
        # Extrair token do header "Bearer <token>"
        token = authorization.replace("Bearer ", "")
        
        # Decodificar token
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("user_id")
        user_type = payload.get("user_type")
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Token inválido")
        
        # Buscar usuário no banco
        # Todos os usuários (admin, agent, client) estão na collection 'users'
        user = await db.users.find_one({"id": user_id})
        
        if not user:
            raise HTTPException(status_code=401, detail="Usuário não encontrado")
        
        # Verificar se o tipo de usuário bate (opcional, mas boa prática)
        if user_type and user.get("user_type") != user_type:
            raise HTTPException(status_code=401, detail="Tipo de usuário inválido")
        
        return user
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Erro na autenticação: {str(e)}")
