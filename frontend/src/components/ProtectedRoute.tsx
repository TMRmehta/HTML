import { useEffect, useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { toast } from "@/hooks/use-toast";
import { useAuthContext } from "@/context/AuthContext";
import { ReactNode } from "react";
import LoginDialog from "@/components/auth/LoginDialog";
import { LoadingSpinner } from "@/components/ui/loading-spinner";

interface ProtectedRouteProps {
  children: ReactNode;
  requiredRoles?: ('PATIENT' | 'RESEARCHER')[];
  requireAll?: boolean;
}

export const ProtectedRoute = ({ 
  children, 
  requiredRoles = ['PATIENT', 'RESEARCHER'],
  requireAll = false 
}: ProtectedRouteProps) => {
  const { user, loading } = useAuthContext();
  const navigate = useNavigate();
  const location = useLocation();
  const [showLoginModal, setShowLoginModal] = useState(false);

  useEffect(() => {
    if (!loading && !user) {
      toast({
        title: "Authentication Required",
        description: "Please sign in to access this content.",
        variant: "destructive",
      });
      setShowLoginModal(true);
    }
  }, [user, loading]);

  const handleLoginSuccess = () => {
    setShowLoginModal(false);
  };

  const handleLoginCancel = () => {
    setShowLoginModal(false);
    navigate("/");
  };

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
      <>
        <LoginDialog 
          open={showLoginModal} 
          onOpenChange={setShowLoginModal}
          onLoginSuccess={handleLoginSuccess}
          onCancel={handleLoginCancel}
        />
      </>
    );
  }

  // Check role permissions
  if (requiredRoles.length > 0) {
    const hasRequiredRole = requireAll
      ? requiredRoles.every(role => user.user_type === role)
      : requiredRoles.some(role => user.user_type === role);

    if (!hasRequiredRole) {
      return (
        <div className="flex items-center justify-center min-h-screen">
          <div className="text-center">
            <h1 className="text-2xl font-bold text-gray-900 mb-4">Access Denied</h1>
            <p className="text-gray-600 mb-4">
              You don't have permission to access this page.
            </p>
            <p className="text-sm text-gray-500">
              Required role: {requiredRoles.join(' or ')}
            </p>
          </div>
        </div>
      );
    }
  }

  return <>{children}</>;
};
