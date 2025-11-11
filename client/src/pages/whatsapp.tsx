import { useState, useEffect } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { WhatsAppQRModal } from "@/components/whatsapp-qr-modal";
import { Phone, Plus, Trash2, RefreshCw, QrCode, CheckCircle2, XCircle } from "lucide-react";
import { toast } from "@/hooks/use-toast";
import { apiRequest, queryClient } from "@/lib/queryClient";
import { connectWebSocket, subscribeToSession } from "@/lib/websocket";
import type { WhatsAppConnection } from "@shared/schema";

export default function WhatsAppPage() {
  const [newSessionName, setNewSessionName] = useState("");
  const [selectedSession, setSelectedSession] = useState<WhatsAppConnection | null>(null);
  const [showQRModal, setShowQRModal] = useState(false);
  const [pendingStartId, setPendingStartId] = useState<string | null>(null);

  const { data: connections = [], isLoading } = useQuery<WhatsAppConnection[]>({
    queryKey: ["/api/whatsapp/connections"],
  });

  useEffect(() => {
    const socket = connectWebSocket((data) => {
      if (data.type === "qr_code") {
        console.log("[WebSocket] QR Code atualizado:", data.sessionName);
        queryClient.invalidateQueries({ queryKey: ["/api/whatsapp/connections"] });
        
        if (selectedSession && data.sessionName === selectedSession.sessionName) {
          toast({
            title: "QR Code Atualizado",
            description: "Um novo QR Code foi gerado",
          });
        }
      }
    });

    return () => {
      if (socket) {
        socket.close();
      }
    };
  }, [selectedSession]);

  const createConnection = useMutation({
    mutationFn: async (sessionName: string) => {
      // Default reseller ID from imported MongoDB backup data
      const DEFAULT_RESELLER_ID = "6b6b483a-98ac-4613-bd88-5e5c6ba67839";
      
      return await apiRequest("POST", "/api/whatsapp/connections", { 
        sessionName,
        provider: "wpp-connect",
        resellerId: DEFAULT_RESELLER_ID
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/whatsapp/connections"] });
      setNewSessionName("");
      toast({
        title: "Sucesso",
        description: "Conexão criada com sucesso!",
      });
    },
    onError: (error: any) => {
      toast({
        title: "Erro",
        description: error.message || "Falha ao criar conexão",
        variant: "destructive",
      });
    },
  });

  const deleteConnection = useMutation({
    mutationFn: async (id: string) => {
      return await apiRequest("DELETE", `/api/whatsapp/connections/${id}`, undefined);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/whatsapp/connections"] });
      toast({
        title: "Sucesso",
        description: "Conexão removida com sucesso!",
      });
    },
    onError: (error: any) => {
      toast({
        title: "Erro",
        description: error.message || "Falha ao remover conexão",
        variant: "destructive",
      });
    },
  });

  const startSession = useMutation({
    mutationFn: async (id: string) => {
      return await apiRequest("POST", `/api/whatsapp/connections/${id}/start`, undefined);
    },
    onMutate: (id) => {
      setPendingStartId(id);
    },
    onSuccess: (data: any, id) => {
      queryClient.invalidateQueries({ queryKey: ["/api/whatsapp/connections"] });
      const connection = connections.find((c) => c.id === id);
      if (connection) {
        // Update connection with QR code from API response
        const updatedConnection = {
          ...connection,
          qrCode: data.qrcode ? `data:image/png;base64,${data.qrcode}` : undefined
        };
        setSelectedSession(updatedConnection);
        setShowQRModal(true);
      }
    },
    onError: (error: any) => {
      toast({
        title: "Erro",
        description: error.message || "Falha ao iniciar sessão",
        variant: "destructive",
      });
    },
    onSettled: () => {
      setPendingStartId(null);
    },
  });

  const refreshStatus = useMutation({
    mutationFn: async (id: string) => {
      return await apiRequest("POST", `/api/whatsapp/connections/${id}/refresh`, undefined);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/whatsapp/connections"] });
    },
  });

  const handleCreateConnection = () => {
    if (!newSessionName.trim()) {
      toast({
        title: "Atenção",
        description: "Digite um nome para a sessão",
        variant: "destructive",
      });
      return;
    }
    createConnection.mutate(newSessionName);
  };

  const handleStartSession = (connection: WhatsAppConnection) => {
    setSelectedSession(connection);
    startSession.mutate(connection.id);
  };

  const handleRefreshQR = () => {
    if (selectedSession) {
      refreshStatus.mutate(selectedSession.id);
    }
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-semibold">WhatsApp</h1>
        <p className="text-muted-foreground mt-2">
          Gerencie suas conexões WhatsApp com WPP Connect
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Criar Nova Conexão</CardTitle>
          <CardDescription>
            Crie uma nova sessão WhatsApp para começar a enviar mensagens
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4">
            <div className="flex-1">
              <Label htmlFor="sessionName">Nome da Sessão</Label>
              <Input
                id="sessionName"
                placeholder="Ex: atendimento, vendas, suporte"
                value={newSessionName}
                onChange={(e) => setNewSessionName(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleCreateConnection()}
                data-testid="input-session-name"
              />
            </div>
            <div className="flex items-end">
              <Button
                onClick={handleCreateConnection}
                disabled={createConnection.isPending}
                data-testid="button-create-connection"
              >
                <Plus className="h-4 w-4 mr-2" />
                Criar Conexão
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      <div>
        <h2 className="text-xl font-semibold mb-4">Conexões Ativas</h2>
        {isLoading ? (
          <div className="text-center py-12">
            <RefreshCw className="h-8 w-8 animate-spin mx-auto text-primary" />
          </div>
        ) : connections.length === 0 ? (
          <Card>
            <CardContent className="py-12 text-center text-muted-foreground">
              <Phone className="h-16 w-16 mx-auto mb-4 opacity-50" />
              <p className="text-lg">Nenhuma conexão criada ainda</p>
              <p className="text-sm mt-2">
                Crie sua primeira conexão para começar
              </p>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {connections.map((connection) => (
              <Card key={connection.id} className="hover-elevate" data-testid={`card-connection-${connection.sessionName}`}>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-base font-medium">
                    {connection.sessionName}
                  </CardTitle>
                  {connection.status === "connected" ? (
                    <Badge className="bg-green-500 hover:bg-green-600" data-testid={`badge-status-${connection.sessionName}`}>
                      <CheckCircle2 className="h-3 w-3 mr-1" />
                      Conectado
                    </Badge>
                  ) : (
                    <Badge variant="secondary" data-testid={`badge-status-${connection.sessionName}`}>
                      <XCircle className="h-3 w-3 mr-1" />
                      Desconectado
                    </Badge>
                  )}
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <p className="text-sm text-muted-foreground">Telefone</p>
                    <p className="text-sm font-mono">
                      {connection.phoneNumber || "Não conectado"}
                    </p>
                  </div>

                  <div className="flex gap-2">
                    {connection.status !== "connected" && (
                      <Button
                        onClick={() => handleStartSession(connection)}
                        size="sm"
                        className="flex-1"
                        disabled={pendingStartId === connection.id && startSession.isPending}
                        data-testid={`button-connect-${connection.sessionName}`}
                      >
                        <QrCode className="h-4 w-4 mr-2" />
                        Conectar Número
                      </Button>
                    )}
                    {connection.status === "connected" && (
                      <Button
                        onClick={() => refreshStatus.mutate(connection.id)}
                        size="sm"
                        variant="outline"
                        className="flex-1"
                        disabled={refreshStatus.isPending}
                        data-testid={`button-refresh-${connection.sessionName}`}
                      >
                        <RefreshCw className="h-4 w-4 mr-2" />
                        Atualizar
                      </Button>
                    )}
                    <Button
                      onClick={() => deleteConnection.mutate(connection.id)}
                      size="sm"
                      variant="destructive"
                      disabled={deleteConnection.isPending}
                      data-testid={`button-delete-${connection.sessionName}`}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>

      {selectedSession && (
        <WhatsAppQRModal
          open={showQRModal}
          onOpenChange={setShowQRModal}
          sessionName={selectedSession.sessionName}
          qrCode={(selectedSession as any).qrCode || selectedSession.qrCodeData || ""}
          status={selectedSession.status === "connected" ? "connected" : "connecting"}
          onRefresh={handleRefreshQR}
        />
      )}
    </div>
  );
}
