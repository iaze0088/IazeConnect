# 📚 API DOCUMENTATION - CYBERTV SUPORTE

## 🔐 Autenticação

Todas as rotas (exceto login) requerem token JWT no header:
```
Authorization: Bearer {token}
```

---

## 🚪 ENDPOINTS DE AUTENTICAÇÃO

### POST /api/auth/admin/login
Login do administrador principal

**Request:**
```json
{
  "password": "senha_admin"
}
```

**Response:**
```json
{
  "token": "eyJ...",
  "user_type": "admin",
  "user_data": {
    "id": "uuid",
    "name": "Admin"
  }
}
```

---

### POST /api/auth/reseller/login
Login de revenda

**Request:**
```json
{
  "email": "revenda@email.com",
  "password": "senha123"
}
```

**Response:**
```json
{
  "token": "eyJ...",
  "user_type": "reseller",
  "user_data": {
    "id": "uuid",
    "name": "Nome da Revenda",
    "email": "revenda@email.com"
  },
  "reseller_id": "uuid"
}
```

---

### POST /api/auth/agent/login
Login de atendente

**Request:**
```json
{
  "login": "agent_login",
  "password": "senha123"
}
```

**Response:**
```json
{
  "token": "eyJ...",
  "user_type": "agent",
  "user_data": {
    "id": "uuid",
    "name": "Nome do Agent",
    "avatar": "url_avatar"
  },
  "reseller_id": "uuid"
}
```

---

## 🎫 ENDPOINTS DE TICKETS

### GET /api/tickets
Lista tickets (com filtro multi-tenant automático)

**Query Params:**
- `status` (opcional): "waiting" | "attending" | "finished"

**Response:**
```json
[
  {
    "id": "uuid",
    "client_id": "uuid",
    "client_name": "Nome Cliente",
    "status": "waiting",
    "department_id": "uuid",
    "agent_id": "uuid",
    "reseller_id": "uuid",
    "created_at": "2025-10-23T00:00:00Z",
    "last_message": {
      "text": "Última mensagem",
      "from_name": "Cliente"
    }
  }
]
```

**Filtros Automáticos:**
- Admin master: vê TODOS os tickets
- Reseller: vê apenas tickets da sua revenda
- Agent: vê apenas tickets da revenda dele
- Client: vê apenas seus próprios tickets

---

### POST /api/tickets
Criar novo ticket

**Request:**
```json
{
  "client_id": "uuid",
  "department_id": "uuid",
  "initial_message": "Mensagem inicial do cliente"
}
```

---

### GET /api/tickets/{ticket_id}/messages
Buscar mensagens de um ticket

**Response:**
```json
[
  {
    "id": "uuid",
    "ticket_id": "uuid",
    "from_id": "uuid",
    "from_name": "Nome",
    "from_type": "client" | "agent" | "ai",
    "text": "Conteúdo da mensagem",
    "file_url": "url_arquivo",
    "created_at": "2025-10-23T00:00:00Z"
  }
]
```

---

### POST /api/messages
Enviar mensagem em um ticket

**Request:**
```json
{
  "ticket_id": "uuid",
  "from_id": "uuid",
  "from_type": "agent" | "client",
  "text": "Mensagem",
  "file_url": "url_arquivo_opcional"
}
```

---

## 👥 ENDPOINTS DE AGENTS

### GET /api/agents
Lista agents (com filtro multi-tenant)

**Response:**
```json
[
  {
    "id": "uuid",
    "name": "Nome Agent",
    "login": "agent_login",
    "avatar": "url",
    "is_active": true,
    "reseller_id": "uuid"
  }
]
```

---

### POST /api/agents
Criar novo agent

**Request:**
```json
{
  "name": "Nome Agent",
  "login": "agent_login",
  "password": "senha123",
  "avatar": "url_opcional"
}
```

---

### PUT /api/agents/{agent_id}
Atualizar agent

---

### DELETE /api/agents/{agent_id}
Deletar agent

---

## 🤖 ENDPOINTS DE IA

### GET /api/ai/agents
Lista agentes de IA configurados

---

### POST /api/ai/agents
Criar agente de IA

**Request:**
```json
{
  "name": "Nome do Agente IA",
  "description": "Descrição",
  "llm_provider": "openai" | "anthropic" | "google",
  "llm_model": "gpt-4" | "claude-3" | "gemini-pro",
  "temperature": 0.7,
  "max_tokens": 500
}
```

