import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { useToast } from '@/hooks/use-toast';
import { getRememberedUser, setRememberedUser, clearRememberedUser } from '@/lib/authFetch';

export default function LoginPage() {
  const { login, isAuthenticated, isLoading } = useAuth();
  const navigate = useNavigate();
  const { toast } = useToast();

  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [remember, setRemember] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    const saved = getRememberedUser();
    if (saved) {
      setUsername(saved);
      setRemember(true);
    }
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
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-purple-500 border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="flex items-center justify-center min-h-screen px-4">
      <div className="w-full max-w-sm">
        {/* Glass card */}
        <div className="rounded-xl border border-white/[0.1] bg-white/[0.04] backdrop-blur-xl p-8 shadow-[0_4px_24px_-4px_rgba(0,0,0,0.4),0_0_0_1px_rgba(255,255,255,0.05)]">
          {/* Logo + Title */}
          <div className="flex flex-col items-center mb-8">
            <div className="h-12 w-12 rounded-xl bg-gradient-to-br from-red-600 to-red-500 flex items-center justify-center shadow-lg shadow-red-500/20 mb-4">
              <svg viewBox="0 0 24 24" className="h-6 w-6 text-white fill-current">
                <path d="M10 15l5.19-3L10 9v6m11.56-7.83c.13.47.22 1.1.28 1.9.07.8.1 1.49.1 2.09L22 12c0 2.19-.16 3.8-.44 4.83-.25.9-.83 1.48-1.73 1.73-.47.13-1.33.22-2.65.28-1.3.07-2.49.1-3.59.1L12 19c-4.19 0-6.8-.16-7.83-.44-.9-.25-1.48-.83-1.73-1.73-.13-.47-.22-1.1-.28-1.9-.07-.8-.1-1.49-.1-2.09L2 12c0-2.19.16-3.8.44-4.83.25-.9.83-1.48 1.73-1.73.47-.13 1.33-.22 2.65-.28 1.3-.07 2.49-.1 3.59-.1L12 5c4.19 0 6.8.16 7.83.44.9.25 1.48.83 1.73 1.73z"/>
              </svg>
            </div>
            <h1 className="text-xl font-bold bg-gradient-to-r from-red-400 via-red-500 to-orange-400 bg-clip-text text-transparent">
              YouTube Dashboard
            </h1>
            <p className="text-sm text-muted-foreground mt-1">Faca login para continuar</p>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4" autoComplete="on">
            <div>
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
                placeholder="cellibs"
                className="w-full h-10 px-3 rounded-lg border border-white/[0.1] bg-white/[0.04] text-foreground placeholder:text-muted-foreground/50 focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500/50 transition-all"
                disabled={submitting}
              />
            </div>

            <div>
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
                className="w-full h-10 px-3 rounded-lg border border-white/[0.1] bg-white/[0.04] text-foreground placeholder:text-muted-foreground/50 focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500/50 transition-all"
                disabled={submitting}
              />
            </div>

            {/* Remember me */}
            <label className="flex items-center gap-2 cursor-pointer select-none">
              <input
                type="checkbox"
                checked={remember}
                onChange={(e) => setRemember(e.target.checked)}
                className="h-4 w-4 rounded border-white/20 bg-white/[0.04] text-purple-500 focus:ring-purple-500/50 focus:ring-offset-0"
              />
              <span className="text-sm text-muted-foreground">Lembrar usuario</span>
            </label>

            <button
              type="submit"
              disabled={submitting || !username.trim() || !password.trim()}
              className="w-full h-10 rounded-lg bg-gradient-to-r from-purple-600 to-violet-500 text-white font-medium text-sm shadow-md shadow-purple-500/20 hover:shadow-lg hover:shadow-purple-500/30 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {submitting ? (
                <span className="flex items-center justify-center gap-2">
                  <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                  Entrando...
                </span>
              ) : (
                'Entrar'
              )}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
