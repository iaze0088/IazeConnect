# 🚀 GUIA COMPLETO: UPGRADE EVOLUTION API v1.8.7 → v2.3.6

## ✅ STATUS ATUAL

### O que já foi feito:
- ✅ **Backup completo criado** em `/app/backups/evolution_upgrade_20251024_172711/`
  - MongoDB com todos os dados
  - Arquivos de configuração (.env)
  - Código backend atual
  - Documentação

- ✅ **docker-compose.evolution.yml atualizado** para v2.3.6
- ✅ **Scripts criados:**
  - `/app/upgrade_evolution_api.sh` - Script de upgrade
  - `/app/test_evolution_v2_endpoints.sh` - Script de testes
  - `/app/backup_before_evolution_upgrade.sh` - Script de backup

---

## 📋 PRÓXIMOS PASSOS

### PASSO 1: Executar Upgrade no Servidor

**No servidor onde o Docker está rodando**, execute:

```bash
cd /app
./upgrade_evolution_api.sh
```

Este script irá:
1. Parar os containers atuais
2. Fazer pull da imagem v2.3.6
3. Iniciar a Evolution API v2.3.6
4. Mostrar logs para verificação

**Tempo estimado:** 2-3 minutos

---

### PASSO 2: Validar Evolution API v2.3.6

Após o upgrade, teste os endpoints:

```bash
cd /app
./test_evolution_v2_endpoints.sh
```

Este script irá testar:
- ✓ GET / (API Info)
- ✓ GET /instance/fetchInstances
- ✓ POST /instance/create
- ✓ GET /instance/connect (QR Code)
- ✓ DELETE /instance/delete

**Resultado esperado:** Todos os testes devem retornar HTTP 200/201 ✅

**Tempo estimado:** 1 minuto

---

### PASSO 3: Testar Criação de Instância pelo Frontend

1. **Acesse o painel admin** do CYBERTV Suporte
2. **Vá para WhatsApp Manager**
3. **Crie uma nova conexão WhatsApp**
4. **Verifique se o QR Code aparece**

**Resultado esperado:** 
- QR Code deve aparecer imediatamente
- Status deve mostrar "Aguardando conexão"

---

### PASSO 4: Conectar WhatsApp e Testar Mensagem

1. **Escaneie o QR Code** com seu WhatsApp
2. **Aguarde conexão** (status deve mudar para "Conectado")
3. **Envie uma mensagem de teste** para o número conectado
4. **Verifique no Dashboard do Agente** se a mensagem chegou

**Resultado esperado:**
- Status muda para "Conectado" ✅
- Mensagem aparece no dashboard do agente ✅
- Ticket é criado automaticamente ✅

---

## 🔍 DIFERENÇAS PRINCIPAIS v1.8.7 vs v2.3.6

| Aspecto | v1.8.7 | v2.3.6 |
|---------|--------|--------|
| **IDs** | Integers | UUIDs |
| **Webhooks** | Menos confiáveis | Mais confiáveis, menos duplicações |
| **Payload** | Estrutura v1 | Estrutura v2 (similar, mas melhorada) |
| **Retry Logic** | Básico | Melhorado |
| **Event Types** | Standard | + Novos eventos disponíveis |

---

## 🐛 TROUBLESHOOTING

### Problema: Evolution API não inicia

**Solução:**
```bash
# Ver logs detalhados
docker compose -f docker-compose.evolution.yml logs evolution-api

# Se necessário, limpar volumes e recriar
docker compose -f docker-compose.evolution.yml down -v
docker compose -f docker-compose.evolution.yml up -d
```

---

### Problema: QR Code não aparece

**Possíveis causas:**
1. Evolution API não está rodando
2. URL no backend está incorreta
3. API Key está incorreta

**Solução:**
```bash
# 1. Verificar se Evolution API está UP
docker compose -f docker-compose.evolution.yml ps

# 2. Verificar .env do backend
grep EVOLUTION /app/backend/.env

# 3. Testar endpoint diretamente
curl -H "apikey: cybertv-suporte-evolution-key-2024" \
  http://localhost:8080/
```

---

### Problema: Mensagens não chegam ao dashboard

**Na v2.3.6, os webhooks são mais confiáveis!**

