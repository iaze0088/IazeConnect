import { useState, useEffect } from 'react';
import api from './api';

// Função para converter VAPID key de base64url para Uint8Array
function urlBase64ToUint8Array(base64String) {
  const padding = '='.repeat((4 - base64String.length % 4) % 4);
  const base64 = (base64String + padding)
    .replace(/-/g, '+')
    .replace(/_/g, '/');

  const rawData = window.atob(base64);
  const outputArray = new Uint8Array(rawData.length);

  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  return outputArray;
}

export function usePushNotifications(clientId, resellerId) {
  const [isSupported, setIsSupported] = useState(false);
  const [permission, setPermission] = useState('default');
  const [isSubscribed, setIsSubscribed] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Verificar se push notifications são suportadas
    const supported = 'serviceWorker' in navigator && 'PushManager' in window;
    setIsSupported(supported);

    if (supported) {
      setPermission(Notification.permission);
    }
  }, []);

  const requestPermission = async () => {
    try {
      const perm = await Notification.requestPermission();
      setPermission(perm);
      return perm === 'granted';
    } catch (error) {
      console.error('❌ Erro ao solicitar permissão:', error);
      return false;
    }
  };

  const subscribe = async () => {
    if (!isSupported || !clientId || !resellerId) {
      console.log('⚠️ Push não suportado ou dados insuficientes');
      return false;
    }

    setLoading(true);

    try {
      // Solicitar permissão se ainda não foi concedida
      if (permission !== 'granted') {
        const granted = await requestPermission();
        if (!granted) {
          console.log('❌ Permissão negada');
          setLoading(false);
          return false;
        }
      }

      // Buscar chave pública VAPID do backend
      console.log('📡 Buscando chave VAPID...');
      const { data: vapidData } = await api.get('/push/vapid-public-key');
      const vapidPublicKey = vapidData.publicKey;
      console.log('✅ Chave VAPID obtida');

      // Registrar service worker
      console.log('📝 Registrando service worker...');
      const registration = await navigator.serviceWorker.register('/push-service-worker.js');
      console.log('✅ Service worker registrado');

      // Aguardar service worker estar ready
      await navigator.serviceWorker.ready;

      // Subscrever para push notifications
      console.log('📲 Subscrevendo para push...');
      const subscription = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(vapidPublicKey)
      });
      console.log('✅ Subscription criada:', subscription);

      // Enviar subscription para o backend
      console.log('💾 Salvando subscription no backend...');
      await api.post('/push/subscribe', {
        client_id: clientId,
        reseller_id: resellerId,
        subscription_data: subscription.toJSON(),
        user_agent: navigator.userAgent
      });

      console.log('✅ Push notifications ativadas com sucesso!');
      setIsSubscribed(true);
      setLoading(false);
      return true;

    } catch (error) {
      console.error('❌ Erro ao ativar push notifications:', error);
      setLoading(false);
      return false;
    }
  };

  const unsubscribe = async () => {
    if (!isSupported || !clientId) {
      return false;
    }

    setLoading(true);

    try {
      // Desregistrar no backend
      await api.post(`/push/unsubscribe/${clientId}`);

      // Desregistrar no navegador
      const registration = await navigator.serviceWorker.ready;
      const subscription = await registration.pushManager.getSubscription();
      if (subscription) {
        await subscription.unsubscribe();
      }

      console.log('✅ Push notifications desativadas');
      setIsSubscribed(false);
      setLoading(false);
      return true;

    } catch (error) {
      console.error('❌ Erro ao desativar push notifications:', error);
      setLoading(false);
      return false;
    }
  };

  return {
    isSupported,
    permission,
    isSubscribed,
    loading,
    subscribe,
    unsubscribe,
    requestPermission
  };
}

export default usePushNotifications;
