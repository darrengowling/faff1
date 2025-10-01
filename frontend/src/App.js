import React, { useState, useEffect, createContext, useContext } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useNavigate, useLocation, useParams } from 'react-router-dom';
import axios from 'axios';
import { Toaster, toast } from 'sonner';
import { io } from 'socket.io-client';
import './App.css';
import './styles/mobile-optimizations.css';

// Initialize i18n
import './i18n';
import { useTranslation } from 'react-i18next';
import { TESTIDS } from './testids.ts';
import { ThemeProvider } from './theme/ThemeProvider';
import { getBrandName } from './brand';
import { AuthBrand } from './components/ui/brand-badge.jsx';
import { CompactRules } from './components/ui/rules-badge.jsx';

// Import testing utilities
import { setupRouteVerification } from './testing/verifyTestIds.ts';

// Import components
import AuctionRoom from './components/AuctionRoom';
import MyClubs from './components/MyClubs';
import Fixtures from './components/Fixtures';
import Leaderboard from './components/Leaderboard';
import AdminDashboard from './components/AdminDashboard';
import DiagnosticPage from './components/DiagnosticPage';
import LandingPage from './components/LandingPage';
import LoginPage from './components/LoginPage';
import CreateLeagueWizard from './components/CreateLeagueWizard';
import LeagueCreationPage from './components/LeagueCreationPage';
import LeagueCreationForm from './components/LeagueCreationForm';
import { SafeRoute } from './components/routing/RouteGuards';
import AppShell from './components/layouts/AppShell';
import EnhancedHomeScreen from './components/EnhancedHomeScreen';
import DashboardContent from './components/DashboardContent';
import AppLayout, { DashboardLayout, AuctionLayout, AdminLayout, RosterLayout, FixturesLayout, LeaderboardLayout } from './components/layouts/AppLayout';
import NotFoundPage from './components/NotFoundPage';
import { BottomTabNav } from './components/ui/mobile-nav';

// Import Shadcn components
import { Button } from './components/ui/button';
import { Input } from './components/ui/input';
import { Card, CardHeader, CardTitle, CardContent } from './components/ui/card';
import { Badge } from './components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogTrigger } from './components/ui/dialog';
import { Label } from './components/ui/label';
import { Separator } from './components/ui/separator';
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from './components/ui/alert-dialog';

import { TestableInput, TestableButton } from './components/testable/TestableComponents.tsx';

// Icons
import { 
  Trophy, 
  Users, 
  Crown, 
  Mail, 
  User, 
  Settings, 
  LogOut,
  Plus,
  Timer,
  DollarSign,
  Gavel,
  Target,
  Send,
  UserPlus,
  CheckCircle,
  Clock,
  XCircle,
  RefreshCw,
  Eye,
  Shield,
  Calendar,
  MapPin,
  Play,
  Copy
} from 'lucide-react';
import { RequireAuth, RedirectIfAuthed } from './guards/AuthGuards';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Configure axios to send cookies with requests
axios.defaults.withCredentials = true;

// Create Auth Context
const AuthContext = createContext();

// Auth Provider Component
const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState(localStorage.getItem('token'));

  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      fetchUser();
    } else {
      // Even without a localStorage token, try to fetch user (for cookie-based auth)
      fetchUser();
    }
    
    // Set up testID verification in development
    if (process.env.NODE_ENV === 'development') {
      setupRouteVerification();
    }
  }, [token]);

  const fetchUser = async () => {
    try {
      const response = await axios.get(`${API}/auth/me`);
      setUser(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch user:', error);
      
      // Only logout on authentication errors (401, 403), not on network/server errors
      if (error.response && (error.response.status === 401 || error.response.status === 403)) {
        console.log('Token expired or invalid, logging out');
        logout(); // This will set loading to false
      } else {
        // For network errors or server issues, keep the token and session active
        console.log('Network/server error, keeping session active');
        setLoading(false);
      }
    }
  };

  const login = (newToken, userData) => {
    localStorage.setItem('token', newToken);
    setToken(newToken);
    setUser(userData);
    axios.defaults.headers.common['Authorization'] = `Bearer ${newToken}`;
  };

  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
    setLoading(false);
    delete axios.defaults.headers.common['Authorization'];
  };

  const refreshUser = () => {
    fetchUser();
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, loading, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
};

// Hook to use Auth Context
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

