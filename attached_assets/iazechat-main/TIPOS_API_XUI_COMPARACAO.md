# 🔐 Comparação: Tipos de API XUI

## 📊 Tabela de Permissões

| Tipo de API | Listar | Ver Dados | Criar | Editar | Deletar | Renovar | Recomendação |
|-------------|--------|-----------|-------|--------|---------|---------|--------------|
| **Admin** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ Muito perigoso |
| **Admin API** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ Muito perigoso |
| **Reseller API** | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ **ESCOLHA ESTE!** |
| **Web Player** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ Muito limitado |

---

## 🎯 Qual Escolher?

### ✅ RECOMENDADO: **Reseller API**

**Por quê?**
```
✅ Pode consultar dados (o que você precisa)
❌ NÃO pode alterar nada (seguro)
✅ Ideal para integração com sistemas externos
✅ Logs de auditoria simples
```

**Use quando:**
- ✅ Quer apenas CONSULTAR dados
- ✅ Integração com chat/atendimento
- ✅ Sistemas que não devem alterar dados
- ✅ APIs expostas externamente

---

### ❌ NÃO RECOMENDADO: **Admin API**

**Por quê?**
```
❌ Pode criar usuários
❌ Pode deletar usuários
❌ Pode editar senhas
❌ Pode renovar assinaturas
❌ Alto risco de segurança
```

**Use SOMENTE quando:**
- Você precisa de um sistema automatizado que GERENCIA usuários
- Ex: sistema de renovação automática, auto-provisionamento
- **NÃO use para simples consultas!**

---

## 🔒 Níveis de Segurança

```
┌─────────────────────────────────────────────────────────┐
│                   MAIS SEGURO ↑                          │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  🔐 Reseller API (READ-ONLY)                            │
│     └─ Apenas consultas                                 │
│     └─ Sem permissões de escrita                        │
│     └─ ✅ RECOMENDADO PARA IAZE                         │
│                                                          │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ⚠️  Admin API (READ + WRITE)                           │
│     └─ Consultas + Alterações                           │
│     └─ Pode criar/editar/deletar                        │
│     └─ ❌ MUITO PERIGOSO para consultas simples         │
│                                                          │
├─────────────────────────────────────────────────────────┤
│                   MENOS SEGURO ↓                         │
└─────────────────────────────────────────────────────────┘
```

---

## 💡 Exemplo Prático

### Cenário: Atendente consultando dados de cliente

#### ✅ COM Reseller API (SEGURO):
```
1. Cliente pergunta: "Qual meu usuário?"
2. Atendente busca no OFFICE
3. IAZE consulta XUI via Reseller API
4. XUI retorna apenas DADOS
5. Atendente vê os dados
6. ✅ NENHUM dado foi alterado
```

#### ❌ COM Admin API (PERIGOSO):
```
1. Cliente pergunta: "Qual meu usuário?"
2. Atendente busca no OFFICE
3. IAZE consulta XUI via Admin API
4. XUI retorna dados
5. ⚠️ SE houver um bug no código...
6. ❌ Poderia DELETAR o usuário acidentalmente!
7. ❌ Poderia ALTERAR a senha!
8. ❌ Poderia RENOVAR sem querer!
```

---

## 🛡️ Matriz de Risco

### Usando Reseller API:
```
┌────────────────────────────────────┐
│  Risco de Segurança:     BAIXO     │
│  Risco de Alteração:     ZERO      │
│  Risco de Perda de Dados: ZERO     │
│  Auditoria:              SIMPLES   │
│  Recomendação:           ✅ USE    │
└────────────────────────────────────┘
```

### Usando Admin API:
```
┌────────────────────────────────────┐
│  Risco de Segurança:     ALTO      │
│  Risco de Alteração:     ALTO      │
│  Risco de Perda de Dados: ALTO     │
│  Auditoria:              COMPLEXA  │
│  Recomendação:           ❌ EVITE  │
└────────────────────────────────────┘
```

---

## 📋 Checklist de Segurança

Antes de usar a API, verifique:

### ✅ Configuração Segura:
- [ ] Escolhi **Reseller API** no XUI
- [ ] Testei com `test_xui_security.sh`
- [ ] Confirmei que CREATE retorna 403/401
- [ ] Confirmei que DELETE retorna 403/401
- [ ] Confirmei que UPDATE retorna 403/401
- [ ] Confirmei que LIST funciona (200)

### ❌ Sinais de Problema:
- [ ] Usando Admin API para consultas simples
- [ ] CREATE retorna 200 (API pode criar!)
- [ ] DELETE retorna 200 (API pode deletar!)
- [ ] Não testei as permissões

---

## 🎯 Resumo Final

### Para IAZE (consultas apenas):

```
┌──────────────────────────────────────────┐
│         CONFIGURAÇÃO CORRETA              │
├──────────────────────────────────────────┤
│                                           │
│  Access Type:  Reseller API  ✅          │
│                                           │
│  Permissões:                              │
│    ✅ users:list    (pode listar)        │
│    ✅ users:read    (pode ler)           │
│    ❌ users:create  (não pode criar)     │
│    ❌ users:update  (não pode editar)    │
│    ❌ users:delete  (não pode deletar)   │
│                                           │
└──────────────────────────────────────────┘
```

---

## 📞 Próximos Passos

1. ✅ Criar API no XUI com **Reseller API**
2. ✅ Configurar no IAZE (.env)
3. ✅ Testar com `test_xui_integration.sh`
4. ✅ Testar segurança com `test_xui_security.sh`
5. ✅ Usar tranquilamente! 🎉

---

**Lembre-se:** Segurança > Conveniência

É melhor ter uma API com permissões LIMITADAS do que uma API com TODAS as permissões! 🔒
