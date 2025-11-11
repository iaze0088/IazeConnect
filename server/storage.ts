import { 
  type WhatsAppConnection, 
  type InsertWhatsAppConnection,
  type WhatsAppLog,
  type InsertWhatsAppLog,
  type WhatsAppMessage,
  type InsertWhatsAppMessage
} from "@shared/schema";
import { randomUUID } from "crypto";

export interface IStorage {
  getWhatsAppConnection(id: string): Promise<WhatsAppConnection | undefined>;
  getWhatsAppConnectionBySessionName(sessionName: string): Promise<WhatsAppConnection | undefined>;
  getAllWhatsAppConnections(): Promise<WhatsAppConnection[]>;
  createWhatsAppConnection(connection: InsertWhatsAppConnection): Promise<WhatsAppConnection>;
  updateWhatsAppConnection(id: string, data: Partial<WhatsAppConnection>): Promise<WhatsAppConnection | undefined>;
  deleteWhatsAppConnection(id: string): Promise<boolean>;
  
  createWhatsAppLog(log: InsertWhatsAppLog): Promise<WhatsAppLog>;
  getAllWhatsAppLogs(limit?: number): Promise<WhatsAppLog[]>;
  
  createWhatsAppMessage(message: InsertWhatsAppMessage): Promise<WhatsAppMessage>;
  getWhatsAppMessages(connectionId: string, limit?: number): Promise<WhatsAppMessage[]>;
}

export class MemStorage implements IStorage {
  private whatsappConnections: Map<string, WhatsAppConnection>;
  private whatsappLogs: Map<string, WhatsAppLog>;
  private whatsappMessages: Map<string, WhatsAppMessage>;

  constructor() {
    this.whatsappConnections = new Map();
    this.whatsappLogs = new Map();
    this.whatsappMessages = new Map();
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
}

export const storage = new MemStorage();
