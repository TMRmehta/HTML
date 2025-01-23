import { useState, useEffect, useCallback } from "react";

// Ensure we use localhost instead of 0.0.0.0 for CORS compatibility
const getApiBase = () => {
  const envUrl = import.meta.env.VITE_API_BASE_URL;
  if (envUrl && envUrl.includes('0.0.0.0')) {
    return envUrl.replace('0.0.0.0', 'localhost');
  }
  return envUrl || "http://localhost:8000";
};

const API_BASE = getApiBase();

interface User {
  userid: string; 
  firstname: string;
  lastname: string;
  email: string;
  user_type: "PATIENT" | "RESEARCHER";
  is_active?: boolean; 
  is_verified: boolean;
  signup_timestamp: string;
  last_login?: string;
}

interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export function useAuth() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [loginLoading, setLoginLoading] = useState(false);
  const [signupLoading, setSignupLoading] = useState(false);
  const [logoutLoading, setLogoutLoading] = useState(false);

  const getStoredTokens = () => {
    const accessToken = localStorage.getItem("access_token");
    const refreshToken = localStorage.getItem("refresh_token");
    return { accessToken, refreshToken };
  };

  const storeTokens = (tokens: AuthTokens) => {
    localStorage.setItem("access_token", tokens.access_token);
    localStorage.setItem("refresh_token", tokens.refresh_token);
  };

  const clearTokens = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
  };

  const refreshAccessToken = useCallback(async (): Promise<string | null> => {
    const { refreshToken } = getStoredTokens();
    if (!refreshToken) return null;

    try {
      const response = await fetch(`${API_BASE}/api/v1/auth/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });

      if (!response.ok) {
        clearTokens();
        return null;
      }

      const data = await response.json();
      localStorage.setItem("access_token", data.access_token);
      return data.access_token;
    } catch (error) {
      console.error("Token refresh failed:", error);
      clearTokens();
      return null;
    }
  }, []);

  const parseApiError = (errorData: any, fallbackMessage: string, status?: number): string => {
    if (!errorData) return fallbackMessage;
    if (Array.isArray(errorData.detail)) {
      const first = errorData.detail[0];
      if (first && typeof first === "object") {
        const location = Array.isArray(first.loc) ? first.loc.join(".") : first.loc;
        const msg = first.msg || first.message || fallbackMessage;
        return location ? `${msg} (${location})` : msg;
      }
      return errorData.detail.map((d: any) => d?.msg || String(d)).join("; ");
    }
    if (Array.isArray(errorData.errors)) {
      const first = errorData.errors[0];
      const msg = (first && (first.msg || first.message)) || fallbackMessage;
      return msg;
    }
    if (typeof errorData.detail === "string") {
      return errorData.detail;
    }
    if (typeof errorData.message === "string") {
      return errorData.message;
    }
    if (status) return `${fallbackMessage} (HTTP ${status})`;
    return fallbackMessage;
  };

  const getUser = useCallback(async () => {
    const { accessToken } = getStoredTokens();
    
    if (!accessToken) {
      setUser(null);
      setLoading(false);
      return;
    }

    try {
      const response = await fetch(`${API_BASE}/api/v1/auth/me`, {
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${accessToken}`,
        },
      });
      if (response.status === 401) {
        const newToken = await refreshAccessToken();
        if (newToken) {
          // Retry with new token
          const retryResponse = await fetch(`${API_BASE}/api/v1/auth/me`, {
            headers: {
              "Content-Type": "application/json",
              Authorization: `Bearer ${newToken}`,
            },
          });
          if (retryResponse.ok) {
            const data = await retryResponse.json();
            setUser(data);
            setLoading(false);
            return;
          }
        }
        // If refresh failed, clear tokens and set user to null
        clearTokens();
        setUser(null);
        setLoading(false);
        return;
      }

      if (!response.ok) {
        // Only clear tokens on authentication errors (401, 403)
        if (response.status === 401 || response.status === 403) {
          clearTokens();
          setUser(null);
        } else {
          setUser(null);
        }
        setLoading(false);
        return;
      }
      
      const data = await response.json();
      setUser(data);
    } catch (err) {
      console.error("Error fetching user:", err);
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, [refreshAccessToken]);

  const login = async (email: string, password: string) => {
    setLoginLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      
      if (!res.ok) {
        const errorData = await res.json().catch(() => undefined);
        const message = parseApiError(errorData, "Login failed", res.status);
        throw new Error(message);
      }
      
      const data = await res.json();
      storeTokens(data);
      await getUser();
      return data;
    } finally {
      setLoginLoading(false);
    }
  };

  const signUp = async (firstName: string, lastName: string, email: string, password: string, userType: "PATIENT" | "RESEARCHER" = "PATIENT") => {
    setSignupLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/auth/signup`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          firstname: firstName,
          lastname: lastName,
          email,
          password,
          user_type: userType,
        }),
      });
      
      if (!res.ok) {
        const errorData = await res.json().catch(() => undefined);
        const message = parseApiError(errorData, "Signup failed", res.status);
        throw new Error(message);
      }
      
      const userData = await res.json();
      
      return userData;
    } finally {
      setSignupLoading(false);
    }
  };

  const logout = async () => {
    setLogoutLoading(true);
    try {
      const { refreshToken } = getStoredTokens();
      
      if (refreshToken) {
        try {
          await fetch(`${API_BASE}/api/v1/auth/logout`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ refresh_token: refreshToken }),
          });
        } catch (error) {
          console.error("Logout error:", error);
        }
      }
      
      clearTokens();
      setUser(null);
    } finally {
      setLogoutLoading(false);
    }
  };

  const logoutAll = async () => {
    setLogoutLoading(true);
    try {
      const { accessToken } = getStoredTokens();
      if (accessToken) {
        await fetch(`${API_BASE}/api/v1/auth/logout-all`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${accessToken}`,
          },
        });
      }
    } catch (error) {
      console.error("Logout all error:", error);
    } finally {
      clearTokens();
      setUser(null);
      setLogoutLoading(false);
    }
  };

  const hasRole = (role: "PATIENT" | "RESEARCHER"): boolean => {
    if (!user) return false;
    
    const roleHierarchy = {
      PATIENT: 1,
      RESEARCHER: 2
    };
    
    const userLevel = roleHierarchy[user.user_type];
    const requiredLevel = roleHierarchy[role];
    
    return userLevel >= requiredLevel;
  };

  const isResearcher = () => hasRole("RESEARCHER");
  const isPatient = () => hasRole("PATIENT");

  const verifyEmail = async (token: string) => {
    const res = await fetch(`${API_BASE}/api/v1/auth/verify-email`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token }),
    });
    
    if (!res.ok) {
      const errorData = await res.json().catch(() => undefined);
      const message = parseApiError(errorData, "Email verification failed", res.status);
      throw new Error(message);
    }
    
    return res.json();
  };

  const resendVerification = async (email?: string) => {
    const emailToUse = email || user?.email;
    if (!emailToUse) {
      throw new Error("Email address is required");
    }

    const res = await fetch(`${API_BASE}/api/v1/auth/resend-verification`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: emailToUse }),
    });
    
    if (!res.ok) {
      const errorData = await res.json().catch(() => undefined);
      const message = parseApiError(errorData, "Failed to resend verification email", res.status);
      throw new Error(message);
    }
    
    return res.json();
  };

  const forgotPassword = async (email: string) => {
    const res = await fetch(`${API_BASE}/api/v1/auth/forgot-password`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email }),
    });
    
    if (!res.ok) {
      const errorData = await res.json().catch(() => undefined);
      const message = parseApiError(errorData, "Failed to send password reset email", res.status);
      throw new Error(message);
    }
    
    return res.json();
  };

  const resetPassword = async (token: string, newPassword: string) => {
    const res = await fetch(`${API_BASE}/api/v1/auth/reset-password`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token, new_password: newPassword }),
    });
    
    if (!res.ok) {
      const errorData = await res.json().catch(() => undefined);
      const message = parseApiError(errorData, "Failed to reset password", res.status);
      throw new Error(message);
    }
    
    return res.json();
  };

  useEffect(() => {
    getUser();
  }, [getUser]);

  return {
    user,
    loading,
    loginLoading,
    signupLoading,
    logoutLoading,
    isAuthenticated: !!user,
    login,
    signUp,
    logout,
    logoutAll,
    refreshUser: getUser,
    hasRole,
    isResearcher,
    isPatient,
    verifyEmail,
    resendVerification,
    forgotPassword,
    resetPassword,
  };
}
