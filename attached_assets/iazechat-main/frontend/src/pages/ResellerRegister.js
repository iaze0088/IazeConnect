import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';
import api from '../lib/api';

const ResellerRegister = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: '',
    custom_domain: ''
  });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!formData.name || !formData.email || !formData.password) {
      toast.error('Preencha todos os campos');
      return;
    }

    if (formData.password !== formData.confirmPassword) {
      toast.error('As senhas não coincidem');
      return;
    }

    if (formData.password.length < 6) {
      toast.error('A senha deve ter pelo menos 6 caracteres');
      return;
    }

    setLoading(true);
    try {
      // Criar revenda com trial de 5 dias
      const response = await api.post('/resellers/register-trial', {
        name: formData.name,
        email: formData.email,
        password: formData.password,
        custom_domain: formData.custom_domain || ''
      });

      toast.success('🎉 Teste grátis ativado! Você tem 5 dias para explorar.');
      
      // Redirecionar para login
      setTimeout(() => {
        navigate('/reseller-login');
      }, 2000);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao criar conta');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-emerald-50 via-teal-50 to-cyan-50 flex items-center justify-center p-4">
      <Card className="w-full max-w-md p-8 space-y-6 bg-white shadow-2xl">
        <div className="flex flex-col items-center space-y-4">
          <div className="w-16 h-16 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-2xl flex items-center justify-center">
            <span className="text-3xl font-bold text-white">I</span>
          </div>
          <h2 className="text-3xl font-bold text-slate-900" style={{fontFamily: 'Space Grotesk, sans-serif'}}>
            IAZE - Crie sua Conta
          </h2>
          <p className="text-slate-600 text-center text-sm">
            Teste grátis por 5 dias, sem compromisso!
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              Nome da Empresa
            </label>
            <Input
              type="text"
              placeholder="Ex: Minha Empresa"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              Email
            </label>
            <Input
              type="email"
              placeholder="seu-email@exemplo.com"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              className="w-full"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              Senha
            </label>
            <Input
              type="password"
              placeholder="Mínimo 6 caracteres"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              className="w-full"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              Confirmar Senha
            </label>
            <Input
              type="password"
              placeholder="Digite a senha novamente"
              value={formData.confirmPassword}
              onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
              className="w-full"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              Domínio Customizado (Opcional)
            </label>
            <Input
              type="text"
              placeholder="Ex: ajuda.vip ou suporte.empresa.com"
              value={formData.custom_domain}
              onChange={(e) => setFormData({ ...formData, custom_domain: e.target.value })}
              className="w-full"
            />
            <p className="text-xs text-slate-500 mt-1">
              💡 Deixe vazio para usar o domínio automático (revenda.suporte.help)
            </p>
          </div>

          <Button
            type="submit"
            disabled={loading}
            className="w-full bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 text-white font-semibold py-3 text-lg"
          >
            {loading ? '⏳ Criando...' : '🎁 INICIAR TESTE GRÁTIS POR 5 DIAS'}
          </Button>
        </form>

        <div className="text-center text-sm text-slate-600">
          Já tem uma conta?{' '}
          <button
            onClick={() => navigate('/reseller-login')}
            className="text-emerald-600 hover:text-emerald-700 font-semibold"
          >
            Fazer Login
          </button>
        </div>

        <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-4 text-xs text-slate-600">
          <p className="font-semibold text-emerald-800 mb-2">✨ O que você ganha no teste:</p>
          <ul className="space-y-1 list-disc list-inside">
            <li>5 dias de acesso completo</li>
            <li>Todos os recursos disponíveis</li>
            <li>Sem cartão de crédito necessário</li>
            <li>Cancele a qualquer momento</li>
          </ul>
        </div>
      </Card>
    </div>
  );
};

export default ResellerRegister;
