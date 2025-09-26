/**
 * AppLayout Component
 * 
 * Consistent layout wrapper for all authenticated in-app routes
 * Includes: brand header, global navbar, footer, and "Back to Home" button
 */

import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { 
  Home, ChevronLeft, ArrowLeft, Trophy
} from 'lucide-react';
import { Button } from '../ui/button';
import GlobalNavbar from '../GlobalNavbar';
import { InAppFooter } from '../ui/footer';
import { getBrandName } from '../../brand';
import { useAuth } from '../../App';

const AppLayout = ({ children, showBackButton = true, pageTitle = null }) => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();
  const { user } = useAuth();

  // Determine if we're on the home/dashboard page
  const isHomePage = location.pathname === '/app' || location.pathname === '/dashboard';

  // Generate breadcrumb based on current route
  const generateBreadcrumb = () => {
    const path = location.pathname;
    const segments = path.split('/').filter(Boolean);
    
    // Map route segments to readable names
    const routeNames = {
      'app': 'Dashboard',
      'dashboard': 'Dashboard', 
      'auction': 'Auction Room',
      'clubs': 'My Roster',
      'fixtures': 'Fixtures',
      'leaderboard': 'Leaderboard',
      'admin': 'League Settings'
    };
    
    if (segments.length <= 1) {
      return 'Dashboard';
    }
    
    const lastSegment = segments[segments.length - 1];
    const secondLastSegment = segments[segments.length - 2];
    
    return routeNames[secondLastSegment] || routeNames[lastSegment] || 'Page';
  };

  const handleBackToHome = () => {
    navigate('/app');
  };

  const currentPageName = pageTitle || generateBreadcrumb();

  return (
    <div className="min-h-screen bg-theme-surface-secondary flex flex-col">
      {/* Global Navigation Header */}
      <GlobalNavbar />
      
      {/* App Header with Back Button and Breadcrumb */}
      <header className="bg-theme-surface border-b border-theme-surface-border shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-14">
            
            {/* Left Side: Back Button + Breadcrumb */}
            <div className="flex items-center space-x-3">
              {/* Mobile Back Button (small screens) */}
              {showBackButton && !isHomePage && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleBackToHome}
                  className="flex items-center space-x-1 md:hidden hover:bg-theme-surface-tertiary"
                  aria-label="Back to Home"
                >
                  <ArrowLeft className="w-4 h-4" />
                  <span className="text-sm">Home</span>
                </Button>
              )}

              {/* Desktop Breadcrumb (larger screens) */}
              <div className="hidden md:flex items-center space-x-2 text-sm" aria-label="Breadcrumb">
                {showBackButton && !isHomePage && (
                  <>
                    <button
                      onClick={handleBackToHome}
                      className="flex items-center space-x-1 text-theme-text-secondary hover:text-theme-primary transition-colors focus:outline-none focus:ring-2 focus:ring-theme-primary focus:ring-offset-2 rounded px-1"
                      aria-label="Navigate to Dashboard"
                    >
                      <Home className="w-4 h-4" />
                      <span>Dashboard</span>
                    </button>
                    <ChevronLeft className="w-4 h-4 text-theme-text-tertiary rotate-180" />
                  </>
                )}
                <span className="font-medium text-theme-text" aria-current="page">
                  {currentPageName}
                </span>
              </div>

              {/* Current page title for mobile when on home page */}
              {isHomePage && (
                <div className="flex items-center space-x-2 md:hidden">
                  <div className="w-6 h-6 bg-theme-primary rounded-full flex items-center justify-center">
                    <Trophy className="w-4 h-4 text-theme-primary-contrast" />
                  </div>
                  <h1 className="text-lg font-semibold text-theme-text">
                    {getBrandName()}
                  </h1>
                </div>
              )}
            </div>

            {/* Right Side: User Info (optional) */}
            <div className="flex items-center space-x-3">
              {user && (
                <div className="hidden sm:flex items-center space-x-2 text-sm text-theme-text-secondary">
                  <span className="font-medium">{user.display_name}</span>
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 relative">
        {children}
      </main>

      {/* Footer */}
      <InAppFooter />
      
      {/* Back to Top Button for long pages */}
      <button
        onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
        className="fixed bottom-6 right-6 w-12 h-12 bg-theme-primary text-theme-primary-contrast rounded-full shadow-lg hover:shadow-xl transition-all duration-200 opacity-0 hover:opacity-100 focus:opacity-100 z-20"
        aria-label="Back to top"
        onMouseEnter={(e) => e.target.style.opacity = '1'}
        onMouseLeave={(e) => e.target.style.opacity = '0'}
      >
        <ChevronLeft className="w-5 h-5 mx-auto -rotate-90" />
      </button>
    </div>
  );
};

// Specialized layout variants for different contexts
export const DashboardLayout = ({ children }) => (
  <AppLayout showBackButton={false} pageTitle="Dashboard">
    {children}
  </AppLayout>
);

export const AuctionLayout = ({ children }) => (
  <AppLayout pageTitle="Auction Room">
    {children}
  </AppLayout>
);

export const AdminLayout = ({ children }) => (
  <AppLayout pageTitle="League Settings">
    {children}
  </AppLayout>
);

export const RosterLayout = ({ children }) => (
  <AppLayout pageTitle="My Roster">
    {children}
  </AppLayout>
);

export const FixturesLayout = ({ children }) => (
  <AppLayout pageTitle="Fixtures">
    {children}
  </AppLayout>
);

export const LeaderboardLayout = ({ children }) => (
  <AppLayout pageTitle="Leaderboard">
    {children}
  </AppLayout>
);

export default AppLayout;