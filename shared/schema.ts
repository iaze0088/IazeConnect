import { sql } from "drizzle-orm";
import { pgTable, text, varchar, boolean, timestamp, jsonb, integer, index } from "drizzle-orm/pg-core";
import { createInsertSchema } from "drizzle-zod";
import { z } from "zod";

// ==================== CORE IDENTITY & TENANCY ====================

export const admins = pgTable("admins", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  email: text("email").notNull().unique(),
  passwordHash: text("password_hash").notNull(),
  superAdmin: boolean("super_admin").notNull().default(false),
  createdAt: timestamp("created_at").notNull().default(sql`now()`),
  lastLoginAt: timestamp("last_login_at"),
});

export const resellers = pgTable("resellers", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  name: text("name").notNull(),
  email: text("email").notNull().unique(),
  passwordHash: text("password_hash").notNull(),
  status: text("status").notNull().default("active"),
  planId: varchar("plan_id"),
  ownerAdminId: varchar("owner_admin_id"),
  domainPrimary: text("domain_primary"),
  settingsJson: jsonb("settings_json"),
  createdAt: timestamp("created_at").notNull().default(sql`now()`),
  updatedAt: timestamp("updated_at").notNull().default(sql`now()`),
});

export const resellerDomains = pgTable("reseller_domains", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  domain: text("domain").notNull().unique(),
  resellerId: varchar("reseller_id").notNull().references(() => resellers.id, { onDelete: "cascade" }),
  channelConfigJson: jsonb("channel_config_json"),
  createdAt: timestamp("created_at").notNull().default(sql`now()`),
}, (table) => ({
  resellerIdx: index("reseller_domains_reseller_idx").on(table.resellerId),
}));

export const resellerFeatures = pgTable("reseller_features", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  resellerId: varchar("reseller_id").notNull().references(() => resellers.id, { onDelete: "cascade" }),
  featureKey: text("feature_key").notNull(),
  enabled: boolean("enabled").notNull().default(true),
  configJson: jsonb("config_json"),
}, (table) => ({
  resellerFeatureIdx: index("reseller_features_reseller_idx").on(table.resellerId),
}));

// Unified users table for all user types
export const users = pgTable("users", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  email: text("email"),
  phone: text("phone"),
  passwordHash: text("password_hash"),
  role: text("role").notNull(), // admin | reseller | agent | client
  status: text("status").notNull().default("active"),
  lastLoginAt: timestamp("last_login_at"),
  createdAt: timestamp("created_at").notNull().default(sql`now()`),
  metadata: jsonb("metadata"),
}, (table) => ({
  emailIdx: index("users_email_idx").on(table.email),
  phoneIdx: index("users_phone_idx").on(table.phone),
}));

export const resellerMembers = pgTable("reseller_members", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  userId: varchar("user_id").notNull().references(() => users.id, { onDelete: "cascade" }),
  resellerId: varchar("reseller_id").notNull().references(() => resellers.id, { onDelete: "cascade" }),
  roleScope: text("role_scope").notNull(), // reseller | agent | manager
  departmentIds: text("department_ids").array(),
  createdAt: timestamp("created_at").notNull().default(sql`now()`),
}, (table) => ({
  userIdx: index("reseller_members_user_idx").on(table.userId),
  resellerIdx: index("reseller_members_reseller_idx").on(table.resellerId),
}));

export const clientAccounts = pgTable("client_accounts", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  userId: varchar("user_id").notNull().references(() => users.id, { onDelete: "cascade" }),
  resellerId: varchar("reseller_id").notNull().references(() => resellers.id, { onDelete: "cascade" }),
  pinHash: text("pin_hash").notNull(),
  whatsappNumber: text("whatsapp_number").notNull(),
  preferredChannel: text("preferred_channel"),
  metadata: jsonb("metadata"),
  createdAt: timestamp("created_at").notNull().default(sql`now()`),
}, (table) => ({
  resellerPhoneIdx: index("client_accounts_reseller_phone_idx").on(table.resellerId, table.whatsappNumber),
}));

export const sessions = pgTable("sessions", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  sessionId: text("session_id").notNull().unique(),
  userId: varchar("user_id").notNull().references(() => users.id, { onDelete: "cascade" }),
  role: text("role").notNull(),
  resellerId: varchar("reseller_id"),
  expiresAt: timestamp("expires_at").notNull(),
  refreshTokenHash: text("refresh_token_hash"),
  userAgent: text("user_agent"),
  ipHash: text("ip_hash"),
  createdAt: timestamp("created_at").notNull().default(sql`now()`),
}, (table) => ({
  sessionIdx: index("sessions_session_id_idx").on(table.sessionId),
}));

