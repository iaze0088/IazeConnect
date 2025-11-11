# 📋 DOCUMENTAÇÃO COMPLETA - SISTEMA IAZE
## Sistema Multi-tenant de Atendimento via WhatsApp com IA

---

## 🏗️ ARQUITETURA DO SISTEMA

### **Stack Tecnológica**
- **Backend**: FastAPI (Python 3.11)
- **Frontend**: React 18 + Vite
- **Banco de Dados**: MongoDB
- **Proxy**: Nginx
- **Gerenciamento de Processos**: Supervisor
- **Servidor**: Ubuntu/Debian (VPS)

### **Portas e Serviços**
```
- Backend API: 8001 (interno)
- Frontend: 3000 (interno)
- Nginx: 80/443 (externo)
- MongoDB: 27017 (interno)
```

---

## 🎯 FUNCIONALIDADES POR MÓDULO

### **1. SISTEMA DE AUTENTICAÇÃO (4 tipos de usuários)**

#### 1.1 **ADMIN** (Administrador Master)
- **URL**: `/admin/login`
- **Credenciais Padrão**: 
  - Senha: `102030ab`
- **Funcionalidades**:
  - Gerenciar Revendedores
  - Configurar Sistema Global
  - Gerenciar Agentes IA
  - Configurar Departamentos
  - Gerenciar WhatsApp Connections
  - Backups e Restauração
  - Configurações de Domínio
  - Assinaturas e Pagamentos

#### 1.2 **RESELLER** (Revenda)
- **URL**: `/revenda/login` ou `/reseller-login`
- **Registro**: `/reseller-register`
- **Funcionalidades**:
  - Dashboard próprio
  - Configurar logo do cliente
  - Gerenciar configurações de atendimento
  - Ver estatísticas
  - Configurar domínio personalizado
  - Gerenciar assinatura

#### 1.3 **AGENT** (Atendente)
- **URL**: `/atendente/login`
- **Funcionalidades**:
  - Atender tickets em tempo real
  - Chat WebSocket
  - Ver fila de espera
  - Transferir atendimentos
  - Busca Office (credenciais)
  - Enviar tutoriais
  - Controlar IA por conversa

#### 1.4 **CLIENT** (Cliente Final)
- **URL**: `/` ou `/client/login`
- **Funcionalidades**:
  - Iniciar conversa
  - Chat em tempo real
  - Receber atendimento humano ou IA
  - Enviar arquivos/áudio
  - Ver avisos importantes

---

### **2. PAINEL ADMIN - TODAS AS ABAS**

#### 📊 **Dashboard**
- Estatísticas em tempo real
- Tickets (Espera/Atendendo/Finalizados)
- Agentes online/offline
- Status IA por agente
- Alertas importantes

#### 👥 **Gerenciar Revendedores**
```
Funções:
- Criar novo revende dor
- Editar configurações
- Ativar/Desativar
- Replicar configurações
- Ver hierarquia
- Gerenciar assinaturas
- Transferir revendedor
```

#### 🤖 **Agentes IA**
```
Funções:
- Criar agente IA personalizado
- Configurar personalidade
- Definir instruções
- Base de conhecimento (uploads)
- Configurar modelo LLM
- Horários de funcionamento
- Linking com departamentos
- Treinamento e feedback
```

**Campos de Configuração IA**:
- Nome/Avatar
- Quem é / O que faz / Objetivo
- Como responder
- Instruções detalhadas
- Tópicos/Palavras a evitar
- Links permitidos
- Regras customizadas
- Provider (OpenAI/Anthropic/Google)
- Modelo e parâmetros
- Temperatura/Max tokens
- Delay de resposta
- Restrição de conhecimento
- Auto-detect idioma
- Timezone

#### 📁 **Departamentos**
```
Funções:
- Criar departamentos
- Vincular agentes IA
- Configurar timeout
- Ativar/Desativar IA
- Configurar horários
- Mensagens personalizadas
```

#### 📱 **WhatsApp Manager**
```
Funções:
- Conectar instâncias WhatsApp
- Gerar QR Code
- Código de pareamento
- Configurar limites (envio/recebimento)
- Desconectar/Reconectar
- Ver status
- Excluir conexões
```

**Tipos de Conexão**:
- WPPConnect (servidor próprio)
- Evolution API (externo)

#### 💾 **Backups**
```
Funções:
- Criar backup manual
- Restaurar backup
- Download backup
- Backups automáticos diários
- Ver tamanho e data
```

**Collections Incluídas**:
- users, agents, tickets, messages
- config, departments, tutorials
- office_credentials, notices
- mercado_pago_config

