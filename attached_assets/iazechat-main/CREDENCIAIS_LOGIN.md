# 🔐 CREDENCIAIS DE LOGIN - IAZE SYSTEM

## 🚨 PROBLEMA DE CACHE?

Se você não conseguir fazer login, acesse esta URL para limpar o cache automaticamente:

**🔧 https://wppconnect-fix.preview.emergentagent.com/clear-cache.html**

Ou limpe manualmente:
- **Ctrl + Shift + Delete** (Windows/Linux)
- **Cmd + Shift + Delete** (Mac)
- Limpar: Cookies + Cache das últimas 24 horas

---

## 👨‍💼 ADMIN

**URL:** https://wppconnect-fix.preview.emergentagent.com/admin/login

**Senha:** `102030@ab`

---

## 👥 ATENDENTES

**URL:** https://wppconnect-fix.preview.emergentagent.com/atendente/login

### Lista de Atendentes:

| Username      | Senha        | Nome      |
|---------------|--------------|-----------|
| leticiaatt    | ab181818ab   | Leticia   |
| biancaatt     | ab181818ab   | Bianca    |
| fabioro       | 102030ab     | Fabio Oro |
| andressaatt   | ab181818ab   | Andressa  |
| jessicaatt    | ab181818ab   | Jessica   |
| fabio321      | fabio321     | Fabio (teste) |

---

## ✅ VERIFICAÇÃO DE STATUS

**Teste as APIs diretamente:**

### Admin:
```bash
curl -X POST https://wppconnect-fix.preview.emergentagent.com/api/auth/admin/login \
  -H "Content-Type: application/json" \
  -d '{"password":"102030@ab"}'
```

### Atendente (exemplo: leticiaatt):
```bash
curl -X POST https://wppconnect-fix.preview.emergentagent.com/api/auth/agent/login \
  -H "Content-Type: application/json" \
  -d '{"login":"leticiaatt","password":"ab181818ab"}'
```

Se retornar `{"token":"..."}` = ✅ API FUNCIONANDO (problema é cache)
Se retornar `401` = ❌ Senha incorreta

---

## 📊 ESTATÍSTICAS DO SISTEMA

- **8.785 clientes** sincronizados do Office (gestor.my)
- **50 usuários** no banco
- **30 clientes** cadastrados
- **6 atendentes** ativos

---

## 🔄 OFFICE RÁPIDO

Após logar como atendente, clique no botão **"Office Rápido"** no dashboard para:
- Buscar clientes instantaneamente
- Visualizar usuário, senha e status
- Sincronizar manualmente os dados

**Busca inteligente de telefone:** Aceita múltiplos formatos:
- ✅ 19989612020
- ✅ +55 19 9 8961-2020
- ✅ 5519989612020
- ✅ 19 9 8961-2020

---

## 🆘 PROBLEMAS?

1. **Não consigo logar:** Acesse `/clear-cache.html` ou limpe o cache manualmente
2. **Esqueci a senha:** As senhas estão neste arquivo
3. **API retorna 401:** Verifique se está usando o username/senha corretos
4. **Office Rápido não funciona:** Verifique se o atendente está logado corretamente

---

**Última atualização:** 01/11/2025 16:35
**Versão:** 2.0.4-agents-fix-20251101-1633
