import React, { createContext, useContext, useState, useEffect } from 'react';

export interface User {
  id: string;
  email: string;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  requireAuth: boolean;
  login: (email: string, pass: string) => Promise<void>;
  logout: () => Promise<void>;
  register: (email: string, pass: string) => Promise<void>;
}

const AuthContext = createContext<AuthContextType | null>(null);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [requireAuth, setRequireAuth] = useState(false);

  useEffect(() => {
    async function checkAuthStatus() {
      try {
        // Fetch config parameters: checks if authentication is toggled active
        const configRes = await fetch('/api/auth/config');
        if (!configRes.ok) {
          throw new Error("Failed to load backend config parameters");
        }
        
        const config = await configRes.json();
        setRequireAuth(config.require_auth);

        if (config.require_auth) {
          // Verify cookie session
          const userRes = await fetch('/api/auth/me');
          if (userRes.ok) {
            const userData = await userRes.json();
            setUser(userData);
          } else {
            setUser(null);
          }
        } else {
          // Bypassed, load a mock user
          setUser({ id: 'anonymous', email: 'anonymous@shelf-life.internal' });
        }
      } catch (err) {
        console.error("Auth initialization failed:", err);
      } finally {
        setLoading(false);
      }
    }
    
    checkAuthStatus();
  }, []);

  const login = async (email: string, pass: string) => {
    const res = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password: pass })
    });
    
    if (!res.ok) {
      const errData = await res.json();
      throw new Error(errData.error?.message || "Invalid credentials");
    }
    
    const data = await res.json();
    setUser({ id: data.user_id, email: data.email });
  };

  const logout = async () => {
    await fetch('/api/auth/logout', { method: 'POST' });
    setUser(null);
  };

  const register = async (email: string, pass: string) => {
    const res = await fetch('/api/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password: pass })
    });
    
    if (!res.ok) {
      const errData = await res.json();
      throw new Error(errData.error?.message || "Registration failed");
    }
  };

  return (
    <AuthContext.Provider value={{ user, loading, requireAuth, login, logout, register }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be wrapped within an AuthProvider");
  }
  return context;
};
export default AuthContext;
