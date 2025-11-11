# 🔄 Guia de Sincronização: Emergent → Servidor Externo

## 📋 Visão Geral

Este guia explica como sincronizar automaticamente as atualizações feitas na **Emergent** para o **seu servidor externo (198.96.94.106)**.

---

## 🎯 Fluxo de Trabalho

```
1. Desenvolvimento/Testes → Emergent (recovery-hub-13.preview.emergentagent.com)
2. Exportação → API de Download
3. Sincronização → Servidor Externo (198.96.94.106)
4. Produção → Sistema funcionando
```

---

## ⚙️ Configuração Inicial (Execute 1x)

### No Servidor Externo (198.96.94.106):

```bash
# 1. Baixar script de sincronização
curl -o /root/sync_iaze.sh https://wppconnect-fix.preview.emergentagent.com/api/download/sync-script

# 2. Tornar executável
chmod +x /root/sync_iaze.sh

# 3. Testar primeira sincronização
/root/sync_iaze.sh
```

---

## 🚀 Como Usar

### Sincronização Manual

Sempre que houver atualizações na Emergent, execute no seu servidor:

```bash
/root/sync_iaze.sh
```

### Sincronização Automática (Recomendado)

Configure um cron job para sincronizar diariamente:

```bash
# Editar crontab
crontab -e

# Adicionar esta linha (sincroniza todos os dias às 3h da manhã)
0 3 * * * /root/sync_iaze.sh >> /var/log/iaze_sync.log 2>&1
```

---

## 📊 Verificar Status da Sincronização

### Ver logs

```bash
tail -f /var/log/iaze_sync.log
```

### Verificar última sincronização

```bash
ls -lth /opt/iaze/backend/server.py.backup_* | head -5
```

### Testar se sistema está funcionando

```bash
curl http://localhost:8001/api/health
```

---

## 🔧 Endpoints Disponíveis

| Endpoint | Descrição |
|----------|-----------|
| `/api/export/status` | Status do sistema de exportação |
| `/api/download/server.py` | Baixar server.py atualizado |
| `/api/download/sync-script` | Baixar script de sincronização |
| `/api/health` | Verificar saúde do backend |

---

## 🛡️ Segurança e Backup

### Proteção Automática

- ✅ Backup automático antes de cada sincronização
- ✅ Arquivo `server.py` protegido contra sobrescritas acidentais (chmod 444)
- ✅ Rollback automático em caso de falha
- ✅ Logs detalhados de todas as operações

### Backups Disponíveis

```bash
# Listar todos os backups
ls -lh /opt/iaze/backend/server.py.backup_*

# Restaurar backup específico
chmod 644 /opt/iaze/backend/server.py
cp /opt/iaze/backend/server.py.backup_YYYYMMDD_HHMMSS /opt/iaze/backend/server.py
chmod 444 /opt/iaze/backend/server.py
cd /opt/iaze && docker-compose restart backend
```

---

## 🔍 Troubleshooting

### Problema: "Não foi possível conectar à Emergent"

```bash
# Verificar conectividade
curl -I https://wppconnect-fix.preview.emergentagent.com/api/export/status

# Se não conectar, verificar firewall/DNS
ping recovery-hub-13.preview.emergentagent.com
```

### Problema: "Backend não responde após sincronização"

```bash
# Ver logs do backend
cd /opt/iaze
docker-compose logs --tail=50 backend

# Restaurar backup anterior
chmod 644 /opt/iaze/backend/server.py
cp /opt/iaze/backend/server.py.backup_* /opt/iaze/backend/server.py  # usar o mais recente
chmod 444 /opt/iaze/backend/server.py
docker-compose restart backend
```

### Problema: "Permissão negada"

```bash
# Remover proteção temporariamente
chmod 644 /opt/iaze/backend/server.py

# Após modificação, proteger novamente
chmod 444 /opt/iaze/backend/server.py
```

---

## 📝 Checklist de Sincronização

Antes de sincronizar:

- [ ] ✅ Emergent está acessível
- [ ] ✅ Backup manual foi feito (opcional, mas recomendado)
- [ ] ✅ Nenhum usuário ativo no sistema (opcional)

Após sincronização:

- [ ] ✅ Backend reiniciou sem erros
- [ ] ✅ `/api/health` responde corretamente
- [ ] ✅ Login do admin funciona
- [ ] ✅ Dashboards acessíveis

---

## 🎯 Comandos Rápidos

```bash
# Sincronizar agora
/root/sync_iaze.sh

# Ver status
curl http://localhost:8001/api/health

# Ver logs de sincronização
tail -f /var/log/iaze_sync.log

# Verificar última modificação do server.py
ls -lh /opt/iaze/backend/server.py

# Listar backups disponíveis
ls -lth /opt/iaze/backend/server.py.backup_* | head -5
```

---

## 📞 Suporte

- **Emergent URL**: https://wppconnect-fix.preview.emergentagent.com
- **Status da API**: https://wppconnect-fix.preview.emergentagent.com/api/export/status
- **Logs**: `/var/log/iaze_sync.log`

---

## ✅ Sistema Configurado

✅ API de exportação ativa na Emergent  
✅ Script de sincronização criado  
✅ Proteção automática de arquivos  
✅ Backup automático  
✅ Rollback em caso de falha  
✅ Logs detalhados  

**Pronto para uso!** 🚀
