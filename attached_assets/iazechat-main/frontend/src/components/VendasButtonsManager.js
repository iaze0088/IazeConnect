import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import api from '@/lib/api';
import { toast } from 'sonner';
import { Plus, Edit, Trash2, ChevronRight, Bot, MessageSquare, Zap } from 'lucide-react';

const VendasButtonsManager = () => {
  const [config, setConfig] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showDialog, setShowDialog] = useState(false);
  const [editingButton, setEditingButton] = useState(null);
  const [parentButton, setParentButton] = useState(null);
  
  const [formData, setFormData] = useState({
    label: '',
    response_text: '',
    action_type: 'message',
    media_url: null,
    media_type: null,
    redirect_url: '',
    api_url: '',
    api_method: 'POST',
    api_headers: {},
    pulse: false,
    color: 'green'
  });
  
  const [uploadingMedia, setUploadingMedia] = useState(false);

  useEffect(() => {
    loadConfig();
  }, []);

  const loadConfig = async () => {
    try {
      setLoading(true);
      const { data } = await api.get('/admin/vendas-bot/buttons/config');
      setConfig(data);
    } catch (error) {
      console.error('Erro ao carregar config:', error);
      // Se não existir, criar padrão
      await createDefaultConfig();
    } finally {
      setLoading(false);
    }
  };

  const createDefaultConfig = async () => {
    try {
      const { data } = await api.post('/admin/vendas-bot/buttons/create-default');
      setConfig(data.config);
      toast.success('Configuração padrão criada!');
    } catch (error) {
      toast.error('Erro ao criar configuração padrão');
    }
  };

  const saveConfig = async () => {
    try {
      await api.post('/admin/vendas-bot/buttons/config', config);
      toast.success('Configuração salva!');
    } catch (error) {
      toast.error('Erro ao salvar configuração');
    }
  };

  // updateMode removido - modo de operação é gerenciado pelo VendasBotManagerV2

  const openAddDialog = (parent = null) => {
    setParentButton(parent);
    setEditingButton(null);
    setFormData({
      label: '',
      response_text: '',
      action_type: 'message',
      media_url: null,
      media_type: null,
      redirect_url: '',
      api_url: '',
      api_method: 'POST',
      api_headers: {},
      pulse: false,
      color: 'green'
    });
    setShowDialog(true);
  };
  
  const handleMediaUpload = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    
    try {
      setUploadingMedia(true);
      
      const formData = new FormData();
      formData.append('file', file);
      
      const { data } = await api.post('/admin/vendas-bot/buttons/upload-media', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      
      setFormData(prev => ({
        ...prev,
        media_url: data.media_url,
        media_type: data.media_type
      }));
      
      toast.success(`${data.media_type === 'image' ? 'Foto' : 'Vídeo'} enviado com sucesso!`);
    } catch (error) {
      console.error('Erro ao fazer upload:', error);
      toast.error('Erro ao fazer upload do arquivo');
    } finally {
      setUploadingMedia(false);
    }
  };
  
  const removeMedia = () => {
    setFormData(prev => ({
      ...prev,
      media_url: null,
      media_type: null
    }));
  };

  const handleSaveButton = async () => {
    if (!formData.label || !formData.response_text) {
      toast.error('Preencha todos os campos');
      return;
    }

    try {
      const newButton = {
        id: editingButton?.id || `btn_${Date.now()}`,
        ...formData,
        sub_buttons: editingButton?.sub_buttons || []
      };

      if (editingButton) {
        // Editar botão existente
        const updateButtons = (buttons) => {
          return buttons.map(btn => {
            if (btn.id === editingButton.id) {
              return {...btn, ...formData};
            }
            if (btn.sub_buttons) {
              return {...btn, sub_buttons: updateButtons(btn.sub_buttons)};
            }
            return btn;
          });
        };
        
        const updatedConfig = {
          ...config,
          root_buttons: updateButtons(config.root_buttons)
        };
        
        setConfig(updatedConfig);
        
        // 🔧 FIX: Salvar no backend após editar
        await api.post('/admin/vendas-bot/buttons/config', updatedConfig);
      } else {
        // Adicionar novo botão
        await api.post('/admin/vendas-bot/buttons/add-button', newButton, {
          params: { parent_id: parentButton?.id }
        });
      }

      await loadConfig();
      setShowDialog(false);
      toast.success(editingButton ? 'Botão atualizado!' : 'Botão adicionado!');
    } catch (error) {
      toast.error('Erro ao salvar botão');
    }
  };

  const handleDeleteButton = async (buttonId) => {
    if (!window.confirm('Deseja realmente excluir este botão?')) return;

    try {
      await api.delete(`/admin/vendas-bot/buttons/button/${buttonId}`);
      await loadConfig();
      toast.success('Botão removido!');
    } catch (error) {
      toast.error('Erro ao remover botão');
    }
  };

  const renderButton = (button, level = 0) => {
    return (
      <div key={button.id} className="mb-2" style={{marginLeft: `${level * 20}px`}}>
        <Card className="p-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 flex-1">
              {level > 0 && <ChevronRight className="w-4 h-4 text-gray-400" />}
              <div className="flex-1">
                <div className="font-medium">{button.label}</div>
                <div className="text-sm text-gray-600">{button.response_text.substring(0, 60)}...</div>
              </div>
            </div>
            <div className="flex gap-2">
              <Button
                size="sm"
                variant="outline"
                onClick={() => openAddDialog(button)}
              >
                <Plus className="w-4 h-4" />
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  setEditingButton(button);
                  setFormData({
                    label: button.label,
                    response_text: button.response_text,
                    action_type: button.action_type,
                    media_url: button.media_url || null,
                    media_type: button.media_type || null,
                    redirect_url: button.redirect_url || '',
                    api_url: button.api_url || '',
                    api_method: button.api_method || 'POST',
                    api_headers: button.api_headers || {},
                    pulse: button.pulse || false,
                    color: button.color || 'green'
                  });
                  setShowDialog(true);
                }}
              >
                <Edit className="w-4 h-4" />
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => handleDeleteButton(button.id)}
              >
                <Trash2 className="w-4 h-4 text-red-600" />
              </Button>
            </div>
          </div>
        </Card>
        
        {button.sub_buttons && button.sub_buttons.length > 0 && (
          <div className="mt-2">
            {button.sub_buttons.map(subBtn => renderButton(subBtn, level + 1))}
          </div>
        )}
      </div>
    );
  };

  if (loading) {
    return <div className="p-4">Carregando...</div>;
  }

  if (!config) {
    return (
      <div className="p-4">
        <Button onClick={createDefaultConfig}>
          Criar Configuração Padrão
        </Button>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-6xl">
      <div className="mb-6">
        <h2 className="text-2xl font-bold mb-4">🎯 Sistema de Botões Interativos</h2>
        
        {/* Modo de Operação removido daqui - gerenciado pelo VendasBotManagerV2 */}

        {/* 🆕 Configurações de Aparência do Bot */}
        <Card className="p-4 mb-4">
          <h3 className="font-bold mb-3 flex items-center gap-2">
            <Bot className="w-5 h-5" />
            Aparência do Bot
          </h3>
          
          <div className="space-y-3">
            <div>
              <label className="font-semibold block mb-2">Nome do Bot:</label>
              <Input
                value={config.bot_name || 'Assistente Virtual'}
                onChange={(e) => setConfig({...config, bot_name: e.target.value})}
                placeholder="Ex: Assistente Virtual, Atendente IAZE"
              />
            </div>
            
            <div>
              <label className="font-semibold block mb-2">URL da Foto de Perfil:</label>
              <Input
                value={config.bot_avatar_url || ''}
                onChange={(e) => setConfig({...config, bot_avatar_url: e.target.value})}
                placeholder="Ex: https://exemplo.com/avatar.jpg"
              />
              {config.bot_avatar_url && (
                <div className="mt-2">
                  <img 
                    src={config.bot_avatar_url} 
                    alt="Preview" 
                    className="w-16 h-16 rounded-full object-cover border-2 border-gray-300"
                    onError={(e) => {
                      e.target.style.display = 'none';
                      toast.error('Erro ao carregar imagem. Verifique a URL.');
                    }}
                  />
                </div>
              )}
            </div>
          </div>
          
          <Button onClick={saveConfig} className="mt-3" size="sm">
            Salvar Aparência
          </Button>
        </Card>

        {/* Mensagem de Boas-Vindas */}
        <Card className="p-4 mb-4">
          <label className="font-semibold block mb-2">Mensagem de Boas-Vindas:</label>
          <Textarea
            value={config.welcome_message}
            onChange={(e) => setConfig({...config, welcome_message: e.target.value})}
            rows={2}
            placeholder="Ex: Olá! Como posso ajudar você hoje?"
          />
          <Button onClick={saveConfig} className="mt-2" size="sm">
            Salvar Mensagem
          </Button>
        </Card>

        {/* Botões */}
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-xl font-semibold">Botões Configurados:</h3>
          <Button onClick={() => openAddDialog()} className="gap-2">
            <Plus className="w-4 h-4" />
            Adicionar Botão Raiz
          </Button>
        </div>

        <div className="space-y-2">
          {config.root_buttons && config.root_buttons.length > 0 ? (
            config.root_buttons.map(btn => renderButton(btn))
          ) : (
            <Card className="p-6 text-center text-gray-500">
              Nenhum botão configurado. Clique em "Adicionar Botão Raiz" para começar.
            </Card>
          )}
        </div>
      </div>

      {/* Dialog para adicionar/editar botão */}
      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {editingButton ? 'Editar Botão' : parentButton ? 'Adicionar Sub-Botão' : 'Adicionar Botão Raiz'}
            </DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4 mt-4">
            <div>
              <label className="block text-sm font-medium mb-1">Texto do Botão:</label>
              <Input
                value={formData.label}
                onChange={(e) => setFormData({...formData, label: e.target.value})}
                placeholder="Ex: SUPORTE, TESTE GRÁTIS"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Mensagem de Resposta:</label>
              <Textarea
                value={formData.response_text}
                onChange={(e) => setFormData({...formData, response_text: e.target.value})}
                rows={4}
                placeholder="Mensagem que será enviada quando o botão for clicado"
              />
              <p className="text-xs text-gray-500 mt-1">
                💡 <strong>Dica:</strong> Use **palavra** para destacar em laranja/negrito. 
                Exemplo: **Código:** rota01
              </p>
            </div>

            {/* 🆕 Link de Redirecionamento */}
            <div>
              <label className="block text-sm font-medium mb-1">🔗 Link de Redirecionamento (Opcional):</label>
              <Input
                type="url"
                value={formData.redirect_url}
                onChange={(e) => setFormData({...formData, redirect_url: e.target.value})}
                placeholder="https://wa.me/5511999999999 ou https://seusite.com"
              />
              <p className="text-xs text-gray-500 mt-1">
                Se preenchido, ao clicar no botão irá abrir este link ao invés de enviar mensagem
              </p>
            </div>

            {/* 🆕 Configuração de API para Criar Usuário */}
            <div className="border-t pt-4 mt-4">
              <label className="block text-sm font-medium mb-2">👤 API para Criar Usuário (Opcional):</label>
              
              <div className="space-y-3">
                <div>
                  <label className="block text-xs text-gray-600 mb-1">URL da API:</label>
                  <Input
                    type="url"
                    value={formData.api_url}
                    onChange={(e) => setFormData({...formData, api_url: e.target.value})}
                    placeholder="https://api.seupanel.com/criar-usuario"
                  />
                </div>
                
                {formData.api_url && (
                  <>
                    <div>
                      <label className="block text-xs text-gray-600 mb-1">Método HTTP:</label>
                      <select
                        value={formData.api_method}
                        onChange={(e) => setFormData({...formData, api_method: e.target.value})}
                        className="w-full border rounded px-3 py-2"
                      >
                        <option value="POST">POST</option>
                        <option value="GET">GET</option>
                        <option value="PUT">PUT</option>
                      </select>
                    </div>
                    
                    <p className="text-xs text-blue-600 bg-blue-50 p-2 rounded">
                      💡 Quando cliente clicar, irá pedir: Nome, WhatsApp e Senha (2 dígitos)
                      <br/>
                      📤 Enviará para API: {`{"name":"...", "whatsapp":"...", "pin":"..."}`}
                      <br/>
                      📥 API deve retornar: {`{"username":"...", "password":"..."}`}
                    </p>
                  </>
                )}
              </div>
            </div>

            {/* 🆕 Personalização Visual do Botão */}
            <div className="border-t pt-4 mt-4">
              <label className="block text-sm font-medium mb-3">🎨 Personalização Visual:</label>
              
              <div className="space-y-3">
                {/* Cor do Botão */}
                <div>
                  <label className="block text-xs text-gray-600 mb-1">Cor do Botão:</label>
                  <select
                    value={formData.color}
                    onChange={(e) => setFormData({...formData, color: e.target.value})}
                    className="w-full border rounded px-3 py-2"
                  >
                    <option value="green">🟢 Verde (Padrão WhatsApp)</option>
                    <option value="blue">🔵 Azul</option>
                    <option value="red">🔴 Vermelho</option>
                  </select>
                </div>
                
                {/* Animação Pulsante */}
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="pulse-checkbox"
                    checked={formData.pulse}
                    onChange={(e) => setFormData({...formData, pulse: e.target.checked})}
                    className="w-4 h-4"
                  />
                  <label htmlFor="pulse-checkbox" className="text-sm cursor-pointer">
                    ✨ Botão Pulsante (chama atenção)
                  </label>
                </div>
                
                {/* Preview */}
                <div className="bg-gray-50 p-3 rounded">
                  <p className="text-xs text-gray-600 mb-2">Preview:</p>
                  <button
                    type="button"
                    className={`px-4 py-2 rounded text-white font-medium ${
                      formData.pulse ? 'animate-pulse' : ''
                    }`}
                    style={{
                      backgroundColor: 
                        formData.color === 'green' ? '#25D366' :
                        formData.color === 'blue' ? '#0088cc' :
                        formData.color === 'red' ? '#dc2626' : '#25D366'
                    }}
                  >
                    {formData.label || 'Botão Exemplo'}
                  </button>
                </div>
              </div>
            </div>

            {/* 🆕 Upload de Foto/Vídeo */}
            <div>
              <label className="block text-sm font-medium mb-2">📎 Foto/Vídeo (Opcional):</label>
              
              {formData.media_url ? (
                <div className="border rounded-lg p-3 bg-gray-50">
                  {formData.media_type === 'image' ? (
                    <img 
                      src={formData.media_url} 
                      alt="Preview" 
                      className="max-h-40 rounded mb-2"
                    />
                  ) : (
                    <video 
                      src={formData.media_url} 
                      controls 
                      className="max-h-40 rounded mb-2"
                    />
                  )}
                  <Button 
                    size="sm" 
                    variant="outline" 
                    onClick={removeMedia}
                    className="w-full"
                  >
                    <Trash2 className="w-4 h-4 mr-2" />
                    Remover {formData.media_type === 'image' ? 'Foto' : 'Vídeo'}
                  </Button>
                </div>
              ) : (
                <div className="border-2 border-dashed rounded-lg p-4 text-center">
                  <input
                    type="file"
                    accept="image/*,video/*"
                    onChange={handleMediaUpload}
                    className="hidden"
                    id="media-upload"
                    disabled={uploadingMedia}
                  />
                  <label 
                    htmlFor="media-upload" 
                    className="cursor-pointer block"
                  >
                    {uploadingMedia ? (
                      <div className="text-gray-500">Enviando...</div>
                    ) : (
                      <>
                        <div className="text-3xl mb-2">📷</div>
                        <div className="text-sm text-gray-600">
                          Clique para enviar foto ou vídeo
                        </div>
                        <div className="text-xs text-gray-400 mt-1">
                          JPG, PNG, GIF, MP4, MOV
                        </div>
                      </>
                    )}
                  </label>
                </div>
              )}
            </div>

            <div className="flex gap-2 justify-end">
              <Button variant="outline" onClick={() => setShowDialog(false)}>
                Cancelar
              </Button>
              <Button onClick={handleSaveButton}>
                {editingButton ? 'Atualizar' : 'Adicionar'}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default VendasButtonsManager;
