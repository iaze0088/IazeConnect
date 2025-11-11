import React, { useState, useEffect } from 'react';
import { Plus, Bot, Edit, Trash2, Power, PowerOff, Brain, TrendingUp, Check, X, Mic } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Textarea } from '@/components/ui/textarea';
import api from '@/lib/api';
import { toast } from 'sonner';
import AITrainingManager from './AITrainingManager';

const AIAgentsManager = () => {
  const [agents, setAgents] = useState([]);
  const [allAgentsUsers, setAllAgentsUsers] = useState([]); // Lista de atendentes disponíveis
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showTemplatesDialog, setShowTemplatesDialog] = useState(false);
  const [showConfigDialog, setShowConfigDialog] = useState(false);
  const [showLinkAgentsDialog, setShowLinkAgentsDialog] = useState(false);
  const [agentToLink, setAgentToLink] = useState(null);
  const [selectedAgentsUsers, setSelectedAgentsUsers] = useState([]);
  const [newAgentName, setNewAgentName] = useState('');
  const [newAgentDesc, setNewAgentDesc] = useState('');
  const [templates, setTemplates] = useState({});
  const [showLearningDialog, setShowLearningDialog] = useState(false);
  const [learningAgent, setLearningAgent] = useState(null);
  const [learningFeedbacks, setLearningFeedbacks] = useState([]);
  const [learningStats, setLearningStats] = useState(null);
  const [showTrainingDialog, setShowTrainingDialog] = useState(false);
  const [trainingAgent, setTrainingAgent] = useState(null);

  useEffect(() => {
    loadAgents();
    loadAllAgentsUsers();
    loadTemplates();
  }, []);
  
  const loadTemplates = async () => {
    try {
      const { data } = await api.get('/ai/agents/templates/list');
      setTemplates(data || {});
    } catch (error) {
      console.error('Error loading templates:', error);
      setTemplates({});
    }
  };
  
  const loadAllAgentsUsers = async () => {
    try {
      const { data } = await api.get('/agents');
      setAllAgentsUsers(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Error loading agents users:', error);
      setAllAgentsUsers([]);
    }
  };

  const loadAgents = async () => {
    try {
      const { data } = await api.get('/ai/agents');
      setAgents(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Error loading agents:', error);
      setAgents([]);
      toast.error('Erro ao carregar agentes');
    }
  };

  const handleCreateAgent = async () => {
    if (!newAgentName.trim()) {
      toast.error('Digite um nome para o agente');
      return;
    }

    try {
      await api.post('/ai/agents', {
        name: newAgentName,
        description: newAgentDesc,
        llm_provider: 'openai',
        llm_model: 'gpt-4o-mini'
      });
      toast.success('Agente criado com sucesso!');
      setShowCreateDialog(false);
      setNewAgentName('');
      setNewAgentDesc('');
      loadAgents();
    } catch (error) {
      toast.error('Erro ao criar agente');
    }
  };

  const handleCreateFromTemplate = async (templateName) => {
    try {
      await api.post(`/ai/agents/templates/${templateName}`);
      toast.success('Agente criado a partir do template!');
      setShowTemplatesDialog(false);
      loadAgents();
    } catch (error) {
      toast.error('Erro ao criar agente do template');
      console.error('Template error:', error);
    }
  };

  const handleDeleteAgent = async (agentId) => {
    if (!confirm('Tem certeza que deseja deletar este agente?')) return;

    try {
      await api.delete(`/ai/agents/${agentId}`);
      toast.success('Agente deletado!');
      loadAgents();
    } catch (error) {
      toast.error('Erro ao deletar agente');
    }
  };

  const handleToggleActive = async (agent) => {
    try {
      // Toggle direto do status enabled (campo correto no backend)
      await api.put(`/ai/agents/${agent.id}`, {
        enabled: !agent.enabled
      });
      toast.success(agent.enabled ? 'Agente desativado!' : 'Agente ativado!');
      loadAgents();
    } catch (error) {
      toast.error('Erro ao alterar status do agente');
      console.error('Erro:', error);
    }
  };
  
  const handleSaveLinkAgents = async () => {
    try {
      await api.put(`/ai/agents/${agentToLink.id}`, {
        is_active: selectedAgentsUsers.length > 0, // Ativo se tiver atendentes vinculados
        linked_agents: selectedAgentsUsers
      });
      toast.success('Atendentes vinculados com sucesso!');
      setShowLinkAgentsDialog(false);
      loadAgents();
    } catch (error) {
      toast.error('Erro ao vincular atendentes');
    }
  };
  
  const toggleAgentUser = (agentUserId) => {
    setSelectedAgentsUsers(prev => 
      prev.includes(agentUserId) 
        ? prev.filter(id => id !== agentUserId)
        : [...prev, agentUserId]
    );
  };

  // Funções do Sistema de Aprendizado
  const loadLearningData = async (agentId) => {
    try {
      // Carregar feedbacks
      const { data: feedbackData } = await api.get('/ai-learning/feedback', {
        params: { agent_id: agentId, limit: 50 }
      });
      setLearningFeedbacks(feedbackData.feedbacks || []);

      // Carregar estatísticas
      const { data: statsData } = await api.get(`/ai-learning/stats/${agentId}`);
      setLearningStats(statsData);
    } catch (error) {
      console.error('Error loading learning data:', error);
      toast.error('Erro ao carregar dados de aprendizado');
    }
  };

  const handleOpenLearning = async (agent) => {
    setLearningAgent(agent);
    setShowLearningDialog(true);
    await loadLearningData(agent.agent_id);
  };

  const handleOpenTraining = (agent) => {
    setTrainingAgent(agent);
    setShowTrainingDialog(true);
  };

  const handleApproveFeedback = async (feedbackId, approve) => {
    try {
      await api.put(`/ai-learning/feedback/${feedbackId}`, {
        aprovado_admin: approve
      });
      toast.success(approve ? 'Feedback aprovado!' : 'Feedback reprovado!');
      await loadLearningData(learningAgent.id);
    } catch (error) {
      toast.error('Erro ao atualizar feedback');
    }
  };

  const handleDeleteFeedback = async (feedbackId) => {
    if (!confirm('Tem certeza que deseja deletar este feedback?')) return;
    try {
      await api.delete(`/ai-learning/feedback/${feedbackId}`);
      toast.success('Feedback deletado!');
      await loadLearningData(learningAgent.id);
    } catch (error) {
      toast.error('Erro ao deletar feedback');
    }
  };

  const handleClearAllLearning = async (agentId) => {
    if (!confirm('⚠️ ATENÇÃO! Isso irá deletar TODOS os feedbacks de aprendizado deste agente. Esta ação não pode ser desfeita. Deseja continuar?')) return;
    try {
      await api.delete(`/ai-learning/feedback/agent/${agentId}/all`);
      toast.success('Todo aprendizado foi limpo!');
      setShowLearningDialog(false);
      setLearningFeedbacks([]);
      setLearningStats(null);
    } catch (error) {
      toast.error('Erro ao limpar aprendizado');
    }
  };

  return (
    <>
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-slate-900 mb-2">🤖 Explore os Super Agentes</h2>
        <p className="text-slate-600 mb-4">Crie os seus Super Agentes</p>
        <p className="text-sm text-slate-500 mb-6">Gerencie seus agentes para automatizar tarefas de forma inteligente.</p>
        
        <Button 
          onClick={() => setShowTemplatesDialog(true)}
          className="bg-indigo-600 hover:bg-indigo-700"
        >
          <Plus className="w-4 h-4 mr-2" />
          Novo agente +
        </Button>
      </div>

      {/* Lista de Agentes */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {(agents || []).map(agent => (
          <Card 
            key={agent.id}
            className="p-4 hover:shadow-lg transition-shadow cursor-pointer"
          >
            <div className="flex items-start justify-between mb-3">
              <div className="flex items-center gap-2">
                <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                  agent.is_active ? 'bg-indigo-100' : 'bg-slate-100'
                }`}>
                  <Bot className={`w-5 h-5 ${agent.is_active ? 'text-indigo-600' : 'text-slate-400'}`} />
                </div>
                <div>
                  <h3 className="font-semibold text-slate-900">{agent.name}</h3>
                  <p className="text-xs text-slate-500">{agent.llm_model}</p>
                </div>
              </div>
              
              <div className="flex gap-1">
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleToggleActive(agent);
                  }}
                  title={agent.enabled ? 'Desativar' : 'Ativar'}
                >
                  {agent.enabled ? (
                    <Power className="w-4 h-4 text-green-600" />
                  ) : (
                    <PowerOff className="w-4 h-4 text-slate-400" />
                  )}
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleOpenLearning(agent);
                  }}
                  title="Sistema de Aprendizado"
                  className="text-purple-600 hover:text-purple-700"
                >
                  <Brain className="w-4 h-4" />
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleOpenTraining(agent);
                  }}
                  title="Treinamento (Áudio)"
                  className="text-blue-600 hover:text-blue-700"
                >
                  <Mic className="w-4 h-4" />
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={(e) => {
                    e.stopPropagation();
                    setSelectedAgent(agent);
                    setShowConfigDialog(true);
                  }}
                >
                  <Edit className="w-4 h-4" />
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDeleteAgent(agent.id);
                  }}
                >
                  <Trash2 className="w-4 h-4 text-red-500" />
                </Button>
              </div>
            </div>
            
            <p className="text-sm text-slate-600 mb-2">{agent.description || 'Sem descrição'}</p>
            
            <div className="flex items-center justify-between text-xs text-slate-500">
              <span>{agent.llm_provider}</span>
              <span className={`px-2 py-1 rounded ${
                agent.enabled ? 'bg-green-100 text-green-700' : 'bg-slate-100 text-slate-500'
              }`}>
                {agent.enabled ? 'Ativo' : 'Inativo'}
              </span>
            </div>
          </Card>
        ))}
      </div>

      {/* Dialog: Escolher Template ou Criar Manual */}
      <Dialog open={showTemplatesDialog} onOpenChange={setShowTemplatesDialog}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="text-2xl">🤖 Criar Novo Agente IA</DialogTitle>
            <p className="text-slate-600 text-sm mt-2">
              Escolha um template pré-configurado ou crie um agente do zero
            </p>
          </DialogHeader>

          <div className="space-y-6">
            {/* Botão criar manual */}
            <div className="bg-gradient-to-r from-indigo-50 to-purple-50 p-6 rounded-lg border-2 border-indigo-200 hover:border-indigo-400 transition-colors cursor-pointer"
              onClick={() => {
                setShowTemplatesDialog(false);
                setShowCreateDialog(true);
              }}
            >
              <div className="flex items-center gap-4">
                <div className="w-16 h-16 bg-indigo-600 rounded-lg flex items-center justify-center">
                  <Plus className="w-8 h-8 text-white" />
                </div>
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-slate-900">✨ Criar do Zero</h3>
                  <p className="text-sm text-slate-600">Configure todas as opções manualmente</p>
                </div>
              </div>
            </div>

            {/* Templates pré-configurados */}
            <div>
              <h3 className="text-lg font-semibold text-slate-900 mb-4">📋 Templates Prontos</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {Object.entries(templates).map(([key, description]) => {
                  // Extrair emoji e título da descrição
                  const parts = description.split(' - ');
                  const emoji = parts[0];
                  const title = parts[1]?.split(' - ')[0] || parts[0];
                  const subtitle = parts[1]?.split(' - ')[1] || parts[1] || '';
                  
                  return (
                    <div
                      key={key}
                      onClick={() => handleCreateFromTemplate(key)}
                      className="p-4 border-2 border-slate-200 rounded-lg hover:border-indigo-400 hover:bg-indigo-50 transition-all cursor-pointer group"
                    >
                      <div className="flex items-start gap-3">
                        <div className="text-3xl">{emoji}</div>
                        <div className="flex-1">
                          <h4 className="font-semibold text-slate-900 group-hover:text-indigo-900">
                            {title}
                          </h4>
                          <p className="text-sm text-slate-600 mt-1">{subtitle}</p>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          <div className="flex justify-end mt-6">
            <Button variant="outline" onClick={() => setShowTemplatesDialog(false)}>
              Cancelar
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Dialog: Criar Novo Agente */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Criar Novo Agente IA</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium mb-2 block">Nome do Agente</label>
              <Input
                placeholder="Ex: Agente de Suporte"
                value={newAgentName}
                onChange={(e) => setNewAgentName(e.target.value)}
              />
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">Descrição</label>
              <Textarea
                placeholder="O que este agente faz?"
                value={newAgentDesc}
                onChange={(e) => setNewAgentDesc(e.target.value)}
                rows={3}
              />
            </div>
            <div className="flex gap-2">
              <Button variant="outline" onClick={() => setShowCreateDialog(false)} className="flex-1">
                Cancelar
              </Button>
              <Button onClick={handleCreateAgent} className="flex-1 bg-indigo-600 hover:bg-indigo-700">
                Criar Agente
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Dialog: Configurar Agente */}
      {selectedAgent && (
        <AgentConfigDialog
          agent={selectedAgent}
          open={showConfigDialog}
          onClose={() => {
            setShowConfigDialog(false);
            setSelectedAgent(null);
            loadAgents();
          }}
        />
      )}
      
      {/* Dialog para vincular atendentes */}
      <Dialog open={showLinkAgentsDialog} onOpenChange={setShowLinkAgentsDialog}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>⚡ Ativar/Desativar Agente IA</DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <p className="text-sm text-blue-900">
                <strong>Agente:</strong> {agentToLink?.name}
              </p>
              <p className="text-sm text-blue-700 mt-2">
                Selecione os atendentes que terão este agente IA ativo. Quando um atendente selecionado receber uma mensagem, a IA responderá automaticamente.
              </p>
            </div>
            
            <div>
              <h4 className="font-semibold mb-3">Selecione os Atendentes:</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {allAgentsUsers.map(agentUser => (
                  <div
                    key={agentUser.id}
                    className={`p-3 border-2 rounded-lg cursor-pointer transition-all ${
                      selectedAgentsUsers.includes(agentUser.id)
                        ? 'border-indigo-600 bg-indigo-50'
                        : 'border-slate-200 hover:border-indigo-300'
                    }`}
                    onClick={() => toggleAgentUser(agentUser.id)}
                  >
                    <div className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={selectedAgentsUsers.includes(agentUser.id)}
                        readOnly
                        className="w-4 h-4"
                      />
                      <div>
                        <p className="font-medium">{agentUser.name}</p>
                        <p className="text-xs text-slate-600">{agentUser.email}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              
              {allAgentsUsers.length === 0 && (
                <p className="text-sm text-slate-500 text-center py-4">
                  Nenhum atendente cadastrado. Crie atendentes primeiro.
                </p>
              )}
            </div>
            
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
              <p className="text-xs text-yellow-800">
                💡 <strong>Dica:</strong> A IA só funcionará para os atendentes selecionados. 
                Se nenhum atendente for selecionado, o agente ficará desativado.
              </p>
            </div>
            
            <div className="flex gap-2">
              <Button
                variant="outline"
                onClick={() => setShowLinkAgentsDialog(false)}
                className="flex-1"
              >
                Cancelar
              </Button>
              <Button
                onClick={handleSaveLinkAgents}
                className="flex-1 bg-indigo-600 hover:bg-indigo-700"
              >
                💾 Salvar ({selectedAgentsUsers.length} selecionados)
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Dialog: Sistema de Aprendizado */}
      <Dialog open={showLearningDialog} onOpenChange={setShowLearningDialog}>
        <DialogContent className="max-w-5xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="text-xl flex items-center gap-2">
              <Brain className="w-6 h-6 text-purple-600" />
              Sistema de Aprendizado - {learningAgent?.name}
            </DialogTitle>
          </DialogHeader>

          {/* Estatísticas */}
          {learningStats && (
            <div className="grid grid-cols-4 gap-4 mb-6">
              <Card className="p-4 bg-gradient-to-br from-green-50 to-green-100 border-green-200">
                <div className="text-center">
                  <p className="text-sm text-green-700 font-medium">Acertos</p>
                  <p className="text-3xl font-bold text-green-800">{learningStats.total_acertos}</p>
                </div>
              </Card>
              <Card className="p-4 bg-gradient-to-br from-red-50 to-red-100 border-red-200">
                <div className="text-center">
                  <p className="text-sm text-red-700 font-medium">Erros</p>
                  <p className="text-3xl font-bold text-red-800">{learningStats.total_erros}</p>
                </div>
              </Card>
              <Card className="p-4 bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200">
                <div className="text-center">
                  <p className="text-sm text-blue-700 font-medium">Total</p>
                  <p className="text-3xl font-bold text-blue-800">{learningStats.total_feedbacks}</p>
                </div>
              </Card>
              <Card className="p-4 bg-gradient-to-br from-purple-50 to-purple-100 border-purple-200">
                <div className="text-center">
                  <p className="text-sm text-purple-700 font-medium">Taxa de Sucesso</p>
                  <p className="text-3xl font-bold text-purple-800">{learningStats.taxa_sucesso}%</p>
                </div>
              </Card>
            </div>
          )}

          {/* Lista de Feedbacks */}
          <div className="space-y-3">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-slate-900">Histórico de Feedbacks</h3>
              <Button
                variant="destructive"
                size="sm"
                onClick={() => handleClearAllLearning(learningAgent?.id)}
                className="bg-red-600 hover:bg-red-700"
              >
                🗑️ Limpar Todo Aprendizado
              </Button>
            </div>

            {learningFeedbacks.length === 0 ? (
              <div className="text-center py-12 text-slate-500">
                <Brain className="w-16 h-16 mx-auto mb-3 opacity-30" />
                <p className="text-sm">Nenhum feedback registrado ainda</p>
                <p className="text-xs mt-1">Os feedbacks aparecerão aqui conforme o sistema aprende</p>
              </div>
            ) : (
              learningFeedbacks.map((feedback) => (
                <Card
                  key={feedback.id}
                  className={`p-4 ${
                    feedback.tipo === 'acerto' 
                      ? 'border-green-200 bg-green-50/50' 
                      : 'border-red-200 bg-red-50/50'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <span className={`px-2 py-1 rounded-full text-xs font-semibold ${
                          feedback.tipo === 'acerto'
                            ? 'bg-green-200 text-green-800'
                            : 'bg-red-200 text-red-800'
                        }`}>
                          {feedback.tipo === 'acerto' ? '✅ Acerto' : '❌ Erro'}
                        </span>
                        <span className="text-xs text-slate-600">
                          {feedback.categoria}
                        </span>
                        <span className="text-xs text-slate-400">
                          {new Date(feedback.created_at).toLocaleString('pt-BR')}
                        </span>
                        {feedback.aprovado_admin && (
                          <span className="px-2 py-0.5 bg-purple-200 text-purple-800 rounded text-xs font-medium">
                            ⭐ Aprovado
                          </span>
                        )}
                      </div>

                      <p className="text-sm text-slate-700 mb-2">
                        <strong>Resultado:</strong> {feedback.resultado}
                      </p>

                      {feedback.contexto && (
                        <div className="bg-white rounded p-2 text-xs">
                          <p className="text-slate-600">
                            <strong>Contexto:</strong> {JSON.stringify(feedback.contexto, null, 2)}
                          </p>
                        </div>
                      )}

                      <p className="text-xs text-slate-500 mt-2">
                        Marcado por: {feedback.marcado_por}
                      </p>
                    </div>

                    <div className="flex flex-col gap-1 ml-3">
                      {!feedback.aprovado_admin && (
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => handleApproveFeedback(feedback.id, true)}
                          className="h-8 px-2 text-green-600 hover:bg-green-100"
                          title="Aprovar feedback"
                        >
                          <Check className="w-4 h-4" />
                        </Button>
                      )}
                      {feedback.aprovado_admin && (
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => handleApproveFeedback(feedback.id, false)}
                          className="h-8 px-2 text-orange-600 hover:bg-orange-100"
                          title="Reprovar feedback"
                        >
                          <X className="w-4 h-4" />
                        </Button>
                      )}
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => handleDeleteFeedback(feedback.id)}
                        className="h-8 px-2 text-red-600 hover:bg-red-100"
                        title="Deletar feedback"
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                </Card>
              ))
            )}
          </div>

          <div className="flex justify-end mt-6">
            <Button onClick={() => setShowLearningDialog(false)} variant="outline">
              Fechar
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Dialog: Treinamento por Áudio */}
      <TrainingDialog
        open={showTrainingDialog}
        onClose={() => setShowTrainingDialog(false)}
        agent={trainingAgent}
      />
    </div>
    </>
  );
};

