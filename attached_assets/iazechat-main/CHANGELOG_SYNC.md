# 📋 CHANGELOG - SINCRONIZAÇÃO EMERGENT → SERVIDOR EXTERNO

## 🎯 RESUMO DAS ATUALIZAÇÕES

Data: 01/11/2025
Servidor: 198.96.94.106

---

## ✅ ARQUIVOS BACKEND MODIFICADOS

### 1. **server.py**
- ✅ Auto-correção de `from_id` vazio
- ✅ Busca em múltiplas coleções (users + clients)
- ✅ Sistema de keywords para credenciais
- ✅ Import socket adicionado
- ✅ SERVER_IP dinâmico
- ✅ Logs aprimorados

### 2. **vendas_models.py**
- ✅ Campo `name` adicionado em VendasStartRequest

### 3. **vendas_routes.py**
- ✅ Salvamento de `client_name` na sessão
- ✅ Salvamento de nome ao gerar teste
- ✅ Logs com nome do cliente

### 4. **vendas_ai_service.py**
- ✅ Database name via variável de ambiente

### 5. **vendas_bot_service.py**
- ✅ URL dinâmica via REACT_APP_BACKEND_URL

### 6. **whatsapp_routes.py**
- ✅ Retry logic para QR code
- ✅ Correção 400/403 errors

### 7. **whatsapp_service.py**
- ✅ Payload Evolution API v2.3
- ✅ Retry logic para get_qr_code

### 8. **office_service_playwright.py**
- ✅ Normalização de busca alfanumérica
- ✅ 8 seletores para campo de pesquisa
- ✅ Login melhorado com fallbacks
- ✅ Screenshots para debug

### 9. **keyword_credential_search.py**
- ✅ Sistema de detecção de keywords
- ✅ Busca automática de credenciais

### 10. **backup_routes.py**
- ✅ Database name via variável

### 11. **backup_scheduler.py**
- ✅ Database name via variável

### 12. **export_routes.py**
- ✅ URL via variável de ambiente

### 13. **create_main_reseller.py**
- ✅ URL genérica (não hardcoded)

### 14. **client_name_service.py** (NOVO)
- ✅ Serviço de busca de nomes
- ✅ Atualização no banco

### 15. **client_name_routes.py** (NOVO)
- ✅ Endpoints /api/client-names/*
- ✅ Status, update-all, update-single

---

## ✅ ARQUIVOS FRONTEND MODIFICADOS

### 1. **AIAgentsManager.js**
- ✅ 4 botões com link de indicação (ref=noit391017)
- ✅ Botão "ABRIR SITE" adicionado

### 2. **VendasChatNew.js**
- ✅ Campo "Nome" no formulário
- ✅ Validação de nome obrigatório
- ✅ Salvamento de nome no localStorage
- ✅ Envio de nome para backend
- ✅ URLs hardcoded removidas

### 3. **AgentDashboard.js**
- ✅ Fix React insertBefore error (UUIDs)

### 4. **index.html**
- ✅ Cache-busting implementado
- ✅ Meta app-version

---

## ✅ NOVOS RECURSOS

1. **Campo Nome no Formulário**
   - Cliente preenche nome manualmente
   - Nome salvo no banco
   - Nome aparece no painel do agente

2. **Links de Indicação Emergent**
   - 4 botões com ref=noit391017
   - Bônus por cada cadastro

3. **Sistema de Keywords**
   - Detecção automática de "qual meu usuario"
   - Busca credenciais no gestor.my

4. **Endpoints de Gerenciamento de Nomes**
   - GET /api/client-names/status
   - POST /api/client-names/update-all
   - POST /api/client-names/update-single/{id}

---

## ⚙️ CONFIGURAÇÕES NECESSÁRIAS

### Variáveis de Ambiente (.env):

```bash
# Backend
MONGO_URL="mongodb://localhost:27017"
DB_NAME="support_chat"
REACT_APP_BACKEND_URL="https://seu-dominio.com/api"
EVOLUTION_API_URL="http://45.157.157.69:8080"
SERVER_IP="198.96.94.106"  # Opcional

# Frontend
REACT_APP_BACKEND_URL="https://seu-dominio.com/api"
```

---

## 🔧 CORREÇÕES CRÍTICAS

1. ✅ URLs hardcoded removidas
2. ✅ IPs hardcoded removidos
3. ✅ Database names via variáveis
4. ✅ Evolution API v2.3 compatível
5. ✅ Busca automática de nomes desabilitada (performance)

---

## ⚠️ RECURSOS DESABILITADOS

- ❌ Busca automática de nomes (causava travamento CPU)
  - Alternativa: Cliente preenche nome no formulário

---

## 📊 ESTATÍSTICAS

- Arquivos Backend: 15 modificados + 2 novos
- Arquivos Frontend: 4 modificados
- Documentação: 2 novos arquivos
- Total: 23 arquivos atualizados

---

## ✅ PRONTO PARA PRODUÇÃO

Todos os URLs hardcoded foram corrigidos.
Todas as variáveis de ambiente configuráveis.
Sistema testado e funcionando no preview.

