# 🏥 Sistema de Monitoramento Automático e Auto-Recuperação

## ✅ O que foi implementado?

Um sistema completo de **auto-healing** que monitora a saúde do servidor externo de armazenamento e faz correções automáticas.

### Funcionalidades:

1. **Monitoramento Contínuo**: Verifica a cada 60 segundos se o servidor externo está funcionando
2. **Auto-Fallback**: Se o servidor externo falhar 3 vezes consecutivas, troca automaticamente para armazenamento local
3. **Auto-Recovery**: Quando o servidor externo voltar e estiver estável por 3 checks consecutivos, volta automaticamente para ele
4. **Logs Detalhados**: Registra todas as ações em `/var/log/health_monitor.log`

---

## 📊 Como Acompanhar o Status

### 1. Via Logs em Tempo Real

```bash
# Ver logs do Health Monitor
tail -f /var/log/health_monitor.log

# Ver últimas 50 linhas
tail -n 50 /var/log/health_monitor.log
```

### 2. Via API

```bash
# Status completo do sistema de armazenamento
curl https://wppconnect-fix.preview.emergentagent.com/api/storage-status

# Health check geral
curl https://wppconnect-fix.preview.emergentagent.com/api/health
```

**Exemplo de resposta do `/api/storage-status`:**
```json
{
  "current_mode": "local",
  "external_server": {
    "host": "198.96.94.106",
    "port": "9000",
    "url": "http://198.96.94.106:9000/health"
  },
  "monitor": {
    "is_running": true,
    "check_interval": 60,
    "consecutive_failures": 1,
    "consecutive_successes": 0,
    "max_failures": 3,
    "last_check": "2025-10-31T14:35:53.123456+00:00"
  }
}
```

---

## ⚙️ Configurações (arquivo .env)

```bash
# Intervalo entre cada verificação (em segundos)
HEALTH_CHECK_INTERVAL="60"

# Timeout para cada verificação (em segundos)
HEALTH_CHECK_TIMEOUT="5"

# Quantas falhas consecutivas antes de fazer fallback
HEALTH_MAX_FAILURES="3"
```

### Ajustar Configurações:

1. Editar `/app/backend/.env`
2. Modificar os valores conforme necessário
3. Reiniciar backend: `sudo supervisorctl restart backend`

**Exemplo de configurações mais agressivas:**
```bash
HEALTH_CHECK_INTERVAL="30"    # Verifica a cada 30s
HEALTH_CHECK_TIMEOUT="3"      # Timeout de 3s
HEALTH_MAX_FAILURES="2"       # Fallback após 2 falhas
```

---

## 🔄 Como Funciona

### Cenário 1: Servidor Externo Cai

```
1. Health Monitor detecta falha (tentativa 1/3)
2. Aguarda 60 segundos
3. Detecta falha novamente (tentativa 2/3)
4. Aguarda 60 segundos
5. Detecta falha pela terceira vez (tentativa 3/3)
6. 🚨 AÇÃO AUTOMÁTICA: Troca para armazenamento LOCAL
7. Logs registram: "AUTO-FALLBACK COMPLETO"
8. Continua monitorando para detectar quando servidor voltar
```

### Cenário 2: Servidor Externo Volta

```
1. Health Monitor detecta que servidor voltou (check 1/3 OK)
2. Aguarda 60 segundos
3. Confirma que está estável (check 2/3 OK)
4. Aguarda 60 segundos
5. Confirma que está estável (check 3/3 OK)
6. 🎉 AÇÃO AUTOMÁTICA: Troca para armazenamento EXTERNO
7. Logs registram: "AUTO-RECOVERY COMPLETO"
```

---

## 📝 Exemplos de Logs

### Quando servidor externo está offline:
```
2025-10-31 14:35:20 [ERROR] ❌ External Storage: CONNECTION ERROR
2025-10-31 14:35:20 [WARNING] ⚠️ Falha 1/3
2025-10-31 14:36:20 [ERROR] ❌ External Storage: CONNECTION ERROR
2025-10-31 14:36:20 [WARNING] ⚠️ Falha 2/3
2025-10-31 14:37:20 [ERROR] ❌ External Storage: CONNECTION ERROR
2025-10-31 14:37:20 [WARNING] ⚠️ Falha 3/3
2025-10-31 14:37:20 [ERROR] 🚨 SERVIDOR EXTERNO INDISPONÍVEL!
2025-10-31 14:37:20 [INFO] 🔄 Iniciando AUTO-FALLBACK para local storage...
2025-10-31 14:37:20 [INFO] ✅ AUTO-FALLBACK COMPLETO
```

### Quando servidor externo volta:
```
2025-10-31 15:00:00 [INFO] ✅ External Storage: HEALTHY (response time: 0.15s)
2025-10-31 15:01:00 [INFO] ✅ External Storage: HEALTHY (response time: 0.12s)
2025-10-31 15:02:00 [INFO] ✅ External Storage: HEALTHY (response time: 0.18s)
2025-10-31 15:02:00 [INFO] 🎉 Servidor externo RECUPERADO e ESTÁVEL!
2025-10-31 15:02:00 [INFO] 🔄 Iniciando AUTO-RECOVERY para external storage...
2025-10-31 15:02:00 [INFO] ✅ AUTO-RECOVERY COMPLETO
```

---

## 🛠️ Comandos Úteis

### Verificar se Health Monitor está rodando:
```bash
ps aux | grep health_monitor
```

### Ver logs em tempo real:
```bash
tail -f /var/log/health_monitor.log
```

### Forçar troca manual para LOCAL (se necessário):
```bash
# Editar .env
nano /app/backend/.env
# Mudar: USE_EXTERNAL_STORAGE="false"
# Reiniciar
sudo supervisorctl restart backend
```

### Forçar troca manual para EXTERNO (se necessário):
```bash
# Editar .env
nano /app/backend/.env
# Mudar: USE_EXTERNAL_STORAGE="true"
# Reiniciar
sudo supervisorctl restart backend
```

---

## 🎯 Status Atual

✅ **Health Monitor**: ATIVO
✅ **Modo Atual**: LOCAL (servidor externo offline)
✅ **Monitoramento**: A cada 60 segundos
✅ **Auto-Recovery**: ATIVO (reconectará automaticamente quando servidor voltar)

---

## 📞 Próximos Passos

1. ✅ **Sistema funcionando localmente** - sem lentidão
2. ⏳ **Aguardando servidor externo voltar** - sistema reconectará automaticamente
3. 📊 **Monitorar logs** - acompanhe em tempo real o que está acontecendo

**O sistema está completamente automatizado e auto-suficiente!** 🚀
