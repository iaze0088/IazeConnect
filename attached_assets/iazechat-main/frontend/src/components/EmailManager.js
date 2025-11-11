import React, { useState, useEffect } from 'react';
import { Mail, Settings, Save, Send, Trash2, Plus } from 'lucide-react';
import api from '../lib/api';
import { toast } from 'sonner';

const EmailManager = () => {
  const [activeTab, setActiveTab] = useState('clients'); // 'clients' ou 'config'
  
  // Estado para emails de clientes
  const [clientEmails, setClientEmails] = useState([]);
  const [loadingClients, setLoadingClients] = useState(false);
  
  // Estado para novo email
  const [newEmail, setNewEmail] = useState({
    usuario: '',
    email: '',
    nome: ''
  });
  
  // Estado para configuração SMTP
  const [smtpConfig, setSmtpConfig] = useState({
    enabled: false,
    days_before: [3, 2, 1],
    send_expired: true,
    send_time: '09:00',
    smtp_host: '',
    smtp_port: 587,
    smtp_user: '',
    smtp_password: '',
    from_email: '',
    from_name: 'Atendimento'
  });
  const [loadingConfig, setLoadingConfig] = useState(false);
  const [testEmail, setTestEmail] = useState('');
  
  // Carregar dados
  useEffect(() => {
    loadClientEmails();
    loadConfig();
  }, []);
  
  const loadClientEmails = async () => {
    setLoadingClients(true);
    try {
      const response = await api.get('/client-emails');
      if (response.data.success) {
        setClientEmails(response.data.emails);
      }
    } catch (error) {
      console.error('Erro ao carregar emails:', error);
      toast.error('Erro ao carregar emails');
    } finally {
      setLoadingClients(false);
    }
  };
  
  const loadConfig = async () => {
    setLoadingConfig(true);
    try {
      const response = await api.get('/reminder-config');
      if (response.data.success) {
        setSmtpConfig(response.data.config);
      }
    } catch (error) {
      console.error('Erro ao carregar config:', error);
    } finally {
      setLoadingConfig(false);
    }
  };
  
  const handleAddEmail = async () => {
    if (!newEmail.usuario || !newEmail.email) {
      toast.error('Preencha usuário e email');
      return;
    }
    
    try {
      const response = await api.post('/client-email', newEmail);
      if (response.data.success) {
        toast.success(response.data.message);
        setNewEmail({ usuario: '', email: '', nome: '' });
        loadClientEmails();
      }
    } catch (error) {
      console.error('Erro ao adicionar email:', error);
      toast.error('Erro ao adicionar email');
    }
  };
  
  const handleDeleteEmail = async (usuario) => {
    if (!confirm(`Remover email de ${usuario}?`)) return;
    
    try {
      const response = await api.delete(`/client-email/${usuario}`);
      if (response.data.success) {
        toast.success('Email removido');
        loadClientEmails();
      }
    } catch (error) {
      console.error('Erro ao remover email:', error);
      toast.error('Erro ao remover email');
    }
  };
  
  const handleSaveConfig = async () => {
    try {
      const response = await api.put('/reminder-config', smtpConfig);
      if (response.data.success) {
        toast.success('Configuração salva!');
      }
    } catch (error) {
      console.error('Erro ao salvar config:', error);
      toast.error('Erro ao salvar configuração');
    }
  };
  
  const handleTestEmail = async () => {
    if (!testEmail) {
      toast.error('Digite um email para teste');
      return;
    }
    
    try {
      const response = await api.post(`/test-reminder-email?test_email=${testEmail}`);
      if (response.data.success) {
        toast.success('Email de teste enviado!');
      }
    } catch (error) {
      console.error('Erro ao enviar teste:', error);
      toast.error(error.response?.data?.detail || 'Erro ao enviar email de teste');
    }
  };
  
  return (
    <div className="p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold flex items-center gap-2">
          <Mail className="w-7 h-7 text-blue-600" />
          Gerenciamento de Emails
        </h2>
        <p className="text-gray-600 mt-1">Configure lembretes de vencimento por email</p>
      </div>
      
      {/* Tabs */}
      <div className="flex gap-2 mb-6 border-b">
        <button
          onClick={() => setActiveTab('clients')}
          className={`px-4 py-2 font-medium border-b-2 transition-colors ${
            activeTab === 'clients' 
              ? 'border-blue-600 text-blue-600' 
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          📧 Emails de Clientes
        </button>
        <button
          onClick={() => setActiveTab('config')}
          className={`px-4 py-2 font-medium border-b-2 transition-colors ${
            activeTab === 'config' 
              ? 'border-blue-600 text-blue-600' 
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          ⚙️ Configuração SMTP
        </button>
      </div>
      
      {/* Conteúdo */}
      {activeTab === 'clients' ? (
        <div>
          {/* Adicionar Email */}
          <div className="bg-white rounded-lg shadow p-4 mb-6">
            <h3 className="font-bold mb-4 flex items-center gap-2">
              <Plus className="w-5 h-5" />
              Adicionar Email de Cliente
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <input
                type="text"
                placeholder="Usuário"
                value={newEmail.usuario}
                onChange={(e) => setNewEmail({...newEmail, usuario: e.target.value})}
                className="px-3 py-2 border rounded"
              />
              <input
                type="email"
                placeholder="Email"
                value={newEmail.email}
                onChange={(e) => setNewEmail({...newEmail, email: e.target.value})}
                className="px-3 py-2 border rounded"
              />
              <input
                type="text"
                placeholder="Nome (opcional)"
                value={newEmail.nome}
                onChange={(e) => setNewEmail({...newEmail, nome: e.target.value})}
                className="px-3 py-2 border rounded"
              />
              <button
                onClick={handleAddEmail}
                className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 flex items-center justify-center gap-2"
              >
                <Plus className="w-4 h-4" />
                Adicionar
              </button>
            </div>
          </div>
          
          {/* Lista de Emails */}
          <div className="bg-white rounded-lg shadow">
            <div className="p-4 border-b">
              <h3 className="font-bold">Emails Cadastrados ({clientEmails.length})</h3>
            </div>
            <div className="overflow-x-auto">
              {loadingClients ? (
                <div className="p-8 text-center">Carregando...</div>
              ) : clientEmails.length === 0 ? (
                <div className="p-8 text-center text-gray-500">
                  Nenhum email cadastrado
                </div>
              ) : (
                <table className="w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left">Usuário</th>
                      <th className="px-4 py-3 text-left">Email</th>
                      <th className="px-4 py-3 text-left">Nome</th>
                      <th className="px-4 py-3 text-left">Cadastrado em</th>
                      <th className="px-4 py-3 text-right">Ações</th>
                    </tr>
                  </thead>
                  <tbody>
                    {clientEmails.map((item) => (
                      <tr key={item.id} className="border-b hover:bg-gray-50">
                        <td className="px-4 py-3 font-mono">{item.usuario}</td>
                        <td className="px-4 py-3">{item.email}</td>
                        <td className="px-4 py-3">{item.nome || '-'}</td>
                        <td className="px-4 py-3 text-sm text-gray-500">
                          {new Date(item.created_at).toLocaleDateString()}
                        </td>
                        <td className="px-4 py-3 text-right">
                          <button
                            onClick={() => handleDeleteEmail(item.usuario)}
                            className="text-red-600 hover:text-red-800"
                            title="Remover"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Ativar/Desativar */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="font-bold mb-4">Status do Sistema</h3>
            <label className="flex items-center gap-3">
              <input
                type="checkbox"
                checked={smtpConfig.enabled}
                onChange={(e) => setSmtpConfig({...smtpConfig, enabled: e.target.checked})}
                className="w-5 h-5"
              />
              <span className="font-medium">Lembretes Automáticos Ativados</span>
            </label>
          </div>
          
          {/* Configuração de Envio */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="font-bold mb-4">Quando Enviar Lembretes</h3>
            <div className="space-y-4">
              <div>
                <label className="block mb-2 font-medium">Enviar quantos dias antes do vencimento?</label>
                <div className="flex gap-4">
                  {[1, 2, 3, 4, 5, 7].map(day => (
                    <label key={day} className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={smtpConfig.days_before.includes(day)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSmtpConfig({
                              ...smtpConfig,
                              days_before: [...smtpConfig.days_before, day].sort((a,b) => b-a)
                            });
                          } else {
                            setSmtpConfig({
                              ...smtpConfig,
                              days_before: smtpConfig.days_before.filter(d => d !== day)
                            });
                          }
                        }}
                      />
                      {day} dia{day > 1 ? 's' : ''}
                    </label>
                  ))}
                </div>
              </div>
              
              <label className="flex items-center gap-3">
                <input
                  type="checkbox"
                  checked={smtpConfig.send_expired}
                  onChange={(e) => setSmtpConfig({...smtpConfig, send_expired: e.target.checked})}
                />
                <span>Enviar para clientes já vencidos</span>
              </label>
              
              <div>
                <label className="block mb-2 font-medium">Horário de Envio (UTC)</label>
                <input
                  type="time"
                  value={smtpConfig.send_time}
                  onChange={(e) => setSmtpConfig({...smtpConfig, send_time: e.target.value})}
                  className="px-3 py-2 border rounded"
                />
              </div>
            </div>
          </div>
          
          {/* Configuração SMTP */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="font-bold mb-4">Configuração SMTP</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block mb-2 font-medium">Servidor SMTP</label>
                <input
                  type="text"
                  placeholder="smtp.gmail.com"
                  value={smtpConfig.smtp_host}
                  onChange={(e) => setSmtpConfig({...smtpConfig, smtp_host: e.target.value})}
                  className="w-full px-3 py-2 border rounded"
                />
              </div>
              
              <div>
                <label className="block mb-2 font-medium">Porta</label>
                <input
                  type="number"
                  value={smtpConfig.smtp_port}
                  onChange={(e) => setSmtpConfig({...smtpConfig, smtp_port: parseInt(e.target.value)})}
                  className="w-full px-3 py-2 border rounded"
                />
              </div>
              
              <div>
                <label className="block mb-2 font-medium">Usuário SMTP</label>
                <input
                  type="text"
                  placeholder="seu-email@gmail.com"
                  value={smtpConfig.smtp_user}
                  onChange={(e) => setSmtpConfig({...smtpConfig, smtp_user: e.target.value})}
                  className="w-full px-3 py-2 border rounded"
                />
              </div>
              
              <div>
                <label className="block mb-2 font-medium">Senha SMTP</label>
                <input
                  type="password"
                  placeholder="••••••••"
                  value={smtpConfig.smtp_password}
                  onChange={(e) => setSmtpConfig({...smtpConfig, smtp_password: e.target.value})}
                  className="w-full px-3 py-2 border rounded"
                />
              </div>
              
              <div>
                <label className="block mb-2 font-medium">Email Remetente</label>
                <input
                  type="email"
                  placeholder="suporte@suporte.help"
                  value={smtpConfig.from_email}
                  onChange={(e) => setSmtpConfig({...smtpConfig, from_email: e.target.value})}
                  className="w-full px-3 py-2 border rounded"
                />
              </div>
              
              <div>
                <label className="block mb-2 font-medium">Nome do Remetente</label>
                <input
                  type="text"
                  placeholder="Atendimento"
                  value={smtpConfig.from_name}
                  onChange={(e) => setSmtpConfig({...smtpConfig, from_name: e.target.value})}
                  className="w-full px-3 py-2 border rounded"
                />
              </div>
            </div>
            
            <div className="mt-6 flex gap-3">
              <button
                onClick={handleSaveConfig}
                className="bg-green-600 text-white px-6 py-2 rounded hover:bg-green-700 flex items-center gap-2"
              >
                <Save className="w-4 h-4" />
                Salvar Configuração
              </button>
            </div>
          </div>
          
          {/* Testar Email */}
          <div className="bg-blue-50 rounded-lg border-2 border-blue-200 p-6">
            <h3 className="font-bold mb-4 flex items-center gap-2">
              <Send className="w-5 h-5 text-blue-600" />
              Enviar Email de Teste
            </h3>
            <div className="flex gap-3">
              <input
                type="email"
                placeholder="Digite um email para teste"
                value={testEmail}
                onChange={(e) => setTestEmail(e.target.value)}
                className="flex-1 px-3 py-2 border rounded"
              />
              <button
                onClick={handleTestEmail}
                className="bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700"
              >
                Enviar Teste
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default EmailManager;
