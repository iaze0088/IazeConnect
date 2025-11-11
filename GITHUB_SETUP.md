# 🚀 Guia de Upload para GitHub

## 📋 Pré-requisitos

1. **Criar repositório no GitHub:**
   - Acesse: https://github.com/iaze0088
   - Clique em **"New repository"**
   - Nome sugerido: `iaze-sistema` ou `iaze-whatsapp`
   - **NÃO** marque "Initialize with README"
   - Clique em **"Create repository"**

2. **Criar Personal Access Token:**
   - Acesse: https://github.com/settings/tokens
   - Clique em **"Generate new token (classic)"**
   - Nome: `Replit IAZE`
   - Selecione escopo: `repo` (marque todos os itens)
   - Clique em **"Generate token"**
   - **COPIE O TOKEN** (você só verá uma vez!)

---

## 🔧 Método 1: Via Interface Git do Replit (RECOMENDADO)

### Passo 1: Abrir Git Pane
1. No Replit, clique em **"Tools"** (🔧) no menu lateral esquerdo
2. Selecione **"Git"** ou procure por "Version Control"

### Passo 2: Conectar ao GitHub
1. Clique em **"Connect to GitHub"** ou **"Initialize Git"**
2. Se aparecer "Already initialized", clique em **"Add Remote"**
3. Cole a URL do seu repositório:
   ```
   https://github.com/iaze0088/NOME-DO-SEU-REPO.git
   ```

### Passo 3: Commit e Push
1. **Stage files**: Marque todos os arquivos que deseja enviar
2. **Commit message**: Digite "Initial commit - Sistema IAZE completo"
3. Clique em **"Commit & Push"**
4. Se pedir credenciais, use:
   - **Username**: iaze0088
   - **Password**: SEU_PERSONAL_ACCESS_TOKEN

---

## 💻 Método 2: Via Shell (Linha de Comando)

### Passo 1: Adicionar Token como Secret
1. No Replit, clique em **"Tools"** → **"Secrets"**
2. Adicione um novo secret:
   - **Key**: `GITHUB_TOKEN`
   - **Value**: Seu Personal Access Token

### Passo 2: Configurar Git
```bash
# No Shell do Replit, execute:

# 1. Verificar status do Git
git status

# 2. Adicionar repositório remoto (substitua NOME-DO-REPO)
git remote add github https://github.com/iaze0088/NOME-DO-REPO.git

# 3. Verificar remotes
git remote -v

# 4. Adicionar todos os arquivos
git add .

# 5. Fazer commit
git commit -m "Initial commit - Sistema IAZE completo"

# 6. Push para GitHub (usando token)
git push https://iaze0088:$GITHUB_TOKEN@github.com/iaze0088/NOME-DO-REPO.git main

# OU se a branch for master:
git push https://iaze0088:$GITHUB_TOKEN@github.com/iaze0088/NOME-DO-REPO.git master
```

---

## 📝 Criar arquivo .gitignore

Antes de fazer o commit, certifique-se de que existe um `.gitignore` adequado:

```gitignore
# Node modules
node_modules/
package-lock.json

# Environment variables
.env
.env.local
.env.production

# Logs
logs/
*.log
npm-debug.log*

# Build files
dist/
build/
.cache/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Replit
.replit
replit.nix
.config/
.upm/

# Database
*.db
*.sqlite

# Temporary files
/tmp/
*.tmp
```

---

## ✅ Verificar Upload

Depois do push, verifique no GitHub:
1. Acesse: `https://github.com/iaze0088/NOME-DO-REPO`
2. Verifique se todos os arquivos foram enviados
3. Verifique se o `.gitignore` está funcionando (node_modules não deve estar no GitHub)

---

## 🔄 Atualizações Futuras

Quando fizer alterações no código:

```bash
# Via Shell
git add .
git commit -m "Descrição das mudanças"
git push https://iaze0088:$GITHUB_TOKEN@github.com/iaze0088/NOME-DO-REPO.git main
```

**OU** use a interface Git do Replit:
1. Tools → Git
2. Stage changes
3. Commit & Push

---

## 🚀 Deploy do GitHub para Servidor

Depois de subir para o GitHub, no seu servidor:

```bash
# 1. Clone o repositório
cd /var/www
git clone https://github.com/iaze0088/NOME-DO-REPO.git iaze

# 2. Entre no diretório
cd iaze

# 3. Instale dependências
npm install --production

# 4. Configure .env
nano .env

# 5. Inicie com PM2
pm2 start ecosystem.config.js
pm2 save
```

---

## 🔐 Segurança

⚠️ **NUNCA** commite:
- Senhas
- Tokens
- Chaves API
- Arquivo `.env`
- Credenciais de banco de dados

Use o arquivo `.gitignore` para excluir arquivos sensíveis!

---

## 📞 Troubleshooting

### Erro: "Authentication failed"
- Verifique se o Personal Access Token está correto
- Certifique-se de que o token tem permissão `repo`

### Erro: "Repository not found"
- Verifique se o nome do repositório está correto
- Certifique-se de que o repositório foi criado no GitHub

### Erro: "Permission denied"
- Use o Personal Access Token ao invés de senha
- Verifique se você é owner do repositório

---

## 🎉 Pronto!

Agora seu código está no GitHub e pode ser:
- Clonado em qualquer servidor
- Compartilhado com a equipe
- Versionado e controlado
- Facilmente deployado
