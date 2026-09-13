import React, { Component, type ErrorInfo } from "react";
import type { ErrorBoundaryProps, ErrorBoundaryState } from "../interfaces/ErrorBoundary.types";
import { ErrorBoundaryFallback } from "./sections/ErrorBoundaryFallback";

/**
 * Universal React Error Boundary Component per Universal App Template Section 4.7.
 * Catches JavaScript errors anywhere in their child component tree and logs them.
 */
export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    console.error("ErrorBoundary caught an unhandled error:", error, errorInfo);
  }

  handleReset = (): void => {
    this.setState({ hasError: false, error: null });
  };

  render(): React.ReactNode {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }
      return (
        <ErrorBoundaryFallback
          error={this.state.error}
          onReset={this.handleReset}
        />
      );
    }
    return this.props.children;
  }
}

export default ErrorBoundary;
