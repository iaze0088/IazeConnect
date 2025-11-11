# 🔗 Guia: Botões com Link de Redirecionamento

## 📋 Nova Funcionalidade Implementada:

Agora você pode criar botões que **abrem links diretamente** ao invés de só enviar mensagens.

## ✅ Casos de Uso:

### 1️⃣ WhatsApp do Atendente
```
SUPORTE
└── FALAR COM ATENDENTE
    └── Link: https://wa.me/5511999999999
```

### 2️⃣ Site Externo
```
TESTE GRATIS
└── CRIAR CONTA
    └── Link: https://seusite.com/cadastro
```

### 3️⃣ Formulário
```
SUPORTE
└── ABRIR CHAMADO
    └── Link: https://forms.google.com/seu-formulario
```

## 🛠️ Como Configurar:

### No Admin (/admin → WA Site):

1. **Criar/Editar Botão**
   - Clique em "➕ Adicionar" ou "✏️ Editar" no botão desejado

2. **Preencher Informações**
   - **Texto do Botão**: Ex: "FALAR COM ATENDENTE"
   - **Mensagem de Resposta**: Pode deixar um espaço ou descrição breve
   - **🔗 Link de Redirecionamento**: Cole o link completo
     - Exemplo WhatsApp: `https://wa.me/5511999999999`
     - Exemplo Site: `https://seusite.com/contato`
     - Exemplo Telegram: `https://t.me/seucanal`

3. **Salvar**

## 🎯 Comportamento:

### ❌ SEM Link de Redirecionamento:
```
Cliente clica "FALAR COM ATENDENTE"
  ↓
[Bot] Envia mensagem de resposta
[Bot] Envia sub-botões (se houver)
```

### ✅ COM Link de Redirecionamento:
```
Cliente clica "FALAR COM ATENDENTE"
  ↓
🌐 ABRE LINK EM NOVA ABA
(Não envia mensagem, não processa backend)
```

## 💡 Dicas:

### WhatsApp Business:
```
https://wa.me/5511999999999
https://wa.me/5511999999999?text=Olá, vim do site
```

### Link com Mensagem Pré-preenchida:
```
https://wa.me/5511999999999?text=Olá!%20Preciso%20de%20suporte
```

### Múltiplos Canais:
```
SUPORTE
├── WhatsApp → https://wa.me/5511999999999
├── Telegram → https://t.me/seucanal
└── Email → mailto:suporte@empresa.com
```

## 🔧 Detalhes Técnicos:

- **Link abre em**: Nova aba (`_blank`)
- **Validação**: Frontend valida se link existe antes de abrir
- **Logs**: Console mostra `🔗 Abrindo link: [URL]`
- **Compatibilidade**: Funciona em desktop e mobile

## ⚠️ Importante:

1. **Sempre use HTTPS** em links externos
2. **Teste o link** antes de salvar
3. **Link deve começar com**:
   - `https://`
   - `http://`
   - `mailto:`
   - `tel:`

## 🧪 Exemplo Prático:

### Configuração:
```
Botão: FALAR COM ATENDENTE
Link: https://wa.me/5511999999999?text=Olá!%20Vim%20do%20/vendas
```

### Resultado:
1. Cliente clica em "FALAR COM ATENDENTE"
2. **WhatsApp Web abre em nova aba**
3. Mensagem já pré-preenchida: "Olá! Vim do /vendas"
4. Cliente só precisa apertar Enter

## 🎉 Vantagens:

✅ Redireciona diretamente para atendimento
✅ Não precisa copiar/colar links
✅ Experiência mais fluida
✅ Funciona com WhatsApp, Telegram, Sites, etc.
