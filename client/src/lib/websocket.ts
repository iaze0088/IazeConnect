export function connectWebSocket(onMessage: (data: any) => void): WebSocket | null {
  try {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${window.location.host}/ws`;
    
    const socket = new WebSocket(wsUrl);

    socket.onopen = () => {
      console.log("[WebSocket] Conectado ao servidor");
    };

    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log("[WebSocket] Mensagem recebida:", data);
        onMessage(data);
      } catch (error) {
        console.error("[WebSocket] Erro ao processar mensagem:", error);
      }
    };

    socket.onclose = () => {
      console.log("[WebSocket] Desconectado do servidor");
    };

    socket.onerror = (error) => {
      console.error("[WebSocket] Erro:", error);
    };

    return socket;
  } catch (error) {
    console.error("[WebSocket] Erro ao conectar:", error);
    return null;
  }
}

export function subscribeToSession(socket: WebSocket, sessionName: string): void {
  if (socket.readyState === WebSocket.OPEN) {
    socket.send(JSON.stringify({ type: "subscribe", sessionName }));
  }
}
