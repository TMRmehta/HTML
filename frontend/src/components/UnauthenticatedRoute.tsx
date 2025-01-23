import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuthContext } from '@/context/AuthContext';
import { LoadingSpinner } from './ui/loading-spinner';

interface UnauthenticatedRouteProps {
  children: React.ReactNode;
  redirectTo?: string;
}

const UnauthenticatedRoute: React.FC<UnauthenticatedRouteProps> = ({ 
  children, 
  redirectTo = '/dashboard' 
}) => {
  const { user, loading } = useAuthContext();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner />
      </div>
    );
  }

  if (user) {
    return <Navigate to={redirectTo} replace />;
  }

  return <>{children}</>;
};

export default UnauthenticatedRoute;
