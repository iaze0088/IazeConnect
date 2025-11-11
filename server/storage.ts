import { 
  type WhatsAppConnection, 
  type InsertWhatsAppConnection,
  type WhatsAppLog,
  type InsertWhatsAppLog,
  type WhatsAppMessage,
  type InsertWhatsAppMessage,
  type ApiKey,
  type InsertApiKey,
  type ApiKeyConnection,
  type InsertApiKeyConnection,
  type WebhookDelivery,
  type InsertWebhookDelivery
} from "@shared/schema";
import { randomUUID } from "crypto";

export interface IStorage {
  // WhatsApp Connections
  getWhatsAppConnection(id: string): Promise<WhatsAppConnection | undefined>;
  getWhatsAppConnectionBySessionName(sessionName: string): Promise<WhatsAppConnection | undefined>;
  getAllWhatsAppConnections(): Promise<WhatsAppConnection[]>;
  createWhatsAppConnection(connection: InsertWhatsAppConnection): Promise<WhatsAppConnection>;
  updateWhatsAppConnection(id: string, data: Partial<WhatsAppConnection>): Promise<WhatsAppConnection | undefined>;
  deleteWhatsAppConnection(id: string): Promise<boolean>;
  
  // Logs
  createWhatsAppLog(log: InsertWhatsAppLog): Promise<WhatsAppLog>;
  getAllWhatsAppLogs(limit?: number): Promise<WhatsAppLog[]>;
  
  // Messages
  createWhatsAppMessage(message: InsertWhatsAppMessage): Promise<WhatsAppMessage>;
  getWhatsAppMessages(connectionId: string, limit?: number): Promise<WhatsAppMessage[]>;
  
  // API Keys
  createApiKey(apiKey: ApiKey): Promise<ApiKey>; // Recebe com hash/prefix já gerados
  getApiKey(id: string): Promise<ApiKey | undefined>;
  getApiKeyByHash(keyHash: string): Promise<ApiKey | undefined>;
  getAllApiKeys(resellerId?: string): Promise<ApiKey[]>;
  updateApiKey(id: string, data: Partial<ApiKey>): Promise<ApiKey | undefined>;
  deleteApiKey(id: string): Promise<boolean>;
  incrementApiKeyUsage(id: string): Promise<void>;
  
  // API Key Connections
  createApiKeyConnection(connection: InsertApiKeyConnection): Promise<ApiKeyConnection>;
  getApiKeyConnections(apiKeyId: string): Promise<ApiKeyConnection[]>;
  deleteApiKeyConnection(id: string): Promise<boolean>;
  countApiKeyConnections(apiKeyId: string): Promise<number>;
  
  // Webhook Deliveries
  createWebhookDelivery(delivery: InsertWebhookDelivery): Promise<WebhookDelivery>;
  getWebhookDeliveries(apiKeyId: string, limit?: number): Promise<WebhookDelivery[]>;
  getPendingWebhookDeliveries(limit?: number): Promise<WebhookDelivery[]>;
  updateWebhookDelivery(id: string, data: Partial<WebhookDelivery>): Promise<WebhookDelivery | undefined>;
}

export class MemStorage implements IStorage {
  private whatsappConnections: Map<string, WhatsAppConnection>;
  private whatsappLogs: Map<string, WhatsAppLog>;
  private whatsappMessages: Map<string, WhatsAppMessage>;
  private apiKeys: Map<string, ApiKey>;
  private apiKeyConnections: Map<string, ApiKeyConnection>;
  private webhookDeliveries: Map<string, WebhookDelivery>;

  constructor() {
    this.whatsappConnections = new Map();
    this.whatsappLogs = new Map();
    this.whatsappMessages = new Map();
    this.apiKeys = new Map();
    this.apiKeyConnections = new Map();
    this.webhookDeliveries = new Map();
  }

  async getWhatsAppConnection(id: string): Promise<WhatsAppConnection | undefined> {
    return this.whatsappConnections.get(id);
  }

