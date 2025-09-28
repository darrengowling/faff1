/**
 * AppShell Component
 * 
 * Single header layout shell for all authenticated pages
 * Ensures exactly one <header> element renders across all routes
 */

import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { 
  Home, ChevronLeft, ArrowLeft, Trophy, Menu, X
} from 'lucide-react';
import { Button } from '../ui/button';
import { InAppFooter } from '../ui/footer';
import { getBrandName } from '../../brand';
import { useAuth } from '../../App';
import { HeaderBrand } from '../ui/brand-badge';
import { ProductDropdownMenu } from '../navigation/ProductDropdownMenu';
import { AuthNavigation } from '../navigation/AuthNavigation';
import { MobileNavigation } from '../navigation/NavigationMenu';
import { IconThemeToggle } from '../ui/theme-toggle';
import { TESTIDS } from '../../testids';

const AppShell = ({ children, showBackButton = true, pageTitle = null }) => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();
  const { user } = useAuth();

  // Mobile menu state
  const [mobileMenuOpen, setMobileMenuOpen] = React.useState(false);
  const [productDropdownOpen, setProductDropdownOpen] = React.useState(false);
  const [focusedIndex, setFocusedIndex] = React.useState(-1);

  // Determine if we're on the home/dashboard page
  const isHomePage = location.pathname === '/app' || location.pathname === '/dashboard';

  // Generate breadcrumb based on current route
  const generateBreadcrumb = () => {
    const path = location.pathname;
    const segments = path.split('/').filter(Boolean);
    
    const routeNames = {
      'app': 'Dashboard',
      'dashboard': 'Dashboard', 
      'auction': 'Auction Room',
      'clubs': 'My Roster',
      'fixtures': 'Fixtures',
      'leaderboard': 'Leaderboard',
      'admin': 'League Settings',
      'leagues': 'Leagues',
      'new': 'Create League'
    };
    
    if (segments.length <= 1) {
      return 'Dashboard';
    }
    
    const lastSegment = segments[segments.length - 1];
    const secondLastSegment = segments[segments.length - 2];
    
    if (routeNames[lastSegment]) {
      return routeNames[lastSegment];
    }
    
    if (routeNames[secondLastSegment]) {
      return `${routeNames[secondLastSegment]} • ${lastSegment}`;
    }
    
    return segments.map(s => routeNames[s] || s).join(' • ');
  };

  const breadcrumb = pageTitle || generateBreadcrumb();

  // Handle product dropdown
  const handleProductDropdownToggle = () => {
    setProductDropdownOpen(!productDropdownOpen);
  };

  // Close dropdowns and mobile menu on route change
  React.useEffect(() => {
    setMobileMenuOpen(false);
    setProductDropdownOpen(false);
    setFocusedIndex(-1);
    
    // Ensure any persistent overlays are removed
    document.body.style.overflow = 'unset';
    
    // Remove any full-screen elements with pointer-events that might persist
    const persistentOverlays = document.querySelectorAll('.drawer-backdrop, [data-persistent-overlay]');
    persistentOverlays.forEach(overlay => {
      if (overlay.style.pointerEvents === 'auto' || overlay.classList.contains('drawer-backdrop')) {
        overlay.remove();
      }
    });
  }, [location.pathname]);

  return (
    <div className="min-h-screen bg-theme-surface-secondary flex flex-col">
      {/* Single App Header */}
      <header 
        className="sticky top-0 w-full bg-theme-surface/95 backdrop-blur-sm border-b border-theme-surface-border z-40"
        data-testid="app-header"
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Left - Brand */}
            <HeaderBrand 
              onClick={() => navigate('/')} 
              className="cursor-pointer hover:opacity-80 transition-opacity"
              data-testid={TESTIDS.navBrand}
            />
            
            {/* Center - Desktop Navigation */}
            <nav className="hidden md:flex items-center space-x-2" role="navigation">
              {/* Product Dropdown */}
              <ProductDropdownMenu
                isOpen={productDropdownOpen}
                onToggle={handleProductDropdownToggle}
                onClose={() => {
                  setProductDropdownOpen(false);
                  setFocusedIndex(-1);
                }}
              />
            </nav>

            {/* Right - Auth Actions */}
            <div className="hidden md:flex items-center space-x-3">
              {/* Create League Button (when authenticated) */}
              {user && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => navigate('/app/leagues/new')}
                  data-testid={TESTIDS.navCreateLeagueBtn}
                  className="flex items-center space-x-1 hover:bg-theme-accent hover:text-theme-accent-foreground transition-colors"
                >
                  <Trophy className="w-4 h-4" />
                  <span>Create League</span>
                </Button>
              )}
              
              <AuthNavigation variant="desktop" />
              
              {/* Theme Toggle */}
              <IconThemeToggle className="hidden md:flex" />
            </div>

            {/* Mobile Menu Button */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="md:hidden p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-md transition-colors"
              aria-label="Toggle navigation menu"
              aria-expanded={mobileMenuOpen}
              aria-controls="mobile-navigation"
              data-testid={TESTIDS.navHamburger}
            >
              {mobileMenuOpen ? (
                <X className="w-6 h-6" />
              ) : (
                <Menu className="w-6 h-6" />
              )}
            </button>
          </div>
        </div>

        {/* Breadcrumb Bar */}
        <div className="bg-theme-surface border-b border-theme-surface-border shadow-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between h-14">
              {/* Left Side - Back Button + Breadcrumb */}
              <div className="flex items-center space-x-3">
                {showBackButton && !isHomePage && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => navigate('/app')}
                    className="flex items-center space-x-1 text-gray-600 hover:text-gray-900 hover:bg-gray-100 transition-colors"
                    data-testid={TESTIDS.backToHomeBtn}
                  >
                    <ArrowLeft className="w-4 h-4" />
                    <span className="hidden sm:inline">Back to Dashboard</span>
                    <span className="sm:hidden">Back</span>
                  </Button>
                )}
                
                {/* Breadcrumb */}
                <div className="flex items-center space-x-2 text-sm">
                  <Home className="w-4 h-4 text-gray-400" />
                  <ChevronLeft className="w-4 h-4 text-gray-400" />
                  <span className="font-medium text-gray-900" data-testid={TESTIDS.breadcrumbCurrent}>
                    {breadcrumb}
                  </span>
                </div>
              </div>

              {/* Right Side - Additional Actions */}
              <div className="flex items-center space-x-3">
                {user && (
                  <div className="text-sm text-gray-600">
                    Welcome, <span className="font-medium text-gray-900">{user.email}</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Mobile Drawer */}
        {mobileMenuOpen && (
          <div 
            className="md:hidden fixed left-0 right-0 top-16 bottom-0 bg-black bg-opacity-50 z-40 drawer-backdrop"
            onClick={() => setMobileMenuOpen(false)}
            aria-hidden="true"
          >
            <div
              className="bg-theme-surface w-full max-w-sm h-full shadow-lg overflow-y-auto drawer-panel"
              id="mobile-navigation"
              role="navigation"
              aria-label="Mobile navigation menu"
              onClick={(e) => e.stopPropagation()}
              data-testid={TESTIDS.navMobileDrawer}
            >
              <div className="p-4">
                <div className="flex items-center justify-between mb-6">
                  <span className="text-lg font-semibold text-gray-900">Menu</span>
                  <button
                    onClick={() => setMobileMenuOpen(false)}
                    className="p-2 text-gray-400 hover:text-gray-600 rounded-md"
                    aria-label="Close menu"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>

                {/* Mobile Auth Navigation */}
                <AuthNavigation variant="mobile" />
              </div>
            </div>
          </div>
        )}
      </header>

      {/* Main Content */}
      <main className="flex-1">
        {children}
      </main>

      {/* Footer */}
      <InAppFooter />
    </div>
  );
};

export default AppShell;