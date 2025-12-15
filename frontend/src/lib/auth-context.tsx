"use client";

import { createContext, useContext, useEffect, useState, useCallback, ReactNode } from "react";
import { api } from "./api";

// Types matching backend schemas
export interface User {
  id: string;
  email: string;
  full_name: string | null;
  role: "user" | "admin";
  is_active: boolean;
  is_verified: boolean;
  avatar_url: string | null;
  created_at: string;
  updated_at: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface LoginResponse {
  user: User;
  tokens: TokenResponse;
}

export interface RegisterData {
  email: string;
  password: string;
  full_name?: string;
}

export interface LoginData {
  email: string;
  password: string;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (data: LoginData) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => Promise<void>;
  refreshToken: () => Promise<boolean>;
  clearError: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Storage keys
const ACCESS_TOKEN_KEY = "money_flow_access_token";
const REFRESH_TOKEN_KEY = "money_flow_refresh_token";
const USER_KEY = "money_flow_user";

// Helper functions for token management
function getStoredTokens() {
  if (typeof window === "undefined") return { accessToken: null, refreshToken: null };
  return {
    accessToken: localStorage.getItem(ACCESS_TOKEN_KEY),
    refreshToken: localStorage.getItem(REFRESH_TOKEN_KEY),
  };
}

function setStoredTokens(accessToken: string, refreshToken: string) {
  localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
  localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
}

function clearStoredTokens() {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

function getStoredUser(): User | null {
  if (typeof window === "undefined") return null;
  const stored = localStorage.getItem(USER_KEY);
  if (stored) {
    try {
      return JSON.parse(stored);
    } catch {
      return null;
    }
  }
  return null;
}

function setStoredUser(user: User) {
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Set up axios interceptor for auth header
  useEffect(() => {
    const requestInterceptor = api.interceptors.request.use(
      (config) => {
        const { accessToken } = getStoredTokens();
        if (accessToken) {
          config.headers.Authorization = `Bearer ${accessToken}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor for handling 401 and token refresh
    const responseInterceptor = api.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config;

        // If 401 and we haven't tried refreshing yet
        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;

          const { refreshToken } = getStoredTokens();
          if (refreshToken) {
            try {
              const response = await api.post("/auth/refresh", { refresh_token: refreshToken });
              const tokens: TokenResponse = response.data;

              setStoredTokens(tokens.access_token, tokens.refresh_token);
              originalRequest.headers.Authorization = `Bearer ${tokens.access_token}`;

              return api(originalRequest);
            } catch (refreshError) {
              // Refresh failed, clear auth state
              clearStoredTokens();
              setUser(null);
              window.location.href = "/login";
              return Promise.reject(refreshError);
            }
          }
        }

        return Promise.reject(error);
      }
    );

    return () => {
      api.interceptors.request.eject(requestInterceptor);
      api.interceptors.response.eject(responseInterceptor);
    };
  }, []);

  // Initialize auth state from storage
  useEffect(() => {
    const initAuth = async () => {
      const storedUser = getStoredUser();
      const { accessToken } = getStoredTokens();

      if (storedUser && accessToken) {
        // Verify the token is still valid by fetching current user
        try {
          const response = await api.get("/auth/me");
          setUser(response.data);
          setStoredUser(response.data);
        } catch {
          // Token invalid, try refresh
          const { refreshToken } = getStoredTokens();
          if (refreshToken) {
            try {
              const refreshResponse = await api.post("/auth/refresh", { refresh_token: refreshToken });
              const tokens: TokenResponse = refreshResponse.data;
              setStoredTokens(tokens.access_token, tokens.refresh_token);

              // Fetch user with new token
              const userResponse = await api.get("/auth/me");
              setUser(userResponse.data);
              setStoredUser(userResponse.data);
            } catch {
              clearStoredTokens();
              setUser(null);
            }
          } else {
            clearStoredTokens();
            setUser(null);
          }
        }
      }

      setIsLoading(false);
    };

    initAuth();
  }, []);

  const login = useCallback(async (data: LoginData) => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await api.post("/auth/login", data);
      const loginResponse: LoginResponse = response.data;

      setStoredTokens(loginResponse.tokens.access_token, loginResponse.tokens.refresh_token);
      setStoredUser(loginResponse.user);
      setUser(loginResponse.user);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Login failed. Please check your credentials.";
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const register = useCallback(async (data: RegisterData) => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await api.post("/auth/register", data);
      const loginResponse: LoginResponse = response.data;

      setStoredTokens(loginResponse.tokens.access_token, loginResponse.tokens.refresh_token);
      setStoredUser(loginResponse.user);
      setUser(loginResponse.user);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Registration failed. Please try again.";
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const logout = useCallback(async () => {
    setIsLoading(true);

    try {
      await api.post("/auth/logout");
    } catch {
      // Ignore logout errors - we'll clear local state anyway
    } finally {
      clearStoredTokens();
      setUser(null);
      setIsLoading(false);
    }
  }, []);

  const refreshToken = useCallback(async (): Promise<boolean> => {
    const { refreshToken: storedRefreshToken } = getStoredTokens();

    if (!storedRefreshToken) {
      return false;
    }

    try {
      const response = await api.post("/auth/refresh", { refresh_token: storedRefreshToken });
      const tokens: TokenResponse = response.data;

      setStoredTokens(tokens.access_token, tokens.refresh_token);
      return true;
    } catch {
      clearStoredTokens();
      setUser(null);
      return false;
    }
  }, []);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        error,
        login,
        register,
        logout,
        refreshToken,
        clearError,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
