import jwt from "jsonwebtoken";
import { Request, Response, NextFunction } from "express";

const JWT_SECRET = process.env.SESSION_SECRET || "iaze-secret-key-change-in-production";
const JWT_EXPIRES_IN = "7d"; // 7 dias

export interface JWTPayload {
  id: string;
  role: "admin" | "reseller" | "agent" | "client";
  resellerId?: string | null;
  whatsapp?: string;
}

export function generateToken(payload: JWTPayload): string {
  return jwt.sign(payload, JWT_SECRET, { expiresIn: JWT_EXPIRES_IN });
}

export function verifyToken(token: string): JWTPayload {
  try {
    return jwt.verify(token, JWT_SECRET) as JWTPayload;
  } catch (error) {
    throw new Error("Token inválido ou expirado");
  }
}

// Middleware de autenticação
export function authMiddleware(req: Request, res: Response, next: NextFunction) {
  try {
    const authHeader = req.headers.authorization;
    
    if (!authHeader) {
      return res.status(401).json({ error: "Token não fornecido" });
    }
    
    const token = authHeader.replace("Bearer ", "");
    const payload = verifyToken(token);
    
    // Adicionar payload ao request para uso posterior
    (req as any).auth = payload;
    
    next();
  } catch (error: any) {
    return res.status(401).json({ error: error.message });
  }
}

// Middleware para validar role específica
export function requireRole(...roles: string[]) {
  return (req: Request, res: Response, next: NextFunction) => {
    const auth = (req as any).auth;
    
    if (!auth) {
      return res.status(401).json({ error: "Não autenticado" });
    }
    
    if (!roles.includes(auth.role)) {
      return res.status(403).json({ error: "Sem permissão" });
    }
    
    next();
  };
}