// ==================== SUPPORT STRUCTURE ====================

export const departments = pgTable("departments", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  resellerId: varchar("reseller_id").notNull().references(() => resellers.id, { onDelete: "cascade" }),
  name: text("name").notNull(),
  description: text("description"),
  routingRulesJson: jsonb("routing_rules_json"),
  active: boolean("active").notNull().default(true),
  createdAt: timestamp("created_at").notNull().default(sql`now()`),
}, (table) => ({
  resellerIdx: index("departments_reseller_idx").on(table.resellerId),
}));

export const customerContacts = pgTable("customer_contacts", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  customerId: varchar("customer_id").notNull().references(() => clientAccounts.id, { onDelete: "cascade" }),
  channel: text("channel").notNull(), // whatsapp | email | phone
  identifier: text("identifier").notNull(),
  verifiedAt: timestamp("verified_at"),
  createdAt: timestamp("created_at").notNull().default(sql`now()`),
});

export const tickets = pgTable("tickets", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  resellerId: varchar("reseller_id").notNull().references(() => resellers.id, { onDelete: "cascade" }),
  customerId: varchar("customer_id").notNull().references(() => clientAccounts.id, { onDelete: "cascade" }),
  departmentId: varchar("department_id").references(() => departments.id),
  assignedAgentId: varchar("assigned_agent_id"),
  status: text("status").notNull().default("pending"), // pending | attending | closed
  priority: integer("priority").notNull().default(0),
  sourceChannel: text("source_channel").notNull(), // wa_suporte | whatsapp | wa_site
  autoAssignFlag: boolean("auto_assign_flag").notNull().default(true),
  createdAt: timestamp("created_at").notNull().default(sql`now()`),
  updatedAt: timestamp("updated_at").notNull().default(sql`now()`),
  closedAt: timestamp("closed_at"),
  lastMessageAt: timestamp("last_message_at"),
}, (table) => ({
  resellerStatusIdx: index("tickets_reseller_status_idx").on(table.resellerId, table.status),
  assignedAgentIdx: index("tickets_assigned_agent_idx").on(table.assignedAgentId),
  sourceChannelIdx: index("tickets_source_channel_idx").on(table.sourceChannel),
}));

export const ticketParticipants = pgTable("ticket_participants", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  ticketId: varchar("ticket_id").notNull().references(() => tickets.id, { onDelete: "cascade" }),
  agentId: varchar("agent_id").notNull(),
  joinedAt: timestamp("joined_at").notNull().default(sql`now()`),
  leftAt: timestamp("left_at"),
});

export const messages = pgTable("messages", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  ticketId: varchar("ticket_id").notNull().references(() => tickets.id, { onDelete: "cascade" }),
  channel: text("channel").notNull(), // wa_suporte | whatsapp | wa_site
  direction: text("direction").notNull(), // inbound | outbound | system
  senderType: text("sender_type").notNull(), // client | agent | bot | integration
  senderId: varchar("sender_id"),
  contentJson: jsonb("content_json").notNull(), // { text, mediaId, templateId }
  status: text("status").notNull().default("sent"), // sent | delivered | read | failed
  createdAt: timestamp("created_at").notNull().default(sql`now()`),
  readAt: timestamp("read_at"),
}, (table) => ({
  ticketCreatedIdx: index("messages_ticket_created_idx").on(table.ticketId, table.createdAt),
}));

export const messageMedia = pgTable("message_media", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  resellerId: varchar("reseller_id").notNull().references(() => resellers.id, { onDelete: "cascade" }),
  storageKey: text("storage_key").notNull(),
  mimeType: text("mime_type").notNull(),
  size: integer("size").notNull(),
  sha256: text("sha256"),
  createdBy: varchar("created_by").notNull(),
  createdAt: timestamp("created_at").notNull().default(sql`now()`),
});

// ==================== CHANNEL INTEGRATIONS ====================

export const waInstances = pgTable("wa_instances", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  resellerId: varchar("reseller_id").notNull().references(() => resellers.id, { onDelete: "cascade" }),
  provider: text("provider").notNull(), // wppconnect | fb_ads | site_ws
  sessionName: text("session_name").notNull().unique(),
  status: text("status").notNull().default("disconnected"),
  qrCodeData: text("qr_code_data"),
  phoneNumber: text("phone_number"),
  metadata: jsonb("metadata"),
  createdAt: timestamp("created_at").notNull().default(sql`now()`),
  lastConnectedAt: timestamp("last_connected_at"),
}, (table) => ({
  resellerIdx: index("wa_instances_reseller_idx").on(table.resellerId),
}));

