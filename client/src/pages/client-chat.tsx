import { useState, useEffect, useRef } from "react";
import { useLocation } from "wouter";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { ScrollArea } from "@/components/ui/scroll-area";
import { LogOut, Send, User } from "lucide-react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { apiRequest, queryClient } from "@/lib/queryClient";
import { useToast } from "@/hooks/use-toast";

interface Message {
  id: string;
  fromType: "client" | "agent" | "system" | "ai";
  text: string;
  createdAt: string;
}

export default function ClientChat() {
  const [, setLocation] = useLocation();
  const { toast } = useToast();
  const [message, setMessage] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);

  // Get user from localStorage
  const userStr = localStorage.getItem("iaze_user");
  const user = userStr ? JSON.parse(userStr) : {};
  const token = localStorage.getItem("iaze_token");

  useEffect(() => {
    if (!token || !user.id) {
      setLocation("/");
    }
  }, [token, user.id, setLocation]);

  // Get user tickets
  const { data: tickets = [] } = useQuery<any[]>({
    queryKey: ["/api/clients/me/tickets"],
    enabled: !!user.id,
  });

  // Get messages for current ticket (first ticket)
  const currentTicket = tickets[0];
  const { data: messages = [], isLoading } = useQuery<Message[]>({
    queryKey: ["/api/tickets", currentTicket?.id, "messages"],
    enabled: !!currentTicket?.id,
  });

  const sendMessage = useMutation({
    mutationFn: async (text: string) => {
      if (!currentTicket?.id) throw new Error("Nenhum ticket ativo");
      return await apiRequest("POST", `/api/tickets/${currentTicket.id}/messages`, {
        text,
        fromType: "client",
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/tickets", currentTicket?.id, "messages"] });
      setMessage("");
      
      // Scroll to bottom
      setTimeout(() => {
        scrollRef.current?.scrollIntoView({ behavior: "smooth" });
      }, 100);
    },
    onError: (error: any) => {
      toast({
        title: "Erro ao enviar mensagem",
        description: error.message,
        variant: "destructive",
      });
    },
  });

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault();
    if (!message.trim()) return;
    sendMessage.mutate(message);
  };

  const handleLogout = () => {
    localStorage.removeItem("iaze_token");
    localStorage.removeItem("iaze_user");
    setLocation("/");
  };

  useEffect(() => {
    // Auto scroll to bottom when messages change
    scrollRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800 p-4">
      <div className="max-w-4xl mx-auto">
        <Card className="h-[calc(100vh-2rem)]">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4 border-b">
            <div className="flex items-center gap-3">
              <Avatar>
                <AvatarFallback>
                  <User className="w-4 h-4" />
                </AvatarFallback>
              </Avatar>
              <div>
                <CardTitle className="text-lg">
                  {user.displayName || "Olá!"}
                </CardTitle>
                <p className="text-sm text-muted-foreground">
                  {user.whatsapp}
                </p>
              </div>
            </div>
            <Button
              variant="ghost"
              size="icon"
              onClick={handleLogout}
              data-testid="button-logout"
            >
              <LogOut className="w-4 h-4" />
            </Button>
          </CardHeader>

          <CardContent className="p-0 flex flex-col h-[calc(100%-5rem)]">
            <ScrollArea className="flex-1 p-4">
              {isLoading && (
                <div className="text-center text-muted-foreground">
                  Carregando mensagens...
                </div>
              )}
              
              {!isLoading && messages.length === 0 && (
                <div className="text-center text-muted-foreground py-8">
                  Nenhuma mensagem ainda. Inicie a conversa!
                </div>
              )}

              <div className="space-y-4">
                {messages.map((msg) => (
                  <div
                    key={msg.id}
                    className={`flex ${msg.fromType === "client" ? "justify-end" : "justify-start"}`}
                    data-testid={`message-${msg.id}`}
                  >
                    <div
                      className={`max-w-[70%] rounded-lg px-4 py-2 ${
                        msg.fromType === "client"
                          ? "bg-primary text-primary-foreground"
                          : msg.fromType === "system"
                          ? "bg-muted text-muted-foreground text-center w-full"
                          : "bg-secondary"
                      }`}
                    >
                      <p className="text-sm">{msg.text}</p>
                      <p className="text-xs opacity-70 mt-1">
                        {new Date(msg.createdAt).toLocaleTimeString()}
                      </p>
                    </div>
                  </div>
                ))}
                <div ref={scrollRef} />
              </div>
            </ScrollArea>

            <form onSubmit={handleSend} className="p-4 border-t flex gap-2">
              <Input
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder="Digite sua mensagem..."
                disabled={sendMessage.isPending || !currentTicket}
                data-testid="input-message"
              />
              <Button
                type="submit"
                size="icon"
                disabled={!message.trim() || sendMessage.isPending || !currentTicket}
                data-testid="button-send"
              >
                <Send className="w-4 h-4" />
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
