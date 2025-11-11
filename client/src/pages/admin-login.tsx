import { useState } from "react";
import { useLocation } from "wouter";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Shield } from "lucide-react";
import { toast } from "@/hooks/use-toast";
import { apiRequest } from "@/lib/queryClient";

export default function AdminLogin() {
  const [, setLocation] = useLocation();
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!password) {
      toast({
        title: "Erro",
        description: "Por favor, digite a senha",
        variant: "destructive",
      });
      return;
    }

    setIsLoading(true);

    try {
      const response = await apiRequest("POST", "/api/auth/admin/login", {
        password,
      });

      if (response.success && response.token) {
        // Salvar token no localStorage
        localStorage.setItem("admin_token", response.token);
        localStorage.setItem("user_role", "admin");
        localStorage.setItem("user_name", response.user.name);

        toast({
          title: "Login realizado",
          description: "Bem-vindo ao Sistema IAZE!",
        });

        // Redirecionar para dashboard
        setLocation("/dashboard");
      }
    } catch (error: any) {
      toast({
        title: "Erro no login",
        description: error.message || "Senha incorreta",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 p-4">
      <div className="absolute inset-0 bg-[url('/grid.svg')] opacity-10" />
      
      <Card className="w-full max-w-md border-slate-700/50 backdrop-blur-xl bg-slate-900/90 relative">
        <CardHeader className="space-y-3 pb-6">
          <div className="mx-auto w-16 h-16 rounded-full bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center">
            <Shield className="h-8 w-8 text-white" />
          </div>
          <CardTitle className="text-2xl text-center bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">
            Sistema IAZE
          </CardTitle>
          <CardDescription className="text-center text-slate-400">
            Acesso Administrativo
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="password" className="text-slate-300">
                Senha de Administrador
              </Label>
              <Input
                id="password"
                type="password"
                placeholder="Digite sua senha"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="bg-slate-800/50 border-slate-700 focus:border-blue-500 focus:ring-blue-500/20"
                data-testid="input-admin-password"
                autoFocus
              />
            </div>

            <Button
              type="submit"
              className="w-full bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-600 hover:to-cyan-600"
              disabled={isLoading}
              data-testid="button-admin-login"
            >
              {isLoading ? "Entrando..." : "Entrar"}
            </Button>
          </form>

          <div className="mt-6 text-center">
            <a
              href="/"
              className="text-sm text-slate-400 hover:text-blue-400 transition-colors"
            >
              ← Voltar para área do cliente
            </a>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
