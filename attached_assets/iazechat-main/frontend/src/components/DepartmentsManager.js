import React, { useState, useEffect } from 'react';
import { Plus, Edit, Trash2, Clock, Bot, Sparkles, ThumbsUp, ThumbsDown, Volume2, Play, Database } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import api from '@/lib/api';
import { toast } from 'sonner';

const DepartmentsManager = () => {
  const [departments, setDepartments] = useState([]);
  const [agents, setAgents] = useState([]);
  const [humanAgents, setHumanAgents] = useState([]); // Atendentes humanos
  const [showDialog, setShowDialog] = useState(false);
  const [showAIDialog, setShowAIDialog] = useState(false); // Modal de IA
  const [showLearningDialog, setShowLearningDialog] = useState(false); // Modal de Aprendizado
  const [showMemoryCleanupDialog, setShowMemoryCleanupDialog] = useState(false); // Modal de Limpeza de Memória
  const [editingDept, setEditingDept] = useState(null);
  const [editingAI, setEditingAI] = useState(null); // Departamento sendo editado para IA
  const [editingLearning, setEditingLearning] = useState(null); // Departamento sendo editado para Aprendizado
  const [editingMemoryCleanup, setEditingMemoryCleanup] = useState(null); // Departamento para configurar limpeza
  const [learningData, setLearningData] = useState([]); // Dados de aprendizado
  const [memoryCleanupDays, setMemoryCleanupDays] = useState(null); // Dias para limpeza (null = nunca)
  const [originFilter, setOriginFilter] = useState('wa_suporte'); // Filtro de origem
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    ai_agent_id: '',
    is_default: false,
    timeout_seconds: 120,
    agent_ids: [], // IDs dos atendentes que podem ver este departamento
    origin: 'wa_suporte' // Origem do departamento
  });
  
  // Form para configuração de IA do departamento
  const [aiFormData, setAIFormData] = useState({
    name: '',
    personality: '',
    instructions: '',
    llm_provider: 'openai',
    llm_model: 'gpt-4o-mini',
    temperature: 0.7,
    max_tokens: 500,
    is_active: true,
    api_key: '',  // Campo API Key específica deste departamento
    schedule_start_time: '',  // Horário de início (HH:MM)
    schedule_end_time: ''  // Horário de fim (HH:MM)
  });

  useEffect(() => {
    loadDepartments();
    loadAgents();
    loadHumanAgents();
  }, []);

  const loadDepartments = async () => {
    try {
      const { data } = await api.get('/ai/departments');
      setDepartments(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Error loading departments:', error);
      setDepartments([]);
    }
  };

  const loadAgents = async () => {
    try {
      const { data } = await api.get('/ai/agents');
      console.log('🤖 Agentes IA carregados:', data);
      const agentsList = Array.isArray(data) ? data : [];
      // Não filtrar por is_active - mostrar todos os agentes
      setAgents(agentsList);
      console.log('✅ Total de agentes:', agentsList.length);
    } catch (error) {
      console.error('Error loading agents:', error);
      setAgents([]);
    }
  };

  const loadHumanAgents = async () => {
    try {
      const { data } = await api.get('/agents');
      setHumanAgents(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Error loading human agents:', error);
      setHumanAgents([]);
    }
  };

  const handleSave = async () => {
    if (!formData.name.trim()) {
      toast.error('Digite um nome para o departamento');
      return;
    }

    try {
      // Garantir que origin está definido com valor atual do filtro
      const dataToSave = {
        ...formData,
        origin: originFilter // FORÇAR origem selecionada SEMPRE
      };
      
      console.log('🔍 DEBUG: Salvando departamento:', {
        nome: dataToSave.name,
        origin: dataToSave.origin,
        originFilter: originFilter,
        agent_ids: dataToSave.agent_ids
      });
      
      if (editingDept) {
        await api.put(`/ai/departments/${editingDept.id}`, dataToSave);
        toast.success(`✅ Departamento atualizado! ${dataToSave.agent_ids?.length || 0} atendente(s) selecionado(s)`);
      } else {
        const response = await api.post('/ai/departments', dataToSave);
        console.log('✅ Resposta do servidor:', response.data);
        toast.success(`✅ Departamento "${dataToSave.name}" criado com ${dataToSave.agent_ids?.length || 0} atendente(s)!`);
      }
      
      setShowDialog(false);
      setEditingDept(null);
      setFormData({
        name: '',
        description: '',
        ai_agent_id: '',
        is_default: false,
        timeout_seconds: 120,
        agent_ids: [],
        origin: originFilter // Manter origem
      });
      await loadDepartments(); // Recarregar lista
    } catch (error) {
      console.error('Error saving department:', error);
      toast.error('Erro ao salvar departamento: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleEdit = (dept) => {
    setEditingDept(dept);
    setFormData({
      name: dept.name,
      description: dept.description || '',
      ai_agent_id: dept.ai_agent_id || '',
      is_default: dept.is_default || false,
      timeout_seconds: dept.timeout_seconds || 120,
      agent_ids: Array.isArray(dept.agent_ids) ? dept.agent_ids : [],
      origin: dept.origin || originFilter // ✅ INCLUIR ORIGIN
    });
    setShowDialog(true);
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Tem certeza que deseja excluir este departamento?')) return;
    
    try {
      await api.delete(`/ai/departments/${id}`);
      toast.success('Departamento excluído!');
      loadDepartments();
    } catch (error) {
      console.error('Error deleting department:', error);
      toast.error('Erro ao excluir departamento');
    }
  };

  const handleOpenAIConfig = (dept) => {
    setEditingAI(dept);
    
    // Se departamento já tem IA configurada, carregar os dados
    const linkedAgent = agents.find(a => a.id === dept.ai_agent_id);
    
    if (linkedAgent) {
      setAIFormData({
        name: linkedAgent.name || `IA ${dept.name}`,
        personality: linkedAgent.personality || '',
        instructions: linkedAgent.instructions || '',
        llm_provider: linkedAgent.llm_provider || 'openai',
        llm_model: linkedAgent.llm_model || 'gpt-4o-mini',
        temperature: linkedAgent.temperature || 0.7,
        max_tokens: linkedAgent.max_tokens || 500,
        is_active: linkedAgent.is_active !== false,
        api_key: linkedAgent.api_key || '',  // Carregar API key se existir
        schedule_start_time: linkedAgent.schedule_start_time || '',
        schedule_end_time: linkedAgent.schedule_end_time || ''
      });
    } else {
      // Valores padrão para nova IA
      setAIFormData({
        name: `IA ${dept.name}`,
        personality: 'Assistente profissional e prestativo',
        instructions: '',
        llm_provider: 'openai',
        llm_model: 'gpt-4o-mini',
        temperature: 0.7,
        max_tokens: 500,
        is_active: true,
        api_key: '',  // Vazio para nova IA
        schedule_start_time: '',
        schedule_end_time: ''
      });
    }
    
    setShowAIDialog(true);
  };

  const handleSaveAI = async () => {
    if (!aiFormData.name.trim()) {
      toast.error('Digite um nome para o agente IA');
      return;
    }

    try {
      let agentId = editingAI.ai_agent_id;
      
      // Se já existe IA, atualizar. Senão, criar nova
      if (agentId) {
        // Atualizar IA existente
        await api.put(`/ai/agents/${agentId}`, aiFormData);
        
        // ⚡ IMPORTANTE: Garantir que continua vinculado ao departamento
        await api.put(`/ai/departments/${editingAI.id}`, {
          ai_agent_id: agentId
        });
        
        toast.success('✅ Agente IA atualizado!');
      } else {
        // Criar nova IA
        const { data } = await api.post('/ai/agents', aiFormData);
        agentId = data.id;
        
        // Vincular ao departamento
        await api.put(`/ai/departments/${editingAI.id}`, {
          ai_agent_id: agentId
        });
        
        toast.success('✅ Agente IA criado e vinculado ao departamento!');
      }
      
      setShowAIDialog(false);
      setEditingAI(null);
      loadDepartments();
      loadAgents();
    } catch (error) {
      console.error('Error saving AI:', error);
      toast.error('Erro ao salvar agente IA: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleDeleteAI = async () => {
    if (!window.confirm('❌ Tem certeza que deseja REMOVER o agente IA deste departamento?\n\nO agente será desvinculado mas não será excluído.')) {
      return;
    }

    try {
      // Desvincular IA do departamento (enviar apenas ai_agent_id: null)
      await api.put(`/ai/departments/${editingAI.id}`, {
        ai_agent_id: null
      });
      
      toast.success('✅ Agente IA desvinculado do departamento');
      setShowAIDialog(false);
      setEditingAI(null);
      loadDepartments();
    } catch (error) {
      console.error('Error removing AI:', error);
      toast.error('Erro ao remover agente IA: ' + (error.response?.data?.detail || error.message));
    }
  };

  // Funções para gerenciar limpeza de memória da IA
  const openMemoryCleanupDialog = async (dept) => {
    setEditingMemoryCleanup(dept);
    
    try {
      // Carregar configuração atual de limpeza
      const { data } = await api.get(`/api/departments/${dept.id}/ai-memory-config`);
      setMemoryCleanupDays(data.ai_memory_cleanup_days);
    } catch (error) {
      console.error('Error loading memory cleanup config:', error);
      setMemoryCleanupDays(null); // Default: nunca limpar
    }
    
    setShowMemoryCleanupDialog(true);
  };

  const handleSaveMemoryCleanup = async () => {
    try {
      await api.put(`/api/departments/${editingMemoryCleanup.id}/ai-memory-config`, {
        ai_memory_cleanup_days: memoryCleanupDays
      });
      
      toast.success('✅ Configuração de limpeza de memória salva!');
      setShowMemoryCleanupDialog(false);
      setEditingMemoryCleanup(null);
      loadDepartments();
    } catch (error) {
      console.error('Error saving memory cleanup config:', error);
      toast.error('Erro ao salvar configuração: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleOpenLearning = async (dept) => {
    setEditingLearning(dept);
    
    // Carregar dados de aprendizado do departamento/agente
    if (dept.ai_agent_id) {
      try {
        const { data } = await api.get(`/ai-learning/learning/${dept.ai_agent_id}`);
        setLearningData(Array.isArray(data) ? data : []);
      } catch (error) {
        console.error('Error loading learning data:', error);
        setLearningData([]);
      }
    } else {
      setLearningData([]);
    }
    
    setShowLearningDialog(true);
  };

  const handleAddManualLearning = async () => {
    // Abrir modal para adicionar exemplo manual
    const userMessage = prompt('📝 Digite a PERGUNTA do cliente:');
    if (!userMessage || !userMessage.trim()) return;
    
    const aiResponse = prompt('🤖 Digite a RESPOSTA CORRETA da IA:');
    if (!aiResponse || !aiResponse.trim()) return;
    
    try {
      await api.post('/ai-learning/learning/manual', {
        agent_id: editingLearning.ai_agent_id,
        user_message: userMessage,
        ai_response: aiResponse,
        feedback: 'correct'  // Exemplo manual sempre marcado como correto
      });
      
      toast.success('✅ Exemplo de aprendizado adicionado!');
      
      // Recarregar dados
      if (editingLearning?.ai_agent_id) {
        const { data } = await api.get(`/ai-learning/learning/${editingLearning.ai_agent_id}`);
        setLearningData(Array.isArray(data) ? data : []);
      }
    } catch (error) {
      console.error('Error adding manual learning:', error);
      toast.error('Erro ao adicionar exemplo: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleSaveLearningFeedback = async (learningId, isCorrect) => {
    try {
      await api.post(`/ai-learning/learning/${learningId}/feedback`, {
        is_correct: isCorrect
      });
      
      toast.success(isCorrect ? '✅ Marcado como CORRETO' : '❌ Marcado como ERRADO');
      
      // Recarregar dados
      if (editingLearning?.ai_agent_id) {
        const { data } = await api.get(`/ai-learning/learning/${editingLearning.ai_agent_id}`);
        setLearningData(Array.isArray(data) ? data : []);
      }
    } catch (error) {
      console.error('Error saving feedback:', error);
      toast.error('Erro ao salvar feedback');
    }
  };

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-slate-900 mb-2">📂 Departamentos por Origem</h2>
        <p className="text-slate-600 mb-4">Crie departamentos específicos para cada canal de atendimento</p>
      </div>

      {/* ABAS DE ORIGEM */}
      <div className="flex gap-2 mb-6">
        <Button
          variant={originFilter === 'wa_suporte' ? 'default' : 'outline'}
          onClick={() => setOriginFilter('wa_suporte')}
          className={`flex-1 ${
            originFilter === 'wa_suporte' 
              ? 'bg-red-600 hover:bg-red-700 text-white' 
              : 'border-red-300 text-red-700 hover:bg-red-50'
          }`}
        >
          📱 WA SUPORTE
        </Button>
        <Button
          variant={originFilter === 'whatsapp_starter' ? 'default' : 'outline'}
          onClick={() => setOriginFilter('whatsapp_starter')}
          className={`flex-1 ${
            originFilter === 'whatsapp_starter' 
              ? 'bg-green-600 hover:bg-green-700 text-white' 
              : 'border-green-300 text-green-700 hover:bg-green-50'
          }`}
        >
          💬 WHATSAPP STARTER
        </Button>
        <Button
          variant={originFilter === 'ia' ? 'default' : 'outline'}
          onClick={() => setOriginFilter('ia')}
          className={`flex-1 ${
            originFilter === 'ia' 
              ? 'bg-purple-600 hover:bg-purple-700 text-white' 
              : 'border-purple-300 text-purple-700 hover:bg-purple-50'
          }`}
        >
          🤖 I.A
        </Button>
      </div>

      {/* Botão Criar Departamento */}
      <div className="mb-6">
        <Button 
          onClick={() => {
            setEditingDept(null);
            setFormData({
              name: '',
              description: '',
              ai_agent_id: '',
              is_default: false,
              timeout_seconds: 120,
              agent_ids: [],
              origin: originFilter // Usar origem selecionada
            });
            setShowDialog(true);
          }}
          className="bg-indigo-600 hover:bg-indigo-700"
        >
          <Plus className="w-4 h-4 mr-2" />
          Novo Departamento para {originFilter === 'wa_suporte' ? 'WA SUPORTE' : originFilter === 'whatsapp_starter' ? 'WHATSAPP STARTER' : 'I.A'}
        </Button>
      </div>

      {/* Lista de Departamentos - Filtrados por origem */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {(departments || [])
          .filter(dept => dept.origin === originFilter) // Filtrar por origem
          .map(dept => {
          const linkedAgent = agents.find(a => a.id === dept.ai_agent_id);
          
          return (
            <Card key={dept.id} className="p-4">
              <div className="flex items-start justify-between mb-3">
                <div>
                  <h3 className="font-semibold text-slate-900">{dept.name}</h3>
                  {dept.is_default && (
                    <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded mt-1 inline-block">
                      Padrão
                    </span>
                  )}
                </div>
                
                <div className="flex gap-1">
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => handleOpenAIConfig(dept)}
                    className="text-purple-600 hover:text-purple-700 hover:bg-purple-50"
                    title="Configurar IA do Departamento"
                  >
                    <Bot className="w-4 h-4" />
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => handleOpenLearning(dept)}
                    className="text-blue-600 hover:text-blue-700 hover:bg-blue-50"
                    title="Sistema de Aprendizado"
                  >
                    <Sparkles className="w-4 h-4" />
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => openMemoryCleanupDialog(dept)}
                    className="text-purple-600 hover:text-purple-700 hover:bg-purple-50"
                    title="Configurar Limpeza de Memória da IA"
                  >
                    <Database className="w-4 h-4" />
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => handleEdit(dept)}
                  >
                    <Edit className="w-4 h-4" />
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => handleDelete(dept.id)}
                  >
                    <Trash2 className="w-4 h-4 text-red-500" />
                  </Button>
                </div>
              </div>
              
              <p className="text-sm text-slate-600 mb-3">{dept.description || 'Sem descrição'}</p>
              
              <div className="space-y-2 text-xs text-slate-500">
                <div className="flex items-center gap-2">
                  <Clock className="w-3 h-3" />
                  <span>Timeout: {dept.timeout_seconds}s</span>
                </div>
                {linkedAgent && (
                  <div className="flex items-center gap-2 text-indigo-600">
                    <span>🤖</span>
                    <span>{linkedAgent.name}</span>
                  </div>
                )}
              </div>
            </Card>
          );
        })}
      </div>

      {/* Dialog: Criar/Editar Departamento */}
      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editingDept ? 'Editar' : 'Criar'} Departamento</DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium mb-2 block">Nome</label>
              <Input
                placeholder="Ex: Suporte, Vendas, Teste Grátis"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              />
            </div>

            <div>
              <label className="text-sm font-medium mb-2 block">Descrição</label>
              <Textarea
                placeholder="Descreva este departamento"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                rows={2}
              />
            </div>

            <div>
              <label className="text-sm font-medium mb-2 block">Agente IA vinculado</label>
              <select
                value={formData.ai_agent_id}
                onChange={(e) => setFormData({ ...formData, ai_agent_id: e.target.value })}
                className="w-full border rounded-lg p-2 bg-white"
                style={{ minHeight: '40px' }}
              >
                <option value="">Nenhum</option>
                {(agents || []).length === 0 ? (
                  <option disabled>⚠️ Nenhum agente IA cadastrado. Vá para a aba "Agentes IA" para criar um.</option>
                ) : (
                  (agents || []).map(agent => (
                    <option key={agent.id} value={agent.id}>{agent.name}</option>
                  ))
                )}
              </select>
              {(agents || []).length === 0 && (
                <p className="text-xs text-orange-600 mt-1">
                  ⚠️ Nenhum agente IA cadastrado. Crie um agente na aba "Agentes IA".
                </p>
              )}
            </div>

            <div>
              <label className="text-sm font-medium mb-2 block">Timeout (segundos)</label>
              <Input
                type="number"
                placeholder="120"
                value={formData.timeout_seconds}
                onChange={(e) => setFormData({ ...formData, timeout_seconds: parseInt(e.target.value) })}
              />
              <p className="text-xs text-slate-500 mt-1">
                Tempo para redirecionar automaticamente para este departamento se o cliente não responder
              </p>
            </div>

            {/* Seleção de Atendentes */}
            <div className="p-4 bg-purple-50 border border-purple-200 rounded-lg">
              <label className="text-sm font-semibold text-purple-900 mb-2 block">
                👥 Atendentes com acesso a este departamento
              </label>
              <p className="text-xs text-purple-700 mb-3">
                Selecione quais atendentes podem visualizar e responder tickets deste departamento. Se não selecionar nenhum, todos os atendentes terão acesso.
              </p>
              {humanAgents.length > 0 ? (
                <div className="space-y-2 max-h-48 overflow-y-auto">
                  {humanAgents.map(agent => (
                    <label key={agent.id} className="flex items-center gap-2 p-2 bg-white rounded border hover:bg-purple-50 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={(formData.agent_ids || []).includes(agent.id)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setFormData({
                              ...formData,
                              agent_ids: [...(formData.agent_ids || []), agent.id]
                            });
                          } else {
                            setFormData({
                              ...formData,
                              agent_ids: (formData.agent_ids || []).filter(id => id !== agent.id)
                            });
                          }
                        }}
                        className="w-4 h-4"
                      />
                      <span className="text-sm font-medium">{agent.name}</span>
                      <span className="text-xs text-slate-500">({agent.login})</span>
                    </label>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-slate-500 italic">Nenhum atendente cadastrado ainda</p>
              )}
            </div>

            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={formData.is_default}
                onChange={(e) => setFormData({ ...formData, is_default: e.target.checked })}
                className="w-4 h-4"
              />
              <label className="text-sm">
                Marcar como departamento padrão (recebe tickets após timeout)
              </label>
            </div>

            <div className="flex gap-2 mt-4">
              <Button variant="outline" onClick={() => setShowDialog(false)} className="flex-1">
                Cancelar
              </Button>
              <Button onClick={handleSave} className="flex-1 bg-indigo-600 hover:bg-indigo-700">
                {editingDept ? 'Atualizar' : 'Criar'}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Dialog: Configurar IA do Departamento */}
      <Dialog open={showAIDialog} onOpenChange={setShowAIDialog}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Bot className="w-6 h-6 text-purple-600" />
              Configurar IA - {editingAI?.name}
            </DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4 mt-4">
            {/* Nome do Agente */}
            <div>
              <label className="text-sm font-medium mb-2 block">Nome do Agente IA</label>
              <Input
                placeholder="Ex: Assistente de Suporte, Bot de Vendas"
                value={aiFormData.name}
                onChange={(e) => setAIFormData({ ...aiFormData, name: e.target.value })}
              />
            </div>

            {/* Personalidade */}
            <div>
              <label className="text-sm font-medium mb-2 block">Personalidade</label>
              <Input
                placeholder="Ex: Profissional e prestativo, Amigável e descontraído"
                value={aiFormData.personality}
                onChange={(e) => setAIFormData({ ...aiFormData, personality: e.target.value })}
              />
            </div>

            {/* Instruções */}
            <div>
              <label className="text-sm font-medium mb-2 block">
                <Sparkles className="w-4 h-4 inline mr-1" />
                Instruções para a IA (Curtas)
              </label>
              <Textarea
                placeholder="Instruções rápidas ou resumo... (se enviar arquivo .txt abaixo, este campo será ignorado)"
                value={aiFormData.instructions}
                onChange={(e) => setAIFormData({ ...aiFormData, instructions: e.target.value })}
                rows={4}
                className="font-mono text-sm"
              />
            </div>

            {/* Upload de Arquivo .txt */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <label className="text-sm font-medium text-blue-900 mb-2 block">
                📄 Upload de Instruções Completas (.txt)
              </label>
              <input
                type="file"
                accept=".txt"
                onChange={async (e) => {
                  const file = e.target.files[0];
                  if (!file) return;
                  
                  if (!file.name.endsWith('.txt')) {
                    toast.error('Apenas arquivos .txt são permitidos');
                    return;
                  }
                  
                  try {
                    const formData = new FormData();
                    formData.append('file', file);
                    
                    const { data } = await api.post(`/api/departments/${editingAI.id}/upload-instructions`, formData, {
                      headers: { 'Content-Type': 'multipart/form-data' }
                    });
                    
                    toast.success(`✅ Arquivo carregado: ${data.filename} (${data.size} chars)`);
                    setAIFormData({ ...aiFormData, instructions_file: data.filename });
                  } catch (error) {
                    console.error('Error uploading file:', error);
                    toast.error('Erro ao fazer upload: ' + (error.response?.data?.detail || error.message));
                  }
                }}
                className="w-full text-sm"
              />
              {aiFormData.instructions_file && (
                <div className="mt-2 flex items-center gap-2">
                  <span className="text-sm text-green-700">✅ Arquivo: {aiFormData.instructions_file}</span>
                  <button
                    onClick={async () => {
                      if (window.confirm('Remover arquivo de instruções?')) {
                        try {
                          await api.delete(`/api/departments/${editingAI.id}/instructions-file`);
                          toast.success('Arquivo removido');
                          setAIFormData({ ...aiFormData, instructions_file: null });
                        } catch (error) {
                          toast.error('Erro ao remover arquivo');
                        }
                      }
                    }}
                    className="text-red-600 hover:text-red-700 text-sm"
                  >
                    ❌ Remover
                  </button>
                </div>
              )}
              <p className="text-xs text-blue-700 mt-2">
                💡 <strong>Como usar:</strong> Crie um arquivo .txt com suas instruções completas e faça upload aqui.
                <br />
                ✅ A IA vai usar o conteúdo do arquivo automaticamente.
                <br />
                ⚠️ Se enviar arquivo, o campo "Instruções Curtas" acima será ignorado.
              </p>
            </div>

            {/* API Key OpenAI */}
            <div>
              <label className="text-sm font-medium mb-2 block">
                🔑 OpenAI API Key (Opcional - específica deste departamento)
              </label>
              <Input
                type="password"
                placeholder="sk-... (deixe vazio para usar key padrão do sistema)"
                value={aiFormData.api_key || ''}
                onChange={(e) => setAIFormData({ ...aiFormData, api_key: e.target.value })}
              />
              <p className="text-xs text-gray-500 mt-1">
                💡 Se não informar, usará a API key configurada no sistema. Use para ter API key diferente por departamento.
              </p>
              <p className="text-xs text-gray-500">
                🔗 Obtenha em: <a href="https://platform.openai.com/api-keys" target="_blank" className="text-blue-600 hover:underline">platform.openai.com/api-keys</a>
              </p>
            </div>

            {/* Configurações do Modelo */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium mb-2 block">Modelo LLM</label>
                <select
                  value={aiFormData.llm_model}
                  onChange={(e) => setAIFormData({ ...aiFormData, llm_model: e.target.value })}
                  className="w-full border border-gray-300 rounded-lg p-2 text-sm"
                >
                  <option value="gpt-4o">GPT-4o (Melhor)</option>
                  <option value="gpt-4o-mini">GPT-4o-mini (Rápido)</option>
                  <option value="gpt-4-turbo">GPT-4 Turbo</option>
                  <option value="gpt-3.5-turbo">GPT-3.5 Turbo (Econômico)</option>
                </select>
              </div>

              <div>
                <label className="text-sm font-medium mb-2 block">Temperatura</label>
                <Input
                  type="number"
                  min="0"
                  max="1"
                  step="0.1"
                  value={aiFormData.temperature}
                  onChange={(e) => setAIFormData({ ...aiFormData, temperature: parseFloat(e.target.value) })}
                />
                <p className="text-xs text-gray-500 mt-1">0 = Preciso, 1 = Criativo</p>
              </div>
            </div>

            {/* Status Ativo */}
            <div className="flex items-center gap-2 p-3 bg-green-50 border border-green-200 rounded-lg">
              <input
                type="checkbox"
                checked={aiFormData.is_active}
                onChange={(e) => setAIFormData({ ...aiFormData, is_active: e.target.checked })}
                className="w-4 h-4"
              />
              <label className="text-sm font-medium">
                {aiFormData.is_active ? '🟢 Agente IA ATIVO' : '🔴 Agente IA DESATIVADO'}
              </label>
            </div>

            {/* Agendamento de Horários */}
            <div className="space-y-2 p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <Clock className="w-4 h-4 text-blue-600" />
                <label className="text-sm font-semibold text-blue-800">⏰ Agendamento (Opcional)</label>
              </div>
              <p className="text-xs text-blue-600 mb-3">
                Configure horários específicos para ativação automática da IA. Deixe em branco para manter ativo 24/7.
              </p>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-medium text-gray-700 mb-1 block">Início</label>
                  <Input
                    type="time"
                    value={aiFormData.schedule_start_time}
                    onChange={(e) => setAIFormData({ ...aiFormData, schedule_start_time: e.target.value })}
                    placeholder="08:00"
                    className="text-sm"
                  />
                </div>
                <div>
                  <label className="text-xs font-medium text-gray-700 mb-1 block">Fim</label>
                  <Input
                    type="time"
                    value={aiFormData.schedule_end_time}
                    onChange={(e) => setAIFormData({ ...aiFormData, schedule_end_time: e.target.value })}
                    placeholder="18:00"
                    className="text-sm"
                  />
                </div>
              </div>
              {aiFormData.schedule_start_time && aiFormData.schedule_end_time && (
                <p className="text-xs text-blue-600 mt-2">
                  🕐 IA ativa de <strong>{aiFormData.schedule_start_time}</strong> até <strong>{aiFormData.schedule_end_time}</strong>
                </p>
              )}
            </div>

            {!aiFormData.is_active && (
              <div className="bg-yellow-50 border border-yellow-300 rounded p-3">
                <p className="text-sm text-yellow-800">
                  ⚠️ <strong>IA Desativada:</strong> Os tickets deste departamento NÃO serão atendidos automaticamente pela IA.
                </p>
              </div>
            )}

            {/* Info Box */}
            {editingAI?.ai_agent_id && (
              <div className="bg-blue-50 border border-blue-200 rounded p-3">
                <p className="text-sm text-blue-800">
                  ✅ Este departamento já possui um agente IA configurado. As alterações atualizarão o agente existente.
                </p>
              </div>
            )}

            {!editingAI?.ai_agent_id && (
              <div className="bg-green-50 border border-green-200 rounded p-3">
                <p className="text-sm text-green-800">
                  ✨ Um novo agente IA será criado e vinculado automaticamente a este departamento.
                </p>
              </div>
            )}

            {/* Botões */}
            <div className="flex gap-2 justify-between pt-4 border-t">
              <div>
                {editingAI?.ai_agent_id && (
                  <Button
                    onClick={handleDeleteAI}
                    variant="outline"
                    className="text-red-600 hover:bg-red-50 border-red-300"
                  >
                    🗑️ Desvincular IA
                  </Button>
                )}
              </div>
              
              <div className="flex gap-2">
                <Button
                  onClick={() => setShowAIDialog(false)}
                  variant="outline"
                >
                  Cancelar
                </Button>
                <Button
                  onClick={handleSaveAI}
                  className="bg-purple-600 hover:bg-purple-700"
                >
                  <Bot className="w-4 h-4 mr-2" />
                  {editingAI?.ai_agent_id ? 'Atualizar IA' : 'Criar e Vincular IA'}
                </Button>
              </div>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Dialog: Sistema de Aprendizado */}
      <Dialog open={showLearningDialog} onOpenChange={setShowLearningDialog}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Sparkles className="w-6 h-6 text-blue-600" />
              Sistema de Aprendizado - {editingLearning?.name}
            </DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4 mt-4">
            {!editingLearning?.ai_agent_id && (
              <div className="bg-yellow-50 border border-yellow-300 rounded p-4">
                <p className="text-sm text-yellow-800">
                  ⚠️ Este departamento não tem um agente IA configurado. Configure primeiro para habilitar o aprendizado.
                </p>
              </div>
            )}

            {editingLearning?.ai_agent_id && (
              <>
                <div className="bg-blue-50 border border-blue-200 rounded p-4">
                  <h4 className="font-semibold text-blue-900 mb-2">📚 Como funciona o Aprendizado Contínuo</h4>
                  <ul className="text-sm text-blue-800 space-y-1">
                    <li>• A IA registra todas as interações e respostas geradas</li>
                    <li>• Você pode marcar cada resposta como CORRETA ou ERRADA</li>
                    <li>• Respostas marcadas como CORRETAS reforçam o aprendizado</li>
                    <li>• Respostas marcadas como ERRADAS são usadas para melhorar</li>
                    <li>• A IA aprende continuamente com seu feedback</li>
                  </ul>
                </div>

                {/* Lista de Aprendizados */}
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <h4 className="font-semibold text-gray-900">Histórico de Interações</h4>
                    <Button
                      onClick={handleAddManualLearning}
                      size="sm"
                      className="bg-green-600 hover:bg-green-700"
                    >
                      <Plus className="w-3 h-3 mr-1" />
                      Adicionar Exemplo
                    </Button>
                  </div>
                  
                  {learningData.length === 0 ? (
                    <div className="text-center py-8 text-gray-500">
                      <Sparkles className="w-12 h-12 mx-auto mb-2 opacity-50" />
                      <p>Nenhuma interação registrada ainda</p>
                      <p className="text-xs mt-1">As interações aparecerão aqui conforme a IA responder clientes</p>
                    </div>
                  ) : (
                    learningData.map((learning, idx) => (
                      <Card key={learning.id || idx} className="p-4">
                        <div className="space-y-3">
                          {/* Pergunta do Cliente */}
                          <div className="bg-gray-50 rounded p-3">
                            <p className="text-xs text-gray-600 mb-1">👤 Cliente perguntou:</p>
                            <p className="text-sm font-medium">{learning.user_message}</p>
                          </div>

                          {/* Resposta da IA */}
                          <div className="bg-blue-50 rounded p-3">
                            <p className="text-xs text-blue-600 mb-1">🤖 IA respondeu:</p>
                            <p className="text-sm">{learning.ai_response}</p>
                          </div>

                          {/* Áudio (se existir) */}
                          {learning.audio_url && (
                            <div className="flex items-center gap-2 p-2 bg-purple-50 rounded">
                              <Volume2 className="w-4 h-4 text-purple-600" />
                              <span className="text-xs text-purple-700">Áudio disponível</span>
                              <Button
                                size="sm"
                                variant="ghost"
                                onClick={() => {
                                  const audio = new Audio(learning.audio_url);
                                  audio.play();
                                  toast.info('🔊 Reproduzindo áudio...');
                                }}
                                className="ml-auto"
                              >
                                <Play className="w-3 h-3 mr-1" />
                                Ouvir
                              </Button>
                            </div>
                          )}

                          {/* Feedback */}
                          <div className="flex items-center gap-2 pt-2 border-t">
                            <span className="text-xs text-gray-600">Esta resposta está:</span>
                            
                            <Button
                              size="sm"
                              variant={learning.feedback === 'correct' ? 'default' : 'outline'}
                              onClick={() => handleSaveLearningFeedback(learning.id, true)}
                              className={learning.feedback === 'correct' ? 'bg-green-600 hover:bg-green-700' : ''}
                            >
                              <ThumbsUp className="w-3 h-3 mr-1" />
                              CORRETA
                            </Button>
                            
                            <Button
                              size="sm"
                              variant={learning.feedback === 'incorrect' ? 'default' : 'outline'}
                              onClick={() => handleSaveLearningFeedback(learning.id, false)}
                              className={learning.feedback === 'incorrect' ? 'bg-red-600 hover:bg-red-700' : ''}
                            >
                              <ThumbsDown className="w-3 h-3 mr-1" />
                              ERRADA
                            </Button>

                            {learning.feedback && (
                              <span className="ml-auto text-xs text-gray-500">
                                {learning.feedback === 'correct' ? '✅ Marcada como correta' : '❌ Marcada como errada'}
                              </span>
                            )}
                          </div>

                          {/* Metadados */}
                          <div className="text-xs text-gray-400 flex gap-4">
                            <span>📅 {new Date(learning.created_at).toLocaleString('pt-BR')}</span>
                            {learning.client_name && <span>👤 {learning.client_name}</span>}
                          </div>
                        </div>
                      </Card>
                    ))
                  )}
                </div>

                {/* Estatísticas */}
                {learningData.length > 0 && (
                  <Card className="p-4 bg-gradient-to-r from-green-50 to-blue-50">
                    <h4 className="font-semibold mb-2">📊 Estatísticas de Aprendizado</h4>
                    <div className="grid grid-cols-3 gap-4 text-center">
                      <div>
                        <p className="text-2xl font-bold text-blue-600">
                          {learningData.length}
                        </p>
                        <p className="text-xs text-gray-600">Total de interações</p>
                      </div>
                      <div>
                        <p className="text-2xl font-bold text-green-600">
                          {learningData.filter(l => l.feedback === 'correct').length}
                        </p>
                        <p className="text-xs text-gray-600">Respostas corretas</p>
                      </div>
                      <div>
                        <p className="text-2xl font-bold text-red-600">
                          {learningData.filter(l => l.feedback === 'incorrect').length}
                        </p>
                        <p className="text-xs text-gray-600">Respostas erradas</p>
                      </div>
                    </div>
                  </Card>
                )}
              </>
            )}
          </div>
        </DialogContent>
      </Dialog>

      {/* Dialog: Configuração de Limpeza de Memória da IA */}
      <Dialog open={showMemoryCleanupDialog} onOpenChange={setShowMemoryCleanupDialog}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Database className="w-5 h-5 text-purple-600" />
              Limpeza de Memória da IA - {editingMemoryCleanup?.name}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
              <h4 className="font-semibold text-purple-900 mb-2">🧠 Como funciona a Memória da IA</h4>
              <ul className="text-sm text-purple-800 space-y-1">
                <li>• A IA guarda as últimas <strong>200 mensagens</strong> de cada conversa</li>
                <li>• Isso permite que ela lembre do contexto e não faça perguntas repetidas</li>
                <li>• Você pode configurar a limpeza automática de conversas antigas</li>
                <li>• Conversas limpas não afetam conversas ativas</li>
              </ul>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Limpar conversas após quantos dias?
              </label>
              <select
                value={memoryCleanupDays || ''}
                onChange={(e) => setMemoryCleanupDays(e.target.value === '' ? null : parseInt(e.target.value))}
                className="w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-purple-500"
              >
                <option value="">Nunca limpar (manter sempre)</option>
                <option value="7">7 dias</option>
                <option value="15">15 dias</option>
                <option value="30">30 dias (recomendado)</option>
                <option value="60">60 dias</option>
                <option value="90">90 dias</option>
              </select>
              <p className="text-xs text-gray-500 mt-1">
                {memoryCleanupDays === null || memoryCleanupDays === 0
                  ? '⚠️ Conversas serão mantidas indefinidamente (pode consumir muito espaço)'
                  : `✅ Conversas com mais de ${memoryCleanupDays} dias serão removidas automaticamente`}
              </p>
            </div>

            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
              <p className="text-sm text-yellow-800">
                <strong>💡 Recomendação:</strong> 30 dias é ideal para manter o contexto recente sem ocupar muito espaço.
              </p>
            </div>

            <div className="flex gap-2 pt-4">
              <Button
                variant="outline"
                onClick={() => setShowMemoryCleanupDialog(false)}
                className="flex-1"
              >
                Cancelar
              </Button>
              <Button
                onClick={handleSaveMemoryCleanup}
                className="flex-1 bg-purple-600 hover:bg-purple-700"
              >
                Salvar Configuração
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default DepartmentsManager;
