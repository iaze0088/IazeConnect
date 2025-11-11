# 🔧 Correção: Evolution API QR Code não está gerando

## 📋 Problema Identificado

**Sintoma:** Ao tentar gerar QR code (tanto no painel IAZE quanto no Evolution Manager), aparece apenas a mensagem "Scan the QR code with your WhatsApp Web" mas nenhum QR code é exibido.

**Causa:** WhatsApp Web atualizou seu protocolo em 2025, e a Evolution API 2.2.3 está usando uma versão antiga do cliente WhatsApp Web (`CONFIG_SESSION_PHONE_VERSION`).

**Fonte:** [GitHub Issue #1511](https://github.com/EvolutionAPI/evolution-api/issues/1511)

---

## ✅ Solução: Atualizar CONFIG_SESSION_PHONE_VERSION

### Método 1: Script Automático (Recomendado)

1. **Acesse o servidor via SSH** onde a Evolution API está rodando:
   ```bash
   ssh root@evolution.suporte.help
   ```

2. **Baixe e execute o script de correção:**
   ```bash
   # Se você tem acesso ao arquivo FIX_EVOLUTION_QR_CODE.sh
   chmod +x FIX_EVOLUTION_QR_CODE.sh
   ./FIX_EVOLUTION_QR_CODE.sh
   ```

3. **Siga as instruções do script** - ele vai:
   - Localizar o arquivo `.env` da Evolution API
   - Fazer backup automático
   - Atualizar `CONFIG_SESSION_PHONE_VERSION` para `2.3000.1025062854`
   - Reiniciar o serviço automaticamente

---

### Método 2: Manual

#### Passo 1: Localizar o arquivo `.env`

Localizações comuns:
- `/root/evolution-api/.env`
- `/opt/evolution-api/.env`
- `/var/www/evolution-api/.env`

```bash
# Procurar o arquivo
find / -name ".env" -path "*/evolution*" 2>/dev/null
```

#### Passo 2: Editar o arquivo

```bash
# Fazer backup primeiro
cp /caminho/para/.env /caminho/para/.env.backup

# Editar
nano /caminho/para/.env
```

#### Passo 3: Adicionar ou atualizar a variável

Procure por `CONFIG_SESSION_PHONE_VERSION`. Se existir, atualize:

```bash
# ANTES (versão antiga)
CONFIG_SESSION_PHONE_VERSION=2.3000.1015901307

# DEPOIS (versão nova - 2025)
CONFIG_SESSION_PHONE_VERSION=2.3000.1025062854
```

Se não existir, adicione ao final do arquivo:

```bash
# WhatsApp Web Version (updated for 2025 compatibility)
CONFIG_SESSION_PHONE_VERSION=2.3000.1025062854
```

#### Passo 4: Salvar e reiniciar

**Docker:**
```bash
docker restart <nome_do_container_evolution>
# ou
docker-compose restart
```

**PM2:**
```bash
pm2 restart evolution-api
```

**Systemd:**
```bash
sudo systemctl restart evolution-api
```

---

## 🧪 Testar a Correção

1. **Aguarde 10-15 segundos** após reiniciar

2. **Acesse o Evolution Manager:**
   ```
   http://evolution.suporte.help:8080/manager
   API Key: iaze-evolution-2025-secure-key
   ```

3. **Tente gerar um QR code**:
   - Clique em uma instância existente
   - Clique em "Connect" ou "Generate QR"
   - O QR code deve aparecer agora! ✅

4. **Teste no painel IAZE:**
   - Login: admin / 102030@ab
   - Vá para aba "WhatsApp"
   - Clique em "Ver QR Code" em uma conexão
   - O QR code deve ser exibido

---

## 🔍 Troubleshooting

### QR code ainda não aparece?

**1. Limpar cache do navegador:**
```
Chrome/Edge: Ctrl+Shift+Del
Firefox: Ctrl+Shift+Del
Safari: Cmd+Option+E
```

**2. Testar em modo anônimo/privado**

**3. Verificar logs da Evolution API:**
```bash
# Docker
docker logs <container_name> --tail 100 -f

# PM2
pm2 logs evolution-api

# Systemd
journalctl -u evolution-api -n 100 -f
```

**4. Verificar se a variável foi aplicada:**
```bash
# Dentro do container Docker
docker exec <container_name> env | grep CONFIG_SESSION_PHONE_VERSION

# Deve retornar:
# CONFIG_SESSION_PHONE_VERSION=2.3000.1025062854
```

**5. Deletar instâncias antigas e criar novas:**
- No Evolution Manager, delete todas as instâncias
- Crie uma nova instância
- Tente gerar o QR code

---

## 📦 Versões Testadas

| Componente | Versão | Status |
|------------|--------|--------|
| Evolution API | 2.2.3 | ✅ Corrigido |
| WhatsApp Web | 2.3000.1025062854 | ✅ Compatível |
| Baileys | Latest | ✅ Atualizado |

---

## 🔄 Alternativa: Atualizar Evolution API para v2.3+

Se a correção acima não funcionar, considere atualizar para a versão mais recente:

```bash
# Docker
docker pull atendai/evolution-api:latest
docker-compose down
docker-compose up -d

# Verificar versão
curl http://evolution.suporte.help:8080/
```

---

## 📚 Referências

- [Evolution API GitHub Issue #1511](https://github.com/EvolutionAPI/evolution-api/issues/1511)
- [Evolution API Documentation](https://doc.evolution-api.com)
- [WhatsApp Web Protocol Updates](https://github.com/WhiskeySockets/Baileys)

---

## ✅ Confirmação de Sucesso

Após aplicar a correção, você deve ver:

1. ✅ QR code aparecendo no Evolution Manager
2. ✅ QR code aparecendo no painel IAZE
3. ✅ Conexão estabelecida após escanear com WhatsApp
4. ✅ Status mudando para "Conectado" ✅

---

**Data:** 31 de Outubro de 2025  
**Issue:** Evolution API QR Code Generation (WhatsApp Web 2025)  
**Status:** CORREÇÃO DOCUMENTADA ✅
