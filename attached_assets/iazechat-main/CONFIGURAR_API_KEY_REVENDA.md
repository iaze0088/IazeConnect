# 🔑 Como Configurar API Key Personalizada por Revenda

## 📋 Visão Geral

Cada revenda pode configurar sua própria chave OpenAI para o WA Site (aba de vendas). Isso permite:
- ✅ Controle total sobre custos de IA
- ✅ Uso de cotas e limites independentes
- ✅ Flexibilidade para escolher o provedor de IA

---

## 🎯 Para o ADMIN (Você)

### Chave Configurada
```
OPENAI_API_KEY=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
```

Esta chave está configurada em:
- ✅ Servidor Emergent: `/app/backend/.env`
- ✅ Servidor Externo (suporte.help): `/root/iaze/backend/.env`

---

## 🏢 Para REVENDAS

### Passo 1: Obter Chave OpenAI

1. Acesse: https://platform.openai.com/api-keys
2. Faça login ou crie uma conta
3. Clique em "Create new secret key"
4. Copie a chave (formato: `sk-proj-...`)

### Passo 2: Configurar no Painel

1. Acesse o painel da revenda
2. Vá em **WA Site** (aba de configuração)
3. Ative **"Configuração Inline da IA"**
4. Cole a chave OpenAI no campo **"API Key"**
5. Configure as instruções da IA
6. Salve

### Exemplo de Configuração:

```json
{
  "name": "Atendente CyberTV",
  "instructions": "Você é Juliana, atendente da CyberTV...",
  "api_key": "sk-proj-SUACHAVEAQUI",
  "temperature": 0.7,
  "llm_model": "gpt-4o-mini"
}
```

---

## 🔧 Configuração Técnica (Backend)

### Como Funciona

O sistema detecta automaticamente o tipo de chave:

- **Chave Emergent** (`sk-emergent-*`): Usa `emergentintegrations`
- **Chave OpenAI nativa** (`sk-proj-*` ou `sk-*`): Usa OpenAI SDK direta

### Ordem de Prioridade

1. **API Key da configuração inline** (WA Site config)
2. **OPENAI_API_KEY** do `.env`
3. **EMERGENT_LLM_KEY** do `.env`

### Código Responsável

Arquivo: `/app/backend/vendas_ai_humanized.py`

```python
async def get_response(
    self,
    user_message: str,
    session_id: str,
    instructions: str,
    db,
    custom_api_key: str = None  # 🔑 Chave personalizada
):
    api_key = custom_api_key or os.environ.get('OPENAI_API_KEY') or os.environ.get('EMERGENT_LLM_KEY')
    
    # Detectar tipo
    use_emergent = api_key.startswith('sk-emergent-')
    
    if use_emergent:
        response_text = await self._call_emergent(...)
    else:
        response_text = await self._call_openai(...)
```

---

## 📊 Custos Estimados (OpenAI GPT-4o-mini)

- **Input**: $0.15 por 1M tokens (~750k palavras)
- **Output**: $0.60 por 1M tokens (~750k palavras)

### Exemplo Prático:
- 1000 conversas/mês
- 10 mensagens por conversa
- ~150 tokens por resposta

**Custo mensal estimado**: $2-5 USD

---

## ⚠️ Importante

1. **Nunca compartilhe sua API key**
2. **Configure limites no painel OpenAI**
3. **Monitore o uso regularmente**
4. **Rotacione chaves a cada 90 dias**

---

## 🧪 Testando

Após configurar, envie uma mensagem no WA Site e verifique:

1. ✅ A IA responde normalmente
2. ✅ Não há erros no log
3. ✅ A resposta segue as instruções configuradas

### Verificar Logs:

**Servidor Externo:**
```bash
tail -f /tmp/backend_new.log | grep "🤖\|✅\|❌"
```

**Servidor Emergent:**
```bash
tail -f /var/log/supervisor/backend.err.log | grep "🤖\|✅\|❌"
```

---

## 🆘 Suporte

Se tiver problemas:

1. Verifique se a chave está correta
2. Confirme que tem saldo na conta OpenAI
3. Teste a chave com curl:

```bash
curl https://api.openai.com/v1/chat/completions \
  -H "Authorization: Bearer SUA_CHAVE_AQUI" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [{"role": "user", "content": "teste"}]
  }'
```

---

**Última atualização**: 03/11/2024
**Versão do sistema**: 2.0 (Multi-key support)
