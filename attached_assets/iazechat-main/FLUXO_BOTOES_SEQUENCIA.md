# 🔄 Fluxo de Botões em Sequência - WA Site

## 📋 Como Funciona Agora:

### Exemplo Prático:

**Configuração no Admin:**
```
TESTE GRATIS (botão raiz)
├── TV BOX (sub-botão 1)
├── SMARTV (sub-botão 2)
└── CELULAR (sub-botão 3)
```

### Fluxo no Chat (/vendas):

**1. Cliente clica em "TESTE GRATIS"**
```
[Cliente] > TESTE GRATIS

[Bot] > Ótimo! Vamos fazer seu teste grátis...
        (descrição configurada no botão TESTE GRATIS)

[Bot] > Escolha uma das opções abaixo:

        • TV BOX
        • SMARTV
        • CELULAR

        [Botão: TV BOX] [Botão: SMARTV] [Botão: CELULAR]
```

**2. Cliente clica em "TV BOX"**
```
[Cliente] > TV BOX

[Bot] > Para configurar na TV BOX, siga estes passos...
        (descrição configurada no botão TV BOX)
        (+ foto/vídeo se tiver configurado)
```

## ✅ Implementação:

### Backend:
- Quando botão é clicado, retorna:
  - `message`: Mensagem com descrição + mídia
  - `has_sub_buttons`: true/false
  - `buttons`: Array de sub-botões (se existir)

### Frontend:
- Renderiza mensagem de resposta
- **SE tem sub-botões:**
  1. Aguarda 500ms (efeito visual)
  2. Envia mensagem automática do bot listando opções
  3. Exibe botões clicáveis embaixo

## 📝 Como Configurar:

1. Acesse `/admin` → Aba "WA Site"
2. Clique em "Editar" no botão que quer adicionar sub-botões
3. Configure a descrição do botão
4. Opcional: Adicione foto/vídeo
5. Clique no botão "➕" ao lado do botão para adicionar sub-botão
6. Configure cada sub-botão com:
   - Texto do botão
   - Descrição (enviada quando clicado)
   - Foto/vídeo (opcional)

## 🎯 Resultado:

**Sequência automática:**
1️⃣ Cliente clica → Descrição do botão
2️⃣ Se tem sub-botões → Mensagem com lista de opções
3️⃣ Sub-botões aparecem para clicar
4️⃣ Cliente clica em sub-botão → Descrição + mídia
5️⃣ Se sub-botão tem sub-botões → Repete o processo

**Profundidade ilimitada!** Você pode ter:
- Botão raiz
  - Sub-botão
    - Sub-sub-botão
      - E assim por diante...

## 🧪 Teste:

1. Configure um botão com sub-botões em `/admin`
2. Acesse `/vendas`
3. Clique no botão pai
4. Veja a descrição + lista de sub-botões aparecerem automaticamente
5. Clique em um sub-botão e veja sua descrição + mídia
