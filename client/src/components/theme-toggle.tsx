import { Moon, Sun } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useTheme } from "@/contexts/ThemeProvider";

export function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();

  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={toggleTheme}
      data-testid="button-theme-toggle"
      className="hover-elevate active-elevate-2"
    >
      {theme === "light" ? (
        <Moon className="h-5 w-5" data-testid="icon-moon" />
      ) : (
        <Sun className="h-5 w-5" data-testid="icon-sun" />
      )}
      <span className="sr-only">Alternar tema</span>
    </Button>
  );
}
