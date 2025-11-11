import React, { useState, useEffect } from 'react';
import { X, RefreshCw, AlertTriangle, CheckCircle } from 'lucide-react';

const WhatsAppQRCodeModal = ({ connection, onClose, onRefreshQR, onRestartSession }) => {
  const [step, setStep] = useState(1); // 1 = aviso, 2 = QR Code
  const [activeTab, setActiveTab] = useState('howto'); // 'howto' ou 'recommendations'
  const [isRefreshing, setIsRefreshing] = useState(false);
  // Usar qr_code_base64 se disponível, senão usar qr_code
  const [qrCode, setQrCode] = useState(connection?.qr_code_base64 || connection?.qr_code);

  // Auto-refresh a cada 40 segundos (QR Code expira em 60s)
  useEffect(() => {
    if (step === 2 && connection?.status !== 'connected') {
      const interval = setInterval(async () => {
        console.log('🔄 Auto-refresh QR Code a cada 40s...');
        await handleRefreshQR();
      }, 40000); // 40 segundos - mais tempo para escanear
      
      return () => clearInterval(interval);
    }
  }, [step, connection?.status]);

  // Verificar status da conexão a cada 3 segundos
  useEffect(() => {
    if (step === 2 && connection?.status !== 'connected' && connection?.id) {
      const checkInterval = setInterval(async () => {
        console.log('🔍 Verificando status da conexão via check-status...');
        try {
          const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/whatsapp/connections/${connection.id}/check-status`, {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
          });
          
          if (response.ok) {
            const statusData = await response.json();
            console.log('📊 Status recebido:', statusData);
            
            if (statusData.connected || statusData.status === 'connected') {
              console.log('✅ WhatsApp CONECTADO!');
              alert('✅ WhatsApp conectado com sucesso!');
              onClose(); // Fechar modal
              window.location.reload(); // Recarregar página
            }
          }
        } catch (error) {
          console.error('Erro ao verificar status:', error);
        }
      }, 3000); // 3 segundos
      
      return () => clearInterval(checkInterval);
    }
  }, [step, connection?.id, connection?.status]);

  // Atualizar QR Code quando connection mudar
  useEffect(() => {
    const newQrCode = connection?.qr_code_base64 || connection?.qr_code;
    if (newQrCode) {
      console.log('🔍 Atualizando QR Code no modal:', newQrCode ? 'SIM' : 'NÃO');
      setQrCode(newQrCode);
    }
  }, [connection?.qr_code, connection?.qr_code_base64]);

  const handleRefreshQR = async () => {
    console.log('🔄 handleRefreshQR chamado');
    console.log('🔍 connection:', connection);
    console.log('🔍 connection.id:', connection?.id);
    
    if (!connection?.id) {
      console.error('❌ Connection ID não disponível!');
      alert('Erro: ID da conexão não encontrado. Por favor, feche e abra o QR Code novamente.');
      return;
    }
    
    setIsRefreshing(true);
    try {
      const result = await onRefreshQR(connection.id);
      if (result?.qr_code || result?.qr_code_base64) {
        setQrCode(result.qr_code_base64 || result.qr_code);
      }
    } catch (error) {
      console.error('Erro ao atualizar QR:', error);
    }
    setTimeout(() => setIsRefreshing(false), 1000);
  };

  const handleContinueToQR = () => {
    setStep(2);
  };

  if (!connection) return null;

  // STEP 1: Aviso para desconectar aparelhos
  if (step === 1) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
        <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full p-8 relative animate-fade-in">
          <button
            onClick={onClose}
            className="absolute top-4 right-4 text-gray-400 hover:text-gray-600"
          >
            <X size={24} />
          </button>

          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-green-100 rounded-full mb-4">
              <svg className="w-10 h-10 text-green-600" fill="currentColor" viewBox="0 0 24 24">
                <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.890-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/>
              </svg>
            </div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">WhatsApp Starter</h2>
          </div>

          <div className="bg-yellow-50 border-l-4 border-yellow-400 p-6 mb-6 rounded-r">
            <div className="flex items-start">
              <AlertTriangle className="text-yellow-600 mr-3 flex-shrink-0 mt-1" size={24} />
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  Limpe as sessões no seu aparelho antes de continuar
                </h3>
                <div className="space-y-3 text-gray-700">
                  <p className="font-medium">1. Abra o WhatsApp em seu celular</p>
                  <ul className="ml-4 space-y-2">
                    <li className="flex items-start">
                      <span className="mr-2">•</span>
                      <span><strong>Android:</strong> Toque em Mais informações → Aparelhos conectados</span>
                    </li>
                    <li className="flex items-start">
                      <span className="mr-2">•</span>
                      <span><strong>iPhone:</strong> Toque em Configurações → Aparelhos conectados</span>
                    </li>
                  </ul>
                  <p className="font-medium">2. Toque em um aparelho conectado.</p>
                  <p className="font-medium">3. Toque em DESCONECTAR.</p>
                </div>
              </div>
            </div>
          </div>

          <div className="flex justify-end gap-3">
            <button
              onClick={onClose}
              className="px-6 py-3 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
            >
              Cancelar
            </button>
            <button
              onClick={handleContinueToQR}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
            >
              Já limpei as sessões e quero continuar
            </button>
          </div>
        </div>
      </div>
    );
  }

  // STEP 2: QR Code
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto relative">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-gray-400 hover:text-gray-600 z-10"
        >
          <X size={24} />
        </button>

        <div className="p-8">
          <div className="text-center mb-6">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-green-100 rounded-full mb-4">
              <svg className="w-10 h-10 text-green-600" fill="currentColor" viewBox="0 0 24 24">
                <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.890-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/>
              </svg>
            </div>
            <h2 className="text-2xl font-bold text-gray-900">
              Sincronize a IAZE com o seu WhatsApp!
            </h2>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Instruções */}
            <div>
              <div className="border-b border-gray-200 mb-4">
                <div className="flex gap-4">
                  <button
                    onClick={() => setActiveTab('howto')}
                    className={`pb-3 px-1 border-b-2 transition-colors ${
                      activeTab === 'howto'
                        ? 'border-blue-600 text-blue-600 font-medium'
                        : 'border-transparent text-gray-500 hover:text-gray-700'
                    }`}
                  >
                    Como sincronizar
                  </button>
                  <button
                    onClick={() => setActiveTab('recommendations')}
                    className={`pb-3 px-1 border-b-2 transition-colors ${
                      activeTab === 'recommendations'
                        ? 'border-blue-600 text-blue-600 font-medium'
                        : 'border-transparent text-gray-500 hover:text-gray-700'
                    }`}
                  >
                    Recomendações
                  </button>
                </div>
              </div>

              {activeTab === 'howto' ? (
                <div className="space-y-4 text-gray-700">
                  <p className="font-medium">1. Abra o WhatsApp em seu celular</p>
                  <ul className="ml-4 space-y-2">
                    <li className="flex items-start">
                      <span className="mr-2">•</span>
                      <span><strong>Android:</strong> Toque em Mais informações → ConnectedDevices</span>
                    </li>
                    <li className="flex items-start">
                      <span className="mr-2">•</span>
                      <span><strong>iPhone:</strong> Toque em Configurações → ConnectedDevices</span>
                    </li>
                  </ul>
                  <p className="font-medium">2. Toque em Conectar um aparelho.</p>
                  <p className="font-medium">3. Aponte seu celular para esta tela para capturar o código gerado.</p>
                  
                  <div className="mt-6 pt-6 border-t border-gray-200">
                    <a href="#" className="text-blue-600 hover:underline text-sm flex items-center gap-1">
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                      </svg>
                      Este processo é seguro?
                    </a>
                  </div>
                </div>
              ) : (
                <div className="space-y-4 text-gray-700">
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <p className="font-medium text-blue-900 mb-2">📱 Use um celular exclusivo</p>
                    <p className="text-sm text-blue-800">Recomendamos usar um número de WhatsApp dedicado para atendimento.</p>
                  </div>
                  
                  <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                    <p className="font-medium text-green-900 mb-2">🔔 Mantenha as notificações ativas</p>
                    <p className="text-sm text-green-800">Isso garante que você receberá todas as mensagens em tempo real.</p>
                  </div>
                  
                  <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                    <p className="font-medium text-yellow-900 mb-2">⚡ Conexão estável</p>
                    <p className="text-sm text-yellow-800">Certifique-se de ter uma conexão de internet estável no celular.</p>
                  </div>
                </div>
              )}
            </div>

            {/* QR Code */}
            <div className="flex flex-col items-center">
              {connection.status === 'connected' ? (
                <div className="text-center p-8">
                  <div className="inline-flex items-center justify-center w-20 h-20 bg-green-100 rounded-full mb-4">
                    <CheckCircle className="text-green-600" size={40} />
                  </div>
                  <h3 className="text-xl font-bold text-gray-900 mb-2">
                    ✅ WhatsApp Conectado!
                  </h3>
                  <p className="text-gray-600 mb-4">
                    Seu WhatsApp está sincronizado e pronto para uso.
                  </p>
                  <button
                    onClick={onClose}
                    className="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors font-medium"
                  >
                    Fechar
                  </button>
                </div>
              ) : (
                <>
                  <div className="bg-white border-2 border-gray-200 rounded-lg p-6 mb-4 relative">
                    {isRefreshing && (
                      <div className="absolute inset-0 bg-white bg-opacity-75 flex items-center justify-center rounded-lg">
                        <RefreshCw className="animate-spin text-blue-600" size={40} />
                      </div>
                    )}
                    {qrCode ? (
                      <img
                        src={qrCode}
                        alt="QR Code WhatsApp"
                        className="w-64 h-64 object-contain"
                      />
                    ) : (
                      <div className="w-64 h-64 flex items-center justify-center bg-gray-100 rounded">
                        <RefreshCw className="animate-spin text-gray-400" size={40} />
                      </div>
                    )}
                  </div>

                  <a href="#" className="text-blue-600 hover:underline text-sm mb-6 flex items-center gap-1">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                    </svg>
                    Por que o código muda?
                  </a>

                  <p className="text-sm text-gray-500 mb-6 text-center">
                    ⏱️ QR Code válido por 60 segundos. Será renovado automaticamente a cada 40s.
                  </p>
                </>
              )}
            </div>
          </div>

          {/* Footer com botões */}
          {connection.status !== 'connected' && (
            <div className="mt-8 pt-6 border-t border-gray-200 flex flex-col sm:flex-row justify-between items-center gap-4">
              <p className="text-sm text-gray-600">
                Problema com a conexão? <a href="#" className="text-blue-600 hover:underline">Estamos online</a>
              </p>
              
              <div className="flex gap-3">
                <button
                  onClick={() => onRestartSession(connection.id)}
                  className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
                >
                  Reiniciar sessão
                </button>
                <button
                  onClick={handleRefreshQR}
                  disabled={isRefreshing}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2 disabled:opacity-50"
                >
                  <RefreshCw size={16} className={isRefreshing ? 'animate-spin' : ''} />
                  Gerar um novo QR Code
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default WhatsAppQRCodeModal;
