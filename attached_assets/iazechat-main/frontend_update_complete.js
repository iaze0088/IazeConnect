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
  const [showContactPopup, setShowContactPopup] = useState(false);
  const [showCredentialsPopup, setShowCredentialsPopup] = useState(false);
  const [showAppDownloadPopup, setShowAppDownloadPopup] = useState(false);
  const [showExitConfirm, setShowExitConfirm] = useState(false);
  
  // Dados
  const [whatsapp, setWhatsapp] = useState('');
  const [pin, setPin] = useState('');
  const [credentials, setCredentials] = useState({ usuario: '', senha: '' });
  const [isGeneratingTest, setIsGeneratingTest] = useState(false);
  
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    initSession();
  }, []);

  const initSession = async () => {
    try {
      setIsLoading(true);
      const response = await fetch(`${BACKEND_URL}/api/vendas/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({})
      });
      const data = await response.json();
      setSessionId(data.session_id);
      setMessages(data.messages || []);
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

  const handleMediaUpload = async (file, mediaType) => {
    if (!file || !sessionId) return;
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
      await new Promise(resolve => setTimeout(resolve, 10000));
      setMessages(prev => [...prev, ...data.messages]);
    } catch (error) {
      console.error('Erro:', error);
      alert('Erro ao processar arquivo.');
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
    if (!whatsapp || !pin || pin.length !== 2) {
      alert('Preencha WhatsApp e PIN de 2 dígitos!');
      return;
    }
    
    setIsGeneratingTest(true);
    
    try {
      const response = await fetch(`${BACKEND_URL}/api/vendas/request-test`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          whatsapp: whatsapp,
          pin: pin
        })
      });
      
      const data = await response.json();
      
      if (data.success) {
        // Salvar credenciais
        setCredentials({
          usuario: data.usuario,
          senha: data.senha
        });
        
        // Fechar pop-up de contato e abrir de credenciais
        setShowContactPopup(false);
        setShowCredentialsPopup(true);
        
        // Adicionar mensagem no chat
        setMessages(prev => [...prev, {
          from_type: 'bot',
          text: data.message,
          timestamp: new Date().toISOString()
        }]);
      } else {
        alert(data.message || 'Erro ao gerar teste');
      }
    } catch (error) {
      console.error('Erro:', error);
      alert('Erro ao solicitar teste');
    } finally {
      setIsGeneratingTest(false);
    }
  };

  const handleDownloadApp = () => {
    setShowCredentialsPopup(false);
    setShowAppDownloadPopup(true);
  };

  const handleInstallApp = () => {
    // Salvar credenciais no localStorage para o PWA
    localStorage.setItem('wa_suporte_user', credentials.usuario);
    localStorage.setItem('wa_suporte_pass', credentials.senha);
    localStorage.setItem('wa_suporte_whatsapp', whatsapp);
    localStorage.setItem('wa_suporte_pin', pin);
    
    // Abrir PWA em nova aba
    window.open('/wa-suporte-app', '_blank');
    
    // Fechar pop-up e enviar mensagem
    setShowAppDownloadPopup(false);
    
    // Adicionar mensagem automática
    setMessages(prev => [...prev, {
      from_type: 'bot',
      text: 'Agora que recebeu o usuário e senha, "POR FAVOR" instala nosso aplicativo de Suporte Humanizado pra realizar a contratação após o teste! 📱',
      timestamp: new Date().toISOString()
    }]);
  };

  const handleCloseChat = () => {
    setShowExitConfirm(true);
  };

  const confirmExit = (shouldExit) => {
    if (shouldExit) {
      // Mostrar mensagem de despedida
      setMessages(prev => [...prev, {
        from_type: 'bot',
        text: 'Caso você mude de ideia me chama nesse link de suporte www.suporte.help\n\nAté mais! 👋',
        timestamp: new Date().toISOString()
      }]);
      
      // Aguardar um pouco e redirecionar
      setTimeout(() => {
        window.location.href = '/';
      }, 2000);
    }
    setShowExitConfirm(false);
  };

  const renderMessage = (msg, index) => {
    const senderClass = msg.from_type === 'client' ? 'user' : 'bot';
    return (
      <div key={index} className={`vendas-message ${senderClass}`}>
        <div className="vendas-message-bubble">
          <p className="vendas-message-text">{msg.text}</p>
          
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
      {/* Header */}
      <div className="vendas-chat-header">
        <div className="vendas-chat-header-info">
          <div className="vendas-chat-avatar">🤖</div>
          <div className="vendas-chat-title">
            <p className="vendas-chat-name">CyberTV Vendas</p>
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

      {/* Input */}
      <div className="vendas-chat-input-area">
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

      {/* Pop-up 1: Solicitar WhatsApp + PIN */}
      {showContactPopup && (
        <div className="vendas-popup-overlay">
          <div className="vendas-popup">
            <h3>📱 Digite seus dados</h3>
            <p>Para gerar o teste, precisamos do seu WhatsApp e uma senha de 2 dígitos</p>
            
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
              disabled={isGeneratingTest || !whatsapp || pin.length !== 2}
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
            
            <button className="vendas-popup-btn-cancel" onClick={() => setShowContactPopup(false)}>
              Cancelar
            </button>
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

      {/* Pop-up 3: Baixar Aplicativo */}
      {showAppDownloadPopup && (
        <div className="vendas-popup-overlay">
          <div className="vendas-popup">
            <h3>📱 Baixar Aplicativo</h3>
            <p>Instale nosso aplicativo para continuar usando o serviço</p>
            
            <div className="vendas-app-info">
              <p>Digite novamente seus dados para salvar no app:</p>
              
              <input
                type="tel"
                placeholder="WhatsApp"
                value={whatsapp}
                onChange={(e) => setWhatsapp(e.target.value.replace(/\D/g, ''))}
                className="vendas-popup-input"
              />
              
              <input
                type="text"
                placeholder="Senha de 2 dígitos"
                value={pin}
                onChange={(e) => setPin(e.target.value.replace(/\D/g, ''))}
                maxLength="2"
                className="vendas-popup-input"
              />
            </div>
            
            <button className="vendas-popup-btn" onClick={handleInstallApp}>
              ✅ INSTALAR AGORA
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
    </div>
  );
}

export default VendasChatNew;
