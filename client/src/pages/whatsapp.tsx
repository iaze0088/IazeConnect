import { useState, useEffect } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { WhatsAppQRModal } from "@/components/whatsapp-qr-modal";
import { Phone, Plus, Trash2, RefreshCw, QrCode, CheckCircle2, XCircle, Smartphone, Clock, Activity } from "lucide-react";
import { toast } from "@/hooks/use-toast";
import { apiRequest, queryClient } from "@/lib/queryClient";
import { connectWebSocket } from "@/lib/websocket";
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
      if (data.type === "qrcode") {
        console.log("[WebSocket] QR Code atualizado:", data.sessionName);
        queryClient.invalidateQueries({ queryKey: ["/api/whatsapp/connections"] });
        
        if (selectedSession && data.sessionName === selectedSession.sessionName) {
          // Evitar duplicação do prefix data:image
          let qrCodeUrl = data.qrCode;
          if (qrCodeUrl && !qrCodeUrl.startsWith('data:image')) {
            qrCodeUrl = `data:image/png;base64,${qrCodeUrl}`;
          }
          
          const updatedSession = {
            ...selectedSession,
            qrCode: qrCodeUrl
          };
          setSelectedSession(updatedSession as any);
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
        // Evitar duplicação do prefix data:image
        let qrCodeUrl = data.qrCode;
        if (qrCodeUrl && !qrCodeUrl.startsWith('data:image')) {
          qrCodeUrl = `data:image/png;base64,${qrCodeUrl}`;
        }
        
        const updatedConnection = {
          ...connection,
          qrCode: qrCodeUrl
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
      toast({
        title: "Sucesso",
        description: "Status atualizado!",
      });
    },
  });

  const handleStartSession = (connection: WhatsAppConnection) => {
    startSession.mutate(connection.id);
  };

  const handleRefreshQR = () => {
    if (selectedSession) {
      startSession.mutate(selectedSession.id);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (newSessionName.trim()) {
      createConnection.mutate(newSessionName.trim());
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Activity className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col gap-6">
      {/* Header */}
      <div className="space-y-2">
        <h1 className="text-4xl font-semibold bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">
          Gerenciamento WhatsApp
        </h1>
        <p className="text-muted-foreground text-lg">
          Gerencie conexões WhatsApp via WPP Connect
        </p>
      </div>

      {/* Split Layout */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-5 gap-6">
        {/* Left Column: Session Inventory (40%) */}
        <div className="lg:col-span-2 space-y-6">
          {/* Command Bar */}
          <Card className="border-slate-700/50 backdrop-blur-xl bg-gradient-to-br from-blue-500/10 to-cyan-500/10">
            <CardHeader>
              <CardTitle className="text-lg">Nova Sessão</CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="session-name" className="text-slate-300">
                    Nome da Sessão
                  </Label>
                  <Input
                    id="session-name"
                    placeholder="Ex: atendimento, vendas, suporte..."
                    value={newSessionName}
                    onChange={(e) => setNewSessionName(e.target.value)}
                    className="bg-slate-800/50 border-slate-700 focus:border-blue-500 focus:ring-blue-500/20"
                    data-testid="input-session-name"
                  />
                </div>
                <Button
                  type="submit"
                  className="w-full bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-600 hover:to-cyan-600"
                  disabled={!newSessionName.trim() || createConnection.isPending}
                  data-testid="button-create-session"
                >
                  <Plus className="h-4 w-4 mr-2" />
                  Criar Conexão
                </Button>
              </form>
            </CardContent>
          </Card>

          {/* Session List */}
          <div className="space-y-3">
            <h2 className="text-sm font-medium text-slate-400 uppercase tracking-wider">
              Sessões ({connections.length})
            </h2>
            
            {connections.length === 0 ? (
              <Card className="border-slate-700/50 backdrop-blur-xl bg-card/40">
                <CardContent className="pt-12 pb-12 text-center text-muted-foreground">
                  <div className="mx-auto w-16 h-16 rounded-full bg-slate-800/50 flex items-center justify-center mb-4">
                    <Phone className="h-8 w-8 text-slate-500" />
                  </div>
                  <p className="font-medium mb-1">Nenhuma sessão criada</p>
                  <p className="text-sm">Crie sua primeira conexão acima</p>
                </CardContent>
              </Card>
            ) : (
              <div className="space-y-3 max-h-[600px] overflow-y-auto pr-2 custom-scrollbar">
                {connections.map((connection) => (
                  <Card
                    key={connection.id}
                    className="border-slate-700/50 backdrop-blur-xl bg-card/40 hover-elevate transition-all duration-200"
                    data-testid={`card-session-${connection.sessionName}`}
                  >
                    <CardHeader className="pb-3">
                      <div className="flex items-start justify-between gap-3">
                        <div className="flex items-center gap-3 flex-1 min-w-0">
                          <div
                            className={`relative flex-shrink-0 h-12 w-12 rounded-full flex items-center justify-center ${
                              connection.status === "connected"
                                ? "bg-green-500/10 ring-2 ring-green-500/20"
                                : "bg-slate-700/30"
                            }`}
                          >
                            <Smartphone
                              className={`h-6 w-6 ${
                                connection.status === "connected"
                                  ? "text-green-400"
                                  : "text-slate-500"
                              }`}
                            />
                            {connection.status === "connected" && (
                              <span className="absolute top-0 right-0 h-3 w-3 rounded-full bg-green-400 ring-2 ring-slate-900 animate-pulse" />
                            )}
                          </div>
                          <div className="flex-1 min-w-0">
                            <h3 className="font-semibold text-slate-100 truncate">
                              {connection.sessionName}
                            </h3>
                            <p className="text-xs text-muted-foreground truncate">
                              {connection.phoneNumber || "Aguardando conexão"}
                            </p>
                          </div>
                        </div>
                        {connection.status === "connected" ? (
                          <Badge className="flex-shrink-0 bg-green-500/10 text-green-400 border-green-500/20 hover:bg-green-500/20" data-testid={`badge-status-${connection.sessionName}`}>
                            <span className="h-1.5 w-1.5 rounded-full bg-green-400 mr-1.5 animate-pulse" />
                            Conectado
                          </Badge>
                        ) : (
                          <Badge variant="secondary" data-testid={`badge-status-${connection.sessionName}`}>
                            <span className="h-1.5 w-1.5 rounded-full bg-slate-500 mr-1.5" />
                            Desconectado
                          </Badge>
                        )}
                      </div>
                    </CardHeader>
                    <CardContent className="pt-0 space-y-2">
                      <div className="flex gap-2">
                        {connection.status !== "connected" && (
                          <Button
                            onClick={() => handleStartSession(connection)}
                            size="sm"
                            className="flex-1 bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-600 hover:to-cyan-600"
                            disabled={pendingStartId === connection.id && startSession.isPending}
                            data-testid={`button-connect-${connection.sessionName}`}
                          >
                            <QrCode className="h-4 w-4 mr-2" />
                            Conectar
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
                          onClick={() => {
                            if (confirm(`Deseja remover a sessão "${connection.sessionName}"?`)) {
                              deleteConnection.mutate(connection.id);
                            }
                          }}
                          size="sm"
                          variant="outline"
                          className="border-red-500/20 text-red-400 hover:bg-red-500/10"
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
        </div>

        {/* Right Column: Connection Workspace (60%) */}
        <div className="lg:col-span-3">
          <Card className="border-slate-700/50 backdrop-blur-xl bg-gradient-to-br from-slate-800/40 to-slate-800/20 h-full">
            <CardContent className="pt-10 pb-10 flex flex-col items-center justify-center text-center h-full">
              <div className="max-w-md space-y-6">
                <div className="mx-auto w-20 h-20 rounded-full bg-gradient-to-br from-blue-500/20 to-cyan-500/20 flex items-center justify-center">
                  <QrCode className="h-10 w-10 text-blue-400" />
                </div>
                <div className="space-y-2">
                  <h2 className="text-2xl font-semibold bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">
                    Pronto para Conectar
                  </h2>
                  <p className="text-muted-foreground">
                    Selecione uma sessão à esquerda e clique em <strong>Conectar</strong> para gerar o QR Code
                  </p>
                </div>
                <div className="grid grid-cols-3 gap-4 pt-4">
                  <div className="space-y-2">
                    <div className="h-12 w-12 mx-auto rounded-full bg-blue-500/10 flex items-center justify-center">
                      <Phone className="h-6 w-6 text-blue-400" />
                    </div>
                    <p className="text-xs text-muted-foreground">
                      Crie Sessão
                    </p>
                  </div>
                  <div className="space-y-2">
                    <div className="h-12 w-12 mx-auto rounded-full bg-cyan-500/10 flex items-center justify-center">
                      <QrCode className="h-6 w-6 text-cyan-400" />
                    </div>
                    <p className="text-xs text-muted-foreground">
                      Escaneie QR
                    </p>
                  </div>
                  <div className="space-y-2">
                    <div className="h-12 w-12 mx-auto rounded-full bg-green-500/10 flex items-center justify-center">
                      <CheckCircle2 className="h-6 w-6 text-green-400" />
                    </div>
                    <p className="text-xs text-muted-foreground">
                      Conectado!
                    </p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
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
