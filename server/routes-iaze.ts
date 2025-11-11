import { Router } from "express";
import { extendedStorage } from "./storage-extended";
import bcrypt from "bcrypt";
import { generateToken, authMiddleware, requireRole } from "./auth";

const router = Router();

// ==================== AUTHENTICATION ROUTES ====================

// Login Admin
router.post("/api/auth/admin/login", async (req, res) => {
  try {
    const { password } = req.body;
    
    // Admin com hash adequado (senha: 102030@ab)
    const adminPasswordHash = "$2b$12$C9d09a9SAMLHD17fECdsEOmEPH.Qu1R2RScUkn.2rmcAwPFZGT2Sy";
    const isValid = await bcrypt.compare(password, adminPasswordHash);
    
    if (!isValid) {
      return res.status(401).json({ error: "Senha inválida" });
    }
    
    // Gerar JWT assinado
    const adminId = "admin_system";
    const token = generateToken({ 
      id: adminId, 
      role: "admin" 
    });
    
    res.json({ 
      success: true, 
      user: { 
        id: adminId,
        role: "admin", 
        name: "Administrador" 
      },
      token
    });
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

// Login Revenda
router.post("/api/auth/reseller/login", async (req, res) => {
  try {
    const { email, password } = req.body;
    
    const reseller = await extendedStorage.getResellerByEmail(email);
    if (!reseller) {
      return res.status(401).json({ error: "Email ou senha inválidos" });
    }
    
    const isValid = await bcrypt.compare(password, reseller.passHash);
    if (!isValid) {
      return res.status(401).json({ error: "Email ou senha inválidos" });
    }
    
    const token = generateToken({
      id: reseller.id,
      role: "reseller",
      resellerId: reseller.id,
    });
    
    res.json({ 
      success: true, 
      user: { 
        id: reseller.id,
        role: "reseller", 
        name: reseller.name,
        email: reseller.email,
        customDomain: reseller.customDomain,
      },
      token
    });
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

// Login Atendente
router.post("/api/auth/agent/login", async (req, res) => {
  try {
    const { login, password } = req.body;
    
    const agent = await extendedStorage.getAgentByLogin(login);
    if (!agent) {
      return res.status(401).json({ error: "Login ou senha inválidos" });
    }
    
    const isValid = await bcrypt.compare(password, agent.passHash);
    if (!isValid) {
      return res.status(401).json({ error: "Login ou senha inválidos" });
    }
    
    const token = generateToken({
      id: agent.id,
      role: "agent",
      resellerId: agent.resellerId,
    });
    
    res.json({ 
      success: true, 
      user: { 
        id: agent.id,
        role: "agent", 
        name: agent.name,
        login: agent.login,
        resellerId: agent.resellerId,
      },
      token
    });
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

// Login Cliente (WhatsApp + PIN)
router.post("/api/auth/client/login", async (req, res) => {
  try {
    const { whatsapp, pin } = req.body;
    
    const user = await extendedStorage.getUserByWhatsapp(whatsapp);
    if (!user) {
      return res.status(404).json({ error: "Usuário não encontrado. Primeiro acesso?" });
    }
    
    const isValid = await bcrypt.compare(pin, user.pinHash);
    if (!isValid) {
      return res.status(401).json({ error: "PIN incorreto" });
    }
    
    const token = generateToken({
      id: user.id,
      role: "client",
      whatsapp: user.whatsapp,
      resellerId: user.resellerId,
    });
    
    res.json({ 
      success: true, 
      user: { 
        id: user.id,
        role: "client", 
        whatsapp: user.whatsapp,
        displayName: user.displayName,
        avatar: user.customAvatar || user.avatar,
      },
      token
    });
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

// Registro Cliente (WhatsApp + criar PIN)
router.post("/api/auth/client/register", async (req, res) => {
  try {
    const { whatsapp, pin } = req.body;
    
    // Verificar se já existe
    const existing = await extendedStorage.getUserByWhatsapp(whatsapp);
    if (existing) {
      return res.status(400).json({ error: "WhatsApp já cadastrado" });
    }
    
    // Criar usuário (apenas com hash, SEM texto plano)
    const pinHash = await bcrypt.hash(pin, 12);
    const user = await extendedStorage.createUser({
      whatsapp,
      pinHash,
      pin: "", // NÃO armazenar PIN em texto plano
      displayName: "",
      avatar: "",
      customAvatar: "",
      gender: "",
      pinnedUser: "",
      pinnedPass: "",
      resellerId: null,
    });
    
    const token = generateToken({
      id: user.id,
      role: "client",
      whatsapp: user.whatsapp,
      resellerId: user.resellerId,
    });
    
    res.json({ 
      success: true, 
      user: { 
        id: user.id,
        role: "client",
        whatsapp: user.whatsapp,
        displayName: user.displayName,
      },
      token,
      message: "Cadastro realizado com sucesso!"
    });
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

// ==================== RESELLER ROUTES ====================

router.get("/api/resellers", async (req, res) => {
  try {
    const resellers = await extendedStorage.getAllResellers();
    res.json(resellers);
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

router.get("/api/resellers/:id", async (req, res) => {
  try {
    const reseller = await extendedStorage.getResellerById(req.params.id);
    if (!reseller) {
      return res.status(404).json({ error: "Revenda não encontrada" });
    }
    res.json(reseller);
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

// ==================== AGENT ROUTES ====================

router.get("/api/agents", async (req, res) => {
  try {
    const { resellerId } = req.query;
    const agents = await extendedStorage.getAllAgents(resellerId as string);
    res.json(agents);
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

// ==================== DEPARTMENT ROUTES ====================

router.get("/api/departments", async (req, res) => {
  try {
    const { resellerId } = req.query;
    const departments = await extendedStorage.getAllDepartments(resellerId as string);
    res.json(departments);
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

// ==================== TICKET ROUTES ====================

router.get("/api/tickets", async (req, res) => {
  try {
    const { resellerId, status, agentId } = req.query;
    const tickets = await extendedStorage.getAllTickets({
      resellerId: resellerId as string,
      status: status as string,
      agentId: agentId as string,
    });
    res.json(tickets);
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

router.get("/api/tickets/:id", async (req, res) => {
  try {
    const ticket = await extendedStorage.getTicketById(req.params.id);
    if (!ticket) {
      return res.status(404).json({ error: "Ticket não encontrado" });
    }
    res.json(ticket);
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

router.get("/api/tickets/:id/messages", async (req, res) => {
  try {
    const messages = await extendedStorage.getMessagesByTicketId(req.params.id);
    res.json(messages);
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

router.post("/api/tickets/:id/messages", async (req, res) => {
  try {
    const { text, fromType } = req.body;
    const ticket = await extendedStorage.getTicketById(req.params.id);
    
    if (!ticket) {
      return res.status(404).json({ error: "Ticket não encontrado" });
    }
    
    const message = await extendedStorage.createMessage({
      ticketId: req.params.id,
      fromType: fromType || "client",
      kind: "text",
      text,
      resellerId: ticket.resellerId,
    });
    
    // Atualizar ticket
    await extendedStorage.updateTicket(req.params.id, {
      status: "ATENDENDO",
    });
    
    res.json(message);
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

// ==================== CLIENT ROUTES ====================

router.get("/api/clients/me/tickets", authMiddleware, requireRole("client"), async (req, res) => {
  try {
    const auth = (req as any).auth;
    const tickets = await extendedStorage.getTicketsByClientId(auth.id);
    res.json(tickets);
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

// ==================== STATS ROUTES ====================

router.get("/api/stats/dashboard", async (req, res) => {
  try {
    const stats = extendedStorage.getStats();
    const tickets = await extendedStorage.getAllTickets();
    
    const ticketsByStatus = {
      PENDENTE: tickets.filter(t => t.status === "PENDENTE").length,
      ATENDENDO: tickets.filter(t => t.status === "ATENDENDO").length,
      FINALIZADAS: tickets.filter(t => t.status === "FINALIZADAS").length,
    };
    
    res.json({
      ...stats,
      ticketsByStatus,
    });
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

export default router;
