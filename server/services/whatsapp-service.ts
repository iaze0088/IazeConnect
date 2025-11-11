import wppconnect from "@wppconnect-team/wppconnect";
import { storage } from "../storage";
import type { Whatsapp } from "@wppconnect-team/wppconnect";

interface SessionClient {
  client: Whatsapp;
  sessionName: string;
  qrCode?: string;
  status: string;
}

class WhatsAppService {
  private sessions: Map<string, SessionClient> = new Map();
  private qrCodeCallbacks: Map<string, (qr: string) => void> = new Map();

  async createSession(sessionName: string): Promise<void> {
    if (this.sessions.has(sessionName)) {
      throw new Error("Sessão já existe");
    }

    console.log(`[WPPConnect] Criando sessão: ${sessionName}`);

    try {
      const client = await wppconnect.create({
        session: sessionName,
        catchQR: async (base64Qr, asciiQR, attempts) => {
          console.log(`[WPPConnect] QR Code recebido (tentativa ${attempts}):`, asciiQR);
          
          try {
            const qrCodeDataURL = `data:image/png;base64,${base64Qr}`;
            
            const connection = await storage.getWhatsAppConnectionBySessionName(sessionName);
            if (connection) {
              await storage.updateWhatsAppConnection(connection.id, {
                qrCode: qrCodeDataURL,
                status: "connecting",
              });

              await storage.createWhatsAppLog({
                connectionId: connection.id,
                level: "info",
                message: `QR Code gerado (tentativa ${attempts})`,
                metadata: { attempts },
              });

              if (global.broadcastToWebSockets) {
                global.broadcastToWebSockets({
                  type: "qr_code",
                  sessionName,
                  connectionId: connection.id,
                  qrCode: qrCodeDataURL,
                });
              }
            }

            const callback = this.qrCodeCallbacks.get(sessionName);
            if (callback) {
              callback(qrCodeDataURL);
            }
          } catch (error) {
            console.error(`[WPPConnect] Erro ao processar QR Code:`, error);
          }
        },
        statusFind: async (statusSession, session) => {
          console.log(`[WPPConnect] Status da sessão ${session}:`, statusSession);
          
          const connection = await storage.getWhatsAppConnectionBySessionName(sessionName);
          if (!connection) return;

          if (statusSession === "inChat" || statusSession === "qrReadSuccess") {
            await storage.updateWhatsAppConnection(connection.id, {
              connected: true,
              status: "connected",
              qrCode: null,
              lastConnectedAt: new Date(),
            });

            await storage.createWhatsAppLog({
              connectionId: connection.id,
              level: "success",
              message: "WhatsApp conectado com sucesso!",
              metadata: { status: statusSession },
            });

            try {
              const hostDevice = await client.getHostDevice();
              if (hostDevice?.id?.user) {
                await storage.updateWhatsAppConnection(connection.id, {
                  phoneNumber: hostDevice.id.user,
                });
              }
            } catch (error) {
              console.error(`[WPPConnect] Erro ao obter número do dispositivo:`, error);
            }
          } else if (statusSession === "desconnected" || statusSession === "notLogged") {
            await storage.updateWhatsAppConnection(connection.id, {
              connected: false,
              status: "disconnected",
            });

            await storage.createWhatsAppLog({
              connectionId: connection.id,
              level: "warning",
              message: "WhatsApp desconectado",
              metadata: { status: statusSession },
            });
          }
        },
        logQR: false,
        disableWelcome: true,
        updatesLog: false,
      });

      this.sessions.set(sessionName, {
        client,
        sessionName,
        status: "connecting",
      });

      console.log(`[WPPConnect] Sessão ${sessionName} criada com sucesso`);

      client.onMessage(async (message) => {
        console.log(`[WPPConnect] Mensagem recebida na sessão ${sessionName}:`, message.body);
        
        const connection = await storage.getWhatsAppConnectionBySessionName(sessionName);
        if (connection) {
          await storage.createWhatsAppMessage({
            connectionId: connection.id,
            fromNumber: message.from,
            toNumber: message.to,
            message: message.body,
            messageType: message.type || "text",
            isIncoming: true,
            metadata: {
              id: message.id,
              timestamp: message.timestamp,
            },
          });
        }
      });

    } catch (error) {
      console.error(`[WPPConnect] Erro ao criar sessão ${sessionName}:`, error);
      throw error;
    }
  }

  async closeSession(sessionName: string): Promise<void> {
    const session = this.sessions.get(sessionName);
    if (!session) {
      throw new Error("Sessão não encontrada");
    }

    try {
      await session.client.close();
      this.sessions.delete(sessionName);
      this.qrCodeCallbacks.delete(sessionName);
      
      const connection = await storage.getWhatsAppConnectionBySessionName(sessionName);
      if (connection) {
        await storage.updateWhatsAppConnection(connection.id, {
          connected: false,
          status: "disconnected",
          qrCode: null,
        });

        await storage.createWhatsAppLog({
          connectionId: connection.id,
          level: "info",
          message: "Sessão encerrada",
        });
      }
      
      console.log(`[WPPConnect] Sessão ${sessionName} encerrada`);
    } catch (error) {
      console.error(`[WPPConnect] Erro ao fechar sessão ${sessionName}:`, error);
      throw error;
    }
  }

  async sendMessage(sessionName: string, to: string, message: string): Promise<any> {
    const session = this.sessions.get(sessionName);
    if (!session) {
      throw new Error("Sessão não encontrada");
    }

    try {
      const result = await session.client.sendText(to, message);
      
      const connection = await storage.getWhatsAppConnectionBySessionName(sessionName);
      if (connection) {
        await storage.createWhatsAppMessage({
          connectionId: connection.id,
          fromNumber: to,
          toNumber: to,
          message,
          messageType: "text",
          isIncoming: false,
        });
      }
      
      return result;
    } catch (error) {
      console.error(`[WPPConnect] Erro ao enviar mensagem:`, error);
      throw error;
    }
  }

  async getSessionStatus(sessionName: string): Promise<any> {
    const session = this.sessions.get(sessionName);
    if (!session) {
      return { connected: false, status: "not_found" };
    }

    try {
      const isConnected = await session.client.isConnected();
      return {
        connected: isConnected,
        status: isConnected ? "connected" : "disconnected",
        sessionName,
      };
    } catch (error) {
      return { connected: false, status: "error", error: String(error) };
    }
  }

  async refreshQRCode(sessionName: string): Promise<string | null> {
    const connection = await storage.getWhatsAppConnectionBySessionName(sessionName);
    return connection?.qrCode || null;
  }

  registerQRCallback(sessionName: string, callback: (qr: string) => void): void {
    this.qrCodeCallbacks.set(sessionName, callback);
  }

  unregisterQRCallback(sessionName: string): void {
    this.qrCodeCallbacks.delete(sessionName);
  }

  hasSession(sessionName: string): boolean {
    return this.sessions.has(sessionName);
  }

  getAllSessions(): string[] {
    return Array.from(this.sessions.keys());
  }
}

export const whatsappService = new WhatsAppService();
