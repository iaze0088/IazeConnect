# Configuração Evolution API - Domínio Público

## ✅ Configuração Atual (RECOMENDADA)

**Evolution API URL**: `http://evolution.suporte.help:8080`  
**API Key**: `iaze-evolution-2025-secure-key`  
**Status**: ✅ Online e funcionando  
**Tipo**: Acesso direto via domínio público (SEM necessidade de SSH tunnel)

## Vantagens do Domínio Público

✅ **Mais Estável**: Sem dependência de SSH tunnel  
✅ **Mais Rápido**: Conexão direta HTTP  
✅ **Mais Simples**: Sem processos de manutenção  
✅ **Mais Confiável**: Sem risco de tunnel cair  

## Teste de Conectividade

```bash
# Testar se Evolution API está online
curl -s -o /dev/null -w "%{http_code}" http://evolution.suporte.help:8080/

# Listar instâncias
curl -s http://evolution.suporte.help:8080/instance/fetchInstances \
  -H "apikey: iaze-evolution-2025-secure-key"
```

## Configuração no Backend

**Arquivo**: `/app/backend/.env`

```env
EVOLUTION_API_URL="http://evolution.suporte.help:8080"
EVOLUTION_API_KEY="iaze-evolution-2025-secure-key"
```

## Status

- ✅ Evolution API acessível via domínio
- ✅ Backend configurado com nova URL
- ✅ Backend reiniciado
- ✅ SSH tunnel desativado (não mais necessário)
- ✅ Sistema pronto para criar conexões WhatsApp

## Próximos Passos

Agora você pode criar conexões WhatsApp normalmente pelo painel admin/reseller:

1. Acesse a aba **WhatsApp**
2. Clique em **"Criar Conexão"**
3. Preencha os dados
4. Escaneie o QR Code com seu celular
5. Pronto! ✅

---

## 📝 Histórico de Mudanças

**Antes**: SSH tunnel para `localhost:8081` → `198.96.94.106:8080`  
**Agora**: Acesso direto via `http://evolution.suporte.help:8080` ✅
