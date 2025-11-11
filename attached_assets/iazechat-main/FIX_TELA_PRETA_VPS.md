# 🚨 FIX TELA PRETA NO VPS - suporte.help/vendas

## 🔍 DIAGNÓSTICO

A tela preta indica que o VPS está rodando uma versão antiga do código SEM as modificações que fiz.

**CAUSA PROVÁVEL:**
- Você copiou apenas o `build/` mas não fez rebuild no VPS
- OU o arquivo fonte `VendasChatNew.js` não foi atualizado

## ✅ SOLUÇÃO DEFINITIVA - ESCOLHA UMA OPÇÃO:

---

### 🎯 OPÇÃO 1: COPIAR BUILD PRONTO (MAIS RÁPIDO)

**No VPS (via SSH):**

```bash
# 1. Parar frontend
cd /var/www/iaze/frontend
supervisorctl stop iaze-frontend

# 2. Fazer backup
mv build build_backup_$(date +%Y%m%d_%H%M%S)

# 3. Você precisa enviar o build atualizado de:
#    ORIGEM: /app/frontend/build/ (deste container)
#    DESTINO: /var/www/iaze/frontend/build/ (no VPS)
#    Use SFTP, FileZilla ou rsync

# 4. Depois de copiar, reiniciar:
supervisorctl start iaze-frontend
supervisorctl status iaze-frontend
```

---

### 🎯 OPÇÃO 2: REBUILD NO VPS (MAIS SEGURO)

**No VPS (via SSH):**

```bash
# 1. Ir para diretório
cd /var/www/iaze/frontend

# 2. Atualizar arquivo fonte
# Você precisa copiar:
#   ORIGEM: /app/frontend/src/pages/VendasChatNew.js (deste container)
#   DESTINO: /var/www/iaze/frontend/src/pages/VendasChatNew.js (no VPS)

# 3. Fazer backup do build atual
mv build build_backup_$(date +%Y%m%d_%H%M%S)

# 4. Rebuild
yarn build

# 5. Reiniciar
supervisorctl restart iaze-frontend

# 6. Verificar
supervisorctl status iaze-frontend
tail -f /var/log/supervisor/iaze-frontend.err.log
```

---

### 🎯 OPÇÃO 3: COPIAR AMBOS (MAIS COMPLETO)

**Copie DOIS arquivos:**

1. **Arquivo Fonte:**
   - Origem: `/app/frontend/src/pages/VendasChatNew.js`
   - Destino: `/var/www/iaze/frontend/src/pages/VendasChatNew.js`

2. **Build Pronto:**
   - Origem: `/app/frontend/build/` (pasta inteira)
   - Destino: `/var/www/iaze/frontend/build/`

**Depois, no VPS:**
```bash
supervisorctl restart iaze-frontend
```

---

## 🔧 COMANDOS ÚTEIS NO VPS

### Verificar se frontend está rodando:
```bash
supervisorctl status iaze-frontend
```

### Ver logs de erro:
```bash
tail -50 /var/log/supervisor/iaze-frontend.err.log
```

### Ver logs normais:
```bash
tail -50 /var/log/supervisor/iaze-frontend.out.log
```

### Testar manualmente (porta 3000):
```bash
curl http://localhost:3000/vendas
```

### Verificar Nginx:
```bash
nginx -t
systemctl status nginx
```

---

## 📦 ARQUIVOS PARA DOWNLOAD

### 1. Build completo (4.2MB):
```
/tmp/vendas_frontend_update.tar.gz
```

**Como baixar:**
- Se estiver em SSH container Emergent: `cp /tmp/vendas_frontend_update.tar.gz /workspace/`
- Depois baixe de `/workspace/` pelo browser

### 2. Arquivo fonte:
```
/app/frontend/src/pages/VendasChatNew.js
```

---

## ✅ COMO TESTAR SE FUNCIONOU

### 1. Limpar cache do navegador:
- Chrome/Firefox: `Ctrl + Shift + Delete`
- Ou usar aba anônima: `Ctrl + Shift + N`

### 2. Acessar:
```
https://suporte.help/vendas
```

### 3. Verificar:
- ✅ Tela NÃO deve estar preta
- ✅ Deve aparecer "Iniciando conversa..." ou chat carregado
- ✅ Abrir DevTools (F12) → Console
- ✅ NÃO deve ter erros em vermelho

### 4. Testar funcionalidade:
- Clicar em botão que abre formulário
- Criar usuário (primeira vez)
- Fechar e reabrir formulário
- ✅ Campos WhatsApp e PIN devem estar BLOQUEADOS

---

## 🆘 SE AINDA ESTIVER COM TELA PRETA

### Verificar Console do Navegador (F12):

1. Apertar `F12` no navegador
2. Ir em aba "Console"
3. Procurar erros em vermelho
4. Copiar mensagem de erro completa
5. Me enviar para eu debugar

### Verificar Network (F12):

1. Apertar `F12` no navegador
2. Ir em aba "Network"
3. Recarregar página (F5)
4. Procurar requisições em vermelho (falhas)
5. Verificar se `/api/vendas/start` está funcionando

---

## 🎯 RESUMO RÁPIDO

**PROBLEMA:** Tela preta = código antigo no VPS

**SOLUÇÃO:**
1. Copiar `/app/frontend/build/` para VPS
2. Substituir `/var/www/iaze/frontend/build/`
3. Reiniciar: `supervisorctl restart iaze-frontend`
4. Limpar cache do navegador
5. Testar em `https://suporte.help/vendas`

---

## 📞 SUPORTE

Se continuar com problema, me envie:
- ✅ Screenshot da tela preta
- ✅ Console do navegador (F12)
- ✅ Logs do VPS: `tail -50 /var/log/supervisor/iaze-frontend.err.log`
