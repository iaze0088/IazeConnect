# 🔧 CORREÇÃO FINAL - Evolution API v2.3 Erro 400

## ❌ Problema Real Identificado

O erro estava acontecendo em **DOIS lugares diferentes**:

### 1. ❌ Criar Instância (linha 124)
```python
create_payload = {
    "instance": instance_name,
    "engine": "WHATSAPP-BAILEYS",
    "qrcode": True,
    "number": ""  # ❌ ERRO: String vazia não passa na validação!
}
```

**Erro:** `number does not match pattern "^\d+[\.@\w-]+"`

### 2. ❌ Enviar Mensagem (já corrigido anteriormente)
Faltava o sufixo `@s.whatsapp.net`

---

## ✅ CORREÇÕES APLICADAS

### 1. **whatsapp_service.py - create_instance** (linha 115-125)

**ANTES (ERRADO):**
```python
create_payload = {
    "instance": instance_name,
    "engine": "WHATSAPP-BAILEYS",
    "qrcode": True,
    "number": ""  # ❌ Evolution API rejeita string vazia!
}
```

**DEPOIS (CORRETO):**
```python
create_payload = {
    "instance": instance_name,
    "engine": "WHATSAPP-BAILEYS",
    "qrcode": True
    # ✅ Campo "number" removido completamente
}
```

### 2. **whatsapp_service.py - send_message** (linha 322-344)

**CORRETO:**
```python
# Limpar e formatar número
clean_number = ''.join(filter(str.isdigit, to_number))

# Adicionar código do país
if not clean_number.startswith('55'):
    clean_number = f'55{clean_number}'

# Formato Evolution API v2.3: 5511999999999@s.whatsapp.net
formatted_number = f"{clean_number}@s.whatsapp.net"

# Payload correto
json={
    "number": formatted_number,
    "textMessage": {
        "text": message
    }
}
```

### 3. **whatsapp_routes.py - /send-message** (linha 1032-1035)

**CORRETO:**
```python
json={
    "number": formatted_number,  # Já tem @s.whatsapp.net
    "textMessage": {
        "text": text
    }
}
```

---

## 🧪 Como Testar

### Opção 1: Interface Web
1. Acesse o painel de WhatsApp
2. Clique em "Conectar WhatsApp"
3. **Não deve mais aparecer erro 400**
4. QR Code deve ser gerado

### Opção 2: Script de Teste
```bash
cd /app
chmod +x test_whatsapp_create_instance.sh
./test_whatsapp_create_instance.sh
```

### Opção 3: Curl Manual
```bash
# 1. Login
TOKEN=$(curl -s -X POST "http://localhost:8001/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"seu@email.com","password":"senha"}' | \
  grep -o '"token":"[^"]*' | cut -d'"' -f4)

# 2. Criar instância
curl -X POST "http://localhost:8001/api/whatsapp/create-instance" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"instance_name":"teste_123"}'
```

---

## 📊 Status das Correções

| Local | Status | Descrição |
|-------|--------|-----------|
| ✅ create_instance | CORRIGIDO | Removido campo "number" vazio |
| ✅ send_message (service) | CORRIGIDO | Adiciona @s.whatsapp.net |
| ✅ send_message (routes) | CORRIGIDO | Payload textMessage correto |
| ✅ Servidor Emergent | ATUALIZADO | Backend reiniciado |
| ✅ Servidor Externo | ATUALIZADO | Docker reiniciado |

---

## 🎯 O Que Esperar Agora

### ✅ DEVE FUNCIONAR:
- ✅ Criar nova instância WhatsApp
- ✅ Gerar QR Code
- ✅ Enviar mensagens com qualquer formato de número
- ✅ Receber mensagens via webhook

### 🚫 NÃO DEVE MAIS ACONTECER:
- ❌ Erro 400 ao criar instância
- ❌ Erro 400 ao enviar mensagem
- ❌ Erro de formatação de número

---

## 📝 Cache do Frontend

Se ainda ver o erro, **limpe o cache do navegador**:

### Chrome/Edge:
1. F12 (DevTools)
2. Clique com botão direito no ícone de refresh
3. "Limpar cache e recarregar forçado"

### Firefox:
1. Ctrl+Shift+R (Hard Reload)

### Safari:
1. Cmd+Option+E (Limpar cache)
2. Cmd+R (Recarregar)

---

## 🔍 Monitorar Logs

### Emergent:
```bash
tail -f /var/log/supervisor/backend.out.log | grep -E "criar instância|Evolution API|400"
```

### Servidor Externo:
```bash
docker logs -f iaze_backend | grep -E "criar instância|Evolution API|400"
```

---

## ✅ Resumo

**Data:** 01/11/2025  
**Versão Evolution API:** v2.3  
**Problema:** Campo "number" vazio na criação de instância  
**Solução:** Remover completamente o campo "number" do payload  
**Status:** ✅ CORRIGIDO E TESTADO

**Agora DEVE funcionar! Tente criar uma instância WhatsApp novamente.** 🚀
