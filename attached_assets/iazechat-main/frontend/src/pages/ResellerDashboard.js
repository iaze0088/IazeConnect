import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Shield, LogOut, Users, MessageSquare, Settings, Bell, Plus, Trash2, Edit, Bot, Folder, Zap, BookOpen, Save, Monitor, Share2, Copy, CheckCircle, Globe, ExternalLink, Phone, CreditCard, Eye, Clock } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Card } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { toast } from 'sonner';
import api from '../lib/api';
import { clearAuth } from '../lib/auth';
import AIAgentsManager from '../components/AIAgentsManager';
import DepartmentsManager from '../components/DepartmentsManager';
import AutoResponder from '../components/AutoResponder';
import TutorialsApps from '../components/TutorialsApps';
import AutoResponderAdvanced from '../components/AutoResponderAdvanced';
import TutorialsAdvanced from '../components/TutorialsAdvanced';
import WhatsAppManager from '../components/WhatsAppManager';
import SubscriptionPayments from '../components/SubscriptionPayments';
import SubscriptionExpirationWarning from '../components/SubscriptionExpirationWarning';
import DomainConfig from '../components/DomainConfig';
import VendasBotManager from '../components/VendasBotManager';

const ResellerDashboard = () => {
  const navigate = useNavigate();
  const [agents, setAgents] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [resellers, setResellers] = useState([]);
  const [hierarchy, setHierarchy] = useState({ hierarchy: [] });
  const [config, setConfig] = useState({ 
    quick_blocks: [], 
    auto_reply: [], 
    apps: [],
    pix_key: '',
    manual_away_mode: false,  // Modo ausente manual
    allowed_data: { cpfs: [], emails: [], phones: [], random_keys: [] },
    api_integration: { api_url: '', api_token: '', api_enabled: false },
    ai_agent: {
      name: 'Assistente IA',
      personality: '',
      instructions: '',
      llm_provider: 'openai',
      llm_model: 'gpt-4',
      temperature: 0.7,
      max_tokens: 500,
      mode: 'standby',
      active_hours: '24/7',
      enabled: false,
      can_access_credentials: true,
      knowledge_base: ''
    }
  });
  const [notices, setNotices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploadingLogo, setUploadingLogo] = useState(false);
  const [uploadingClientLogo, setUploadingClientLogo] = useState(false);
  const logoInputRef = useRef(null);
  const clientLogoInputRef = useRef(null);
  const [clientLogoUrl, setClientLogoUrl] = useState('https://customer-assets.emergentagent.com/job_535f0fc0-1515-4938-9910-2bc0af524212/artifacts/qwn9iyvo_image.png');
  const [clientLogoLinkInput, setClientLogoLinkInput] = useState('');

  // IPTV Apps
  const [iptvApps, setIptvApps] = useState([]);
  const [newApp, setNewApp] = useState({
    name: '',
    type: 'SSIPTV',
    config_url: '',
    url_template: '',
    fields: [],
    instructions: ''
  });
  const [editingApp, setEditingApp] = useState(null);

  // Agent form
  const [newAgent, setNewAgent] = useState({ name: '', login: '', password: '', avatar: '', department_ids: [] });
  const [editingAgent, setEditingAgent] = useState(null);
  
  // Reseller form
  const [newReseller, setNewReseller] = useState({ name: '', email: '', password: '', domain: '', parent_id: null });
  const [editingReseller, setEditingReseller] = useState(null);
  const [expandedResellers, setExpandedResellers] = useState(new Set());
  const [activeTab, setActiveTab] = useState('dashboard');
  const [subscriptionExpired, setSubscriptionExpired] = useState(false);
  const [transferModal, setTransferModal] = useState({ open: false, reseller: null });
  const [viewMode, setViewMode] = useState('list'); // 'list' or 'tree'
  const [resellerInfoModal, setResellerInfoModal] = useState({ open: false, data: null });

  // Dashboard
  const [dashboardStats, setDashboardStats] = useState({});
  const [agentsOnline, setAgentsOnline] = useState([]);
  const [aiAgentsStatus, setAiAgentsStatus] = useState([]);
  const [dashboardLoading, setDashboardLoading] = useState(true);
  const [importantAlerts, setImportantAlerts] = useState([]);
  const [resellerData, setResellerData] = useState(null);

  useEffect(() => {
    loadData();
    
    // Carregar dashboard inicial
    if (activeTab === 'dashboard') {
      loadDashboardData();
    }
    
    // Auto-refresh dashboard
    const interval = setInterval(() => {
      if (activeTab === 'dashboard') {
        loadDashboardData();
      }
    }, 30000);
    
    return () => clearInterval(interval);
  }, [activeTab]);

  // Bloquear mudança de aba se assinatura expirada
  useEffect(() => {
    if (subscriptionExpired && activeTab !== 'payments') {
      setActiveTab('payments');
      toast.error('⚠️ Sua assinatura expirou! Renove para acessar o painel.', { duration: 5000 });
    }
  }, [subscriptionExpired, activeTab]);

  const handleTabChange = (newTab) => {
    if (subscriptionExpired && newTab !== 'payments') {
      toast.error('⚠️ Renove sua assinatura para acessar outras áreas do painel!', { duration: 3000 });
      return; // Não permite mudar
    }
    setActiveTab(newTab);
  };

  const loadData = async () => {
    try {
      const [agentsRes, resellersRes, hierarchyRes, configRes, noticesRes, departmentsRes, iptvAppsRes, resellerMeRes] = await Promise.all([
        api.get('/agents').catch(() => ({ data: [] })),
        api.get('/resellers').catch(() => ({ data: [] })),
        api.get('/resellers/hierarchy').catch(() => ({ data: { hierarchy: [] } })),
        api.get('/config').catch(() => ({ data: { quick_blocks: [], auto_reply: [], apps: [], pix_key: '', allowed_data: {}, api_integration: {}, ai_agent: {} } })),
        api.get('/notices').catch(() => ({ data: [] })),
        api.get('/ai/departments').catch(() => ({ data: [] })),
        api.get('/iptv-apps').catch(() => ({ data: [] })),
        api.get('/resellers/me').catch(() => ({ data: null }))
      ]);
      setAgents(Array.isArray(agentsRes.data) ? agentsRes.data : []);
      setResellers(Array.isArray(resellersRes.data) ? resellersRes.data : []);
      setHierarchy(hierarchyRes.data || { hierarchy: [] });
      setConfig(configRes.data || { quick_blocks: [], auto_reply: [], apps: [], pix_key: '', allowed_data: {}, api_integration: {}, ai_agent: {} });
      setNotices(Array.isArray(noticesRes.data) ? noticesRes.data : []);
      setDepartments(Array.isArray(departmentsRes.data) ? departmentsRes.data : []);
      setIptvApps(Array.isArray(iptvAppsRes.data) ? iptvAppsRes.data : []);
      
      // Salvar dados do reseller
      if (resellerMeRes.data) {
        setResellerData(resellerMeRes.data);
      }
      
      // Carregar logo do cliente
      if (resellerMeRes.data && resellerMeRes.data.client_logo_url) {
        setClientLogoUrl(resellerMeRes.data.client_logo_url);
      }
      // Verificar se assinatura está expirada
      if (resellerMeRes.data && resellerMeRes.data.subscription_active === false) {
        setSubscriptionExpired(true);
        setActiveTab('payments'); // Forçar ir para payments
      }
    } catch (error) {
      console.error('Error loading data:', error);
      toast.error('Erro ao carregar dados');
    } finally {
      setLoading(false);
    }
  };

  const loadDashboardData = async () => {
    setDashboardLoading(true);
    try {
      const [stats, agents, aiStatus, alerts] = await Promise.all([
        api.get('/reseller/dashboard/stats'),
        api.get('/reseller/dashboard/agents-online'),
        api.get('/reseller/dashboard/ai-agents-status'),
        api.get('/reseller/dashboard/important-alerts')
      ]);
      
      setDashboardStats(stats.data);
      setAgentsOnline(agents.data);
      setAiAgentsStatus(aiStatus.data);
      setImportantAlerts(alerts.data.alerts || []);
    } catch (error) {
      console.error('Error loading dashboard:', error);
    } finally {
      setDashboardLoading(false);
    }
  };

  const handleLogout = () => {
    clearAuth();
    navigate('/');
  };

  const toggleAwayMode = async () => {
    try {
      const newAwayMode = !config.manual_away_mode;
      
      // Salvar no backend
      await api.put('/config', { manual_away_mode: newAwayMode });
      
      // Atualizar estado local
      setConfig(prev => ({ ...prev, manual_away_mode: newAwayMode }));
      
      toast.success(
        newAwayMode 
          ? '⚠️ Modo Ausente ativado - Clientes verão status "Ausente"' 
          : '✅ Modo Online ativado - Clientes verão status normal',
        { duration: 3000 }
      );
    } catch (error) {
      console.error('Erro ao alternar modo ausente:', error);
      toast.error('Erro ao alterar status');
    }
  };

  const handleCopyResellerInfo = () => {
    const info = resellerInfoModal.data;
    const text = `
🎉 *REVENDA CRIADA COM SUCESSO!*

📋 *Informações de Acesso:*
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👤 *Nome:* ${info.name}
📧 *Email:* ${info.email}
🔑 *Senha:* ${info.password}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔗 *ACESSO UNIFICADO - Use este link:*

🟢 *Login da Revenda:*
${window.location.origin}/reseller-login

📧 Email: ${info.email}
🔑 Senha: ${info.password}

⚠️ *Importante:*
• A revenda deve acessar pelo link acima
• Fazer login com email e senha
• Terá 24 horas para configurar domínio próprio
• Após configurar, avisar você (Master) para ativar

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ *IMPORTANTE:*
• Use o domínio provisório para acessar o painel
• Após o primeiro login, você poderá configurar seu domínio oficial
• No menu "Domínio" você encontra instruções para apontar seu domínio próprio
• Quando ativar o domínio oficial, o domínio de teste será desativado

🚀 *Próximos Passos:*
1. Acesse o Painel Revenda pelo link acima
2. Faça login com email e senha fornecidos
3. Você será solicitado a trocar a senha no primeiro acesso
4. Configure seu domínio oficial quando estiver pronto

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
`.trim();

    navigator.clipboard.writeText(text);
    toast.success('✅ Informações copiadas! Pronto para enviar ao cliente.');
  };

  const handleCreateAgent = async () => {
    try {
      await api.post('/agents', newAgent);
      toast.success('Atendente criado com sucesso!');
      setNewAgent({ name: '', login: '', password: '', avatar: '', department_ids: [] });
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao criar atendente');
    }
  };

  const handleUpdateAgent = async (agentId, data) => {
    try {
      await api.put(`/agents/${agentId}`, data);
      toast.success('Atendente atualizado!');
      setEditingAgent(null);
      loadData();
    } catch (error) {
      toast.error('Erro ao atualizar atendente');
    }
  };

  const handleDeleteAgent = async (agentId) => {
    if (!window.confirm('Tem certeza que deseja excluir este atendente?')) return;
    try {
      await api.delete(`/agents/${agentId}`);
      toast.success('Atendente excluído!');
      loadData();
    } catch (error) {
      toast.error('Erro ao excluir atendente');
    }
  };
  
  // Reseller functions
  const handleCreateReseller = async () => {
    try {
      const { data } = await api.post('/resellers', newReseller);
      
      if (data.ok) {
        toast.success('Revenda criada com sucesso!');
        
        // Abrir modal com informações da revenda criada
        setResellerInfoModal({
          open: true,
          data: {
            name: data.name,
            email: data.email,
            password: data.password,
            test_domain: data.test_domain,
            urls: data.urls
          }
        });
        
        setNewReseller({ name: '', email: '', password: '', domain: '', parent_id: null });
        loadData();
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao criar revenda');
    }
  };
  
  const handleUpdateReseller = async () => {
    if (!editingReseller) return;
    try {
      // Preparar dados para atualização (remover campos vazios/undefined)
      const updateData = {};
      if (editingReseller.name) updateData.name = editingReseller.name;
      if (editingReseller.email) updateData.email = editingReseller.email;
      if (editingReseller.password) updateData.password = editingReseller.password;
      if (editingReseller.custom_domain !== undefined) updateData.custom_domain = editingReseller.custom_domain;
      if (editingReseller.is_active !== undefined) updateData.is_active = editingReseller.is_active;
      
      await api.put(`/resellers/${editingReseller.id}`, updateData);
      toast.success('Revenda atualizada com sucesso!');
      setEditingReseller(null);
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao atualizar revenda');
    }
  };
  
  const handleDeleteReseller = async (resellerId) => {
    if (!window.confirm('Tem certeza que deseja excluir esta revenda?')) return;
    try {
      await api.delete(`/resellers/${resellerId}`);
      toast.success('Revenda excluída!');
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao excluir revenda');
    }
  };
  
  const handleTransferReseller = async () => {
    try {
      await api.post('/resellers/transfer', {
        reseller_id: transferModal.reseller.id,
        new_parent_id: transferModal.new_parent_id
      });
      toast.success('Revenda transferida com sucesso!');
      setTransferModal({ open: false, reseller: null });
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao transferir revenda');
    }
  };
  
  const toggleExpand = (resellerId) => {
    const newExpanded = new Set(expandedResellers);
    if (newExpanded.has(resellerId)) {
      newExpanded.delete(resellerId);
    } else {
      newExpanded.add(resellerId);
    }
    setExpandedResellers(newExpanded);
  };

  const handleSaveConfig = async () => {
    try {
      await api.put('/config', config);
      toast.success('Configurações salvas!');
    } catch (error) {
      toast.error('Erro ao salvar configurações');
    }
  };

  const handleLogoUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    if (!file.type.startsWith('image/')) {
      toast.error('Por favor, selecione uma imagem');
      return;
    }

    setUploadingLogo(true);
    try {
      const formData = new FormData();
      formData.append('file', file);

      const { data } = await api.post('/config/support-avatar', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      // Atualizar config com nova logo
      setConfig(prev => ({ ...prev, support_avatar: data.avatar_url }));
      toast.success('Logo atualizada com sucesso!');
      loadData(); // Recarregar dados
    } catch (error) {
      toast.error('Erro ao fazer upload da logo');
      console.error('Upload error:', error);
    } finally {
      setUploadingLogo(false);
    }
  };

  const handleClientLogoUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    if (!file.type.startsWith('image/')) {
      toast.error('Por favor, selecione uma imagem');
      return;
    }

    setUploadingClientLogo(true);
    try {
      const formData = new FormData();
      formData.append('file', file);

      const { data } = await api.post('/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      // Atualizar logo do cliente
      await updateClientLogo(data.url);
    } catch (error) {
      toast.error('Erro ao fazer upload da foto');
      console.error('Upload error:', error);
    } finally {
      setUploadingClientLogo(false);
    }
  };

  const handleClientLogoLinkUpdate = async () => {
    if (!clientLogoLinkInput.trim()) {
      toast.error('Digite uma URL válida');
      return;
    }
    await updateClientLogo(clientLogoLinkInput.trim());
    setClientLogoLinkInput('');
  };

  const updateClientLogo = async (logoUrl) => {
    try {
      // Obter informações do reseller atual
      const meRes = await api.get('/resellers/me');
      const resellerId = meRes.data.id;
      
      // Atualizar logo
      await api.put(`/resellers/${resellerId}`, { client_logo_url: logoUrl });
      setClientLogoUrl(logoUrl);
      toast.success('Foto de perfil atualizada com sucesso!');
    } catch (error) {
      toast.error('Erro ao atualizar foto de perfil');
      console.error('Update error:', error);
    }
  };

  const handleUpload = async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    try {
      const { data } = await api.post('/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      return data.url;
    } catch (error) {
      toast.error('Erro ao fazer upload');
      return null;
    }
  };

  // IPTV Apps functions
  const handleCreateIPTVApp = async () => {
    try {
      await api.post('/iptv-apps', newApp);
      toast.success('App IPTV criado com sucesso!');
      setNewApp({
        name: '',
        type: 'SSIPTV',
        config_url: '',
        url_template: '',
        fields: [],
        instructions: ''
      });
      loadData();
    } catch (error) {
      toast.error('Erro ao criar app IPTV');
    }
  };

  const handleUpdateIPTVApp = async (appId, data) => {
    try {
      await api.put(`/iptv-apps/${appId}`, data);
      toast.success('App atualizado!');
      setEditingApp(null);
      loadData();
    } catch (error) {
      toast.error('Erro ao atualizar app');
    }
  };

  const handleDeleteIPTVApp = async (appId) => {
    if (!window.confirm('Tem certeza que deseja deletar este app?')) return;
    try {
      await api.delete(`/iptv-apps/${appId}`);
      toast.success('App deletado!');
      loadData();
    } catch (error) {
      toast.error('Erro ao deletar app');
    }
  };

  const loadIPTVTemplate = (type) => {
    if (type === 'SSIPTV') {
      setNewApp({
        ...newApp,
        type: 'SSIPTV',
        name: 'SS-IPTV',
        config_url: 'http://ss-iptv.com/en/users/playlist',
        url_template: 'http://gestor.my/ssiptv/{username}/{password}/download_m3u',
        fields: ['codigo', 'username', 'password'],
        instructions: '1. Acesse http://ss-iptv.com/en/users/playlist\n2. Cole o código do cliente\n3. Crie uma pasta\n4. Cole o link m3u gerado\n5. Salve'
      });
    } else if (type === 'SMARTONE') {
      setNewApp({
        ...newApp,
        type: 'SMARTONE',
        name: 'SmartOne IPTV',
        config_url: 'https://smartone-iptv.com/plugin/smart_one/main_generate',
        url_template: 'http://vem4.lol/get.php?username={username}&password={password}&type=m3u_plus&output=mpegts',
        fields: ['mac', 'nome_pasta', 'username', 'password'],
        instructions: '1. Acesse https://smartone-iptv.com/plugin/smart_one/main_generate\n2. Cole o MAC do cliente\n3. Na frente do MAC, coloque o nome da pasta\n4. Embaixo, cole o link m3u8\n5. Salve'
      });
    } else if (type === 'DUPLEXPLAY') {
      setNewApp({
        ...newApp,
        type: 'DUPLEXPLAY',
        name: 'Duplex Play',
        config_url: 'https://edit.duplexplay.com/',
        url_template: 'http://gestor.my/duplexplay/{username}/{password}/playlist.m3u',
        fields: ['mac', 'username', 'password'],
        instructions: '1. Acesse https://edit.duplexplay.com/\n2. Cole o MAC do dispositivo\n3. Adicione username e password\n4. Cole o link da playlist\n5. Salve a configuração'
      });
    } else if (type === 'IBOPLAYER') {
      setNewApp({
        ...newApp,
        type: 'IBOPLAYER',
        name: 'IBO Player',
        config_url: 'https://iboplayer.com/device/login',
        url_template: 'http://gestor.my/iboplayer/{username}/{password}/playlist.m3u',
        fields: ['codigo_ativacao', 'username', 'password'],
        instructions: '1. Acesse https://iboplayer.com/device/login\n2. Cole o código de ativação da TV\n3. Faça login com username e password\n4. Adicione a playlist URL\n5. Salve'
      });
    } else if (type === 'SMARTIPTV') {
      setNewApp({
        ...newApp,
        type: 'SMARTIPTV',
        name: 'Smart IPTV',
        config_url: 'https://siptv.app/mylist/',
        url_template: 'http://gestor.my/smartiptv/{username}/{password}/playlist.m3u',
        fields: ['mac', 'username', 'password'],
        instructions: '1. Acesse https://siptv.app/mylist/\n2. Cole o MAC Address da TV\n3. Adicione a playlist URL\n4. Username e password do servidor\n5. Salve a lista'
      });
    } else if (type === 'BAYTV') {
      setNewApp({
        ...newApp,
        type: 'BAYTV',
        name: 'Bay TV',
        config_url: 'https://cms.bayip.tv/',
        url_template: 'http://gestor.my/baytv/{username}/{password}/playlist.m3u',
        fields: ['device_id', 'username', 'password'],
        instructions: '1. Acesse https://cms.bayip.tv/\n2. Cole o Device ID\n3. Adicione username e password\n4. Cole a URL da playlist\n5. Salve a configuração'
      });
    } else if (type === 'DUPLECAST') {
      setNewApp({
        ...newApp,
        type: 'DUPLECAST',
        name: 'Duplecast',
        config_url: 'https://duplecast.com/plugin/duplecast/device_login/',
        url_template: 'http://gestor.my/duplecast/{username}/{password}/playlist.m3u',
        fields: ['mac', 'username', 'password'],
        instructions: '1. Acesse https://duplecast.com/plugin/duplecast/device_login/\n2. Cole o MAC do dispositivo\n3. Faça login com username e password\n4. Adicione URL da playlist\n5. Salve'
      });
    }
  };

  const handleCreateNotice = async (kind, text, file) => {
    try {
      let fileUrl = '';
      if (file) {
        fileUrl = await handleUpload(file);
        if (!fileUrl) return;
      }
      await api.post('/notices', { kind, text: text || '', file_url: fileUrl || '' });
      toast.success('Aviso publicado!');
      loadData();
    } catch (error) {
      toast.error('Erro ao publicar aviso');
    }
  };

  const handleDeleteNotice = async (noticeId) => {
    if (!window.confirm('Tem certeza que deseja deletar este aviso?')) return;
    try {
      await api.delete(`/notices/${noticeId}`);
      toast.success('Aviso deletado!');
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao deletar aviso');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-purple-600 border-t-transparent rounded-full animate-spin mx-auto"></div>
          <p className="mt-4 text-slate-600">Carregando...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col bg-slate-50">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 flex-shrink-0 z-10">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-purple-600 rounded-xl flex items-center justify-center">
              <Shield className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-slate-900">Admin Dashboard</h1>
              <p className="text-sm text-slate-600">Gerenciamento completo</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            {/* Toggle Status Ausente/Online */}
            <div className="flex items-center gap-2 px-3 py-2 bg-slate-50 rounded-lg border border-slate-200">
              <span className="text-sm font-medium text-slate-700">Status:</span>
              <button
                onClick={toggleAwayMode}
                className={`
                  relative inline-flex h-6 w-11 items-center rounded-full transition-colors
                  ${config.manual_away_mode ? 'bg-orange-500' : 'bg-green-500'}
                `}
                title={config.manual_away_mode ? 'Clique para ativar modo Online' : 'Clique para ativar modo Ausente'}
              >
                <span
                  className={`
                    inline-block h-4 w-4 transform rounded-full bg-white transition-transform
                    ${config.manual_away_mode ? 'translate-x-6' : 'translate-x-1'}
                  `}
                />
              </button>
              <span className={`text-sm font-semibold ${config.manual_away_mode ? 'text-orange-600' : 'text-green-600'}`}>
                {config.manual_away_mode ? '⚠️ Ausente' : '✅ Online'}
              </span>
            </div>

            <Button data-testid="logout-btn" onClick={handleLogout} variant="outline" size="sm">
              <LogOut className="w-4 h-4 mr-2" />
              Sair
            </Button>
          </div>
        </div>
      </header>

      {/* Popup de Aviso de Expiração */}
      <SubscriptionExpirationWarning 
        onNavigateToPayments={() => setActiveTab('payments')}
      />

      <div className="flex-1 overflow-y-auto">
        <div className="max-w-7xl mx-auto px-4 py-8">
        <Tabs value={activeTab} onValueChange={handleTabChange} className="space-y-6">
          {/* Menu reorganizado: Dashboard como primeiro item, 10 por linha com destaque verde-azulado */}
          <TabsList className="grid grid-cols-5 md:grid-cols-11 gap-2 bg-transparent h-auto p-0">
            {/* Primeira linha - 10 itens */}
            <TabsTrigger 
              value="dashboard" 
              data-testid="tab-dashboard"
              className="data-[state=active]:bg-teal-500 data-[state=active]:text-white hover:bg-teal-50"
            >
              <Bell className="w-4 h-4 mr-1" />
              Dashboard
            </TabsTrigger>
            <TabsTrigger 
              value="resellers" 
              data-testid="tab-resellers"
              className="data-[state=active]:bg-teal-500 data-[state=active]:text-white hover:bg-teal-50"
            >
              <Users className="w-4 h-4 mr-1" />
              Revendas
            </TabsTrigger>
            <TabsTrigger 
              value="agents" 
              data-testid="tab-agents"
              className="data-[state=active]:bg-teal-500 data-[state=active]:text-white hover:bg-teal-50"
            >
              <Users className="w-4 h-4 mr-1" />
              Atendentes
            </TabsTrigger>
            <TabsTrigger 
              value="ai-agents" 
              data-testid="tab-ai-agents"
              className="data-[state=active]:bg-teal-500 data-[state=active]:text-white hover:bg-teal-50"
            >
              <Bot className="w-4 h-4 mr-1" />
              Agentes IA
            </TabsTrigger>
            <TabsTrigger 
              value="departments" 
              data-testid="tab-departments"
              className="data-[state=active]:bg-teal-500 data-[state=active]:text-white hover:bg-teal-50"
            >
              <Folder className="w-4 h-4 mr-1" />
              Departamentos
            </TabsTrigger>
            <TabsTrigger 
              value="quick" 
              data-testid="tab-quick"
              className="data-[state=active]:bg-teal-500 data-[state=active]:text-white hover:bg-teal-50"
            >
              <MessageSquare className="w-4 h-4 mr-1" />
              Msg Rápidas
            </TabsTrigger>
            <TabsTrigger 
              value="security" 
              data-testid="tab-security"
              className="data-[state=active]:bg-teal-500 data-[state=active]:text-white hover:bg-teal-50"
            >
              <Shield className="w-4 h-4 mr-1" />
              Dados Permitidos
            </TabsTrigger>
            <TabsTrigger 
              value="api" 
              data-testid="tab-api"
              className="data-[state=active]:bg-teal-500 data-[state=active]:text-white hover:bg-teal-50"
            >
              <Settings className="w-4 h-4 mr-1" />
              API
            </TabsTrigger>
            <TabsTrigger 
              value="notices" 
              data-testid="tab-notices"
              className="data-[state=active]:bg-teal-500 data-[state=active]:text-white hover:bg-teal-50"
            >
              <Bell className="w-4 h-4 mr-1" />
              Avisos
            </TabsTrigger>
            <TabsTrigger 
              value="auto-responder" 
              data-testid="tab-auto-responder"
              className="data-[state=active]:bg-teal-500 data-[state=active]:text-white hover:bg-teal-50"
            >
              <Zap className="w-4 h-4 mr-1" />
              Auto-Responder
            </TabsTrigger>
            <TabsTrigger 
              value="domain" 
              data-testid="tab-domain"
              className="data-[state=active]:bg-blue-500 data-[state=active]:text-white hover:bg-blue-50"
            >
              <Globe className="w-4 h-4 mr-1" />
              Domínio
            </TabsTrigger>
            
            {/* Segunda linha - 4 itens */}
            <TabsTrigger 
              value="tutorials" 
              data-testid="tab-tutorials"
              className="data-[state=active]:bg-teal-500 data-[state=active]:text-white hover:bg-teal-50"
            >
              <BookOpen className="w-4 h-4 mr-1" />
              Tutoriais/Apps
            </TabsTrigger>
            <TabsTrigger 
              value="iptv-apps" 
              data-testid="tab-iptv-apps"
              className="data-[state=active]:bg-teal-500 data-[state=active]:text-white hover:bg-teal-50"
            >
              <Monitor className="w-4 h-4 mr-1" />
              Aplicativos
            </TabsTrigger>
            <TabsTrigger 
              value="whatsapp" 
              data-testid="tab-whatsapp"
              className="data-[state=active]:bg-teal-500 data-[state=active]:text-white hover:bg-teal-50"
            >
              <Phone className="w-4 h-4 mr-1" />
              WhatsApp
            </TabsTrigger>
            <TabsTrigger 
              value="vendas-bot" 
              data-testid="tab-vendas-bot"
              className="data-[state=active]:bg-blue-500 data-[state=active]:text-white hover:bg-blue-50"
            >
              <Bot className="w-4 h-4 mr-1" />
              WA Site
            </TabsTrigger>
            <TabsTrigger 
              value="payments" 
              data-testid="tab-payments"
              className="data-[state=active]:bg-teal-500 data-[state=active]:text-white hover:bg-teal-50"
            >
              <CreditCard className="w-4 h-4 mr-1" />
              Pagamentos
            </TabsTrigger>
          </TabsList>

          {/* Dashboard Tab - PRIMEIRO ITEM */}
          <TabsContent value="dashboard" className="space-y-6">
            {dashboardLoading ? (
              <div className="flex items-center justify-center h-64">
                <div className="text-center">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-teal-600 mx-auto mb-4"></div>
                  <p className="text-slate-600">Carregando dashboard...</p>
                </div>
              </div>
            ) : (
              <>
                {/* Cards de Estatísticas */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  {/* Mensagens em Entrada */}
                  <Card className="p-6">
                    <div className="flex items-center gap-3 mb-3">
                      <div className="p-3 bg-blue-50 rounded-lg">
                        <MessageSquare className="w-6 h-6 text-blue-600" />
                      </div>
                      <div>
                        <p className="text-sm text-slate-600">Em Entrada</p>
                        <h3 className="text-2xl font-bold">{dashboardStats.tickets_entrada || 0}</h3>
                      </div>
                    </div>
                    <p className="text-xs text-slate-500">Aguardando atendimento</p>
                  </Card>

                  {/* Em Atendimento */}
                  <Card className="p-6">
                    <div className="flex items-center gap-3 mb-3">
                      <div className="p-3 bg-green-50 rounded-lg">
                        <Users className="w-6 h-6 text-green-600" />
                      </div>
                      <div>
                        <p className="text-sm text-slate-600">Em Atendimento</p>
                        <h3 className="text-2xl font-bold">{dashboardStats.tickets_atendimento || 0}</h3>
                      </div>
                    </div>
                    <p className="text-xs text-slate-500">Conversas ativas</p>
                  </Card>

                  {/* Finalizadas Hoje */}
                  <Card className="p-6">
                    <div className="flex items-center gap-3 mb-3">
                      <div className="p-3 bg-purple-50 rounded-lg">
                        <CheckCircle className="w-6 h-6 text-purple-600" />
                      </div>
                      <div>
                        <p className="text-sm text-slate-600">Finalizadas Hoje</p>
                        <h3 className="text-2xl font-bold">{dashboardStats.tickets_finalizadas_hoje || 0}</h3>
                      </div>
                    </div>
                    <p className="text-xs text-slate-500">Conversas concluídas</p>
                  </Card>

                  {/* Tempo Médio */}
                  <Card className="p-6">
                    <div className="flex items-center gap-3 mb-3">
                      <div className="p-3 bg-orange-50 rounded-lg">
                        <Clock className="w-6 h-6 text-orange-600" />
                      </div>
                      <div>
                        <p className="text-sm text-slate-600">Tempo Médio</p>
                        <h3 className="text-2xl font-bold">{dashboardStats.tempo_medio_resposta || 'N/A'}</h3>
                      </div>
                    </div>
                    <p className="text-xs text-slate-500">Resposta inicial</p>
                  </Card>
                </div>

                {/* Atendentes Online */}
                <Card className="p-6">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2">
                      <Users className="w-5 h-5 text-teal-600" />
                      <h3 className="text-lg font-semibold">Atendentes Online</h3>
                    </div>
                    <span className="text-sm bg-green-100 text-green-700 px-3 py-1 rounded-full">
                      {agentsOnline.online_count || 0} online
                    </span>
                  </div>

                  {agentsOnline.online_agents && agentsOnline.online_agents.length > 0 ? (
                    <div className="space-y-3">
                      {agentsOnline.online_agents.map((agent) => (
                        <div key={agent.id} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg hover:bg-slate-100 transition">
                          <div className="flex items-center gap-3">
                            <div className="relative">
                              <div className="w-10 h-10 bg-teal-600 rounded-full flex items-center justify-center text-white font-semibold">
                                {agent.name.charAt(0).toUpperCase()}
                              </div>
                              <div className="absolute -bottom-1 -right-1 w-4 h-4 bg-green-500 rounded-full border-2 border-white"></div>
                            </div>
                            <div>
                              <p className="font-medium">{agent.name}</p>
                              <p className="text-xs text-slate-500">{agent.email}</p>
                              <p className="text-xs text-slate-600 mt-1">
                                📊 {agent.active_tickets} conversas ativas
                              </p>
                            </div>
                          </div>
                          <Button 
                            size="sm" 
                            variant="outline"
                            className="gap-2"
                            onClick={() => toast.info('Funcionalidade de monitoramento em breve!')}
                          >
                            <Eye className="w-4 h-4" />
                            Monitorar
                          </Button>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-8 text-slate-400">
                      <Users className="w-12 h-12 mx-auto mb-2 opacity-50" />
                      <p>Nenhum atendente online no momento</p>
                    </div>
                  )}

                  {agentsOnline.offline_agents && agentsOnline.offline_agents.length > 0 && (
                    <details className="mt-4">
                      <summary className="cursor-pointer text-sm text-slate-600 hover:text-slate-900">
                        Ver {agentsOnline.offline_count} atendente(s) offline
                      </summary>
                      <div className="mt-3 space-y-2">
                        {agentsOnline.offline_agents.map((agent) => (
                          <div key={agent.id} className="flex items-center gap-3 p-2 text-sm">
                            <div className="w-8 h-8 bg-slate-300 rounded-full flex items-center justify-center text-white font-semibold">
                              {agent.name.charAt(0).toUpperCase()}
                            </div>
                            <div className="flex-1">
                              <p className="text-slate-600">{agent.name}</p>
                              <p className="text-xs text-slate-400">{agent.email}</p>
                            </div>
                            <span className="text-xs text-slate-400">Offline</span>
                          </div>
                        ))}
                      </div>
                    </details>
                  )}
                </Card>

                {/* Agentes de IA */}
                <Card className="p-6">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2">
                      <Bot className="w-5 h-5 text-teal-600" />
                      <h3 className="text-lg font-semibold">Agentes de IA</h3>
                    </div>
                    <span className="text-sm bg-purple-100 text-purple-700 px-3 py-1 rounded-full">
                      {aiAgentsStatus.active_count || 0} ativos
                    </span>
                  </div>

                  {aiAgentsStatus.agents && aiAgentsStatus.agents.length > 0 ? (
                    <div className="space-y-3">
                      {aiAgentsStatus.agents.map((agent, idx) => (
                        <div key={idx} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                          <div className="flex items-center gap-3">
                            <div className={`w-10 h-10 ${agent.status === 'active' ? 'bg-teal-600' : 'bg-slate-400'} rounded-full flex items-center justify-center text-white`}>
                              <Bot className="w-6 h-6" />
                            </div>
                            <div>
                              <p className="font-medium">{agent.name}</p>
                              <p className="text-xs text-slate-500">Modelo: {agent.model}</p>
                              <p className="text-xs text-slate-600 mt-1">
                                💬 {agent.interactions_today} interações hoje
                              </p>
                            </div>
                          </div>
                          <div className={`px-3 py-1 rounded-full text-xs ${
                            agent.status === 'active' ? 'bg-green-100 text-green-700' :
                            agent.status === 'disabled' ? 'bg-yellow-100 text-yellow-700' :
                            'bg-slate-100 text-slate-700'
                          }`}>
                            {agent.status === 'active' ? 'Ativo' :
                             agent.status === 'disabled' ? 'Desabilitado' :
                             'Não Configurado'}
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-8 text-slate-400">
                      <Bot className="w-12 h-12 mx-auto mb-2 opacity-50" />
                      <p>Nenhum agente de IA configurado</p>
                    </div>
                  )}
                </Card>

                {/* Avisos Importantes */}
                <Card className="p-6 border-2 border-orange-200 bg-orange-50/30">
                  <div className="flex items-center gap-2 mb-4">
                    <Bell className="w-5 h-5 text-orange-600 animate-pulse" />
                    <h3 className="text-lg font-semibold text-orange-900">⚠️ Avisos Importantes</h3>
                  </div>

                  {importantAlerts && importantAlerts.length > 0 ? (
                    <div className="space-y-3">
                      {importantAlerts.map((alert, idx) => (
                        <div 
                          key={idx} 
                          className={`p-4 rounded-lg border-2 ${
                            alert.severity === 'warning' ? 'bg-yellow-50 border-yellow-300' :
                            alert.severity === 'error' ? 'bg-red-50 border-red-300' :
                            'bg-blue-50 border-blue-300'
                          }`}
                        >
                          <div className="flex items-start gap-3">
                            <span className="text-2xl">{alert.icon}</span>
                            <div className="flex-1">
                              <h4 className="font-semibold text-slate-900">{alert.title}</h4>
                              <p className="text-sm text-slate-700 mt-1">{alert.message}</p>
                              {alert.type === 'whatsapp' && (
                                <Button
                                  size="sm"
                                  variant="outline"
                                  className="mt-2"
                                  onClick={() => setActiveTab('whatsapp')}
                                >
                                  Verificar WhatsApp
                                </Button>
                              )}
                              {alert.type === 'ai' && (
                                <Button
                                  size="sm"
                                  variant="outline"
                                  className="mt-2"
                                  onClick={() => setActiveTab('ai-agents')}
                                >
                                  Configurar IA
                                </Button>
                              )}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-8 text-slate-400">
                      <CheckCircle className="w-12 h-12 mx-auto mb-2 opacity-50 text-green-500" />
                      <p className="text-green-700 font-medium">✅ Tudo funcionando perfeitamente!</p>
                      <p className="text-sm text-slate-500 mt-1">Nenhum aviso importante no momento</p>
                    </div>
                  )}
                </Card>
              </>
            )}
          </TabsContent>

          {/* Resellers Tab */}
          <TabsContent value="resellers" className="space-y-6">
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-4">Nova Revenda</h3>
              <p className="text-sm text-slate-600 mb-4">Crie sub-revendas com isolamento completo de dados</p>
              <div className="grid md:grid-cols-2 gap-4 mb-4">
                <Input
                  placeholder="Nome da Revenda"
                  value={newReseller.name}
                  onChange={(e) => setNewReseller({ ...newReseller, name: e.target.value })}
                />
                <Input
                  placeholder="Email"
                  type="email"
                  value={newReseller.email}
                  onChange={(e) => setNewReseller({ ...newReseller, email: e.target.value })}
                />
                <Input
                  placeholder="Senha"
                  type="password"
                  value={newReseller.password}
                  onChange={(e) => setNewReseller({ ...newReseller, password: e.target.value })}
                />
                <Input
                  placeholder="Domínio customizado (opcional)"
                  value={newReseller.domain}
                  onChange={(e) => setNewReseller({ ...newReseller, domain: e.target.value })}
                />
              </div>
              <Button onClick={handleCreateReseller} className="bg-purple-600 hover:bg-purple-700">
                <Plus className="w-4 h-4 mr-2" />
                Criar Revenda
              </Button>
            </Card>

            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-4">Revendas Existentes</h3>
              <p className="text-sm text-slate-600 mb-4">Sistema multi-tenant ativo com isolamento de dados</p>
              <div className="grid gap-4">
                {(resellers || []).map((reseller) => (
                  <Card key={reseller.id} className="p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h4 className="font-semibold">{reseller.name}</h4>
                        <p className="text-sm text-slate-600">Email: {reseller.email}</p>
                        {reseller.custom_domain && (
                          <p className="text-sm text-emerald-600">Domínio: {reseller.custom_domain}</p>
                        )}
                        <span className="text-xs bg-purple-100 text-purple-700 px-2 py-1 rounded inline-block mt-2">
                          Nível {reseller.level || 0}
                        </span>
                        {reseller.is_active !== undefined && (
                          <span className={`text-xs px-2 py-1 rounded inline-block ml-2 mt-2 ${reseller.is_active ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                            {reseller.is_active ? 'Ativo' : 'Inativo'}
                          </span>
                        )}
                      </div>
                      <div className="flex gap-2">
                        <Dialog>
                          <DialogTrigger asChild>
                            <Button 
                              variant="outline" 
                              size="sm"
                              onClick={() => setEditingReseller({...reseller, password: ''})}
                            >
                              <Edit className="w-4 h-4" />
                            </Button>
                          </DialogTrigger>
                          <DialogContent>
                            <DialogHeader>
                              <DialogTitle>✏️ Editar Revenda</DialogTitle>
                            </DialogHeader>
                            {editingReseller && editingReseller.id === reseller.id && (
                              <div className="space-y-4">
                                <div>
                                  <label className="text-sm font-medium block mb-1">Nome:</label>
                                  <Input
                                    value={editingReseller.name}
                                    onChange={(e) => setEditingReseller({...editingReseller, name: e.target.value})}
                                    placeholder="Nome da revenda"
                                  />
                                </div>
                                <div>
                                  <label className="text-sm font-medium block mb-1">Email:</label>
                                  <Input
                                    type="email"
                                    value={editingReseller.email}
                                    onChange={(e) => setEditingReseller({...editingReseller, email: e.target.value})}
                                    placeholder="Email de acesso"
                                  />
                                </div>
                                <div>
                                  <label className="text-sm font-medium block mb-1">Nova Senha (deixe vazio para manter):</label>
                                  <Input
                                    type="password"
                                    value={editingReseller.password || ''}
                                    onChange={(e) => setEditingReseller({...editingReseller, password: e.target.value})}
                                    placeholder="Nova senha (opcional)"
                                  />
                                </div>
                                <div>
                                  <label className="text-sm font-medium block mb-1">Domínio Customizado:</label>
                                  <Input
                                    value={editingReseller.custom_domain || ''}
                                    onChange={(e) => setEditingReseller({...editingReseller, custom_domain: e.target.value})}
                                    placeholder="exemplo.com"
                                  />
                                </div>
                                <div className="flex items-center gap-2">
                                  <input
                                    type="checkbox"
                                    checked={editingReseller.is_active !== false}
                                    onChange={(e) => setEditingReseller({...editingReseller, is_active: e.target.checked})}
                                    className="w-4 h-4"
                                  />
                                  <label className="text-sm font-medium">Ativo</label>
                                </div>
                                <Button onClick={handleUpdateReseller} className="w-full">
                                  <Save className="w-4 h-4 mr-2" />
                                  Salvar Alterações
                                </Button>
                              </div>
                            )}
                          </DialogContent>
                        </Dialog>
                        <Button 
                          variant="destructive" 
                          size="sm"
                          onClick={() => handleDeleteReseller(reseller.id)}
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  </Card>
                ))}
              </div>
            </Card>
          </TabsContent>

          {/* Agents Tab */}
          <TabsContent value="agents" className="space-y-6">
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-4">Novo Atendente</h3>
              <div className="grid md:grid-cols-2 gap-4">
                <Input
                  data-testid="agent-name-input"
                  placeholder="Nome"
                  value={newAgent.name}
                  onChange={(e) => setNewAgent({ ...newAgent, name: e.target.value })}
                />
                <Input
                  data-testid="agent-login-input-field"
                  placeholder="Login"
                  value={newAgent.login}
                  onChange={(e) => setNewAgent({ ...newAgent, login: e.target.value })}
                />
                <Input
                  data-testid="agent-password-input-field"
                  type="password"
                  placeholder="Senha"
                  value={newAgent.password}
                  onChange={(e) => setNewAgent({ ...newAgent, password: e.target.value })}
                />
                <Input
                  data-testid="agent-avatar-input"
                  placeholder="Avatar URL (opcional)"
                  value={newAgent.avatar}
                  onChange={(e) => setNewAgent({ ...newAgent, avatar: e.target.value })}
                />
              </div>
              
              {/* Seleção de Departamentos */}
              <div className="mt-4 p-4 bg-indigo-50 border border-indigo-200 rounded-lg">
                <label className="text-sm font-semibold text-indigo-900 mb-2 block">
                  📂 Departamentos (Atendente verá apenas tickets destes departamentos)
                </label>
                <p className="text-xs text-indigo-700 mb-3">
                  Selecione quais departamentos este atendente pode acessar. Se não selecionar nenhum, terá acesso a todos.
                </p>
                {departments.length > 0 ? (
                  <div className="space-y-2">
                    {departments.map(dept => (
                      <label key={dept.id} className="flex items-center gap-2 p-2 bg-white rounded border hover:bg-indigo-50 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={newAgent.department_ids.includes(dept.id)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setNewAgent({
                                ...newAgent,
                                department_ids: [...newAgent.department_ids, dept.id]
                              });
                            } else {
                              setNewAgent({
                                ...newAgent,
                                department_ids: newAgent.department_ids.filter(id => id !== dept.id)
                              });
                            }
                          }}
                          className="w-4 h-4"
                        />
                        <span className="text-sm font-medium">{dept.name}</span>
                        {dept.description && (
                          <span className="text-xs text-slate-500">- {dept.description}</span>
                        )}
                      </label>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-slate-500 italic">Configure departamentos na aba "Departamentos" primeiro</p>
                )}
              </div>
              
              <Button data-testid="create-agent-btn" onClick={handleCreateAgent} className="mt-4 bg-purple-600 hover:bg-purple-700">
                <Plus className="w-4 h-4 mr-2" />
                Adicionar Atendente
              </Button>
            </Card>

            <div className="grid gap-4">
              {agents.map((agent) => (
                <Card key={agent.id} className="p-6">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      {agent.avatar && (
                        <img src={agent.avatar} alt={agent.name} className="w-12 h-12 rounded-full object-cover" />
                      )}
                      <div>
                        <h4 className="font-semibold text-slate-900">{agent.name}</h4>
                        <p className="text-sm text-slate-600">@{agent.login}</p>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <Dialog>
                        <DialogTrigger asChild>
                          <Button data-testid={`edit-agent-${agent.id}-btn`} variant="outline" size="sm" onClick={() => setEditingAgent(agent)}>
                            <Edit className="w-4 h-4" />
                          </Button>
                        </DialogTrigger>
                        <DialogContent>
                          <DialogHeader>
                            <DialogTitle>Editar Atendente</DialogTitle>
                          </DialogHeader>
                          {editingAgent && editingAgent.id === agent.id && (
                            <div className="space-y-4">
                              <Input
                                placeholder="Nome"
                                defaultValue={agent.name}
                                onChange={(e) => setEditingAgent({ ...editingAgent, name: e.target.value })}
                              />
                              <Input
                                placeholder="Login"
                                defaultValue={agent.login}
                                onChange={(e) => setEditingAgent({ ...editingAgent, login: e.target.value })}
                              />
                              <Input
                                type="password"
                                placeholder="Nova senha (opcional)"
                                onChange={(e) => setEditingAgent({ ...editingAgent, password: e.target.value })}
                              />
                              <Button onClick={() => handleUpdateAgent(agent.id, editingAgent)} className="w-full">
                                Salvar
                              </Button>
                            </div>
                          )}
                        </DialogContent>
                      </Dialog>
                      <Button data-testid={`delete-agent-${agent.id}-btn`} variant="outline" size="sm" onClick={() => handleDeleteAgent(agent.id)}>
                        <Trash2 className="w-4 h-4 text-red-600" />
                      </Button>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          </TabsContent>

          {/* AI Agents Tab - NOVO */}
          <TabsContent value="ai-agents" className="space-y-6">
            <AIAgentsManager />
          </TabsContent>

          {/* Departments Tab - NOVO */}
          <TabsContent value="departments" className="space-y-6">
            <DepartmentsManager />
          </TabsContent>

          {/* Quick Messages Tab */}
          <TabsContent value="quick" className="space-y-6">
            <Card className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold">Mensagens Rápidas</h3>
                <Button
                  data-testid="add-quick-block-btn"
                  size="sm"
                  onClick={() => setConfig({
                    ...config,
                    quick_blocks: [...config.quick_blocks, { name: '', text: '' }]
                  })}
                >
                  <Plus className="w-4 h-4 mr-2" />
                  Novo Bloco
                </Button>
              </div>
              <div className="space-y-4">
                {(config.quick_blocks || []).map((block, idx) => (
                  <div key={idx} className="border border-slate-200 rounded-lg p-4 space-y-3">
                    <div className="flex items-center justify-between">
                      <Input
                        placeholder="Nome do bloco"
                        value={block.name}
                        onChange={(e) => {
                          const updated = [...config.quick_blocks];
                          updated[idx].name = e.target.value;
                          setConfig({ ...config, quick_blocks: updated });
                        }}
                        className="flex-1 mr-2"
                      />
                      <Button
                        data-testid={`remove-quick-block-${idx}-btn`}
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          const updated = config.quick_blocks.filter((_, i) => i !== idx);
                          setConfig({ ...config, quick_blocks: updated });
                        }}
                      >
                        <Trash2 className="w-4 h-4 text-red-600" />
                      </Button>
                    </div>
                    <Textarea
                      placeholder="Texto da mensagem"
                      value={block.text}
                      onChange={(e) => {
                        const updated = [...config.quick_blocks];
                        updated[idx].text = e.target.value;
                        setConfig({ ...config, quick_blocks: updated });
                      }}
                      rows={3}
                    />
                  </div>
                ))}
              </div>
              <Button data-testid="save-quick-blocks-btn" onClick={handleSaveConfig} className="mt-4 bg-purple-600 hover:bg-purple-700">
                Salvar Configurações
              </Button>
            </Card>
          </TabsContent>

          {/* Security Tab - Dados Permitidos */}
          <TabsContent value="security" className="space-y-6">
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-4">🔐 Dados Permitidos para Envio</h3>
              <p className="text-sm text-slate-600 mb-6">Configure quais dados sensíveis podem ser enviados nas conversas</p>
              
              {/* Logo/Foto do Suporte */}
              <div className="mb-6 bg-gradient-to-r from-indigo-50 to-purple-50 border-2 border-indigo-200 rounded-lg p-4">
                <h4 className="font-semibold mb-3">🖼️ Logo/Foto do Suporte</h4>
                <p className="text-xs text-slate-600 mb-3">Esta imagem aparecerá como foto do suporte nas conversas com clientes</p>
                <div className="flex items-center gap-4">
                  <div className="w-20 h-20 bg-white rounded-full flex items-center justify-center overflow-hidden border-2 border-indigo-200">
                    {config.support_avatar ? (
                      <img src={config.support_avatar} alt="Logo do Suporte" className="w-full h-full object-cover" />
                    ) : (
                      <Shield className="w-10 h-10 text-indigo-400" />
                    )}
                  </div>
                  <div className="flex-1">
                    <input
                      ref={logoInputRef}
                      type="file"
                      accept="image/*"
                      onChange={handleLogoUpload}
                      className="hidden"
                    />
                    <Button
                      onClick={() => logoInputRef.current?.click()}
                      disabled={uploadingLogo}
                      className="bg-indigo-600 hover:bg-indigo-700"
                      size="sm"
                    >
                      {uploadingLogo ? 'Enviando...' : '📤 Fazer Upload da Logo'}
                    </Button>
                    <p className="text-xs text-slate-500 mt-1">Formato: JPG, PNG. Recomendado: 512x512px</p>
                  </div>
                </div>
              </div>

              {/* Foto de Perfil da Área do Cliente */}
              <div className="mb-6 bg-gradient-to-r from-purple-50 to-pink-50 border-2 border-purple-200 rounded-lg p-4">
                <h4 className="font-semibold mb-3">👤 Foto de Perfil da Área do Cliente</h4>
                <p className="text-xs text-slate-600 mb-3">Esta foto aparecerá na área do cliente. Cada revenda pode personalizar a sua.</p>
                <div className="flex items-center gap-4 mb-4">
                  <div className="w-24 h-24 bg-white rounded-lg flex items-center justify-center overflow-hidden border-2 border-purple-200">
                    <img src={clientLogoUrl} alt="Foto do Cliente" className="w-full h-full object-cover" />
                  </div>
                  <div className="flex-1 space-y-2">
                    {/* Upload de arquivo */}
                    <div>
                      <input
                        ref={clientLogoInputRef}
                        type="file"
                        accept="image/*"
                        onChange={handleClientLogoUpload}
                        className="hidden"
                      />
                      <Button
                        onClick={() => clientLogoInputRef.current?.click()}
                        disabled={uploadingClientLogo}
                        className="bg-purple-600 hover:bg-purple-700"
                        size="sm"
                      >
                        {uploadingClientLogo ? 'Enviando...' : '📤 Fazer Upload'}
                      </Button>
                      <p className="text-xs text-slate-500 mt-1">Formato: JPG, PNG</p>
                    </div>
                    {/* Link URL */}
                    <div className="flex gap-2">
                      <Input
                        placeholder="Ou cole o link da imagem"
                        value={clientLogoLinkInput}
                        onChange={(e) => setClientLogoLinkInput(e.target.value)}
                        className="flex-1 text-sm"
                      />
                      <Button
                        onClick={handleClientLogoLinkUpdate}
                        size="sm"
                        variant="outline"
                      >
                        🔗 Usar Link
                      </Button>
                    </div>
                  </div>
                </div>
              </div>

              {/* Chave PIX */}
              <div className="mb-6">
                <h4 className="font-semibold mb-3">💰 Chave PIX</h4>
                <div className="flex gap-2">
                  <Input
                    placeholder="Digite a chave PIX (CPF, Email, Telefone ou Chave Aleatória)"
                    value={config.pix_key || ''}
                    onChange={(e) => setConfig({ ...config, pix_key: e.target.value })}
                    className="flex-1"
                  />
                  <Button onClick={handleSaveConfig} className="bg-emerald-600 hover:bg-emerald-700">
                    💾 Salvar PIX
                  </Button>
                </div>
                {config.pix_key && (
                  <p className="text-sm text-emerald-600 mt-2">✅ Chave PIX cadastrada: {config.pix_key}</p>
                )}
              </div>

              {/* CPFs Permitidos */}
              <div className="mb-6">
                <h4 className="font-semibold mb-3">📄 CPFs Permitidos</h4>
                <p className="text-xs text-slate-500 mb-2">Apenas CPFs cadastrados aqui poderão ser enviados nas conversas</p>
                <div className="flex gap-2 mb-2">
                  <Input
                    placeholder="000.000.000-00"
                    id="new-cpf"
                    onKeyPress={(e) => {
                      if (e.key === 'Enter') {
                        const input = document.getElementById('new-cpf');
                        const cpf = input.value.trim();
                        if (cpf) {
                          const cpfs = config.allowed_data?.cpfs || [];
                          setConfig({
                            ...config,
                            allowed_data: { ...config.allowed_data, cpfs: [...cpfs, cpf] }
                          });
                          input.value = '';
                        }
                      }
                    }}
                  />
                  <Button onClick={() => {
                    const input = document.getElementById('new-cpf');
                    const cpf = input.value.trim();
                    if (cpf) {
                      const cpfs = config.allowed_data?.cpfs || [];
                      setConfig({
                        ...config,
                        allowed_data: { ...config.allowed_data, cpfs: [...cpfs, cpf] }
                      });
                      input.value = '';
                      handleSaveConfig();
                    }
                  }}>
                    Adicionar
                  </Button>
                </div>
                <div className="flex flex-wrap gap-2">
                  {(config.allowed_data?.cpfs || []).map((cpf, idx) => (
                    <span key={idx} className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm flex items-center gap-2">
                      {cpf}
                      <button onClick={() => {
                        const cpfs = config.allowed_data.cpfs.filter((_, i) => i !== idx);
                        setConfig({ ...config, allowed_data: { ...config.allowed_data, cpfs } });
                        handleSaveConfig();
                      }} className="text-red-600 hover:text-red-800">×</button>
                    </span>
                  ))}
                </div>
              </div>

              {/* Emails Permitidos */}
              <div className="mb-6">
                <h4 className="font-semibold mb-3">📧 Emails Permitidos</h4>
                <div className="flex gap-2 mb-2">
                  <Input
                    placeholder="email@exemplo.com"
                    type="email"
                    id="new-email"
                    onKeyPress={(e) => {
                      if (e.key === 'Enter') {
                        const input = document.getElementById('new-email');
                        const email = input.value.trim();
                        if (email) {
                          const emails = config.allowed_data?.emails || [];
                          setConfig({
                            ...config,
                            allowed_data: { ...config.allowed_data, emails: [...emails, email] }
                          });
                          input.value = '';
                        }
                      }
                    }}
                  />
                  <Button onClick={() => {
                    const input = document.getElementById('new-email');
                    const email = input.value.trim();
                    if (email) {
                      const emails = config.allowed_data?.emails || [];
                      setConfig({
                        ...config,
                        allowed_data: { ...config.allowed_data, emails: [...emails, email] }
                      });
                      input.value = '';
                      handleSaveConfig();
                    }
                  }}>
                    Adicionar
                  </Button>
                </div>
                <div className="flex flex-wrap gap-2">
                  {(config.allowed_data?.emails || []).map((email, idx) => (
                    <span key={idx} className="bg-green-100 text-green-800 px-3 py-1 rounded-full text-sm flex items-center gap-2">
                      {email}
                      <button onClick={() => {
                        const emails = config.allowed_data.emails.filter((_, i) => i !== idx);
                        setConfig({ ...config, allowed_data: { ...config.allowed_data, emails } });
                        handleSaveConfig();
                      }} className="text-red-600 hover:text-red-800">×</button>
                    </span>
                  ))}
                </div>
              </div>

              {/* Telefones Permitidos */}
              <div className="mb-6">
                <h4 className="font-semibold mb-3">📱 Telefones/WhatsApp Permitidos</h4>
                <div className="flex gap-2 mb-2">
                  <Input
                    placeholder="+55 11 91111-1111"
                    id="new-phone"
                    onKeyPress={(e) => {
                      if (e.key === 'Enter') {
                        const input = document.getElementById('new-phone');
                        const phone = input.value.trim();
                        if (phone) {
                          const phones = config.allowed_data?.phones || [];
                          setConfig({
                            ...config,
                            allowed_data: { ...config.allowed_data, phones: [...phones, phone] }
                          });
                          input.value = '';
                        }
                      }
                    }}
                  />
                  <Button onClick={() => {
                    const input = document.getElementById('new-phone');
                    const phone = input.value.trim();
                    if (phone) {
                      const phones = config.allowed_data?.phones || [];
                      setConfig({
                        ...config,
                        allowed_data: { ...config.allowed_data, phones: [...phones, phone] }
                      });
                      input.value = '';
                      handleSaveConfig();
                    }
                  }}>
                    Adicionar
                  </Button>
                </div>
                <div className="flex flex-wrap gap-2">
                  {(config.allowed_data?.phones || []).map((phone, idx) => (
                    <span key={idx} className="bg-purple-100 text-purple-800 px-3 py-1 rounded-full text-sm flex items-center gap-2">
                      {phone}
                      <button onClick={() => {
                        const phones = config.allowed_data.phones.filter((_, i) => i !== idx);
                        setConfig({ ...config, allowed_data: { ...config.allowed_data, phones } });
                        handleSaveConfig();
                      }} className="text-red-600 hover:text-red-800">×</button>
                    </span>
                  ))}
                </div>
              </div>

              {/* Chaves Aleatórias PIX */}
              <div>
                <h4 className="font-semibold mb-3">🔑 Chaves Aleatórias PIX</h4>
                <div className="flex gap-2 mb-2">
                  <Input
                    placeholder="UUID ou chave aleatória"
                    id="new-random-key"
                    onKeyPress={(e) => {
                      if (e.key === 'Enter') {
                        const input = document.getElementById('new-random-key');
                        const key = input.value.trim();
                        if (key) {
                          const keys = config.allowed_data?.random_keys || [];
                          setConfig({
                            ...config,
                            allowed_data: { ...config.allowed_data, random_keys: [...keys, key] }
                          });
                          input.value = '';
                        }
                      }
                    }}
                  />
                  <Button onClick={() => {
                    const input = document.getElementById('new-random-key');
                    const key = input.value.trim();
                    if (key) {
                      const keys = config.allowed_data?.random_keys || [];
                      setConfig({
                        ...config,
                        allowed_data: { ...config.allowed_data, random_keys: [...keys, key] }
                      });
                      input.value = '';
                      handleSaveConfig();
                    }
                  }}>
                    Adicionar
                  </Button>
                </div>
                <div className="flex flex-wrap gap-2">
                  {(config.allowed_data?.random_keys || []).map((key, idx) => (
                    <span key={idx} className="bg-orange-100 text-orange-800 px-3 py-1 rounded-full text-sm flex items-center gap-2">
                      {key}
                      <button onClick={() => {
                        const keys = config.allowed_data.random_keys.filter((_, i) => i !== idx);
                        setConfig({ ...config, allowed_data: { ...config.allowed_data, random_keys: keys } });
                        handleSaveConfig();
                      }} className="text-red-600 hover:text-red-800">×</button>
                    </span>
                  ))}
                </div>
              </div>
            </Card>
          </TabsContent>

          {/* API Tab */}
          <TabsContent value="api" className="space-y-6">
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-4">🔌 Integração API Office</h3>
              <p className="text-sm text-slate-600 mb-6">Configure a API para buscar automaticamente usuário e senha dos clientes</p>
              
              <div className="space-y-4">
                <div>
                  <label className="text-sm font-medium mb-2 block">URL da API</label>
                  <Input
                    placeholder="https://api.office.com/v1/..."
                    value={config.api_integration?.api_url || ''}
                    onChange={(e) => setConfig({
                      ...config,
                      api_integration: { ...config.api_integration, api_url: e.target.value }
                    })}
                  />
                </div>
                
                <div>
                  <label className="text-sm font-medium mb-2 block">Token de Autenticação</label>
                  <Input
                    type="password"
                    placeholder="Bearer token ou API key"
                    value={config.api_integration?.api_token || ''}
                    onChange={(e) => setConfig({
                      ...config,
                      api_integration: { ...config.api_integration, api_token: e.target.value }
                    })}
                  />
                </div>

                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="api-enabled"
                    checked={config.api_integration?.api_enabled || false}
                    onChange={(e) => setConfig({
                      ...config,
                      api_integration: { ...config.api_integration, api_enabled: e.target.checked }
                    })}
                    className="rounded"
                  />
                  <label htmlFor="api-enabled" className="text-sm font-medium">
                    Ativar integração com API
                  </label>
                </div>

                <div className="flex gap-2">
                  <Button
                    onClick={async () => {
                      if (!config.api_integration?.api_url) {
                        toast.error('Configure a URL da API primeiro');
                        return;
                      }
                      try {
                        toast.info('Testando conexão...');
                        // TODO: Implementar teste real quando houver API
                        setTimeout(() => toast.success('✅ API configurada! (teste futuro)'), 1000);
                      } catch (error) {
                        toast.error('Erro ao testar API');
                      }
                    }}
                    variant="outline"
                  >
                    🧪 Testar Conexão
                  </Button>
                  
                  <Button onClick={handleSaveConfig} className="bg-blue-600 hover:bg-blue-700">
                    💾 Salvar Configuração
                  </Button>
                </div>

                {config.api_integration?.api_enabled && (
                  <div className="bg-green-50 border border-green-200 rounded-lg p-4 mt-4">
                    <p className="text-sm text-green-800">
                      ✅ Integração API ativa! Os atendentes poderão buscar credenciais automaticamente.
                    </p>
                  </div>
                )}
              </div>
            </Card>
          </TabsContent>

          {/* AI Tab */}
          {/* Config Tab */}
          <TabsContent value="config" className="space-y-6">
            <Card className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold">Auto-Resposta</h3>
                <Button
                  data-testid="add-auto-reply-btn"
                  size="sm"
                  onClick={() => setConfig({
                    ...config,
                    auto_reply: [...config.auto_reply, { q: '', a: '' }]
                  })}
                >
                  <Plus className="w-4 h-4 mr-2" />
                  Nova Regra
                </Button>
              </div>
              <div className="space-y-4">
                {(config.auto_reply || []).map((rule, idx) => (
                  <div key={idx} className="border border-slate-200 rounded-lg p-4 space-y-3">
                    <div className="flex items-center justify-between">
                      <h4 className="font-medium text-slate-700">Regra {idx + 1}</h4>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          const updated = config.auto_reply.filter((_, i) => i !== idx);
                          setConfig({ ...config, auto_reply: updated });
                        }}
                      >
                        <Trash2 className="w-4 h-4 text-red-600" />
                      </Button>
                    </div>
                    <Input
                      placeholder="Pergunta do cliente"
                      value={rule.q}
                      onChange={(e) => {
                        const updated = [...config.auto_reply];
                        updated[idx].q = e.target.value;
                        setConfig({ ...config, auto_reply: updated });
                      }}
                    />
                    <Textarea
                      placeholder="Resposta automática"
                      value={rule.a}
                      onChange={(e) => {
                        const updated = [...config.auto_reply];
                        updated[idx].a = e.target.value;
                        setConfig({ ...config, auto_reply: updated });
                      }}
                      rows={2}
                    />
                  </div>
                ))}
              </div>
              <Button onClick={handleSaveConfig} className="mt-4 bg-purple-600 hover:bg-purple-700">
                Salvar Auto-Resposta
              </Button>
            </Card>

            <Card className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold">Aplicativos / Tutoriais</h3>
                <Button
                  data-testid="add-app-btn"
                  size="sm"
                  onClick={() => setConfig({
                    ...config,
                    apps: [...config.apps, { cat: 'SmartTV', title: '', content: '' }]
                  })}
                >
                  <Plus className="w-4 h-4 mr-2" />
                  Novo Item
                </Button>
              </div>
              <div className="space-y-4">
                {(config.apps || []).map((app, idx) => (
                  <div key={idx} className="border border-slate-200 rounded-lg p-4 space-y-3">
                    <div className="flex items-center gap-2">
                      <Select
                        value={app.cat}
                        onValueChange={(value) => {
                          const updated = [...config.apps];
                          updated[idx].cat = value;
                          setConfig({ ...config, apps: updated });
                        }}
                      >
                        <SelectTrigger className="w-[200px]">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {['Tv box', 'SmartTV', 'Celular IOS', 'Celular Android', 'AndroidTV', 'Projetor', 'Fire stick TV', 'Video Game', 'Chromecast'].map(cat => (
                            <SelectItem key={cat} value={cat}>{cat}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      <Input
                        placeholder="Título"
                        value={app.title}
                        onChange={(e) => {
                          const updated = [...config.apps];
                          updated[idx].title = e.target.value;
                          setConfig({ ...config, apps: updated });
                        }}
                        className="flex-1"
                      />
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          const updated = config.apps.filter((_, i) => i !== idx);
                          setConfig({ ...config, apps: updated });
                        }}
                      >
                        <Trash2 className="w-4 h-4 text-red-600" />
                      </Button>
                    </div>
                    <Textarea
                      placeholder="Conteúdo / instruções"
                      value={app.content}
                      onChange={(e) => {
                        const updated = [...config.apps];
                        updated[idx].content = e.target.value;
                        setConfig({ ...config, apps: updated });
                      }}
                      rows={3}
                    />
                  </div>
                ))}
              </div>
              <Button onClick={handleSaveConfig} className="mt-4 bg-purple-600 hover:bg-purple-700">
                Salvar Aplicativos
              </Button>
            </Card>
          </TabsContent>

          {/* Notices Tab */}
          <TabsContent value="notices" className="space-y-6">
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-4">Publicar Novo Aviso</h3>
              <NoticeForm onSubmit={handleCreateNotice} />
            </Card>

            <div className="grid gap-4">
              {notices.map((notice) => (
                <Card key={notice.id} className="p-4">
                  <div className="flex items-start gap-4">
                    {notice.kind === 'image' && (
                      <img src={notice.file_url} alt="" className="w-24 h-24 object-cover rounded-lg" />
                    )}
                    {notice.kind === 'video' && (
                      <video src={notice.file_url} controls className="w-48 rounded-lg" />
                    )}
                    {notice.kind === 'audio' && (
                      <audio src={notice.file_url} controls className="w-full" />
                    )}
                    <div className="flex-1">
                      {notice.text && <p className="text-slate-700">{notice.text}</p>}
                      <p className="text-xs text-slate-500 mt-2">
                        {new Date(notice.created_at).toLocaleString('pt-BR')}
                      </p>
                    </div>
                    <Button 
                      size="sm" 
                      variant="outline" 
                      onClick={() => handleDeleteNotice(notice.id)}
                      className="text-red-600 hover:text-red-700 hover:bg-red-50"
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </Card>
              ))}
            </div>
          </TabsContent>
          
          {/* Auto-Responder Tab */}
          <TabsContent value="auto-responder" className="space-y-6">
            <AutoResponderAdvanced />
          </TabsContent>
          
          {/* Tab de Domínio */}
          <TabsContent value="domain" className="space-y-6">
            <DomainConfig 
              resellerData={resellerData} 
              onUpdate={loadData}
            />
          </TabsContent>
          
          {/* Tutoriais/Apps Tab */}
          <TabsContent value="tutorials" className="space-y-6">
            <TutorialsAdvanced />
          </TabsContent>

          {/* IPTV Apps Tab */}
          <TabsContent value="iptv-apps" className="space-y-6">
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-4">📺 Gerenciar Aplicativos</h3>
              
              {/* Formulário */}
              <div className="space-y-4 mb-6">
                <div>
                  <label className="block text-sm font-medium mb-1">Nome do App</label>
                  <Input
                    placeholder="Ex: Meu Sistema"
                    value={newApp.name}
                    onChange={(e) => setNewApp({ ...newApp, name: e.target.value })}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">URL de Configuração</label>
                  <Input
                    placeholder="http://seu_aplicativo.com/configuracao"
                    value={newApp.config_url}
                    onChange={(e) => setNewApp({ ...newApp, config_url: e.target.value })}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">Template da URL</label>
                  <Input
                    placeholder="http://seu_aplicativo.com/{usuario}/{senha}"
                    value={newApp.url_template}
                    onChange={(e) => setNewApp({ ...newApp, url_template: e.target.value })}
                  />
                  <p className="text-xs text-gray-500 mt-1">Use {'{'}variavel{'}'} para campos dinâmicos</p>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">Campos (separados por vírgula)</label>
                  <Input
                    placeholder="username, password, codigo"
                    value={newApp.fields.join(', ')}
                    onChange={(e) => setNewApp({ ...newApp, fields: e.target.value.split(',').map(f => f.trim()).filter(Boolean) })}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">Instruções para o Agente</label>
                  <Textarea
                    placeholder="1. Acesse o site...&#10;2. Cole o código...&#10;3. Salve"
                    value={newApp.instructions}
                    onChange={(e) => setNewApp({ ...newApp, instructions: e.target.value })}
                    rows={5}
                  />
                </div>

                <Button onClick={handleCreateIPTVApp} className="w-full">
                  <Plus className="w-4 h-4 mr-2" />
                  Criar Aplicativo
                </Button>
              </div>

              {/* Lista de Apps */}
              <div className="border-t pt-4">
                <h4 className="font-semibold mb-3">Apps Cadastrados ({iptvApps.length})</h4>
                <div className="space-y-2">
                  {iptvApps.map((app) => (
                    <div key={app.id} className="border rounded-lg p-4 flex justify-between items-start">
                      <div className="flex-1">
                        <h5 className="font-medium">{app.name}</h5>
                        <p className="text-xs text-gray-500">{app.type}</p>
                        <p className="text-xs text-gray-600 mt-1">{app.config_url}</p>
                        <p className="text-xs bg-gray-100 p-2 rounded mt-2 font-mono">{app.url_template}</p>
                        <p className="text-xs text-gray-500 mt-1">Campos: {app.fields.join(', ')}</p>
                      </div>
                      <div className="flex gap-2">
                        <Button size="sm" variant="outline" onClick={() => setEditingApp(app)}>
                          <Edit className="w-3 h-3" />
                        </Button>
                        <Button size="sm" variant="outline" onClick={() => handleDeleteIPTVApp(app.id)}>
                          <Trash2 className="w-3 h-3" />
                        </Button>
                      </div>
                    </div>
                  ))}
                  {iptvApps.length === 0 && (
                    <p className="text-gray-400 text-center py-4">Nenhum app cadastrado ainda</p>
                  )}
                </div>
              </div>
            </Card>
          </TabsContent>

          {/* WhatsApp Tab */}
          <TabsContent value="whatsapp" className="space-y-6">
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Phone className="w-6 h-6 text-green-600" />
                📱 Gerenciar WhatsApp
              </h3>
              <p className="text-sm text-slate-600 mb-6">
                Conecte múltiplos números WhatsApp, configure limites anti-banimento e gerencie rotação automática.
              </p>
              <WhatsAppManager />
            </Card>
          </TabsContent>

          {/* WA Site Tab */}
          <TabsContent value="vendas-bot" className="space-y-6">
            <VendasBotManager />
          </TabsContent>

          {/* Payments Tab */}
          <TabsContent value="payments" className="space-y-6">
            <SubscriptionPayments />
          </TabsContent>
        </Tabs>
      </div>

      {/* Modal de Edição de App */}
      <Dialog open={!!editingApp} onOpenChange={(open) => !open && setEditingApp(null)}>
        <DialogContent className="sm:max-w-[600px] max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Editar Aplicativo</DialogTitle>
          </DialogHeader>
          {editingApp && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Nome do App</label>
                <Input
                  value={editingApp.name}
                  onChange={(e) => setEditingApp({ ...editingApp, name: e.target.value })}
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">URL de Configuração</label>
                <Input
                  placeholder="http://seu_aplicativo.com/configuracao"
                  value={editingApp.config_url}
                  onChange={(e) => setEditingApp({ ...editingApp, config_url: e.target.value })}
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Template da URL</label>
                <Input
                  placeholder="http://seu_aplicativo.com/{usuario}/{senha}"
                  value={editingApp.url_template}
                  onChange={(e) => setEditingApp({ ...editingApp, url_template: e.target.value })}
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Campos (separados por vírgula)</label>
                <Input
                  value={editingApp.fields?.join(', ') || ''}
                  onChange={(e) => setEditingApp({ 
                    ...editingApp, 
                    fields: e.target.value.split(',').map(f => f.trim()).filter(Boolean) 
                  })}
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Instruções</label>
                <Textarea
                  value={editingApp.instructions}
                  onChange={(e) => setEditingApp({ ...editingApp, instructions: e.target.value })}
                  rows={5}
                />
              </div>
              <div className="flex gap-2">
                <Button onClick={() => handleUpdateIPTVApp(editingApp.id, editingApp)} className="flex-1">
                  <Save className="w-4 h-4 mr-2" />
                  Salvar Alterações
                </Button>
                <Button variant="outline" onClick={() => setEditingApp(null)}>
                  Cancelar
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Modal de Informações da Revenda Criada */}
      <Dialog open={resellerInfoModal.open} onOpenChange={(open) => setResellerInfoModal({ open, data: null })}>
        <DialogContent className="sm:max-w-[700px] max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-xl">
              <CheckCircle className="w-6 h-6 text-green-600" />
              Revenda Criada com Sucesso!
            </DialogTitle>
          </DialogHeader>
          
          {resellerInfoModal.data && (
            <div className="space-y-6 py-4">
              {/* Informações de Acesso */}
              <div className="bg-blue-50 border-2 border-blue-200 rounded-lg p-4">
                <h3 className="font-bold text-blue-900 mb-3 flex items-center gap-2">
                  <Users className="w-5 h-5" />
                  Informações de Acesso
                </h3>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-blue-700 font-semibold">Nome:</span>
                    <span className="text-blue-900">{resellerInfoModal.data.name}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-blue-700 font-semibold">Email:</span>
                    <span className="text-blue-900">{resellerInfoModal.data.email}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-blue-700 font-semibold">Senha:</span>
                    <span className="text-blue-900 font-mono bg-blue-100 px-2 py-1 rounded">{resellerInfoModal.data.password}</span>
                  </div>
                </div>
              </div>

              {/* Acesso Unificado */}
              <div className="bg-green-50 border-2 border-green-200 rounded-lg p-4">
                <h3 className="font-bold text-green-900 mb-3 flex items-center gap-2">
                  <ExternalLink className="w-5 h-5" />
                  🔗 Link de Acesso Unificado
                </h3>
                <div className="space-y-3">
                  <p className="text-sm text-green-800 font-semibold">
                    A revenda deve usar ESTE link para acessar:
                  </p>
                  <div className="bg-white rounded-lg p-3 border-2 border-green-300">
                    <a 
                      href={`${window.location.origin}/reseller-login`}
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="text-sm text-blue-600 hover:text-blue-800 underline font-mono break-all block"
                    >
                      {window.location.origin}/reseller-login
                    </a>
                  </div>
                  <div className="bg-green-100 rounded-lg p-3">
                    <p className="text-xs text-green-800">
                      <strong>Instruções:</strong>
                    </p>
                    <ol className="text-xs text-green-700 mt-1 ml-4 list-decimal space-y-1">
                      <li>Acesse o link acima</li>
                      <li>Faça login com o email e senha informados</li>
                      <li>No primeiro acesso, será solicitado trocar a senha</li>
                      <li>A revenda terá <strong>24 horas</strong> para configurar domínio próprio</li>
                      <li>Após configurar o domínio, ela deve <strong>avisar você</strong> para ativar</li>
                    </ol>
                  </div>
                </div>
              </div>

              {/* Próximos Passos */}
              <div className="bg-purple-50 border-2 border-purple-200 rounded-lg p-4">
                <h3 className="font-bold text-purple-900 mb-2">🚀 Próximos Passos:</h3>
                <ol className="text-sm text-purple-800 space-y-1 list-decimal ml-5">
                  <li>Acesse o Painel Revenda pelo link acima</li>
                  <li>Faça login com email e senha fornecidos</li>
                  <li>No primeiro acesso, será solicitado a trocar a senha</li>
                  <li>No menu "Domínio", configure seu domínio oficial quando estiver pronto</li>
                </ol>
              </div>

              {/* Botões de Ação */}
              <div className="flex gap-3 justify-end pt-4 border-t">
                <Button 
                  variant="outline" 
                  onClick={() => setResellerInfoModal({ open: false, data: null })}
                >
                  Fechar
                </Button>
                <Button 
                  onClick={handleCopyResellerInfo}
                  className="bg-gradient-to-r from-green-600 to-blue-600 hover:from-green-700 hover:to-blue-700"
                >
                  <Copy className="w-4 h-4 mr-2" />
                  Copiar Tudo
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
      </div>
    </div>
  );
};

const NoticeForm = ({ onSubmit }) => {
  const [kind, setKind] = useState('text');
  const [text, setText] = useState('');
  const [file, setFile] = useState(null);

  const handleSubmit = () => {
    onSubmit(kind, text, file);
    setText('');
    setFile(null);
  };

  return (
    <div className="space-y-4">
      <Select value={kind} onValueChange={setKind}>
        <SelectTrigger>
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="text">Texto</SelectItem>
          <SelectItem value="image">Imagem</SelectItem>
          <SelectItem value="video">Vídeo</SelectItem>
          <SelectItem value="audio">Áudio</SelectItem>
        </SelectContent>
      </Select>

      {kind === 'text' && (
        <Textarea
          placeholder="Mensagem do aviso"
          value={text}
          onChange={(e) => setText(e.target.value)}
          rows={3}
        />
      )}

      {kind !== 'text' && (
        <Input
          type="file"
          accept={kind === 'image' ? 'image/*' : kind === 'video' ? 'video/*' : 'audio/*'}
          onChange={(e) => setFile(e.target.files[0])}
        />
      )}

      <Button data-testid="publish-notice-btn" onClick={handleSubmit} className="bg-purple-600 hover:bg-purple-700">
        <Bell className="w-4 h-4 mr-2" />
        Publicar Aviso
      </Button>
    </div>
  );
};

export default ResellerDashboard;
