/**
 * NavigationMenu Component
 * 
 * Reusable component that dynamically renders navigation menus
 * from the navigation registry with conditional visibility and enablement
 */

import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { 
  ChevronDown, ChevronRight, ExternalLink
} from 'lucide-react';
import { 
  getVisibleItems, 
  getEnabledItems, 
  buildHref,
  menuConfigs 
} from '../../navigation/navRegistry.js';
import { useAuth } from '../../App';
import { TESTIDS } from '../../testing/testids.ts';

/**
 * Hook to get current app state for navigation
 */
const useAppState = () => {
  const { user } = useAuth();
  const [selectedLeague, setSelectedLeague] = useState(null);
  const [leagues, setLeagues] = useState([]);
  
  // In a real app, this would fetch from your state management or API
  // For now, we'll use a simplified version
  const appState = {
    selectedLeague,
    leagues,
    isAuthenticated: !!user,
    user
  };
  
  return { appState, user };
};

/**
 * Map navigation item IDs to test IDs
 */
const getItemTestId = (item, variant) => {
  const idMap = {
    // App navigation items
    'auction-room': TESTIDS.navItemAuction,
    'my-roster': TESTIDS.navItemRoster, 
    'fixtures': TESTIDS.navDropdownItemFixtures,
    'leaderboard': TESTIDS.navItemLeaderboard,
    'league-admin': TESTIDS.navDropdownItemSettings,
    'league-settings': TESTIDS.navDropdownItemSettings,
    'dashboard': TESTIDS.navItemDashboard,

    // Landing page anchor items  
    'home': TESTIDS.navItemHome,
    'how': TESTIDS.navItemHow,
    'why': TESTIDS.navItemWhy,
    'features': TESTIDS.navItemFeatures,
    'safety': TESTIDS.navItemSafety,
    'faq': TESTIDS.navItemFaq
  };
  
  return idMap[item.id] || null;
};

/**
 * Generic Navigation Item Component
 */
const NavigationItem = ({ 
  item, 
  user, 
  appState, 
  variant = 'default', 
  onClick,
  className = '',
  children 
}) => {
  const navigate = useNavigate();
  const isEnabled = item.enabled(user, appState);
  const isVisible = item.visible(user, appState);
  const href = buildHref(item, appState);
  
  if (!isVisible) return null;
  
  const handleClick = (e) => {
    e.preventDefault();
    if (onClick) {
      onClick(item);
    } else if (isEnabled) {
      if (item.external) {
        // Handle external links
        if (href.startsWith('http')) {
          window.open(href, '_blank', 'noopener,noreferrer');
        } else {
          // Navigate to external placeholder pages
          navigate(href);
        }
      } else {
        navigate(href);
      }
    }
  };
  
  const baseClasses = {
    default: 'flex items-center space-x-2 px-3 py-2 text-sm font-medium transition-colors rounded-md',
    desktop: 'hover:text-blue-600 hover:bg-blue-50',
    mobile: 'w-full text-left px-4 py-3 hover:bg-gray-50',
    dropdown: 'w-full flex items-start space-x-3 px-4 py-3 text-left hover:bg-theme-surface-tertiary transition-colors',
    footer: 'block text-sm text-gray-600 hover:text-blue-600 transition-colors text-left'
  };
  
  const variantClasses = baseClasses[variant] || baseClasses.default;
  const disabledClasses = !isEnabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer';
  const testId = getItemTestId(item, variant);
  
  return (
    <button
      onClick={handleClick}
      disabled={!isEnabled}
      className={`${variantClasses} ${disabledClasses} ${className}`}
      aria-label={item.description || `Navigate to ${item.label}`}
      data-testid={testId}
      data-href={href}
    >
      {item.icon && (
        <item.icon className={`w-${variant === 'dropdown' ? '5' : '4'} h-${variant === 'dropdown' ? '5' : '4'} flex-shrink-0 ${
          variant === 'dropdown' ? 'mt-0.5 text-gray-400' : ''
        }`} />
      )}
      <div className="flex-1">
        <div className="flex items-center space-x-1">
          <span>{item.label}</span>
          {item.external && <ExternalLink className="w-3 h-3" />}
        </div>
        {item.description && variant === 'dropdown' && (
          <div className="text-xs text-gray-500 mt-0.5">{item.description}</div>
        )}
      </div>
      {children}
    </button>
  );
};

