# 🧪 INSTRUÇÕES PARA TESTE DE LOGIN

## ✅ CORREÇÕES APLICADAS

### 1. Frontend - Detecção Dinâmica de Protocolo
**Arquivo:** `/app/frontend/src/lib/apiConfig.js`
- ❌ **ANTES:** URL hardcoded `https://suporte.help`
- ✅ **AGORA:** Detecta automaticamente o protocolo da página atual
  - Se acessar via `http://151.243.218.223` → API usa `http://151.243.218.223/api`
  - Se acessar via `https://suporte.help` → API usa `https://suporte.help/api`

### 2. Frontend Reiniciado
- ✅ Mudanças aplicadas e frontend rodando na porta 3000

## 🌐 CONFIGURAÇÃO CLOUDFLARE

### OPÇÃO 1: Modo Full (Recomendado) ⭐

**Passo 1:** Acesse Cloudflare Dashboard
- Vá em: **SSL/TLS → Overview**
- Altere de **"Flexible"** para **"Full"**

**Por que Full?**
- ✅ Cloudflare → Servidor: HTTPS
- ✅ Já temos certificado self-signed no servidor
- ✅ Elimina problema de Mixed Content

**Aguarde 2-3 minutos** após a mudança para propagação.

### OPÇÃO 2: Modo Flexible (Atual)

Se você preferir manter **Flexible**:
- ⚠️ Cloudflare → Servidor: HTTP
- ⚠️ Você deve acessar: `http://suporte.help` (sem S)
- ⚠️ Ou desativar proxy do Cloudflare (DNS Only)

## 🧪 TESTES PASSO A PASSO

### TESTE 1: Acesso via IP Direto (Bypass Cloudflare)

**1.1 - Limpar Cache do Browser:**
```
1. Pressione F12 (Abrir DevTools)
2. Clique com botão direito no ícone de Refresh
3. Selecione "Limpar cache e recarregar totalmente"
```

**1.2 - Acessar via HTTP:**
```
URL: http://151.243.218.223/admin/login
Email: admin@admin.com
Senha: 102030ab
```

**Resultado Esperado:**
- ✅ Página carrega
- ✅ Console (F12) mostra: "🔧 DYNAMIC CONFIG LOADED"
- ✅ Console mostra: `BASE_URL: http://151.243.218.223`
- ✅ Login funciona sem erros

**Se falhar:**
- Copie TODOS os erros do Console (F12 → Console)
- Tire screenshot do Network tab (F12 → Network)

---

### TESTE 2: Acesso via Domínio (Com Cloudflare)

**2.1 - Se Cloudflare está em modo "Full":**
```
URL: https://suporte.help/admin/login
Email: admin@admin.com
Senha: 102030ab
```

**Resultado Esperado:**
- ✅ Página carrega via HTTPS
- ✅ Console mostra: `BASE_URL: https://suporte.help`
- ✅ Login funciona sem erros de Mixed Content
- ✅ Sem erros 502/503

**2.2 - Se Cloudflare está em modo "Flexible":**
```
URL: http://suporte.help/admin/login
Email: admin@admin.com
Senha: 102030ab
```

**Resultado Esperado:**
- ✅ Cloudflare redireciona automaticamente para HTTPS
- ⚠️ Mas agora frontend detecta HTTPS e usa `https://suporte.help/api`
- ✅ Login deve funcionar

**Se falhar:**
- Verifique no Console se há erros de "Mixed Content"
- Verifique se SSL/TLS mode está "Full" ou "Flexible"

---

## 🔍 DIAGNÓSTICO DE ERROS

### Erro: "Mixed Content"
```
Mixed Content: The page at '<URL>' was loaded over HTTPS, 
but requested an insecure XMLHttpRequest endpoint
```

**Causa:** Cloudflare em modo "Flexible" + página em HTTPS tentando chamar API HTTP

**Solução:**
1. Mudar Cloudflare para modo "Full" ✅
2. OU desabilitar proxy do Cloudflare temporariamente

---

### Erro: "CORS policy"
```
Access to XMLHttpRequest has been blocked by CORS policy
```

**Causa:** Acesso via IP diferente do domínio configurado

