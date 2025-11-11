import { randomBytes, createHash, createHmac } from "crypto";
import { storage } from "../storage";
import type { ApiKey, InsertApiKey } from "@shared/schema";
import { randomUUID } from "crypto";

/**
 * API Key Format: iaze_live_<40 random chars>
 * Example: iaze_live_k3m9p2x7q5n8w1z4h6j0r9t2y5u8v1b3
 * 
 * Storage: Hash completo, armazenar apenas prefix (8) e suffix (4) para display
 */

export class ApiKeyService {
  /**
   * Gera uma nova API key com formato iaze_live_<40 chars>
   * Retorna: { fullKey, hash, prefix, suffix }
   */
  static generateApiKey(): {
    fullKey: string;
    keyHash: string;
    keyPrefix: string;
    keyLastChars: string;
  } {
    // Gerar 30 bytes aleatórios (40 chars em base32-like)
    const randomPart = randomBytes(30)
      .toString("base64")
      .replace(/\+/g, "x")
      .replace(/\//g, "z")
      .replace(/=/g, "")
      .substring(0, 40)
      .toLowerCase();

    const fullKey = `iaze_live_${randomPart}`;

    // Hash da chave completa para armazenamento
    const keyHash = createHash("sha256").update(fullKey).digest("hex");

    // Prefix e suffix para display
    const keyPrefix = fullKey.substring(0, 13); // "iaze_live_k3m"
    const keyLastChars = fullKey.substring(fullKey.length - 4); // últimos 4 chars

    return {
      fullKey,
      keyHash,
      keyPrefix,
      keyLastChars,
    };
  }

  /**
   * Gera segredo webhook (32 bytes hex)
   */
  static generateWebhookSecret(): string {
    return randomBytes(32).toString("hex");
  }

  /**
   * Valida uma API key fornecida contra o hash armazenado
   */
  static validateApiKey(providedKey: string, storedHash: string): boolean {
    const providedHash = createHash("sha256").update(providedKey).digest("hex");
    return providedHash === storedHash;
  }

  /**
   * Busca API key a partir do token fornecido
   */
  static async authenticateApiKey(apiKeyToken: string): Promise<ApiKey | null> {
    if (!apiKeyToken.startsWith("iaze_live_")) {
      return null;
    }

    const hash = createHash("sha256").update(apiKeyToken).digest("hex");
    const apiKey = await storage.getApiKeyByHash(hash);

    if (!apiKey || apiKey.status !== "active") {
      return null;
    }

    return apiKey;
  }

  /**
   * Cria nova API key completa
   */
  static async createApiKey(
    data: Omit<InsertApiKey, "keyHash" | "keyPrefix" | "keyLastChars">
  ): Promise<{ apiKey: ApiKey; fullKey: string }> {
    const { fullKey, keyHash, keyPrefix, keyLastChars } = this.generateApiKey();

    // Gerar webhook secret se webhookUrl foi fornecido
    const webhookSecret = data.webhookUrl
      ? this.generateWebhookSecret()
      : null;

    const apiKeyRecord: ApiKey = {
      id: randomUUID(),
      resellerId: data.resellerId,
      name: data.name,
      keyHash,
      keyPrefix,
      keyLastChars,
      connectionLimit: data.connectionLimit || 5,
      webhookUrl: data.webhookUrl || null,
      webhookSecret,
      webhookEvents: data.webhookEvents || ["message", "status", "qr", "connection"],
      status: data.status || "active",
      currentConnections: 0,
      totalRequests: 0,
      lastUsedAt: null,
      createdAt: new Date(),
    };

    const created = await storage.createApiKey(apiKeyRecord);

    return {
      apiKey: created,
      fullKey, // Retorna a chave completa APENAS na criação
    };
  }

  /**
   * Rotaciona (regenera) uma API key existente
   */
  static async rotateApiKey(apiKeyId: string): Promise<{ apiKey: ApiKey; fullKey: string } | null> {
    const existing = await storage.getApiKey(apiKeyId);
    if (!existing) return null;

    const { fullKey, keyHash, keyPrefix, keyLastChars } = this.generateApiKey();

    const updated = await storage.updateApiKey(apiKeyId, {
      keyHash,
      keyPrefix,
      keyLastChars,
    });

    if (!updated) return null;

    return {
      apiKey: updated,
      fullKey,
    };
  }

  /**
   * Verifica se API key pode criar mais conexões
   */
  static async canCreateConnection(apiKeyId: string): Promise<boolean> {
    const apiKey = await storage.getApiKey(apiKeyId);
    if (!apiKey || apiKey.status !== "active") {
      return false;
    }

    const currentCount = await storage.countApiKeyConnections(apiKeyId);
    return currentCount < apiKey.connectionLimit;
  }

  /**
   * Calcula assinatura HMAC para webhook payload
   */
  static signWebhookPayload(payload: string, secret: string): string {
    const hmac = createHmac("sha256", secret);
    hmac.update(payload);
    return `sha256=${hmac.digest("hex")}`;
  }

  /**
   * Valida assinatura HMAC de webhook
   */
  static verifyWebhookSignature(
    payload: string,
    signature: string,
    secret: string
  ): boolean {
    const expectedSignature = this.signWebhookPayload(payload, secret);
    return signature === expectedSignature;
  }
}
