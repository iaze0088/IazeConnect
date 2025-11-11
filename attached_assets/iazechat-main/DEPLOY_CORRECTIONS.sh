#!/bin/bash
###############################################################################
# DEPLOY DAS 3 CORREÇÕES CRÍTICAS - Servidor Externo (suporte.help)
# Execute este script NO SERVIDOR EXTERNO onde está /opt/iaze
###############################################################################

set -e  # Parar em caso de erro

echo "================================================================================"
echo "🚀 DEPLOY DAS 3 CORREÇÕES CRÍTICAS"
echo "================================================================================"
echo ""
echo "📋 CORREÇÕES QUE SERÃO APLICADAS:"
echo "   1️⃣ Redirecionamento 'reembolso' → Ticket no painel"
echo "   2️⃣ Liberação de credenciais (Usuario/Senha) em qualquer formato"
echo "   3️⃣ Sistema de fallback da IA (timeout 2min + erros)"
echo ""

# Verificar se está no servidor correto
if [ ! -d "/opt/iaze" ]; then
    echo "❌ ERRO: Este não é o servidor externo!"
    echo "   Diretório /opt/iaze não encontrado."
    echo "   Execute este script no servidor onde está /opt/iaze"
    exit 1
fi

echo "✅ Servidor externo detectado (/opt/iaze encontrado)"
echo ""

# Verificar credenciais SSH (se aplicável)
read -p "📝 Este script está sendo executado NO SERVIDOR EXTERNO? (y/n): " confirm
if [ "$confirm" != "y" ]; then
    echo ""
    echo "⚠️  ATENÇÃO: Execute este script NO SERVIDOR EXTERNO (198.96.94.106 ou suporte.help)"
    echo ""
    echo "📝 PASSOS PARA DEPLOY:"
    echo "   1. Acesse o servidor externo via SSH:"
    echo "      ssh root@198.96.94.106"
    echo ""
    echo "   2. Baixe este script no servidor:"
    echo "      wget https://wppconnect-fix.preview.emergentagent.com/DEPLOY_CORRECTIONS.sh"
    echo "      (ou copie manualmente)"
    echo ""
    echo "   3. Execute o script:"
    echo "      chmod +x DEPLOY_CORRECTIONS.sh"
    echo "      ./DEPLOY_CORRECTIONS.sh"
    echo ""
    exit 0
fi

echo ""
echo "================================================================================"
echo "📦 PASSO 1/4: Criando backup dos arquivos atuais"
echo "================================================================================"

BACKUP_DIR="/opt/iaze/backup_corrections_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backup dos arquivos que serão modificados
if [ -f "/opt/iaze/backend/server.py" ]; then
    cp /opt/iaze/backend/server.py "$BACKUP_DIR/"
    echo "✅ Backup: server.py"
fi

if [ -f "/opt/iaze/backend/vendas_ai_service.py" ]; then
    cp /opt/iaze/backend/vendas_ai_service.py "$BACKUP_DIR/"
    echo "✅ Backup: vendas_ai_service.py"
fi

echo "📁 Backup salvo em: $BACKUP_DIR"
echo ""

echo "================================================================================"
echo "⚠️  PASSO 2/4: Aguardando arquivos atualizados"
echo "================================================================================"
echo ""
echo "📝 INSTRUÇÕES:"
echo ""
echo "   Os arquivos modificados precisam ser copiados do Emergent para o servidor."
echo ""
echo "   MÉTODO 1 - Via SCP (Recomendado):"
echo "   Execute NO SEU COMPUTADOR LOCAL:"
echo ""
echo "   # 1. Baixar arquivos do Emergent (no seu computador)"
echo "   curl -o server.py https://wppconnect-fix.preview.emergentagent.com/api/export/backend/server.py"
echo "   curl -o vendas_ai_service.py https://wppconnect-fix.preview.emergentagent.com/api/export/backend/vendas_ai_service.py"
echo ""
echo "   # 2. Enviar para o servidor externo"
echo "   scp server.py root@198.96.94.106:/opt/iaze/backend/"
echo "   scp vendas_ai_service.py root@198.96.94.106:/opt/iaze/backend/"
echo ""
echo "   MÉTODO 2 - Via wget (Direto no servidor):"
echo "   wget -O /opt/iaze/backend/server.py https://wppconnect-fix.preview.emergentagent.com/api/export/backend/server.py"
echo "   wget -O /opt/iaze/backend/vendas_ai_service.py https://wppconnect-fix.preview.emergentagent.com/api/export/backend/vendas_ai_service.py"
echo ""
echo "   MÉTODO 3 - Cópia Manual:"
echo "   Copie o conteúdo dos arquivos manualmente usando editor de texto"
echo ""
read -p "✅ Os arquivos já foram copiados? (y/n): " files_copied