**Verificar:**
```bash
# 1. Ver logs da Evolution API
docker compose -f docker-compose.evolution.yml logs -f evolution-api

# 2. Ver logs do backend
tail -f /var/log/supervisor/backend.out.log

# 3. Verificar se webhook está configurado
curl -H "apikey: cybertv-suporte-evolution-key-2024" \
  http://localhost:8080/instance/fetchInstances
```

---

## 📊 ENDPOINTS v2.3.6 (CONFIRMADOS)

### Endpoints principais (SEM MUDANÇAS):
✅ `POST /instance/create` - Criar instância
✅ `GET /instance/fetchInstances` - Listar instâncias  
✅ `GET /instance/connect/{name}` - Obter QR Code
✅ `DELETE /instance/delete/{name}` - Deletar instância
✅ `GET /instance/connectionState/{name}` - Status da conexão

### Estrutura de Webhook v2 (messages.upsert):
```json
{
  "event": "messages.upsert",
  "instance": "instance_name",
  "data": {
    "key": {
      "id": "message-uuid-here",
      "fromMe": false,
      "remoteJid": "5511999999999@s.whatsapp.net"
    },
    "message": {
      "conversation": "Texto da mensagem"
    },
    "pushName": "Nome do Contato"
  }
}
```

---

## 🔄 ROLLBACK (SE NECESSÁRIO)

Se algo der errado, você pode voltar para v1.8.7:

```bash
# 1. Parar v2.3.6
docker compose -f docker-compose.evolution.yml down

# 2. Restaurar docker-compose antigo
cp /app/backups/evolution_upgrade_20251024_172711/docker-compose.evolution.yml.bak \
   /app/docker-compose.evolution.yml

# 3. Restaurar dados MongoDB (se necessário)
mongorestore --uri="MONGO_URL" \
  /app/backups/evolution_upgrade_20251024_172711/mongodb_backup

# 4. Subir v1.8.7
docker compose -f docker-compose.evolution.yml up -d
```

---

## 📝 MUDANÇAS NO CÓDIGO BACKEND

**NENHUMA MUDANÇA NECESSÁRIA por enquanto!** 🎉

Os endpoints são os mesmos, e o código atual já está preparado para:
- ✅ Usar UUIDs (já usamos `str(uuid.uuid4())` em todo lugar)
- ✅ Processar webhooks no formato correto
- ✅ Lidar com payloads v2

**MAS** vamos adicionar logs melhores e tratamento de erros aprimorado na próxima etapa.

---

## ✨ BENEFÍCIOS DO UPGRADE

1. **Webhooks mais confiáveis** → Mensagens NÃO vão mais se perder! 🎯
2. **Menos duplicações** → Cada mensagem processada uma vez
3. **Melhor retry logic** → Se webhook falhar, Evolution v2 tenta novamente
4. **Status mais preciso** → Connection updates mais frequentes e precisos
5. **Base para futuro** → Suporte a novos eventos e features

---

## 🎯 PRÓXIMA ETAPA APÓS UPGRADE

Após confirmar que v2.3.6 está funcionando:

1. **Melhorar logs** no backend para debug mais fácil
2. **Adicionar testes automatizados** para webhooks
3. **Implementar monitoring** de saúde da Evolution API
4. **Documentar fluxo completo** de mensagens

---

## 📞 SUPORTE

Se encontrar problemas:
1. Verifique logs: `docker compose -f docker-compose.evolution.yml logs evolution-api`
2. Teste endpoints: `./test_evolution_v2_endpoints.sh`
3. Consulte backup: `/app/backups/evolution_upgrade_20251024_172711/BACKUP_INFO.txt`
4. Documentação oficial: https://doc.evolution-api.com/v2/

---

## ✅ CHECKLIST FINAL

- [ ] Backup verificado
- [ ] Upgrade executado com sucesso
- [ ] Todos os testes de endpoint passaram
- [ ] QR Code aparece no frontend
- [ ] WhatsApp conectado com sucesso
- [ ] Mensagem de teste chegou ao dashboard
- [ ] Status atualiza corretamente

**Quando todos os itens estiverem ✅, o upgrade está COMPLETO!**

---

*Última atualização: $(date)*
*Versão: Evolution API v2.3.6*
*Status: Pronto para executar* 🚀
