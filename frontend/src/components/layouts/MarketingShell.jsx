/**
 * MarketingShell Component
 * 
 * Layout shell for marketing/unauthenticated pages (/, /login)
 * Ensures exactly one <header> element with proper spacing for login form
 */

import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Menu, X, Trophy, Home } from 'lucide-react';
import { Button } from '../ui/button';
import { HeaderBrand } from '../ui/brand-badge';
import { ProductDropdownMenu } from '../navigation/ProductDropdownMenu';
import { AuthNavigation } from '../navigation/AuthNavigation';
import { MobileNavigation } from '../navigation/NavigationMenu';
import { IconThemeToggle } from '../ui/theme-toggle';
import { TESTIDS } from '../../testids';
import { useAuth } from '../../App';
import BackToHomeLink from '../BackToHomeLink.tsx';
import useScrollSpy from '../../hooks/useScrollSpy';
import { useHashSpy } from '../../hooks/useHashSpy.js';

const MarketingShell = ({ children }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user } = useAuth();

  // Mobile menu state and count tracking
  const [mobileMenuOpen, setMobileMenuOpen] = React.useState(false);
  const [mobileItemCount, setMobileItemCount] = React.useState(0);
  const [productDropdownOpen, setProductDropdownOpen] = React.useState(false);
  const [focusedIndex, setFocusedIndex] = React.useState(-1);
  // Hash handling for anchor navigation - use hash spy for stable navigation
  const { currentHash, setHash } = useHashSpy(['#home', '#how', '#why', '#features', '#safety', '#faq']);

  // Force drawer closed on any route or anchor navigation
  useEffect(() => {
    // Close drawer on route change
    setMobileMenuOpen(false);
    // Update count immediately 
    setMobileItemCount(current => current);
  }, [location.pathname, location.hash]);

  // Count visible mobile menu items
  React.useEffect(() => {
    // Count nav items, auth actions, and theme toggle for marketing shell
    let count = 0;
    
    // Back to Home link
    count += 1;
    
    // MobileNavigation items (marketing focused)
    count += 3; // Features, Pricing, About
    
    // Auth actions 
    count += 2; // Sign In, Get Started
    
    // Theme toggle
    count += 1;
    
    setMobileItemCount(count);
  }, []);

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
    <div className="min-h-screen bg-theme-surface flex flex-col">
      {/* Single Marketing Header */}
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
          data-testid={TESTIDS.mobileDrawer}
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

      {/* Hash navigation marker - always present */}
      <div 
        data-testid={TESTIDS.navCurrentHash}
        className="sr-only"
        aria-hidden="true"
      >
        {currentHash}
      </div>

      {/* Main Content with proper padding for header */}
      <main className="flex-1">
        {children}
      </main>
    </div>
  );
};

export default MarketingShell;