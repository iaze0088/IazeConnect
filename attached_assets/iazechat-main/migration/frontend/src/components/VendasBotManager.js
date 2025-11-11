import React, { useState, useEffect } from 'react';
import { Save, MessageSquare, Sparkles, Bot } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';

function VendasBotManager() {
  const [config, setConfig] = useState({
    empresa_nome: 'CyberTV',
    usa_ia: true,
    api_teste_url: 'https://gesth.io/api/get-teste?hash=TG1OTW5QWHlaTW5Q',
    agent_id: null,
    custom_instructions: ''
  });
  const [agents, setAgents] = useState([]);
  const [isSaving, setIsSaving] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadConfig();
    loadAgents();
  }, []);

  const loadConfig = async () => {
    try {
      setIsLoading(true);
      const response = await fetch(`${BACKEND_URL}/api/admin/vendas-bot/simple-config`);
      if (response.ok) {
        const data = await response.json();
        if (data.config_id) {
          setConfig(data);
        }
      }
    } catch (error) {
      console.error('Erro ao carregar config:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const loadAgents = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/ai/agents`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setAgents(Array.isArray(data) ? data : []);
      }
    } catch (error) {
      console.error('Erro ao carregar agentes:', error);
    }
  };

  const saveConfig = async () => {
    try {
      setIsSaving(true);
      
      const response = await fetch(`${BACKEND_URL}/api/admin/vendas-bot/simple-config`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
      });

      if (!response.ok) throw new Error('Erro ao salvar');

      alert('✅ Configuração salva com sucesso!');
      await loadConfig();
    } catch (error) {
      console.error('Erro ao salvar:', error);
      alert('❌ Erro ao salvar configuração');
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Carregando...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <MessageSquare className="text-blue-600" size={24} />
          <div>
            <h2 className="text-2xl font-bold">WA Site - Configuração</h2>
            <p className="text-sm text-gray-600">Configure o chat de vendas do seu site</p>
          </div>
        </div>
        <button
          onClick={saveConfig}
          disabled={isSaving}
          className="flex items-center gap-2 bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 disabled:opacity-50"
        >
          <Save size={18} />
          {isSaving ? 'Salvando...' : 'Salvar'}
        </button>
      </div>

      {/* Configurações Básicas */}
      <div className="bg-white rounded-lg shadow p-6 space-y-4">
        <h3 className="text-lg font-semibold flex items-center gap-2">
          <Sparkles className="text-yellow-500" size={20} />
          Configuração Simples
        </h3>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Nome da Empresa
          </label>
          <input
            type="text"
            value={config.empresa_nome}
            onChange={(e) => setConfig({...config, empresa_nome: e.target.value})}
            className="w-full border border-gray-300 rounded-lg p-3 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="Ex: CyberTV"
          />
          <p className="text-sm text-gray-500 mt-1">
            Nome que aparecerá no cabeçalho do chat
          </p>
        </div>

        <div>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={config.usa_ia}
              onChange={(e) => setConfig({...config, usa_ia: e.target.checked})}
              className="rounded text-blue-600 h-5 w-5"
            />
            <span className="text-sm font-medium text-gray-700">
              Usar IA para responder automaticamente
            </span>
          </label>
          <p className="text-sm text-gray-500 mt-1 ml-7">
            A IA irá responder os clientes e enviar o botão de teste quando apropriado
          </p>
        </div>

        {config.usa_ia && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
              <Bot size={18} className="text-blue-600" />
              Agente IA para WA Site
            </label>
            <select
              value={config.agent_id || ''}
              onChange={(e) => setConfig({...config, agent_id: e.target.value || null})}
              className="w-full border border-gray-300 rounded-lg p-3 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">Selecione um Agente IA</option>
              {agents.map(agent => (
                <option key={agent.id} value={agent.id}>
                  {agent.name}
                </option>
              ))}
            </select>
            <p className="text-sm text-gray-500 mt-1">
              📌 Crie um agente específico para WA Site na aba "Agentes IA"
            </p>
            {!config.agent_id && (
              <div className="mt-2 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                <p className="text-sm text-yellow-800">
                  ⚠️ <strong>Importante:</strong> Crie um Agente IA dedicado para o WA Site na aba "Agentes IA" com instruções específicas para vendas.
                </p>
              </div>
            )}
          </div>
        )}

        {/* Instruções Customizadas */}
        {config.usa_ia && !config.agent_id && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              📝 Instruções para a IA (Opcional)
            </label>
            <textarea
              value={config.custom_instructions || ''}
              onChange={(e) => setConfig({...config, custom_instructions: e.target.value})}
              className="w-full border border-gray-300 rounded-lg p-3 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              rows="6"
              placeholder="Digite as instruções para a IA responder os clientes...&#10;&#10;Exemplo:&#10;- Seja amigável e profissional&#10;- Ofereça teste grátis de 3 horas&#10;- Pergunte o nome do cliente&#10;- Explique os benefícios do serviço IPTV"
            />
            <p className="text-sm text-gray-500 mt-1">
              💡 Use este campo se não tiver criado um Agente IA. As instruções guiarão como a IA deve responder.
            </p>
          </div>
        )}

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            API de Teste IPTV
          </label>
          <input
            type="text"
            value={config.api_teste_url}
            onChange={(e) => setConfig({...config, api_teste_url: e.target.value})}
            className="w-full border border-gray-300 rounded-lg p-3 focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono text-sm"
            placeholder="https://..."
          />
          <p className="text-sm text-gray-500 mt-1">
            URL da API que gera os testes IPTV
          </p>
        </div>
      </div>

      {/* Como Funciona */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-blue-900 mb-3">
          ℹ️ Como Funciona
        </h3>
        <ol className="space-y-2 text-sm text-blue-800">
          <li>1. Cliente acessa <code className="bg-blue-200 px-2 py-1 rounded">/vendas</code> no seu site</li>
          <li>2. Cliente digita <strong>"12"</strong> → Abre modal para WhatsApp + PIN</li>
          <li>3. Sistema salva dados e mostra link do app <strong>WA Vendas</strong></li>
          <li>4. IA responde e oferece teste grátis quando apropriado</li>
          <li>5. Cliente clica no botão <strong>"CRIAR TESTE GRÁTIS"</strong></li>
          <li>6. Sistema gera teste via API e envia credenciais (3 horas)</li>
        </ol>
      </div>

      {/* Creditos da IA */}
      <div className="bg-purple-50 border border-purple-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-purple-900 mb-3">
          💰 Créditos da IA (Universal Key)
        </h3>
        <p className="text-sm text-purple-800 mb-3">
          Para ver seu saldo e adicionar créditos:
        </p>
        <ol className="space-y-2 text-sm text-purple-800 ml-4">
          <li>1. Saia do Admin Dashboard</li>
          <li>2. Volte para a tela principal da <strong>Plataforma Emergent</strong></li>
          <li>3. No menu ou perfil, procure <strong>"Universal Key"</strong></li>
          <li>4. Lá você verá: Saldo atual + Botão "Add Balance"</li>
        </ol>
        <div className="mt-3 p-3 bg-purple-100 rounded-lg">
          <p className="text-sm text-purple-900">
            <strong>💡 Dica:</strong> Ative o "Auto Top-Up" para nunca ficar sem crédito!
          </p>
        </div>
      </div>

      {/* Preview */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">
          👁️ Preview do Link
        </h3>
        <div className="bg-gray-100 rounded-lg p-4">
          <p className="text-sm font-medium text-gray-700 mb-2">
            Link para anúncios / redes sociais:
          </p>
          <code className="bg-white px-4 py-2 rounded border border-gray-300 block text-center text-blue-600 font-semibold">
            {window.location.origin}/vendas
          </code>
          <p className="text-xs text-gray-500 mt-2 text-center">
            Cole este link nos seus anúncios do Facebook, Instagram, etc.
          </p>
        </div>
      </div>
    </div>
  );
}

export default VendasBotManager;
