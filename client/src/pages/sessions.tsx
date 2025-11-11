import { useQuery } from "@tanstack/react-query";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { CheckCircle2, XCircle, Activity } from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import { ptBR } from "date-fns/locale";
import type { WhatsAppConnection } from "@shared/schema";

export default function SessionsPage() {
  const { data: connections = [], isLoading } = useQuery<WhatsAppConnection[]>({
    queryKey: ["/api/whatsapp/connections"],
  });

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
        <h1 className="text-3xl font-semibold">Sessões</h1>
        <p className="text-muted-foreground mt-2">
          Gerencie todas as sessões WhatsApp do sistema
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Todas as Sessões</CardTitle>
          <CardDescription>
            Visualize o status e informações de todas as conexões
          </CardDescription>
        </CardHeader>
        <CardContent>
          {connections.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              <Activity className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>Nenhuma sessão encontrada</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Sessão</TableHead>
                  <TableHead>Telefone</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Última Conexão</TableHead>
                  <TableHead>Criado em</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {connections.map((connection) => (
                  <TableRow key={connection.id} data-testid={`row-session-${connection.sessionName}`}>
                    <TableCell className="font-medium">
                      {connection.sessionName}
                    </TableCell>
                    <TableCell className="font-mono text-sm">
                      {connection.phoneNumber || "-"}
                    </TableCell>
                    <TableCell>
                      {connection.connected ? (
                        <Badge className="bg-green-500 hover:bg-green-600" data-testid={`badge-connected-${connection.sessionName}`}>
                          <CheckCircle2 className="h-3 w-3 mr-1" />
                          Conectado
                        </Badge>
                      ) : (
                        <Badge variant="secondary" data-testid={`badge-disconnected-${connection.sessionName}`}>
                          <XCircle className="h-3 w-3 mr-1" />
                          Desconectado
                        </Badge>
                      )}
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {connection.lastConnectedAt
                        ? formatDistanceToNow(new Date(connection.lastConnectedAt), {
                            addSuffix: true,
                            locale: ptBR,
                          })
                        : "Nunca"}
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {formatDistanceToNow(new Date(connection.createdAt), {
                        addSuffix: true,
                        locale: ptBR,
                      })}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
