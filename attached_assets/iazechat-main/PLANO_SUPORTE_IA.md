# IMPLEMENTAÇÃO: Sistema de Redirecionamento para Suporte + Aba I.A

## RESUMO DAS MUDANÇAS NECESSÁRIAS:

### 1. Backend - vendas_routes.py
- Criar endpoint `/api/vendas/ai-sessions` para listar conversas ativas da IA
- Atualizar endpoint de mensagem para detectar palavras-chave de redirecionamento

### 2. Backend - vendas_ai_service.py
- Detectar palavras-chave: "reembolso", "atendente humanizado", "falar com humano"
- Detectar sentimento negativo/frustração
- Enviar mensagem de transferência
- Desativar IA por 1 hora
- Criar ticket no sistema de suporte

### 3. Frontend - AgentDashboard.js
- Adicionar botão "ATIVAR IA NA CONVERSA"
- Mostrar status da IA (ativa/desativada)
- Mostrar tempo restante até reativação automática

### 4. Backend - Criar nova collection no MongoDB
- `ai_redirections`: armazenar redirecionamentos e tempo de desativação

## ARQUIVOS A MODIFICAR:
- /app/backend/vendas_routes.py
- /app/backend/vendas_ai_service.py
- /app/backend/server.py (adicionar endpoint de reativação)
- /app/frontend/src/pages/AgentDashboard.js

## COMEÇANDO IMPLEMENTAÇÃO...
