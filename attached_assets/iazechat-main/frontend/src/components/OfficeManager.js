import React, { useState, useEffect } from 'react';
import { Plus, Trash2, Eye, EyeOff, ExternalLink } from 'lucide-react';
import api from '../lib/api';

const OfficeManager = () => {
  const [credentials, setCredentials] = useState([]);
  const [showAddForm, setShowAddForm] = useState(false);
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState({});
  
  const [formData, setFormData] = useState({
    url: 'https://gestor.my',
    username: '',
    password: '',
    nome: ''
  });

  useEffect(() => {
    loadCredentials();
  }, []);

  const loadCredentials = async () => {
    try {
      setLoading(true);
      console.log('🔍 Buscando credenciais do Office...');
      const response = await api.get('/office-sync/credentials');
      console.log('✅ Credenciais recebidas:', response.data);
      setCredentials(response.data.credentials || []);
    } catch (error) {
      console.error('❌ Erro ao carregar credenciais:', error);
      console.error('Detalhes do erro:', error.response?.data || error.message);
      // Não mostrar alert no primeiro carregamento
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.username || !formData.password) {
      alert('Preencha usuário e senha!');
      return;
    }

    try {
      setLoading(true);
      console.log('📤 Enviando credenciais:', {
        ...formData,
        password: '***'
      });
      
      const response = await api.post('/office-sync/credentials', formData);
      console.log('✅ Resposta:', response.data);
      
      alert('Credenciais cadastradas com sucesso!');
      setFormData({
        url: 'https://gestor.my',
        username: '',
        password: '',
        nome: ''
      });
      setShowAddForm(false);
      loadCredentials();
    } catch (error) {
      console.error('❌ Erro ao cadastrar:', error);
      console.error('Detalhes:', error.response?.data || error.message);
      alert(`Erro ao cadastrar credenciais: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (credentialId) => {
    if (!window.confirm('Tem certeza que deseja remover estas credenciais?')) {
      return;
    }

    try {
      setLoading(true);
      await api.delete(`/office-sync/credentials/${credentialId}`);
      alert('Credenciais removidas com sucesso!');
      loadCredentials();
    } catch (error) {
      console.error('Erro ao deletar:', error);
      alert('Erro ao remover credenciais');
    } finally {
      setLoading(false);
    }
  };

  const togglePasswordVisibility = (id) => {
    setShowPassword(prev => ({
      ...prev,
      [id]: !prev[id]
    }));
  };

  return (
    <div className="p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              🏢 Gerenciar Office
            </h1>
            <p className="text-gray-600 mt-1">
              Cadastre as credenciais do gestor.my para consulta automática
            </p>
          </div>
          <button
            onClick={() => setShowAddForm(!showAddForm)}
            className="flex items-center gap-2 bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors"
          >
            <Plus size={20} />
            Adicionar Credenciais
          </button>
        </div>

        {/* Formulário de Adicionar */}
        {showAddForm && (
          <div className="bg-white rounded-lg shadow-md p-6 mb-6 border border-gray-200">
            <h2 className="text-lg font-semibold mb-4">
              ➕ Adicionar Novas Credenciais
            </h2>
            <form onSubmit={handleSubmit}>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Nome/Descrição
                  </label>
                  <input
                    type="text"
                    value={formData.nome}
                    onChange={(e) => setFormData({ ...formData, nome: e.target.value })}
                    placeholder="Ex: Office Principal, Office Revenda 1..."
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    URL do Office
                  </label>
                  <input
                    type="text"
                    value={formData.url}
                    onChange={(e) => setFormData({ ...formData, url: e.target.value })}
                    placeholder="https://gestor.my"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Usuário *
                  </label>
                  <input
                    type="text"
                    value={formData.username}
                    onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                    placeholder="fabiotec35"
                    required
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Senha *
                  </label>
                  <input
                    type="password"
                    value={formData.password}
                    onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                    placeholder="••••••••"
                    required
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                  />
                </div>
              </div>

              <div className="flex gap-3 mt-6">
                <button
                  type="submit"
                  disabled={loading}
                  className="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700 disabled:bg-gray-400 transition-colors"
                >
                  {loading ? 'Salvando...' : '✅ Salvar Credenciais'}
                </button>
                <button
                  type="button"
                  onClick={() => setShowAddForm(false)}
                  className="bg-gray-200 text-gray-700 px-6 py-2 rounded-lg hover:bg-gray-300 transition-colors"
                >
                  Cancelar
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Lista de Credenciais */}
        <div className="bg-white rounded-lg shadow-md">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold">
              📋 Credenciais Cadastradas ({credentials.length})
            </h2>
          </div>

          {loading && credentials.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              Carregando...
            </div>
          ) : credentials.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              <p className="mb-2">Nenhuma credencial cadastrada</p>
              <p className="text-sm">
                Clique em "Adicionar Credenciais" para começar
              </p>
            </div>
          ) : (
            <div className="divide-y divide-gray-200">
              {credentials.map((cred) => (
                <div
                  key={cred.id}
                  className="p-6 hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-3">
                        <h3 className="text-lg font-semibold text-gray-900">
                          {cred.nome}
                        </h3>
                        <span className="px-3 py-1 bg-green-100 text-green-800 text-xs font-medium rounded-full">
                          Ativo
                        </span>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                        <div>
                          <span className="text-gray-600">🌐 URL:</span>
                          <div className="flex items-center gap-2 mt-1">
                            <span className="font-medium text-gray-900">
                              {cred.url}
                            </span>
                            <a
                              href={cred.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-blue-600 hover:text-blue-800"
                            >
                              <ExternalLink size={16} />
                            </a>
                          </div>
                        </div>

                        <div>
                          <span className="text-gray-600">👤 Usuário:</span>
                          <p className="font-medium text-gray-900 mt-1">
                            {cred.username}
                          </p>
                        </div>

                        <div>
                          <span className="text-gray-600">📅 Cadastrado em:</span>
                          <p className="font-medium text-gray-900 mt-1">
                            {new Date(cred.created_at).toLocaleDateString('pt-BR')}
                          </p>
                        </div>
                      </div>
                    </div>

                    <button
                      onClick={() => handleDelete(cred.id)}
                      disabled={loading}
                      className="ml-4 p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors disabled:opacity-50"
                      title="Remover credenciais"
                    >
                      <Trash2 size={20} />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Info */}
        <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h3 className="font-semibold text-blue-900 mb-2">
            ℹ️ Como funciona?
          </h3>
          <ul className="text-sm text-blue-800 space-y-1">
            <li>• As credenciais são usadas para fazer login automático no Office (gestor.my)</li>
            <li>• Atendentes podem buscar clientes sem precisar fazer login manualmente</li>
            <li>• Você pode cadastrar múltiplas credenciais (diferentes revendas)</li>
            <li>• A senha é armazenada de forma segura no banco de dados</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default OfficeManager;
