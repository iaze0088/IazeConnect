import { Home, MessageSquare, Activity, FileText, Settings, Phone, LogOut } from "lucide-react";
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarFooter,
} from "@/components/ui/sidebar";
import { Link, useLocation } from "wouter";
import { useAuth } from "@/hooks/use-auth";

const menuItems = [
  {
    title: "Dashboard",
    url: "/dashboard",
    icon: Home,
  },
  {
    title: "WhatsApp",
    url: "/whatsapp",
    icon: Phone,
  },
  {
    title: "Sessões",
    url: "/sessions",
    icon: MessageSquare,
  },
  {
    title: "Logs",
    url: "/logs",
    icon: FileText,
  },
  {
    title: "Configurações",
    url: "/settings",
    icon: Settings,
  },
];

export function AppSidebar() {
  const [location] = useLocation();
  const { logout, userName } = useAuth();

  return (
    <Sidebar>
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel className="text-lg font-semibold px-4 py-6">
            IAZE
          </SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {menuItems.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton asChild isActive={location === item.url} data-testid={`link-${item.title.toLowerCase()}`}>
                    <Link href={item.url}>
                      <item.icon className="h-4 w-4" />
                      <span>{item.title}</span>
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
      <SidebarFooter className="border-t border-border/50 p-4">
        <div className="space-y-3">
          {userName && (
            <div className="px-3 py-2 text-sm text-muted-foreground">
              Logado como: <span className="font-medium text-foreground">{userName}</span>
            </div>
          )}
          <SidebarMenuButton
            onClick={logout}
            className="w-full hover-elevate"
            data-testid="button-logout"
          >
            <LogOut className="h-4 w-4" />
            <span>Sair</span>
          </SidebarMenuButton>
        </div>
      </SidebarFooter>
    </Sidebar>
  );
}
