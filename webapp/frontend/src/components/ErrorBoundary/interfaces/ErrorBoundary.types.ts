export interface ErrorBoundaryProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

export interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

export interface ErrorBoundaryFallbackProps {
  error: Error | null;
  onReset: () => void;
}
