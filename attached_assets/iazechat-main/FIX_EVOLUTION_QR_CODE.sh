#!/bin/bash

# Script para corrigir o problema de QR Code na Evolution API
# Problema: WhatsApp Web mudou o protocolo e a Evolution API precisa ser atualizada

echo "🔧 FIX: Evolution API QR Code Generation"
echo "========================================"
echo ""
echo "⚠️  IMPORTANTE: Execute este script no servidor onde a Evolution API está rodando"
echo ""
echo "Problema identificado:"
echo "  - Evolution API versão: 2.2.3"
echo "  - WhatsApp Web mudou protocolo em 2025"
echo "  - QR Code não está sendo gerado"
echo ""
echo "Solução:"
echo "  - Atualizar CONFIG_SESSION_PHONE_VERSION para versão mais recente"
echo ""

# Verificar se está no servidor correto
read -p "Você está no servidor evolution.suporte.help? (s/n): " confirm
if [ "$confirm" != "s" ]; then
    echo "❌ Execute este script no servidor da Evolution API"
    exit 1
fi

# Localizar o arquivo .env da Evolution API
echo "📁 Procurando arquivo de configuração da Evolution API..."

# Possíveis localizações
POSSIBLE_PATHS=(
    "/root/evolution-api/.env"
    "/opt/evolution-api/.env"
    "/var/www/evolution-api/.env"
    "$HOME/evolution-api/.env"
    "/usr/local/evolution-api/.env"
)

ENV_FILE=""
for path in "${POSSIBLE_PATHS[@]}"; do
    if [ -f "$path" ]; then
        ENV_FILE="$path"
        echo "✅ Encontrado: $ENV_FILE"
        break
    fi
done

if [ -z "$ENV_FILE" ]; then
    echo "❌ Arquivo .env não encontrado automaticamente"
    read -p "Digite o caminho completo do arquivo .env da Evolution API: " ENV_FILE
    
    if [ ! -f "$ENV_FILE" ]; then
        echo "❌ Arquivo não encontrado: $ENV_FILE"
        exit 1
    fi
fi

# Fazer backup
echo "💾 Criando backup..."
cp "$ENV_FILE" "${ENV_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
echo "✅ Backup criado: ${ENV_FILE}.backup"

# Verificar se a variável já existe
if grep -q "CONFIG_SESSION_PHONE_VERSION" "$ENV_FILE"; then
    echo "📝 Variável CONFIG_SESSION_PHONE_VERSION encontrada. Atualizando..."
    # Substituir valor existente
    sed -i 's/^CONFIG_SESSION_PHONE_VERSION=.*/CONFIG_SESSION_PHONE_VERSION=2.3000.1025062854/' "$ENV_FILE"
else
    echo "📝 Variável CONFIG_SESSION_PHONE_VERSION não encontrada. Adicionando..."
    # Adicionar nova linha
    echo "" >> "$ENV_FILE"
    echo "# WhatsApp Web Version (updated for 2025 compatibility)" >> "$ENV_FILE"
    echo "CONFIG_SESSION_PHONE_VERSION=2.3000.1025062854" >> "$ENV_FILE"
fi

echo "✅ Configuração atualizada!"
echo ""
echo "Nova configuração:"
grep "CONFIG_SESSION_PHONE_VERSION" "$ENV_FILE"
echo ""

# Reiniciar Evolution API
echo "🔄 Reiniciando Evolution API..."
echo ""
echo "Detectando método de deploy..."

# Verificar se está usando Docker
if command -v docker &> /dev/null && docker ps | grep -q evolution; then
    echo "🐳 Docker detectado. Reiniciando container..."
    CONTAINER_NAME=$(docker ps --filter "name=evolution" --format "{{.Names}}" | head -1)
    if [ -n "$CONTAINER_NAME" ]; then
        docker restart "$CONTAINER_NAME"
        echo "✅ Container $CONTAINER_NAME reiniciado"
    else
        echo "⚠️  Container não encontrado. Reinicie manualmente com: docker restart <container_name>"
    fi
    
# Verificar se está usando docker-compose
elif [ -f "docker-compose.yml" ] || [ -f "docker-compose.yaml" ]; then
    echo "🐳 Docker Compose detectado. Reiniciando..."
    docker-compose restart
    echo "✅ Serviço reiniciado via docker-compose"
    
# Verificar se está usando PM2
elif command -v pm2 &> /dev/null; then
    echo "📦 PM2 detectado. Reiniciando..."
    pm2 restart evolution-api
    echo "✅ Serviço reiniciado via PM2"
    
# Verificar se está usando systemctl
elif command -v systemctl &> /dev/null && systemctl list-units | grep -q evolution; then
    echo "🔧 Systemd detectado. Reiniciando..."
    sudo systemctl restart evolution-api
    echo "✅ Serviço reiniciado via systemctl"
    
else
    echo "⚠️  Método de deploy não detectado automaticamente"
    echo "Por favor, reinicie a Evolution API manualmente"
    echo ""
    echo "Comandos possíveis:"
    echo "  - Docker: docker restart <container_name>"
    echo "  - Docker Compose: docker-compose restart"
    echo "  - PM2: pm2 restart evolution-api"
    echo "  - Systemd: sudo systemctl restart evolution-api"
fi

echo ""
echo "✅ CORREÇÃO CONCLUÍDA!"
echo ""
echo "Próximos passos:"
echo "1. Aguarde 10-15 segundos para o serviço inicializar"
echo "2. Acesse: http://evolution.suporte.help:8080/manager"
echo "3. Tente gerar um QR code novamente"
echo "4. O QR code deve aparecer agora!"
echo ""
echo "Se o problema persistir:"
echo "  - Verifique os logs: docker logs <container_name>"
echo "  - Tente limpar cache do navegador"
echo "  - Tente em modo anônimo/privado"
echo ""
