# 🌐 Sincronização de Atualizações entre Servidores

## ✅ Atualizações Aplicadas

### Servidor LOCAL (Emergent - deploy-wizard-38):
- ✅ Mensagens instantâneas (ClientChat.js)
- ✅ Health Monitor Service
- ✅ Auto-recovery de storage externo
- ✅ Logs automáticos

### Servidor EXTERNO (198.96.94.106):
- ✅ Mensagens instantâneas (ClientChat.js) - SINCRONIZADO
- ✅ Health Monitor Service - SINCRONIZADO  
- ✅ Auto-recovery de storage externo - SINCRONIZADO
- ✅ Configurações .env - SINCRONIZADO

---

## 📊 Arquitetura dos Servidores

### SERVIDOR LOCAL (Emergent):
```
Local: deploy-wizard-38.preview.emergentagent.com
- MongoDB: localhost:27017
- Backend: :8001
- Frontend: :3000
- Dados: Mensagens, tickets, clientes, atendentes
```

### SERVIDOR EXTERNO (198.96.94.106):
```
Externo: 198.96.94.106
- MongoDB: localhost:27017 (independente)
- Backend: :8001
- Frontend: :3000
- Storage: :9000 (nginx para arquivos)
- Dados: Mensagens, tickets, clientes, atendentes (SEPARADOS do local)
```

**IMPORTANTE:** São dois sistemas INDEPENDENTES rodando em paralelo!

---

## 🔄 Script de Sincronização Automática

Foi criado um script que sincroniza automaticamente todas as atualizações:

### Localização:
- Local: `/tmp/sync_updates.sh`

### O que sincroniza:
1. ✅ health_monitor_service.py
2. ✅ server.py atualizado
3. ✅ ClientChat.js com mensagens instantâneas
4. ✅ Configurações .env
5. ✅ Guia de monitoramento

### Como executar:
```bash
# No servidor LOCAL
bash /tmp/sync_updates.sh
```

---

## 📝 Verificar Status dos Servidores

### SERVIDOR LOCAL:
```bash
# Status do Health Monitor
curl https://wppconnect-fix.preview.emergentagent.com/api/storage-status

# Health check geral
curl https://wppconnect-fix.preview.emergentagent.com/api/health

# Logs do Health Monitor
tail -f /var/log/health_monitor.log
```

### SERVIDOR EXTERNO:
```bash
# Conectar via SSH
ssh root@198.96.94.106

# Ver containers rodando
docker ps

# Ver logs do backend
docker logs iaze_backend --tail 50

# Ver logs do Health Monitor (dentro do container)
docker exec iaze_backend tail -f /var/log/health_monitor.log

# Reiniciar containers
docker restart iaze_backend iaze_frontend
```

---

## 🔐 Credenciais

### Servidor Externo:
- **Host**: 198.96.94.106
- **User**: root
- **Pass**: 102030a

---

## ⚙️ Configurações Aplicadas

### Ambos os servidores agora têm:

**1. Health Monitor Configuration (.env):**
```bash
HEALTH_CHECK_INTERVAL="60"       # Verifica a cada 60s
HEALTH_CHECK_TIMEOUT="5"         # Timeout de 5s
HEALTH_MAX_FAILURES="3"          # Fallback após 3 falhas
```

**2. Features:**
- ✅ Mensagens instantâneas no ClientChat
- ✅ Auto-recovery de storage
- ✅ Monitoramento automático
- ✅ Logs detalhados

---

## 🚀 Próximos Passos

### Para manter sincronizado no futuro:

1. **Sempre que fizer mudanças no LOCAL**, execute:
```bash
bash /tmp/sync_updates.sh
```

2. **Ou crie um cron job** para sincronizar automaticamente:
```bash
# Adicionar ao crontab (sincroniza a cada 6 horas)
0 */6 * * * /tmp/sync_updates.sh >> /var/log/sync_updates.log 2>&1
```

---

## 📊 Monitoramento

### Ver status em tempo real:

**Servidor LOCAL:**
```bash
watch -n 2 'curl -s https://wppconnect-fix.preview.emergentagent.com/api/storage-status | python3 -m json.tool'
```

**Servidor EXTERNO:**
```bash
ssh root@198.96.94.106 "watch -n 2 'docker exec iaze_backend curl -s http://localhost:8001/api/storage-status 2>/dev/null | python3 -m json.tool'"
```

---

## ✅ Checklist de Sincronização

- [x] health_monitor_service.py copiado
- [x] server.py atualizado
- [x] ClientChat.js com mensagens instantâneas
- [x] Configurações .env atualizadas
- [x] Containers reiniciados
- [x] Ambos os servidores rodando

---

## 🎉 Resultado

**Ambos os servidores agora têm:**
- ✅ Sistema de auto-recovery
- ✅ Mensagens instantâneas
- ✅ Monitoramento automático
- ✅ Logs detalhados
- ✅ Alta disponibilidade

**Os sistemas funcionam de forma INDEPENDENTE mas com as MESMAS FEATURES!**