// Componente de Configuração do Agente (com abas)
const AgentConfigDialog = ({ agent, open, onClose }) => {
  const [config, setConfig] = useState(agent);
  const [showKeyTutorial, setShowKeyTutorial] = useState(false);

  // Atualizar config quando agent mudar ou dialog abrir
  useEffect(() => {
    if (open && agent) {
      setConfig(agent);
    }
  }, [open, agent]);

  const handleSave = async () => {
    try {
      await api.put(`/ai/agents/${agent.id}`, config);
      toast.success('Configurações salvas!');
      onClose();
      // Recarregar a página ou lista de agentes após salvar
      window.location.reload();
    } catch (error) {
      toast.error('Erro ao salvar configurações');
      console.error('Erro ao salvar:', error);
    }
  };

  // Calcular tamanho total do prompt
  const calculateTotalPromptSize = () => {
    const fields = [
      config.who_is || '',
      config.what_does || '',
      config.objective || '',
      config.how_respond || '',
      config.instructions || '',
      config.avoid_topics || '',
      config.avoid_words || '',
      config.allowed_links || '',
      config.custom_rules || '',
      config.knowledge_base || ''
    ];
    return fields.reduce((sum, field) => sum + field.length, 0);
  };

  const totalSize = calculateTotalPromptSize();

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-xl">⚙️ Configurar: {agent.name}</DialogTitle>
        </DialogHeader>

        {/* Aviso de tamanho total */}
        {totalSize > 0 && (
          <div className={`p-3 rounded-lg border ${
            totalSize > 100000 ? 'bg-red-50 border-red-200' :
            totalSize > 50000 ? 'bg-yellow-50 border-yellow-200' :
            'bg-blue-50 border-blue-200'
          }`}>
            <div className="flex items-center justify-between">
              <div>
                <p className={`text-sm font-semibold ${
                  totalSize > 100000 ? 'text-red-800' :
                  totalSize > 50000 ? 'text-yellow-800' :
                  'text-blue-800'
                }`}>
                  {totalSize > 100000 ? '⚠️ Prompt MUITO GRANDE' :
                   totalSize > 50000 ? '💡 Prompt Grande' :
                   '✅ Tamanho do Prompt'
                  }
                </p>
                <p className={`text-xs ${
                  totalSize > 100000 ? 'text-red-700' :
                  totalSize > 50000 ? 'text-yellow-700' :
                  'text-blue-700'
                }`}>
                  Total: {totalSize.toLocaleString()} caracteres
                  {totalSize > 100000 && ' - Recomendamos reduzir para evitar erros!'}
                </p>
              </div>
              <div className={`text-2xl ${
                totalSize > 100000 ? 'text-red-600' :
                totalSize > 50000 ? 'text-yellow-600' :
                'text-blue-600'
              }`}>
                {totalSize > 100000 ? '🔴' : totalSize > 50000 ? '🟡' : '🟢'}
              </div>
            </div>
          </div>
        )}

        <Tabs defaultValue="prompt" className="w-full">
          <TabsList className="grid grid-cols-4 mb-4">
            <TabsTrigger value="prompt">Instruções</TabsTrigger>
            <TabsTrigger value="knowledge">Base de Conhecimento</TabsTrigger>
            <TabsTrigger value="model">Tecnologia</TabsTrigger>
            <TabsTrigger value="behavior">Comportamento</TabsTrigger>
          </TabsList>

          {/* Aba: Instruções */}
          <TabsContent value="prompt" className="space-y-4">
            <div className="bg-gradient-to-r from-indigo-50 to-purple-50 p-4 rounded-lg mb-4">
              <h3 className="font-semibold text-indigo-900 mb-2">📝 Configurações do Prompt</h3>
              <p className="text-sm text-indigo-700">Personalize o prompt do seu Agente</p>
            </div>

            <div className="bg-white border rounded-lg p-4 space-y-4">
              <h4 className="font-semibold text-slate-900 mb-3">Informações Essenciais</h4>
              
              <div>
                <label className="text-sm font-medium mb-2 block">Quem é o seu Agente?</label>
                <Input
                  placeholder="Ex: Sou um assistente especializado em suporte técnico"
                  value={config.who_is || ''}
                  onChange={(e) => setConfig({ ...config, who_is: e.target.value })}
                />
              </div>

              <div>
                <label className="text-sm font-medium mb-2 block">O que seu Agente faz?</label>
                <Input
                  placeholder="Ex: Ajudo clientes com problemas técnicos e dúvidas"
                  value={config.what_does || ''}
                  onChange={(e) => setConfig({ ...config, what_does: e.target.value })}
                />
              </div>

              <div>
                <label className="text-sm font-medium mb-2 block">Qual o objetivo do seu Agente?</label>
                <Input
                  placeholder="Ex: Resolver problemas rapidamente e com clareza"
                  value={config.objective || ''}
                  onChange={(e) => setConfig({ ...config, objective: e.target.value })}
                />
              </div>

              <div>
                <label className="text-sm font-medium mb-2 block">Como seu Agente deve responder?</label>
                <Textarea
                  placeholder="Ex: De forma clara, objetiva e amigável"
                  value={config.how_respond || ''}
                  onChange={(e) => setConfig({ ...config, how_respond: e.target.value })}
                  rows={3}
                />
              </div>
            </div>

            <div className="bg-white border rounded-lg p-4 space-y-4">
              <h4 className="font-semibold text-slate-900 mb-3">Regras Gerais</h4>
              
              <div>
                <div className="flex justify-between items-center mb-2">
                  <label className="text-sm font-medium block">Instruções para o Agente</label>
                  <span className={`text-xs ${(config.instructions || '').length > 50000 ? 'text-red-600 font-bold' : 'text-slate-500'}`}>
                    {(config.instructions || '').length.toLocaleString()} caracteres
                  </span>
                </div>
                <Textarea
                  placeholder="Instruções específicas de como agir&#10;&#10;Você pode usar quebras de linha (Enter) normalmente.&#10;&#10;Exemplo:&#10;- Sempre seja educado&#10;- Responda com clareza&#10;- Não use termos técnicos"
                  value={config.instructions || ''}
                  onChange={(e) => setConfig({ ...config, instructions: e.target.value })}
                  rows={10}
                  className="font-mono text-sm resize-y min-h-[200px]"
                  style={{ whiteSpace: 'pre-wrap' }}
                />
                {(config.instructions || '').length > 50000 && (
                  <div className="mt-2 p-3 bg-red-50 border border-red-200 rounded-lg">
                    <p className="text-sm text-red-800">
                      ⚠️ <strong>Atenção:</strong> Prompt muito grande ({(config.instructions || '').length.toLocaleString()} caracteres). 
                      Recomendamos manter abaixo de 50.000 caracteres para evitar erros.
                    </p>
                  </div>
                )}
                {(config.instructions || '').length > 20000 && (config.instructions || '').length <= 50000 && (
                  <div className="mt-2 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                    <p className="text-sm text-yellow-800">
                      💡 <strong>Dica:</strong> Seu prompt está grande ({(config.instructions || '').length.toLocaleString()} caracteres). 
                      Considere otimizar removendo repetições.
                    </p>
                  </div>
                )}
              </div>

              <div>
                <label className="text-sm font-medium mb-2 block">Quais temas ele deve evitar?</label>
                <Input
                  placeholder="Ex: Política, religião, assuntos pessoais"
                  value={config.avoid_topics || ''}
                  onChange={(e) => setConfig({ ...config, avoid_topics: e.target.value })}
                />
              </div>

              <div>
                <label className="text-sm font-medium mb-2 block">Quais palavras ele deve evitar?</label>
                <Input
                  placeholder="Ex: palavrões, termos ofensivos"
                  value={config.avoid_words || ''}
                  onChange={(e) => setConfig({ ...config, avoid_words: e.target.value })}
                />
              </div>

              <div>
                <label className="text-sm font-medium mb-2 block">Links permitidos:</label>
                <Textarea
                  placeholder="Cole os links que o agente pode compartilhar (um por linha)"
                  value={config.allowed_links || ''}
                  onChange={(e) => setConfig({ ...config, allowed_links: e.target.value })}
                  rows={3}
                  className="font-mono text-sm"
                />
              </div>

              <div>
                <div className="flex justify-between items-center mb-2">
                  <label className="text-sm font-medium block">Regras personalizadas:</label>
                  <span className={`text-xs ${(config.custom_rules || '').length > 30000 ? 'text-orange-600 font-bold' : 'text-slate-500'}`}>
                    {(config.custom_rules || '').length.toLocaleString()} caracteres
                  </span>
                </div>
                <Textarea
                  placeholder="Adicione regras customizadas específicas&#10;&#10;Use quebras de linha normalmente para organizar melhor."
                  value={config.custom_rules || ''}
                  onChange={(e) => setConfig({ ...config, custom_rules: e.target.value })}
                  rows={8}
                  className="font-mono text-sm resize-y min-h-[150px]"
                  style={{ whiteSpace: 'pre-wrap' }}
                />
              </div>
            </div>
          </TabsContent>

          {/* Aba: Base de Conhecimento */}
          <TabsContent value="knowledge" className="space-y-4">
            <div className="bg-gradient-to-r from-blue-50 to-cyan-50 p-4 rounded-lg mb-4">
              <h3 className="font-semibold text-blue-900 mb-2">📚 Base de Conhecimento</h3>
              <p className="text-sm text-blue-700">Adicione informações que o agente deve conhecer</p>
            </div>

            <div className="flex justify-between items-center mb-2">
              <p className="text-sm text-slate-600">
                Cole aqui textos, documentos, FAQs ou qualquer informação relevante
              </p>
              <span className={`text-xs font-semibold ${
                (config.knowledge_base || '').length > 100000 ? 'text-red-600' : 
                (config.knowledge_base || '').length > 50000 ? 'text-orange-600' : 
                'text-slate-500'
              }`}>
                {(config.knowledge_base || '').length.toLocaleString()} caracteres
              </span>
            </div>

            <Textarea
              placeholder="Base de conhecimento do agente...&#10;&#10;Você pode colar textos grandes aqui.&#10;Use quebras de linha (Enter) normalmente para organizar o conteúdo.&#10;&#10;Exemplo:&#10;## Produtos&#10;- Produto A: descrição&#10;- Produto B: descrição&#10;&#10;## FAQ&#10;Q: Como fazer X?&#10;A: Para fazer X, siga estes passos..."
              value={config.knowledge_base || ''}
              onChange={(e) => setConfig({ ...config, knowledge_base: e.target.value })}
              rows={20}
              className="font-mono text-sm resize-y min-h-[400px]"
              style={{ whiteSpace: 'pre-wrap' }}
            />

            {(config.knowledge_base || '').length > 100000 && (
              <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-sm text-red-800 font-semibold">
                  ⚠️ Atenção: Base de conhecimento muito grande!
                </p>
                <p className="text-sm text-red-700 mt-2">
                  Seu conteúdo tem {(config.knowledge_base || '').length.toLocaleString()} caracteres.
                  Para melhor performance, recomendamos manter abaixo de 100.000 caracteres.
                </p>
              </div>
            )}

            {(config.knowledge_base || '').length > 50000 && (config.knowledge_base || '').length <= 100000 && (
              <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                <p className="text-sm text-yellow-800">
                  💡 <strong>Dica:</strong> Base de conhecimento grande ({(config.knowledge_base || '').length.toLocaleString()} caracteres).
                  Considere otimizar removendo informações duplicadas.
                </p>
              </div>
            )}

            <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <p className="text-sm text-blue-800">
                <strong>💡 Dicas para organizar:</strong>
              </p>
              <ul className="text-sm text-blue-700 mt-2 space-y-1 ml-4 list-disc">
                <li>Use títulos com ## para separar seções</li>
                <li>Use quebras de linha para melhorar legibilidade</li>
                <li>Organize por tópicos (FAQ, Produtos, Regras, etc)</li>
                <li>Evite informações redundantes</li>
              </ul>
            </div>
          </TabsContent>

          {/* Aba: Tecnologia (Modelo) */}
          <TabsContent value="model" className="space-y-4">
            <div className="bg-gradient-to-r from-purple-50 to-pink-50 p-4 rounded-lg mb-4">
              <h3 className="font-semibold text-purple-900 mb-2">🔧 Configurações do Modelo</h3>
              <p className="text-sm text-purple-700">Configure o modelo de IA que seu Agente vai utilizar</p>
            </div>

            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium mb-2 block">Provedor LLM</label>
                <select
                  value={config.llm_provider}
                  onChange={(e) => setConfig({ ...config, llm_provider: e.target.value })}
                  className="w-full border rounded-lg p-2"
                >
                  <option value="openai">OpenAI</option>
                  <option value="claude">Claude (Anthropic)</option>
                  <option value="gemini">Gemini (Google)</option>
                </select>
              </div>

              <div>
                <label className="text-sm font-medium mb-2 block">Modelo</label>
                <select
                  value={config.llm_model}
                  onChange={(e) => setConfig({ ...config, llm_model: e.target.value })}
                  className="w-full border rounded-lg p-2"
                >
                  <option value="gpt-4o-mini">GPT-4o Mini (Recomendado)</option>
                  <option value="gpt-4o">GPT-4o</option>
                  <option value="gpt-4-turbo">GPT-4 Turbo</option>
                  <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
                  <option value="claude-3-sonnet">Claude 3 Sonnet</option>
                  <option value="gemini-pro">Gemini Pro</option>
                </select>
                <p className="text-xs text-slate-500 mt-1">
                  O modelo GPT-4o oferece respostas mais precisas e segue as instruções com mais eficácia.
                </p>
              </div>

              <div>
                <label className="text-sm font-medium mb-2 block">🔑 API Key</label>
                <Input
                  type="password"
                  placeholder="sk-... ou sua Emergent LLM Key"
                  value={config.api_key || ''}
                  onChange={(e) => setConfig({ ...config, api_key: e.target.value })}
                />
                
                {/* Helper para obter Emergent Key */}
                <div className="mt-3 bg-gradient-to-r from-purple-50 to-blue-50 border-2 border-purple-200 rounded-lg p-4">
                  <div className="flex items-start gap-3">
                    <div className="flex-shrink-0 w-10 h-10 bg-purple-600 rounded-lg flex items-center justify-center">
                      <span className="text-white font-bold text-lg">E</span>
                    </div>
                    <div className="flex-1">
                      <h4 className="font-semibold text-purple-900 mb-2">
                        🎁 Não tem uma Emergent LLM Key?
                      </h4>
                      <p className="text-sm text-purple-700 mb-3">
                        A Emergent LLM Key é uma chave universal que funciona com OpenAI, Anthropic e Google.
                      </p>
                      
                      <div className="flex items-center gap-3 flex-wrap">
                        <a
                          href="https://app.emergent.sh/register?ref=noit391017"
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-2 bg-purple-600 hover:bg-purple-700 text-white px-5 py-2.5 rounded-lg font-semibold transition-all duration-200 transform hover:scale-105 shadow-lg"
                        >
                          <span>🚀</span>
                          <span>Gerar sua Chave API Key</span>
                        </a>
                        
                        <span className="text-sm text-purple-700 font-medium">
                          💡 Após criar sua conta, você receberá créditos grátis para testar!
                        </span>
                      </div>
                      
                      <button
                        onClick={() => setShowKeyTutorial(true)}
                        className="mt-3 text-sm text-purple-600 hover:text-purple-800 font-medium underline"
                      >
                        📖 Ver tutorial passo a passo
                      </button>
                    </div>
                  </div>
                </div>
                
                {/* Modal Tutorial */}
                {showKeyTutorial && (
                  <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4" onClick={() => setShowKeyTutorial(false)}>
                    <div className="bg-white rounded-xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
                      <div className="bg-gradient-to-r from-purple-600 to-blue-600 text-white p-6">
                        <div className="flex items-center gap-3 mb-2">
                          <div className="w-12 h-12 bg-white rounded-lg flex items-center justify-center">
                            <span className="text-purple-600 font-bold text-2xl">E</span>
                          </div>
                          <div>
                            <h3 className="text-2xl font-bold">Como Obter sua Emergent LLM Key</h3>
                            <p className="text-purple-100 text-sm">Tutorial passo a passo</p>
                          </div>
                        </div>
                      </div>
                      
                      <div className="p-6 space-y-6">
                        {/* Passo 1 */}
                        <div className="flex gap-4">
                          <div className="flex-shrink-0 w-10 h-10 bg-purple-600 rounded-full flex items-center justify-center text-white font-bold">
                            1
                          </div>
                          <div className="flex-1">
                            <h4 className="font-bold text-lg mb-2">Criar Conta na Emergent</h4>
                            <p className="text-gray-600 mb-3">
                              Acesse o site da Emergent e crie sua conta gratuitamente. É rápido e sem necessidade de cartão de crédito.
                            </p>
                            <a
                              href="https://app.emergent.sh/register?ref=noit391017"
                              target="_blank"
                              rel="noopener noreferrer"
                              className="inline-flex items-center gap-2 bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg font-medium transition-all"
                            >
                              <span>🔗</span>
                              <span>Ir para Registro</span>
                            </a>
                          </div>
                        </div>
                        
                        <div className="border-t border-gray-200"></div>
                        
                        {/* Passo 2 */}
                        <div className="flex gap-4">
                          <div className="flex-shrink-0 w-10 h-10 bg-purple-600 rounded-full flex items-center justify-center text-white font-bold">
                            2
                          </div>
                          <div className="flex-1">
                            <h4 className="font-bold text-lg mb-2">Acessar Dashboard</h4>
                            <p className="text-gray-600 mb-3">
                              Após criar sua conta e fazer login, você será direcionado ao dashboard da Emergent.
                            </p>
                            <div className="bg-gray-100 p-3 rounded-lg text-sm mb-3">
                              <p className="font-mono">https://emergentagent.com/dashboard</p>
                            </div>
                            <a
                              href="https://app.emergent.sh/register?ref=noit391017"
                              target="_blank"
                              rel="noopener noreferrer"
                              className="inline-flex items-center gap-2 bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg font-medium transition-all"
                            >
                              <span>🌐</span>
                              <span>ABRIR SITE</span>
                            </a>
                          </div>
                        </div>
                        
                        <div className="border-t border-gray-200"></div>
                        
                        {/* Passo 3 */}
                        <div className="flex gap-4">
                          <div className="flex-shrink-0 w-10 h-10 bg-purple-600 rounded-full flex items-center justify-center text-white font-bold">
                            3
                          </div>
                          <div className="flex-1">
                            <h4 className="font-bold text-lg mb-2">Obter Universal Key</h4>
                            <p className="text-gray-600 mb-3">
                              No menu lateral, clique em <strong>"Profile"</strong> e depois em <strong>"Universal Key"</strong>.
                            </p>
                            <div className="bg-blue-50 border-2 border-blue-200 p-4 rounded-lg">
                              <p className="font-semibold text-blue-900 mb-2">📍 Caminho:</p>
                              <p className="text-blue-700">Profile → Universal Key → Copiar Key</p>
                            </div>
                          </div>
                        </div>
                        
                        <div className="border-t border-gray-200"></div>
                        
                        {/* Passo 4 */}
                        <div className="flex gap-4">
                          <div className="flex-shrink-0 w-10 h-10 bg-purple-600 rounded-full flex items-center justify-center text-white font-bold">
                            4
                          </div>
                          <div className="flex-1">
                            <h4 className="font-bold text-lg mb-2">Colar a Key Aqui</h4>
                            <p className="text-gray-600 mb-3">
                              Copie a chave que começa com <code className="bg-gray-100 px-2 py-1 rounded">sk-emergent-...</code> e cole no campo "API Key" acima.
                            </p>
                            <div className="bg-green-50 border-2 border-green-200 p-4 rounded-lg">
                              <p className="font-semibold text-green-900 mb-2">✅ Pronto!</p>
                              <p className="text-green-700">Seu agente agora pode usar OpenAI, Anthropic e Google com uma única chave!</p>
                            </div>
                          </div>
                        </div>
                        
                        <div className="border-t border-gray-200"></div>
                        
                        {/* Créditos Grátis */}
                        <div className="bg-gradient-to-r from-yellow-50 to-orange-50 border-2 border-yellow-300 rounded-lg p-4">
                          <div className="flex items-start gap-3">
                            <span className="text-3xl">🎁</span>
                            <div>
                              <h4 className="font-bold text-yellow-900 mb-1">Créditos Grátis!</h4>
                              <p className="text-yellow-800 text-sm">
                                Ao criar sua conta, você recebe créditos grátis para testar todos os modelos de IA.
                                Você também pode configurar auto-recarga para nunca ficar sem créditos.
                              </p>
                            </div>
                          </div>
                        </div>
                      </div>
                      
                      <div className="bg-gray-50 p-4 flex justify-end gap-2">
                        <button
                          onClick={() => setShowKeyTutorial(false)}
                          className="px-4 py-2 bg-gray-200 hover:bg-gray-300 rounded-lg font-medium transition-all"
                        >
                          Fechar
                        </button>
                        <a
                          href="https://app.emergent.sh/register?ref=noit391017"
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-2 bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg font-medium transition-all"
                        >
                          <span>🚀</span>
                          <span>Criar Minha Conta</span>
                        </a>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              <div>
                <label className="text-sm font-medium mb-2 block">
                  Aleatoriedade da resposta (Temperatura): {config.temperature}
                </label>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.1"
                  value={config.temperature}
                  onChange={(e) => setConfig({ ...config, temperature: parseFloat(e.target.value) })}
                  className="w-full"
                />
                <div className="flex justify-between text-xs text-slate-500 mt-1">
                  <span>0 (Consistente)</span>
                  <span>0.5 (Balanceado)</span>
                  <span>1 (Criativo)</span>
                </div>
                <p className="text-xs text-slate-500 mt-2">
                  Mantenha em 0.5 para uma resposta mais consistente
                </p>
              </div>

              <div>
                <label className="text-sm font-medium mb-2 block">Máximo de Tokens</label>
                <Input
                  type="number"
                  value={config.max_tokens}
                  onChange={(e) => setConfig({ ...config, max_tokens: parseInt(e.target.value) })}
                />
              </div>
              
              <div className="bg-yellow-50 border-2 border-yellow-200 rounded-lg p-4">
                <label className="text-sm font-medium mb-2 block text-yellow-900">
                  ⏱️ Tempo de Resposta (Humanização)
                </label>
                <div className="flex items-center gap-3">
                  <Input
                    type="number"
                    min="0"
                    max="60"
                    value={config.response_delay_seconds || 3}
                    onChange={(e) => {
                      const value = Math.min(60, Math.max(0, parseInt(e.target.value) || 0));
                      setConfig({ ...config, response_delay_seconds: value });
                    }}
                    className="w-24"
                  />
                  <span className="text-sm text-yellow-800">segundos</span>
                </div>
                <p className="text-xs text-yellow-700 mt-2">
                  🤖 Simula um atendimento humanizado. A IA aguarda esse tempo antes de responder (0-60 segundos).
                  Recomendado: 3-5 segundos.
                </p>
              </div>
            </div>
          </TabsContent>

          {/* Aba: Comportamento */}
          <TabsContent value="behavior" className="space-y-4">
            <div className="bg-gradient-to-r from-green-50 to-emerald-50 p-4 rounded-lg mb-4">
              <h3 className="font-semibold text-green-900 mb-2">⚙️ Comportamento</h3>
              <p className="text-sm text-green-700">Configure como o agente se comporta</p>
            </div>

            <div className="space-y-4">
              <div className="flex items-center gap-3 p-4 border rounded-lg">
                <input
                  type="checkbox"
                  checked={config.knowledge_restriction}
                  onChange={(e) => setConfig({ ...config, knowledge_restriction: e.target.checked })}
                  className="w-4 h-4"
                />
                <div>
                  <label className="font-medium text-sm">Restrição de conhecimento</label>
                  <p className="text-xs text-slate-500">
                    Quando ativado, algumas instruções extras serão adicionadas ao prompt do sistema
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-3 p-4 border rounded-lg">
                <input
                  type="checkbox"
                  checked={config.auto_detect_language}
                  onChange={(e) => setConfig({ ...config, auto_detect_language: e.target.checked })}
                  className="w-4 h-4"
                />
                <div>
                  <label className="font-medium text-sm">Detector de Idioma automático</label>
                  <p className="text-xs text-slate-500">
                    Quando ativado, algumas instruções extras são adicionadas ao prompt do sistema
                  </p>
                </div>
              </div>

              <div>
                <label className="text-sm font-medium mb-2 block">Fuso horário</label>
                <select
                  value={config.timezone}
                  onChange={(e) => setConfig({ ...config, timezone: e.target.value })}
                  className="w-full border rounded-lg p-2"
                >
                  <option value="America/Sao_Paulo">America/Sao_Paulo (GMT-3)</option>
                  <option value="America/New_York">America/New_York (GMT-5)</option>
                  <option value="Europe/London">Europe/London (GMT+0)</option>
                  <option value="Asia/Tokyo">Asia/Tokyo (GMT+9)</option>
                </select>
              </div>
            </div>
          </TabsContent>
        </Tabs>

        {/* Botões de Ação */}
        <div className="flex gap-2 mt-6">
          <Button variant="outline" onClick={onClose} className="flex-1">
            Cancelar
          </Button>
          <Button onClick={handleSave} className="flex-1 bg-indigo-600 hover:bg-indigo-700">
            💾 Salvar Configurações
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
};

// Dialog de Treinamento por Áudio
const TrainingDialog = ({ open, onClose, agent }) => {
  if (!agent) return null;

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-xl font-bold flex items-center gap-2">
            <Mic className="w-5 h-5 text-blue-600" />
            Treinamento por Áudio - {agent.name}
          </DialogTitle>
        </DialogHeader>
        
        <AITrainingManager agentId={agent.agent_id} />
        
        <div className="flex justify-end mt-4">
          <Button onClick={onClose} variant="outline">
            Fechar
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default AIAgentsManager;
