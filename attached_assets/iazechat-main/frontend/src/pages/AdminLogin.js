import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Shield, Lock } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card } from '@/components/ui/card';
import { toast } from 'sonner';
import api from '../lib/api';
import { setAuth } from '../lib/auth';

const AdminLogin = () => {
  const navigate = useNavigate();
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await api.post('/auth/admin/login', { password });
      console.log('✅ Admin login response:', response.data);
      
      // Usar setAuth() para garantir consistência
      const userData = response.data.user_data || { 
        id: 'admin', 
        name: 'Admin Master',
        email: 'admin@admin.com'
      };
      
      setAuth(response.data.token, 'admin', userData);
      
      console.log('✅ Auth saved:', {
        token: localStorage.getItem('token')?.substring(0, 20) + '...',
        user_type: localStorage.getItem('user_type'),
        user_data: localStorage.getItem('user_data')
      });
      
      toast.success('✅ Login admin realizado!');
      
      // Usar navigate ao invés de window.location
      navigate('/admin');
    } catch (error) {
      console.error('❌ Admin login error:', error);
      toast.error(error.response?.data?.detail || 'Senha incorreta');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-pink-50 to-indigo-50 flex items-center justify-center p-4">
      <Card className="w-full max-w-md p-8 space-y-6 bg-white shadow-2xl">
        <div className="flex flex-col items-center space-y-4">
          <div className="w-16 h-16 bg-purple-600 rounded-2xl flex items-center justify-center">
            <Shield className="w-8 h-8 text-white" />
          </div>
          <h2 className="text-3xl font-bold text-slate-900" style={{fontFamily: 'Space Grotesk, sans-serif'}}>
            Admin Login
          </h2>
          <p className="text-slate-600 text-center">
            Acesso exclusivo para administradores
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-700">Senha Admin</label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
              <Input
                data-testid="admin-password-input"
                type="password"
                placeholder="Digite a senha admin"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="pl-10"
                required
              />
            </div>
          </div>

          <Button 
            data-testid="admin-submit-btn"
            type="submit" 
            className="w-full bg-purple-600 hover:bg-purple-700" 
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

export default AdminLogin;
