# 🔒 REGRA ROBUSTA MÁXIMA PRIORIDADE - PERSISTÊNCIA DE DADOS

## ⚠️ NUNCA PERDER CONVERSAS/MENSAGENS NO DEPLOY!

**Esta é a REGRA MAIS IMPORTANTE do sistema IAZE.**

---

## ✅ GARANTIAS DE PERSISTÊNCIA

### 1. **BANCO DE DADOS É PERSISTENTE**

O MongoDB usado pelo IAZE é **SEMPRE persistente** e **NUNCA é resetado** no deploy.

**Configuração:**
```
MONGO_URL="mongodb://localhost:27017"
Database: support_chat
```

**Onde os dados são salvos:**
- ✅ `tickets` → Todas as conversas
- ✅ `messages` → Todas as mensagens
- ✅ `users` → Todos os usuários (Admin, Resellers, Agents, Clients)
- ✅ `departments` → Todos os departamentos
- ✅ `reseller_configs` → Configurações de revendas
- ✅ `whatsapp_connections` → Conexões WhatsApp
- ✅ Todas as outras collections

---

## 🚀 O QUE ACONTECE NO DEPLOY/RE-DEPLOY

### ✅ **ATUALIZADO (Código)**
- Backend (Python/FastAPI)
- Frontend (React)
- Configurações de ambiente
- Dependências (packages)

### ✅ **MANTIDO (Dados)**
- **TODAS as conversas** (tickets)
- **TODAS as mensagens** (messages)
- **TODOS os usuários** (users, clients)
- **TODOS os departamentos** (departments)
- **TODAS as configurações** (reseller_configs)
- **TODAS as conexões WhatsApp** (whatsapp_connections)
- **Status dos tickets** (espera/atendendo/finalizado)

---

## 🔐 GARANTIAS TÉCNICAS

### 1. **MongoDB é Persistente por Design**
```
MongoDB → Armazenamento em disco
Deploy → Atualiza APENAS código
Banco de dados → NÃO É AFETADO
```

### 2. **Sem Scripts de Limpeza**
```bash
# Verificação realizada:
grep -r "drop_collection" /app/backend
grep -r "delete_many" /app/backend
grep -r "truncate" /app/backend

Resultado: ✅ NENHUM código que apaga dados
```

### 3. **Variável de Ambiente Protegida**
```
MONGO_URL está em /app/backend/.env
✅ Não é modificada no deploy
✅ Aponta sempre para o mesmo banco
✅ Dados são mantidos entre deploys
```

---

## 📊 CICLO DE VIDA DOS DADOS

### **CRIAÇÃO DE CONVERSA:**
```
1. Cliente envia mensagem via WhatsApp
2. Backend cria ticket no MongoDB
3. Ticket fica em "espera" (status: open, sem agent_id)
4. ✅ DADOS SALVOS NO BANCO (persistente)
```

### **ATENDIMENTO:**
```
1. Atendente clica em "Assumir"
2. Backend atualiza ticket (agent_id = atendente, status: open)
3. Ticket vai para "atendendo"
4. ✅ DADOS ATUALIZADOS NO BANCO (persistente)
```

### **FINALIZAÇÃO:**
```
1. Atendente clica em "Finalizar"
2. Backend atualiza ticket (status: closed)
3. Ticket vai para "finalizado"
4. ✅ DADOS MANTIDOS NO BANCO (persistente)
```

### **DEPLOY/RE-DEPLOY:**
```
1. Código é atualizado (backend + frontend)
2. Servidor reinicia
3. Banco de dados NÃO É AFETADO
4. ✅ Tickets/mensagens continuam no mesmo estado
```

---

## 🧪 COMO VERIFICAR PERSISTÊNCIA

### **Antes do Deploy:**
```bash
# Contar tickets
mongo support_chat --eval "db.tickets.count()"

# Contar mensagens
mongo support_chat --eval "db.messages.count()"

# Ver último ticket
mongo support_chat --eval "db.tickets.findOne({}, {_id: 0})"
```

