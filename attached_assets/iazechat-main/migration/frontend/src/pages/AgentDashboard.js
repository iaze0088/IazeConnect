import { useState, useEffect, useRef, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { Headphones, LogOut, Send, Paperclip, Mic, Phone, User, Key, RefreshCw, Bot, BookOpen, Search, X, Monitor, Copy, ExternalLink, ChevronDown } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Card } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { ScrollArea } from '@/components/ui/scroll-area';
import { toast } from 'sonner';
import api, { createWebSocket } from '../lib/api';
import { clearAuth, getAuth } from '../lib/auth';
import { formatWhatsApp } from '../utils/formatters';
import WhatsAppAudioPlayer from '../components/WhatsAppAudioPlayer';

const AgentDashboard = () => {
  const navigate = useNavigate();
  const { userData } = getAuth();
  const [status, setStatus] = useState('EM_ESPERA');  // Frontend usa português, backend mapeia para 'open'
  const [tickets, setTickets] = useState([]);
  const [allTickets, setAllTickets] = useState([]); // Todos os tickets
  const [selectedTicket, setSelectedTicket] = useState(null);
  const [messages, setMessages] = useState([]);
  const [messageText, setMessageText] = useState('');
  const [counts, setCounts] = useState({ EM_ESPERA: 0, ATENDENDO: 0, FINALIZADAS: 0 });
  const [filteredCounts, setFilteredCounts] = useState({ EM_ESPERA: 0, ATENDENDO: 0, FINALIZADAS: 0 }); // Counts filtrados por origem
  const [config, setConfig] = useState({ quick_blocks: [], support_avatar: '' });
  const [tutorials, setTutorials] = useState([]); // Tutoriais/Aplicativos
  const [showTutorials, setShowTutorials] = useState(false); // Modal de tutoriais
  const [pinnedUser, setPinnedUser] = useState('');
  const [pinnedPass, setPinnedPass] = useState('');
  const [resetPhone, setResetPhone] = useState('');
  const [clientCredentials, setClientCredentials] = useState({ pinned_user: '', pinned_pass: '' });
  const [myDepartments, setMyDepartments] = useState([]); // Departamentos do atendente
  const [selectedDepartment, setSelectedDepartment] = useState('all'); // Filtro de departamento
  const [aiEnabled, setAiEnabled] = useState(true); // Estado da IA para o ticket atual
  const [searchTerm, setSearchTerm] = useState(''); // Termo de pesquisa
  const [searchResults, setSearchResults] = useState([]); // Resultados da pesquisa
  const [isSearching, setIsSearching] = useState(false); // Estado da pesquisa
  const wsRef = useRef(null);
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);
  const messagesContainerRef = useRef(null);
  const reconnectAttempts = useRef(0);
  const selectedTicketRef = useRef(null);
  const maxReconnectAttempts = 5;
  const [isLoadingOlderMessages, setIsLoadingOlderMessages] = useState(false);
  const [hasMoreMessages, setHasMoreMessages] = useState(true);
  const [messageOffset, setMessageOffset] = useState(0);
  const [isSendingMessage, setIsSendingMessage] = useState(false);
  const [lightboxImage, setLightboxImage] = useState(null);
  const [originFilter, setOriginFilter] = useState('wa_suporte'); // 'wa_suporte', 'whatsapp_starter', 'ia'
  const [showAllTickets, setShowAllTickets] = useState(false); // Mostrar todos ou apenas 5
  const TICKETS_LIMIT = 5; // ⚡ OTIMIZAÇÃO: Limite inicial de tickets por aba (performance)
  
  // IPTV Apps
  const [iptvApps, setIptvApps] = useState([]);
  const [showIPTVModal, setShowIPTVModal] = useState(false);
  const [selectedApp, setSelectedApp] = useState(null);
  const [appFormData, setAppFormData] = useState({});
  const [generatedUrl, setGeneratedUrl] = useState('');

  // ⚡ OTIMIZAÇÃO: Separar carregamento inicial de filtros
  useEffect(() => {
    // Carregar dados iniciais apenas uma vez
    loadConfig();
    loadMyDepartments();
    loadTutorials();
    loadIPTVApps();
  }, []); // Apenas ao montar

  useEffect(() => {
    // Carregar tickets quando STATUS mudar (não originFilter!)
    loadTickets();
    loadCounts();
    calculateFilteredCounts();
    
    // Atualizar counts a cada 30 segundos (não 5!)
    const interval = setInterval(() => {
      loadCounts();
      calculateFilteredCounts();
    }, 30000);
    return () => clearInterval(interval);
  }, [status]); // ⚡ APENAS quando status mudar (não originFilter)

  // ⚡ MEMOIZAÇÃO: Filtrar tickets usando useMemo (evita re-cálculos)
  const filteredTickets = useMemo(() => {
    return allTickets.filter(ticket => {
      if (ticket.ticket_origin) {
        return ticket.ticket_origin === originFilter;
      }
      
      const isWhatsAppStarter = ticket.whatsapp_origin === true || 
                                 ticket.whatsapp_instance || 
                                 ticket.whatsapp_connection_id ||
                                 ticket.is_whatsapp === true;
      
      const isIA = ticket.ai_agent_id || 
                   ticket.ai_enabled === true ||
                   ticket.ai_responding === true;
      
      const isWASuporte = !isWhatsAppStarter && !isIA;
      
      if (originFilter === 'whatsapp_starter') return isWhatsAppStarter;
      if (originFilter === 'ia') return isIA;
      if (originFilter === 'wa_suporte') return isWASuporte;
      
      return false;
    });
  }, [originFilter, allTickets]);

  // ⚡ Atualizar tickets filtrados e recalcular counts quando filtro mudar
  useEffect(() => {
    setTickets(filteredTickets);
    calculateFilteredCounts();
  }, [filteredTickets]); // ⚡ Filtro local instantâneo

  // Manter selectedTicketRef sempre atualizado
  useEffect(() => {
    selectedTicketRef.current = selectedTicket;
  }, [selectedTicket]);

  // WebSocket connection (Atendente recebe mensagens em tempo real)
  useEffect(() => {
    if (!userData?.id) return;
    
    console.log('🔌 Conectando WebSocket para atendente:', userData.id);
    const ws = createWebSocket(userData.id);
    
    ws.onopen = () => {
      console.log('✅ WebSocket conectado (Atendente)');
      reconnectAttempts.current = 0;
    };
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log('📩 Mensagem recebida (Atendente):', data);
      
      // Aceitar tanto 'message' quanto 'new_message' (da IA)
      if (data.type === 'message' || data.type === 'new_message') {
        // Sempre recarregar lista de tickets para atualizar contadores
        loadTickets();
        loadCounts();
        
        // Se está no ticket ativo, adicionar mensagem em tempo real
        // USAR CALLBACK para acessar o selectedTicket mais recente
        setMessages(prev => {
          // Verificar se a mensagem pertence ao ticket atualmente selecionado
          const currentTicketId = selectedTicketRef.current?.id;
          
          if (currentTicketId && data.message.ticket_id === currentTicketId) {
            const exists = prev.some(m => m.id === data.message.id);
            if (exists) {
              console.log('⚠️ Mensagem duplicada ignorada');
              return prev;
            }
            console.log('✅ Nova mensagem adicionada ao chat ativo:', data.message.text?.substring(0, 50));
            
            // Som de notificação para mensagem de cliente
            if (data.message.from_type === 'client') {
              try {
                const audio = new Audio('/notification.mp3');
                audio.volume = 0.7;
                audio.play().catch(() => {});
              } catch (e) {}
            }
            
            // Scroll automático
            setTimeout(() => {
              messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
            }, 100);
            
            return [...prev, data.message];
          } else {
            console.log('ℹ️ Mensagem não pertence ao ticket ativo, apenas recarregando lista');
            return prev; // Não adicionar se não for do ticket ativo
          }
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
      console.error('❌ WebSocket erro:', error);
    };
    
    ws.onclose = () => {
      if (reconnectAttempts.current < maxReconnectAttempts) {
        reconnectAttempts.current += 1;
        console.log(`⚠️ WebSocket desconectado, tentando reconectar... (tentativa ${reconnectAttempts.current}/${maxReconnectAttempts})`);
        // Reconectar após 3 segundos
        setTimeout(() => {
          if (userData?.id) {
            console.log('🔄 Reconectando WebSocket...');
            // Recursivamente tentar reconectar criando novo WebSocket
          }
        }, 3000);
      } else {
        console.warn('⚠️ Máximo de tentativas de reconexão atingido');
      }
    };
    
    wsRef.current = ws;
    return () => ws.close();
  }, [userData, navigate]); // Removido selectedTicket das dependências

  useEffect(() => {
    console.log('🟢🟢🟢 AGENTDASHBOARD VERSÃO NOVA CARREGADA! 🟢🟢🟢');
    console.log('✅ Lista tickets: maxHeight 480px');
    console.log('✅ Mensagens: altura fixa com calc');
    console.log('✅ Input: fixo na parte inferior');
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Remover filtro complexo de departamento - backend já filtra
  useEffect(() => {
    console.log('🔄 Tickets atualizados:', tickets.length);
  }, [tickets]);

  const loadTickets = async () => {
    try {
      // Backend usa 'open' mas frontend mostra 'EM_ESPERA'
      // Mapear status do frontend para backend
      const backendStatus = status === 'EM_ESPERA' ? 'open' : status;
      
      const { data } = await api.get('/tickets', { params: { status: backendStatus } });
      console.log('📥 Tickets recebidos da API:', data.length, 'tickets', 'Status:', backendStatus);
      
      // ⚡ OTIMIZAÇÃO: Apenas guardar todos os tickets
      // Filtro será aplicado localmente pelo useEffect
      setAllTickets(data);
    } catch (error) {
      console.error('❌ Error loading tickets:', error);
    }
  };

  // **CALCULAR COUNTS ESPECÍFICOS POR ORIGEM**
  const calculateFilteredCounts = async () => {
    try {
      // Buscar TODOS os tickets de todos os status
      const promises = [
        api.get('/tickets', { params: { status: 'open' } }),
        api.get('/tickets', { params: { status: 'ATENDENDO' } }),
        api.get('/tickets', { params: { status: 'FINALIZADAS' } })
      ];
      
      const [esperaRes, atendendoRes, finalizadasRes] = await Promise.all(promises);
      
      // Função auxiliar para filtrar por origem usando ticket_origin
      const filterByOrigin = (tickets) => {
        return tickets.filter(ticket => {
          // Usar campo ticket_origin se existir
          if (ticket.ticket_origin) {
            return ticket.ticket_origin === originFilter;
          }
          
          // Fallback para tickets antigos
          const isWhatsAppStarter = ticket.whatsapp_origin === true || 
                                     ticket.whatsapp_instance || 
                                     ticket.whatsapp_connection_id ||
                                     ticket.is_whatsapp === true;
          
          const isIA = ticket.ai_agent_id || 
                       ticket.ai_enabled === true ||
                       ticket.ai_responding === true;
          
          const isWASuporte = !isWhatsAppStarter && !isIA;
          
          if (originFilter === 'whatsapp_starter') return isWhatsAppStarter;
          if (originFilter === 'ia') return isIA;
          if (originFilter === 'wa_suporte') return isWASuporte;
          
          return false;
        });
      };
      
      // Filtrar cada status por origem
      const esperaFiltered = filterByOrigin(esperaRes.data);
      const atendendoFiltered = filterByOrigin(atendendoRes.data);
      const finalizadasFiltered = filterByOrigin(finalizadasRes.data);
      
      // Atualizar counts filtrados
      setFilteredCounts({
        EM_ESPERA: esperaFiltered.length,
        ATENDENDO: atendendoFiltered.length,
        FINALIZADAS: finalizadasFiltered.length
      });
      
      console.log(`📊 Counts para ${originFilter}:`, {
        EM_ESPERA: esperaFiltered.length,
        ATENDENDO: atendendoFiltered.length,
        FINALIZADAS: finalizadasFiltered.length
      });
    } catch (error) {
      console.error('❌ Error calculating filtered counts:', error);
    }
  };

  const loadMyDepartments = async () => {
    try {
      // Buscar informações do agente logado para pegar seus departamentos
      const { data } = await api.get('/agents/me');
      setMyDepartments(data.department_ids || []);
    } catch (error) {
      console.error('Error loading departments:', error);
    }
  };

  const loadCounts = async () => {
    try {
      const { data } = await api.get('/tickets/counts');
      setCounts(data);
    } catch (error) {
      console.error('Error loading counts:', error);
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

  const loadTutorials = async () => {
    try {
      const { data } = await api.get('/config/tutorials');
      setTutorials(data.filter(t => t.active) || []);
    } catch (error) {
      console.error('Error loading tutorials:', error);
    }
  };

  const loadIPTVApps = async () => {
    try {
      const { data } = await api.get('/iptv-apps');
      setIptvApps(data || []);
    } catch (error) {
      console.error('Error loading IPTV apps:', error);
    }
  };

  const selectIPTVApp = (app) => {
    setSelectedApp(app);
    // Inicializar form data com campos vazios
    const initialData = {};
    app.fields.forEach(field => {
      initialData[field] = '';
    });
    setAppFormData(initialData);
    setGeneratedUrl('');
  };

  const generateIPTVUrl = () => {
    if (!selectedApp) return;
    
    let url = selectedApp.url_template;
    
    // Substituir cada variável {campo} pelo valor do formulário
    selectedApp.fields.forEach(field => {
      const value = appFormData[field] || '';
      url = url.replace(`{${field}}`, value);
    });
    
    setGeneratedUrl(url);
    toast.success('URL gerada com sucesso!');
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    toast.success('URL copiada para a área de transferência!');
  };

  const [automationLogs, setAutomationLogs] = useState([]);
  const [automationProgress, setAutomationProgress] = useState(false);
  const [automationResult, setAutomationResult] = useState(null);

  const automateIPTVConfig = async () => {
    if (!selectedApp) return;
    
    // Validar se todos os campos estão preenchidos
    const allFilled = selectedApp.fields.every(field => appFormData[field]);
    if (!allFilled) {
      toast.error('Preencha todos os campos primeiro!');
      return;
    }
    
    // Limpar logs anteriores e iniciar
    setAutomationLogs([]);
    setAutomationProgress(true);
    setAutomationResult(null);
    
    toast.loading('🤖 Iniciando automação inteligente...', { id: 'automation' });
    
    try {
      const { data } = await api.post(`/iptv-apps/${selectedApp.id}/automate`, {
        form_data: appFormData
      });
      
      // Armazenar logs
      if (data.logs && data.logs.length > 0) {
        setAutomationLogs(data.logs);
      }
      
      // Armazenar resultado
      setAutomationResult(data);
      
      if (data.success || data.ok) {
        toast.success(`✅ Configuração automatizada com sucesso! Score: ${data.automation_score || 0}%`, { id: 'automation' });
        setGeneratedUrl(data.final_url);
        
        // Mostrar detalhes em um toast separado
        if (data.logs && data.logs.length > 0) {
          console.log('📋 Logs da automação:', data.logs);
        }
      } else {
        toast.error(`⚠️ ${data.message || 'Automação falhou. Use o modo manual abaixo.'}`, { id: 'automation' });
        
        // Se tem logs, mostrar no console
        if (data.logs && data.logs.length > 0) {
          console.error('❌ Logs de erro:', data.logs);
        }
      }
    } catch (error) {
      console.error('Automation error:', error);
      toast.error('❌ Erro na automação. Use o método manual abaixo.', { id: 'automation' });
      setAutomationResult({
        success: false,
        message: 'Erro de comunicação com o servidor',
        error: error.message
      });
    } finally {
      setAutomationProgress(false);
    }
  };

  const sendTutorial = (tutorial) => {
    let tutorialText = `📚 ${tutorial.category} - ${tutorial.appName}\n\n`;
    if (tutorial.code) tutorialText += `🔑 Código/Provedor: ${tutorial.code}\n\n`;
    if (tutorial.instructions) tutorialText += `📝 Instruções:\n${tutorial.instructions}\n\n`;
    if (tutorial.videoUrl) tutorialText += `🎥 Vídeo Tutorial: ${tutorial.videoUrl}`;
    
    setMessageText(tutorialText);
    setShowTutorials(false);
    toast.success('Tutorial adicionado ao campo de mensagem!');
  };

  const handleSearch = async (term) => {
    setSearchTerm(term);
    
    if (!term || term.trim() === '') {
      setIsSearching(false);
      setSearchResults([]);
      return;
    }
    
    setIsSearching(true);
    
    try {
      // Buscar em todos os tickets (de todos os status)
      const [esperaRes, atendendoRes, finalizadasRes] = await Promise.all([
        api.get('/tickets', { params: { status: 'EM_ESPERA' } }),
        api.get('/tickets', { params: { status: 'ATENDENDO' } }),
        api.get('/tickets', { params: { status: 'FINALIZADAS' } })
      ]);
      
      const allTicketsData = [
        ...(esperaRes.data || []),
        ...(atendendoRes.data || []),
        ...(finalizadasRes.data || [])
      ];
      
      // Buscar mensagens de todos os tickets e filtrar
      const searchLower = term.toLowerCase();
      const results = [];
      
      for (const ticket of allTicketsData) {
        let matchFound = false;
        let matchDetails = [];
        
        // Buscar no WhatsApp do cliente
        if (ticket.client_id && ticket.client_id.toLowerCase().includes(searchLower)) {
          matchFound = true;
          matchDetails.push('WhatsApp');
        }
        
        // Buscar nas mensagens do ticket
        try {
          const { data: ticketMessages } = await api.get(`/messages/${ticket.id}`);
          for (const msg of ticketMessages) {
            if (msg.text && msg.text.toLowerCase().includes(searchLower)) {
              matchFound = true;
              if (!matchDetails.includes('Mensagem')) {
                matchDetails.push('Mensagem');
              }
              break;
            }
          }
        } catch (error) {
          console.error(`Erro ao buscar mensagens do ticket ${ticket.id}:`, error);
        }
        
        if (matchFound) {
          results.push({
            ...ticket,
            matchDetails: matchDetails.join(', ')
          });
        }
      }
      
      setSearchResults(results);
      toast.success(`${results.length} resultado(s) encontrado(s)`);
    } catch (error) {
      console.error('Erro na pesquisa:', error);
      toast.error('Erro ao realizar pesquisa');
    }
  };

  const clearSearch = () => {
    setSearchTerm('');
    setIsSearching(false);
    setSearchResults([]);
  };

  const loadMessages = async (ticketId, resetScroll = true) => {
    try {
      console.log('🔍 Carregando mensagens do ticket:', ticketId);
      const { data } = await api.get(`/messages/${ticketId}`);
      console.log('✅ Mensagens carregadas:', data.length, 'mensagens');
      console.log('📨 Primeiras 3 mensagens:', data.slice(0, 3));
      setMessages(data);
      setMessageOffset(0);
      setHasMoreMessages(false); // Já carrega todas as mensagens
      
      if (resetScroll) {
        // Scroll para o final após carregar
        setTimeout(() => {
          messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
        }, 100);
      }
    } catch (error) {
      console.error('❌ Erro ao carregar mensagens:', error);
      toast.error('Erro ao carregar mensagens');
    }
  };

  const handleSelectTicket = async (ticket) => {
    setSelectedTicket(ticket);
    loadMessages(ticket.id);
    
    // Marcar mensagens como lidas
    try {
      await api.post(`/tickets/${ticket.id}/mark-as-read`);
      console.log('✅ Mensagens marcadas como lidas');
      
      // Recarregar lista de tickets para atualizar contador
      loadTickets();
    } catch (error) {
      console.error('Error marking as read:', error);
    }
    
    // Atribuir ticket ao atendente atual automaticamente (para IA funcionar)
    try {
      await api.put(`/tickets/${ticket.id}/assign`, {});
      console.log('Ticket atribuído ao atendente');
    } catch (error) {
      console.error('Error assigning ticket:', error);
    }
    
    // Verificar se IA está habilitada para este ticket
    const aiDisabledUntil = ticket.ai_disabled_until;
    if (aiDisabledUntil) {
      const disabledUntilDate = new Date(aiDisabledUntil);
      const now = new Date();
      setAiEnabled(now >= disabledUntilDate);
    } else {
      setAiEnabled(true);
    }
    
    // Marcar como lido (zerar contador)
    if (ticket.unread_count > 0) {
      try {
        await api.post(`/tickets/${ticket.id}/mark-read`);
        // Atualizar localmente
        loadTickets(status);
      } catch (error) {
        console.error('Error marking as read:', error);
      }
    }
    
    // Load client credentials usando endpoint específico
    try {
      const { data } = await api.get(`/users/${ticket.client_id}/credentials`);
      setClientCredentials({
        pinned_user: data.pinned_user || '',
        pinned_pass: data.pinned_pass || ''
      });
    } catch (error) {
      console.error('Error loading client credentials:', error);
      // Se falhar, limpar credenciais para não mostrar as do cliente anterior
      setClientCredentials({
        pinned_user: '',
        pinned_pass: ''
      });
    }
  };

  const handleSendMessage = async (newStatus = null) => {
    if (!selectedTicket || !messageText.trim() || isSendingMessage) return;
    
    setIsSendingMessage(true);
    const textToSend = messageText.trim();
    // Limpar campo IMEDIATAMENTE
    setMessageText('');
    
    try {
      await api.post('/messages', {
        ticket_id: selectedTicket.id,
        from_type: 'agent',
        from_id: userData.id,
        to_type: 'client',
        to_id: selectedTicket.client_id,
        kind: 'text',
        text: textToSend,
        file_url: ''
      });
      
      if (newStatus) {
        await api.post(`/tickets/${selectedTicket.id}/status`, { status: newStatus });
        loadTickets();
      }
      
      // ✅ Mensagem aparecerá via WebSocket em tempo real
      console.log('✅ Mensagem do agente enviada - WebSocket exibirá instantaneamente');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao enviar mensagem');
      // Restaurar mensagem se erro
      setMessageText(textToSend);
    } finally {
      setIsSendingMessage(false);
    }
  };

  const handleFileUpload = async (file) => {
    if (!selectedTicket) return;
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      const { data } = await api.post('/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      await api.post('/messages', {
        ticket_id: selectedTicket.id,
        from_type: 'agent',
        from_id: userData.id,
        to_type: 'client',
        to_id: selectedTicket.client_id,
        kind: data.kind,
        text: '',
        file_url: data.url
      });
      
      // ✅ Arquivo aparecerá via WebSocket em tempo real
      toast.success('Arquivo enviado!');
      console.log('✅ Arquivo do agente enviado - WebSocket exibirá instantaneamente');
    } catch (error) {
      toast.error('Erro ao enviar arquivo');
    }
  };

  const handlePinCredentials = async () => {
    if (!selectedTicket) return;
    try {
      await api.put(`/users/${selectedTicket.client_id}/pin-credentials`, {
        pinned_user: pinnedUser,
        pinned_pass: pinnedPass
      });
      
      // Update local state
      setClientCredentials({
        pinned_user: pinnedUser,
        pinned_pass: pinnedPass
      });
      
      toast.success('Credenciais fixadas!');
      setPinnedUser('');
      setPinnedPass('');
    } catch (error) {
      toast.error('Erro ao fixar credenciais');
    }
  };
  
  const handleToggleAI = async () => {
    if (!selectedTicket) return;
    try {
      const { data } = await api.post(`/tickets/${selectedTicket.id}/toggle-ai`, {});
      setAiEnabled(data.ai_enabled);
      toast.success(data.message);
      
      // Atualizar o ticket localmente
      loadTickets(status);
    } catch (error) {
      toast.error('Erro ao alterar status da IA');
    }
  };

  const handleResetPin = async () => {
    try {
      await api.post('/users/reset-pin', { whatsapp: resetPhone });
      toast.success('PIN resetado!');
      setResetPhone('');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao resetar PIN');
    }
  };

  return (
    <div className="h-screen bg-slate-50 flex flex-col overflow-hidden">
      {/* Header fixo - v2024.01.20.FINAL */}
      <header className="bg-white border-b border-slate-200 flex-shrink-0">
        <div className="max-w-full mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-indigo-600 rounded-xl flex items-center justify-center">
              <Headphones className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-slate-900">Painel do Atendente</h1>
              <p className="text-sm text-slate-600">{userData?.name}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {/* Campo de Pesquisa */}
            <div className="relative">
              <Input
                placeholder="Buscar em conversas..."
                value={searchTerm}
                onChange={(e) => handleSearch(e.target.value)}
                className="w-64 pr-20 h-9"
              />
              {isSearching && searchTerm && (
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={clearSearch}
                  className="absolute right-1 top-1/2 -translate-y-1/2 h-7 w-7 p-0"
                  title="Limpar pesquisa"
                >
                  <X className="w-4 h-4" />
                </Button>
              )}
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
            </div>
            
            {/* Botão Subir Listas */}
            {iptvApps.length > 0 && (
              <Button 
                onClick={() => setShowIPTVModal(true)} 
                variant="outline" 
                size="sm"
                className="bg-blue-50 hover:bg-blue-100 border-blue-300"
              >
                <Monitor className="w-4 h-4 mr-2" />
                Subir Listas
              </Button>
            )}
            
            {tutorials.length > 0 && (
              <Button 
                onClick={() => setShowTutorials(true)} 
                variant="outline" 
                size="sm"
                className="bg-purple-50 hover:bg-purple-100 border-purple-300"
              >
                <BookOpen className="w-4 h-4 mr-2" />
                Tutoriais ({tutorials.length})
              </Button>
            )}
            <Button data-testid="agent-logout-btn" onClick={() => { clearAuth(); navigate('/'); }} variant="outline" size="sm">
              <LogOut className="w-4 h-4 mr-2" />
              Sair
            </Button>
          </div>
        </div>
      </header>

      {/* Conteúdo principal com altura fixa */}
      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar - Lista de clientes */}
        <div className="w-80 bg-white border-r border-slate-200 flex flex-col overflow-hidden">
          {/* Tools */}
          <div className="p-3 border-b border-slate-200 space-y-2 flex-shrink-0">
            <div className="space-y-1">
              <label className="text-xs font-medium text-slate-700">Fixar Credenciais</label>
              <div className="flex gap-1">
                <Input data-testid="pin-user-input" placeholder="Usuário" value={pinnedUser} onChange={(e) => setPinnedUser(e.target.value)} className="text-sm h-8" />
                <Input data-testid="pin-pass-input" placeholder="Senha" value={pinnedPass} onChange={(e) => setPinnedPass(e.target.value)} className="text-sm h-8" />
              </div>
              <Button data-testid="pin-credentials-btn" onClick={handlePinCredentials} size="sm" className="w-full h-7 text-xs">
                Fixar
              </Button>
            </div>
            
            <div className="space-y-1">
              <label className="text-xs font-medium text-slate-700">Resetar PIN</label>
              <div className="flex gap-1">
                <Input data-testid="reset-phone-input" placeholder="WhatsApp" value={resetPhone} onChange={(e) => setResetPhone(e.target.value)} className="text-sm h-8" />
                <Button data-testid="reset-pin-btn" onClick={handleResetPin} size="sm" className="h-8 px-2">
                  <RefreshCw className="w-4 h-4" />
                </Button>
              </div>
            </div>
          </div>

          {/* Tabs e lista de tickets */}
          {isSearching ? (
            // Modo de pesquisa - mostrar resultados
            <div className="flex-1 flex flex-col overflow-hidden">
              <div className="p-3 bg-amber-50 border-b border-amber-200 flex items-center justify-between flex-shrink-0">
                <div className="flex items-center gap-2">
                  <Search className="w-4 h-4 text-amber-600" />
                  <span className="text-sm font-medium text-amber-900">
                    Resultados da Pesquisa: "{searchTerm}"
                  </span>
                  <span className="text-xs bg-amber-200 text-amber-800 px-2 py-0.5 rounded-full">
                    {searchResults.length} encontrado(s)
                  </span>
                </div>
                <Button size="sm" variant="ghost" onClick={clearSearch}>
                  <X className="w-4 h-4 mr-1" />
                  Limpar
                </Button>
              </div>
              
              <div className="flex-1 overflow-y-auto px-2 pb-2 pt-2">
                <div className="space-y-2">
                  {searchResults.length === 0 ? (
                    <div className="text-center py-8 text-slate-500">
                      <Search className="w-12 h-12 mx-auto mb-2 opacity-30" />
                      <p className="text-sm">Nenhum resultado encontrado</p>
                      <p className="text-xs mt-1">Tente buscar por WhatsApp ou conteúdo de mensagens</p>
                    </div>
                  ) : (
                    searchResults.map(ticket => (
                      <Card
                        key={ticket.id}
                        className={`p-3 cursor-pointer transition-all hover:shadow-md relative ${
                          selectedTicket?.id === ticket.id ? 'border-2 border-indigo-500 bg-indigo-50' : ''
                        }`}
                        onClick={() => handleSelectTicket(ticket)}
                      >
                        {ticket.unread_count > 0 && (
                          <span className="absolute -top-2 -right-2 bg-red-500 text-white text-xs font-bold rounded-full w-6 h-6 flex items-center justify-center">
                            {ticket.unread_count}
                          </span>
                        )}
                        
                        <div className="flex items-center gap-2">
                          {ticket.client_avatar && (
                            <img src={ticket.client_avatar} alt="" className="w-10 h-10 rounded-full object-cover" />
                          )}
                          <div className="flex-1 min-w-0">
                            <p className="font-medium text-sm text-slate-900 truncate">
                              {ticket.client_name || formatWhatsApp(ticket.client_whatsapp)}
                            </p>
                            <p className="text-xs text-slate-500 truncate">{formatWhatsApp(ticket.client_whatsapp)}</p>
                            
                            {/* Mostrar onde foi encontrado */}
                            <div className="flex items-center gap-1 mt-1">
                              <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded">
                                {ticket.matchDetails}
                              </span>
                              <span className="text-xs text-slate-400">
                                Status: {ticket.status === 'EM_ESPERA' ? 'Espera' : ticket.status === 'ATENDENDO' ? 'Atendendo' : 'Finalizado'}
                              </span>
                            </div>
                          </div>
                        </div>
                      </Card>
                    ))
                  )}
                </div>
              </div>
            </div>
          ) : (
            // Modo normal - mostrar por status
            <div className="flex-1 flex flex-col overflow-hidden">
              {/* ABAS DE ORIGEM - Primeira camada de filtro */}
              <div className="flex gap-1 p-2 bg-slate-50 border-b flex-shrink-0">
                <Button
                  variant={originFilter === 'wa_suporte' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => {
                    setOriginFilter('wa_suporte');
                    setShowAllTickets(false); // ⚡ Reset ao trocar de aba
                  }}
                  className={`flex-1 text-xs font-semibold transition-all whitespace-nowrap ${
                    originFilter === 'wa_suporte' 
                      ? 'bg-red-600 hover:bg-red-700 text-white border-red-600' 
                      : 'bg-white hover:bg-red-50 text-red-700 border-red-300'
                  }`}
                >
                  WA Suporte
                </Button>
                <Button
                  variant={originFilter === 'whatsapp_starter' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => {
                    setOriginFilter('whatsapp_starter');
                    setShowAllTickets(false); // ⚡ Reset ao trocar de aba
                  }}
                  className={`flex-1 text-xs font-semibold transition-all whitespace-nowrap ${
                    originFilter === 'whatsapp_starter' 
                      ? 'bg-green-600 hover:bg-green-700 text-white border-green-600' 
                      : 'bg-white hover:bg-green-50 text-green-700 border-green-300'
                  }`}
                >
                  WhatsApp
                </Button>
                <Button
                  variant={originFilter === 'ia' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => {
                    setOriginFilter('ia');
                    setShowAllTickets(false); // ⚡ Reset ao trocar de aba
                  }}
                  className={`flex-1 text-xs font-semibold transition-all whitespace-nowrap ${
                    originFilter === 'ia' 
                      ? 'bg-purple-600 hover:bg-purple-700 text-white border-purple-600' 
                      : 'bg-white hover:bg-purple-50 text-purple-700 border-purple-300'
                  }`}
                >
                  I.A
                </Button>
              </div>

              {/* ABAS DE STATUS - Segunda camada de filtro */}
              <Tabs value={status} onValueChange={(newStatus) => {
                setStatus(newStatus);
                setShowAllTickets(false); // ⚡ Reset para mostrar apenas 5 ao mudar de aba
              }} className="flex-1 flex flex-col overflow-hidden">
                <TabsList className="grid grid-cols-3 m-2 flex-shrink-0">
                  <TabsTrigger value="EM_ESPERA" data-testid="tab-em-espera" className="text-xs">
                    Espera <span className="ml-1 px-1.5 py-0.5 bg-red-100 text-red-700 rounded-full text-[10px]">{filteredCounts.EM_ESPERA}</span>
                  </TabsTrigger>
                  <TabsTrigger value="ATENDENDO" data-testid="tab-atendendo" className="text-xs">
                    Atendendo <span className="ml-1 px-1.5 py-0.5 bg-blue-100 text-blue-700 rounded-full text-[10px]">{filteredCounts.ATENDENDO}</span>
                  </TabsTrigger>
                  <TabsTrigger value="FINALIZADAS" data-testid="tab-finalizadas" className="text-xs">
                    Finalizadas <span className="ml-1 px-1.5 py-0.5 bg-green-100 text-green-700 rounded-full text-[10px]">{filteredCounts.FINALIZADAS}</span>
                  </TabsTrigger>
                </TabsList>

              {/* Lista de tickets com scroll interno - ALTURA FIXA para mostrar ~7 tickets */}
              <div className="flex-1 overflow-y-auto px-2 pb-2">
                <div className="space-y-2">
                  {tickets.slice(0, showAllTickets ? tickets.length : TICKETS_LIMIT).map(ticket => (
                  <Card
                    key={ticket.id}
                    data-testid={`ticket-${ticket.id}`}
                    className={`p-3 cursor-pointer transition-all hover:shadow-md relative ${
                      selectedTicket?.id === ticket.id ? 'border-2 border-indigo-500 bg-indigo-50' : ''
                    }`}
                    onClick={() => handleSelectTicket(ticket)}
                  >
                    {/* Badge de mensagens não lidas */}
                    {ticket.unread_count > 0 && (
                      <span className="absolute -top-2 -right-2 bg-red-500 text-white text-xs font-bold rounded-full w-6 h-6 flex items-center justify-center animate-pulse">
                        {ticket.unread_count}
                      </span>
                    )}
                    
                    <div className="flex items-center gap-3">
                      {/* Foto do cliente */}
                      <div className="w-12 h-12 rounded-full bg-gray-200 flex items-center justify-center overflow-hidden flex-shrink-0">
                        {ticket.client_avatar ? (
                          <img src={ticket.client_avatar} alt="Cliente" className="w-full h-full object-cover" />
                        ) : (
                          <User className="w-6 h-6 text-gray-400" />
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-sm text-slate-900 truncate">
                          {ticket.client_name || formatWhatsApp(ticket.client_whatsapp)}
                        </p>
                        <p className="text-xs text-slate-500 truncate">{formatWhatsApp(ticket.client_whatsapp)}</p>
                        
                        {/* Preview da última mensagem (20 caracteres) */}
                        {ticket.last_message && (
                          <p className="text-xs text-slate-400 truncate mt-1">
                            {ticket.last_message.text ? 
                              (ticket.last_message.text.length > 20 ? 
                                ticket.last_message.text.substring(0, 20) + '...' : 
                                ticket.last_message.text
                              ) : 
                              '📎 Arquivo'
                            }
                          </p>
                        )}
                      </div>
                    </div>
                  </Card>
                  ))}
                  
                  {/* Botão "Ver todas" - DESTACADO para melhor visibilidade */}
                  {!showAllTickets && tickets.length > TICKETS_LIMIT && (
                    <div className="pt-3 pb-2 px-2">
                      <Button
                        variant="default"
                        className="w-full text-sm font-semibold bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white shadow-md"
                        onClick={() => setShowAllTickets(true)}
                      >
                        <ChevronDown className="w-4 h-4 mr-2" />
                        Ver Todas as Conversas ({tickets.length - TICKETS_LIMIT} restantes)
                      </Button>
                      <p className="text-xs text-center text-gray-500 mt-2">
                        📊 Mostrando apenas 5 conversas para melhor performance
                      </p>
                    </div>
                  )}
                  
                  {/* Indicador quando mostrando todas */}
                  {showAllTickets && tickets.length > TICKETS_LIMIT && (
                    <div className="pt-2 pb-1 px-2">
                      <div className="bg-green-50 border border-green-200 rounded-lg p-2 text-center">
                        <span className="text-xs font-medium text-green-700">
                          ✅ Mostrando todas as {tickets.length} conversas
                        </span>
                      </div>
                      <Button
                        variant="outline"
                        size="sm"
                        className="w-full mt-2 text-xs"
                        onClick={() => setShowAllTickets(false)}
                      >
                        Mostrar apenas 5
                      </Button>
                    </div>
                  )}
                </div>
              </div>
            </Tabs>
            </div>
          )}
        </div>

        {/* Área de Conversas - Layout fixo e profissional */}
        <div className="flex-1 bg-slate-100 flex flex-col">
          {selectedTicket ? (
            <>
              {/* Header do Chat - Fixo no topo */}
              <div className="bg-white border-b border-slate-200 p-4 flex-shrink-0">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    {/* Foto do cliente */}
                    <div className="w-14 h-14 rounded-full bg-gray-200 flex items-center justify-center overflow-hidden flex-shrink-0">
                      {selectedTicket.client_avatar ? (
                        <img src={selectedTicket.client_avatar} alt="Cliente" className="w-full h-full object-cover" />
                      ) : (
                        <User className="w-7 h-7 text-gray-400" />
                      )}
                    </div>
                    <div>
                      <h3 className="font-semibold text-lg text-slate-900">
                        {selectedTicket.client_name || formatWhatsApp(selectedTicket.client_whatsapp)}
                      </h3>
                      <p className="text-sm text-slate-600 flex items-center gap-2">
                        <Phone className="w-3 h-3" />
                        <span className="font-mono">{formatWhatsApp(selectedTicket.client_whatsapp)}</span>
                      </p>
                    </div>
                  </div>
                  
                  {/* Status badges */}
                  <div className="flex gap-2">
                    {status === 'EM_ESPERA' && (
                      <span className="px-3 py-1 bg-red-100 text-red-700 text-xs font-medium rounded-full">
                        Em Espera
                      </span>
                    )}
                    {status === 'ATENDENDO' && (
                      <span className="px-3 py-1 bg-blue-100 text-blue-700 text-xs font-medium rounded-full">
                        Atendendo
                      </span>
                    )}
                    {status === 'FINALIZADAS' && (
                      <span className="px-3 py-1 bg-green-100 text-green-700 text-xs font-medium rounded-full">
                        Finalizado
                      </span>
                    )}
                  </div>
                </div>
                
                {/* Credenciais fixadas */}
                {(clientCredentials.pinned_user || clientCredentials.pinned_pass) && (
                  <div className="mt-3 p-3 bg-gradient-to-r from-cyan-50 to-blue-50 border-l-4 border-cyan-500 rounded-lg">
                    <div className="flex items-center gap-2">
                      <Key className="w-4 h-4 text-cyan-600" />
                      <span className="font-semibold text-cyan-900 text-sm">Credenciais do Cliente:</span>
                    </div>
                    <div className="mt-2 font-mono text-sm text-cyan-800">
                      <span className="font-semibold">Usuário:</span> {clientCredentials.pinned_user} •{' '}
                      <span className="font-semibold">Senha:</span> {clientCredentials.pinned_pass}
                    </div>
                  </div>
                )}
                
                {/* Botão Toggle IA */}
                <div className="mt-3">
                  <button
                    onClick={handleToggleAI}
                    className={`w-full px-4 py-2 rounded-lg flex items-center justify-center gap-2 transition-all font-medium ${
                      aiEnabled 
                        ? 'bg-green-100 text-green-700 hover:bg-green-200 border-2 border-green-300' 
                        : 'bg-red-100 text-red-700 hover:bg-red-200 border-2 border-red-300'
                    }`}
                  >
                    {aiEnabled ? (
                      <>
                        <Bot className="w-4 h-4" />
                        <span>IA Ativa - Clique para Desativar (1h)</span>
                      </>
                    ) : (
                      <>
                        <Bot className="w-4 h-4" />
                        <span>IA Desativada - Clique para Reativar</span>
                      </>
                    )}
                  </button>
                  <p className="text-xs text-slate-500 mt-1 text-center">
                    {aiEnabled 
                      ? 'IA responderá automaticamente nesta conversa' 
                      : 'IA não responderá nesta conversa até ser reativada'}
                  </p>
                </div>
              </div>

              {/* Área de Mensagens - Com scroll interno APENAS aqui */}
              <div 
                ref={messagesContainerRef}
                className="flex-1 overflow-y-auto bg-slate-50 p-4" 
                style={{ 
                  minHeight: '400px'
                }}
              >
                <div className="space-y-3">
                  {console.log('🎨 Renderizando mensagens:', messages.length, 'total')}
                  {messages.length === 0 ? (
                    <div className="text-center text-slate-500 py-8 bg-white rounded-lg shadow-sm">
                      <p className="font-medium">Nenhuma mensagem ainda</p>
                      <p className="text-sm mt-2">Aguardando mensagens do cliente...</p>
                    </div>
                  ) : (
                    messages.map((msg, index) => {
                      console.log(`📝 Mensagem ${index}:`, msg.from_type, msg.text?.substring(0, 30));
                      
                      // Verificar se deve mostrar data (primeira mensagem ou mudança de dia)
                      const showDate = index === 0 || 
                        new Date(messages[index - 1].created_at).toDateString() !== new Date(msg.created_at).toDateString();
                      
                      return (
                        <div key={msg.id}>
                          {/* Separador de data */}
                          {showDate && (
                            <div className="flex justify-center my-3">
                              <span className="bg-slate-200 text-slate-600 text-xs px-3 py-1 rounded-full">
                                {new Date(msg.created_at).toLocaleDateString('pt-BR', { 
                                  day: '2-digit', 
                                  month: 'long', 
                                  year: 'numeric' 
                                })}
                              </span>
                            </div>
                          )}
                          
                          <div className={`flex gap-2 items-end ${msg.from_type === 'agent' ? 'justify-end' : 'justify-start'} animate-fadeIn`}>
                            {/* Foto do cliente (esquerda) */}
                            {msg.from_type === 'client' && (
                              <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center overflow-hidden flex-shrink-0">
                                {selectedTicket?.client_avatar ? (
                                  <img src={selectedTicket.client_avatar} alt="Cliente" className="w-full h-full object-cover" />
                                ) : (
                                  <User className="w-4 h-4 text-gray-400" />
                                )}
                              </div>
                            )}
                            
                            <div
                              className={`max-w-[70%] p-3 rounded-2xl shadow-sm ${
                                msg.from_type === 'agent'
                                  ? 'bg-indigo-600 text-white rounded-br-sm'
                                  : msg.from_type === 'ai'
                                  ? 'bg-purple-100 text-purple-900 rounded-bl-sm border border-purple-200'
                                  : 'bg-white text-slate-900 rounded-bl-sm border border-slate-200'
                              }`}
                            >
                        {/* Mostrar texto se existir */}
                        {msg.text && msg.kind !== 'pix' && <p className="whitespace-pre-wrap break-words text-sm mb-2">{msg.text}</p>}
                        
                        {/* Renderizar mídia */}
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
                              className="max-w-[250px] max-h-[250px] w-auto h-auto object-contain rounded-lg cursor-pointer hover:opacity-80 transition-opacity block" 
                              onClick={() => window.open(msg.file_url, '_blank')}
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
                              className="max-w-[250px] max-h-[250px] w-auto h-auto rounded-lg block bg-black"
                              onError={(e) => {
                                console.error('Erro ao carregar vídeo:', msg.file_url);
                              }}
                            >
                              Seu navegador não suporta vídeo.
                            </video>
                          ) : null
                        )}
                        {msg.kind === 'audio' && (
                          msg.media_expired ? (
                            <div className="flex items-center gap-2 p-3 bg-gray-100 rounded-lg text-gray-500 text-sm max-w-[250px]">
                              <span>🎵</span>
                              <span>Áudio expirado (7 dias)</span>
                            </div>
                          ) : msg.file_url ? (
                            <WhatsAppAudioPlayer 
                              src={msg.file_url} 
                              isSentByMe={msg.sender_type === 'agent'} 
                            />
                          ) : null
                        )}
                        {msg.kind === 'pix' && (
                          <div>
                            <p className="font-semibold mb-2 text-sm">💰 Chave PIX</p>
                            <code className="text-xs bg-black/10 px-2 py-1 rounded block">{msg.text}</code>
                          </div>
                        )}
                            {/* Nome e horário */}
                            <div className="flex items-center justify-between mt-1 gap-2">
                              {msg.from_type === 'client' && selectedTicket?.client_name && (
                                <span className="text-[10px] font-semibold opacity-80">
                                  {selectedTicket.client_name}
                                </span>
                              )}
                              <p className="text-[10px] opacity-70 ml-auto">
                                {new Date(msg.created_at).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}
                              </p>
                            </div>
                          </div>
                          
                          {/* Foto do agente (direita) */}
                          {msg.from_type === 'agent' && (
                            <div className="w-8 h-8 rounded-full bg-indigo-200 flex items-center justify-center overflow-hidden flex-shrink-0">
                              {config.support_avatar ? (
                                <img src={config.support_avatar} alt="Agente" className="w-full h-full object-cover" />
                              ) : (
                                <Headphones className="w-4 h-4 text-indigo-600" />
                              )}
                            </div>
                          )}
                        </div>
                        </div>
                      );
                    })
                  )}
                  <div ref={messagesEndRef} />
                </div>
              </div>

              {/* Mensagens Rápidas - SEMPRE VISÍVEL, fixo acima do input */}
              {config.quick_blocks && config.quick_blocks.length > 0 && (
                <div className="bg-white border-t border-slate-200 px-4 py-2 flex-shrink-0" style={{ minHeight: '60px' }}>
                  <p className="text-xs font-semibold text-slate-700 mb-2">⚡ Mensagens Rápidas:</p>
                  <div className="flex flex-wrap gap-2">
                    {/* Botão especial de Chave PIX */}
                    {config.pix_key && (
                      <Button
                        size="sm"
                        className="text-xs h-7 bg-emerald-600 hover:bg-emerald-700 text-white font-medium"
                        onClick={() => setMessageText(`💰 CHAVE PIX:\n\n${config.pix_key}\n\n👇 Copie a chave clicando no botão abaixo`)}
                      >
                        💰 PIX
                      </Button>
                    )}
                    
                    {config.quick_blocks.map((block, idx) => (
                      <Button
                        key={idx}
                        data-testid={`quick-block-${idx}`}
                        size="sm"
                        variant="outline"
                        onClick={() => setMessageText(block.text)}
                        className="text-xs h-7 hover:bg-indigo-50 hover:border-indigo-400 hover:text-indigo-700 transition-all"
                      >
                        {block.name}
                      </Button>
                    ))}
                  </div>
                </div>
              )}

              {/* Input de Mensagem - SEMPRE VISÍVEL E FIXO na parte inferior */}
              <div className="bg-white border-t-2 border-slate-300 p-4 flex-shrink-0 shadow-lg" style={{ minHeight: '140px' }}>
                <div className="flex gap-3">
                  <input
                    ref={fileInputRef}
                    type="file"
                    className="hidden"
                    onChange={(e) => e.target.files[0] && handleFileUpload(e.target.files[0])}
                  />
                  <Button
                    data-testid="attach-file-btn"
                    variant="outline"
                    size="icon"
                    onClick={() => fileInputRef.current?.click()}
                    className="flex-shrink-0 h-20 w-12 hover:bg-slate-100"
                    title="Anexar arquivo"
                  >
                    <Paperclip className="w-5 h-5" />
                  </Button>
                  
                  <Textarea
                    data-testid="message-input"
                    placeholder="Digite sua mensagem... (Enter para enviar, Shift+Enter para nova linha)"
                    value={messageText}
                    onChange={(e) => setMessageText(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        handleSendMessage('ATENDENDO');
                      }
                    }}
                    className="flex-1 resize-none border-2 border-slate-300 focus:border-indigo-500 rounded-lg p-3"
                    style={{ height: '80px', minHeight: '80px', maxHeight: '80px' }}
                  />
                  
                  <div className="flex flex-col gap-2 flex-shrink-0">
                    <Button 
                      data-testid="send-and-continue-btn" 
                      onClick={() => handleSendMessage('ATENDENDO')} 
                      disabled={isSendingMessage || !messageText.trim()}
                      className="bg-indigo-600 hover:bg-indigo-700 h-[26px] px-4 font-medium disabled:opacity-50"
                      title="Enviar e continuar atendendo"
                    >
                      {isSendingMessage ? (
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-1"></div>
                      ) : (
                        <Send className="w-4 h-4 mr-1" />
                      )}
                      Enviar
                    </Button>
                    <Button 
                      data-testid="send-and-wait-btn" 
                      onClick={() => handleSendMessage('EM_ESPERA')} 
                      disabled={isSendingMessage || !messageText.trim()}
                      variant="outline"
                      className="h-[26px] px-4 hover:bg-amber-50 hover:border-amber-400 hover:text-amber-700 disabled:opacity-50"
                      title="Enviar e colocar em espera"
                    >
                      ⏸️ Espera
                    </Button>
                    <Button 
                      data-testid="send-and-finish-btn" 
                      onClick={() => handleSendMessage('FINALIZADAS')} 
                      variant="outline"
                      className="h-[26px] px-4 hover:bg-green-50 hover:border-green-400 hover:text-green-700"
                      title="Enviar e finalizar atendimento"
                    >
                      ✓ Finalizar
                    </Button>
                  </div>
                </div>
              </div>
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center text-slate-400">
                <Headphones className="w-20 h-20 mx-auto mb-4 opacity-30" />
                <p className="text-lg font-medium">Selecione um ticket para iniciar o atendimento</p>
                <p className="text-sm mt-2">Escolha um cliente da lista ao lado</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Modal de Tutoriais */}
      <Dialog open={showTutorials} onOpenChange={setShowTutorials}>
        <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>📚 Tutoriais e Aplicativos</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 mt-4">
            {tutorials.length === 0 ? (
              <p className="text-center text-slate-500 py-8">Nenhum tutorial disponível no momento.</p>
            ) : (
              tutorials.map((tutorial) => (
                <Card key={tutorial.id} className="p-4 bg-gradient-to-r from-purple-50 to-blue-50 border-2 border-purple-200">
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <h3 className="font-bold text-lg text-purple-900">{tutorial.category}</h3>
                      <p className="font-semibold text-indigo-700">{tutorial.appName}</p>
                    </div>
                    <Button
                      size="sm"
                      onClick={() => sendTutorial(tutorial)}
                      className="bg-purple-600 hover:bg-purple-700"
                    >
                      <Send className="w-4 h-4 mr-2" />
                      Enviar ao Cliente
                    </Button>
                  </div>
                  
                  {tutorial.code && (
                    <div className="mb-2">
                      <span className="text-xs font-semibold text-slate-600">Código/Provedor:</span>
                      <p className="text-sm font-mono bg-white px-2 py-1 rounded border border-slate-300 mt-1">{tutorial.code}</p>
                    </div>
                  )}
                  
                  {tutorial.instructions && (
                    <div className="mb-2">
                      <span className="text-xs font-semibold text-slate-600">Instruções:</span>
                      <p className="text-sm whitespace-pre-wrap bg-white px-3 py-2 rounded border border-slate-300 mt-1">{tutorial.instructions}</p>
                    </div>
                  )}
                  
                  {tutorial.videoUrl && (
                    <div className="mt-2">
                      <a 
                        href={tutorial.videoUrl} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="text-xs text-blue-600 hover:text-blue-800 underline flex items-center gap-1"
                      >
                        🎥 Assistir vídeo tutorial
                      </a>
                    </div>
                  )}
                </Card>
              ))
            )}
          </div>
        </DialogContent>
      </Dialog>

      {/* Modal Subir Listas IPTV */}
      <Dialog open={showIPTVModal} onOpenChange={setShowIPTVModal}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>📺 Subir Listas - Aplicativos</DialogTitle>
          </DialogHeader>
          
          {!selectedApp ? (
            /* Lista de Apps */
            <div className="space-y-3">
              <p className="text-sm text-gray-600">Selecione um app para configurar:</p>
              {iptvApps.map((app) => (
                <div
                  key={app.id}
                  className="border rounded-lg p-4 hover:bg-gray-50 cursor-pointer transition"
                  onClick={() => selectIPTVApp(app)}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h4 className="font-semibold text-lg">{app.name}</h4>
                      <p className="text-xs text-gray-500 mb-2">{app.type}</p>
                      <p className="text-xs text-blue-600 mb-2">🔗 {app.config_url}</p>
                      {app.instructions && (
                        <div className="mt-2 p-2 bg-yellow-50 rounded text-xs">
                          <p className="font-medium mb-1">📋 Instruções:</p>
                          <p className="whitespace-pre-line">{app.instructions}</p>
                        </div>
                      )}
                    </div>
                    <Button size="sm" variant="outline">
                      Configurar →
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            /* Assistente Guiado Passo a Passo */
            <div className="space-y-4">
              {/* Etapa 1: Preencher dados do cliente */}
              <div className="border-2 border-blue-500 rounded-lg p-4 bg-blue-50">
                <h3 className="font-bold text-lg mb-3 flex items-center gap-2">
                  <span className="bg-blue-500 text-white rounded-full w-8 h-8 flex items-center justify-center text-sm">1</span>
                  Preencha os dados do cliente
                </h3>
                <div className="space-y-3">
                  {selectedApp.fields.map((field) => (
                    <div key={field}>
                      <label className="block text-sm font-medium mb-1 capitalize">
                        {field.replace('_', ' ')}
                      </label>
                      <Input
                        placeholder={`Digite ${field}...`}
                        value={appFormData[field] || ''}
                        onChange={(e) => setAppFormData({ ...appFormData, [field]: e.target.value })}
                        className="bg-white"
                      />
                    </div>
                  ))}
                </div>
              </div>

              {/* Botão de Automação - APENAS PARA SS-IPTV */}
              {Object.keys(appFormData).length > 0 && Object.values(appFormData).every(v => v) && selectedApp?.type === 'SSIPTV' && (
                <div className="border-2 border-green-500 rounded-lg p-4 bg-gradient-to-br from-green-50 to-emerald-50">
                  <h3 className="font-bold text-lg mb-3 flex items-center gap-2">
                    <span className="bg-green-500 text-white rounded-full w-8 h-8 flex items-center justify-center text-sm">🤖</span>
                    Configuração Automática (SS-IPTV)
                  </h3>
                  <p className="text-sm text-gray-600 mb-3">
                    Sistema automático exclusivo para SS-IPTV! Configuração rápida e inteligente.
                  </p>
                  <Button 
                    onClick={automateIPTVConfig}
                    disabled={automationProgress}
                    className="w-full bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700"
                    size="lg"
                  >
                    {automationProgress ? (
                      <>
                        <span className="animate-spin mr-2">⚙️</span>
                        Configurando automaticamente...
                      </>
                    ) : (
                      <>
                        <span className="text-xl mr-2">⚡</span>
                        Configurar Automaticamente
                      </>
                    )}
                  </Button>
                  <p className="text-xs text-center text-gray-500 mt-2">
                    ✨ Sistema inteligente com retry automático e validação
                  </p>
                  
                  {/* Logs da Automação */}
                  {automationLogs.length > 0 && (
                    <div className="mt-4 bg-gray-900 rounded-lg p-3 max-h-48 overflow-y-auto">
                      <h4 className="text-xs font-bold text-green-400 mb-2">📋 Logs da Automação:</h4>
                      {automationLogs.map((log, index) => (
                        <div key={index} className="text-xs font-mono mb-1">
                          <span className="text-gray-500">[{log.time}]</span>{' '}
                          <span className={
                            log.level === 'error' ? 'text-red-400' :
                            log.level === 'warning' ? 'text-yellow-400' :
                            'text-green-400'
                          }>
                            {log.message}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                  
                  {/* Resultado da Automação */}
                  {automationResult && !automationProgress && (
                    <div className={`mt-4 p-3 rounded-lg border-2 ${
                      automationResult.success ? 'bg-green-50 border-green-500' : 'bg-red-50 border-red-500'
                    }`}>
                      <div className="flex items-start gap-2">
                        <span className="text-2xl">{automationResult.success ? '✅' : '⚠️'}</span>
                        <div className="flex-1">
                          <p className="text-sm font-semibold mb-1">
                            {automationResult.message}
                          </p>
                          {automationResult.final_url && (
                            <p className="text-xs text-gray-600 break-all">
                              🔗 URL: {automationResult.final_url}
                            </p>
                          )}
                          {automationResult.automation_score && (
                            <p className="text-xs text-gray-600 mt-1">
                              📊 Score de automação: {automationResult.automation_score}%
                            </p>
                          )}
                          {!automationResult.success && (
                            <p className="text-xs text-red-600 mt-2">
                              👉 Use o método manual abaixo para configurar
                            </p>
                          )}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Divisor OU */}
              {Object.keys(appFormData).length > 0 && Object.values(appFormData).every(v => v) && (
                <div className="flex items-center gap-3 my-4">
                  <div className="flex-1 h-px bg-gray-300"></div>
                  <span className="text-sm text-gray-500 font-medium">OU CONFIGURE MANUALMENTE</span>
                  <div className="flex-1 h-px bg-gray-300"></div>
                </div>
              )}

              {/* Etapa 2: Abrir Site */}
              <div className="border-2 border-blue-500 rounded-lg p-4 bg-gradient-to-br from-blue-50 to-indigo-50">
                <h3 className="font-bold text-lg mb-3 flex items-center gap-2">
                  <span className="bg-blue-500 text-white rounded-full w-8 h-8 flex items-center justify-center text-sm">2</span>
                  Abra o site de configuração (Manual)
                </h3>
                <Button 
                  onClick={() => window.open(selectedApp.config_url, '_blank')}
                  className="w-full bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700"
                  size="lg"
                >
                  <ExternalLink className="w-5 h-5 mr-2" />
                  Abrir {selectedApp.name} 🚀
                </Button>
                <p className="text-xs text-center text-gray-600 mt-2">O site abrirá em uma nova aba</p>
              </div>

              {/* Etapa 3: Copiar e Colar */}
              <div className="border-2 border-green-500 rounded-lg p-4 bg-green-50">
                <h3 className="font-bold text-lg mb-3 flex items-center gap-2">
                  <span className="bg-green-500 text-white rounded-full w-8 h-8 flex items-center justify-center text-sm">3</span>
                  Copie e cole no site (cada campo)
                </h3>
                
                {Object.keys(appFormData).length > 0 && Object.values(appFormData).every(v => v) ? (
                  <div className="space-y-3">
                    {selectedApp.fields.map((field, index) => (
                      <div key={field} className="bg-white p-3 rounded-lg border border-green-200">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-xs font-semibold text-green-700 uppercase">
                            #{index + 1} - {field.replace('_', ' ')}
                          </span>
                          <Button
                            size="sm"
                            onClick={() => copyToClipboard(appFormData[field])}
                            className="h-7"
                          >
                            <Copy className="w-3 h-3 mr-1" />
                            Copiar
                          </Button>
                        </div>
                        <div className="bg-gray-50 p-2 rounded border font-mono text-sm break-all">
                          {appFormData[field]}
                        </div>
                      </div>
                    ))}
                    
                    {/* URL Final */}
                    <div className="mt-4 pt-4 border-t border-green-300">
                      <p className="text-sm font-semibold mb-2">📋 URL Final (Cole na última etapa):</p>
                      <div className="bg-white p-3 rounded-lg border border-green-200 mb-2">
                        <div className="bg-gray-50 p-2 rounded border font-mono text-xs break-all">
                          {selectedApp.url_template.replace(/\{([^}]+)\}/g, (match, field) => appFormData[field] || match)}
                        </div>
                      </div>
                      <Button
                        size="sm"
                        onClick={() => copyToClipboard(selectedApp.url_template.replace(/\{([^}]+)\}/g, (match, field) => appFormData[field] || match))}
                        className="w-full"
                      >
                        <Copy className="w-3 h-3 mr-2" />
                        Copiar URL Completa
                      </Button>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-8 text-gray-400">
                    <p className="text-sm">Preencha todos os campos acima primeiro</p>
                  </div>
                )}
              </div>

              {/* Instruções Detalhadas */}
              {selectedApp.instructions && (
                <div className="bg-yellow-50 border-2 border-yellow-300 rounded-lg p-4">
                  <h3 className="font-bold text-sm mb-2 flex items-center gap-2">
                    💡 Instruções Passo a Passo:
                  </h3>
                  <p className="text-xs whitespace-pre-line text-gray-700">{selectedApp.instructions}</p>
                </div>
              )}

              {/* Botões de Navegação */}
              <div className="flex gap-2 pt-4 border-t">
                <Button variant="outline" onClick={() => { setSelectedApp(null); setGeneratedUrl(''); setAppFormData({}); }} className="flex-1">
                  ← Voltar
                </Button>
                <Button variant="outline" onClick={() => { setShowIPTVModal(false); setSelectedApp(null); setAppFormData({}); }} className="flex-1">
                  Fechar
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
      
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
    </div>
  );
};

export default AgentDashboard;
