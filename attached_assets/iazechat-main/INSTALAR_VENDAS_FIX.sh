#!/bin/bash

###############################################################################
# Script de Instalação - Correções Chat /vendas
# Data: $(date +%Y-%m-%d)
###############################################################################

set -e  # Parar em caso de erro

echo "=========================================="
echo "🚀 INSTALAÇÃO: Correções Chat /vendas"
echo "=========================================="
echo ""

# Verificar se está rodando como root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Por favor, execute como root (use sudo)"
    exit 1
fi

# Diretório de destino
DESTINO="/opt/iaze"

# Verificar se o diretório existe
if [ ! -d "$DESTINO" ]; then
    echo "❌ Diretório $DESTINO não encontrado!"
    echo "   Certifique-se de que está no servidor externo correto."
    exit 1
fi

echo "📂 Diretório de destino: $DESTINO"
echo ""

# Passo 1: Instalar FFmpeg (se não estiver instalado)
echo "===================================="
echo "📦 PASSO 1: Verificando FFmpeg..."
echo "===================================="

if ! command -v ffmpeg &> /dev/null; then
    echo "⚠️  FFmpeg não encontrado. Instalando..."
    apt-get update -qq
    DEBIAN_FRONTEND=noninteractive apt-get install -y ffmpeg > /dev/null 2>&1
    echo "✅ FFmpeg instalado com sucesso!"
else
    echo "✅ FFmpeg já está instalado"
fi

ffmpeg -version | head -n 1
echo ""

# Passo 2: Fazer backup dos arquivos atuais
echo "===================================="
echo "💾 PASSO 2: Backup dos arquivos..."
echo "===================================="

BACKUP_DIR="$DESTINO/backup_vendas_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backup dos arquivos que serão modificados
if [ -f "$DESTINO/frontend/src/pages/VendasChatNew.js" ]; then
    cp "$DESTINO/frontend/src/pages/VendasChatNew.js" "$BACKUP_DIR/"
    echo "✅ Backup: VendasChatNew.js"
fi

if [ -f "$DESTINO/frontend/src/pages/VendasChatNew.css" ]; then
    cp "$DESTINO/frontend/src/pages/VendasChatNew.css" "$BACKUP_DIR/"
    echo "✅ Backup: VendasChatNew.css"
fi

echo "📁 Backup salvo em: $BACKUP_DIR"
echo ""

# Passo 3: Extrair e copiar arquivos atualizados
echo "===================================="
echo "📥 PASSO 3: Instalando atualizações..."
echo "===================================="

# Extrair o pacote
TAR_FILE=$(ls -t /root/vendas_chat_fix_*.tar.gz 2>/dev/null | head -n 1)

if [ -z "$TAR_FILE" ]; then
    echo "❌ Arquivo vendas_chat_fix_*.tar.gz não encontrado em /root/"
    echo "   Por favor, faça upload do arquivo primeiro."
    exit 1
fi

echo "📦 Extraindo: $TAR_FILE"
tar -xzf "$TAR_FILE" -C "$DESTINO/"

echo "✅ Arquivos copiados:"
echo "   - frontend/src/pages/VendasChatNew.js"
echo "   - frontend/src/pages/VendasChatNew.css"
echo ""

# Passo 4: Ajustar permissões
echo "===================================="
echo "🔐 PASSO 4: Ajustando permissões..."
echo "===================================="

chown -R root:root "$DESTINO/frontend/src/pages/VendasChatNew.js"
chown -R root:root "$DESTINO/frontend/src/pages/VendasChatNew.css"
chmod 644 "$DESTINO/frontend/src/pages/VendasChatNew.js"
chmod 644 "$DESTINO/frontend/src/pages/VendasChatNew.css"

echo "✅ Permissões ajustadas"
echo ""

# Passo 5: Reiniciar serviços
echo "===================================="
echo "🔄 PASSO 5: Reiniciando serviços..."
echo "===================================="

echo "⏳ Reiniciando backend..."
supervisorctl restart backend
sleep 3

echo "⏳ Reiniciando frontend..."
supervisorctl restart frontend
sleep 5

echo "✅ Serviços reiniciados"
echo ""

# Passo 6: Verificar status
echo "===================================="
echo "✅ PASSO 6: Verificando status..."
echo "===================================="

supervisorctl status backend frontend

echo ""
echo "=========================================="
echo "🎉 INSTALAÇÃO CONCLUÍDA COM SUCESSO!"
echo "=========================================="
echo ""
echo "📋 RESUMO DAS CORREÇÕES APLICADAS:"
echo ""
echo "✅ FFmpeg instalado (processamento de áudio)"
echo "✅ Mensagens separadas (cliente=direita/verde, IA=esquerda/branco)"
echo "✅ Botões de mídia aumentados (52px) e mais visíveis"
echo ""
echo "📁 Backup dos arquivos antigos em:"
echo "   $BACKUP_DIR"
echo ""
echo "🔗 Teste o chat em:"
echo "   https://suporte.help/vendas"
echo ""
echo "=========================================="
