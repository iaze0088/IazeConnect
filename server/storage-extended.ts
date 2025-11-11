import { randomUUID } from "crypto";

// Tipos baseados no backup MongoDB real
export interface Reseller {
  id: string;
  name: string;
  email: string;
  passHash: string;
  domain: string;
  customDomain: string;
  testDomain: string;
  testDomainActive: boolean;
  isActive: boolean;
  parentId: string | null;
  level: number;
  clientLogoUrl: string;
  createdAt: Date;
}

export interface User {
  id: string;
  whatsapp: string;
  pinHash: string;
  displayName: string;
  avatar: string;
  customAvatar: string;
  gender: string;
  pinnedUser: string;
  pinnedPass: string;
  resellerId: string | null;
  createdAt: Date;
  pin: string;
  updatedAt?: Date;
  nameAskedAt?: Date;
}

export interface Client {
  id: string;
  resellerId: string;
  name: string;
  email: string;
  phone: string;
  whatsappOrigin: boolean;
  whatsappNumber: string | null;
  createdAt: Date;
}

export interface Agent {
  id: string;
  name: string;
  login: string;
  passHash: string;
  avatar: string;
  customAvatar: string;
  resellerId: string;
  username: string;
  createdAt: Date;
}

export interface Department {
  id: string;
  name: string;
  description: string;
  aiAgentId: string | null;
  isDefault: boolean;
  timeoutSeconds: number;
  agentIds: string[];
  origin: string;
  resellerId: string | null;
  createdAt: Date;
  aiEnabled: boolean;
  assignedAgents: string[];
}

export interface Ticket {
  id: string;
  clientId: string;
  status: "PENDENTE" | "ATENDENDO" | "FINALIZADAS";
  departmentId: string;
  awaitingDepartmentChoice: boolean;
  departmentChoiceSentAt: Date | null;
  unreadCount: number;
  resellerId: string | null;
  ticketOrigin: "wa_suporte" | "whatsapp" | "wa_site";
  createdAt: Date;
  updatedAt: Date;
  assignedAgentId: string | null;
  aiDisabledBy: string | null;
}

export interface Message {
  id: string;
  ticketId: string;
  fromType: "system" | "client" | "agent" | "ai";
  kind: string;
  text: string;
  buttons?: Array<{ id: string; label: string; description: string }>;
  createdAt: Date;
  resellerId: string | null;
  mediaUrl?: string;
  mediaType?: string;
}

export interface IExtendedStorage {
  // Resellers
  getAllResellers(): Promise<Reseller[]>;
  getResellerById(id: string): Promise<Reseller | undefined>;
  getResellerByEmail(email: string): Promise<Reseller | undefined>;
  createReseller(reseller: Omit<Reseller, 'id' | 'createdAt'>): Promise<Reseller>;
  
  // Users (clientes do chat)
  getAllUsers(): Promise<User[]>;
  getUserById(id: string): Promise<User | undefined>;
  getUserByWhatsapp(whatsapp: string, resellerId?: string): Promise<User | undefined>;
  createUser(user: Omit<User, 'id' | 'createdAt'>): Promise<User>;
  
  // Clients (CRM)
  getAllClients(resellerId?: string): Promise<Client[]>;
  getClientById(id: string): Promise<Client | undefined>;
  createClient(client: Omit<Client, 'id' | 'createdAt'>): Promise<Client>;
  
  // Agents
  getAllAgents(resellerId?: string): Promise<Agent[]>;
  getAgentById(id: string): Promise<Agent | undefined>;
  getAgentByLogin(login: string): Promise<Agent | undefined>;
  createAgent(agent: Omit<Agent, 'id' | 'createdAt'>): Promise<Agent>;
  
  // Departments
  getAllDepartments(resellerId?: string): Promise<Department[]>;
  getDepartmentById(id: string): Promise<Department | undefined>;
  createDepartment(department: Omit<Department, 'id' | 'createdAt'>): Promise<Department>;
  
  // Tickets
  getAllTickets(filters?: { resellerId?: string; status?: string; agentId?: string }): Promise<Ticket[]>;
  getTicketById(id: string): Promise<Ticket | undefined>;
  getTicketsByClientId(clientId: string): Promise<Ticket[]>;
  createTicket(ticket: Omit<Ticket, 'id' | 'createdAt' | 'updatedAt'>): Promise<Ticket>;
  updateTicket(id: string, data: Partial<Ticket>): Promise<Ticket | undefined>;
  
  // Messages
  getMessagesByTicketId(ticketId: string): Promise<Message[]>;
  createMessage(message: Omit<Message, 'id' | 'createdAt'>): Promise<Message>;
}

export class ExtendedMemStorage implements IExtendedStorage {
  private resellers: Map<string, Reseller> = new Map();
  private users: Map<string, User> = new Map();
  private clients: Map<string, Client> = new Map();
  private agents: Map<string, Agent> = new Map();
  private departments: Map<string, Department> = new Map();
  private tickets: Map<string, Ticket> = new Map();
  private messages: Map<string, Message> = new Map();

  // Resellers
  async getAllResellers(): Promise<Reseller[]> {
    return Array.from(this.resellers.values());
  }

  async getResellerById(id: string): Promise<Reseller | undefined> {
    return this.resellers.get(id);
  }

  async getResellerByEmail(email: string): Promise<Reseller | undefined> {
    return Array.from(this.resellers.values()).find(r => r.email === email);
  }

  async createReseller(data: Omit<Reseller, 'id' | 'createdAt'>): Promise<Reseller> {
    const id = randomUUID();
    const reseller: Reseller = { ...data, id, createdAt: new Date() };
    this.resellers.set(id, reseller);
    return reseller;
  }

