import React, { useState, useEffect, useRef } from 'react';
import { Send, Loader2, X, Image as ImageIcon, Mic, Download, AlertCircle } from 'lucide-react';
import './VendasChatNew.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';

function VendasChatNew() {
  const [sessionId, setSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [isProcessingMedia, setIsProcessingMedia] = useState(false);
  
  // Pop-ups
  const [showContactPopup, setShowContactPopup] = useState(false); // NÃO mostrar popup automaticamente (apenas se modo não for "button")
  const [showCredentialsPopup, setShowCredentialsPopup] = useState(false);
  const [showExitConfirm, setShowExitConfirm] = useState(false);
  const [showAppInstallPopup, setShowAppInstallPopup] = useState(false); // 🆕 NOVO: Popup de instalação do app
  const [pendingTestData, setPendingTestData] = useState(null); // 🆕 NOVO: Dados do teste pendente
  const [showNavigationBlockPopup, setShowNavigationBlockPopup] = useState(false); // 🚫 NOVO: Popup de bloqueio de navegação
  
  // Dados
  const [whatsapp, setWhatsapp] = useState('');
  const [pin, setPin] = useState('');
  const [clientName, setClientName] = useState(''); // NOVO: Nome do cliente
  const [credentials, setCredentials] = useState({ usuario: '', senha: '' });
  const [isGeneratingTest, setIsGeneratingTest] = useState(false);
  const [agentProfile, setAgentProfile] = useState({ 
    name: 'Assistente Virtual', 
    photo: '', 
    show_verified_badge: true 
  });
  
  // 🆕 SISTEMA DE BOTÕES
  const [buttonConfig, setButtonConfig] = useState({
    is_enabled: false,
    mode: 'ia',
    buttons: [],
    bot_name: 'Assistente Virtual',
    bot_avatar_url: null
  });
  const [currentButtons, setCurrentButtons] = useState([]);
  
  // 🆕 Estados para criação de usuário
  const [showUserForm, setShowUserForm] = useState(false);
  const [userFormData, setUserFormData] = useState({ name: '', whatsapp: '', pin: '' });
  const [creatingUser, setCreatingUser] = useState(false);
  const [selectedButtonForUser, setSelectedButtonForUser] = useState(null);
  const [hasCreatedUser, setHasCreatedUser] = useState(false); // 🔒 Controle de bloqueio
  const [copiedField, setCopiedField] = useState(null); // Para feedback de cópia
  
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Buscar perfil do agente da config
  useEffect(() => {
    const fetchAgentProfile = async () => {
      try {
        const response = await fetch(`${BACKEND_URL}/api/admin/vendas-bot/simple-config`);
        if (response.ok) {
          const config = await response.json();
          
          // 🔧 DECODIFICAR operation_mode (bypass gateway)
          if (config.empresa_nome && config.empresa_nome.includes('|OM:')) {
            const [nome, modeStr] = config.empresa_nome.split('|OM:');
            config.empresa_nome = nome;
            config.operation_mode = modeStr;
          }
          
          if (config.agent_profile) {
            setAgentProfile(config.agent_profile);
          }
        }
      } catch (error) {
        console.error('Error loading agent profile:', error);
      }
    };
    
    fetchAgentProfile();
  }, []);

  // 🔒 Verificar se usuário já criou teste (localStorage)
  useEffect(() => {
    const savedUserData = localStorage.getItem('vendas_user_data');
    if (savedUserData) {
      try {
        const parsed = JSON.parse(savedUserData);
        setHasCreatedUser(true);
        setUserFormData(parsed); // Preencher com dados salvos
        console.log('🔒 Usuário já criou teste. Campos bloqueados:', parsed);
      } catch (error) {
        console.error('Erro ao carregar dados do usuário:', error);
      }
    }
  }, []);

  // Capturar evento de instalação PWA
  useEffect(() => {
    const handleBeforeInstallPrompt = (e) => {
      // Prevenir que o mini-infobar apareça em mobile
      e.preventDefault();
      // Guardar o evento para usar depois
      window.deferredPrompt = e;
      console.log('✅ PWA pode ser instalado!');
    };

    window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt);

    return () => {
      window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
    };
  }, []);

  // 🚫 BLOQUEIO DE NAVEGAÇÃO - Prevenir saída acidental da página
  useEffect(() => {
    // Adicionar um estado ao histórico para interceptar o botão voltar
    window.history.pushState(null, '', window.location.href);
    console.log('🚫 Bloqueio de navegação ativado');

    // Handler para botão voltar do navegador
    const handlePopState = (e) => {
      console.log('🚫 Tentativa de voltar detectada');
      // Adicionar novamente o estado para manter o usuário na página
      window.history.pushState(null, '', window.location.href);
      // Mostrar popup de confirmação
      setShowNavigationBlockPopup(true);
    };

    // Handler para fechar aba/navegador
    const handleBeforeUnload = (e) => {
      console.log('🚫 Tentativa de fechar página detectada');
      // Mensagem padrão do navegador (alguns navegadores não permitem customização)
      e.preventDefault();
      e.returnValue = 'Deseja realmente fechar a página e perder a promoção com 3 telas liberadas?';
      return e.returnValue;
    };

    // Adicionar listeners
    window.addEventListener('popstate', handlePopState);
    window.addEventListener('beforeunload', handleBeforeUnload);

    // Cleanup
    return () => {
      window.removeEventListener('popstate', handlePopState);
      window.removeEventListener('beforeunload', handleBeforeUnload);
    };
  }, []);

  // 🚫 Função para permitir saída (quando usuário clica SIM)
  const handleAllowExit = () => {
    console.log('✅ Usuário confirmou saída');
    setShowNavigationBlockPopup(false);
    // Remover os listeners temporariamente
    window.removeEventListener('popstate', () => {});
    window.removeEventListener('beforeunload', () => {});
    // Voltar para a página anterior
    window.history.back();
  };

  // 🚫 Função para cancelar saída (quando usuário clica NÃO)
  const handleCancelExit = () => {
    console.log('❌ Usuário cancelou saída');
    setShowNavigationBlockPopup(false);
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    // Verificar se há WhatsApp e Nome salvos no localStorage
    const savedWhatsapp = localStorage.getItem('vendas_whatsapp');
    const savedName = localStorage.getItem('vendas_name');
    initSession(savedWhatsapp, savedName);
  }, []);

  const initSession = async (initialWhatsapp = null, initialName = null) => {
    try {
      setIsLoading(true);
      const response = await fetch(`${BACKEND_URL}/api/vendas/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          whatsapp: initialWhatsapp || undefined,
          name: initialName || undefined
        })
      });
      const data = await response.json();
      setSessionId(data.session_id);
      setMessages(data.messages || []);
      
      console.log('✅ Sessão criada:', data.session_id);
      
      // 🆕 SOLUÇÃO FINAL: Buscar configuração via endpoint separado
      try {
        console.log('📋 Buscando configuração de botões...');
        const configResponse = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/vendas/config`);
        const buttonConfigData = await configResponse.json();
        
        console.log('✅ Configuração recebida:', buttonConfigData);
        console.log('📊 Status:', buttonConfigData.status, '| Enabled:', buttonConfigData.is_enabled, '| Botões:', buttonConfigData.buttons.length);
        
        // Aplicar configuração
        if (buttonConfigData.is_enabled && buttonConfigData.buttons.length > 0) {
          setButtonConfig(buttonConfigData);
          setCurrentButtons(buttonConfigData.buttons);
          console.log('✅ Botões ativos:', buttonConfigData.buttons.map(b => b.label).join(', '));
          
          // 🆕 Atualizar perfil do bot com dados da configuração
          if (buttonConfigData.bot_name || buttonConfigData.bot_avatar_url) {
            setAgentProfile(prev => ({
              ...prev,
              name: buttonConfigData.bot_name || prev.name,
              photo: buttonConfigData.bot_avatar_url || prev.photo
            }));
            console.log('✅ Perfil do bot atualizado:', buttonConfigData.bot_name, buttonConfigData.bot_avatar_url);
          }
          
          const status = buttonConfigData.status || 2;
          
          // 🆕 Mostrar popup apenas se modo NÃO for "button" (status !== 1)
          if (status !== 1 && !initialWhatsapp) {
            setShowContactPopup(true);
          }
        } else {
          console.log('⚠️ Nenhum botão configurado (is_enabled:', buttonConfigData.is_enabled, ')');
          // Sem configuração de botões, mostrar popup tradicional
          if (!initialWhatsapp) {
            setShowContactPopup(true);
          }
        }
      } catch (configError) {
        console.error('❌ Erro ao buscar configuração de botões:', configError);
        // Em caso de erro, mostrar popup tradicional
        if (!initialWhatsapp) {
          setShowContactPopup(true);
        }
      }
    } catch (error) {
      console.error('Erro:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const sendMessage = async (e) => {
    e?.preventDefault();
    if (!inputText.trim() || !sessionId || isSending) return;
    
    const messageText = inputText.trim();
    setInputText('');
    setIsSending(true);
    
    try {
      const response = await fetch(`${BACKEND_URL}/api/vendas/message`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId, text: messageText })
      });
      const data = await response.json();
      await new Promise(resolve => setTimeout(resolve, 10000));
      setMessages(prev => [...prev, ...data.messages]);
      
      // 🆕 Atualizar botões se retornados
      if (data.buttons) {
        setCurrentButtons(data.buttons);
      }
      
      // Verificar se tem botão de solicitar teste
      const lastMessage = data.messages[data.messages.length - 1];
      if (lastMessage?.button_action === 'REQUEST_TEST') {
        // Aguardar um pouco e mostrar o pop-up
        setTimeout(() => setShowContactPopup(true), 1000);
      }
    } catch (error) {
      console.error('Erro:', error);
      alert('Erro ao enviar mensagem.');
    } finally {
      setIsSending(false);
    }
  };

  // 🆕 FUNÇÃO PARA PROCESSAR CLIQUE EM BOTÃO
  const handleButtonClick = async (buttonId, buttonLabel, button) => {
    if (!sessionId || isSending) return;
    
    // 🆕 Se botão tem redirect_url, abrir link E processar normalmente
    if (button?.redirect_url) {
      console.log('🔗 Abrindo link:', button.redirect_url);
      
      // 💰 Se for botão de PAGAMENTO, adicionar credenciais na URL
      if (buttonLabel.toUpperCase().includes('PAGAMENTO') || buttonLabel.toUpperCase().includes('PAGAR')) {
        const savedData = localStorage.getItem('vendas_user_data');
        if (savedData) {
          try {
            const userData = JSON.parse(savedData);
            // Pegar credenciais GERADAS (usuario/senha), não WhatsApp/PIN
            // Buscar na última mensagem do bot que contém as credenciais
            let generatedUser = '';
            let generatedPass = '';
            
            // Procurar nas mensagens recentes por credenciais geradas
            for (let i = messages.length - 1; i >= 0; i--) {
              const msg = messages[i];
              if (msg.from_type === 'bot' && msg.text) {
                const userMatch = msg.text.match(/Usuário:\s*(\S+)/i);
                const passMatch = msg.text.match(/Senha:\s*(\S+)/i);
                if (userMatch && passMatch) {
                  generatedUser = userMatch[1];
                  generatedPass = passMatch[1];
                  break;
                }
              }
            }
            
            // Se encontrou credenciais geradas, usar elas. Senão usar WhatsApp/PIN
            const username = generatedUser || userData.whatsapp || '';
            const password = generatedPass || userData.pin || '';
            
            // Adicionar credenciais como query parameters
            const url = new URL(button.redirect_url);
            url.searchParams.set('username', username);
            url.searchParams.set('password', password);
            console.log('💰 Redirecionando com credenciais:', url.toString());
            window.open(url.toString(), '_blank');
          } catch (error) {
            console.error('❌ Erro ao processar credenciais:', error);
            window.open(button.redirect_url, '_blank');
          }
        } else {
          window.open(button.redirect_url, '_blank');
        }
      } else {
        window.open(button.redirect_url, '_blank');
      }
      
      // ⚠️ NÃO RETORNAR! Continuar processando para mostrar mensagem do botão
    }
    
    // 🆕 Se botão tem API configurada, mostrar formulário de criação
    if (button?.api_url) {
      console.log('👤 Criação de usuário:', button.label);
      setSelectedButtonForUser(button);
      
      // 🔒 SEMPRE verificar se já tem dados salvos e bloquear
      const savedData = localStorage.getItem('vendas_user_data');
      if (savedData) {
        try {
          const parsed = JSON.parse(savedData);
          setUserFormData(parsed);
          setHasCreatedUser(true); // 🔒 GARANTIR bloqueio
          console.log('🔒 Campos serão bloqueados - usuário já criou teste');
        } catch (error) {
          console.error('Erro ao carregar dados salvos:', error);
        }
      }
      
      setShowUserForm(true);
      return;
    }
    
    setIsSending(true);
    
    try {
      // ✅ Adicionar mensagem do cliente mostrando qual botão escolheu
      const userMessage = {
        message_id: Date.now().toString(),
        from_type: 'client',
        text: buttonLabel,
        timestamp: new Date().toISOString(),
        has_button: false
      };
      setMessages(prev => [...prev, userMessage]);
      
      // Processar clique no backend
      const response = await fetch(`${BACKEND_URL}/api/vendas/button-click`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          session_id: sessionId, 
          button_id: buttonId 
        })
      });
      
      if (!response.ok) {
        throw new Error('Erro ao processar botão');
      }
      
      const data = await response.json();
      
      // Adicionar mensagem de resposta do bot com descrição
      setMessages(prev => [...prev, data.message]);
      
      // 🆕 Se tem sub-botões, apenas atualizar os botões (SEM mensagem de texto)
      if (data.has_sub_buttons && data.buttons && data.buttons.length > 0) {
        // ✅ Apenas mostrar os botões clicáveis (sem listar nomes em texto)
        setCurrentButtons(data.buttons);
      } else {
        // Se não tem sub-botões, limpar botões
        setCurrentButtons([]);
      }
      
      console.log('✅ Botão processado:', buttonLabel, '| Sub-botões:', data.buttons?.length || 0);
      
    } catch (error) {
      console.error('❌ Erro ao processar botão:', error);
      alert('Erro ao processar sua escolha. Tente novamente.');
    } finally {
      setIsSending(false);
    }
  };

  // 🆕 FUNÇÃO PARA CRIAR USUÁRIO VIA API
  const handleCreateUser = async () => {
    // Validação 1: Verificar se o botão foi selecionado
    if (!selectedButtonForUser) {
      console.error('❌ selectedButtonForUser está undefined');
      alert('Erro: Botão não identificado. Por favor, feche e abra o formulário novamente.');
      return;
    }
    
    // Validação 2: Verificar se o botão tem ID
    if (!selectedButtonForUser.id) {
      console.error('❌ selectedButtonForUser.id está undefined:', selectedButtonForUser);
      alert('Erro: Configuração do botão incompleta. Por favor, tente novamente.');
      return;
    }
    
    // Validação 3: Verificar campos do formulário
    if (!userFormData.name || !userFormData.whatsapp || !userFormData.pin) {
      alert('Por favor, preencha todos os campos');
      return;
    }
    
    if (userFormData.pin.length !== 2) {
      alert('A senha deve ter exatamente 2 dígitos');
      return;
    }
    
    setCreatingUser(true);
    
    try {
      console.log('📝 Criando usuário com:', {
        button_id: selectedButtonForUser.id,
        button_label: selectedButtonForUser.label,
        user_data: userFormData
      });
      
      // 🔄 Função com retry (até 2 tentativas)
      let response;
      let lastError;
      
      for (let attempt = 1; attempt <= 2; attempt++) {
        try {
          console.log(`🔄 Tentativa ${attempt}/2...`);
          
          response = await fetch(`${BACKEND_URL}/api/admin/vendas-bot/buttons/create-user`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              button_id: selectedButtonForUser.id,
              user_data: userFormData
            }),
            signal: AbortSignal.timeout(30000) // 30 segundos timeout
          });
          
          console.log('📡 Resposta do servidor:', response.status, response.statusText);
          
          if (response.ok) {
            break; // Sucesso! Sair do loop
          }
          
          // Erro HTTP
          const errorData = await response.json().catch(() => ({ detail: 'Erro desconhecido' }));
          console.error(`❌ Tentativa ${attempt} falhou:`, errorData);
          lastError = new Error(errorData.detail || 'Erro ao criar usuário');
          
          // Se for a primeira tentativa, aguardar 2s antes de tentar novamente
          if (attempt === 1) {
            console.log('⏳ Aguardando 2s antes de retry...');
            await new Promise(resolve => setTimeout(resolve, 2000));
          }
          
        } catch (fetchError) {
          console.error(`❌ Erro de rede na tentativa ${attempt}:`, fetchError);
          lastError = fetchError;
          
          // Se for a primeira tentativa, aguardar 2s antes de tentar novamente
          if (attempt === 1) {
            console.log('⏳ Aguardando 2s antes de retry...');
            await new Promise(resolve => setTimeout(resolve, 2000));
          }
        }
      }
      
      // Verificar se teve sucesso
      if (!response || !response.ok) {
        throw lastError || new Error('Erro ao criar usuário após 2 tentativas');
      }
      
      const data = await response.json();
      console.log('✅ Usuário criado:', data);
      
      // Salvar dados no localStorage e marcar que criou usuário
      localStorage.setItem('vendas_user_data', JSON.stringify(userFormData));
      setHasCreatedUser(true); // 🔒 BLOQUEAR campos na próxima abertura
      
      // Fechar formulário
      setShowUserForm(false);
      
      // ✅ Adicionar mensagem do cliente mostrando qual botão escolheu
      const userMessage = {
        message_id: Date.now().toString(),
        from_type: 'client',
        text: selectedButtonForUser.label,
        timestamp: new Date().toISOString(),
        has_button: false
      };
      setMessages(prev => [...prev, userMessage]);
      
      // Verificar se já tinha teste ativo
      if (data.already_exists) {
        // 🔒 TESTE JÁ EXISTE - Reenviar credenciais
        setTimeout(() => {
          const existingMessage = {
            message_id: `existing_${Date.now()}`,
            from_type: 'bot',
            text: `⚠️ Você já possui um teste ativo!\n\n✅ Suas credenciais:\n\n👤 **Usuário:** ${data.credentials.generated_user}\n🔑 **Senha:** ${data.credentials.generated_password}\n\n📱 WhatsApp: ${data.credentials.whatsapp}\n🔐 PIN: ${data.credentials.pin}\n\n💰 Para criar um novo teste, clique em **REALIZAR PAGAMENTO** e finalize seu plano.`,
            timestamp: new Date().toISOString(),
            has_button: false
          };
          setMessages(prev => [...prev, existingMessage]);
        }, 500);
      } else {
        // ✅ NOVO TESTE CRIADO
        setTimeout(() => {
          const credentialsMessage = {
            message_id: `cred_${Date.now()}`,
            from_type: 'bot',
            text: `✅ Teste criado com sucesso!\n\n👤 **Usuário:** ${data.credentials.generated_user}\n🔑 **Senha:** ${data.credentials.generated_password}\n\n📱 WhatsApp: ${data.credentials.whatsapp}\n🔐 PIN: ${data.credentials.pin}\n\n⚠️ **Importante:** Guarde essas informações!\n\n💡 Gostou? Clique em **REALIZAR PAGAMENTO** para continuar usando!`,
            timestamp: new Date().toISOString(),
            has_button: false
          };
          setMessages(prev => [...prev, credentialsMessage]);
        }, 500);
      }
      
    } catch (error) {
      console.error('❌ Erro ao criar usuário:', error);
      alert('Erro ao criar usuário. Tente novamente.');
    } finally {
      setCreatingUser(false);
    }
  };

  // 📋 FUNÇÃO PARA COPIAR CREDENCIAIS
  const handleCopyCredential = async (text, field) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedField(field);
      setTimeout(() => setCopiedField(null), 2000); // Limpar feedback após 2s
      console.log(`✅ ${field} copiado:`, text);
    } catch (error) {
      console.error('❌ Erro ao copiar:', error);
      alert('Erro ao copiar. Tente novamente.');
    }
  };

  // 🆕 FUNÇÃO PARA PROCESSAR PAGAMENTO (desbloqueia número)
  const handlePayment = async () => {
    try {
      // Buscar dados do usuário no localStorage
      const savedData = localStorage.getItem('vendas_user_data');
      if (!savedData) {
        alert('Dados não encontrados. Por favor, crie um teste primeiro.');
        return;
      }
      
      const userData = JSON.parse(savedData);
      
      // Marcar pagamento no backend
      const response = await fetch(`${BACKEND_URL}/api/admin/vendas-bot/buttons/mark-payment`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ whatsapp: userData.whatsapp })
      });
      
      if (!response.ok) {
        throw new Error('Erro ao processar pagamento');
      }
      
      const data = await response.json();
      
      // Adicionar mensagem de confirmação
      const confirmMessage = {
        message_id: `payment_${Date.now()}`,
        from_type: 'bot',
        text: `✅ **Pagamento registrado com sucesso!**\n\n🎉 Seu número foi liberado!\n\nAgora você pode criar novos testes a qualquer momento.\n\n👤 Usuário atual continua ativo:\n**Usuário:** ${userData.whatsapp}\n**PIN:** ${userData.pin}\n\nObrigado pela preferência! 💚`,
        timestamp: new Date().toISOString(),
        has_button: false
      };
      setMessages(prev => [...prev, confirmMessage]);
      
      console.log('✅ Pagamento processado');
      
    } catch (error) {
      console.error('❌ Erro ao processar pagamento:', error);
      alert('Erro ao processar pagamento. Tente novamente.');
    }
  };

  // 🆕 FUNÇÃO PARA RESETAR MENU DE BOTÕES
  const handleResetButtons = async () => {
    if (!sessionId) return;
    
    try {
      // Adicionar mensagem visual do reset
      const resetMessage = {
        message_id: `reset_${Date.now()}`,
        from_type: 'bot',
        text: '🔄 Voltando ao menu principal...',
        timestamp: new Date().toISOString(),
        has_button: false
      };
      setMessages(prev => [...prev, resetMessage]);
      
      // Chamar endpoint de reset
      const response = await fetch(`${BACKEND_URL}/api/vendas/button-reset`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId })
      });
      
      if (response.ok) {
        const data = await response.json();
        
        // Recarregar configuração inicial de botões
        try {
          const configResponse = await fetch(`${BACKEND_URL}/api/vendas/config`);
          const buttonConfigData = await configResponse.json();
          
          if (buttonConfigData.is_enabled && buttonConfigData.buttons.length > 0) {
            setCurrentButtons(buttonConfigData.buttons);
            
            // Mensagem com menu principal
            setTimeout(() => {
              const menuMessage = {
                message_id: `menu_${Date.now()}`,
                from_type: 'bot',
                text: '👇 Selecione uma opção:',
                timestamp: new Date().toISOString(),
                has_button: false
              };
              setMessages(prev => [...prev, menuMessage]);
            }, 300);
          }
        } catch (configError) {
          console.error('❌ Erro ao recarregar config:', configError);
          setCurrentButtons(data.buttons || []);
        }
        
        console.log('✅ Menu de botões resetado');
      }
    } catch (error) {
      console.error('❌ Erro ao resetar menu:', error);
      alert('Erro ao voltar ao início. Tente novamente.');
    }
  };

  const handleMediaUpload = async (file, mediaType) => {
    if (!file || !sessionId) return;
    
    // Mostrar pop-up de processamento
    const mediaTypeText = mediaType === 'audio' ? 'áudio' : mediaType === 'video' ? 'vídeo' : 'foto';
    alert(`Por favor, aguarde na conversa enquanto processamos o ${mediaTypeText}... ⏳`);
    
    setIsProcessingMedia(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('session_id', sessionId);
      formData.append('media_type', mediaType);
      
      const response = await fetch(`${BACKEND_URL}/api/vendas/media`, {
        method: 'POST',
        body: formData
      });
      
      if (!response.ok) throw new Error('Erro ao processar');
      
      const data = await response.json();
      
      // Remover delay desnecessário - processar imediatamente
      setMessages(prev => [...prev, ...data.messages]);
    } catch (error) {
      console.error('Erro:', error);
      alert('Erro ao processar arquivo. Tente novamente.');
    } finally {
      setIsProcessingMedia(false);
    }
  };

  const handleFileSelect = (e, mediaType) => {
    const file = e.target.files[0];
    if (!file) return;
    e.target.value = '';
    const maxSize = mediaType === 'video' ? 50 : mediaType === 'audio' ? 25 : 20;
    if (file.size > maxSize * 1024 * 1024) {
      alert(`Arquivo muito grande. Máximo: ${maxSize}MB`);
      return;
    }
    handleMediaUpload(file, mediaType);
  };

  const handleRequestTest = async () => {
    if (!clientName.trim() || !whatsapp || !pin || pin.length !== 2) {
      alert('Preencha Nome, WhatsApp e PIN de 2 dígitos!');
      return;
    }
    
    // 🆕 NOVO FLUXO: Primeiro perguntar sobre instalação do app
    setPendingTestData({ clientName, whatsapp, pin });
    setShowContactPopup(false);
    setShowAppInstallPopup(true);
  };
  
  // 🆕 NOVO: Gerar teste após confirmar instalação do app
  const handleGenerateTestAfterAppInstall = async () => {
    if (!pendingTestData) return;
    
    setIsGeneratingTest(true);
    
    try {
      const { clientName, whatsapp, pin } = pendingTestData;
      
      // Salvar nome e whatsapp no localStorage
      localStorage.setItem('vendas_name', clientName);
      localStorage.setItem('vendas_whatsapp', whatsapp);
      
      const response = await fetch(`${BACKEND_URL}/api/vendas/request-test`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          whatsapp: whatsapp,
          pin: pin,
          name: clientName
        })
      });
      
      const data = await response.json();
      
      if (data.success) {
        // Salvar credenciais
        setCredentials({
          usuario: data.usuario,
          senha: data.senha
        });
        
        // Fechar pop-up de instalação e abrir de credenciais
        setShowAppInstallPopup(false);
        setShowCredentialsPopup(true);
        
        // Adicionar mensagem no chat
        setMessages(prev => [...prev, {
          from_type: 'bot',
          text: data.message,
          timestamp: new Date().toISOString()
        }]);
      } else {
        alert(data.message || 'Erro ao gerar teste');
        setShowAppInstallPopup(false);
      }
    } catch (error) {
      console.error('Erro:', error);
      alert('Erro ao solicitar teste');
      setShowAppInstallPopup(false);
    } finally {
      setIsGeneratingTest(false);
      setPendingTestData(null);
    }
  };
  
  // 🆕 NOVO: Cliente recusou instalar app
  const handleDeclineAppInstall = () => {
    setShowAppInstallPopup(false);
    
    // Enviar mensagem de erro
    setMessages(prev => [...prev, {
      from_type: 'bot',
      text: '❌ Não foi possível gerar o teste grátis.\n\nPara receber suas credenciais, você precisa instalar o aplicativo suporte.help.\n\nDeseja instalar o aplicativo agora?',
      timestamp: new Date().toISOString()
    }]);
    
    // Reabrir popup após 1 segundo
    setTimeout(() => {
      setShowAppInstallPopup(true);
    }, 1500);
  };

  const handleDownloadApp = async () => {
    setShowCredentialsPopup(false);
    
    // Salvar dados no localStorage ANTES de instalar
    localStorage.setItem('iaze_whatsapp', whatsapp);
    localStorage.setItem('iaze_pin', pin);
    localStorage.setItem('iaze_iptv_user', credentials.usuario);
    localStorage.setItem('iaze_iptv_pass', credentials.senha);
    localStorage.setItem('iaze_from_vendas', 'true');
    localStorage.setItem('iaze_vendas_session', sessionId);
    
    console.log('💾 Dados salvos no localStorage:');
    console.log('  - iaze_whatsapp:', localStorage.getItem('iaze_whatsapp'));
    console.log('  - iaze_pin:', localStorage.getItem('iaze_pin'));
    console.log('  - iaze_from_vendas:', localStorage.getItem('iaze_from_vendas'));
    
    // Migrar sessão para o chat principal
    try {
      await fetch(`${BACKEND_URL}/api/vendas/migrate-session`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          vendas_session_id: sessionId,
          whatsapp: whatsapp,
          pin: pin,
          credentials: credentials
        })
      });
      console.log('✅ Sessão migrada com sucesso');
    } catch (error) {
      console.error('Erro ao migrar sessão:', error);
    }
    
    // Verificar se PWA está disponível para instalação
    if (window.deferredPrompt) {
      // Mostrar prompt de instalação
      window.deferredPrompt.prompt();
      
      // Aguardar resposta do usuário
      const { outcome } = await window.deferredPrompt.userChoice;
      
      if (outcome === 'accepted') {
        console.log('✅ PWA instalado com sucesso!');
        
        // Limpar o prompt
        window.deferredPrompt = null;
        
        // Mostrar pop-up de confirmação
        alert('✅ Nosso aplicativo de SUPORTE já está instalado em seu celular!');
        
        // Determinar URL de redirecionamento (usa hostname atual se não for localhost)
        const currentHost = window.location.hostname;
        const redirectUrl = (currentHost !== 'localhost' && currentHost !== '127.0.0.1')
          ? window.location.origin 
          : '/';
        
        console.log('🔄 Redirecionando para:', redirectUrl);
        
        // Redirecionar após confirmação
        window.location.href = redirectUrl;
      } else {
        console.log('❌ Usuário recusou instalação');
        alert('Por favor, instale o aplicativo para continuar com melhor experiência!');
      }
    } else {
      // PWA já instalado OU não disponível - apenas redirecionar
      console.log('ℹ️ PWA não disponível ou já instalado');
      alert('✅ Aplicativo pronto! Redirecionando para o suporte...');
      
      // Determinar URL de redirecionamento (usa hostname atual se não for localhost)
      const currentHost = window.location.hostname;
      const redirectUrl = (currentHost !== 'localhost' && currentHost !== '127.0.0.1')
        ? window.location.origin 
        : '/';
      
      console.log('🔄 Redirecionando para:', redirectUrl);
      
      // Redirecionar após 1 segundo
      setTimeout(() => {
        window.location.href = redirectUrl;
      }, 1000);
    }
  };

  const handleInstallApp = async () => {
    // Validar dados antes de prosseguir
    if (!whatsapp || !pin || pin.length !== 2) {
      alert('Por favor, preencha WhatsApp e PIN corretamente!');
      return;
    }
    
    try {
      // 1. Salvar tudo no localStorage ANTES de redirecionar
      localStorage.setItem('iaze_whatsapp', whatsapp);
      localStorage.setItem('iaze_pin', pin);
      localStorage.setItem('iaze_iptv_user', credentials.usuario);
      localStorage.setItem('iaze_iptv_pass', credentials.senha);
      localStorage.setItem('iaze_from_vendas', 'true');
      localStorage.setItem('iaze_vendas_session', sessionId);
      
      // 2. Migrar sessão do /vendas para o chat principal
      await fetch(`${BACKEND_URL}/api/vendas/migrate-session`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          vendas_session_id: sessionId,
          whatsapp: whatsapp,
          pin: pin,
          credentials: credentials
        })
      });
      
      // 3. Fechar pop-up
      setShowAppDownloadPopup(false);
      
      // 4. Mensagem de sucesso
      setMessages(prev => [...prev, {
        from_type: 'bot',
        text: 'Agora que recebeu o usuário e senha, "POR FAVOR" instala nosso aplicativo de Suporte Humanizado pra realizar a contratação após o teste! 📱\n\nVocê será redirecionado em 3 segundos...',
        timestamp: new Date().toISOString()
      }]);
      
      // 5. Redirecionar para o domínio atual (dados já salvos)
      setTimeout(() => {
        window.location.href = window.location.origin;
      }, 3000);
      
    } catch (error) {
      console.error('Erro ao processar instalação:', error);
      alert('Erro ao processar. Tente novamente.');
    }
  };

  const handleCloseChat = () => {
    setShowExitConfirm(true);
  };

  const confirmExit = (shouldExit) => {
    if (shouldExit) {
      // Mostrar mensagem de despedida
      setMessages(prev => [...prev, {
        from_type: 'bot',
        text: 'Caso você mude de ideia me chama nesse link de suporte!\n\nAté mais! 👋',
        timestamp: new Date().toISOString()
      }]);
      
      // Aguardar um pouco e redirecionar
      setTimeout(() => {
        window.location.href = '/';
      }, 2000);
    }
    setShowExitConfirm(false);
  };

  // Função para formatar mensagem com links e destaques
  // 📋 Extrair credenciais da mensagem (para botões de copiar)
  const extractCredentials = (text) => {
    if (!text) return null;
    
    const credentials = {};
    
    // ✅ VERSÃO SUPER RESTRITIVA - APENAS "Usuário: valor" e "Senha: valor"
    // Deve ter OBRIGATORIAMENTE dois pontos ":" seguido do valor
    
    // Buscar "Usuário:" (com emoji opcional, asteriscos, espaços) + dois pontos OBRIGATÓRIOS + valor alfanumérico
    const userRegex = /(?:🧑|👤)?\s*\*?\*?usuário\*?\*?\s*:\s*\*?\*?\s*([a-zA-Z0-9]{5,})/i;
    const userMatch = text.match(userRegex);
    
    if (userMatch && userMatch[1]) {
      const valor = userMatch[1].trim();
      // Validar que é realmente uma credencial (mínimo 5 caracteres alfanuméricos)
      if (valor.length >= 5 && /^[a-zA-Z0-9]+$/.test(valor)) {
        credentials.usuario = valor;
        console.log('✅ USUÁRIO VÁLIDO:', credentials.usuario);
      }
    }
    
    // Buscar "Senha:" (com emoji opcional, asteriscos, espaços) + dois pontos OBRIGATÓRIOS + valor alfanumérico
    const passRegex = /(?:🔑|🔐|🗝️)?\s*\*?\*?senha\*?\*?\s*:\s*\*?\*?\s*([a-zA-Z0-9]{5,})/i;
    const passMatch = text.match(passRegex);
    
    if (passMatch && passMatch[1]) {
      const valor = passMatch[1].trim();
      // Validar que é realmente uma credencial (mínimo 5 caracteres alfanuméricos)
      if (valor.length >= 5 && /^[a-zA-Z0-9]+$/.test(valor)) {
        credentials.senha = valor;
        console.log('✅ SENHA VÁLIDA:', credentials.senha);
      }
    }
    
    // ✅ Só retornar se encontrou PELO MENOS uma credencial válida
    if (credentials.usuario || credentials.senha) {
      console.log('🎯 BOTÕES VÃO APARECER - Credenciais válidas:', credentials);
      return credentials;
    }
    
    // ❌ Não encontrou credenciais válidas - NÃO mostrar botões
    return null;
  };

  const formatMessageText = (text) => {
    if (!text) return text;
    
    // Regex para detectar URLs
    const urlRegex = /(https?:\/\/[^\s]+|www\.[^\s]+)/g;
    
    // 🆕 Regex para detectar **texto em negrito**
    const boldRegex = /\*\*(.*?)\*\*/g;
    
    // Regex para detectar padrões importantes (usuário: xxx, senha: xxx, código: xxx)
    const highlightRegex = /(usuario|usuário|senha|codigo|código|login|email|telefone|cpf|chave):\s*([^\s,;.\n]+)/gi;
    
    let parts = [];
    let lastIndex = 0;
    
    // 🆕 Primeiro, processar **negrito** em todo o texto
    let processedText = text;
    const boldMatches = Array.from(text.matchAll(boldRegex));
    
    // Coletar todos os padrões (negrito, links) e ordenar por posição
    const allMatches = [
      ...Array.from(text.matchAll(boldRegex)).map(m => ({ ...m, type: 'bold' })),
      ...Array.from(text.matchAll(urlRegex)).map(m => ({ ...m, type: 'link' }))
    ].sort((a, b) => a.index - b.index);
    
    for (const match of allMatches) {
      const offset = match.index;
      
      // Adicionar texto antes do match
      if (offset > lastIndex) {
        const beforeText = text.substring(lastIndex, offset);
        parts.push({ type: 'text', content: beforeText });
      }
      
      if (match.type === 'bold') {
        // Adicionar texto em negrito (sem os **)
        parts.push({ type: 'bold', content: match[1] }); // match[1] é o conteúdo entre **
        lastIndex = offset + match[0].length;
      } else if (match.type === 'link') {
        // Adicionar link
        const url = match[0].startsWith('www.') ? `https://${match[0]}` : match[0];
        parts.push({ type: 'link', content: match[0], url: url });
        lastIndex = offset + match[0].length;
      }
    }
    
    // Adicionar texto restante
    if (lastIndex < text.length) {
      parts.push({ type: 'text', content: text.substring(lastIndex) });
    }
    
    // Se não encontrou nada, processar texto normal
    if (parts.length === 0) {
      parts.push({ type: 'text', content: text });
    }
    
    // Processar destaques em cada parte de texto
    const finalParts = [];
    parts.forEach(part => {
      if (part.type === 'text') {
        const textParts = [];
        let textLastIndex = 0;
        
        part.content.replace(highlightRegex, (match, label, value, offset) => {
          // Texto antes do destaque
          if (offset > textLastIndex) {
            textParts.push({ type: 'text', content: part.content.substring(textLastIndex, offset) });
          }
          
          // Destaque
          textParts.push({ 
            type: 'highlight', 
            label: label, 
            value: value 
          });
          
          textLastIndex = offset + match.length;
        });
        
        // Texto restante
        if (textLastIndex < part.content.length) {
          textParts.push({ type: 'text', content: part.content.substring(textLastIndex) });
        }
        
        if (textParts.length > 0) {
          finalParts.push(...textParts);
        } else {
          finalParts.push(part);
        }
      } else {
        finalParts.push(part);
      }
    });
    
    return finalParts;
  };

  const renderMessage = (msg, index) => {
    const senderClass = msg.from_type === 'client' ? 'user' : 'bot';
    const formattedParts = formatMessageText(msg.text);
    
    return (
      <div key={index} className={`vendas-message ${senderClass}`}>
        <div className="vendas-message-bubble">
          {/* 🆕 Renderizar mídia se existir */}
          {msg.media_url && (
            <div className="vendas-message-media" style={{marginBottom: '8px'}}>
              {msg.media_type === 'image' ? (
                <img 
                  src={msg.media_url} 
                  alt="Mídia" 
                  style={{
                    maxWidth: '100%',
                    maxHeight: '300px',
                    borderRadius: '8px',
                    objectFit: 'cover'
                  }}
                />
              ) : msg.media_type === 'video' ? (
                <video 
                  src={msg.media_url} 
                  controls 
                  style={{
                    maxWidth: '100%',
                    maxHeight: '300px',
                    borderRadius: '8px'
                  }}
                />
              ) : null}
            </div>
          )}
          
          <div className="vendas-message-text" style={{whiteSpace: 'pre-wrap'}}>
            {Array.isArray(formattedParts) ? (
              formattedParts.map((part, i) => {
                if (part.type === 'link') {
                  return (
                    <a 
                      key={i} 
                      href={part.url} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      style={{ 
                        color: '#3b82f6', 
                        textDecoration: 'underline',
                        wordBreak: 'break-all'
                      }}
                    >
                      {part.content}
                    </a>
                  );
                } else if (part.type === 'bold') {
                  return (
                    <strong 
                      key={i}
                      style={{ 
                        fontWeight: 'bold',
                        color: '#d97706',
                        fontSize: '1.05em'
                      }}
                    >
                      {part.content}
                    </strong>
                  );
                } else if (part.type === 'highlight') {
                  return (
                    <span key={i}>
                      <span style={{ fontWeight: 'normal' }}>{part.label}: </span>
                      <strong 
                        style={{ 
                          backgroundColor: '#fef3c7', 
                          padding: '2px 6px', 
                          borderRadius: '4px',
                          fontWeight: 'bold',
                          color: '#92400e'
                        }}
                      >
                        {part.value}
                      </strong>
                    </span>
                  );
                } else {
                  return <span key={i}>{part.content}</span>;
                }
              })
            ) : (
              <span>{msg.text}</span>
            )}
          </div>
          
          {/* 📋 Botões para copiar credenciais */}
          {(() => {
            const credentials = extractCredentials(msg.text);
            if (!credentials || msg.from_type === 'client') return null;
            
            return (
              <div style={{
                display: 'flex',
                gap: '8px',
                marginTop: '12px',
                flexWrap: 'wrap'
              }}>
                {credentials.usuario && (
                  <button
                    onClick={() => handleCopyCredential(credentials.usuario, 'usuario')}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px',
                      padding: '8px 12px',
                      backgroundColor: copiedField === 'usuario' ? '#10b981' : '#3b82f6',
                      color: 'white',
                      border: 'none',
                      borderRadius: '6px',
                      fontSize: '13px',
                      fontWeight: '500',
                      cursor: 'pointer',
                      transition: 'all 0.2s'
                    }}
                  >
                    <span>{copiedField === 'usuario' ? '✅' : '📋'}</span>
                    <span>{copiedField === 'usuario' ? 'Copiado!' : 'Copiar Usuário'}</span>
                  </button>
                )}
                
                {credentials.senha && (
                  <button
                    onClick={() => handleCopyCredential(credentials.senha, 'senha')}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px',
                      padding: '8px 12px',
                      backgroundColor: copiedField === 'senha' ? '#10b981' : '#3b82f6',
                      color: 'white',
                      border: 'none',
                      borderRadius: '6px',
                      fontSize: '13px',
                      fontWeight: '500',
                      cursor: 'pointer',
                      transition: 'all 0.2s'
                    }}
                  >
                    <span>{copiedField === 'senha' ? '✅' : '📋'}</span>
                    <span>{copiedField === 'senha' ? 'Copiado!' : 'Copiar Senha'}</span>
                  </button>
                )}
              </div>
            );
          })()}
          
          {msg.button_action === 'REQUEST_TEST' && (
            <button 
              className="vendas-action-button"
              onClick={() => setShowContactPopup(true)}
            >
              🚀 CONECTAR AGORA
            </button>
          )}
          
          <span className="vendas-message-time">
            {new Date(msg.timestamp).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}
          </span>
        </div>
      </div>
    );
  };

  if (isLoading) {
    return (
      <div className="vendas-chat-container">
        <div style={{display:'flex',flexDirection:'column',alignItems:'center',justifyContent:'center',height:'100%',color:'white'}}>
          <Loader2 size={48} style={{animation:'spin 1s linear infinite',marginBottom:'16px'}} />
          <p>Iniciando conversa...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="vendas-chat-container">
      {/* 🆕 Modal: Formulário de Criação de Usuário */}
      {showUserForm && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.7)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 9999
        }}>
          <div style={{
            backgroundColor: 'white',
            borderRadius: '12px',
            padding: '24px',
            maxWidth: '400px',
            width: '90%',
            boxShadow: '0 4px 20px rgba(0,0,0,0.3)'
          }}>
            {console.log('🔍 DEBUG Modal Aberto:', {
              selectedButtonForUser,
              buttonId: selectedButtonForUser?.id,
              buttonLabel: selectedButtonForUser?.label,
              hasCreatedUser,
              userFormData
            })}
            
            <h3 style={{
              fontSize: '20px',
              fontWeight: 'bold',
              marginBottom: '16px',
              color: '#333'
            }}>
              👤 Criar Usuário - {selectedButtonForUser?.label || 'Carregando...'}
            </h3>
            
            {hasCreatedUser && (
              <div style={{
                padding: '12px',
                backgroundColor: '#fef3c7',
                borderRadius: '8px',
                marginBottom: '16px',
                fontSize: '14px',
                color: '#92400e'
              }}>
                🔒 <strong>Atenção:</strong> Você já criou um teste. Os campos WhatsApp e PIN estão bloqueados para evitar múltiplos testes grátis.
              </div>
            )}
            
            <div style={{ marginBottom: '16px' }}>
              <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', fontWeight: '500' }}>
                Nome Completo:
              </label>
              <input
                type="text"
                value={userFormData.name}
                onChange={(e) => setUserFormData({...userFormData, name: e.target.value})}
                placeholder="Seu nome"
                style={{
                  width: '100%',
                  padding: '10px',
                  border: '1px solid #ddd',
                  borderRadius: '8px',
                  fontSize: '15px'
                }}
              />
            </div>
            
            <div style={{ marginBottom: '16px' }}>
              <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', fontWeight: '500' }}>
                WhatsApp (com DDD):
                {hasCreatedUser && <span style={{ color: '#f59e0b', fontSize: '12px', marginLeft: '8px' }}>🔒 Bloqueado</span>}
              </label>
              <input
                type="tel"
                value={userFormData.whatsapp}
                onChange={(e) => setUserFormData({...userFormData, whatsapp: e.target.value})}
                placeholder="11999999999"
                disabled={hasCreatedUser}
                readOnly={hasCreatedUser}
                style={{
                  width: '100%',
                  padding: '10px',
                  border: '1px solid #ddd',
                  borderRadius: '8px',
                  fontSize: '15px',
                  backgroundColor: hasCreatedUser ? '#f3f4f6' : 'white',
                  cursor: hasCreatedUser ? 'not-allowed' : 'text',
                  opacity: hasCreatedUser ? 0.7 : 1
                }}
              />
              {hasCreatedUser && (
                <p style={{ fontSize: '12px', color: '#ef4444', marginTop: '4px' }}>
                  ⚠️ Não é possível alterar o WhatsApp após criar teste
                </p>
              )}
            </div>
            
            <div style={{ marginBottom: '20px' }}>
              <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', fontWeight: '500' }}>
                Escolha uma Senha (2 dígitos):
                {hasCreatedUser && <span style={{ color: '#f59e0b', fontSize: '12px', marginLeft: '8px' }}>🔒 Bloqueado</span>}
              </label>
              <input
                type="text"
                value={userFormData.pin}
                onChange={(e) => {
                  const value = e.target.value.replace(/\D/g, '').slice(0, 2);
                  setUserFormData({...userFormData, pin: value});
                }}
                placeholder="00"
                maxLength={2}
                disabled={hasCreatedUser}
                readOnly={hasCreatedUser}
                style={{
                  width: '100%',
                  padding: '10px',
                  border: '1px solid #ddd',
                  borderRadius: '8px',
                  fontSize: '15px',
                  textAlign: 'center',
                  letterSpacing: '4px',
                  backgroundColor: hasCreatedUser ? '#f3f4f6' : 'white',
                  cursor: hasCreatedUser ? 'not-allowed' : 'text',
                  opacity: hasCreatedUser ? 0.7 : 1
                }}
              />
              {hasCreatedUser && (
                <p style={{ fontSize: '12px', color: '#ef4444', marginTop: '4px' }}>
                  ⚠️ Não é possível alterar o PIN após criar teste
                </p>
              )}
            </div>
            
            <div style={{ display: 'flex', gap: '12px' }}>
              <button
                onClick={() => setShowUserForm(false)}
                disabled={creatingUser}
                style={{
                  flex: 1,
                  padding: '12px',
                  backgroundColor: '#ddd',
                  border: 'none',
                  borderRadius: '8px',
                  fontSize: '15px',
                  fontWeight: '500',
                  cursor: creatingUser ? 'not-allowed' : 'pointer',
                  opacity: creatingUser ? 0.5 : 1
                }}
              >
                Cancelar
              </button>
              <button
                onClick={handleCreateUser}
                disabled={creatingUser}
                style={{
                  flex: 1,
                  padding: '12px',
                  backgroundColor: '#25D366',
                  color: 'white',
                  border: 'none',
                  borderRadius: '8px',
                  fontSize: '15px',
                  fontWeight: '500',
                  cursor: creatingUser ? 'not-allowed' : 'pointer',
                  opacity: creatingUser ? 0.5 : 1
                }}
              >
                {creatingUser ? 'Criando...' : 'Criar Usuário'}
              </button>
            </div>
          </div>
        </div>
      )}
      
      {/* Header */}
      <div className="vendas-chat-header">
        <div className="vendas-chat-header-info">
          <div className="vendas-chat-avatar">
            {agentProfile.photo ? (
              <img 
                src={agentProfile.photo} 
                alt="Agente" 
                style={{ 
                  width: '40px', 
                  height: '40px', 
                  borderRadius: '50%', 
                  objectFit: 'cover' 
                }}
                onError={(e) => { e.target.style.display = 'none'; e.target.nextSibling.style.display = 'block'; }}
              />
            ) : null}
            <span style={{ display: agentProfile.photo ? 'none' : 'block', fontSize: '24px' }}>🤖</span>
          </div>
          <div className="vendas-chat-title">
            <p className="vendas-chat-name" style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              {agentProfile.name || 'Assistente Virtual'}
              {agentProfile.show_verified_badge && (
                <span 
                  style={{ 
                    display: 'inline-flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    width: '16px',
                    height: '16px',
                    backgroundColor: '#1d9bf0',
                    borderRadius: '50%',
                    color: 'white',
                    fontSize: '10px',
                    fontWeight: 'bold',
                    marginLeft: '2px'
                  }}
                  title="Verificado"
                >
                  ✓
                </span>
              )}
            </p>
            <p className="vendas-chat-status">{isProcessingMedia ? 'Processando mídia...' : 'Online'}</p>
          </div>
        </div>
        <button className="vendas-chat-close-btn" onClick={handleCloseChat}>
          <X size={20} />
        </button>
      </div>

      {/* Mensagens */}
      <div className="vendas-chat-messages-area">
        {messages.map((msg, i) => renderMessage(msg, i))}
        
        {isSending && (
          <div className="vendas-message bot">
            <div className="vendas-typing-indicator">
              <div className="vendas-typing-dot"></div>
              <div className="vendas-typing-dot"></div>
              <div className="vendas-typing-dot"></div>
            </div>
          </div>
        )}
        
        {isProcessingMedia && (
          <div className="vendas-message bot">
            <div className="vendas-message-bubble">
              <div style={{display:'flex',alignItems:'center',gap:'8px'}}>
                <Loader2 size={16} style={{animation:'spin 1s linear infinite'}} />
                <span>Processando arquivo...</span>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* 🆕 BOTÕES INTERATIVOS */}
      {buttonConfig.is_enabled && currentButtons.length > 0 && (
        <div className="vendas-buttons-container" style={{
          padding: '16px',
          display: 'flex',
          flexDirection: 'column',
          gap: '8px',
          backgroundColor: '#f5f5f5',
          borderTop: '1px solid #e0e0e0'
        }}>
          {currentButtons.map((button) => {
            // Definir cores baseado na configuração
            const buttonColor = 
              button.color === 'blue' ? '#0088cc' :
              button.color === 'red' ? '#dc2626' :
              '#25D366'; // verde padrão
            
            const buttonColorHover = 
              button.color === 'blue' ? '#006699' :
              button.color === 'red' ? '#b91c1c' :
              '#1fb855'; // verde escuro
            
            return (
              <button
                key={button.id}
                onClick={() => handleButtonClick(button.id, button.label, button)}
                disabled={isSending}
                className={button.pulse ? 'vendas-button-pulse' : ''}
                style={{
                  padding: '12px 16px',
                  backgroundColor: buttonColor,
                  color: 'white',
                  border: 'none',
                  borderRadius: '8px',
                  fontSize: '15px',
                  fontWeight: '500',
                  cursor: isSending ? 'not-allowed' : 'pointer',
                  opacity: isSending ? 0.6 : 1,
                  transition: 'all 0.2s',
                  textAlign: 'left',
                  boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
                }}
                onMouseEnter={(e) => {
                  if (!isSending) {
                    e.target.style.backgroundColor = buttonColorHover;
                    e.target.style.transform = 'translateY(-2px)';
                    e.target.style.boxShadow = '0 4px 8px rgba(0,0,0,0.15)';
                  }
                }}
                onMouseLeave={(e) => {
                  if (!isSending) {
                    e.target.style.backgroundColor = buttonColor;
                    e.target.style.transform = 'translateY(0)';
                    e.target.style.boxShadow = '0 2px 4px rgba(0,0,0,0.1)';
                  }
                }}
              >
                {button.label}
              </button>
            );
          })}
          
          {/* 🆕 Botão "Voltar ao Início" - Sempre visível quando tem botões */}
          {currentButtons.length > 0 && (
            <button
              onClick={handleResetButtons}
              disabled={isSending}
              style={{
                padding: '10px 16px',
                backgroundColor: '#666',
                color: 'white',
                border: 'none',
                borderRadius: '8px',
                fontSize: '14px',
                fontWeight: '500',
                cursor: isSending ? 'not-allowed' : 'pointer',
                opacity: isSending ? 0.6 : 1,
                transition: 'all 0.2s',
                textAlign: 'center',
                boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                marginTop: '8px'
              }}
              onMouseEnter={(e) => {
                if (!isSending) {
                  e.target.style.backgroundColor = '#555';
                  e.target.style.transform = 'translateY(-2px)';
                  e.target.style.boxShadow = '0 4px 8px rgba(0,0,0,0.15)';
                }
              }}
              onMouseLeave={(e) => {
                if (!isSending) {
                  e.target.style.backgroundColor = '#666';
                  e.target.style.transform = 'translateY(0)';
                  e.target.style.boxShadow = '0 2px 4px rgba(0,0,0,0.1)';
                }
              }}
            >
              ◀️ Voltar ao Início
            </button>
          )}
        </div>
      )}

      {/* Input - Ocultar se modo = "button" (status = 1) */}
      <div className="vendas-chat-input-area" style={{
        display: (buttonConfig.is_enabled && buttonConfig.status === 1) ? 'none' : 'flex'
      }}>
        <div className="vendas-media-buttons">
          <button className="vendas-media-btn" title="Enviar foto ou vídeo" disabled={isProcessingMedia}>
            <ImageIcon size={26} />
            <input type="file" accept="image/*,video/*" onChange={(e) => handleFileSelect(e, e.target.files[0]?.type.startsWith('video') ? 'video' : 'image')} disabled={isProcessingMedia} />
          </button>
          <button className="vendas-media-btn" title="Enviar áudio" disabled={isProcessingMedia}>
            <Mic size={26} />
            <input type="file" accept="audio/*" onChange={(e) => handleFileSelect(e, 'audio')} disabled={isProcessingMedia} />
          </button>
        </div>
        <div className="vendas-input-wrapper">
          <textarea ref={inputRef} className="vendas-chat-input" placeholder="Digite uma mensagem..." value={inputText} onChange={(e) => setInputText(e.target.value)} onKeyPress={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); } }} rows={1} disabled={isSending || isProcessingMedia} />
        </div>
        <button className="vendas-send-btn" onClick={sendMessage} disabled={!inputText.trim() || isSending || isProcessingMedia}>
          <Send size={20} />
        </button>
      </div>

      {/* Pop-up 1: Solicitar WhatsApp + PIN + Nome */}
      {showContactPopup && (
        <div className="vendas-popup-overlay">
          <div className="vendas-popup">
            <h3>📱 Digite seus dados</h3>
            <p>Para gerar o teste, precisamos do seu nome, WhatsApp e uma senha de 2 dígitos</p>
            
            <input
              type="text"
              placeholder="Nome (ex: João)"
              value={clientName}
              onChange={(e) => setClientName(e.target.value)}
              className="vendas-popup-input"
            />
            
            <input
              type="tel"
              placeholder="WhatsApp (ex: 11999999999)"
              value={whatsapp}
              onChange={(e) => setWhatsapp(e.target.value.replace(/\D/g, ''))}
              maxLength="11"
              className="vendas-popup-input"
            />
            
            <input
              type="text"
              placeholder="Senha de 2 dígitos (ex: 42)"
              value={pin}
              onChange={(e) => setPin(e.target.value.replace(/\D/g, ''))}
              maxLength="2"
              className="vendas-popup-input"
            />
            
            <button 
              className="vendas-popup-btn"
              onClick={handleRequestTest}
              disabled={isGeneratingTest || !clientName.trim() || !whatsapp || pin.length !== 2}
            >
              {isGeneratingTest ? (
                <>
                  <Loader2 size={16} style={{animation:'spin 1s linear infinite'}} />
                  Gerando...
                </>
              ) : (
                '🎉 GERAR TESTE'
              )}
            </button>
            
            <button className="vendas-popup-btn-cancel" onClick={() => {
              // Salvar WhatsApp e Nome mesmo se cancelar
              if (whatsapp) {
                localStorage.setItem('vendas_whatsapp', whatsapp);
              }
              if (clientName) {
                localStorage.setItem('vendas_name', clientName);
              }
              initSession(whatsapp, clientName);
              setShowContactPopup(false);
            }}>
              Continuar sem gerar teste
            </button>
          </div>
        </div>
      )}

      {/* 🆕 NOVO Pop-up: Confirmar Instalação do App */}
      {showAppInstallPopup && (
        <div className="vendas-popup-overlay">
          <div className="vendas-popup">
            <h3>📱 Instalar Aplicativo</h3>
            <p style={{marginBottom: '20px'}}>
              Antes de gerar o teste grátis, você precisa instalar nosso aplicativo <strong>suporte.help</strong>
            </p>
            
            <div style={{background: '#f3f4f6', padding: '16px', borderRadius: '8px', marginBottom: '20px'}}>
              <p style={{margin: '0', fontSize: '14px', color: '#666'}}>
                ℹ️ O aplicativo é necessário para você utilizar suas credenciais de teste
              </p>
            </div>
            
            <p style={{fontSize: '16px', fontWeight: 'bold', marginBottom: '16px'}}>
              Você já instalou o aplicativo?
            </p>
            
            <div style={{display: 'flex', gap: '12px'}}>
              <button 
                className="vendas-popup-btn"
                onClick={handleGenerateTestAfterAppInstall}
                disabled={isGeneratingTest}
                style={{flex: 1}}
              >
                {isGeneratingTest ? (
                  <>
                    <Loader2 size={16} style={{animation:'spin 1s linear infinite'}} />
                    Gerando...
                  </>
                ) : (
                  '✅ SIM, INSTALAR'
                )}
              </button>
              
              <button 
                className="vendas-popup-btn-cancel"
                onClick={handleDeclineAppInstall}
                disabled={isGeneratingTest}
                style={{flex: 1}}
              >
                ❌ NÃO INSTALEI
              </button>
            </div>
            
            <p style={{fontSize: '12px', color: '#888', marginTop: '16px', textAlign: 'center'}}>
              Clique em "SIM, INSTALAR" quando tiver instalado o app
            </p>
          </div>
        </div>
      )}

      {/* Pop-up 2: Credenciais Geradas */}
      {showCredentialsPopup && (
        <div className="vendas-popup-overlay">
          <div className="vendas-popup">
            <h3>🎉 Teste Criado!</h3>
            <p>Suas credenciais foram geradas com sucesso:</p>
            
            <div className="vendas-credentials">
              <div className="vendas-credential-item">
                <strong>👤 Usuário:</strong>
                <span>{credentials.usuario}</span>
              </div>
              <div className="vendas-credential-item">
                <strong>🔐 Senha:</strong>
                <span>{credentials.senha}</span>
              </div>
            </div>
            
            <button className="vendas-popup-btn" onClick={handleDownloadApp}>
              <Download size={16} />
              BAIXAR APLICATIVO
            </button>
          </div>
        </div>
      )}

      {/* Pop-up 4: Confirmação de Saída */}
      {showExitConfirm && (
        <div className="vendas-popup-overlay">
          <div className="vendas-popup">
            <AlertCircle size={48} style={{color:'#f59e0b',margin:'0 auto 16px'}} />
            <h3>Você deseja continuar na página?</h3>
            
            <div style={{display:'flex',gap:'12px',marginTop:'24px'}}>
              <button className="vendas-popup-btn" onClick={() => confirmExit(false)}>
                ✅ SIM
              </button>
              <button className="vendas-popup-btn-cancel" onClick={() => confirmExit(true)}>
                ❌ NÃO
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 🚫 Pop-up 5: Bloqueio de Navegação - Confirmação de Saída */}
      {showNavigationBlockPopup && (
        <div className="vendas-popup-overlay" style={{zIndex: 99999}}>
          <div className="vendas-popup" style={{maxWidth: '400px'}}>
            <AlertCircle size={56} style={{color:'#ef4444',margin:'0 auto 20px'}} />
            <h3 style={{fontSize: '20px', marginBottom: '16px', color: '#1f2937'}}>
              Deseja realmente fechar a página?
            </h3>
            <p style={{fontSize: '16px', color: '#6b7280', marginBottom: '24px', lineHeight: '1.5'}}>
              Você perderá a <strong style={{color: '#ef4444'}}>promoção com 3 telas liberadas!</strong>
            </p>
            
            <div style={{display:'flex', gap:'12px', marginTop:'24px'}}>
              <button 
                className="vendas-popup-btn-cancel" 
                onClick={handleAllowExit}
                style={{flex: 1, fontSize: '16px', padding: '14px'}}
              >
                SIM
              </button>
              <button 
                className="vendas-popup-btn" 
                onClick={handleCancelExit}
                style={{flex: 1, fontSize: '16px', padding: '14px'}}
              >
                NÃO
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default VendasChatNew;
