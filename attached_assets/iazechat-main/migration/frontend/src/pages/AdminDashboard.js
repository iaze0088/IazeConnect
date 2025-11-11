import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Shield, LogOut, Users, MessageSquare, Settings, Bell, Plus, Trash2, Edit, Bot, Folder, Zap, BookOpen, Save, Monitor, Share2, Copy, CheckCircle, Globe, ExternalLink, Phone, CreditCard, ChevronDown, Eye, Clock } from 'lucide-react';
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
import MercadoPagoConfig from '../components/MercadoPagoConfig';
import VendasBotManager from '../components/VendasBotManager';

const AdminDashboard = () => {
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
  const logoInputRef = useRef(null);
  
  // Replicação de configurações
  const [replicateModal, setReplicateModal] = useState(false);
  const [replicating, setReplicating] = useState(false);

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
  const [newReseller, setNewReseller] = useState({ name: '', email: '', password: '', domain: '', custom_domain: '', parent_id: null });
  const [editingReseller, setEditingReseller] = useState(null);
  const [expandedResellers, setExpandedResellers] = useState(new Set());
  const [transferModal, setTransferModal] = useState({ open: false, reseller: null });
  const [viewMode, setViewMode] = useState('list'); // 'list' or 'tree'
  const [resellerInfoModal, setResellerInfoModal] = useState({ open: false, data: null });

  // Renovação manual
  const [renewalData, setRenewalData] = useState({ reseller_id: '', plan_type: 'basico', months: 1 });
  const [subscriptions, setSubscriptions] = useState([]);
  const [editingSubscription, setEditingSubscription] = useState(null);
  const [resellerSearch, setResellerSearch] = useState('');
  const [showResellerDropdown, setShowResellerDropdown] = useState(false);
  
  // Menu de Perfil
  const [showProfileMenu, setShowProfileMenu] = useState(false);
  const [showChangePassword, setShowChangePassword] = useState(false);
  const [passwordData, setPasswordData] = useState({ currentPassword: '', newPassword: '', confirmPassword: '' });
  const [adminInfo, setAdminInfo] = useState({ name: 'Admin', email: '' });
  
  // Tab ativa
  const [activeTab, setActiveTab] = useState('dashboard');
  
  // Dashboard
  const [dashboardStats, setDashboardStats] = useState({});
  const [agentsOnline, setAgentsOnline] = useState([]);
  const [aiAgentsStatus, setAiAgentsStatus] = useState([]);
  const [dashboardLoading, setDashboardLoading] = useState(true);
  const [importantAlerts, setImportantAlerts] = useState([]);
  
  // Domínio
  const [domainConfig, setDomainConfig] = useState({
    mainDomain: '',
    resellerPath: '/login',
    agentPath: '/atendente/login',
    clientPath: '/'
  });

  // Carregar dados iniciais apenas uma vez
  useEffect(() => {
    loadAdminInfo();
    loadDomainConfig();
  }, []);
  
  // Carregar dados específicos da aba
  useEffect(() => {
    if (activeTab === 'dashboard') {
      loadDashboardData();
      const interval = setInterval(loadDashboardData, 30000);
      return () => clearInterval(interval);
    }
    
    if (activeTab === 'resellers' && resellers.length === 0) {
      loadData();
    }
    
    if (activeTab === 'subscriptions' && subscriptions.length === 0) {
      loadSubscriptions();
    }
  }, [activeTab]);

  const loadDomainConfig = async () => {
    try {
      const { data } = await api.get('/admin/domain-config');
      if (data && data.config) {
        setDomainConfig(data.config);
      }
    } catch (error) {
      console.error('Error loading domain config:', error);
    }
  };

  const loadDashboardData = async () => {
    setDashboardLoading(true);
    try {
      const [stats, agents, aiStatus, alerts] = await Promise.all([
        api.get('/admin/dashboard/stats'),
        api.get('/admin/dashboard/agents-online'),
        api.get('/admin/dashboard/ai-agents-status'),
        api.get('/admin/dashboard/important-alerts')
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

  const saveDomainConfig = async () => {
    try {
      await api.post('/admin/domain-config', domainConfig);
      toast.success('✅ Configuração de domínio salva com sucesso!');
    } catch (error) {
      toast.error('Erro ao salvar configuração');
    }
  };

  const loadAdminInfo = () => {
    const userStr = localStorage.getItem('user');
    if (userStr) {
      const user = JSON.parse(userStr);
      setAdminInfo({ name: user.name || 'Admin', email: user.email || '' });
    }
  };

  // Fechar dropdown ao clicar fora
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (showResellerDropdown && !event.target.closest('.reseller-search-container')) {
        setShowResellerDropdown(false);
      }
      if (showProfileMenu && !event.target.closest('.profile-menu-container')) {
        setShowProfileMenu(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [showResellerDropdown, showProfileMenu]);

  const loadSubscriptions = async () => {
    try {
      const { data } = await api.get('/admin/subscriptions');
      setSubscriptions(data);
    } catch (error) {
      console.error('Error loading subscriptions:', error);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [agentsRes, resellersRes, hierarchyRes, configRes, noticesRes, departmentsRes, iptvAppsRes] = await Promise.all([
        api.get('/agents').catch(() => ({ data: [] })),
        api.get('/resellers').catch(() => ({ data: [] })),
        api.get('/resellers/hierarchy').catch(() => ({ data: { hierarchy: [] } })),
        api.get('/config').catch(() => ({ data: { quick_blocks: [], auto_reply: [], apps: [], pix_key: '', allowed_data: {}, api_integration: {}, ai_agent: {} } })),
        api.get('/notices').catch(() => ({ data: [] })),
        api.get('/ai/departments').catch(() => ({ data: [] })),
        api.get('/iptv-apps').catch(() => ({ data: [] }))
      ]);
      setAgents(Array.isArray(agentsRes.data) ? agentsRes.data : []);
      setResellers(Array.isArray(resellersRes.data) ? resellersRes.data : []);
      setHierarchy(hierarchyRes.data || { hierarchy: [] });
      setConfig(configRes.data || { quick_blocks: [], auto_reply: [], apps: [], pix_key: '', allowed_data: {}, api_integration: {}, ai_agent: {} });
      setNotices(Array.isArray(noticesRes.data) ? noticesRes.data : []);
      setDepartments(Array.isArray(departmentsRes.data) ? departmentsRes.data : []);
      setIptvApps(Array.isArray(iptvAppsRes.data) ? iptvAppsRes.data : []);
    } catch (error) {
      console.error('Error loading data:', error);
      toast.error('Erro ao carregar dados');
    } finally {
      setLoading(false);
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

  const handleReplicateConfig = async () => {
    setReplicating(true);
    try {
      const { data } = await api.post('/admin/replicate-config-to-resellers');
      
      if (data.ok) {
        toast.success(`✅ ${data.message}`, { duration: 5000 });
        setReplicateModal(false);
      } else {
        toast.error('Erro ao replicar configurações');
      }
    } catch (error) {
      console.error('Erro ao replicar:', error);
      toast.error(error.response?.data?.detail || 'Erro ao replicar configurações para revendas');
    } finally {
      setReplicating(false);
    }
  };

  const handleOpenReplicateModal = () => {
    setReplicateModal(true);
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
🔗 *ACESSO UNIFICADO - Use ESTE link:*

🟢 *Login da Revenda (FUNCIONA AGORA):*
${window.location.origin}/revenda/login

OU

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
1. Acesse o Painel Admin pelo link acima
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
        
        setNewReseller({ name: '', email: '', password: '', domain: '', custom_domain: '', parent_id: null });
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
    if (!window.confirm('⚠️ ATENÇÃO: Tem certeza que deseja deletar esta revenda? Esta ação não pode ser desfeita!')) return;
    try {
      await api.delete(`/resellers/${resellerId}`);
      toast.success('✅ Revenda deletada com sucesso!');
      loadData();
      loadSubscriptions();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao deletar revenda');
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

  const handleCreateNotice = async (title, message, recipientType = 'all', targetAudience = 'own') => {
    try {
      await api.post('/notices', { 
        title: title || 'Aviso Importante',
        message: message || '', 
        recipient_type: recipientType,  // all, team, clients
        target_audience: targetAudience,
        target_reseller_ids: [] // TODO: implementar seleção de revendas específicas
      });
      const recipientLabel = recipientType === 'all' ? 'Todos' : recipientType === 'team' ? 'Equipe' : 'Clientes';
      toast.success(`✅ Aviso publicado para: ${recipientLabel}!`);
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

  const handleManualRenewal = async () => {
    if (!renewalData.reseller_id) {
      toast.error('Selecione uma revenda');
      return;
    }

    try {
      await api.post('/admin/subscriptions/manual-renew', renewalData);
      toast.success(`✅ Assinatura renovada por ${renewalData.months} ${renewalData.months === 1 ? 'mês' : 'meses'}!`);
      loadSubscriptions();
      setRenewalData({ reseller_id: '', plan_type: 'basico', months: 1 });
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao renovar assinatura');
    }
  };

  const handleUpdateSubscriptionDate = async (resellerId, newEndDate) => {
    try {
      await api.put(`/admin/subscriptions/${resellerId}/end-date`, { end_date: newEndDate });
      toast.success('✅ Data de vencimento atualizada!');
      loadSubscriptions();
      setEditingSubscription(null);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao atualizar data');
    }
  };

  const handleChangePassword = async () => {
    if (!passwordData.currentPassword || !passwordData.newPassword || !passwordData.confirmPassword) {
      toast.error('Preencha todos os campos');
      return;
    }

    if (passwordData.newPassword !== passwordData.confirmPassword) {
      toast.error('As senhas não coincidem');
      return;
    }

    if (passwordData.newPassword.length < 6) {
      toast.error('A nova senha deve ter pelo menos 6 caracteres');
      return;
    }

    try {
      await api.post('/admin/change-password', {
        current_password: passwordData.currentPassword,
        new_password: passwordData.newPassword
      });
      
      toast.success('✅ Senha alterada com sucesso!');
      setShowChangePassword(false);
      setPasswordData({ currentPassword: '', newPassword: '', confirmPassword: '' });
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao alterar senha');
    }
  };

  const filteredResellers = resellers.filter(r => 
    r.name.toLowerCase().includes(resellerSearch.toLowerCase()) ||
    r.email.toLowerCase().includes(resellerSearch.toLowerCase())
  );

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
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setActiveTab('security')}
                className="text-xs text-slate-600 hover:text-purple-600 hover:bg-purple-50 px-2 py-1 h-auto"
              >
                <Settings className="w-3 h-3 mr-1" />
                Dados Permitidos
              </Button>
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

            <Button 
              onClick={handleOpenReplicateModal} 
              className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white"
              size="sm"
            >
              <Share2 className="w-4 h-4 mr-2" />
              Aplicar para Revendas
            </Button>
            
            {/* Menu de Perfil */}
            <div className="relative profile-menu-container">
              <Button 
                onClick={() => setShowProfileMenu(!showProfileMenu)}
                variant="outline" 
                size="sm"
                className="gap-2"
              >
                <div className="w-6 h-6 bg-purple-600 rounded-full flex items-center justify-center text-white text-xs font-bold">
                  {adminInfo.name.charAt(0).toUpperCase()}
                </div>
                {adminInfo.name}
              </Button>
              
              {showProfileMenu && (
                <div className="absolute right-0 mt-2 w-64 bg-white border rounded-lg shadow-lg py-2 z-50">
                  {/* Informações do perfil */}
                  <div className="px-4 py-3 border-b">
                    <p className="text-sm font-semibold text-slate-900">{adminInfo.name}</p>
                    <p className="text-xs text-slate-500">{adminInfo.email || 'admin@sistema.com'}</p>
                  </div>
                  
                  {/* Opções */}
                  <button
                    onClick={() => {
                      setShowProfileMenu(false);
                      setShowChangePassword(true);
                    }}
                    className="w-full px-4 py-2 text-left text-sm hover:bg-slate-100 flex items-center gap-2"
                  >
                    <Settings className="w-4 h-4" />
                    Trocar Senha
                  </button>
                  
                  <button
                    onClick={() => {
                      setShowProfileMenu(false);
                      handleLogout();
                    }}
                    className="w-full px-4 py-2 text-left text-sm hover:bg-slate-100 flex items-center gap-2 text-red-600"
                    data-testid="logout-btn"
                  >
                    <LogOut className="w-4 h-4" />
                    Sair
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      <div className="flex-1 overflow-y-auto">
        <div className="max-w-7xl mx-auto px-4 py-8">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          {/* Menu reorganizado: 10 itens por linha com destaque verde-azulado */}
          <TabsList className="grid grid-cols-5 md:grid-cols-10 gap-2 bg-transparent h-auto p-0">
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
              value="dominio" 
              data-testid="tab-dominio"
              className="data-[state=active]:bg-teal-500 data-[state=active]:text-white hover:bg-teal-50"
            >
              <Globe className="w-4 h-4 mr-1" />
              Domínio
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
            
            {/* Segunda linha - 6 itens */}
            <TabsTrigger 
              value="auto-responder" 
              data-testid="tab-auto-responder"
              className="data-[state=active]:bg-teal-500 data-[state=active]:text-white hover:bg-teal-50"
            >
              <Zap className="w-4 h-4 mr-1" />
              Auto-Responder
            </TabsTrigger>
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
              value="whatsapp-plans" 
              data-testid="tab-whatsapp-plans"
              className="data-[state=active]:bg-teal-500 data-[state=active]:text-white hover:bg-teal-50"
            >
              <Phone className="w-4 h-4 mr-1" />
              Planos WhatsApp
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
              value="mercado-pago" 
              data-testid="tab-mercado-pago"
              className="data-[state=active]:bg-teal-500 data-[state=active]:text-white hover:bg-teal-50"
            >
              <CreditCard className="w-4 h-4 mr-1" />
              Mercado Pago
            </TabsTrigger>
            <TabsTrigger 
              value="vendas-bot" 
              data-testid="tab-vendas-bot"
              className="data-[state=active]:bg-teal-500 data-[state=active]:text-white hover:bg-teal-50"
            >
              <MessageSquare className="w-4 h-4 mr-1" />
              WA Site
            </TabsTrigger>
          </TabsList>

          {/* Dashboard Tab */}
          <TabsContent value="dashboard" className="space-y-6">
            {dashboardLoading ? (
              <div className="flex items-center justify-center h-64">
                <div className="text-center">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto mb-4"></div>
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
                      <Users className="w-5 h-5 text-purple-600" />
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
                              <div className="w-10 h-10 bg-purple-600 rounded-full flex items-center justify-center text-white font-semibold">
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
                      <Bot className="w-5 h-5 text-purple-600" />
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
                            <div className={`w-10 h-10 ${agent.status === 'active' ? 'bg-purple-600' : 'bg-slate-400'} rounded-full flex items-center justify-center text-white`}>
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

          {/* DOMINIO Tab */}
          <TabsContent value="dominio" className="space-y-6">
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Globe className="w-5 h-5 text-blue-600" />
                🌐 Configuração de Domínio
              </h3>
              
              <div className="grid md:grid-cols-2 gap-6">
                {/* Coluna 1: Passo a Passo Cloudflare */}
                <div className="space-y-4">
                  <div className="bg-blue-50 border-2 border-blue-200 rounded-lg p-4">
                    <h4 className="font-semibold text-blue-900 mb-3 flex items-center gap-2">
                      ☁️ Passo a Passo - Cloudflare
                    </h4>
                    <ol className="space-y-3 text-sm text-slate-700">
                      <li className="flex items-start gap-2">
                        <span className="font-bold text-blue-600">1.</span>
                        <div>
                          <strong>Acesse a Cloudflare:</strong>
                          <br />
                          <a href="https://dash.cloudflare.com" target="_blank" rel="noopener noreferrer" className="text-blue-600 underline">
                            https://dash.cloudflare.com
                          </a>
                        </div>
                      </li>
                      
                      <li className="flex items-start gap-2">
                        <span className="font-bold text-blue-600">2.</span>
                        <div>
                          <strong>Selecione seu domínio</strong>
                          <br />
                          Clique no domínio que deseja configurar
                        </div>
                      </li>
                      
                      <li className="flex items-start gap-2">
                        <span className="font-bold text-blue-600">3.</span>
                        <div>
                          <strong>Vá em "DNS" no menu lateral</strong>
                        </div>
                      </li>
                      
                      <li className="flex items-start gap-2">
                        <span className="font-bold text-blue-600">4.</span>
                        <div>
                          <strong>Clique em "Add record"</strong>
                        </div>
                      </li>
                      
                      <li className="flex items-start gap-2">
                        <span className="font-bold text-blue-600">5.</span>
                        <div>
                          <strong>Configure o registro:</strong>
                          <ul className="mt-2 space-y-1 ml-4 text-xs">
                            <li>• <strong>Type:</strong> A</li>
                            <li>• <strong>Name:</strong> @ (ou seu subdomínio)</li>
                            <li>• <strong>IPv4 address:</strong> {'{'}IP do servidor{'}'}</li>
                            <li>• <strong>Proxy status:</strong> ✅ Proxied (laranja)</li>
                          </ul>
                        </div>
                      </li>
                      
                      <li className="flex items-start gap-2">
                        <span className="font-bold text-blue-600">6.</span>
                        <div>
                          <strong>Clique em "Save"</strong>
                        </div>
                      </li>
                      
                      <li className="flex items-start gap-2">
                        <span className="font-bold text-blue-600">7.</span>
                        <div>
                          <strong>Aguarde propagação (até 48h)</strong>
                          <br />
                          <span className="text-xs text-slate-500">Normalmente leva apenas alguns minutos</span>
                        </div>
                      </li>
                    </ol>
                  </div>
                </div>

                {/* Coluna 2: Configurar Links */}
                <div className="space-y-4">
                  <div className="bg-purple-50 border-2 border-purple-200 rounded-lg p-4">
                    <h4 className="font-semibold text-purple-900 mb-3">
                      🔗 Configurar Domínio Principal
                    </h4>
                    
                    <div className="space-y-3">
                      <div>
                        <label className="block text-sm font-medium mb-1">
                          Domínio Principal
                        </label>
                        <Input
                          placeholder="Ex: meudominio.com"
                          value={domainConfig.mainDomain}
                          onChange={(e) => setDomainConfig({ ...domainConfig, mainDomain: e.target.value })}
                        />
                        <p className="text-xs text-slate-500 mt-1">
                          Digite apenas o domínio, sem http:// ou https://
                        </p>
                      </div>
                      
                      <Button onClick={saveDomainConfig} className="w-full bg-purple-600 hover:bg-purple-700">
                        <Save className="w-4 h-4 mr-2" />
                        Salvar Configuração
                      </Button>
                    </div>
                  </div>

                  {/* Links Gerados */}
                  {domainConfig.mainDomain && (
                    <div className="bg-green-50 border-2 border-green-200 rounded-lg p-4">
                      <h4 className="font-semibold text-green-900 mb-3">
                        ✅ Links Gerados
                      </h4>
                      
                      <div className="space-y-3">
                        {/* Painel de Revenda */}
                        <div>
                          <label className="block text-xs font-medium text-green-800 mb-1">
                            📊 Painel de Revenda:
                          </label>
                          <div className="flex gap-2">
                            <Input
                              value={`https://${domainConfig.mainDomain}${domainConfig.resellerPath}`}
                              readOnly
                              className="text-sm"
                            />
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => {
                                navigator.clipboard.writeText(`https://${domainConfig.mainDomain}${domainConfig.resellerPath}`);
                                toast.success('Link copiado!');
                              }}
                            >
                              <Copy className="w-4 h-4" />
                            </Button>
                          </div>
                        </div>

                        {/* Painel de Atendente */}
                        <div>
                          <label className="block text-xs font-medium text-green-800 mb-1">
                            👤 Painel de Atendente:
                          </label>
                          <div className="flex gap-2">
                            <Input
                              value={`https://${domainConfig.mainDomain}${domainConfig.agentPath}`}
                              readOnly
                              className="text-sm"
                            />
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => {
                                navigator.clipboard.writeText(`https://${domainConfig.mainDomain}${domainConfig.agentPath}`);
                                toast.success('Link copiado!');
                              }}
                            >
                              <Copy className="w-4 h-4" />
                            </Button>
                          </div>
                        </div>

                        {/* Painel do Cliente */}
                        <div>
                          <label className="block text-xs font-medium text-green-800 mb-1">
                            🌟 Painel do Cliente:
                          </label>
                          <div className="flex gap-2">
                            <Input
                              value={`https://${domainConfig.mainDomain}${domainConfig.clientPath}`}
                              readOnly
                              className="text-sm"
                            />
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => {
                                navigator.clipboard.writeText(`https://${domainConfig.mainDomain}${domainConfig.clientPath}`);
                                toast.success('Link copiado!');
                              }}
                            >
                              <Copy className="w-4 h-4" />
                            </Button>
                          </div>
                        </div>
                      </div>

                      <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded">
                        <p className="text-xs text-yellow-800">
                          <strong>⚠️ Importante:</strong>
                          <br />
                          • Revenda e Atendente sempre usam <strong>/login</strong>
                          <br />
                          • Cliente acessa direto sem /login
                        </p>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </Card>
          </TabsContent>

          {/* Resellers Tab */}
          <TabsContent value="resellers" className="space-y-6">
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-4">Nova Revenda</h3>
              <p className="text-sm text-slate-600 mb-4">Crie sub-revendas com isolamento completo de dados</p>
              <div className="grid md:grid-cols-2 gap-4 mb-4">
                <Input
                  placeholder="Nome da Revenda (ex: lucasrv)"
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
              
              {/* Preview do subdomínio que será gerado */}
              {newReseller.name && (
                <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded">
                  <p className="text-sm font-medium text-blue-900">🌐 Subdomínio que será criado:</p>
                  <p className="text-lg font-mono text-blue-700 mt-1">
                    {newReseller.name.toLowerCase().replace(/[^a-z0-9]/g, '')}.suporte.help
                  </p>
                  <p className="text-xs text-blue-600 mt-2">
                    📋 Clientes da revenda acessarão: https://{newReseller.name.toLowerCase().replace(/[^a-z0-9]/g, '')}.suporte.help/chat
                  </p>
                  <p className="text-xs text-amber-600 mt-1">
                    ⚠️ Após criar, configure DNS tipo A apontando para o IP do servidor
                  </p>
                </div>
              )}
              
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

              {/* Botão Replicar Configurações */}
              <div className="bg-gradient-to-r from-amber-50 to-orange-50 border-2 border-amber-200 rounded-lg p-4 mb-6">
                <h4 className="font-semibold text-amber-900 mb-2">⚡ Replicar para Todas as Revendas</h4>
                <p className="text-sm text-amber-700 mb-3">
                  Propaga todas as configurações desta página (PIX, Dados Permitidos) para TODAS as revendas do sistema.
                </p>
                <Button 
                  onClick={handleReplicateConfig} 
                  className="bg-amber-600 hover:bg-amber-700 w-full"
                  variant="default"
                >
                  🔄 Replicar Configurações
                </Button>
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
                
                {/* Botão Replicar Configurações */}
                <div className="bg-gradient-to-r from-amber-50 to-orange-50 border-2 border-amber-200 rounded-lg p-4 mt-4">
                  <h4 className="font-semibold text-amber-900 mb-2">⚡ Replicar para Todas as Revendas</h4>
                  <p className="text-sm text-amber-700 mb-3">
                    Propaga as configurações de API para TODAS as revendas do sistema.
                  </p>
                  <Button 
                    onClick={handleReplicateConfig} 
                    className="bg-amber-600 hover:bg-amber-700 w-full"
                    variant="default"
                  >
                    🔄 Replicar Configurações
                  </Button>
                </div>
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
            {/* Formulário de Avisos */}
            <Card className="p-6">
              <NoticeForm onSubmit={handleCreateNotice} isAdmin={true} />
            </Card>

            {/* Lista de Avisos */}
            {notices.map((notice) => (
              <Card key={notice.id} className="p-4">
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <h3 className="font-semibold text-lg">{notice.title || 'Aviso'}</h3>
                      <span className="text-xs px-2 py-1 rounded-full bg-purple-100 text-purple-700">
                        {notice.recipient_type === 'all' ? '🌍 Todos' : notice.recipient_type === 'team' ? '👔 Equipe' : '👤 Clientes'}
                      </span>
                    </div>
                    <p className="text-slate-700 whitespace-pre-wrap">{notice.message}</p>
                    <p className="text-xs text-slate-500 mt-2">
                      {new Date(notice.created_at).toLocaleString('pt-BR')}
                    </p>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="text-red-600 hover:text-red-700 hover:bg-red-50"
                    onClick={() => handleDeleteNotice(notice.id)}
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              </Card>
            ))}
          </TabsContent>
          
          {/* Auto-Responder Tab */}
          <TabsContent value="auto-responder" className="space-y-6">
            <AutoResponderAdvanced />
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
                  Criar App IPTV
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

          {/* WhatsApp Plans Tab */}
          <TabsContent value="whatsapp-plans" className="space-y-6">
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Phone className="w-6 h-6 text-green-600" />
                📱 Gerenciar Planos WhatsApp
              </h3>
              <p className="text-sm text-slate-600 mb-6">
                Configure os planos WhatsApp para cada revenda. Controle quantos números cada revenda pode conectar.
              </p>

              {/* Tabela de Planos Disponíveis */}
              <div className="mb-8">
                <h4 className="font-semibold mb-4">Planos Disponíveis:</h4>
                <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
                  <Card className="p-4 border-2 border-blue-200 bg-blue-50">
                    <div className="text-center">
                      <p className="text-lg font-bold text-blue-900">Básico</p>
                      <p className="text-3xl font-bold text-blue-600 my-2">1</p>
                      <p className="text-sm text-blue-700">número</p>
                      <p className="text-lg font-bold text-blue-900 mt-2">R$ 49/mês</p>
                    </div>
                  </Card>
                  
                  <Card className="p-4 border-2 border-purple-200 bg-purple-50">
                    <div className="text-center">
                      <p className="text-lg font-bold text-purple-900">Plus</p>
                      <p className="text-3xl font-bold text-purple-600 my-2">2</p>
                      <p className="text-sm text-purple-700">números</p>
                      <p className="text-lg font-bold text-purple-900 mt-2">R$ 89/mês</p>
                    </div>
                  </Card>
                  
                  <Card className="p-4 border-2 border-green-200 bg-green-50">
                    <div className="text-center">
                      <p className="text-lg font-bold text-green-900">Pro</p>
                      <p className="text-3xl font-bold text-green-600 my-2">3</p>
                      <p className="text-sm text-green-700">números</p>
                      <p className="text-lg font-bold text-green-900 mt-2">R$ 129/mês</p>
                    </div>
                  </Card>
                  
                  <Card className="p-4 border-2 border-orange-200 bg-orange-50">
                    <div className="text-center">
                      <p className="text-lg font-bold text-orange-900">Premium</p>
                      <p className="text-3xl font-bold text-orange-600 my-2">5</p>
                      <p className="text-sm text-orange-700">números</p>
                      <p className="text-lg font-bold text-orange-900 mt-2">R$ 199/mês</p>
                    </div>
                  </Card>
                  
                  <Card className="p-4 border-2 border-red-200 bg-red-50">
                    <div className="text-center">
                      <p className="text-lg font-bold text-red-900">Enterprise</p>
                      <p className="text-3xl font-bold text-red-600 my-2">∞</p>
                      <p className="text-sm text-red-700">ilimitado</p>
                      <p className="text-lg font-bold text-red-900 mt-2">R$ 499/mês</p>
                    </div>
                  </Card>
                </div>
              </div>

              {/* Aviso de Configuração */}
              <Card className="mb-6 bg-yellow-50 border-2 border-yellow-300 p-4">
                <div className="flex items-start gap-3">
                  <div className="text-3xl">⚠️</div>
                  <div>
                    <h4 className="font-semibold text-yellow-900 mb-1">
                      Importante: Configure o Mercado Pago primeiro!
                    </h4>
                    <p className="text-sm text-yellow-800 mb-2">
                      Antes que as revendas possam fazer pagamentos, você precisa configurar o Mercado Pago na aba 
                      <strong> "Mercado Pago"</strong>.
                    </p>
                    <p className="text-xs text-yellow-700">
                      Sem a configuração do Mercado Pago, as revendas verão uma mensagem de erro ao tentar gerar QR Code de pagamento.
                    </p>
                  </div>
                </div>
              </Card>

              {/* Renovação Manual */}
              <Card className="mb-8 bg-gradient-to-r from-emerald-50 to-teal-50 border-2 border-emerald-200 p-6">
                <h4 className="font-semibold mb-4 text-lg flex items-center gap-2">
                  <CreditCard className="w-5 h-5 text-emerald-600" />
                  💳 Renovação Manual de Assinatura
                </h4>
                <p className="text-sm text-slate-600 mb-4">Renove manualmente a assinatura de qualquer revenda</p>
                
                <div className="grid md:grid-cols-4 gap-4 mb-4">
                  <div className="relative reseller-search-container">
                    <label className="block text-sm font-medium mb-1">Revenda</label>
                    <div className="relative">
                      <Input
                        placeholder="🔍 Pesquisar revenda..."
                        value={resellerSearch}
                        onChange={(e) => {
                          setResellerSearch(e.target.value);
                          setShowResellerDropdown(true);
                        }}
                        onFocus={() => setShowResellerDropdown(true)}
                        className="w-full pr-10"
                      />
                      <button
                        onClick={() => {
                          setShowResellerDropdown(!showResellerDropdown);
                          if (!showResellerDropdown) {
                            setResellerSearch(''); // Limpar busca ao abrir menu completo
                          }
                        }}
                        className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-600 hover:text-slate-900"
                      >
                        <ChevronDown className={`w-5 h-5 transition-transform ${showResellerDropdown ? 'rotate-180' : ''}`} />
                      </button>
                    </div>
                    {showResellerDropdown && (
                      <div className="absolute z-50 w-full mt-1 bg-white border rounded-lg shadow-lg max-h-60 overflow-y-auto">
                        {(resellerSearch ? filteredResellers : resellers).length > 0 ? (
                          (resellerSearch ? filteredResellers : resellers).map((reseller) => (
                            <div
                              key={reseller.id}
                              className="px-4 py-2 hover:bg-slate-100 cursor-pointer flex items-center justify-between"
                              onClick={() => {
                                setRenewalData({ ...renewalData, reseller_id: reseller.id });
                                setResellerSearch(`${reseller.name} (${reseller.email})`);
                                setShowResellerDropdown(false);
                              }}
                            >
                              <div>
                                <p className="font-medium text-sm">{reseller.name}</p>
                                <p className="text-xs text-slate-500">{reseller.email}</p>
                              </div>
                              <Button
                                size="sm"
                                variant="ghost"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  setShowResellerDropdown(false);
                                  handleDeleteReseller(reseller.id);
                                }}
                                className="text-red-600 hover:text-red-700 hover:bg-red-50"
                              >
                                <Trash2 className="w-4 h-4" />
                              </Button>
                            </div>
                          ))
                        ) : (
                          <div className="px-4 py-3 text-sm text-slate-500 text-center">
                            Nenhuma revenda encontrada
                          </div>
                        )}
                      </div>
                    )}
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-1">Plano</label>
                    <Select value={renewalData.plan_type} onValueChange={(value) => setRenewalData({ ...renewalData, plan_type: value })}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="basico">Básico - R$ 49/mês</SelectItem>
                        <SelectItem value="plus">Plus - R$ 89/mês</SelectItem>
                        <SelectItem value="pro">Pro - R$ 129/mês</SelectItem>
                        <SelectItem value="premium">Premium - R$ 199/mês</SelectItem>
                        <SelectItem value="enterprise">Enterprise - R$ 499/mês</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-1">Meses</label>
                    <Select value={renewalData.months.toString()} onValueChange={(value) => setRenewalData({ ...renewalData, months: parseInt(value) })}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="1">1 mês</SelectItem>
                        <SelectItem value="3">3 meses</SelectItem>
                        <SelectItem value="6">6 meses</SelectItem>
                        <SelectItem value="12">12 meses (1 ano)</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="flex items-end">
                    <Button onClick={handleManualRenewal} className="w-full bg-emerald-600 hover:bg-emerald-700">
                      ✅ Renovar Agora
                    </Button>
                  </div>
                </div>
              </Card>

              {/* Lista de Assinaturas Ativas */}
              <Card className="mb-8 p-6">
                <h4 className="font-semibold mb-4 text-lg">📋 Assinaturas Ativas</h4>
                <div className="space-y-3">
                  {subscriptions.map((sub) => (
                    <Card key={sub.id} className="p-4 bg-slate-50">
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <p className="font-medium">{sub.reseller_name || 'Nome não disponível'}</p>
                          <p className="text-xs text-slate-600">{sub.reseller_email}</p>
                          <p className="text-xs text-slate-500 mt-1">
                            Plano: <span className="font-semibold text-slate-700">{sub.plan_type?.toUpperCase()}</span>
                          </p>
                        </div>
                        <div className="text-right">
                          {editingSubscription === sub.reseller_id ? (
                            <div className="flex gap-2">
                              <Input
                                type="datetime-local"
                                defaultValue={sub.current_period_end?.split('.')[0]}
                                onChange={(e) => {
                                  const newDate = e.target.value + ':00.000Z';
                                  handleUpdateSubscriptionDate(sub.reseller_id, newDate);
                                }}
                                className="text-xs"
                              />
                              <Button size="sm" variant="outline" onClick={() => setEditingSubscription(null)}>
                                Cancelar
                              </Button>
                            </div>
                          ) : (
                            <>
                              <p className="text-xs text-slate-500">Vencimento:</p>
                              <p className="font-semibold text-sm">
                                {new Date(sub.current_period_end).toLocaleDateString('pt-BR')}
                              </p>
                              <Button 
                                size="sm" 
                                variant="outline" 
                                onClick={() => setEditingSubscription(sub.reseller_id)}
                                className="mt-2"
                              >
                                <Edit className="w-3 h-3 mr-1" />
                                Editar Data
                              </Button>
                            </>
                          )}
                        </div>
                      </div>
                    </Card>
                  ))}
                  {subscriptions.length === 0 && (
                    <p className="text-center text-slate-400 py-4">Nenhuma assinatura encontrada</p>
                  )}
                </div>
              </Card>

              {/* Lista de Revendas com Planos */}
              <div>
                <h4 className="font-semibold mb-4">Configurar Plano por Revenda:</h4>
                <div className="space-y-4">
                  {resellers.map((reseller) => (
                    <Card key={reseller.id} className="p-4">
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <p className="font-semibold">{reseller.name}</p>
                          <p className="text-sm text-slate-600">{reseller.email}</p>
                        </div>
                        
                        <div className="flex items-center gap-4">
                          <div>
                            <p className="text-xs text-slate-600">Plano WhatsApp:</p>
                            <select
                              value={reseller.whatsapp_plan || 'basico'}
                              onChange={async (e) => {
                                try {
                                  await api.put(`/whatsapp/config/plan/${reseller.id}?plan=${e.target.value}`);
                                  alert('✅ Plano atualizado com sucesso!');
                                  // Atualizar apenas o plano da revenda no estado local
                                  setResellers(resellers.map(r => 
                                    r.id === reseller.id ? { ...r, whatsapp_plan: e.target.value } : r
                                  ));
                                } catch (error) {
                                  alert('❌ Erro ao atualizar plano: ' + (error.response?.data?.detail || error.message));
                                }
                              }}
                              className="border rounded px-3 py-1 text-sm font-semibold"
                            >
                              <option value="basico">Básico (1 - R$ 49)</option>
                              <option value="plus">Plus (2 - R$ 89)</option>
                              <option value="pro">Pro (3 - R$ 129)</option>
                              <option value="premium">Premium (5 - R$ 199)</option>
                              <option value="enterprise">Enterprise (∞ - R$ 499)</option>
                            </select>
                          </div>
                          
                          <Button
                            onClick={() => window.open(`https://${reseller.test_domain}/reseller-login`, '_blank')}
                            variant="outline"
                            size="sm"
                          >
                            <ExternalLink className="w-4 h-4 mr-1" />
                            Acessar Painel
                          </Button>
                        </div>
                      </div>
                    </Card>
                  ))}
                </div>
              </div>

              {/* Instruções */}
              <Card className="p-4 bg-blue-50 border-blue-200 mt-6">
                <h4 className="font-semibold text-blue-900 mb-2">ℹ️ Como Funciona:</h4>
                <ul className="text-sm text-blue-800 space-y-1 list-disc list-inside">
                  <li>Selecione o plano WhatsApp para cada revenda</li>
                  <li>O plano limita quantos números a revenda pode conectar</li>
                  <li>Revenda gerencia as conexões no próprio painel (Aba WhatsApp)</li>
                  <li>Você pode ver as estatísticas de uso de cada revenda</li>
                  <li>Mudanças de plano são aplicadas imediatamente</li>
                </ul>
              </Card>
            </Card>
          </TabsContent>

          {/* WhatsApp Tab - Admin gerencia suas próprias conexões */}
          <TabsContent value="whatsapp" className="space-y-6">
            <Card className="p-6 bg-green-50 border-green-200 mb-4">
              <h3 className="text-lg font-semibold mb-2 flex items-center gap-2 text-green-900">
                <Phone className="w-6 h-6 text-green-600" />
                📱 WhatsApp - Conexões do Admin
              </h3>
              <p className="text-sm text-green-800">
                Conecte números WhatsApp para seus atendentes. Os tickets chegarão para os atendentes selecionados nos departamentos.
              </p>
            </Card>
            
            <WhatsAppManager />
          </TabsContent>

          {/* Mercado Pago Config Tab */}
          <TabsContent value="mercado-pago" className="space-y-6">
            <MercadoPagoConfig />
          </TabsContent>

          {/* WA Site Tab */}
          <TabsContent value="vendas-bot" className="space-y-6">
            <VendasBotManager />
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
                <label className="block text-sm font-medium mb-1">Tipo</label>
                <Select value={editingApp.type} onValueChange={(value) => setEditingApp({ ...editingApp, type: value })}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="SSIPTV">SS-IPTV</SelectItem>
                    <SelectItem value="SMARTONE">SmartOne IPTV</SelectItem>
                    <SelectItem value="DUPLEXPLAY">Duplex Play</SelectItem>
                    <SelectItem value="IBOPLAYER">IBO Player</SelectItem>
                    <SelectItem value="SMARTIPTV">Smart IPTV</SelectItem>
                    <SelectItem value="BAYTV">Bay TV</SelectItem>
                    <SelectItem value="DUPLECAST">Duplecast</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">URL de Configuração</label>
                <Input
                  value={editingApp.config_url}
                  onChange={(e) => setEditingApp({ ...editingApp, config_url: e.target.value })}
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Template da URL</label>
                <Input
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

      {/* Modal de Confirmação de Replicação */}
      <Dialog open={replicateModal} onOpenChange={setReplicateModal}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-xl">
              <Share2 className="w-6 h-6 text-purple-600" />
              Aplicar Configurações para Todas as Revendas
            </DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <p className="text-sm text-yellow-800 font-semibold mb-2">⚠️ ATENÇÃO:</p>
              <p className="text-sm text-yellow-700">
                Esta ação irá <strong>replicar TODAS as configurações de sistema</strong> do painel admin principal para <strong>TODAS as revendas</strong>.
              </p>
            </div>
            
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <p className="text-sm text-blue-900 font-semibold mb-2">✅ Será replicado:</p>
              <ul className="text-sm text-blue-800 space-y-1 ml-4 list-disc">
                <li>Logo do suporte</li>
                <li>Configurações de IA</li>
                <li>Auto-respostas</li>
                <li>Tutoriais</li>
                <li>Apps IPTV (templates)</li>
                <li>Configurações gerais do sistema</li>
              </ul>
            </div>
            
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <p className="text-sm text-green-900 font-semibold mb-2">❌ NÃO será replicado:</p>
              <ul className="text-sm text-green-800 space-y-1 ml-4 list-disc">
                <li>Agentes criados manualmente</li>
                <li>Atendentes criados</li>
                <li>Departamentos criados</li>
                <li>Clientes/Tickets das revendas</li>
                <li>Domínios das revendas</li>
              </ul>
            </div>
            
            <div className="bg-red-50 border-2 border-red-300 rounded-lg p-4">
              <p className="text-sm text-red-900 font-bold text-center">
                ⚠️ Esta ação IRÁ SOBRESCREVER as configurações atuais de todas as revendas!
              </p>
            </div>
          </div>
          
          <div className="flex gap-3 justify-end pt-4">
            <Button 
              variant="outline" 
              onClick={() => setReplicateModal(false)}
              disabled={replicating}
            >
              Cancelar
            </Button>
            <Button 
              onClick={handleReplicateConfig}
              disabled={replicating}
              className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700"
            >
              {replicating ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                  Replicando...
                </>
              ) : (
                <>
                  <Share2 className="w-4 h-4 mr-2" />
                  Confirmar e Aplicar
                </>
              )}
            </Button>
          </div>
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
                  <li>Acesse o Painel Admin pelo link acima</li>
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

const NoticeForm = ({ onSubmit, isAdmin = false }) => {
  const [title, setTitle] = useState('');
  const [message, setMessage] = useState('');
  const [recipientType, setRecipientType] = useState('all'); // 'all', 'team', 'clients'
  const [targetAudience, setTargetAudience] = useState('own'); // 'own', 'all', 'specific'

  const handleSubmit = () => {
    onSubmit(title, message, recipientType, targetAudience);
    setTitle('');
    setMessage('');
    setRecipientType('all');
    setTargetAudience('own');
  };

  return (
    <div className="space-y-4">
      {/* Título do Aviso */}
      <div>
        <label className="block text-sm font-medium mb-1">Título do Aviso</label>
        <Input
          placeholder="Ex: Manutenção Programada"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
        />
      </div>

      {/* Destinatários */}
      <div>
        <label className="block text-sm font-medium mb-1">👥 Enviar Para</label>
        <Select value={recipientType} onValueChange={setRecipientType}>
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">🌍 Todos (Equipe + Clientes)</SelectItem>
            <SelectItem value="team">👔 Apenas Equipe (Atendentes)</SelectItem>
            <SelectItem value="clients">👤 Apenas Clientes</SelectItem>
          </SelectContent>
        </Select>
        <p className="text-xs text-slate-500 mt-1">
          {recipientType === 'all' && '📢 Aviso visível para toda a equipe e clientes'}
          {recipientType === 'team' && '👥 Aviso visível apenas para atendentes'}
          {recipientType === 'clients' && '💬 Aviso visível apenas para clientes'}
        </p>
      </div>

      {/* Público-Alvo (apenas para Admin) */}
      {isAdmin && (
        <div>
          <label className="block text-sm font-medium mb-1">🎯 Público-Alvo</label>
          <Select value={targetAudience} onValueChange={setTargetAudience}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="own">🔒 Apenas Admin (restrito)</SelectItem>
              <SelectItem value="all">🌍 Global (todas as revendas)</SelectItem>
              <SelectItem value="specific">🎯 Revendas Específicas</SelectItem>
            </SelectContent>
          </Select>
          <p className="text-xs text-slate-500 mt-1">
            {targetAudience === 'own' && 'Visível apenas no domínio master (suporte.help)'}
            {targetAudience === 'all' && 'Visível em todos os domínios (admin, revendas, clientes)'}
            {targetAudience === 'specific' && 'Você poderá escolher revendas específicas (em breve)'}
          </p>
        </div>
      )}

      {/* Mensagem do Aviso */}
      <div>
        <label className="block text-sm font-medium mb-1">Mensagem</label>
        <Textarea
          placeholder="Digite a mensagem do aviso..."
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          rows={4}
        />
      </div>

      <Button data-testid="publish-notice-btn" onClick={handleSubmit} className="w-full bg-purple-600 hover:bg-purple-700">
        <Bell className="w-4 h-4 mr-2" />
        Publicar Aviso
      </Button>
    </div>
  );
};

export default AdminDashboard;
