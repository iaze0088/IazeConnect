import React, { useState } from 'react';
import WhatsAppDashboard from './WhatsAppDashboard';
import WhatsAppChat from './WhatsAppChat';
import WhatsAppSettings from './WhatsAppSettings';
import WhatsAppManager from './WhatsAppManager';

const WhatsAppPro = () => {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [selectedInstance, setSelectedInstance] = useState(null);
  const [showSettings, setShowSettings] = useState(false);

  const tabs = [
    { id: 'dashboard', label: '📊 Dashboard', icon: '📊' },
    { id: 'connections', label: '📱 Conexões', icon: '📱' },
    { id: 'chat', label: '💬 Chat', icon: '💬' },
  ];

  return (
    <div className="whatsapp-pro-container">
      {/* Header com Tabs */}
      <div className="pro-header">
        <div className="header-title">
          <h1>📲 WhatsApp Manager Pro</h1>
          <p>Gerenciamento completo de instâncias WhatsApp</p>
        </div>
        
        <div className="header-tabs">
          {tabs.map(tab => (
            <button
              key={tab.id}
              className={`tab-button ${activeTab === tab.id ? 'active' : ''}`}
              onClick={() => setActiveTab(tab.id)}
            >
              <span className="tab-icon">{tab.icon}</span>
              <span className="tab-label">{tab.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Content Area */}
      <div className="pro-content">
        {/* Dashboard Tab */}
        {activeTab === 'dashboard' && (
          <div className="tab-content">
            <WhatsAppDashboard />
          </div>
        )}

        {/* Conexões Tab */}
        {activeTab === 'connections' && (
          <div className="tab-content">
            <WhatsAppManager 
              onInstanceSelect={(instance) => {
                setSelectedInstance(instance);
                setActiveTab('chat');
              }}
            />
          </div>
        )}

        {/* Chat Tab */}
        {activeTab === 'chat' && (
          <div className="tab-content">
            {!selectedInstance ? (
              <div className="empty-state">
                <div className="empty-icon">💬</div>
                <h3>Selecione uma Instância</h3>
                <p>Vá para a aba "Conexões" e selecione uma instância para iniciar o chat</p>
                <button 
                  className="btn-primary"
                  onClick={() => setActiveTab('connections')}
                >
                  📱 Ir para Conexões
                </button>
              </div>
            ) : (
              <div className="chat-container">
                <div className="chat-header-bar">
                  <div className="instance-info">
                    <span className="instance-badge">📱 {selectedInstance.instance_name}</span>
                    <span className="status-dot connected"></span>
                    <span className="status-text">Conectado</span>
                  </div>
                  <div className="header-actions">
                    <button 
                      className="btn-settings"
                      onClick={() => setShowSettings(true)}
                      title="Configurações"
                    >
                      ⚙️
                    </button>
                    <button 
                      className="btn-close"
                      onClick={() => {
                        setSelectedInstance(null);
                        setActiveTab('connections');
                      }}
                      title="Voltar"
                    >
                      ✕
                    </button>
                  </div>
                </div>
                <WhatsAppChat instanceName={selectedInstance.instance_name} />
              </div>
            )}
          </div>
        )}
      </div>

      {/* Modal de Configurações */}
      {showSettings && selectedInstance && (
        <div className="modal-overlay" onClick={() => setShowSettings(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <WhatsAppSettings 
              instanceName={selectedInstance.instance_name}
              onClose={() => setShowSettings(false)}
            />
          </div>
        </div>
      )}

      <style jsx>{`
        .whatsapp-pro-container {
          min-height: 100vh;
          background: #f5f7fa;
        }

        .pro-header {
          background: white;
          border-bottom: 1px solid #e0e0e0;
          padding: 20px 30px;
        }

        .header-title h1 {
          margin: 0 0 5px 0;
          font-size: 28px;
          font-weight: 700;
          color: #1a1a1a;
        }

        .header-title p {
          margin: 0;
          color: #666;
          font-size: 14px;
        }

        .header-tabs {
          display: flex;
          gap: 10px;
          margin-top: 20px;
        }

        .tab-button {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 12px 20px;
          border: 2px solid #e0e0e0;
          border-radius: 10px;
          background: white;
          cursor: pointer;
          transition: all 0.3s ease;
          font-size: 14px;
          font-weight: 500;
          color: #666;
        }

        .tab-button:hover {
          border-color: #25d366;
          background: #f0fdf4;
          color: #25d366;
        }

        .tab-button.active {
          border-color: #25d366;
          background: linear-gradient(135deg, #25d366 0%, #20ba5a 100%);
          color: white;
          box-shadow: 0 4px 12px rgba(37, 211, 102, 0.3);
        }

        .tab-icon {
          font-size: 18px;
        }

        .pro-content {
          padding: 30px;
        }

        .tab-content {
          animation: fadeIn 0.3s ease;
        }

        @keyframes fadeIn {
          from {
            opacity: 0;
            transform: translateY(10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        .empty-state {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          padding: 80px 20px;
          background: white;
          border-radius: 12px;
          text-align: center;
        }

        .empty-icon {
          font-size: 72px;
          margin-bottom: 20px;
          opacity: 0.5;
        }

        .empty-state h3 {
          margin: 0 0 10px 0;
          font-size: 24px;
          color: #1a1a1a;
        }

        .empty-state p {
          margin: 0 0 30px 0;
          color: #666;
          max-width: 400px;
        }

        .btn-primary {
          padding: 12px 24px;
          border: none;
          border-radius: 8px;
          background: linear-gradient(135deg, #25d366 0%, #20ba5a 100%);
          color: white;
          font-size: 14px;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.2s;
        }

        .btn-primary:hover {
          transform: translateY(-2px);
          box-shadow: 0 4px 12px rgba(37, 211, 102, 0.3);
        }

        .chat-container {
          background: white;
          border-radius: 12px;
          overflow: hidden;
          box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }

        .chat-header-bar {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 15px 20px;
          background: #f9fafb;
          border-bottom: 1px solid #e0e0e0;
        }

        .instance-info {
          display: flex;
          align-items: center;
          gap: 10px;
        }

        .instance-badge {
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
          padding: 6px 12px;
          border-radius: 6px;
          font-size: 13px;
          font-weight: 600;
        }

        .status-dot {
          width: 10px;
          height: 10px;
          border-radius: 50%;
          background: #10b981;
          animation: pulse 2s infinite;
        }

        @keyframes pulse {
          0%, 100% {
            opacity: 1;
          }
          50% {
            opacity: 0.5;
          }
        }

        .status-text {
          font-size: 13px;
          color: #10b981;
          font-weight: 500;
        }

        .header-actions {
          display: flex;
          gap: 10px;
        }

        .btn-settings, .btn-close {
          width: 36px;
          height: 36px;
          border: 1px solid #e0e0e0;
          border-radius: 6px;
          background: white;
          cursor: pointer;
          font-size: 16px;
          transition: all 0.2s;
        }

        .btn-settings:hover {
          background: #f0f0f0;
          border-color: #25d366;
        }

        .btn-close:hover {
          background: #fee2e2;
          border-color: #ef4444;
          color: #ef4444;
        }

        .modal-overlay {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0, 0, 0, 0.5);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 1000;
          animation: fadeIn 0.2s ease;
        }

        .modal-content {
          max-width: 90vw;
          max-height: 90vh;
          overflow-y: auto;
          animation: slideUp 0.3s ease;
        }

        @keyframes slideUp {
          from {
            opacity: 0;
            transform: translateY(20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        @media (max-width: 768px) {
          .pro-header {
            padding: 15px;
          }

          .header-title h1 {
            font-size: 22px;
          }

          .header-tabs {
            overflow-x: auto;
            -webkit-overflow-scrolling: touch;
          }

          .tab-button {
            white-space: nowrap;
          }

          .pro-content {
            padding: 15px;
          }
        }
      `}</style>
    </div>
  );
};

export default WhatsAppPro;
