import React, { useState, useEffect } from 'react';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { AlertCircle, CheckCircle, CreditCard, Eye, EyeOff } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';

const MercadoPagoConfig = () => {
  const [config, setConfig] = useState({
    access_token: '',
    public_key: '',
    webhook_secret: '',
    enabled: true
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [showAccessToken, setShowAccessToken] = useState(false);
  const [showPublicKey, setShowPublicKey] = useState(false);
  const [message, setMessage] = useState(null);

  useEffect(() => {
    fetchConfig();
  }, []);

  const fetchConfig = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/admin/mercado-pago/config`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        if (data.config) {
          setConfig(data.config);
        }
      }
    } catch (error) {
      console.error('Error fetching config:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    setMessage(null);

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/admin/mercado-pago/config`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(config)
      });

      if (response.ok) {
        setMessage({ type: 'success', text: 'Configurações salvas com sucesso!' });
      } else {
        const error = await response.json();
        setMessage({ type: 'error', text: error.detail || 'Erro ao salvar configurações' });
      }
    } catch (error) {
      console.error('Error saving config:', error);
      setMessage({ type: 'error', text: 'Erro ao salvar configurações' });
    } finally {
      setSaving(false);
    }
  };

  const handleTestConnection = async () => {
    if (!config.access_token) {
      setMessage({ type: 'error', text: 'Preencha o Access Token primeiro' });
      return;
    }

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/admin/mercado-pago/test`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ access_token: config.access_token })
      });

      if (response.ok) {
        const data = await response.json();
        setMessage({ 
          type: 'success', 
          text: `Conexão OK! Conta: ${data.account_info?.email || 'Verificada'}` 
        });
      } else {
        setMessage({ type: 'error', text: 'Erro ao testar conexão. Verifique o Access Token.' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Erro ao testar conexão' });
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card className="p-6 bg-gradient-to-r from-blue-600 to-cyan-600 text-white">
        <div className="flex items-center gap-4">
          <div className="w-16 h-16 rounded-full bg-white/20 flex items-center justify-center">
            <CreditCard className="w-8 h-8" />
          </div>
          <div>
            <h2 className="text-2xl font-bold mb-1">Configurações Mercado Pago</h2>
            <p className="text-blue-100">
              Configure suas credenciais para receber pagamentos via PIX
            </p>
          </div>
        </div>
      </Card>

      {/* Message */}
      {message && (
        <Card className={`p-4 ${message.type === 'success' ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'}`}>
          <div className="flex items-center gap-3">
            {message.type === 'success' ? (
              <CheckCircle className="w-5 h-5 text-green-600" />
            ) : (
              <AlertCircle className="w-5 h-5 text-red-600" />
            )}
            <p className={message.type === 'success' ? 'text-green-800' : 'text-red-800'}>
              {message.text}
            </p>
          </div>
        </Card>
      )}

      {/* Instruções */}
      <Card className="p-6 bg-yellow-50 border-yellow-200">
        <h3 className="font-bold text-lg mb-3 flex items-center gap-2 text-yellow-900">
          <AlertCircle className="w-5 h-5" />
          Como obter suas credenciais
        </h3>
        <ol className="space-y-2 text-sm text-yellow-800">
          <li><strong>1.</strong> Acesse: <a href="https://www.mercadopago.com.br/developers/panel/app" target="_blank" rel="noopener noreferrer" className="underline font-bold">Painel do Mercado Pago</a></li>
          <li><strong>2.</strong> Faça login com sua conta</li>
          <li><strong>3.</strong> Vá em "Suas integrações" → "Criar aplicação"</li>
          <li><strong>4.</strong> Escolha "Pagamentos online"</li>
          <li><strong>5.</strong> Copie o <strong>Access Token</strong> e <strong>Public Key</strong></li>
          <li><strong>6.</strong> Cole abaixo e clique em "Salvar"</li>
        </ol>
      </Card>

      {/* Formulário */}
      <Card className="p-6">
        <div className="space-y-6">
          {/* Access Token */}
          <div>
            <Label className="text-base font-semibold mb-2 block">
              Access Token (Credencial Secreta)
            </Label>
            <p className="text-sm text-gray-600 mb-3">
              Token privado usado para criar pagamentos. Mantenha em segredo!
            </p>
            <div className="relative">
              <Input
                type={showAccessToken ? "text" : "password"}
                value={config.access_token}
                onChange={(e) => setConfig({ ...config, access_token: e.target.value })}
                placeholder="APP_USR-1234567890123456-012345-abcdef1234567890abcdef1234567890-123456789"
                className="pr-10 font-mono text-sm"
              />
              <button
                type="button"
                onClick={() => setShowAccessToken(!showAccessToken)}
                className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-500 hover:text-gray-700"
              >
                {showAccessToken ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>

          {/* Public Key */}
          <div>
            <Label className="text-base font-semibold mb-2 block">
              Public Key (Chave Pública)
            </Label>
            <p className="text-sm text-gray-600 mb-3">
              Chave pública usada no frontend. Pode ser compartilhada.
            </p>
            <div className="relative">
              <Input
                type={showPublicKey ? "text" : "password"}
                value={config.public_key}
                onChange={(e) => setConfig({ ...config, public_key: e.target.value })}
                placeholder="APP_USR-abcdef12-3456-7890-abcd-ef1234567890"
                className="pr-10 font-mono text-sm"
              />
              <button
                type="button"
                onClick={() => setShowPublicKey(!showPublicKey)}
                className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-500 hover:text-gray-700"
              >
                {showPublicKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>

          {/* Webhook Secret (Opcional) */}
          <div>
            <Label className="text-base font-semibold mb-2 block">
              Webhook Secret (Opcional)
            </Label>
            <p className="text-sm text-gray-600 mb-3">
              Para validar webhooks. Deixe em branco se não souber.
            </p>
            <Input
              type="text"
              value={config.webhook_secret}
              onChange={(e) => setConfig({ ...config, webhook_secret: e.target.value })}
              placeholder="seu-secret-aqui (opcional)"
              className="font-mono text-sm"
            />
          </div>

          {/* Enabled */}
          <div className="flex items-center gap-3">
            <input
              type="checkbox"
              id="enabled"
              checked={config.enabled}
              onChange={(e) => setConfig({ ...config, enabled: e.target.checked })}
              className="w-5 h-5 text-blue-600"
            />
            <Label htmlFor="enabled" className="text-base font-medium cursor-pointer">
              Habilitar pagamentos Mercado Pago
            </Label>
          </div>

          {/* Botões */}
          <div className="flex gap-3 pt-4">
            <Button
              onClick={handleSave}
              disabled={saving || !config.access_token || !config.public_key}
              className="flex-1 bg-blue-600 hover:bg-blue-700"
            >
              {saving ? (
                <span className="flex items-center gap-2">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  Salvando...
                </span>
              ) : (
                'Salvar Configurações'
              )}
            </Button>

            <Button
              onClick={handleTestConnection}
              disabled={!config.access_token}
              variant="outline"
              className="px-6"
            >
              Testar Conexão
            </Button>
          </div>
        </div>
      </Card>

      {/* Info Adicional */}
      <Card className="p-4 bg-blue-50 border-blue-200">
        <p className="text-sm text-blue-800">
          <strong>💡 Dica:</strong> Todas as revendas farão pagamentos que cairão na SUA conta do Mercado Pago.
          O sistema de bônus é gerenciado internamente e não afeta os valores recebidos.
        </p>
      </Card>
    </div>
  );
};

export default MercadoPagoConfig;
