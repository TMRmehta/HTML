import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuthContext } from "@/context/AuthContext";
import { LoadingSpinner } from "@/components/ui/loading-spinner";
import { toast } from "@/hooks/use-toast";

interface RoleRestrictedRouteProps {
  children: React.ReactNode;
  allowedRoles: ("PATIENT" | "RESEARCHER")[];
  fallbackRoute?: string;
}

export const RoleRestrictedRoute = ({ 
  children, 
  allowedRoles,
  fallbackRoute = "/dashboard"
}: RoleRestrictedRouteProps) => {
  const { user, loading } = useAuthContext();
  const navigate = useNavigate();

  useEffect(() => {
    if (!loading && user) {
      const userRole = user.user_type;
      
      // Check if user has permission to access this route
      if (!allowedRoles.includes(userRole)) {
        toast({
          title: "Access Denied",
          description: "You don't have permission to access this page.",
          variant: "destructive",
        });
        
        // Redirect to appropriate portal based on role
        switch (userRole) {
          case "PATIENT":
            navigate("/patients");
            break;
          case "RESEARCHER":
            navigate("/research");
            break;
          default:
            navigate(fallbackRoute);
        }
      }
    }
  }, [user, loading, navigate, allowedRoles, fallbackRoute]);

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

  if (!user) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="flex flex-col items-center gap-4">
          <LoadingSpinner size="lg" className="text-primary" />
          <p className="text-muted-foreground">Redirecting to login...</p>
        </div>
      </div>
    );
  }

  // Check if user has permission
  if (!allowedRoles.includes(user.user_type)) {
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
