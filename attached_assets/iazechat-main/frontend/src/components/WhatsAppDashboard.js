import React, { useState, useEffect } from 'react';
import { toast } from 'sonner';

const WhatsAppDashboard = () => {
  const [stats, setStats] = useState({
    totalInstances: 0,
    connectedInstances: 0,
    disconnectedInstances: 0,
    totalMessages: 0,
    messagesLastHour: 0,
    messagesLast24h: 0,
    uptime: '0h 0m',
    evolution_api_status: 'unknown'
  });
  const [instancesList, setInstancesList] = useState([]);
  const [loading, setLoading] = useState(true);

  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

  // Carregar estatísticas
  const loadStats = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/whatsapp/dashboard-stats`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (error) {
      console.error('Erro ao carregar estatísticas:', error);
    }
  };

  // Carregar lista de instâncias
  const loadInstances = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/whatsapp/connections`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setInstancesList(data.connections || []);
      }
    } catch (error) {
      console.error('Erro ao carregar instâncias:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadStats();
    loadInstances();

    // Atualizar a cada 30 segundos
    const interval = setInterval(() => {
      loadStats();
      loadInstances();
    }, 30000);

    return () => clearInterval(interval);
  }, []);

  // Calcular porcentagem de uptime
  const calculateUptimePercentage = () => {
    if (stats.totalInstances === 0) return 0;
    return ((stats.connectedInstances / stats.totalInstances) * 100).toFixed(1);
  };

  return (
    <div className="whatsapp-dashboard">
      <div className="dashboard-header">
        <h2>📊 Dashboard WhatsApp</h2>
        <div className="last-update">
          Última atualização: {new Date().toLocaleTimeString()}
        </div>
      </div>

      {/* Cards de Estatísticas */}
      <div className="stats-grid">
        {/* Total de Instâncias */}
        <div className="stat-card">
          <div className="stat-icon">📱</div>
          <div className="stat-content">
            <div className="stat-value">{stats.totalInstances}</div>
            <div className="stat-label">Total de Instâncias</div>
          </div>
        </div>

        {/* Instâncias Conectadas */}
        <div className="stat-card stat-success">
          <div className="stat-icon">✅</div>
          <div className="stat-content">
            <div className="stat-value">{stats.connectedInstances}</div>
            <div className="stat-label">Conectadas</div>
          </div>
        </div>

        {/* Instâncias Desconectadas */}
        <div className="stat-card stat-warning">
          <div className="stat-icon">⚠️</div>
          <div className="stat-content">
            <div className="stat-value">{stats.disconnectedInstances}</div>
            <div className="stat-label">Desconectadas</div>
          </div>
        </div>

        {/* Uptime */}
        <div className="stat-card stat-info">
          <div className="stat-icon">⏱️</div>
          <div className="stat-content">
            <div className="stat-value">{calculateUptimePercentage()}%</div>
            <div className="stat-label">Uptime</div>
          </div>
        </div>

        {/* Mensagens Última Hora */}
        <div className="stat-card">
          <div className="stat-icon">📨</div>
          <div className="stat-content">
            <div className="stat-value">{stats.messagesLastHour}</div>
            <div className="stat-label">Mensagens (1h)</div>
          </div>
        </div>

        {/* Mensagens 24h */}
        <div className="stat-card">
          <div className="stat-icon">📊</div>
          <div className="stat-content">
            <div className="stat-value">{stats.messagesLast24h}</div>
            <div className="stat-label">Mensagens (24h)</div>
          </div>
        </div>

        {/* Status Evolution API */}
        <div className={`stat-card ${stats.evolution_api_status === 'online' ? 'stat-success' : 'stat-danger'}`}>
          <div className="stat-icon">{stats.evolution_api_status === 'online' ? '🟢' : '🔴'}</div>
          <div className="stat-content">
            <div className="stat-value">{stats.evolution_api_status === 'online' ? 'Online' : 'Offline'}</div>
            <div className="stat-label">Evolution API</div>
          </div>
        </div>

        {/* Tempo de Atividade */}
        <div className="stat-card stat-info">
          <div className="stat-icon">⏰</div>
          <div className="stat-content">
            <div className="stat-value">{stats.uptime}</div>
            <div className="stat-label">Tempo Ativo</div>
          </div>
        </div>
      </div>

      {/* Lista de Instâncias */}
      <div className="instances-section">
        <h3>📱 Instâncias Ativas</h3>
        
        {loading ? (
          <div className="loading-spinner">Carregando...</div>
        ) : instancesList.length === 0 ? (
          <div className="empty-state">
            <p>Nenhuma instância encontrada</p>
          </div>
        ) : (
          <div className="instances-table">
            <table>
              <thead>
                <tr>
                  <th>Nome</th>
                  <th>Status</th>
                  <th>Número</th>
                  <th>Mensagens</th>
                  <th>Uptime</th>
                  <th>Última Atividade</th>
                </tr>
              </thead>
              <tbody>
                {instancesList.map((instance) => (
                  <tr key={instance.id}>
                    <td>
                      <strong>{instance.instance_name}</strong>
                    </td>
                    <td>
                      <span className={`status-badge status-${instance.status || 'unknown'}`}>
                        {instance.status === 'open' ? '🟢 Conectado' : 
                         instance.status === 'close' ? '🔴 Desconectado' : 
                         '⚪ Desconhecido'}
                      </span>
                    </td>
                    <td>{instance.number || 'N/A'}</td>
                    <td className="text-center">{instance.message_count || 0}</td>
                    <td>{instance.uptime || 'N/A'}</td>
                    <td>{instance.last_activity ? new Date(instance.last_activity).toLocaleString() : 'N/A'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <style jsx>{`
        .whatsapp-dashboard {
          padding: 20px;
        }

        .dashboard-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 30px;
        }

        .dashboard-header h2 {
          font-size: 24px;
          font-weight: 600;
          color: #1a1a1a;
        }

        .last-update {
          font-size: 14px;
          color: #666;
        }

        .stats-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
          gap: 20px;
          margin-bottom: 40px;
        }

        .stat-card {
          background: white;
          border: 1px solid #e0e0e0;
          border-radius: 12px;
          padding: 20px;
          display: flex;
          align-items: center;
          gap: 15px;
          transition: all 0.3s ease;
        }

        .stat-card:hover {
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
          transform: translateY(-2px);
        }

        .stat-card.stat-success {
          border-left: 4px solid #10b981;
        }

        .stat-card.stat-warning {
          border-left: 4px solid #f59e0b;
        }

        .stat-card.stat-danger {
          border-left: 4px solid #ef4444;
        }

        .stat-card.stat-info {
          border-left: 4px solid #3b82f6;
        }

        .stat-icon {
          font-size: 36px;
        }

        .stat-content {
          flex: 1;
        }

        .stat-value {
          font-size: 28px;
          font-weight: 700;
          color: #1a1a1a;
          margin-bottom: 5px;
        }

        .stat-label {
          font-size: 14px;
          color: #666;
          font-weight: 500;
        }

        .instances-section {
          background: white;
          border: 1px solid #e0e0e0;
          border-radius: 12px;
          padding: 25px;
        }

        .instances-section h3 {
          font-size: 18px;
          font-weight: 600;
          margin-bottom: 20px;
          color: #1a1a1a;
        }

        .instances-table {
          overflow-x: auto;
        }

        .instances-table table {
          width: 100%;
          border-collapse: collapse;
        }

        .instances-table th {
          background: #f9fafb;
          padding: 12px;
          text-align: left;
          font-weight: 600;
          font-size: 14px;
          color: #6b7280;
          border-bottom: 2px solid #e5e7eb;
        }

        .instances-table td {
          padding: 12px;
          border-bottom: 1px solid #e5e7eb;
          font-size: 14px;
        }

        .instances-table tr:hover {
          background: #f9fafb;
        }

        .text-center {
          text-align: center;
        }

        .status-badge {
          display: inline-block;
          padding: 4px 12px;
          border-radius: 12px;
          font-size: 12px;
          font-weight: 600;
        }

        .status-badge.status-open {
          background: #d1fae5;
          color: #065f46;
        }

        .status-badge.status-close {
          background: #fee2e2;
          color: #991b1b;
        }

        .status-badge.status-unknown {
          background: #f3f4f6;
          color: #6b7280;
        }

        .loading-spinner {
          text-align: center;
          padding: 40px;
          color: #666;
        }

        .empty-state {
          text-align: center;
          padding: 40px;
          color: #999;
        }
      `}</style>
    </div>
  );
};

export default WhatsAppDashboard;
