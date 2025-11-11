import { Switch, Route, Redirect } from "wouter";
import { queryClient } from "./lib/queryClient";
import { QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import { SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/app-sidebar";
import { ThemeProvider } from "@/contexts/ThemeProvider";
import { ThemeToggle } from "@/components/theme-toggle";
import { AuthProvider, ProtectedRoute } from "@/hooks/use-auth";
import Dashboard from "@/pages/dashboard";
import WhatsAppPage from "@/pages/whatsapp";
import SessionsPage from "@/pages/sessions";
import LogsPage from "@/pages/logs";
import SettingsPage from "@/pages/settings";
import AdminLogin from "@/pages/admin-login";
import ClientLogin from "@/pages/client-login";
import ClientChat from "@/pages/client-chat";
import NotFound from "@/pages/not-found";

function Router() {
  return (
    <Switch>
      <Route path="/admin" component={AdminLogin} />
      <Route path="/client" component={ClientLogin} />
      <Route path="/client/chat" component={ClientChat} />
      <Route path="/dashboard">
        <ProtectedRoute>
          <AdminLayout>
            <Dashboard />
          </AdminLayout>
        </ProtectedRoute>
      </Route>
      <Route path="/whatsapp">
        <ProtectedRoute>
          <AdminLayout>
            <WhatsAppPage />
          </AdminLayout>
        </ProtectedRoute>
      </Route>
      <Route path="/sessions">
        <ProtectedRoute>
          <AdminLayout>
            <SessionsPage />
          </AdminLayout>
        </ProtectedRoute>
      </Route>
      <Route path="/logs">
        <ProtectedRoute>
          <AdminLayout>
            <LogsPage />
          </AdminLayout>
        </ProtectedRoute>
      </Route>
      <Route path="/settings">
        <ProtectedRoute>
          <AdminLayout>
            <SettingsPage />
          </AdminLayout>
        </ProtectedRoute>
      </Route>
      <Route path="/">
        {() => {
          const token = localStorage.getItem("admin_token");
          const role = localStorage.getItem("user_role");
          
          if (token && role === "admin") {
            return <Redirect to="/dashboard" />;
          }
          return <Redirect to="/admin" />;
        }}
      </Route>
      <Route component={NotFound} />
    </Switch>
  );
}

function AdminLayout({ children }: { children: React.ReactNode }) {
  const style = {
    "--sidebar-width": "16rem",
    "--sidebar-width-icon": "3rem",
  };

  return (
    <SidebarProvider style={style as React.CSSProperties}>
      <div className="flex h-screen w-full">
        <AppSidebar />
        <div className="flex flex-col flex-1 min-w-0">
          <header className="flex items-center justify-between p-4 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
            <SidebarTrigger data-testid="button-sidebar-toggle" />
            <div className="flex items-center gap-4">
              <span className="text-sm text-muted-foreground">
                Sistema IAZE
              </span>
              <ThemeToggle />
            </div>
          </header>
          <main className="flex-1 overflow-auto p-8">
            <div className="max-w-7xl mx-auto">
              {children}
            </div>
          </main>
        </div>
      </div>
    </SidebarProvider>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <TooltipProvider>
          <AuthProvider>
            <Router />
            <Toaster />
          </AuthProvider>
        </TooltipProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
}
