import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { toast } from 'sonner';
import { Button } from './ui/button';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { Separator } from './ui/separator';
import { TESTIDS } from '../testids';
import { ArrowLeft, Mail, CheckCircle, AlertCircle } from 'lucide-react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Check if running in test mode to disable animations
const isTestMode = process.env.NODE_ENV === 'test' || process.env.PLAYWRIGHT_TEST === 'true';

const LoginPage = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [magicLink, setMagicLink] = useState('');

  // Email validation
  const isValidEmail = (email) => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Reset states
    setError('');
    setSuccess('');
    setMagicLink('');
    
    // Validate email
    if (!email || !isValidEmail(email)) {
      setError('Please enter a valid email address');
      return;
    }

    setLoading(true);

    try {
      const response = await axios.post(`${API}/auth/magic-link`, {
        email: email.trim()
      });

      setSuccess('Magic link sent! Check your email or use the link below.');
      
      // In development, show the magic link
      if (response.data.dev_magic_link) {
        setMagicLink(response.data.dev_magic_link);
      }

      // Auto-redirect after 3 seconds in test mode
      if (isTestMode) {
        setTimeout(() => {
          navigate('/app');
        }, 1000);
      }

    } catch (err) {
      console.error('Magic link request failed:', err);
      const errorMessage = err.response?.data?.detail || 'Failed to send magic link. Please try again.';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleMagicLinkClick = () => {
    if (magicLink) {
      // Extract token from magic link and navigate to verification
      const url = new URL(magicLink);
      const token = url.searchParams.get('token');
      if (token) {
        navigate(`/auth/verify?token=${token}`);
      }
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Global Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-4">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => navigate('/')}
                className="text-gray-600 hover:text-gray-900"
                data-testid="back-to-home-link"
              >
                <ArrowLeft className="w-4 h-4 mr-2" />
                Back to Home
              </Button>
            </div>
            <div className="flex items-center">
              <h1 className="text-lg font-semibold text-gray-900">Friends of PIFA</h1>
            </div>
          </div>
        </div>
      </header>

      {/* Main Login Content */}
      <main className="flex-1 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
        <div className="w-full max-w-md">
          <div className="text-center mb-8">
            <Mail className="w-12 h-12 text-blue-600 mx-auto mb-4" />
            <h2 className="text-3xl font-bold text-gray-900 mb-2">Sign In</h2>
            <p className="text-gray-600">
              Enter your email to receive a magic link for secure access
            </p>
          </div>

          <Card className={`shadow-lg ${isTestMode ? '' : 'transition-all duration-300'}`}>
            <CardHeader>
              <CardTitle className="text-xl text-center">Magic Link Authentication</CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-6">
                {/* Email Input */}
                <div>
                  <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
                    Email Address
                  </label>
                  <input
                    type="email"
                    id="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-50 disabled:cursor-not-allowed"
                    placeholder="your.email@example.com"
                    disabled={loading}
                    data-testid={TESTIDS.authEmailInput}
                    autoComplete="email"
                    required
                  />
                </div>

                {/* Error Message */}
                {error && (
                  <div 
                    className="flex items-center space-x-2 text-red-600 bg-red-50 p-3 rounded-md"
                    data-testid={TESTIDS.authError}
                  >
                    <AlertCircle className="w-4 h-4 flex-shrink-0" />
                    <span className="text-sm">{error}</span>
                  </div>
                )}

                {/* Success Message */}
                {success && (
                  <div 
                    className="flex items-center space-x-2 text-green-600 bg-green-50 p-3 rounded-md"
                    data-testid={TESTIDS.authSuccess}
                  >
                    <CheckCircle className="w-4 h-4 flex-shrink-0" />
                    <span className="text-sm">{success}</span>
                  </div>
                )}

                {/* Submit Button */}
                <Button
                  type="submit"
                  disabled={loading || !email || !isValidEmail(email)}
                  className={`w-full ${isTestMode ? '' : 'transition-all duration-200'}`}
                  data-testid={TESTIDS.authSubmitBtn}
                >
                  {loading ? (
                    <div className="flex items-center justify-center space-x-2">
                      <div className={`w-4 h-4 border-2 border-white border-t-transparent rounded-full ${isTestMode ? '' : 'animate-spin'}`}></div>
                      <span>Sending Magic Link...</span>
                    </div>
                  ) : (
                    <div className="flex items-center justify-center space-x-2">
                      <Mail className="w-4 h-4" />
                      <span>Send Magic Link</span>
                    </div>
                  )}
                </Button>

                {/* Development Magic Link */}
                {magicLink && (
                  <div className="mt-4">
                    <Separator className="mb-4" />
                    <div className="text-center">
                      <p className="text-sm text-gray-600 mb-2">Development Mode - Magic Link:</p>
                      <Button
                        type="button"
                        variant="outline"
                        onClick={handleMagicLinkClick}
                        className="text-blue-600 hover:text-blue-800"
                        data-testid="dev-magic-link-btn"
                      >
                        Login Now
                      </Button>
                    </div>
                  </div>
                )}
              </form>
            </CardContent>
          </Card>

          {/* Additional Help */}
          <div className="mt-6 text-center">
            <p className="text-sm text-gray-600">
              No password required. We'll send you a secure link to sign in.
            </p>
          </div>
        </div>
      </main>
    </div>
  );
};

export default LoginPage;