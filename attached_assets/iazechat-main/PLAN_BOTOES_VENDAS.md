# 📋 PLANO: Melhorias nos Botões WA Site

## 🐛 Problemas Identificados:

### 1. Descrições não salvam
**Causa**: Na linha 87-104 do VendasButtonsManager.js, quando edita botão:
- Atualiza estado local `setConfig()`
- **MAS NÃO chama `saveConfig()`** para persistir no backend
- Por isso mostra "salvo" localmente mas perde ao recarregar

**Solução**: Adicionar `await saveConfig()` após `setConfig()`

## 🎯 Novas Funcionalidades a Implementar:

### 2. Upload de Foto/Vídeo nos Botões
- Adicionar campo `media_url` e `media_type` no modelo `Button`
- Interface para upload de arquivo (foto/vídeo)
- Armazenar arquivo e retornar URL

### 3. Enviar Mídia quando Cliente Clica no Botão
- Quando cliente clica em botão, verificar se tem mídia
- Enviar mensagem com texto + mídia configurada

## 📝 Arquivos a Modificar:

### Backend:
1. `/app/backend/vendas_buttons_service.py`
   - Adicionar `media_url` e `media_type` ao modelo Button
   
2. `/app/backend/vendas_routes_new.py`
   - Modificar lógica de resposta para incluir mídia
   - Adicionar endpoint de upload

### Frontend:
1. `/app/frontend/src/components/VendasButtonsManager.js`
   - Adicionar `await saveConfig()` após edições
   - Adicionar interface de upload de mídia
   - Preview de foto/vídeo

2. `/app/frontend/src/pages/VendasChatNew.js`
   - Exibir mídia quando botão for clicado
   - Renderizar imagem/vídeo na mensagem

## 🚀 Ordem de Implementação:

1. ✅ FIX: Adicionar saveConfig() após edições
2. ✅ Backend: Atualizar modelo Button com mídia
3. ✅ Backend: Endpoint de upload
4. ✅ Frontend: Interface de upload
5. ✅ Frontend: Exibir mídia ao clicar botão
6. ✅ Testar em produção
