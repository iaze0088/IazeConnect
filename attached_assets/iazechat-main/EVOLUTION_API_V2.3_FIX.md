# 🔧 Correção: Evolution API v2.3 - QR Code Generation

## 📋 Problema Identificado

A integração com a Evolution API não estava gerando QR codes corretamente devido ao uso de campos incorretos no payload de criação de instâncias.

### Sintomas:
- ❌ QR code não era gerado após criar uma conexão WhatsApp
- ❌ Mensagem de erro: "Scan the QR code with your WhatsApp Web"
- ❌ Evolution API retornava `{"count": 0}` para requisições de QR code

## 🔍 Causa Raiz

O código estava usando nomes de campos da **Evolution API v1.x**, mas o servidor estava rodando a **versão v2.3** que possui uma estrutura de payload diferente.

### Payload INCORRETO (v1.x):
```json
{
  "instanceName": "instance_name",
  "integration": "WHATSAPP-BAILEYS",
  "qrcode": true
}
```

### Payload CORRETO (v2.3):
```json
{
  "instance": "instance_name",
  "engine": "WHATSAPP-BAILEYS",
  "qrcode": true,
  "number": ""
}
```

## ✅ Solução Implementada

### 1. Atualização dos Campos no Payload

**Arquivo: `/app/backend/whatsapp_service.py`**

#### Método: `create_instance()` (linha ~118)

**ANTES:**
```python
create_payload = {
    "instanceName": instance_name,  # ❌
    "qrcode": True,
    "integration": "WHATSAPP-BAILEYS"  # ❌
}
```

**DEPOIS:**
```python
create_payload = {
    "instance": instance_name,      # ✅
    "engine": "WHATSAPP-BAILEYS",   # ✅
    "qrcode": True,
    "number": ""  # ✅ Vazio para forçar QR code
}
```

#### Método: `create_instance()` - Retry Logic (linha ~176)

**ANTES:**
```python
json={
    "instanceName": instance_name,  # ❌
    "qrcode": True
}
```

**DEPOIS:**
```python
json={
    "instance": instance_name,      # ✅
    "engine": "WHATSAPP-BAILEYS",   # ✅
    "qrcode": True,
    "number": ""  # ✅
}
```

---

### 2. Melhorias no QR Code Fetching

**Arquivo: `/app/backend/whatsapp_routes.py`**

#### Endpoint: `POST /api/whatsapp/connections` (linha ~578)

Implementado **retry logic** com 5 tentativas e delay de 2 segundos entre cada tentativa:

**ANTES:**
```python
# Uma única tentativa
async with httpx.AsyncClient(timeout=10.0) as client:
    qr_response = await client.get(...)
    if qr_response.status_code == 200:
        qr_code = qr_data.get('base64') or qr_data.get('code')
```

**DEPOIS:**
```python
# 5 tentativas com retry
max_retries = 5
retry_delay = 2  # segundos

for attempt in range(1, max_retries + 1):
    print(f"🔄 Tentativa {attempt}/{max_retries}...")
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        qr_response = await client.get(...)
        if qr_response.status_code == 200:
            qr_code = qr_data.get('base64') or qr_data.get('code') or qr_data.get('qrcode', {}).get('base64')
            if qr_code:
                break
    
    if attempt < max_retries:
        await asyncio.sleep(retry_delay)
```

**Motivo:** A Evolution API pode levar alguns segundos para gerar o QR code após a criação da instância.

---

#### Endpoint: `POST /api/whatsapp/connections/{connection_id}/refresh-qr` (linha ~882)

Aplicada a mesma lógica de retry:

```python
max_retries = 5
retry_delay = 2
new_qr = None

for attempt in range(1, max_retries + 1):
    # Buscar QR code
    # ...
    if new_qr:
        break
    if attempt < max_retries:
        await asyncio.sleep(retry_delay)
```

---

#### Endpoint: `POST /api/whatsapp/connections/{connection_id}/restart-session` (linha ~999)

Atualizado payload de recriação:

**ANTES:**
```python
create_payload = {
    "instanceName": instance_name,      # ❌
    "qrcode": True,
    "integration": "WHATSAPP-BAILEYS",  # ❌
    "webhook": {...}
}
```

**DEPOIS:**
```python
create_payload = {
    "instance": instance_name,      # ✅
    "engine": "WHATSAPP-BAILEYS",   # ✅
    "qrcode": True,
    "number": ""  # ✅
}
```

---

## 📚 Referência da Documentação

Baseado na documentação oficial da **Evolution API v2.3**:
- [Postman Documentation](https://www.postman.com/agenciadgcode/evolution-api/documentation/nm0wqgt/evolution-api-v2-3)
- [Official Docs](https://doc.evolution-api.com/v2/api-reference/instance-controller/create-instance-basic)

## 🎯 Campos Importantes

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `instance` | `string` | ✅ | Nome único da instância |
| `engine` | `string` | ✅ | Motor WhatsApp (`WHATSAPP-BAILEYS` ou `WHATSAPP-BUSINESS`) |
| `qrcode` | `boolean` | ✅ | `true` para gerar QR code automaticamente |
| `number` | `string` | ✅ | Número de telefone. **Deixar vazio (`""`)** para forçar geração de QR code |

### ⚠️ **Importante sobre o campo `number`:**

- **`number: ""`** (vazio) → Gera QR code para escaneamento
- **`number: "559999999999"`** (preenchido) → Tenta conexão automática via número (não gera QR code)

---

## 🧪 Teste

### Como testar a criação de uma nova conexão:

1. Acesse o **WhatsApp Manager** no frontend
2. Clique em **"Adicionar Nova Conexão"**
3. Configure os limites desejados
4. Clique em **"Criar Conexão"**
5. Aguarde até 10 segundos (retry logic)
6. O QR code deve aparecer automaticamente

### Se o QR code não aparecer:

1. Clique no botão **"Atualizar QR"**
2. Aguarde o retry (até 5 tentativas)
3. Verifique os logs do backend: `tail -f /var/log/supervisor/backend.*.log`

---

## 📝 Arquivos Modificados

- ✅ `/app/backend/whatsapp_service.py`
- ✅ `/app/backend/whatsapp_routes.py`

---

## 🚀 Próximos Passos

1. Teste criar uma nova conexão WhatsApp
2. Verifique se o QR code é gerado corretamente
3. Escaneie o QR code com WhatsApp Web no celular
4. Confirme se a conexão é estabelecida com sucesso

---

**Data:** 31 de Outubro de 2025  
**Versão:** Evolution API v2.3 (atendai/evolution-api:latest)
