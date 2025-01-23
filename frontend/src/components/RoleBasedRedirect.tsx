import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuthContext } from "@/context/AuthContext";
import { LoadingSpinner } from "@/components/ui/loading-spinner";

interface RoleBasedRedirectProps {
  children: React.ReactNode;
  allowedRoles?: ("PATIENT" | "RESEARCHER")[];
  redirectTo?: string;
}

export const RoleBasedRedirect = ({ 
  children, 
  allowedRoles = ["PATIENT", "RESEARCHER"],
  redirectTo 
}: RoleBasedRedirectProps) => {
  const { user, loading } = useAuthContext();
  const navigate = useNavigate();

  useEffect(() => {
    if (!loading && user) {
      const userRole = user.user_type;
      
      if (redirectTo) {
        navigate(redirectTo);
      } else {
        switch (userRole) {
          case "PATIENT":
            navigate("/patients");
            break;
          case "RESEARCHER":
            navigate("/research");
            break;
          default:
            navigate("/dashboard");
        }
      }
    }
  }, [user, loading, navigate, redirectTo]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="flex flex-col items-center gap-4">
          <LoadingSpinner size="lg" className="text-primary" />
          <p className="text-muted-foreground">Loading...</p>
        </div>
      </div>
    );
  }

  if (user) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="flex flex-col items-center gap-4">
          <LoadingSpinner size="lg" className="text-primary" />
          <p className="text-muted-foreground">Redirecting to your portal...</p>
        </div>
      </div>
    );
  }

  return <>{children}</>;
};
