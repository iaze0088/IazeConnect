# 🔧 Guia: Atualizar VPS 198.96.94.106

## 📋 Informações do VPS
- **IP**: 198.96.94.106
- **Domínio**: suporte.help
- **Senha**: 102030@ab

---

## Passo 1: Conectar via SSH

```bash
# Conecte ao VPS (substitua 'root' se usar outro usuário)
ssh root@198.96.94.106
# Senha: 102030@ab
```

---

## Passo 2: Atualizar Credenciais no MongoDB

### 2.1. Verificar MongoDB está rodando
```bash
systemctl status mongod
# OU
ps aux | grep mongod
```

### 2.2. Atualizar Admin
```bash
mongosh support_chat --eval '
db.users.updateOne(
  { user_type: "admin" },
  { 
    $set: { 
      email: "admin@admin.com",
      pass_hash: "$2b$12$aJlRikPuVr84.exj6v6hk.diQGJMwCezFZdpK1pu8fliiufpiexWq"
    }
  }
)'
```

**Resultado esperado**: `{ acknowledged: true, modifiedCount: 1 }`

### 2.3. Atualizar Atendentes
```bash
mongosh support_chat --eval '
db.users.updateMany(
  { 
    username: { $in: ["biancaatt", "leticiaatt", "andressaatt", "jessicaatt"] },
    user_type: "agent"
  },
  { 
    $set: { 
      pass_hash: "$2b$12$qm8pZbfFDtnTtDRj6Vd9pO7OfrnBetQ8a2tnWX57ghgEvxtX8pkoS" 
    }
  }
)'
```

**Resultado esperado**: `{ acknowledged: true, modifiedCount: 4 }`

### 2.4. Verificar atualizações
```bash
mongosh support_chat --eval '
// Verificar admin
print("Admin:");
printjson(db.users.findOne({user_type: "admin"}, {email: 1, name: 1}));

// Verificar atendentes
print("\nAtendentes:");
db.users.find({user_type: "agent", username: {$in: ["biancaatt", "leticiaatt"]}}, {username: 1, name: 1}).forEach(printjson);
'
```

---

## Passo 3: Verificar/Atualizar Backend

### 3.1. Localizar arquivo server.py
```bash
# Procurar server.py
find /opt /root /home -name "server.py" -type f 2>/dev/null | grep -i iaze
```

### 3.2. Verificar endpoint de admin login
```bash
# Ver o endpoint atual (procurar por @.*admin.*login)
grep -A 20 "admin.*login" /caminho/para/server.py
```

### 3.3. Se necessário, atualizar código
O código do admin login deve buscar do MongoDB:
```python
@api_router.post("/auth/admin/login")
async def admin_login(data: AdminLogin):
    # Buscar admin no MongoDB
    admin_user = await db.users.find_one({"user_type": "admin"})
    
    if not admin_user:
        raise HTTPException(status_code=401, detail="Admin não encontrado")
    
    # Verificar senha com bcrypt
    if not bcrypt.checkpw(data.password.encode('utf-8'), admin_user['pass_hash'].encode('utf-8')):
        raise HTTPException(status_code=401, detail="Senha incorreta")
    
    token = create_token(admin_user['id'], "admin")
    return TokenResponse(
        token=token, 
        user_type="admin", 
        user_data={
            "id": admin_user['id'],
            "reseller_id": admin_user.get('reseller_id'),
            "name": admin_user.get('name', 'Admin'),
            "email": admin_user.get('email', ''),
            "user_type": "admin"
        }
    )
```

### 3.4. Reiniciar Backend
```bash
# Opção 1: systemd
systemctl restart iaze-backend
systemctl status iaze-backend

# Opção 2: supervisor
supervisorctl restart backend
supervisorctl status backend

# Opção 3: script de start
/usr/local/bin/iaze-start.sh
```

---

## Passo 4: Verificar Frontend

### 4.1. Verificar .env do frontend
```bash
# Procurar .env
find /opt /root /home -name ".env" -path "*/frontend/*" 2>/dev/null

# Ver conteúdo
cat /caminho/para/frontend/.env | grep BACKEND
```

### 4.2. Deve conter
```
REACT_APP_BACKEND_URL=http://suporte.help
```

**NÃO deve ter**: `https://` ou `juliana-chat.preview`

### 4.3. Reiniciar Frontend
```bash
# Opção 1: systemd
systemctl restart iaze-frontend

# Opção 2: supervisor
supervisorctl restart frontend

# Opção 3: PM2
pm2 restart iaze-frontend
```

---

## Passo 5: Testar Localmente no VPS

### 5.1. Testar Backend
```bash
# Health check
curl http://localhost:8001/api/health

# Admin login
curl -X POST http://localhost:8001/api/auth/admin/login \
  -H "Content-Type: application/json" \
  -d '{"password":"102030@ab"}'

# Deve retornar token válido!
```

### 5.2. Testar Atendente
```bash
curl -X POST http://localhost:8001/api/auth/agent/login \
  -H "Content-Type: application/json" \
  -d '{"login":"biancaatt","password":"ab181818ab"}'

# Deve retornar token válido!
```

---

## Passo 6: Verificar Nginx

### 6.1. Ver configuração Nginx
```bash
nginx -T | grep -A 30 "server_name.*suporte"
```

### 6.2. Deve ter proxy para backend
```nginx
location /api {
    proxy_pass http://localhost:8001;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection 'upgrade';
    proxy_set_header Host $host;
    proxy_cache_bypass $http_upgrade;
}
```

### 6.3. Recarregar Nginx se alterado
```bash
nginx -t
systemctl reload nginx
```

---

## Passo 7: Testar Externamente

```bash
# Do VPS, testar acesso externo
curl http://suporte.help/api/health

# Do seu computador, testar:
curl http://suporte.help/api/health
```

---

## ✅ Checklist Final

- [ ] MongoDB rodando
- [ ] Admin atualizado (admin@admin.com)
- [ ] 4 atendentes atualizados
- [ ] Backend reiniciado
- [ ] Frontend .env correto (http://suporte.help)
- [ ] Frontend reiniciado
- [ ] Nginx configurado
- [ ] Teste local no VPS: OK
- [ ] Teste externo: OK

---

## 🆘 Se algo não funcionar

**Me envie**:
1. Saída de: `curl http://localhost:8001/api/health`
2. Saída de: `curl -X POST http://localhost:8001/api/auth/admin/login -H "Content-Type: application/json" -d '{"password":"102030@ab"}'`
3. Logs do backend: `tail -50 /var/log/iaze-backend.log` (ou onde estiver o log)
4. Status dos serviços: `supervisorctl status` ou `systemctl status iaze-*`

---

## 📝 Credenciais Finais

**Admin**:
- URL: https://suporte.help/admin/login
- Senha: `102030@ab`

**Atendentes**:
- URL: https://suporte.help/agent
- Usuários: biancaatt, leticiaatt, andressaatt, jessicaatt
- Senha: `ab181818ab`

**Vendas**:
- URL: https://suporte.help/vendas
- Bot "Juliana" deve responder automaticamente
