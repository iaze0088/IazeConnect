import { readFileSync } from "fs";
import { extendedStorage } from "./storage-extended";
import type { Reseller, User, Client, Agent, Department, Ticket, Message } from "./storage-extended";

interface MongoBackup {
  created_at: string;
  collections: {
    resellers: any[];
    users: any[];
    clients: any[];
    agents: any[];
    departments: any[];
    tickets: any[];
    messages: any[];
    [key: string]: any[];
  };
}

export async function importAllData(filePath: string) {
  console.log("\n🚀 [Import] Iniciando importação completa do backup...\n");
  
  const backup: MongoBackup = JSON.parse(readFileSync(filePath, "utf8"));
  
  let stats = {
    resellers: 0,
    users: 0,
    clients: 0,
    agents: 0,
    departments: 0,
    tickets: 0,
    messages: 0,
  };

  // 1. Import Resellers
  console.log("📦 Importando Revendas...");
  for (const doc of backup.collections.resellers || []) {
    const reseller: Reseller = {
      id: doc.id,
      name: doc.name,
      email: doc.email,
      passHash: doc.pass_hash,
      domain: doc.domain || "",
      customDomain: doc.custom_domain || "",
      testDomain: doc.test_domain || "",
      testDomainActive: doc.test_domain_active || false,
      isActive: doc.is_active !== false,
      parentId: doc.parent_id || null,
      level: doc.level || 0,
      clientLogoUrl: doc.client_logo_url || "",
      createdAt: new Date(doc.created_at),
    };
    await extendedStorage.importReseller(reseller);
    stats.resellers++;
  }
  console.log(`  ✅ ${stats.resellers} revendas importadas`);

  // 2. Import Users (clientes do chat)
  console.log("📦 Importando Usuários do Chat...");
  for (const doc of backup.collections.users || []) {
    const user: User = {
      id: doc.id,
      whatsapp: doc.whatsapp,
      pinHash: doc.pin_hash,
      displayName: doc.display_name || "",
      avatar: doc.avatar || "",
      customAvatar: doc.custom_avatar || "",
      gender: doc.gender || "",
      pinnedUser: doc.pinned_user || "",
      pinnedPass: doc.pinned_pass || "",
      resellerId: doc.reseller_id || null,
      createdAt: new Date(doc.created_at),
      pin: doc.pin || "",
      updatedAt: doc.updated_at ? new Date(doc.updated_at) : undefined,
      nameAskedAt: doc.name_asked_at ? new Date(doc.name_asked_at) : undefined,
    };
    await extendedStorage.importUser(user);
    stats.users++;
  }
  console.log(`  ✅ ${stats.users} usuários importados`);

  // 3. Import Clients (CRM)
  console.log("📦 Importando Clientes CRM...");
  for (const doc of backup.collections.clients || []) {
    const client: Client = {
      id: doc.id,
      resellerId: doc.reseller_id,
      name: doc.name,
      email: doc.email,
      phone: doc.phone,
      whatsappOrigin: doc.whatsapp_origin || false,
      whatsappNumber: doc.whatsapp_number || null,
      createdAt: new Date(doc.created_at),
    };
    await extendedStorage.importClient(client);
    stats.clients++;
  }
  console.log(`  ✅ ${stats.clients} clientes importados`);

  // 4. Import Agents
  console.log("📦 Importando Atendentes...");
  for (const doc of backup.collections.agents || []) {
    const agent: Agent = {
      id: doc.id,
      name: doc.name,
      login: doc.login,
      passHash: doc.pass_hash,
      avatar: doc.avatar || "",
      customAvatar: doc.custom_avatar || "",
      resellerId: doc.reseller_id,
      username: doc.username || doc.login,
      createdAt: new Date(doc.created_at),
    };
    await extendedStorage.importAgent(agent);
    stats.agents++;
  }
  console.log(`  ✅ ${stats.agents} atendentes importados`);

  // 5. Import Departments
  console.log("📦 Importando Departamentos...");
  for (const doc of backup.collections.departments || []) {
    const dept: Department = {
      id: doc.id,
      name: doc.name,
      description: doc.description || "",
      aiAgentId: doc.ai_agent_id || null,
      isDefault: doc.is_default || false,
      timeoutSeconds: doc.timeout_seconds || 300,
      agentIds: doc.agent_ids || [],
      origin: doc.origin || "wa_suporte",
      resellerId: doc.reseller_id || null,
      createdAt: new Date(doc.created_at),
      aiEnabled: doc.ai_enabled || false,
      assignedAgents: doc.assigned_agents || [],
    };
    await extendedStorage.importDepartment(dept);
    stats.departments++;
  }
  console.log(`  ✅ ${stats.departments} departamentos importados`);

  // 6. Import Tickets
  console.log("📦 Importando Tickets de Atendimento...");
  for (const doc of backup.collections.tickets || []) {
    const ticket: Ticket = {
      id: doc.id,
      clientId: doc.client_id,
      status: doc.status as any,
      departmentId: doc.department_id,
      awaitingDepartmentChoice: doc.awaiting_department_choice || false,
      departmentChoiceSentAt: doc.department_choice_sent_at ? new Date(doc.department_choice_sent_at) : null,
      unreadCount: doc.unread_count || 0,
      resellerId: doc.reseller_id || null,
      ticketOrigin: doc.ticket_origin as any,
      createdAt: new Date(doc.created_at),
      updatedAt: new Date(doc.updated_at || doc.created_at),
      assignedAgentId: doc.assigned_agent_id || null,
      aiDisabledBy: doc.ai_disabled_by || null,
    };
    await extendedStorage.importTicket(ticket);
    stats.tickets++;
  }
  console.log(`  ✅ ${stats.tickets} tickets importados`);

  // 7. Import Messages
  console.log("📦 Importando Mensagens...");
  for (const doc of backup.collections.messages || []) {
    const message: Message = {
      id: doc.id,
      ticketId: doc.ticket_id,
      fromType: doc.from_type as any,
      kind: doc.kind,
      text: doc.text || "",
      buttons: doc.buttons,
      createdAt: new Date(doc.created_at),
      resellerId: doc.reseller_id || null,
      mediaUrl: doc.media_url,
      mediaType: doc.media_type,
    };
    await extendedStorage.importMessage(message);
    stats.messages++;
  }
  console.log(`  ✅ ${stats.messages} mensagens importadas`);

  console.log("\n✨ Importação Completa!\n");
  console.log("📊 Estatísticas Finais:");
  console.log(`  • Revendas: ${stats.resellers}`);
  console.log(`  • Usuários: ${stats.users}`);
  console.log(`  • Clientes CRM: ${stats.clients}`);
  console.log(`  • Atendentes: ${stats.agents}`);
  console.log(`  • Departamentos: ${stats.departments}`);
  console.log(`  • Tickets: ${stats.tickets}`);
  console.log(`  • Mensagens: ${stats.messages}`);
  console.log(`  • TOTAL: ${Object.values(stats).reduce((a, b) => a + b, 0)} registros\n`);

  return stats;
}

// Execute import if running directly
const isMain = import.meta.url === `file://${process.argv[1]}`;
if (isMain) {
  importAllData("attached_assets/backup_20251110_002339_1762885836046.json")
    .then((stats) => {
      console.log("✅ Sistema pronto com dados reais do backup!");
      console.log("\nDados carregados na memória:");
      console.log(JSON.stringify(stats, null, 2));
    })
    .catch((error) => {
      console.error("❌ Erro na importação:", error);
      process.exit(1);
    });
}
