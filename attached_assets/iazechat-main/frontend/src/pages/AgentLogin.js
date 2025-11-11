import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Headphones, User, Lock } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card } from '@/components/ui/card';
import { toast } from 'sonner';
import api from '../lib/api';
import { setAuth } from '../lib/auth';

const AgentLogin = () => {
  const navigate = useNavigate();
  const [login, setLogin] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      // Endpoint correto (api.js já adiciona /api)
      const response = await api.post('/auth/agent/login', { login, password });
      
      const data = response.data;
      setAuth(data.token, data.user_type, data.user_data);
      toast.success(`Bem-vindo, ${data.user_data.name}!`);
      navigate('/atendente');
    } catch (error) {
      console.error('Erro no login:', error);
      toast.error(error.response?.data?.detail || 'Login ou senha inválidos');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-blue-50 to-cyan-50 flex items-center justify-center p-4">
      <Card className="w-full max-w-md p-8 space-y-6 bg-white shadow-2xl">
        <div className="flex flex-col items-center space-y-4">
          <div className="w-16 h-16 bg-indigo-600 rounded-2xl flex items-center justify-center">
            <Headphones className="w-8 h-8 text-white" />
          </div>
          <h2 className="text-3xl font-bold text-slate-900" style={{fontFamily: 'Space Grotesk, sans-serif'}}>
            Atendente Login
          </h2>
          <p className="text-slate-600 text-center">
            Entre para gerenciar tickets e conversas
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-700">Login</label>
            <div className="relative">
              <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
              <Input
                data-testid="agent-login-input"
                type="text"
                placeholder="Seu login"
                value={login}
                onChange={(e) => setLogin(e.target.value)}
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
                data-testid="agent-password-input"
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
            data-testid="agent-submit-btn"
            type="submit" 
            className="w-full bg-indigo-600 hover:bg-indigo-700" 
            disabled={loading}
          >
            {loading ? 'Entrando...' : 'Entrar'}
          </Button>
        </form>

        <div className="flex gap-2">
          <Button
            data-testid="back-home-btn"
            variant="outline"
            onClick={() => navigate('/')}
            className="flex-1"
          >
            Voltar
          </Button>
          
          <Button
            data-testid="clear-cache-btn"
            variant="outline"
            onClick={() => window.location.href = '/clear-cache.html'}
            className="flex-1 text-orange-600 border-orange-300 hover:bg-orange-50"
          >
            🔧 Limpar Cache
          </Button>
        </div>
      </Card>
    </div>
  );
};

export default AgentLogin;
