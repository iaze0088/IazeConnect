import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Settings as SettingsIcon } from "lucide-react";

export default function SettingsPage() {
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-semibold">Configurações</h1>
        <p className="text-muted-foreground mt-2">
          Configure as preferências do sistema
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Configurações do WPP Connect</CardTitle>
          <CardDescription>
            Informações sobre a integração com o WPP Connect
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label htmlFor="apiUrl">URL da API</Label>
            <Input
              id="apiUrl"
              value={import.meta.env.VITE_WPPCONNECT_API_URL || "Configurado no servidor"}
              readOnly
              className="font-mono text-sm"
              data-testid="input-api-url"
            />
            <p className="text-xs text-muted-foreground mt-1">
              A URL do servidor WPP Connect está configurada nas variáveis de ambiente
            </p>
          </div>

          <div>
            <Label htmlFor="status">Status da Integração</Label>
            <div className="flex items-center gap-2 mt-2">
              <div className="h-3 w-3 rounded-full bg-green-500"></div>
              <span className="text-sm">Conectado e Operacional</span>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Sobre o Sistema</CardTitle>
          <CardDescription>
            Informações sobre a versão e recursos
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center gap-4">
            <div className="h-16 w-16 rounded-lg bg-primary/10 flex items-center justify-center">
              <SettingsIcon className="h-8 w-8 text-primary" />
            </div>
            <div>
              <h3 className="font-semibold text-lg">IAZE WhatsApp Manager</h3>
              <p className="text-sm text-muted-foreground">
                Sistema profissional de gerenciamento WhatsApp
              </p>
              <p className="text-xs text-muted-foreground mt-1">
                Versão 1.0.0 - Powered by WPP Connect
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
