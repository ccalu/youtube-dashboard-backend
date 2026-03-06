import { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { useToast } from '@/hooks/use-toast';
import { getRememberedUser, setRememberedUser, clearRememberedUser } from '@/lib/authFetch';

// Floating particles background
function Particles() {
  const particles = useMemo(() =>
    Array.from({ length: 20 }, (_, i) => ({
      id: i,
      x: Math.random() * 100,
      y: Math.random() * 100,
      size: Math.random() * 3 + 1,
      duration: Math.random() * 15 + 10,
      delay: Math.random() * -20,
      opacity: Math.random() * 0.3 + 0.1,
    })), []);

  return (
    <div className="fixed inset-0 overflow-hidden pointer-events-none">
      {particles.map((p) => (
        <div
          key={p.id}
          className="absolute rounded-full"
          style={{
            left: `${p.x}%`,
            top: `${p.y}%`,
            width: `${p.size}px`,
            height: `${p.size}px`,
            background: p.id % 3 === 0
              ? 'rgba(239, 68, 68, 0.4)'
              : p.id % 3 === 1
              ? 'rgba(249, 115, 22, 0.3)'
              : 'rgba(255, 255, 255, 0.15)',
            opacity: p.opacity,
            animation: `login-float ${p.duration}s ease-in-out ${p.delay}s infinite`,
          }}
        />
      ))}
    </div>
  );
}

export default function LoginPage() {
  const { login, isAuthenticated, isLoading } = useAuth();
  const navigate = useNavigate();
  const { toast } = useToast();

  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [remember, setRemember] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    const saved = getRememberedUser();
    if (saved) {
      setUsername(saved);
      setRemember(true);
    }
    // Trigger mount animation
    requestAnimationFrame(() => setMounted(true));
  }, []);

  useEffect(() => {
    if (isAuthenticated && !isLoading) {
      navigate('/', { replace: true });
    }
  }, [isAuthenticated, isLoading, navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username.trim() || !password.trim()) return;

    setSubmitting(true);
    try {
      await login(username.trim(), password);
      if (remember) {
        setRememberedUser(username.trim());
      } else {
        clearRememberedUser();
      }
      navigate('/', { replace: true });
    } catch (err) {
      toast({
        title: 'Erro no login',
        description: err instanceof Error ? err.message : 'Credenciais invalidas',
        variant: 'destructive',
      });
    } finally {
      setSubmitting(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-red-500 border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="flex items-center justify-center min-h-screen px-4 relative">
      {/* Animated particles */}
      <Particles />

      {/* Login animation styles */}
      <style>{`
        @keyframes login-float {
          0%, 100% { transform: translateY(0px) translateX(0px); }
          25% { transform: translateY(-20px) translateX(10px); }
          50% { transform: translateY(-10px) translateX(-10px); }
          75% { transform: translateY(-30px) translateX(5px); }
        }
        @keyframes login-glow {
          0%, 100% { box-shadow: 0 4px 24px -4px rgba(0,0,0,0.4), 0 0 0 1px rgba(255,255,255,0.05), 0 0 30px -10px rgba(239,68,68,0.0); }
          50% { box-shadow: 0 4px 24px -4px rgba(0,0,0,0.4), 0 0 0 1px rgba(239,68,68,0.15), 0 0 40px -10px rgba(239,68,68,0.15); }
        }
        @keyframes login-shimmer {
          0% { transform: translateX(-100%); }
          100% { transform: translateX(100%); }
        }
        @keyframes login-logo-pulse {
          0%, 100% { box-shadow: 0 10px 15px -3px rgba(239,68,68,0.2); }
          50% { box-shadow: 0 10px 25px -3px rgba(239,68,68,0.4); }
        }
      `}</style>

      <div
        className={`w-full max-w-sm transition-all duration-700 ease-out ${
          mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'
        }`}
      >
        {/* Glass card with glow pulse */}
        <div
          className="rounded-xl border border-white/[0.1] bg-white/[0.04] backdrop-blur-xl p-8 relative overflow-hidden"
          style={{ animation: 'login-glow 4s ease-in-out infinite' }}
        >
          {/* Logo + Title */}
          <div className="flex flex-col items-center mb-8">
            <div
              className={`h-12 w-12 rounded-xl bg-gradient-to-br from-red-600 to-red-500 flex items-center justify-center mb-4 transition-all duration-700 delay-200 ${
                mounted ? 'opacity-100 scale-100' : 'opacity-0 scale-50'
              }`}
              style={{ animation: 'login-logo-pulse 3s ease-in-out infinite' }}
            >
              <svg viewBox="0 0 24 24" className="h-6 w-6 text-white fill-current">
                <path d="M10 15l5.19-3L10 9v6m11.56-7.83c.13.47.22 1.1.28 1.9.07.8.1 1.49.1 2.09L22 12c0 2.19-.16 3.8-.44 4.83-.25.9-.83 1.48-1.73 1.73-.47.13-1.33.22-2.65.28-1.3.07-2.49.1-3.59.1L12 19c-4.19 0-6.8-.16-7.83-.44-.9-.25-1.48-.83-1.73-1.73-.13-.47-.22-1.1-.28-1.9-.07-.8-.1-1.49-.1-2.09L2 12c0-2.19.16-3.8.44-4.83.25-.9.83-1.48 1.73-1.73.47-.13 1.33-.22 2.65-.28 1.3-.07 2.49-.1 3.59-.1L12 5c4.19 0 6.8.16 7.83.44.9.25 1.48.83 1.73 1.73z"/>
              </svg>
            </div>
            <h1
              className={`text-xl font-bold bg-gradient-to-r from-red-400 via-red-500 to-orange-400 bg-clip-text text-transparent transition-all duration-700 delay-300 ${
                mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
              }`}
            >
              YouTube Dashboard
            </h1>
            <p
              className={`text-sm text-muted-foreground mt-1 transition-all duration-700 delay-400 ${
                mounted ? 'opacity-100' : 'opacity-0'
              }`}
            >
              Faca login para continuar
            </p>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4" autoComplete="on">
            <div
              className={`transition-all duration-500 delay-[450ms] ${
                mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
              }`}
            >
              <label htmlFor="username" className="block text-sm font-medium text-muted-foreground mb-1.5">
                Username
              </label>
              <input
                id="username"
                name="username"
                type="text"
                autoComplete="username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Digite aqui..."
                className="w-full h-10 px-3 rounded-lg border border-white/[0.1] bg-white/[0.04] text-foreground placeholder:text-muted-foreground/50 focus:outline-none focus:ring-2 focus:ring-red-500/50 focus:border-red-500/50 transition-all"
                disabled={submitting}
              />
            </div>

            <div
              className={`transition-all duration-500 delay-[550ms] ${
                mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
              }`}
            >
              <label htmlFor="password" className="block text-sm font-medium text-muted-foreground mb-1.5">
                Senha
              </label>
              <input
                id="password"
                name="password"
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••"
                className="w-full h-10 px-3 rounded-lg border border-white/[0.1] bg-white/[0.04] text-foreground placeholder:text-muted-foreground/50 focus:outline-none focus:ring-2 focus:ring-red-500/50 focus:border-red-500/50 transition-all"
                disabled={submitting}
              />
            </div>

            {/* Remember me */}
            <label
              className={`flex items-center gap-2 cursor-pointer select-none transition-all duration-500 delay-[650ms] ${
                mounted ? 'opacity-100' : 'opacity-0'
              }`}
            >
              <input
                type="checkbox"
                checked={remember}
                onChange={(e) => setRemember(e.target.checked)}
                className="h-4 w-4 rounded-full border-white/20 bg-white/[0.04] text-red-500 accent-red-500 focus:ring-red-500/50 focus:ring-offset-0"
              />
              <span className="text-sm text-muted-foreground">Lembrar usuario</span>
            </label>

            <div
              className={`transition-all duration-500 delay-[750ms] ${
                mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
              }`}
            >
              <button
                type="submit"
                disabled={submitting || !username.trim() || !password.trim()}
                className="w-full h-10 rounded-lg bg-gradient-to-r from-red-600 to-orange-500 text-white font-medium text-sm shadow-md shadow-red-500/20 hover:shadow-lg hover:shadow-red-500/30 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed relative overflow-hidden"
              >
                {/* Shimmer effect */}
                {!submitting && (
                  <span
                    className="absolute inset-0 pointer-events-none"
                    style={{
                      background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent)',
                      animation: 'login-shimmer 3s ease-in-out infinite',
                    }}
                  />
                )}
                {submitting ? (
                  <span className="flex items-center justify-center gap-2 relative z-10">
                    <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                    Entrando...
                  </span>
                ) : (
                  <span className="relative z-10">Entrar</span>
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
