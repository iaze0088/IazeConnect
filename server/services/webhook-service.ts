import axios from "axios";
import { storage } from "../storage";
import { ApiKeyService } from "./api-key-service";
import type { InsertWebhookDelivery, WebhookDelivery } from "@shared/schema";
import { randomUUID } from "crypto";

export type WebhookEventType = "message" | "status" | "qr" | "connection";

export interface WebhookPayload {
  eventType: WebhookEventType;
  timestamp: Date;
  resellerId: string;
  source: {
    connectionId: string;
    sessionName: string;
  };
  data: any;
}

export class WebhookService {
  private static processing = false;
  private static processInterval: NodeJS.Timeout | null = null;

  /**
   * Inicia o worker de processamento de webhooks
   */
  static startWorker() {
    if (this.processInterval) {
      console.log("[Webhook Worker] Já está em execução");
      return;
    }

    console.log("[Webhook Worker] Iniciando processamento de webhooks...");
    
    // Processar a cada 10 segundos
    this.processInterval = setInterval(() => {
      this.processWebhookQueue().catch((err) => {
        console.error("[Webhook Worker] Erro ao processar fila:", err);
      });
    }, 10000);

    // Processar imediatamente
    this.processWebhookQueue().catch((err) => {
      console.error("[Webhook Worker] Erro ao processar fila:", err);
    });
  }

  /**
   * Para o worker de processamento
   */
  static stopWorker() {
    if (this.processInterval) {
      clearInterval(this.processInterval);
      this.processInterval = null;
      console.log("[Webhook Worker] Parado");
    }
  }

  /**
   * Dispara um webhook para uma API key
   */
  static async triggerWebhook(
    apiKeyId: string,
    eventType: WebhookEventType,
    payload: WebhookPayload
  ): Promise<void> {
    const apiKey = await storage.getApiKey(apiKeyId);
    
    if (!apiKey || apiKey.status !== "active") {
      console.log(`[Webhook] API Key ${apiKeyId} não está ativa, ignorando`);
      return;
    }

    // Verificar se o evento está habilitado
    if (!apiKey.webhookEvents.includes(eventType)) {
      console.log(`[Webhook] Evento ${eventType} não habilitado para ${apiKey.name}`);
      return;
    }

    if (!apiKey.webhookUrl) {
      console.log(`[Webhook] Nenhuma URL de webhook configurada para ${apiKey.name}`);
      return;
    }

    // Criar registro de entrega
    const deliveryData: InsertWebhookDelivery = {
      apiKeyId,
      eventType,
      payload,
      status: "pending",
      attempts: 0,
      nextRetryAt: null,
      responseStatus: null,
      responseBody: null,
      errorMessage: null,
    };

    await storage.createWebhookDelivery(deliveryData);
    console.log(`[Webhook] Enfileirado webhook ${eventType} para ${apiKey.name}`);
  }

  /**
   * Processa a fila de webhooks pendentes
   */
  private static async processWebhookQueue(): Promise<void> {
    if (this.processing) {
      return;
    }

    this.processing = true;

    try {
      const pendingDeliveries = await storage.getPendingWebhookDeliveries(50);
      
      if (pendingDeliveries.length === 0) {
        return;
      }

      console.log(`[Webhook Worker] Processando ${pendingDeliveries.length} webhooks pendentes`);

      // Processar em paralelo (max 10 simultâneos)
      const chunks = this.chunkArray(pendingDeliveries, 10);
      
      for (const chunk of chunks) {
        await Promise.all(
          chunk.map((delivery) => this.deliverWebhook(delivery))
        );
      }
    } finally {
      this.processing = false;
    }
  }

