import { useEffect, useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Loader2, RefreshCw, CheckCircle2, XCircle } from "lucide-react";
import { Badge } from "@/components/ui/badge";

interface WhatsAppQRModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  sessionName: string;
  qrCode?: string;
  status: string;
  onRefresh: () => void;
}

export function WhatsAppQRModal({
  open,
  onOpenChange,
  sessionName,
  qrCode,
  status,
  onRefresh,
}: WhatsAppQRModalProps) {
  const [countdown, setCountdown] = useState(45);

  useEffect(() => {
    if (!open || status === "connected") return;

    const timer = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) {
          onRefresh();
          return 45;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [open, status, onRefresh]);

  const getStatusBadge = () => {
    switch (status) {
      case "connected":
        return (
          <Badge className="bg-green-500 hover:bg-green-600" data-testid="badge-connected">
            <CheckCircle2 className="h-3 w-3 mr-1" />
            Conectado
          </Badge>
        );
      case "connecting":
        return (
          <Badge variant="secondary" data-testid="badge-connecting">
            <Loader2 className="h-3 w-3 mr-1 animate-spin" />
            Aguardando Scan
          </Badge>
        );
      case "disconnected":
        return (
          <Badge variant="destructive" data-testid="badge-disconnected">
            <XCircle className="h-3 w-3 mr-1" />
            Desconectado
          </Badge>
        );
      default:
        return (
          <Badge variant="outline" data-testid="badge-unknown">
            {status}
          </Badge>
        );
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md" data-testid="dialog-qr-modal">
        <DialogHeader>
          <DialogTitle className="flex items-center justify-between">
            <span>Conectar WhatsApp</span>
            {getStatusBadge()}
          </DialogTitle>
          <DialogDescription>
            Escaneie o QR Code com seu WhatsApp para conectar a sessão{" "}
            <span className="font-mono font-semibold">{sessionName}</span>
          </DialogDescription>
        </DialogHeader>

        <div className="flex flex-col items-center justify-center space-y-6 py-6">
          {status === "connected" ? (
            <div className="flex flex-col items-center space-y-4">
              <div className="rounded-full bg-green-100 dark:bg-green-900/20 p-6">
                <CheckCircle2 className="h-16 w-16 text-green-600 dark:text-green-400" />
              </div>
              <div className="text-center">
                <h3 className="text-lg font-semibold text-green-600 dark:text-green-400">
                  Conectado com Sucesso!
                </h3>
                <p className="text-sm text-muted-foreground mt-1">
                  Sua sessão WhatsApp está ativa
                </p>
              </div>
            </div>
          ) : qrCode ? (
            <>
              <div className="relative bg-white p-4 rounded-lg shadow-lg border-2 border-primary/20">
                <img
                  src={qrCode}
                  alt="QR Code WhatsApp"
                  className="w-64 h-64 object-contain"
                  data-testid="img-qrcode"
                />
              </div>

              <div className="text-center space-y-2">
                <p className="text-sm text-muted-foreground">
                  Abra o WhatsApp no seu celular e escaneie o código
                </p>
                <div className="flex items-center justify-center gap-2">
                  <span className="text-xs text-muted-foreground">
                    Expira em {countdown}s
                  </span>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={onRefresh}
                    data-testid="button-refresh-qr"
                  >
                    <RefreshCw className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </>
          ) : (
            <div className="flex flex-col items-center space-y-4 py-8">
              <Loader2 className="h-12 w-12 animate-spin text-primary" />
              <p className="text-sm text-muted-foreground">
                Gerando QR Code...
              </p>
            </div>
          )}
        </div>

        {status === "connected" && (
          <div className="flex justify-end">
            <Button onClick={() => onOpenChange(false)} data-testid="button-close-modal">
              Fechar
            </Button>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