  // Users
  async getAllUsers(): Promise<User[]> {
    return Array.from(this.users.values());
  }

  async getUserById(id: string): Promise<User | undefined> {
    return this.users.get(id);
  }

  async getUserByWhatsapp(whatsapp: string, resellerId?: string): Promise<User | undefined> {
    return Array.from(this.users.values()).find(
      u => u.whatsapp === whatsapp && (!resellerId || u.resellerId === resellerId)
    );
  }

  async createUser(data: Omit<User, 'id' | 'createdAt'>): Promise<User> {
    const id = randomUUID();
    const user: User = { ...data, id, createdAt: new Date() };
    this.users.set(id, user);
    return user;
  }

  // Clients
  async getAllClients(resellerId?: string): Promise<Client[]> {
    const clients = Array.from(this.clients.values());
    return resellerId ? clients.filter(c => c.resellerId === resellerId) : clients;
  }

  async getClientById(id: string): Promise<Client | undefined> {
    return this.clients.get(id);
  }

  async createClient(data: Omit<Client, 'id' | 'createdAt'>): Promise<Client> {
    const id = randomUUID();
    const client: Client = { ...data, id, createdAt: new Date() };
    this.clients.set(id, client);
    return client;
  }

  // Agents
  async getAllAgents(resellerId?: string): Promise<Agent[]> {
    const agents = Array.from(this.agents.values());
    return resellerId ? agents.filter(a => a.resellerId === resellerId) : agents;
  }

  async getAgentById(id: string): Promise<Agent | undefined> {
    return this.agents.get(id);
  }

  async getAgentByLogin(login: string): Promise<Agent | undefined> {
    return Array.from(this.agents.values()).find(a => a.login === login);
  }

  async createAgent(data: Omit<Agent, 'id' | 'createdAt'>): Promise<Agent> {
    const id = randomUUID();
    const agent: Agent = { ...data, id, createdAt: new Date() };
    this.agents.set(id, agent);
    return agent;
  }

  // Departments
  async getAllDepartments(resellerId?: string): Promise<Department[]> {
    const depts = Array.from(this.departments.values());
    return resellerId ? depts.filter(d => d.resellerId === resellerId) : depts;
  }

  async getDepartmentById(id: string): Promise<Department | undefined> {
    return this.departments.get(id);
  }

  async createDepartment(data: Omit<Department, 'id' | 'createdAt'>): Promise<Department> {
    const id = randomUUID();
    const dept: Department = { ...data, id, createdAt: new Date() };
    this.departments.set(id, dept);
    return dept;
  }

  // Tickets
  async getAllTickets(filters?: { resellerId?: string; status?: string; agentId?: string }): Promise<Ticket[]> {
    let tickets = Array.from(this.tickets.values());
    
    if (filters?.resellerId) {
      tickets = tickets.filter(t => t.resellerId === filters.resellerId);
    }
    if (filters?.status) {
      tickets = tickets.filter(t => t.status === filters.status);
    }
    if (filters?.agentId) {
      tickets = tickets.filter(t => t.assignedAgentId === filters.agentId);
    }
    
    return tickets.sort((a, b) => b.updatedAt.getTime() - a.updatedAt.getTime());
  }

  async getTicketById(id: string): Promise<Ticket | undefined> {
    return this.tickets.get(id);
  }

  async getTicketsByClientId(clientId: string): Promise<Ticket[]> {
    return Array.from(this.tickets.values())
      .filter(t => t.clientId === clientId)
      .sort((a, b) => b.updatedAt.getTime() - a.updatedAt.getTime());
  }

  async createTicket(data: Omit<Ticket, 'id' | 'createdAt' | 'updatedAt'>): Promise<Ticket> {
    const id = randomUUID();
    const now = new Date();
    const ticket: Ticket = { ...data, id, createdAt: now, updatedAt: now };
    this.tickets.set(id, ticket);
    return ticket;
  }

  async updateTicket(id: string, data: Partial<Ticket>): Promise<Ticket | undefined> {
    const ticket = this.tickets.get(id);
    if (!ticket) return undefined;
    
    const updated = { ...ticket, ...data, updatedAt: new Date() };
    this.tickets.set(id, updated);
    return updated;
  }

  // Messages
  async getMessagesByTicketId(ticketId: string): Promise<Message[]> {
    return Array.from(this.messages.values())
      .filter(m => m.ticketId === ticketId)
      .sort((a, b) => a.createdAt.getTime() - b.createdAt.getTime());
  }

  async createMessage(data: Omit<Message, 'id' | 'createdAt'>): Promise<Message> {
    const id = randomUUID();
    const message: Message = { ...data, id, createdAt: new Date() };
    this.messages.set(id, message);
    return message;
  }

  // Bulk import methods
  async importReseller(reseller: Reseller): Promise<void> {
    this.resellers.set(reseller.id, reseller);
  }

  async importUser(user: User): Promise<void> {
    this.users.set(user.id, user);
  }

  async importClient(client: Client): Promise<void> {
    this.clients.set(client.id, client);
  }

  async importAgent(agent: Agent): Promise<void> {
    this.agents.set(agent.id, agent);
  }

  async importDepartment(dept: Department): Promise<void> {
    this.departments.set(dept.id, dept);
  }

  async importTicket(ticket: Ticket): Promise<void> {
    this.tickets.set(ticket.id, ticket);
  }

  async importMessage(message: Message): Promise<void> {
    this.messages.set(message.id, message);
  }

  // Statistics
  getStats() {
    return {
      resellers: this.resellers.size,
      users: this.users.size,
      clients: this.clients.size,
      agents: this.agents.size,
      departments: this.departments.size,
      tickets: this.tickets.size,
      messages: this.messages.size,
    };
  }
}

export const extendedStorage = new ExtendedMemStorage();