// Login Component
const Login = () => {
  const { t } = useTranslation();
  const location = useLocation();
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [linkSent, setLinkSent] = useState(false);
  const [magicLink, setMagicLink] = useState(null);

  const handleSendMagicLink = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await axios.post(`${API}/auth/magic-link`, { email });
      setLinkSent(true);
      
      // Check if development magic link is provided
      if (response.data.dev_magic_link) {
        let magicLinkUrl = response.data.dev_magic_link;
        
        // Add redirect parameter if present
        const urlParams = new URLSearchParams(location.search);
        const redirectTo = urlParams.get('next') || urlParams.get('redirect');
        if (redirectTo) {
          const url = new URL(magicLinkUrl);
          url.searchParams.set('redirect', redirectTo);
          magicLinkUrl = url.toString();
        }
        
        setMagicLink(magicLinkUrl);
        toast.success(t('auth.magicLinkSent'));
      } else {
        toast.success(t('auth.magicLinkSent'));
      }
    } catch (error) {
      toast.error('Failed to send magic link. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  if (linkSent) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center">
            <CardTitle className="text-2xl font-bold text-gray-900">
              {magicLink ? t('auth.magicLinkReady') : t('auth.checkEmail')}
            </CardTitle>
          </CardHeader>
          <CardContent className="text-center space-y-4">
            {magicLink ? (
              // Development mode - show magic link directly
              <div className="space-y-4">
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <Shield className="w-8 h-8 text-blue-600 mx-auto mb-2" />
                  <p className="text-blue-800 mb-2">
                    <strong>{t('auth.developmentMode')}</strong>
                  </p>
                  <p className="text-sm text-blue-600 mb-3">
                    {t('auth.developmentLoginText')}
                  </p>
                  <Button
                    onClick={() => window.location.href = magicLink}
                    className="w-full mb-3 touch-target"
                    size="lg"
                    data-testid={TESTIDS.loginNowButton}
                  >
                    {t('auth.loginNow')}
                  </Button>
                  <div className="text-xs text-gray-500 border-t pt-3">
                    <p>{t('auth.orCopyLink')}</p>
                    <div className="bg-gray-100 p-2 rounded text-xs break-all mt-1">
                      {magicLink}
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        navigator.clipboard.writeText(magicLink);
                        toast.success(t('auth.magicLinkCopied'));
                      }}
                      className="mt-2"
                    >
                      {t('auth.copyLink')}
                    </Button>
                  </div>
                </div>
              </div>
            ) : (
              // Production mode - email sent
              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <Mail className="w-8 h-8 text-green-600 mx-auto mb-2" />
                <p className="text-green-800">
                  {t('auth.emailSentMessage', { email })}
                </p>
                <p className="text-sm text-green-600 mt-2">
                  {t('auth.clickEmailLink')}
                </p>
              </div>
            )}
            <Button
              variant="outline"
              onClick={() => {
                setLinkSent(false);
                setMagicLink(null);
              }}
              className="w-full"
            >
              {t('auth.sendAnotherLink')}
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <AuthBrand className="mx-auto mb-4" />
          <CardTitle className="text-2xl font-bold text-gray-900">{t('auth.loginTitle', { brandName: getBrandName() })}</CardTitle>
          <p className="text-gray-600">{t('auth.loginSubtitle')}</p>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSendMagicLink} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">{t('common.email')}</Label>
              <Input
                id="email"
                type="email"
                placeholder="your@email.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                data-testid={TESTIDS.emailInput}
              />
            </div>
            <Button
              type="submit"
              className="w-full touch-target"
              size="lg"
              disabled={loading}
              data-testid={TESTIDS.magicLinkSubmit}
            >
              {loading ? t('auth.sending') : t('auth.sendMagicLink')}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
};

// Magic Link Verification Component
const MagicLinkVerify = () => {
  const { t } = useTranslation();
  const { login } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const verifyToken = async () => {
      const urlParams = new URLSearchParams(window.location.search);
      const token = urlParams.get('token');

      if (!token) {
        setError(t('auth.invalidToken'));
        setLoading(false);
        return;
      }

      try {
        const response = await axios.post(`${API}/auth/verify`, { token });
        login(response.data.access_token, response.data.user);
        toast.success(t('auth.loginSuccess'));
        
        // Check for redirect parameter
        const redirectTo = urlParams.get('redirect');
        if (redirectTo) {
          navigate(decodeURIComponent(redirectTo));
        } else {
          navigate('/app');
        }
      } catch (error) {
        setError(t('auth.invalidToken'));
        toast.error(t('auth.invalidMagicLink'));
      } finally {
        setLoading(false);
      }
    };

    verifyToken();
  }, [login, navigate]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <Card className="w-full max-w-md">
          <CardContent className="text-center p-8">
            <div className="animate-spin w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full mx-auto mb-4"></div>
            <p>{t('auth.verifyingLogin')}</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <Card className="w-full max-w-md">
          <CardContent className="text-center p-8">
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <p className="text-red-800">{error}</p>
            </div>
            <Button
              className="mt-4"
              onClick={() => navigate('/login')}
            >
              {t('auth.backToLogin')}
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return null;
};