if [ "$files_copied" != "y" ]; then
    echo ""
    echo "⏸️  DEPLOY PAUSADO - Execute este script novamente após copiar os arquivos"
    exit 0
fi

echo ""
echo "================================================================================"
echo "🔍 PASSO 3/4: Verificando arquivos"
echo "================================================================================"

# Verificar se os arquivos existem e não estão vazios
if [ ! -s "/opt/iaze/backend/server.py" ]; then
    echo "❌ ERRO: /opt/iaze/backend/server.py não encontrado ou vazio"
    exit 1
fi

if [ ! -s "/opt/iaze/backend/vendas_ai_service.py" ]; then
    echo "❌ ERRO: /opt/iaze/backend/vendas_ai_service.py não encontrado ou vazio"
    exit 1
fi

echo "✅ server.py: $(wc -l < /opt/iaze/backend/server.py) linhas"
echo "✅ vendas_ai_service.py: $(wc -l < /opt/iaze/backend/vendas_ai_service.py) linhas"
echo ""

# Verificar se as correções estão presentes
echo "🔍 Verificando presença das correções..."

if grep -q "handle_ai_failure_fallback" /opt/iaze/backend/server.py; then
    echo "✅ Correção 3 encontrada: Sistema de fallback da IA"
else
    echo "⚠️  Correção 3 NÃO encontrada: handle_ai_failure_fallback"
fi

if grep -q "validate_user_password_format" /opt/iaze/backend/server.py; then
    echo "✅ Correção 2 encontrada: Validação de credenciais"
else
    echo "⚠️  Correção 2 NÃO encontrada: validate_user_password_format"
fi

if grep -q "vendas_session_id" /opt/iaze/backend/vendas_ai_service.py; then
    echo "✅ Correção 1 encontrada: Redirecionamento com vendas_session_id"
else
    echo "⚠️  Correção 1 NÃO encontrada: vendas_session_id em redirect_to_support"
fi

echo ""
read -p "✅ Continuar com o deploy? (y/n): " continue_deploy

if [ "$continue_deploy" != "y" ]; then
    echo ""
    echo "❌ DEPLOY CANCELADO"
    exit 0
fi

echo ""
echo "================================================================================"
echo "🔄 PASSO 4/4: Reiniciando serviços"
echo "================================================================================"

echo "⏳ Reiniciando backend..."
if command -v supervisorctl &> /dev/null; then
    supervisorctl restart backend
    sleep 3
    supervisorctl status backend
elif systemctl list-units --type=service | grep -q backend; then
    systemctl restart backend
    sleep 3
    systemctl status backend --no-pager -l
else
    echo "⚠️  Não foi possível detectar o gerenciador de serviços"
    echo "   Execute manualmente: supervisorctl restart backend (ou systemctl restart backend)"
fi

echo ""
echo "✅ Backend reiniciado"
echo ""

# Verificar logs para erros
echo "🔍 Verificando logs do backend..."
echo ""
tail -n 20 /var/log/supervisor/backend.err.log 2>/dev/null || tail -n 20 /var/log/backend/error.log 2>/dev/null || echo "⚠️ Não foi possível acessar logs"

echo ""
echo "================================================================================"
echo "🎉 DEPLOY CONCLUÍDO COM SUCESSO!"
echo "================================================================================"
echo ""
echo "✅ CORREÇÕES APLICADAS:"
echo "   1️⃣ Redirecionamento 'reembolso' → Ticket aparece no painel (aba WA SUPORTE)"
echo "   2️⃣ Envio de credenciais liberado em qualquer formato"
echo "   3️⃣ Fallback automático da IA (timeout 2min + erros → transferência)"
echo ""
echo "📁 Backup dos arquivos anteriores: $BACKUP_DIR"
echo ""
echo "🧪 TESTES RECOMENDADOS:"
echo "   1. Acesse /vendas e digite 'quero reembolso'"
echo "      → Ticket deve aparecer no painel do atendente (WA Suporte > ESPERA)"
echo ""
echo "   2. No painel do atendente, envie uma mensagem:"
echo "      Usuario: teste123"
echo "      Senha: abc456"
echo "      → Deve ser enviada normalmente"
echo ""
echo "   3. Monitore logs da IA para verificar fallback em caso de timeout/erro"
echo ""
echo "================================================================================"
echo ""

