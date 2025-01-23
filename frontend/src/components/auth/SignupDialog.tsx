import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { UserPlus, Heart, Microscope } from "lucide-react";
import { useAuthContext } from "@/context/AuthContext";
import { useNavigate } from "react-router-dom";
import { Alert, AlertDescription } from "@/components/ui/alert";
import EmailVerificationDialog from "./EmailVerificationDialog";

interface SignupDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSignupSuccess?: () => void;
}

const SignupDialog = ({ open, onOpenChange, onSignupSuccess }: SignupDialogProps) => {
  const [formData, setFormData] = useState({
    firstName: "",
    lastName: "",
    email: "",
    password: "",
    type: "patient" as "patient" | "researcher"
  });
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);
  const [showVerificationDialog, setShowVerificationDialog] = useState(false);
  const [userEmail, setUserEmail] = useState("");
  const { signUp, signupLoading } = useAuthContext();
  const navigate = useNavigate();

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setSuccess(false);

    try {
      await signUp(
        formData.firstName,
        formData.lastName,
        formData.email,
        formData.password,
        formData.type.toUpperCase() as "PATIENT" | "RESEARCHER"
      );
      setSuccess(true);
      setUserEmail(formData.email);
      setTimeout(() => {
        onOpenChange(false);
        if (onSignupSuccess) {
          onSignupSuccess();
        }
      }, 15000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Signup failed. Please try again.");
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <UserPlus className="h-5 w-5" />
            Join OncoSight AI
          </DialogTitle>
          <DialogDescription>
            Create your account to access our AI-powered medical platform.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
          {success && (
            <Alert className="border-green-200 bg-green-50 text-green-800">
              <AlertDescription>
                Account created successfully! Please check your email for a verification link. You'll be redirected to verify your email.
              </AlertDescription>
            </Alert>
          )}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="firstName">First Name</Label>
              <Input
                id="firstName"
                placeholder="Enter first name"
                value={formData.firstName}
                onChange={(e) => handleInputChange("firstName", e.target.value)}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="lastName">Last Name</Label>
              <Input
                id="lastName"
                placeholder="Enter last name"
                value={formData.lastName}
                onChange={(e) => handleInputChange("lastName", e.target.value)}
                required
              />
            </div>
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="email">Email Address</Label>
            <Input
              id="email"
              type="email"
              placeholder="Enter your email"
              value={formData.email}
              onChange={(e) => handleInputChange("email", e.target.value)}
              required
            />
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="password">Password</Label>
            <Input
              id="password"
              type="password"
              placeholder="Create a secure password"
              value={formData.password}
              onChange={(e) => handleInputChange("password", e.target.value)}
              required
            />
          </div>

          <div className="space-y-3">
            <Label>I am a:</Label>
            <RadioGroup
              value={formData.type}
              onValueChange={(value) => handleInputChange("type", value)}
              className="flex gap-6"
            >
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="patient" id="patient" />
                <Label htmlFor="patient" className="flex items-center gap-2 cursor-pointer">
                  <Heart className="h-4 w-4 text-primary" />
                  Patient
                </Label>
              </div>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="researcher" id="researcher" />
                <Label htmlFor="researcher" className="flex items-center gap-2 cursor-pointer">
                  <Microscope className="h-4 w-4 text-accent" />
                  Researcher
                </Label>
              </div>
            </RadioGroup>
          </div>

          <div className="flex flex-col gap-3 pt-4">
            <Button type="submit" variant="medical" className="w-full" disabled={signupLoading || success}>
              <UserPlus className="h-4 w-4" />
              {success ? "Account Created!" : signupLoading ? "Creating Account..." : "Create Account"}
            </Button>
            <p className="text-xs text-muted-foreground text-center">
              By creating an account, you agree to our Medical Disclaimers.
            </p>
          </div>
        </form>
      </DialogContent>
      
      <EmailVerificationDialog
        open={showVerificationDialog}
        onOpenChange={setShowVerificationDialog}
        onVerificationSuccess={() => {
          setShowVerificationDialog(false);
        }}
        onCancel={() => {
          setShowVerificationDialog(false);
        }}
        userEmail={userEmail}
      />
    </Dialog>
  );
};

export default SignupDialog;