  async getWhatsAppConnectionBySessionName(sessionName: string): Promise<WhatsAppConnection | undefined> {
    return Array.from(this.whatsappConnections.values()).find(
      (conn) => conn.sessionName === sessionName
    );
  }

  async getAllWhatsAppConnections(): Promise<WhatsAppConnection[]> {
    return Array.from(this.whatsappConnections.values()).sort(
      (a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
    );
  }

  async createWhatsAppConnection(insertConnection: InsertWhatsAppConnection): Promise<WhatsAppConnection> {
    const id = randomUUID();
    const now = new Date();
    const connection: WhatsAppConnection = {
      ...insertConnection,
      id,
      qrCodeData: null,
      phoneNumber: null,
      lastConnectedAt: null,
      createdAt: now,
    };
    this.whatsappConnections.set(id, connection);
    return connection;
  }

  async updateWhatsAppConnection(id: string, data: Partial<WhatsAppConnection>): Promise<WhatsAppConnection | undefined> {
    const connection = this.whatsappConnections.get(id);
    if (!connection) return undefined;

    const updated: WhatsAppConnection = {
      ...connection,
      ...data,
    };
    this.whatsappConnections.set(id, updated);
    return updated;
  }

  async deleteWhatsAppConnection(id: string): Promise<boolean> {
    return this.whatsappConnections.delete(id);
  }

  async createWhatsAppLog(insertLog: InsertWhatsAppLog): Promise<WhatsAppLog> {
    const id = randomUUID();
    const log: WhatsAppLog = {
      ...insertLog,
      id,
      timestamp: new Date(),
      metadata: insertLog.metadata || null,
      connectionId: insertLog.connectionId || null,
      level: insertLog.level || "info",
    };
    this.whatsappLogs.set(id, log);
    return log;
  }

  async getAllWhatsAppLogs(limit: number = 100): Promise<WhatsAppLog[]> {
    const logs = Array.from(this.whatsappLogs.values()).sort(
      (a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
    );
    return logs.slice(0, limit);
  }

  async createWhatsAppMessage(insertMessage: InsertWhatsAppMessage): Promise<WhatsAppMessage> {
    const id = randomUUID();
    const message: WhatsAppMessage = {
      ...insertMessage,
      id,
      timestamp: new Date(),
      metadata: insertMessage.metadata || null,
      messageType: insertMessage.messageType || "text",
      isIncoming: insertMessage.isIncoming !== undefined ? insertMessage.isIncoming : true,
    };
    this.whatsappMessages.set(id, message);
    return message;
  }

  async getWhatsAppMessages(connectionId: string, limit: number = 50): Promise<WhatsAppMessage[]> {
    const messages = Array.from(this.whatsappMessages.values())
      .filter((msg) => msg.connectionId === connectionId)
      .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
    return messages.slice(0, limit);
  }

  // ==================== API KEYS ====================

  async createApiKey(apiKey: ApiKey): Promise<ApiKey> {
    this.apiKeys.set(apiKey.id, apiKey);
    return apiKey;
  }

  async getApiKey(id: string): Promise<ApiKey | undefined> {
    return this.apiKeys.get(id);
  }

  async getApiKeyByHash(keyHash: string): Promise<ApiKey | undefined> {
    return Array.from(this.apiKeys.values()).find(
      (key) => key.keyHash === keyHash
    );
  }

  async getAllApiKeys(resellerId?: string): Promise<ApiKey[]> {
    const keys = Array.from(this.apiKeys.values());
    const filtered = resellerId
      ? keys.filter((key) => key.resellerId === resellerId)
      : keys;
    return filtered.sort(
      (a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
    );
  }

  async updateApiKey(id: string, data: Partial<ApiKey>): Promise<ApiKey | undefined> {
    const apiKey = this.apiKeys.get(id);
    if (!apiKey) return undefined;

    const updated: ApiKey = {
      ...apiKey,
      ...data,
    };
    this.apiKeys.set(id, updated);
    return updated;
  }

  async deleteApiKey(id: string): Promise<boolean> {
    const deleted = this.apiKeys.delete(id);
    
    // Delete related connections
    if (deleted) {
      const connections = Array.from(this.apiKeyConnections.values())
        .filter((conn) => conn.apiKeyId === id);
      connections.forEach((conn) => this.apiKeyConnections.delete(conn.id));
      
      // Delete related webhook deliveries
      const deliveries = Array.from(this.webhookDeliveries.values())
        .filter((delivery) => delivery.apiKeyId === id);
      deliveries.forEach((delivery) => this.webhookDeliveries.delete(delivery.id));
    }
    
    return deleted;
  }

  async incrementApiKeyUsage(id: string): Promise<void> {
    const apiKey = this.apiKeys.get(id);
    if (!apiKey) return;

    const updated: ApiKey = {
      ...apiKey,
      totalRequests: apiKey.totalRequests + 1,
      lastUsedAt: new Date(),
    };
    this.apiKeys.set(id, updated);
  }

  // ==================== API KEY CONNECTIONS ====================

  async createApiKeyConnection(insertConnection: InsertApiKeyConnection): Promise<ApiKeyConnection> {
    const id = randomUUID();
    const connection: ApiKeyConnection = {
      ...insertConnection,
      id,
      createdAt: new Date(),
    };
    this.apiKeyConnections.set(id, connection);

    // Update current connections count
    const apiKey = await this.getApiKey(connection.apiKeyId);
    if (apiKey) {
      await this.updateApiKey(apiKey.id, {
        currentConnections: apiKey.currentConnections + 1,
      });
    }

    return connection;
  }

  async getApiKeyConnections(apiKeyId: string): Promise<ApiKeyConnection[]> {
    return Array.from(this.apiKeyConnections.values())
      .filter((conn) => conn.apiKeyId === apiKeyId);
  }

  async deleteApiKeyConnection(id: string): Promise<boolean> {
    const connection = this.apiKeyConnections.get(id);
    if (!connection) return false;

    const deleted = this.apiKeyConnections.delete(id);

    // Update current connections count
    if (deleted) {
      const apiKey = await this.getApiKey(connection.apiKeyId);
      if (apiKey && apiKey.currentConnections > 0) {
        await this.updateApiKey(apiKey.id, {
          currentConnections: apiKey.currentConnections - 1,
        });
      }
    }

    return deleted;
  }

  async countApiKeyConnections(apiKeyId: string): Promise<number> {
    return Array.from(this.apiKeyConnections.values())
      .filter((conn) => conn.apiKeyId === apiKeyId).length;
  }

  // ==================== WEBHOOK DELIVERIES ====================

  async createWebhookDelivery(insertDelivery: InsertWebhookDelivery): Promise<WebhookDelivery> {
    const id = randomUUID();
    const delivery: WebhookDelivery = {
      ...insertDelivery,
      id,
      createdAt: new Date(),
      deliveredAt: null,
    };
    this.webhookDeliveries.set(id, delivery);
    return delivery;
  }

  async getWebhookDeliveries(apiKeyId: string, limit: number = 50): Promise<WebhookDelivery[]> {
    const deliveries = Array.from(this.webhookDeliveries.values())
      .filter((d) => d.apiKeyId === apiKeyId)
      .sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime());
    return deliveries.slice(0, limit);
  }

  async getPendingWebhookDeliveries(limit: number = 100): Promise<WebhookDelivery[]> {
    const now = new Date();
    const deliveries = Array.from(this.webhookDeliveries.values())
      .filter((d) => 
        (d.status === "pending" || d.status === "retrying") &&
        (!d.nextRetryAt || new Date(d.nextRetryAt) <= now) &&
        d.attempts < 5 // Max 5 attempts
      )
      .sort((a, b) => new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime());
    return deliveries.slice(0, limit);
  }

  async updateWebhookDelivery(id: string, data: Partial<WebhookDelivery>): Promise<WebhookDelivery | undefined> {
    const delivery = this.webhookDeliveries.get(id);
    if (!delivery) return undefined;

    const updated: WebhookDelivery = {
      ...delivery,
      ...data,
    };
    this.webhookDeliveries.set(id, updated);
    return updated;
  }
}

export const storage = new MemStorage();