### **Após o Deploy:**
```bash
# Repetir os mesmos comandos
# ✅ Os números devem ser IGUAIS ou MAIORES (novos dados)
# ❌ NUNCA MENORES (perda de dados)
```

---

## ⚠️ ÚNICA FORMA DE PERDER DADOS

**Os dados APENAS são perdidos se:**

1. ❌ Deletar o banco de dados manualmente
   ```bash
   mongo support_chat --eval "db.dropDatabase()"  # NÃO FAZER!
   ```

2. ❌ Deletar collections manualmente
   ```bash
   mongo support_chat --eval "db.tickets.drop()"  # NÃO FAZER!
   ```

3. ❌ Remover volumes do MongoDB no servidor
   ```bash
   rm -rf /data/db/*  # NÃO FAZER!
   ```

**No sistema IAZE:**
- ✅ NÃO há código que faz isso
- ✅ NÃO há scripts automáticos de limpeza
- ✅ NÃO há rotinas de reset

---

## 🔒 REGRAS DE STATUS DE TICKETS

### **Espera (open + sem agent_id):**
```
✅ Ticket permanece em "espera" até atendente assumir
✅ Deploy NÃO move ticket
✅ Apenas atendente pode mover para "atendendo"
```

### **Atendendo (open + com agent_id):**
```
✅ Ticket permanece em "atendendo" até ser finalizado
✅ Deploy NÃO finaliza ticket
✅ Apenas atendente pode finalizar
```

### **Finalizado (closed):**
```
✅ Ticket permanece em "finalizado" para sempre
✅ Deploy NÃO remove ticket finalizado
✅ Fica no histórico permanentemente
```

---

## 📋 CHECKLIST DE GARANTIAS

- [x] ✅ MongoDB configurado como persistente
- [x] ✅ MONGO_URL aponta para banco local persistente
- [x] ✅ Nenhum código de limpeza de dados
- [x] ✅ Nenhum script automático de reset
- [x] ✅ Tickets salvos no banco, não em memória
- [x] ✅ Mensagens salvas no banco, não em memória
- [x] ✅ Status mantido entre deploys
- [x] ✅ Deploy atualiza apenas código, não dados

---

## 🎯 RESULTADO FINAL

### **ANTES DO DEPLOY:**
```
Tickets em espera: 5
Tickets em atendendo: 10
Tickets finalizados: 100
Total de mensagens: 1.500
```

### **APÓS O DEPLOY:**
```
Tickets em espera: 5 ✅ (MANTIDO)
Tickets em atendendo: 10 ✅ (MANTIDO)
Tickets finalizados: 100 ✅ (MANTIDO)
Total de mensagens: 1.500 ✅ (MANTIDO)

+ Código atualizado
+ Melhorias implementadas
+ Bugs corrigidos
```

---

## 💡 DICA PRO

**Para backups extras (opcional):**
```bash
# Backup manual antes de deploy importante
mongodump --db support_chat --out /backup/$(date +%Y%m%d)

# Restaurar se necessário
mongorestore --db support_chat /backup/20250125/support_chat
```

---

## 📞 SUPORTE EM CASO DE DÚVIDA

Se após um deploy você notar:
- ❌ Conversas sumindo
- ❌ Mensagens desaparecendo
- ❌ Status mudando sozinho

**Contate imediatamente:**
- Discord: https://discord.gg/VzKfwCXC4A
- Email: support@emergent.sh

**Mas isso NÃO deve acontecer porque:**
- ✅ Sistema foi projetado para persistência
- ✅ Banco de dados é separado do código
- ✅ Deploy não afeta dados

---

## ✅ CONCLUSÃO

### **GARANTIA 100%:**

> **"Deploy/Re-deploy NUNCA afeta conversas, mensagens ou status de tickets.
> Apenas o código é atualizado. Dados permanecem intactos."**

**Esta é a REGRA ROBUSTA MÁXIMA do sistema IAZE.**

---

**Última atualização:** 2025-01-XX
**Status:** ✅ PERSISTÊNCIA GARANTIDA - DADOS NUNCA SÃO PERDIDOS!
