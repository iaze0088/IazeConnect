import React, { useState } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

const OfficeSearchFast = ({ onClose }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState([]);
  const [searchTime, setSearchTime] = useState(null);
  const [error, setError] = useState('');
  const [syncing, setSyncing] = useState(false);
  const [syncStatus, setSyncStatus] = useState(null);

  const handleSync = async () => {
    if (syncing) return;

    const confirmSync = window.confirm(
      '🔄 Sincronizar todos os clientes?\n\n' +
      'Isso vai buscar TODOS os clientes de TODOS os painéis Office.\n' +
      'Pode demorar 10-15 minutos.\n\n' +
      'Deseja continuar?'
    );

    if (!confirmSync) return;

    setSyncing(true);
    setSyncStatus('Iniciando sincronização...');

    try {
      const token = localStorage.getItem('token');
      
      const response = await axios.post(
        `${BACKEND_URL}/api/office-sync/sync-now`,
        {},
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );

      if (response.data.success) {
        setSyncStatus('✅ Sincronização iniciada em background!');
        
        // Aguardar um pouco e verificar o status
        setTimeout(async () => {
          try {
            const statusResponse = await axios.get(
              `${BACKEND_URL}/api/office-sync/sync-status`,
              {
                headers: {
                  'Authorization': `Bearer ${token}`
                }
              }
            );

            if (statusResponse.data.last_sync) {
              const summary = statusResponse.data.last_sync.summary;
              setSyncStatus(
                `✅ Última sincronização:\n` +
                `   • Total: ${summary.total_clients} clientes\n` +
                `   • Novos: ${summary.new_clients}\n` +
                `   • Atualizados: ${summary.updated_clients}`
              );
            }
          } catch (err) {
            console.error('Erro ao verificar status:', err);
          }
        }, 5000);

      } else {
        setSyncStatus('❌ Erro ao iniciar sincronização');
      }

    } catch (err) {
      console.error('Erro ao sincronizar:', err);
      setSyncStatus('❌ Erro: ' + (err.response?.data?.detail || err.message));
    } finally {
      setSyncing(false);
    }
  };

  const handleSearch = async () => {
    if (!searchTerm.trim()) {
      setError('Digite um termo de busca');
      return;
    }

    setLoading(true);
    setError('');
    setResults([]);
    setSearchTime(null);

    const startTime = Date.now();

    try {
      const token = localStorage.getItem('token');
      
      // Usar busca geral para maior flexibilidade
      // Se for apenas dígitos, pode ser telefone OU usuario (muitos usuarios são números)
      const response = await axios.post(
        `${BACKEND_URL}/api/office-sync/search-clients`,
        { search: searchTerm.trim() },
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      );

      const endTime = Date.now();
      const duration = endTime - startTime;

      if (response.data.success) {
        setResults(response.data.clients || []);
        setSearchTime(duration);
      } else {
        setError('Erro na busca');
      }

    } catch (err) {
      console.error('Erro ao buscar:', err);
      setError(err.response?.data?.detail || 'Erro ao buscar cliente');
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    alert('Copiado!');
  };

  const formatClientInfo = (client) => {
    return `📺 Dados do Cliente

👤 Nome: ${client.nome || 'N/A'}
🆔 Usuário: ${client.usuario}
🔑 Senha: ${client.senha}
📱 Telefone: ${client.telefone || 'N/A'}
📅 Vencimento: ${client.vencimento}
🟢 Status: ${client.status}
📡 Conexões: ${client.conexoes}
🏢 Painel: ${client.office_account}`;
  };

  return (
    <div style={styles.overlay}>
      <div style={styles.modal}>
        <div style={styles.header}>
          <h2 style={styles.title}>🚀 Busca Rápida Office</h2>
          <div style={styles.headerButtons}>
            <button 
              onClick={handleSync} 
              disabled={syncing}
              style={{...styles.syncButton, opacity: syncing ? 0.6 : 1}}
              title="Sincronizar todos os clientes de todos os painéis"
            >
              {syncing ? '🔄 Sincronizando...' : '🔄 Sincronizar'}
            </button>
            <button onClick={onClose} style={styles.closeButton}>✕</button>
          </div>
        </div>

        <div style={styles.content}>
          {/* Status de Sincronização */}
          {syncStatus && (
            <div style={styles.syncStatusBox}>
              {syncStatus.split('\n').map((line, i) => (
                <div key={i}>{line}</div>
              ))}
            </div>
          )}

          {/* Campo de busca */}
          <div style={styles.searchBox}>
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Digite telefone ou usuário..."
              style={styles.input}
              autoFocus
            />
            <button 
              onClick={handleSearch} 
              disabled={loading}
              style={styles.searchButton}
            >
              {loading ? '🔍 Buscando...' : '🔍 Buscar'}
            </button>
          </div>

          {/* Tempo de busca */}
          {searchTime !== null && (
            <div style={styles.searchTimeBox}>
              ⚡ Busca concluída em <strong>{searchTime}ms</strong> ({(searchTime/1000).toFixed(2)}s)
            </div>
          )}

          {/* Erro */}
          {error && (
            <div style={styles.errorBox}>
              ❌ {error}
            </div>
          )}

          {/* Resultados */}
          {results.length > 0 && (
            <div style={styles.resultsContainer}>
              <div style={styles.resultsHeader}>
                ✅ Encontrados {results.length} cliente(s)
              </div>

              {results.map((client, index) => (
                <div key={index} style={styles.clientCard}>
                  <div style={styles.clientHeader}>
                    <span style={styles.clientName}>
                      {client.nome || client.usuario}
                    </span>
                    <span style={styles.clientStatus}>
                      {client.status}
                    </span>
                  </div>

                  <div style={styles.clientDetails}>
                    <div style={styles.detailRow}>
                      <span style={styles.detailLabel}>👤 Usuário:</span>
                      <span style={styles.detailValue}>
                        {client.usuario}
                        <button 
                          onClick={() => copyToClipboard(client.usuario)}
                          style={styles.copyButton}
                        >
                          📋
                        </button>
                      </span>
                    </div>

                    <div style={styles.detailRow}>
                      <span style={styles.detailLabel}>🔑 Senha:</span>
                      <span style={styles.detailValue}>
                        {client.senha}
                        <button 
                          onClick={() => copyToClipboard(client.senha)}
                          style={styles.copyButton}
                        >
                          📋
                        </button>
                      </span>
                    </div>

                    {client.telefone && (
                      <div style={styles.detailRow}>
                        <span style={styles.detailLabel}>📱 Telefone:</span>
                        <span style={styles.detailValue}>{client.telefone}</span>
                      </div>
                    )}

                    <div style={styles.detailRow}>
                      <span style={styles.detailLabel}>📅 Vencimento:</span>
                      <span style={styles.detailValue}>{client.vencimento}</span>
                    </div>

                    <div style={styles.detailRow}>
                      <span style={styles.detailLabel}>📡 Conexões:</span>
                      <span style={styles.detailValue}>{client.conexoes}</span>
                    </div>

                    <div style={styles.detailRow}>
                      <span style={styles.detailLabel}>🏢 Painel:</span>
                      <span style={styles.detailValue}>{client.office_account}</span>
                    </div>
                  </div>

                  <button 
                    onClick={() => copyToClipboard(formatClientInfo(client))}
                    style={styles.copyAllButton}
                  >
                    📋 Copiar Tudo
                  </button>
                </div>
              ))}
            </div>
          )}

          {/* Nenhum resultado */}
          {!loading && results.length === 0 && searchTerm && !error && (
            <div style={styles.noResults}>
              ℹ️ Nenhum cliente encontrado com esse termo
            </div>
          )}

          {/* Info inicial */}
          {!searchTerm && !loading && (
            <div style={styles.infoBox}>
              <p><strong>💡 Como usar:</strong></p>
              <ul style={styles.infoList}>
                <li>Digite um <strong>telefone</strong> (ex: 11999999999)</li>
                <li>Ou digite um <strong>usuário</strong> (ex: 3334567oro)</li>
                <li>Pressione Enter ou clique em Buscar</li>
              </ul>
              <p style={styles.infoSpeed}>⚡ Busca instantânea em <strong>8.785 clientes</strong>!</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

const styles = {
  overlay: {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 9999,
  },
  modal: {
    backgroundColor: '#fff',
    borderRadius: '12px',
    width: '90%',
    maxWidth: '600px',
    maxHeight: '90vh',
    overflow: 'hidden',
    boxShadow: '0 10px 40px rgba(0,0,0,0.3)',
    display: 'flex',
    flexDirection: 'column',
  },
  header: {
    padding: '20px',
    borderBottom: '2px solid #e0e0e0',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#4CAF50',
  },
  title: {
    margin: 0,
    color: '#fff',
    fontSize: '24px',
  },
  headerButtons: {
    display: 'flex',
    gap: '10px',
    alignItems: 'center',
  },
  syncButton: {
    padding: '8px 16px',
    backgroundColor: '#2196F3',
    color: '#fff',
    border: 'none',
    borderRadius: '6px',
    cursor: 'pointer',
    fontSize: '14px',
    fontWeight: 'bold',
    transition: 'all 0.3s',
  },
  closeButton: {
    background: 'none',
    border: 'none',
    color: '#fff',
    fontSize: '28px',
    cursor: 'pointer',
    padding: '0 10px',
  },
  content: {
    padding: '20px',
    overflowY: 'auto',
    flex: 1,
  },
  searchBox: {
    display: 'flex',
    gap: '10px',
    marginBottom: '15px',
  },
  input: {
    flex: 1,
    padding: '12px',
    fontSize: '16px',
    border: '2px solid #ddd',
    borderRadius: '6px',
    outline: 'none',
  },
  searchButton: {
    padding: '12px 24px',
    backgroundColor: '#4CAF50',
    color: '#fff',
    border: 'none',
    borderRadius: '6px',
    cursor: 'pointer',
    fontSize: '16px',
    fontWeight: 'bold',
  },
  searchTimeBox: {
    padding: '10px',
    backgroundColor: '#e8f5e9',
    border: '1px solid #4CAF50',
    borderRadius: '6px',
    marginBottom: '15px',
    textAlign: 'center',
    color: '#2e7d32',
  },
  syncStatusBox: {
    padding: '15px',
    backgroundColor: '#e3f2fd',
    border: '2px solid #2196F3',
    borderRadius: '8px',
    marginBottom: '15px',
    color: '#1565c0',
    fontWeight: 'bold',
    whiteSpace: 'pre-line',
  },
  errorBox: {
    padding: '12px',
    backgroundColor: '#ffebee',
    border: '1px solid #f44336',
    borderRadius: '6px',
    color: '#c62828',
    marginBottom: '15px',
  },
  resultsContainer: {
    marginTop: '10px',
  },
  resultsHeader: {
    padding: '10px',
    backgroundColor: '#e3f2fd',
    border: '1px solid #2196F3',
    borderRadius: '6px',
    marginBottom: '15px',
    fontWeight: 'bold',
    color: '#1976d2',
  },
  clientCard: {
    border: '2px solid #e0e0e0',
    borderRadius: '8px',
    padding: '15px',
    marginBottom: '15px',
    backgroundColor: '#fafafa',
  },
  clientHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '15px',
    paddingBottom: '10px',
    borderBottom: '1px solid #ddd',
  },
  clientName: {
    fontSize: '18px',
    fontWeight: 'bold',
    color: '#333',
  },
  clientStatus: {
    padding: '4px 12px',
    borderRadius: '12px',
    fontSize: '12px',
    fontWeight: 'bold',
    backgroundColor: '#4CAF50',
    color: '#fff',
  },
  clientDetails: {
    display: 'flex',
    flexDirection: 'column',
    gap: '10px',
  },
  detailRow: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  detailLabel: {
    fontWeight: 'bold',
    color: '#666',
    minWidth: '120px',
  },
  detailValue: {
    flex: 1,
    textAlign: 'right',
    fontFamily: 'monospace',
    fontSize: '14px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'flex-end',
    gap: '8px',
  },
  copyButton: {
    background: 'none',
    border: 'none',
    cursor: 'pointer',
    fontSize: '16px',
    padding: '4px',
  },
  copyAllButton: {
    width: '100%',
    marginTop: '15px',
    padding: '12px',
    backgroundColor: '#2196F3',
    color: '#fff',
    border: 'none',
    borderRadius: '6px',
    cursor: 'pointer',
    fontSize: '16px',
    fontWeight: 'bold',
  },
  noResults: {
    padding: '20px',
    textAlign: 'center',
    color: '#666',
    backgroundColor: '#f5f5f5',
    borderRadius: '6px',
  },
  infoBox: {
    padding: '20px',
    backgroundColor: '#fff9e6',
    border: '2px solid #ffc107',
    borderRadius: '8px',
  },
  infoList: {
    listStyle: 'none',
    padding: 0,
    margin: '10px 0',
  },
  infoSpeed: {
    marginTop: '15px',
    fontSize: '14px',
    color: '#4CAF50',
    fontWeight: 'bold',
  },
};

export default OfficeSearchFast;
