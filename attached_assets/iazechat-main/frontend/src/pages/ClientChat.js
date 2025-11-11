import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { MessageCircle, Send, Paperclip, Mic, LogOut, Bell, Settings, User, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Card } from '@/components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { ScrollArea } from '@/components/ui/scroll-area';
import { toast } from 'sonner';
import api, { createWebSocket } from '../lib/api';
import { clearAuth, getAuth } from '../lib/auth';
import { formatWhatsApp, isWithinBusinessHours, shouldShowQueuePopup, markQueuePopupShown } from '../utils/formatters';
import AlertModal from '../components/AlertModal';
import InstallPWA from '../components/InstallPWA';
import WhatsAppAudioPlayer from '../components/WhatsAppAudioPlayer';
import usePushNotifications from '../lib/usePushNotifications';

const ClientChat = () => {
  const navigate = useNavigate();
  const auth = getAuth();
  const [userData, setUserData] = useState(auth.userData);
  const [messages, setMessages] = useState([]);
  const [messageText, setMessageText] = useState('');
  const [credentials, setCredentials] = useState({ pinned_user: '', pinned_pass: '' });
  const [notices, setNotices] = useState([]);
  const [showNotices, setShowNotices] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [newPin, setNewPin] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [hasNewNotices, setHasNewNotices] = useState(false);
  const [onlineStatus, setOnlineStatus] = useState('Carregando...');
  const [lastNoticeCount, setLastNoticeCount] = useState(0);
  const [showNoticePopup, setShowNoticePopup] = useState(false);  // Popup automático
  const [alertModal, setAlertModal] = useState({ isOpen: false, title: '', message: '', icon: 'info' });
  const [showNamePopup, setShowNamePopup] = useState(false);
  const [nameInput, setNameInput] = useState('');
  const [firstMessageSent, setFirstMessageSent] = useState(false);
  const [pixKey, setPixKey] = useState('');
  const wsRef = useRef(null);
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const queueTimerRef = useRef(null);
  const notificationAudioRef = useRef(null);
  const reconnectAttempts = useRef(0);
  // Removido maxReconnectAttempts - reconectar infinitamente
  const [audioEnabled, setAudioEnabled] = useState(false);
  const [lightboxImage, setLightboxImage] = useState(null);
  const [config, setConfig] = useState({ support_avatar: '' });
  const [isSendingMessage, setIsSendingMessage] = useState(false);
  const [uploadingAvatar, setUploadingAvatar] = useState(false);
  const avatarInputRef = useRef(null);
  const [showExitConfirm, setShowExitConfirm] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const messageInputRef = useRef(null);
  const [showCredentialsPopup, setShowCredentialsPopup] = useState(false); // 🆕 Popup de credenciais
  const credentialsTimeoutRef = useRef(null); // 🆕 Timer para fechar popup
  
  // Push Notifications
  const pushNotifications = usePushNotifications(
    userData?.client_id,
    userData?.reseller_id
  );

  // Função para conectar WebSocket com reconexão automática
  const connectWebSocket = () => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      console.log('✅ WebSocket já está conectado');
      return; // Já conectado
    }
    
    // Fechar conexão anterior se existir
    if (wsRef.current) {
      try {
        wsRef.current.close();
      } catch (e) {
        console.log('Erro ao fechar WebSocket anterior:', e);
      }
      wsRef.current = null;
    }
    
    // Remover limite de tentativas - reconectar infinitamente em background
    
    if (!userData?.id) {
      console.warn('⚠️ Aguardando dados do usuário para conectar WebSocket');
      setTimeout(() => connectWebSocket(), 1000); // Tentar novamente em 1s
      return;
    }
    
    console.log(`🔌 Tentando conectar WebSocket (tentativa ${reconnectAttempts.current + 1})`);
    const ws = createWebSocket(userData.id);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('✅ WebSocket conectado - Mensagens INSTANTÂNEAS ativadas!');
      reconnectAttempts.current = 0; // Reset contador ao conectar com sucesso
      setOnlineStatus('🟢 Online - Tempo Real');
      // Remover toast de sucesso - muito barulho visual
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log('📨 Nova mensagem via WebSocket:', data);
      
      // Mensagens de chat (novo tipo ou tipo message)
      if ((data.type === 'new_message' || data.type === 'message') && data.message) {
        setMessages(prev => {
          // Evitar duplicação
          if (prev.some(m => m.id === data.message.id)) {
            console.log('⚠️ Mensagem duplicada ignorada');
            return prev;
          }
          console.log('✅ Nova mensagem adicionada:', data.message.text?.substring(0, 50));
          
          // REGRA RIGOROSA: Som de notificação para TODAS as mensagens novas (exceto as próprias)
          if (data.message.from_type !== 'client') {
            // Tocar som de notificação do WhatsApp
            try {
              if (notificationAudioRef.current) {
                // Resetar o áudio para o início para permitir tocar novamente
                notificationAudioRef.current.currentTime = 0;
                notificationAudioRef.current.volume = 1.0;
                
                // Tentar tocar - usando Promise
                const playPromise = notificationAudioRef.current.play();
                
                if (playPromise !== undefined) {
                  playPromise
                    .then(() => {
                      console.log('🔊 Som de notificação tocado com sucesso!');
                    })
                    .catch((error) => {
                      console.warn('⚠️ Não foi possível tocar o som (autoplay bloqueado):', error);
                      // Tentar criar um novo áudio como fallback
                      try {
                        const fallbackAudio = new Audio('/notification.mp3');
                        fallbackAudio.volume = 1.0;
                        fallbackAudio.play().catch(e => console.log('Fallback também falhou:', e));
                      } catch (e) {
                        console.error('Erro no fallback:', e);
                      }
                    });
                }
              }
            } catch (e) {
              console.error('❌ Erro ao tocar som:', e);
            }
            
            // Vibrar dispositivo (se suportado)
            if ('vibrate' in navigator) {
              navigator.vibrate([200, 100, 200]);
            }
            
            // Atualizar badge count se página estiver em background
            if (document.hidden && 'setAppBadge' in navigator) {
              // Contar mensagens não lidas (do suporte)
              const unreadCount = prev.filter(m => m.from_type !== 'client').length + 1;
              navigator.setAppBadge(unreadCount)
                .then(() => console.log(`🔢 Badge atualizado: ${unreadCount} mensagens`))
                .catch(err => console.warn('Erro ao atualizar badge:', err));
            }
            
            // Mostrar notificação do navegador se página não estiver em foco
            if ('Notification' in window && Notification.permission === 'granted' && document.hidden) {
              try {
                const notification = new Notification('Nova mensagem de Suporte', {
                  body: data.message.text || 'Você recebeu uma nova mensagem',
                  icon: '/icon-192.png',
                  badge: '/icon-192.png',
                  tag: 'chat-message',
                  requireInteraction: false,
                  silent: false // Não silenciar - queremos o som do sistema também
                });
                
                // Clicar na notificação foca na janela
                notification.onclick = () => {
                  window.focus();
                  notification.close();
                  // Limpar badge ao focar na janela
                  if ('clearAppBadge' in navigator) {
                    navigator.clearAppBadge();
                  }
                };
                
                // Fechar notificação automaticamente após 5 segundos
                setTimeout(() => notification.close(), 5000);
              } catch (e) {
                console.error('Erro ao mostrar notificação:', e);
              }
            }
            
            // Toast notification (banner no topo) quando app está aberto
            if (!document.hidden) {
              toast.info(`💬 ${data.message.text || 'Nova mensagem'}`, {
                duration: 4000,
                position: 'top-center',
                style: {
                  background: '#075E54',
                  color: 'white',
                  borderRadius: '8px',
                  padding: '12px 20px'
                }
              });
            }
          }
          
          return [...prev, data.message];
        });
        
        // Scroll automático para a nova mensagem
        setTimeout(() => {
          messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
        }, 100);
      }
      
      // Credenciais atualizadas
      if (data.type === 'credentials_updated') {
        setCredentials({ 
          pinned_user: data.pinned_user, 
          pinned_pass: data.pinned_pass 
        });
      }
      
      // Comentado: Não forçar logout automático
      // if (data.type === 'force_logout') {
      //   clearAuth();
      //   alert('Você foi desconectado porque outra pessoa fez login com suas credenciais.');
      //   navigate('/');
      // }
    };

    ws.onerror = (error) => {
      console.error('❌ Erro no WebSocket:', error);
      // Remover toast de erro - reconectar silenciosamente
    };

    ws.onclose = () => {
      reconnectAttempts.current += 1;
      console.log(`⚠️ WebSocket desconectado, reconectando em background... (tentativa ${reconnectAttempts.current})`);
      setOnlineStatus('🔴 Desconectado');
      // Remover toast warning - reconectar silenciosamente
      
      // Reconectar automaticamente (500ms de delay)
      setTimeout(() => {
        if (auth.token) {
          console.log('🔄 Tentando reconectar...');
          connectWebSocket();
        }
      }, 500);
    };
  };

  useEffect(() => {
    // Bloquear botão voltar com popup de confirmação
    const handleBackButton = (e) => {
      e.preventDefault();
      setShowExitConfirm(true);
      window.history.pushState(null, '', window.location.href);
    };
    
    // Adicionar estado inicial ao histórico
    window.history.pushState(null, '', window.location.href);
    
    // Listener para interceptar botão voltar
    window.addEventListener('popstate', handleBackButton);
    
    // Adicionar classe fullscreen apenas no ClientChat
    document.body.classList.add('client-chat-fullscreen');
    
    console.log('🔒 Botão voltar com confirmação ativado');
    
    return () => {
      window.removeEventListener('popstate', handleBackButton);
      document.body.classList.remove('client-chat-fullscreen');
      // 🆕 Limpar timer de credenciais ao desmontar
      if (credentialsTimeoutRef.current) {
        clearTimeout(credentialsTimeoutRef.current);
      }
    };
  }, []);

  // Ativar push notifications automaticamente após login
  useEffect(() => {
    if (userData && pushNotifications.isSupported && !pushNotifications.isSubscribed) {
      // Aguardar 3 segundos antes de solicitar permissão
      const timer = setTimeout(async () => {
        console.log('📲 Ativando push notifications...');
        const success = await pushNotifications.subscribe();
        if (success) {
          toast.success('🔔 Notificações ativadas! Você receberá alertas de novas mensagens.');
        }
      }, 3000);
      
      return () => clearTimeout(timer);
    }
  }, [userData, pushNotifications.isSupported]);

  // Limpar badge de notificações ao abrir o app
  useEffect(() => {
    if ('clearAppBadge' in navigator) {
      navigator.clearAppBadge()
        .then(() => console.log('🧹 Badge limpo ao abrir app'))
        .catch(err => console.log('Badge API não disponível:', err));
    }
    
    // Limpar badge quando usuário volta para o app
    const handleVisibilityChange = () => {
      if (!document.hidden && 'clearAppBadge' in navigator) {
        navigator.clearAppBadge()
          .then(() => console.log('🧹 Badge limpo ao focar no app'))
          .catch(() => {});
      }
    };
    
    document.addEventListener('visibilitychange', handleVisibilityChange);
    
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, []);

  useEffect(() => {
    // Pre-carregar o áudio de notificação COM FALLBACK MÚLTIPLO
    try {
      const audio = new Audio('/notification.mp3');
      audio.preload = 'auto';
      audio.volume = 1.0;
      audio.load(); // Forçar carregamento
      notificationAudioRef.current = audio;
      console.log('✅ Áudio de notificação pré-carregado (Assobio WhatsApp)');
      
      // Testar se carregou corretamente
      audio.addEventListener('canplaythrough', () => {
        console.log('✅ Áudio PRONTO para tocar!');
      });
      
      audio.addEventListener('error', (e) => {
        console.error('❌ Erro ao carregar áudio:', e);
      });
    } catch (e) {
      console.error('❌ Erro ao pré-carregar áudio:', e);
    }
    
    // Habilitar áudio ao primeiro toque/clique (necessário para navegadores móveis e PWA)
    const enableAudio = () => {
      if (notificationAudioRef.current && !audioEnabled) {
        try {
          console.log('🔊 Tentando habilitar áudio após interação...');
          notificationAudioRef.current.play().then(() => {
            notificationAudioRef.current.pause();
            notificationAudioRef.current.currentTime = 0;
            setAudioEnabled(true);
            console.log('✅ Áudio HABILITADO após interação do usuário');
            toast.success('🔊 Som de notificações habilitado!', { duration: 2000 });
          }).catch((e) => {
            console.error('⚠️ Falha ao habilitar áudio:', e);
          });
        } catch (e) {
          console.error('❌ Erro ao habilitar áudio:', e);
        }
      }
    };
    
    // Adicionar listeners para habilitar áudio (múltiplos eventos)
    document.addEventListener('click', enableAudio, { once: true });
    document.addEventListener('touchstart', enableAudio, { once: true });
    document.addEventListener('touchend', enableAudio, { once: true });
    document.addEventListener('keydown', enableAudio, { once: true });
    
    loadMessages();
    loadNotices();
    loadUserData();
    loadPixKey();
    loadConfig();
    checkOnlineStatus();
    
    // Solicitar permissão para notificações
    if ('Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission().then(permission => {
        console.log('🔔 Permissão de notificação:', permission);
      });
    }
    
    // Conectar WebSocket IMEDIATAMENTE
    connectWebSocket();
    
    // Check notices every 30 seconds
    const noticesInterval = setInterval(() => {
      checkForNewNotices();
    }, 30000);
    
    // Check online status every minute
    const statusInterval = setInterval(() => {
      checkOnlineStatus();
    }, 60000);
    
    return () => {
      clearInterval(noticesInterval);
      clearInterval(statusInterval);
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (queueTimerRef.current) {
        clearTimeout(queueTimerRef.current);
      }
      if (notificationAudioRef.current) {
        notificationAudioRef.current.pause();
        notificationAudioRef.current = null;
      }
    };
  }, []);

  // Reconectar WebSocket quando userData estiver disponível
  useEffect(() => {
    if (userData?.id && (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN)) {
      console.log('🔄 Conectando WebSocket com userId:', userData.id);
      connectWebSocket();
    }
  }, [userData]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const loadMessages = async () => {
    try {
      const ticketsRes = await api.get('/tickets', { params: { status: null } });
      const myTicket = ticketsRes.data.find(t => t.client_id === userData.id);
      if (myTicket) {
        const { data } = await api.get(`/messages/${myTicket.id}`);
        setMessages(data);
      }
    } catch (error) {
      console.error('Error loading messages:', error);
    }
  };

  const loadNotices = async () => {
    try {
      const { data } = await api.get('/notices');
      setNotices(data);
      
      // Check if there are new notices
      const stored = parseInt(localStorage.getItem('last_notice_count') || '0');
      if (data.length > stored && data.length > 0) {
        setHasNewNotices(true);
        // Mostrar popup automático "NOVO AVISO"
        setShowNoticePopup(true);
      }
      setLastNoticeCount(data.length);
    } catch (error) {
      console.error('Error loading notices:', error);
    }
  };
  
  const checkForNewNotices = async () => {
    try {
      const { data } = await api.get('/notices');
      const stored = parseInt(localStorage.getItem('last_notice_count') || '0');
      if (data.length > stored) {
        setHasNewNotices(true);
      }
    } catch (error) {
      console.error('Error checking notices:', error);
    }
  };
  
  const checkOnlineStatus = async () => {
    try {
      const { data } = await api.get('/agents/online-status');
      
      // Se fora do horário de trabalho (antes das 9h ou depois das 23h)
      if (!isWithinBusinessHours()) {
        setOnlineStatus('Fora de horário');
        return;
      }
      
      // Se admin ativou modo ausente manualmente
      if (data.manual && data.status === 'away') {
        setOnlineStatus('Ausente');
        return;
      }
      
      // Dentro do horário de trabalho (9h-23h)
      if (data.online > 0) {
        setOnlineStatus('Online');
      } else {
        // Não mostrar "Ausente" automaticamente
        // Mostrar apenas horário de funcionamento
        setOnlineStatus('Online - Horário: 9h às 23h');
      }
    } catch (error) {
      // Fallback: verificar horário
      if (!isWithinBusinessHours()) {
        setOnlineStatus('Fora de horário');
      } else {
        setOnlineStatus('Online - Horário: 9h às 23h');
      }
    }
  };

  const loadPixKey = async () => {
    try {
      const { data } = await api.get('/config');
      setPixKey(data.pix_key || '');
    } catch (error) {
      console.error('Error loading PIX key:', error);
    }
  };

  const checkNamePopup = async () => {
    try {
      const { data } = await api.get('/users/name-popup-status');
      if (data.should_show && firstMessageSent) {
        // Mostrar popup de nome após enviar primeira mensagem
        setTimeout(() => {
          setShowNamePopup(true);
        }, 2000);
      }
    } catch (error) {
      console.error('Error checking name popup:', error);
    }
  };

  const handleConfirmName = async () => {
    const name = nameInput.trim();
    if (!name) {
      toast.error('Por favor, digite seu nome');
      return;
    }
    
    // Validação no frontend também
    if (name.length < 2) {
      toast.error('Nome muito curto');
      return;
    }
    
    if (name.split(' ').length > 3) {
      toast.error('Digite apenas seu nome (máximo 3 palavras)');
      return;
    }
    
    if (!/^[A-Za-zÀ-ÿ\s]+$/.test(name)) {
      toast.error('Nome deve conter apenas letras');
      return;
    }
    
    try {
      await api.put('/users/me/name', { name });
      toast.success(`Bem-vindo(a), ${name}!`);
      setShowNamePopup(false);
      setNameInput('');
      loadTicket(); // Recarregar para atualizar nome
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao salvar nome');
    }
  };

  const loadUserData = async () => {
    try {
      const { data } = await api.get('/users/me');
      setUserData(data);  // Update userData with fresh data from server
      setCredentials({ pinned_user: data.pinned_user, pinned_pass: data.pinned_pass });
      
      // 🆕 Se cliente tem credenciais, mostrar popup automaticamente
      if (data.pinned_user && data.pinned_pass) {
        setShowCredentialsPopup(true);
        
        // Fechar automaticamente após 30 segundos
        if (credentialsTimeoutRef.current) {
          clearTimeout(credentialsTimeoutRef.current);
        }
        credentialsTimeoutRef.current = setTimeout(() => {
          setShowCredentialsPopup(false);
        }, 30000); // 30 segundos
      }
    } catch (error) {
      console.error('Error loading user data:', error);
    }
  };

  const loadConfig = async () => {
    try {
      const { data } = await api.get('/config');
      setConfig(data);
    } catch (error) {
      console.error('Error loading config:', error);
    }
  };

  const handleAvatarUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    if (!file.type.startsWith('image/')) {
      toast.error('Por favor, selecione uma imagem');
      return;
    }

    setUploadingAvatar(true);
    try {
      const formData = new FormData();
      formData.append('file', file);

      const { data } = await api.post('/users/me/avatar', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      // Atualizar userData com nova foto
      setUserData(prev => ({ ...prev, custom_avatar: data.avatar_url }));
      toast.success('Foto atualizada com sucesso!');
    } catch (error) {
      toast.error('Erro ao fazer upload da foto');
      console.error('Upload error:', error);
    } finally {
      setUploadingAvatar(false);
    }
  };

  // Handler para atualizar app e conversa
  const handleRefreshApp = async () => {
    setIsRefreshing(true);
    
    try {
      // 1. Recarregar mensagens
      console.log('🔄 Atualizando mensagens...');
      await loadMessages();
      
      // 2. Verificar e atualizar Service Worker
      if ('serviceWorker' in navigator) {
        const registration = await navigator.serviceWorker.getRegistration();
        if (registration) {
          console.log('🔄 Verificando atualizações do app...');
          await registration.update();
          
          // Se houver uma nova versão esperando, ativar
          if (registration.waiting) {
            console.log('✅ Nova versão encontrada! Atualizando...');
            registration.waiting.postMessage({ type: 'SKIP_WAITING' });
            
            // Aguardar um pouco e recarregar a página
            setTimeout(() => {
              window.location.reload();
            }, 1000);
            
            toast.success('🚀 Nova versão instalada! Atualizando...');
            return;
          }
        }
      }
      
      toast.success('✅ Conversa atualizada!');
    } catch (error) {
      console.error('❌ Erro ao atualizar:', error);
      toast.error('Erro ao atualizar');
    } finally {
      setTimeout(() => setIsRefreshing(false), 500);
    }
  };

  const handleSendMessage = async () => {
    if (!messageText.trim() || isSendingMessage) return;
    
    // Marcar como enviando
    setIsSendingMessage(true);
    const textToSend = messageText.trim();
    
    // Habilitar áudio na primeira interação do usuário (contornar autoplay policy)
    if (!audioEnabled && notificationAudioRef.current) {
      try {
        // Tentar tocar e pausar imediatamente para "desbloquear" o áudio
        notificationAudioRef.current.volume = 0.01;
        notificationAudioRef.current.play().then(() => {
          notificationAudioRef.current.pause();
          notificationAudioRef.current.currentTime = 0;
          notificationAudioRef.current.volume = 1.0;
          setAudioEnabled(true);
          console.log('✅ Áudio habilitado após interação do usuário');
        }).catch(e => {
          console.log('⚠️ Não foi possível habilitar áudio:', e);
        });
      } catch (e) {
        console.error('Erro ao habilitar áudio:', e);
      }
    }
    
    if (!userData?.id) {
      toast.error('Erro: Dados do usuário não carregados');
      setIsSendingMessage(false);
      return;
    }
    
    // Check business hours
    if (!isWithinBusinessHours()) {
      setAlertModal({
        isOpen: true,
        title: 'Fora do Horário',
        message: 'Estamos fora do horário de atendimento (9h às 23h). Sua mensagem será respondida assim que possível.',
        icon: 'clock'
      });
    }
    
    // Não mostrar popup de "Ausente" dentro do horário
    // Cliente pode enviar mensagem normalmente
    
    try {
      // Get first available agent
      const agents = await api.get('/agents');
      if (!agents.data || agents.data.length === 0) {
        toast.error('Nenhum atendente disponível no momento');
        setIsSendingMessage(false);
        return;
      }
      const agentId = agents.data[0].id;
      
      // Criar mensagem local para exibir IMEDIATAMENTE
      const tempMessage = {
        id: `temp-${Date.now()}`,
        from_type: 'client',
        from_id: userData.id,
        to_type: 'agent',
        to_id: agentId,
        kind: 'text',
        text: textToSend,
        file_url: '',
        created_at: new Date().toISOString(),
        is_read: false
      };
      
      // Adicionar mensagem LOCALMENTE IMEDIATAMENTE
      setMessages(prev => [...prev, tempMessage]);
      
      // Limpar campo IMEDIATAMENTE
      setMessageText('');
      
      // Scroll para última mensagem
      setTimeout(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
      }, 100);
      
      console.log('Sending message:', { from_id: userData.id, to_id: agentId });
      
      // Send message (backend will create ticket automatically if needed)
      const response = await api.post('/messages', {
        ticket_id: '',  // Backend creates ticket for new clients
        from_type: 'client',
        from_id: userData.id,
        to_type: 'agent',
        to_id: agentId,
        kind: 'text',
        text: textToSend,
        file_url: ''
      });
      
      // Substituir mensagem temporária pela real (se retornar)
      if (response.data && response.data.id) {
        setMessages(prev => prev.map(msg => 
          msg.id === tempMessage.id ? { ...response.data } : msg
        ));
      }
      
      console.log('✅ Mensagem enviada e exibida INSTANTANEAMENTE!');
      
      // Marcar que enviou primeira mensagem e verificar se deve pedir nome
      if (!firstMessageSent) {
        setFirstMessageSent(true);
        setTimeout(() => {
          checkNamePopup();
        }, 2000);
      }
      
      // Show queue popup after 10 seconds (once per day)
      if (shouldShowQueuePopup()) {
        queueTimerRef.current = setTimeout(async () => {
          try {
            const { data } = await api.get('/tickets/counts');
            const queueCount = data.EM_ESPERA || 0;
            setAlertModal({
              isOpen: true,
              title: 'Fila de Espera',
              message: `Você está na fila de espera. ${queueCount} pessoa(s) aguardando atendimento. Em breve você será atendido!`,
              icon: 'queue'
            });
            markQueuePopupShown();
          } catch (error) {
            console.error('Error getting queue count:', error);
          }
        }, 10000);
      }
    } catch (error) {
      // Remover mensagem temporária em caso de erro
      setMessages(prev => prev.filter(msg => msg.id?.startsWith('temp-')));
      console.error('Send error:', error);
      toast.error(error.response?.data?.detail || 'Erro ao enviar mensagem');
      // Restaurar mensagem se erro
      setMessageText(textToSend);
    } finally {
      setIsSendingMessage(false);
    }
  };

  const handleFileUpload = async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    
    const agents = await api.get('/agents');
    if (!agents.data || agents.data.length === 0) {
      toast.error('Nenhum atendente disponível');
      return;
    }
    const agentId = agents.data[0].id;
    
    // Criar mensagem local temporária com loading
    const tempMessage = {
      id: `temp-file-${Date.now()}`,
      from_type: 'client',
      from_id: userData.id,
      to_type: 'agent',
      to_id: agentId,
      kind: 'image', // Será atualizado depois
      text: '',
      file_url: 'uploading', // Flag para mostrar loading
      created_at: new Date().toISOString(),
      is_read: false
    };
    
    // Adicionar mensagem temporária com loading
    setMessages(prev => [...prev, tempMessage]);
    
    // Scroll para última mensagem
    setTimeout(() => {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, 100);
    
    try {
      const { data } = await api.post('/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      const response = await api.post('/messages', {
        ticket_id: '',  // Backend creates ticket automatically
        from_type: 'client',
        from_id: userData.id,
        to_type: 'agent',
        to_id: agentId,
        kind: data.kind,
        text: '',
        file_url: data.url
      });
      
      // Substituir mensagem temporária pela real
      setMessages(prev => prev.map(msg => 
        msg.id === tempMessage.id 
          ? { ...response.data, file_url: data.url, kind: data.kind } 
          : msg
      ));
      
      toast.success('Arquivo enviado!');
      console.log('✅ Arquivo enviado e exibido INSTANTANEAMENTE!');
    } catch (error) {
      // Remover mensagem temporária em caso de erro
      setMessages(prev => prev.filter(msg => msg.id !== tempMessage.id));
      console.error('Upload error:', error);
      toast.error(error.response?.data?.detail || 'Erro ao enviar arquivo');
    }
  };

  const handleStartRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      const chunks = [];
      
      mediaRecorder.ondataavailable = (e) => chunks.push(e.data);
      mediaRecorder.onstop = async () => {
        const blob = new Blob(chunks, { type: 'audio/webm' });
        const file = new File([blob], 'audio.webm', { type: 'audio/webm' });
        await handleFileUpload(file);
        stream.getTracks().forEach(track => track.stop());
      };
      
      mediaRecorder.start();
      mediaRecorderRef.current = mediaRecorder;
      setIsRecording(true);
      
      setTimeout(() => {
        if (mediaRecorder.state !== 'inactive') {
          mediaRecorder.stop();
          setIsRecording(false);
        }
      }, 60000);
    } catch (error) {
      toast.error('Erro ao acessar microfone');
    }
  };

  const handleStopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const handleUpdatePin = async () => {
    try {
      await api.put('/users/me/pin', { pin: newPin });
      toast.success('PIN atualizado!');
      setNewPin('');
      setShowSettings(false);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao atualizar PIN');
    }
  };

  const handleUpdateName = async (name) => {
    if (!name || name.trim() === '') {
      toast.error('Por favor, digite um nome');
      return;
    }
    
    try {
      await api.put('/users/me/name', { name: name.trim() });
      toast.success('Nome atualizado com sucesso!');
      // Atualizar userData local
      setUserData(prev => ({ ...prev, display_name: name.trim() }));
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao atualizar nome');
    }
  };

  // Função para ativar notificações push
  const handleEnablePushNotifications = async () => {
    if (!pushNotifications.isSupported) {
      toast.error('Notificações push não são suportadas neste navegador');
      return;
    }

    if (pushNotifications.permission === 'denied') {
      toast.error('Permissão de notificações foi negada. Ative nas configurações do navegador.');
      return;
    }

    toast.loading('Ativando notificações...', { id: 'push-setup' });

    try {
      const success = await pushNotifications.subscribe();
      
      if (success) {
        toast.success('✅ Notificações ativadas! Você receberá notificações mesmo com o app fechado.', { 
          id: 'push-setup',
          duration: 5000 
        });
        
        // Mostrar badge de confirmação
        if ('setAppBadge' in navigator) {
          navigator.setAppBadge(1).catch(() => {});
          setTimeout(() => {
            navigator.clearAppBadge().catch(() => {});
          }, 3000);
        }
      } else {
        toast.error('Não foi possível ativar as notificações. Tente novamente.', { id: 'push-setup' });
      }
    } catch (error) {
      console.error('Erro ao ativar notificações:', error);
      toast.error('Erro ao ativar notificações', { id: 'push-setup' });
    }
  };

  return (
    <div className="fixed inset-0 bg-[#e5ddd5] flex flex-col overflow-hidden">
      {/* Header - FIXO NO TOPO - Estilo WhatsApp */}
      <div className="bg-[#075E54] text-white p-3 flex-shrink-0 z-20">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3 flex-1">
            <div className="relative">
              <div className="w-10 h-10 bg-white/20 rounded-full flex items-center justify-center overflow-hidden">
                {config.support_avatar ? (
                  <img src={config.support_avatar} alt="Suporte" className="w-full h-full object-cover" />
                ) : (
                  <MessageCircle className="w-5 h-5" />
                )}
              </div>
              {onlineStatus && (
                <span className="absolute bottom-0 right-0 w-3 h-3 bg-green-400 rounded-full border-2 border-[#075E54]"></span>
              )}
            </div>
            <div className="flex-1">
              <h1 className="font-semibold text-base">Suporte</h1>
              <p className="text-xs text-white/80">
                {onlineStatus ? 'online' : 'offline'}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-1">
            <Button
              data-testid="notices-btn"
              variant="ghost"
              size="icon"
              onClick={() => {
                setShowNotices(true);
                setHasNewNotices(false);
                localStorage.setItem('last_notice_count', lastNoticeCount.toString());
              }}
              className={`text-white hover:bg-white/10 h-9 w-9 relative ${hasNewNotices ? 'pulse' : ''}`}
            >
              <Bell className={`w-5 h-5 ${hasNewNotices ? 'text-red-300' : ''}`} />
              {hasNewNotices && (
                <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full animate-pulse"></span>
              )}
            </Button>
            
            {/* Botão de Atualizar */}
            <Button
              data-testid="settings-btn"
              variant="ghost"
              size="icon"
              onClick={() => setShowSettings(true)}
              className="text-white hover:bg-white/10 h-9 w-9"
            >
              <Settings className="w-5 h-5" />
            </Button>
            <Button
              data-testid="client-logout-btn"
              variant="ghost"
              size="icon"
              onClick={() => { 
                // Limpar credenciais salvas
                localStorage.removeItem('client_credentials');
                clearAuth(); 
                navigate('/'); 
              }}
              className="text-white hover:bg-white/10 h-9 w-9"
            >
              <LogOut className="w-5 h-5" />
            </Button>
          </div>
        </div>
      </div>

      {/* Credentials Bar */}
      {(credentials.pinned_user || credentials.pinned_pass) && (
        <div className="bg-cyan-100 border-b border-cyan-200 px-4 py-2 text-sm flex-shrink-0 z-10">
          <span className="font-medium">Usuário:</span> {credentials.pinned_user} • 
          <span className="font-medium">Senha:</span> {credentials.pinned_pass}
        </div>
      )}

      {/* Messages - ÁREA COM SCROLL - Fundo estilo WhatsApp */}
      <div 
        className="flex-1 overflow-y-auto p-4" 
        style={{
          backgroundImage: 'url("data:image/svg+xml,%3Csvg width=\'100\' height=\'100\' xmlns=\'http://www.w3.org/2000/svg\'%3E%3Cpath d=\'M10 10 L90 10 L90 90 L10 90 Z\' fill=\'none\' stroke=\'%23d9d9d9\' stroke-width=\'0.5\' opacity=\'0.1\'/%3E%3C/svg%3E")',
          backgroundColor: '#e5ddd5'
        }}
      >
          <div className="space-y-3">
            {messages.map((msg, index) => {
              // Debug: log mensagem
              console.log('📝 Renderizando mensagem:', {
                id: msg.id?.substring(0, 8),
                from_type: msg.from_type,
                kind: msg.kind,
                text: msg.text?.substring(0, 50),
                has_text: !!msg.text
              });
              
              // Verificar se deve mostrar data (primeira mensagem do dia)
              const showDate = index === 0 || 
                new Date(messages[index - 1].created_at).toDateString() !== new Date(msg.created_at).toDateString();
              
              return (
              <div key={msg.id}>
                {/* Separador de data - Estilo WhatsApp */}
                {showDate && (
                  <div className="flex justify-center my-2">
                    <span className="bg-[#E1F5FE] text-gray-700 text-xs px-3 py-1 rounded-md shadow-sm">
                      {new Date(msg.created_at).toLocaleDateString('pt-BR', { 
                        day: '2-digit', 
                        month: 'long', 
                        year: 'numeric' 
                      })}
                    </span>
                  </div>
                )}
                
                <div className={`flex gap-2 items-end ${msg.from_type === 'client' ? 'justify-end' : 'justify-start'}`}>
                  {/* Foto de perfil do suporte/agente (esquerda) */}
                  {(msg.from_type === 'agent' || msg.from_type === 'ai' || msg.from_type === 'system') && (
                    <div className="w-8 h-8 rounded-full bg-white/20 flex items-center justify-center overflow-hidden flex-shrink-0">
                      {config.support_avatar ? (
                        <img src={config.support_avatar} alt="Suporte" className="w-full h-full object-cover" />
                      ) : (
                        <MessageCircle className="w-4 h-4 text-gray-400" />
                      )}
                    </div>
                  )}
                  
                  <div
                    className={`max-w-[75%] px-3 py-2 rounded-lg shadow-sm ${
                      msg.from_type === 'client'
                        ? 'bg-[#DCF8C6] text-gray-900 rounded-br-none'
                        : msg.from_type === 'ai'
                        ? 'bg-[#E1F5FE] text-gray-900 rounded-bl-none border border-blue-200'
                        : 'bg-white text-gray-900 rounded-bl-none border border-gray-200'
                    }`}
                  >
                  {/* Mostrar texto se existir */}
                  {msg.text && (
                    <p 
                      className="whitespace-pre-wrap break-words text-sm" 
                      style={{ minHeight: '20px' }}
                      dangerouslySetInnerHTML={{
                        __html: msg.text.replace(
                          /(https?:\/\/[^\s]+)/g,
                          '<a href="$1" target="_blank" rel="noopener noreferrer" class="underline text-blue-300 hover:text-blue-100">$1</a>'
                        )
                      }}
                    />
                  )}
                  
                  {/* Renderizar mídia (imagem, vídeo, áudio) - TAMANHO CONTIDO */}
                  {msg.kind === 'image' && (
                    msg.media_expired ? (
                      <div className="flex items-center gap-2 p-3 bg-gray-100 rounded-lg text-gray-500 text-sm max-w-[250px]">
                        <span>📷</span>
                        <span>Imagem expirada (7 dias)</span>
                      </div>
                    ) : msg.file_url ? (
                      <img 
                        src={msg.file_url} 
                        alt="Imagem" 
                        className="max-w-[250px] max-h-[250px] w-auto h-auto object-contain rounded-lg mt-2 cursor-pointer hover:opacity-80 transition-opacity block" 
                        onClick={() => setLightboxImage(msg.file_url)}
                        onError={(e) => {
                          console.error('Erro ao carregar imagem:', msg.file_url);
                          e.target.src = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100"><text x="50%" y="50%" text-anchor="middle" dy=".3em">❌ Erro</text></svg>';
                        }}
                      />
                    ) : null
                  )}
                  {msg.kind === 'video' && (
                    msg.media_expired ? (
                      <div className="flex items-center gap-2 p-3 bg-gray-100 rounded-lg text-gray-500 text-sm max-w-[250px]">
                        <span>🎥</span>
                        <span>Vídeo expirado (7 dias)</span>
                      </div>
                    ) : msg.file_url ? (
                      <video 
                        src={msg.file_url} 
                        controls 
                        preload="metadata"
                        className="max-w-[250px] max-h-[250px] w-auto h-auto rounded-lg mt-2 block bg-black"
                        onError={(e) => {
                          console.error('❌ Erro ao carregar vídeo:', msg.file_url);
                          console.error('Detalhes:', e);
                          // Mostrar mensagem de erro ao usuário
                          e.target.style.display = 'none';
                          const errorDiv = document.createElement('div');
                          errorDiv.className = 'flex flex-col items-center gap-2 p-3 bg-red-50 rounded-lg text-red-600 text-sm max-w-[250px]';
                          errorDiv.innerHTML = `
                            <span>❌</span>
                            <span>Erro ao reproduzir vídeo</span>
                            <a href="${msg.file_url}" target="_blank" class="text-blue-500 underline text-xs">Tentar abrir em nova aba</a>
                          `;
                          e.target.parentNode.appendChild(errorDiv);
                        }}
                      >
                        Seu navegador não suporta reprodução de vídeo.
                      </video>
                    ) : (
                      <div className="flex items-center gap-2 p-3 bg-gray-100 rounded-lg text-gray-500 text-sm max-w-[250px]">
                        <span>🎥</span>
                        <span>Vídeo não disponível</span>
                      </div>
                    )
                  )}
                  {msg.kind === 'audio' && (
                    msg.media_expired ? (
                      <div className="flex items-center gap-2 p-3 bg-gray-100 rounded-lg text-gray-500 text-sm max-w-[250px]">
                        <span>🎵</span>
                        <span>Áudio expirado (7 dias)</span>
                      </div>
                    ) : msg.file_url ? (
                      <div className="mt-2">
                        <WhatsAppAudioPlayer 
                          src={msg.file_url} 
                          isSentByMe={msg.sender_type === 'client'} 
                        />
                      </div>
                    ) : null
                  )}
                  {msg.kind === 'department_selection' && (
                    <div>
                      <p className="font-semibold text-sm mb-3">{msg.text}</p>
                      <div className="space-y-2">
                        {msg.buttons && msg.buttons.map((btn, idx) => (
                          <Button
                            key={btn.id}
                            onClick={async () => {
                              try {
                                await api.post(`/tickets/${msg.ticket_id}/select-department`, {
                                  department_id: btn.id
                                });
                                toast.success(`Departamento selecionado: ${btn.label}`);
                              } catch (error) {
                                toast.error('Erro ao selecionar departamento');
                              }
                            }}
                            className="w-full bg-indigo-600 hover:bg-indigo-700 text-white justify-start"
                          >
                            <span className="font-bold mr-2">{idx + 1}:</span>
                            <div className="text-left">
                              <div className="font-semibold">{btn.label}</div>
                              {btn.description && (
                                <div className="text-xs opacity-80">{btn.description}</div>
                              )}
                            </div>
                          </Button>
                        ))}
                      </div>
                    </div>
                  )}
                  {msg.kind === 'pix' && (
                    <div className="space-y-2">
                      <Button
                        size="sm"
                        onClick={() => {
                          const pixKey = msg.pix_key || msg.text;
                          navigator.clipboard.writeText(pixKey);
                          toast.success('Chave PIX copiada!');
                        }}
                        className="w-full bg-green-600 hover:bg-green-700 text-white"
                      >
                        💰 Copiar Chave PIX
                      </Button>
                    </div>
                  )}
                    {/* Nome e horário */}
                    <div className="flex items-center justify-between mt-1 gap-2">
                      {msg.from_type === 'client' && userData?.display_name && (
                        <span className="text-[10px] font-semibold opacity-80">
                          {userData.display_name}
                        </span>
                      )}
                      <p className="text-[10px] opacity-70 ml-auto">
                        {new Date(msg.created_at).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}
                      </p>
                    </div>
                  </div>
                  
                  {/* Foto de perfil do cliente (direita) */}
                  {msg.from_type === 'client' && userData.custom_avatar && (
                    <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center overflow-hidden flex-shrink-0">
                      <img 
                        src={userData.custom_avatar} 
                        alt="Você" 
                        className="w-full h-full object-cover"
                        onError={(e) => {
                          e.target.style.display = 'none';
                        }}
                      />
                    </div>
                  )}
                </div>
              </div>
              );
            })}
            <div ref={messagesEndRef} />
          </div>
        </div>

      {/* Input - FIXO NA PARTE INFERIOR - Estilo WhatsApp */}
      <div className="bg-[#F0F0F0] p-2 flex-shrink-0 z-10">
        <div className="flex items-center gap-2">
          <input
            ref={fileInputRef}
            type="file"
            className="hidden"
            accept="image/*,video/*"
            onChange={(e) => e.target.files[0] && handleFileUpload(e.target.files[0])}
          />
          <Button
            data-testid="attach-btn"
            variant="ghost"
            size="icon"
            onClick={() => fileInputRef.current?.click()}
            className="text-gray-600 hover:bg-gray-200 h-10 w-10"
          >
            <Paperclip className="w-5 h-5" />
          </Button>
          <div className="flex-1 bg-white rounded-full px-4 py-2 flex items-center gap-2">
            <Input
              ref={messageInputRef}
              data-testid="client-message-input"
              placeholder="Mensagem"
              value={messageText}
              onChange={(e) => setMessageText(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  handleSendMessage();
                }
              }}
              className="flex-1 border-none focus:ring-0 px-0 bg-transparent"
            />
            <Button
              data-testid="record-btn"
              variant="ghost"
              size="icon"
              onClick={isRecording ? handleStopRecording : handleStartRecording}
              className={`h-8 w-8 ${isRecording ? 'bg-red-100 text-red-600' : 'text-gray-600 hover:bg-gray-100'}`}
            >
              <Mic className="w-5 h-5" />
            </Button>
          </div>
          <Button 
            data-testid="send-message-btn" 
            onClick={handleSendMessage} 
            disabled={isSendingMessage || !messageText.trim()}
            className="bg-[#075E54] hover:bg-[#064d44] h-10 w-10 rounded-full p-0 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isSendingMessage ? (
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
            ) : (
              <Send className="w-5 h-5" />
            )}
          </Button>
        </div>
      </div>

      {/* Popup Automático de Novo Aviso */}
      <Dialog open={showNoticePopup} onOpenChange={setShowNoticePopup}>
        <DialogContent className="max-w-sm">
          <DialogHeader>
            <DialogTitle className="text-center text-2xl">📢 NOVO AVISO</DialogTitle>
          </DialogHeader>
          <div className="flex flex-col items-center gap-4 py-4">
            <p className="text-center text-lg">Você tem {notices.length} aviso(s) importante(s) para visualizar!</p>
            <Button
              onClick={() => {
                setShowNoticePopup(false);
                setShowNotices(true);
                setHasNewNotices(false);
                localStorage.setItem('last_notice_count', notices.length.toString());
              }}
              className="w-full bg-purple-600 hover:bg-purple-700 text-lg py-6"
            >
              Abrir
            </Button>
            <Button
              variant="ghost"
              onClick={() => {
                setShowNoticePopup(false);
                localStorage.setItem('last_notice_count', notices.length.toString());
              }}
              className="text-sm"
            >
              Fechar
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Notices Dialog */}
      <Dialog open={showNotices} onOpenChange={setShowNotices}>
        <DialogContent data-testid="notices-dialog" className="max-w-md">
          <DialogHeader>
            <DialogTitle>📢 Avisos Importantes</DialogTitle>
          </DialogHeader>
          <ScrollArea className="max-h-[400px]">
            <div className="space-y-4">
              {notices.length === 0 ? (
                <p className="text-center text-slate-500 py-8">Nenhum aviso no momento</p>
              ) : (
                notices.map(notice => (
                  <Card key={notice.id} className="p-4">
                    <h3 className="font-semibold text-lg mb-2">{notice.title || 'Aviso'}</h3>
                    <p className="whitespace-pre-wrap">{notice.message}</p>
                    <p className="text-xs text-slate-500 mt-3">
                      {new Date(notice.created_at).toLocaleString('pt-BR')}
                    </p>
                  </Card>
                ))
              )}
            </div>
          </ScrollArea>
        </DialogContent>
      </Dialog>

      {/* Settings Dialog */}
      <Dialog open={showSettings} onOpenChange={setShowSettings}>
        <DialogContent data-testid="settings-dialog" className="max-w-md">
          <DialogHeader>
            <DialogTitle>Configurações</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            {/* Nome do Cliente */}
            <div>
              <label className="text-sm font-medium text-slate-700 block mb-2">Seu Nome</label>
              <div className="flex gap-2">
                <Input
                  data-testid="client-name-input"
                  placeholder="Digite seu nome"
                  value={userData.display_name || ''}
                  onChange={(e) => setUserData({ ...userData, display_name: e.target.value })}
                  className="flex-1"
                />
                <Button 
                  data-testid="update-name-btn" 
                  onClick={() => handleUpdateName(userData.display_name)}
                  disabled={!userData.display_name || userData.display_name.trim() === ''}
                >
                  Salvar
                </Button>
              </div>
              <p className="text-xs text-slate-500 mt-1">Seu nome aparecerá nas conversas com o suporte</p>
            </div>

            <div>
              <label className="text-sm font-medium text-slate-700 block mb-2">Foto de Perfil</label>
              <div className="flex items-center gap-4">
                <div className="w-16 h-16 bg-gray-200 rounded-full flex items-center justify-center overflow-hidden">
                  {userData.custom_avatar ? (
                    <img 
                      src={userData.custom_avatar} 
                      alt="Perfil" 
                      className="w-full h-full object-cover"
                      onError={(e) => {
                        console.error('❌ Erro ao carregar avatar:', userData.custom_avatar);
                        e.target.style.display = 'none';
                        e.target.parentElement.innerHTML = '<svg class="w-8 h-8 text-gray-400" fill="currentColor" viewBox="0 0 24 24"><path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/></svg>';
                      }}
                    />
                  ) : (
                    <User className="w-8 h-8 text-gray-400" />
                  )}
                </div>
                <div className="flex-1">
                  <input
                    ref={avatarInputRef}
                    type="file"
                    accept="image/*"
                    onChange={handleAvatarUpload}
                    className="hidden"
                  />
                  <Button
                    onClick={() => avatarInputRef.current?.click()}
                    disabled={uploadingAvatar}
                    variant="outline"
                    size="sm"
                  >
                    {uploadingAvatar ? 'Enviando...' : 'Alterar Foto'}
                  </Button>
                  <p className="text-xs text-slate-500 mt-1">Clique para enviar uma foto</p>
                </div>
              </div>
            </div>
            
            <div>
              <label className="text-sm font-medium text-slate-700 block mb-2">Alterar PIN (2 dígitos)</label>
              <div className="flex gap-2">
                <Input
                  data-testid="new-pin-input"
                  type="password"
                  placeholder="Novo PIN"
                  value={newPin}
                  onChange={(e) => setNewPin(e.target.value.replace(/\D/g, '').slice(0, 2))}
                  maxLength={2}
                />
                <Button data-testid="update-pin-btn" onClick={handleUpdatePin}>
                  Atualizar
                </Button>
              </div>
            </div>
            <div className="pt-4 border-t">
              <p className="text-sm text-slate-600">
                <span className="font-medium">WhatsApp:</span> {userData.whatsapp}
              </p>
              {userData.display_name && (
                <p className="text-sm text-slate-600 mt-1">
                  <span className="font-medium">Nome:</span> {userData.display_name}
                </p>
              )}
            </div>
          </div>
        </DialogContent>
      </Dialog>
      
      {/* Alert Modal */}
      <AlertModal
        isOpen={alertModal.isOpen}
        onClose={() => setAlertModal({ ...alertModal, isOpen: false })}
        title={alertModal.title}
        message={alertModal.message}
        icon={alertModal.icon}
        autoCloseDelay={30000}
      />
      
      {/* Name Confirmation Dialog */}
      <Dialog open={showNamePopup} onOpenChange={setShowNamePopup}>
        <DialogContent data-testid="name-dialog" className="max-w-md">
          <DialogHeader>
            <DialogTitle>👤 Como você gostaria de ser chamado?</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <p className="text-sm text-slate-600">
              Digite seu nome para um atendimento mais personalizado:
            </p>
            <Input
              data-testid="name-input"
              placeholder="Seu nome"
              value={nameInput}
              onChange={(e) => setNameInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  handleConfirmName();
                }
              }}
              autoFocus
            />
            <p className="text-xs text-slate-500">
              💡 Digite apenas seu nome (ex: João, Maria Silva)
            </p>
            <div className="flex gap-2">
              <Button
                data-testid="name-skip-btn"
                variant="outline"
                onClick={() => setShowNamePopup(false)}
                className="flex-1"
              >
                Depois
              </Button>
              <Button
                data-testid="name-confirm-btn"
                onClick={handleConfirmName}
                className="flex-1 bg-indigo-600 hover:bg-indigo-700"
              >
                Confirmar
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* 🆕 Popup Automático de Credenciais */}
      <Dialog open={showCredentialsPopup} onOpenChange={(open) => {
        setShowCredentialsPopup(open);
        if (!open && credentialsTimeoutRef.current) {
          clearTimeout(credentialsTimeoutRef.current);
        }
      }}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="text-center text-lg font-bold text-green-600">
              🔑 Suas Credenciais de Acesso
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="bg-blue-50 border-2 border-blue-200 rounded-lg p-4">
              <div className="space-y-3">
                <div>
                  <label className="text-sm font-semibold text-gray-600">Usuário:</label>
                  <div className="mt-1 bg-white px-4 py-3 rounded border border-gray-300">
                    <code className="text-lg font-mono font-bold text-blue-600">
                      {credentials.pinned_user}
                    </code>
                  </div>
                </div>
                <div>
                  <label className="text-sm font-semibold text-gray-600">Senha:</label>
                  <div className="mt-1 bg-white px-4 py-3 rounded border border-gray-300">
                    <code className="text-lg font-mono font-bold text-blue-600">
                      {credentials.pinned_pass}
                    </code>
                  </div>
                </div>
              </div>
            </div>
            <p className="text-xs text-center text-gray-500">
              💡 Guarde essas informações em local seguro
            </p>
            <Button 
              onClick={() => {
                setShowCredentialsPopup(false);
                if (credentialsTimeoutRef.current) {
                  clearTimeout(credentialsTimeoutRef.current);
                }
              }}
              className="w-full bg-green-600 hover:bg-green-700"
            >
              OK, Entendi
            </Button>
            <p className="text-xs text-center text-gray-400">
              Este popup fechará automaticamente em 30 segundos
            </p>
          </div>
        </DialogContent>
      </Dialog>
      
      {/* PWA Install Prompt */}
      <InstallPWA />
      
      {/* Lightbox para visualizar imagens em tamanho completo */}
      {lightboxImage && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-90 z-50 flex items-center justify-center p-4"
          onClick={() => setLightboxImage(null)}
        >
          <div className="relative max-w-5xl max-h-full">
            <img 
              src={lightboxImage} 
              alt="Imagem ampliada" 
              className="max-w-full max-h-[90vh] object-contain rounded-lg"
              onClick={(e) => e.stopPropagation()}
            />
            <button
              onClick={() => setLightboxImage(null)}
              className="absolute top-4 right-4 bg-white text-black rounded-full w-10 h-10 flex items-center justify-center hover:bg-gray-200 transition-colors"
            >
              ✕
            </button>
          </div>
        </div>
      )}

      {/* Dialog de Confirmação de Saída */}
      <Dialog open={showExitConfirm} onOpenChange={setShowExitConfirm}>
        <DialogContent className="max-w-xs sm:max-w-sm">
          <DialogHeader className="pb-2">
            <DialogTitle className="text-center text-base font-semibold">
              Deseja sair do atendimento?
            </DialogTitle>
          </DialogHeader>
          <div className="flex flex-col gap-2 pt-2">
            <Button
              onClick={() => setShowExitConfirm(false)}
              className="w-full bg-green-600 hover:bg-green-700 text-white font-medium py-3"
            >
              Não, Desejo ficar
            </Button>
            <Button
              variant="outline"
              onClick={() => {
                setShowExitConfirm(false);
                handleLogout();
              }}
              className="w-full border-red-500 text-red-600 hover:bg-red-50 font-medium py-3"
            >
              Sim, Quero sair
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default ClientChat;
