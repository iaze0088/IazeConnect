# 🔧 Configuração Cloudflare para suporte.help

## ✅ STATUS ATUAL

### Backend
- ✅ FastAPI rodando na porta 8001
- ✅ Respondendo corretamente em `http://127.0.0.1:8001/api/health`
- ✅ TenantMiddleware reabilitado e configurado com domínios corretos

### Frontend
- ✅ React rodando na porta 3000
- ✅ `REACT_APP_BACKEND_URL` configurado para `https://suporte.help`

### Nginx
- ✅ Rodando nas portas 80 (HTTP) e 443 (HTTPS)
- ✅ Proxy reverso `/api` → Backend (porta 8001)
- ✅ Proxy reverso `/` → Frontend (porta 3000)
- ✅ Certificado SSL self-signed gerado
- ✅ Configurado como `default_server` para aceitar requisições via IP e domínio

## 🌐 CONFIGURAÇÃO CLOUDFLARE NECESSÁRIA

### 1. Modo SSL/TLS (CRÍTICO)

Acesse: **Cloudflare Dashboard → SSL/TLS → Overview**

**Escolha uma das opções:**

#### Opção A: Full (Recomendado) ✅
- Cloudflare → Origin Server: **HTTPS com certificado self-signed**
- ✅ Já configurado no servidor
- ✅ Certificado self-signed gerado: `/etc/ssl/certs/suporte_help.crt`
- **Configure no Cloudflare: SSL/TLS mode = Full**

#### Opção B: Flexible (Mais simples, menos seguro)
- Cloudflare → Origin Server: **HTTP**
- ⚠️ Conexão entre Cloudflare e servidor não é criptografada
- **Configure no Cloudflare: SSL/TLS mode = Flexible**

**NÃO USE:** Full (Strict) - requer certificado válido assinado por CA

### 2. Page Rules (IMPORTANTE)

Crie as seguintes Page Rules para evitar cache de API:

#### Rule 1: Bypass Cache para API
- URL: `suporte.help/api/*`
- Settings:
  - Cache Level: **Bypass**
  - Disable Apps: **On**
  - Disable Performance: **On**

#### Rule 2: Cache Frontend
- URL: `suporte.help/*`
- Settings:
  - Cache Level: **Standard**
  - Browser Cache TTL: **4 hours**

### 3. Firewall / WAF

Verifique se não há regras bloqueando:
- POST requests para `/api/auth/*`
- WebSocket connections
- Requests grandes (uploads de mídia)

**Cloudflare Dashboard → Security → WAF**
- ✅ Certifique-se que não há regras bloqueando `/api/*`

### 4. DNS (Já configurado conforme screenshot)

```
Tipo: A
Nome: suporte.help
Conteúdo: 151.243.218.223
Proxy: ✅ Proxied (nuvem laranja)
```

### 5. Origin Rules (Opcional mas recomendado)

Para preservar IP real do cliente:

**Cloudflare Dashboard → Rules → Transform Rules → HTTP Request Header Modification**

Adicione:
- Header: `X-Forwarded-For`
- Value: `ip.src`

## 🧪 TESTES PARA VALIDAR

### Teste 1: Health Check
```bash
curl https://suporte.help/api/health
```
**Esperado:** `{"status":"healthy","service":"backend",...}`

### Teste 2: Login Admin
```bash
curl -X POST https://suporte.help/api/auth/admin/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@admin.com","password":"102030ab"}'
```
**Esperado:** `{"token":"...","user_type":"admin",...}`

### Teste 3: Frontend
Acesse no navegador: `https://suporte.help/admin/login`
**Esperado:** Página de login carrega corretamente

### Teste 4: WebSocket (se aplicável)
Verifique se conexões WebSocket estão funcionando:
- Chat em tempo real
- Notificações

## 🔍 TROUBLESHOOTING

### Problema: "senha invalida" ao fazer login

**Possíveis causas:**

1. **Cloudflare está bloqueando requests** (403/502)
   - Solução: Desabilitar WAF temporariamente
   - Ou: Adicionar regra para permitir `/api/auth/*`

2. **SSL/TLS mode incorreto**
   - Solução: Alterar para "Full" ou "Flexible"

3. **Page Rules cacheando API**
   - Solução: Criar regra de Bypass para `/api/*`

4. **Cloudflare Challenge bloqueando**
   - Solução: Security → Settings → Security Level = Medium ou Low

### Problema: Frontend carrega mas não conecta ao backend

1. **Verifique CORS:**
   ```bash
   curl -I https://suporte.help/api/health \
     -H "Origin: https://suporte.help"
   ```
   Deve incluir: `Access-Control-Allow-Origin: *`

2. **Verifique se requests chegam ao servidor:**
   ```bash
   tail -f /var/log/supervisor/backend.out.log
   ```

### Problema: WebSocket não conecta

1. **Cloudflare free plan limita WebSocket:**
   - Solução: Criar subdomínio `ws.suporte.help` sem proxy (DNS Only)
   - Apontar para: `151.243.218.223`
   - Usar no frontend: `wss://ws.suporte.help/api/ws/...`

## 📊 CONFIGURAÇÃO ATUAL DO SERVIDOR

### Nginx Config
```nginx
# HTTP (porta 80)
server {
    listen 80 default_server;
    server_name suporte.help 151.243.218.223 _;
    
    location /api {
        proxy_pass http://127.0.0.1:8001;
        # ... headers WebSocket
    }
    
    location / {
        proxy_pass http://127.0.0.1:3000;
        # ... headers WebSocket
    }
}

# HTTPS (porta 443)
server {
    listen 443 ssl http2 default_server;
    server_name suporte.help 151.243.218.223 _;
    
    ssl_certificate /etc/ssl/certs/suporte_help.crt;
    ssl_certificate_key /etc/ssl/private/suporte_help.key;
    
    # ... mesmas locations
}
```

### Variáveis de Ambiente

**Frontend (.env):**
```env
REACT_APP_BACKEND_URL=https://suporte.help
```

**Backend (.env):**
```env
MONGO_URL="mongodb://localhost:27017"
ADMIN_PASSWORD="102030ab"
CORS_ORIGINS="*"
```

### Serviços
```bash
sudo supervisorctl status
# backend   RUNNING   pid xxx
# frontend  RUNNING   pid xxx
# mongodb   RUNNING   pid xxx
```

## 🎯 PRÓXIMOS PASSOS

1. **Configure Cloudflare SSL/TLS mode** (Full ou Flexible)
2. **Crie Page Rules** para bypass de cache em `/api/*`
3. **Teste o login** em `https://suporte.help/admin/login`
4. **Verifique logs** se houver problemas: `tail -f /var/log/supervisor/backend.out.log`
5. **Se WebSocket falhar:** Crie subdomínio `ws.suporte.help` (DNS Only)

## 📞 SUPORTE

Se após configurar o Cloudflare ainda houver problemas:

1. Compartilhe screenshot do erro no browser (F12 → Console)
2. Compartilhe screenshot das configurações SSL/TLS do Cloudflare
3. Teste acesso direto via IP: `http://151.243.218.223/admin/login`

---

**Última atualização:** 2025-11-06
**Servidor:** 151.243.218.223
**Domínio:** suporte.help
