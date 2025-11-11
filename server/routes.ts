import type { Express } from "express";
import { createServer, type Server } from "http";
import { WebSocketServer, WebSocket } from "ws";
import { storage } from "./storage";
import { WppConnectAPI } from "./wppconnect-api";
import { insertWhatsAppConnectionSchema, insertApiKeySchema } from "@shared/schema";
import { z } from "zod";
import iazeRoutes from "./routes-iaze";
import { ServerMetricsService, type ConnectionStats } from "./services/server-metrics";
import { ApiKeyService } from "./services/api-key-service";
import { WebhookService } from "./services/webhook-service";
import { authMiddleware, requireRole } from "./auth";

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

        // Trigger webhook para evento QR
        await WebhookService.notifyWhatsAppEvent(
          id,
          connection.sessionName,
          connection.resellerId || "default",
          "qr",
          { qrCode: result.qrcode }
        );
      }

      res.json({ 
        success: true, 
        message: "Sessão iniciada com servidor WPP Connect externo",
        connectionId: id,
        status: result.status,
        qrCode: result.qrcode
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

      res.json({ success: true });
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

  // Server metrics endpoint
  app.get("/api/server/metrics", async (req, res) => {
    try {
      // Aggregate connection stats
      const allConnections = await storage.getAllWhatsAppConnections();
      const connectionStats: ConnectionStats = {
        active: allConnections.filter(c => c.status === "connected").length,
        connecting: allConnections.filter(c => c.status === "connecting").length,
        disconnected: allConnections.filter(c => c.status === "disconnected").length,
        error: allConnections.filter(c => c.status === "error").length,
        total: allConnections.length
      };

      // Get comprehensive metrics (with 5s cache)
      const metrics = await ServerMetricsService.getMetrics(connectionStats);
      res.json(metrics);
    } catch (error: any) {
      console.error("Erro ao buscar métricas do servidor:", error);
      res.status(500).json({ error: error.message });
    }
  });

  // ==================== API KEYS ====================

  // Listar todas as API keys
  app.get("/api/api-keys", authMiddleware, requireRole("reseller"), async (req, res) => {
    try {
      const resellerId = (req as any).auth.resellerId;
      const apiKeys = await storage.getAllApiKeys(resellerId);
      
      // SECURITY: Não retornar keyHash nem webhookSecret
      const safe = apiKeys.map(({ keyHash, webhookSecret, ...rest }) => rest);
      res.json(safe);
    } catch (error: any) {
      console.error("Erro ao listar API keys:", error);
      res.status(500).json({ error: error.message });
    }
  });

  // Criar nova API key
  app.post("/api/api-keys", authMiddleware, requireRole("reseller"), async (req, res) => {
    try {
      const resellerId = (req as any).auth.resellerId;
      
      // SECURITY: Substituir resellerId do body pelo autenticado
      const validatedData = insertApiKeySchema.parse({
        ...req.body,
        resellerId,
      });
      
      const { apiKey, fullKey, webhookSecret } = await ApiKeyService.createApiKey(validatedData);
      
      await storage.createWhatsAppLog({
        level: "info",
        message: `API Key criada: ${apiKey.name} (${apiKey.keyPrefix}...${apiKey.keyLastChars})`,
      });

      // Retornar fullKey e webhookSecret APENAS na criação (única vez!)
      res.status(201).json({
        apiKey: {
          ...apiKey,
          keyHash: undefined, // Não expor hash
        },
        fullKey, // Mostrar chave completa apenas agora
        webhookSecret, // Mostrar webhook secret apenas agora
        warning: "ATENÇÃO: Guarde a API Key e o Webhook Secret em local seguro! Eles não serão mostrados novamente.",
      });
    } catch (error: any) {
      if (error instanceof z.ZodError) {
        return res.status(400).json({ error: "Dados inválidos", details: error.errors });
      }
      console.error("Erro ao criar API key:", error);
      res.status(500).json({ error: error.message });
    }
  });

  // Buscar detalhes de uma API key
  app.get("/api/api-keys/:id", authMiddleware, requireRole("reseller"), async (req, res) => {
    try {
      const { id } = req.params;
      const resellerId = (req as any).auth.resellerId;
      
      const apiKey = await storage.getApiKey(id);
      
      if (!apiKey) {
        return res.status(404).json({ error: "API key não encontrada" });
      }

      // SECURITY: Verificar tenant isolation
      if (apiKey.resellerId !== resellerId) {
        return res.status(403).json({ error: "Acesso negado" });
      }

      // Buscar conexões associadas
      const connections = await storage.getApiKeyConnections(id);
      const webhookDeliveries = await storage.getWebhookDeliveries(id, 20);

      res.json({
        ...apiKey,
        keyHash: undefined, // Não expor hash
        webhookSecret: undefined, // Não expor secret após criação
        connections,
        recentWebhooks: webhookDeliveries,
      });
    } catch (error: any) {
      console.error("Erro ao buscar API key:", error);
      res.status(500).json({ error: error.message });
    }
  });

  // Atualizar API key
  app.patch("/api/api-keys/:id", authMiddleware, requireRole("reseller"), async (req, res) => {
    try {
      const { id } = req.params;
      const resellerId = (req as any).auth.resellerId;
      const { name, webhookUrl, webhookSecret, webhookEvents, connectionLimit, status } = req.body;

      const existing = await storage.getApiKey(id);
      if (!existing) {
        return res.status(404).json({ error: "API key não encontrada" });
      }

      // SECURITY: Verificar tenant isolation
      if (existing.resellerId !== resellerId) {
        return res.status(403).json({ error: "Acesso negado" });
      }

      // Permitir update de webhook secret se fornecido
      const finalWebhookSecret = webhookSecret || existing.webhookSecret;

      const updated = await storage.updateApiKey(id, {
        name,
        webhookUrl,
        webhookSecret: finalWebhookSecret,
        webhookEvents,
        connectionLimit,
        status,
      });

      res.json({
        ...updated,
        keyHash: undefined,
        webhookSecret: undefined, // Não retornar secret no update
      });
    } catch (error: any) {
      console.error("Erro ao atualizar API key:", error);
      res.status(500).json({ error: error.message });
    }
  });

  // Deletar API key
  app.delete("/api/api-keys/:id", authMiddleware, requireRole("reseller"), async (req, res) => {
    try {
      const { id } = req.params;
      const resellerId = (req as any).auth.resellerId;
      
      const apiKey = await storage.getApiKey(id);
      if (!apiKey) {
        return res.status(404).json({ error: "API key não encontrada" });
      }

      // SECURITY: Verificar tenant isolation
      if (apiKey.resellerId !== resellerId) {
        return res.status(403).json({ error: "Acesso negado" });
      }

      const deleted = await storage.deleteApiKey(id);
      
      if (deleted) {
        await storage.createWhatsAppLog({
          level: "warn",
          message: `API Key deletada: ${apiKey.name}`,
        });
      }

      res.json({ success: deleted });
    } catch (error: any) {
      console.error("Erro ao deletar API key:", error);
      res.status(500).json({ error: error.message });
    }
  });

  // Rotacionar token de uma API key
  app.post("/api/api-keys/:id/rotate", authMiddleware, requireRole("reseller"), async (req, res) => {
    try {
      const { id } = req.params;
      const resellerId = (req as any).auth.resellerId;

      // SECURITY: Verificar tenant isolation antes de rotacionar
      const existing = await storage.getApiKey(id);
      if (!existing) {
        return res.status(404).json({ error: "API key não encontrada" });
      }

      if (existing.resellerId !== resellerId) {
        return res.status(403).json({ error: "Acesso negado" });
      }

      const result = await ApiKeyService.rotateApiKey(id);
      if (!result) {
        return res.status(404).json({ error: "API key não encontrada" });
      }

      await storage.createWhatsAppLog({
        level: "warn",
        message: `API Key rotacionada: ${result.apiKey.name}`,
      });

      res.json({
        apiKey: {
          ...result.apiKey,
          keyHash: undefined,
          webhookSecret: undefined,
        },
        fullKey: result.fullKey,
        warning: "ATENÇÃO: A chave anterior foi invalidada! Guarde esta nova chave.",
      });
    } catch (error: any) {
      console.error("Erro ao rotacionar API key:", error);
      res.status(500).json({ error: error.message });
    }
  });

  // Buscar estatísticas de uso
  app.get("/api/api-keys/:id/usage", authMiddleware, requireRole("reseller"), async (req, res) => {
    try {
      const { id } = req.params;
      const resellerId = (req as any).auth.resellerId;
      
      const apiKey = await storage.getApiKey(id);
      if (!apiKey) {
        return res.status(404).json({ error: "API key não encontrada" });
      }

      // SECURITY: Verificar tenant isolation
      if (apiKey.resellerId !== resellerId) {
        return res.status(403).json({ error: "Acesso negado" });
      }

      const connections = await storage.getApiKeyConnections(id);
      const webhooks = await storage.getWebhookDeliveries(id, 100);

      const stats = {
        totalRequests: apiKey.totalRequests,
        currentConnections: apiKey.currentConnections,
        connectionLimit: apiKey.connectionLimit,
        utilizationPercent: Math.round((apiKey.currentConnections / apiKey.connectionLimit) * 100),
        lastUsedAt: apiKey.lastUsedAt,
        webhookStats: {
          total: webhooks.length,
          success: webhooks.filter(w => w.status === "success").length,
          failed: webhooks.filter(w => w.status === "failed").length,
          pending: webhooks.filter(w => w.status === "pending" || w.status === "retrying").length,
        },
        activeConnections: connections,
      };

      res.json(stats);
    } catch (error: any) {
      console.error("Erro ao buscar estatísticas:", error);
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
