import * as React from "react";
import { cn } from "@/lib/utils";
import { X } from "lucide-react";
import { Button } from "./button";

interface BottomSheetProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  children: React.ReactNode;
  title?: string;
}

export const BottomSheet = ({ open, onOpenChange, children, title }: BottomSheetProps) => {
  const [startY, setStartY] = React.useState<number | null>(null);
  const [currentY, setCurrentY] = React.useState<number | null>(null);

  const handleTouchStart = (e: React.TouchEvent) => {
    setStartY(e.touches[0].clientY);
  };

  const handleTouchMove = (e: React.TouchEvent) => {
    if (!startY) return;
    setCurrentY(e.touches[0].clientY);
  };

  const handleTouchEnd = () => {
    if (!startY || !currentY) return;
    const diff = currentY - startY;
    if (diff > 100) {
      onOpenChange(false);
    }
    setStartY(null);
    setCurrentY(null);
  };

  if (!open) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 z-50 bg-black/50 animate-in fade-in"
        onClick={() => onOpenChange(false)}
      />
      
      {/* Sheet */}
      <div
        className={cn(
          "fixed inset-x-0 bottom-0 z-50 bg-dashboard-card border-t border-dashboard-border",
          "rounded-t-2xl max-h-[70vh] overflow-hidden",
          "animate-in slide-in-from-bottom duration-300"
        )}
        onTouchStart={handleTouchStart}
        onTouchMove={handleTouchMove}
        onTouchEnd={handleTouchEnd}
      >
        {/* Handle */}
        <div className="flex justify-center pt-3 pb-2 cursor-grab active:cursor-grabbing">
          <div className="w-10 h-1 bg-muted-foreground/30 rounded-full" />
        </div>

        {/* Header */}
        <div className="flex items-center justify-between px-5 pb-3 border-b border-dashboard-border">
          <h3 className="text-lg font-semibold text-foreground">{title || "Filtros"}</h3>
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8"
            onClick={() => onOpenChange(false)}
          >
            <X className="h-5 w-5" />
          </Button>
        </div>

        {/* Content */}
        <div className="overflow-y-auto max-h-[calc(70vh-8rem)] p-5">
          {children}
        </div>
      </div>
    </>
  );
};

interface BottomSheetActionsProps {
  onClear: () => void;
  onApply: () => void;
}

export const BottomSheetActions = ({ onClear, onApply }: BottomSheetActionsProps) => {
  return (
    <div className="sticky bottom-0 left-0 right-0 bg-dashboard-card border-t border-dashboard-border p-5 flex gap-3">
      <Button
        variant="outline"
        className="flex-1 h-11"
        onClick={onClear}
      >
        Limpar
      </Button>
      <Button
        className="flex-1 h-11"
        onClick={onApply}
      >
        Aplicar
      </Button>
    </div>
  );
};
