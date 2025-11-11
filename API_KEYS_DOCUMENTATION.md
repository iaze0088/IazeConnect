# IAZE API Keys & Webhook System - Documentação Completa

## 📋 Visão Geral

O Sistema de API Keys do IAZE permite que integrações externas gerenciem conexões WhatsApp e recebam eventos em tempo real via webhooks. Este documento descreve como criar, usar e gerenciar API Keys para integrar sistemas externos com o IAZE.

---

## 🔑 Autenticação

Todas as requisições à API devem incluir o header de autenticação:

```http
Authorization: Bearer iaze_live_XXXXXXXXXXXXXXXXXXXX
```

### Formato da API Key

- **Prefixo**: `iaze_live_`
- **Formato**: Base32 (32 caracteres após o prefixo)
- **Exemplo**: `iaze_live_A1B2C3D4E5F6G7H8I9J0K1L2M3N4O5P6`

---

## 📡 Endpoints Disponíveis

### 1. Criar Nova API Key

```http
POST /api/api-keys
Content-Type: application/json
Authorization: Bearer <JWT_TOKEN_DO_RESELLER>

{
  "name": "Servidor IAZE Externo",
  "connectionLimit": 10,
  "webhookUrl": "https://seu-servidor.com/webhooks/iaze",
  "webhookSecret": "seu_secret_aqui_min_32_chars_xyz",
  "webhookEvents": ["message", "status", "qr", "connection"]
}
```

**Resposta (201)**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Servidor IAZE Externo",
  "keyPrefix": "iaze_liv",
  "keyLastChars": "O5P6",
  "apiKey": "iaze_live_A1B2C3D4E5F6G7H8I9J0K1L2M3N4O5P6",
  "connectionLimit": 10,
  "webhookUrl": "https://seu-servidor.com/webhooks/iaze",
  "webhookEvents": ["message", "status", "qr", "connection"],
  "status": "active",
  "currentConnections": 0,
  "totalRequests": 0,
  "createdAt": "2025-11-11T21:30:00.000Z"
}
```

⚠️ **IMPORTANTE**: A `apiKey` completa só é exibida uma vez na criação. Guarde-a em local seguro!

---

### 2. Listar API Keys

```http
GET /api/api-keys
Authorization: Bearer <JWT_TOKEN_DO_RESELLER>
```

**Resposta (200)**:
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Servidor IAZE Externo",
    "keyPrefix": "iaze_liv",
    "keyLastChars": "O5P6",
    "connectionLimit": 10,
    "currentConnections": 3,
    "totalRequests": 1543,
    "status": "active",
    "createdAt": "2025-11-11T21:30:00.000Z",
    "lastUsedAt": "2025-11-11T22:15:00.000Z"
  }
]
```

---

### 3. Renovar API Key (Rotate)

```http
POST /api/api-keys/:id/rotate
Authorization: Bearer <JWT_TOKEN_DO_RESELLER>
```

**Resposta (200)**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "apiKey": "iaze_live_Z9Y8X7W6V5U4T3S2R1Q0P9O8N7M6L5K4",
  "message": "API Key renovada com sucesso. Atualize suas integrações!"
}
```

⚠️ A chave antiga é invalidada imediatamente.

---

### 4. Atualizar API Key

```http
PATCH /api/api-keys/:id
Content-Type: application/json
Authorization: Bearer <JWT_TOKEN_DO_RESELLER>

