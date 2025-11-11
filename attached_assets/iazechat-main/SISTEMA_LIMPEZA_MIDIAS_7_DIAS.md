# ✅ Sistema de Limpeza Automática de Mídias - 7 Dias

## 🎯 **Objetivo**

Manter fotos, vídeos e áudios salvos por **7 dias** após o recebimento. Após esse período, são automaticamente deletados para economizar espaço em disco.

---

## 📊 **Como Funciona**

### **Ciclo de Vida de uma Mídia**:

```
Dia 0: Cliente envia foto/vídeo/áudio
   ↓
Dias 1-7: Mídia disponível no chat
   ↓
Dia 7: Sistema verifica mídias antigas
   ↓
Dia 7+: Arquivo deletado do servidor
   ↓
Chat mostra: "📷 Mídia expirada (7 dias)"
```

---

## 🔧 **Componentes do Sistema**

### 1. **Script de Limpeza**: `/app/cleanup_old_media.py`

**Funções**:
- ✅ Busca mensagens com mídia criadas há mais de 7 dias
- ✅ Deleta arquivos físicos do disco
- ✅ Marca mensagens como `media_expired: true`
- ✅ Remove `file_url` (arquivo não existe mais)
- ✅ Limpa arquivos órfãos (sem referência no banco)

**Configuração**:
```python
UPLOADS_DIR = Path('/data/uploads')  # Diretório persistente
DAYS_TO_KEEP = 7  # 7 dias de retenção
```

### 2. **Agendamento Automático**: `/etc/supervisor/conf.d/media-cleanup.conf`

**Execução**: A cada **24 horas** (diária)

**Supervisor Config**:
```ini
[program:media-cleanup-daily]
command=/bin/bash -c "while true; do sleep 86400; cd /app && python3 cleanup_old_media.py; done"
autostart=true
autorestart=true
```

### 3. **Frontend - Exibição de Mídia Expirada**

**Arquivos**: 
- `/app/frontend/src/pages/AgentDashboard.js`
- `/app/frontend/src/pages/ClientChat.js`

**Lógica**:
```javascript
{msg.media_expired ? (
  <div className="flex items-center gap-2 p-3 bg-gray-100 rounded-lg text-gray-500 text-sm">
    <span>📷</span>
    <span>Mídia expirada (7 dias)</span>
  </div>
) : (
  // Mostrar mídia normalmente
)}
```

---

## 📅 **Logs e Monitoramento**

### **Ver Logs do Cleanup**:
```bash
tail -f /var/log/supervisor/media-cleanup.log
```

### **Executar Manualmente** (teste):
```bash
cd /app
python3 cleanup_old_media.py
```

### **Saída Esperada**:
```
🚀 INICIANDO LIMPEZA AUTOMÁTICA DE MÍDIAS

🧹 Iniciando limpeza de mídias antigas...
📅 Data limite: 2025-10-18 20:33:50
📊 Encontradas 5 mensagens com mídia antiga

🗑️  Deletado: abc123.jpg (234.56 KB)
🗑️  Deletado: xyz789.mp4 (1.23 MB)
...

============================================================
📊 RESUMO DA LIMPEZA
============================================================
🗑️  Arquivos deletados: 5
💾 Espaço liberado: 12.34 MB
📝 Mensagens atualizadas: 5
❌ Erros: 0
============================================================
```

---

## 🧪 **Como Testar**

### **Teste 1: Criar Mídia Antiga** (forçar data)

```bash
mongosh mongodb://localhost:27017/support_chat --eval '
db.messages.updateOne(
  {kind: "image", file_url: {$exists: true}},
  {$set: {created_at: new Date("2025-10-10").toISOString()}}
)
'
```

### **Teste 2: Executar Cleanup**

```bash
cd /app && python3 cleanup_old_media.py
```

### **Teste 3: Verificar no Chat**

