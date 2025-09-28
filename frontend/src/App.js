import React, { useState, useEffect, createContext, useContext } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom';
import axios from 'axios';
import { Toaster, toast } from 'sonner';
import './App.css';
import './styles/mobile-optimizations.css';

// Initialize i18n
import './i18n';
import { useTranslation } from 'react-i18next';
import { TESTIDS } from './testids.js';
import { ThemeProvider } from './theme/ThemeProvider';
import { getBrandName } from './brand';
import { AuthBrand } from './components/ui/brand-badge.jsx';

// Import components
import AuctionRoom from './components/AuctionRoom';
import MyClubs from './components/MyClubs';
import Fixtures from './components/Fixtures';
import Leaderboard from './components/Leaderboard';
import AdminDashboard from './components/AdminDashboard';
import DiagnosticPage from './components/DiagnosticPage';
import LandingPage from './components/LandingPage';
import LoginPage from './components/LoginPage';
import SimpleLandingPage from './components/SimpleLandingPage';
import CreateLeagueWizard from './components/CreateLeagueWizard';
import { SafeRoute } from './components/routing/RouteGuards';
import GlobalNavbar from './components/GlobalNavbar';
import StickyPageNav from './components/StickyPageNav';
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
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from './components/ui/dialog';
import { Label } from './components/ui/label';
import { Separator } from './components/ui/separator';
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from './components/ui/alert-dialog';

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

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

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
      setLoading(false);
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

  return (
    <AuthContext.Provider value={{ user, login, logout, loading }}>
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
        setMagicLink(response.data.dev_magic_link);
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
        navigate('/app');
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

// Enhanced League Creation Dialog
const CreateLeagueDialog = ({ open, onOpenChange, onLeagueCreated }) => {
  const { t } = useTranslation();
  const [competitionProfiles, setCompetitionProfiles] = useState([]);
  const [selectedProfile, setSelectedProfile] = useState('ucl');
  const [formData, setFormData] = useState({
    name: '',
    season: '2025-26',
    settings: {
      budget_per_manager: 100,
      min_increment: 1,
      club_slots_per_manager: 5,  // Default to 5 instead of 3
      anti_snipe_seconds: 30,
      bid_timer_seconds: 60,
      league_size: { min: 2, max: 8 },  // Default to min: 2, max: 8
      scoring_rules: {
        club_goal: 1,
        club_win: 3,
        club_draw: 1
      }
    }
  });
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState('');
  const [justCreatedId, setJustCreatedId] = useState(null);

  // Validation functions
  const validateForm = () => {
    const newErrors = {};
    
    // Name validation
    if (!formData.name.trim()) {
      newErrors.name = 'League name is required';
    } else if (formData.name.trim().length < 3) {
      newErrors.name = 'League name must be at least 3 characters';
    }
    
    // Budget validation
    const budget = parseInt(formData.settings.budget_per_manager);
    if (isNaN(budget) || budget < 50) {
      newErrors.budget = 'Budget must be at least £50';
    } else if (budget > 500) {
      newErrors.budget = 'Budget cannot exceed £500';
    }
    
    // Slots validation
    const slots = parseInt(formData.settings.club_slots_per_manager);
    if (isNaN(slots) || slots < 1) {
      newErrors.slots = 'Must have at least 1 club slot';
    } else if (slots > 10) {
      newErrors.slots = 'Cannot exceed 10 club slots';
    }
    
    // Min managers validation
    const minManagers = parseInt(formData.settings.league_size?.min || 2);
    if (isNaN(minManagers) || minManagers < 2) {
      newErrors.min = 'Must have at least 2 managers';
    } else if (minManagers > 8) {
      newErrors.min = 'Cannot exceed 8 managers';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Clear specific error when user starts typing
  const clearError = (field) => {
    if (errors[field]) {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[field];
        return newErrors;
      });
    }
  };

  // Fetch competition profiles on component mount
  useEffect(() => {
    const fetchCompetitionProfiles = async () => {
      try {
        const response = await axios.get(`${API}/competition-profiles`);
        setCompetitionProfiles(response.data.profiles || []);
      } catch (error) {
        console.error('Failed to fetch competition profiles:', error);
        toast.error('Failed to load competition templates');
        setCompetitionProfiles([]); // Ensure it stays an array on error
      }
    };

    if (open) {
      fetchCompetitionProfiles();
    }
  }, [open]);

  // Update form data when selected profile changes
  useEffect(() => {
    if (selectedProfile && competitionProfiles.length > 0) {
      const profile = competitionProfiles.find(p => p._id === selectedProfile);
      if (profile && profile.defaults) {
        setFormData(prev => ({
          ...prev,
          settings: {
            ...prev.settings,
            budget_per_manager: profile.defaults.budget_per_manager,
            club_slots_per_manager: profile.defaults.club_slots,
            league_size: profile.defaults.league_size,
            min_increment: profile.defaults.min_increment,
            anti_snipe_seconds: profile.defaults.anti_snipe_seconds,
            bid_timer_seconds: profile.defaults.bid_timer_seconds,
            scoring_rules: profile.defaults.scoring_rules
          }
        }));
      }
    }
  }, [selectedProfile, competitionProfiles]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Validate form before submission
    if (!validateForm()) {
      return;
    }
    
    setSubmitting(true);
    setSubmitError(''); // Clear previous errors
    setErrors({}); // Clear field errors

    try {
      const response = await axios.post(`${API}/leagues`, formData);
      
      if (response.status === 201) {
        // Close the dialog and navigate (both)
        onOpenChange(false); // This should set data-state="closed"
        
        // Set success marker for tests
        setJustCreatedId(response.data.leagueId);
        
        // Navigate to lobby after a brief delay
        setTimeout(() => {
          window.location.href = `/app/leagues/${response.data.leagueId}/lobby`;
        }, 0);
        
        // Reset form and notify
        setFormData({
          name: '',
          season: '2025-26',
          settings: {
            budget_per_manager: 100,
            min_increment: 1,
            club_slots_per_manager: 5,
            anti_snipe_seconds: 30,
            bid_timer_seconds: 60,
            league_size: { min: 2, max: 8 },
            scoring_rules: {
              club_goal: 1,
              club_win: 3,
              club_draw: 1
            }
          }
        });
        setErrors({});
        
        // Call the callback with new data
        onLeagueCreated && onLeagueCreated(response.data);
        
        toast.success(t('leagueCreation.leagueCreatedSuccess'));
        
      } else {
        // Handle non-201 responses
        const errorMessage = response.data?.message || 'Could not create league';
        setSubmitError(errorMessage);
      }
      
    } catch (error) {
      console.error('League creation error:', error);
      
      // Handle structured error responses
      if (error.response?.status === 400) {
        const errorData = error.response.data;
        
        if (errorData.field) {
          // Field-specific error
          setErrors({ [errorData.field]: errorData.message });
        } else {
          // General validation error
          setSubmitError(errorData.message || 'Validation failed');
        }
      } else if (error.response?.status === 500) {
        const errorData = error.response.data;
        setSubmitError(`Server error${errorData.requestId ? ` (${errorData.requestId})` : ''}: ${errorData.message || 'Internal error'}`);
      } else {
        // Network or other errors
        setSubmitError(error.response?.data?.message || 'Could not create league');
      }
      
    } finally {
      setSubmitting(false);
    }
  };

  const updateSettings = (key, value) => {
    setFormData(prev => ({
      ...prev,
      settings: {
        ...prev.settings,
        [key]: parseInt(value) || value
      }
    }));
  };

  const updateScoringRules = (key, value) => {
    setFormData(prev => ({
      ...prev,
      settings: {
        ...prev.settings,
        scoring_rules: {
          ...prev.settings.scoring_rules,
          [key]: parseInt(value) || 0
        }
      }
    }));
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto" data-testid={TESTIDS.createDialog}>
        <DialogHeader>
          {/* Breadcrumb Navigation */}
          <div className="flex items-center space-x-2 text-sm text-gray-500 mb-2">
            <button
              type="button"
              onClick={() => onOpenChange(false)}
              className="text-blue-600 hover:text-blue-800 hover:underline"
              data-testid="breadcrumb-home"
            >
              Home
            </button>
            <span>/</span>
            <span className="text-gray-900 font-medium">New League</span>
          </div>
          <DialogTitle>{t('leagueCreation.createNewLeague')}</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Basic Info */}
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name">{t('leagueCreation.leagueName')}</Label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e) => {
                  setFormData(prev => ({ ...prev, name: e.target.value }));
                  clearError('name');
                }}
                required
                aria-describedby={errors.name ? "name-error" : undefined}
                className={errors.name ? 'border-red-500 focus:border-red-500 focus:ring-red-500' : ''}
                data-testid="create-name"
              />
              {errors.name && (
                <p id="name-error" className="text-sm text-red-600" data-testid="create-error-name">
                  {errors.name}
                </p>
              )}
            </div>
            <div className="space-y-2">
              <Label htmlFor="season">{t('dashboard.season')}</Label>
              <Input
                id="season"
                placeholder="2025-26"
                value={formData.season}
                onChange={(e) => setFormData(prev => ({ ...prev, season: e.target.value }))}
                required
              />
            </div>
            
            {/* Competition Profile Selection */}
            <div className="space-y-2">
              <Label htmlFor="profile">Competition Template</Label>
              <select
                id="profile"
                className="w-full p-2 border border-gray-300 rounded-md"
                value={selectedProfile}
                onChange={(e) => setSelectedProfile(e.target.value)}
              >
                {Array.isArray(competitionProfiles) && competitionProfiles.map(profile => (
                  <option key={profile._id} value={profile._id}>
                    {profile.competition} ({profile.short_name}) - {profile.defaults.club_slots} slots
                  </option>
                ))}
              </select>
              <p className="text-sm text-gray-600">
                Choose a template to set default values. You can customize them below.
              </p>
            </div>
          </div>

          <Separator />

          {/* League Settings */}
          <div className="space-y-4">
            <h4 className="font-medium text-gray-900">League Settings</h4>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="budget">Budget per Manager (£)</Label>
                <Input
                  id="budget"
                  type="number"
                  min="50"
                  max="500"
                  value={formData.settings.budget_per_manager}
                  onChange={(e) => {
                    updateSettings('budget_per_manager', e.target.value);
                    clearError('budget');
                  }}
                  aria-describedby={errors.budget ? "budget-error" : undefined}
                  className={errors.budget ? 'border-red-500 focus:border-red-500 focus:ring-red-500' : ''}
                  data-testid="create-budget"
                />
                {errors.budget && (
                  <p id="budget-error" className="text-sm text-red-600" data-testid="create-error-budget">
                    {errors.budget}
                  </p>
                )}
              </div>
              <div className="space-y-2">
                <Label htmlFor="slots">Club Slots per Manager</Label>
                <Input
                  id="slots"
                  type="number"
                  min="1"
                  max="10"
                  value={formData.settings.club_slots_per_manager}
                  onChange={(e) => {
                    updateSettings('club_slots_per_manager', e.target.value);
                    clearError('slots');
                  }}
                  aria-describedby={errors.slots ? "slots-error" : undefined}
                  className={errors.slots ? 'border-red-500 focus:border-red-500 focus:ring-red-500' : ''}
                  data-testid="create-slots-input"
                />
                {errors.slots && (
                  <p id="slots-error" className="text-sm text-red-600" data-testid="create-error-slots">
                    {errors.slots}
                  </p>
                )}
              </div>
              <div className="space-y-2">
                <Label htmlFor="minIncrement">Min Bid Increment</Label>
                <Input
                  id="minIncrement"
                  type="number"
                  min="1"
                  max="10"
                  value={formData.settings.min_increment}
                  onChange={(e) => updateSettings('min_increment', e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="bidTimer">Bid Timer (seconds)</Label>
                <Input
                  id="bidTimer"
                  type="number"
                  min="30"
                  max="300"
                  value={formData.settings.bid_timer_seconds}
                  onChange={(e) => updateSettings('bid_timer_seconds', e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="minManagers">Min Managers</Label>
                <Input
                  id="minManagers"
                  type="number"
                  min="2"
                  max="8"
                  value={formData.settings.league_size?.min || 2}
                  onChange={(e) => {
                    updateSettings('league_size', { 
                      ...formData.settings.league_size, 
                      min: parseInt(e.target.value) || 2 
                    });
                    clearError('min');
                  }}
                  aria-describedby={errors.min ? "min-error" : undefined}
                  className={errors.min ? 'border-red-500 focus:border-red-500 focus:ring-red-500' : ''}
                  data-testid="create-min"
                />
                {errors.min && (
                  <p id="min-error" className="text-sm text-red-600" data-testid="create-error-min">
                    {errors.min}
                  </p>
                )}
              </div>
              <div className="space-y-2">
                <Label htmlFor="maxManagers">Max Managers</Label>
                <Input
                  id="maxManagers"
                  type="number"
                  min="2"
                  max="8"
                  value={formData.settings.league_size?.max || 8}
                  onChange={(e) => updateSettings('league_size', { 
                    ...formData.settings.league_size, 
                    max: parseInt(e.target.value) || 8 
                  })}
                  data-testid={TESTIDS.createMaxInput}
                />
              </div>
            </div>
          </div>

          <Separator />

          {/* Scoring Rules */}
          <div className="space-y-4">
            <h4 className="font-medium text-gray-900">Scoring Rules</h4>
            <div className="grid grid-cols-3 gap-4">
              <div className="space-y-2">
                <Label htmlFor="goalPoints">Points per Goal</Label>
                <Input
                  id="goalPoints"
                  type="number"
                  min="0"
                  max="10"
                  value={formData.settings.scoring_rules.club_goal}
                  onChange={(e) => updateScoringRules('club_goal', e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="winPoints">Points per Win</Label>
                <Input
                  id="winPoints"
                  type="number"
                  min="0"
                  max="10"
                  value={formData.settings.scoring_rules.club_win}
                  onChange={(e) => updateScoringRules('club_win', e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="drawPoints">Points per Draw</Label>
                <Input
                  id="drawPoints"
                  type="number"
                  min="0"
                  max="10"
                  value={formData.settings.scoring_rules.club_draw}
                  onChange={(e) => updateScoringRules('club_draw', e.target.value)}
                />
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex space-x-2 pt-4">
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              className="flex-1"
              data-testid={TESTIDS.createCancel}
            >
              Cancel
            </Button>
            <Button 
              type="submit" 
              className="flex-1" 
              disabled={loading || Object.keys(errors).length > 0} 
              data-testid="create-submit"
            >
              {loading ? 'Creating...' : 'Create League'}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
};

// League Management Component
const LeagueManagement = ({ league, onBack }) => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [members, setMembers] = useState([]);
  const [invitations, setInvitations] = useState([]);
  const [leagueStatus, setLeagueStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteLoading, setInviteLoading] = useState(false);

  const isCommissioner = league.commissioner_id === user.id;

  useEffect(() => {
    fetchLeagueData();
  }, [league.id]);

  const fetchLeagueData = async () => {
    try {
      const [membersRes, statusRes, invitationsRes] = await Promise.all([
        axios.get(`${API}/leagues/${league.id}/members`),
        axios.get(`${API}/leagues/${league.id}/status`),
        isCommissioner ? axios.get(`${API}/leagues/${league.id}/invitations`) : Promise.resolve({ data: [] })
      ]);

      setMembers(membersRes.data);
      setLeagueStatus(statusRes.data);
      setInvitations(invitationsRes.data);
    } catch (error) {
      toast.error('Failed to load league data');
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
    <div className="space-y-6">
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

      {/* League Status */}
      {leagueStatus && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Shield className="w-5 h-5" />
              <span>League Status</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600" data-testid={TESTIDS.lobbyJoinedCount}>{leagueStatus.member_count}</div>
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
                          onClick={() => navigator.clipboard.writeText(`${window.location.origin}/join/${league._id}`)}
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

  if (selectedLeague) {
    return (
      <div className="min-h-screen bg-gray-50">
        <header className="bg-white shadow-sm border-b">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center h-16">
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
                  <Trophy className="w-5 h-5 text-white" />
                </div>
                <h1 className="text-xl font-bold text-gray-900">{t('nav.appName', { brandName: getBrandName() })}</h1>
              </div>
              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-2">
                  <User className="w-4 h-4 text-gray-600" />
                  <span className="text-sm text-gray-700">{user.display_name}</span>
                </div>
                <Button variant="outline" size="sm" onClick={logout}>
                  <LogOut className="w-4 h-4 mr-2" />
                  Logout
                </Button>
              </div>
            </div>
          </div>
        </header>
        <main className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
          <LeagueManagement 
            league={selectedLeague} 
            onBack={() => setSelectedLeague(null)} 
          />
        </main>
      </div>
    );
  }

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

// Smart Root Route Component
const RootRoute = () => {
  const { user, loading } = useAuth();
  
  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <div className="animate-spin w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full"></div>
      </div>
    );
  }
  
  // If user is logged in, redirect to dashboard (/app)
  if (user) {
    return <Navigate to="/app" replace />;
  }
  
  // If user is not logged in, show landing page
  return <SimpleLandingPage />;
};

// Main App Component
function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <Router>
          <div className="App">
            <Toaster />
            {/* Global Navigation */}
            <GlobalNavbar />
            
            {/* Sticky Page Navigation - only shows on landing page */}
            <StickyPageNav />
            
            {/* Main Content */}
            <main id="main-content" className="min-h-screen">
              <Routes>
              <Route path="/login" element={<LoginPage />} />
              <Route path="/auth/verify" element={<MagicLinkVerify />} />
              <Route path="/invite" element={
                <ProtectedRoute>
                  <InvitationAccept />
                </ProtectedRoute>
              } />
              <Route path="/auction/:auctionId" element={
                <SafeRoute path="/auction/:auctionId" authRequired={true} leagueRequired={true}>
                  <AuctionLayout>
                    <AuctionRoomWrapper />
                  </AuctionLayout>
                </SafeRoute>
              } />
              <Route path="/clubs" element={
                <SafeRoute path="/clubs" authRequired={true} leagueRequired={true}>
                  <RosterLayout>
                    <MyClubsWrapper />
                  </RosterLayout>
                </SafeRoute>
              } />
              <Route path="/fixtures" element={
                <SafeRoute path="/fixtures" authRequired={true} leagueRequired={true}>
                  <FixturesLayout>
                    <FixturesWrapper />
                  </FixturesLayout>
                </SafeRoute>
              } />
              <Route path="/leaderboard" element={
                <SafeRoute path="/leaderboard" authRequired={true} leagueRequired={true}>
                  <LeaderboardLayout>
                    <LeaderboardWrapper />
                  </LeaderboardLayout>
                </SafeRoute>
              } />
              <Route path="/admin" element={
                <SafeRoute path="/admin" authRequired={true} leagueRequired={true}>
                  <AdminLayout>
                    <AdminDashboardWrapper />
                  </AdminLayout>
                </SafeRoute>
              } />
              <Route path="/dashboard" element={
                <ProtectedRoute>
                  <DashboardLayout>
                    <Dashboard />
                  </DashboardLayout>
                </ProtectedRoute>
              } />
              <Route path="/app" element={
                <ProtectedRoute>
                  <DashboardLayout>
                    <Dashboard />
                  </DashboardLayout>
                </ProtectedRoute>
              } />
              <Route path="/app/leagues/new" element={
                <SafeRoute path="/app/leagues/new" authRequired={true}>
                  <CreateLeagueWizard />
                </SafeRoute>
              } />
              <Route path="/diag" element={<DiagnosticPage />} />
              <Route path="/" element={<RootRoute />} />
              {/* 404 - Catch all unmatched routes */}
              <Route path="*" element={<NotFoundPage />} />
              </Routes>
            </main>
          </div>
        </Router>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