export const channelEndpoints = pgTable("channel_endpoints", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  resellerId: varchar("reseller_id").notNull().references(() => resellers.id, { onDelete: "cascade" }),
  channel: text("channel").notNull(), // whatsapp | wa_site | email | sms
  credentialsJson: jsonb("credentials_json"),
  webhookSecret: text("webhook_secret"),
  active: boolean("active").notNull().default(true),
  createdAt: timestamp("created_at").notNull().default(sql`now()`),
});

// ==================== AUTOMATION ====================

export const quickReplies = pgTable("quick_replies", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  resellerId: varchar("reseller_id").notNull().references(() => resellers.id, { onDelete: "cascade" }),
  name: text("name").notNull(),
  contentJson: jsonb("content_json").notNull(), // { text, mediaIds, attachments }
  visibility: text("visibility").notNull().default("reseller"), // reseller | department | agent
  departmentId: varchar("department_id"),
  agentId: varchar("agent_id"),
  createdAt: timestamp("created_at").notNull().default(sql`now()`),
}, (table) => ({
  resellerIdx: index("quick_replies_reseller_idx").on(table.resellerId),
}));

export const autoResponderSequences = pgTable("auto_responder_sequences", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  resellerId: varchar("reseller_id").notNull().references(() => resellers.id, { onDelete: "cascade" }),
  name: text("name").notNull(),
  triggerType: text("trigger_type").notNull(), // keyword | schedule | event
  rulesJson: jsonb("rules_json").notNull(),
  active: boolean("active").notNull().default(true),
  createdAt: timestamp("created_at").notNull().default(sql`now()`),
});

export const notices = pgTable("notices", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  resellerId: varchar("reseller_id").notNull().references(() => resellers.id, { onDelete: "cascade" }),
  audience: text("audience").notNull(), // admin | agent | all
  message: text("message").notNull(),
  schedule: timestamp("schedule"),
  active: boolean("active").notNull().default(true),
  createdAt: timestamp("created_at").notNull().default(sql`now()`),
});

export const aiModels = pgTable("ai_models", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  resellerId: varchar("reseller_id").notNull().references(() => resellers.id, { onDelete: "cascade" }),
  provider: text("provider").notNull(), // openai | anthropic | custom
  configJson: jsonb("config_json").notNull(),
  active: boolean("active").notNull().default(false),
  createdAt: timestamp("created_at").notNull().default(sql`now()`),
});

export const aiMemories = pgTable("ai_memories", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  resellerId: varchar("reseller_id").notNull().references(() => resellers.id, { onDelete: "cascade" }),
  conversationKey: text("conversation_key").notNull(),
  dataJson: jsonb("data_json").notNull(),
  updatedAt: timestamp("updated_at").notNull().default(sql`now()`),
});

// ==================== BILLING & INTEGRATIONS ====================

export const plans = pgTable("plans", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  name: text("name").notNull(),
  description: text("description"),
  limitsJson: jsonb("limits_json").notNull(), // { maxAgents, maxTickets, maxWhatsAppConnections, features: [] }
  priceMonthly: integer("price_monthly"),
  active: boolean("active").notNull().default(true),
  createdAt: timestamp("created_at").notNull().default(sql`now()`),
});

export const resellerPlanSubscriptions = pgTable("reseller_plan_subscriptions", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  resellerId: varchar("reseller_id").notNull().references(() => resellers.id, { onDelete: "cascade" }),
  planId: varchar("plan_id").notNull().references(() => plans.id),
  status: text("status").notNull().default("active"), // active | suspended | cancelled
  seats: integer("seats").notNull().default(1),
  whatsappLimits: integer("whatsapp_limits"),
  mercadoPagoConfigJson: jsonb("mercado_pago_config_json"),
  createdAt: timestamp("created_at").notNull().default(sql`now()`),
  expiresAt: timestamp("expires_at"),
});

export const payments = pgTable("payments", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  resellerId: varchar("reseller_id").notNull().references(() => resellers.id, { onDelete: "cascade" }),
  provider: text("provider").notNull(), // mercado_pago | manual
  amount: integer("amount").notNull(),
  status: text("status").notNull().default("pending"), // pending | approved | rejected
  detailsJson: jsonb("details_json"),
  createdAt: timestamp("created_at").notNull().default(sql`now()`),
  paidAt: timestamp("paid_at"),
});

