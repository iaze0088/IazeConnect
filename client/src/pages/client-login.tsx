import { useState } from "react";
import { useLocation } from "wouter";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { MessageSquare } from "lucide-react";
import { apiRequest } from "@/lib/queryClient";
import { useToast } from "@/hooks/use-toast";

export default function ClientLogin() {
  const [, setLocation] = useLocation();
  const { toast } = useToast();
  const [isLogin, setIsLogin] = useState(true);
  const [whatsapp, setWhatsapp] = useState("");
  const [pin, setPin] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const endpoint = isLogin ? "/api/auth/client/login" : "/api/auth/client/register";
      const data = await apiRequest("POST", endpoint, { whatsapp, pin });

      localStorage.setItem("iaze_token", data.token);
      localStorage.setItem("iaze_user", JSON.stringify(data.user));

      toast({
        title: isLogin ? "Login realizado!" : "Cadastro realizado!",
        description: "Redirecionando para o chat...",
      });

      setLocation("/client/chat");
    } catch (error: any) {
      toast({
        title: "Erro",
        description: error.message || "Erro ao processar solicitação",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800 p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="flex justify-center mb-4">
            <div className="w-16 h-16 bg-primary rounded-full flex items-center justify-center">
              <MessageSquare className="w-8 h-8 text-primary-foreground" />
            </div>
          </div>
          <CardTitle className="text-2xl">Área do Cliente</CardTitle>
          <CardDescription>
            {isLogin 
              ? "Entre com seu WhatsApp e PIN para acessar o chat"
              : "Primeiro acesso? Crie seu PIN de 2 dígitos"}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="whatsapp">WhatsApp</Label>
              <Input
                id="whatsapp"
                type="text"
                placeholder="5519999999999"
                value={whatsapp}
                onChange={(e) => setWhatsapp(e.target.value)}
                required
                data-testid="input-whatsapp"
                disabled={loading}
              />
              <p className="text-xs text-muted-foreground">
                Formato: código do país + DDD + número
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="pin">PIN (2 dígitos)</Label>
              <Input
                id="pin"
                type="password"
                placeholder="••"
                value={pin}
                onChange={(e) => setPin(e.target.value.slice(0, 2))}
                maxLength={2}
                required
                data-testid="input-pin"
                disabled={loading}
              />
              <p className="text-xs text-muted-foreground">
                {isLogin ? "Digite seu PIN de 2 dígitos" : "Crie um PIN de 2 dígitos"}
              </p>
            </div>

            <Button 
              type="submit" 
              className="w-full" 
              disabled={loading || whatsapp.length < 10 || pin.length !== 2}
              data-testid="button-submit"
            >
              {loading ? "Processando..." : isLogin ? "Entrar" : "Criar Conta"}
            </Button>

            <div className="text-center">
              <Button
                type="button"
                variant="ghost"
                onClick={() => setIsLogin(!isLogin)}
                data-testid="button-toggle-mode"
                disabled={loading}
              >
                {isLogin ? "Primeiro acesso? Crie sua conta" : "Já tem conta? Faça login"}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
