import type { Express } from "express";
import { createServer, type Server } from "http";
import { WebSocketServer, WebSocket } from "ws";
import { storage } from "./storage";
import { WppConnectAPI } from "./wppconnect-api";
import { insertWhatsAppConnectionSchema } from "@shared/schema";
import { z } from "zod";
import iazeRoutes from "./routes-iaze";

export async function registerRoutes(app: Express): Promise<Server> {
  // Register IAZE routes
  app.use(iazeRoutes);
  console.log("[Server] Rotas IAZE registradas com sucesso");
  
  app.get("/api/whatsapp/connections", async (req, res) => {
    try {
      const connections = await storage.getAllWhatsAppConnections();
      res.json(connections);
    } catch (error: any) {
      console.error("Erro ao buscar conexões:", error);
      res.status(500).json({ error: error.message });
    }
  });

  app.post("/api/whatsapp/connections", async (req, res) => {
    try {
      const data = insertWhatsAppConnectionSchema.parse(req.body);
      
      const existing = await storage.getWhatsAppConnectionBySessionName(data.sessionName);
      if (existing) {
        return res.status(400).json({ error: "Já existe uma conexão com este nome de sessão" });
      }

      const connection = await storage.createWhatsAppConnection(data);
      
      await storage.createWhatsAppLog({
        connectionId: connection.id,
        level: "info",
        message: `Conexão criada: ${connection.sessionName}`,
      });

      res.json(connection);
    } catch (error: any) {
      if (error instanceof z.ZodError) {
        return res.status(400).json({ error: "Dados inválidos", details: error.errors });
      }
      console.error("Erro ao criar conexão:", error);
      res.status(500).json({ error: error.message });
    }
  });

  app.delete("/api/whatsapp/connections/:id", async (req, res) => {
    try {
      const { id } = req.params;
      
      const connection = await storage.getWhatsAppConnection(id);
      if (!connection) {
        return res.status(404).json({ error: "Conexão não encontrada" });
      }

      // Fechar sessão na API WPP Connect
      await WppConnectAPI.closeSession(connection.sessionName);

      await storage.deleteWhatsAppConnection(id);
      
      res.json({ success: true });
    } catch (error: any) {
      console.error("Erro ao deletar conexão:", error);
      res.status(500).json({ error: error.message });
    }
  });

  app.post("/api/whatsapp/connections/:id/start", async (req, res) => {
    try {
      const { id } = req.params;
      
      const connection = await storage.getWhatsAppConnection(id);
      if (!connection) {
        return res.status(404).json({ error: "Conexão não encontrada" });
      }

      await storage.updateWhatsAppConnection(id, {
        status: "connecting",
      });

      // Gerar token e iniciar sessão no servidor WPP Connect externo
      const token = await WppConnectAPI.generateToken(connection.sessionName);
      const result = await WppConnectAPI.startSession(connection.sessionName);

      // Atualizar status
      await storage.updateWhatsAppConnection(id, {
        status: result.status.toLowerCase(),
      });

      // Log
      await storage.createWhatsAppLog({
        connectionId: id,
        level: "info",
        message: `Sessão iniciada: ${connection.sessionName} - Status: ${result.status}`,
      });

      // Se já tiver QR code, enviar via WebSocket
      if (result.qrcode && wss) {
        wss.clients.forEach((client) => {
          if (client.readyState === WebSocket.OPEN) {
            client.send(JSON.stringify({
              type: "qrcode",
              sessionName: connection.sessionName,
              qrCode: result.qrcode,
            }));
          }
        });
      }

      res.json({ 
        success: true, 
        message: "Sessão iniciada com servidor WPP Connect externo",
        connectionId: id,
        status: result.status,
        qrcode: result.qrcode
      });
    } catch (error: any) {
      console.error("Erro ao iniciar sessão:", error);
      
      await storage.createWhatsAppLog({
        connectionId: req.params.id,
        level: "error",
        message: `Erro ao iniciar sessão: ${error.message}`,
      });
      
      res.status(500).json({ error: error.message });
    }
  });

  app.post("/api/whatsapp/connections/:id/refresh", async (req, res) => {
    try {
      const { id } = req.params;
      
      const connection = await storage.getWhatsAppConnection(id);
      if (!connection) {
        return res.status(404).json({ error: "Conexão não encontrada" });
      }

      // Verificar conexão via API REST
      const connected = await WppConnectAPI.checkConnection(connection.sessionName);
      const session = WppConnectAPI.getSession(connection.sessionName);
      
      await storage.updateWhatsAppConnection(id, {
        status: connected ? "connected" : (session?.status || "disconnected"),
      });

      const updated = await storage.getWhatsAppConnection(id);
      res.json(updated);
    } catch (error: any) {
      console.error("Erro ao atualizar status:", error);
      res.status(500).json({ error: error.message });
    }
  });

  app.post("/api/whatsapp/connections/:id/send", async (req, res) => {
    try {
      const { id } = req.params;
      const { to, message } = req.body;

      if (!to || !message) {
        return res.status(400).json({ error: "Campos 'to' e 'message' são obrigatórios" });
      }
      
      const connection = await storage.getWhatsAppConnection(id);
      if (!connection) {
        return res.status(404).json({ error: "Conexão não encontrada" });
      }

      // Verificar se sessão existe
      const session = WppConnectAPI.getSession(connection.sessionName);
      if (!session) {
        return res.status(400).json({ error: "Sessão não está ativa. Inicie a sessão primeiro." });
      }

      // Enviar mensagem via API WPP Connect
      await WppConnectAPI.sendMessage(connection.sessionName, to, message);
      
      await storage.createWhatsAppLog({
        connectionId: id,
        level: "info",
        message: `Mensagem enviada para ${to}`,
        metadata: { to, messageLength: message.length },
      });

      res.json({ success: true, result });
    } catch (error: any) {
      console.error("Erro ao enviar mensagem:", error);
      res.status(500).json({ error: error.message });
    }
  });

  app.get("/api/whatsapp/logs", async (req, res) => {
    try {
      const limit = req.query.limit ? parseInt(req.query.limit as string) : 100;
      const logs = await storage.getAllWhatsAppLogs(limit);
      res.json(logs);
    } catch (error: any) {
      console.error("Erro ao buscar logs:", error);
      res.status(500).json({ error: error.message });
    }
  });

  const httpServer = createServer(app);

  const wss = new WebSocketServer({ server: httpServer, path: '/ws' });

  wss.on('connection', (ws: WebSocket) => {
    console.log('[WebSocket] Cliente conectado');

    ws.on('message', (message: string) => {
      try {
        const data = JSON.parse(message.toString());
        console.log('[WebSocket] Mensagem recebida:', data);

        if (data.type === 'subscribe' && data.sessionName) {
          (ws as any).sessionName = data.sessionName;
          console.log(`[WebSocket] Cliente inscrito na sessão: ${data.sessionName}`);
        }
      } catch (error) {
        console.error('[WebSocket] Erro ao processar mensagem:', error);
      }
    });

    ws.on('close', () => {
      console.log('[WebSocket] Cliente desconectado');
    });

    ws.on('error', (error) => {
      console.error('[WebSocket] Erro:', error);
    });
  });

  function broadcastToWebSockets(message: any) {
    wss.clients.forEach((client) => {
      if (client.readyState === WebSocket.OPEN) {
        const sessionName = (client as any).sessionName;
        if (!sessionName || sessionName === message.sessionName) {
          client.send(JSON.stringify(message));
        }
      }
    });
  }

  global.broadcastToWebSockets = broadcastToWebSockets;

  console.log('[Server] Rotas registradas com sucesso');
  console.log('[WebSocket] Servidor WebSocket iniciado em /ws');

  return httpServer;
}

declare global {
  var broadcastToWebSockets: (message: any) => void;
}