#### ⚙️ **Configurações Gerais**
```
ABAS:
1. Geral
   - Nome empresa
   - Usar IA
   - Avatar/Foto agente
   - Badge verificado
   - Tema/Cores
   
2. IA Inline
   - Fontes conhecimento
   - Texto fallback
   - Parâmetros LLM
   - Keywords auto-transfer
   - Mensagens (saudação/fallback)
   - Histórico conversação
   - Lembrar contexto

3. APIs Externas
   - Teste IPTV
   - Consulta Crédito
   - Webhooks
   
4. Fluxos
   - Teste Grátis
   - Vendas/Pagamentos
   
5. Integrações
   - SMTP
   - Webhooks
   - Analytics
```

#### 📺 **Apps IPTV**
```
Funções:
- Cadastrar apps IPTV
- Campos customizados
- URL template com variáveis
- Automatização de preenchimento
```

#### 📢 **Avisos**
```
Funções:
- Criar avisos
- Segmentar público (todos/agentes/clientes/revendedor específico)
- Upload mídia
- Prioridade
```

#### 📧 **Emails de Cliente**
```
Funções:
- Gerenciar lista emails
- Configurar SMTP
- Emails de expiração
- Horário envio
- Dias antes vencimento
```

#### 🔐 **Office Search**
```
Funções:
- Busca credenciais em tempo real
- Sync com Office/Gestor
- Copiar credenciais
- Renovar acesso
```

#### 🌐 **Configuração Domínio**
```
Funções:
- Domínio principal
- Path revendedor
- Path agente  
- Path cliente
- Domínio teste
```

#### 💳 **Assinaturas**
```
Funções:
- Ver todas assinaturas
- Renovação manual
- Alterar data vencimento
- Planos disponíveis
```

---

### **3. PAINEL AGENT (Atendente)**

#### 🎫 **Abas de Tickets**
1. **Espera** - Tickets aguardando atendimento (vermelho)
2. **Atendendo** - Tickets em atendimento (azul)
3. **Finalizadas** - Tickets concluídos (hoje)
4. **WhatsApp** - Tickets de WhatsApp conectado
5. **IA** - Sessões gerenciadas pela IA

#### 💬 **Chat em Tempo Real**
```
Funções:
- WebSocket bidire cional
- Enviar texto/emoji
- Upload arquivos (imagem/vídeo/áudio)
- Gravar áudio
- Ver histórico
- Marcar como lido
- Finalizar atendimento
```

#### 🔍 **Busca Office (Rápida)**
```
Funções:
- Buscar por CPF/Telefone/Chave
- Copiar usuário/senha
- Copiar tudo
- Renovar credencial
```

#### 📚 **Tutoriais**
```
Funções:
- Enviar tutorial
- Vídeo/Texto/Imagem
- Categorizado
```

#### 📰 **Avisos**
```
Funções:
- Ver avisos importantes
- Notificações
```

#### 📅 **Agendar Mensagem**
```
Funções:
- Agendar para datetime específico
- Agendar "daqui X horas"
```

---

### **4. PAINEL CLIENTE**

#### 💬 **Chat**
```
Funções:
- Iniciar conversa
- Escolher departamento
- Chat com IA ou humano
- Upload arquivos
- Gravar áudio
- Notificações push
```

#### 📱 **PWA (Progressive Web App)**
```
Funções:
- Instalar como app
- Notificações push
- Trabalhar offline
- Ícone na tela inicial
```

---

### **5. WA SITE (Vendas)**

**URL**: `/vendas`

#### 🎯 **Bot de Vendas Interativo**
```
Funções:
- Chat bot com botões
- Fluxo configurável
- Coleta dados
- Teste grátis
- Pagamento
- Submenu navegável
- Mensagens personalizadas
```

**Configuração Botões**:
- Botões raiz
- Sub-botões (hierarquia)
- Texto resposta
- Tipo ação (resposta/dados/pagamento)
- Upload mídia

---

## 🗄️ ESTRUTURA DO BANCO DE DADOS

### **Collections MongoDB**

