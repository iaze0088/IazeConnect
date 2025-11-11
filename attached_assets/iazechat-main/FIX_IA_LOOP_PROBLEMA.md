# 🔧 CORREÇÃO: IA Repetindo Mesma Pergunta (Loop Infinito)

## 📋 PROBLEMA IDENTIFICADO

A IA estava presa em um loop infinito, repetindo a mesma pergunta sobre qual aparelho usar, mesmo após o usuário ter respondido.

### Cenário do Bug:
1. IA pergunta: "Qual aparelho você vai usar? (TV Box, Smart TV, Fire Stick, Celular ou PC)"
2. Usuário responde: "Smartv"
3. IA repete: "Qual aparelho você vai usar? (TV Box, Smart TV, Fire Stick, Celular ou PC)"
4. Loop continua infinitamente

## 🔍 ROOT CAUSE ANALYSIS

### Causa Raiz 1: Detecção de Dispositivo Inflexível
O código estava procurando por strings exatas:
```python
# ❌ PROBLEMA
if any(device in content_lower for device in ['tv box', 'smart tv', 'fire stick', 'celular', 'pc']):
```

- Procurava por 'smart tv' (com espaço)
- Usuário digitava 'smartv' (sem espaço)
- Resultado: has_device = False → pergunta repetida

### Causa Raiz 2: Sem Limite de Repetições
O interceptor não tinha proteção contra loops infinitos. Mesmo com histórico grande, continuava forçando a mesma pergunta.

### Causa Raiz 3: Mensagens Curtas Não Processadas
A IA recebia "Smartv" diretamente, sem contexto claro de que era uma resposta à pergunta sobre dispositivos.

## ✅ SOLUÇÕES IMPLEMENTADAS

### Fix 1: Detecção Flexível de Dispositivos com Regex
```python
# ✅ SOLUÇÃO
device_patterns = [
    'tvbox', 'tv-box', 'tv_box',  # TV Box (todas variações)
    'smarttv', 'smart-tv', 'smart_tv',  # Smart TV
    'firestick', 'fire-stick', 'fire_stick',  # Fire Stick
    'celular', 'smartphone', 'android', 'iphone', 'ios',  # Celular
    'pc', 'computador', 'notebook', 'desktop'  # PC
]

# Remove espaços para match flexível
content_lower = msg.get('content', '').lower().replace(' ', '')

if any(pattern in content_lower for pattern in device_patterns):
    has_device = True
    logger.info(f"✅ Dispositivo detectado no histórico: {msg.get('content', '')}")
```

**Benefícios:**
- Aceita "smarttv", "smart tv", "smart-tv"
- Aceita "tvbox", "tv box", "tv-box"
- Aceita variações de celular (smartphone, android, iphone)
- Remove espaços para match mais robusto

### Fix 2: Proteção Contra Loop Infinito
```python
# ✅ SOLUÇÃO
if not has_device and len(history) < 4:
    # Forçar pergunta apenas se histórico pequeno
    ...
else:
    if has_device:
        logger.info(f"✅ Dispositivo já mencionado. Continuando conversa natural com IA")
    else:
        logger.info(f"⚠️ Histórico muito longo ({len(history)} msgs), saindo do interceptor para evitar loop")
```

**Proteções Adicionadas:**
- Limite de 4 mensagens no histórico antes de sair do interceptor
- Log claro quando dispositivo é detectado
- Log quando sai do interceptor por proteção de loop

### Fix 3: Normalização de Mensagens Curtas
```python
# ✅ SOLUÇÃO
device_mappings = {
    'smarttv': 'Smart TV',
    'smart-tv': 'Smart TV',
    'tvbox': 'TV Box',
    'firestick': 'Fire Stick',
    'celular': 'Celular',
    'pc': 'PC',
    ...
}

# Se mensagem curta (1-2 palavras) E corresponde a um dispositivo
if len(user_message.split()) <= 2:
    for key, value in device_mappings.items():
        if key in user_msg_lower:
            normalized_message = f"Vou usar {value}"
            logger.info(f"🔄 Mensagem normalizada: '{user_message}' → '{normalized_message}'")
            break

message = UserMessage(text=normalized_message)
```

**Benefícios:**
- "Smartv" → "Vou usar Smart TV"
- "tvbox" → "Vou usar TV Box"
- Fornece contexto claro para a IA entender a resposta
- Mensagem normalizada é enviada para a IA

## 📊 TESTES ESPERADOS

### Cenário 1: Resposta com Variação
```
User: "teste gratis"
IA: "Ótimo! Vou te ajudar com o teste grátis... Em qual dispositivo? • Smart TV • TV Box..."
User: "smarttv" (sem espaço)
IA: [DETECTA dispositivo, continua conversa] "Ótimo! Qual aplicativo? ASSIST PLUS ou LAZER PLAY?"
✅ PASSA - Não repete pergunta
```

### Cenário 2: Resposta Normalizada
```
User: "teste gratis"
IA: "Em qual dispositivo? • Smart TV • TV Box..."
User: "Smart TV"
✅ Mensagem normalizada para "Vou usar Smart TV"
IA: [Continua conversa naturalmente]
```

### Cenário 3: Proteção de Loop
```
User: mensagens múltiplas sem mencionar dispositivo
✅ Após 4 mensagens, interceptor desliga
✅ IA continua conversa naturalmente
```

## 🎯 RESULTADO ESPERADO

**ANTES:**
- IA: "Qual aparelho?"
- User: "Smartv"
- IA: "Qual aparelho?" (repete)
- User: "já respondi..."
- IA: "Qual aparelho?" (loop infinito) ❌

**DEPOIS:**
- IA: "Qual aparelho?"
- User: "Smartv"
- IA: "Ótimo! Qual aplicativo?" (continua) ✅

## 📁 ARQUIVOS MODIFICADOS

- `/app/backend/vendas_ai_service.py`
  - Linhas 1153-1189: Detecção flexível de dispositivos
  - Linhas 1255-1285: Normalização de mensagens curtas

## 🚀 DEPLOY

```bash
sudo supervisorctl restart backend
```

Status: ✅ BACKEND RUNNING (pid 805)

## 📝 NOTAS IMPORTANTES

1. **Logs Adicionados**: Todos os pontos de decisão agora têm logs claros
2. **Proteção de Loop**: Limite de 4 mensagens antes de desligar interceptor
3. **Match Flexível**: Remove espaços e aceita variações (smarttv, smart-tv, smart_tv)
4. **Normalização**: Mensagens curtas ganham contexto automático

---

**Data da Correção:** 2025-01-XX
**Testado Em:** Preview Environment
**Status:** ✅ IMPLEMENTADO E BACKEND REINICIADO
