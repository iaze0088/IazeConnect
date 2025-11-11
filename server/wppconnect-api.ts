import axios, { AxiosError } from "axios";

// Função auxiliar para retry com exponential backoff
async function retryWithBackoff<T>(
  fn: () => Promise<T>,
  retries = 3,
  delay = 1000
): Promise<T> {
  for (let i = 0; i < retries; i++) {
    try {
      return await fn();
    } catch (error) {
      if (i === retries - 1) throw error;
      
      const backoffDelay = delay * Math.pow(2, i);
      console.log(`[WPP API] Tentativa ${i + 1}/${retries} falhou. Aguardando ${backoffDelay}ms...`);
      await new Promise(resolve => setTimeout(resolve, backoffDelay));
    }
  }
  throw new Error("Retry limit exceeded");
}

// Configuração do servidor WPP Connect externo
// Usa env vars se disponíveis, senão usa domínio personalizado
const WPP_CONNECT_URL = process.env.WPPCONNECT_API_URL || "https://wppconnect.suporte.help";
const WPP_SECRET_KEY = process.env.WPPCONNECT_SECRET_KEY || "THISISMYSECURETOKEN";

console.log(`[WPP API] Configurado para usar servidor: ${WPP_CONNECT_URL}`);

interface WppSession {
  sessionName: string;
  token?: string;
  qrCode?: string;
  status: string;
}

const sessions = new Map<string, WppSession>();

export class WppConnectAPI {
  /**
   * Gera token de autenticação para uma sessão (com retry)
   */
  static async generateToken(sessionName: string): Promise<string> {
    return retryWithBackoff(async () => {
      try {
        const response = await axios.post(
          `${WPP_CONNECT_URL}/api/${sessionName}/${WPP_SECRET_KEY}/generate-token`,
          {},
          { 
            headers: { "Content-Type": "application/json" },
            timeout: 15000 
          }
        );

        // IMPORTANTE: Usar apenas o campo 'token' (bcrypt hash), NÃO o campo 'full'
        const token = response.data.token; // "$2b$10$..." (apenas o hash)
        
        if (!token) {
          throw new Error("Token não recebido do servidor");
        }
        
        // Armazenar token da sessão
        const session = sessions.get(sessionName) || { sessionName, status: "initializing" };
        session.token = token;
        sessions.set(sessionName, session);

        console.log(`[WPP API] Token gerado para sessão ${sessionName}: ${token.substring(0, 15)}...`);
        return token;
      } catch (error: any) {
        const errorMsg = error.response?.data?.message || error.message;
        console.error(`[WPP API] Erro ao gerar token:`, errorMsg);
        throw new Error(`Falha ao gerar token: ${errorMsg}`);
      }
    }, 3, 1000);
  }

  /**
   * Inicia uma sessão WhatsApp e retorna QR code
   */
  static async startSession(sessionName: string): Promise<{ status: string; qrcode?: string }> {
    try {
      // Garantir que temos token
      let session = sessions.get(sessionName);
      if (!session?.token) {
        await this.generateToken(sessionName);
        session = sessions.get(sessionName);
      }

      const response = await axios.post(
        `${WPP_CONNECT_URL}/api/${sessionName}/start-session`,
        { waitQrCode: true },
        {
          headers: {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": `Bearer ${session!.token}` // Bearer + bcrypt hash
          },
          timeout: 15000
        }
      );

      const { status, qrcode } = response.data;

      // Atualizar sessão
      session!.status = status;
      if (qrcode) {
        session!.qrCode = qrcode;
      }
      sessions.set(sessionName, session!);

      console.log(`[WPP API] Sessão ${sessionName} - Status: ${status}, QR: ${!!qrcode}`);
      
      return { status, qrcode };
    } catch (error: any) {
      console.error(`[WPP API] Erro ao iniciar sessão:`, error.message);
      throw new Error(`Falha ao iniciar sessão: ${error.message}`);
    }
  }

  /**
   * Busca QR code de uma sessão já iniciada
   */
  static async getQRCode(sessionName: string): Promise<{ status: string; qrcode?: string }> {
    try {
      const session = sessions.get(sessionName);
      if (!session?.token) {
        throw new Error("Sessão não iniciada. Execute startSession primeiro.");
      }

      const response = await axios.get(
        `${WPP_CONNECT_URL}/api/${sessionName}/qrcode-session`,
        {
          headers: {
            "Accept": "application/json",
            "Authorization": `Bearer ${session.token}`
          },
          timeout: 10000
        }
      );

      const { status, qrcode } = response.data;

      // Atualizar sessão
      session.status = status;
      if (qrcode) {
        session.qrCode = qrcode;
      }
      sessions.set(sessionName, session);

      return { status, qrcode };
    } catch (error: any) {
      console.error(`[WPP API] Erro ao buscar QR code:`, error.message);
      throw new Error(`Falha ao buscar QR code: ${error.message}`);
    }
  }

  /**
   * Verifica status de conexão da sessão
   */
  static async checkConnection(sessionName: string): Promise<boolean> {
    try {
      const session = sessions.get(sessionName);
      if (!session?.token) {
        return false;
      }

      const response = await axios.get(
        `${WPP_CONNECT_URL}/api/${sessionName}/check-connection-session`,
        {
          headers: {
            "Accept": "application/json",
            "Authorization": `Bearer ${session.token}`
          },
          timeout: 10000
        }
      );

      const connected = response.data.connected === true;
      
      if (connected) {
        session.status = "CONNECTED";
        sessions.set(sessionName, session);
      }

      return connected;
    } catch (error: any) {
      console.error(`[WPP API] Erro ao verificar conexão:`, error.message);
      return false;
    }
  }

  /**
   * Fecha uma sessão
   */
  static async closeSession(sessionName: string): Promise<void> {
    try {
      const session = sessions.get(sessionName);
      if (!session?.token) {
        return;
      }

      await axios.post(
        `${WPP_CONNECT_URL}/api/${sessionName}/close-session`,
        {},
        {
          headers: {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": `Bearer ${session.token}`
          },
          timeout: 10000
        }
      );

      sessions.delete(sessionName);
      console.log(`[WPP API] Sessão ${sessionName} fechada`);
    } catch (error: any) {
      console.error(`[WPP API] Erro ao fechar sessão:`, error.message);
    }
  }

  /**
   * Envia mensagem via API WPP Connect
   */
  static async sendMessage(sessionName: string, phone: string, message: string): Promise<void> {
    try {
      const session = sessions.get(sessionName);
      if (!session?.token) {
        throw new Error("Sessão não iniciada");
      }

      await axios.post(
        `${WPP_CONNECT_URL}/api/${sessionName}/send-message`,
        {
          phone: phone,
          message: message
        },
        {
          headers: {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": `Bearer ${session.token}`
          },
          timeout: 10000
        }
      );

      console.log(`[WPP API] Mensagem enviada para ${phone}`);
    } catch (error: any) {
      console.error(`[WPP API] Erro ao enviar mensagem:`, error.message);
      throw new Error(`Falha ao enviar mensagem: ${error.message}`);
    }
  }

  /**
   * Lista todas as sessões ativas
   */
  static getSessions(): WppSession[] {
    return Array.from(sessions.values());
  }

  /**
   * Pega uma sessão específica
   */
  static getSession(sessionName: string): WppSession | undefined {
    return sessions.get(sessionName);
  }
}
