/* eslint-disable no-restricted-globals */
// Service Worker para Push Notifications

// Escutar evento de push
self.addEventListener('push', function(event) {
  console.log('📲 Push notification recebida!', event);
  
  if (!event.data) {
    console.log('❌ Push sem dados');
    return;
  }
  
  try {
    const data = event.data.json();
    console.log('📦 Dados da notificação:', data);
    
    // Atualizar badge no ícone do app
    if ('setAppBadge' in navigator) {
      // Incrementar badge
      self.registration.getNotifications().then(function(notifications) {
        const count = notifications.length + 1;
        navigator.setAppBadge(count);
        console.log('🔢 Badge atualizado:', count);
      });
    }
    
    const options = {
      body: data.body || 'Você tem uma nova mensagem',
      icon: data.icon || '/logo192.png',
      badge: data.badge || '/badge72.png',
      tag: data.tag || 'iaze-notification',
      vibrate: data.vibrate || [200, 100, 200],
      requireInteraction: data.requireInteraction || false,
      silent: false,  // NÃO silenciar - reproduzir som
      renotify: true,  // Tocar som mesmo se já houver notificação com mesma tag
      data: {
        url: data.url || '/',
        timestamp: data.timestamp || Date.now()
      },
      actions: [
        {
          action: 'open',
          title: 'Abrir',
          icon: '/logo192.png'
        },
        {
          action: 'close',
          title: 'Fechar'
        }
      ]
    };
    
    // Reproduzir som customizado se disponível
    if (data.sound) {
      options.sound = data.sound;
    }
    
    event.waitUntil(
      self.registration.showNotification(data.title || 'IAZE', options)
    );
  } catch (error) {
    console.error('❌ Erro ao processar push:', error);
  }
});

// Escutar clique na notificação
self.addEventListener('notificationclick', function(event) {
  console.log('👆 Notificação clicada:', event);
  
  event.notification.close();
  
  if (event.action === 'close') {
    return;
  }
  
  // Abrir ou focar na janela do app
  const urlToOpen = event.notification.data?.url || '/';
  
  event.waitUntil(
    clients.matchAll({
      type: 'window',
      includeUncontrolled: true
    }).then(function(clientList) {
      // Se já tem uma janela aberta, focar nela
      for (let i = 0; i < clientList.length; i++) {
        const client = clientList[i];
        if (client.url.includes(self.location.origin) && 'focus' in client) {
          return client.focus().then(() => {
            if ('navigate' in client) {
              return client.navigate(urlToOpen);
            }
          });
        }
      }
      
      // Se não tem janela aberta, abrir nova
      if (clients.openWindow) {
        return clients.openWindow(urlToOpen);
      }
    })
  );
});

// Instalação do service worker
self.addEventListener('install', function(event) {
  console.log('✅ Service Worker instalado');
  self.skipWaiting();
});

// Ativação do service worker
self.addEventListener('activate', function(event) {
  console.log('✅ Service Worker ativado');
  event.waitUntil(clients.claim());
});

// Escutar mensagens do frontend para forçar atualização
self.addEventListener('message', function(event) {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    console.log('📲 Comando SKIP_WAITING recebido - ativando nova versão');
    self.skipWaiting();
  }
});
