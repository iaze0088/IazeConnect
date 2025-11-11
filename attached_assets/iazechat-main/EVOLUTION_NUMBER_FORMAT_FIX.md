# 🔧 Correção Evolution API v2.3 - Formatação de Números

## ❌ Problema Identificado

**Erro:** `Evolution API error - Status 400: {"status":400,"error":"Bad Request","response":{"message":[["number does not match pattern \"^\\\\d+[\\\\.@\\\\w-]+\""]]}}`

**Causa:** A Evolution API v2.3 exige que o número do WhatsApp siga o padrão exato:
```
5511999999999@s.whatsapp.net
```

## ✅ Correções Aplicadas

### 1. **whatsapp_service.py** (linha 322-344)
```python
async def send_message(self, instance_name: str, to_number: str, message: str) -> Dict:
    """Enviar mensagem via Evolution API v2.3"""
    try:
        # Limpar formatação do número (remover tudo exceto dígitos)
        clean_number = ''.join(filter(str.isdigit, to_number))
        
        # Adicionar código do país se não tiver
        if not clean_number.startswith('55'):
            clean_number = f'55{clean_number}'
        
        # Evolution API v2.3 exige formato: 5511999999999@s.whatsapp.net
        formatted_number = f"{clean_number}@s.whatsapp.net"
        
        logger.info(f"📱 Enviando mensagem para: {formatted_number} (original: {to_number})")
```

### 2. **whatsapp_routes.py** (linha 1024-1035)

**Alteração do payload:**

❌ **ANTES (Incorreto):**
```json
{
    "number": "5511999999999@s.whatsapp.net",
    "text": "Mensagem"
}
```

✅ **DEPOIS (Correto para Evolution API v2.3):**
```json
{
    "number": "5511999999999@s.whatsapp.net",
    "textMessage": {
        "text": "Mensagem"
    }
}
```

## 📊 Formatos de Entrada Aceitos

A função agora aceita QUALQUER formato de entrada e converte corretamente:

| Entrada | Saída |
|---------|-------|
| `(11) 99999-9999` | `5511999999999@s.whatsapp.net` |
| `11999999999` | `5511999999999@s.whatsapp.net` |
| `5511999999999` | `5511999999999@s.whatsapp.net` |
| `+55 11 99999-9999` | `5511999999999@s.whatsapp.net` |
| `55 11 99999 9999` | `5511999999999@s.whatsapp.net` |

## 🚀 Servidores Atualizados

✅ **Emergent:** Backend reiniciado com correções  
✅ **Servidor Externo (198.96.94.106):** Docker container atualizado e reiniciado

## 🔍 Como Verificar

### No Servidor Emergent:
```bash
tail -f /var/log/supervisor/backend.out.log | grep "📱"
```

### No Servidor Externo:
```bash
docker logs -f iaze_backend | grep "📱"
```

Você verá logs como:
```
📱 Enviando mensagem para: 5511999999999@s.whatsapp.net (original: (11) 99999-9999)
```

## 📝 Teste Manual

Use o endpoint `/api/whatsapp/send-message`:
```bash
curl -X POST "https://seu-dominio/api/whatsapp/send-message" \
  -H "Authorization: Bearer SEU_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "instance_name": "sua_instancia",
    "number": "(11) 99999-9999",
    "text": "Teste Evolution API v2.3"
  }'
```

## ✅ Status: CORRIGIDO

Data: 01/11/2025  
Versão Evolution API: v2.3  
Status: ✅ Funcionando corretamente
