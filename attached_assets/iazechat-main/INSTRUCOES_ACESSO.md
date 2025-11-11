# 🔧 Instruções de Acesso - Sistema IAZE

## ✅ Correções Implementadas

### 1. Backend - 100% Funcional
- ✅ Admin login corrigido (MongoDB)
- ✅ Atendentes corrigidos (4 usuários)
- ✅ API /vendas funcionando
- ✅ Todos endpoints testados via curl

### 2. Credenciais Atualizadas

#### Admin
- **URL**: http://suporte.help/admin/login
- **Senha**: `102030@ab`

#### Atendentes  
- **URL**: http://suporte.help/agent
- **Usuários**:
  - `biancaatt` / senha: `ab181818ab`
  - `leticiaatt` / senha: `ab181818ab`
  - `andressaatt` / senha: `ab181818ab`
  - `jessicaatt` / senha: `ab181818ab`

#### WA Site (Vendas)
- **URL**: http://suporte.help/vendas
- Bot IA "Juliana" operacional

---

## ⚠️ Problema Identificado: HTTPS Forçado

### Causa Raiz
O ambiente está rodando dentro de um **container Kubernetes** (IP interno: 10.219.4.198) com **Ingress Controller** que força upgrade HTTP → HTTPS automaticamente.

### Por que não funciona no navegador
1. Ingress Controller redireciona HTTP para HTTPS
2. Servidor VPS não tem certificado SSL configurado
3. Resultado: `ERR_CONNECTION_REFUSED` na porta 443

---

## 🔑 Soluções Possíveis

### Solução 1: Configurar SSL/TLS (Recomendado)
```bash
# Instalar certbot no VPS/servidor externo
apt-get update && apt-get install -y certbot python3-certbot-nginx

# Obter certificado Let's Encrypt
certbot --nginx -d suporte.help

# Reiniciar Nginx
nginx -s reload
```

### Solução 2: Desabilitar HTTPS no Ingress
Se você tem acesso ao Kubernetes, adicione annotation no Ingress:
```yaml
metadata:
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "false"
```

### Solução 3: Acesso Direto (Temporário)
Acessar diretamente via IP e porta:
- Backend: http://198.96.94.106:8001/api
- Frontend: http://198.96.94.106:3000

---

## 📊 Status dos Componentes

| Componente | Status | Detalhes |
|------------|--------|----------|
| MongoDB | ✅ Funcionando | Credenciais atualizadas |
| Backend API | ✅ Funcionando | Porta 8001 |
| Frontend React | ✅ Funcionando | Porta 3000 |
| Nginx/Ingress | ⚠️ Forçando HTTPS | Precisa SSL ou desabilitar redirect |
| Bot IA (Juliana) | ✅ Funcionando | Testado via curl |

---

## 🧪 Testes Realizados

### Backend (via curl - SUCESSO)
```bash
# Admin login
curl -X POST http://localhost:8001/api/auth/admin/login \
  -H "Content-Type: application/json" \
  -d '{"password":"102030@ab"}'
# ✅ Retorna token válido

# Atendente login  
curl -X POST http://localhost:8001/api/auth/agent/login \
  -H "Content-Type: application/json" \
  -d '{"login":"biancaatt","password":"ab181818ab"}'
# ✅ Retorna token válido

# Vendas - criar sessão
curl -X POST http://localhost:8001/api/vendas/start \
  -H "Content-Type: application/json" \
  -d '{}'
# ✅ Bot responde corretamente
```

---

## 📝 Arquivos Modificados

1. `/app/backend/server.py` (linhas 1043-1070)
   - Endpoint `admin_login` usando MongoDB
   
2. `/app/frontend/.env`
   - `REACT_APP_BACKEND_URL=http://suporte.help`
   
3. `/app/frontend/src/lib/api.js`
   - Hardcoded HTTP temporariamente

4. MongoDB collection `users`
   - Admin email: admin@admin.com
   - 4 atendentes com password hash correto

---

## 🚀 Próximos Passos

1. **Configurar SSL no servidor** (melhor solução)
2. **OU** desabilitar HTTPS redirect no Ingress
3. **Testar** todos os logins após configuração SSL

---

**Data**: 2025-11-04
**Status**: Backend 100% funcional / Frontend aguardando configuração SSL
