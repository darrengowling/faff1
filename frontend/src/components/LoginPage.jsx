import React, { useState, useMemo, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { toast } from 'sonner';
import { Button } from './ui/button';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { Separator } from './ui/separator';
import { TESTIDS } from '../testids';
import { ArrowLeft, Mail, CheckCircle, AlertCircle, Home } from 'lucide-react';
import { getSearchParam } from '../utils/safeBrowser.ts';
import EmailValidator from '../utils/emailValidator';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const LoginPage = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [magicLink, setMagicLink] = useState('');
  
  // Ref for keeping focus on email input during errors
  const emailInputRef = React.useRef(null);

  // Compute test mode safely inside component (SSR-compatible)
  const isTestMode = useMemo(() => {
    if (process.env.NODE_ENV === 'test') return true;
    if (process.env.REACT_APP_PLAYWRIGHT_TEST === 'true') return true;
    return getSearchParam('playwright') === 'true';
  }, []);

  // Email validation using shared utility
  const isValidEmail = (email) => {
    return EmailValidator.isValidEmail(email);
  };

  // Check if submit button should be enabled
  const isSubmitEnabled = () => {
    return !loading && email.trim() && isValidEmail(email.trim());
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Reset states
    setError('');
    setSuccess('');
    setMagicLink('');
    
    // Validate email using shared validator
    if (!email.trim() || !isValidEmail(email.trim())) {
      const errorMsg = !email.trim() ? 'Email is required' : 'Please enter a valid email.';
      setError(errorMsg);
      
      // Keep focus on email input for better UX - immediate in TEST_MODE
      const focusDelay = isTestMode ? 0 : 100;
      setTimeout(() => {
        if (emailInputRef.current) {
          emailInputRef.current.focus();
        }
      }, focusDelay);
      return;
    }

    setLoading(true);

    try {
      const response = await axios.post(`${API}/auth/magic-link`, {
        email: email.trim()
      });

      setSuccess('Magic link sent! Check your email or use the link below.');
      
      console.log('Magic link response:', response.data);
      console.log('Test mode:', isTestMode);
      
      // In development, show the magic link
      if (response.data.dev_magic_link) {
        setMagicLink(response.data.dev_magic_link);
        
        // In test mode, auto-click the magic link for seamless testing
        if (isTestMode) {
          console.log('Auto-navigating to magic link verification...');
          setTimeout(() => {
            const url = new URL(response.data.dev_magic_link);
            const token = url.searchParams.get('token');
            if (token) {
              console.log('Navigating to /auth/verify with token:', token);
              navigate(`/auth/verify?token=${token}`);
            }
          }, 500);
          return;
        }
      }

    } catch (err) {
      console.error('Magic link request failed:', err);
      
      // Create concise error messages based on response
      let errorMessage = 'Unable to send magic link. Please try again.';
      
      if (err.response?.status === 400) {
        errorMessage = 'Invalid email address format';
      } else if (err.response?.status === 429) {
        errorMessage = 'Too many requests. Please wait a moment and try again.';
      } else if (err.response?.status >= 500) {
        errorMessage = 'Server error. Please try again in a moment.';
      } else if (err.response?.data?.detail) {
        // Use server message if it's concise
        const serverMsg = err.response.data.detail;
        if (serverMsg.length < 80) {
          errorMessage = serverMsg;
        }
      }
      
      setError(errorMessage);
      
      // Keep focus on email input for immediate retry
      setTimeout(() => {
        if (emailInputRef.current) {
          emailInputRef.current.focus();
          emailInputRef.current.select(); // Select text for easy correction
        }
      }, 100);
      
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
      {/* Global Header - Always Visible for Navigation */}
      <header className="bg-white shadow-sm border-b" data-testid="login-header">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* Left: Back to Home Navigation */}
            <div className="flex items-center space-x-4">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => navigate('/')}
                className="text-gray-600 hover:text-gray-900 flex items-center"
                data-testid="back-to-home-link"
              >
                <Home className="w-4 h-4 mr-2" />
                Back to Home
              </Button>
            </div>
            
            {/* Center: Brand */}
            <div className="flex items-center">
              <h1 className="text-lg font-semibold text-gray-900">Friends of PIFA</h1>
            </div>
            
            {/* Right: Additional Navigation (Future) */}
            <div className="flex items-center space-x-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => navigate('/')}
                className="text-gray-600 hover:text-gray-900"
                data-testid="home-nav-button"
              >
                Home
              </Button>
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
                    ref={emailInputRef}
                    type="email"
                    id="email"
                    value={email}
                    onChange={(e) => {
                      setEmail(e.target.value);
                      // Clear error when user starts typing
                      if (error) {
                        setError('');
                      }
                    }}
                    className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 disabled:bg-gray-50 disabled:cursor-not-allowed ${
                      error 
                        ? 'border-red-500 focus:ring-red-500 focus:border-red-500' 
                        : 'border-gray-300 focus:ring-blue-500 focus:border-blue-500'
                    }`}
                    placeholder="your.email@example.com"
                    disabled={loading}
                    data-testid={TESTIDS.authEmailInput}
                    autoComplete="email"
                    required
                    aria-describedby={error ? "email-error" : undefined}
                  />
                </div>

                {/* Error Message */}
                {error && (
                  <div 
                    id="email-error"
                    className="flex items-center space-x-2 text-red-600 bg-red-50 border border-red-200 p-3 rounded-md"
                    data-testid={TESTIDS.authError}
                    role="alert"
                    aria-live="polite"
                  >
                    <AlertCircle className="w-4 h-4 flex-shrink-0" />
                    <span className="text-sm font-medium">{error}</span>
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
                  disabled={!isSubmitEnabled()}
                  className={`w-full ${
                    loading 
                      ? 'bg-blue-400 cursor-not-allowed' 
                      : error 
                        ? 'bg-blue-600 hover:bg-blue-700 focus:ring-blue-500' 
                        : 'bg-blue-600 hover:bg-blue-700'
                  } ${isTestMode ? '' : 'transition-all duration-200'}`}
                  data-testid={TESTIDS.authSubmitBtn}
                >
                  {loading ? (
                    <div className="flex items-center justify-center space-x-2">
                      <div className={`w-4 h-4 border-2 border-white border-t-transparent rounded-full ${isTestMode ? '' : 'animate-spin'}`}></div>
                      <span>Sending Magic Link</span>
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