**Solução:**
1. ✅ Nosso CORS já está configurado para aceitar `*` (todos)
2. Certifique-se de que está acessando via HTTP ou HTTPS consistente
3. Limpe cache do browser (Ctrl+Shift+Delete)

---

### Erro: "net::ERR_FAILED"
```
POST http://suporte.help/api/auth/admin/login net::ERR_FAILED
```

**Causa:** Requisição não chegou ao servidor

**Possíveis razões:**
1. Cloudflare bloqueando (verifique Firewall rules)
2. Nginx não está rodando
3. Backend não está respondendo

**Solução:**
```bash
# Verifique se Nginx está rodando:
sudo netstat -tlnp | grep :80
sudo netstat -tlnp | grep :443

# Verifique se backend está rodando:
curl http://127.0.0.1:8001/api/health
```

---

### Erro: "502 Bad Gateway"
```
502 Bad Gateway - nginx
```

**Causa:** Nginx não consegue conectar ao backend

**Solução:**
```bash
# Reinicie backend:
sudo supervisorctl restart backend

# Verifique logs:
tail -f /var/log/supervisor/backend.err.log
```

---

## 📊 VERIFICAÇÃO TÉCNICA

### Console do Browser (F12 → Console)

**Ao carregar a página, você deve ver:**
```javascript
🔧 DYNAMIC CONFIG LOADED: {
  PROTOCOL: 'http:' ou 'https:',
  HOST: '151.243.218.223' ou 'suporte.help',
  BASE_URL: 'http://151.243.218.223' ou 'https://suporte.help',
  API_BASE_URL: 'http://151.243.218.223/api' ou 'https://suporte.help/api'
}

🔧 API CONFIG (DYNAMIC): {
  BACKEND_URL: 'http://151.243.218.223' ou 'https://suporte.help',
  API_URL: 'http://151.243.218.223/api' ou 'https://suporte.help/api'
}
```

### Network Tab (F12 → Network)

**Ao fazer login, você deve ver:**
```
POST /api/auth/admin/login
Status: 200 OK
Response: {"token":"...","user_type":"admin",...}
```

**Se Status não for 200:**
- 401: Senha incorreta
- 403: Forbidden (Cloudflare bloqueando?)
- 404: Rota não encontrada (Nginx não configurado?)
- 502: Backend não respondendo
- 503: Serviço indisponível

---

## 🎯 CHECKLIST DE TESTE

- [ ] 1. Limpei cache do browser (F12 → Botão direito em Refresh)
- [ ] 2. Testei via IP: `http://151.243.218.223/admin/login`
- [ ] 3. Vi mensagem "DYNAMIC CONFIG LOADED" no Console
- [ ] 4. Login via IP funcionou? (Sim/Não)
- [ ] 5. Mudei Cloudflare para modo "Full"
- [ ] 6. Aguardei 2-3 minutos após mudança
- [ ] 7. Testei via domínio: `https://suporte.help/admin/login`
- [ ] 8. Login via domínio funcionou? (Sim/Não)

---

## 📸 SE AINDA FALHAR

**Compartilhe comigo:**

1. **Screenshot do Console (F12 → Console)** mostrando:
   - Mensagens "DYNAMIC CONFIG LOADED"
   - Todos os erros em vermelho

2. **Screenshot do Network Tab (F12 → Network)** mostrando:
   - Request para `/api/auth/admin/login`
   - Status Code (200, 404, 502, etc)
   - Response (se houver)

3. **Screenshot do Cloudflare SSL/TLS Settings** mostrando:
   - SSL/TLS mode selecionado (Flexible, Full, Full Strict)

4. **Informe:**
   - Qual URL você está usando? (IP ou domínio)
   - Está usando HTTP ou HTTPS?
   - Cloudflare está em qual modo? (Flexible ou Full)

---

## 🚀 PRÓXIMOS PASSOS

**Se Teste 1 (IP) funcionar mas Teste 2 (domínio) falhar:**
→ Problema está no Cloudflare (mude para modo "Full")

**Se ambos falharem:**
→ Problema está no servidor (compartilhe screenshots)

**Se ambos funcionarem:**
→ 🎉 Login resolvido! Pode começar a usar o sistema.

---

**Última atualização:** 2025-11-06
**Servidor:** 151.243.218.223
**Domínio:** suporte.help