---

### PUT /api/ai/agents/{agent_id}
Atualizar configuração do agente IA

---

### DELETE /api/ai/agents/{agent_id}
Deletar agente IA

---

## 🏢 ENDPOINTS DE DEPARTMENTS

### GET /api/ai/departments
Lista departamentos

---

### POST /api/ai/departments
Criar departamento

**Request:**
```json
{
  "name": "Suporte Técnico",
  "description": "Departamento de suporte",
  "ai_agent_id": "uuid",
  "is_default": false,
  "timeout_seconds": 300
}
```

---

## 🎬 ENDPOINTS DE IPTV

### GET /api/iptv-apps
Lista aplicativos IPTV configurados

---

### POST /api/iptv-apps
Criar template de app IPTV

---

### PUT /api/iptv-apps/{app_id}
Atualizar template

---

### DELETE /api/iptv-apps/{app_id}
Deletar template

---

## 📢 ENDPOINTS DE NOTICES

### GET /api/notices
Buscar avisos dos últimos 60 dias

---

### POST /api/notices
Criar aviso

**Request:**
```json
{
  "kind": "warning" | "info" | "success",
  "text": "Texto do aviso",
  "file_url": "url_opcional"
}
```

---

## 🏪 ENDPOINTS DE REVENDAS

### GET /api/resellers
Lista revendas (apenas admin)

---

### POST /api/resellers
Criar revenda

**Request:**
```json
{
  "name": "Nome Revenda",
  "email": "revenda@email.com",
  "password": "senha123",
  "domain": "revenda.domain.com",
  "parent_id": "uuid_opcional"
}
```

---

### PUT /api/resellers/{reseller_id}
Atualizar revenda

---

### DELETE /api/resellers/{reseller_id}
Deletar revenda

---

## 📊 CÓDIGOS DE STATUS

- `200` - Sucesso
- `201` - Criado com sucesso
- `400` - Requisição inválida
- `401` - Não autenticado
- `403` - Não autorizado (sem permissão)
- `404` - Recurso não encontrado
- `429` - Rate limit excedido
- `500` - Erro interno do servidor

---

## 🔒 SEGURANÇA MULTI-TENANT

**IMPORTANTE:** Todos os endpoints aplicam isolamento multi-tenant automaticamente:

- ✅ Admin master vê TODOS os dados
- ✅ Reseller vê apenas dados da sua revenda
- ✅ Agent vê apenas dados da revenda dele
- ✅ Client vê apenas seus próprios dados

**Nenhum usuário pode acessar dados de outra revenda!**

---

## 📈 RATE LIMITS

| Tipo de Usuário | Limite |
|-----------------|--------|
| Admin | 1000 req/min |
| Reseller | 500 req/min |
| Agent | 200 req/min |
| Client | 100 req/min |

**Ações específicas:**
- Login: 10 tentativas/min
- Criar ticket: 30/min
- Enviar mensagem: 60/min

---

## 🔌 WEBSOCKETS

### /ws/{user_id}
Conexão WebSocket para notificações em tempo real

**Eventos recebidos:**
- `new_message` - Nova mensagem em ticket
- `ticket_status_change` - Status do ticket mudou
- `new_ticket` - Novo ticket criado
- `agent_joined` - Agent entrou no atendimento

---

## 💡 EXEMPLOS DE USO

### Login e Listar Tickets (Python)
```python
import requests

# 1. Login
response = requests.post(
    "https://api.example.com/api/auth/agent/login",
    json={"login": "agent1", "password": "senha123"}
)
token = response.json()["token"]

# 2. Listar tickets
response = requests.get(
    "https://api.example.com/api/tickets?status=waiting",
    headers={"Authorization": f"Bearer {token}"}
)
tickets = response.json()
```

### Login e Listar Tickets (JavaScript)
```javascript
// 1. Login
const loginResponse = await fetch('/api/auth/agent/login', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({login: 'agent1', password: 'senha123'})
});
const {token} = await loginResponse.json();

// 2. Listar tickets
const ticketsResponse = await fetch('/api/tickets?status=waiting', {
  headers: {'Authorization': `Bearer ${token}`}
});
const tickets = await ticketsResponse.json();
```

---

Desenvolvido com ❤️ por CYBERTV
