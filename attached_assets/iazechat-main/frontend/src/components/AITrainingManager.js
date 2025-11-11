import React, { useState, useEffect } from 'react';
import { Mic, Upload, Trash2, Loader2, Play, Pause, Volume2 } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';

function AITrainingManager({ agentId }) {
  const [knowledgeList, setKnowledgeList] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(0);

  useEffect(() => {
    if (agentId) {
      loadKnowledge();
    }
  }, [agentId]);

  const loadKnowledge = async () => {
    try {
      setIsLoading(true);
      const response = await fetch(`${BACKEND_URL}/api/media/training-knowledge?agent_id=${agentId}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (!response.ok) throw new Error('Erro ao carregar conhecimentos');

      const data = await response.json();
      setKnowledgeList(data.data.items || []);
    } catch (error) {
      console.error('Erro ao carregar conhecimentos:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (!file) return;

    // Validar tipo de arquivo
    const validTypes = ['audio/mpeg', 'audio/wav', 'audio/m4a', 'audio/ogg', 'audio/webm'];
    if (!validTypes.includes(file.type) && !file.name.match(/\.(mp3|wav|m4a|ogg|webm)$/i)) {
      alert('Formato não suportado. Use: MP3, WAV, M4A, OGG, WEBM');
      return;
    }

    // Validar tamanho (25MB)
    if (file.size > 25 * 1024 * 1024) {
      alert('Arquivo muito grande. Máximo: 25MB');
      return;
    }

    setSelectedFile(file);
  };

  const uploadAudio = async () => {
    if (!selectedFile) return;

    try {
      setIsUploading(true);
      setUploadProgress(0);

      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('language', 'pt');
      formData.append('save_as_training', 'true');
      formData.append('agent_id', agentId);

      const response = await fetch(`${BACKEND_URL}/api/media/transcribe-audio`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: formData
      });

      if (!response.ok) throw new Error('Erro ao fazer upload');

      const data = await response.json();
      
      alert('Áudio transcrito e salvo com sucesso! A IA agora tem esse conhecimento.');
      setSelectedFile(null);
      loadKnowledge();

    } catch (error) {
      console.error('Erro ao fazer upload:', error);
      alert('Erro ao processar áudio. Tente novamente.');
    } finally {
      setIsUploading(false);
      setUploadProgress(0);
    }
  };

  const deleteKnowledge = async (id) => {
    if (!window.confirm('Deseja remover este conhecimento?')) return;

    try {
      const response = await fetch(`${BACKEND_URL}/api/media/training-knowledge/${id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (!response.ok) throw new Error('Erro ao deletar');

      alert('Conhecimento removido com sucesso!');
      loadKnowledge();

    } catch (error) {
      console.error('Erro ao deletar:', error);
      alert('Erro ao remover conhecimento.');
    }
  };

  return (
    <div style={{ padding: '20px' }}>
      <div style={{ marginBottom: '30px' }}>
        <h2 style={{ fontSize: '24px', fontWeight: '600', marginBottom: '8px' }}>
          🎤 Treinamento da IA por Áudio
        </h2>
        <p style={{ color: '#666', fontSize: '14px' }}>
          Grave áudios explicando processos, informações do servidor ou qualquer conhecimento que a IA deve ter.
          O sistema transcreve automaticamente e salva na base de conhecimento.
        </p>
      </div>

      {/* Upload Area */}
      <div style={{
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        borderRadius: '12px',
        padding: '24px',
        marginBottom: '30px',
        color: 'white'
      }}>
        <div style={{ marginBottom: '20px' }}>
          <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '8px' }}>
            Adicionar Novo Conhecimento
          </h3>
          <p style={{ fontSize: '14px', opacity: 0.9 }}>
            Envie um áudio com informações importantes que a IA deve aprender
          </p>
        </div>

        {selectedFile ? (
          <div style={{
            background: 'rgba(255,255,255,0.2)',
            borderRadius: '8px',
            padding: '16px',
            marginBottom: '16px'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '12px' }}>
              <Mic size={24} />
              <div style={{ flex: 1 }}>
                <p style={{ fontWeight: '600', marginBottom: '4px' }}>{selectedFile.name}</p>
                <p style={{ fontSize: '12px', opacity: 0.8 }}>
                  {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                </p>
              </div>
              <button
                onClick={() => setSelectedFile(null)}
                style={{
                  background: 'rgba(255,255,255,0.2)',
                  border: 'none',
                  borderRadius: '50%',
                  width: '32px',
                  height: '32px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  cursor: 'pointer',
                  color: 'white'
                }}
              >
                <Trash2 size={16} />
              </button>
            </div>

            <button
              onClick={uploadAudio}
              disabled={isUploading}
              style={{
                background: 'white',
                color: '#667eea',
                border: 'none',
                borderRadius: '8px',
                padding: '12px 24px',
                fontWeight: '600',
                cursor: isUploading ? 'not-allowed' : 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                width: '100%',
                justifyContent: 'center',
                opacity: isUploading ? 0.7 : 1
              }}
            >
              {isUploading ? (
                <>
                  <Loader2 size={20} style={{ animation: 'spin 1s linear infinite' }} />
                  Processando áudio...
                </>
              ) : (
                <>
                  <Upload size={20} />
                  Transcrever e Salvar
                </>
              )}
            </button>
          </div>
        ) : (
          <label style={{
            background: 'rgba(255,255,255,0.2)',
            border: '2px dashed rgba(255,255,255,0.5)',
            borderRadius: '8px',
            padding: '32px',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: '12px',
            cursor: 'pointer',
            transition: 'all 0.3s'
          }}
          onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(255,255,255,0.3)'}
          onMouseLeave={(e) => e.currentTarget.style.background = 'rgba(255,255,255,0.2)'}
          >
            <Mic size={48} />
            <div style={{ textAlign: 'center' }}>
              <p style={{ fontWeight: '600', marginBottom: '4px' }}>
                Clique para selecionar áudio
              </p>
              <p style={{ fontSize: '12px', opacity: 0.8 }}>
                MP3, WAV, M4A, OGG, WEBM (máx. 25MB)
              </p>
            </div>
            <input
              type="file"
              accept="audio/*"
              onChange={handleFileSelect}
              style={{ display: 'none' }}
            />
          </label>
        )}
      </div>

      {/* Lista de Conhecimentos */}
      <div>
        <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '16px' }}>
          Conhecimentos Salvos ({knowledgeList.length})
        </h3>

        {isLoading ? (
          <div style={{ textAlign: 'center', padding: '40px' }}>
            <Loader2 size={32} style={{ animation: 'spin 1s linear infinite' }} />
          </div>
        ) : knowledgeList.length === 0 ? (
          <div style={{
            textAlign: 'center',
            padding: '40px',
            background: '#f5f5f5',
            borderRadius: '8px',
            color: '#666'
          }}>
            <Mic size={48} style={{ margin: '0 auto 16px', opacity: 0.5 }} />
            <p>Nenhum conhecimento adicionado ainda</p>
            <p style={{ fontSize: '14px', marginTop: '8px' }}>
              Faça upload de áudios para treinar a IA
            </p>
          </div>
        ) : (
          <div style={{ display: 'grid', gap: '12px' }}>
            {knowledgeList.map((knowledge, index) => (
              <div
                key={knowledge._id}
                style={{
                  background: 'white',
                  border: '1px solid #e0e0e0',
                  borderRadius: '8px',
                  padding: '16px',
                  display: 'flex',
                  gap: '16px',
                  alignItems: 'start'
                }}
              >
                <div style={{
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  borderRadius: '8px',
                  width: '40px',
                  height: '40px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: 'white',
                  flexShrink: 0
                }}>
                  <Mic size={20} />
                </div>

                <div style={{ flex: 1 }}>
                  <p style={{
                    fontSize: '12px',
                    color: '#999',
                    marginBottom: '8px'
                  }}>
                    Adicionado em: {new Date(knowledge.created_at).toLocaleDateString('pt-BR')}
                  </p>
                  <p style={{
                    fontSize: '14px',
                    lineHeight: '1.6',
                    color: '#333'
                  }}>
                    {knowledge.content.length > 200 
                      ? knowledge.content.substring(0, 200) + '...' 
                      : knowledge.content}
                  </p>
                </div>

                <button
                  onClick={() => deleteKnowledge(knowledge._id)}
                  style={{
                    background: '#fee',
                    border: '1px solid #fcc',
                    borderRadius: '6px',
                    padding: '8px',
                    cursor: 'pointer',
                    color: '#c00',
                    transition: 'all 0.2s'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.background = '#fdd';
                    e.currentTarget.style.transform = 'scale(1.05)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.background = '#fee';
                    e.currentTarget.style.transform = 'scale(1)';
                  }}
                  title="Remover conhecimento"
                >
                  <Trash2 size={18} />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}

export default AITrainingManager;
