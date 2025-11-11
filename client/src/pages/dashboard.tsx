import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Phone, CheckCircle, XCircle, Activity } from "lucide-react";
import type { WhatsAppConnection } from "@shared/schema";

export default function Dashboard() {
  const { data: connections = [], isLoading } = useQuery<WhatsAppConnection[]>({
    queryKey: ["/api/whatsapp/connections"],
  });

  const stats = {
    total: connections.length,
    connected: connections.filter((c) => c.connected).length,
    disconnected: connections.filter((c) => !c.connected).length,
  };

  const cards = [
    {
      title: "Total de Conexões",
      value: stats.total,
      description: "Sessões criadas",
      icon: Phone,
      color: "text-blue-600 dark:text-blue-400",
    },
    {
      title: "Conexões Ativas",
      value: stats.connected,
      description: "Online agora",
      icon: CheckCircle,
      color: "text-green-600 dark:text-green-400",
    },
    {
      title: "Desconectadas",
      value: stats.disconnected,
      description: "Aguardando conexão",
      icon: XCircle,
      color: "text-red-600 dark:text-red-400",
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
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-semibold">Dashboard</h1>
        <p className="text-muted-foreground mt-2">
          Visão geral do sistema de gerenciamento WhatsApp
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {cards.map((card) => (
          <Card key={card.title} className="hover-elevate" data-testid={`card-${card.title.toLowerCase().replace(/\s+/g, "-")}`}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                {card.title}
              </CardTitle>
              <card.icon className={`h-4 w-4 ${card.color}`} />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold" data-testid={`text-${card.title.toLowerCase().replace(/\s+/g, "-")}-value`}>{card.value}</div>
              <p className="text-xs text-muted-foreground mt-1">
                {card.description}
              </p>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Conexões Recentes</CardTitle>
          <CardDescription>
            Últimas sessões WhatsApp criadas
          </CardDescription>
        </CardHeader>
        <CardContent>
          {connections.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              <Phone className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>Nenhuma conexão criada ainda</p>
              <p className="text-sm mt-2">
                Vá para a página WhatsApp para criar sua primeira conexão
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {connections.slice(0, 5).map((conn) => (
                <div
                  key={conn.id}
                  className="flex items-center justify-between p-4 border rounded-lg hover-elevate"
                  data-testid={`connection-${conn.sessionName}`}
                >
                  <div className="flex items-center gap-4">
                    <div
                      className={`h-10 w-10 rounded-full flex items-center justify-center ${
                        conn.connected
                          ? "bg-green-100 dark:bg-green-900/20"
                          : "bg-gray-100 dark:bg-gray-800"
                      }`}
                    >
                      <Phone
                        className={`h-5 w-5 ${
                          conn.connected
                            ? "text-green-600 dark:text-green-400"
                            : "text-gray-500"
                        }`}
                      />
                    </div>
                    <div>
                      <p className="font-medium">{conn.sessionName}</p>
                      <p className="text-sm text-muted-foreground">
                        {conn.phoneNumber || "Aguardando conexão"}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {conn.connected ? (
                      <span className="text-sm text-green-600 dark:text-green-400 font-medium">
                        Conectado
                      </span>
                    ) : (
                      <span className="text-sm text-muted-foreground">
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
