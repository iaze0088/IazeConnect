import React, { useState, useEffect } from 'react';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog';
import { Check, X, Crown, Zap, Rocket, Star, Infinity, Copy, QrCode as QrCodeIcon } from 'lucide-react';
import { QRCodeSVG } from 'qrcode.react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';

const SubscriptionPayments = () => {
  const [subscriptionData, setSubscriptionData] = useState(null);
  const [plans, setPlans] = useState({});
  const [loading, setLoading] = useState(true);
  const [selectedPlan, setSelectedPlan] = useState(null);
  const [paymentData, setPaymentData] = useState(null);
  const [showQRCode, setShowQRCode] = useState(false);
  const [copying, setCopying] = useState(false);
  const [processing, setProcessing] = useState(false);

  useEffect(() => {
    fetchSubscriptionData();
    fetchPlans();
  }, []);

  const fetchSubscriptionData = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/subscription/status`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        setSubscriptionData(data);
      }
    } catch (error) {
      console.error('Error fetching subscription:', error);
    }
  };

  const fetchPlans = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/subscription/plans`);
      
      if (response.ok) {
        const data = await response.json();
        setPlans(data.plans);
      }
    } catch (error) {
      console.error('Error fetching plans:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectPlan = (planType) => {
    setSelectedPlan(planType);
  };

  const handlePayWithPix = async () => {
    if (!selectedPlan) return;

    setProcessing(true);

    try {
      const token = localStorage.getItem('token');
      
      // CORREÇÃO: O auth.js salva como 'user_data', não 'user'
      const userStr = localStorage.getItem('user_data');
      const user = userStr ? JSON.parse(userStr) : {};

      console.log('🔍 [PAYMENT] Dados do usuário:', user);
      console.log('🔍 [PAYMENT] Plano selecionado:', selectedPlan);

      // Buscar reseller_id de múltiplas fontes possíveis
      const resellerId = user.reseller_id || user.id;
      console.log('🔍 [PAYMENT] Reseller ID encontrado:', resellerId);

      if (!resellerId) {
        console.error('❌ [PAYMENT] Reseller ID não encontrado no localStorage!');
        console.error('❌ [PAYMENT] Dados disponíveis:', Object.keys(user));
        console.error('❌ [PAYMENT] Conteúdo completo:', user);
        alert('Erro: ID da revenda não encontrado. Faça logout e login novamente.');
        setProcessing(false);
        return;
      }

      const requestBody = {
        plan_type: selectedPlan,
        reseller_id: resellerId,
        customer_name: user.name || 'Cliente',
        customer_email: user.email || 'cliente@email.com'
      };

      console.log('📤 [PAYMENT] Enviando requisição:', requestBody);

      const response = await fetch(`${BACKEND_URL}/api/payment/create`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(requestBody)
      });

      console.log('📥 [PAYMENT] Status da resposta:', response.status);

      if (response.ok) {
        const data = await response.json();
        console.log('✅ [PAYMENT] Pagamento criado:', data);
        setPaymentData(data);
        setShowQRCode(true);
      } else {
        const error = await response.json();
        console.error('❌ [PAYMENT] Erro na resposta:', error);
        
        if (response.status === 503 && error.detail?.includes('Mercado Pago não configurado')) {
          alert('⚠️ Sistema de Pagamento não configurado!\n\nO administrador ainda não configurou o Mercado Pago.\n\nEntre em contato com o suporte para ativar os pagamentos.');
        } else {
          alert(`Erro ao criar pagamento: ${error.detail || 'Erro desconhecido'}`);
        }
      }
    } catch (error) {
      console.error('❌ [PAYMENT] Erro crítico:', error);
      alert('Erro ao criar pagamento. Tente novamente.');
    } finally {
      setProcessing(false);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    setCopying(true);
    setTimeout(() => setCopying(false), 2000);
  };

  const getPlanIcon = (planType) => {
    const icons = {
      basico: Crown,
      plus: Zap,
      pro: Rocket,
      premium: Star,
      enterprise: Infinity
    };
    return icons[planType] || Crown;
  };

  const getPlanColor = (planType) => {
    const colors = {
      basico: 'from-blue-500 to-blue-600',
      plus: 'from-purple-500 to-purple-600',
      pro: 'from-orange-500 to-orange-600',
      premium: 'from-pink-500 to-pink-600',
      enterprise: 'from-green-500 to-green-600'
    };
    return colors[planType] || 'from-gray-500 to-gray-600';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  const currentPlan = subscriptionData?.subscription?.plan_type || 'basico';
  const bonusBalance = subscriptionData?.bonus_balance || 0;
  const daysLeft = subscriptionData?.days_left || 0;
  const status = subscriptionData?.subscription?.status || 'trial';

  return (
    <div className="space-y-6">
      {/* Header com Status */}
      <Card className="p-6 bg-gradient-to-r from-blue-600 to-purple-600 text-white">
        <div className="flex justify-between items-center">
          <div>
            <h2 className="text-2xl font-bold mb-2">Minha Assinatura</h2>
            <p className="text-blue-100">
              Plano Atual: <span className="font-bold">{plans[currentPlan]?.name || 'Básico'}</span>
            </p>
            <p className="text-blue-100">
              Status: <span className="font-bold capitalize">{status === 'trial' ? 'Trial Grátis' : status === 'active' ? 'Ativo' : 'Expirado'}</span>
            </p>
          </div>
          <div className="text-right">
            <p className="text-sm text-blue-100">Dias Restantes</p>
            <p className="text-4xl font-bold">{daysLeft}</p>
          </div>
        </div>
      </Card>

      {/* Bônus Disponível */}
      {bonusBalance > 0 && (
        <Card className="p-4 bg-gradient-to-r from-green-50 to-emerald-50 border-green-200">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-full bg-green-500 flex items-center justify-center">
              <Star className="w-6 h-6 text-white" />
            </div>
            <div>
              <p className="text-sm text-green-700 font-medium">BÔNUS DISPONÍVEL</p>
              <p className="text-2xl font-bold text-green-900">R$ {bonusBalance.toFixed(2)}</p>
              <p className="text-xs text-green-600">Será usado automaticamente como desconto</p>
            </div>
          </div>
        </Card>
      )}

      {/* Planos Disponíveis */}
      <div>
        <h3 className="text-xl font-bold mb-4">Escolha seu Plano</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Object.entries(plans).map(([planType, plan]) => {
            const Icon = getPlanIcon(planType);
            const isCurrentPlan = currentPlan === planType;
            const isSelected = selectedPlan === planType;
            
            return (
              <Card
                key={planType}
                className={`relative overflow-hidden cursor-pointer transition-all ${
                  isSelected ? 'ring-4 ring-blue-500 shadow-lg scale-105' : 'hover:shadow-md'
                } ${isCurrentPlan ? 'border-2 border-green-500' : ''}`}
                onClick={() => handleSelectPlan(planType)}
              >
                {isCurrentPlan && (
                  <div className="absolute top-2 right-2 bg-green-500 text-white text-xs px-2 py-1 rounded-full">
                    Plano Atual
                  </div>
                )}
                
                <div className={`h-2 bg-gradient-to-r ${getPlanColor(planType)}`}></div>
                
                <div className="p-6">
                  <div className="flex items-center gap-3 mb-4">
                    <div className={`w-12 h-12 rounded-full bg-gradient-to-r ${getPlanColor(planType)} flex items-center justify-center`}>
                      <Icon className="w-6 h-6 text-white" />
                    </div>
                    <div>
                      <h4 className="font-bold text-lg">{plan.name}</h4>
                      <p className="text-2xl font-bold text-blue-600">
                        R$ {plan.price.toFixed(2)}
                        <span className="text-sm text-gray-500">/mês</span>
                      </p>
                    </div>
                  </div>

                  <div className="space-y-2 mb-4">
                    <div className="flex items-center gap-2 text-sm">
                      <Check className="w-4 h-4 text-green-500" />
                      <span>
                        {plan.whatsapp_limit === -1 ? '∞ Ilimitado' : `${plan.whatsapp_limit} número${plan.whatsapp_limit > 1 ? 's' : ''}`} WhatsApp
                      </span>
                    </div>
                    {plan.features.map((feature, idx) => (
                      <div key={idx} className="flex items-center gap-2 text-sm text-gray-600">
                        <Check className="w-4 h-4 text-green-500" />
                        <span>{feature}</span>
                      </div>
                    ))}
                  </div>

                  {bonusBalance > 0 && (
                    <div className="bg-green-50 border border-green-200 rounded p-2 mb-3">
                      <p className="text-xs text-green-700">
                        Com bônus: <span className="font-bold">R$ {Math.max(0.01, plan.price - bonusBalance).toFixed(2)}</span>
                      </p>
                    </div>
                  )}

                  <Button
                    className={`w-full ${isSelected ? 'bg-blue-600' : 'bg-gray-200 text-gray-700'}`}
                    disabled={isCurrentPlan}
                  >
                    {isCurrentPlan ? 'Plano Atual' : isSelected ? 'Selecionado' : 'Selecionar'}
                  </Button>
                </div>
              </Card>
            );
          })}
        </div>
      </div>

      {/* Botão Pagar com PIX */}
      {selectedPlan && (
        <Card className="p-6 bg-gradient-to-r from-green-50 to-emerald-50 border-green-200">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-bold text-green-900 mb-1">
                Plano {plans[selectedPlan]?.name} Selecionado
              </h3>
              <p className="text-sm text-green-700">
                Valor: R$ {plans[selectedPlan]?.price.toFixed(2)}
                {bonusBalance > 0 && (
                  <span> - Bônus: R$ {bonusBalance.toFixed(2)} = <span className="font-bold">R$ {Math.max(0.01, plans[selectedPlan]?.price - bonusBalance).toFixed(2)}</span></span>
                )}
              </p>
            </div>
            <Button
              onClick={handlePayWithPix}
              disabled={processing}
              className="bg-green-600 hover:bg-green-700 text-white px-8 py-6 text-lg"
            >
              {processing ? (
                <span className="flex items-center gap-2">
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                  Gerando PIX...
                </span>
              ) : (
                <span className="flex items-center gap-2">
                  <QrCodeIcon className="w-5 h-5" />
                  Pagar com PIX
                </span>
              )}
            </Button>
          </div>
        </Card>
      )}

      {/* Modal QR Code */}
      <Dialog open={showQRCode} onOpenChange={setShowQRCode}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="text-center text-xl">Pagamento PIX</DialogTitle>
          </DialogHeader>

          {paymentData && (
            <div className="space-y-4">
              {/* Info do Pagamento */}
              <div className="bg-blue-50 p-4 rounded-lg">
                <p className="text-sm text-gray-600">Valor a pagar:</p>
                <p className="text-3xl font-bold text-blue-600">R$ {paymentData.amount.toFixed(2)}</p>
                <p className="text-xs text-gray-500 mt-1">Plano: {plans[paymentData.plan_type]?.name}</p>
              </div>

              {/* QR Code */}
              <div className="flex justify-center bg-white p-4 rounded-lg border-2 border-gray-200">
                <QRCodeSVG value={paymentData.qr_code} size={256} />
              </div>

              {/* Código Copia e Cola */}
              <div>
                <p className="text-sm font-medium mb-2">Ou copie o código PIX:</p>
                <div className="bg-gray-100 p-3 rounded border border-gray-300 relative">
                  <p className="text-xs font-mono break-all pr-8">{paymentData.copy_paste_code}</p>
                  <Button
                    size="sm"
                    onClick={() => copyToClipboard(paymentData.copy_paste_code)}
                    className="absolute top-2 right-2"
                  >
                    {copying ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                  </Button>
                </div>
              </div>

              {/* Instruções */}
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                <p className="text-sm text-yellow-800">
                  <strong>Instruções:</strong>
                  <br />
                  1. Abra seu app de banco
                  <br />
                  2. Escolha pagar com PIX
                  <br />
                  3. Escaneie o QR Code ou cole o código
                  <br />
                  4. Confirme o pagamento
                  <br />
                  <br />
                  A confirmação é automática em até 5 minutos!
                </p>
              </div>

              <Button
                onClick={() => {
                  setShowQRCode(false);
                  fetchSubscriptionData();
                }}
                className="w-full"
                variant="outline"
              >
                Fechar
              </Button>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default SubscriptionPayments;
