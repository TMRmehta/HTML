import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { CheckCircle, XCircle, Mail, ArrowLeft, RefreshCw } from 'lucide-react';
import { useAuthContext } from '@/context/AuthContext';

const EmailVerification = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { verifyEmail, resendVerification } = useAuthContext();
  const [verificationStatus, setVerificationStatus] = useState<'verifying' | 'success' | 'error' | 'idle'>('idle');
  const [error, setError] = useState('');
  const [isResending, setIsResending] = useState(false);
  const [resendMessage, setResendMessage] = useState('');

  const token = searchParams.get('token');

  useEffect(() => {
    if (token) {
      handleVerification();
    } else {
      setVerificationStatus('error');
      setError('No verification token provided');
    }
  }, [token]);

  const handleVerification = async () => {
    if (!token) return;

    setVerificationStatus('verifying');
    setError('');

    try {
      const result = await verifyEmail(token);
      if (result.verified) {
        setVerificationStatus('success');
        setTimeout(() => {
          navigate('/');
        }, 3000);
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
    setIsResending(true);
    setResendMessage('');
    setError('');

    try {
      const result = await resendVerification();
      if (result.sent) {
        setResendMessage('Verification email sent! Please check your inbox.');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to resend verification email');
    } finally {
      setIsResending(false);
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
              Your email has been verified. You'll be redirected to your dashboard shortly.
            </p>
            <div className="pt-4">
              <Button onClick={() => navigate('/dashboard')} variant="medical">
                Go to Dashboard
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
                <Button onClick={() => navigate('/')} variant="ghost">
                  <ArrowLeft className="h-4 w-4 mr-2" />
                  Back to Home
                </Button>
              </div>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <Card className="shadow-lg">
          <CardHeader className="text-center">
            <CardTitle className="text-3xl font-bold text-gray-900 mb-2">
              OncoSight AI
            </CardTitle>
            <CardDescription className="text-gray-600">
              AI-Powered Medical Platform
            </CardDescription>
          </CardHeader>
          <CardContent className="p-6">
            {renderContent()}
            
            {resendMessage && (
              <Alert className="mt-4 border-green-200 bg-green-50 text-green-800">
                <CheckCircle className="h-4 w-4" />
                <AlertDescription>{resendMessage}</AlertDescription>
              </Alert>
            )}

            {error && verificationStatus === 'error' && (
              <Alert variant="destructive" className="mt-4">
                <XCircle className="h-4 w-4" />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default EmailVerification;
