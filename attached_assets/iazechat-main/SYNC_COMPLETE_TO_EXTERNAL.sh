#!/bin/bash

# ========================================
# SINCRONIZAÇÃO COMPLETA PARA SERVIDOR EXTERNO
# Inclui: Office Sync, Auto-response, Clear Cache, Atendentes
# ========================================

EXTERNAL_SERVER="198.96.94.106"
EXTERNAL_USER="root"
EXTERNAL_PASSWORD="102030ab"
EXTERNAL_PATH="/opt/iaze"

echo "🚀 SINCRONIZAÇÃO COMPLETA PARA SERVIDOR EXTERNO"
echo "================================================"
echo ""

# Instalar sshpass
if ! command -v sshpass &> /dev/null; then
    echo "📦 Instalando sshpass..."
    apt-get update && apt-get install -y sshpass
fi

# Funções
remote_exec() {
    sshpass -p "$EXTERNAL_PASSWORD" ssh -o StrictHostKeyChecking=no "$EXTERNAL_USER@$EXTERNAL_SERVER" "$1"
}

copy_file() {
    echo "📤 $1 → $2"
    sshpass -p "$EXTERNAL_PASSWORD" scp -o StrictHostKeyChecking=no "$1" "$EXTERNAL_USER@$EXTERNAL_SERVER:$2"
    [ $? -eq 0 ] && echo "   ✅" || echo "   ❌"
}

echo "1️⃣ CRIANDO BACKUP..."
remote_exec "cp -r $EXTERNAL_PATH ${EXTERNAL_PATH}_backup_\$(date +%Y%m%d_%H%M%S)"
echo "✅ Backup criado"
echo ""

echo "2️⃣ PARANDO SERVIÇOS..."
remote_exec "supervisorctl stop all"
echo "✅ Serviços parados"
echo ""

echo "3️⃣ BACKEND - ARQUIVOS PRINCIPAIS..."
copy_file "/app/backend/server.py" "$EXTERNAL_PATH/backend/"
copy_file "/app/backend/whatsapp_routes.py" "$EXTERNAL_PATH/backend/"
copy_file "/app/backend/whatsapp_service.py" "$EXTERNAL_PATH/backend/"
copy_file "/app/backend/office_service_playwright.py" "$EXTERNAL_PATH/backend/"
copy_file "/app/backend/requirements.txt" "$EXTERNAL_PATH/backend/"
echo ""

echo "4️⃣ BACKEND - OFFICE SYNC (NOVOS)..."
copy_file "/app/backend/office_sync_service.py" "$EXTERNAL_PATH/backend/"
copy_file "/app/backend/office_sync_routes.py" "$EXTERNAL_PATH/backend/"
copy_file "/app/backend/office_sync_scheduler.py" "$EXTERNAL_PATH/backend/"
echo ""

echo "5️⃣ BACKEND - AUTO RESPONSE (NOVO)..."
copy_file "/app/backend/auto_response_service.py" "$EXTERNAL_PATH/backend/"
echo ""

echo "6️⃣ FRONTEND - PÁGINAS DE LOGIN..."
copy_file "/app/frontend/src/pages/AdminLogin.js" "$EXTERNAL_PATH/frontend/src/pages/"
copy_file "/app/frontend/src/pages/AgentLogin.js" "$EXTERNAL_PATH/frontend/src/pages/"
echo ""

echo "7️⃣ FRONTEND - OFFICE RÁPIDO..."
copy_file "/app/frontend/src/components/OfficeSearchFast.js" "$EXTERNAL_PATH/frontend/src/components/"
copy_file "/app/frontend/src/pages/AgentDashboard.js" "$EXTERNAL_PATH/frontend/src/pages/"
echo ""

echo "8️⃣ FRONTEND - CLEAR CACHE..."
copy_file "/app/frontend/public/clear-cache.html" "$EXTERNAL_PATH/frontend/public/"
copy_file "/app/frontend/public/index.html" "$EXTERNAL_PATH/frontend/public/"
echo ""

echo "9️⃣ DOCUMENTAÇÃO..."
copy_file "/app/CREDENCIAIS_LOGIN.md" "$EXTERNAL_PATH/"
copy_file "/app/OFFICE_SYNC_GUIDE.md" "$EXTERNAL_PATH/"
copy_file "/app/AUTO_RESPOSTA_GUIA_COMPLETO.md" "$EXTERNAL_PATH/"
echo ""

echo "🔟 CRIANDO ATENDENTES NO SERVIDOR EXTERNO..."
remote_exec "cd $EXTERNAL_PATH && python3 - <<'PYEOF'
import asyncio
import bcrypt
import uuid
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone

async def create_agents():
    client = AsyncIOMotorClient('mongodb://localhost:27017')
    db = client['support_chat']
    
    agents = [
        {'username': 'leticiaatt', 'password': 'ab181818ab', 'name': 'Leticia'},
        {'username': 'biancaatt', 'password': 'ab181818ab', 'name': 'Bianca'},
        {'username': 'fabioro', 'password': '102030ab', 'name': 'Fabio Oro'},
        {'username': 'andressaatt', 'password': 'ab181818ab', 'name': 'Andressa'},
        {'username': 'jessicaatt', 'password': 'ab181818ab', 'name': 'Jessica'},
    ]
    
    reseller = await db.resellers.find_one({})
    if not reseller:
        print('❌ Nenhum reseller encontrado!')
        return
    
    reseller_id = reseller.get('id') or str(reseller.get('_id'))
    
    for agent in agents:
        password_hash = bcrypt.hashpw(agent['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        agent_doc = {
            'id': str(uuid.uuid4()),
            'reseller_id': reseller_id,
            'username': agent['username'],
            'pass_hash': password_hash,
            'name': agent['name'],
            'email': f\"{agent['username']}@temp.com\",
            'user_type': 'agent',
            'department_ids': [],
            'is_active': True,
            'created_at': datetime.now(timezone.utc).isoformat(),
        }
        
        existing = await db.users.find_one({'username': agent['username']})
        if existing:
            await db.users.update_one({'username': agent['username']}, {'\$set': agent_doc})
            print(f\"✅ {agent['username']} atualizado\")
        else:
            await db.users.insert_one(agent_doc)
            print(f\"✅ {agent['username']} criado\")
    
    print('✅ TODOS OS ATENDENTES CRIADOS!')

asyncio.run(create_agents())
PYEOF
"
echo ""

echo "1️⃣1️⃣ INSTALANDO DEPENDÊNCIAS..."
remote_exec "cd $EXTERNAL_PATH/backend && pip3 install -r requirements.txt --quiet"
echo "✅ Dependências instaladas"
echo ""

echo "1️⃣2️⃣ REINICIANDO SERVIÇOS..."
remote_exec "supervisorctl start all"
sleep 5
echo ""

echo "1️⃣3️⃣ VERIFICANDO STATUS..."
remote_exec "supervisorctl status"
echo ""

echo "================================================"
echo "✅ SINCRONIZAÇÃO COMPLETA CONCLUÍDA!"
echo "================================================"
echo ""
echo "📋 TESTANDO NO SERVIDOR EXTERNO..."
echo ""
