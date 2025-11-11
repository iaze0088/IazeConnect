# ✅ CHECKLIST COMPLETO PARA DEPLOY - CYBERTV SUPORTE

## 📋 ÍNDICE
1. [Pré-Requisitos](#1-pré-requisitos)
2. [Verificação do Banco de Dados](#2-verificação-do-banco-de-dados)
3. [Verificação do Backend](#3-verificação-do-backend)
4. [Verificação do Frontend](#4-verificação-do-frontend)
5. [Testes de Funcionalidade](#5-testes-de-funcionalidade)
6. [Deploy Final](#6-deploy-final)
7. [Pós-Deploy](#7-pós-deploy)

---

## 1. PRÉ-REQUISITOS

### ✅ Backup do Banco de Dados
```bash
# Criar backup ANTES de qualquer mudança
mkdir -p /app/backups
mongodump --uri="mongodb://localhost:27017/support_chat" \
  --out="/app/backups/pre_deploy_$(date +%Y%m%d_%H%M%S)"
```

**Status:** [ ] Backup criado em: ________________

### ✅ Verificar Serviços Rodando
```bash
sudo supervisorctl status
```

**Esperado:**
- backend: RUNNING
- frontend: RUNNING  
- mongodb: RUNNING

**Status:** [ ] Todos rodando

---

## 2. VERIFICAÇÃO DO BANCO DE DADOS

### ✅ 2.1 Contar Documentos
```bash
cd /app/backend && python3 << 'EOF'
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os

async def count_docs():
    client = AsyncIOMotorClient(os.environ.get('MONGO_URL'))
    db = client[os.environ.get('DB_NAME', 'support_chat')]
    
    print("📊 CONTAGEM DE DOCUMENTOS:")
    print(f"   Resellers: {await db.resellers.count_documents({})}")
    print(f"   Agents: {await db.agents.count_documents({})}")
    print(f"   Tickets: {await db.tickets.count_documents({})}")
    print(f"   Messages: {await db.messages.count_documents({})}")
    print(f"   AI Agents: {await db.ai_agents.count_documents({})}")
    print(f"   Departments: {await db.departments.count_documents({})}")

asyncio.run(count_docs())
EOF
```

**Registrar valores:**
- Resellers: ____
- Agents: ____
- Tickets: ____
- Messages: ____

**Status:** [ ] Valores registrados

### ✅ 2.2 Verificar Índices
```bash
cd /app/backend && python3 create_indexes.py
```

**Status:** [ ] Índices criados

---

## 3. VERIFICAÇÃO DO BACKEND

### ✅ 3.1 Verificar Arquivo .env
```bash
cat /app/backend/.env
```

**Verificar se contém:**
- [ ] MONGO_URL
- [ ] DB_NAME
- [ ] JWT_SECRET
- [ ] ADMIN_PASSWORD_HASH

**Status:** [ ] Todas variáveis presentes

### ✅ 3.2 Testar Imports
```bash
cd /app/backend && python3 << 'EOF'
try:
    import server
    import tenant_helpers
    import audit_logger
    import rate_limiter
    print("✅ Todos os imports OK")
except Exception as e:
    print(f"❌ Erro: {e}")
EOF
```

**Status:** [ ] Imports OK

### ✅ 3.3 Testar Endpoints Críticos
```bash
# Testar health check
curl -s http://localhost:8001/api/health || echo "Endpoint /api/health não existe (OK)"

# Testar login admin
curl -s -X POST http://localhost:8001/api/auth/admin/login \
  -H "Content-Type: application/json" \
  -d '{"password":"102030@ab"}' | python3 -c "import sys,json; d=json.load(sys.stdin); print('✅ Login admin OK' if 'token' in d else '❌ Login falhou')"
```

**Status:** [ ] Login admin funciona

### ✅ 3.4 Testar Login de Agent
```bash
curl -s -X POST http://localhost:8001/api/auth/agent/login \
  -H "Content-Type: application/json" \
  -d '{"login":"fabioteste","password":"123"}' | python3 -c "import sys,json; d=json.load(sys.stdin); print('✅ Login agent OK' if 'token' in d else '❌ Login falhou: ' + d.get('detail',''))"
```

**Status:** [ ] Login agent funciona

### ✅ 3.5 Testar Filtro Multi-Tenant
```bash
cd /app/backend && python3 << 'EOF'
import requests

# Login
response = requests.post("http://localhost:8001/api/auth/agent/login",
    json={"login": "fabioteste", "password": "123"})

if response.status_code == 200:
    token = response.json()['token']
    
    # Buscar tickets
    tickets_response = requests.get("http://localhost:8001/api/tickets",
        headers={"Authorization": f"Bearer {token}"})
    
    if tickets_response.status_code == 200:
        tickets = tickets_response.json()
        print(f"✅ Filtro multi-tenant OK - Retornou {len(tickets)} tickets")
        
        if len(tickets) == 0:
            print("✅ PERFEITO! Agent sem tickets vê 0 tickets")
        else:
            print(f"⚠️ Agent vê {len(tickets)} tickets")
    else:
        print(f"❌ Erro ao buscar tickets")
else:
    print(f"❌ Erro no login")
EOF
```

**Status:** [ ] Filtro funcionando

---

## 4. VERIFICAÇÃO DO FRONTEND

### ✅ 4.1 Verificar .env do Frontend
```bash
cat /app/frontend/.env
```

**Verificar:**
- [ ] REACT_APP_BACKEND_URL está correto

**Status:** [ ] URL correta

### ✅ 4.2 Build do Frontend
```bash
cd /app/frontend
yarn build 2>&1 | tail -20
```

**Status:** [ ] Build sem erros

### ✅ 4.3 Verificar Service Worker
```bash
head -5 /app/frontend/public/service-worker.js
```

**Verificar:**
- [ ] CACHE_NAME está com versão atualizada
- [ ] Não faz cache de /api/

**Status:** [ ] Service worker OK

---

## 5. TESTES DE FUNCIONALIDADE

### ✅ 5.1 Teste de Login Admin
**URL:** https://wppconnect-fix.preview.emergentagent.com/admin/login
**Credenciais:** senha do .env

- [ ] Login funciona
- [ ] Dashboard carrega
- [ ] Vê todas as revendas
- [ ] Vê todos os tickets

**Status:** [ ] Admin OK

### ✅ 5.2 Teste de Login Agent
**URL:** https://wppconnect-fix.preview.emergentagent.com/atendente/login
**Credenciais:** fabioteste / 123

- [ ] Login funciona
- [ ] Dashboard carrega
- [ ] Vê apenas tickets da sua revenda
- [ ] Chat funciona

**Status:** [ ] Agent OK

### ✅ 5.3 Teste de Login Revenda
**URL:** https://wppconnect-fix.preview.emergentagent.com/revenda/login
**Credenciais:** email da revenda / senha

- [ ] Login funciona
- [ ] Dashboard carrega
- [ ] Vê apenas seus dados
- [ ] Pode criar agents

**Status:** [ ] Revenda OK

### ✅ 5.4 Teste Multi-Tenant Isolation
**Criar 2 agents de revendas diferentes e verificar:**

- [ ] Agent A NÃO vê tickets de Agent B
- [ ] Agent A NÃO vê dados de outra revenda
- [ ] Admin vê TUDO

**Status:** [ ] Isolamento OK

### ✅ 5.5 Teste de WebSocket
- [ ] Notificações funcionam
- [ ] Chat em tempo real funciona
- [ ] Som de notificação toca

**Status:** [ ] WebSocket OK

---

## 6. DEPLOY FINAL

### ✅ 6.1 Limpar Caches
```bash
# Limpar cache Python
find /app/backend -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null

# Limpar cache do frontend
rm -rf /app/frontend/node_modules/.cache
rm -rf /app/frontend/build

# Rebuild frontend
cd /app/frontend && yarn build
```

**Status:** [ ] Caches limpos e rebuild feito

### ✅ 6.2 Reiniciar Todos os Serviços
```bash
sudo supervisorctl restart all
sleep 10
sudo supervisorctl status
```

**Status:** [ ] Todos serviços rodando

### ✅ 6.3 Verificar Logs
```bash
# Ver logs de erro
tail -50 /var/log/supervisor/backend.err.log | grep -i error

# Ver logs de startup
tail -20 /var/log/supervisor/backend.out.log
```

**Status:** [ ] Sem erros críticos

---

## 7. PÓS-DEPLOY

### ✅ 7.1 Monitorar por 5 Minutos
```bash
# Em um terminal separado, monitorar logs
tail -f /var/log/supervisor/backend.out.log
```

**Verificar:**
- [ ] Sem erros aparecem
- [ ] Requisições sendo processadas
- [ ] Sem crashes

**Status:** [ ] Sistema estável

### ✅ 7.2 Teste de Carga Leve
**Fazer login com 3 usuários diferentes simultaneamente:**
- [ ] Admin
- [ ] Revenda
- [ ] Agent

**Status:** [ ] Sistema suporta múltiplos usuários

### ✅ 7.3 Verificar Performance
```bash
# Ver uso de CPU/memória
top -b -n 1 | head -20
```

**Registrar:**
- CPU: ____%
- Memória: ____%

**Status:** [ ] Performance aceitável

### ✅ 7.4 Criar Backup Pós-Deploy
```bash
mongodump --uri="mongodb://localhost:27017/support_chat" \
  --out="/app/backups/pos_deploy_$(date +%Y%m%d_%H%M%S)"
```

**Status:** [ ] Backup pós-deploy criado

---

## 8. CHECKLIST FINAL

### ✅ Sistema Funcional
- [ ] Backend rodando sem erros
- [ ] Frontend carregando
- [ ] Login de todos tipos funciona
- [ ] Multi-tenant isolamento funcionando
- [ ] WebSocket funcionando
- [ ] Sem agents sendo deletados
- [ ] Sem revendas sendo deletadas

### ✅ Performance
- [ ] Queries rápidas (< 500ms)
- [ ] CPU < 80%
- [ ] Memória < 80%
- [ ] Sem memory leaks

### ✅ Segurança
- [ ] JWT funcionando
- [ ] Senhas hasheadas
- [ ] Filtro multi-tenant ativo
- [ ] Sem vazamento de dados

### ✅ Documentação
- [ ] README atualizado
- [ ] API docs disponível
- [ ] Melhorias documentadas
- [ ] Backup criado

---

## 9. TROUBLESHOOTING

### Se algo der errado:

#### Backend não inicia
```bash
# Ver erro completo
cat /var/log/supervisor/backend.err.log

# Verificar sintaxe Python
cd /app/backend && python3 -m py_compile server.py
```

#### Frontend não carrega
```bash
# Rebuild
cd /app/frontend && yarn build

# Ver logs
tail -50 /var/log/supervisor/frontend.err.log
```

#### Agents sendo deletados
```bash
# Ver quem está chamando DELETE
tail -100 /var/log/supervisor/backend.out.log | grep DELETE

# Desativar endpoints de teste
# Comentar /api/test-system em server.py
```

#### Banco corrompido
```bash
# Restaurar do backup
mongorestore --uri="mongodb://localhost:27017" \
  --drop \
  /app/backups/backup_XXXXXXXX_XXXXXX/support_chat
```

---

## 10. CONTATOS DE EMERGÊNCIA

- **Suporte Emergent:** [inserir contato]
- **DBA:** [inserir contato]
- **DevOps:** [inserir contato]

---

## 📝 NOTAS DO DEPLOY

**Data:** ________________  
**Realizado por:** ________________  
**Versão:** 2.0.0  
**Duração:** ________________  

**Problemas encontrados:**
- 
- 
- 

**Ações corretivas:**
- 
- 
- 

**Status final:** [ ] SUCESSO  [ ] PARCIAL  [ ] FALHA

---

**Assinatura:** ________________  
**Data/Hora:** ________________
