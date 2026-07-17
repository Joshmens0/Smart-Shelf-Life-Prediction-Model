import React, { lazy, Suspense } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import AppLayout from './components/layout/AppLayout';

// Lazy loading views for compilation bundling optimizations
const PredictPage = lazy(() => import('./pages/predict/PredictPage'));
const HistoryPage = lazy(() => import('./pages/history/HistoryPage'));
const SettingsPage = lazy(() => import('./pages/settings/SettingsPage'));
const LoginPage = lazy(() => import('./pages/auth/LoginPage'));

interface RouteProps {
  children: React.ReactNode;
}

const ProtectedRoute: React.FC<RouteProps> = ({ children }) => {
  const { user, loading, requireAuth } = useAuth();

  if (loading) {
    return (
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        height: '100vh', color: 'var(--text-secondary)', background: 'var(--bg-primary)'
      }}>
        Verifying Session...
      </div>
    );
  }

  // If authentication is required but user is unauthenticated, redirect to login
  if (requireAuth && !user) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};

const PublicRoute: React.FC<RouteProps> = ({ children }) => {
  const { user, loading, requireAuth } = useAuth();

  if (loading) return null;

  // If authenticated, redirect to home predictor
  if (requireAuth && user) {
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
};

const AppRoutes: React.FC = () => {
  return (
    <Suspense fallback={
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        height: '100vh', color: 'var(--text-secondary)', background: 'var(--bg-primary)'
      }}>
        Loading Page View...
      </div>
    }>
      <Routes>
        {/* Public authentication page */}
        <Route path="/login" element={<PublicRoute><LoginPage /></PublicRoute>} />

        {/* Layout wrapper routes */}
        <Route element={<ProtectedRoute><AppLayout /></ProtectedRoute>}>
          <Route path="/" element={<PredictPage />} />
          <Route path="/history" element={<HistoryPage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Route>

        {/* Navigation Fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Suspense>
  );
};

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  );
};
export default App;
