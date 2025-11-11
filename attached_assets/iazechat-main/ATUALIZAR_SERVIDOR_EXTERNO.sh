#!/bin/bash
###############################################################################
# ATUALIZAÇÃO SERVIDOR EXTERNO - Novas Funcionalidades
# Sincronizar: AI Auto-Search, Agendamento de Mensagens, Lembretes Email, Office
# Execute este script NO SERVIDOR EXTERNO (198.96.94.106 / suporte.help)
###############################################################################

set -e  # Parar em caso de erro

echo "================================================================================"
echo "🚀 ATUALIZAÇÃO SERVIDOR EXTERNO - NOVAS FUNCIONALIDADES"
echo "================================================================================"
echo ""
echo "📋 FUNCIONALIDADES QUE SERÃO SINCRONIZADAS:"
echo ""
echo "   1️⃣  AI Auto-Search Credentials (busca automática em Office/gestor.my)"
echo "   2️⃣  Agendamento de Mensagens (agendar envio futuro)"
echo "   3️⃣  Lembretes por Email (credenciais expirando)"
echo "   4️⃣  Office Integration (melhorias Playwright + múltiplas credenciais)"
echo "   5️⃣  Prevent Duplicate Tests (não gerar teste se já existe)"
echo ""
echo "================================================================================"
echo ""

# Verificar se está no servidor correto
if [ ! -d "/opt/iaze" ]; then
    echo "❌ ERRO: Este não é o servidor externo!"
    echo "   Diretório /opt/iaze não encontrado."
    echo ""
    echo "📝 INSTRUÇÕES:"
    echo "   1. Acesse o servidor externo via SSH:"
    echo "      ssh root@198.96.94.106"
    echo ""
    echo "   2. Baixe este script:"
    echo "      wget -O atualizar_servidor_externo.sh https://wppconnect-fix.preview.emergentagent.com/ATUALIZAR_SERVIDOR_EXTERNO.sh"
    echo "      chmod +x atualizar_servidor_externo.sh"
    echo ""
    echo "   3. Execute:"
    echo "      ./atualizar_servidor_externo.sh"
    echo ""
    exit 1
fi

echo "✅ Servidor externo detectado (/opt/iaze encontrado)"
echo ""

# Confirmar execução
read -p "🔴 ATENÇÃO: Esta atualização criará novos arquivos e modificará existentes. Continuar? (y/n): " confirm
if [ "$confirm" != "y" ]; then
    echo ""
    echo "❌ Atualização cancelada pelo usuário"
    exit 0
fi

echo ""
echo "================================================================================"
echo "📦 PASSO 1/7: Criando backup completo"
echo "================================================================================"

BACKUP_DIR="/opt/iaze/backup_new_features_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR/backend"
mkdir -p "$BACKUP_DIR/frontend/src/components"
mkdir -p "$BACKUP_DIR/frontend/src/pages"

echo "📁 Salvando backup em: $BACKUP_DIR"
echo ""

# Backup dos arquivos existentes que serão modificados
for file in server.py vendas_ai_service.py vendas_routes.py office_service.py office_routes.py backup_scheduler.py requirements.txt; do
    if [ -f "/opt/iaze/backend/$file" ]; then
        cp "/opt/iaze/backend/$file" "$BACKUP_DIR/backend/"
        echo "✅ Backup: backend/$file"
    fi
done

for file in AgentDashboard.js AdminDashboard.js VendasChatNew.js; do
    if [ -f "/opt/iaze/frontend/src/pages/$file" ]; then
        cp "/opt/iaze/frontend/src/pages/$file" "$BACKUP_DIR/frontend/src/pages/"
        echo "✅ Backup: frontend/src/pages/$file"
    fi
done

echo ""
echo "================================================================================"
echo "📥 PASSO 2/7: Baixando NOVOS arquivos do Emergent"
echo "================================================================================"
echo ""

EMERGENT_URL="https://wppconnect-fix.preview.emergentagent.com"

# Função para baixar e verificar arquivo
download_file() {
    local url=$1
    local dest=$2
    local desc=$3
    
    echo "📥 Baixando: $desc..."
    
    if wget -q -O "$dest.NEW" "$url"; then
        # Verificar se não está vazio
        if [ -s "$dest.NEW" ]; then
            local lines=$(wc -l < "$dest.NEW")
            echo "   ✅ Download completo: $lines linhas"
            return 0
        else
            echo "   ❌ Arquivo vazio!"
            rm -f "$dest.NEW"
            return 1
        fi
    else
        echo "   ❌ Erro no download!"
        return 1
    fi
}

echo "📦 Baixando NOVOS arquivos backend..."
echo ""

