import { Badge } from './badge';
import { cn } from '@/lib/utils';

interface ColoredBadgeProps {
  text: string;
  type: 'language' | 'subnicho';
  className?: string;
}

// Badges minimalistas e neutras (o card já tem cor de fundo)
export const ColoredBadge = ({ text, type, className }: ColoredBadgeProps) => {
  return (
    <Badge 
      variant="outline" 
      className={cn('border-white/30 text-white/90 bg-white/5', className)}
    >
      {text}
    </Badge>
  );
};
