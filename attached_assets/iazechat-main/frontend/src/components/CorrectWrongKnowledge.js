import React, { useState, useEffect } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';

const CorrectWrongKnowledge = () => {
  const [entries, setEntries] = useState([]);
  const [config, setConfig] = useState({
    default_correct_template: "✅ **Opções Corretas:**\n{options}",
    default_wrong_template: "⚠️ **Alternativas (usar apenas se as corretas não funcionarem):**\n{options}",
    use_numbered_menu: true
  });
  const [showModal, setShowModal] = useState(false);
  const [editingEntry, setEditingEntry] = useState(null);
  const [formData, setFormData] = useState({
    question: '',
    correct_options: [''],
    wrong_options: [''],
    correct_template: '',
    wrong_template: ''
  });
  const [uploadFile, setUploadFile] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadEntries();
    loadConfig();
  }, []);

  const loadEntries = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(
        `${BACKEND_URL}/api/admin/vendas-bot/knowledge/correct-wrong`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setEntries(response.data);
    } catch (error) {
      console.error('Erro ao carregar entradas:', error);
    }
  };

  const loadConfig = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(
        `${BACKEND_URL}/api/admin/vendas-bot/knowledge/correct-wrong/config`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setConfig(response.data);
    } catch (error) {
      console.error('Erro ao carregar config:', error);
    }
  };

  const handleAddCorrectOption = () => {
    setFormData({
      ...formData,
      correct_options: [...formData.correct_options, '']
    });
  };

  const handleAddWrongOption = () => {
    setFormData({
      ...formData,
      wrong_options: [...formData.wrong_options, '']
    });
  };

  const handleCorrectOptionChange = (index, value) => {
    const newOptions = [...formData.correct_options];
    newOptions[index] = value;
    setFormData({ ...formData, correct_options: newOptions });
  };

  const handleWrongOptionChange = (index, value) => {
    const newOptions = [...formData.wrong_options];
    newOptions[index] = value;
    setFormData({ ...formData, wrong_options: newOptions });
  };

  const handleRemoveCorrectOption = (index) => {
    const newOptions = formData.correct_options.filter((_, i) => i !== index);
    setFormData({ ...formData, correct_options: newOptions.length ? newOptions : [''] });
  };

  const handleRemoveWrongOption = (index) => {
    const newOptions = formData.wrong_options.filter((_, i) => i !== index);
    setFormData({ ...formData, wrong_options: newOptions.length ? newOptions : [''] });
  };

  const handleOpenModal = (entry = null) => {
    if (entry) {
      setEditingEntry(entry);
      setFormData({
        question: entry.question,
        correct_options: entry.correct_options.length ? entry.correct_options : [''],
        wrong_options: entry.wrong_options.length ? entry.wrong_options : [''],
        correct_template: entry.correct_template,
        wrong_template: entry.wrong_template
      });
    } else {
      setEditingEntry(null);
      setFormData({
        question: '',
        correct_options: [''],
        wrong_options: [''],
        correct_template: config.default_correct_template,
        wrong_template: config.default_wrong_template
      });
    }
    setShowModal(true);
  };

  const handleCloseModal = () => {
    setShowModal(false);
    setEditingEntry(null);
    setFormData({
      question: '',
      correct_options: [''],
      wrong_options: [''],
      correct_template: '',
      wrong_template: ''
    });
  };

  const handleSave = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      // Filtrar opções vazias
      const cleanData = {
        ...formData,
        correct_options: formData.correct_options.filter(opt => opt.trim()),
        wrong_options: formData.wrong_options.filter(opt => opt.trim())
      };

      if (editingEntry) {
        await axios.put(
          `${BACKEND_URL}/api/admin/vendas-bot/knowledge/correct-wrong/${editingEntry.id}`,
          cleanData,
          { headers: { Authorization: `Bearer ${token}` } }
        );
        alert('✅ Entrada atualizada com sucesso!');
      } else {
        await axios.post(
          `${BACKEND_URL}/api/admin/vendas-bot/knowledge/correct-wrong`,
          cleanData,
          { headers: { Authorization: `Bearer ${token}` } }
        );
        alert('✅ Entrada criada com sucesso!');
      }

      handleCloseModal();
      loadEntries();
    } catch (error) {
      console.error('Erro ao salvar:', error);
      alert('❌ Erro ao salvar entrada');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Tem certeza que deseja deletar esta entrada?')) {
      return;
    }

    try {
      const token = localStorage.getItem('token');
      await axios.delete(
        `${BACKEND_URL}/api/admin/vendas-bot/knowledge/correct-wrong/${id}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      alert('✅ Entrada deletada!');
      loadEntries();
    } catch (error) {
      console.error('Erro ao deletar:', error);
      alert('❌ Erro ao deletar entrada');
    }
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!uploadFile) {
      alert('Selecione um arquivo TXT');
      return;
    }

    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const formData = new FormData();
      formData.append('file', uploadFile);

      const response = await axios.post(
        `${BACKEND_URL}/api/admin/vendas-bot/knowledge/correct-wrong/upload`,
        formData,
        {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'multipart/form-data'
          }
        }
      );

      alert(`✅ ${response.data.message}`);
      setUploadFile(null);
      loadEntries();
    } catch (error) {
      console.error('Erro ao fazer upload:', error);
      alert('❌ Erro ao processar arquivo');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveConfig = async () => {
    try {
      const token = localStorage.getItem('token');
      await axios.put(
        `${BACKEND_URL}/api/admin/vendas-bot/knowledge/correct-wrong/config`,
        config,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      alert('✅ Templates salvos!');
    } catch (error) {
      console.error('Erro ao salvar config:', error);
      alert('❌ Erro ao salvar templates');
    }
  };

  return (
    <div style={{ padding: '20px' }}>
      <h2>📚 Base de Conhecimento - CERTO | ERRADO</h2>
      <p style={{ color: '#666', marginBottom: '20px' }}>
        Configure respostas corretas e erradas para perguntas específicas. A IA sempre enviará as opções CERTAS primeiro.
      </p>

      {/* Templates Globais */}
      <div style={{ background: '#f5f5f5', padding: '15px', borderRadius: '8px', marginBottom: '20px' }}>
        <h3>🎨 Templates de Mensagem</h3>
        <div style={{ marginBottom: '15px' }}>
          <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
            Template CERTO:
          </label>
          <textarea
            value={config.default_correct_template}
            onChange={(e) => setConfig({ ...config, default_correct_template: e.target.value })}
            style={{ width: '100%', padding: '10px', borderRadius: '4px', border: '1px solid #ddd', minHeight: '60px' }}
            placeholder="Use {options} onde as opções devem aparecer"
          />
          <small style={{ color: '#666' }}>Use <code>{'{options}'}</code> onde as opções devem aparecer</small>
        </div>

        <div style={{ marginBottom: '15px' }}>
          <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
            Template ERRADO:
          </label>
          <textarea
            value={config.default_wrong_template}
            onChange={(e) => setConfig({ ...config, default_wrong_template: e.target.value })}
            style={{ width: '100%', padding: '10px', borderRadius: '4px', border: '1px solid #ddd', minHeight: '60px' }}
            placeholder="Use {options} onde as opções devem aparecer"
          />
          <small style={{ color: '#666' }}>Use <code>{'{options}'}</code> onde as opções devem aparecer</small>
        </div>

        <button
          onClick={handleSaveConfig}
          style={{
            padding: '10px 20px',
            background: '#4CAF50',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer'
          }}
        >
          💾 Salvar Templates
        </button>
      </div>

      {/* Upload e Adicionar */}
      <div style={{ display: 'flex', gap: '10px', marginBottom: '20px', flexWrap: 'wrap' }}>
        <button
          onClick={() => handleOpenModal()}
          style={{
            padding: '12px 24px',
            background: '#2196F3',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
            fontWeight: 'bold'
          }}
        >
          ➕ Adicionar Novo
        </button>

        <form onSubmit={handleUpload} style={{ display: 'flex', gap: '10px' }}>
          <input
            type="file"
            accept=".txt"
            onChange={(e) => setUploadFile(e.target.files[0])}
            style={{ padding: '10px' }}
          />
          <button
            type="submit"
            disabled={!uploadFile || loading}
            style={{
              padding: '12px 24px',
              background: uploadFile ? '#FF9800' : '#ccc',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: uploadFile ? 'pointer' : 'not-allowed',
              fontWeight: 'bold'
            }}
          >
            📤 Upload TXT
          </button>
        </form>
      </div>

      {/* Formato do arquivo */}
      <details style={{ marginBottom: '20px', background: '#fff3cd', padding: '15px', borderRadius: '8px' }}>
        <summary style={{ cursor: 'pointer', fontWeight: 'bold' }}>
          📋 Formato do arquivo TXT
        </summary>
        <pre style={{ background: '#f8f9fa', padding: '10px', borderRadius: '4px', marginTop: '10px', fontSize: '12px' }}>
{`PERGUNTA: qual o app para smart tv?
CERTO:
ASSIST PLUS
XCLOUD
HD PLAYER
ERRADO:
CYBERXC
SITE PC
---
PERGUNTA: qual aplicativo para tv box?
CERTO:
FLEX PLAY
BRASIL IPTV
ERRADO:
CYBERV3
CYBERV4
---`}
        </pre>
      </details>

      {/* Lista de Entradas */}
      <div>
        <h3>📝 Entradas Cadastradas ({entries.length})</h3>
        {entries.length === 0 ? (
          <p style={{ color: '#999', textAlign: 'center', padding: '40px' }}>
            Nenhuma entrada cadastrada ainda. Clique em "Adicionar Novo" ou faça upload de um arquivo TXT.
          </p>
        ) : (
          <div style={{ display: 'grid', gap: '15px' }}>
            {entries.map((entry) => (
              <div
                key={entry.id}
                style={{
                  background: 'white',
                  border: '1px solid #ddd',
                  borderRadius: '8px',
                  padding: '15px',
                  cursor: 'pointer',
                  transition: 'all 0.2s'
                }}
                onMouseEnter={(e) => e.currentTarget.style.boxShadow = '0 2px 8px rgba(0,0,0,0.1)'}
                onMouseLeave={(e) => e.currentTarget.style.boxShadow = 'none'}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                  <div style={{ flex: 1 }} onClick={() => handleOpenModal(entry)}>
                    <h4 style={{ margin: '0 0 10px 0', color: '#333' }}>
                      ❓ {entry.question}
                    </h4>
                    
                    {entry.correct_options && entry.correct_options.length > 0 && (
                      <div style={{ marginBottom: '10px' }}>
                        <strong style={{ color: '#4CAF50' }}>✅ CERTO:</strong>
                        <div style={{ marginLeft: '20px', marginTop: '5px' }}>
                          {entry.correct_options.map((opt, idx) => (
                            <div key={idx} style={{ color: '#666' }}>• {opt}</div>
                          ))}
                        </div>
                      </div>
                    )}

                    {entry.wrong_options && entry.wrong_options.length > 0 && (
                      <div>
                        <strong style={{ color: '#f44336' }}>❌ ERRADO:</strong>
                        <div style={{ marginLeft: '20px', marginTop: '5px' }}>
                          {entry.wrong_options.map((opt, idx) => (
                            <div key={idx} style={{ color: '#999' }}>• {opt}</div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>

                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDelete(entry.id);
                    }}
                    style={{
                      padding: '8px 16px',
                      background: '#f44336',
                      color: 'white',
                      border: 'none',
                      borderRadius: '4px',
                      cursor: 'pointer',
                      marginLeft: '10px'
                    }}
                  >
                    🗑️ Deletar
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Modal de Edição/Criação */}
      {showModal && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(0,0,0,0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 9999,
            padding: '20px'
          }}
          onClick={handleCloseModal}
        >
          <div
            style={{
              background: 'white',
              borderRadius: '8px',
              padding: '30px',
              maxWidth: '800px',
              width: '100%',
              maxHeight: '90vh',
              overflow: 'auto'
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <h3 style={{ marginTop: 0 }}>
              {editingEntry ? '✏️ Editar Entrada' : '➕ Nova Entrada'}
            </h3>

            {/* Pergunta */}
            <div style={{ marginBottom: '20px' }}>
              <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                ❓ Pergunta:
              </label>
              <input
                type="text"
                value={formData.question}
                onChange={(e) => setFormData({ ...formData, question: e.target.value })}
                placeholder="Ex: qual o app para smart tv?"
                style={{ width: '100%', padding: '10px', borderRadius: '4px', border: '1px solid #ddd' }}
              />
            </div>

            {/* Opções CERTAS */}
            <div style={{ marginBottom: '20px' }}>
              <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold', color: '#4CAF50' }}>
                ✅ Opções CERTAS:
              </label>
              {formData.correct_options.map((option, index) => (
                <div key={index} style={{ display: 'flex', gap: '5px', marginBottom: '5px' }}>
                  <input
                    type="text"
                    value={option}
                    onChange={(e) => handleCorrectOptionChange(index, e.target.value)}
                    placeholder={`Opção ${index + 1}`}
                    style={{ flex: 1, padding: '8px', borderRadius: '4px', border: '1px solid #ddd' }}
                  />
                  <button
                    onClick={() => handleRemoveCorrectOption(index)}
                    style={{
                      padding: '8px 12px',
                      background: '#f44336',
                      color: 'white',
                      border: 'none',
                      borderRadius: '4px',
                      cursor: 'pointer'
                    }}
                  >
                    ✖
                  </button>
                </div>
              ))}
              <button
                onClick={handleAddCorrectOption}
                style={{
                  padding: '8px 16px',
                  background: '#4CAF50',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  marginTop: '5px'
                }}
              >
                ➕ Adicionar Opção CERTA
              </button>
            </div>

            {/* Opções ERRADAS */}
            <div style={{ marginBottom: '20px' }}>
              <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold', color: '#f44336' }}>
                ❌ Opções ERRADAS:
              </label>
              {formData.wrong_options.map((option, index) => (
                <div key={index} style={{ display: 'flex', gap: '5px', marginBottom: '5px' }}>
                  <input
                    type="text"
                    value={option}
                    onChange={(e) => handleWrongOptionChange(index, e.target.value)}
                    placeholder={`Opção ${index + 1}`}
                    style={{ flex: 1, padding: '8px', borderRadius: '4px', border: '1px solid #ddd' }}
                  />
                  <button
                    onClick={() => handleRemoveWrongOption(index)}
                    style={{
                      padding: '8px 12px',
                      background: '#f44336',
                      color: 'white',
                      border: 'none',
                      borderRadius: '4px',
                      cursor: 'pointer'
                    }}
                  >
                    ✖
                  </button>
                </div>
              ))}
              <button
                onClick={handleAddWrongOption}
                style={{
                  padding: '8px 16px',
                  background: '#FF9800',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  marginTop: '5px'
                }}
              >
                ➕ Adicionar Opção ERRADA
              </button>
            </div>

            {/* Templates */}
            <div style={{ marginBottom: '20px' }}>
              <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                Template CERTO (deixe vazio para usar o padrão):
              </label>
              <textarea
                value={formData.correct_template}
                onChange={(e) => setFormData({ ...formData, correct_template: e.target.value })}
                placeholder={config.default_correct_template}
                style={{ width: '100%', padding: '10px', borderRadius: '4px', border: '1px solid #ddd', minHeight: '60px' }}
              />
            </div>

            <div style={{ marginBottom: '20px' }}>
              <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                Template ERRADO (deixe vazio para usar o padrão):
              </label>
              <textarea
                value={formData.wrong_template}
                onChange={(e) => setFormData({ ...formData, wrong_template: e.target.value })}
                placeholder={config.default_wrong_template}
                style={{ width: '100%', padding: '10px', borderRadius: '4px', border: '1px solid #ddd', minHeight: '60px' }}
              />
            </div>

            {/* Botões */}
            <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
              <button
                onClick={handleCloseModal}
                style={{
                  padding: '10px 20px',
                  background: '#999',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer'
                }}
              >
                Cancelar
              </button>
              <button
                onClick={handleSave}
                disabled={loading || !formData.question}
                style={{
                  padding: '10px 20px',
                  background: formData.question ? '#2196F3' : '#ccc',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: formData.question ? 'pointer' : 'not-allowed'
                }}
              >
                {loading ? '⏳ Salvando...' : '💾 Salvar'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CorrectWrongKnowledge;
