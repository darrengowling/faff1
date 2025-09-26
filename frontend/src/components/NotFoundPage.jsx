/**
 * 404 Not Found Page Component
 * 
 * Displays when user navigates to non-existent route with helpful actions
 */

import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { 
  Home, Plus, Trophy, Search, AlertCircle, ArrowRight
} from 'lucide-react';
import { Button } from './ui/button';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { getBrandName } from '../brand';
import { useAuth } from '../App';

const NotFoundPage = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { user, isAuthenticated } = useAuth();

  const handleNavigation = (path) => {
    navigate(path);
  };

  const quickActions = [
    {
      id: 'home',
      title: 'Home',
      description: 'Return to your dashboard',
      icon: Home,
      action: () => handleNavigation('/app'),
      variant: 'default',
      show: isAuthenticated
    },
    {
      id: 'create-league',
      title: 'Create League',
      description: 'Start a new football auction',
      icon: Plus,
      action: () => handleNavigation('/app'), // Will redirect to dashboard where they can create
      variant: 'outline',
      show: isAuthenticated
    },
    {
      id: 'my-leagues',
      title: 'My Leagues',
      description: 'View your existing leagues',
      icon: Trophy,
      action: () => handleNavigation('/app'),
      variant: 'outline',
      show: isAuthenticated
    },
    {
      id: 'landing',
      title: 'Get Started',
      description: 'Learn about Friends of PIFA',
      icon: Search,
      action: () => handleNavigation('/'),
      variant: 'outline',
      show: !isAuthenticated
    }
  ];

  const visibleActions = quickActions.filter(action => action.show);

  return (
    <div className="min-h-screen bg-gradient-to-br from-theme-surface via-theme-surface-secondary to-theme-surface-tertiary flex items-center justify-center px-4">
      <div className="max-w-2xl w-full text-center">
        
        {/* 404 Icon and Message */}
        <div className="mb-8">
          <div className="w-24 h-24 bg-theme-primary/10 rounded-full flex items-center justify-center mx-auto mb-6">
            <AlertCircle className="w-12 h-12 text-theme-primary" />
          </div>
          
          <h1 className="text-4xl sm:text-5xl font-bold text-theme-text mb-4">
            404
          </h1>
          
          <h2 className="text-2xl font-semibold text-theme-text mb-2">
            Page Not Found
          </h2>
          
          <p className="text-lg text-theme-text-secondary max-w-lg mx-auto">
            The page you're looking for doesn't exist or has been moved. 
            Let's get you back to your football auctions!
          </p>
        </div>

        {/* Brand Context */}
        <div className="mb-8">
          <div className="flex items-center justify-center space-x-2 mb-2">
            <div className="w-8 h-8 bg-theme-primary rounded-full flex items-center justify-center">
              <Trophy className="w-5 h-5 text-theme-primary-contrast" />
            </div>
            <span className="text-lg font-semibold text-theme-text">
              {getBrandName()}
            </span>
          </div>
          <p className="text-sm text-theme-text-tertiary">
            {t('branding.tagline')}
          </p>
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
          {visibleActions.map((action) => {
            const Icon = action.icon;
            
            return (
              <Card 
                key={action.id}
                className="group hover:shadow-lg transition-all duration-200 cursor-pointer border-2 hover:border-theme-primary/50 bg-theme-surface"
                onClick={action.action}
              >
                <CardContent className="p-6 text-center">
                  <div className="w-12 h-12 bg-theme-primary/10 rounded-full flex items-center justify-center mx-auto mb-4 group-hover:bg-theme-primary/20 transition-colors">
                    <Icon className="w-6 h-6 text-theme-primary" />
                  </div>
                  
                  <h3 className="font-semibold text-theme-text mb-2">
                    {action.title}
                  </h3>
                  
                  <p className="text-sm text-theme-text-secondary mb-4">
                    {action.description}
                  </p>
                  
                  <Button
                    variant={action.variant}
                    size="sm"
                    className="w-full group-hover:shadow-md transition-all"
                    onClick={(e) => {
                      e.stopPropagation();
                      action.action();
                    }}
                  >
                    <span className="flex items-center space-x-2">
                      <span>{action.title}</span>
                      <ArrowRight className="w-3 h-3 group-hover:translate-x-1 transition-transform" />
                    </span>
                  </Button>
                </CardContent>
              </Card>
            );
          })}
        </div>

        {/* User Context (if authenticated) */}
        {isAuthenticated && user && (
          <div className="bg-theme-surface-secondary/50 rounded-lg p-4 mb-6">
            <p className="text-sm text-theme-text-secondary">
              Welcome back, <span className="font-medium text-theme-text">{user.display_name}</span>
            </p>
          </div>
        )}

        {/* Additional Help */}
        <div className="text-center">
          <p className="text-sm text-theme-text-tertiary mb-4">
            Still having trouble? Try refreshing the page or check your URL.
          </p>
          
          <div className="flex flex-col sm:flex-row items-center justify-center space-y-2 sm:space-y-0 sm:space-x-4">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => window.location.reload()}
              className="text-theme-text-secondary hover:text-theme-text"
            >
              Refresh Page
            </Button>
            
            <span className="hidden sm:inline text-theme-text-tertiary">•</span>
            
            <Button
              variant="ghost"
              size="sm"
              onClick={() => window.history.back()}
              className="text-theme-text-secondary hover:text-theme-text"
            >
              Go Back
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default NotFoundPage;