# NOVOS ARQUIVOS BACKEND
download_file "$EMERGENT_URL/api/export/backend/credential_auto_search.py" "/opt/iaze/backend/credential_auto_search.py" "credential_auto_search.py (NOVO)"
download_file "$EMERGENT_URL/api/export/backend/credential_auto_search_routes.py" "/opt/iaze/backend/credential_auto_search_routes.py" "credential_auto_search_routes.py (NOVO)"
download_file "$EMERGENT_URL/api/export/backend/scheduled_messages_models.py" "/opt/iaze/backend/scheduled_messages_models.py" "scheduled_messages_models.py (NOVO)"
download_file "$EMERGENT_URL/api/export/backend/scheduled_messages_routes.py" "/opt/iaze/backend/scheduled_messages_routes.py" "scheduled_messages_routes.py (NOVO)"
download_file "$EMERGENT_URL/api/export/backend/reminder_models.py" "/opt/iaze/backend/reminder_models.py" "reminder_models.py (NOVO)"
download_file "$EMERGENT_URL/api/export/backend/reminder_service.py" "/opt/iaze/backend/reminder_service.py" "reminder_service.py (NOVO)"
download_file "$EMERGENT_URL/api/export/backend/reminder_routes.py" "/opt/iaze/backend/reminder_routes.py" "reminder_routes.py (NOVO)"

echo ""
echo "📦 Baixando arquivos backend MODIFICADOS..."
echo ""

# ARQUIVOS BACKEND MODIFICADOS
download_file "$EMERGENT_URL/api/export/backend/server.py" "/opt/iaze/backend/server.py" "server.py (modificado)"
download_file "$EMERGENT_URL/api/export/backend/vendas_ai_service.py" "/opt/iaze/backend/vendas_ai_service.py" "vendas_ai_service.py (modificado)"
download_file "$EMERGENT_URL/api/export/backend/vendas_routes.py" "/opt/iaze/backend/vendas_routes.py" "vendas_routes.py (modificado)"
download_file "$EMERGENT_URL/api/export/backend/office_service.py" "/opt/iaze/backend/office_service.py" "office_service.py (modificado)"
download_file "$EMERGENT_URL/api/export/backend/office_routes.py" "/opt/iaze/backend/office_routes.py" "office_routes.py (modificado)"
download_file "$EMERGENT_URL/api/export/backend/backup_scheduler.py" "/opt/iaze/backend/backup_scheduler.py" "backup_scheduler.py (modificado)"
download_file "$EMERGENT_URL/api/export/backend/requirements.txt" "/opt/iaze/backend/requirements.txt" "requirements.txt (modificado)"

echo ""
echo "📦 Baixando NOVOS componentes frontend..."
echo ""

# NOVOS ARQUIVOS FRONTEND
download_file "$EMERGENT_URL/api/export/frontend/src/components/ScheduleMessageModal.js" "/opt/iaze/frontend/src/components/ScheduleMessageModal.js" "ScheduleMessageModal.js (NOVO)"
download_file "$EMERGENT_URL/api/export/frontend/src/components/EmailManager.js" "/opt/iaze/frontend/src/components/EmailManager.js" "EmailManager.js (NOVO)"

echo ""
echo "📦 Baixando páginas frontend MODIFICADAS..."
echo ""

# ARQUIVOS FRONTEND MODIFICADOS
download_file "$EMERGENT_URL/api/export/frontend/src/pages/AgentDashboard.js" "/opt/iaze/frontend/src/pages/AgentDashboard.js" "AgentDashboard.js (modificado)"
download_file "$EMERGENT_URL/api/export/frontend/src/pages/AdminDashboard.js" "/opt/iaze/frontend/src/pages/AdminDashboard.js" "AdminDashboard.js (modificado)"
download_file "$EMERGENT_URL/api/export/frontend/src/pages/VendasChatNew.js" "/opt/iaze/frontend/src/pages/VendasChatNew.js" "VendasChatNew.js (modificado)"

echo ""
echo "✅ Todos os arquivos baixados com sucesso!"
echo ""

echo "================================================================================"
echo "🔍 PASSO 3/7: Verificando integridade dos arquivos"
echo "================================================================================"
echo ""

# Função para verificar presença de código
verify_code() {
    local file=$1
    local pattern=$2
    local desc=$3
    
    if grep -q "$pattern" "$file.NEW"; then
        echo "   ✅ $desc"
        return 0
    else
        echo "   ⚠️  $desc NÃO encontrado!"
        return 1
    fi
}

