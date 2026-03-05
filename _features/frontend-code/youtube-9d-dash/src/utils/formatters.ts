// ⚡ OTIMIZAÇÃO: Cache de formatação para evitar recálculos
const formatCache = new Map<number, string>();

export function formatNumber(num: number | undefined | null): string {
  if (num == null || num === undefined) {
    return '0';
  }
  
  // Verifica cache
  if (formatCache.has(num)) {
    return formatCache.get(num)!;
  }
  
  let result: string;
  if (num >= 1_000_000) {
    result = `${(num / 1_000_000).toFixed(1)}M`;
  } else if (num >= 1_000) {
    result = `${(num / 1_000).toFixed(1)}K`;
  } else {
    result = num.toString();
  }
  
  // Limita o cache a 1000 entradas para não crescer infinitamente
  if (formatCache.size > 1000) {
    const firstKey = formatCache.keys().next().value;
    formatCache.delete(firstKey);
  }
  
  formatCache.set(num, result);
  return result;
}

export function formatGrowth(growth: number | undefined | null): string {
  if (growth == null || growth === undefined) {
    return '0.0%';
  }
  const sign = growth >= 0 ? '+' : '';
  return `${sign}${growth.toFixed(1)}%`;
}

export function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric'
  });
}

export function formatRelativeDate(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffInMs = now.getTime() - date.getTime();
  const diffInDays = Math.floor(diffInMs / (1000 * 60 * 60 * 24));
  
  if (diffInDays === 0) {
    return 'Publicado hoje';
  } else if (diffInDays === 1) {
    return 'Publicado há 1 dia';
  } else if (diffInDays < 30) {
    return `Publicado há ${diffInDays} dias`;
  } else if (diffInDays < 60) {
    return 'Publicado há 1 mês';
  } else {
    const months = Math.floor(diffInDays / 30);
    return `Publicado há ${months} meses`;
  }
}