import React, { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog';
import { Button } from './ui/button';
import { AlertCircle, Clock, CreditCard, X } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';

const SubscriptionExpirationWarning = ({ onNavigateToPayments }) => {
  const [showWarning, setShowWarning] = useState(false);
  const [subscriptionData, setSubscriptionData] = useState(null);
  const [lastShownDate, setLastShownDate] = useState(null);

  useEffect(() => {
    checkSubscriptionStatus();
    
    // Verificar 2x ao dia (12 horas de intervalo)
    const interval = setInterval(() => {
      checkSubscriptionStatus();
    }, 12 * 60 * 60 * 1000); // 12 horas

    return () => clearInterval(interval);
  }, []);

  const checkSubscriptionStatus = async () => {
    try {
      const token = localStorage.getItem('token');
      const userStr = localStorage.getItem('user');
      const user = userStr ? JSON.parse(userStr) : {};

      // Apenas para resellers
      if (user.user_type !== 'reseller') return;

      const response = await fetch(`${BACKEND_URL}/api/subscription/status`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setSubscriptionData(data);

        // Verificar se deve mostrar o aviso
        if (data.show_expiration_warning) {
          const today = new Date().toDateString();
          const lastShown = localStorage.getItem('last_expiration_warning');

          // Mostrar se não foi mostrado hoje ainda
          if (lastShown !== today) {
            setShowWarning(true);
            localStorage.setItem('last_expiration_warning', today);
          }
        }
      }
    } catch (error) {
      console.error('Error checking subscription:', error);
    }
  };

  const handleClose = () => {
    setShowWarning(false);
  };

  const handleGoToPayments = () => {
    setShowWarning(false);
    if (onNavigateToPayments) {
      onNavigateToPayments();
    }
  };

  if (!subscriptionData || !showWarning) return null;

  const daysLeft = subscriptionData.days_left || 0;
  const isExpired = daysLeft <= 0;
  const status = subscriptionData.subscription?.status;
  const planName = subscriptionData.subscription?.plan_type || 'básico';

  return (
    <Dialog open={showWarning} onOpenChange={setShowWarning}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-3 text-xl">
            <div className={`w-12 h-12 rounded-full ${isExpired ? 'bg-red-500' : 'bg-yellow-500'} flex items-center justify-center`}>
              {isExpired ? (
                <X className="w-6 h-6 text-white" />
              ) : (
                <AlertCircle className="w-6 h-6 text-white" />
              )}
            </div>
            {isExpired ? 'Assinatura Expirada!' : 'Sua Assinatura Está Vencendo!'}
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          {/* Contador de Dias */}
          <div className={`p-6 rounded-lg ${isExpired ? 'bg-red-50 border-2 border-red-200' : 'bg-yellow-50 border-2 border-yellow-200'}`}>
            <div className="flex items-center justify-center gap-4">
              <Clock className={`w-12 h-12 ${isExpired ? 'text-red-600' : 'text-yellow-600'}`} />
              <div className="text-center">
                {isExpired ? (
                  <>
                    <p className="text-sm text-red-700 font-medium">Assinatura Expirada</p>
                    <p className="text-4xl font-bold text-red-900">0</p>
                    <p className="text-xs text-red-600">dias restantes</p>
                  </>
                ) : (
                  <>
                    <p className="text-sm text-yellow-700 font-medium">Dias Restantes</p>
                    <p className="text-5xl font-bold text-yellow-900">{daysLeft}</p>
                    <p className="text-xs text-yellow-600">
                      {daysLeft === 1 ? 'dia' : 'dias'}
                    </p>
                  </>
                )}
              </div>
            </div>
          </div>

          {/* Mensagem */}
          <div className="space-y-2">
            {isExpired ? (
              <>
                <p className="text-center text-gray-700 font-medium">
                  Sua assinatura do plano <span className="font-bold uppercase">{planName}</span> expirou!
                </p>
                <p className="text-center text-sm text-gray-600">
                  Para continuar usando a plataforma, renove sua assinatura agora.
                </p>
              </>
            ) : (
              <>
                <p className="text-center text-gray-700 font-medium">
                  Sua assinatura do plano <span className="font-bold uppercase">{planName}</span> vence em {daysLeft} {daysLeft === 1 ? 'dia' : 'dias'}!
                </p>
                <p className="text-center text-sm text-gray-600">
                  Renove agora para não perder acesso aos recursos da plataforma.
                </p>
              </>
            )}
          </div>

          {/* Bônus Disponível */}
          {subscriptionData.bonus_balance > 0 && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-3">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-full bg-green-500 flex items-center justify-center">
                  <span className="text-white font-bold">%</span>
                </div>
                <div>
                  <p className="text-sm font-medium text-green-900">
                    Você tem bônus disponível!
                  </p>
                  <p className="text-xs text-green-700">
                    R$ {subscriptionData.bonus_balance.toFixed(2)} de desconto
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Botões */}
          <div className="flex gap-3 pt-2">
            <Button
              onClick={handleClose}
              variant="outline"
              className="flex-1"
            >
              Lembrar Depois
            </Button>
            <Button
              onClick={handleGoToPayments}
              className={`flex-1 ${isExpired ? 'bg-red-600 hover:bg-red-700' : 'bg-yellow-600 hover:bg-yellow-700'} text-white`}
            >
              <CreditCard className="w-4 h-4 mr-2" />
              Renovar Agora
            </Button>
          </div>

          {/* Info Adicional */}
          <p className="text-xs text-center text-gray-500">
            Este aviso aparece 2x ao dia quando faltam 5 dias ou menos para o vencimento.
          </p>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default SubscriptionExpirationWarning;
