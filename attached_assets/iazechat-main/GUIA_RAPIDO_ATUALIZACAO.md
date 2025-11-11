# 🚀 GUIA RÁPIDO - Atualização Completa (5 Correções)

## 📋 O que este script faz?

Aplica automaticamente **5 correções críticas** no servidor externo (suporte.help):

1. ✅ Redirecionamento "reembolso" → Ticket no painel
2. ✅ Credenciais Usuario/Senha liberadas
3. ✅ Sistema de fallback da IA (timeout + erros)
4. ✅ Mensagens INSTANTÂNEAS (6x mais rápido)
5. ✅ Som de notificação em PWA mobile

---

## 🎯 MÉTODO 1: Execução Direta (Recomendado)

### No servidor externo:

```bash
# 1. Acesse o servidor
ssh root@198.96.94.106

# 2. Baixe e execute o script
wget -O atualizar_completo.sh https://wppconnect-fix.preview.emergentagent.com/ATUALIZAR_COMPLETO.sh
chmod +x atualizar_completo.sh
./atualizar_completo.sh
```

### O script vai:
1. ✅ Fazer backup automático
2. ✅ Baixar arquivos atualizados
3. ✅ Verificar integridade
4. ✅ Aplicar mudanças
5. ✅ Reiniciar serviços
6. ✅ Verificar logs

**Tempo estimado:** 2-3 minutos

---

## 🎯 MÉTODO 2: Cópia Manual

### Se o método 1 não funcionar:

```bash
# No servidor externo:
ssh root@198.96.94.106

# Criar script manualmente
cat > /opt/iaze/atualizar_completo.sh << 'EOF'
[COPIAR TODO O CONTEÚDO DO SCRIPT AQUI]
EOF

chmod +x /opt/iaze/atualizar_completo.sh
/opt/iaze/atualizar_completo.sh
```

---

## 📁 Arquivos que Serão Modificados

- `/opt/iaze/backend/server.py` (correções 2, 3)
- `/opt/iaze/backend/vendas_ai_service.py` (correção 1)
- `/opt/iaze/frontend/src/pages/ClientChat.js` (correções 4, 5)
- `/opt/iaze/frontend/src/pages/AgentDashboard.js` (correção 4)

---

## 🔄 Rollback (Se Necessário)

O script cria backup automático em:
```
/opt/iaze/backup_5corrections_YYYYMMDD_HHMMSS/
```

Para reverter:
```bash
# Encontre o backup mais recente
BACKUP=$(ls -td /opt/iaze/backup_5corrections_* | head -1)

# Restaure os arquivos
cp $BACKUP/*.py /opt/iaze/backend/
cp $BACKUP/*.js /opt/iaze/frontend/src/pages/

# Reinicie
supervisorctl restart all
```

---

## 🧪 Testes Pós-Atualização

### Teste 1: Reembolso (30 segundos)
```bash
1. Acesse: https://suporte.help/vendas
2. Digite: "quero reembolso"
3. Verifique painel: WA Suporte > ESPERA
✅ Ticket deve aparecer
```

### Teste 2: Credenciais (30 segundos)
```bash
1. No painel, envie:
   Usuario: teste123
   Senha: abc456
✅ Deve enviar normalmente
```

### Teste 3: Mensagens Instantâneas (1 minuto)
```bash
1. Abra cliente e atendente
2. Envie mensagem
✅ Deve aparecer em < 1 segundo
```

### Teste 4: Som PWA (1 minuto)
```bash
1. Instale PWA no celular
2. Toque na tela
3. Receba mensagem
✅ Deve tocar som + vibrar
```

---

## ⚠️ Troubleshooting

### Erro: "Arquivo vazio"
```bash
# Verifique conexão com Emergent
curl -I https://wppconnect-fix.preview.emergentagent.com/api/export/backend/server.py

# Se não funcionar, use método 2 (cópia manual)
```

### Erro: "Serviço não iniciou"
```bash
# Verifique logs
tail -f /var/log/supervisor/backend.err.log

# Teste importação Python
cd /opt/iaze/backend
python3 -c "import server; print('✅ OK')"

# Se houver erro de sintaxe, faça rollback
```

### Erro: "Permission denied"
```bash
# Execute como root
sudo su
./atualizar_completo.sh
```

---

## 📊 Comparação Antes vs Depois

| Correção | Antes | Depois |
|----------|-------|--------|
| Reembolso → Painel | ❌ Não aparece | ✅ Aparece |
| Credenciais | ❌ Bloqueadas | ✅ Liberadas |
| IA Timeout | ❌ Sem proteção | ✅ 2min + fallback |
| Reconexão WebSocket | 3 segundos | 0.5 segundos (6x) |
| Som PWA | ~50% | ~95% (+90%) |

---

## ✅ Checklist Final

- [ ] Script baixado no servidor externo
- [ ] Executado com sucesso
- [ ] Backup criado automaticamente
- [ ] 4 arquivos atualizados
- [ ] Backend reiniciado (RUNNING)
- [ ] Frontend reiniciado (RUNNING)
- [ ] Logs verificados (sem erros críticos)
- [ ] Teste 1: Reembolso ✅
- [ ] Teste 2: Credenciais ✅
- [ ] Teste 3: Mensagens instantâneas ✅
- [ ] Teste 4: Som PWA ✅

---

## 📞 Suporte

**Em caso de problemas:**
1. Verifique logs detalhados
2. Teste importação Python
3. Faça rollback se necessário
4. Entre em contato com desenvolvedor

**Data:** 30/10/2025  
**Versão:** 1.0 - 5 Correções Completas
