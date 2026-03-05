import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Dashboard from "./components/Dashboard";
import NotFound from "./pages/NotFound";

// ⚡ CACHE: Calcula ms até 5h da manhã (Brasília) - reseta após coleta diária
const getMsUntil5AMBrasilia = () => {
  const now = new Date();
  // Brasília = UTC-3
  const brasiliaOffset = -3 * 60;
  const localOffset = now.getTimezoneOffset();
  const diffMinutes = brasiliaOffset - (-localOffset);
  
  // Hora atual em Brasília
  const brasiliaTime = new Date(now.getTime() + diffMinutes * 60 * 1000);
  
  // Próximas 5h em Brasília (horário da coleta diária)
  const next5AM = new Date(brasiliaTime);
  next5AM.setHours(5, 0, 0, 0);
  
  // Se já passou das 5h, vai para amanhã
  if (brasiliaTime.getHours() >= 5) {
    next5AM.setDate(next5AM.getDate() + 1);
  }
  
  // Converte de volta para horário local
  const next5AMLocal = new Date(next5AM.getTime() - diffMinutes * 60 * 1000);
  
  const msUntil5AM = next5AMLocal.getTime() - now.getTime();
  
  // Cache máximo de 4 horas, ou até as 5h se for antes
  const FOUR_HOURS = 4 * 60 * 60 * 1000;
  return Math.min(msUntil5AM, FOUR_HOURS);
};

const cacheTime = getMsUntil5AMBrasilia();

// ⚡ OTIMIZAÇÃO: Cache de 4h ou até 5h Brasília (coleta diária)
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: cacheTime, // Dados frescos por 4h ou até coleta
      gcTime: cacheTime + 60 * 60 * 1000, // +1h de margem
      refetchOnWindowFocus: false, // Evita refetch desnecessários
      retry: 1, // Apenas 1 retry para falhar mais rápido
    },
  },
});

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter basename="/dash">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