/**
 * Desktop Dropdown Menu Component
 */
const DesktopDropdown = ({ 
  items, 
  label, 
  user, 
  appState, 
  isOpen, 
  onToggle,
  className = '',
  focusedIndex = -1,
  onFocusChange,
  onKeyDown
}) => {
  const dropdownRef = useRef(null);
  const visibleItems = getVisibleItems(items, user, appState);
  
  return (
    <div className="relative group">
      <button
        onClick={onToggle}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            onToggle();
          }
          if (onKeyDown) onKeyDown(e);
        }}
        className={`flex items-center space-x-1 px-3 py-2 text-sm font-medium transition-colors rounded-md hover:text-blue-600 hover:bg-blue-50 ${
          isOpen ? 'text-blue-600 bg-blue-50' : 'text-gray-700'
        } ${className}`}
        aria-expanded={isOpen}
        aria-haspopup="true"
        data-testid={TESTIDS.navDropdownProduct}
      >
        <span>{label}</span>
        <ChevronDown className={`w-4 h-4 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && visibleItems.length > 0 && (
        <div
          ref={dropdownRef}
          className="absolute top-full left-0 mt-1 w-64 bg-theme-surface rounded-lg shadow-lg border border-theme-surface-border py-2 z-[60]"
          role="menu"
          data-testid="product-dropdown-menu"
        >
          {visibleItems.map((item, index) => (
            <NavigationItem
              key={item.id}
              item={item}
              user={user}
              appState={appState}
              variant="dropdown"
              className={`${index === focusedIndex ? 'bg-theme-surface-tertiary text-theme-primary' : 'text-theme-text'}`}
              onMouseEnter={() => onFocusChange && onFocusChange(index)}
            />
          ))}
        </div>
      )}
    </div>
  );
};

/**
 * Mobile Navigation List Component
 */
const MobileNavList = ({ 
  items, 
  user, 
  appState, 
  onItemClick,
  className = '',
  nested = false 
}) => {
  const [expandedItems, setExpandedItems] = useState({});
  const visibleItems = getVisibleItems(items, user, appState);
  
  const toggleExpanded = (itemId) => {
    setExpandedItems(prev => ({
      ...prev,
      [itemId]: !prev[itemId]
    }));
  };
  
  if (visibleItems.length === 0) return null;
  
  return (
    <div className={className}>
      {visibleItems.map((item) => {
        const hasChildren = item.items && item.items.length > 0;
        const isExpanded = expandedItems[item.id];
        
        if (hasChildren) {
          return (
            <div key={item.id}>
              <button
                onClick={() => toggleExpanded(item.id)}
                className={`w-full flex items-center justify-between px-4 py-3 text-left font-medium transition-colors hover:bg-gray-50 ${
                  nested ? 'pl-8' : ''
                }`}
                aria-expanded={isExpanded}
              >
                <div className="flex items-center space-x-2">
                  {item.icon && <item.icon className="w-5 h-5 text-gray-400" />}
                  <span className="text-gray-900">{item.label}</span>
                </div>
                <ChevronRight className={`w-5 h-5 text-gray-400 transition-transform ${isExpanded ? 'rotate-90' : ''}`} />
              </button>
              
              {isExpanded && (
                <div className="bg-gray-50">
                  <MobileNavList
                    items={item.items}
                    user={user}
                    appState={appState}
                    onItemClick={onItemClick}
                    nested={true}
                  />
                </div>
              )}
            </div>
          );
        }
        
        return (
          <NavigationItem
            key={item.id}
            item={item}
            user={user}
            appState={appState}
            variant="mobile"
            onClick={onItemClick}
            className={nested ? 'pl-8' : ''}
          />
        );
      })}
    </div>
  );
};

/**
 * Main NavigationMenu Component
 * Supports different menu types from the navigation registry
 */
const NavigationMenu = ({ 
  menuType = 'globalNavbar', 
  section = 'primary',
  variant = 'desktop',
  className = '',
  onItemClick,
  ...props 
}) => {
  const { appState, user } = useAppState();
  const config = menuConfigs[menuType];
  
  if (!config || !config[section]) {
    console.warn(`NavigationMenu: Invalid menuType "${menuType}" or section "${section}"`);
    return null;
  }
  
  const items = config[section];
  
  // Simple list variant (for footer, etc.)
  if (variant === 'list') {
    const visibleItems = getVisibleItems(items, user, appState);
    
    return (
      <div className={className}>
        {visibleItems.map((item) => (
          <NavigationItem
            key={item.id}
            item={item}
            user={user}
            appState={appState}
            variant="footer"
            onClick={onItemClick}
          />
        ))}
      </div>
    );
  }
  
  // Mobile variant
  if (variant === 'mobile') {
    return (
      <MobileNavList
        items={items}
        user={user}
        appState={appState}
        onItemClick={onItemClick}
        className={className}
      />
    );
  }
  
  // Desktop variant (default)
  const visibleItems = getVisibleItems(items, user, appState);
  
  return (
    <div className={`flex items-center space-x-2 ${className}`}>
      {visibleItems.map((item) => (
        <NavigationItem
          key={item.id}
          item={item}
          user={user}
          appState={appState}
          variant="default"
          onClick={onItemClick}
        />
      ))}
    </div>
  );
};

/**
 * Specialized Navigation Components
 */

// Primary navigation for desktop navbar
export const PrimaryNavigation = ({ className, onItemClick }) => (
  <NavigationMenu
    menuType="globalNavbar"
    section="primary"
    variant="desktop"
    className={className}
    onItemClick={onItemClick}
  />
);

// Product dropdown navigation
export const ProductDropdownMenu = ({ 
  isOpen, 
  onToggle, 
  className,
  focusedIndex,
  onFocusChange,
  onKeyDown 
}) => {
  const { appState, user } = useAppState();
  
  return (
    <DesktopDropdown
      items={menuConfigs.globalNavbar.productDropdown}
      label="Product"
      user={user}
      appState={appState}
      isOpen={isOpen}
      onToggle={onToggle}
      className={className}
      focusedIndex={focusedIndex}
      onFocusChange={onFocusChange}
      onKeyDown={onKeyDown}
    />
  );
};

// Auth navigation buttons
export const AuthNavigation = ({ className, variant = 'desktop', onItemClick }) => {
  const { user } = useAuth();
  const navigate = useNavigate();
  
  if (user) {
    return (
      <div className={`flex items-center space-x-3 ${className}`}>
        <span className="text-sm text-gray-600">
          Welcome, {user.name || user.email}
        </span>
        <button
          onClick={() => navigate('/app')}
          className="px-3 py-2 text-sm font-medium bg-blue-600 text-white rounded-md hover:bg-blue-700"
          data-testid={TESTIDS.navDashboard}
        >
          Dashboard
        </button>
      </div>
    );
  }
  
  return (
    <div className={`flex items-center space-x-3 ${className}`}>
      <button
        onClick={() => navigate('/login')}
        className="px-3 py-2 text-sm font-medium text-gray-700 hover:text-blue-600"
        data-testid={TESTIDS.navSignIn}
      >
        Sign In
      </button>
      <button
        onClick={() => navigate('/login')}
        className="px-3 py-2 text-sm font-medium bg-blue-600 text-white rounded-md hover:bg-blue-700"
        data-testid={TESTIDS.navGetStarted}
      >
        Get Started
      </button>
    </div>
  );
};

// Footer navigation
export const FooterNavigation = ({ className, onItemClick }) => (
  <NavigationMenu
    menuType="footer"
    section="legal"
    variant="list"
    className={className}
    onItemClick={onItemClick}
  />
);

// Dashboard quick actions
export const DashboardNavigation = ({ className, variant = 'desktop', onItemClick }) => (
  <NavigationMenu
    menuType="dashboard"
    section="quickActions"
    variant={variant}
    className={className}
    onItemClick={onItemClick}
  />
);

// Mobile navigation (all menu items)
export const MobileNavigation = ({ className, onItemClick }) => {
  const { appState, user } = useAppState();
  const allMenuItems = [
    ...menuConfigs.globalNavbar.primary,
    {
      id: 'product-mobile',
      label: 'Product',
      items: menuConfigs.globalNavbar.productDropdown,
      visible: (user, appState) => true,
      enabled: (user, appState) => true
    },
    ...menuConfigs.globalNavbar.auth
  ];
  
  return (
    <MobileNavList
      items={allMenuItems}
      user={user}
      appState={appState}
      onItemClick={onItemClick}
      className={className}
    />
  );
};

export default NavigationMenu;