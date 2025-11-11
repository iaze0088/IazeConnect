# MIGRATION GUIDE: Evolution API v1.8.7 → v2.3.6

## 📋 RESUMO DAS MUDANÇAS

### Breaking Changes Identificados:

1. **IDs mudaram de Integer para UUID**
   - v1: `"id": 1234`
   - v2: `"id": "550e8400-e29b-41d4-a716-446655440000"`

2. **Estrutura de Webhooks Modificada**
   - Payloads podem ter campos diferentes
   - Eventos podem ter nomes diferentes
   - Mais confiável, menos duplicações

3. **Endpoints da API podem ter mudado**
   - Verificar documentação v2 para novos endpoints

## 🔧 MUDANÇAS NECESSÁRIAS NO CÓDIGO

### 1. whatsapp_service.py

#### Endpoints que precisam ser verificados/atualizados:
- `POST /instance/create` → Verificar se mudou
- `GET /instance/connect/{instance_name}` → Verificar se mudou  
- `GET /instance/fetchInstances` → Verificar se mudou
- `DELETE /instance/delete/{instance_name}` → Verificar se mudou
- `GET /instance/connectionState/{instance_name}` → Verificar se mudou

#### Mudanças necessárias:
```python
# ANTES (v1.8.7):
check_response = await client.get(
    f"{EVOLUTION_API_URL}/instance/fetchInstances",
    headers={"apikey": EVOLUTION_API_KEY}
)

# DEPOIS (v2.3.6) - Verificar se endpoint mudou:
# Pode ser /v2/instance/list ou similar
check_response = await client.get(
    f"{EVOLUTION_API_URL}/instance/fetchInstances",  # Ou novo endpoint v2
    headers={"apikey": EVOLUTION_API_KEY}
)
```

### 2. whatsapp_routes.py - Webhook Handler

#### process_evolution_message()
```python
# MUDANÇA PRINCIPAL: IDs podem vir como UUID agora

# Verificar estrutura do payload v2:
# - message_data.get("key", {})
# - message_data.get("message", {})
# - Campos adicionais ou removidos?

# ANTES:
# Pode ter campos específicos v1

# DEPOIS:
# Precisamos adaptar para novos campos v2
# Exemplo: verificar se "pushName" ainda existe ou mudou para "push_name"
```

### 3. whatsapp_models.py

#### Verificar se modelos precisam de ajustes:
```python
class WhatsAppConnection(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    # Garantir que todos os IDs sejam strings UUID
```

## 📝 PASSOS DE MIGRAÇÃO

### Fase 1: Upgrade Docker (CONCLUÍDO ✅)
- [x] Backup completo criado
- [x] docker-compose.evolution.yml atualizado para v2.3.6
- [ ] Executar upgrade no servidor

### Fase 2: Testes de Endpoints
- [ ] Testar POST /instance/create
- [ ] Testar GET /instance/connect/{name}
- [ ] Testar GET /instance/fetchInstances
- [ ] Testar DELETE /instance/delete/{name}
- [ ] Testar webhook payload structure

### Fase 3: Adaptação do Código
- [ ] Atualizar whatsapp_service.py se necessário
- [ ] Atualizar whatsapp_routes.py para novos payloads
- [ ] Atualizar logs e debug info
- [ ] Garantir compatibilidade com UUIDs

### Fase 4: Validação
- [ ] Criar instância de teste
- [ ] Verificar QR code gerado
- [ ] Conectar WhatsApp de teste
- [ ] Enviar mensagem e verificar webhook
- [ ] Confirmar ticket criado no dashboard

## 🚨 PONTOS DE ATENÇÃO

1. **Webhooks v2 são mais confiáveis** - Devem resolver problemas de mensagens não chegando
2. **UUIDs** - Todos os IDs agora são UUIDs, não integers
3. **Payload structure** - Pode ter campos novos ou removidos
4. **Retry logic** - v2 tem melhor lógica de retry
5. **Event types** - Verificar se nomes de eventos mudaram

## 📚 REFERÊNCIAS

- Evolution API v2 Documentation: https://doc.evolution-api.com/v2/en/
- Migration Guide: https://doc.evolution-api.com/v2/en/updates
- Breaking Changes: Webhooks agora usam UUIDs e estrutura modificada

## ✅ STATUS ATUAL

- [x] Backup completo criado em: `/app/backups/evolution_upgrade_20251024_172711/`
- [x] docker-compose.yml atualizado para v2.3.6
- [x] Script de upgrade criado: `/app/upgrade_evolution_api.sh`
- [ ] Upgrade executado no servidor
- [ ] Testes de endpoints v2
- [ ] Código backend adaptado
- [ ] Validação completa
