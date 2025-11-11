import React, { useState, useEffect } from 'react';
import { 
  Save, MessageSquare, Sparkles, Bot, Settings, 
  Key, Database, FileText, Image as ImageIcon,
  Globe, Zap, AlertCircle, CheckCircle, Code,
  Upload, Download, Trash2, Eye, EyeOff
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';

/**
 * WA SITE MANAGER V2 - COMPLETO E ROBUSTO
 * 
 * TUDO centralizado em um único lugar:
 * - Instruções da IA
 * - Base de Conhecimento
 * - API Keys
 * - Configurações de Modelo
 * - Personalização Visual
 * - APIs Externas
 * - Testes e Validação
 */

function VendasBotManagerV2() {
  const [activeTab, setActiveTab] = useState('instructions'); // instructions, knowledge, settings, api, visual, testing
  const [config, setConfig] = useState({
    // Configurações Básicas
    empresa_nome: 'CyberTV',
    usa_ia: true,
    is_active: true,
    operation_mode: 'ia', // Modos: 'ia', 'button', 'hybrid'
    
    // IA - Configuração Completa
    ia_config: {
      // Identidade
      name: 'Juliana',
      role: 'Consultora de Vendas',
      personality: 'Profissional, amigável e prestativa',
      
      // Instruções Principais
      instructions: `Você é Juliana, consultora de vendas especializada em IPTV.

**SUAS RESPONSABILIDADES:**
1. Atender clientes com cordialidade
2. Responder dúvidas sobre produtos IPTV
3. Gerar testes gratuitos quando solicitado
4. Transferir para humano quando necessário

**REGRAS IMPORTANTES:**
- Seja sempre educada e profissional
- Responda de forma clara e objetiva
- Uma pergunta por vez
- Se não souber, seja honesta

**PRODUTOS:**
- Plano Básico: R$ 29,90/mês
- Plano Premium: R$ 49,90/mês
- Plano VIP: R$ 79,90/mês`,
      
      // Base de Conhecimento
      knowledge_base: {
        enabled: true,
        sources: [
          {
            type: 'url',
            url: 'https://site.suporte.help/base-conhecimento.html',
            description: 'Base principal de conhecimento'
          }
        ],
        fallback_text: 'Informações adicionais sobre produtos e serviços'
      },
      
      // Modelo LLM
      llm_provider: 'openai', // openai, anthropic, google
      llm_model: 'gpt-4o-mini',
      temperature: 0.7,
      max_tokens: 500,
      top_p: 1.0,
      
      // API Key (específica desta revenda)
      api_key: '',
      use_system_key: true, // Usar chave do sistema ou própria
      
      // Comportamento
      auto_transfer_keywords: ['humano', 'atendente', 'pessoa', 'falar com alguém'],
      greeting_message: 'Olá! Sou a Juliana, como posso ajudar você hoje?',
      fallback_message: 'Desculpe, não entendi. Pode reformular?',
      transfer_message: 'Vou transferir você para um atendente humano. Aguarde...',
      
      // Memória
      conversation_history_limit: 10, // Últimas N mensagens
      remember_context: true
    },
    
    // Visual - Aparência do Chat
    visual_config: {
      agent_photo: '',
      agent_name_display: 'Juliana Silva',
      show_verified_badge: true,
      theme_color: '#0084ff',
      background_image: '',
      welcome_banner: '',
      chat_position: 'bottom-right', // bottom-right, bottom-left, fullscreen
      chat_size: 'medium', // small, medium, large
    },
    
    // APIs Externas
    external_apis: {
      // API de Teste IPTV
      teste_iptv: {
        enabled: true,
        url: 'https://gesth.io/api/get-teste?hash=TG1OTW5QWHlaTW5Q',
        method: 'GET',
        headers: {},
        trigger_keywords: ['teste', 'testar', 'teste grátis']
      },
      
      // API de Consulta de Créditos
      consulta_credito: {
        enabled: false,
        url: '',
        method: 'POST',
        headers: {},
        trigger_keywords: ['crédito', 'saldo', 'consultar']
      }
    },
    
    // Regras e Fluxos
    flows: {
      // Fluxo de Teste Grátis
      teste_gratis: {
        enabled: true,
        require_app_install: true,
        app_url: 'https://suporte.help',
        steps: [
          'Confirmar interesse',
          'Solicitar WhatsApp',
          'Gerar credenciais',
          'Enviar instruções'
        ]
      },
      
      // Fluxo de Vendas
      vendas: {
        enabled: true,
        collect_data: ['nome', 'whatsapp', 'interesse'],
        payment_methods: ['Pix', 'Cartão']
      }
    },
    
    // Integrações
    integrations: {
      whatsapp: {
        enabled: true,
        instance_name: ''
      },
      email: {
        enabled: false,
        smtp_config: {}
      },
      webhook: {
        enabled: false,
        url: '',
        events: []
      }
    },
    
    // Analytics e Logs
    analytics: {
      track_conversations: true,
      track_conversions: true,
      track_user_satisfaction: false
    }
  });

  const [isSaving, setIsSaving] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [testMode, setTestMode] = useState(false);
  const [showApiKey, setShowApiKey] = useState(false);
  const [importExportMode, setImportExportMode] = useState(null);

  useEffect(() => {
    loadConfig();
  }, []);

  const loadConfig = async () => {
    try {
      setIsLoading(true);
      const response = await fetch(`${BACKEND_URL}/api/admin/vendas-bot/simple-config`);
      if (response.ok) {
        const data = await response.json();
        
        // 🔧 DECODIFICAR status de empresa_nome (bypass gateway)
        if (data.empresa_nome && data.empresa_nome.includes('|S:')) {
          const [nome, statusStr] = data.empresa_nome.split('|S:');
          data.empresa_nome = nome;
          data.status = parseInt(statusStr);
          console.log('✅ Status decodificado:', data.status);
        }
        
        // Merge com estrutura padrão
        setConfig(prev => ({
          ...prev,
          ...data,
          ia_config: { ...prev.ia_config, ...(data.ia_inline || data.ia_config || {}) },
          visual_config: { ...prev.visual_config, ...(data.visual_config || data.agent_profile || {}) },
          external_apis: { ...prev.external_apis, ...(data.external_apis || {}) }
        }));
      }
    } catch (error) {
      console.error('Erro ao carregar config:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const saveConfig = async (configToSave = null) => {
    try {
      setIsSaving(true);
      
      const dataToSave = configToSave || config;
      
      const response = await fetch(`${BACKEND_URL}/api/admin/vendas-bot/simple-config`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(dataToSave)
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

  const exportConfig = () => {
    const dataStr = JSON.stringify(config, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
    const exportFileDefaultName = `wa-site-config-${Date.now()}.json`;
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
  };

  const importConfig = (event) => {
    const file = event.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const imported = JSON.parse(e.target.result);
          setConfig(imported);
          alert('✅ Configuração importada! Clique em Salvar para aplicar.');
        } catch (error) {
          alert('❌ Erro ao importar: arquivo inválido');
        }
      };
      reader.readAsText(file);
    }
  };

  const testIA = async () => {
    try {
      setTestMode(true);
      const response = await fetch(`${BACKEND_URL}/api/vendas/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: 'Teste', whatsapp: '5511999999999' })
      });
      const data = await response.json();
      alert(`✅ Teste OK! Resposta: ${data.messages[0]?.text || 'Sem resposta'}`);
    } catch (error) {
      alert('❌ Erro no teste: ' + error.message);
    } finally {
      setTestMode(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Carregando configuração...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="bg-blue-100 p-3 rounded-lg">
              <MessageSquare className="text-blue-600" size={24} />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-gray-900">WA Site - Configuração Completa</h2>
              <p className="text-sm text-gray-600">Todas as configurações do seu chat de vendas em um só lugar</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={exportConfig}
              className="flex items-center gap-2 bg-gray-100 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-200"
            >
              <Download size={18} />
              Exportar
            </button>
            <label className="flex items-center gap-2 bg-gray-100 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-200 cursor-pointer">
              <Upload size={18} />
              Importar
              <input type="file" accept=".json" onChange={importConfig} className="hidden" />
            </label>
            <button
              onClick={testIA}
              disabled={testMode}
              className="flex items-center gap-2 bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 disabled:opacity-50"
            >
              <Zap size={18} />
              {testMode ? 'Testando...' : 'Testar IA'}
            </button>
            <button
              onClick={saveConfig}
              disabled={isSaving}
              className="flex items-center gap-2 bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 disabled:opacity-50"
            >
              <Save size={18} />
              {isSaving ? 'Salvando...' : 'Salvar Tudo'}
            </button>
          </div>
        </div>

        {/* Status Indicators */}
        <div className="mt-4 flex items-center gap-4">
          <div className={`flex items-center gap-2 px-3 py-1 rounded-full ${config.usa_ia ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-700'}`}>
            {config.usa_ia ? <CheckCircle size={16} /> : <AlertCircle size={16} />}
            <span className="text-sm font-medium">IA {config.usa_ia ? 'Ativada' : 'Desativada'}</span>
          </div>
          <div className={`flex items-center gap-2 px-3 py-1 rounded-full ${config.ia_config?.api_key || config.ia_config?.use_system_key ? 'bg-blue-100 text-blue-700' : 'bg-yellow-100 text-yellow-700'}`}>
            <Key size={16} />
            <span className="text-sm font-medium">
              {config.ia_config?.use_system_key ? 'Chave do Sistema' : config.ia_config?.api_key ? 'Chave Própria' : 'Sem API Key'}
            </span>
          </div>
          <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-purple-100 text-purple-700">
            <Bot size={16} />
            <span className="text-sm font-medium">{config.ia_config?.llm_model || 'gpt-4o-mini'}</span>
          </div>
        </div>

        {/* Modo de Operação Toggle */}
        <div className="mt-6 p-4 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg border border-blue-200">
          <h4 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
            <Zap size={16} className="text-blue-600" />
            Modo de Operação do WA Site
          </h4>
          <div className="grid grid-cols-3 gap-3">
            <button
              onClick={async () => {
                const newConfig = { ...config, status: 2, usa_ia: true };
                setConfig(newConfig);
                await saveConfig(newConfig);
              }}
              className={`p-3 rounded-lg border-2 transition-all ${
                config.status === 2
                  ? 'border-blue-600 bg-blue-100 text-blue-800' 
                  : 'border-gray-200 bg-white text-gray-600 hover:border-blue-300'
              }`}
            >
              <div className="text-center">
                <Bot size={24} className="mx-auto mb-1" />
                <p className="text-xs font-semibold">ATIVO IA</p>
                <p className="text-[10px] text-gray-500 mt-1">Apenas IA responde</p>
              </div>
            </button>
            <button
              onClick={async () => {
                const newConfig = { ...config, status: 1, usa_ia: false };
                setConfig(newConfig);
                await saveConfig(newConfig);
              }}
              className={`p-3 rounded-lg border-2 transition-all ${
                config.status === 1
                  ? 'border-purple-600 bg-purple-100 text-purple-800' 
                  : 'border-gray-200 bg-white text-gray-600 hover:border-purple-300'
              }`}
            >
              <div className="text-center">
                <span className="text-2xl">🎯</span>
                <p className="text-xs font-semibold mt-1">ATIVO BOTÃO</p>
                <p className="text-[10px] text-gray-500 mt-1">Apenas botões</p>
              </div>
            </button>
            <button
              onClick={async () => {
                const newConfig = { ...config, status: 3, usa_ia: true };
                setConfig(newConfig);
                await saveConfig(newConfig);
              }}
              className={`p-3 rounded-lg border-2 transition-all ${
                config.status === 3
                  ? 'border-green-600 bg-green-100 text-green-800' 
                  : 'border-gray-200 bg-white text-gray-600 hover:border-green-300'
              }`}
            >
              <div className="text-center">
                <div className="flex justify-center gap-1 mb-1">
                  <Bot size={20} />
                  <span className="text-lg">🎯</span>
                </div>
                <p className="text-xs font-semibold">ATIVO HÍBRIDO</p>
                <p className="text-[10px] text-gray-500 mt-1">Botões + IA</p>
              </div>
            </button>
          </div>
          <p className="text-xs text-gray-600 mt-3 text-center">
            {config.status === 2 && '🤖 IA responde automaticamente todas as mensagens'}
            {config.status === 1 && '🎯 Clientes usam apenas botões interativos'}
            {config.status === 3 && '🔀 Combina botões interativos com respostas da IA'}
          </p>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="bg-white rounded-lg shadow-sm">
        <div className="border-b border-gray-200">
          <nav className="flex -mb-px">
            {[
              { id: 'instructions', label: 'Instruções & Personalidade', icon: FileText },
              { id: 'knowledge', label: 'Base de Conhecimento', icon: Database },
              { id: 'settings', label: 'Modelo & Comportamento', icon: Settings },
              { id: 'api', label: 'API Keys & Integrações', icon: Key },
              { id: 'visual', label: 'Aparência Visual', icon: ImageIcon },
              { id: 'flows', label: 'Fluxos & Regras', icon: Zap }
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`
                  flex items-center gap-2 px-6 py-4 text-sm font-medium border-b-2 transition-colors
                  ${activeTab === tab.id 
                    ? 'border-blue-600 text-blue-600' 
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }
                `}
              >
                <tab.icon size={18} />
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        {/* Tab Content */}
        <div className="p-6">
          {/* ABA 1: INSTRUÇÕES & PERSONALIDADE */}
          {activeTab === 'instructions' && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Nome da IA */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Nome da IA
                  </label>
                  <input
                    type="text"
                    value={config.ia_config?.name || ''}
                    onChange={(e) => setConfig({
                      ...config,
                      ia_config: { ...config.ia_config, name: e.target.value }
                    })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="Ex: Juliana"
                  />
                </div>

                {/* Cargo/Função */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Cargo/Função
                  </label>
                  <input
                    type="text"
                    value={config.ia_config?.role || ''}
                    onChange={(e) => setConfig({
                      ...config,
                      ia_config: { ...config.ia_config, role: e.target.value }
                    })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="Ex: Consultora de Vendas"
                  />
                </div>
              </div>

              {/* Personalidade */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Personalidade
                </label>
                <input
                  type="text"
                  value={config.ia_config?.personality || ''}
                  onChange={(e) => setConfig({
                    ...config,
                    ia_config: { ...config.ia_config, personality: e.target.value }
                  })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  placeholder="Ex: Profissional, amigável e prestativa"
                />
              </div>

              {/* Instruções Principais */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Instruções Completas da IA
                  <span className="text-gray-500 font-normal ml-2">(O coração do seu assistente)</span>
                </label>
                <textarea
                  value={config.ia_config?.instructions || ''}
                  onChange={(e) => setConfig({
                    ...config,
                    ia_config: { ...config.ia_config, instructions: e.target.value }
                  })}
                  rows={20}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 font-mono text-sm"
                  placeholder="Digite as instruções completas aqui...&#10;&#10;Exemplo:&#10;Você é [Nome], especialista em [Área].&#10;&#10;**SUAS RESPONSABILIDADES:**&#10;- Atender clientes&#10;- Responder dúvidas&#10;- Gerar leads&#10;&#10;**REGRAS:**&#10;- Seja sempre educado&#10;- Responda de forma clara"
                />
                <p className="mt-2 text-sm text-gray-500">
                  💡 Dica: Seja específico! Quanto mais detalhado, melhor a IA vai performar.
                </p>
              </div>

              {/* Mensagens Padrão */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Mensagem de Boas-Vindas
                  </label>
                  <textarea
                    value={config.ia_config?.greeting_message || ''}
                    onChange={(e) => setConfig({
                      ...config,
                      ia_config: { ...config.ia_config, greeting_message: e.target.value }
                    })}
                    rows={3}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-sm"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Mensagem de Fallback
                  </label>
                  <textarea
                    value={config.ia_config?.fallback_message || ''}
                    onChange={(e) => setConfig({
                      ...config,
                      ia_config: { ...config.ia_config, fallback_message: e.target.value }
                    })}
                    rows={3}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-sm"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Mensagem de Transferência
                  </label>
                  <textarea
                    value={config.ia_config?.transfer_message || ''}
                    onChange={(e) => setConfig({
                      ...config,
                      ia_config: { ...config.ia_config, transfer_message: e.target.value }
                    })}
                    rows={3}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-sm"
                  />
                </div>
              </div>
            </div>
          )}

          {/* ABA 2: BASE DE CONHECIMENTO */}
          {activeTab === 'knowledge' && (
            <div className="space-y-6">
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex items-start gap-3">
                  <Database className="text-blue-600 flex-shrink-0 mt-0.5" size={20} />
                  <div>
                    <h3 className="font-medium text-blue-900">Sobre a Base de Conhecimento</h3>
                    <p className="text-sm text-blue-700 mt-1">
                      A IA vai buscar informações automaticamente dessas fontes para complementar suas respostas.
                      Pode ser uma URL, arquivo ou texto direto.
                    </p>
                  </div>
                </div>
              </div>

              {/* Ativar/Desativar */}
              <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div>
                  <h3 className="font-medium text-gray-900">Ativar Base de Conhecimento</h3>
                  <p className="text-sm text-gray-600">A IA vai buscar informações das fontes configuradas</p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={config.ia_config?.knowledge_base?.enabled || false}
                    onChange={(e) => setConfig({
                      ...config,
                      ia_config: {
                        ...config.ia_config,
                        knowledge_base: {
                          ...config.ia_config?.knowledge_base,
                          enabled: e.target.checked
                        }
                      }
                    })}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                </label>
              </div>

              {/* Fontes de Conhecimento */}
              {config.ia_config?.knowledge_base?.enabled && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      URL da Base de Conhecimento
                    </label>
                    <input
                      type="url"
                      value={config.ia_config?.knowledge_base?.sources?.[0]?.url || ''}
                      onChange={(e) => {
                        const sources = config.ia_config?.knowledge_base?.sources || [{}];
                        sources[0] = { ...sources[0], url: e.target.value, type: 'url' };
                        setConfig({
                          ...config,
                          ia_config: {
                            ...config.ia_config,
                            knowledge_base: {
                              ...config.ia_config?.knowledge_base,
                              sources
                            }
                          }
                        });
                      }}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                      placeholder="https://site.suporte.help/base-conhecimento.html"
                    />
                    <p className="mt-2 text-sm text-gray-500">
                      💡 A IA vai acessar essa URL automaticamente para buscar informações
                    </p>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Descrição da Fonte
                    </label>
                    <input
                      type="text"
                      value={config.ia_config?.knowledge_base?.sources?.[0]?.description || ''}
                      onChange={(e) => {
                        const sources = config.ia_config?.knowledge_base?.sources || [{}];
                        sources[0] = { ...sources[0], description: e.target.value };
                        setConfig({
                          ...config,
                          ia_config: {
                            ...config.ia_config,
                            knowledge_base: {
                              ...config.ia_config?.knowledge_base,
                              sources
                            }
                          }
                        });
                      }}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                      placeholder="Ex: Base principal de conhecimento sobre produtos IPTV"
                    />
                  </div>

                  {/* Texto Fallback */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Texto Adicional (Fallback)
                    </label>
                    <textarea
                      value={config.ia_config?.knowledge_base?.fallback_text || ''}
                      onChange={(e) => setConfig({
                        ...config,
                        ia_config: {
                          ...config.ia_config,
                          knowledge_base: {
                            ...config.ia_config?.knowledge_base,
                            fallback_text: e.target.value
                          }
                        }
                      })}
                      rows={8}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                      placeholder="Informações adicionais que a IA pode usar caso a URL não esteja acessível..."
                    />
                    <p className="mt-2 text-sm text-gray-500">
                      💡 Este texto será usado se a URL não estiver disponível
                    </p>
                  </div>
                </>
              )}
            </div>
          )}

          {/* ABA 3: MODELO & COMPORTAMENTO */}
          {activeTab === 'settings' && (
            <div className="space-y-6">
              {/* Modelo LLM */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Provedor LLM
                  </label>
                  <select
                    value={config.ia_config?.llm_provider || 'openai'}
                    onChange={(e) => setConfig({
                      ...config,
                      ia_config: { ...config.ia_config, llm_provider: e.target.value }
                    })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="openai">OpenAI</option>
                    <option value="anthropic">Anthropic (Claude)</option>
                    <option value="google">Google (Gemini)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Modelo
                  </label>
                  <select
                    value={config.ia_config?.llm_model || 'gpt-4o-mini'}
                    onChange={(e) => setConfig({
                      ...config,
                      ia_config: { ...config.ia_config, llm_model: e.target.value }
                    })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  >
                    {config.ia_config?.llm_provider === 'openai' && (
                      <>
                        <option value="gpt-4o-mini">GPT-4o Mini (Recomendado)</option>
                        <option value="gpt-4o">GPT-4o</option>
                        <option value="gpt-4-turbo">GPT-4 Turbo</option>
                      </>
                    )}
                    {config.ia_config?.llm_provider === 'anthropic' && (
                      <>
                        <option value="claude-3-5-sonnet">Claude 3.5 Sonnet</option>
                        <option value="claude-3-opus">Claude 3 Opus</option>
                      </>
                    )}
                    {config.ia_config?.llm_provider === 'google' && (
                      <>
                        <option value="gemini-2.0-flash-exp">Gemini 2.0 Flash</option>
                        <option value="gemini-1.5-pro">Gemini 1.5 Pro</option>
                      </>
                    )}
                  </select>
                </div>
              </div>

              {/* Parâmetros do Modelo */}
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Temperature: {config.ia_config?.temperature || 0.7}
                    <span className="text-gray-500 font-normal ml-2">(Criatividade)</span>
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.1"
                    value={config.ia_config?.temperature || 0.7}
                    onChange={(e) => setConfig({
                      ...config,
                      ia_config: { ...config.ia_config, temperature: parseFloat(e.target.value) }
                    })}
                    className="w-full"
                  />
                  <div className="flex justify-between text-xs text-gray-500 mt-1">
                    <span>Mais Preciso</span>
                    <span>Mais Criativo</span>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Max Tokens (Tamanho da Resposta)
                  </label>
                  <input
                    type="number"
                    value={config.ia_config?.max_tokens || 500}
                    onChange={(e) => setConfig({
                      ...config,
                      ia_config: { ...config.ia_config, max_tokens: parseInt(e.target.value) }
                    })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              {/* Comportamento */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Palavras-chave para Transferir Humano
                  <span className="text-gray-500 font-normal ml-2">(separadas por vírgula)</span>
                </label>
                <input
                  type="text"
                  value={config.ia_config?.auto_transfer_keywords?.join(', ') || ''}
                  onChange={(e) => setConfig({
                    ...config,
                    ia_config: { 
                      ...config.ia_config, 
                      auto_transfer_keywords: e.target.value.split(',').map(k => k.trim()) 
                    }
                  })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  placeholder="humano, atendente, pessoa, falar com alguém"
                />
              </div>

              {/* Memória */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Limite de Histórico de Conversa
                </label>
                <input
                  type="number"
                  value={config.ia_config?.conversation_history_limit || 10}
                  onChange={(e) => setConfig({
                    ...config,
                    ia_config: { ...config.ia_config, conversation_history_limit: parseInt(e.target.value) }
                  })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
                <p className="mt-2 text-sm text-gray-500">
                  Número de mensagens anteriores que a IA vai lembrar
                </p>
              </div>
            </div>
          )}

          {/* ABA 4: API KEYS & INTEGRAÇÕES */}
          {activeTab === 'api' && (
            <div className="space-y-6">
              {/* API Key Principal */}
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <div className="flex items-start gap-3">
                  <AlertCircle className="text-yellow-600 flex-shrink-0 mt-0.5" size={20} />
                  <div>
                    <h3 className="font-medium text-yellow-900">Importante: API Keys</h3>
                    <p className="text-sm text-yellow-700 mt-1">
                      Você pode usar a chave do sistema (compartilhada) ou configurar sua própria chave para ter controle total dos custos e quotas.
                    </p>
                  </div>
                </div>
              </div>

              {/* Usar Chave do Sistema */}
              <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div>
                  <h3 className="font-medium text-gray-900">Usar Chave do Sistema</h3>
                  <p className="text-sm text-gray-600">Usar a chave compartilhada do sistema (mais fácil)</p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={config.ia_config?.use_system_key !== false}
                    onChange={(e) => setConfig({
                      ...config,
                      ia_config: { ...config.ia_config, use_system_key: e.target.checked }
                    })}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                </label>
              </div>

              {/* API Key Própria */}
              {!config.ia_config?.use_system_key && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Sua API Key {config.ia_config?.llm_provider === 'openai' ? 'OpenAI' : config.ia_config?.llm_provider}
                  </label>
                  <div className="relative">
                    <input
                      type={showApiKey ? "text" : "password"}
                      value={config.ia_config?.api_key || ''}
                      onChange={(e) => setConfig({
                        ...config,
                        ia_config: { ...config.ia_config, api_key: e.target.value }
                      })}
                      className="w-full px-4 py-2 pr-12 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 font-mono"
                      placeholder="sk-proj-..."
                    />
                    <button
                      type="button"
                      onClick={() => setShowApiKey(!showApiKey)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                    >
                      {showApiKey ? <EyeOff size={20} /> : <Eye size={20} />}
                    </button>
                  </div>
                  <p className="mt-2 text-sm text-gray-500">
                    💡 Obtenha sua chave em: {config.ia_config?.llm_provider === 'openai' ? 'platform.openai.com/api-keys' : 'console do provedor'}
                  </p>
                </div>
              )}

              {/* API de Teste IPTV */}
              <div className="border-t pt-6">
                <h3 className="text-lg font-medium text-gray-900 mb-4">APIs Externas</h3>
                
                <div className="space-y-4">
                  <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                    <div>
                      <h4 className="font-medium text-gray-900">API de Teste IPTV</h4>
                      <p className="text-sm text-gray-600">Gerar testes gratuitos automaticamente</p>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        checked={config.external_apis?.teste_iptv?.enabled || false}
                        onChange={(e) => setConfig({
                          ...config,
                          external_apis: {
                            ...config.external_apis,
                            teste_iptv: {
                              ...config.external_apis?.teste_iptv,
                              enabled: e.target.checked
                            }
                          }
                        })}
                        className="sr-only peer"
                      />
                      <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                    </label>
                  </div>

                  {config.external_apis?.teste_iptv?.enabled && (
                    <>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          URL da API
                        </label>
                        <input
                          type="url"
                          value={config.external_apis?.teste_iptv?.url || ''}
                          onChange={(e) => setConfig({
                            ...config,
                            external_apis: {
                              ...config.external_apis,
                              teste_iptv: {
                                ...config.external_apis?.teste_iptv,
                                url: e.target.value
                              }
                            }
                          })}
                          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                          placeholder="https://gesth.io/api/get-teste?hash=..."
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Palavras-chave que Ativam (separadas por vírgula)
                        </label>
                        <input
                          type="text"
                          value={config.external_apis?.teste_iptv?.trigger_keywords?.join(', ') || ''}
                          onChange={(e) => setConfig({
                            ...config,
                            external_apis: {
                              ...config.external_apis,
                              teste_iptv: {
                                ...config.external_apis?.teste_iptv,
                                trigger_keywords: e.target.value.split(',').map(k => k.trim())
                              }
                            }
                          })}
                          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                          placeholder="teste, testar, teste grátis"
                        />
                      </div>
                    </>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* ABA 5: APARÊNCIA VISUAL */}
          {activeTab === 'visual' && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Nome Exibido
                  </label>
                  <input
                    type="text"
                    value={config.visual_config?.agent_name_display || ''}
                    onChange={(e) => setConfig({
                      ...config,
                      visual_config: { ...config.visual_config, agent_name_display: e.target.value }
                    })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="Ex: Juliana Silva"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    URL da Foto do Agente
                  </label>
                  <input
                    type="url"
                    value={config.visual_config?.agent_photo || ''}
                    onChange={(e) => setConfig({
                      ...config,
                      visual_config: { ...config.visual_config, agent_photo: e.target.value }
                    })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="https://..."
                  />
                </div>
              </div>

              <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div>
                  <h3 className="font-medium text-gray-900">Mostrar Selo de Verificado</h3>
                  <p className="text-sm text-gray-600">Exibir badge azul ao lado do nome</p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={config.visual_config?.show_verified_badge !== false}
                    onChange={(e) => setConfig({
                      ...config,
                      visual_config: { ...config.visual_config, show_verified_badge: e.target.checked }
                    })}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                </label>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Cor do Tema
                </label>
                <input
                  type="color"
                  value={config.visual_config?.theme_color || '#0084ff'}
                  onChange={(e) => setConfig({
                    ...config,
                    visual_config: { ...config.visual_config, theme_color: e.target.value }
                  })}
                  className="w-full h-12 border border-gray-300 rounded-lg"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Posição do Chat
                </label>
                <select
                  value={config.visual_config?.chat_position || 'bottom-right'}
                  onChange={(e) => setConfig({
                    ...config,
                    visual_config: { ...config.visual_config, chat_position: e.target.value }
                  })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="bottom-right">Inferior Direito</option>
                  <option value="bottom-left">Inferior Esquerdo</option>
                  <option value="fullscreen">Tela Cheia</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Tamanho do Chat
                </label>
                <select
                  value={config.visual_config?.chat_size || 'medium'}
                  onChange={(e) => setConfig({
                    ...config,
                    visual_config: { ...config.visual_config, chat_size: e.target.value }
                  })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="small">Pequeno</option>
                  <option value="medium">Médio</option>
                  <option value="large">Grande</option>
                </select>
              </div>
            </div>
          )}

          {/* ABA 6: FLUXOS & REGRAS */}
          {activeTab === 'flows' && (
            <div className="space-y-6">
              <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                <div className="flex items-start gap-3">
                  <Zap className="text-purple-600 flex-shrink-0 mt-0.5" size={20} />
                  <div>
                    <h3 className="font-medium text-purple-900">Fluxos Automatizados</h3>
                    <p className="text-sm text-purple-700 mt-1">
                      Configure fluxos específicos que a IA vai seguir automaticamente
                    </p>
                  </div>
                </div>
              </div>

              {/* Fluxo Teste Grátis */}
              <div className="border rounded-lg p-4">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h3 className="font-medium text-gray-900">Fluxo: Teste Grátis</h3>
                    <p className="text-sm text-gray-600">Gerar teste IPTV automaticamente</p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={config.flows?.teste_gratis?.enabled || false}
                      onChange={(e) => setConfig({
                        ...config,
                        flows: {
                          ...config.flows,
                          teste_gratis: {
                            ...config.flows?.teste_gratis,
                            enabled: e.target.checked
                          }
                        }
                      })}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                  </label>
                </div>

                {config.flows?.teste_gratis?.enabled && (
                  <div className="space-y-4">
                    <div className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={config.flows?.teste_gratis?.require_app_install || false}
                        onChange={(e) => setConfig({
                          ...config,
                          flows: {
                            ...config.flows,
                            teste_gratis: {
                              ...config.flows?.teste_gratis,
                              require_app_install: e.target.checked
                            }
                          }
                        })}
                        className="rounded"
                      />
                      <label className="text-sm text-gray-700">
                        Exigir instalação do app antes de gerar teste
                      </label>
                    </div>

                    {config.flows?.teste_gratis?.require_app_install && (
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          URL do App
                        </label>
                        <input
                          type="url"
                          value={config.flows?.teste_gratis?.app_url || ''}
                          onChange={(e) => setConfig({
                            ...config,
                            flows: {
                              ...config.flows,
                              teste_gratis: {
                                ...config.flows?.teste_gratis,
                                app_url: e.target.value
                              }
                            }
                          })}
                          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                          placeholder="https://suporte.help"
                        />
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Fluxo de Vendas */}
              <div className="border rounded-lg p-4">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h3 className="font-medium text-gray-900">Fluxo: Vendas</h3>
                    <p className="text-sm text-gray-600">Coletar dados e processar vendas</p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={config.flows?.vendas?.enabled || false}
                      onChange={(e) => setConfig({
                        ...config,
                        flows: {
                          ...config.flows,
                          vendas: {
                            ...config.flows?.vendas,
                            enabled: e.target.checked
                          }
                        }
                      })}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                  </label>
                </div>

                {config.flows?.vendas?.enabled && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Dados a Coletar (separados por vírgula)
                    </label>
                    <input
                      type="text"
                      value={config.flows?.vendas?.collect_data?.join(', ') || ''}
                      onChange={(e) => setConfig({
                        ...config,
                        flows: {
                          ...config.flows,
                          vendas: {
                            ...config.flows?.vendas,
                            collect_data: e.target.value.split(',').map(d => d.trim())
                          }
                        }
                      })}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                      placeholder="nome, whatsapp, email, interesse"
                    />
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Footer com Dicas */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <Sparkles className="text-blue-600 flex-shrink-0 mt-0.5" size={20} />
          <div>
            <h3 className="font-medium text-blue-900">💡 Dicas para Melhor Performance</h3>
            <ul className="text-sm text-blue-700 mt-2 space-y-1">
              <li>• Seja específico nas instruções - quanto mais detalhado, melhor</li>
              <li>• Use exemplos de conversas nas instruções</li>
              <li>• Mantenha a base de conhecimento atualizada</li>
              <li>• Teste regularmente para garantir qualidade</li>
              <li>• Use Temperature entre 0.7-0.9 para respostas mais naturais</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

export default VendasBotManagerV2;
