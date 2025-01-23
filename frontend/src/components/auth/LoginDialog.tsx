import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { LogIn } from "lucide-react";
import { useAuthContext } from "@/context/AuthContext";
import { useNavigate } from "react-router-dom";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Mail, RefreshCw, Lock } from "lucide-react";
import ForgotPasswordDialog from "./ForgotPasswordDialog";

interface LoginDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onLoginSuccess?: () => void;
  onCancel?: () => void;
}

const LoginDialog = ({ open, onOpenChange, onLoginSuccess, onCancel }: LoginDialogProps) => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isEmailNotVerified, setIsEmailNotVerified] = useState(false);
  const [isResending, setIsResending] = useState(false);
  const [resendMessage, setResendMessage] = useState("");
  const [showForgotPassword, setShowForgotPassword] = useState(false);
  const { login, loginLoading, resendVerification } = useAuthContext();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setIsEmailNotVerified(false);
    setResendMessage("");

    try {
      await login(email, password);
      onOpenChange(false);
      if (onLoginSuccess) {
        onLoginSuccess();
      } else {
        navigate("/dashboard");
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Login failed. Please try again.";
      setError(errorMessage);
      
      if (errorMessage.includes("verify your email")) {
        setIsEmailNotVerified(true);
      }
    }
  };

  const handleResendVerification = async () => {
    if (!email) {
      setError("Please enter your email address first");
      return;
    }

    setIsResending(true);
    setResendMessage("");
    setError("");

    try {
      const result = await resendVerification(email);
      if (result.sent) {
        setResendMessage("Verification email sent! Please check your inbox.");
        setIsEmailNotVerified(false);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to resend verification email");
    } finally {
      setIsResending(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <LogIn className="h-5 w-5" />
            Sign In to OncoSight AI
          </DialogTitle>
          <DialogDescription>
            Access your account to continue with medical research and patient support.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
          <div className="space-y-2">
            <Label htmlFor="email">Email Address</Label>
            <Input
              id="email"
              type="email"
              placeholder="Enter your email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="password">Password</Label>
            <Input
              id="password"
              type="password"
              placeholder="Enter your password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          <div className="flex flex-col gap-3 pt-4">
            <Button type="submit" variant="medical" className="w-full" disabled={loginLoading}>
              <LogIn className="h-4 w-4" />
              {loginLoading ? "Signing In..." : "Sign In"}
            </Button>
            <div className="flex gap-2">
              <Button
                type="button"
                variant="outline"
                className="flex-1"
                onClick={() => {
                  if (onCancel) {
                    onCancel();
                  } else {
                    onOpenChange(false);
                  }
                }}
              >
                Cancel
              </Button>
              <Button
                type="button"
                variant="ghost"
                className="flex-1 text-sm text-muted-foreground"
                onClick={() => setShowForgotPassword(true)}
              >
                <Lock className="h-3 w-3 mr-1" />
                Forgot password?
              </Button>
            </div>
          </div>
        </form>
      </DialogContent>
      
      <ForgotPasswordDialog
        open={showForgotPassword}
        onOpenChange={setShowForgotPassword}
        onBackToLogin={() => setShowForgotPassword(false)}
      />
    </Dialog>
  );
};

export default LoginDialog;