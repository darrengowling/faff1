import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../App';
import { useTranslation } from 'react-i18next';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Card, CardContent } from '../ui/card';
import { 
  Trophy, 
  User, 
  LogOut, 
  Menu, 
  X, 
  Home,
  Users,
  Calendar,
  Crown,
  Settings,
  Bell,
  Search,
  Plus
} from 'lucide-react';
import { getBrandName } from '../../brand';
import { TESTIDS } from '../../testids';
import { TestableRouterLink } from '../testable/TestableComponents.tsx';

const AppShell = ({ children }) => {
  const { user, logout } = useAuth();
  const { t } = useTranslation();
  const location = useLocation();
  const navigate = useNavigate();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  // Close mobile menu when route changes
  useEffect(() => {
    setMobileMenuOpen(false);
  }, [location.pathname]);

  const navigationItems = [
    { 
      name: t('nav.dashboard'), 
      href: '/app', 
      icon: Home,
      active: location.pathname === '/app'
    },
    { 
      name: t('nav.leagues'), 
      href: '/app/leagues', 
      icon: Trophy,
      active: location.pathname.startsWith('/app/leagues')
    },
    { 
      name: t('nav.profile'), 
      href: '/profile', 
      icon: User,
      active: location.pathname === '/profile'
    }
  ];

  const handleCreateLeague = () => {
    navigate('/app/leagues/new');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="sticky top-0 z-40 bg-white shadow-sm border-b" data-testid={TESTIDS.appHeader}>
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
                  {t('nav.appName', { brandName: getBrandName() })}
                </h1>
              </TestableRouterLink>
            </div>

            {/* Desktop Navigation */}
            <nav className="hidden md:flex items-center space-x-8">
              {navigationItems.map((item) => (
                <TestableRouterLink
                  key={item.name}
                  to={item.href}
                  className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    item.active
                      ? 'bg-blue-100 text-blue-700'
                      : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                  }`}
                >
                  <item.icon className="w-4 h-4" />
                  <span>{item.name}</span>
                </TestableRouterLink>
              ))}
            </nav>

            {/* Right side actions */}
            <div className="flex items-center space-x-4">
              {/* Create League Button */}
              <Button
                onClick={handleCreateLeague}
                className="hidden sm:flex items-center space-x-2 bg-blue-600 hover:bg-blue-700"
                size="sm"
              >
                <Plus className="w-4 h-4" />
                <span>{t('nav.createLeague')}</span>
              </Button>

              {/* User Menu */}
              <div className="flex items-center space-x-3">
                <div className="hidden sm:flex items-center space-x-2">
                  <div className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center">
                    <User className="w-4 h-4 text-gray-600" />
                  </div>
                  <div className="text-sm">
                    <div className="font-medium text-gray-900">{user?.display_name || user?.email}</div>
                    <div className="text-gray-500">{t('nav.manager')}</div>
                  </div>
                </div>
                
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={logout}
                  className="hidden sm:flex items-center space-x-2"
                >
                  <LogOut className="w-4 h-4" />
                  <span>{t('nav.logout')}</span>
                </Button>
              </div>

              {/* Mobile menu button */}
              <Button
                variant="outline"
                size="sm"
                className="md:hidden"
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                data-testid={TESTIDS.mobileDrawer}
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
          <div className="md:hidden border-t bg-white">
            <div className="px-4 py-3 space-y-3">
              {/* User Info */}
              <div className="flex items-center space-x-3 pb-3 border-b">
                <div className="w-10 h-10 bg-gray-200 rounded-full flex items-center justify-center">
                  <User className="w-5 h-5 text-gray-600" />
                </div>
                <div>
                  <div className="font-medium text-gray-900">{user?.display_name || user?.email}</div>
                  <div className="text-sm text-gray-500">{t('nav.manager')}</div>
                </div>
              </div>

              {/* Navigation Items */}
              <div className="space-y-2">
                {navigationItems.map((item) => (
                  <TestableRouterLink
                    key={item.name}
                    to={item.href}
                    className={`flex items-center space-x-3 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                      item.active
                        ? 'bg-blue-100 text-blue-700'
                        : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                    }`}
                  >
                    <item.icon className="w-5 h-5" />
                    <span>{item.name}</span>
                  </TestableRouterLink>
                ))}
              </div>

              {/* Mobile Actions */}
              <div className="pt-3 border-t space-y-2">
                <Button
                  onClick={handleCreateLeague}
                  className="w-full flex items-center justify-center space-x-2 bg-blue-600 hover:bg-blue-700"
                  size="sm"
                >
                  <Plus className="w-4 h-4" />
                  <span>{t('nav.createLeague')}</span>
                </Button>
                
                <Button 
                  variant="outline" 
                  onClick={logout}
                  className="w-full flex items-center justify-center space-x-2"
                  size="sm"
                >
                  <LogOut className="w-4 h-4" />
                  <span>{t('nav.logout')}</span>
                </Button>
              </div>
            </div>
          </div>
        )}
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
        {children}
      </main>
    </div>
  );
};

export default AppShell;