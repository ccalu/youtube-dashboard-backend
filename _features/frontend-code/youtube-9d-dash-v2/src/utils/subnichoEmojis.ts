/**
 * Mapeamento centralizado de emojis para subnichos.
 * Use este arquivo para manter consistência em todo o dashboard.
 */

const normalizeString = (str: string): string =>
  str.toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '');

const SUBNICHO_EMOJIS: Record<string, string> = {
  'monetizados': '💸',
  'historias sombrias': '🦇',
  'relatos de guerra': '⚔️',
  'frentes de guerra': '💣',
  'culturas macabras': '💀',
  'reis perversos': '👑',
  'terror': '👻',
  'historias aleatorias': '📚',
  'contos familiares': '👩🏼‍🤝‍👨🏻',
  'stickman': '🕺',
  'misterios': '👽',
  'mentalidade masculina e financas': '💼',
  'psicologia & mindset': '🧠',
  'psicologia': '🧠',
  'mindset': '🧠',
  'empreendedorismo': '💰',
  'guerras e civilizacoes': '🛡️',
  'pessoas desaparecidas': '🔎',
  'noticias e atualidade': '📰',
  'conspiracao': '🔍',
  'historias motivacionais': '🌟',
  'antiguidade': '🏛️',
  'licoes de vida': '👴🏻',
  'registros malditos': '👺',
  'desmonetizado': '❌',
  'desmonetizados': '❌',
};

export const getSubnichoEmoji = (subnicho: string): string => {
  const normalized = normalizeString(subnicho);
  return SUBNICHO_EMOJIS[normalized] || '📺';
};
