# 🚀 Guia Rápido - Atualizar Servidor Externo

## 📋 Resumo das Novas Funcionalidades

Este guia explica como sincronizar as últimas funcionalidades desenvolvidas no Emergent para o servidor externo (198.96.94.106 / suporte.help).

### ✨ Funcionalidades Incluídas:

1. **AI Auto-Search Credentials** - IA busca automaticamente credenciais em Office/gestor.my quando cliente pergunta
2. **Agendamento de Mensagens** - Agentes podem agendar envio de mensagens futuras
3. **Lembretes por Email** - Sistema automático de emails para credenciais expirando
4. **Office Integration (Playwright)** - Scraping robusto com suporte a múltiplas credenciais
5. **Prevent Duplicate Tests** - Cliente não pode gerar múltiplos testes no /vendas

---

## 🎯 Passo a Passo para Atualização

### 1️⃣ Acesse o Servidor Externo via SSH

```bash
ssh root@198.96.94.106
```

**Senha:** (use a senha que você já conhece)

---

### 2️⃣ Baixe o Script de Atualização

```bash
cd /root
wget -O atualizar_servidor_externo.sh https://wppconnect-fix.preview.emergentagent.com/ATUALIZAR_SERVIDOR_EXTERNO.sh
chmod +x atualizar_servidor_externo.sh
```

---

### 3️⃣ Execute o Script

```bash
./atualizar_servidor_externo.sh
```

O script irá:
- ✅ Criar backup automático dos arquivos atuais
- ✅ Baixar todos os arquivos novos e modificados do Emergent
- ✅ Verificar integridade dos arquivos
- ✅ Aplicar as atualizações
- ✅ Instalar dependências Python (playwright, beautifulsoup4)
- ✅ Reiniciar serviços (backend e frontend)
- ✅ Verificar logs para garantir que tudo está funcionando

---

### 4️⃣ Durante a Execução

O script pedirá confirmação em 2 momentos:

1. **Início:** Confirmar que deseja continuar com a atualização
2. **Após verificação:** Confirmar que deseja aplicar as mudanças

Responda `y` (yes) para ambos.

---

### 5️⃣ Após a Atualização

O script mostrará:
- ✅ Status dos serviços (backend e frontend devem estar RUNNING)
- ✅ Últimas linhas do log do backend
- ✅ Localização do backup (caso precise reverter)

---

## 🧪 Testes Recomendados

Após a atualização, teste as novas funcionalidades:

### 1. **AI Auto-Search Credentials**
- Acesse https://suporte.help
- Cliente WA SUPORTE pergunta: "qual meu usuário e senha?"
- IA deve buscar automaticamente em Office
- Credenciais aparecem no painel do agente

### 2. **Agendamento de Mensagens**
- Acesse painel do agente (https://suporte.help/agent)
- Abra uma conversa de cliente
- Clique no botão "Agendar" ao lado do campo de mensagem
- Configure data/hora futura
- Mensagem será enviada automaticamente no horário programado

### 3. **Email Reminder**
- Acesse admin dashboard (https://suporte.help/admin)
- Vá para a aba "Email"
- Configure SMTP (host, porta, usuário, senha)
- Configure timing dos lembretes (3, 2, 1 dias antes)
- Sistema enviará emails diariamente às 9h UTC

### 4. **Office Search**
- Admin Dashboard → aba "Office"
- Configure credenciais do gestor.my
- Agent Dashboard → botão "Office" → buscar por WhatsApp
- Deve retornar credenciais encontradas

### 5. **Prevent Duplicate Tests**
- Acesse https://suporte.help/vendas
- Cliente solicita teste
- Teste é gerado com sucesso
- Mesmo cliente solicita novamente → IA deve recusar

---

## 🔧 Arquivos Modificados/Criados

### Backend (NOVOS):
- `credential_auto_search.py` - Lógica de busca automática
- `credential_auto_search_routes.py` - Rotas da API
- `scheduled_messages_models.py` - Modelos de dados
- `scheduled_messages_routes.py` - Rotas da API
- `reminder_models.py` - Modelos de dados
- `reminder_service.py` - Serviço de email
- `reminder_routes.py` - Rotas da API

### Backend (MODIFICADOS):
- `server.py` - Integração das novas rotas
- `vendas_ai_service.py` - Function calling + prevent duplicate
- `vendas_routes.py` - Verificação de testes
- `office_service.py` - Playwright scraping
- `office_routes.py` - Limpeza de código
- `backup_scheduler.py` - Scheduled tasks
- `requirements.txt` - Novas dependências

### Frontend (NOVOS):
- `components/ScheduleMessageModal.js` - Modal de agendamento
- `components/EmailManager.js` - Gerenciador de email

### Frontend (MODIFICADOS):
- `pages/AgentDashboard.js` - Botão agendar + credenciais auto
- `pages/AdminDashboard.js` - Aba Email
- `pages/VendasChatNew.js` - Melhorias UI

---

## 🔄 Reverter Atualização (se necessário)

Se algo der errado, você pode reverter para a versão anterior:

```bash
# O script cria backup em: /opt/iaze/backup_new_features_YYYYMMDD_HHMMSS
# Exemplo de rollback:
cp -r /opt/iaze/backup_new_features_20250131_143000/backend/* /opt/iaze/backend/
cp -r /opt/iaze/backup_new_features_20250131_143000/frontend/* /opt/iaze/frontend/
supervisorctl restart all
```

---

## 📞 Suporte

Em caso de problemas:

1. **Verificar logs do backend:**
   ```bash
   tail -f /var/log/supervisor/backend.err.log
   ```

2. **Verificar logs do frontend:**
   ```bash
   tail -f /var/log/supervisor/frontend.out.log
   ```

3. **Testar importação Python:**
   ```bash
   cd /opt/iaze/backend
   python3 -c 'import server'
   ```

4. **Verificar status dos serviços:**
   ```bash
   supervisorctl status
   ```

5. **Reiniciar serviços manualmente:**
   ```bash
   supervisorctl restart backend
   supervisorctl restart frontend
   ```

---

## ⏱️ Tempo Estimado

- Download e verificação: 2-3 minutos
- Instalação de dependências: 5-7 minutos (playwright browsers)
- Aplicação e reinício: 1-2 minutos
- **Total: ~10 minutos**

---

## ✅ Checklist Final

Após a atualização, verifique:

- [ ] Backend está RUNNING (`supervisorctl status backend`)
- [ ] Frontend está RUNNING (`supervisorctl status frontend`)
- [ ] Sem erros nos logs do backend
- [ ] Site https://suporte.help está acessível
- [ ] Login no admin funciona
- [ ] Login no agent funciona
- [ ] Aba "Email" aparece no admin dashboard
- [ ] Botão "Agendar" aparece no agent dashboard
- [ ] Botão "Office" aparece no agent dashboard

---

## 🎉 Pronto!

Todas as funcionalidades foram sincronizadas com sucesso. O sistema está pronto para uso em produção!
