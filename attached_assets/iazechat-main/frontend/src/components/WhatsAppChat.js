import React, { useState, useEffect, useRef } from 'react';
import { toast } from 'sonner';

const WhatsAppChat = ({ instanceName }) => {
  const [chats, setChats] = useState([]);
  const [selectedChat, setSelectedChat] = useState(null);
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [sending, setSending] = useState(false);
  const messagesEndRef = useRef(null);

  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

  // Carregar lista de chats
  const loadChats = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/whatsapp/chats/${instanceName}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setChats(data.chats || []);
      }
    } catch (error) {
      console.error('Erro ao carregar chats:', error);
      toast.error('Erro ao carregar chats');
    } finally {
      setLoading(false);
    }
  };

  // Carregar mensagens do chat selecionado
  const loadMessages = async (chatId) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(
        `${BACKEND_URL}/api/whatsapp/messages/${instanceName}/${chatId}`,
        { headers: { 'Authorization': `Bearer ${token}` } }
      );

      if (response.ok) {
        const data = await response.json();
        setMessages(data.messages || []);
        scrollToBottom();
      }
    } catch (error) {
      console.error('Erro ao carregar mensagens:', error);
      toast.error('Erro ao carregar mensagens');
    }
  };

  // Enviar mensagem
  const sendMessage = async (e) => {
    e.preventDefault();
    if (!newMessage.trim() || !selectedChat) return;

    try {
      setSending(true);
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/whatsapp/send-message`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          instance_name: instanceName,
          number: selectedChat.id,
          text: newMessage
        })
      });

      if (response.ok) {
        setNewMessage('');
        // Adicionar mensagem localmente
        const tempMessage = {
          id: Date.now(),
          fromMe: true,
          body: newMessage,
          timestamp: new Date().toISOString()
        };
        setMessages(prev => [...prev, tempMessage]);
        scrollToBottom();
        toast.success('Mensagem enviada!');
      } else {
        toast.error('Erro ao enviar mensagem');
      }
    } catch (error) {
      console.error('Erro ao enviar:', error);
      toast.error('Erro ao enviar mensagem');
    } finally {
      setSending(false);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    if (instanceName) {
      loadChats();
      const interval = setInterval(loadChats, 30000); // Atualizar a cada 30s
      return () => clearInterval(interval);
    }
  }, [instanceName]);

  useEffect(() => {
    if (selectedChat) {
      loadMessages(selectedChat.id);
      const interval = setInterval(() => loadMessages(selectedChat.id), 10000); // Atualizar a cada 10s
      return () => clearInterval(interval);
    }
  }, [selectedChat]);

  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString('pt-BR', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const formatPhone = (phone) => {
    const cleaned = phone.replace(/\D/g, '');
    if (cleaned.length === 13) {
      return `+${cleaned.slice(0, 2)} ${cleaned.slice(2, 4)} ${cleaned.slice(4, 9)}-${cleaned.slice(9)}`;
    }
    return phone;
  };

  return (
    <div className="whatsapp-chat-container">
      {/* Lista de Chats */}
      <div className="chat-sidebar">
        <div className="sidebar-header">
          <h3>💬 Conversas</h3>
          <button onClick={loadChats} className="refresh-btn" title="Atualizar">
            🔄
          </button>
        </div>

        {loading ? (
          <div className="loading-chats">Carregando...</div>
        ) : chats.length === 0 ? (
          <div className="empty-chats">Nenhuma conversa</div>
        ) : (
          <div className="chats-list">
            {chats.map((chat) => (
              <div
                key={chat.id}
                className={`chat-item ${selectedChat?.id === chat.id ? 'active' : ''}`}
                onClick={() => setSelectedChat(chat)}
              >
                <div className="chat-avatar">
                  {chat.name ? chat.name.charAt(0).toUpperCase() : '👤'}
                </div>
                <div className="chat-info">
                  <div className="chat-name">{chat.name || formatPhone(chat.id)}</div>
                  <div className="chat-last-message">
                    {chat.lastMessage?.substring(0, 30) || 'Sem mensagens'}
                  </div>
                </div>
                {chat.unreadCount > 0 && (
                  <div className="unread-badge">{chat.unreadCount}</div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Área de Mensagens */}
      <div className="messages-area">
        {!selectedChat ? (
          <div className="no-chat-selected">
            <div className="empty-icon">💬</div>
            <h3>Selecione uma conversa</h3>
            <p>Escolha um chat na lista para visualizar as mensagens</p>
          </div>
        ) : (
          <>
            {/* Header do Chat */}
            <div className="messages-header">
              <div className="chat-avatar large">
                {selectedChat.name ? selectedChat.name.charAt(0).toUpperCase() : '👤'}
              </div>
              <div className="header-info">
                <h3>{selectedChat.name || formatPhone(selectedChat.id)}</h3>
                <p className="status">{formatPhone(selectedChat.id)}</p>
              </div>
            </div>

            {/* Lista de Mensagens */}
            <div className="messages-list">
              {messages.length === 0 ? (
                <div className="no-messages">Nenhuma mensagem</div>
              ) : (
                messages.map((message) => (
                  <div
                    key={message.id}
                    className={`message ${message.fromMe ? 'sent' : 'received'}`}
                  >
                    <div className="message-bubble">
                      <div className="message-text">{message.body || message.text}</div>
                      <div className="message-time">{formatTime(message.timestamp)}</div>
                    </div>
                  </div>
                ))
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Input de Mensagem */}
            <form className="message-input" onSubmit={sendMessage}>
              <input
                type="text"
                value={newMessage}
                onChange={(e) => setNewMessage(e.target.value)}
                placeholder="Digite uma mensagem..."
                disabled={sending}
              />
              <button type="submit" disabled={sending || !newMessage.trim()}>
                {sending ? '⏳' : '📤'}
              </button>
            </form>
          </>
        )}
      </div>

      <style jsx>{`
        .whatsapp-chat-container {
          display: flex;
          height: 600px;
          border: 1px solid #e0e0e0;
          border-radius: 12px;
          overflow: hidden;
          background: white;
        }

        .chat-sidebar {
          width: 350px;
          border-right: 1px solid #e0e0e0;
          display: flex;
          flex-direction: column;
        }

        .sidebar-header {
          padding: 20px;
          border-bottom: 1px solid #e0e0e0;
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .sidebar-header h3 {
          margin: 0;
          font-size: 18px;
          font-weight: 600;
        }

        .refresh-btn {
          background: none;
          border: none;
          font-size: 20px;
          cursor: pointer;
          padding: 5px;
        }

        .refresh-btn:hover {
          opacity: 0.7;
        }

        .chats-list {
          flex: 1;
          overflow-y: auto;
        }

        .chat-item {
          display: flex;
          align-items: center;
          padding: 15px;
          gap: 12px;
          cursor: pointer;
          border-bottom: 1px solid #f0f0f0;
          transition: background 0.2s;
        }

        .chat-item:hover {
          background: #f5f5f5;
        }

        .chat-item.active {
          background: #e3f2fd;
        }

        .chat-avatar {
          width: 48px;
          height: 48px;
          border-radius: 50%;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          display: flex;
          align-items: center;
          justify-content: center;
          color: white;
          font-weight: 600;
          font-size: 18px;
        }

        .chat-avatar.large {
          width: 40px;
          height: 40px;
        }

        .chat-info {
          flex: 1;
          min-width: 0;
        }

        .chat-name {
          font-weight: 600;
          margin-bottom: 4px;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }

        .chat-last-message {
          font-size: 14px;
          color: #666;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }

        .unread-badge {
          background: #25d366;
          color: white;
          border-radius: 12px;
          padding: 2px 8px;
          font-size: 12px;
          font-weight: 600;
        }

        .messages-area {
          flex: 1;
          display: flex;
          flex-direction: column;
        }

        .no-chat-selected {
          flex: 1;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          color: #999;
        }

        .empty-icon {
          font-size: 64px;
          margin-bottom: 20px;
        }

        .messages-header {
          padding: 15px 20px;
          border-bottom: 1px solid #e0e0e0;
          display: flex;
          align-items: center;
          gap: 12px;
          background: #f9fafb;
        }

        .header-info h3 {
          margin: 0;
          font-size: 16px;
          font-weight: 600;
        }

        .header-info .status {
          margin: 0;
          font-size: 13px;
          color: #666;
        }

        .messages-list {
          flex: 1;
          overflow-y: auto;
          padding: 20px;
          background: #efeae2;
        }

        .message {
          display: flex;
          margin-bottom: 12px;
        }

        .message.sent {
          justify-content: flex-end;
        }

        .message.received {
          justify-content: flex-start;
        }

        .message-bubble {
          max-width: 65%;
          padding: 8px 12px;
          border-radius: 8px;
          position: relative;
        }

        .message.sent .message-bubble {
          background: #dcf8c6;
          border-bottom-right-radius: 2px;
        }

        .message.received .message-bubble {
          background: white;
          border-bottom-left-radius: 2px;
        }

        .message-text {
          margin-bottom: 4px;
          word-wrap: break-word;
        }

        .message-time {
          font-size: 11px;
          color: #667;
          text-align: right;
        }

        .message-input {
          padding: 15px;
          border-top: 1px solid #e0e0e0;
          display: flex;
          gap: 10px;
          background: white;
        }

        .message-input input {
          flex: 1;
          padding: 12px 16px;
          border: 1px solid #e0e0e0;
          border-radius: 24px;
          font-size: 14px;
          outline: none;
        }

        .message-input input:focus {
          border-color: #25d366;
        }

        .message-input button {
          width: 48px;
          height: 48px;
          border: none;
          border-radius: 50%;
          background: #25d366;
          color: white;
          font-size: 20px;
          cursor: pointer;
          transition: all 0.2s;
        }

        .message-input button:hover:not(:disabled) {
          background: #20ba5a;
          transform: scale(1.05);
        }

        .message-input button:disabled {
          background: #ccc;
          cursor: not-allowed;
        }

        .loading-chats, .empty-chats, .no-messages {
          padding: 40px;
          text-align: center;
          color: #999;
        }

        @media (max-width: 768px) {
          .chat-sidebar {
            width: 100%;
            border-right: none;
          }
          
          .messages-area {
            display: none;
          }
        }
      `}</style>
    </div>
  );
};

export default WhatsAppChat;
