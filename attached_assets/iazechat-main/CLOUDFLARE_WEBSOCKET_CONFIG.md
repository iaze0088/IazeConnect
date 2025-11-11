# 🔧 Configuração do Cloudflare para WebSocket

## ⚠️ Problema Identificado

O WebSocket não funciona através do Cloudflare porque o Cloudflare está bloqueando ou não roteando corretamente as conexões WebSocket.

## ✅ Solução: Configurar Cloudflare

### Opção 1: Ativar WebSockets no Cloudflare (RECOMENDADO)

1. **Acesse o dashboard do Cloudflare**: https://dash.cloudflare.com
2. **Selecione o domínio**: `suporte.help`
3. **Vá para "Network"**
4. **Ative "WebSockets"**: Deve estar em `ON`

### Opção 2: Bypass Cloudflare para WebSocket

Crie um subdomínio específico para WebSocket que não passe pelo Cloudflare:

1. **No Cloudflare DNS**:
   - Adicione um registro A: `ws.suporte.help` → `198.96.94.106`
   - **IMPORTANTE**: Desative o proxy (clique na nuvem laranja até ficar cinza ☁️ → DNS only)

2. **Atualize o frontend** para usar `wss://ws.suporte.help/api`:
   ```bash
   ssh root@198.96.94.106
   # Edite /app/src/lib/api.js no container iaze_frontend
   # Altere a URL do WebSocket para wss://ws.suporte.help/api
   docker restart iaze_frontend
   ```

### Opção 3: Configurar Cloudflare Workers (Avançado)

Se as opções acima não funcionarem, você pode usar Cloudflare Workers para rotear WebSockets.

## 🧪 Teste

Após configurar, teste o WebSocket:

```bash
# Teste 1: Verificar se WebSocket está acessível
curl -I -N -H "Connection: Upgrade" -H "Upgrade: websocket" \
  -H "Sec-WebSocket-Version: 13" -H "Sec-WebSocket-Key: test" \
  https://suporte.help/api/ws/test/test

# Teste 2: No navegador (Console do DevTools)
const ws = new WebSocket('wss://suporte.help/api/ws/test-user/test-session');
ws.onopen = () => console.log('✅ Conectado!');
ws.onerror = (e) => console.log('❌ Erro:', e);
```

## 📊 Status Atual

- ✅ Backend funcionando (porta 8001)
- ✅ Nginx configurado com suporte a WebSocket
- ✅ WebSocket acessível diretamente (ws://198.96.94.106:8001)
- ❌ WebSocket bloqueado através do Cloudflare (wss://suporte.help)

## 🔍 Logs Úteis

```bash
# Ver logs do Nginx
tail -f /var/log/nginx/error.log

# Ver logs do backend
docker logs -f iaze_backend | grep -i websocket

# Ver tentativas de conexão WebSocket
docker logs -f iaze_backend | grep "GET /api/ws"
```

## 📝 Notas

- O Cloudflare **suporta WebSockets** em todos os planos (incluindo Free)
- WebSockets devem estar habilitados no dashboard
- Se estiver usando Cloudflare, DEVE usar `wss://` (não `ws://`)
- Mixed content (HTTPS com WS) é bloqueado pelos navegadores
