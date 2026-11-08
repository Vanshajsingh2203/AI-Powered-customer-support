
import {
  createContext,
  useContext,
  useEffect,
  useRef,
  useState,
} from 'react';

import {
  loginUser,
  registerUser,
  logoutUser,
  refreshTokens,
} from '../api/auth';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const storedUser = sessionStorage.getItem('user');

    try {
      return storedUser ? JSON.parse(storedUser) : null;
    } catch {
      return null;
    }
  });

  const [loading, setLoading] = useState(true);

  // Prevent duplicate session restoration in React StrictMode.
  const restoreStarted = useRef(false);

  const clearSession = () => {
    sessionStorage.removeItem('access_token');
    sessionStorage.removeItem('refresh_token');
    sessionStorage.removeItem('user');

    setUser(null);
  };

  // Restore the authentication session when the app starts.
  useEffect(() => {
    const handleSessionExpired = () => {
      clearSession();
    };

    window.addEventListener(
      'auth:session-expired',
      handleSessionExpired
    );

    if (restoreStarted.current) {
      return () => {
        window.removeEventListener(
          'auth:session-expired',
          handleSessionExpired
        );
      };
    }

    restoreStarted.current = true;

    const restoreSession = async () => {
      const accessToken = sessionStorage.getItem('access_token');
      const refreshToken = sessionStorage.getItem('refresh_token');
      const storedUser = sessionStorage.getItem('user');

      if (!accessToken || !refreshToken || !storedUser) {
        clearSession();
        setLoading(false);
        return;
      }

      try {
        const data = await refreshTokens(refreshToken);

        sessionStorage.setItem('access_token', data.access_token);
        sessionStorage.setItem('refresh_token', data.refresh_token);
      } catch (error) {
        console.error('Session restoration failed:', error);
        clearSession();
      } finally {
        setLoading(false);
      }
    };

    restoreSession();

    return () => {
      window.removeEventListener(
        'auth:session-expired',
        handleSessionExpired
      );
    };
  }, []);

  // Log in an existing user.
  const login = async (credentials) => {
    const data = await loginUser(credentials);

    sessionStorage.setItem('access_token', data.access_token);
    sessionStorage.setItem('refresh_token', data.refresh_token);
    sessionStorage.setItem('user', JSON.stringify(data.user));

    setUser(data.user);

    return data.user;
  };

  // Register a new customer.
  const register = async (userData) => {
    return await registerUser(userData);
  };

  // Log out the current user.
  const logout = async () => {
    const refreshToken = sessionStorage.getItem('refresh_token');

    try {
      if (refreshToken) {
        await logoutUser(refreshToken);
      }
    } catch (error) {
      console.error('Logout API request failed:', error);
    } finally {
      clearSession();
    }
  };

  const isAuthenticated = Boolean(
    user && sessionStorage.getItem('access_token')
  );

  const value = {
    user,
    loading,
    isAuthenticated,
    login,
    register,
    logout,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

// Custom hook for accessing authentication functionality.
export function useAuth() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error('useAuth must be used inside AuthProvider');
  }

  return context;
}
