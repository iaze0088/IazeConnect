# SSH Tunnel para Evolution API - Guia de Setup

## Problema Resolvido
**Erro**: "All connection attempts failed" ao criar conexão WhatsApp

**Causa**: SSH tunnel não estava ativo para acessar Evolution API via `localhost:8081`

## Configuração

### Evolution API (Servidor Remoto)
- **Host**: 198.96.94.106
- **Porta Remota**: 8080 (Evolution API)
- **Porta Local (Tunnel)**: 8081
- **Credenciais SSH**: root / 102030ab

### Backend IAZE
- **EVOLUTION_API_URL**: http://localhost:8081
- **EVOLUTION_API_KEY**: iaze-evolution-2025-secure-key

## Solução Implementada

### 1. Instalação do sshpass
```bash
apt-get update && apt-get install -y sshpass
```

### 2. Estabelecer SSH Tunnel Manual
```bash
sshpass -p "102030ab" ssh -o StrictHostKeyChecking=no \
  -o ServerAliveInterval=60 \
  -o ServerAliveCountMax=3 \
  -o ConnectTimeout=10 \
  -f -N -L 127.0.0.1:8081:localhost:8080 \
  root@198.96.94.106
```

### 3. Script de Manutenção Automática
- **Arquivo**: `/app/keep_ssh_tunnel.sh`
- **Função**: Verifica e reconecta o tunnel a cada 30 segundos se cair
- **Execução**: 
```bash
nohup bash /app/keep_ssh_tunnel.sh > /tmp/ssh_tunnel.log 2>&1 &
```

### 4. Verificar Status do Tunnel
```bash
# Verificar processo SSH ativo
pgrep -a ssh | grep 8081

# Testar conectividade
curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/

# Ver logs do script de manutenção
tail -f /tmp/ssh_tunnel.log
```

## Status Atual
✅ SSH tunnel estabelecido e ativo
✅ Evolution API acessível via localhost:8081
✅ Script de manutenção rodando (PID: 2166)
✅ Backend configurado corretamente
✅ Sistema pronto para criar conexões WhatsApp

## Troubleshooting

### Se o tunnel cair:
1. Verificar se o script de manutenção está ativo:
   ```bash
   ps aux | grep keep_ssh_tunnel.sh
   ```

2. Se não estiver, reiniciar:
   ```bash
   nohup bash /app/keep_ssh_tunnel.sh > /tmp/ssh_tunnel.log 2>&1 &
   ```

3. Verificar logs:
   ```bash
   tail -20 /tmp/ssh_tunnel.log
   ```

### Se Evolution API não responder:
1. Verificar se está rodando no servidor remoto (198.96.94.106)
2. Verificar firewall no servidor remoto
3. Verificar credenciais SSH

## Notas Importantes
- O tunnel usa porta local 8081 → porta remota 8080
- KeepAlive configurado para detectar conexões perdidas
- Reconexão automática em caso de queda
- Log disponível em `/tmp/ssh_tunnel.log`
