import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Phone, CheckCircle, XCircle, Activity, TrendingUp, Clock } from "lucide-react";
import type { WhatsAppConnection } from "@shared/schema";

export default function Dashboard() {
  const { data: connections = [], isLoading } = useQuery<WhatsAppConnection[]>({
    queryKey: ["/api/whatsapp/connections"],
  });

  const stats = {
    total: connections.length,
    connected: connections.filter((c) => c.status === "connected").length,
    disconnected: connections.filter((c) => c.status !== "connected").length,
    uptime: 99.8,
  };

  const cards = [
    {
      title: "Total de Conexões",
      value: stats.total,
      description: "Sessões gerenciadas",
      icon: Phone,
      gradient: "from-blue-500/20 to-cyan-500/20",
      iconColor: "text-blue-400",
      trend: "+12%",
      trendUp: true,
    },
    {
      title: "Conexões Ativas",
      value: stats.connected,
      description: "Online agora",
      icon: CheckCircle,
      gradient: "from-green-500/20 to-emerald-500/20",
      iconColor: "text-green-400",
      trend: "+8%",
      trendUp: true,
    },
    {
      title: "Desconectadas",
      value: stats.disconnected,
      description: "Aguardando conexão",
      icon: XCircle,
      gradient: "from-red-500/20 to-rose-500/20",
      iconColor: "text-red-400",
      trend: "-3%",
      trendUp: false,
    },
    {
      title: "Disponibilidade",
      value: `${stats.uptime}%`,
      description: "Uptime do sistema",
      icon: Activity,
      gradient: "from-violet-500/20 to-purple-500/20",
      iconColor: "text-violet-400",
      trend: "+0.2%",
      trendUp: true,
    },
  ];

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Activity className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="space-y-10">
      <div className="space-y-2">
        <h1 className="text-4xl font-semibold bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">
          Dashboard
        </h1>
        <p className="text-muted-foreground text-lg">
          Visão geral do sistema de gerenciamento WhatsApp
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {cards.map((card) => (
          <Card
            key={card.title}
            className={`relative overflow-hidden border-slate-700/50 bg-gradient-to-br ${card.gradient} backdrop-blur-xl hover-elevate transition-all duration-300`}
            data-testid={`card-${card.title.toLowerCase().replace(/\s+/g, "-")}`}
          >
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-slate-300">
                {card.title}
              </CardTitle>
              <card.icon className={`h-8 w-8 ${card.iconColor}`} />
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="text-3xl font-bold" data-testid={`text-${card.title.toLowerCase().replace(/\s+/g, "-")}-value`}>
                {card.value}
              </div>
              <div className="flex items-center justify-between">
                <p className="text-xs text-muted-foreground">
                  {card.description}
                </p>
                <div className={`flex items-center gap-1 text-xs font-medium ${card.trendUp ? 'text-green-400' : 'text-red-400'}`}>
                  <TrendingUp className={`h-3 w-3 ${!card.trendUp && 'rotate-180'}`} />
                  {card.trend}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card className="border-slate-700/50 backdrop-blur-xl bg-card/40">
        <CardHeader className="border-b border-slate-700/50 pb-6">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-2xl">Conexões Recentes</CardTitle>
              <p className="text-muted-foreground mt-2">
                Últimas sessões WhatsApp gerenciadas
              </p>
            </div>
            <Clock className="h-6 w-6 text-slate-400" />
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
                          ? "bg-green-500/10 ring-2 ring-green-500/20"
                          : "bg-slate-700/30"
                      }`}
                    >
                      <Phone
                        className={`h-6 w-6 ${
                          conn.status === "connected"
                            ? "text-green-400"
                            : "text-slate-500"
                        }`}
                      />
                      {conn.status === "connected" && (
                        <span className="absolute top-0 right-0 h-3 w-3 rounded-full bg-green-400 ring-2 ring-slate-900" />
                      )}
                    </div>
                    <div>
                      <p className="font-semibold text-slate-100">{conn.sessionName}</p>
                      <p className="text-sm text-muted-foreground">
                        {conn.phoneNumber || "Aguardando conexão"}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    {conn.status === "connected" ? (
                      <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-green-500/10 text-green-400 text-sm font-medium ring-1 ring-green-500/20">
                        <span className="h-1.5 w-1.5 rounded-full bg-green-400 animate-pulse" />
                        Conectado
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-slate-700/30 text-slate-400 text-sm font-medium">
                        <span className="h-1.5 w-1.5 rounded-full bg-slate-500" />
                        Desconectado
                      </span>
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
