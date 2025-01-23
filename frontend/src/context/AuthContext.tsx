import { createContext, useContext } from "react";
import { useAuth } from "@/hooks/useAuth";

type AuthContextType = ReturnType<typeof useAuth> | null;

const AuthContext = createContext<AuthContextType>(null);

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const auth = useAuth(); 
  return (
    <AuthContext.Provider value={auth}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuthContext = () => useContext(AuthContext);
