import { Component, type ReactNode } from 'react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex items-center justify-center min-h-screen px-4">
          <div className="w-full max-w-md rounded-xl border border-white/[0.1] bg-white/[0.04] backdrop-blur-xl p-8 text-center">
            <div className="h-12 w-12 rounded-xl bg-gradient-to-br from-red-600 to-red-500 flex items-center justify-center mx-auto mb-4">
              <svg viewBox="0 0 24 24" className="h-6 w-6 text-white fill-current">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z" />
              </svg>
            </div>
            <h2 className="text-lg font-bold text-foreground mb-2">Algo deu errado</h2>
            <p className="text-sm text-muted-foreground mb-6">
              {this.state.error?.message || 'Ocorreu um erro inesperado.'}
            </p>
            <button
              onClick={() => window.location.reload()}
              className="px-6 h-10 rounded-lg bg-gradient-to-r from-red-500 to-orange-400 text-white font-semibold text-sm shadow-lg shadow-red-500/30 hover:brightness-110 transition-all"
            >
              Recarregar
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
