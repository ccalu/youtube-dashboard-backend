/**
 * Sistema de cores equilibradas para subniches
 * Paleta moderna profissional estilo Médio/Equilibrado
 * Saturação: 50-60% (cores vivas mas não cansativas)
 */

export function obterCorSubnicho(subniche: string): { fundo: string; borda: string; gradient?: string } {
  switch (subniche) {
    // 💸 Monetizados - Verde NEON vibrante (PRIMEIRO na lista) - COR ÚNICA
    case 'Monetizados':
    case 'monetizados':
      return { 
        fundo: '#22C55E', 
        borda: '#16A34A',
        gradient: 'linear-gradient(135deg, #4ADE80 0%, #22C55E 50%, #16A34A 100%)'
      };

    // 👻 Terror - Marrom avermelhado sombrio
    case 'Terror':
      return { fundo: '#7C2D12', borda: '#431407', gradient: 'linear-gradient(135deg, #9A3412 0%, #7C2D12 50%, #431407 100%)' };

    // 🦇 Histórias Sombrias - Roxo médio equilibrado
    case 'Histórias Sombrias':
    case 'Historias Sombrias':
      return { fundo: '#7C3AED', borda: '#5B21B6', gradient: 'linear-gradient(135deg, #A78BFA 0%, #7C3AED 50%, #5B21B6 100%)' };

    // ⚔️ Relatos de Guerra - Verde OLIVA militar (diferente de Monetizados)
    case 'Relatos de Guerra':
      return { fundo: '#65A30D', borda: '#4D7C0F', gradient: 'linear-gradient(135deg, #84CC16 0%, #65A30D 50%, #4D7C0F 100%)' };

    // 💣 Frentes de Guerra - Verde escuro militar
    case 'Frentes de Guerra':
      return { fundo: '#166534', borda: '#14532D', gradient: 'linear-gradient(135deg, #22C55E 0%, #166534 50%, #14532D 100%)' };

    // 💀 Culturas Macabras - Vinho tinto sinistro
    case 'Culturas Macabras':
      return { fundo: '#831843', borda: '#701A3A', gradient: 'linear-gradient(135deg, #BE185D 0%, #831843 50%, #701A3A 100%)' };

    // 👑 Reis Perversos - Roxo imperial profundo
    case 'Reis Perversos':
      return { fundo: '#581C87', borda: '#4C1D95', gradient: 'linear-gradient(135deg, #7C3AED 0%, #581C87 50%, #4C1D95 100%)' };

    // 🏛️ Antiguidade - Âmbar médio equilibrado
    case 'Antiguidade':
      return { fundo: '#D97706', borda: '#B45309', gradient: 'linear-gradient(135deg, #F59E0B 0%, #D97706 50%, #B45309 100%)' };

    // ⭐ Histórias Motivacionais - Verde lima equilibrado
    case 'Histórias Motivacionais':
    case 'Historias Motivacionais':
      return { fundo: '#65A30D', borda: '#4D7C0F', gradient: 'linear-gradient(135deg, #84CC16 0%, #65A30D 50%, #4D7C0F 100%)' };

    // 🔍 Mistérios - Índigo médio equilibrado
    case 'Mistérios':
    case 'Misterios':
      return { fundo: '#4F46E5', borda: '#3730A3', gradient: 'linear-gradient(135deg, #818CF8 0%, #4F46E5 50%, #3730A3 100%)' };

    // 🌫️ Pessoas Desaparecidas - Azul céu equilibrado
    case 'Pessoas Desaparecidas':
      return { fundo: '#0284C7', borda: '#075985', gradient: 'linear-gradient(135deg, #38BDF8 0%, #0284C7 50%, #075985 100%)' };

    // 🧠 Psicologia & Mindset - Azul profundo
    case 'Psicologia & Mindset':
    case 'Psicologia':
    case 'Mindset':
      return { fundo: '#3B82F6', borda: '#2563EB', gradient: 'linear-gradient(135deg, #60A5FA 0%, #3B82F6 50%, #2563EB 100%)' };

    // 🛡️ Guerras e Civilizações - Laranja vibrante
    case 'Guerras e Civilizações':
    case 'Guerras e Civilizacoes':
      return { fundo: '#EA580C', borda: '#C2410C', gradient: 'linear-gradient(135deg, #FB923C 0%, #EA580C 50%, #C2410C 100%)' };

    // 🕵️ Conspiração - Ciano escuro misterioso
    case 'Conspiração':
    case 'Conspiracao':
      return { fundo: '#0891B2', borda: '#0E7490', gradient: 'linear-gradient(135deg, #22D3EE 0%, #0891B2 50%, #0E7490 100%)' };

    // 💼 Empreendedorismo - Dourado/Amarelo
    case 'Empreendedorismo':
      return { fundo: '#F59E0B', borda: '#D97706', gradient: 'linear-gradient(135deg, #FBBF24 0%, #F59E0B 50%, #D97706 100%)' };

    // 💪 Mentalidade Masculina e Finanças - Azul Navy profissional
    case 'Mentalidade Masculina e Finanças':
    case 'Mentalidade Masculina e Financas':
      return { fundo: '#1E3A8A', borda: '#1E40AF', gradient: 'linear-gradient(135deg, #3B82F6 0%, #1E3A8A 50%, #1E40AF 100%)' };

    // 📰 Notícias e Atualidade - Coral vibrante
    case 'Notícias e Atualidade':
    case 'Noticias e Atualidade':
      return { fundo: '#F43F5E', borda: '#E11D48', gradient: 'linear-gradient(135deg, #FB7185 0%, #F43F5E 50%, #E11D48 100%)' };

    // 👴🏻 Lições de Vida - Azul petróleo único
    case 'Lições de Vida':
    case 'Licoes de Vida':
      return { fundo: '#0E7C93', borda: '#0A5E70', gradient: 'linear-gradient(135deg, #14B8A6 0%, #0E7C93 50%, #0A5E70 100%)' };

    // 👺 Registros Malditos - Amarelo mostarda escuro
    case 'Registros Malditos':
      return { fundo: '#CA8A04', borda: '#A16207', gradient: 'linear-gradient(135deg, #EAB308 0%, #CA8A04 50%, #A16207 100%)' };

    // ❌ Desmonetizado/Desmonetizados - Vermelho forte com gradiente
    case 'Desmonetizado':
    case 'Desmonetizados':
    case 'desmonetizado':
    case 'desmonetizados':
      return { 
        fundo: '#B91C1C', 
        borda: '#7F1D1D',
        gradient: 'linear-gradient(135deg, #EF4444 0%, #B91C1C 50%, #7F1D1D 100%)'
      };

    // 📖 Histórias Aleatórias - Rosa coral quente
    case 'Histórias Aleatórias':
    case 'Historias Aleatorias':
      return { 
        fundo: '#E879A0', 
        borda: '#DB2777',
        gradient: 'linear-gradient(135deg, #F9A8D4 0%, #E879A0 50%, #DB2777 100%)'
      };

    // 📖 Biografias - Bronze equilibrado
    case 'Biografias':
      return { fundo: '#92400E', borda: '#78350F', gradient: 'linear-gradient(135deg, #D97706 0%, #92400E 50%, #78350F 100%)' };

    // ⚔️ Frentes de Batalha - Verde escuro militar
    case 'Frentes de Batalha':
      return { fundo: '#166534', borda: '#14532D', gradient: 'linear-gradient(135deg, #22C55E 0%, #166534 50%, #14532D 100%)' };

    // ⚙️ Cor padrão (fallback para subniches não mapeados)
    default:
      return { fundo: '#6B7280', borda: '#9CA3AF', gradient: 'linear-gradient(135deg, #9CA3AF 0%, #6B7280 50%, #4B5563 100%)' };
  }
}

/**
 * Retorna a cor de fundo com opacidade para uso em backgrounds
 * @param subniche - Nome do subniche
 * @param opacity - Opacidade em hexadecimal (ex: '25' = 15%, '40' = 25%)
 */
export function obterCorSubnichoComOpacidade(
  subniche: string,
  opacity: string = '25'
): string {
  const cores = obterCorSubnicho(subniche);
  return cores.fundo + opacity;
}

/**
 * Retorna o gradiente do subnicho com opacidade translúcida
 * Adiciona sufixo hex de opacidade a cada cor #RRGGBB no gradiente
 */
export function obterGradienteTranslucido(subniche: string, opacity: string = '40'): string {
  const cores = obterCorSubnicho(subniche);
  if (cores.gradient) {
    return cores.gradient.replace(/#([0-9A-Fa-f]{6})/g, `#$1${opacity}`);
  }
  return cores.fundo + opacity;
}