```javascript
support_chat (database) {
  
  // Usuários
  users: {
    id, email, password, pass_hash,
    user_type: 'admin'|'reseller'|'agent'|'client',
    reseller_id, name, phone, avatar,
    is_active, created_at, pinned_user,
    pinned_pass
  },
  
  // Agentes IA
  agents: {
    id, reseller_id, name, avatar,
    ia_config: {
      who_is, what_does, objective,
      how_respond, instructions,
      avoid_topics, avoid_words,
      allowed_links, custom_rules,
      knowledge_base: [],
      llm_provider, llm_model, api_key,
      temperature, max_tokens,
      response_delay_seconds,
      knowledge_restriction,
      auto_detect_language, timezone
    },
    active_hours, department_ids,
    is_active, created_at
  },
  
  // Departamentos
  departments: {
    id, reseller_id, nome, agent_ids,
    timeout_seconds, ai_agent_id,
    is_default, personality,
    greeting_message, schedule_start_time,
    schedule_end_time, ai_enabled
  },
  
  // Tickets
  tickets: {
    id, reseller_id, client_id,
    agent_id, status: 'EM_ESPERA'|'ATENDENDO'|'FINALIZADO',
    department_id, department_origin,
    ticket_origin, created_at, updated_at,
    last_message, last_message_time,
    unread_count, ai_enabled, ai_responding,
    ai_disabled_until, client_name,
    client_email, client_phone,
    client_whatsapp, client_avatar,
    whatsapp_origin, whatsapp_instance,
    whatsapp_connection_id, is_whatsapp,
    vendas_session_id
  },
  
  // Mensagens
  messages: {
    id, ticket_id, reseller_id,
    text, sender_type: 'agent'|'client'|'system'|'ai',
    sender_id, from_id, from_type,
    to_id, to_type, file_url,
    media_type, timestamp, is_read,
    ai_context, credentials_found,
    credentials_data
  },
  
  // Configuração
  config: {
    reseller_id, empresa_nome, usa_ia,
    ia_config: { ... },
    visual_config: { ... },
    external_apis: { ... },
    flows: { ... },
    transfer_message
  },
  
  // WhatsApp Connections
  whatsapp_connections: {
    id, reseller_id, instance_name,
    phone_number, status,
    qr_code, pairing_code,
    limits: {
      max_received_per_day,
      max_sent_per_day,
      received_today,
      sent_today
    },
    active, deleted_from_evolution,
    deleted_from_db, created_at,
    updated_at, last_qr_generated
  },
  
  // Office Credentials
  office_credentials: {
    id, reseller_id, credential_id,
    credential_user, usuario, senha,
    vencimento, texto_completo,
    last_sync, cpf, telefone,
    conexoes
  },
  
  // Avisos
  notices: {
    id, reseller_id, title, content,
    recipient_type: 'all'|'agents'|'clients'|'reseller',
    target_reseller_ids,
    media_url, media_type,
    priority, created_at, updated_at
  },
  
  // Tutoriais
  tutorials: {
    id, reseller_id, title, category,
    content: {
      type: 'text'|'video'|'image',
      text, video_url, image_url
    },
    created_at, updated_at
  },
  
  // Apps IPTV
  iptv_apps: {
    id, reseller_id, name, config_url,
    url_template, fields: [],
    created_at, updated_at
  },
  
  // Backups
  backups: {
    id, reseller_id, filename,
    filepath, size_mb, created_at
  },
  
  // Mercado Pago
  mercado_pago_config: {
    reseller_id, access_token,
    public_key, webhook_secret,
    created_at, updated_at
  },
  
  // Assinaturas
  subscriptions: {
    reseller_id, plan_type,
    whatsapp_plan, current_period_end,
    is_active, created_at,
    updated_at
  },
  
  // Domínio Config
  domain_config: {
    main_domain, reseller_path,
    agent_path, client_path, test_domain
  }
}
```

---

## 🚀 PROCESSO DE INSTALAÇÃO COMPLETO

### **Passo 1: Preparar Servidor VPS**

```bash
# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar dependências
sudo apt install -y \
  python3.11 python3.11-venv python3-pip \
  nodejs npm yarn \
  mongodb-org nginx supervisor \
  git curl wget

# Verificar versões
python3 --version  # 3.11+
node --version     # 16+
mongo --version    # 6.0+
```

### **Passo 2: Configurar MongoDB**

```bash
# Iniciar MongoDB
sudo systemctl start mongod
sudo systemctl enable mongod

# Criar banco e usuário admin
mongosh << EOF
use support_chat

db.createUser({
  user: "admin",
  pwd: "senha_segura_aqui",
  roles: ["readWrite", "dbAdmin"]
})

db.users.insertOne({
  id: "01",
  user_type: "admin",
  name: "Admin Master",
  email: "admin@admin.com",
  pass_hash: "$2b$12$...",  // bcrypt de "102030ab"
  password: "102030ab",
  reseller_id: null,
  is_active: true,
  created_at: new Date().toISOString()
})
EOF
```

### **Passo 3: Clonar e Configurar Backend**

