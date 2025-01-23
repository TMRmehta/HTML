import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { HashRouter, Routes, Route } from "react-router-dom";
import Index from "./pages/Index";
import Dashboard from "./pages/Dashboard";
import PatientPortal from "./pages/PatientPortal";
import ResearchPortal from "./pages/ResearchPortal";
import ChatPage from "./pages/ChatPage";
import About from "./pages/About";
import EmailVerification from "./pages/EmailVerification";
import ResetPassword from "./pages/ResetPassword";
import NotFound from "./pages/NotFound";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { RoleBasedRedirect } from "./components/RoleBasedRedirect";
import { RoleRestrictedRoute } from "./components/RoleRestrictedRoute";
import UnauthenticatedRoute from "./components/UnauthenticatedRoute";
import { AuthProvider } from "./context/AuthContext";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <HashRouter>
      <AuthProvider>
        <Routes>
          <Route path="/" element={
            <RoleBasedRedirect>
              <Index />
            </RoleBasedRedirect>
          } />
          <Route path="/dashboard" element={
            <ProtectedRoute>
              <RoleRestrictedRoute allowedRoles={["PATIENT", "RESEARCHER"]}>
                <Dashboard />
              </RoleRestrictedRoute>
            </ProtectedRoute>
          } />
          <Route path="/patients" element={
            <ProtectedRoute requiredRoles={["PATIENT"]}>
              <RoleRestrictedRoute allowedRoles={["PATIENT"]}>
                <PatientPortal />
              </RoleRestrictedRoute>
            </ProtectedRoute>
          } />
          <Route path="/research" element={
            <ProtectedRoute>
              <RoleRestrictedRoute allowedRoles={["RESEARCHER"]}>
                <ResearchPortal />
              </RoleRestrictedRoute>
            </ProtectedRoute>
          } />
          <Route path="/chat/patient" element={
            <ProtectedRoute requiredRoles={["PATIENT"]}>
              <RoleRestrictedRoute allowedRoles={["PATIENT"]}>
                <ChatPage />
              </RoleRestrictedRoute>
            </ProtectedRoute>
          } />
          <Route path="/chat/research" element={
            <ProtectedRoute requiredRoles={["RESEARCHER"]}>
              <RoleRestrictedRoute allowedRoles={["RESEARCHER"]}>
                <ChatPage />
              </RoleRestrictedRoute>
            </ProtectedRoute>
          } />
          <Route path="/about" element={<About />} />
          <Route path="/verify-email" element={
            <UnauthenticatedRoute>
              <EmailVerification />
            </UnauthenticatedRoute>
          } />
          <Route path="/reset-password" element={
            <UnauthenticatedRoute>
              <ResetPassword />
            </UnauthenticatedRoute>
          } />
          <Route path="*" element={<NotFound />} />
        </Routes>
        </AuthProvider>
      </HashRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
