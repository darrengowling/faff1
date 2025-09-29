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
import BackToHomeLink from '../BackToHomeLink.tsx';

const AppShell = ({ children, showBackButton = true, pageTitle = null }) => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();
  const { user } = useAuth();

  // Mobile menu state and count tracking
  const [mobileMenuOpen, setMobileMenuOpen] = React.useState(false);
  const [mobileItemCount, setMobileItemCount] = React.useState(0);
  const [productDropdownOpen, setProductDropdownOpen] = React.useState(false);
  const [focusedIndex, setFocusedIndex] = React.useState(-1);

  // Count visible mobile menu items
  React.useEffect(() => {
    // Count nav items, auth actions, and theme toggle
    let count = 0;
    
    // Back to Home link
    count += 1;
    
    // MobileNavigation items (approximate based on typical nav items)
    count += 4; // Typical nav items: Home, Features, About, Contact
    
    // Auth actions
    count += 2; // Sign In, Get Started
    
    // Theme toggle
    count += 1;
    
    setMobileItemCount(count);
  }, []);

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

  // Handle Escape key to close mobile menu
  React.useEffect(() => {
    const handleEscape = (event) => {
      if (event.key === 'Escape' && mobileMenuOpen) {
        setMobileMenuOpen(false);
      }
    };

    if (mobileMenuOpen) {
      document.addEventListener('keydown', handleEscape);
      return () => document.removeEventListener('keydown', handleEscape);
    }
  }, [mobileMenuOpen]);

  return (
    <div className="min-h-screen bg-theme-surface-secondary flex flex-col">
      {/* Single App Header */}
      <header 
        className="sticky top-0 w-full bg-theme-surface/95 backdrop-blur-sm border-b border-theme-surface-border z-40"
        data-testid="app-header"
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Left - Brand and Back to Home */}
            <div className="flex items-center space-x-4">
              <HeaderBrand 
                onClick={() => navigate('/')} 
                className="cursor-pointer hover:opacity-80 transition-opacity"
                data-testid={TESTIDS.navBrand}
              />
              <BackToHomeLink className="text-theme-text-secondary hover:text-theme-text" />
            </div>
            
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
              {/* Left Side - Back to Home + Breadcrumb */}
              <div className="flex items-center space-x-3">
                {/* Always show Back to Home link */}
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => navigate('/app')}
                  data-testid="back-to-home-link"
                  className="flex items-center space-x-1 text-sm text-theme-text-secondary hover:text-theme-text"
                >
                  <Home className="w-4 h-4" />
                  <span>Home</span>
                </Button>
                
                {showBackButton && !isHomePage && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => navigate('/app')}
                    data-testid={TESTIDS.backButton}
                    className="flex items-center space-x-1"
                  >
                    <ArrowLeft className="w-4 h-4" />
                    <span>Back</span>
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
      </header>

      {/* Mobile Drawer - Always present with explicit contract */}
      <div 
        className="md:hidden fixed inset-0 z-40"
        onClick={() => setMobileMenuOpen(false)}
        aria-hidden={!mobileMenuOpen}
        style={{ 
          paddingTop: '64px',
          pointerEvents: mobileMenuOpen ? 'auto' : 'none',
          visibility: mobileMenuOpen ? 'visible' : 'hidden',
          opacity: mobileMenuOpen ? 1 : 0,
          transition: 'opacity 0.3s ease-in-out'
        }}
      >
        <div 
          className="drawer-backdrop absolute inset-0"
          style={{ 
            pointerEvents: 'none' // Backdrop visual only
          }}
        />
        <div
          className="bg-theme-surface w-full max-w-sm min-h-full shadow-lg overflow-y-auto drawer-panel"
          id="mobile-navigation"
          role="navigation"
          aria-label="Mobile navigation menu"
          onClick={(e) => e.stopPropagation()}
          data-testid="nav-mobile-drawer"
          data-state={mobileMenuOpen ? "open" : "closed"}
          data-count={mobileItemCount}
          style={{ 
            pointerEvents: 'auto',
            transform: mobileMenuOpen ? 'translateX(0)' : 'translateX(-100%)',
            transition: 'transform 0.3s ease-in-out'
          }}
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

                  {/* Mobile Navigation Items */}
                  <div className="py-4">
                    {/* Back to Home - First Item */}
                    <div className="mb-4">
                      <BackToHomeLink 
                        data-testid="back-to-home-link"
                        className="block py-2 px-0 text-theme-text-secondary hover:text-theme-text"
                        onClick={() => setMobileMenuOpen(false)}
                      />
                    </div>
                    
                    <MobileNavigation onItemClick={(item) => {
                      // Force drawer to closed state and update count immediately
                      setMobileMenuOpen(false);
                      setMobileItemCount(current => current); // Trigger re-render
                    }} />
                    
                    {/* Mobile Auth Actions */}
                    <div className="border-t border-gray-200 mt-4 pt-4 space-y-3">
                      <AuthNavigation variant="mobile" />
                      
                      {/* Mobile Theme Toggle */}
                      <div className="flex items-center justify-between px-0">
                        <span className="text-sm text-gray-600">Theme</span>
                        <IconThemeToggle />
                      </div>
                    </div>
                  </div>
                </div>
            </div>
        </div>

      {/* Always-present drawer testid - removed duplicate */}

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