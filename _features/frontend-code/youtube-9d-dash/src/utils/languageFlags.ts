/**
 * Centralized language flag mapping
 * Returns appropriate flag emoji for each language
 */

const normalizeString = (str: string): string =>
  str.toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '');

const LANGUAGE_FLAGS: Record<string, string> = {
  // Portuguese variations
  'portuguese': '🇧🇷',
  'portugues': '🇧🇷',
  'pt': '🇧🇷',
  'pt-br': '🇧🇷',
  'br': '🇧🇷',
  
  // English variations
  'english': '🇺🇸',
  'ingles': '🇺🇸',
  'en': '🇺🇸',
  'en-us': '🇺🇸',
  'us': '🇺🇸',
  
  // Spanish variations
  'spanish': '🇪🇸',
  'espanhol': '🇪🇸',
  'es': '🇪🇸',
  
  // French variations
  'french': '🇫🇷',
  'frances': '🇫🇷',
  'francais': '🇫🇷',
  'fr': '🇫🇷',
  
  // German variations
  'german': '🇩🇪',
  'alemao': '🇩🇪',
  'de': '🇩🇪',
  
  // Italian variations
  'italian': '🇮🇹',
  'italiano': '🇮🇹',
  'it': '🇮🇹',
  
  // Japanese variations
  'japanese': '🇯🇵',
  'japones': '🇯🇵',
  'jp': '🇯🇵',
  'ja': '🇯🇵',
  '古代の物語': '🇯🇵',
  'kodai no monogatari': '🇯🇵',
  
  // Korean variations
  'korean': '🇰🇷',
  'coreano': '🇰🇷',
  'ko': '🇰🇷',
  'kr': '🇰🇷',
  
  // Arabic variations
  'arabic': '🇸🇦',
  'arabe': '🇸🇦',
  'ar': '🇸🇦',
  
  // Chinese variations
  'chinese': '🇨🇳',
  'chines': '🇨🇳',
  'zh': '🇨🇳',
  'cn': '🇨🇳',
  
  // Russian variations
  'russian': '🇷🇺',
  'russo': '🇷🇺',
  'ru': '🇷🇺',
  
  // Hindi variations
  'hindi': '🇮🇳',
  'hi': '🇮🇳',
  'in': '🇮🇳',
  
  // Turkish variations
  'turkish': '🇹🇷',
  'turco': '🇹🇷',
  'tr': '🇹🇷',
  'turquia': '🇹🇷',
  
  // Polish variations
  'polish': '🇵🇱',
  'polones': '🇵🇱',
  'pl': '🇵🇱',
};

export const getLanguageFlag = (lingua: string | null | undefined): string => {
  if (!lingua) return '🏳️';
  
  const normalized = normalizeString(lingua);
  return LANGUAGE_FLAGS[normalized] || '🏳️';
};