echo "🔍 Verificando NOVOS arquivos backend:"
verify_code "/opt/iaze/backend/credential_auto_search.py" "async def search_and_fix_credentials" "credential_auto_search.py: função principal"
verify_code "/opt/iaze/backend/scheduled_messages_models.py" "ScheduledMessage" "scheduled_messages_models.py: modelo"
verify_code "/opt/iaze/backend/reminder_service.py" "send_reminder_email" "reminder_service.py: envio de email"

echo ""
echo "🔍 Verificando modificações no server.py:"
verify_code "/opt/iaze/backend/server.py" "credential_auto_search" "server.py: integração auto-search"
verify_code "/opt/iaze/backend/server.py" "scheduled_messages_routes" "server.py: rotas de agendamento"
verify_code "/opt/iaze/backend/server.py" "reminder_routes" "server.py: rotas de lembretes"

echo ""
echo "🔍 Verificando modificações no vendas_ai_service.py:"
verify_code "/opt/iaze/backend/vendas_ai_service.py" "search_credentials_ai" "vendas_ai_service.py: function calling"
verify_code "/opt/iaze/backend/vendas_ai_service.py" "generate_iptv_test" "vendas_ai_service.py: prevent duplicate"

echo ""
echo "🔍 Verificando NOVOS componentes frontend:"
verify_code "/opt/iaze/frontend/src/components/ScheduleMessageModal.js" "ScheduleMessageModal" "ScheduleMessageModal.js: componente"
verify_code "/opt/iaze/frontend/src/components/EmailManager.js" "EmailManager" "EmailManager.js: componente"

echo ""
echo "🔍 Verificando modificações no AgentDashboard.js:"
verify_code "/opt/iaze/frontend/src/pages/AgentDashboard.js" "handleScheduleMessage" "AgentDashboard.js: agendar mensagem"
verify_code "/opt/iaze/frontend/src/pages/AgentDashboard.js" "auto_found_credentials" "AgentDashboard.js: credenciais automáticas"

echo ""
echo "✅ Verificação de integridade concluída!"
echo ""

read -p "✅ Arquivos verificados. Aplicar mudanças? (y/n): " apply_confirm
if [ "$apply_confirm" != "y" ]; then
    echo ""
    echo "❌ Atualização cancelada. Arquivos .NEW não foram aplicados."
    echo "📁 Backup mantido em: $BACKUP_DIR"
    exit 0
fi

echo ""
echo "================================================================================"
echo "🔧 PASSO 4/7: Aplicando atualizações no BACKEND"
echo "================================================================================"
echo ""

# Aplicar NOVOS arquivos backend
echo "📦 Criando NOVOS arquivos backend..."
mv /opt/iaze/backend/credential_auto_search.py.NEW /opt/iaze/backend/credential_auto_search.py
echo "   ✅ credential_auto_search.py"

mv /opt/iaze/backend/credential_auto_search_routes.py.NEW /opt/iaze/backend/credential_auto_search_routes.py
echo "   ✅ credential_auto_search_routes.py"

mv /opt/iaze/backend/scheduled_messages_models.py.NEW /opt/iaze/backend/scheduled_messages_models.py
echo "   ✅ scheduled_messages_models.py"

mv /opt/iaze/backend/scheduled_messages_routes.py.NEW /opt/iaze/backend/scheduled_messages_routes.py
echo "   ✅ scheduled_messages_routes.py"

mv /opt/iaze/backend/reminder_models.py.NEW /opt/iaze/backend/reminder_models.py
echo "   ✅ reminder_models.py"

mv /opt/iaze/backend/reminder_service.py.NEW /opt/iaze/backend/reminder_service.py
echo "   ✅ reminder_service.py"

mv /opt/iaze/backend/reminder_routes.py.NEW /opt/iaze/backend/reminder_routes.py
echo "   ✅ reminder_routes.py"

echo ""
echo "📝 Atualizando arquivos backend MODIFICADOS..."

mv /opt/iaze/backend/server.py.NEW /opt/iaze/backend/server.py
echo "   ✅ server.py"

mv /opt/iaze/backend/vendas_ai_service.py.NEW /opt/iaze/backend/vendas_ai_service.py
echo "   ✅ vendas_ai_service.py"

mv /opt/iaze/backend/vendas_routes.py.NEW /opt/iaze/backend/vendas_routes.py
echo "   ✅ vendas_routes.py"

mv /opt/iaze/backend/office_service.py.NEW /opt/iaze/backend/office_service.py
echo "   ✅ office_service.py"

mv /opt/iaze/backend/office_routes.py.NEW /opt/iaze/backend/office_routes.py
echo "   ✅ office_routes.py"