{
  "name": "Servidor IAZE Principal",
  "connectionLimit": 20,
  "webhookUrl": "https://novo-servidor.com/webhooks",
  "webhookEvents": ["qr", "connection"]
}
```

---

### 5. Deletar API Key

```http
DELETE /api/api-keys/:id
Authorization: Bearer <JWT_TOKEN_DO_RESELLER>
```

**Resposta (200)**:
```json
{
  "message": "API Key deletada com sucesso"
}
```

⚠️ Todas as conexões associadas serão desvinculadas.

---

### 6. Estatísticas de Uso

```http
GET /api/api-keys/:id/usage
Authorization: Bearer <JWT_TOKEN_DO_RESELLER>
```

**Resposta (200)**:
```json
{
  "apiKeyId": "550e8400-e29b-41d4-a716-446655440000",
  "currentConnections": 3,
  "connectionLimit": 10,
  "totalRequests": 1543,
  "connections": [
    {
      "id": "conn-123",
      "sessionName": "support-bot-1",
      "status": "connected",
      "phoneNumber": "5511999999999",
      "createdAt": "2025-11-11T20:00:00.000Z"
    }
  ]
}
```

---

## 🪝 Sistema de Webhooks

### Configuração

Ao criar uma API Key, configure:

1. **webhookUrl**: URL HTTPS do seu endpoint
2. **webhookSecret**: Segredo mínimo de 32 caracteres para validação HMAC
3. **webhookEvents**: Array com eventos que deseja receber

### Eventos Disponíveis

| Evento | Descrição |
|--------|-----------|
| `message` | Nova mensagem recebida/enviada |
| `status` | Mudança de status da conexão |
| `qr` | QR Code gerado para autenticação |
| `connection` | Conexão estabelecida/perdida |

---

### Estrutura do Webhook

Cada webhook POST enviado ao seu endpoint contém:

**Headers**:
```http
Content-Type: application/json
X-IAZE-Signature: sha256=abc123def456...
X-IAZE-Event: qr
X-IAZE-Delivery-ID: 550e8400-e29b-41d4-a716-446655440000
```

**Body**:
```json
{
  "eventType": "qr",
  "timestamp": "2025-11-11T21:45:00.000Z",
  "resellerId": "reseller-123",
  "source": {
    "connectionId": "conn-456",
    "sessionName": "support-bot-1"
  },
  "data": {
    "qrCode": "data:image/png;base64,iVBORw0KGgoAAAANS..."
  }
}
```

---

### Validação de Assinatura HMAC

**CRÍTICO PARA SEGURANÇA**: Sempre valide a assinatura antes de processar o webhook!

#### Exemplo em Node.js:

```javascript
const crypto = require('crypto');

function validateWebhookSignature(req, webhookSecret) {
  const signature = req.headers['x-iaze-signature'];
  const payload = JSON.stringify(req.body);
  
  const hmac = crypto.createHmac('sha256', webhookSecret);
  hmac.update(payload);
  const expectedSignature = 'sha256=' + hmac.digest('hex');
  
  return crypto.timingSafeEqual(
    Buffer.from(signature),
    Buffer.from(expectedSignature)
  );
}

// Uso no endpoint
app.post('/webhooks/iaze', (req, res) => {
  const isValid = validateWebhookSignature(req, process.env.IAZE_WEBHOOK_SECRET);
  
  if (!isValid) {
    return res.status(401).json({ error: 'Invalid signature' });
  }
  
  // Processar evento
  const { eventType, data } = req.body;
  console.log(`Evento recebido: ${eventType}`, data);
  
  res.status(200).json({ received: true });
});
```

#### Exemplo em Python:

```python
import hmac
import hashlib

def validate_webhook_signature(request, webhook_secret):
    signature = request.headers.get('X-IAZE-Signature', '')
    payload = request.get_data(as_text=True)
    
    expected_signature = 'sha256=' + hmac.new(
        webhook_secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected_signature)

# Uso no Flask
@app.route('/webhooks/iaze', methods=['POST'])
def handle_webhook():
    if not validate_webhook_signature(request, os.getenv('IAZE_WEBHOOK_SECRET')):
        return jsonify({'error': 'Invalid signature'}), 401
    
    event = request.json
    print(f"Evento recebido: {event['eventType']}", event['data'])
    
    return jsonify({'received': True}), 200
