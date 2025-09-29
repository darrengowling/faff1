import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Button } from '../ui/button';
import { 
  Trophy, 
  Menu, 
  X, 
  Home,
  HelpCircle,
  Star,
  Shield,
  Zap,
  Users
} from 'lucide-react';
import { getBrandName } from '../../brand';
import { TESTIDS } from '../../testids';
import { TestableRouterLink } from '../testable/TestableComponents.tsx';

const MarketingShell = ({ children }) => {
  const { t } = useTranslation();
  const location = useLocation();
  const navigate = useNavigate();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  // Close mobile menu when route changes
  useEffect(() => {
    setMobileMenuOpen(false);
  }, [location.pathname]);

  // Navigation items for marketing pages
  const navigationItems = [
    { 
      name: t('nav.home'), 
      href: '#home', 
      icon: Home,
      testid: TESTIDS.navItemHome
    },
    { 
      name: t('nav.howItWorks'), 
      href: '#how', 
      icon: HelpCircle,
      testid: TESTIDS.navItemHow
    },
    { 
      name: t('nav.whyChoose'), 
      href: '#why', 
      icon: Star,
      testid: TESTIDS.navItemWhy
    },
    { 
      name: t('nav.features'), 
      href: '#features', 
      icon: Zap,
      testid: TESTIDS.navItemFeatures
    },
    { 
      name: t('nav.safety'), 
      href: '#safety', 
      icon: Shield,
      testid: TESTIDS.navItemSafety
    },
    { 
      name: t('nav.faq'), 
      href: '#faq', 
      icon: HelpCircle,
      testid: TESTIDS.navItemFaq
    }
  ];

  const handleNavClick = (href) => {
    if (href.startsWith('#')) {
      // Smooth scroll to section
      const element = document.querySelector(href);
      if (element) {
        element.scrollIntoView({ behavior: 'smooth' });
      }
    } else {
      navigate(href);
    }
    setMobileMenuOpen(false);
  };

  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="sticky top-0 z-40 bg-white/95 backdrop-blur-sm shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* Logo and Brand */}
            <div className="flex items-center space-x-3">
              <TestableRouterLink 
                to="/" 
                className="flex items-center space-x-3 hover:opacity-80 transition-opacity"
                data-testid={TESTIDS.backToHome}
              >
                <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
                  <Trophy className="w-5 h-5 text-white" />
                </div>
                <h1 className="text-xl font-bold text-gray-900">
                  {getBrandName()}
                </h1>
              </TestableRouterLink>
            </div>

            {/* Desktop Navigation */}
            <nav className="hidden md:flex items-center space-x-6">
              {navigationItems.map((item) => (
                <button
                  key={item.name}
                  onClick={() => handleNavClick(item.href)}
                  className="flex items-center space-x-1 px-3 py-2 rounded-md text-sm font-medium text-gray-600 hover:text-gray-900 hover:bg-gray-100 transition-colors"
                  data-testid={item.testid}
                >
                  <item.icon className="w-4 h-4" />
                  <span>{item.name}</span>
                </button>
              ))}
            </nav>

            {/* Right side actions */}
            <div className="flex items-center space-x-4">
              <Button
                onClick={() => navigate('/login')}
                variant="outline"
                size="sm"
                className="hidden sm:flex"
              >
                {t('nav.signIn')}
              </Button>
              
              <Button
                onClick={() => navigate('/login')}
                className="hidden sm:flex bg-blue-600 hover:bg-blue-700"
                size="sm"
              >
                {t('nav.getStarted')}
              </Button>

              {/* Mobile menu button */}
              <Button
                variant="outline"
                size="sm"
                className="md:hidden"
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                data-testid={TESTIDS.mobileDrawer}
                data-state={mobileMenuOpen ? 'open' : 'closed'}
                data-count={navigationItems.length}
              >
                {mobileMenuOpen ? (
                  <X className="w-4 h-4" />
                ) : (
                  <Menu className="w-4 h-4" />
                )}
              </Button>
            </div>
          </div>
        </div>

        {/* Mobile Navigation */}
        {mobileMenuOpen && (
          <div className="md:hidden border-t bg-white/95 backdrop-blur-sm">
            <div className="px-4 py-3 space-y-2">
              {/* Navigation Items */}
              {navigationItems.map((item) => (
                <button
                  key={item.name}
                  onClick={() => handleNavClick(item.href)}
                  className="flex items-center space-x-3 px-3 py-2 rounded-md text-sm font-medium text-gray-600 hover:text-gray-900 hover:bg-gray-100 transition-colors w-full text-left"
                  data-testid={item.testid}
                >
                  <item.icon className="w-5 h-5" />
                  <span>{item.name}</span>
                </button>
              ))}

              {/* Mobile Actions */}
              <div className="pt-3 border-t space-y-2">
                <Button
                  onClick={() => navigate('/login')}
                  variant="outline"
                  className="w-full"
                  size="sm"
                >
                  {t('nav.signIn')}
                </Button>
                
                <Button
                  onClick={() => navigate('/login')}
                  className="w-full bg-blue-600 hover:bg-blue-700"
                  size="sm"
                >
                  {t('nav.getStarted')}
                </Button>
              </div>
            </div>
          </div>
        )}
      </header>

      {/* Main Content */}
      <main>
        {children}
      </main>

      {/* Hash Navigation Indicator */}
      <div 
        data-testid={TESTIDS.navCurrentHash}
        className="sr-only"
        aria-hidden="true"
      >
        {location.hash || '#home'}
      </div>
    </div>
  );
};

export default MarketingShell;