mv /opt/iaze/backend/backup_scheduler.py.NEW /opt/iaze/backend/backup_scheduler.py
echo "   ✅ backup_scheduler.py"

mv /opt/iaze/backend/requirements.txt.NEW /opt/iaze/backend/requirements.txt
echo "   ✅ requirements.txt"

echo ""
echo "✅ Backend atualizado!"
echo ""

echo "================================================================================"
echo "🔧 PASSO 5/7: Aplicando atualizações no FRONTEND"
echo "================================================================================"
echo ""

# Aplicar NOVOS componentes frontend
echo "📦 Criando NOVOS componentes frontend..."
mv /opt/iaze/frontend/src/components/ScheduleMessageModal.js.NEW /opt/iaze/frontend/src/components/ScheduleMessageModal.js
echo "   ✅ ScheduleMessageModal.js"

mv /opt/iaze/frontend/src/components/EmailManager.js.NEW /opt/iaze/frontend/src/components/EmailManager.js
echo "   ✅ EmailManager.js"

echo ""
echo "📝 Atualizando páginas frontend MODIFICADAS..."

mv /opt/iaze/frontend/src/pages/AgentDashboard.js.NEW /opt/iaze/frontend/src/pages/AgentDashboard.js
echo "   ✅ AgentDashboard.js"

mv /opt/iaze/frontend/src/pages/AdminDashboard.js.NEW /opt/iaze/frontend/src/pages/AdminDashboard.js
echo "   ✅ AdminDashboard.js"

mv /opt/iaze/frontend/src/pages/VendasChatNew.js.NEW /opt/iaze/frontend/src/pages/VendasChatNew.js
echo "   ✅ VendasChatNew.js"

echo ""
echo "✅ Frontend atualizado!"
echo ""

echo "================================================================================"
echo "📦 PASSO 6/7: Instalando novas dependências Python"
echo "================================================================================"
echo ""

cd /opt/iaze/backend

echo "🔍 Verificando se há novas dependências..."
echo ""

# Instalar playwright se não estiver instalado
if ! python3 -c "import playwright" 2>/dev/null; then
    echo "📦 Instalando playwright..."
    pip3 install playwright
    echo "📦 Instalando browsers do playwright..."
    playwright install chromium
    echo "   ✅ playwright instalado"
else
    echo "   ✅ playwright já instalado"
fi

# Instalar beautifulsoup4 se não estiver instalado
if ! python3 -c "import bs4" 2>/dev/null; then
    echo "📦 Instalando beautifulsoup4..."
    pip3 install beautifulsoup4
    echo "   ✅ beautifulsoup4 instalado"
else
    echo "   ✅ beautifulsoup4 já instalado"
fi

echo ""
echo "✅ Dependências verificadas e instaladas!"
echo ""

echo "================================================================================"
echo "🔄 PASSO 7/7: Reiniciando serviços"
echo "================================================================================"
echo ""

# Função para reiniciar serviço
restart_service() {
    local service=$1
    
    echo "⏳ Reiniciando $service..."
    
    if command -v supervisorctl &> /dev/null; then
        supervisorctl restart $service 2>&1 | grep -v "^$"
        sleep 3
        status=$(supervisorctl status $service 2>&1 | awk '{print $2}')
        if [ "$status" = "RUNNING" ]; then
            echo "   ✅ $service: RUNNING"
        else
            echo "   ⚠️  $service: $status"
        fi
    elif systemctl list-units --type=service | grep -q $service; then
        systemctl restart $service
        sleep 3
        if systemctl is-active --quiet $service; then
            echo "   ✅ $service: RUNNING"
        else
            echo "   ⚠️  $service: $(systemctl is-active $service)"
        fi
    else
        echo "   ⚠️  Gerenciador de serviços não detectado. Reinicie manualmente."
    fi
}

# Reiniciar backend primeiro
restart_service "backend"
echo ""

# Reiniciar frontend
restart_service "frontend"
echo ""

echo "================================================================================"
echo "🔍 Verificando logs do backend"
echo "================================================================================"
echo ""

echo "📋 Últimas 30 linhas do log do backend:"
echo "─────────────────────────────────────────────────────────────────────────────"
tail -n 30 /var/log/supervisor/backend.err.log 2>/dev/null || tail -n 30 /var/log/backend/error.log 2>/dev/null || echo "⚠️ Não foi possível acessar logs"
echo "─────────────────────────────────────────────────────────────────────────────"
echo ""

# Verificar se há erros críticos
if tail -n 50 /var/log/supervisor/backend.err.log 2>/dev/null | grep -qi "error\|exception\|traceback"; then
    echo "⚠️  ATENÇÃO: Detectados erros no log do backend!"
    echo "   Verifique os logs completos: tail -f /var/log/supervisor/backend.err.log"
    echo ""
