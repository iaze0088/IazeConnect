# IAZE - Sistema de Gerenciamento WhatsApp

## 📋 Visão Geral

Sistema profissional de gerenciamento de conexões WhatsApp com integração WPP Connect. Permite criar múltiplas sessões WhatsApp, gerar QR Codes para conexão, monitorar status em tempo real e enviar mensagens.

## 🏗️ Arquitetura

### Frontend (React + TypeScript)
- **Framework**: React 19 com Wouter para roteamento
- **UI**: Shadcn/ui + Tailwind CSS (Material Design 3 adaptado)
- **State Management**: TanStack Query v5
- **Real-time**: WebSocket para atualizações de QR Code e status

### Backend (Node.js + Express)
- **Runtime**: Node.js 20
- **API**: Express.js com endpoints REST
- **WhatsApp**: @wppconnect-team/wppconnect
- **Storage**: In-memory storage (MemStorage) + PostgreSQL preparado
- **Real-time**: WebSocket Server (path: /ws)

## 📁 Estrutura do Projeto

```
├── client/                    # Frontend React
│   ├── src/
│   │   ├── components/       # Componentes reutilizáveis
│   │   │   ├── app-sidebar.tsx       # Navegação lateral
│   │   │   ├── whatsapp-qr-modal.tsx # Modal QR Code
│   │   │   └── ui/                   # Componentes Shadcn
│   │   ├── pages/            # Páginas da aplicação
│   │   │   ├── dashboard.tsx         # Dashboard principal
│   │   │   ├── whatsapp.tsx         # Gerenciamento WhatsApp
│   │   │   ├── sessions.tsx         # Lista de sessões
│   │   │   ├── logs.tsx             # Visualizador de logs
│   │   │   └── settings.tsx         # Configurações
│   │   ├── lib/              # Utilitários
│   │   └── App.tsx           # Componente raiz
├── server/                   # Backend Node.js
│   ├── routes.ts            # Rotas da API
│   ├── storage.ts           # Interface de armazenamento
│   └── services/            # Serviços (WhatsApp, etc)
├── shared/                  # Código compartilhado
│   └── schema.ts           # Schemas TypeScript + Zod
└── design_guidelines.md    # Guia de design do sistema
```

## 🎨 Design System

- **Paleta de Cores**: Blues profissionais (#2563EB) com suporte a dark mode
- **Tipografia**: Inter (UI), Roboto Mono (código/logs)
- **Espaçamento**: Grid 8px (Tailwind: 2, 4, 6, 8, 12, 16)
- **Componentes**: Shadcn/ui com elevação e interações sutis
- **Responsivo**: Mobile-first, breakpoints: 768px (tablet), 1024px (desktop)

## 🔧 Funcionalidades MVP

### ✅ Implementado (Frontend)
1. **Dashboard**: Visão geral com estatísticas de conexões
2. **Gerenciamento WhatsApp**:
   - Criar novas sessões
   - Botão "CONECTAR NÚMERO" para gerar QR Code
   - Visualizar status das conexões (conectado/desconectado)
   - Deletar sessões
3. **Modal QR Code**:
   - Display do QR Code base64
   - Contagem regressiva (45s)
   - Botão de refresh
   - Feedback visual de status (conectando/conectado)
4. **Sessões**: Tabela com todas as sessões e seus status
5. **Logs**: Visualizador de eventos do sistema
6. **Configurações**: Informações sobre a integração

### 🔨 A Implementar (Backend - Task 2)
1. API Endpoints:
   - `GET /api/whatsapp/connections` - Listar conexões
   - `POST /api/whatsapp/connections` - Criar conexão
   - `DELETE /api/whatsapp/connections/:id` - Remover conexão
   - `POST /api/whatsapp/connections/:id/start` - Iniciar sessão + gerar QR
   - `POST /api/whatsapp/connections/:id/refresh` - Atualizar status
   - `GET /api/whatsapp/logs` - Buscar logs

2. Integração WPP Connect:
   - Configurar @wppconnect-team/wppconnect
   - Gerenciar múltiplas sessões simultâneas
   - Gerar QR Code base64
   - Detectar conexão estabelecida
   - Persistir dados de sessão

3. WebSocket:
   - Enviar atualizações de QR Code em tempo real
   - Notificar mudanças de status
   - Sincronizar frontend/backend

## 🚀 Como Usar

### 1. Criar Conexão WhatsApp
1. Vá para a página "WhatsApp"
2. Digite um nome para a sessão (ex: "atendimento")
3. Clique em "Criar Conexão"

### 2. Conectar Número
1. No card da conexão, clique em "CONECTAR NÚMERO"
2. Modal abrirá mostrando o QR Code
3. Abra WhatsApp no celular > Configurações > Aparelhos Conectados
4. Escaneie o QR Code
5. Aguarde confirmação de conexão

### 3. Monitorar Status
- Dashboard mostra totais de conexões ativas/inativas
- Página Sessões lista todas com timestamps
- Logs mostram todos os eventos do sistema

## 📦 Variáveis de Ambiente

```env
# WPP Connect (será configurado no backend)
WPPCONNECT_API_URL=http://localhost:21465  # URL do servidor WPP Connect
WPPCONNECT_SECRET_KEY=SUA_SECRET_KEY_AQUI  # Secret key para autenticação

# Database (opcional - usa MemStorage por padrão)
DATABASE_URL=postgresql://...
```

## 🎯 Próximos Passos

**Task 2 - Backend Completo**:
- Instalar @wppconnect-team/wppconnect
- Implementar todos os endpoints da API
- Configurar WebSocket
- Integrar com WPP Connect
- Persistência de dados

**Task 3 - Integração & Testing**:
- Conectar frontend ↔ backend
- Testar fluxo completo de conexão
- Adicionar estados de loading/error polidos
- Feedback do architect
- Testes end-to-end

## 🎨 Padrões de Código

- **TypeScript**: Strict mode, tipos explícitos
- **React**: Functional components, hooks
- **API**: REST com Zod validation
- **Styling**: Tailwind classes, sem CSS inline
- **Testes**: data-testid em elementos interativos

## 📝 Notas Técnicas

- Frontend usa porta 5000 (0.0.0.0:5000)
- Backend integra WPP Connect como biblioteca
- WebSocket em /ws para não conflitar com Vite HMR
- QR Code em base64 (data:image/png;base64,...)
- Sessões identificadas por sessionName único
