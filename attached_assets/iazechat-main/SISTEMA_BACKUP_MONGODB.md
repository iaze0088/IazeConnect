# 🔒 Sistema de Backup Automático do MongoDB - IAZE

## ✅ Configuração Atual

### 📦 Localização dos Backups
- **Diretório**: `/root/backups_iaze_mongodb/`
- **Retenção**: Últimos 10 backups
- **Formato**: `backup_YYYYMMDD_HHMMSS/`

### ⏰ Frequência
- **Automático**: A cada 6 horas
- **Sistema**: systemd timer
- **Primeira execução**: 10 minutos após o boot
- **Logs**: `/var/log/mongodb-backup.log`

### 📊 Backup Atual
```
- tickets: 275 documentos
- messages: 3.570 documentos
- agents: 2 documentos
- departments: 4 departamentos
- users: 343 usuários
- Total: ~5.443 documentos
```

## 🛠️ Comandos Úteis

### Verificar Status do Timer
```bash
systemctl status mongodb-backup.timer
systemctl list-timers mongodb-backup.timer
```

### Executar Backup Manual
```bash
/root/backup-mongodb.sh
```

### Restaurar Backup
```bash
# 1. Identificar backup mais recente
ls -lht /root/backups_iaze_mongodb/

# 2. Copiar para o container
docker cp /root/backups_iaze_mongodb/backup_YYYYMMDD_HHMMSS iaze_mongodb:/tmp/

# 3. Restaurar
docker exec iaze_mongodb mongorestore --db=iaze --drop /tmp/backup_YYYYMMDD_HHMMSS/iaze/
```

### Verificar Logs de Backup
```bash
tail -f /var/log/mongodb-backup.log
```

## 🚨 Procedimento de Recuperação de Emergência

### Se os dados sumirem (como aconteceu hoje):

1. **Verificar o MongoDB:**
   ```bash
   docker exec iaze_mongodb mongosh iaze --eval "db.getCollectionNames()"
   ```

2. **Identificar o backup mais recente:**
   ```bash
   ls -lht /root/backups_iaze_mongodb/ | head -5
   ```

3. **Restaurar:**
   ```bash
   docker cp /root/backups_iaze_mongodb/backup_MAIS_RECENTE iaze_mongodb:/tmp/
   docker exec iaze_mongodb mongorestore --db=iaze --drop /tmp/backup_MAIS_RECENTE/iaze/
   ```

4. **Verificar restauração:**
   ```bash
   docker exec iaze_mongodb mongosh iaze --eval "
   print('tickets:', db.tickets.countDocuments());
   print('messages:', db.messages.countDocuments());
   print('agents:', db.agents.countDocuments());
   print('departments:', db.departments.countDocuments());
   print('users:', db.users.countDocuments());
   "
   ```

## 📝 Histórico de Recuperação

### 03/11/2025 - 16:00 UTC
- **Problema**: Database `iaze` vazio (todas coleções perdidas)
- **Causa**: Desconhecida (investigar)
- **Solução**: Restaurado do backup `backup_20251102_123143`
- **Resultado**: ✅ 5.443 documentos restaurados com sucesso
- **Tempo de recuperação**: ~2 minutos

## ⚠️ Recomendações Futuras

1. **Backup em Nuvem**:
   - Implementar sync com S3/Backblaze
   - Manter cópias off-site

2. **Monitoramento**:
   - Alertas se backup falhar
   - Verificação diária da integridade

3. **Documentação**:
   - Procedimentos de disaster recovery
   - Contatos de emergência

4. **Testes**:
   - Testar restauração mensalmente
   - Validar integridade dos backups

## 📞 Em Caso de Emergência

1. ✅ Verificar se há backup disponível
2. ✅ Restaurar do backup mais recente
3. ✅ Validar dados críticos
4. ✅ Informar usuários se necessário
5. ✅ Investigar causa raiz

---

**Última atualização**: 03/11/2025
**Responsável**: Sistema Automático
**Status**: ✅ Operacional
