import { createContext, useContext, useEffect, useState } from "react";
import { useLocation } from "wouter";

interface AuthContextType {
  isAuthenticated: boolean;
  isAdmin: boolean;
  userName: string | null;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [, setLocation] = useLocation();
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isAdmin, setIsAdmin] = useState(false);
  const [userName, setUserName] = useState<string | null>(null);

  useEffect(() => {
    const token = localStorage.getItem("admin_token");
    const role = localStorage.getItem("user_role");
    const name = localStorage.getItem("user_name");

    if (token && role === "admin") {
      setIsAuthenticated(true);
      setIsAdmin(true);
      setUserName(name);
    }
  }, []);

  const logout = () => {
    localStorage.removeItem("admin_token");
    localStorage.removeItem("user_role");
    localStorage.removeItem("user_name");
    setIsAuthenticated(false);
    setIsAdmin(false);
    setUserName(null);
    setLocation("/admin");
  };

  return (
    <AuthContext.Provider value={{ isAuthenticated, isAdmin, userName, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const [, setLocation] = useLocation();
  const token = localStorage.getItem("admin_token");
  const role = localStorage.getItem("user_role");

  useEffect(() => {
    if (!token || role !== "admin") {
      setLocation("/admin");
    }
  }, [token, role, setLocation]);

  if (!token || role !== "admin") {
    return null;
  }

  return <>{children}</>;
}