export const externalAccounts = pgTable("external_accounts", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  resellerId: varchar("reseller_id").notNull().references(() => resellers.id, { onDelete: "cascade" }),
  type: text("type").notNull(), // mercado_pago | office | smtp | storage
  credentialsJson: jsonb("credentials_json").notNull(),
  status: text("status").notNull().default("active"),
  lastSyncAt: timestamp("last_sync_at"),
  createdAt: timestamp("created_at").notNull().default(sql`now()`),
});

export const systemBackups = pgTable("system_backups", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  type: text("type").notNull(), // full | incremental
  storageKey: text("storage_key").notNull(),
  size: integer("size"),
  status: text("status").notNull().default("completed"),
  createdBy: varchar("created_by"),
  createdAt: timestamp("created_at").notNull().default(sql`now()`),
});

// ==================== API KEYS & WEBHOOKS ====================

export const apiKeys = pgTable("api_keys", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  resellerId: varchar("reseller_id").notNull().references(() => resellers.id, { onDelete: "cascade" }),
  name: text("name").notNull(), // Human-readable label (e.g., "Outro Servidor IAZE")
  keyHash: text("key_hash").notNull(), // Hashed version of the full API key
  keyPrefix: text("key_prefix").notNull(), // First 8 chars (iaze_liv) for display
  keyLastChars: text("key_last_chars").notNull(), // Last 4 chars for display
  connectionLimit: integer("connection_limit").notNull().default(5), // Max WhatsApp connections allowed
  webhookUrl: text("webhook_url"), // URL to send webhook events
  webhookSecret: text("webhook_secret"), // Secret for HMAC signature
  webhookEvents: text("webhook_events").array().notNull().default(sql`ARRAY['message', 'status', 'qr', 'connection']::text[]`), // Events to send
  status: text("status").notNull().default("active"), // active | inactive
  currentConnections: integer("current_connections").notNull().default(0), // Live counter
  totalRequests: integer("total_requests").notNull().default(0), // Usage stats
  lastUsedAt: timestamp("last_used_at"),
  createdAt: timestamp("created_at").notNull().default(sql`now()`),
}, (table) => ({
  resellerIdx: index("api_keys_reseller_idx").on(table.resellerId),
  keyHashIdx: index("api_keys_key_hash_idx").on(table.keyHash),
}));

export const apiKeyConnections = pgTable("api_key_connections", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  apiKeyId: varchar("api_key_id").notNull().references(() => apiKeys.id, { onDelete: "cascade" }),
  connectionId: varchar("connection_id").notNull().references(() => waInstances.id, { onDelete: "cascade" }),
  createdAt: timestamp("created_at").notNull().default(sql`now()`),
}, (table) => ({
  apiKeyIdx: index("api_key_connections_key_idx").on(table.apiKeyId),
  connectionIdx: index("api_key_connections_conn_idx").on(table.connectionId),
}));

export const webhookDeliveries = pgTable("webhook_deliveries", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  apiKeyId: varchar("api_key_id").notNull().references(() => apiKeys.id, { onDelete: "cascade" }),
  eventType: text("event_type").notNull(), // message | status | qr | connection
  payload: jsonb("payload").notNull(),
  status: text("status").notNull().default("pending"), // pending | success | failed | retrying
  attempts: integer("attempts").notNull().default(0),
  lastError: text("last_error"),
  nextRetryAt: timestamp("next_retry_at"),
  deliveredAt: timestamp("delivered_at"),
  createdAt: timestamp("created_at").notNull().default(sql`now()`),
}, (table) => ({
  apiKeyIdx: index("webhook_deliveries_key_idx").on(table.apiKeyId),
  statusIdx: index("webhook_deliveries_status_idx").on(table.status),
  nextRetryIdx: index("webhook_deliveries_retry_idx").on(table.nextRetryAt),
}));

// ==================== INSERT SCHEMAS & TYPES ====================

// Admins
export const insertAdminSchema = createInsertSchema(admins).omit({ id: true, createdAt: true, lastLoginAt: true });
export type InsertAdmin = z.infer<typeof insertAdminSchema>;
export type Admin = typeof admins.$inferSelect;

// Resellers
export const insertResellerSchema = createInsertSchema(resellers).omit({ id: true, createdAt: true, updatedAt: true });
export type InsertReseller = z.infer<typeof insertResellerSchema>;
export type Reseller = typeof resellers.$inferSelect;

// Users
export const insertUserSchema = createInsertSchema(users).omit({ id: true, createdAt: true, lastLoginAt: true });
export type InsertUser = z.infer<typeof insertUserSchema>;
export type User = typeof users.$inferSelect;

// Client Accounts
export const insertClientAccountSchema = createInsertSchema(clientAccounts).omit({ id: true, createdAt: true });
export type InsertClientAccount = z.infer<typeof insertClientAccountSchema>;
export type ClientAccount = typeof clientAccounts.$inferSelect;

