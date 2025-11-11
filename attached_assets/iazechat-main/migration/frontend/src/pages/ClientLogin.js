import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { MessageCircle, Phone, Hash } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card } from '@/components/ui/card';
import { toast } from 'sonner';
import api from '../lib/api';
import { setAuth } from '../lib/auth';

const ClientLogin = () => {
  const navigate = useNavigate();
  const [whatsapp, setWhatsapp] = useState('');
  const [pin, setPin] = useState('');
  const [loading, setLoading] = useState(false);
  const [autoLoggingIn, setAutoLoggingIn] = useState(true);

  // Auto-login ao carregar a página se houver credenciais salvas
  useEffect(() => {
    const attemptAutoLogin = async () => {
      try {
        console.log('🔍 [AUTO-LOGIN] Iniciando verificação...');
        console.log('🔍 [AUTO-LOGIN] URL atual:', window.location.href);
        
        const savedCredentials = localStorage.getItem('client_credentials');
        console.log('📦 [AUTO-LOGIN] Credenciais no localStorage:', savedCredentials);
        
        if (!savedCredentials) {
          console.log('⚠️ [AUTO-LOGIN] Nenhuma credencial salva encontrada');
          setAutoLoggingIn(false);
          return;
        }
        
        const { whatsapp: savedWhatsapp, pin: savedPin } = JSON.parse(savedCredentials);
        console.log('🔄 [AUTO-LOGIN] Tentando login automático com:', { 
          whatsapp: savedWhatsapp, 
          pin: savedPin 
        });
        
        const { data } = await api.post('/auth/client/login', { 
          whatsapp: savedWhatsapp, 
          pin: savedPin 
        });
        
        console.log('✅ [AUTO-LOGIN] Login bem-sucedido! Dados:', data);
        
        setAuth(data.token, data.user_type, data.user_data);
        console.log('✅ [AUTO-LOGIN] Token salvo, navegando para /chat...');
        
        // Pequeno delay antes de navegar
        await new Promise(resolve => setTimeout(resolve, 100));
        
        navigate('/chat', { replace: true });
        console.log('✅ [AUTO-LOGIN] Navegação completa!');
      } catch (error) {
        console.error('❌ [AUTO-LOGIN] Falhou:', error);
        console.error('❌ [AUTO-LOGIN] Detalhes:', error.response?.data);
        
        // Limpar credenciais inválidas
        localStorage.removeItem('client_credentials');
        setAutoLoggingIn(false);
        
        // Só mostrar erro se não for 404 (credenciais inválidas)
        if (error.response?.status !== 404) {
          toast.error('Sessão expirada. Faça login novamente.');
        }
      }
    };

    attemptAutoLogin();
  }, [navigate]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      console.log('📝 Fazendo login com:', { whatsapp, pin });
      const { data } = await api.post('/auth/client/login', { whatsapp, pin });
      
      // Salvar credenciais ANTES de navegar
      const credentials = { whatsapp, pin };
      localStorage.setItem('client_credentials', JSON.stringify(credentials));
      
      // Salvar auth
      setAuth(data.token, data.user_type, data.user_data);
      
      // Verificar salvamento
      console.log('💾 Credenciais salvas:', credentials);
      console.log('🔍 Verificando localStorage:');
      console.log('  - client_credentials:', localStorage.getItem('client_credentials'));
      console.log('  - token:', localStorage.getItem('token'));
      console.log('  - user_type:', localStorage.getItem('user_type'));
      
      // Pequeno delay para garantir que localStorage foi salvo
      await new Promise(resolve => setTimeout(resolve, 100));
      
      toast.success('Bem-vindo ao chat!');
      navigate('/chat');
    } catch (error) {
      console.error('❌ Erro no login:', error);
      toast.error(error.response?.data?.detail || 'Erro ao fazer login');
    } finally {
      setLoading(false);
    }
  };

  // Mostrar loading enquanto tenta auto-login
  if (autoLoggingIn) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-cyan-50 to-teal-50 flex items-center justify-center p-4">
        <Card className="w-full max-w-md p-8 space-y-6 bg-white shadow-2xl">
          <div className="flex flex-col items-center space-y-4">
            <img 
              src="/cybertv.png" 
              alt="CYBERTV" 
              className="w-64 h-64 object-contain animate-pulse"
            />
            <h2 className="text-xl font-medium text-slate-600">
              Entrando automaticamente...
            </h2>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-cyan-50 to-teal-50 flex items-center justify-center p-4">
      <Card className="w-full max-w-md p-8 space-y-6 bg-white shadow-2xl">
        <div className="flex flex-col items-center space-y-4">
          <img 
            src="/cybertv.png" 
            alt="CYBERTV" 
            className="w-64 h-64 object-contain"
          />
          <h2 className="text-3xl font-bold text-slate-900" style={{fontFamily: 'Space Grotesk, sans-serif'}}>
            Área do Cliente
          </h2>
          <p className="text-slate-600 text-center">
            Entre com seu WhatsApp e PIN para acessar o chat
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-700">WhatsApp</label>
            <div className="relative">
              <Phone className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
              <Input
                data-testid="client-whatsapp-input"
                type="text"
                placeholder="55 11 99999-9999"
                value={whatsapp}
                onChange={(e) => setWhatsapp(e.target.value)}
                className="pl-10"
                required
              />
            </div>
            <p className="text-xs text-slate-500">
              Formato: código do país + DDD + número
            </p>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-700">PIN (2 dígitos)</label>
            <div className="relative">
              <Hash className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
              <Input
                data-testid="client-pin-input"
                type="password"
                placeholder="00"
                value={pin}
                onChange={(e) => setPin(e.target.value.replace(/\D/g, '').slice(0, 2))}
                className="pl-10"
                maxLength={2}
                required
              />
            </div>
            <p className="text-xs text-slate-500">
              Primeiro acesso? Crie seu PIN de 2 dígitos
            </p>
          </div>

          <Button 
            data-testid="client-submit-btn"
            type="submit" 
            className="w-full bg-blue-600 hover:bg-blue-700" 
            disabled={loading}
          >
            {loading ? 'Entrando...' : 'Avançar'}
          </Button>
        </form>

        <Button
          data-testid="back-home-btn"
          variant="outline"
          onClick={() => navigate('/')}
          className="w-full"
        >
          Voltar
        </Button>
      </Card>
    </div>
  );
};

export default ClientLogin;
