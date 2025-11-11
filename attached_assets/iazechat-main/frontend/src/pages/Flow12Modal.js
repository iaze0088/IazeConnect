import React, { useState } from 'react';
import './Flow12Modal.css';

const Flow12Modal = ({ isOpen, onClose, onSubmit }) => {
  const [whatsapp, setWhatsapp] = useState('');
  const [password, setPassword] = useState('');
  const [errors, setErrors] = useState({});
  const [isLoading, setIsLoading] = useState(false);

  if (!isOpen) return null;

  const validateWhatsapp = (value) => {
    const clean = value.replace(/\D/g, '');
    if (clean.length < 10 || clean.length > 11) {
      return 'WhatsApp deve ter 10 ou 11 dígitos com DDD';
    }
    return null;
  };

  const validatePassword = (value) => {
    if (value.length !== 2) {
      return 'Senha deve ter exatamente 2 dígitos';
    }
    if (!/^\d+$/.test(value)) {
      return 'Senha deve conter apenas números';
    }
    return null;
  };

  const handleWhatsappChange = (e) => {
    const value = e.target.value.replace(/\D/g, '');
    if (value.length <= 11) {
      setWhatsapp(value);
      if (errors.whatsapp) {
        setErrors({ ...errors, whatsapp: null });
      }
    }
  };

  const handlePasswordChange = (e) => {
    const value = e.target.value.replace(/\D/g, '');
    if (value.length <= 2) {
      setPassword(value);
      if (errors.password) {
        setErrors({ ...errors, password: null });
      }
    }
  };

  const handleSubmit = async () => {
    // Validar
    const whatsappError = validateWhatsapp(whatsapp);
    const passwordError = validatePassword(password);

    if (whatsappError || passwordError) {
      setErrors({
        whatsapp: whatsappError,
        password: passwordError
      });
      return;
    }

    // Enviar
    setIsLoading(true);
    try {
      await onSubmit({ whatsapp, password });
    } catch (error) {
      console.error('Erro ao enviar:', error);
      setErrors({ submit: 'Erro ao processar. Tente novamente.' });
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !isLoading) {
      handleSubmit();
    }
  };

  return (
    <div className="flow12-modal-overlay" onClick={onClose}>
      <div className="flow12-modal" onClick={(e) => e.stopPropagation()}>
        <div className="flow12-modal-header">
          <div className="flow12-modal-icon">🎁</div>
          <h2 className="flow12-modal-title">Criar Teste Grátis</h2>
          <p className="flow12-modal-subtitle">
            Preencha seus dados para gerar suas credenciais de teste
          </p>
        </div>

        <div className="flow12-modal-body">
          <div className="flow12-form-group">
            <label className="flow12-form-label">
              📱 WhatsApp <span className="required">*</span>
            </label>
            <input
              type="tel"
              className="flow12-form-input"
              placeholder="11999999999"
              value={whatsapp}
              onChange={handleWhatsappChange}
              onKeyPress={handleKeyPress}
              autoFocus
            />
            {errors.whatsapp ? (
              <span className="flow12-form-error">{errors.whatsapp}</span>
            ) : (
              <span className="flow12-form-hint">Digite com DDD (ex: 11999999999)</span>
            )}
          </div>

          <div className="flow12-form-group">
            <label className="flow12-form-label">
              🔐 Senha de 2 dígitos <span className="required">*</span>
            </label>
            <input
              type="tel"
              className="flow12-form-input"
              placeholder="99"
              value={password}
              onChange={handlePasswordChange}
              onKeyPress={handleKeyPress}
              maxLength={2}
            />
            {errors.password ? (
              <span className="flow12-form-error">{errors.password}</span>
            ) : (
              <span className="flow12-form-hint">Crie uma senha fácil de lembrar (ex: 12, 99)</span>
            )}
          </div>

          {errors.submit && (
            <div className="flow12-form-error" style={{ textAlign: 'center', marginTop: '16px' }}>
              {errors.submit}
            </div>
          )}
        </div>

        <div className="flow12-modal-footer">
          <button
            className="flow12-btn flow12-btn-secondary"
            onClick={onClose}
            disabled={isLoading}
          >
            Cancelar
          </button>
          <button
            className="flow12-btn flow12-btn-primary"
            onClick={handleSubmit}
            disabled={isLoading || !whatsapp || !password}
          >
            {isLoading ? <span className="flow12-loading"></span> : '✅ Criar Teste'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default Flow12Modal;
