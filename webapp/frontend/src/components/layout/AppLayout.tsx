import React from 'react';
import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { Activity, History, Settings, LogOut, Apple } from 'lucide-react';

export const AppLayout: React.FC = () => {
  const { user, requireAuth, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    try {
      await logout();
      navigate('/login');
    } catch (err) {
      console.error("Logout failed:", err);
    }
  };

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: 'var(--bg-primary)' }}>
      {/* Sidebar navigation */}
      <aside style={{
        width: 'var(--sidebar-width)',
        background: 'var(--bg-secondary)',
        borderRight: '1px solid var(--border-subtle)',
        display: 'flex',
        flexDirection: 'column',
        padding: '24px 16px'
      }}>
        {/* Brand Logo header */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '36px', paddingLeft: '8px' }}>
          <div style={{
            background: 'var(--gradient-primary)',
            padding: '8px',
            borderRadius: 'var(--radius-md)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: 'var(--shadow-glow)'
          }}>
            <Apple size={22} color="#fff" />
          </div>
          <div>
            <h1 style={{ fontSize: '1.15rem', fontWeight: 800, letterSpacing: '-0.025em' }}>
              Fresh<span style={{ color: 'var(--accent-cyan)' }}>Track</span>
            </h1>
            <p style={{ fontSize: '0.6875rem', color: 'var(--text-tertiary)', fontWeight: 500 }}>
              AI Freshness Monitor
            </p>
          </div>
        </div>

        {/* Navigation list */}
        <nav style={{ display: 'flex', flexDirection: 'column', gap: '6px', flex: 1 }}>
          <NavLink
            to="/"
            end
            style={({ isActive }) => ({
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              padding: '12px 16px',
              borderRadius: 'var(--radius-md)',
              fontSize: '0.9rem',
              fontWeight: 500,
              color: isActive ? 'var(--text-primary)' : 'var(--text-secondary)',
              background: isActive ? 'var(--bg-tertiary)' : 'transparent',
              border: isActive ? '1px solid var(--border-medium)' : '1px solid transparent',
              transition: 'all var(--transition-fast)'
            })}
          >
            <Activity size={18} />
            Run Predictor
          </NavLink>

          <NavLink
            to="/history"
            style={({ isActive }) => ({
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              padding: '12px 16px',
              borderRadius: 'var(--radius-md)',
              fontSize: '0.9rem',
              fontWeight: 500,
              color: isActive ? 'var(--text-primary)' : 'var(--text-secondary)',
              background: isActive ? 'var(--bg-tertiary)' : 'transparent',
              border: isActive ? '1px solid var(--border-medium)' : '1px solid transparent',
              transition: 'all var(--transition-fast)'
            })}
          >
            <History size={18} />
            Freshness Inventory
          </NavLink>

          <NavLink
            to="/settings"
            style={({ isActive }) => ({
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              padding: '12px 16px',
              borderRadius: 'var(--radius-md)',
              fontSize: '0.9rem',
              fontWeight: 500,
              color: isActive ? 'var(--text-primary)' : 'var(--text-secondary)',
              background: isActive ? 'var(--bg-tertiary)' : 'transparent',
              border: isActive ? '1px solid var(--border-medium)' : '1px solid transparent',
              transition: 'all var(--transition-fast)'
            })}
          >
            <Settings size={18} />
            Model Settings
          </NavLink>
        </nav>

        {/* User Footer Session */}
        <div style={{
          borderTop: '1px solid var(--border-subtle)',
          paddingTop: '16px',
          display: 'flex',
          flexDirection: 'column',
          gap: '12px'
        }}>
          {user && (
            <div style={{ paddingLeft: '8px' }}>
              <p style={{
                fontSize: '0.8125rem',
                fontWeight: 600,
                color: 'var(--text-primary)',
                textOverflow: 'ellipsis',
                overflow: 'hidden',
                whiteSpace: 'nowrap'
              }}>
                {user.email.split('@')[0]}
              </p>
              <p style={{ fontSize: '0.6875rem', color: 'var(--text-secondary)' }}>
                {requireAuth ? 'Secured Session' : 'Anonymous Mode'}
              </p>
            </div>
          )}

          {requireAuth && (
            <button
              onClick={handleLogout}
              className="btn btn-secondary"
              style={{
                width: '100%',
                justifyContent: 'center',
                padding: '8px 12px',
                fontSize: '0.8rem'
              }}
            >
              <LogOut size={14} />
              Logout
            </button>
          )}
        </div>
      </aside>

      {/* Main dashboard content */}
      <main style={{ flex: 1, padding: '40px', overflowY: 'auto', height: '100vh' }}>
        <Outlet />
      </main>
    </div>
  );
};
export default AppLayout;
