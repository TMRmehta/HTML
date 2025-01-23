import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { CheckCircle, XCircle, Mail, RefreshCw, ArrowLeft } from "lucide-react";
import { useAuthContext } from "@/context/AuthContext";

interface EmailVerificationDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onVerificationSuccess?: () => void;
  onCancel?: () => void;
  userEmail?: string;
}

const EmailVerificationDialog = ({ 
  open, 
  onOpenChange, 
  onVerificationSuccess, 
  onCancel,
  userEmail 
}: EmailVerificationDialogProps) => {
  const [verificationStatus, setVerificationStatus] = useState<'idle' | 'verifying' | 'success' | 'error'>('idle');
  const [error, setError] = useState('');
  const [isResending, setIsResending] = useState(false);
  const [resendMessage, setResendMessage] = useState('');
  const { verifyEmail, resendVerification, login } = useAuthContext();

  const handleVerification = async (token: string) => {
    setVerificationStatus('verifying');
    setError('');

    try {
      const result = await verifyEmail(token);
      if (result.verified) {
        setVerificationStatus('success');
        if (userEmail) {
          try {
            setTimeout(() => {
              if (onVerificationSuccess) {
                onVerificationSuccess();
              }
            }, 2000);
          } catch (err) {
            console.error("Auto-login failed:", err);
          }
        }
      } else {
        setVerificationStatus('error');
        setError('Email verification failed');
      }
    } catch (err) {
      setVerificationStatus('error');
      setError(err instanceof Error ? err.message : 'Verification failed');
    }
  };

  const handleResendVerification = async () => {
    if (!userEmail) {
      setError("Email address is required");
      return;
    }

    setIsResending(true);
    setResendMessage('');
    setError('');

    try {
      const result = await resendVerification(userEmail);
      if (result.sent) {
        setResendMessage('Verification email sent! Please check your inbox.');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to resend verification email');
    } finally {
      setIsResending(false);
    }
  };

  const handleCancel = () => {
    setVerificationStatus('idle');
    setError('');
    setResendMessage('');
    onOpenChange(false);
    if (onCancel) {
      onCancel();
    }
  };

  const renderContent = () => {
    switch (verificationStatus) {
      case 'verifying':
        return (
          <div className="text-center space-y-4">
            <div className="mx-auto w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center">
              <RefreshCw className="h-8 w-8 text-blue-600 animate-spin" />
            </div>
            <h2 className="text-2xl font-semibold text-gray-900">Verifying Your Email</h2>
            <p className="text-gray-600">Please wait while we verify your email address...</p>
          </div>
        );

      case 'success':
        return (
          <div className="text-center space-y-4">
            <div className="mx-auto w-16 h-16 bg-green-100 rounded-full flex items-center justify-center">
              <CheckCircle className="h-8 w-8 text-green-600" />
            </div>
            <h2 className="text-2xl font-semibold text-gray-900">Email Verified Successfully!</h2>
            <p className="text-gray-600">
              Your email has been verified. You can now log in to your account.
            </p>
            <div className="pt-4">
              <Button onClick={handleCancel} variant="medical">
                Continue
              </Button>
            </div>
          </div>
        );

      case 'error':
        return (
          <div className="text-center space-y-4">
            <div className="mx-auto w-16 h-16 bg-red-100 rounded-full flex items-center justify-center">
              <XCircle className="h-8 w-8 text-red-600" />
            </div>
            <h2 className="text-2xl font-semibold text-gray-900">Verification Failed</h2>
            <p className="text-gray-600">
              {error || 'There was an error verifying your email address.'}
            </p>
            <div className="space-y-3">
              <Button onClick={handleResendVerification} disabled={isResending} variant="outline">
                <Mail className="h-4 w-4 mr-2" />
                {isResending ? 'Sending...' : 'Resend Verification Email'}
              </Button>
              <div>
                <Button onClick={handleCancel} variant="ghost">
                  <ArrowLeft className="h-4 w-4 mr-2" />
                  Back to Signup
                </Button>
              </div>
            </div>
          </div>
        );

      default:
        return (
          <div className="text-center space-y-4">
            <div className="mx-auto w-16 h-16 bg-amber-100 rounded-full flex items-center justify-center">
              <Mail className="h-8 w-8 text-amber-600" />
            </div>
            <h2 className="text-2xl font-semibold text-gray-900">Verify Your Email</h2>
            <p className="text-gray-600">
              We've sent a verification link to <strong>{userEmail}</strong>
            </p>
            <p className="text-sm text-gray-500">
              Please check your email and click the verification link to activate your account.
            </p>
            <div className="space-y-3">
              <Button onClick={handleResendVerification} disabled={isResending} variant="outline">
                <RefreshCw className={`h-4 w-4 mr-2 ${isResending ? 'animate-spin' : ''}`} />
                {isResending ? 'Sending...' : 'Resend Verification Email'}
              </Button>
              <div>
                <Button onClick={handleCancel} variant="ghost">
                  <ArrowLeft className="h-4 w-4 mr-2" />
                  Back to Signup
                </Button>
              </div>
            </div>
          </div>
        );
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle className="text-center">Email Verification</DialogTitle>
          <DialogDescription className="text-center">
            Complete your account setup
          </DialogDescription>
        </DialogHeader>
        
        {renderContent()}
        
        {resendMessage && (
          <Alert className="border-green-200 bg-green-50 text-green-800">
            <CheckCircle className="h-4 w-4" />
            <AlertDescription>{resendMessage}</AlertDescription>
          </Alert>
        )}

        {error && verificationStatus === 'error' && (
          <Alert variant="destructive">
            <XCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}
      </DialogContent>
    </Dialog>
  );
};

export default EmailVerificationDialog;
