# Credenciais de Exemplo - IAZE API Keys

## 🎯 Como Gerar Suas Credenciais

### Passo 1: Acessar o Sistema

1. Faça login no IAZE com suas credenciais de **Reseller**
2. Navegue até a página **WhatsApp** (`/whatsapp`)
3. Clique na aba **"API Keys"**

---

### Passo 2: Criar Nova API Key

Clique em **"Criar Nova API Key"** e preencha:

```
Nome da API Key: Servidor IAZE Externo
Limite de Conexões: 10
URL do Webhook: https://seu-servidor-externo.com/webhooks/iaze
Segredo do Webhook: seu_secret_minimo_32_caracteres_aqui_xyz123
Eventos do Webhook: 
  ✅ message
  ✅ status  
  ✅ qr
  ✅ connection
```

**⚠️ IMPORTANTE**: Após criar, a API Key completa será exibida **UMA ÚNICA VEZ**:

```
iaze_live_A1B2C3D4E5F6G7H8I9J0K1L2M3N4O5P6
```

**Copie e guarde em local seguro!** Você não poderá ver a chave completa novamente.

---

## 🔑 Exemplo de Credenciais Geradas

```bash
# API Key (guarde em variável de ambiente)
export IAZE_API_KEY="iaze_live_A1B2C3D4E5F6G7H8I9J0K1L2M3N4O5P6"

# Webhook Secret (use para validar assinaturas)
export IAZE_WEBHOOK_SECRET="seu_secret_minimo_32_caracteres_aqui_xyz123"

# Reseller ID (automático do seu login)
export IAZE_RESELLER_ID="reseller-123"
```

---

## 🧪 Testando a API Key

### 1. Listar suas API Keys

```bash
curl -X GET "https://iaze.suporte.help/api/api-keys" \
  -H "Authorization: Bearer <SEU_JWT_TOKEN_DO_RESELLER>"
```

Resposta esperada:
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Servidor IAZE Externo",
    "keyPrefix": "iaze_liv",
    "keyLastChars": "O5P6",
    "connectionLimit": 10,
    "currentConnections": 0,
    "totalRequests": 0,
    "status": "active"
  }
]
```

---

### 2. Criar uma Conexão WhatsApp

```bash
curl -X POST "https://iaze.suporte.help/api/whatsapp/connections" \
  -H "Authorization: Bearer iaze_live_A1B2C3D4E5F6G7H8I9J0K1L2M3N4O5P6" \
  -H "Content-Type: application/json" \
  -d '{
    "sessionName": "bot-teste-1",
    "resellerId": "reseller-123"
  }'
```

---

### 3. Iniciar Sessão e Gerar QR Code

```bash
curl -X POST "https://iaze.suporte.help/api/whatsapp/connections/<CONNECTION_ID>/start" \
  -H "Authorization: Bearer iaze_live_A1B2C3D4E5F6G7H8I9J0K1L2M3N4O5P6"
```

**Resultado**: Seu webhook receberá o QR Code automaticamente!

---

## 🪝 Recebendo Webhooks

### Configurar Endpoint no Seu Servidor

Crie um endpoint que receba POST requests do IAZE:

```javascript
// server.js (Node.js/Express)
const express = require('express');
const crypto = require('crypto');
const app = express();

app.use(express.json());

// Validar assinatura HMAC
function validateSignature(req) {
  const signature = req.headers['x-iaze-signature'];
  const secret = process.env.IAZE_WEBHOOK_SECRET;
  const payload = JSON.stringify(req.body);
  
  const hmac = crypto.createHmac('sha256', secret);
  hmac.update(payload);
  const expected = 'sha256=' + hmac.digest('hex');
  
  return crypto.timingSafeEqual(
    Buffer.from(signature),
    Buffer.from(expected)
  );
}

// Endpoint webhook
app.post('/webhooks/iaze', (req, res) => {
  // 1. Validar assinatura
  if (!validateSignature(req)) {
    console.error('❌ Assinatura inválida!');
    return res.status(401).json({ error: 'Invalid signature' });
  }
  
  // 2. Processar evento
  const { eventType, timestamp, source, data } = req.body;
  
  console.log(`✅ Webhook recebido: ${eventType}`);
  console.log(`   Sessão: ${source.sessionName}`);
  console.log(`   Timestamp: ${timestamp}`);
  console.log(`   Dados:`, data);
  
  // 3. Processar por tipo de evento
  switch (eventType) {
    case 'qr':
      console.log('📱 QR Code gerado:', data.qrCode.substring(0, 50) + '...');
      // Salvar QR code no banco ou exibir em interface
      break;
      
    case 'connection':
      console.log('🔌 Status da conexão:', data.status);
      if (data.phoneNumber) {
        console.log('📞 Número conectado:', data.phoneNumber);
      }
      break;
      
    case 'message':
      console.log('💬 Nova mensagem:', data.body);
      console.log('   De:', data.from);
      // Processar mensagem recebida
      break;
      
    case 'status':
      console.log('📊 Mudança de status:', data.status);
      break;
  }
  
  // 4. Responder sucesso (SEMPRE responda 200 para evitar retries)
  res.status(200).json({ received: true });
});

