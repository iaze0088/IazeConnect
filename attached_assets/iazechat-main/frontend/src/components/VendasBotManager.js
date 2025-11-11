import React, { useState, useEffect } from 'react';
import { Save, MessageSquare, Sparkles, Bot, Settings } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';

function VendasBotManager() {
  const [config, setConfig] = useState({
    empresa_nome: 'CyberTV',
    usa_ia: true,
    api_teste_url: 'https://gesth.io/api/get-teste?hash=TG1OTW5QWHlaTW5Q',
    agent_id: null,
    custom_instructions: '',
    // Perfil do Agente IA
    agent_profile: {
      name: 'Assistente Virtual',
      photo: '',  // URL da foto
      show_verified_badge: true  // Mostrar selo verificado
    },
    // Configuração de IA inline
    ia_inline: {
      name: 'Vendedor IA',
      personality: 'Amigável, profissional e focado em vendas',
      instructions: '',
      llm_provider: 'openai',
      llm_model: 'gpt-4o-mini',
      temperature: 0.7,
      max_tokens: 500,
      api_key: '' // Campo para API Key
    }
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
        
        // Garantir que ia_inline sempre exista
        if (!data.ia_inline) {
          data.ia_inline = {
            name: 'Vendedor IA',
            personality: 'Amigável, profissional e focado em vendas',
            instructions: data.custom_instructions || '',
            llm_provider: 'openai',
            llm_model: 'gpt-4o-mini',
            temperature: 0.7,
            max_tokens: 500,
            api_key: ''
          };
        }
        
        // Garantir que agent_profile sempre exista
        if (!data.agent_profile) {
          data.agent_profile = {
            name: 'Assistente Virtual',
            photo: '',
            show_verified_badge: true
          };
        }
        
        setConfig(data);
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
          <Settings size={20} className="text-blue-600" />
          Configurações Básicas
        </h3>

        {/* Perfil do Agente IA */}
        <div className="border-2 border-blue-200 rounded-lg p-4 bg-blue-50 space-y-4">
          <h4 className="font-semibold text-blue-900 flex items-center gap-2">
            👤 Perfil do Agente Virtual
          </h4>
          
          {/* Nome do Agente */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Nome do Agente (visível para o cliente)
            </label>
            <input
              type="text"
              value={config.agent_profile?.name || 'Assistente Virtual'}
              onChange={(e) => setConfig({
                ...config, 
                agent_profile: {...(config.agent_profile || {}), name: e.target.value}
              })}
              className="w-full border border-gray-300 rounded-lg p-3 focus:ring-2 focus:ring-blue-500"
              placeholder="Ex: Atendente Virtual, Assistente Maria, etc"
            />
          </div>

          {/* Foto do Agente */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              📸 Foto do Agente (URL)
            </label>
            <input
              type="url"
              value={config.agent_profile?.photo || ''}
              onChange={(e) => setConfig({
                ...config, 
                agent_profile: {...(config.agent_profile || {}), photo: e.target.value}
              })}
              className="w-full border border-gray-300 rounded-lg p-3 focus:ring-2 focus:ring-blue-500"
              placeholder="https://exemplo.com/foto-agente.jpg"
            />
            <p className="text-xs text-gray-500 mt-1">
              💡 Cole a URL de uma imagem. Recomendado: foto quadrada, tamanho mínimo 200x200px
            </p>
            
            {/* Preview da foto */}
            {config.agent_profile?.photo && (
              <div className="mt-3 flex items-center gap-3">
                <img 
                  src={config.agent_profile.photo} 
                  alt="Preview" 
                  className="w-16 h-16 rounded-full object-cover border-2 border-blue-300"
                  onError={(e) => {
                    e.target.style.display = 'none';
                  }}
                />
                <span className="text-sm text-gray-600">Preview da foto</span>
              </div>
            )}
          </div>

          {/* Selo Verificado */}
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="verified-badge"
              checked={config.agent_profile?.show_verified_badge !== false}
              onChange={(e) => setConfig({
                ...config, 
                agent_profile: {...(config.agent_profile || {}), show_verified_badge: e.target.checked}
              })}
              className="w-4 h-4 rounded"
            />
            <label htmlFor="verified-badge" className="text-sm font-medium">
              ✓ Mostrar selo de verificado ao lado do nome
            </label>
          </div>
        </div>

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
          <div className="space-y-4 border-2 border-blue-200 rounded-lg p-4 bg-blue-50">
            <h4 className="font-semibold text-blue-900 flex items-center gap-2">
              <Bot size={20} className="text-blue-600" />
              Configuração da IA
            </h4>
            
            {/* Nome do Agente */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Nome do Agente IA
              </label>
              <input
                type="text"
                value={config.ia_inline?.name || 'Vendedor IA'}
                onChange={(e) => setConfig({
                  ...config, 
                  ia_inline: {...(config.ia_inline || {}), name: e.target.value}
                })}
                className="w-full border border-gray-300 rounded-lg p-3 focus:ring-2 focus:ring-blue-500"
                placeholder="Ex: Vendedor Virtual, Assistente CyberTV"
              />
            </div>

            {/* Personalidade */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Personalidade
              </label>
              <input
                type="text"
                value={config.ia_inline?.personality || ''}
                onChange={(e) => setConfig({
                  ...config, 
                  ia_inline: {...(config.ia_inline || {}), personality: e.target.value}
                })}
                className="w-full border border-gray-300 rounded-lg p-3 focus:ring-2 focus:ring-blue-500"
                placeholder="Ex: Amigável, profissional e focado em vendas"
              />
            </div>

            {/* Instruções */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                📝 Instruções para a IA (Curtas)
              </label>
              <textarea
                value={config.ia_inline?.instructions || config.custom_instructions || ''}
                onChange={(e) => setConfig({
                  ...config, 
                  ia_inline: {...(config.ia_inline || {}), instructions: e.target.value},
                  custom_instructions: e.target.value
                })}
                className="w-full border border-gray-300 rounded-lg p-3 focus:ring-2 focus:ring-blue-500"
                rows="4"
                placeholder="Instruções rápidas ou resumo... (se tiver instruções completas abaixo, este campo será ignorado)"
              />
            </div>

            {/* URL de Instruções Completas */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <label className="block text-sm font-medium text-blue-900 mb-2">
                🌐 URL das Instruções Completas (Recomendado para instruções grandes)
              </label>
              <input
                type="url"
                value={config.ia_inline?.instructions_url || ''}
                onChange={(e) => setConfig({
                  ...config, 
                  ia_inline: {...(config.ia_inline || {}), instructions_url: e.target.value}
                })}
                className="w-full border border-blue-300 rounded-lg p-3 focus:ring-2 focus:ring-blue-500"
                placeholder="https://pastebin.com/raw/sua-instrucao ou Google Docs (público)"
              />
              <p className="text-xs text-blue-700 mt-2">
                💡 <strong>Como usar:</strong> Coloque suas instruções em um site público (Pastebin, Google Docs público, etc) e cole a URL aqui.
                <br />
                ✅ A IA vai buscar e usar essas instruções automaticamente.
                <br />
                ⚠️ Se preencher URL, o campo "Instruções Curtas" acima será ignorado.
              </p>
              <p className="text-xs text-blue-600 mt-1">
                📌 <strong>Sites recomendados:</strong> pastebin.com/raw, justpaste.it/raw, hastebin.com/raw
              </p>
            </div>

            {/* Upload de Arquivo .txt */}
            <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
              <label className="block text-sm font-medium text-purple-900 mb-2">
                📄 Upload de Instruções Completas (.txt) ⭐ Recomendado
              </label>
              <input
                type="file"
                accept=".txt"
                onChange={async (e) => {
                  const file = e.target.files[0];
                  if (!file) return;
                  
                  if (!file.name.endsWith('.txt')) {
                    alert('Apenas arquivos .txt são permitidos');
                    return;
                  }
                  
                  try {
                    const formData = new FormData();
                    formData.append('file', file);
                    
                    const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/admin/vendas-bot/upload-instructions`, {
                      method: 'POST',
                      body: formData
                    });
                    
                    if (!response.ok) throw new Error('Erro no upload');
                    
                    const data = await response.json();
                    
                    alert(`✅ Arquivo carregado com sucesso!\n\n${data.filename}\nTamanho: ${data.size} caracteres`);
                    
                    setConfig({
                      ...config, 
                      ia_inline: {...(config.ia_inline || {}), instructions_file: data.filename}
                    });
                    
                    // Recarregar config
                    loadConfig();
                  } catch (error) {
                    console.error('Error uploading file:', error);
                    alert('Erro ao fazer upload do arquivo. Tente novamente.');
                  }
                }}
                className="w-full text-sm border border-purple-300 rounded-lg p-2 bg-white"
              />
              {config.ia_inline?.instructions_file && (
                <div className="mt-3 flex items-center gap-2 p-2 bg-green-50 border border-green-200 rounded">
                  <span className="text-sm text-green-700 flex-1">✅ Arquivo ativo: {config.ia_inline.instructions_file}</span>
                  <button
                    onClick={async () => {
                      if (window.confirm('❌ Remover arquivo de instruções?\n\nA IA voltará a usar o campo "Instruções Curtas" ou URL.')) {
                        try {
                          const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/admin/vendas-bot/instructions-file`, {
                            method: 'DELETE'
                          });
                          
                          if (!response.ok) throw new Error('Erro ao remover');
                          
                          alert('✅ Arquivo removido com sucesso!');
                          
                          setConfig({
                            ...config, 
                            ia_inline: {...(config.ia_inline || {}), instructions_file: null}
                          });
                          
                          loadConfig();
                        } catch (error) {
                          alert('Erro ao remover arquivo');
                        }
                      }
                    }}
                    className="text-red-600 hover:text-red-700 text-sm font-medium px-2 py-1 hover:bg-red-100 rounded"
                  >
                    ❌ Remover
                  </button>
                </div>
              )}
              <p className="text-xs text-purple-700 mt-2">
                💡 <strong>Como usar:</strong> Crie um arquivo .txt com todas as suas instruções e faça upload aqui.
                <br />
                ✅ A IA vai usar o conteúdo do arquivo automaticamente.
                <br />
                ⚠️ <strong>Prioridade:</strong> Arquivo .txt > URL > Campo de Instruções Curtas
              </p>
              <p className="text-xs text-purple-600 mt-1">
                📌 <strong>Vantagem:</strong> Sem limite de tamanho! Perfeito para instruções detalhadas.
              </p>
            </div>

            {/* API Key OpenAI */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                🔑 OpenAI API Key (Obrigatória)
              </label>
              <input
                type="password"
                value={config.ia_inline?.api_key || ''}
                onChange={(e) => setConfig({
                  ...config, 
                  ia_inline: {...(config.ia_inline || {}), api_key: e.target.value}
                })}
                className="w-full border border-gray-300 rounded-lg p-3 focus:ring-2 focus:ring-blue-500"
                placeholder="sk-..."
              />
              <p className="text-xs text-gray-500 mt-1">
                🔗 Obtenha sua chave em: <a href="https://platform.openai.com/api-keys" target="_blank" className="text-blue-600 hover:underline">platform.openai.com/api-keys</a>
              </p>
              {!config.ia_inline?.api_key && (
                <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded">
                  <p className="text-xs text-red-700">
                    ⚠️ <strong>API Key obrigatória!</strong> Sem ela, a IA não funcionará.
                  </p>
                </div>
              )}
            </div>

            {/* Modelo LLM */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Modelo LLM
                </label>
                <select
                  value={config.ia_inline?.llm_model || 'gpt-4o-mini'}
                  onChange={(e) => setConfig({
                    ...config, 
                    ia_inline: {...(config.ia_inline || {}), llm_model: e.target.value}
                  })}
                  className="w-full border border-gray-300 rounded-lg p-3 focus:ring-2 focus:ring-blue-500"
                >
                  <option value="gpt-4o">GPT-4o (Melhor)</option>
                  <option value="gpt-4o-mini">GPT-4o-mini (Rápido)</option>
                  <option value="gpt-4-turbo">GPT-4 Turbo</option>
                  <option value="gpt-3.5-turbo">GPT-3.5 Turbo (Econômico)</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Temperatura (Criatividade)
                </label>
                <input
                  type="number"
                  min="0"
                  max="1"
                  step="0.1"
                  value={config.ia_inline?.temperature || 0.7}
                  onChange={(e) => setConfig({
                    ...config, 
                    ia_inline: {...(config.ia_inline || {}), temperature: parseFloat(e.target.value)}
                  })}
                  className="w-full border border-gray-300 rounded-lg p-3 focus:ring-2 focus:ring-blue-500"
                />
                <p className="text-xs text-gray-500 mt-1">0 = Preciso, 1 = Criativo</p>
              </div>
            </div>

            <div className="bg-blue-100 border border-blue-300 rounded p-3">
              <p className="text-sm text-blue-800">
                ✅ <strong>Configuração inline:</strong> A IA será configurada direto aqui, sem precisar criar na aba "Agentes IA"
              </p>
            </div>
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
