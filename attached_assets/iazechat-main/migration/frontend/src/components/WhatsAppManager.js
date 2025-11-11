import React, { useState, useEffect } from 'react';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Phone, QrCode, Trash2, Settings, TrendingUp, AlertCircle, CheckCircle, XCircle, RefreshCw, CheckSquare, Eye, EyeOff } from 'lucide-react';
import api from '../lib/api';
import WhatsAppQRCodeModal from './WhatsAppQRCodeModal';

const WhatsAppManager = () => {
  const [connections, setConnections] = useState([]);
  const [config, setConfig] = useState(null);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [qrCode, setQrCode] = useState(null);
  const [pairingCode, setPairingCode] = useState(null);
  const [selectedConnection, setSelectedConnection] = useState(null);
  
  // Configurações
  const [transferMessage, setTransferMessage] = useState('');
  const [showConfig, setShowConfig] = useState(false);
  
  // 🆕 Estados para nova UX
  const [showInactive, setShowInactive] = useState(false);
  const [conflictDialog, setConflictDialog] = useState(null);
  const [showQRModal, setShowQRModal] = useState(false);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 10000); // Atualizar a cada 10s
    return () => clearInterval(interval);
  }, []);

  const loadData = async () => {
    try {
      const endpoint = showInactive ? '/whatsapp/connections/inactive' : '/whatsapp/connections';
      
      const [connectionsRes, configRes, statsRes] = await Promise.all([
        api.get(endpoint),
        api.get('/whatsapp/config'),
        api.get('/whatsapp/stats')
      ]);
      
      setConnections(connectionsRes.data);
      setConfig(configRes.data);
      setStats(statsRes.data);
      setTransferMessage(configRes.data.transfer_message || '');
      
      // Se estava mostrando QR Code e a conexão agora está conectada, fechar o modal
      if (selectedConnection && qrCode) {
        const connUpdated = connectionsRes.data.find(c => c.id === selectedConnection);
        if (connUpdated && connUpdated.connected) {
          console.log('✅ Conexão detectada! Fechando modal...');
          setQrCode(null);
          setPairingCode(null);
          setSelectedConnection(null);
        }
      }
      
      setLoading(false);
    } catch (error) {
      console.error('Error loading WhatsApp data:', error);
      setLoading(false);
    }
  };

  const handleRefreshStatus = async (connectionId) => {
    try {
      const response = await api.post(`/whatsapp/connections/${connectionId}/refresh-status`);
      console.log('✅ Status atualizado:', response.data);
      
      // Recarregar dados
      loadData();
      
      if (response.data.connected) {
        alert('✅ WhatsApp conectado com sucesso!');
        // Fechar QR code se estiver aberto
        if (selectedConnection === connectionId) {
          setQrCode(null);
          setPairingCode(null);
          setSelectedConnection(null);
        }
      }
    } catch (error) {
      console.error('Error refreshing status:', error);
      alert('❌ Erro ao verificar status: ' + (error.response?.data?.detail || error.message));
    }
  };


  // Estado para prevenir cliques múltiplos
  const [isCreatingConnection, setIsCreatingConnection] = useState(false);

  const handleAddConnection = async () => {
    // **PREVENIR MÚLTIPLOS CLIQUES**
    if (isCreatingConnection) {
      console.log('⚠️ Já existe uma conexão sendo criada. Aguarde...');
      return;
    }
    
    console.log('🔧 [DEBUG] handleAddConnection iniciado - Versão 2.0.3');
    
    try {
      const maxReceived = prompt('Limite de mensagens RECEBIDAS por dia:', '200');
      const maxSent = prompt('Limite de mensagens ENVIADAS por dia:', '200');
      
      if (!maxReceived || !maxSent) return;
      
      setIsCreatingConnection(true); // **BLOQUEAR NOVOS CLIQUES**
      
      const userData = JSON.parse(localStorage.getItem('user_data'));
      console.log('🔧 [DEBUG] userData:', userData);
      
      // **CORREÇÃO: Garantir que resellerId seja null (não undefined)**
      let resellerId = userData?.reseller_id;
      if (resellerId === undefined) {
        console.warn('⚠️ [DEBUG] reseller_id está undefined - convertendo para null');
        resellerId = null;
      }
      
      console.log('🔧 [DEBUG] resellerId (corrigido):', resellerId);
      
      // Admin master pode ter reseller_id = null
      // Apenas verificar se user_data existe
      if (!userData) {
        console.log('🔧 [DEBUG] userData não existe!');
        alert('❌ Erro: Dados do usuário não encontrados. Faça login novamente.');
        setIsCreatingConnection(false);
        return;
      }
      
      console.log('🔧 [DEBUG] Validação OK - Enviando para backend...');
      console.log('Criando conexão WhatsApp:', { resellerId, maxReceived, maxSent });
      
      try {
        const response = await api.post('/whatsapp/connections', {
          reseller_id: resellerId || null,  // Enviar null explicitamente para admin
          max_received_daily: parseInt(maxReceived),
          max_sent_daily: parseInt(maxSent)
        });
        
        console.log('✅ Conexão criada com sucesso:', response.data);
        
        // **ABRIR MODAL AUTOMATICAMENTE COM O QR CODE**
        if (response.data.qr_code) {
          setSelectedConnection(response.data);
          setQrModalOpen(true);
          toast.success('✅ Conexão criada! Escaneie o QR Code para conectar.');
        } else {
          toast.success('✅ Conexão criada! Aguarde alguns segundos e clique em "Ver QR Code".');
        }
        
        await loadData(); // Recarregar lista
        return;
      } catch (backendError) {
        // 🆕 Tratar erro 409 (Conflict - conexão já existe)
        if (backendError.response?.status === 409) {
          const errorData = backendError.response.data.detail;
          setConflictDialog({
            message: errorData.message,
            connection: errorData.connection,
            options: errorData.options,
            maxReceived: parseInt(maxReceived),
            maxSent: parseInt(maxSent),
            resellerId: resellerId
          });
          return;
        }
        
        // Se backend falhar (503), tentar método alternativo direto ao WPPConnect
        if (backendError.response?.status === 503) {
          console.log('Backend não conseguiu acessar WPPConnect, tentando método direto...');
          alert('⚠️ Método alternativo sendo usado... aguarde.');
          await handleDirectWPPConnect(resellerId, maxReceived, maxSent);
          return;
        }
        // Se for outro erro, propagar
        throw backendError;
      }
    } catch (error) {
      console.error('Erro detalhado ao criar conexão:', error);
      
      let errorMessage = 'Erro ao criar conexão WhatsApp';
      
      if (error.response) {
        const { data, status } = error.response;
        
        if (status === 503) {
          errorMessage = '⚠️ Evolution API não está disponível.\n\nPara conectar números WhatsApp, é necessário que a Evolution API esteja rodando.\n\nEntre em contato com o suporte.';
        } else if (status === 400) {
          errorMessage = data?.detail || 'Requisição inválida';
        } else if (typeof data === 'string') {
          errorMessage = data;
          
          // Detectar erro "already in use" e sugerir limpeza
          if (errorMessage.toLowerCase().includes('already in use') || errorMessage.includes('já está em uso')) {
            errorMessage += '\n\n💡 SOLUÇÃO:\n\n1. Clique no botão vermelho "Limpar Tudo"\n2. Confirme a limpeza\n3. Aguarde a página recarregar\n4. Tente adicionar o número novamente\n\nIsso vai remover instâncias antigas da Evolution API.';
          }
        } else if (data?.detail) {
          errorMessage = data.detail;
          
          // Detectar erro "already in use" e sugerir limpeza
          if (errorMessage.toLowerCase().includes('already in use') || errorMessage.includes('já está em uso')) {
            errorMessage += '\n\n💡 SOLUÇÃO:\n\n1. Clique no botão vermelho "Limpar Tudo"\n2. Confirme a limpeza\n3. Aguarde a página recarregar\n4. Tente adicionar o número novamente\n\nIsso vai remover instâncias antigas da Evolution API.';
          }
        } else if (data?.message) {
          errorMessage = data.message;
        } else {
          errorMessage = `Erro ${status}: ${JSON.stringify(data)}`;
        }
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      // Verificar novamente se é erro de "already in use"
      if (errorMessage.toLowerCase().includes('already in use') || errorMessage.includes('já está em uso')) {
        if (!errorMessage.includes('💡 SOLUÇÃO')) {
          errorMessage += '\n\n💡 SOLUÇÃO:\n\n1. Clique no botão vermelho "Limpar Tudo"\n2. Confirme a limpeza\n3. Aguarde a página recarregar\n4. Tente adicionar o número novamente\n\nIsso vai remover instâncias antigas da Evolution API.';
        }
      }
      
      alert('❌ ' + errorMessage);
    } finally {
      // **SEMPRE DESBLOQUEAR O BOTÃO**
      setIsCreatingConnection(false);
    }
  };

  const handleReactivateConnection = async () => {
    if (!conflictDialog) return;
    
    try {
      const response = await api.post(`/whatsapp/connections/${conflictDialog.connection.id}/reactivate`);
      
      alert('✅ ' + response.data.message);
      setConflictDialog(null);
      setShowInactive(true); // Mostrar conexões inativas
      loadData();
    } catch (error) {
      console.error('Erro ao reativar:', error);
      alert('❌ Erro ao reativar conexão: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleDeleteAndRecreate = async () => {
    if (!conflictDialog) return;
    
    if (!confirm('Confirma deletar a conexão existente e criar uma nova?')) return;
    
    try {
      // 1. Deletar conexão existente
      await api.delete(`/whatsapp/connections/${conflictDialog.connection.id}`);
      
      // 2. Aguardar 2 segundos
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // 3. Criar nova conexão
      const response = await api.post('/whatsapp/connections', {
        reseller_id: conflictDialog.resellerId,
        max_received_daily: conflictDialog.maxReceived,
        max_sent_daily: conflictDialog.maxSent
      });
      
      alert('✅ Conexão antiga deletada e nova criada com sucesso!\n\nClique em "Ver QR Code" para conectar.');
      setConflictDialog(null);
      loadData();
    } catch (error) {
      console.error('Erro ao deletar e recriar:', error);
      alert('❌ Erro: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleDirectWPPConnect = async (resellerId, maxReceived, maxSent) => {
    try {
      // Gerar nome da instância
      const timestamp = Date.now();
      const instanceName = `IAZE_${timestamp}`;
      
      console.log('Criando sessão via proxy backend:', instanceName);
      
      // Criar sessão via proxy do backend (evita CORS)
      const wppResponse = await api.post(`/whatsapp/proxy/start-session/${instanceName}`);
      
      console.log('Sessão WPPConnect criada via proxy:', wppResponse.data);
      
      // Salvar no banco via backend
      const saveResponse = await api.post('/whatsapp/connections/manual', {
        reseller_id: resellerId,
        instance_name: instanceName,
        max_received_daily: parseInt(maxReceived),
        max_sent_daily: parseInt(maxSent),
        wpp_data: wppResponse.data
      });
      
      alert('✅ Conexão criada! Clique em "Ver QR Code" para conectar.');
      loadData();
    } catch (error) {
      console.error('Erro no método direto WPPConnect:', error);
      
      let errorMsg = 'Não foi possível conectar ao WPPConnect';
      if (error.response?.data?.detail) {
        errorMsg = error.response.data.detail;
      } else if (error.message) {
        errorMsg = error.message;
      }
      
      alert(`❌ ${errorMsg}\n\nVerifique se o WPPConnect está rodando no servidor Hetzner.`);
    }
  };

  const handleShowQRCode = async (connectionId) => {
    try {
      // Buscar dados da conexão
      const connResponse = await api.get('/whatsapp/connections');
      const connection = connResponse.data.find(c => c.id === connectionId);
      
      if (!connection) {
        alert('Conexão não encontrada');
        return;
      }
      
      // Definir conexão selecionada e abrir modal
      setSelectedConnection(connectionId);
      setShowQRModal(true);
      
      // Se não tem QR Code, buscar
      if (!connection.qr_code) {
        await handleRefreshQRCode(connectionId);
      }
      
    } catch (error) {
      console.error('Error showing QR code:', error);
      alert('Erro ao exibir QR Code: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleRefreshQRCode = async (connectionId) => {
    try {
      const response = await api.post(`/whatsapp/connections/${connectionId}/refresh-qr`);
      
      if (response.data.success) {
        // Recarregar dados para atualizar o QR Code
        await loadData();
        return response.data;
      }
    } catch (error) {
      console.error('Error refreshing QR code:', error);
      alert('Erro ao gerar novo QR Code: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleRestartSession = async (connectionId) => {
    try {
      if (!confirm('Tem certeza que deseja reiniciar a sessão? Isso irá desconectar e recriar a instância.')) {
        return;
      }
      
      const response = await api.post(`/whatsapp/connections/${connectionId}/restart-session`);
      
      if (response.data.success) {
        alert('✅ Sessão reiniciada com sucesso! Novo QR Code gerado.');
        // Recarregar dados
        await loadData();
        return response.data;
      }
    } catch (error) {
      console.error('Error restarting session:', error);
      alert('Erro ao reiniciar sessão: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleCloseQRModal = () => {
    setShowQRModal(false);
    setSelectedConnection(null);
    setQrCode(null);
    setPairingCode(null);
  };

  const fetchQRCodeDirect = async (connectionId) => {
    try {
      // Buscar conexão para pegar instance_name
      const connResponse = await api.get('/whatsapp/connections');
      const connection = connResponse.data.find(c => c.id === connectionId);
      
      if (!connection) {
        alert('❌ Conexão não encontrada');
        return;
      }
      
      alert('⏳ Buscando QR Code... pode demorar até 60 segundos.');
      
      // Tentar buscar QR code (com retries)
      for (let i = 0; i < 20; i++) {
        try {
          const qrResponse = await api.get(`/whatsapp/connections/${connectionId}/qrcode`);
          
          const qrCodeData = qrResponse.data.qr_code;
          
          if (qrCodeData && qrCodeData !== 'null' && qrCodeData !== '') {
            setQrCode(qrCodeData);
            setSelectedConnection(connectionId);
            setPairingCode(null);
            alert('✅ QR Code obtido com sucesso! Escaneie com seu celular e aguarde a conexão.');
            
            // Iniciar polling para verificar status
            startConnectionPolling(connectionId);
            return;
          }
        } catch (err) {
          console.log(`Tentativa ${i + 1}/20 falhou:`, err.message);
        }
        
        // Aguardar 3 segundos antes da próxima tentativa
        await new Promise(resolve => setTimeout(resolve, 3000));
      }
      
      alert('❌ Não foi possível obter o QR Code após 20 tentativas (60 segundos).\n\nVerifique se a instância está ativa na Evolution API.\n\nA Evolution API pode demorar até 1-2 minutos para gerar o QR Code na primeira vez.');
    } catch (error) {
      console.error('Erro ao buscar QR Code via proxy:', error);
      alert(`❌ Erro ao buscar QR Code: ${error.response?.data?.detail || error.message}`);
    }
  };

  // Função para verificar status da conexão periodicamente
  const startConnectionPolling = (connectionId) => {
    let attempts = 0;
    const maxAttempts = 40; // 40 tentativas x 3 segundos = 2 minutos
    
    console.log('🔄 Iniciando polling para conexão:', connectionId);
    
    const pollInterval = setInterval(async () => {
      attempts++;
      
      try {
        const response = await api.get('/whatsapp/connections');
        const connection = response.data.find(c => c.id === connectionId);
        
        console.log(`🔍 Polling tentativa ${attempts}/${maxAttempts}:`, {
          found: !!connection,
          status: connection?.status,
          connected: connection?.connected
        });
        
        // Verificar tanto status quanto connected
        if (connection && (connection.status === 'connected' || connection.connected === true)) {
          console.log('✅ CONEXÃO DETECTADA! Fechando modal...');
          clearInterval(pollInterval);
          
          // Fechar modal do QR Code
          setQrCode(null);
          setSelectedConnection(null);
          
          // Recarregar lista de conexões
          loadData();
          
          // Mostrar mensagem de sucesso
          alert('🎉 WhatsApp conectado com sucesso!\n\nVocê já pode começar a receber e enviar mensagens.');
          
          return;
        }
        
        if (attempts >= maxAttempts) {
          clearInterval(pollInterval);
          alert('⏱️ Tempo limite atingido.\n\nSe você já escaneou o QR Code, feche esta janela e verifique o status na lista de conexões.\n\nSe ainda não conectou, tente gerar um novo QR Code.');
        }
        
      } catch (error) {
        console.error('Erro ao verificar status:', error);
      }
    }, 3000); // Verificar a cada 3 segundos
  };

  const handleShowPairingCode = async (connectionId) => {
    const phoneNumber = prompt('Digite o número do WhatsApp (com DDI):\n\nExemplo: 5511999999999\n\n(Código do país + DDD + número)');
    
    if (!phoneNumber) return;
    
    // Validar formato
    if (phoneNumber.length < 12 || !phoneNumber.match(/^\d+$/)) {
      alert('❌ Número inválido! Use apenas números com DDI.\n\nExemplo: 5511999999999');
      return;
    }
    
    try {
      const response = await api.post(`/whatsapp/connections/${connectionId}/pairing-code?phone_number=${phoneNumber}`);
      
      if (response.data.pairing_code) {
        setPairingCode({
          code: response.data.pairing_code,
          phone: phoneNumber,
          connectionId: connectionId
        });
        setQrCode(null); // Limpar QR code se tiver
        setSelectedConnection(connectionId);
      } else {
        alert('❌ Não foi possível gerar o código. Tente novamente.');
      }
    } catch (error) {
      console.error('Error generating pairing code:', error);
      const message = error.response?.data?.detail || 'Erro ao gerar código. Verifique o número e tente novamente.';
      alert('❌ ' + message);
    }
  };

  const handleDisconnect = async (connectionId) => {
    if (!confirm('Deseja realmente desconectar este número WhatsApp?')) return;
    
    try {
      await api.delete(`/whatsapp/connections/${connectionId}`);
      alert('✅ Número desconectado com sucesso!');
      loadData();
    } catch (error) {
      console.error('Error disconnecting:', error);
      alert('❌ Erro ao desconectar: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleRestart = async (connectionId) => {
    if (!confirm('Deseja reiniciar a conexão deste número?')) return;
    
    try {
      // Deletar e recriar a conexão
      const conn = connections.find(c => c.id === connectionId);
      if (!conn) return;
      
      await api.delete(`/whatsapp/connections/${connectionId}`);
      
      const resellerId = JSON.parse(localStorage.getItem('user_data'))?.reseller_id;
      await api.post('/whatsapp/connections', {
        reseller_id: resellerId,
        max_received_daily: conn.limits?.max_received_per_day || 500,
        max_sent_daily: conn.limits?.max_sent_per_day || 500
      });
      
      alert('✅ Conexão reiniciada! Aguarde alguns segundos e clique em "Ver QR Code".');
      loadData();
    } catch (error) {
      console.error('Error restarting:', error);
      alert('❌ Erro ao reiniciar: ' + (error.response?.data?.detail || error.message));
    }
  };

  const [selectedForClear, setSelectedForClear] = useState([]);
  const [showClearMenu, setShowClearMenu] = useState(false);

  const handleClearAll = async () => {
    if (!confirm('⚠️ Isso vai limpar TODAS as conexões WhatsApp do Evolution API e do banco de dados.\n\nEsta ação é irreversível. Deseja continuar?')) return;
    
    try {
      // Usar o novo endpoint de cleanup
      const response = await api.post('/whatsapp/cleanup-all', {});
      
      console.log('Cleanup result:', response.data);
      
      const { deleted_from_evolution, deleted_from_db, errors } = response.data;
      
      let message = `✅ Limpeza completa realizada!\n\n`;
      message += `- Instâncias removidas da Evolution API: ${deleted_from_evolution}\n`;
      message += `- Registros removidos do banco de dados: ${deleted_from_db}\n`;
      
      if (errors && errors.length > 0) {
        message += `\n⚠️ Alguns erros ocorreram:\n${errors.join('\n')}`;
      }
      
      alert(message);
      
      // Recarregar a página após 1 segundo
      setTimeout(() => {
        window.location.reload();
      }, 1000);
    } catch (error) {
      console.error('Error in cleanup:', error);
      
      // Mesmo com erro, tentar recarregar
      alert('⚠️ Limpeza executada. A página será recarregada.\n\nSe o erro persistir, entre em contato com o suporte.');
      
      setTimeout(() => {
        window.location.reload();
      }, 1000);
    }
  };

  const handleClearSelected = async () => {
    if (selectedForClear.length === 0) {
      alert('⚠️ Selecione pelo menos uma conexão para limpar.');
      return;
    }

    if (!confirm(`Limpar ${selectedForClear.length} conexão(ões) selecionada(s)?`)) return;

    try {
      for (const connId of selectedForClear) {
        try {
          await api.delete(`/whatsapp/connections/${connId}`);
        } catch (e) {
          console.log('Erro ao deletar:', e);
        }
      }
      
      setSelectedForClear([]);
      setShowClearMenu(false);
      alert('✅ Conexões selecionadas limpas!');
      loadData();
    } catch (error) {
      alert('✅ Limpeza concluída!');
      loadData();
    }
  };

  const toggleConnectionSelection = (connId) => {
    setSelectedForClear(prev => 
      prev.includes(connId) 
        ? prev.filter(id => id !== connId)
        : [...prev, connId]
    );
  };

  const handleForceSync = async (connectionId) => {
    try {
      // Força atualização do status via backend consultando Evolution API
      await handleRefreshStatus(connectionId);
      alert('✅ Status verificado e atualizado!');
    } catch (error) {
      alert('❌ Erro ao sincronizar');
    }
  };

  const handleDeleteConnection = async (connectionId) => {
    if (!window.confirm('Deseja realmente deletar esta conexão WhatsApp?')) return;
    
    try {
      await api.delete(`/whatsapp/connections/${connectionId}`);
      alert('✅ Conexão deletada!');
      loadData();
    } catch (error) {
      alert('❌ Erro ao deletar: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleUpdateLimits = async (connectionId) => {
    const conn = connections.find(c => c.id === connectionId);
    const maxReceived = prompt('Limite de mensagens RECEBIDAS por dia:', conn.max_received_daily);
    const maxSent = prompt('Limite de mensagens ENVIADAS por dia:', conn.max_sent_daily);
    
    if (!maxReceived || !maxSent) return;
    
    try {
      await api.put(`/whatsapp/connections/${connectionId}`, {
        max_received_daily: parseInt(maxReceived),
        max_sent_daily: parseInt(maxSent)
      });
      
      alert('✅ Limites atualizados!');
      loadData();
    } catch (error) {
      alert('❌ Erro ao atualizar: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleSaveConfig = async () => {
    try {
      await api.put('/whatsapp/config', {
        transfer_message: transferMessage
      });
      
      alert('✅ Configurações salvas!');
      setShowConfig(false);
      loadData();
    } catch (error) {
      alert('❌ Erro ao salvar: ' + (error.response?.data?.detail || error.message));
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'connected':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'connecting':
        return <AlertCircle className="w-5 h-5 text-yellow-500" />;
      default:
        return <XCircle className="w-5 h-5 text-red-500" />;
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'connected':
        return 'Conectado';
      case 'connecting':
        return 'Conectando...';
      default:
        return 'Desconectado';
    }
  };

  if (loading) {
    return <div className="p-6 text-center">Carregando...</div>;
  }

  return (
    <div className="space-y-6">
      {/* Botão de Emergência - Limpar Tudo ou Selecionadas */}
      <Card className="p-4 bg-red-50 border-red-200">
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-semibold text-red-900">🚨 Correção de Erros</h3>
              <p className="text-sm text-red-700">
                {showClearMenu 
                  ? 'Selecione as conexões que deseja limpar' 
                  : 'Se houver algum erro 500 ou conexão travada, use estas opções para corrigir.'}
              </p>
            </div>
            <div className="flex gap-2">
              {!showClearMenu ? (
                <>
                  <Button 
                    onClick={() => setShowClearMenu(true)}
                    variant="outline"
                    className="border-red-300 text-red-700 hover:bg-red-100"
                  >
                    <CheckSquare className="w-4 h-4 mr-2" />
                    Limpar Selecionadas
                  </Button>
                  <Button 
                    onClick={handleClearAll}
                    className="bg-red-600 hover:bg-red-700 text-white"
                  >
                    <Trash2 className="w-4 h-4 mr-2" />
                    Limpar Tudo
                  </Button>
                </>
              ) : (
                <>
                  <Button 
                    onClick={() => {
                      setShowClearMenu(false);
                      setSelectedForClear([]);
                    }}
                    variant="outline"
                  >
                    Cancelar
                  </Button>
                  <Button 
                    onClick={handleClearSelected}
                    className="bg-red-600 hover:bg-red-700 text-white"
                    disabled={selectedForClear.length === 0}
                  >
                    <Trash2 className="w-4 h-4 mr-2" />
                    Limpar {selectedForClear.length > 0 ? `(${selectedForClear.length})` : ''}
                  </Button>
                </>
              )}
            </div>
          </div>

          {/* Menu de Seleção de Conexões */}
          {showClearMenu && connections.length > 0 && (
            <div className="mt-4 p-4 bg-white rounded border border-red-200">
              <p className="text-sm font-semibold mb-3 text-gray-700">
                Selecione as conexões para limpar:
              </p>
              <div className="space-y-2 max-h-60 overflow-y-auto">
                {connections.map(conn => (
                  <label 
                    key={conn.id}
                    className="flex items-center gap-3 p-2 hover:bg-gray-50 rounded cursor-pointer"
                  >
                    <input
                      type="checkbox"
                      checked={selectedForClear.includes(conn.id)}
                      onChange={() => toggleConnectionSelection(conn.id)}
                      className="w-4 h-4"
                    />
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="font-medium">{conn.phone_number || conn.instance_name}</span>
                        <span className={`text-xs px-2 py-1 rounded ${
                          conn.status === 'connected' ? 'bg-green-100 text-green-700' :
                          conn.status === 'connecting' ? 'bg-yellow-100 text-yellow-700' :
                          'bg-red-100 text-red-700'
                        }`}>
                          {conn.status === 'connected' ? 'Conectado' :
                           conn.status === 'connecting' ? 'Conectando' :
                           'Desconectado'}
                        </span>
                      </div>
                      <p className="text-xs text-gray-500">Instância: {conn.instance_name}</p>
                    </div>
                  </label>
                ))}
              </div>
              
              <div className="mt-3 pt-3 border-t border-gray-200">
                <button
                  onClick={() => {
                    if (selectedForClear.length === connections.length) {
                      setSelectedForClear([]);
                    } else {
                      setSelectedForClear(connections.map(c => c.id));
                    }
                  }}
                  className="text-sm text-blue-600 hover:text-blue-700"
                >
                  {selectedForClear.length === connections.length ? 'Desmarcar Todas' : 'Selecionar Todas'}
                </button>
              </div>
            </div>
          )}

          {showClearMenu && connections.length === 0 && (
            <div className="mt-4 p-4 bg-white rounded border border-red-200">
              <p className="text-sm text-gray-600 text-center">
                Nenhuma conexão disponível para limpar.
              </p>
            </div>
          )}
        </div>
      </Card>
      
      {/* Estatísticas */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-600">Números Conectados</p>
                <p className="text-2xl font-bold text-green-600">{stats.active_connections}/{stats.total_connections}</p>
              </div>
              <Phone className="w-8 h-8 text-green-500" />
            </div>
          </Card>
          
          <Card className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-600">Plano Atual</p>
                <p className="text-2xl font-bold text-purple-600">{stats.plan?.name || 'Básico'}</p>
              </div>
              <TrendingUp className="w-8 h-8 text-purple-500" />
            </div>
          </Card>
          
          <Card className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-600">Recebidas Hoje</p>
                <p className="text-2xl font-bold text-blue-600">{stats.total_received_today}</p>
              </div>
              <TrendingUp className="w-8 h-8 text-blue-500" />
            </div>
          </Card>
          
          <Card className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-600">Enviadas Hoje</p>
                <p className="text-2xl font-bold text-orange-600">{stats.total_sent_today}</p>
              </div>
              <TrendingUp className="w-8 h-8 text-orange-500" />
            </div>
          </Card>
        </div>
      )}

      {/* Botões de Ação */}
      <div className="flex gap-4">
        <Button 
          onClick={handleAddConnection} 
          disabled={isCreatingConnection}
          className="bg-green-600 hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isCreatingConnection ? (
            <>
              <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
              Criando...
            </>
          ) : (
            <>
              <Phone className="w-4 h-4 mr-2" />
              Adicionar Número
            </>
          )}
        </Button>
        
        <Button 
          onClick={() => {
            setShowInactive(!showInactive);
            loadData();
          }} 
          variant="outline"
          className={showInactive ? "bg-blue-50 border-blue-300" : ""}
        >
          {showInactive ? <EyeOff className="w-4 h-4 mr-2" /> : <Eye className="w-4 h-4 mr-2" />}
          {showInactive ? 'Mostrar Ativas' : 'Mostrar Desativadas'}
        </Button>
        
        <Button onClick={() => setShowConfig(!showConfig)} variant="outline">
          <Settings className="w-4 h-4 mr-2" />
          Configurações
        </Button>
      </div>

      {/* Painel de Configurações */}
      {showConfig && (
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4">⚙️ Configurações</h3>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">
                Mensagem de Transferência
                <span className="text-slate-500 text-xs ml-2">(Enviada quando rotaciona para outro número)</span>
              </label>
              <textarea
                value={transferMessage}
                onChange={(e) => setTransferMessage(e.target.value)}
                className="w-full border rounded p-2 min-h-[100px]"
                placeholder="⏳ Sua mensagem está sendo transferida para outro atendente..."
              />
            </div>
            
            <Button onClick={handleSaveConfig} className="bg-purple-600 hover:bg-purple-700">
              💾 Salvar Configurações
            </Button>
          </div>
        </Card>
      )}

      {/* Lista de Conexões */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {connections.map((conn, index) => (
          <Card key={conn.id} className="p-6">
            <div className="flex items-start justify-between mb-4">
              <div>
                <h3 className="text-lg font-semibold flex items-center gap-2">
                  <Phone className="w-5 h-5" />
                  Número {index + 1}
                </h3>
                <p className="text-sm text-slate-600">{conn.instance_name}</p>
                {conn.phone_number && (
                  <p className="text-sm font-mono text-blue-600">{conn.phone_number}</p>
                )}
              </div>
              
              <div className="flex items-center gap-2">
                {getStatusIcon(conn.status)}
                <span className="text-sm">{getStatusText(conn.status)}</span>
              </div>
            </div>

            {/* Estatísticas do Número */}
            <div className="grid grid-cols-2 gap-4 mb-4 p-4 bg-slate-50 rounded">
              <div>
                <p className="text-xs text-slate-600">Recebidas Hoje</p>
                <p className="text-lg font-bold text-blue-600">
                  {conn.received_today || 0}/{conn.max_received_daily}
                </p>
                <div className="w-full bg-slate-200 rounded-full h-2 mt-1">
                  <div 
                    className="bg-blue-500 h-2 rounded-full"
                    style={{width: `${(conn.received_today || 0) / conn.max_received_daily * 100}%`}}
                  />
                </div>
              </div>
              
              <div>
                <p className="text-xs text-slate-600">Enviadas Hoje</p>
                <p className="text-lg font-bold text-orange-600">
                  {conn.sent_today || 0}/{conn.max_sent_daily}
                </p>
                <div className="w-full bg-slate-200 rounded-full h-2 mt-1">
                  <div 
                    className="bg-orange-500 h-2 rounded-full"
                    style={{width: `${(conn.sent_today || 0) / conn.max_sent_daily * 100}%`}}
                  />
                </div>
              </div>
            </div>

            {/* Botões de Ação */}
            <div className="flex gap-2 flex-wrap">
              {conn.status !== 'connected' && (
                <>
                  <Button 
                    onClick={() => handleShowQRCode(conn.id)}
                    className="bg-blue-600 hover:bg-blue-700"
                    size="sm"
                  >
                    <QrCode className="w-4 h-4 mr-2" />
                    Ver QR Code
                  </Button>
                  <Button 
                    onClick={() => handleShowPairingCode(conn.id)}
                    className="bg-green-600 hover:bg-green-700"
                    size="sm"
                  >
                    <Phone className="w-4 h-4 mr-2" />
                    Código de 8 Dígitos
                  </Button>
                </>
              )}
              
              {conn.status === 'connected' && (
                <Button 
                  onClick={() => handleDisconnect(conn.id)}
                  className="bg-red-600 hover:bg-red-700"
                  size="sm"
                >
                  <XCircle className="w-4 h-4 mr-2" />
                  Desconectar
                </Button>
              )}
              
              <Button 
                onClick={() => handleRestart(conn.id)}
                className="bg-orange-600 hover:bg-orange-700"
                size="sm"
                title="Reiniciar conexão (útil quando travado)"
              >
                <RefreshCw className="w-4 h-4 mr-2" />
                Reiniciar
              </Button>
              
              <Button 
                onClick={() => handleForceSync(conn.id)}
                variant="outline"
                size="sm"
                title="Atualizar status"
              >
                <RefreshCw className="w-4 h-4" />
              </Button>
              
              <Button 
                onClick={() => handleUpdateLimits(conn.id)}
                variant="outline"
                size="sm"
                title="Configurar limites"
              >
                <Settings className="w-4 h-4" />
              </Button>
              
              <Button 
                onClick={() => handleDeleteConnection(conn.id)}
                variant="outline"
                size="sm"
                className="text-red-600 hover:text-red-700"
                title="Deletar conexão"
              >
                <Trash2 className="w-4 h-4" />
              </Button>
            </div>
          </Card>
        ))}
      </div>

      {/* Novo Modal QR Code */}
      {showQRModal && selectedConnection && (
        <WhatsAppQRCodeModal
          connection={connections.find(c => c.id === selectedConnection)}
          onClose={handleCloseQRModal}
          onRefreshQR={handleRefreshQRCode}
          onRestartSession={handleRestartSession}
        />
      )}

      {/* Modal Pairing Code */}
      {pairingCode && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" onClick={() => setPairingCode(null)}>
          <Card className="p-8 max-w-md" onClick={(e) => e.stopPropagation()}>
            <h3 className="text-xl font-bold mb-4 text-center">🔢 Código de Pareamento</h3>
            
            <div className="bg-green-50 border-2 border-green-200 p-6 rounded-lg mb-4 text-center">
              <p className="text-sm text-green-700 mb-2">Código para o número:</p>
              <p className="font-mono text-lg font-bold text-green-800 mb-4">{pairingCode.phone}</p>
              <div className="text-4xl font-bold text-green-600 tracking-widest font-mono">
                {pairingCode.code}
              </div>
            </div>
            
            <div className="text-sm text-slate-600 space-y-2">
              <p>1. Abra o WhatsApp no celular <strong>{pairingCode.phone}</strong></p>
              <p>2. Vá em: <strong>Configurações → Aparelhos conectados</strong></p>
              <p>3. Toque em <strong>Conectar aparelho</strong></p>
              <p>4. Escolha <strong>"Conectar com código"</strong></p>
              <p>5. Digite o código: <strong className="font-mono text-green-600">{pairingCode.code}</strong></p>
            </div>
            
            <p className="text-xs text-center text-slate-500 mt-4">
              Código válido por alguns minutos. Não compartilhe com terceiros.
            </p>
            
            <Button onClick={() => setPairingCode(null)} className="w-full mt-4">
              Fechar
            </Button>
          </Card>
        </div>
      )}

      {/* 🆕 Modal de Conflito de Conexão */}
      {conflictDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <Card className="p-8 max-w-lg" onClick={(e) => e.stopPropagation()}>
            <h3 className="text-xl font-bold mb-4 text-center text-orange-600">⚠️ Conexão Já Existe</h3>
            
            <div className="bg-orange-50 border-2 border-orange-200 p-6 rounded-lg mb-6">
              <p className="text-sm text-orange-900 mb-4">
                <strong>{conflictDialog.message}</strong>
              </p>
              
              <div className="space-y-2 text-sm">
                <p><strong>Instância:</strong> {conflictDialog.connection.instance_name}</p>
                <p><strong>Status:</strong> <span className={`px-2 py-1 rounded ${
                  conflictDialog.connection.status === 'connected' ? 'bg-green-100 text-green-700' :
                  conflictDialog.connection.status === 'connecting' ? 'bg-yellow-100 text-yellow-700' :
                  'bg-red-100 text-red-700'
                }`}>
                  {conflictDialog.connection.status === 'connected' ? 'Conectado' :
                   conflictDialog.connection.status === 'connecting' ? 'Conectando' :
                   'Desconectado'}
                </span></p>
                {conflictDialog.connection.phone_number && (
                  <p><strong>Número:</strong> {conflictDialog.connection.phone_number}</p>
                )}
                <p><strong>Criada em:</strong> {new Date(conflictDialog.connection.created_at).toLocaleString('pt-BR')}</p>
              </div>
            </div>
            
            <p className="text-sm text-slate-600 mb-6">
              Você tem duas opções:
            </p>
            
            <div className="space-y-3 mb-6">
              <div className="border rounded-lg p-4 hover:bg-slate-50 cursor-pointer" onClick={handleReactivateConnection}>
                <h4 className="font-semibold text-green-700 mb-1">✅ Reativar Conexão Existente</h4>
                <p className="text-sm text-slate-600">
                  Usar a mesma conexão que já existe. Você poderá gerar um novo QR Code para conectar.
                </p>
              </div>
              
              <div className="border rounded-lg p-4 hover:bg-slate-50 cursor-pointer" onClick={handleDeleteAndRecreate}>
                <h4 className="font-semibold text-red-700 mb-1">🗑️ Deletar e Criar Nova</h4>
                <p className="text-sm text-slate-600">
                  Deletar a conexão existente (Evolution API + Banco) e criar uma completamente nova.
                </p>
              </div>
            </div>
            
            <Button onClick={() => setConflictDialog(null)} variant="outline" className="w-full">
              Cancelar
            </Button>
          </Card>
        </div>
      )}

      {/* Info do Plano */}
      {stats?.plan && (
        <Card className="p-4 bg-purple-50 border-purple-200">
          <p className="text-sm text-purple-900">
            <strong>Plano {stats.plan.name}:</strong> Até {stats.plan.max_numbers === -1 ? 'ilimitados' : stats.plan.max_numbers} números WhatsApp.
            {stats.total_connections >= stats.plan.max_numbers && stats.plan.max_numbers !== -1 && (
              <span className="text-red-600 ml-2">
                ⚠️ Limite atingido! Entre em contato com o admin para fazer upgrade.
              </span>
            )}
          </p>
        </Card>
      )}
    </div>
  );
};

export default WhatsAppManager;
