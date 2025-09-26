import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Button } from './button';
import { 
  Menu, 
  X, 
  Home, 
  Users, 
  Trophy, 
  Gavel, 
  BarChart3,
  Settings,
  LogOut 
} from 'lucide-react';

/**
 * Mobile Navigation Component
 * 
 * Provides mobile-first navigation with hamburger menu
 * Addresses usability issue: "Missing mobile navigation pattern"
 */

export const MobileNav = ({ user, onLogout }) => {
  const [isOpen, setIsOpen] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  const navItems = [
    { icon: Home, label: 'Dashboard', path: '/dashboard' },
    { icon: Users, label: 'My Clubs', path: '/my-clubs' },
    { icon: Gavel, label: 'Live Auction', path: '/auction' },
    { icon: BarChart3, label: 'Leaderboard', path: '/leaderboard' },
    { icon: Trophy, label: 'Fixtures', path: '/fixtures' },
    { icon: Settings, label: 'Admin', path: '/admin', adminOnly: true }
  ];

  const handleNavigation = (path) => {
    navigate(path);
    setIsOpen(false);
  };

  const handleLogout = () => {
    setIsOpen(false);
    if (onLogout) onLogout();
  };

  // Only show on mobile screens
  return (
    <div className="md:hidden">
      {/* Mobile menu button */}
      <Button
        variant="ghost"
        size="sm"
        onClick={() => setIsOpen(!isOpen)}
        className="p-2"
        aria-label={isOpen ? "Close navigation menu" : "Open navigation menu"}
        aria-expanded={isOpen}
      >
        {isOpen ? (
          <X className="w-6 h-6" aria-hidden="true" />
        ) : (
          <Menu className="w-6 h-6" aria-hidden="true" />
        )}
      </Button>

      {/* Mobile menu overlay */}
      {isOpen && (
        <div className="fixed inset-0 z-50 bg-black bg-opacity-50" onClick={() => setIsOpen(false)} />
      )}

      {/* Mobile menu */}
      <div className={`
        fixed top-0 right-0 h-full w-64 bg-white shadow-lg transform transition-transform duration-300 z-50
        ${isOpen ? 'translate-x-0' : 'translate-x-full'}
      `}>
        <div className="p-4">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-semibold text-gray-900">Menu</h2>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsOpen(false)}
              aria-label="Close menu"
            >
              <X className="w-5 h-5" aria-hidden="true" />
            </Button>
          </div>

          {/* User info */}
          {user && (
            <div className="mb-6 p-3 bg-gray-50 rounded-lg">
              <div className="text-sm font-medium text-gray-900">{user.email}</div>
              <div className="text-xs text-gray-500">{user.role || 'Manager'}</div>
            </div>
          )}

          {/* Navigation items */}
          <div className="space-y-2" role="navigation">
            {navItems.map((item) => {
              // Skip admin-only items for non-admin users
              if (item.adminOnly && user?.role !== 'commissioner') {
                return null;
              }

              const isActive = location.pathname === item.path;
              const Icon = item.icon;

              return (
                <Button
                  key={item.path}
                  variant={isActive ? "default" : "ghost"}
                  className={`w-full justify-start ${isActive ? 'bg-blue-100 text-blue-700' : ''}`}
                  onClick={() => handleNavigation(item.path)}
                >
                  <Icon className="w-4 h-4 mr-3" aria-hidden="true" />
                  {item.label}
                </Button>
              );
            })}
          </div>

          {/* Logout */}
          {user && (
            <div className="mt-8 pt-4 border-t">
              <Button
                variant="ghost"
                className="w-full justify-start text-red-600 hover:text-red-700 hover:bg-red-50"
                onClick={handleLogout}
              >
                <LogOut className="w-4 h-4 mr-3" aria-hidden="true" />
                Logout
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export const BottomTabNav = ({ user }) => {
  const navigate = useNavigate();
  const location = useLocation();

  const tabItems = [
    { icon: Home, label: 'Home', path: '/dashboard' },
    { icon: Users, label: 'Clubs', path: '/my-clubs' },
    { icon: Gavel, label: 'Auction', path: '/auction' },
    { icon: BarChart3, label: 'Rankings', path: '/leaderboard' }
  ];

  return (
    <nav 
      className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 md:hidden z-40"
      role="navigation"
      aria-label="Bottom navigation"
    >
      <div className="flex justify-around py-2">
        {tabItems.map((item) => {
          const isActive = location.pathname === item.path;
          const Icon = item.icon;

          return (
            <Button
              key={item.path}
              variant="ghost"
              size="sm"
              className={`flex flex-col items-center p-2 min-w-0 flex-1 ${
                isActive ? 'text-blue-600' : 'text-gray-600'
              }`}
              onClick={() => navigate(item.path)}
            >
              <Icon 
                className={`w-5 h-5 mb-1 ${isActive ? 'text-blue-600' : ''}`} 
                aria-hidden="true" 
              />
              <span className="text-xs truncate">{item.label}</span>
            </Button>
          );
        })}
      </div>
    </nav>
  );
};

export default MobileNav;