```

---

### Sistema de Retry

Se o webhook falhar (timeout, erro HTTP 5xx), o sistema tentará reenviar com backoff exponencial:

| Tentativa | Intervalo |
|-----------|-----------|
| 1 | Imediato |
| 2 | 1 minuto |
| 3 | 5 minutos |
| 4 | 15 minutos |
| 5 | 1 hora |

Após 5 tentativas falhas, o webhook é marcado como "failed" e não será mais reenviado.

**Requisitos para Retry Bem-Sucedido**:
- Responder com HTTP 200-299
- Timeout máximo: 10 segundos
- Endpoint deve estar acessível publicamente via HTTPS

---

## 🔒 Segurança

### Rate Limiting

- **Limite de Conexões**: Configurável por API Key (campo `connectionLimit`)
- **Controle**: Tentativas de criar conexões além do limite retornam HTTP 429

### Armazenamento Seguro

- ✅ API Keys são hasheadas com bcrypt (custo 10)
- ✅ Webhook secrets são armazenados em texto puro (necessário para HMAC)
- ✅ Apenas o prefixo (8 chars) e últimos 4 chars são exibidos na UI

### Boas Práticas

1. **Nunca exponha API Keys** em código cliente (frontend)
2. **Use HTTPS** para todas as comunicações
3. **Valide sempre** a assinatura HMAC dos webhooks
4. **Rotacione keys** periodicamente (a cada 90 dias)
5. **Monitore uso** via endpoint `/api/api-keys/:id/usage`
6. **Webhook secrets** devem ter pelo menos 32 caracteres aleatórios

---

## 📊 Exemplos de Fluxo Completo

### Fluxo 1: Criar Conexão WhatsApp via API

```bash
# 1. Criar API Key (via UI do IAZE ou JWT do reseller)
curl -X POST https://iaze.com/api/api-keys \
  -H "Authorization: Bearer <JWT_RESELLER>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Bot Atendimento",
    "connectionLimit": 5,
    "webhookUrl": "https://meubot.com/webhooks",
    "webhookSecret": "abc123def456ghi789jkl012mno345pqr678stu901vwx234yz",
    "webhookEvents": ["qr", "connection", "message"]
  }'

# Resposta: { "apiKey": "iaze_live_X1Y2Z3..." }

# 2. Criar conexão WhatsApp
curl -X POST https://iaze.com/api/whatsapp/connections \
  -H "Authorization: Bearer iaze_live_X1Y2Z3..." \
  -H "Content-Type: application/json" \
  -d '{
    "sessionName": "suporte-vendas",
    "resellerId": "reseller-123"
  }'

# 3. Iniciar sessão (gera QR Code)
curl -X POST https://iaze.com/api/whatsapp/connections/<ID>/start \
  -H "Authorization: Bearer iaze_live_X1Y2Z3..."

# 4. Seu webhook recebe:
# POST https://meubot.com/webhooks
# {
#   "eventType": "qr",
#   "data": { "qrCode": "data:image/png;base64,..." }
# }

# 5. Após scan, webhook recebe:
# {
#   "eventType": "connection",
#   "data": { "status": "connected", "phoneNumber": "5511999999999" }
# }
```

---

### Fluxo 2: Monitorar Uso e Rotacionar Key

```bash
# 1. Verificar estatísticas
curl https://iaze.com/api/api-keys/<ID>/usage \
  -H "Authorization: Bearer <JWT_RESELLER>"

# Resposta:
# {
#   "currentConnections": 4,
#   "connectionLimit": 5,
#   "totalRequests": 10542
# }

# 2. Rotacionar key (antes de expirar)
curl -X POST https://iaze.com/api/api-keys/<ID>/rotate \
  -H "Authorization: Bearer <JWT_RESELLER>"

# Resposta:
# {
#   "apiKey": "iaze_live_NEW_KEY_HERE",
#   "message": "API Key renovada com sucesso"
# }

# 3. Atualizar sistema externo com nova key
# (A antiga para de funcionar imediatamente)
```

---

## 🛠️ Troubleshooting

### Webhook não está sendo recebido

1. ✅ Verifique se `webhookUrl` é HTTPS válida
2. ✅ Confirme que endpoint responde HTTP 200
3. ✅ Verifique firewall/rede do servidor
4. ✅ Timeout do servidor < 10s

### Erro "Invalid Signature"

1. ✅ Use `webhookSecret` exato configurado na API Key
2. ✅ Valide contra body JSON **exato** (sem formatação)
3. ✅ Use `crypto.timingSafeEqual` para evitar timing attacks

### Limite de conexões excedido

```json
{
  "error": "Connection limit exceeded. Current: 5, Limit: 5"
}
```

**Solução**: Aumente `connectionLimit` via PATCH ou delete conexões antigas.

---

## 📞 Suporte

- **Documentação**: Este arquivo
- **UI de Gerenciamento**: `/whatsapp` → Aba "API Keys"
- **Logs do Sistema**: Console do servidor IAZE

---

**Versão**: 1.0.0 | **Data**: Novembro 2025
