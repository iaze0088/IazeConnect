import { sql } from "drizzle-orm";
import { pgTable, text, varchar, boolean, timestamp, jsonb } from "drizzle-orm/pg-core";
import { createInsertSchema } from "drizzle-zod";
import { z } from "zod";

export const whatsappConnections = pgTable("whatsapp_connections", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  sessionName: text("session_name").notNull().unique(),
  phoneNumber: text("phone_number"),
  status: text("status").notNull().default("disconnected"),
  connected: boolean("connected").notNull().default(false),
  qrCode: text("qr_code"),
  lastConnectedAt: timestamp("last_connected_at"),
  createdAt: timestamp("created_at").notNull().default(sql`now()`),
  updatedAt: timestamp("updated_at").notNull().default(sql`now()`),
  metadata: jsonb("metadata"),
});

export const whatsappMessages = pgTable("whatsapp_messages", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  connectionId: varchar("connection_id").notNull().references(() => whatsappConnections.id, { onDelete: "cascade" }),
  fromNumber: text("from_number").notNull(),
  toNumber: text("to_number").notNull(),
  message: text("message").notNull(),
  messageType: text("message_type").notNull().default("text"),
  timestamp: timestamp("timestamp").notNull().default(sql`now()`),
  isIncoming: boolean("is_incoming").notNull().default(true),
  metadata: jsonb("metadata"),
});

export const whatsappLogs = pgTable("whatsapp_logs", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  connectionId: varchar("connection_id").references(() => whatsappConnections.id, { onDelete: "cascade" }),
  level: text("level").notNull().default("info"),
  message: text("message").notNull(),
  timestamp: timestamp("timestamp").notNull().default(sql`now()`),
  metadata: jsonb("metadata"),
});

export const insertWhatsAppConnectionSchema = createInsertSchema(whatsappConnections).omit({
  id: true,
  createdAt: true,
  updatedAt: true,
  qrCode: true,
  lastConnectedAt: true,
});

export const insertWhatsAppMessageSchema = createInsertSchema(whatsappMessages).omit({
  id: true,
  timestamp: true,
});

export const insertWhatsAppLogSchema = createInsertSchema(whatsappLogs).omit({
  id: true,
  timestamp: true,
});

export type InsertWhatsAppConnection = z.infer<typeof insertWhatsAppConnectionSchema>;
export type WhatsAppConnection = typeof whatsappConnections.$inferSelect;

export type InsertWhatsAppMessage = z.infer<typeof insertWhatsAppMessageSchema>;
export type WhatsAppMessage = typeof whatsappMessages.$inferSelect;

export type InsertWhatsAppLog = z.infer<typeof insertWhatsAppLogSchema>;
export type WhatsAppLog = typeof whatsappLogs.$inferSelect;
