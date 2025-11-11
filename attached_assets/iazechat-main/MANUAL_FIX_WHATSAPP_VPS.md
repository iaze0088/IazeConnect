# 🔧 Correção Manual do WhatsApp Admin no VPS suporte.help

## Problema
Erro "❌ Not Found" ao clicar em "Adicionar Conexão" na aba WhatsApp do Admin.

## Causa
Import circular entre `whatsapp_routes.py` e `server.py` no servidor de produção.

---

## 🛠️ CORREÇÃO PASSO A PASSO

### 1. Conectar ao VPS via SSH

```bash
ssh root@151.243.218.223
```

### 2. Fazer Backup

```bash
cd /var/www/iaze/backend
cp whatsapp_routes.py whatsapp_routes.py.backup
cp tenant_middleware.py tenant_middleware.py.backup
```

### 3. Editar whatsapp_routes.py

```bash
nano /var/www/iaze/backend/whatsapp_routes.py
```

**Encontre a linha (por volta da linha 17):**
```python
from server import get_current_user, db
```

**REMOVA** `get_current_user` dessa linha, deixando apenas:
```python
from server import db
```

**Logo APÓS a linha:**
```python
router = APIRouter(prefix="/api/whatsapp", tags=["whatsapp"])
```

**ADICIONE este código:**
```python
# Criar uma dependência que funciona sem import circular
async def get_current_user(authorization: Optional[str] = Header(None)):
    """Dependência de autenticação - importa dinamicamente para evitar circular import"""
    from server import verify_token
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = authorization.split(" ")[1]
    return verify_token(token)
```

**Certifique-se de que `Optional` está importado no topo do arquivo:**
```python
from typing import List, Optional
```

Salve com `Ctrl+O`, Enter, `Ctrl+X`

### 4. Criar Admin (se não existir)

```bash
cd /var/www/iaze/backend
python3 << 'EOF'
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
import bcrypt

async def create_admin():
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    client = AsyncIOMotorClient(mongo_url)
    db_name = os.environ.get('DB_NAME', 'support_chat')
    db = client[db_name]
    
    # Verificar se já existe
    existing = await db.users.find_one({"email": "admin@admin.com", "user_type": "admin"})
    if existing:
        print("✅ Admin já existe")
        return
    
    # Criar admin
    password = "102030@ab"
    pass_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    admin = {
        "id": "01",
        "email": "admin@admin.com",
        "pass_hash": pass_hash,
        "user_type": "admin",
        "reseller_id": None,
        "name": "Admin Master"
    }
    
    await db.users.insert_one(admin)
    print("✅ Admin criado!")

asyncio.run(create_admin())
EOF
```

### 5. Reiniciar Backend

```bash
sudo supervisorctl restart backend
```

### 6. Aguardar e Testar

```bash
sleep 5
curl -s http://localhost:8001/api/health | jq '.status'
```

Se retornar `"healthy"`, está OK!

### 7. Testar Login

```bash
curl -s -X POST https://suporte.help/api/auth/admin/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@admin.com","password":"102030@ab"}' | jq '.token'
```

Se retornar um token JWT, está funcionando!

---

## 🧪 TESTE FINAL

1. Acesse: https://suporte.help/admin
2. Login: `admin@admin.com` / Senha: `102030@ab`
3. Clique na aba "WhatsApp"
4. Clique em "Adicionar Conexão"
5. Não deve mais aparecer "❌ Not Found"!

---

## ❌ Se ainda não funcionar

Verifique os logs:
```bash
tail -n 100 /var/log/supervisor/backend.err.log
```

Procure por erros de import ou "Not Found".

---

## 📝 Arquivos Modificados

- `/var/www/iaze/backend/whatsapp_routes.py` - Correção do import circular
- Database `support_chat.users` - Admin criado

---

## 🔙 Reverter (se necessário)

```bash
cd /var/www/iaze/backend
cp whatsapp_routes.py.backup whatsapp_routes.py
sudo supervisorctl restart backend
```