- Abra o chat que tinha a mídia
- Deve mostrar: **"📷 Mídia expirada (7 dias)"**

---

## 🔍 **Verificações**

### **1. Status do Serviço**:
```bash
sudo supervisorctl status media-cleanup-daily
```

**Esperado**: `RUNNING`

### **2. Quantas Mídias no Banco**:
```bash
mongosh mongodb://localhost:27017/support_chat --quiet --eval '
db.messages.countDocuments({kind: {$in: ["audio", "image", "video"]}})
'
```

### **3. Quantas Mídias Expiradas**:
```bash
mongosh mongodb://localhost:27017/support_chat --quiet --eval '
db.messages.countDocuments({media_expired: true})
'
```

### **4. Arquivos no Disco**:
```bash
ls -1 /data/uploads | wc -l
```

---

## ⚙️ **Configurações Personalizadas**

### **Alterar Período de Retenção**:

Edite `/app/cleanup_old_media.py`:
```python
DAYS_TO_KEEP = 14  # Manter por 14 dias em vez de 7
```

Reinicie o serviço:
```bash
sudo supervisorctl restart media-cleanup-daily
```

### **Alterar Frequência de Limpeza**:

Edite `/etc/supervisor/conf.d/media-cleanup.conf`:
```ini
# Executar a cada 12 horas (43200 segundos)
command=/bin/bash -c "while true; do sleep 43200; cd /app && python3 cleanup_old_media.py; done"
```

Recarregar:
```bash
sudo supervisorctl reread
sudo supervisorctl update
```

---

## 🎯 **Benefícios**

| Aspecto | Benefício |
|---------|-----------|
| **Espaço em Disco** | Economia automática de storage |
| **Performance** | Menos arquivos = backup mais rápido |
| **Conformidade** | LGPD/GDPR (dados temporários) |
| **Manutenção** | Zero intervenção manual |
| **Transparência** | Cliente vê "Mídia expirada" claramente |

---

## 🚨 **Importante**

### **O Que É Deletado**:
- ✅ Arquivos de áudio (.mp3, .ogg, etc.)
- ✅ Imagens (.jpg, .png, .webp, etc.)
- ✅ Vídeos (.mp4, .webm, etc.)

### **O Que NÃO É Deletado**:
- ❌ Mensagens de texto (permanecem)
- ❌ Metadados das mensagens
- ❌ Histórico de conversas

### **Recuperação**:
⚠️ **Arquivos deletados NÃO podem ser recuperados**. É um processo irreversível.

---

## 📊 **Estatísticas**

### **Verificar Última Execução**:
```bash
tail -20 /var/log/supervisor/media-cleanup.log
```

### **Espaço Total Liberado** (última semana):
```bash
grep "Espaço total liberado" /var/log/supervisor/media-cleanup.log | tail -7
```

---

## ✅ **Checklist de Implementação**

- [x] Script `/app/cleanup_old_media.py` criado
- [x] Configuração do Supervisor criada
- [x] Serviço `media-cleanup-daily` rodando
- [x] Frontend mostra "Mídia expirada (7 dias)"
- [x] Diretório correto: `/data/uploads` (persistente)
- [x] Logs em `/var/log/supervisor/media-cleanup.log`
- [x] Execução automática a cada 24h

---

## 🎉 **Sistema Ativo e Funcionando!**

O sistema de limpeza automática está:
- ✅ **Rodando em background** (supervisor)
- ✅ **Executando diariamente** (24 em 24 horas)
- ✅ **Deletando mídias antigas** (7+ dias)
- ✅ **Liberando espaço** automaticamente
- ✅ **Marcando mensagens** como expiradas
- ✅ **Logs disponíveis** para auditoria

**Nenhuma ação manual necessária!** O sistema cuida de tudo automaticamente. 🚀

---

**Data de implementação**: 25/10/2025 20:40 UTC  
**Status**: ✅ Ativo e testado  
**Próxima execução**: Automática (a cada 24h)
