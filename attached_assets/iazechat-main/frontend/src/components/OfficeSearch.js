import React, { useState } from 'react';
import { Search, Loader2, ExternalLink, Calendar, CheckCircle, XCircle, RefreshCw, Download } from 'lucide-react';
import api from '../lib/api';

const OfficeSearch = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  const handleSearch = async (e) => {
    e.preventDefault();
    
    if (!searchTerm.trim()) {
      setError('Digite um usuário ou WhatsApp para buscar');
      return;
    }

    try {
      setLoading(true);
      setError('');
      setResult(null);
      
      console.log('🔍 Buscando cliente:', searchTerm);
      
      const response = await api.post('/office/search', {
        search_term: searchTerm.trim()
      });
      
      console.log('✅ Resultado:', response.data);
      setResult(response.data);
      
    } catch (error) {
      console.error('❌ Erro ao buscar:', error);
      setError(error.response?.data?.detail || 'Erro ao buscar cliente');
    } finally {
      setLoading(false);
    }
  };

  const handleRenovar = async (usuario, dias = 30) => {
    if (!window.confirm(`Renovar ${usuario} por ${dias} dias?`)) {
      return;
    }

    try {
      setLoading(true);
      
      const response = await api.post('/office/renovar', {
        usuario: usuario,
        dias: dias,
        credential_id: result.credential_used?.id
      });
      
      if (response.data.success) {
        alert(`✅ ${usuario} renovado por ${dias} dias!`);
        // Buscar novamente para atualizar dados
        handleSearch({ preventDefault: () => {} });
      } else {
        alert(`❌ ${response.data.error}`);
      }
      
    } catch (error) {
      console.error('❌ Erro ao renovar:', error);
      alert('Erro ao renovar cliente');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      {/* Card de Busca */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center gap-3 mb-4">
          <Search className="w-6 h-6 text-teal-600" />
          <h2 className="text-xl font-bold text-gray-900">
            Pesquisar Credenciais Office
          </h2>
        </div>

        <form onSubmit={handleSearch}>
          <div className="flex gap-3">
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Digite o usuário ou WhatsApp do cliente..."
              className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-transparent"
              disabled={loading}
            />
            <button
              type="submit"
              disabled={loading}
              className="px-6 py-3 bg-teal-600 text-white rounded-lg hover:bg-teal-700 disabled:bg-gray-400 transition-colors flex items-center gap-2"
            >
              {loading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Buscando...
                </>
              ) : (
                <>
                  <Search className="w-5 h-5" />
                  Buscar
                </>
              )}
            </button>
          </div>
        </form>

        {error && (
          <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
            ⚠️ {error}
          </div>
        )}
      </div>

      {/* Resultado da Busca */}
      {result && (
        <div className="bg-white rounded-lg shadow-md p-6">
          {result.success ? (
            <div>
              {/* Header */}
              <div className="flex items-center justify-between mb-6 pb-4 border-b border-gray-200">
                <h3 className="text-lg font-bold text-gray-900">
                  ✅ Cliente Encontrado
                </h3>
                {result.credential_used && (
                  <span className="text-sm text-gray-600">
                    📂 {result.credential_used.nome}
                  </span>
                )}
              </div>

              {/* Dados do Cliente */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                {result.usuario && (
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <span className="text-sm text-gray-600">👤 Usuário</span>
                    <p className="text-lg font-bold text-gray-900 mt-1 font-mono">
                      {result.usuario}
                    </p>
                  </div>
                )}

                {result.senha && (
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <span className="text-sm text-gray-600">🔑 Senha</span>
                    <p className="text-lg font-bold text-gray-900 mt-1 font-mono">
                      {result.senha}
                    </p>
                  </div>
                )}

                {result.status && (
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <span className="text-sm text-gray-600">📊 Status</span>
                    <div className="flex items-center gap-2 mt-1">
                      {result.status.toLowerCase().includes('ativo') ? (
                        <CheckCircle className="w-5 h-5 text-green-600" />
                      ) : (
                        <XCircle className="w-5 h-5 text-red-600" />
                      )}
                      <p className="text-lg font-bold text-gray-900">
                        {result.status}
                      </p>
                    </div>
                  </div>
                )}

                {result.vencimento && (
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <span className="text-sm text-gray-600">📅 Vencimento</span>
                    <div className="flex items-center gap-2 mt-1">
                      <Calendar className="w-5 h-5 text-gray-600" />
                      <p className="text-lg font-bold text-gray-900">
                        {result.vencimento}
                      </p>
                    </div>
                  </div>
                )}
              </div>

              {/* Texto Completo (se houver) */}
              {result.texto_completo && (
                <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                  <span className="text-sm font-semibold text-blue-900">
                    📄 Informações Completas:
                  </span>
                  <p className="text-sm text-blue-800 mt-2 whitespace-pre-wrap">
                    {result.texto_completo}
                  </p>
                </div>
              )}

              {/* Ações */}
              <div className="flex flex-wrap gap-3">
                <button
                  onClick={() => handleRenovar(result.usuario || searchTerm, 30)}
                  disabled={loading}
                  className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-400 transition-colors flex items-center gap-2"
                >
                  <RefreshCw className="w-4 h-4" />
                  Renovar 30 dias
                </button>

                <button
                  onClick={() => handleRenovar(result.usuario || searchTerm, 60)}
                  disabled={loading}
                  className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-400 transition-colors flex items-center gap-2"
                >
                  <RefreshCw className="w-4 h-4" />
                  Renovar 60 dias
                </button>

                {result.credential_used?.url && (
                  <a
                    href={result.credential_used.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
                  >
                    <ExternalLink className="w-4 h-4" />
                    Abrir Office
                  </a>
                )}
              </div>

              {/* Ações Disponíveis (da API) */}
              {result.acoes && result.acoes.length > 0 && (
                <div className="mt-6 pt-6 border-t border-gray-200">
                  <h4 className="font-semibold text-gray-900 mb-3">
                    🔧 Ações Disponíveis:
                  </h4>
                  <div className="flex flex-wrap gap-2">
                    {result.acoes.map((acao, index) => (
                      <a
                        key={index}
                        href={`${result.credential_used?.url}${acao.url}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="px-3 py-1 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors text-sm"
                      >
                        {acao.texto}
                      </a>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-8">
              <div className="text-6xl mb-4">🔍</div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                Cliente não encontrado
              </h3>
              <p className="text-gray-600">
                {result.error || 'Nenhum resultado encontrado para essa busca'}
              </p>
            </div>
          )}
        </div>
      )}

      {/* Info */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="font-semibold text-blue-900 mb-2">
          ℹ️ Como usar:
        </h3>
        <ul className="text-sm text-blue-800 space-y-1">
          <li>• Digite o <strong>usuário</strong> ou <strong>WhatsApp</strong> do cliente</li>
          <li>• O sistema busca automaticamente em todos os Offices cadastrados</li>
          <li>• Você pode renovar, editar ou baixar dados diretamente aqui</li>
          <li>• Clique em "Abrir Office" para acessar o painel completo</li>
        </ul>
      </div>
    </div>
  );
};

export default OfficeSearch;
