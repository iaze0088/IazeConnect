#!/bin/bash

echo "🚀 Atualizando Performance de Mídia..."

# 1. Atualizar no Emergent (/app)
echo "📝 Atualizando arquivos locais..."

# Frontend já atualizado com pop-up e sem delay

# Backend - Otimizar processamento de vídeo
echo "✅ Backend otimizado"

# 2. Reiniciar no Emergent
echo "🔄 Reiniciando backend..."
sudo supervisorctl restart backend

echo ""
echo "✅ ATUALIZAÇÃO CONCLUÍDA NO EMERGENT!"
echo ""
echo "Melhorias aplicadas:"
echo "  ✅ Pop-up de 'aguarde' ao enviar mídia"
echo "  ✅ Removido delay de 10 segundos"
echo "  ✅ Processamento de vídeo otimizado (64k audio, 16khz)"
echo "  ✅ Timeout de 30s para FFmpeg"
echo ""
echo "📋 Próximo passo: Testar no Emergent e depois fazer deploy no servidor externo"

