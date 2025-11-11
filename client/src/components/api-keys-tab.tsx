import { useQuery, useMutation } from "@tanstack/react-query";
import { apiRequest, queryClient } from "@/lib/queryClient";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Form, FormControl, FormDescription, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { useToast } from "@/hooks/use-toast";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { insertApiKeySchema, type ApiKey } from "@shared/schema";
import { z } from "zod";
import { useState } from "react";
import { Plus, Copy, RotateCw, Trash2, Key, Activity, AlertTriangle, CheckCircle2, Clock } from "lucide-react";

const eventTypes = [
  { id: "message", label: "Mensagens" },
  { id: "status", label: "Status de Conexão" },
  { id: "qr", label: "QR Code" },
  { id: "connection", label: "Eventos de Conexão" },
];

export function ApiKeysTab() {
  const { toast } = useToast();
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [keyDisplayDialog, setKeyDisplayDialog] = useState<{ open: boolean; key: string; name: string }>({
    open: false,
    key: "",
    name: "",
  });
  const [selectedKey, setSelectedKey] = useState<string | null>(null);

  const { data: apiKeys = [], isLoading } = useQuery<ApiKey[]>({
    queryKey: ["/api/api-keys"],
  });

  const createForm = useForm<z.infer<typeof insertApiKeySchema>>({
    resolver: zodResolver(insertApiKeySchema),
    defaultValues: {
      resellerId: "default-reseller",
      name: "",
      connectionLimit: 5,
      webhookUrl: "",
      webhookEvents: ["message", "status", "qr", "connection"],
      status: "active",
    },
  });

  const createMutation = useMutation({
    mutationFn: async (data: z.infer<typeof insertApiKeySchema>) => {
      return apiRequest("POST", "/api/api-keys", data);
    },
    onSuccess: (response: any) => {
      queryClient.invalidateQueries({ queryKey: ["/api/api-keys"] });
      setCreateDialogOpen(false);
      createForm.reset();
      
      // Mostrar chave completa (APENAS UMA VEZ!)
      setKeyDisplayDialog({
        open: true,
        key: response.fullKey,
        name: response.apiKey.name,
      });

      toast({
        title: "API Key Criada!",
        description: "Guarde a chave em local seguro. Ela não será mostrada novamente.",
      });
    },
    onError: (error: any) => {
      toast({
        title: "Erro ao criar API Key",
        description: error.message,
        variant: "destructive",
      });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      return apiRequest("DELETE", `/api/api-keys/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/api-keys"] });
      toast({
        title: "API Key Deletada",
        description: "A chave foi removida com sucesso.",
      });
    },
  });

  const rotateMutation = useMutation({
    mutationFn: async (id: string) => {
      return apiRequest("POST", `/api/api-keys/${id}/rotate`);
    },
    onSuccess: (response: any) => {
      queryClient.invalidateQueries({ queryKey: ["/api/api-keys"] });
      
      // Mostrar nova chave
      setKeyDisplayDialog({
        open: true,
        key: response.fullKey,
        name: response.apiKey.name,
      });

      toast({
        title: "Chave Rotacionada!",
        description: "A chave anterior foi invalidada.",
      });
    },
  });

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    toast({
      title: "Copiado!",
      description: "API Key copiada para área de transferência",
    });
  };

  const getStatusBadge = (status: string) => {
    const variants: Record<string, { variant: "default" | "secondary" | "destructive"; icon: any }> = {
      active: { variant: "default", icon: CheckCircle2 },
      inactive: { variant: "secondary", icon: Clock },
      suspended: { variant: "destructive", icon: AlertTriangle },
    };

    const config = variants[status] || variants.inactive;
    const Icon = config.icon;

    return (
      <Badge variant={config.variant} className="gap-1">
        <Icon className="h-3 w-3" />
        {status}
      </Badge>
    );
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">API Keys & Webhooks</h2>
          <p className="text-sm text-muted-foreground">
            Gerencie chaves de API para integração com sistemas externos
          </p>
        </div>
        <Button onClick={() => setCreateDialogOpen(true)} data-testid="button-create-api-key">
          <Plus className="h-4 w-4 mr-2" />
          Nova API Key
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total de Keys</CardTitle>
            <Key className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold" data-testid="text-total-keys">{apiKeys.length}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Conexões Ativas</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold" data-testid="text-active-connections">
              {apiKeys.reduce((sum, key) => sum + key.currentConnections, 0)}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total de Requisições</CardTitle>
            <CheckCircle2 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold" data-testid="text-total-requests">
              {apiKeys.reduce((sum, key) => sum + key.totalRequests, 0)}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* API Keys Table */}
      <Card>
        <CardHeader>
          <CardTitle>Suas API Keys</CardTitle>
          <CardDescription>
            Gerencie suas chaves de API para integração com sistemas externos
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="text-center py-8 text-muted-foreground">Carregando...</div>
          ) : apiKeys.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              Nenhuma API key criada. Clique em "Nova API Key" para começar.
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Nome</TableHead>
                  <TableHead>Chave</TableHead>
                  <TableHead>Conexões</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Requisições</TableHead>
                  <TableHead className="text-right">Ações</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {apiKeys.map((key) => (
                  <TableRow key={key.id} data-testid={`row-api-key-${key.id}`}>
                    <TableCell className="font-medium">{key.name}</TableCell>
                    <TableCell>
                      <code className="text-xs bg-muted px-2 py-1 rounded">
                        {key.keyPrefix}...{key.keyLastChars}
                      </code>
                    </TableCell>
                    <TableCell>
                      <span className={key.currentConnections >= key.connectionLimit ? "text-destructive font-medium" : ""}>
                        {key.currentConnections} / {key.connectionLimit}
                      </span>
                    </TableCell>
                    <TableCell>{getStatusBadge(key.status)}</TableCell>
                    <TableCell>{key.totalRequests.toLocaleString()}</TableCell>
                    <TableCell className="text-right space-x-2">
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => rotateMutation.mutate(key.id)}
                        disabled={rotateMutation.isPending}
                        data-testid={`button-rotate-${key.id}`}
                      >
                        <RotateCw className="h-3 w-3" />
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => deleteMutation.mutate(key.id)}
                        disabled={deleteMutation.isPending}
                        data-testid={`button-delete-${key.id}`}
                      >
                        <Trash2 className="h-3 w-3" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Create Dialog */}
      <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Criar Nova API Key</DialogTitle>
            <DialogDescription>
              Configure uma nova chave de API para integração externa
            </DialogDescription>
          </DialogHeader>

          <Form {...createForm}>
            <form onSubmit={createForm.handleSubmit((data) => createMutation.mutate(data))} className="space-y-4">
              <FormField
                control={createForm.control}
                name="name"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Nome da API Key</FormLabel>
                    <FormControl>
                      <Input placeholder="Ex: Servidor IAZE Externo" {...field} data-testid="input-api-key-name" />
                    </FormControl>
                    <FormDescription>Identificador amigável para esta chave</FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={createForm.control}
                name="connectionLimit"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Limite de Conexões</FormLabel>
                    <FormControl>
                      <Input
                        type="number"
                        min={1}
                        max={100}
                        {...field}
                        onChange={(e) => field.onChange(parseInt(e.target.value))}
                        data-testid="input-connection-limit"
                      />
                    </FormControl>
                    <FormDescription>Máximo de conexões simultâneas permitidas</FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={createForm.control}
                name="webhookUrl"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Webhook URL (Opcional)</FormLabel>
                    <FormControl>
                      <Input
                        placeholder="https://seu-servidor.com/webhook"
                        {...field}
                        value={field.value || ""}
                        data-testid="input-webhook-url"
                      />
                    </FormControl>
                    <FormDescription>URL para receber eventos em tempo real</FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={createForm.control}
                name="webhookEvents"
                render={() => (
                  <FormItem>
                    <FormLabel>Eventos do Webhook</FormLabel>
                    <div className="space-y-2">
                      {eventTypes.map((event) => (
                        <FormField
                          key={event.id}
                          control={createForm.control}
                          name="webhookEvents"
                          render={({ field }) => (
                            <FormItem className="flex items-center space-x-2 space-y-0">
                              <FormControl>
                                <Checkbox
                                  checked={field.value?.includes(event.id)}
                                  onCheckedChange={(checked) => {
                                    const current = field.value || [];
                                    field.onChange(
                                      checked
                                        ? [...current, event.id]
                                        : current.filter((v: string) => v !== event.id)
                                    );
                                  }}
                                  data-testid={`checkbox-event-${event.id}`}
                                />
                              </FormControl>
                              <FormLabel className="font-normal cursor-pointer">
                                {event.label}
                              </FormLabel>
                            </FormItem>
                          )}
                        />
                      ))}
                    </div>
                    <FormDescription>Selecione quais eventos serão enviados</FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <div className="flex gap-3 justify-end">
                <Button type="button" variant="outline" onClick={() => setCreateDialogOpen(false)}>
                  Cancelar
                </Button>
                <Button type="submit" disabled={createMutation.isPending} data-testid="button-submit-create">
                  {createMutation.isPending ? "Criando..." : "Criar API Key"}
                </Button>
              </div>
            </form>
          </Form>
        </DialogContent>
      </Dialog>

      {/* Key Display Dialog (ÚNICA VEZ!) */}
      <Dialog open={keyDisplayDialog.open} onOpenChange={(open) => setKeyDisplayDialog({ ...keyDisplayDialog, open })}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <CheckCircle2 className="h-5 w-5 text-green-500" />
              API Key Criada com Sucesso!
            </DialogTitle>
            <DialogDescription>
              <span className="text-destructive font-semibold">
                ATENÇÃO: Esta chave será mostrada apenas agora. Guarde em local seguro!
              </span>
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium">Nome da Chave:</label>
              <p className="text-lg font-bold">{keyDisplayDialog.name}</p>
            </div>

            <div>
              <label className="text-sm font-medium">API Key Completa:</label>
              <div className="flex items-center gap-2 mt-2">
                <code className="flex-1 bg-muted p-3 rounded text-xs font-mono break-all" data-testid="text-full-api-key">
                  {keyDisplayDialog.key}
                </code>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => copyToClipboard(keyDisplayDialog.key)}
                  data-testid="button-copy-api-key"
                >
                  <Copy className="h-4 w-4" />
                </Button>
              </div>
            </div>

            <div className="bg-amber-50 dark:bg-amber-950 border border-amber-200 dark:border-amber-800 rounded-lg p-4">
              <div className="flex items-start gap-2">
                <AlertTriangle className="h-5 w-5 text-amber-600 dark:text-amber-400 mt-0.5" />
                <div className="text-sm">
                  <p className="font-semibold text-amber-900 dark:text-amber-100">Importante:</p>
                  <ul className="list-disc list-inside text-amber-800 dark:text-amber-200 mt-1 space-y-1">
                    <li>Guarde esta chave em local seguro (gerenciador de senhas, variáveis de ambiente)</li>
                    <li>Ela não será mostrada novamente após fechar esta janela</li>
                    <li>Use a opção "Rotacionar" se precisar gerar uma nova chave</li>
                  </ul>
                </div>
              </div>
            </div>

            <Button
              className="w-full"
              onClick={() => setKeyDisplayDialog({ open: false, key: "", name: "" })}
              data-testid="button-close-key-dialog"
            >
              Entendi, já guardei a chave
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
