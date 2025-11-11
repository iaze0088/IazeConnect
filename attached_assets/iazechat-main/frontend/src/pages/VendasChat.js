import React, { useState, useEffect, useRef } from 'react';
import { Send, Loader2, X, CheckCircle } from 'lucide-react';
import './VendasChat.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';

function VendasChat() {
  const [sessionId, setSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [showModal, setShowModal] = useState(true); // Mostrar modal automaticamente no início
  const [whatsapp, setWhatsapp] = useState('');
  const [pin, setPin] = useState('');
  const [userCredentials, setUserCredentials] = useState({ user: '', password: '' });
  const messagesEndRef = useRef(null);

  // Auto-scroll para última mensagem
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Iniciar sessão ao carregar página
  useEffect(() => {
    // Verificar se há WhatsApp salvo no localStorage
    const savedWhatsapp = localStorage.getItem('vendas_whatsapp');
    initSession(savedWhatsapp);
  }, []);

  const initSession = async (initialWhatsapp = null) => {
    // FORÇAR nova sessão sempre (limpar cache)
    sessionStorage.removeItem('vendas_session_id');
    
    try {
      setIsLoading(true);
      const response = await fetch(`${BACKEND_URL}/api/vendas/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          whatsapp: initialWhatsapp || undefined
        })
      });

      if (!response.ok) throw new Error('Erro ao iniciar sessão');

      const data = await response.json();
      setSessionId(data.session_id);
      sessionStorage.setItem('vendas_session_id', data.session_id);
      setMessages(data.messages || []);
    } catch (error) {
      console.error('Erro ao iniciar sessão:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const sendMessage = async (e) => {
    e.preventDefault();
    
    if (!inputText.trim() || !sessionId || isSending) return;

    const messageText = inputText.trim();
    setInputText('');
    
    setIsSending(true);

    try {
      const response = await fetch(`${BACKEND_URL}/api/vendas/message`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          text: messageText
        })
      });

      if (!response.ok) throw new Error('Erro ao enviar mensagem');

      const data = await response.json();
      
      // Adicionar mensagens (cliente + bot)
      setMessages(prev => [...prev, ...data.messages]);
      
      // Detectar usuário e senha nas respostas do bot
      data.messages.forEach(msg => {
        if (msg.sender === 'bot') {
          const userMatch = msg.text.match(/(?:Usuário|Usuario):\s*(\S+)/i);
          const passMatch = msg.text.match(/Senha:\s*(\S+)/i);
          
          if (userMatch && passMatch) {
            setUserCredentials({
              user: userMatch[1],
              password: passMatch[1]
            });
          }
        }
      });
      
    } catch (error) {
      console.error('Erro ao enviar mensagem:', error);
      alert('Erro ao enviar mensagem. Tente novamente.');
    } finally {
      setIsSending(false);
    }
  };

  const handleModalSubmit = async () => {
    if (!whatsapp || !pin || pin.length !== 2) {
      alert('Preencha o WhatsApp e PIN de 2 dígitos!');
      return;
    }

    try {
      // Salvar dados no backend
      const response = await fetch(`${BACKEND_URL}/api/vendas/save-contact`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          whatsapp: whatsapp,
          pin: pin
        })
      });

      if (!response.ok) throw new Error('Erro ao salvar dados');

      // Salvar WhatsApp no localStorage para próximas sessões
      localStorage.setItem('vendas_whatsapp', whatsapp);

      // Fechar modal
      setShowModal(false);
      
      // Reinicializar sessão com WhatsApp
      await initSession(whatsapp);
      
      // Adicionar mensagem do bot com link do app
      const botMessage = {
        message_id: Date.now().toString(),
        from_type: 'bot',
        text: '✅ Dados salvos com sucesso!\n\n📱 Agora instale o aplicativo WA Vendas:\n\n👇 Clique no link abaixo',
        timestamp: new Date().toISOString(),
        has_button: false,
        app_download: true
      };
      
      setMessages(prev => [...prev, botMessage]);
      
    } catch (error) {
      console.error('Erro ao salvar contato:', error);
      alert('Erro ao salvar dados. Tente novamente.');
    }
  };

  const handleButtonClick = async (action) => {
    if (!sessionId) return;

    try {
      const response = await fetch(`${BACKEND_URL}/api/vendas/button-action`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          action: action
        })
      });

      if (!response.ok) throw new Error('Erro ao processar ação');

      const data = await response.json();
      
      if (data.success && data.message) {
        // Adicionar mensagem de resposta do bot
        setMessages(prev => [...prev, data.message]);
      } else if (!data.success) {
        alert(data.message || 'Erro ao processar ação');
      }
      
    } catch (error) {
      console.error('Erro ao processar botão:', error);
      alert('Erro ao processar ação. Tente novamente.');
    }
  };

  const formatMessage = (text) => {
    // Converter **texto** para <strong>
    let formatted = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    // Converter URLs em links
    formatted = formatted.replace(
      /(https?:\/\/[^\s]+)/g,
      '<a href="$1" target="_blank" rel="noopener noreferrer">$1</a>'
    );
    
    // Quebras de linha
    formatted = formatted.replace(/\n/g, '<br>');
    
    return { __html: formatted };
  };

  if (isLoading) {
    return (
      <div className="vendas-loading">
        <Loader2 className="spin" size={48} />
        <p>Iniciando chat...</p>
      </div>
    );
  }

  return (
    <div className="vendas-container">
      {/* Header estilo WhatsApp */}
      <div className="vendas-header">
        <div className="vendas-logo">
          <img 
            src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='40' height='40'%3E%3Ccircle cx='20' cy='20' r='20' fill='%23128C7E'/%3E%3Ctext x='20' y='27' font-size='20' text-anchor='middle' fill='white' font-family='Arial'%3ES%3C/text%3E%3C/svg%3E"
            alt="Suporte"
          />
        </div>
        <div className="vendas-header-info">
          <h1 className="flex items-center gap-1">
            Suporte
            <svg width="18" height="18" viewBox="0 0 24 24" className="verified-badge">
              <circle cx="12" cy="12" r="10" fill="#25D366"/>
              <path d="M9 12l2 2 4-4" stroke="white" strokeWidth="2.5" fill="none" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </h1>
          <p className="vendas-status">
            <span className="status-dot"></span>
            online
          </p>
        </div>
      </div>

      {/* Credentials Bar - Fixado após header */}
      {userCredentials.user && userCredentials.password && (
        <div className="credentials-bar">
          <span className="font-medium">Usuário:</span> {userCredentials.user} • 
          <span className="font-medium">Senha:</span> {userCredentials.password}
        </div>
      )}

      {/* Mensagens */}
      <div className="vendas-messages">
        {messages.map((msg) => (
          <div 
            key={msg.message_id} 
            className={`message ${msg.from_type === 'client' ? 'message-client' : 'message-bot'}`}
          >
            <div className="message-bubble">
              <div 
                className="message-text"
                dangerouslySetInnerHTML={formatMessage(msg.text)}
              />
              
              {/* Link do App WA Vendas */}
              {msg.app_download && (
                <a 
                  href={`${window.location.origin}`} 
                  target="_blank"
                  rel="noopener noreferrer"
                  className="app-download-card"
                >
                  <img 
                    src="https://customer-assets.emergentagent.com/job_realtime-messenger-19/artifacts/zowasq8c_Sem%20t%C3%ADtulo.jpg" 
                    alt="WA Vendas"
                    className="app-icon"
                  />
                  <div className="app-info">
                    <strong>WA Vendas</strong>
                    <span>Instalar Aplicativo</span>
                  </div>
                </a>
              )}
              
              {/* Botão de ação */}
              {msg.has_button && msg.button_action && (
                <button
                  className="message-button"
                  onClick={() => handleButtonClick(msg.button_action)}
                >
                  {msg.button_text || 'Clique aqui'}
                </button>
              )}
              
              <div className="message-time">
                {new Date(msg.timestamp).toLocaleTimeString('pt-BR', {
                  hour: '2-digit',
                  minute: '2-digit'
                })}
              </div>
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Input de mensagem */}
      <form className="vendas-input" onSubmit={sendMessage}>
        <input
          type="text"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          placeholder="Digite sua mensagem..."
          disabled={isSending || !sessionId}
        />
        <button 
          type="submit" 
          disabled={isSending || !inputText.trim() || !sessionId}
          className={isSending ? 'sending' : ''}
        >
          {isSending ? <Loader2 className="spin" size={20} /> : <Send size={20} />}
        </button>
      </form>

      {/* Modal para WhatsApp + PIN */}
      {showModal && (
        <div className="modal-overlay">
          <div className="modal-content">
            <button className="modal-close" onClick={() => setShowModal(false)}>
              <X size={24} />
            </button>
            
            <h2>📱 Dados para Cadastro</h2>
            <p>Preencha seus dados para continuar:</p>
            
            <div className="modal-form">
              <div className="form-group">
                <label>WhatsApp (com DDD)</label>
                <input
                  type="tel"
                  placeholder="11999999999"
                  value={whatsapp}
                  onChange={(e) => setWhatsapp(e.target.value.replace(/\D/g, ''))}
                  maxLength={11}
                />
              </div>
              
              <div className="form-group">
                <label>PIN (2 dígitos)</label>
                <input
                  type="text"
                  placeholder="25"
                  value={pin}
                  onChange={(e) => setPin(e.target.value.replace(/\D/g, ''))}
                  maxLength={2}
                />
              </div>
              
              <button 
                className="modal-submit"
                onClick={handleModalSubmit}
              >
                Continuar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default VendasChat;
