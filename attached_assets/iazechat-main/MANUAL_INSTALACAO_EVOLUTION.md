# 📋 MANUAL DE INSTALAÇÃO - EVOLUTION API V2.1.1

## 🎯 Objetivo
Instalar Evolution API V2.1.1 no servidor IAZE (151.243.218.223 / suporte.help)

---

## 📝 PASSO A PASSO

### 1️⃣ Conectar no Servidor via SSH

```bash
ssh root@151.243.218.223
# Senha: 102030ab
```

### 2️⃣ Baixar o Script de Instalação

```bash
cd /root
wget https://raw.githubusercontent.com/seu-repo/INSTALL_EVOLUTION_API_V2.sh
# OU copiar o conteúdo do arquivo INSTALL_EVOLUTION_API_V2.sh manualmente
```

**ALTERNATIVA (Copiar conteúdo manualmente):**

```bash
cd /root
nano INSTALL_EVOLUTION_API_V2.sh
# Cole o conteúdo do arquivo INSTALL_EVOLUTION_API_V2.sh aqui
# Salve com Ctrl+O, Enter, Ctrl+X
```

### 3️⃣ Dar Permissão de Execução

```bash
chmod +x INSTALL_EVOLUTION_API_V2.sh
```

### 4️⃣ Executar a Instalação

```bash
./INSTALL_EVOLUTION_API_V2.sh
```

**O script irá:**
- ✅ Verificar e instalar Docker (se necessário)
- ✅ Verificar e instalar Docker Compose (se necessário)
- ✅ Criar diretório `/opt/evolution-api`
- ✅ Criar `docker-compose.yml` com PostgreSQL, Redis e Evolution API
- ✅ Baixar e iniciar os containers
- ✅ Aguardar serviços ficarem prontos
- ✅ Testar a API
- ✅ Criar comando `evolution-ctl` para gerenciar

---

## 🔍 Verificações Após Instalação

### Verificar Containers Rodando
```bash
docker ps
```

Deve mostrar:
- `evolution_api` (porta 8080)
- `evolution_postgres` (porta 5432)
- `evolution_redis` (porta 6379)

### Testar Evolution API
```bash
curl http://localhost:8080/
```

Deve retornar:
```json
{
  "status": 200,
  "message": "Welcome to the Evolution API, it is working!",
  "version": "2.1.1"
}
```

### Ver Logs
```bash
evolution-ctl logs
# OU
cd /opt/evolution-api && docker-compose logs -f evolution-api
```

---

## 🧪 TESTAR CRIAÇÃO DE INSTÂNCIA

```bash
curl -X POST http://localhost:8080/instance/create \
  -H 'apikey: iaze-evolution-2025-secure-key' \
  -H 'Content-Type: application/json' \
  -d '{
    "instanceName": "teste_001",
    "integration": "WHATSAPP-BAILEYS",
    "qrcode": true
  }'
```

---

## 🛠️ COMANDOS ÚTEIS

### Gerenciar Evolution API
```bash
evolution-ctl start     # Iniciar
evolution-ctl stop      # Parar
evolution-ctl restart   # Reiniciar
evolution-ctl status    # Ver status
evolution-ctl logs      # Ver logs
```

### Gerenciar via Docker Compose
```bash
cd /opt/evolution-api

docker-compose ps           # Ver containers
docker-compose logs -f      # Ver todos os logs
docker-compose restart      # Reiniciar tudo
docker-compose down         # Parar tudo
docker-compose up -d        # Iniciar tudo
```

---

## 📊 INFORMAÇÕES DA INSTALAÇÃO

### Evolution API
- **URL Externa**: `http://151.243.218.223:8080`
- **URL Interna**: `http://localhost:8080`
- **API Key**: `iaze-evolution-2025-secure-key`
- **Porta**: `8080`

### PostgreSQL
- **Host**: `localhost:5432`
- **User**: `evolution`
- **Password**: `iaze-postgres-2025`
- **Database**: `evolution`

### Redis
- **Host**: `localhost:6379`

---

## ❌ SOLUÇÃO DE PROBLEMAS

### Porta 8080 já está em uso
```bash
# Ver o que está usando a porta
netstat -tuln | grep :8080
# OU
lsof -i :8080

# Ver containers na porta 8080
docker ps --filter "publish=8080"

# Parar container específico
docker stop CONTAINER_NAME
```

### Evolution API não inicia
```bash
# Ver logs detalhados
cd /opt/evolution-api
docker-compose logs evolution-api

# Reiniciar containers
docker-compose restart

# Recriar containers
docker-compose down
docker-compose up -d
```

### PostgreSQL com problemas
```bash
# Verificar se PostgreSQL está rodando
docker exec evolution_postgres pg_isready -U evolution

# Ver logs do PostgreSQL
docker-compose logs postgres
```

### Redis com problemas
```bash
# Testar conexão Redis
docker exec evolution_redis redis-cli ping

# Ver logs do Redis
docker-compose logs redis
```

---

## 🔄 ATUALIZAR EVOLUTION API

```bash
cd /opt/evolution-api

# Parar serviços
docker-compose down

# Atualizar imagem
docker-compose pull

# Iniciar novamente
docker-compose up -d
```

---

## 🗑️ DESINSTALAR

```bash
cd /opt/evolution-api

# Parar e remover containers + volumes
docker-compose down -v

# Remover diretório
cd /
rm -rf /opt/evolution-api

# Remover comando
rm -f /usr/local/bin/evolution-ctl
```

---

## 📞 PRÓXIMO PASSO

Após instalar com sucesso, **avisar o desenvolvedor** para atualizar o backend da IAZE e apontar para:

```
EVOLUTION_API_URL=http://localhost:8080
EVOLUTION_API_KEY=iaze-evolution-2025-secure-key
```

---

## ✅ CHECKLIST DE INSTALAÇÃO

- [ ] Conectar via SSH no servidor
- [ ] Baixar/copiar script de instalação
- [ ] Executar script `./INSTALL_EVOLUTION_API_V2.sh`
- [ ] Verificar containers rodando com `docker ps`
- [ ] Testar API com `curl http://localhost:8080/`
- [ ] Testar criação de instância
- [ ] Avisar desenvolvedor para atualizar backend

---

🎉 **Boa sorte com a instalação!**
