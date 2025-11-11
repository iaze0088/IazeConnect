# Evolution API - Source Code Archives

## Arquivos Disponíveis

O usuário forneceu os seguintes arquivos de código-fonte da Evolution API:

### Versão 2.3.2
- **TAR.GZ**: https://customer-assets.emergentagent.com/job_realtime-messenger-19/artifacts/dfp4p48e_evolution-api-2.3.2.tar.gz
- **ZIP**: https://customer-assets.emergentagent.com/job_realtime-messenger-19/artifacts/mrj0h8vw_evolution-api-2.3.2.zip

### Versão 2.3.3
- **TAR.GZ**: https://customer-assets.emergentagent.com/job_realtime-messenger-19/artifacts/hjn3xrme_evolution-api-2.3.3.tar.gz
- **ZIP**: https://customer-assets.emergentagent.com/job_realtime-messenger-19/artifacts/a6ebefb3_evolution-api-2.3.3.zip

### Versão 2.3.4
- **ZIP**: https://customer-assets.emergentagent.com/job_realtime-messenger-19/artifacts/87uo0j9o_evolution-api-2.3.4.zip

## Formato Correto do Webhook (v2.3.x)

Baseado na análise do arquivo `/src/api/integrations/event/webhook/webhook.schema.ts` da versão 2.3.3:

```json
{
  "webhook": {
    "enabled": true,
    "url": "https://your-backend-url/api/whatsapp/webhook/evolution",
    "headers": {},
    "byEvents": false,
    "base64": false,
    "events": []
  }
}
```

### Campos Obrigatórios
- `webhook` (objeto raiz)
- `webhook.enabled` (boolean)
- `webhook.url` (string, não pode ser vazio)

### Campos Opcionais
- `webhook.headers` (objeto)
- `webhook.byEvents` (boolean)
- `webhook.base64` (boolean)
- `webhook.events` (array de strings)

## Endpoint de Configuração

```
PUT /webhook/set/{instance_name}
```

## Correção Aplicada

Data: 27/10/2024

O payload do webhook em `backend/whatsapp_service.py` foi corrigido para incluir o objeto `webhook` como raiz, conforme exigido pela Evolution API v2.3.x.

**Antes (incorreto):**
```json
{
  "enabled": true,
  "url": "webhook_url",
  "webhookByEvents": false,
  "events": []
}
```

**Depois (correto):**
```json
{
  "webhook": {
    "enabled": true,
    "url": "webhook_url",
    "headers": {},
    "byEvents": false,
    "base64": false,
    "events": []
  }
}
```
