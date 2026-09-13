import React from "react";
import type { ErrorBoundaryFallbackProps } from "../../interfaces/ErrorBoundary.types";
import { ERROR_BOUNDARY_DEFAULTS } from "../../constants/ErrorBoundary.constants";
import "../../css/ErrorBoundary.css";

export const ErrorBoundaryFallback: React.FC<ErrorBoundaryFallbackProps> = ({
  error,
  onReset,
}) => {
  return (
    <div className="error-boundary-fallback" role="alert">
      <div className="error-boundary-card">
        <div className="error-boundary-icon" aria-hidden="true">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="8" x2="12" y2="12" />
            <line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
        </div>
        <h2 className="error-boundary-title">{ERROR_BOUNDARY_DEFAULTS.TITLE}</h2>
        <p className="error-boundary-desc">{ERROR_BOUNDARY_DEFAULTS.DESCRIPTION}</p>
        
        {error && (
          <pre className="error-boundary-details">{error.message}</pre>
        )}

        <div className="error-boundary-actions">
          <button
            type="button"
            className="error-btn-primary"
            onClick={onReset}
            aria-label="Retry loading this section"
          >
            {ERROR_BOUNDARY_DEFAULTS.RETRY_BUTTON_TEXT}
          </button>
          <button
            type="button"
            className="error-btn-secondary"
            onClick={() => window.location.assign("/")}
            aria-label="Navigate to dashboard"
          >
            {ERROR_BOUNDARY_DEFAULTS.HOME_BUTTON_TEXT}
          </button>
        </div>
      </div>
    </div>
  );
};
