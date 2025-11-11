#!/bin/bash

# Script para Upgrade Evolution API para v2.3.6
# Execute este script no servidor onde o Docker está instalado

echo "=========================================="
echo "UPGRADE EVOLUTION API v1.8.7 → v2.3.6"
echo "=========================================="

cd /app

echo ""
echo "[1/5] Parando containers atuais..."
docker compose -f docker-compose.evolution.yml down

echo ""
echo "[2/5] Fazendo pull da nova imagem v2.3.6..."
docker compose -f docker-compose.evolution.yml pull

echo ""
echo "[3/5] Iniciando Evolution API v2.3.6..."
docker compose -f docker-compose.evolution.yml up -d

echo ""
echo "[4/5] Aguardando inicialização (30 segundos)..."
sleep 30

echo ""
echo "[5/5] Verificando status..."
docker compose -f docker-compose.evolution.yml ps
echo ""
docker compose -f docker-compose.evolution.yml logs evolution-api --tail=50

echo ""
echo "=========================================="
echo "UPGRADE CONCLUÍDO!"
echo "=========================================="
echo "Evolution API v2.3.6 está rodando em:"
echo "http://localhost:8080"
echo ""
echo "Para ver logs em tempo real:"
echo "docker compose -f docker-compose.evolution.yml logs -f evolution-api"
echo "=========================================="
