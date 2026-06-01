import { Component } from 'react';
import type { ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';

type ErrorLevel = 'app' | 'page' | 'section';

interface ErrorBoundaryProps {
  level: ErrorLevel;
  children: ReactNode;
  fallback?: (error: Error, reset: () => void) => ReactNode;
  onError?: (error: Error, info: ErrorInfo) => void;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  state: ErrorBoundaryState = { hasError: false, error: null };

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    this.props.onError?.(error, info);
    // Production projects can hook Sentry etc. here
    // eslint-disable-next-line no-console
    console.error('[ErrorBoundary]', this.props.level, error, info);
  }

  reset = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (!this.state.hasError) return this.props.children;

    const error = this.state.error!;
    const reset = this.reset;

    if (this.props.fallback) return this.props.fallback(error, reset);

    if (this.props.level === 'section') {
      return (
        <div className="flex items-center justify-center gap-3 p-6 rounded-lg border border-[var(--danger-soft)] bg-[var(--danger-soft)]/30 text-sm">
          <AlertTriangle className="w-4 h-4 text-[var(--danger)]" />
          <span className="text-[var(--text-muted)]">加载失败</span>
          <Button variant="ghost" size="sm" onClick={reset}>
            <RefreshCw className="w-3 h-3 mr-1" />
            重试
          </Button>
        </div>
      );
    }

    if (this.props.level === 'page') {
      return (
        <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4">
          <div className="w-16 h-16 rounded-full bg-[var(--danger-soft)] flex items-center justify-center">
            <AlertTriangle className="w-8 h-8 text-[var(--danger)]" />
          </div>
          <h2 className="text-xl font-semibold text-[var(--text)]">页面出错了</h2>
          <p className="text-sm text-[var(--text-muted)] max-w-md text-center">
            {error.message || '发生未知错误，请刷新页面重试。'}
          </p>
          <Button onClick={() => window.location.reload()}>
            <RefreshCw className="w-4 h-4 mr-2" />
            刷新页面
          </Button>
        </div>
      );
    }

    // app level
    return (
      <div className="flex items-center justify-center min-h-screen p-4">
        <div className="text-center">
          <h1 className="text-lg font-semibold mb-2">应用出错，请刷新</h1>
          <p className="text-xs text-[var(--text-muted)]">错误 ID: {Date.now()}</p>
        </div>
      </div>
    );
  }
}

// Convenience exports
export const AppErrorBoundary = (p: Omit<ErrorBoundaryProps, 'level'>) => <ErrorBoundary level="app" {...p} />;
export const PageErrorBoundary = (p: Omit<ErrorBoundaryProps, 'level'>) => <ErrorBoundary level="page" {...p} />;
export const SectionErrorBoundary = (p: Omit<ErrorBoundaryProps, 'level'>) => <ErrorBoundary level="section" {...p} />;
