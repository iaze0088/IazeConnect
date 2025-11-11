# 📦 Evolution API - Backup e Localização

## 🎯 Resumo Executivo

Os arquivos da **Evolution API v2.3.6** foram salvos com sucesso no servidor para uso futuro.

---

## 📍 Localização dos Arquivos

### Servidor Evolution
- **IP:** 198.96.94.106
- **Usuário:** root
- **Senha:** 102030ab

### Estrutura de Diretórios

```
/root/evolution-api-sources/
├── evolution-api-2.3.6.tar.gz    (1.3 MB)
├── evolution-api-2.3.6.zip       (1.5 MB)
└── README_EVOLUTION.md           (4.0 KB)
```

---

## 📚 Documentação Completa

**Arquivo Principal:** `/root/evolution-api-sources/README_EVOLUTION.md`

Este arquivo contém:
- ✅ Comandos de backup
- ✅ Instruções de migração para v2.3.6
- ✅ Comandos úteis do Docker
- ✅ Como restaurar dados
- ✅ Troubleshooting
- ✅ Histórico de versões

---

## 🚀 Versão Atual em Produção

### Evolution API v1.8.5
- **Status:** ✅ Rodando
- **Container:** evolution_api
- **Porta:** 8080 (interna)
- **Acesso IAZE:** Via túnel SSH em localhost:8081
- **API Key:** iaze-evolution-2025-secure-key

### Comandos Rápidos

```bash
# Conectar ao servidor
ssh root@198.96.94.106

# Ver status
docker ps | grep evolution

# Ver logs
docker logs evolution_api -f

# Reiniciar
docker restart evolution_api
```

---

## 🔄 Como Usar os Arquivos Salvos

### Quando Precisar da v2.3.6:

**1. Conectar ao servidor:**
```bash
ssh root@198.96.94.106
```

**2. Navegar até os arquivos:**
```bash
cd /root/evolution-api-sources
ls -lh
```

**3. Extrair (escolha um):**
```bash
# Opção A - tar.gz
tar -xzf evolution-api-2.3.6.tar.gz

# Opção B - zip
unzip evolution-api-2.3.6.zip
```

**4. Seguir instruções:**
```bash
# Ler o README completo
cat README_EVOLUTION.md

# Ou seguir documentação da v2.3.6
cd evolution-api-2.3.6
cat README.md  # (do próprio pacote)
```

---

## 🔐 Backup Strategy

### O que foi Salvo:
- ✅ Código fonte completo da Evolution API v2.3.6
- ✅ Duas versões (tar.gz e zip) para compatibilidade
- ✅ Documentação detalhada de migração
- ✅ Comandos de backup e restore

### O que NÃO foi Salvo (e como fazer):
**Dados da instalação atual (v1.8.5):**
```bash
# Backup do banco de dados
docker exec evolution_postgres pg_dump -U evolution evolution > evolution_backup_$(date +%Y%m%d).sql

# Backup dos volumes
docker run --rm -v evolution_store:/data -v /root/evolution-backups:/backup alpine tar czf /backup/evolution_store_$(date +%Y%m%d).tar.gz -C /data .
```

---

## 📊 Comparação de Versões

| Item | v1.8.5 (Atual) | v2.3.6 (Backup) |
|------|----------------|-----------------|
| Status | ✅ Em produção | 💾 Arquivado |
| Localização | Docker Container | /root/evolution-api-sources/ |
| Tamanho | Running | 1.3 MB (compactado) |
| Documentação | Online | /root/evolution-api-sources/README_EVOLUTION.md |

---

## 🎯 Quando Migrar para v2.3.6?

### Considere migrar quando:
- ✅ Precisar de features específicas da v2.3.6
- ✅ Houver bugs críticos na v1.8.5
- ✅ Tiver tempo para testar em desenvolvimento primeiro
- ✅ Tiver backup completo dos dados atuais

### Antes de migrar:
1. Fazer backup completo (DB + volumes)
2. Testar em ambiente de desenvolvimento
3. Ler changelog da v2.3.6
4. Verificar breaking changes
5. Planejar downtime (se necessário)

---

## 📝 Checklist de Acesso Rápido

```bash
# ✅ Conectar ao servidor Evolution
ssh root@198.96.94.106
# Senha: 102030ab

# ✅ Ver arquivos salvos
ls -lh /root/evolution-api-sources/

# ✅ Ler documentação completa
cat /root/evolution-api-sources/README_EVOLUTION.md

# ✅ Ver versão atual rodando
docker ps | grep evolution

# ✅ Verificar logs
docker logs evolution_api -f

# ✅ Testar API
curl http://localhost:8080
```

---

## 🆘 Suporte

### Em caso de dúvidas:
1. Consultar: `/root/evolution-api-sources/README_EVOLUTION.md`
2. Documentação oficial: https://doc.evolution-api.com
3. Verificar logs: `docker logs evolution_api`

### Contatos de Emergência:
- **Servidor:** 198.96.94.106
- **Acesso:** root / 102030ab
- **Túnel SSH:** localhost:8081 (IAZE Backend)

---

## ✅ Status Final

**Arquivos Salvos:**
- ✅ evolution-api-2.3.6.tar.gz (1.3 MB)
- ✅ evolution-api-2.3.6.zip (1.5 MB)
- ✅ README_EVOLUTION.md (documentação completa)

**Localização:**
- ✅ Servidor: 198.96.94.106
- ✅ Diretório: /root/evolution-api-sources/
- ✅ Acesso: ssh root@198.96.94.106

**Versão Atual Rodando:**
- ✅ v1.8.5 - Estável e funcionando
- ✅ Conectada ao IAZE via túnel SSH
- ✅ Sem necessidade de migração imediata

---

**Documento criado em:** 27/10/2024  
**Última verificação:** 27/10/2024  
**Status:** ✅ Todos os arquivos salvos e verificados
