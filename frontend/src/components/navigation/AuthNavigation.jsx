/**
 * Auth Navigation Component
 * Authentication-related navigation elements
 */

import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../ui/button';
import { User, LogOut } from 'lucide-react';
import { useAuth } from '../../App';
import { TESTIDS } from '../../testids.ts';

export const AuthNavigation = ({ variant = 'desktop' }) => {
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  if (variant === 'mobile') {
    return (
      <div className="space-y-3">
        {user ? (
          <>
            <div className="flex items-center space-x-2 p-3 bg-gray-50 rounded-lg" data-testid={TESTIDS.userMenu}>
              <User className="w-4 h-4 text-gray-600" />
              <span className="text-sm text-gray-700">{user.email}</span>
            </div>
            <Button
              variant="outline"
              onClick={logout}
              className="w-full flex items-center space-x-2"
            >
              <LogOut className="w-4 h-4" />
              <span>Sign Out</span>
            </Button>
          </>
        ) : (
          <>
            <Button
              variant="outline"
              onClick={() => navigate('/login')}
              className="w-full"
              data-testid={TESTIDS.navSignInMobile}
            >
              Sign In
            </Button>
            <Button
              onClick={() => navigate('/login')}
              className="w-full"
            >
              Get Started
            </Button>
          </>
        )}
      </div>
    );
  }

  // Desktop variant
  return (
    <div className="flex items-center space-x-3">
      {user ? (
        <>
          <div className="flex items-center space-x-2 text-sm text-gray-600">
            <User className="w-4 h-4" />
            <span>{user.email}</span>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={logout}
            className="flex items-center space-x-1"
          >
            <LogOut className="w-4 h-4" />
            <span>Sign Out</span>
          </Button>
        </>
      ) : (
        <>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => navigate('/login')}
            data-testid={TESTIDS.navSignInDesktop}
          >
            Sign In
          </Button>
          <Button
            size="sm"
            onClick={() => navigate('/login')}
          >
            Get Started
          </Button>
        </>
      )}
    </div>
  );
};

export default AuthNavigation;