```bash
# Criar diretório
mkdir -p /app/backend
cd /app/backend

# Copiar arquivos do sistema
# (todos os arquivos .py, requirements.txt, etc)

# Criar ambiente virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt

# Criar .env
cat > .env << 'EOF'
MONGO_URL="mongodb://localhost:27017"
DB_NAME="support_chat"
CORS_ORIGINS="*"
JWT_SECRET="sua-chave-secreta-aqui"
ADMIN_PASSWORD="102030ab"
REACT_APP_BACKEND_URL="http://SEU_IP"
EOF
```

### **Passo 4: Configurar Frontend**

```bash
# Criar diretório
mkdir -p /app/frontend
cd /app/frontend

# Copiar arquivos
# (package.json, src/, public/, etc)

# Instalar dependências
yarn install

# Criar .env
cat > .env << 'EOF'
REACT_APP_BACKEND_URL=http://SEU_IP
REACT_APP_ENABLE_VISUAL_EDITS=false
ENABLE_HEALTH_CHECK=false
EOF

# Build produção
yarn build
```

### **Passo 5: Configurar Nginx**

```bash
# Criar config
sudo tee /etc/nginx/sites-available/default << 'EOF'
server {
    listen 80 default_server;
    server_name _;
    
    client_max_body_size 100M;
    
    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:8001/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_buffering off;
    }
    
    # Frontend
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        add_header Cache-Control "no-cache, no-store, must-revalidate";
    }
}
EOF

# Testar e recarregar
sudo nginx -t
sudo systemctl reload nginx
sudo systemctl enable nginx
```

### **Passo 6: Configurar Supervisor**

```bash
# Backend
sudo tee /etc/supervisor/conf.d/backend.conf << 'EOF'
[program:backend]
directory=/app/backend
command=/app/backend/venv/bin/uvicorn server:app --host 0.0.0.0 --port 8001 --workers 1
autostart=true
autorestart=true
stderr_logfile=/var/log/supervisor/backend.err.log
stdout_logfile=/var/log/supervisor/backend.out.log
EOF

# Frontend
sudo tee /etc/supervisor/conf.d/frontend.conf << 'EOF'
[program:frontend]
directory=/app/frontend
command=/usr/bin/yarn serve -s build -l 3000
autostart=true
autorestart=true
stderr_logfile=/var/log/supervisor/frontend.err.log
stdout_logfile=/var/log/supervisor/frontend.out.log
EOF

# Recarregar
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start all
```

### **Passo 7: Verificar Sistema**

```bash
# Verificar serviços
sudo supervisorctl status

# Testar backend
curl http://localhost:8001/api/health

# Testar login
curl -X POST http://SEU_IP/api/auth/admin/login \
  -H "Content-Type: application/json" \
  -d '{"password":"102030ab"}'

# Acessar frontend
# http://SEU_IP/admin/login
```

---

## 🔧 MANUTENÇÃO E TROUBLESHOOTING

### **Comandos Úteis**

```bash
# Reiniciar serviços
sudo supervisorctl restart all
sudo supervisorctl restart backend
sudo supervisorctl restart frontend

# Ver logs
tail -f /var/log/supervisor/backend.err.log
tail -f /var/log/supervisor/frontend.err.log
tail -f /var/log/nginx/error.log

# MongoDB
mongosh support_chat

# Limpar cache frontend
rm -rf /app/frontend/build
cd /app/frontend && yarn build

# Ver processos
ps aux | grep python
ps aux | grep node
```

### **Problemas Comuns**

#### 1. Login não funciona
```bash
# Verificar senha no banco
mongosh support_chat --eval "db.users.findOne({user_type:'admin'})"

# Recriar admin
mongosh support_chat --eval "
db.users.deleteMany({user_type:'admin'});
db.users.insertOne({
  id: '01',
  user_type: 'admin',
  email: 'admin@admin.com',
  pass_hash: '\$2b\$12\$NEW_HASH',
  password: '102030ab',
  is_active: true
});
"

# Reiniciar backend
sudo supervisorctl restart backend
```

#### 2. Frontend não carrega
```bash
# Verificar build
ls -la /app/frontend/build/

# Rebuild
cd /app/frontend
rm -rf build node_modules/.cache
yarn build

# Restart
sudo supervisorctl restart frontend
```

#### 3. WhatsApp não conecta
```bash
# Verificar wppconnect rodando
curl http://95.217.178.51:21465/api/status

# Ver conexões no banco
mongosh support_chat --eval "db.whatsapp_connections.find().pretty()"
```

---

## 📊 ESTATÍSTICAS E MÉTRICAS

