#!/bin/bash
# Script para manter túnel SSH sempre ativo para Evolution API
# Executar em background: nohup bash /app/keep_ssh_tunnel.sh > /tmp/ssh_tunnel.log 2>&1 &

while true; do
    # Verificar se o túnel está ativo
    if ! pgrep -f "ssh.*8080:localhost:8080" > /dev/null; then
        echo "[$(date)] Túnel SSH caiu, reconectando..."
        
        # Matar processos antigos
        pkill -f "ssh.*8080:localhost:8080" 2>/dev/null
        
        # Criar novo túnel
        sshpass -p "102030ab" ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=60 -o ServerAliveCountMax=3 -f -N -L 127.0.0.1:8081:localhost:8080 root@198.96.94.106
        
        if [ $? -eq 0 ]; then
            echo "[$(date)] ✅ Túnel SSH reconectado com sucesso"
        else
            echo "[$(date)] ❌ Falha ao reconectar túnel SSH"
        fi
    fi
    
    # Aguardar 30 segundos antes de verificar novamente
    sleep 30
done
