import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Store, Mail, Lock } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card } from '@/components/ui/card';
import { toast } from 'sonner';
import api from '../lib/api';
import { setAuth } from '../lib/auth';

const ResellerLogin = () => {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [subscriptionExpired, setSubscriptionExpired] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const { data } = await api.post('/resellers/login', { email, password });
      setAuth(data.token, data.user_type, data.user_data);
      toast.success(`Bem-vindo, ${data.user_data.name}!`);
      navigate('/revenda/dashboard');
    } catch (error) {
      const errorDetail = error.response?.data?.detail || 'Email ou senha inválidos';
      const subscriptionStatus = error.response?.headers?.['x-subscription-status'];
      
      // Verificar se é erro de assinatura expirada
      if (subscriptionStatus === 'expired' || errorDetail.toLowerCase().includes('assinatura expirada')) {
        setSubscriptionExpired(true);
        toast.error(
          '⚠️ ' + errorDetail,
          {
            duration: 5000,
            action: {
              label: 'Ver Planos',
              onClick: () => {
                // Tentar fazer login e redirecionar para aba de pagamentos
                // (usuário precisa ver os planos mesmo com assinatura expirada)
                toast.info('Por favor, contate o administrador para renovar sua assinatura.');
              }
            }
          }
        );
      } else {
        toast.error(errorDetail);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-emerald-50 via-teal-50 to-cyan-50 flex items-center justify-center p-4">
      <Card className="w-full max-w-md p-8 space-y-6 bg-white shadow-2xl">
        {/* Aviso de assinatura expirada */}
        {subscriptionExpired && (
          <div className="bg-red-50 border-l-4 border-red-500 p-4 rounded-r-lg">
            <div className="flex items-start">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">
                  Assinatura Expirada
                </h3>
                <div className="mt-2 text-sm text-red-700">
                  <p>
                    Sua assinatura expirou. Entre em contato com o administrador para renovar e voltar a acessar o sistema.
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}
        
        <div className="flex flex-col items-center space-y-4">
          <div className="w-16 h-16 bg-emerald-600 rounded-2xl flex items-center justify-center">
            <Store className="w-8 h-8 text-white" />
          </div>
          <h2 className="text-3xl font-bold text-slate-900" style={{fontFamily: 'Space Grotesk, sans-serif'}}>
            Painel de Revenda
          </h2>
          <p className="text-slate-600 text-center">
            Faça login para gerenciar sua revenda
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-700">Email</label>
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
              <Input
                data-testid="reseller-email-input"
                type="email"
                placeholder="seu-email@exemplo.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="pl-10"
                required
              />
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-700">Senha</label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
              <Input
                data-testid="reseller-password-input"
                type="password"
                placeholder="Sua senha"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="pl-10"
                required
              />
            </div>
          </div>

          <Button 
            data-testid="reseller-submit-btn"
            type="submit" 
            className="w-full bg-emerald-600 hover:bg-emerald-700" 
            disabled={loading}
          >
            {loading ? 'Entrando...' : 'Entrar'}
          </Button>
        </form>

        <div className="text-center text-sm text-slate-600">
          Não tem uma conta?{' '}
          <button
            onClick={() => navigate('/reseller-register')}
            className="text-emerald-600 hover:text-emerald-700 font-semibold"
          >
            Criar Conta Grátis
          </button>
        </div>
      </Card>
    </div>
  );
};

export default ResellerLogin;