app.listen(3000, () => {
  console.log('🚀 Webhook server rodando na porta 3000');
});
```

---

### Exemplo de Payload de Webhook - QR Code

```json
{
  "eventType": "qr",
  "timestamp": "2025-11-11T22:45:00.000Z",
  "resellerId": "reseller-123",
  "source": {
    "connectionId": "conn-456",
    "sessionName": "bot-teste-1"
  },
  "data": {
    "qrCode": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA..."
  }
}
```

**Headers recebidos**:
```
Content-Type: application/json
X-IAZE-Signature: sha256=abc123def456...
X-IAZE-Event: qr
X-IAZE-Delivery-ID: 550e8400-e29b-41d4-a716-446655440000
```

---

### Exemplo de Payload - Conexão Estabelecida

```json
{
  "eventType": "connection",
  "timestamp": "2025-11-11T22:46:30.000Z",
  "resellerId": "reseller-123",
  "source": {
    "connectionId": "conn-456",
    "sessionName": "bot-teste-1"
  },
  "data": {
    "status": "connected",
    "phoneNumber": "5511999999999",
    "connected": true
  }
}
```

---

## 🔒 Segurança - Checklist

Antes de colocar em produção, verifique:

- [ ] API Key armazenada em variável de ambiente (nunca em código)
- [ ] Webhook Secret com pelo menos 32 caracteres aleatórios
- [ ] Endpoint webhook usa HTTPS (não HTTP)
- [ ] Validação de assinatura HMAC implementada
- [ ] Timeout de resposta < 10 segundos
- [ ] Tratamento de erros e logging adequados
- [ ] Rotação de API Keys programada (a cada 90 dias)

---

## 📊 Monitoramento

### Verificar Uso da API Key

```bash
curl -X GET "https://iaze.suporte.help/api/api-keys/<API_KEY_ID>/usage" \
  -H "Authorization: Bearer <JWT_RESELLER>"
```

Resposta:
```json
{
  "apiKeyId": "550e8400-e29b-41d4-a716-446655440000",
  "currentConnections": 3,
  "connectionLimit": 10,
  "totalRequests": 1543,
  "connections": [
    {
      "id": "conn-456",
      "sessionName": "bot-teste-1",
      "status": "connected",
      "phoneNumber": "5511999999999"
    }
  ]
}
```

---

## 🆘 Troubleshooting

### Webhook não está chegando?

1. **Testar endpoint externamente**:
   ```bash
   curl -X POST https://seu-servidor.com/webhooks/iaze \
     -H "Content-Type: application/json" \
     -H "X-IAZE-Signature: sha256=test" \
     -d '{"test": true}'
   ```

2. **Verificar logs do IAZE** (aba WhatsApp → Logs)

3. **Confirmar URL webhook** na API Key está correta

4. **Firewall/Rede**: Seu servidor aceita requests do IP do IAZE?

---

### Erro "Invalid signature"?

Certifique-se de:
- Usar o `webhookSecret` **exato** configurado
- Calcular HMAC sobre o body **JSON exato** (sem formatação)
- Usar `crypto.timingSafeEqual` para comparar assinaturas

---

### Limite de conexões excedido?

```bash
# Aumentar limite
curl -X PATCH "https://iaze.suporte.help/api/api-keys/<ID>" \
  -H "Authorization: Bearer <JWT_RESELLER>" \
  -H "Content-Type: application/json" \
  -d '{"connectionLimit": 20}'
```

---

## 📞 Próximos Passos

1. ✅ Criar sua API Key na UI do IAZE
2. ✅ Configurar endpoint webhook no seu servidor
3. ✅ Testar com conexão WhatsApp de teste
4. ✅ Validar assinaturas HMAC
5. ✅ Monitorar uso e logs
6. ✅ Rotacionar keys regularmente

---

**Documentação Completa**: `API_KEYS_DOCUMENTATION.md`
