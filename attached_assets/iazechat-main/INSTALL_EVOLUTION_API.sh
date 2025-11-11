#!/bin/bash

echo "🚀 INSTALAÇÃO EVOLUTION API - CYBERTV SUPORTE"
echo "=============================================="
echo ""

# Verificar se é root
if [ "$EUID" -ne 0 ]; then 
  echo "⚠️  Execute com sudo: sudo bash INSTALL_EVOLUTION_API.sh"
  exit
fi

# Passo 1: Instalar Docker
echo "📦 Passo 1: Verificando Docker..."
if ! command -v docker &> /dev/null; then
    echo "Docker não encontrado. Instalando..."
    curl -fsSL https://get.docker.com | sh
    usermod -aG docker $SUDO_USER
    echo "✅ Docker instalado!"
else
    echo "✅ Docker já instalado!"
fi

# Passo 2: Instalar Docker Compose (se não tiver)
echo ""
echo "📦 Passo 2: Verificando Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    echo "Docker Compose não encontrado. Instalando..."
    curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    echo "✅ Docker Compose instalado!"
else
    echo "✅ Docker Compose já instalado!"
fi

# Passo 3: Iniciar Evolution API
echo ""
echo "🚀 Passo 3: Iniciando Evolution API..."
cd /app

# Parar se já estiver rodando
docker-compose -f docker-compose.evolution.yml down 2>/dev/null

# Iniciar containers
docker-compose -f docker-compose.evolution.yml up -d

echo ""
echo "⏳ Aguardando Evolution API inicializar (60 segundos)..."
sleep 60

# Verificar se está rodando
echo ""
echo "🔍 Verificando status..."
if docker ps | grep -q evolution-api; then
    echo "✅ Evolution API está rodando!"
    echo ""
    echo "📊 Containers ativos:"
    docker ps | grep -E "evolution|postgres"
    echo ""
    echo "🌐 Evolution API disponível em: http://localhost:8080"
    echo "🔑 API Key: cybertv-suporte-evolution-key-2024"
    echo ""
    echo "✅ INSTALAÇÃO COMPLETA!"
    echo ""
    echo "📋 Próximos passos:"
    echo "   1. Reinicie o backend: sudo supervisorctl restart backend"
    echo "   2. Acesse: https://wppconnect-fix.preview.emergentagent.com/reseller-login"
    echo "   3. Vá na aba 'WhatsApp'"
    echo "   4. Clique em 'Adicionar Número'"
    echo "   5. Escaneie o QR Code"
    echo ""
else
    echo "❌ Erro ao iniciar Evolution API"
    echo ""
    echo "Ver logs:"
    echo "   docker-compose -f docker-compose.evolution.yml logs -f evolution-api"
fi

echo ""
echo "🔧 Comandos úteis:"
echo "   Ver logs: docker-compose -f /app/docker-compose.evolution.yml logs -f evolution-api"
echo "   Parar: docker-compose -f /app/docker-compose.evolution.yml down"
echo "   Reiniciar: docker-compose -f /app/docker-compose.evolution.yml restart"
echo ""
