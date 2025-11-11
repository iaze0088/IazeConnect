#!/bin/bash
# Script para sincronizar Emergent → Servidor Externo (198.96.94.106)
# Execute este script NO SEU SERVIDOR EXTERNO

set -e

EMERGENT_URL="https://wppconnect-fix.preview.emergentagent.com"
BACKEND_PATH="/opt/iaze/backend"
LOG_FILE="/var/log/iaze_sync.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "🚀 Iniciando sincronização Emergent → Servidor Externo"

# 1. Verificar se o sistema de exportação está disponível
log "📡 Verificando disponibilidade da Emergent..."
if ! curl -sf "${EMERGENT_URL}/api/export/status" > /dev/null; then
    log "❌ ERRO: Não foi possível conectar à Emergent"
    exit 1
fi

log "✅ Emergent disponível"

# 2. Fazer backup do arquivo atual
log "💾 Fazendo backup do server.py atual..."
BACKUP_FILE="${BACKEND_PATH}/server.py.backup_$(date +%Y%m%d_%H%M%S)"
if [ -f "${BACKEND_PATH}/server.py" ]; then
    cp "${BACKEND_PATH}/server.py" "$BACKUP_FILE"
    log "✅ Backup salvo: $BACKUP_FILE"
fi

# 3. Baixar novo server.py da Emergent
log "📥 Baixando server.py atualizado..."
if curl -sf -o "${BACKEND_PATH}/server.py.NEW" "${EMERGENT_URL}/api/download/server.py"; then
    log "✅ Download completo"
    
    # Verificar se o arquivo não está vazio
    if [ -s "${BACKEND_PATH}/server.py.NEW" ]; then
        # Remover proteção, copiar novo arquivo e proteger novamente
        chmod 644 "${BACKEND_PATH}/server.py" 2>/dev/null || true
        mv "${BACKEND_PATH}/server.py.NEW" "${BACKEND_PATH}/server.py"
        chmod 444 "${BACKEND_PATH}/server.py"
        log "✅ server.py atualizado e protegido"
    else
        log "❌ ERRO: Arquivo baixado está vazio"
        rm -f "${BACKEND_PATH}/server.py.NEW"
        exit 1
    fi
else
    log "❌ ERRO: Falha no download do server.py"
    exit 1
fi

# 4. Reiniciar backend
log "🔄 Reiniciando backend..."
cd /opt/iaze
docker-compose restart backend

# 5. Aguardar inicialização
log "⏳ Aguardando backend iniciar..."
sleep 15

# 6. Testar se o backend está funcionando
log "🔍 Testando backend..."
if curl -sf http://localhost:8001/api/health > /dev/null; then
    log "✅ Backend funcionando corretamente!"
    log "🎉 Sincronização completa com sucesso!"
    
    # Mostrar status final
    echo ""
    echo "========================================="
    echo "     SINCRONIZAÇÃO CONCLUÍDA COM SUCESSO"
    echo "========================================="
    echo "Backup anterior: $BACKUP_FILE"
    echo "Novo arquivo: ${BACKEND_PATH}/server.py"
    echo "Log completo: $LOG_FILE"
    echo ""
else
    log "⚠️ AVISO: Backend pode não estar respondendo"
    log "Verificando logs..."
    docker-compose logs --tail=20 backend | tee -a "$LOG_FILE"
    
    log "🔄 Tentando restaurar backup..."
    chmod 644 "${BACKEND_PATH}/server.py"
    cp "$BACKUP_FILE" "${BACKEND_PATH}/server.py"
    chmod 444 "${BACKEND_PATH}/server.py"
    docker-compose restart backend
    
    log "❌ Sincronização falhou. Sistema restaurado para versão anterior."
    exit 1
fi

