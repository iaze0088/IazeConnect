import React, { useState, useEffect } from 'react';
import { toast } from 'sonner';

const WhatsAppSettings = ({ instanceName, onClose }) => {
  const [settings, setSettings] = useState({
    rejectCall: false,
    msgCall: '',
    groupsIgnore: true,
    alwaysOnline: false,
    readMessages: false,
    readStatus: false,
    syncFullHistory: false,
    proxyHost: '',
    proxyPort: '',
    proxyProtocol: 'http',
    proxyUsername: '',
    proxyPassword: '',
    webhookUrl: '',
    webhookByEvents: false,
    webhookBase64: false,
    webhookEvents: []
  });
  
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [activeTab, setActiveTab] = useState('general');

  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

  const availableEvents = [
    'QRCODE_UPDATED',
    'MESSAGES_UPSERT',
    'MESSAGES_UPDATE',
    'MESSAGES_DELETE',
    'SEND_MESSAGE',
    'CONNECTION_UPDATE',
    'CALL',
    'NEW_JWT_TOKEN'
  ];

  useEffect(() => {
    loadSettings();
  }, [instanceName]);

  const loadSettings = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(
        `${BACKEND_URL}/api/whatsapp/settings/${instanceName}`,
        { headers: { 'Authorization': `Bearer ${token}` } }
      );

      if (response.ok) {
        const data = await response.json();
        setSettings({ ...settings, ...data.settings });
      }
    } catch (error) {
      console.error('Erro ao carregar configurações:', error);
    } finally {
      setLoading(false);
    }
  };

  const saveSettings = async () => {
    try {
      setSaving(true);
      const token = localStorage.getItem('token');
      const response = await fetch(
        `${BACKEND_URL}/api/whatsapp/settings/${instanceName}`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify(settings)
        }
      );

      if (response.ok) {
        toast.success('Configurações salvas com sucesso!');
        onClose?.();
      } else {
        toast.error('Erro ao salvar configurações');
      }
    } catch (error) {
      console.error('Erro ao salvar:', error);
      toast.error('Erro ao salvar configurações');
    } finally {
      setSaving(false);
    }
  };

  const toggleWebhookEvent = (event) => {
    setSettings(prev => ({
      ...prev,
      webhookEvents: prev.webhookEvents.includes(event)
        ? prev.webhookEvents.filter(e => e !== event)
        : [...prev.webhookEvents, event]
    }));
  };

  if (loading) {
    return <div className="settings-loading">Carregando configurações...</div>;
  }

  return (
    <div className="whatsapp-settings">
      <div className="settings-header">
        <h2>⚙️ Configurações - {instanceName}</h2>
        <button onClick={onClose} className="close-btn">✕</button>
      </div>

      <div className="settings-tabs">
        <button
          className={`tab ${activeTab === 'general' ? 'active' : ''}`}
          onClick={() => setActiveTab('general')}
        >
          🔧 Geral
        </button>
        <button
          className={`tab ${activeTab === 'proxy' ? 'active' : ''}`}
          onClick={() => setActiveTab('proxy')}
        >
          🌐 Proxy
        </button>
        <button
          className={`tab ${activeTab === 'webhook' ? 'active' : ''}`}
          onClick={() => setActiveTab('webhook')}
        >
          🔗 Webhook
        </button>
      </div>

      <div className="settings-content">
        {/* Tab Geral */}
        {activeTab === 'general' && (
          <div className="settings-section">
            <h3>Configurações Gerais</h3>

            <div className="setting-item">
              <label className="setting-label">
                <input
                  type="checkbox"
                  checked={settings.rejectCall}
                  onChange={(e) => setSettings({...settings, rejectCall: e.target.checked})}
                />
                <span>Rejeitar Chamadas Automaticamente</span>
              </label>
              <p className="setting-description">
                Rejeita automaticamente chamadas de voz/vídeo recebidas
              </p>
            </div>

            {settings.rejectCall && (
              <div className="setting-item">
                <label>Mensagem ao Rejeitar Chamada:</label>
                <input
                  type="text"
                  value={settings.msgCall}
                  onChange={(e) => setSettings({...settings, msgCall: e.target.value})}
                  placeholder="Ex: Não aceito chamadas, envie mensagem"
                  className="setting-input"
                />
              </div>
            )}

            <div className="setting-item">
              <label className="setting-label">
                <input
                  type="checkbox"
                  checked={settings.groupsIgnore}
                  onChange={(e) => setSettings({...settings, groupsIgnore: e.target.checked})}
                />
                <span>Ignorar Mensagens de Grupos</span>
              </label>
              <p className="setting-description">
                Não processar mensagens recebidas em grupos
              </p>
            </div>

            <div className="setting-item">
              <label className="setting-label">
                <input
                  type="checkbox"
                  checked={settings.alwaysOnline}
                  onChange={(e) => setSettings({...settings, alwaysOnline: e.target.checked})}
                />
                <span>Sempre Online</span>
              </label>
              <p className="setting-description">
                Manter status sempre online no WhatsApp
              </p>
            </div>

            <div className="setting-item">
              <label className="setting-label">
                <input
                  type="checkbox"
                  checked={settings.readMessages}
                  onChange={(e) => setSettings({...settings, readMessages: e.target.checked})}
                />
                <span>Marcar Mensagens como Lidas</span>
              </label>
              <p className="setting-description">
                Automaticamente marcar todas mensagens como lidas
              </p>
            </div>

            <div className="setting-item">
              <label className="setting-label">
                <input
                  type="checkbox"
                  checked={settings.readStatus}
                  onChange={(e) => setSettings({...settings, readStatus: e.target.checked})}
                />
                <span>Visualizar Status Automaticamente</span>
              </label>
              <p className="setting-description">
                Visualizar automaticamente os status dos contatos
              </p>
            </div>

            <div className="setting-item">
              <label className="setting-label">
                <input
                  type="checkbox"
                  checked={settings.syncFullHistory}
                  onChange={(e) => setSettings({...settings, syncFullHistory: e.target.checked})}
                />
                <span>Sincronizar Histórico Completo</span>
              </label>
              <p className="setting-description">
                Sincronizar todas as mensagens antigas ao conectar
              </p>
            </div>
          </div>
        )}

        {/* Tab Proxy */}
        {activeTab === 'proxy' && (
          <div className="settings-section">
            <h3>Configurações de Proxy</h3>
            <p className="section-description">
              Configure um proxy para rotear o tráfego da instância
            </p>

            <div className="setting-item">
              <label>Host do Proxy:</label>
              <input
                type="text"
                value={settings.proxyHost}
                onChange={(e) => setSettings({...settings, proxyHost: e.target.value})}
                placeholder="Ex: proxy.example.com"
                className="setting-input"
              />
            </div>

            <div className="setting-item">
              <label>Porta:</label>
              <input
                type="text"
                value={settings.proxyPort}
                onChange={(e) => setSettings({...settings, proxyPort: e.target.value})}
                placeholder="Ex: 8080"
                className="setting-input"
              />
            </div>

            <div className="setting-item">
              <label>Protocolo:</label>
              <select
                value={settings.proxyProtocol}
                onChange={(e) => setSettings({...settings, proxyProtocol: e.target.value})}
                className="setting-input"
              >
                <option value="http">HTTP</option>
                <option value="https">HTTPS</option>
                <option value="socks4">SOCKS4</option>
                <option value="socks5">SOCKS5</option>
              </select>
            </div>

            <div className="setting-item">
              <label>Usuário (opcional):</label>
              <input
                type="text"
                value={settings.proxyUsername}
                onChange={(e) => setSettings({...settings, proxyUsername: e.target.value})}
                placeholder="Usuário do proxy"
                className="setting-input"
              />
            </div>

            <div className="setting-item">
              <label>Senha (opcional):</label>
              <input
                type="password"
                value={settings.proxyPassword}
                onChange={(e) => setSettings({...settings, proxyPassword: e.target.value})}
                placeholder="Senha do proxy"
                className="setting-input"
              />
            </div>
          </div>
        )}

        {/* Tab Webhook */}
        {activeTab === 'webhook' && (
          <div className="settings-section">
            <h3>Configurações de Webhook</h3>
            <p className="section-description">
              Configure webhooks para receber eventos em tempo real
            </p>

            <div className="setting-item">
              <label>URL do Webhook:</label>
              <input
                type="url"
                value={settings.webhookUrl}
                onChange={(e) => setSettings({...settings, webhookUrl: e.target.value})}
                placeholder="https://seu-servidor.com/webhook"
                className="setting-input"
              />
            </div>

            <div className="setting-item">
              <label className="setting-label">
                <input
                  type="checkbox"
                  checked={settings.webhookByEvents}
                  onChange={(e) => setSettings({...settings, webhookByEvents: e.target.checked})}
                />
                <span>Filtrar por Eventos Específicos</span>
              </label>
            </div>

            {settings.webhookByEvents && (
              <div className="setting-item">
                <label>Eventos para Webhook:</label>
                <div className="events-grid">
                  {availableEvents.map(event => (
                    <label key={event} className="event-checkbox">
                      <input
                        type="checkbox"
                        checked={settings.webhookEvents.includes(event)}
                        onChange={() => toggleWebhookEvent(event)}
                      />
                      <span>{event}</span>
                    </label>
                  ))}
                </div>
              </div>
            )}

            <div className="setting-item">
              <label className="setting-label">
                <input
                  type="checkbox"
                  checked={settings.webhookBase64}
                  onChange={(e) => setSettings({...settings, webhookBase64: e.target.checked})}
                />
                <span>Enviar Mídia em Base64</span>
              </label>
              <p className="setting-description">
                Incluir arquivos de mídia codificados em base64 no payload
              </p>
            </div>
          </div>
        )}
      </div>

      <div className="settings-footer">
        <button onClick={onClose} className="btn-cancel">
          Cancelar
        </button>
        <button onClick={saveSettings} className="btn-save" disabled={saving}>
          {saving ? '⏳ Salvando...' : '💾 Salvar Configurações'}
        </button>
      </div>

      <style jsx>{`
        .whatsapp-settings {
          background: white;
          border-radius: 12px;
          max-width: 800px;
          margin: 0 auto;
          box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        }

        .settings-header {
          padding: 20px;
          border-bottom: 1px solid #e0e0e0;
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .settings-header h2 {
          margin: 0;
          font-size: 20px;
          font-weight: 600;
        }

        .close-btn {
          background: none;
          border: none;
          font-size: 24px;
          cursor: pointer;
          color: #666;
        }

        .close-btn:hover {
          color: #333;
        }

        .settings-tabs {
          display: flex;
          border-bottom: 1px solid #e0e0e0;
          padding: 0 20px;
        }

        .tab {
          padding: 15px 20px;
          border: none;
          background: none;
          cursor: pointer;
          font-size: 14px;
          font-weight: 500;
          color: #666;
          border-bottom: 3px solid transparent;
          transition: all 0.2s;
        }

        .tab:hover {
          color: #333;
        }

        .tab.active {
          color: #25d366;
          border-bottom-color: #25d366;
        }

        .settings-content {
          padding: 20px;
          max-height: 500px;
          overflow-y: auto;
        }

        .settings-section h3 {
          margin-top: 0;
          margin-bottom: 10px;
          font-size: 18px;
        }

        .section-description {
          color: #666;
          font-size: 14px;
          margin-bottom: 20px;
        }

        .setting-item {
          margin-bottom: 20px;
        }

        .setting-item label {
          display: block;
          margin-bottom: 8px;
          font-weight: 500;
          font-size: 14px;
        }

        .setting-label {
          display: flex !important;
          align-items: center;
          gap: 10px;
          cursor: pointer;
        }

        .setting-label input[type="checkbox"] {
          width: 20px;
          height: 20px;
          cursor: pointer;
        }

        .setting-description {
          font-size: 13px;
          color: #666;
          margin-top: 5px;
          margin-left: 30px;
        }

        .setting-input {
          width: 100%;
          padding: 10px 12px;
          border: 1px solid #e0e0e0;
          border-radius: 6px;
          font-size: 14px;
        }

        .setting-input:focus {
          outline: none;
          border-color: #25d366;
        }

        .events-grid {
          display: grid;
          grid-template-columns: repeat(2, 1fr);
          gap: 10px;
          margin-top: 10px;
        }

        .event-checkbox {
          display: flex !important;
          align-items: center;
          gap: 8px;
          padding: 8px;
          border: 1px solid #e0e0e0;
          border-radius: 6px;
          cursor: pointer;
        }

        .event-checkbox:hover {
          background: #f5f5f5;
        }

        .event-checkbox input {
          cursor: pointer;
        }

        .settings-footer {
          padding: 20px;
          border-top: 1px solid #e0e0e0;
          display: flex;
          justify-content: flex-end;
          gap: 10px;
        }

        .btn-cancel, .btn-save {
          padding: 10px 20px;
          border: none;
          border-radius: 6px;
          font-size: 14px;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.2s;
        }

        .btn-cancel {
          background: #f5f5f5;
          color: #333;
        }

        .btn-cancel:hover {
          background: #e0e0e0;
        }

        .btn-save {
          background: #25d366;
          color: white;
        }

        .btn-save:hover:not(:disabled) {
          background: #20ba5a;
        }

        .btn-save:disabled {
          background: #ccc;
          cursor: not-allowed;
        }

        .settings-loading {
          padding: 40px;
          text-align: center;
          color: #666;
        }
      `}</style>
    </div>
  );
};

export default WhatsAppSettings;