// Departments
export const insertDepartmentSchema = createInsertSchema(departments).omit({ id: true, createdAt: true });
export type InsertDepartment = z.infer<typeof insertDepartmentSchema>;
export type Department = typeof departments.$inferSelect;

// Tickets
export const insertTicketSchema = createInsertSchema(tickets).omit({ id: true, createdAt: true, updatedAt: true, closedAt: true, lastMessageAt: true });
export type InsertTicket = z.infer<typeof insertTicketSchema>;
export type Ticket = typeof tickets.$inferSelect;

// Messages
export const insertMessageSchema = createInsertSchema(messages).omit({ id: true, createdAt: true, readAt: true });
export type InsertMessage = z.infer<typeof insertMessageSchema>;
export type Message = typeof messages.$inferSelect;

// WA Instances
export const insertWaInstanceSchema = createInsertSchema(waInstances).omit({ id: true, createdAt: true, lastConnectedAt: true, qrCodeData: true });
export type InsertWaInstance = z.infer<typeof insertWaInstanceSchema>;
export type WaInstance = typeof waInstances.$inferSelect;

// Quick Replies
export const insertQuickReplySchema = createInsertSchema(quickReplies).omit({ id: true, createdAt: true });
export type InsertQuickReply = z.infer<typeof insertQuickReplySchema>;
export type QuickReply = typeof quickReplies.$inferSelect;

// Plans
export const insertPlanSchema = createInsertSchema(plans).omit({ id: true, createdAt: true });
export type InsertPlan = z.infer<typeof insertPlanSchema>;
export type Plan = typeof plans.$inferSelect;

// API Keys
export const insertApiKeySchema = createInsertSchema(apiKeys).omit({ 
  id: true, 
  createdAt: true, 
  lastUsedAt: true,
  currentConnections: true,
  totalRequests: true,
  keyHash: true,
  keyPrefix: true,
  keyLastChars: true,
});
export type InsertApiKey = z.infer<typeof insertApiKeySchema>;
export type ApiKey = typeof apiKeys.$inferSelect;

// API Key Connections
export const insertApiKeyConnectionSchema = createInsertSchema(apiKeyConnections).omit({ id: true, createdAt: true });
export type InsertApiKeyConnection = z.infer<typeof insertApiKeyConnectionSchema>;
export type ApiKeyConnection = typeof apiKeyConnections.$inferSelect;

// Webhook Deliveries
export const insertWebhookDeliverySchema = createInsertSchema(webhookDeliveries).omit({ id: true, createdAt: true, deliveredAt: true });
export type InsertWebhookDelivery = z.infer<typeof insertWebhookDeliverySchema>;
export type WebhookDelivery = typeof webhookDeliveries.$inferSelect;

// ==================== BACKWARD COMPATIBILITY (temporary) ====================
// Aliases for existing code that uses old WhatsApp naming
export const whatsappConnections = waInstances;
export type WhatsAppConnection = WaInstance;
export const insertWhatsAppConnectionSchema = insertWaInstanceSchema;
export type InsertWhatsAppConnection = InsertWaInstance;

// WhatsAppMessage and WhatsAppLog compatibility
export const whatsappMessages = pgTable("whatsapp_messages_legacy", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  connectionId: varchar("connection_id").notNull(),
  fromNumber: text("from_number").notNull(),
  toNumber: text("to_number").notNull(),
  message: text("message").notNull(),
  messageType: text("message_type").notNull().default("text"),
  timestamp: timestamp("timestamp").notNull().default(sql`now()`),
  isIncoming: boolean("is_incoming").notNull().default(true),
  metadata: jsonb("metadata"),
});

export const whatsappLogs = pgTable("whatsapp_logs_legacy", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  connectionId: varchar("connection_id"),
  level: text("level").notNull().default("info"),
  message: text("message").notNull(),
  timestamp: timestamp("timestamp").notNull().default(sql`now()`),
  metadata: jsonb("metadata"),
});

export const insertWhatsAppMessageSchema = createInsertSchema(whatsappMessages).omit({ id: true, timestamp: true });
export const insertWhatsAppLogSchema = createInsertSchema(whatsappLogs).omit({ id: true, timestamp: true });

export type WhatsAppMessage = typeof whatsappMessages.$inferSelect;
export type InsertWhatsAppMessage = z.infer<typeof insertWhatsAppMessageSchema>;
export type WhatsAppLog = typeof whatsappLogs.$inferSelect;
export type InsertWhatsAppLog = z.infer<typeof insertWhatsAppLogSchema>;
