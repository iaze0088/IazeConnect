# 🔒 Isolamento de Avisos por Domínio - IAZE

## Visão Geral

Os avisos agora são **isolados por DOMÍNIO**, não apenas por usuário. Isso significa que o que você vê depende de **QUAL DOMÍNIO você está acessando**.

---

## 🌐 Cenários de Uso

### 1️⃣ **Admin acessando pelo domínio MASTER (suporte.help)**

**O que vê:**
- ✅ Avisos globais (`target_audience: "all"`)
- ✅ Avisos próprios do admin (`reseller_id: null`, `target_audience: "own"`)

**O que pode criar:**
- ✅ Avisos globais (visíveis para TODOS)
- ✅ Avisos específicos para revendas (escolhe IDs)
- ✅ Avisos próprios do admin

**Exemplo:**
```
Admin logado em: https://suporte.help/admin/login
Vê: Avisos do sistema + Avisos administrativos
```

---

### 2️⃣ **Revenda acessando pelo PRÓPRIO domínio (dominio.revenda)**

**O que vê:**
- ✅ Avisos globais do admin
- ✅ Avisos próprios da revenda
- ✅ Avisos direcionados especificamente à revenda

**O que pode criar:**
- ✅ Avisos próprios (visíveis apenas no domínio dela)

**Exemplo:**
```
Revenda logada em: https://dominio.revenda/reseller-login
Vê: Avisos globais + Avisos da revenda "dominio.revenda"
```

---

### 3️⃣ **Cliente/Agent acessando domínio de revenda**

**O que vê:**
- ✅ Avisos globais do admin
- ✅ Avisos da revenda (daquele domínio)

**Exemplo:**
```
Cliente acessando: https://dominio.revenda/client/chat
Vê: Avisos globais + Avisos da revenda "dominio.revenda"
```

---

### 4️⃣ **Sub-revenda com subdomínio (subdominio.revenda)**

**O que vê:**
- ✅ Avisos globais do admin
- ✅ Avisos da sub-revenda
- ✅ Avisos direcionados à sub-revenda

**Exemplo:**
```
Sub-revenda logada em: https://subdominio.revenda/reseller-login
Vê: Avisos globais + Avisos da sub-revenda "subdominio.revenda"
```

---

## 🎯 Regras de Isolamento

| Domínio Acessado | Usuário | Avisos Visíveis |
|------------------|---------|-----------------|
| `suporte.help` (master) | Admin | Globais + Admin |
| `suporte.help` (master) | Client/Agent | Apenas Globais |
| `dominio.revenda` | Qualquer usuário | Globais + Revenda "dominio.revenda" |
| `subdominio.revenda` | Qualquer usuário | Globais + Sub-revenda "subdominio.revenda" |

---

## 🛠️ Implementação Técnica

### Backend

**Arquivo:** `/app/backend/server.py`

**Lógica:**
1. Captura o tenant pelo domínio (`get_request_tenant(request)`)
2. Identifica se é domínio master (`tenant.is_master`) ou de revenda (`tenant.reseller_id`)
3. Filtra avisos baseado no domínio acessado

**Query exemplo (domínio de revenda):**
```python
{
  "$or": [
    {"target_audience": "all"},  # Avisos globais
    {"reseller_id": tenant.reseller_id, "target_audience": "own"},  # Avisos da revenda
    {"target_audience": "specific", "target_reseller_ids": tenant.reseller_id}  # Direcionados
  ]
}
```

---

## ✅ Garantias de Segurança

- ✅ **Isolamento Total**: Revenda A NUNCA vê avisos da Revenda B
- ✅ **Multi-tenancy por Domínio**: Cada domínio tem seus próprios avisos
- ✅ **Avisos Globais**: Admin pode enviar comunicados para TODOS
- ✅ **Avisos Direcionados**: Admin pode escolher revendas específicas

---

## 📌 Exemplos Práticos

### Exemplo 1: Admin cria aviso global
```json
{
  "kind": "text",
  "text": "Manutenção programada para amanhã às 3h",
  "target_audience": "all",
  "reseller_id": null
}
```
**Resultado:** TODOS os domínios veem este aviso

---

### Exemplo 2: Revenda cria aviso próprio
```json
{
  "kind": "text",
  "text": "Nova promoção: 20% de desconto!",
  "target_audience": "own",
  "reseller_id": "revenda-123"
}
```
**Resultado:** Apenas usuários acessando o domínio da "revenda-123" veem

---

### Exemplo 3: Admin cria aviso para 2 revendas específicas
```json
{
  "kind": "text",
  "text": "Vocês ganharam 10 conexões extras!",
  "target_audience": "specific",
  "target_reseller_ids": ["revenda-123", "revenda-456"],
  "reseller_id": null
}
```
**Resultado:** Apenas "revenda-123" e "revenda-456" veem (em seus domínios)

---

## 🔍 Como Testar

1. **Teste 1:** Criar aviso como Admin no domínio master
   - Acesse: `https://suporte.help/admin/login`
   - Crie aviso com `target_audience: "all"`
   - Verifique que aparece em todos os domínios

2. **Teste 2:** Criar aviso como Revenda
   - Acesse: `https://dominio.revenda/reseller-login`
   - Crie aviso próprio
   - Verifique que aparece APENAS naquele domínio

3. **Teste 3:** Verificar isolamento
   - Acesse domínio da Revenda A
   - Crie aviso
   - Acesse domínio da Revenda B
   - Confirme que o aviso da Revenda A NÃO aparece

---

## ⚠️ Importante

- **Domínio é a verdade absoluta**: Não importa quem está logado, o domínio define os avisos
- **Isolamento robusto**: Impossível vazar avisos entre revendas
- **Admin tem controle total**: Pode enviar avisos globais ou direcionados

---

**Última atualização:** 2025-01-XX
**Status:** ✅ Implementado e funcionando