// Invitation Accept Component
const InvitationAccept = () => {
  const { t } = useTranslation();
  const { user } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [league, setLeague] = useState(null);

  useEffect(() => {
    const acceptInvitation = async () => {
      const urlParams = new URLSearchParams(location.search);
      const token = urlParams.get('token');

      if (!token) {
        setError(t('leagueManagement.noInvitationToken'));
        setLoading(false);
        return;
      }

      if (!user) {
        // Redirect to login with return URL
        navigate(`/login?redirect=${encodeURIComponent(location.pathname + location.search)}`);
        return;
      }

      try {
        const response = await axios.post(`${API}/invitations/accept`, { token });
        setLeague(response.data);
        toast.success(t('leagueManagement.joinedSuccessfully', { league: response.data.name }));
        setTimeout(() => {
          navigate('/app');
        }, 2000);
      } catch (error) {
        setError(error.response?.data?.detail || t('leagueManagement.failedToAcceptInvitation'));
        toast.error(t('leagueManagement.failedToAcceptInvitation'));
      } finally {
        setLoading(false);
      }
    };

    acceptInvitation();
  }, [user, location, navigate]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <Card className="w-full max-w-md">
          <CardContent className="text-center p-8">
            <div className="animate-spin w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full mx-auto mb-4"></div>
            <p>{t('leagueManagement.processingInvitation')}</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <Card className="w-full max-w-md">
          <CardContent className="text-center p-8">
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <XCircle className="w-8 h-8 text-red-600 mx-auto mb-2" />
              <p className="text-red-800">{error}</p>
            </div>
            <Button
              className="mt-4"
              onClick={() => navigate('/app')}
            >
              Go to Dashboard
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (league) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-green-50 to-emerald-100 flex items-center justify-center">
        <Card className="w-full max-w-md">
          <CardContent className="text-center p-8">
            <div className="bg-green-50 border border-green-200 rounded-lg p-4" data-testid={TESTIDS.joinSuccessMessage}>
              <CheckCircle className="w-12 h-12 text-green-600 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-green-900 mb-2">Welcome to the League!</h3>
              <p className="text-green-800">
                You've successfully joined <strong>{league.name}</strong>
              </p>
              <p className="text-sm text-green-600 mt-2">
                Redirecting to dashboard...
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return null;
};

// League Join Component
const LeagueJoin = () => {
  const { leagueId } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [league, setLeague] = useState(null);
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    const joinLeague = async () => {
      if (!leagueId) {
        setError('Invalid league link');
        setLoading(false);
        return;
      }

      if (!user) {
        // Redirect to login with return URL
        navigate(`/login?next=${encodeURIComponent(`/join/${leagueId}`)}`);
        return;
      }

      try {
        setLoading(true);
        
        // First, get league details to show user what they're joining
        const leagueResponse = await axios.get(`${API}/leagues/${leagueId}`);
        setLeague(leagueResponse.data);
        
        // Then join the league
        await axios.post(`${API}/leagues/${leagueId}/join`);
        
        setSuccess(true);
        toast.success(`Successfully joined ${leagueResponse.data.name}!`);
        
        setTimeout(() => {
          navigate(`/app/leagues/${leagueId}/lobby`);
        }, 2000);
        
      } catch (error) {
        console.error('Join league error:', error);
        if (error.response?.status === 404) {
          setError('League not found. The link may be invalid or expired.');
        } else if (error.response?.status === 400) {
          setError(error.response?.data?.detail || 'Cannot join this league.');
        } else {
          setError('Failed to join league. Please try again.');
        }
        toast.error(error.response?.data?.detail || 'Failed to join league');
      } finally {
        setLoading(false);
      }
    };

    joinLeague();
  }, [leagueId, user, navigate]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <Card className="w-full max-w-md">
          <CardContent className="text-center p-8">
            <div className="animate-spin w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full mx-auto mb-4"></div>
            <p>Joining league...</p>
            {league && (
              <p className="text-sm text-gray-600 mt-2">
                Joining "{league.name}"
              </p>
            )}
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <Card className="w-full max-w-md">
          <CardContent className="text-center p-8">
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <XCircle className="w-8 h-8 text-red-600 mx-auto mb-2" />
              <h3 className="text-lg font-semibold text-red-900 mb-2">Unable to Join League</h3>
              <p className="text-red-800">{error}</p>
            </div>
            <div className="flex space-x-2 mt-4">
              <Button
                variant="outline"
                className="flex-1"
                onClick={() => navigate('/app')}
              >
                Go to Dashboard
              </Button>
              {league && (
                <Button
                  className="flex-1"
                  onClick={() => window.location.reload()}
                >
                  Try Again
                </Button>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (success && league) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-green-50 to-emerald-100 flex items-center justify-center">
        <Card className="w-full max-w-md">
          <CardContent className="text-center p-8">
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <CheckCircle className="w-12 h-12 text-green-600 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-green-900 mb-2">Welcome to the League!</h3>
              <p className="text-green-800">
                You've successfully joined <strong>{league.name}</strong>
              </p>
              <p className="text-sm text-green-600 mt-2">
                Redirecting to league lobby...
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return null;
};

// Enhanced League Creation Dialog
const CreateLeagueDialog = ({ open, onOpenChange, onLeagueCreated }) => {
  const { t } = useTranslation();

  const handleSuccess = (data) => {
    if (onLeagueCreated) {
      onLeagueCreated(data);
    }
  };

  const handleCancel = () => {
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange} data-state={open ? "open" : "closed"}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          {/* Breadcrumb Navigation */}
          <div className="flex items-center space-x-2 text-sm text-gray-500 mb-2">
            <button
              type="button"
              onClick={handleCancel}
              className="text-blue-600 hover:text-blue-800 hover:underline"
              data-testid="breadcrumb-home"
            >
              Home
            </button>
            <span>/</span>
            <span className="text-gray-900 font-medium">New League</span>
          </div>
          <DialogTitle>{t('leagueCreation.createNewLeague')}</DialogTitle>
          <DialogDescription>
            Choose a template to set default values and customize your league settings.
          </DialogDescription>
        </DialogHeader>
        
        <LeagueCreationForm
          onCancel={handleCancel}
          onSuccess={handleSuccess}
          isDialog={true}
        />
      </DialogContent>
    </Dialog>
  );
};

// League Management Component
const LeagueLobby = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [league, setLeague] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchLeague = async () => {
      try {
        setLoading(true);
        const response = await axios.get(`${API}/leagues/${id}`);
        setLeague(response.data);
      } catch (err) {
        console.error('Failed to fetch league:', err);
        setError('Failed to load league. Please try again.');
      } finally {
        setLoading(false);
      }
    };

    if (id) {
      fetchLeague();
    }
  }, [id]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-64">
        <div className="animate-spin w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-8">
        <p className="text-red-600">{error}</p>
        <Button 
          onClick={() => navigate('/app')} 
          variant="outline" 
          className="mt-4"
        >
          Back to Dashboard
        </Button>
      </div>
    );
  }

  if (!league) {
    return (
      <div className="text-center py-8">
        <p className="text-gray-600">League not found.</p>
        <Button 
          onClick={() => navigate('/app')} 
          variant="outline" 
          className="mt-4"
        >
          Back to Dashboard
        </Button>
      </div>
    );
  }

  return (
    <LeagueManagement 
      league={league} 
      onBack={() => navigate('/app')} 
    />
  );
};

