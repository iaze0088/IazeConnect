import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Phone, CheckCircle, XCircle, AlertCircle, Cpu, HardDrive, Activity, Wifi, Clock, TrendingUp } from "lucide-react";
import type { WhatsAppConnection } from "@shared/schema";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";

interface ServerMetrics {
  connections: {
    active: number;
    connecting: number;
    disconnected: number;
    error: number;
    total: number;
  };
  server: {
    status: "healthy" | "warning" | "critical";
    cpuPercent: number;
    ramUsed: number;
    ramTotal: number;
    ramPercent: number;
    bandwidthIn: number;
    bandwidthOut: number;
    uptime: number;
    lastSampleAt: string;
  };
}

export default function Dashboard() {
  const { data: metrics, isLoading: metricsLoading } = useQuery<ServerMetrics>({
    queryKey: ["/api/server/metrics"],
    refetchInterval: 10000, // Poll every 10s
  });

  const { data: connections = [], isLoading: connectionsLoading } = useQuery<WhatsAppConnection[]>({
    queryKey: ["/api/whatsapp/connections"],
    refetchInterval: 10000,
  });

  const isLoading = metricsLoading || connectionsLoading;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Activity className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  const connectionCards = [
    {
      title: "Conexões Ativas",
      value: metrics?.connections.active || 0,
      description: "Online agora",
      icon: CheckCircle,
      gradient: "from-success/30 to-success/10",
      iconColor: "text-success",
      bgAccent: "bg-success/10",
    },
    {
      title: "Conectando",
      value: metrics?.connections.connecting || 0,
      description: "Em processo",
      icon: Activity,
      gradient: "from-warning/30 to-warning/10",
      iconColor: "text-warning",
      bgAccent: "bg-warning/10",
    },
    {
      title: "Desconectadas",
      value: metrics?.connections.disconnected || 0,
      description: "Aguardando",
      icon: XCircle,
      gradient: "from-slate-500/30 to-slate-500/10",
      iconColor: "text-slate-400",
      bgAccent: "bg-slate-500/10",
    },
    {
      title: "Com Erro",
      value: metrics?.connections.error || 0,
      description: "Precisa atenção",
      icon: AlertCircle,
      gradient: "from-destructive/30 to-destructive/10",
      iconColor: "text-destructive",
      bgAccent: "bg-destructive/10",
    },
  ];

  const formatUptime = (seconds: number) => {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    
    if (days > 0) return `${days}d ${hours}h`;
    if (hours > 0) return `${hours}h ${minutes}m`;
    return `${minutes}m`;
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "healthy":
        return "bg-success text-success-foreground";
      case "warning":
        return "bg-warning text-warning-foreground";
      case "critical":
        return "bg-destructive text-destructive-foreground";
      default:
        return "bg-muted text-muted-foreground";
    }
  };

  const getProgressColor = (percent: number) => {
    if (percent > 85) return "bg-destructive";
    if (percent > 60) return "bg-warning";
    return "bg-success";
  };

  return (
    <div className="space-y-10">
      <div className="space-y-2">
        <h1 className="text-4xl font-semibold bg-gradient-to-r from-primary to-cyan-400 bg-clip-text text-transparent">
          Dashboard
        </h1>
        <p className="text-muted-foreground text-lg">
          Monitoramento em tempo real do sistema IAZE
        </p>
      </div>

      {/* Connection Status Cards */}
      <div>
        <h2 className="text-xl font-semibold mb-4 text-foreground">Status das Conexões WhatsApp</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {connectionCards.map((card) => (
            <Card
              key={card.title}
              className={`relative overflow-hidden border-slate-700/50 bg-gradient-to-br ${card.gradient} backdrop-blur-xl hover-elevate transition-all duration-300`}
              data-testid={`card-${card.title.toLowerCase().replace(/\s+/g, "-")}`}
            >
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium text-foreground">
                  {card.title}
                </CardTitle>
                <div className={`p-2 rounded-lg ${card.bgAccent}`}>
                  <card.icon className={`h-5 w-5 ${card.iconColor}`} />
                </div>
              </CardHeader>
              <CardContent className="space-y-1">
                <div className="text-4xl font-bold" data-testid={`text-${card.title.toLowerCase().replace(/\s+/g, "-")}-value`}>
                  {card.value}
                </div>
                <p className="text-xs text-muted-foreground">
                  {card.description}
                </p>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      {/* Server Health Monitor */}
      {metrics && (
        <Card className="border-slate-700/50 backdrop-blur-xl bg-card/40">
          <CardHeader className="border-b border-slate-700/50 pb-6">
            <div className="flex items-center justify-between flex-wrap gap-4">
              <div>
                <CardTitle className="text-2xl flex items-center gap-3">
                  Monitor de Saúde do Servidor
                  <Badge className={getStatusColor(metrics.server.status)} data-testid="badge-server-status">
                    {metrics.server.status === "healthy" && "✓ Saudável"}
                    {metrics.server.status === "warning" && "⚠ Atenção"}
                    {metrics.server.status === "critical" && "✕ Crítico"}
                  </Badge>
                </CardTitle>
                <p className="text-muted-foreground mt-2">
                  Métricas do sistema em tempo real • Atualização a cada 10s
                </p>
              </div>
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Clock className="h-4 w-4" />
                Uptime: {formatUptime(metrics.server.uptime)}
              </div>
            </div>
          </CardHeader>
          <CardContent className="pt-8">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              {/* CPU */}
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-primary/10">
                      <Cpu className="h-5 w-5 text-primary" />
                    </div>
                    <div>
                      <p className="font-semibold text-foreground">CPU</p>
                      <p className="text-xs text-muted-foreground">Processamento</p>
                    </div>
                  </div>
                  <span className="text-2xl font-bold" data-testid="text-cpu-percent">
                    {metrics.server.cpuPercent}%
                  </span>
                </div>
                <div className="space-y-2">
                  <Progress 
                    value={metrics.server.cpuPercent} 
                    className="h-3"
                    data-testid="progress-cpu"
                  />
                  <p className="text-xs text-muted-foreground">
                    {metrics.server.cpuPercent > 85 ? "⚠ Uso crítico" : 
                     metrics.server.cpuPercent > 60 ? "⚠ Uso elevado" : "✓ Normal"}
                  </p>
                </div>
              </div>

              {/* RAM */}
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-success/10">
                      <HardDrive className="h-5 w-5 text-success" />
                    </div>
                    <div>
                      <p className="font-semibold text-foreground">Memória RAM</p>
                      <p className="text-xs text-muted-foreground">
                        {metrics.server.ramUsed}GB / {metrics.server.ramTotal}GB
                      </p>
                    </div>
                  </div>
                  <span className="text-2xl font-bold" data-testid="text-ram-percent">
                    {metrics.server.ramPercent}%
                  </span>
                </div>
                <div className="space-y-2">
                  <Progress 
                    value={metrics.server.ramPercent} 
                    className="h-3"
                    data-testid="progress-ram"
                  />
                  <p className="text-xs text-muted-foreground">
                    {metrics.server.ramPercent > 85 ? "⚠ Memória crítica" : 
                     metrics.server.ramPercent > 60 ? "⚠ Memória elevada" : "✓ Normal"}
                  </p>
                </div>
              </div>

              {/* Bandwidth */}
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-warning/10">
                      <Wifi className="h-5 w-5 text-warning" />
                    </div>
                    <div>
                      <p className="font-semibold text-foreground">Largura de Banda</p>
                      <p className="text-xs text-muted-foreground">Rede</p>
                    </div>
                  </div>
                </div>
                <div className="space-y-3">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground flex items-center gap-2">
                      <TrendingUp className="h-3 w-3 rotate-180 text-primary" />
                      Download
                    </span>
                    <span className="font-medium" data-testid="text-bandwidth-in">
                      {metrics.server.bandwidthIn} KB/s
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground flex items-center gap-2">
                      <TrendingUp className="h-3 w-3 text-success" />
                      Upload
                    </span>
                    <span className="font-medium" data-testid="text-bandwidth-out">
                      {metrics.server.bandwidthOut} KB/s
                    </span>
                  </div>
                  <p className="text-xs text-muted-foreground pt-1">
                    ✓ Conexão estável
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Recent Connections */}
      <Card className="border-slate-700/50 backdrop-blur-xl bg-card/40">
        <CardHeader className="border-b border-slate-700/50 pb-6">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-2xl">Conexões Recentes</CardTitle>
              <p className="text-muted-foreground mt-2">
                Últimas sessões WhatsApp gerenciadas
              </p>
            </div>
            <Phone className="h-6 w-6 text-primary" />
          </div>
        </CardHeader>
        <CardContent className="pt-6">
          {connections.length === 0 ? (
            <div className="text-center py-16 text-muted-foreground">
              <div className="mx-auto w-16 h-16 rounded-full bg-slate-800/50 flex items-center justify-center mb-4">
                <Phone className="h-8 w-8 text-slate-500" />
              </div>
              <p className="text-lg font-medium mb-2">Nenhuma conexão criada ainda</p>
              <p className="text-sm">
                Vá para a página WhatsApp para criar sua primeira conexão
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {connections.slice(0, 5).map((conn) => (
                <div
                  key={conn.id}
                  className="flex items-center justify-between p-4 rounded-xl border border-slate-700/50 bg-slate-800/20 hover-elevate transition-all duration-200"
                  data-testid={`connection-${conn.sessionName}`}
                >
                  <div className="flex items-center gap-4">
                    <div
                      className={`relative h-12 w-12 rounded-full flex items-center justify-center ${
                        conn.status === "connected"
                          ? "bg-success/10 ring-2 ring-success/30"
                          : conn.status === "error"
                          ? "bg-destructive/10 ring-2 ring-destructive/30"
                          : "bg-slate-700/30"
                      }`}
                    >
                      <Phone
                        className={`h-6 w-6 ${
                          conn.status === "connected"
                            ? "text-success"
                            : conn.status === "error"
                            ? "text-destructive"
                            : "text-slate-500"
                        }`}
                      />
                      {conn.status === "connected" && (
                        <span className="absolute top-0 right-0 h-3 w-3 rounded-full bg-success ring-2 ring-slate-900 animate-pulse" />
                      )}
                    </div>
                    <div>
                      <p className="font-semibold text-foreground">{conn.sessionName}</p>
                      <p className="text-sm text-muted-foreground">
                        {conn.phoneNumber || "Aguardando conexão"}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    {conn.status === "connected" ? (
                      <Badge className="bg-success/10 text-success ring-1 ring-success/20" data-testid={`badge-status-${conn.sessionName}`}>
                        <span className="h-1.5 w-1.5 rounded-full bg-success mr-2 animate-pulse" />
                        Conectado
                      </Badge>
                    ) : conn.status === "error" ? (
                      <Badge className="bg-destructive/10 text-destructive ring-1 ring-destructive/20" data-testid={`badge-status-${conn.sessionName}`}>
                        <AlertCircle className="h-3 w-3 mr-1" />
                        Erro
                      </Badge>
                    ) : (
                      <Badge className="bg-slate-700/30 text-slate-400" data-testid={`badge-status-${conn.sessionName}`}>
                        <span className="h-1.5 w-1.5 rounded-full bg-slate-500 mr-2" />
                        Desconectado
                      </Badge>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