  /**
   * Entrega um webhook específico
   */
  private static async deliverWebhook(delivery: WebhookDelivery): Promise<void> {
    const apiKey = await storage.getApiKey(delivery.apiKeyId);
    
    if (!apiKey || !apiKey.webhookUrl || !apiKey.webhookSecret) {
      await storage.updateWebhookDelivery(delivery.id, {
        status: "failed",
        errorMessage: "API Key ou webhook URL não encontrados",
      });
      return;
    }

    try {
      const payloadString = JSON.stringify(delivery.payload);
      const signature = ApiKeyService.signWebhookPayload(payloadString, apiKey.webhookSecret);

      const response = await axios.post(apiKey.webhookUrl, delivery.payload, {
        headers: {
          "Content-Type": "application/json",
          "X-IAZE-Signature": signature,
          "X-IAZE-Event": delivery.eventType,
          "X-IAZE-Delivery-ID": delivery.id,
        },
        timeout: 30000, // 30 segundos
        validateStatus: () => true, // Aceitar qualquer status code
      });

      const success = response.status >= 200 && response.status < 300;

      if (success) {
        await storage.updateWebhookDelivery(delivery.id, {
          status: "success",
          attempts: delivery.attempts + 1,
          deliveredAt: new Date(),
          responseStatus: response.status,
          responseBody: JSON.stringify(response.data).substring(0, 1000),
        });

        console.log(`[Webhook] ✓ Entregue: ${delivery.eventType} para ${apiKey.name} (${response.status})`);
      } else {
        await this.handleWebhookFailure(delivery, response.status, response.data);
      }
    } catch (error: any) {
      await this.handleWebhookFailure(
        delivery,
        null,
        error.message || "Erro desconhecido"
      );
    }
  }

  /**
   * Trata falha de webhook com retry logic
   */
  private static async handleWebhookFailure(
    delivery: WebhookDelivery,
    responseStatus: number | null,
    errorData: any
  ): Promise<void> {
    const newAttempts = delivery.attempts + 1;
    const maxAttempts = 5;

    // Backoff exponencial: 1m, 5m, 15m, 1h, 4h
    const retryDelays = [60, 300, 900, 3600, 14400]; // em segundos
    const retryDelay = retryDelays[Math.min(newAttempts - 1, retryDelays.length - 1)];

    const nextRetryAt =
      newAttempts < maxAttempts
        ? new Date(Date.now() + retryDelay * 1000)
        : null;

    const status = newAttempts >= maxAttempts ? "failed" : "retrying";

    await storage.updateWebhookDelivery(delivery.id, {
      status,
      attempts: newAttempts,
      nextRetryAt,
      responseStatus,
      responseBody: JSON.stringify(errorData).substring(0, 1000),
      errorMessage: typeof errorData === "string" ? errorData : errorData.message || "Erro ao entregar webhook",
    });

    const apiKey = await storage.getApiKey(delivery.apiKeyId);
    const keyName = apiKey?.name || delivery.apiKeyId;

    if (status === "failed") {
      console.error(`[Webhook] ✗ FALHOU DEFINITIVAMENTE: ${delivery.eventType} para ${keyName} (${newAttempts}/${maxAttempts})`);
    } else {
      console.warn(`[Webhook] ⟳ Retry ${newAttempts}/${maxAttempts}: ${delivery.eventType} para ${keyName} (próxima em ${retryDelay}s)`);
    }
  }

  /**
   * Divide array em chunks
   */
  private static chunkArray<T>(array: T[], size: number): T[][] {
    const chunks: T[][] = [];
    for (let i = 0; i < array.length; i += size) {
      chunks.push(array.slice(i, i + size));
    }
    return chunks;
  }

  /**
   * Dispara webhooks para eventos de uma conexão WhatsApp
   */
  static async notifyWhatsAppEvent(
    connectionId: string,
    sessionName: string,
    resellerId: string,
    eventType: WebhookEventType,
    data: any
  ): Promise<void> {
    // Buscar todas as API keys ativas com webhooks habilitados
    const allKeys = await storage.getAllApiKeys();
    const activeKeys = allKeys.filter(
      (key) =>
        key.status === "active" &&
        key.webhookUrl &&
        key.webhookEvents.includes(eventType)
    );

    if (activeKeys.length === 0) {
      return;
    }

    const payload: WebhookPayload = {
      eventType,
      timestamp: new Date(),
      resellerId,
      source: {
        connectionId,
        sessionName,
      },
      data,
    };

    // Disparar webhooks para todas as keys
    await Promise.all(
      activeKeys.map((key) =>
        this.triggerWebhook(key.id, eventType, payload)
      )
    );

    console.log(`[Webhook] Notificou ${activeKeys.length} API keys sobre evento ${eventType}`);
  }
}
