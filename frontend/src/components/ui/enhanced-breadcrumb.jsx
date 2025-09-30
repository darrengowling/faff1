/**
 * Enhanced Breadcrumb Navigation Component
 * 
 * Provides "You are here" indication and "Back to Home" functionality
 * Built on top of the existing breadcrumb components
 */

import React from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { Home, ArrowLeft } from 'lucide-react';
import { Button } from './button';
import { 
  Breadcrumb, 
  BreadcrumbList, 
  BreadcrumbItem, 
  BreadcrumbLink, 
  BreadcrumbPage, 
  BreadcrumbSeparator 
} from './breadcrumb';
import { TESTIDS } from '../../testids.ts';

/**
 * Generate breadcrumb items based on current path
 */
const generateBreadcrumbs = (pathname, selectedLeague) => {
  const segments = pathname.split('/').filter(Boolean);
  const breadcrumbs = [];

  // Always start with Home for app routes
  if (pathname.startsWith('/app') || pathname.includes('auction') || pathname.includes('clubs')) {
    breadcrumbs.push({
      label: 'Home',
      href: '/app',
      testid: 'breadcrumb-home'
    });
  }

  // Build breadcrumbs based on path segments
  segments.forEach((segment, index) => {
    const path = '/' + segments.slice(0, index + 1).join('/');
    
    switch (segment) {
      case 'app':
        // Don't duplicate home
        if (segments.length > 1) {
          breadcrumbs.push({
            label: 'Dashboard',
            href: '/app',
            testid: 'breadcrumb-dashboard'
          });
        }
        break;
        
      case 'auction':
        breadcrumbs.push({
          label: 'Auction Room',
          href: path,
          testid: 'breadcrumb-auction'
        });
        break;
        
      case 'clubs':
        breadcrumbs.push({
          label: 'My Roster',
          href: path,
          testid: 'breadcrumb-clubs'
        });
        break;
        
      case 'fixtures':
        breadcrumbs.push({
          label: 'Fixtures',
          href: path,
          testid: 'breadcrumb-fixtures'
        });
        break;
        
      case 'leaderboard':
        breadcrumbs.push({
          label: 'Leaderboard',
          href: path,
          testid: 'breadcrumb-leaderboard'
        });
        break;
        
      case 'admin':
        breadcrumbs.push({
          label: 'League Settings',
          href: path,
          testid: 'breadcrumb-admin'
        });
        break;
        
      case 'leagues':
        // Check if this is the leagues/new path for Create League wizard
        if (segments[index + 1] === 'new') {
          breadcrumbs.push({
            label: 'New League',
            href: path + '/new',
            testid: 'breadcrumb-new-league'
          });
        } else {
          breadcrumbs.push({
            label: 'Leagues',
            href: path,
            testid: 'breadcrumb-leagues'
          });
        }
        break;
        
      case 'new':
        // Skip 'new' segment as it's handled by 'leagues' case above
        break;
        
      case 'login':
        breadcrumbs.splice(0); // Clear all for login page
        breadcrumbs.push({
          label: 'Sign In',
          href: '/login',
          testid: 'breadcrumb-login'
        });
        break;
        
      default:
        // Handle dynamic segments (like league IDs)
        if (selectedLeague && segment === selectedLeague.id) {
          breadcrumbs.push({
            label: selectedLeague.name,
            href: path,
            testid: 'breadcrumb-league'
          });
        } else if (segment.length > 20) {
          // Probably a UUID or long ID, skip it
          return;
        } else {
          // Generic segment
          breadcrumbs.push({
            label: segment.charAt(0).toUpperCase() + segment.slice(1),
            href: path,
            testid: `breadcrumb-${segment}`
          });
        }
        break;
    }
  });

  return breadcrumbs;
};

/**
 * Enhanced Breadcrumb Component with Navigation Actions
 */
export const EnhancedBreadcrumb = ({ 
  className = '', 
  showBackButton = true,
  selectedLeague = null
}) => {
  const navigate = useNavigate();
  const location = useLocation();
  const breadcrumbs = generateBreadcrumbs(location.pathname, selectedLeague);

  const handleBackToHome = () => {
    navigate('/app');
  };

  const handleGoBack = () => {
    if (window.history.length > 1) {
      navigate(-1);
    } else {
      navigate('/app');
    }
  };

  // Don't show breadcrumbs on landing page or app home
  if (location.pathname === '/' || (location.pathname === '/app' && breadcrumbs.length <= 1)) {
    return null;
  }

  return (
    <div className={`flex items-center justify-between py-3 px-4 bg-gray-50 border-b border-gray-200 ${className}`}>
      {/* Breadcrumb Navigation */}
      <div className="flex items-center space-x-3">
        <span className="text-sm text-gray-500 font-medium">You are here:</span>
        
        <Breadcrumb>
          <BreadcrumbList>
            {breadcrumbs.map((crumb, index) => (
              <React.Fragment key={index}>
                <BreadcrumbItem>
                  {index === breadcrumbs.length - 1 ? (
                    // Current page - not a link
                    <BreadcrumbPage 
                      className="font-medium text-gray-900"
                      data-testid={crumb.testid}
                    >
                      {crumb.label}
                    </BreadcrumbPage>
                  ) : (
                    // Breadcrumb link
                    <BreadcrumbLink
                      asChild
                      data-testid={crumb.testid}
                    >
                      <Link
                        to={crumb.href}
                        className="text-blue-600 hover:text-blue-800"
                      >
                        {crumb.label}
                      </Link>
                    </BreadcrumbLink>
                  )}
                </BreadcrumbItem>
                {index < breadcrumbs.length - 1 && <BreadcrumbSeparator />}
              </React.Fragment>
            ))}
          </BreadcrumbList>
        </Breadcrumb>
      </div>

      {/* Navigation Actions */}
      {showBackButton && (
        <div className="flex items-center space-x-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={handleGoBack}
            className="text-gray-600 hover:text-gray-900"
            data-testid="back-button"
          >
            <ArrowLeft className="w-4 h-4 mr-1" />
            Back
          </Button>
          
          <Button
            variant="ghost"
            size="sm"
            onClick={handleBackToHome}
            className="text-blue-600 hover:text-blue-800"
            data-testid="back-to-home-button"
          >
            <Home className="w-4 h-4 mr-1" />
            Home
          </Button>
        </div>
      )}
    </div>
  );
};

/**
 * Page Header with Enhanced Breadcrumb
 */
export const PageHeader = ({ 
  title, 
  subtitle, 
  children,
  showBreadcrumb = true,
  selectedLeague = null,
  className = ''
}) => {
  return (
    <div className={`bg-white ${className}`}>
      {showBreadcrumb && (
        <EnhancedBreadcrumb selectedLeague={selectedLeague} />
      )}
      
      <div className="px-4 py-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{title}</h1>
            {subtitle && (
              <p className="mt-1 text-sm text-gray-600">{subtitle}</p>
            )}
          </div>
          {children && (
            <div className="flex items-center space-x-2">
              {children}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default EnhancedBreadcrumb;