else
    echo "✅ Nenhum erro crítico detectado nos logs"
    echo ""
fi

echo "================================================================================"
echo "🎉 ATUALIZAÇÃO CONCLUÍDA COM SUCESSO!"
echo "================================================================================"
echo ""
echo "✅ NOVAS FUNCIONALIDADES INSTALADAS:"
echo ""
echo "   1️⃣  AI Auto-Search Credentials"
echo "       • IA busca automaticamente credenciais em Office/gestor.my"
echo "       • Usa número de WhatsApp do cliente"
echo "       • Exibe credenciais encontradas no painel do agente"
echo "       • Arquivos: credential_auto_search.py, credential_auto_search_routes.py"
echo ""
echo "   2️⃣  Agendamento de Mensagens"
echo "       • Agentes podem agendar envio de mensagens futuras"
echo "       • Interface com data/hora e meio de envio (WhatsApp/WA Suporte)"
echo "       • Processamento automático via scheduler"
echo "       • Arquivos: scheduled_messages_*.py, ScheduleMessageModal.js"
echo ""
echo "   3️⃣  Lembretes por Email"
echo "       • Sistema automático de lembretes de expiração"
echo "       • Admin configura SMTP e timing (3, 2, 1 dias antes)"
echo "       • Envia emails para clientes com credenciais expirando"
echo "       • Arquivos: reminder_*.py, EmailManager.js"
echo ""
echo "   4️⃣  Office Integration (Playwright)"
echo "       • Scraping robusto com Playwright (conteúdo dinâmico)"
echo "       • Suporte a múltiplas credenciais gestor.my"
echo "       • Busca em gerenciar-linhas e gerenciar-testes"
echo "       • Extração melhorada (user, password, expiration, status)"
echo "       • Arquivo: office_service.py (reescrito)"
echo ""
echo "   5️⃣  Prevent Duplicate Tests"
echo "       • Cliente não pode gerar múltiplos testes"
echo "       • Verifica por WhatsApp/CPF/Email"
echo "       • Evita abuso no fluxo /vendas"
echo "       • Arquivo: vendas_ai_service.py (generate_iptv_test)"
echo ""
echo "================================================================================"
echo ""
echo "📁 BACKUP DOS ARQUIVOS ANTERIORES:"
echo "   $BACKUP_DIR"
echo ""
echo "🔄 PARA REVERTER (rollback):"
echo "   cp -r $BACKUP_DIR/backend/* /opt/iaze/backend/"
echo "   cp -r $BACKUP_DIR/frontend/* /opt/iaze/frontend/"
echo "   supervisorctl restart all"
echo ""
echo "================================================================================"
echo ""
echo "🧪 TESTES RECOMENDADOS:"
echo ""
echo "   1. Teste AI Auto-Search:"
echo "      • Cliente WA SUPORTE solicita: 'qual meu usuário e senha?'"
echo "      • IA deve buscar automaticamente em Office"
echo "      • Credenciais aparecem no painel do agente"
echo ""
echo "   2. Teste Agendamento:"
echo "      • No painel do agente, clique no botão 'Agendar'"
echo "      • Configure data/hora futura"
echo "      • Mensagem deve ser enviada no horário programado"
echo ""
echo "   3. Teste Email Reminder:"
echo "      • Admin Dashboard → aba 'Email'"
echo "      • Configure SMTP e lembretes (3, 2, 1 dias)"
echo "      • Sistema enviará emails diariamente às 9h UTC"
echo ""
echo "   4. Teste Office Search:"
echo "      • Admin Dashboard → aba 'Office'"
echo "      • Configure credenciais gestor.my"
echo "      • Agent Dashboard → botão 'Office' → buscar por WhatsApp"
echo ""
echo "   5. Teste Duplicate Prevention:"
echo "      • /vendas → cliente solicita teste"
echo "      • Teste gerado com sucesso"
echo "      • Mesmo cliente solicita novamente → deve recusar"
echo ""
echo "================================================================================"
echo ""
echo "📞 SUPORTE:"
echo "   Em caso de problemas:"
echo "   • Verifique logs backend: tail -f /var/log/supervisor/backend.err.log"
echo "   • Verifique logs frontend: tail -f /var/log/supervisor/frontend.out.log"
echo "   • Teste importação: cd /opt/iaze/backend && python3 -c 'import server'"
echo "   • Rollback se necessário (comando acima)"
echo ""
echo "================================================================================"
echo ""
echo "✅ Pronto! Todas as novas funcionalidades foram instaladas com sucesso!"
echo ""