### **Dashboard Metrics**
- Total de tickets (Espera/Atendendo/Finalizados)
- Agentes online
- Status IA
- Tempo médio de resposta
- Interações IA hoje
- Tickets por origem (WhatsApp/Web)

### **Reseller Metrics**
- Conexões WhatsApp ativas
- Uso diário (recebidos/enviados)
- Limites de plano
- Dias restantes assinatura
- Bonus disponível

---

## 🔐 SEGURANÇA

### **Autenticação**
- JWT tokens (exp: 3650 dias)
- Bcrypt password hashing
- Middleware de autorização
- Validação por tipo de usuário

### **Multi-tenancy**
- Isolamento por reseller_id
- Queries filtradas automaticamente
- Middleware tenant-aware

### **Uploads**
- Validação de tipo
- Limite de tamanho (100MB)
- Armazenamento seguro
- URLs assinadas

---

## 🌐 INTEGRAÇÕES EXTERNAS

### **WhatsApp**
- WPPConnect (próprio)
- Evolution API (terceiro)
- QR Code / Pairing Code
- Webhooks recebimento

### **IA / LLM**
- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude)
- Google (Gemini)
- Configurável por agente

### **Office/Gestor**
- Sync credenciais
- Busca em tempo real
- Renovação automática

### **Pagamentos**
- Mercado Pago
- PIX
- Webhooks

### **Email**
- SMTP configurável
- Emails de expiração
- Notificações

---

## 📝 VARIÁVEIS DE AMBIENTE

### **Backend (.env)**
```bash
MONGO_URL="mongodb://localhost:27017"
DB_NAME="support_chat"
CORS_ORIGINS="*"
JWT_SECRET="sua-chave-secreta"
ADMIN_PASSWORD="102030ab"
REACT_APP_BACKEND_URL="http://SEU_IP"
EMERGENT_LLM_KEY="sk-emergent-..."
OPENAI_API_KEY="sk-proj-..."
```

### **Frontend (.env)**
```bash
REACT_APP_BACKEND_URL=http://SEU_IP
REACT_APP_ENABLE_VISUAL_EDITS=false
ENABLE_HEALTH_CHECK=false
REACT_APP_WPPCONNECT_URL=http://WPPCONNECT_IP:21465
```

---

## 🎨 CUSTOMIZAÇÃO

### **Temas**
- Cor primária
- Logo empresa
- Imagem de fundo
- Avatar agente
- Badge verificado

### **Mensagens**
- Saudação
- Fallback
- Transferência
- Fila de espera
- Agradecimento

### **Fluxos**
- Teste grátis
- Vendas
- Coleta de dados
- Pagamento
- Follow-up

---

## 📚 RECURSOS ADICIONAIS

### **Documentação APIs**
- FastAPI Docs: `http://SEU_IP:8001/docs`
- ReDoc: `http://SEU_IP:8001/redoc`

### **WebSocket**
- Endpoint: `ws://SEU_IP/api/ws/{user_id}/{session_id}`
- Eventos: message, status, typing

### **Webhooks**
- WhatsApp incoming
- Pagamento confirmado
- Ticket atualizado

---

## ✅ CHECKLIST MIGRAÇÃO

- [ ] Backup MongoDB completo
- [ ] Exportar configurações
- [ ] Copiar arquivos uploads
- [ ] Copiar .env files
- [ ] Testar conectividade MongoDB
- [ ] Testar autenticação
- [ ] Testar WhatsApp connections
- [ ] Testar IA agents
- [ ] Verificar domínio/DNS
- [ ] Testar webhooks
- [ ] Backup final

---

## 🆘 SUPORTE

### **Logs Importantes**
```bash
# Backend errors
/var/log/supervisor/backend.err.log

# Backend output
/var/log/supervisor/backend.out.log

# Frontend
/var/log/supervisor/frontend.err.log

# Nginx
/var/log/nginx/error.log
/var/log/nginx/access.log

# MongoDB
/var/log/mongodb/mongod.log
```

### **Comandos Debug**
```bash
# Ver todas collections
mongosh support_chat --eval "db.getCollectionNames()"

# Contar documentos
mongosh support_chat --eval "db.users.countDocuments()"

# Ver último erro
mongosh support_chat --eval "db.getLastError()"

# Status sistema
sudo supervisorctl status
sudo systemctl status nginx
sudo systemctl status mongod
```

---

**FIM DA DOCUMENTAÇÃO**
**Versão**: 1.0
**Data**: 06/01/2025
**Sistema**: IAZE Multi-tenant WhatsApp + IA
