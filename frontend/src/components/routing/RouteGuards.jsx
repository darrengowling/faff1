/**
 * Route Guards for Authentication and League-based Access Control
 * 
 * Provides safe redirects with user-friendly messages and no dead-ends
 */

import React, { useEffect } from 'react';
import { Navigate, useLocation, useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { useAuth } from '../../App';

/**
 * Authentication Guard - Requires user to be logged in
 */
export const AuthGuard = ({ children }) => {
  const { user, loading } = useAuth();
  const location = useLocation();

  // Show loading state while checking authentication
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Checking authentication...</p>
        </div>
      </div>
    );
  }

  // If not authenticated, redirect to login with toast
  if (!user) {
    // Show toast notification
    toast.error('Please sign in to access this page', {
      duration: 4000,
      data: { testid: 'auth-required-toast' }
    });

    // Redirect to login with return path
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return children;
};

/**
 * League Guard - Requires user to have an active league
 */
export const LeagueGuard = ({ children, fallbackPath = '/app', reason = 'You need to select a league first' }) => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  
  // Mock league state - in real app this would come from state management
  const [selectedLeague, setSelectedLeague] = React.useState(null);
  const [leagues, setLeagues] = React.useState([]);

  // Mock: Check if user has leagues and a selected league
  useEffect(() => {
    if (user) {
      // In real app, fetch user's leagues here
      // For now, simulate no leagues or no selected league
      const hasLeagues = Math.random() > 0.7; // 30% chance of having leagues
      
      if (hasLeagues) {
        setLeagues([
          { id: 'league-1', name: 'Demo League', status: 'active' }
        ]);
        setSelectedLeague({ id: 'league-1', name: 'Demo League', status: 'active' });
      }
    }
  }, [user]);

  // If user has no active league, redirect with reason
  if (user && !selectedLeague) {
    // Show toast with specific reason
    toast.info(reason, {
      duration: 4000,
      action: {
        label: 'Create League',
        onClick: () => navigate('/app')
      },
      data: { testid: 'league-required-toast' }
    });

    // Redirect to app home where they can create/join a league
    return <Navigate to={fallbackPath} replace />;
  }

  return children;
};

/**
 * Public Route - Accessible without authentication
 */
export const PublicRoute = ({ children }) => {
  return children;
};

/**
 * Protected Route - Combines Auth + League guards with custom logic
 */
export const ProtectedRoute = ({ 
  children, 
  requireLeague = false,
  fallbackPath = '/app',
  redirectReason = 'Access restricted'
}) => {
  // First check authentication
  const AuthenticatedComponent = (
    <AuthGuard>
      {requireLeague ? (
        <LeagueGuard fallbackPath={fallbackPath} reason={redirectReason}>
          {children}
        </LeagueGuard>
      ) : (
        children
      )}
    </AuthGuard>
  );

  return AuthenticatedComponent;
};

/**
 * Route wrapper with redirect logic for specific route patterns
 */
export const SafeRoute = ({ 
  children,
  path,
  authRequired = false,
  leagueRequired = false
}) => {
  const { user } = useAuth();
  const location = useLocation();

  // Define route-specific redirect logic
  const getRedirectInfo = () => {
    if (!authRequired && !leagueRequired) {
      return null; // Public route
    }

    if (authRequired && !user) {
      return {
        to: '/login',
        reason: 'Please sign in to access this page',
        toastType: 'error'
      };
    }

    if (leagueRequired && user) {
      // Check league-specific routes
      if (path?.includes('/auction')) {
        return {
          to: '/app',
          reason: 'Join a league first to access the auction room',
          toastType: 'info'
        };
      }
      
      if (path?.includes('/clubs')) {
        return {
          to: '/app',
          reason: 'Join a league first to view your roster',
          toastType: 'info'
        };
      }

      if (path?.includes('/fixtures')) {
        return {
          to: '/app',
          reason: 'Join a league first to view fixtures',
          toastType: 'info'
        };
      }

      if (path?.includes('/leaderboard')) {
        return {
          to: '/app',
          reason: 'Join a league first to view the leaderboard',
          toastType: 'info'
        };
      }

      if (path?.includes('/admin')) {
        return {
          to: '/app',
          reason: 'League admin access requires commissioner permissions',
          toastType: 'warning'
        };
      }
    }

    return null;
  };

  const redirectInfo = getRedirectInfo();

  if (redirectInfo) {
    // Show appropriate toast
    const toastMethod = redirectInfo.toastType === 'error' ? toast.error : 
                       redirectInfo.toastType === 'warning' ? toast.warning : toast.info;
    
    toastMethod(redirectInfo.reason, {
      duration: 4000,
      data: { testid: `redirect-toast-${redirectInfo.toastType}` }
    });

    return <Navigate to={redirectInfo.to} state={{ from: location }} replace />;
  }

  return children;
};

export default {
  AuthGuard,
  LeagueGuard,
  PublicRoute,
  ProtectedRoute,
  SafeRoute
};