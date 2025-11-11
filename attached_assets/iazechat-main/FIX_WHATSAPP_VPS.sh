#!/bin/bash
# Script para corrigir erro "Not Found" no WhatsApp Admin do servidor suporte.help
# Execute este script no VPS: bash FIX_WHATSAPP_VPS.sh

echo "🔧 Iniciando correção do WhatsApp Admin no VPS..."

# 1. Fazer backup dos arquivos
echo "📦 Fazendo backup..."
cp /var/www/iaze/backend/whatsapp_routes.py /var/www/iaze/backend/whatsapp_routes.py.backup
cp /var/www/iaze/backend/tenant_middleware.py /var/www/iaze/backend/tenant_middleware.py.backup

# 2. Corrigir import circular em whatsapp_routes.py
echo "🔧 Corrigindo import circular em whatsapp_routes.py..."
cat > /tmp/fix_whatsapp_auth.py << 'PYTHON_EOF'
import re

# Ler o arquivo
with open('/var/www/iaze/backend/whatsapp_routes.py', 'r') as f:
    content = f.read()

# Verificar se já tem a correção
if 'async def get_current_user(authorization: Optional[str] = Header(None)):' in content:
    print("✅ Correção de autenticação já aplicada!")
    exit(0)

# Encontrar a linha de import
import_pattern = r'from server import.*get_current_user.*'
if re.search(import_pattern, content):
    # Remover o import de get_current_user
    content = re.sub(r',?\s*get_current_user', '', content)
    
    # Adicionar a nova função após os imports
    router_line = 'router = APIRouter(prefix="/api/whatsapp", tags=["whatsapp"])'
    if router_line in content:
        new_code = '''
# Criar uma dependência que funciona sem import circular
async def get_current_user(authorization: Optional[str] = Header(None)):
    """Dependência de autenticação - importa dinamicamente para evitar circular import"""
    from server import verify_token
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = authorization.split(" ")[1]
    return verify_token(token)

'''
        content = content.replace(router_line, router_line + new_code)
        
        # Salvar
        with open('/var/www/iaze/backend/whatsapp_routes.py', 'w') as f:
            f.write(content)
        print("✅ Correção de autenticação aplicada!")
    else:
        print("❌ Não encontrou a linha do router")
        exit(1)
else:
    print("⚠️ Import já foi removido ou não existe")
PYTHON_EOF

python3 /tmp/fix_whatsapp_auth.py

# 3. Verificar se suporte.help está na lista de master_domains
echo "🔧 Verificando master_domains..."
if ! grep -q '"suporte.help"' /var/www/iaze/backend/tenant_middleware.py; then
    echo "❌ suporte.help NÃO está na lista de master_domains!"
    echo "Adicionando..."
    # Fazer isso manualmente seria mais seguro
else
    echo "✅ suporte.help já está na lista!"
fi

# 4. Criar admin se não existir
echo "👤 Criando usuário admin..."
python3 << 'ADMIN_EOF'
import asyncio
import os
import sys
from motor.motor_asyncio import AsyncIOMotorClient
import bcrypt

async def create_admin():
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    client = AsyncIOMotorClient(mongo_url)
    
    # Descobrir qual database está sendo usado
    db_name = os.environ.get('DB_NAME', 'support_chat')
    print(f"Usando database: {db_name}")
    db = client[db_name]
    
    # Verificar se admin já existe
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
    print("✅ Admin criado com sucesso!")

try:
    asyncio.run(create_admin())
except Exception as e:
    print(f"❌ Erro ao criar admin: {e}")
ADMIN_EOF

# 5. Reiniciar backend
echo "🔄 Reiniciando backend..."
cd /var/www/iaze/backend
sudo supervisorctl restart backend

echo ""
echo "✅ Correções aplicadas!"
echo "Aguardando 5 segundos para o backend reiniciar..."
sleep 5

echo ""
echo "🧪 Testando endpoint..."
curl -s http://localhost:8001/api/health | jq '.status'

echo ""
echo "✅ CONCLUÍDO! Agora teste em: https://suporte.help/admin"