const LeagueManagement = ({ league, onBack }) => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [members, setMembers] = useState([]);
  const [invitations, setInvitations] = useState([]);
  const [leagueStatus, setLeagueStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteLoading, setInviteLoading] = useState(false);
  const [auctionStartLoading, setAuctionStartLoading] = useState(false);

  const handleStartAuction = async () => {
    if (!leagueStatus?.is_ready || auctionStartLoading) {
      return;
    }
    
    setAuctionStartLoading(true);
    
    try {
      // Add explicit delay to ensure backend is ready
      await new Promise(resolve => setTimeout(resolve, 500));
      
      toast.info('Starting auction...');
      
      const startResponse = await axios.post(`${API}/auction/${league.id}/start`);
      
      if (startResponse.status === 200) {
        toast.success('Auction started successfully! Redirecting...');
        
        // Wait for backend to fully initialize auction
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        navigate(`/auction/${league.id}`);
      } else {
        throw new Error(`Unexpected status: ${startResponse.status}`);
      }
    } catch (error) {
      console.error('Start auction error:', error);
      
      let errorMessage = 'Failed to start auction. ';
      
      if (error.response?.status === 404) {
        errorMessage += 'League not found. Please try refreshing the page.';
      } else if (error.response?.status === 400) {
        errorMessage += error.response.data?.detail || 'League not ready for auction.';
      } else if (error.code === 'NETWORK_ERROR' || !error.response) {
        errorMessage += 'Network error. Please check your connection and try again.';
      } else {
        errorMessage += 'Please try again in a moment.';
      }
      
      toast.error(errorMessage);
    } finally {
      setAuctionStartLoading(false);
    }
  };

  const isCommissioner = league.commissioner_id === user.id;

  const fetchLeagueDataWithRetry = async (retryCount = 0) => {
    try {
      await fetchLeagueData();
    } catch (error) {
      if (retryCount < 2) {
        console.log(`Retrying league data fetch (${retryCount + 1}/2)...`);
        setTimeout(() => fetchLeagueDataWithRetry(retryCount + 1), 1000);
      }
    }
  };

  useEffect(() => {
    fetchLeagueDataWithRetry();
    
    // Set up real-time WebSocket connection for league updates
    const origin = process.env.REACT_APP_BACKEND_URL || 
                   'https://leaguemate-1.preview.emergentagent.com';
    
    const socket = io(origin, {
      path: '/socket.io',  // STANDARD SOCKET.IO PATH - INGRESS CONFIGURED
      transports: ['websocket', 'polling'],
      withCredentials: true,
      reconnection: true
    });

    socket.on('connect', () => {
      console.log('Connected to league real-time updates');
      // Join league room for real-time updates
      socket.emit('join_league', { 
        league_id: league.id,
        user_id: user.id 
      });
    });

    socket.on('member_joined', (data) => {
      console.log('Member joined event:', data);
      if (data.league_id === league.id) {
        // Refresh league data to show new member
        fetchLeagueData();
        toast.success(`New member joined the league!`);
      }
    });

    socket.on('league_status_update', (data) => {
      console.log('League status update:', data);
      if (data.league_id === league.id) {
        setLeagueStatus(prev => ({
          ...prev,
          member_count: data.member_count,
          is_ready: data.is_ready
        }));
      }
    });

    socket.on('auction_started', (data) => {
      console.log('Auction started event:', data);
      if (data.league_id === league.id) {
        toast.success('Auction has started! Redirecting...');
        setTimeout(() => {
          navigate(`/auction/${league.id}`);
        }, 1500);
      }
    });

    socket.on('disconnect', () => {
      console.log('Disconnected from league updates');
    });
    
    return () => {
      socket.disconnect();
    };
  }, [league.id, user.id]);

  const fetchLeagueData = async () => {
    try {
      // Add small delay to ensure backend consistency
      await new Promise(resolve => setTimeout(resolve, 200));
      
      const [membersRes, statusRes, invitationsRes] = await Promise.all([
        axios.get(`${API}/leagues/${league.id}/members`),
        axios.get(`${API}/leagues/${league.id}/status`),
        isCommissioner ? axios.get(`${API}/leagues/${league.id}/invitations`) : Promise.resolve({ data: [] })
      ]);

      setMembers(membersRes.data);
      setLeagueStatus(statusRes.data);
      setInvitations(invitationsRes.data);
      
      // Log status for debugging
      console.log('League status updated:', statusRes.data);
      
    } catch (error) {
      console.error('Failed to load league data:', error);
      
      let errorMessage = 'Failed to load league data. ';
      if (error.response?.status === 404) {
        errorMessage += 'League not found.';
      } else if (error.code === 'NETWORK_ERROR' || !error.response) {
        errorMessage += 'Please check your connection.';
      } else {
        errorMessage += 'Please try refreshing the page.';
      }
      
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleInvite = async (e) => {
    e.preventDefault();
    setInviteLoading(true);

    try {
      await axios.post(`${API}/leagues/${league.id}/invite`, { 
        league_id: league.id, 
        email: inviteEmail 
      });
      setInviteEmail('');
      toast.success('Invitation sent successfully!');
      fetchLeagueData(); // Refresh data
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to send invitation');
    } finally {
      setInviteLoading(false);
    }
  };

  const handleResendInvitation = async (invitationId) => {
    try {
      await axios.post(`${API}/leagues/${league.id}/invitations/${invitationId}/resend`);
      toast.success('Invitation resent successfully!');
      fetchLeagueData();
    } catch (error) {
      toast.error('Failed to resend invitation');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full"></div>
      </div>
    );
  }

  return (
    <div 
      className={`space-y-6 ${auctionStartLoading ? 'relative' : ''}`}
      {...(leagueStatus && members.length > 0 && { 'data-testid': TESTIDS.lobbyReady })}
    >
      {/* Auction Start Loading Overlay */}
      {auctionStartLoading && (
        <div className="absolute inset-0 bg-white bg-opacity-90 flex items-center justify-center z-50 rounded-lg">
          <div className="text-center">
            <RefreshCw className="w-8 h-8 animate-spin text-blue-600 mx-auto mb-2" />
            <p className="text-lg font-medium text-gray-900">Starting Auction...</p>
            <p className="text-sm text-gray-600">Please wait while we initialize the auction</p>
          </div>
        </div>
      )}
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Button variant="outline" onClick={onBack} data-testid={TESTIDS.backButton}>
            ← Back
          </Button>
          <div>
            <h2 className="text-2xl font-bold text-gray-900">{league.name}</h2>
            <p className="text-gray-600">{league.season} • {league.competition}</p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <Badge variant={leagueStatus?.is_ready ? "default" : "secondary"}>
            {leagueStatus?.status || 'setup'}
          </Badge>
          {isCommissioner && (
            <Badge variant="outline" className="bg-yellow-50 text-yellow-700 border-yellow-200">
              <Crown className="w-3 h-3 mr-1" />
              Commissioner
            </Badge>
          )}
        </div>
      </div>

      {/* Join Count Display */}
      {leagueStatus && (
        <div className="mb-6">
          <div className="flex items-center justify-between mb-4">
            <div className="text-lg font-semibold" data-testid={TESTIDS.lobbyJoined}>
              <span data-testid={TESTIDS.lobbyJoinedCount}>{leagueStatus.member_count}</span>/{leagueStatus.max_members}
            </div>
            <div className={`px-3 py-1 rounded-full text-sm font-medium ${
              leagueStatus.is_ready ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
            }`}>
              {leagueStatus.is_ready ? 'Ready to Start' : `Need ${leagueStatus.min_members - leagueStatus.member_count} more`}
            </div>
          </div>
          
          {/* Rules Badge */}
          <div className="mb-4">
            <CompactRules 
              leagueSettings={{
                clubSlots: league.settings?.roster_size,
                budgetPerManager: league.settings?.budget,
                leagueSize: { min: leagueStatus.min_members, max: leagueStatus.max_members }
              }}
              loading={false}
              className=""
            />
          </div>
          
          {/* Start Auction Button - Commissioner Only */}
          {isCommissioner && (
            <div className="mb-6">
              <TestableButton
                onClick={() => {
                  // Ensure all data is loaded and league is truly ready
                  if (leagueStatus?.is_ready && 
                      !auctionStartLoading && 
                      !loading && 
                      members.length >= (leagueStatus?.min_members || 2) &&
                      league.id) {
                    handleStartAuction();
                  }
                }}
                className={`w-full transition-all duration-200 ${
                  auctionStartLoading 
                    ? 'bg-blue-600 cursor-wait' 
                    : leagueStatus?.is_ready 
                      ? 'bg-green-600 hover:bg-green-700 active:bg-green-800' 
                      : 'bg-gray-400 cursor-not-allowed'
                }`}
                data-testid={TESTIDS.startAuction}
                disabled={
                  !leagueStatus?.is_ready || 
                  auctionStartLoading || 
                  loading || 
                  members.length < (leagueStatus?.min_members || 2) ||
                  !league.id
                }
                title={
                  auctionStartLoading 
                    ? 'Starting auction...'
                    : !leagueStatus?.is_ready 
                      ? `Cannot start auction - need minimum ${leagueStatus?.min_members || 2} members (currently ${leagueStatus?.member_count || 0})` 
                      : 'Start the auction now'
                }
              >
                {auctionStartLoading ? (
                  <>
                    <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                    Starting Auction...
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4 mr-2" />
                    Start Auction
                  </>
                )}
              </TestableButton>
            </div>
          )}
        </div>
      )}

      {/* League Status Details (keep existing card for more details) */}
      {leagueStatus && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Shield className="w-5 h-5" />
              <span>League Status Details</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">{leagueStatus.member_count}</div>
                <div className="text-sm text-gray-600">Members</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">{leagueStatus.min_members}</div>
                <div className="text-sm text-gray-600">Min Required</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-orange-600">{leagueStatus.max_members}</div>
                <div className="text-sm text-gray-600">Max Allowed</div>
              </div>
              <div className="text-center">
                <div className={`text-2xl font-bold ${leagueStatus.is_ready ? 'text-green-600' : 'text-red-600'}`}>
                  {leagueStatus.is_ready ? '✓' : '✗'}
                </div>
                <div className="text-sm text-gray-600">Ready</div>
              </div>
            </div>
            {leagueStatus.is_ready && (
              <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-lg">
                <p className="text-green-800 text-sm font-medium">
                  🎉 League is ready! You can now start the auction when all members are prepared.
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Teams to be Auctioned */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Trophy className="w-5 h-5" />
            <span>Teams in Auction</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {/* Hardcoded teams for now - replace with actual data from backend */}
            {[
              { name: 'Manchester City', country: 'England', short_name: 'MCI' },
              { name: 'Barcelona', country: 'Spain', short_name: 'BAR' },
              { name: 'Bayern Munich', country: 'Germany', short_name: 'BAY' },
              { name: 'Paris Saint-Germain', country: 'France', short_name: 'PSG' },
              { name: 'Real Madrid', country: 'Spain', short_name: 'RMA' },
              { name: 'Liverpool', country: 'England', short_name: 'LIV' },
              { name: 'Chelsea', country: 'England', short_name: 'CHE' },
              { name: 'Juventus', country: 'Italy', short_name: 'JUV' },
              { name: 'Arsenal', country: 'England', short_name: 'ARS' },
              { name: 'Atletico Madrid', country: 'Spain', short_name: 'ATM' },
              { name: 'Tottenham', country: 'England', short_name: 'TOT' },
              { name: 'AC Milan', country: 'Italy', short_name: 'MIL' }
            ].map((team, index) => (
              <div key={index} className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                {/* Team Badge */}
                <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-purple-600 rounded-full flex items-center justify-center">
                  <span className="text-white text-xs font-bold">
                    {team.short_name}
                  </span>
                </div>
                <div>
                  <div className="font-medium text-gray-900">{team.name}</div>
                  <div className="text-sm text-gray-600">{team.country}</div>
                </div>
              </div>
            ))}
          </div>
          <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
            <p className="text-blue-800 text-sm">
              <Trophy className="w-4 h-4 inline mr-1" />
              These teams will be available for bidding once the auction starts. Plan your strategy!
            </p>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Members */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Users className="w-5 h-5" />
              <span>Members ({members.length})</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3" data-testid={TESTIDS.lobbyMembersList}>
              {members.map((member) => (
                <div key={member.user_id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center space-x-3">
                    <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
                      <User className="w-4 h-4 text-white" />
                    </div>
                    <div>
                      <div className="font-medium">{member.display_name}</div>
                      <div className="text-sm text-gray-600">{member.email}</div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Badge variant={member.role === 'commissioner' ? 'default' : 'secondary'}>
                      {member.role === 'commissioner' && <Crown className="w-3 h-3 mr-1" />}
                      {member.role}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Invitations (Commissioner Only) */}
        {isCommissioner && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Send className="w-5 h-5" />
                <span>Invitations</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Send Invitation */}
              <form onSubmit={handleInvite} className="flex space-x-2">
                <Input
                  type="email"
                  placeholder="manager@example.com"
                  value={inviteEmail}
                  onChange={(e) => setInviteEmail(e.target.value)}
                  required
                  className="flex-1"
                  data-testid={TESTIDS.inviteEmailInput}
                />
                <Button type="submit" disabled={inviteLoading} data-testid={TESTIDS.inviteSubmitButton}>
                  {inviteLoading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <UserPlus className="w-4 h-4" />}
                </Button>
              </form>

              {/* Copy Invitation Link Button */}
              <div className="flex items-center justify-center">
                <Button
                  variant="outline"
                  onClick={() => {
                    const inviteCode = league.invite_code || 'CODE_NOT_FOUND';
                    navigator.clipboard.writeText(inviteCode).then(() => {
                      toast.success(`Invite code ${inviteCode} copied to clipboard!`);
                    }).catch(() => {
                      toast.error('Failed to copy invite code');
                    });
                  }}
                  className="w-full bg-blue-50 hover:bg-blue-100 text-blue-700 border-blue-200"
                  data-testid={TESTIDS.copyInvitationLinkButton}
                >
                  <Copy className="w-4 h-4 mr-2" />
                  Copy Invite Code: {league.invite_code || 'Loading...'}
                </Button>
              </div>

              {/* Invitation List */}
              <div className="space-y-2">
                {invitations.length === 0 ? (
                  <p className="text-gray-500 text-sm">No invitations sent yet</p>
                ) : (
                  invitations.map((invitation) => (
                    <div key={invitation.id} className="flex items-center justify-between p-2 bg-gray-50 rounded" data-testid={TESTIDS.inviteLinkItem}>
                      <div className="flex items-center space-x-2">
                        <div className="text-sm font-medium" data-testid={TESTIDS.inviteLinkUrl}>{invitation.email}</div>
                        <Badge 
                          variant={
                            invitation.status === 'accepted' ? 'default' :
                            invitation.status === 'expired' ? 'destructive' : 'secondary'
                          }
                        >
                          {invitation.status === 'accepted' && <CheckCircle className="w-3 h-3 mr-1" />}
                          {invitation.status === 'pending' && <Clock className="w-3 h-3 mr-1" />}
                          {invitation.status === 'expired' && <XCircle className="w-3 h-3 mr-1" />}
                          {invitation.status}
                        </Badge>
                      </div>
                      <div className="flex space-x-2">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => navigator.clipboard.writeText(`${window.location.origin}/join/${league.id}`)}
                          data-testid={TESTIDS.inviteCopyButton}
                        >
                          <Copy className="w-3 h-3" />
                        </Button>
                        {invitation.status === 'pending' && (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleResendInvitation(invitation.id)}
                          >
                            <RefreshCw className="w-3 h-3" />
                          </Button>
                        )}
                      </div>
                    </div>
                  ))
                )}
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      {/* League Settings */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Settings className="w-5 h-5" />
            <span>League Settings</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            <div className="text-center p-3 bg-blue-50 rounded-lg">
              <DollarSign className="w-6 h-6 text-blue-600 mx-auto mb-2" />
              <div className="text-lg font-bold">{league.settings.budget_per_manager}</div>
              <div className="text-sm text-gray-600">Budget</div>
            </div>
            <div className="text-center p-3 bg-green-50 rounded-lg">
              <Target className="w-6 h-6 text-green-600 mx-auto mb-2" />
              <div className="text-lg font-bold">{league.settings.club_slots_per_manager}</div>
              <div className="text-sm text-gray-600">Club Slots</div>
            </div>
            <div className="text-center p-3 bg-orange-50 rounded-lg">
              <Gavel className="w-6 h-6 text-orange-600 mx-auto mb-2" />
              <div className="text-lg font-bold">{league.settings.min_increment}</div>
              <div className="text-sm text-gray-600">Min Increment</div>
            </div>
            <div className="text-center p-3 bg-purple-50 rounded-lg">
              <Timer className="w-6 h-6 text-purple-600 mx-auto mb-2" />
              <div className="text-lg font-bold">{league.settings.bid_timer_seconds}s</div>
              <div className="text-sm text-gray-600">Bid Timer</div>
            </div>
          </div>
          
          <Separator className="my-4" />
          
          <div>
            <h4 className="font-medium mb-3">Scoring Rules</h4>
            <div className="grid grid-cols-3 gap-4">
              <div className="text-center p-3 bg-gray-50 rounded-lg">
                <div className="text-lg font-bold text-blue-600">+{league.settings.scoring_rules.club_goal}</div>
                <div className="text-sm text-gray-600">Per Goal</div>
              </div>
              <div className="text-center p-3 bg-gray-50 rounded-lg">
                <div className="text-lg font-bold text-green-600">+{league.settings.scoring_rules.club_win}</div>
                <div className="text-sm text-gray-600">Per Win</div>
              </div>
              <div className="text-center p-3 bg-gray-50 rounded-lg">
                <div className="text-lg font-bold text-orange-600">+{league.settings.scoring_rules.club_draw}</div>
                <div className="text-sm text-gray-600">Per Draw</div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Quick Access Navigation */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <MapPin className="w-5 h-5" />
            <span>Quick Access</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className={`grid grid-cols-1 gap-4 ${isCommissioner ? 'md:grid-cols-4' : 'md:grid-cols-3'}`}>
            <Button 
              className="flex flex-col items-center justify-center h-20 bg-blue-50 hover:bg-blue-100 text-blue-700 border-blue-200"
              variant="outline"
              onClick={() => navigate(`/clubs/${league.id}`)}
            >
              <Trophy className="w-6 h-6 mb-2" />
              <span className="text-sm font-medium">My Clubs</span>
            </Button>
            <Button 
              className="flex flex-col items-center justify-center h-20 bg-green-50 hover:bg-green-100 text-green-700 border-green-200"
              variant="outline"
              onClick={() => navigate(`/fixtures/${league.id}`)}
            >
              <Calendar className="w-6 h-6 mb-2" />
              <span className="text-sm font-medium">Fixtures & Results</span>
            </Button>
            <Button 
              className="flex flex-col items-center justify-center h-20 bg-purple-50 hover:bg-purple-100 text-purple-700 border-purple-200"
              variant="outline"
              onClick={() => navigate(`/leaderboard/${league.id}`)}
            >
              <Crown className="w-6 h-6 mb-2" />
              <span className="text-sm font-medium">Leaderboard</span>
            </Button>
            {isCommissioner && (
              <Button 
                className="flex flex-col items-center justify-center h-20 bg-red-50 hover:bg-red-100 text-red-700 border-red-200"
                variant="outline"
                onClick={() => navigate(`/admin/${league.id}`)}
              >
                <Shield className="w-6 h-6 mb-2" />
                <span className="text-sm font-medium">Admin Panel</span>
              </Button>
            )}
          </div>
        </CardContent>
      </Card>
      
      {/* Bottom Mobile Navigation */}
      <BottomTabNav 
        user={{ email: user?.email, role: isCommissioner ? 'commissioner' : 'manager' }}
      />
    </div>
  );
};

// Dashboard Component
const Dashboard = () => {
  const { t } = useTranslation();
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [leagues, setLeagues] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateLeague, setShowCreateLeague] = useState(false);
  const [selectedLeague, setSelectedLeague] = useState(null);

  useEffect(() => {
    fetchLeagues();
    seedClubs(); // Seed clubs data
  }, []);

  const fetchLeagues = async () => {
    try {
      const response = await axios.get(`${API}/leagues`);
      setLeagues(response.data);
    } catch (error) {
      toast.error('Failed to fetch leagues');
    } finally {
      setLoading(false);
    }
  };

  const seedClubs = async () => {
    try {
      await axios.post(`${API}/clubs/seed`);
    } catch (error) {
      console.log('Clubs already seeded or failed to seed');
    }
  };

  const handleLeagueCreated = (newLeague) => {
    setLeagues([newLeague, ...leagues]);
  };

  const handleViewLeague = (league) => {
    setSelectedLeague(league);
  };

  const handleStartAuction = async (leagueId) => {
    try {
      // Get the auction for this league
      const auctionResponse = await axios.get(`${API}/leagues/${leagueId}`);
      const league = auctionResponse.data;
      
      // Find the auction ID (simplified - in full app would be stored properly)
      // For now, we'll create or find the auction
      const startResponse = await axios.post(`${API}/auction/${leagueId}/start`);
      
      if (startResponse.data) {
        toast.success('Auction started successfully!');
        // Navigate to auction room
        navigate(`/auction/${leagueId}`);
      }
    } catch (error) {
      console.error('Start auction error:', error);
      toast.error('Failed to start auction. Make sure league is ready.');
    }
  };

  const handleViewAuction = (leagueId) => {
    // Navigate to auction room
    navigate(`/auction/${leagueId}`);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full"></div>
      </div>
    );
  }

  return (
    <>
      <DashboardContent
        leagues={leagues}
        loading={loading}
        onCreateLeague={() => setShowCreateLeague(true)}
        onViewLeague={handleViewLeague}
        onStartAuction={handleStartAuction}
        onViewAuction={handleViewAuction}
      />

      {/* Create League Dialog */}
      <CreateLeagueDialog
        open={showCreateLeague}
        onOpenChange={setShowCreateLeague}
        onLeagueCreated={handleLeagueCreated}
      />
    </>
  );
};

// Protected Route Component
const ProtectedRoute = ({ children }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full"></div>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (!user.verified) {
    return (
      <div className="min-h-screen bg-red-50 flex items-center justify-center">
        <Card className="w-full max-w-md">
          <CardContent className="text-center p-8">
            <div className="bg-red-100 rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-4">
              <Mail className="w-8 h-8 text-red-600" />
            </div>
            <h3 className="text-lg font-medium text-red-900 mb-2">Email Not Verified</h3>
            <p className="text-red-700">Please verify your email address to continue.</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return children;
};

// Component Wrappers to provide user context
const AuctionRoomWrapper = () => {
  const { user } = useAuth();
  const token = localStorage.getItem('token');
  
  return <AuctionRoom user={user} token={token} />;
};

const MyClubsWrapper = () => {
  const { user } = useAuth();
  const token = localStorage.getItem('token');
  
  return <MyClubs user={user} token={token} />;
};

const FixturesWrapper = () => {
  const { user } = useAuth();
  const token = localStorage.getItem('token');
  
  return <Fixtures user={user} token={token} />;
};

const LeaderboardWrapper = () => {
  const { user } = useAuth();
  const token = localStorage.getItem('token');
  
  return <Leaderboard user={user} token={token} />;
};

const AdminDashboardWrapper = () => {
  const { user } = useAuth();
  const token = localStorage.getItem('token');
  
  return <AdminDashboard user={user} token={token} />;
};

// Simple App Root Redirect Component - NO MARKETING SHELL
const AppRootRedirect = () => {
  const { user, loading } = useAuth();
  
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full"></div>
      </div>
    );
  }
  
  // Direct redirect: authenticated = app, unauthenticated = login
  return <Navigate to={user ? "/app" : "/login"} replace />;
};

// Global League Creation Success Marker Component
const LeagueCreateSuccessMarker = () => {
  const [showSuccess, setShowSuccess] = useState(false);
  const [leagueId, setLeagueId] = useState(null);
  const location = useLocation();

  useEffect(() => {
    // Check for league creation success in sessionStorage
    const successLeagueId = sessionStorage.getItem('leagueCreateSuccess');
    if (successLeagueId) {
      setLeagueId(successLeagueId);
      setShowSuccess(true);
      
      // Clear the success marker when we reach the lobby page
      if (location.pathname.includes('/lobby')) {
        sessionStorage.removeItem('leagueCreateSuccess');
        // Keep showing for a brief moment to allow tests to detect it
        setTimeout(() => {
          setShowSuccess(false);
        }, 500);
      }
    }
  }, [location.pathname]);

  if (!showSuccess || !leagueId) return null;

  return (
    <div 
      data-testid="create-success" 
      className="fixed top-16 left-1/2 transform -translate-x-1/2 z-50 bg-green-50 border border-green-200 rounded-md px-4 py-2 text-green-800 shadow-lg"
    >
      League created successfully! Redirecting to lobby...
    </div>
  );
};

// Simplified app state - no marketing navigation needed
const ConditionalBackToHomeLink = () => {
  const location = useLocation();
  
  return null; // No conditional navigation needed in simplified app
};

// Main App Component
function App() {
  // TEST_MODE: Globally disable animations/transitions to prevent timing issues
  useEffect(() => {
    const isTestMode = () => {
      return (
        process.env.NODE_ENV === 'test' ||
        process.env.REACT_APP_PLAYWRIGHT_TEST === 'true' ||
        process.env.REACT_APP_TEST_MODE === 'true' ||
        (typeof window !== 'undefined' && window.location.search.includes('playwright=true'))
      );
    };

    if (isTestMode()) {
      console.log('🧪 TEST_MODE: Injecting global animation/transition disablement CSS');
      
      // Create and inject TEST_MODE CSS
      const testModeStyles = document.createElement('style');
      testModeStyles.id = 'test-mode-styles';
      testModeStyles.innerHTML = `
        /* TEST_MODE: Disable animations and transitions globally */
        * {
          animation: none !important;
          transition: none !important;
        }
        
        /* TEST_MODE: Disable smooth scrolling */
        html {
          scroll-behavior: auto !important;
        }
        
        /* TEST_MODE: Prevent sticky jitter */
        * {
          animation-duration: 0s !important;
          animation-delay: 0s !important;
          transition-duration: 0s !important;
          transition-delay: 0s !important;
        }
      `;
      
      // Inject at the end of head to override other styles
      document.head.appendChild(testModeStyles);
      
      // TEST_MODE uniqueness guard for back-to-home-link
      const uniquenessGuard = setInterval(() => {
        const n = document.querySelectorAll('[data-testid="back-to-home-link"]').length;
        if (n !== 1) console.warn(`[testid-uniqueness] back-to-home-link count = ${n}`);
      }, 1000);
      
      // Cleanup on unmount
      return () => {
        const existingStyles = document.getElementById('test-mode-styles');
        if (existingStyles) {
          document.head.removeChild(existingStyles);
        }
        clearInterval(uniquenessGuard);
      };
    }
  }, []);

  return (
    <ThemeProvider>
      <AuthProvider>
        <Router>
          <Toaster />
            
            {/* Simplified App - no conditional marketing links needed */}
            
            {/* Global League Creation Success Marker */}
            <LeagueCreateSuccessMarker />
            
            {/* Routes - Simplified App-Only Structure */}
            <Routes>
              {/* Login Route - Standalone without shell wrapper */}
              <Route path="/login" element={
                <RedirectIfAuthed>
                  <LoginPage />
                </RedirectIfAuthed>
              } />
              
              {/* Root Route - Direct redirect to login or app */}
              <Route path="/" element={<AppRootRedirect />} />
              
              {/* Auth verification without shell */}
              <Route path="/auth/verify" element={<MagicLinkVerify />} />
              
              {/* App Shell Routes - Require authentication */}
              <Route path="/invite" element={
                <RequireAuth>
                  <AppShell>
                    <InvitationAccept />
                  </AppShell>
                </RequireAuth>
              } />
              <Route path="/auction/:auctionId" element={
                <RequireAuth>
                  <AppShell showBackButton={true} pageTitle="Auction Room">
                    <AuctionLayout>
                      <AuctionRoomWrapper />
                    </AuctionLayout>
                  </AppShell>
                </RequireAuth>
              } />
              <Route path="/clubs" element={
                <RequireAuth>
                  <AppShell showBackButton={true} pageTitle="My Roster">
                    <RosterLayout>
                      <MyClubsWrapper />
                    </RosterLayout>
                  </AppShell>
                </RequireAuth>
              } />
              <Route path="/fixtures" element={
                <RequireAuth>
                  <AppShell showBackButton={true} pageTitle="Fixtures">
                    <FixturesLayout>
                      <FixturesWrapper />
                    </FixturesLayout>
                  </AppShell>
                </RequireAuth>
              } />
              <Route path="/leaderboard" element={
                <RequireAuth>
                  <AppShell showBackButton={true} pageTitle="Leaderboard">
                    <LeaderboardLayout>
                      <LeaderboardWrapper />
                    </LeaderboardLayout>
                  </AppShell>
                </RequireAuth>
              } />
              <Route path="/admin" element={
                <RequireAuth>
                  <AppShell showBackButton={true} pageTitle="League Settings">
                    <AdminLayout>
                      <AdminDashboardWrapper />
                    </AdminLayout>
                  </AppShell>
                </RequireAuth>
              } />
              <Route path="/dashboard" element={
                <RequireAuth>
                  <AppShell showBackButton={false} pageTitle="Dashboard">
                    <Dashboard />
                  </AppShell>
                </RequireAuth>
              } />
              <Route path="/app" element={
                <RequireAuth>
                  <AppShell showBackButton={false} pageTitle="Dashboard">
                    <Dashboard />
                  </AppShell>
                </RequireAuth>
              } />
              {/* League Creation Route - Dedicated Page */}
              <Route path="/app/leagues/new" element={
                <RequireAuth>
                  <AppShell showBackButton={true} pageTitle="Create New League">
                    <LeagueCreationPage />
                  </AppShell>
                </RequireAuth>
              } />
              
              {/* League Lobby Route */}
              <Route path="/app/leagues/:id/lobby" element={
                <RequireAuth>
                  <AppShell showBackButton={true} pageTitle="League Lobby">
                    <LeagueLobby />
                  </AppShell>
                </RequireAuth>
              } />
              {/* Utility routes without specific shell */}
              <Route path="/diag" element={<DiagnosticPage />} />
              
              {/* League Join Route */}
              <Route path="/join/:leagueId" element={
                <RequireAuth>
                  <AppShell>
                    <LeagueJoin />
                  </AppShell>
                </RequireAuth>
              } />
              
              {/* 404 - Catch all unmatched routes */}
              <Route path="*" element={
                <AppShell>
                  <NotFoundPage />
                </AppShell>
              } />
            </Routes>
        </Router>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
