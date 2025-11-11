import React, { useState } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Copy, ExternalLink, CheckCircle2, Globe } from 'lucide-react';
import { toast } from 'sonner';
import api from '../lib/api';

const DomainConfig = ({ resellerData, onUpdate }) => {
  const [isEditing, setIsEditing] = useState(false);
  const [customDomain, setCustomDomain] = useState(resellerData?.custom_domain || '');
  const [loading, setLoading] = useState(false);

  const SERVER_IP = '34.57.15.54';
  
  // Domínio padrão gerado automaticamente
  const defaultDomain = resellerData?.domain || 'revenda.suporte.help';
  
  // Domínio atual (customizado ou padrão)
  const currentDomain = resellerData?.custom_domain || defaultDomain;

  // Links importantes
  const links = [
    { path: '/', label: 'Chat do Cliente', description: 'Interface de atendimento para seus clientes' },
    { path: '/revenda/login', label: 'Painel Revenda', description: 'Seu painel de administração' },
    { path: '/atendente/login', label: 'Painel Atendente', description: 'Login dos seus atendentes' },
    { path: '/vendas', label: 'Funil de Vendas', description: 'Bot de vendas automatizado' }
  ];

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    toast.success('Copiado!');
  };

  const handleSave = async () => {
    setLoading(true);
    try {
      await api.put(`/resellers/${resellerData.id}`, {
        custom_domain: customDomain.trim()
      });
      toast.success('Domínio atualizado com sucesso!');
      setIsEditing(false);
      if (onUpdate) onUpdate();
    } catch (error) {
      toast.error('Erro ao atualizar domínio');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Configuração de Domínio */}
      <Card className="p-6">
        <div className="flex items-center gap-3 mb-4">
          <Globe className="w-6 h-6 text-blue-600" />
          <h3 className="text-lg font-semibold">Configuração de Domínio</h3>
        </div>

        {/* Domínio Atual */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-blue-900">Domínio Atual:</span>
            <CheckCircle2 className="w-5 h-5 text-blue-600" />
          </div>
          <div className="flex items-center gap-2">
            <code className="text-lg font-mono text-blue-700 bg-white px-3 py-2 rounded flex-1">
              {currentDomain}
            </code>
            <Button
              size="sm"
              variant="outline"
              onClick={() => copyToClipboard(currentDomain)}
            >
              <Copy className="w-4 h-4" />
            </Button>
          </div>
        </div>

        {/* Editar Domínio */}
        {isEditing ? (
          <div className="space-y-3">
            <div>
              <label className="block text-sm font-medium mb-1">Domínio Customizado:</label>
              <Input
                value={customDomain}
                onChange={(e) => setCustomDomain(e.target.value)}
                placeholder="Ex: ajuda.vip ou suporte.empresa.com"
              />
              <p className="text-xs text-slate-500 mt-1">
                Deixe vazio para usar o domínio padrão ({defaultDomain})
              </p>
            </div>
            <div className="flex gap-2">
              <Button onClick={handleSave} disabled={loading}>
                {loading ? 'Salvando...' : 'Salvar'}
              </Button>
              <Button variant="outline" onClick={() => setIsEditing(false)}>
                Cancelar
              </Button>
            </div>
          </div>
        ) : (
          <Button variant="outline" onClick={() => setIsEditing(true)}>
            {resellerData?.custom_domain ? 'Alterar Domínio' : 'Configurar Domínio Customizado'}
          </Button>
        )}
      </Card>

      {/* Configuração DNS */}
      <Card className="p-6 bg-gradient-to-br from-purple-50 to-blue-50">
        <h3 className="text-lg font-semibold mb-3">📡 Configuração DNS</h3>
        <p className="text-sm text-slate-600 mb-4">
          Para usar um domínio customizado, configure o DNS do seu domínio com o seguinte registro:
        </p>
        
        <div className="bg-white border-2 border-purple-200 rounded-lg p-4">
          <div className="grid grid-cols-3 gap-4 text-sm">
            <div>
              <span className="font-semibold text-purple-700">Tipo:</span>
              <p className="font-mono mt-1">A</p>
            </div>
            <div>
              <span className="font-semibold text-purple-700">Nome:</span>
              <p className="font-mono mt-1">@</p>
            </div>
            <div>
              <span className="font-semibold text-purple-700">IP:</span>
              <div className="flex items-center gap-2 mt-1">
                <code className="font-mono font-bold text-purple-900">{SERVER_IP}</code>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => copyToClipboard(SERVER_IP)}
                >
                  <Copy className="w-3 h-3" />
                </Button>
              </div>
            </div>
          </div>
        </div>
        
        <p className="text-xs text-slate-500 mt-3">
          ⚠️ A propagação DNS pode levar até 48 horas
        </p>
      </Card>

      {/* Links da Revenda */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">🔗 Links do Sistema</h3>
        <div className="space-y-3">
          {links.map((link) => {
            const fullUrl = `https://${currentDomain}${link.path}`;
            return (
              <div key={link.path} className="flex items-center gap-3 p-3 bg-slate-50 rounded-lg hover:bg-slate-100 transition">
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-slate-900">{link.label}</span>
                    <a
                      href={fullUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:text-blue-700"
                    >
                      <ExternalLink className="w-4 h-4" />
                    </a>
                  </div>
                  <p className="text-xs text-slate-500">{link.description}</p>
                  <code className="text-xs text-slate-600 mt-1 block">{fullUrl}</code>
                </div>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => copyToClipboard(fullUrl)}
                >
                  <Copy className="w-4 h-4" />
                </Button>
              </div>
            );
          })}
        </div>
      </Card>
    </div>
  );
};

export default DomainConfig;
