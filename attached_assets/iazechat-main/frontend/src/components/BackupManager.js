import React, { useState, useEffect } from 'react';
import { Save, AlertCircle, RefreshCw, Download, Upload, Trash2, Clock } from 'lucide-react';
import { Button } from './ui/button';
import { Card } from './ui/card';
import api from '../lib/api';
import { toast } from 'sonner';

function BackupManager() {
  const [backups, setBackups] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isCreating, setIsCreating] = useState(false);
  const [isRestoring, setIsRestoring] = useState(false);
  const [isUploading, setIsUploading] = useState(false);

  useEffect(() => {
    loadBackups();
  }, []);

  const loadBackups = async () => {
    try {
      setIsLoading(true);
      const { data } = await api.get('/backups');
      // Transformar para o formato esperado pelo frontend
      const formatted = data.map(b => ({
        filename: `backup_${b.backup_id}.json`,
        created_at: b.created_at,
        size: b.size_mb * 1024 * 1024, // Converter MB para bytes
        backup_id: b.backup_id,
        collections_count: b.collections_count,
        total_documents: b.total_documents
      }));
      setBackups(formatted);
    } catch (error) {
      console.error('Error loading backups:', error);
      toast.error('Erro ao carregar backups');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateBackup = async () => {
    try {
      setIsCreating(true);
      toast.info('Criando backup completo do sistema...');
      const { data } = await api.post('/backups/create');
      toast.success(`✅ Backup criado! ${data.collections_count} collections, ${data.total_documents} documentos (${data.size_mb}MB)`);
      await loadBackups();
    } catch (error) {
      console.error('Error creating backup:', error);
      toast.error('❌ Erro ao criar backup: ' + (error.response?.data?.detail || error.message));
    } finally {
      setIsCreating(false);
    }
  };

  const handleDownloadBackup = async (backup) => {
    try {
      toast.info('📥 Baixando backup...');
      
      const response = await api.get(`/admin/backup/download/${backup.backup_id}`, {
        responseType: 'blob'
      });
      
      // Criar URL para download
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', backup.filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      toast.success('✅ Backup baixado com sucesso!');
    } catch (error) {
      console.error('Error downloading backup:', error);
      toast.error('❌ Erro ao baixar backup');
    }
  };

  const handleUploadBackup = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    
    if (!file.name.endsWith('.json')) {
      toast.error('❌ Apenas arquivos .json são permitidos');
      return;
    }
    
    try {
      setIsUploading(true);
      toast.info('📤 Enviando backup...');
      
      const formData = new FormData();
      formData.append('file', file);
      
      await api.post('/admin/backup/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      
      toast.success('✅ Backup enviado com sucesso!');
      await loadBackups();
      
      // Limpar input
      event.target.value = '';
    } catch (error) {
      console.error('Error uploading backup:', error);
      toast.error('❌ Erro ao enviar backup: ' + (error.response?.data?.detail || error.message));
    } finally {
      setIsUploading(false);
    }
  };

  const handleRestoreBackup = async (filename) => {
    // Extrair backup_id do filename
    const backup_id = filename.replace('backup_', '').replace('.json', '');
    
    if (!window.confirm(`⚠️ TEM CERTEZA que deseja RESTAURAR o backup "${filename}"?\n\nISTO IRÁ SUBSTITUIR TODOS OS DADOS ATUAIS!`)) {
      return;
    }

    try {
      setIsRestoring(true);
      toast.info('Restaurando backup... Isso pode levar alguns minutos.');
      await api.post(`/admin/backup/restore/${backup_id}`);
      toast.success('✅ Backup restaurado com sucesso! Recarregue a página.');
      setTimeout(() => window.location.reload(), 2000);
    } catch (error) {
      console.error('Error restoring backup:', error);
      toast.error('❌ Erro ao restaurar backup: ' + (error.response?.data?.detail || error.message));
    } finally {
      setIsRestoring(false);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Data desconhecida';
    try {
      const date = new Date(dateString);
      return date.toLocaleString('pt-BR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      });
    } catch {
      return dateString;
    }
  };

  const formatSize = (bytes) => {
    if (!bytes) return 'N/A';
    const mb = bytes / (1024 * 1024);
    return mb.toFixed(2) + ' MB';
  };

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold flex items-center gap-3">
            <Save size={28} className="text-purple-600" />
            Sistema de Backup
          </h2>
          <p className="text-gray-600 text-sm mt-1">
            Gerencie backups do MongoDB e restaure dados anteriores
          </p>
        </div>
        <div className="flex gap-2">
          <Button 
            onClick={loadBackups} 
            variant="outline" 
            size="sm"
            disabled={isLoading}
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
            Atualizar
          </Button>
          
          {/* Botão Upload */}
          <Button 
            onClick={() => document.getElementById('backup-upload').click()}
            variant="outline"
            size="sm"
            disabled={isUploading}
          >
            <Upload className="w-4 h-4 mr-2" />
            {isUploading ? 'Enviando...' : 'Enviar Backup'}
          </Button>
          <input
            id="backup-upload"
            type="file"
            accept=".json"
            onChange={handleUploadBackup}
            style={{ display: 'none' }}
          />
          
          <Button 
            onClick={handleCreateBackup}
            disabled={isCreating}
            className="bg-green-600 hover:bg-green-700"
          >
            <Save className="w-4 h-4 mr-2" />
            {isCreating ? 'Criando...' : 'Criar Backup Manual'}
          </Button>
        </div>
      </div>

      {/* Info Card */}
      <Card className="bg-gradient-to-br from-purple-500 to-indigo-600 text-white p-6">
        <div className="space-y-4">
          <div>
            <h3 className="text-lg font-semibold mb-2">🔄 Backup Automático Configurado</h3>
            <p className="text-sm opacity-90">
              O sistema faz backups automáticos do MongoDB diariamente
            </p>
          </div>
          <div className="bg-white/20 rounded-lg p-4 space-y-2">
            <div className="flex items-center gap-2">
              <Clock className="w-4 h-4" />
              <span className="text-sm font-medium">Frequência: Diário (automático via cron)</span>
            </div>
            <div className="flex items-center gap-2">
              <Download className="w-4 h-4" />
              <span className="text-sm font-mono">/opt/iaze/backups/</span>
            </div>
          </div>
        </div>
      </Card>

      {/* Lista de Backups */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">📦 Backups Disponíveis</h3>
        
        {isLoading ? (
          <div className="text-center py-8">
            <RefreshCw className="w-8 h-8 animate-spin mx-auto text-gray-400 mb-2" />
            <p className="text-gray-500">Carregando backups...</p>
          </div>
        ) : backups.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <AlertCircle className="w-12 h-12 mx-auto mb-2 opacity-50" />
            <p>Nenhum backup encontrado</p>
            <p className="text-sm mt-1">Clique em "Criar Backup Manual" para criar o primeiro</p>
          </div>
        ) : (
          <div className="space-y-2">
            {backups.map((backup, idx) => (
              <div 
                key={idx}
                className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50"
              >
                <div className="flex-1">
                  <p className="font-mono text-sm font-medium">{backup.filename}</p>
                  <div className="flex gap-4 mt-1 text-xs text-gray-500">
                    <span>📅 {formatDate(backup.created_at)}</span>
                    <span>💾 {formatSize(backup.size)}</span>
                  </div>
                </div>
                <div className="flex gap-2">
                  <Button
                    onClick={() => handleDownloadBackup(backup)}
                    variant="outline"
                    size="sm"
                    className="border-blue-300 hover:bg-blue-50 text-blue-700"
                  >
                    <Download className="w-4 h-4 mr-2" />
                    Baixar
                  </Button>
                  <Button
                    onClick={() => handleRestoreBackup(backup.filename)}
                    disabled={isRestoring}
                    variant="outline"
                    size="sm"
                    className="border-amber-300 hover:bg-amber-50 text-amber-700"
                  >
                    <Upload className="w-4 h-4 mr-2" />
                    Restaurar
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* Warning */}
      <Card className="bg-yellow-50 border-2 border-yellow-300 p-4">
        <div className="flex gap-3">
          <AlertCircle className="w-5 h-5 text-yellow-700 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-semibold text-yellow-900 mb-1">⚠️ Importante</p>
            <p className="text-sm text-yellow-800">
              <strong>Restaurar um backup IRÁ SUBSTITUIR TODOS OS DADOS ATUAIS</strong> do sistema. 
              Certifique-se de criar um backup atual antes de restaurar um anterior.
              A operação pode levar alguns minutos dependendo do tamanho do banco de dados.
            </p>
          </div>
        </div>
      </Card>
    </div>
  );
}

export default BackupManager;
