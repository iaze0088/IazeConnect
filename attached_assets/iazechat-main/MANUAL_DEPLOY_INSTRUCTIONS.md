# 📦 INSTRUÇÕES DE DEPLOY MANUAL - suporte.help/vendas

## ✅ Funcionalidades Implementadas

### 1. 🔒 Bloqueio de Campos após Criação de Teste
- **Problema resolvido**: Cliente não pode mais editar WhatsApp e PIN após criar o primeiro teste
- **Como funciona**:
  - Ao criar usuário pela primeira vez, os dados são salvos no `localStorage`
  - Na próxima vez que abrir o formulário, os campos aparecem **desabilitados**
  - Mostra aviso: "⚠️ Não é possível alterar o WhatsApp/PIN após criar teste"
  - Campos ficam com fundo cinza e cursor "not-allowed"
  - Persistência funciona mesmo após recarregar a página

### 2. 📋 Botões para Copiar Credenciais
- **Problema resolvido**: Cliente pode copiar facilmente usuário e senha
- **Como funciona**:
  - Detecta automaticamente mensagens com credenciais
  - Adiciona botões "📋 Copiar Usuário" e "📋 Copiar Senha"
  - Ao clicar, copia para clipboard e mostra "✅ Copiado!"
  - Feedback visual muda cor do botão por 2 segundos

---

## 🚀 OPÇÃO 1: Deploy Automático via SSH

Se você tem acesso SSH ao VPS, execute:

```bash
# No VPS (151.243.218.223)
cd /var/www/iaze/frontend
yarn build
supervisorctl restart iaze-frontend
```

---

## 🚀 OPÇÃO 2: Deploy Manual (SEM SSH)

### Passo 1: Baixar o build atualizado

O build já está pronto em: `/app/frontend/build/`

### Passo 2: Enviar para o VPS

Use SFTP, FileZilla ou painel de controle do VPS para:

1. Fazer backup do diretório atual:
   ```bash
   cd /var/www/iaze/frontend
   mv build build_backup_$(date +%Y%m%d_%H%M%S)
   ```

2. Enviar o novo build:
   - Origem: `/app/frontend/build/`
   - Destino: `/var/www/iaze/frontend/build/`

3. Atualizar também o arquivo fonte:
   - Origem: `/app/frontend/src/pages/VendasChatNew.js`
   - Destino: `/var/www/iaze/frontend/src/pages/VendasChatNew.js`

### Passo 3: Reiniciar serviço

No VPS, execute:

```bash
supervisorctl restart iaze-frontend
# OU
pm2 restart iaze-frontend
# OU (se usar nginx + serve)
systemctl restart nginx
```

### Passo 4: Limpar cache do navegador

Após o deploy, limpe o cache:
- Ctrl + Shift + Delete (Chrome/Firefox)
- Ou abrir em aba anônima

---

## 🧪 COMO TESTAR

### Teste 1: Bloqueio de Campos

1. Acesse `https://suporte.help/vendas`
2. Clique em um botão que abre formulário de criar usuário
3. Preencha:
   - Nome: Teste Fabio
   - WhatsApp: 19989612021
   - PIN: 11
4. Clique em "Criar Usuário"
5. ✅ **PRIMEIRA VEZ**: Campos devem estar editáveis
6. Feche e abra o formulário novamente
7. ✅ **SEGUNDA VEZ**: Campos WhatsApp e PIN devem estar **BLOQUEADOS**
8. Deve aparecer:
   - Tag "🔒 Bloqueado" ao lado dos labels
   - Campos com fundo cinza
   - Mensagem de aviso em vermelho
   - Cursor "not-allowed"

### Teste 2: Botões de Copiar

1. Após criar usuário, credenciais aparecem no chat
2. ✅ Devem aparecer 2 botões azuis:
   - "📋 Copiar Usuário"
   - "📋 Copiar Senha"
3. Clique em "Copiar Usuário"
4. ✅ Botão deve mudar para verde e mostrar "✅ Copiado!"
5. Cole em qualquer lugar (Ctrl+V)
6. ✅ Deve colar o nome de usuário correto
7. Repita para "Copiar Senha"

---

## 📁 ARQUIVOS MODIFICADOS

```
/app/frontend/src/pages/VendasChatNew.js
  ├── Linha 45-46: Estados hasCreatedUser e copiedField
  ├── Linha 80-95: useEffect para verificar localStorage
  ├── Linha 322-324: Marcar hasCreatedUser após criar
  ├── Linha 372-382: Função handleCopyCredential
  ├── Linha 790-808: Função extractCredentials
  ├── Linha 1029-1050: Campo WhatsApp com bloqueio
  ├── Linha 1048-1090: Campo PIN com bloqueio
  └── Linha 1000-1110: Botões de copiar credenciais
```

---

## 🔍 TROUBLESHOOTING

### Problema: Campos não bloqueiam após criar usuário

**Solução**:
1. Abrir DevTools (F12)
2. Ir em "Application" → "Local Storage"
3. Verificar se existe `vendas_user_data` com os dados
4. Se não existir, houve erro na criação

### Problema: Botões de copiar não aparecem

**Solução**:
1. Verificar se a mensagem contém "Usuário:" ou "Senha:"
2. Verificar console do navegador (F12) para erros
3. Limpar cache do navegador

### Problema: Cópia não funciona

**Solução**:
1. Verificar se navegador suporta `navigator.clipboard` (requer HTTPS)
2. Se estiver em HTTP, usar proxy reverso com SSL
3. Testar em navegador atualizado

---

## ✅ CHECKLIST FINAL

- [ ] Build do frontend concluído sem erros
- [ ] Arquivos enviados para `/var/www/iaze/frontend/build/`
- [ ] Serviço reiniciado no VPS
- [ ] Cache do navegador limpo
- [ ] Teste 1: Campos bloqueados após primeira criação ✅
- [ ] Teste 2: Botões de copiar funcionando ✅
- [ ] Site acessível em https://suporte.help/vendas

---

## 📞 SUPORTE

Se encontrar problemas:
1. Verificar logs do frontend: `supervisorctl tail -f iaze-frontend`
2. Verificar logs do nginx: `tail -f /var/log/nginx/error.log`
3. Testar em aba anônima (sem cache)
4. Verificar console do navegador (F12)
