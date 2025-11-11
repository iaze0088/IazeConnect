import { useEffect, useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Loader2, RefreshCw, CheckCircle2, Smartphone, HelpCircle } from "lucide-react";
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
  const [showSuccess, setShowSuccess] = useState(false);

  useEffect(() => {
    if (!open || status === "connected") {
      if (status === "connected" && open) {
        setShowSuccess(true);
        const successTimeout = setTimeout(() => {
          onOpenChange(false);
          setShowSuccess(false);
        }, 3000);
        return () => clearTimeout(successTimeout);
      }
      return;
    }

    // Reset countdown when modal opens for new session
    setCountdown(45);

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
  }, [open, status, onRefresh, onOpenChange]);

  const getCountdownColor = () => {
    if (countdown > 30) return "stroke-green-400";
    if (countdown > 15) return "stroke-yellow-400";
    return "stroke-red-400";
  };

  const circumference = 2 * Math.PI * 54;
  const strokeDashoffset = circumference - (countdown / 45) * circumference;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent 
        className="sm:max-w-xl border-slate-700/50 bg-slate-900/95 backdrop-blur-2xl shadow-2xl shadow-blue-500/10" 
        data-testid="dialog-qr-modal"
      >
        <DialogHeader className="space-y-3">
          <DialogTitle className="text-2xl bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">
            Conectar WhatsApp
          </DialogTitle>
          <DialogDescription className="text-slate-400">
            Escaneie o QR Code para conectar a sessão{" "}
            <span className="font-mono font-semibold text-slate-300">{sessionName}</span>
          </DialogDescription>
        </DialogHeader>

        <div className="flex flex-col items-center justify-center space-y-8 py-6">
          {showSuccess || status === "connected" ? (
            <div className="flex flex-col items-center space-y-6 animate-in fade-in duration-500">
              <div className="relative">
                <div className="absolute inset-0 rounded-full bg-green-500/20 blur-2xl animate-pulse" />
                <div className="relative rounded-full bg-gradient-to-br from-green-500/20 to-emerald-500/20 p-8 ring-4 ring-green-500/20">
                  <CheckCircle2 className="h-20 w-20 text-green-400 animate-in zoom-in duration-500" />
                </div>
              </div>
              <div className="text-center space-y-2">
                <h3 className="text-2xl font-semibold bg-gradient-to-r from-green-400 to-emerald-400 bg-clip-text text-transparent">
                  Conectado com Sucesso!
                </h3>
                <p className="text-slate-400">
                  Sua sessão WhatsApp está ativa e pronta para uso
                </p>
                <Badge className="mt-4 bg-green-500/10 text-green-400 border-green-500/20 hover:bg-green-500/20">
                  <span className="h-2 w-2 rounded-full bg-green-400 mr-2 animate-pulse" />
                  Online
                </Badge>
              </div>
              <Button 
                onClick={() => onOpenChange(false)} 
                className="bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-600 hover:to-cyan-600"
                data-testid="button-close-modal"
              >
                Continuar
              </Button>
            </div>
          ) : qrCode ? (
            <>
              <div className="relative">
                {/* Pulsing Border Animation */}
                <div className="absolute -inset-4 rounded-2xl bg-gradient-to-r from-blue-500 to-cyan-500 opacity-20 blur-xl animate-pulse" />
                
                {/* Countdown Ring */}
                <svg className="absolute -inset-2 w-[calc(100%+16px)] h-[calc(100%+16px)] -rotate-90">
                  <circle
                    cx="50%"
                    cy="50%"
                    r="54"
                    stroke="currentColor"
                    strokeWidth="3"
                    fill="none"
                    className="text-slate-700/30"
                  />
                  <circle
                    cx="50%"
                    cy="50%"
                    r="54"
                    strokeWidth="3"
                    fill="none"
                    strokeDasharray={circumference}
                    strokeDashoffset={strokeDashoffset}
                    className={`${getCountdownColor()} transition-all duration-1000 ease-linear`}
                    strokeLinecap="round"
                  />
                </svg>

                {/* QR Code */}
                <div className="relative bg-white p-6 rounded-xl shadow-2xl ring-1 ring-slate-800">
                  <img
                    src={qrCode}
                    alt="QR Code WhatsApp"
                    className="w-64 h-64 object-contain"
                    data-testid="img-qrcode"
                  />
                </div>

                {/* Countdown Badge */}
                <div className="absolute -bottom-3 left-1/2 -translate-x-1/2">
                  <Badge className="bg-slate-800/90 backdrop-blur-sm border-slate-700/50 text-slate-300 px-4 py-1.5">
                    Expira em {countdown}s
                  </Badge>
                </div>
              </div>

              {/* Instructions */}
              <div className="space-y-4 w-full max-w-sm">
                <div className="flex items-center gap-3 p-4 rounded-lg bg-blue-500/5 border border-blue-500/10">
                  <div className="flex-shrink-0 w-10 h-10 rounded-full bg-blue-500/10 flex items-center justify-center">
                    <Smartphone className="h-5 w-5 text-blue-400" />
                  </div>
                  <div className="text-sm">
                    <p className="font-medium text-slate-300 mb-1">Como conectar</p>
                    <ol className="text-slate-400 space-y-1 text-xs">
                      <li>1. Abra WhatsApp no celular</li>
                      <li>2. Toque em Configurações → Aparelhos conectados</li>
                      <li>3. Escaneie este QR Code</li>
                    </ol>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex gap-2">
                  <Button
                    onClick={onRefresh}
                    variant="outline"
                    className="flex-1 border-slate-700 hover:bg-slate-800/50"
                    data-testid="button-refresh-qr"
                  >
                    <RefreshCw className="h-4 w-4 mr-2" />
                    Atualizar QR
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="flex-shrink-0"
                    onClick={() => window.open('https://faq.whatsapp.com/1317564962315842/', '_blank')}
                  >
                    <HelpCircle className="h-4 w-4" />
                  </Button>
                </div>

                {/* Status Indicator */}
                <div className="flex items-center justify-center gap-2 pt-2">
                  <span className="relative flex h-2 w-2">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-500"></span>
                  </span>
                  <span className="text-xs text-slate-400">Aguardando scan...</span>
                </div>
              </div>
            </>
          ) : (
            <div className="flex flex-col items-center space-y-6 py-12">
              <div className="relative">
                <div className="absolute inset-0 rounded-full bg-blue-500/20 blur-2xl animate-pulse" />
                <div className="relative">
                  <Loader2 className="h-16 w-16 animate-spin text-blue-400" />
                </div>
              </div>
              <div className="text-center space-y-2">
                <p className="text-lg font-medium text-slate-300">
                  Gerando QR Code
                </p>
                <p className="text-sm text-slate-400">
                  Aguarde alguns instantes...
                </p>
              </div>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
