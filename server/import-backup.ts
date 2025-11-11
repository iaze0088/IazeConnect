import { readFileSync } from "fs";
import { storage } from "./storage";
import bcrypt from "bcrypt";

interface MongoBackup {
  created_at: string;
  collections: {
    resellers: any[];
    users: any[];
    clients: any[];
    agents: any[];
    tickets: any[];
    messages: any[];
    departments: any[];
    whatsapp_connections: any[];
    whatsapp_config: any[];
    [key: string]: any[];
  };
}

export async function importBackup(filePath: string) {
  console.log("[Import] Carregando backup...");
  const backupData: MongoBackup = JSON.parse(readFileSync(filePath, "utf8"));
  
  console.log("[Import] Backup carregado com sucesso");
  console.log(`[Import] Total de coleções: ${Object.keys(backupData.collections).length}`);
  
  // Log estatísticas
  const stats = {
    resellers: backupData.collections.resellers?.length || 0,
    users: backupData.collections.users?.length || 0,
    clients: backupData.collections.clients?.length || 0,
    agents: backupData.collections.agents?.length || 0,
    tickets: backupData.collections.tickets?.length || 0,
    messages: backupData.collections.messages?.length || 0,
    departments: backupData.collections.departments?.length || 0,
  };
  
  console.log("\n[Import] Estatísticas do backup:");
  Object.entries(stats).forEach(([key, value]) => {
    console.log(`  - ${key}: ${value} documentos`);
  });
  
  console.log("\n[Import] Sistema pronto para importação!");
  console.log("[Import] As collections principais foram identificadas:");
  console.log("  ✅ Revendas (resellers)");
  console.log("  ✅ Usuários/Clientes do chat (users)");
  console.log("  ✅ Clientes CRM (clients)");
  console.log("  ✅ Atendentes (agents)");
  console.log("  ✅ Departamentos (departments)");
  console.log("  ✅ Tickets de atendimento (tickets)");
  console.log("  ✅ Mensagens (messages)");
  
  return { stats, collections: backupData.collections };
}

// Estruturas identificadas do backup:
export interface MongoReseller {
  id: string;
  name: string;
  email: string;
  pass_hash: string;
  domain: string;
  custom_domain: string;
  test_domain: string;
  test_domain_active: boolean;
  is_active: boolean;
  parent_id: string | null;
  level: number;
  client_logo_url: string;
  created_at: string;
}

export interface MongoUser {
  id: string;
  whatsapp: string;  // Número WhatsApp
  pin_hash: string;  // PIN de 2 dígitos hasheado
  display_name: string;
  avatar: string;
  custom_avatar: string;
  gender: string;
  pinned_user: string;
  pinned_pass: string;
  reseller_id: string | null;
  created_at: string;
  pin: string;
}

export interface MongoClient {
  id: string;
  reseller_id: string;
  name: string;
  email: string;
  phone: string;
  whatsapp_origin: boolean;
  whatsapp_number: string | null;
  created_at: string;
}

export interface MongoAgent {
  id: string;
  name: string;
  login: string;
  pass_hash: string;
  avatar: string;
  custom_avatar: string;
  reseller_id: string;
  username: string;
  created_at: string;
}

export interface MongoDepartment {
  id: string;
  name: string;
  description: string;
  ai_agent_id: string | null;
  is_default: boolean;
  timeout_seconds: number;
  agent_ids: string[];
  origin: string;  // wa_suporte, whatsapp, wa_site
  reseller_id: string | null;
  created_at: string;
  ai_enabled: boolean;
  assigned_agents: string[];
}

export interface MongoTicket {
  id: string;
  client_id: string;
  status: string;  // PENDENTE, ATENDENDO, FINALIZADAS
  department_id: string;
  awaiting_department_choice: boolean;
  department_choice_sent_at: string;
  unread_count: number;
  reseller_id: string | null;
  ticket_origin: string;  // wa_suporte, whatsapp, wa_site
  created_at: string;
  updated_at: string;
  assigned_agent_id: string | null;
  ai_disabled_by: string | null;
}

export interface MongoMessage {
  id: string;
  ticket_id: string;
  from_type: string;  // system, client, agent, ai
  kind: string;  // text, department_selection, media, audio, etc
  text: string;
  buttons?: Array<{ id: string; label: string; description: string }>;
  created_at: string;
  reseller_id: string | null;
  media_url?: string;
  media_type?: string;
}

// Run if this is the main module
const isMain = import.meta.url === `file://${process.argv[1]}`;
if (isMain) {
  importBackup("attached_assets/backup_20251110_002339_1762885836046.json")
    .then(({ stats }) => {
      console.log("\n✅ Análise do backup concluída!");
      console.log("\nPróximos passos:");
      console.log("1. Adaptar schema PostgreSQL para match com estrutura MongoDB");
      console.log("2. Criar funções de migração para cada coleção");
      console.log("3. Importar dados preservando relacionamentos");
      console.log("4. Testar sistema com dados reais");
    })
    .catch((error) => {
      console.error("❌ Erro ao importar backup:", error);
      process.exit(1);
    });
}
