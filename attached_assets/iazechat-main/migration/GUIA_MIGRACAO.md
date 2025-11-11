# 🚀 GUIA COMPLETO DE MIGRAÇÃO - SERVIDOR DEDICADO

## 📋 INFORMAÇÕES DO SERVIDOR
- **IP:** 198.96.94.106
- **Usuário:** root
- **Senha:** 102030a
- **Domínio:** suporte.help

---

## ⚡ MIGRAÇÃO RÁPIDA (30 MINUTOS)

### PASSO 1: Conectar no Servidor
```bash
ssh root@198.96.94.106
# Senha: 102030a
```

### PASSO 2: Baixar Arquivos de Migração
```bash
# Criar diretório
mkdir -p /opt/iaze
cd /opt/iaze

# Baixar via SCP do servidor Emergent (executar do seu computador local)
scp -r root@EMERGENT_SERVER:/app/migration/* /opt/iaze/
```

**OU** copiar manualmente os arquivos:
- docker-compose.yml
- .env
- nginx.conf
- backend/ (pasta completa)
- frontend/ (pasta completa)
- mongodb_backup/ (backup do banco)

### PASSO 3: Executar Instalação Automática
```bash
cd /opt/iaze
chmod +x install.sh
./install.sh
```

**O script vai instalar:**
- ✅ Docker
- ✅ Docker Compose
- ✅ Certbot (SSL)
- ✅ Firewall configurado

### PASSO 4: Gerar Certificados SSL
```bash
# Parar qualquer serviço na porta 80/443
systemctl stop nginx 2>/dev/null
docker stop iaze_nginx 2>/dev/null

# Gerar certificado SSL
certbot certonly --standalone -d suporte.help -d www.suporte.help --non-interactive --agree-tos --email admin@suporte.help

# Copiar certificados para pasta do projeto
cp /etc/letsencrypt/live/suporte.help/fullchain.pem /opt/iaze/ssl/
cp /etc/letsencrypt/live/suporte.help/privkey.pem /opt/iaze/ssl/
```

### PASSO 5: Restaurar Backup do MongoDB
```bash
cd /opt/iaze

# Subir apenas MongoDB primeiro
docker-compose up -d mongodb

# Aguardar MongoDB iniciar
sleep 10

# Restaurar backup
docker exec -i iaze_mongodb mongorestore --db support_chat /docker-entrypoint-initdb.d/support_chat
```

### PASSO 6: Subir Todos os Serviços
```bash
cd /opt/iaze

# Subir todos os containers
docker-compose up -d

# Verificar status
docker-compose ps
```

Deve mostrar:
```
iaze_mongodb    Up
iaze_backend    Up
iaze_frontend   Up
iaze_nginx      Up
```

### PASSO 7: Configurar DNS
No seu provedor de domínio (onde comprou suporte.help):

**Registro A:**
```
Tipo: A
Nome: @
Valor: 198.96.94.106
TTL: 3600
```

**Registro A (www):**
```
Tipo: A
Nome: www
Valor: 198.96.94.106
TTL: 3600
```

**Tempo de propagação:** 5 minutos a 1 hora

### PASSO 8: Testar o Sistema
```bash
# Verificar logs
docker-compose logs -f

# Testar backend
curl http://localhost:8001/api/health

# Testar frontend
curl http://localhost:3000
```

**Acessar via navegador:**
- https://suporte.help
- https://suporte.help/revenda/login
- https://suporte.help/atendente

---

## 🔧 COMANDOS ÚTEIS

### Ver logs em tempo real
```bash
cd /opt/iaze
docker-compose logs -f
```

### Reiniciar serviços
```bash
cd /opt/iaze
docker-compose restart
```

### Parar tudo
```bash
cd /opt/iaze
docker-compose down
```

### Atualizar código
```bash
cd /opt/iaze
git pull  # Se usar Git
docker-compose restart backend frontend
```

### Backup do MongoDB
```bash
docker exec iaze_mongodb mongodump --db support_chat --out /backup
docker cp iaze_mongodb:/backup ./mongodb_backup_$(date +%Y%m%d)
```

---

## ⚙️ CONFIGURAÇÕES IMPORTANTES

### Editar .env
```bash
nano /opt/iaze/.env
```

**Variáveis principais:**
- `JWT_SECRET` - Chave secreta JWT (mude para algo único)
- `EVOLUTION_API_URL` - URL da API do Evolution
- `EVOLUTION_API_KEY` - Chave da API do Evolution

### Renovar SSL Automaticamente
```bash
# Adicionar ao crontab
crontab -e

# Adicionar linha:
0 3 * * * certbot renew --quiet --post-hook "docker restart iaze_nginx"
```

---

## 📊 MONITORAMENTO

### Verificar uso de recursos
```bash
docker stats
```

### Verificar espaço em disco
```bash
df -h
```

### Verificar logs de erro
```bash
docker-compose logs backend | grep ERROR
docker-compose logs frontend | grep ERROR
```

---

## 🚨 TROUBLESHOOTING

### Backend não inicia
```bash
docker-compose logs backend
# Verificar erros de conexão com MongoDB
```

### Frontend não carrega
```bash
docker-compose logs frontend
# Verificar se REACT_APP_BACKEND_URL está correto
```

### SSL não funciona
```bash
# Verificar certificados
ls -la /opt/iaze/ssl/
# Devem existir: fullchain.pem e privkey.pem
```

### MongoDB sem dados
```bash
# Re-importar backup
docker exec -i iaze_mongodb mongorestore --db support_chat /docker-entrypoint-initdb.d/support_chat --drop
```

---

## ✅ CHECKLIST FINAL

- [ ] Docker instalado
- [ ] Docker Compose instalado
- [ ] Certificados SSL gerados
- [ ] Backup MongoDB restaurado
- [ ] DNS configurado (198.96.94.106)
- [ ] Firewall configurado
- [ ] Todos containers rodando (docker-compose ps)
- [ ] https://suporte.help acessível
- [ ] Login funcionando
- [ ] SSL válido (cadeado verde)

---

## 🎯 VANTAGENS DO SERVIDOR DEDICADO

✅ **10-20x MAIS RÁPIDO** (recursos dedicados)
✅ **Sem limites** de CPU/RAM/Disco
✅ **Controle total** sobre configuração
✅ **Escalável** quando precisar
✅ **Sem custos mensais** de plataforma
✅ **Performance previsível** e estável

---

## 📞 SUPORTE

Se tiver problemas:
1. Verificar logs: `docker-compose logs -f`
2. Reiniciar serviços: `docker-compose restart`
3. Verificar portas: `netstat -tulpn | grep -E '80|443|3000|8001|27017'`

**Sistema estará MUITO mais rápido após migração!** 🚀
