# 🔧 INSTALAÇÃO DO IAZE NO SERVIDOR COM X-UI

## ⚠️ SERVIDOR JÁ TEM X-UI INSTALADO

**Configuração:**
- X-UI ocupa portas 80 e 443
- Solução: Nginx compartilhado com subdomínios

---

## 🚀 INSTALAÇÃO (40 MINUTOS)

### PASSO 1: Conectar e Preparar
```bash
ssh root@198.96.94.106

# Criar diretório
mkdir -p /opt/iaze
cd /opt/iaze

# Upload dos arquivos (do seu computador)
scp iaze_migration_package.tar.gz root@198.96.94.106:/opt/iaze/
```

### PASSO 2: Extrair Arquivos
```bash
cd /opt/iaze
tar -xzf iaze_migration_package.tar.gz

# Usar docker-compose SEM nginx
mv docker-compose-sem-nginx.yml docker-compose.yml
```

### PASSO 3: Instalar Dependências
```bash
# Se Docker não estiver instalado
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
```

### PASSO 4: Configurar DNS
No provedor de domínio:

**Registro A (principal):**
```
Tipo: A
Nome: @
Valor: 198.96.94.106
```

**Registro A (VPN - subdomínio):**
```
Tipo: A
Nome: vpn
Valor: 198.96.94.106
```

### PASSO 5: Gerar Certificado SSL Wildcard
```bash
# Parar X-UI temporariamente
systemctl stop x-ui

# Gerar certificado wildcard (cobre suporte.help e vpn.suporte.help)
certbot certonly --standalone \
  -d suporte.help \
  -d www.suporte.help \
  -d vpn.suporte.help \
  --non-interactive --agree-tos --email admin@suporte.help

# Reiniciar X-UI
systemctl start x-ui
```

### PASSO 6: Configurar Nginx (Sistema - NÃO Docker)
```bash
# Backup do nginx atual do X-UI
cp /etc/nginx/nginx.conf /etc/nginx/nginx.conf.backup

# Copiar nova configuração (com X-UI + IAZE)
cp /opt/iaze/nginx_com_xui.conf /etc/nginx/nginx.conf

# IMPORTANTE: Ajustar porta do X-UI no nginx.conf
nano /etc/nginx/nginx.conf
# Linha ~65: proxy_pass http://localhost:54321;
# Mudar 54321 para a porta do seu X-UI panel
```

### PASSO 7: Descobrir Porta do X-UI
```bash
# Ver porta do X-UI
netstat -tulpn | grep x-ui
# OU
ps aux | grep x-ui

# Ou acessar painel X-UI e ver nas configurações
```

### PASSO 8: Subir IAZE (Sem Nginx)
```bash
cd /opt/iaze

# Subir apenas MongoDB primeiro
docker-compose up -d mongodb
sleep 10

# Restaurar backup
docker exec -i iaze_mongodb mongorestore --db support_chat /docker-entrypoint-initdb.d/support_chat

# Subir backend e frontend
docker-compose up -d
```

### PASSO 9: Testar Nginx
```bash
# Testar configuração
nginx -t

# Se OK, recarregar
nginx -s reload
# OU
systemctl reload nginx
```

### PASSO 10: Verificar Tudo Rodando
```bash
# Ver containers Docker
docker ps

# Ver portas abertas
netstat -tulpn | grep -E '80|443|3000|8001|27017|54321'

# Testar backend
curl http://localhost:8001/api/health

# Testar frontend
curl http://localhost:3000
```

---

## 🌐 ACESSAR OS SISTEMAS

Após DNS propagar (5-60 minutos):

**IAZE:**
- https://suporte.help (frontend)
- https://suporte.help/revenda/login
- https://suporte.help/atendente

**X-UI:**
- https://vpn.suporte.help (painel X-UI)

---

## 🔧 ESTRUTURA FINAL

```
Servidor: 198.96.94.106
├── Porta 80/443: Nginx (sistema - compartilhado)
│   ├── suporte.help → IAZE (localhost:3000/8001)
│   └── vpn.suporte.help → X-UI (localhost:54321)
├── IAZE Docker:
│   ├── Backend: localhost:8001
│   ├── Frontend: localhost:3000
│   └── MongoDB: localhost:27017
└── X-UI: localhost:54321 (ou outra porta)
```

---

## ⚙️ COMANDOS ÚTEIS

### Gerenciar IAZE
```bash
cd /opt/iaze
docker-compose logs -f        # Ver logs
docker-compose restart        # Reiniciar
docker-compose down           # Parar
docker-compose up -d          # Iniciar
```

### Gerenciar X-UI
```bash
systemctl status x-ui         # Status
systemctl restart x-ui        # Reiniciar
x-ui                         # Menu do painel
```

### Gerenciar Nginx
```bash
nginx -t                      # Testar config
nginx -s reload               # Recarregar
systemctl status nginx        # Status
systemctl restart nginx       # Reiniciar
```

---

## 🚨 TROUBLESHOOTING

### X-UI não aparece
```bash
# Verificar porta do X-UI
netstat -tulpn | grep x-ui

# Ajustar no nginx.conf linha ~65
nano /etc/nginx/nginx.conf
# Mudar proxy_pass http://localhost:PORTA_CORRETA;

nginx -s reload
```

### IAZE não carrega
```bash
# Verificar containers
docker ps

# Ver logs
docker-compose logs backend
docker-compose logs frontend

# Reiniciar
docker-compose restart
```

### SSL não funciona
```bash
# Verificar certificados
ls -la /etc/letsencrypt/live/suporte.help/

# Renovar se necessário
certbot renew
```

---

## ✅ CHECKLIST

- [ ] X-UI funcionando antes da instalação
- [ ] Porta do X-UI identificada
- [ ] DNS configurado (suporte.help + vpn.suporte.help)
- [ ] Certificado SSL wildcard gerado
- [ ] Docker instalado
- [ ] IAZE containers rodando
- [ ] Nginx configurado com ambos serviços
- [ ] https://suporte.help acessível (IAZE)
- [ ] https://vpn.suporte.help acessível (X-UI)

---

## 🎯 RESULTADO FINAL

✅ **Ambos sistemas funcionando**
✅ **Sem conflitos de porta**
✅ **SSL válido em ambos**
✅ **Subdomínios separados**
✅ **Performance otimizada**

**Servidor único rodando:**
- IAZE em suporte.help
- X-UI em vpn.suporte.help
