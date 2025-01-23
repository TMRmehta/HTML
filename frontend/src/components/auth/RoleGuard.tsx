import React from 'react';
import { useAuthContext } from '@/context/AuthContext';

interface RoleGuardProps {
  children: React.ReactNode;
  requiredRoles: ('PATIENT' | 'RESEARCHER')[];
  fallback?: React.ReactNode;
  requireAll?: boolean; 
}

export const RoleGuard: React.FC<RoleGuardProps> = ({
  children,
  requiredRoles,
  fallback = null,
  requireAll = false
}) => {
  const { user, isAuthenticated } = useAuthContext();

  if (!isAuthenticated || !user) {
    return <>{fallback}</>;
  }

  const hasRequiredRole = requireAll
    ? requiredRoles.every(role => user.user_type === role)
    : requiredRoles.some(role => user.user_type === role);

  if (!hasRequiredRole) {
    return <>{fallback}</>;
  }

  return <>{children}</>;
};

// Convenience components for common role checks
export const ResearcherOnly: React.FC<{ children: React.ReactNode; fallback?: React.ReactNode }> = ({
  children,
  fallback = null
}) => (
  <RoleGuard requiredRoles={['RESEARCHER']} fallback={fallback}>
    {children}
  </RoleGuard>
);

export const PatientOnly: React.FC<{ children: React.ReactNode; fallback?: React.ReactNode }> = ({
  children,
  fallback = null
}) => (
  <RoleGuard requiredRoles={['PATIENT']} fallback={fallback}>
    {children}
  </RoleGuard>
);

export const AuthenticatedOnly: React.FC<{ children: React.ReactNode; fallback?: React.ReactNode }> = ({
  children,
  fallback = null
}) => (
  <RoleGuard requiredRoles={['PATIENT', 'RESEARCHER']} fallback={fallback}>
    {children}
  </RoleGuard>
);
