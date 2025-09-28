/**
 * Enhanced NavigationMenu Component with Full Accessibility
 * 
 * Features:
 * - Proper ARIA roles and properties
 * - Keyboard navigation (arrows, ESC, Enter, Space)
 * - Focus trap for mobile drawer
 * - No placeholder items or empty href attributes 
 * - All data-testid attributes for testing
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { 
  ChevronDown, ChevronUp, ExternalLink, Menu, X, 
  ArrowLeft, ArrowRight, ArrowUp, ArrowDown
} from 'lucide-react';
import { 
  getVisibleItems, 
  getEnabledItems, 
  buildHref,
  productDropdownNavigation 
} from '../../navigation/navRegistry.js';
import { useAuth } from '../../App';
import { TESTIDS } from '../../testids.js';

/**
 * Hook to get current app state for navigation
 */
const useAppState = () => {
  const { user } = useAuth();
  const [selectedLeague, setSelectedLeague] = useState(null);
  const [leagues, setLeagues] = useState([]);
  
  // TODO: In real app, fetch actual selected league from state management
  useEffect(() => {
    // Mock selected league for demonstration
    if (user && leagues.length > 0) {
      setSelectedLeague({
        id: 'demo-league-123',
        name: 'Demo League',
        commissioner_id: user.id,
        status: 'active'
      });
    }
  }, [user, leagues]);
  
  const appState = {
    selectedLeague,
    leagues,
    isAuthenticated: !!user,
    user
  };
  
  return { appState, user };
};

/**
 * Map navigation item IDs to test IDs for consistency
 */
const getItemTestId = (item) => {
  const idMap = {
    'auction-room': TESTIDS.navDdAuction,
    'my-roster': TESTIDS.navDdRoster, 
    'fixtures': TESTIDS.navDdFixtures,
    'leaderboard': TESTIDS.navDdLeaderboard,
    'league-admin': TESTIDS.navDdSettings
  };
  
  return idMap[item.id] || null;
};

/**
 * Enhanced Product Dropdown Component
 */
export const ProductDropdownMenu = ({ 
  isOpen, 
  onToggle, 
  onClose,
  className = ''
}) => {
  const navigate = useNavigate();
  const location = useLocation();
  const { appState, user } = useAppState();
  const dropdownRef = useRef(null);
  const buttonRef = useRef(null);
  const [focusedIndex, setFocusedIndex] = useState(-1);

  // Close dropdown on route change
  useEffect(() => {
    if (isOpen) {
      onClose();
      setFocusedIndex(-1);
    }
  }, [location.pathname, onClose, isOpen]);
  
  // Get only visible items (enabled items are automatically navigable)
  const visibleItems = getVisibleItems(productDropdownNavigation, user, appState);
  
  // Focus management
  const focusItem = useCallback((index) => {
    const items = dropdownRef.current?.querySelectorAll('[role="menuitem"]');
    if (items && items[index]) {
      items[index].focus();
      setFocusedIndex(index);
    }
  }, []);

  // Keyboard navigation
  const handleKeyDown = useCallback((e) => {
    if (!isOpen) return;

    switch (e.key) {
      case 'Escape':
        e.preventDefault();
        onClose();
        buttonRef.current?.focus();
        break;
        
      case 'ArrowDown':
        e.preventDefault();
        const nextIndex = focusedIndex < visibleItems.length - 1 ? focusedIndex + 1 : 0;
        focusItem(nextIndex);
        break;
        
      case 'ArrowUp':
        e.preventDefault();
        const prevIndex = focusedIndex > 0 ? focusedIndex - 1 : visibleItems.length - 1;
        focusItem(prevIndex);
        break;
        
      case 'Tab':
        // Allow natural tab behavior but close dropdown
        onClose();
        break;
        
      case 'Enter':
      case ' ':
        if (e.target.getAttribute('role') === 'menuitem') {
          e.preventDefault();
          e.target.click();
        }
        break;
    }
  }, [isOpen, focusedIndex, visibleItems.length, onClose, focusItem]);

  // Click outside handler
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target) &&
          buttonRef.current && !buttonRef.current.contains(event.target)) {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      document.addEventListener('keydown', handleKeyDown);
      return () => {
        document.removeEventListener('mousedown', handleClickOutside);
        document.removeEventListener('keydown', handleKeyDown);
      };
    }
  }, [isOpen, onClose, handleKeyDown]);

  // Focus first item when dropdown opens
  useEffect(() => {
    if (isOpen && visibleItems.length > 0) {
      // Small delay to ensure dropdown is rendered
      setTimeout(() => focusItem(0), 50);
    } else {
      setFocusedIndex(-1);
    }
  }, [isOpen, visibleItems.length, focusItem]);

  const handleItemClick = (item) => {
    const href = buildHref(item, appState);
    
    if (item.external) {
      if (href.startsWith('http')) {
        window.open(href, '_blank', 'noopener,noreferrer');
      }
    } else {
      navigate(href);
    }
    
    onClose();
  };

  // Don't render dropdown if no visible items
  if (visibleItems.length === 0) {
    return null;
  }

  return (
    <div className={`relative ${className}`}>
      {/* Dropdown Button */}
      <button
        ref={buttonRef}
        type="button"
        className="flex items-center space-x-1 px-3 py-2 text-sm font-medium text-gray-700 hover:text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
        aria-expanded={isOpen}
        aria-haspopup="menu"
        data-testid={TESTIDS.navDropdownProduct}
        onClick={onToggle}
      >
        <span>Product</span>
        {isOpen ? (
          <ChevronUp className="w-4 h-4" aria-hidden="true" />
        ) : (
          <ChevronDown className="w-4 h-4" aria-hidden="true" />
        )}
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div
          ref={dropdownRef}
          className="absolute top-full left-0 mt-2 w-64 bg-white rounded-lg shadow-lg border border-gray-200 py-2 z-50"
          role="menu"
          aria-label="Product menu"
        >
          {visibleItems.map((item, index) => {
            const testId = getItemTestId(item);
            const href = buildHref(item, appState);
            
            return (
              <button
                key={item.id}
                type="button"
                className="w-full text-left px-4 py-3 text-sm text-gray-700 hover:bg-gray-50 focus:bg-blue-50 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-blue-500"
                role="menuitem"
                tabIndex={-1}
                data-testid={testId}
                onClick={() => handleItemClick(item)}
                onFocus={() => setFocusedIndex(index)}
              >
                <div className="flex items-center space-x-3">
                  {item.icon && (
                    <item.icon className="w-4 h-4 text-gray-400" aria-hidden="true" />
                  )}
                  <div>
                    <div className="font-medium">{item.label}</div>
                    {item.description && (
                      <div className="text-xs text-gray-500">{item.description}</div>
                    )}
                  </div>
                  {item.external && (
                    <ExternalLink className="w-3 h-3 text-gray-400 ml-auto" aria-hidden="true" />
                  )}
                </div>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
};

/**
 * Enhanced Mobile Navigation with Focus Trap
 */
export const MobileNavigation = ({ 
  isOpen, 
  onClose,
  className = '' 
}) => {
  const navigate = useNavigate();
  const { appState, user } = useAppState();
  const drawerRef = useRef(null);
  const firstFocusableRef = useRef(null);
  const lastFocusableRef = useRef(null);
  const [focusedIndex, setFocusedIndex] = useState(-1);

  // Get all navigation items for mobile
  const visibleItems = getVisibleItems(productDropdownNavigation, user, appState);

  // Focus trap implementation
  const trapFocus = useCallback((e) => {
    if (!isOpen) return;

    const focusableElements = drawerRef.current?.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    
    if (focusableElements && focusableElements.length > 0) {
      const firstElement = focusableElements[0];
      const lastElement = focusableElements[focusableElements.length - 1];

      if (e.key === 'Tab') {
        if (e.shiftKey) {
          if (document.activeElement === firstElement) {
            e.preventDefault();
            lastElement.focus();
          }
        } else {
          if (document.activeElement === lastElement) {
            e.preventDefault();
            firstElement.focus();
          }
        }
      }
    }
  }, [isOpen]);

  // Keyboard navigation
  const handleKeyDown = useCallback((e) => {
    if (!isOpen) return;

    switch (e.key) {
      case 'Escape':
        e.preventDefault();
        onClose();
        break;
        
      case 'ArrowDown':
        e.preventDefault();
        const nextIndex = focusedIndex < visibleItems.length - 1 ? focusedIndex + 1 : 0;
        setFocusedIndex(nextIndex);
        const nextElement = drawerRef.current?.querySelectorAll('[role="menuitem"]')[nextIndex];
        nextElement?.focus();
        break;
        
      case 'ArrowUp':
        e.preventDefault();
        const prevIndex = focusedIndex > 0 ? focusedIndex - 1 : visibleItems.length - 1;
        setFocusedIndex(prevIndex);
        const prevElement = drawerRef.current?.querySelectorAll('[role="menuitem"]')[prevIndex];
        prevElement?.focus();
        break;
    }
    
    trapFocus(e);
  }, [isOpen, focusedIndex, visibleItems.length, onClose, trapFocus]);

  // Event listeners
  useEffect(() => {
    if (isOpen) {
      document.addEventListener('keydown', handleKeyDown);
      // Focus first element when drawer opens
      setTimeout(() => {
        firstFocusableRef.current?.focus();
      }, 100);
      
      return () => {
        document.removeEventListener('keydown', handleKeyDown);
      };
    }
  }, [isOpen, handleKeyDown]);

  const handleItemClick = (item) => {
    const href = buildHref(item, appState);
    
    if (item.external) {
      if (href.startsWith('http')) {
        window.open(href, '_blank', 'noopener,noreferrer');
      }
    } else {
      navigate(href);
    }
    
    onClose();
  };

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black bg-opacity-50 z-40"
        onClick={onClose}
        aria-hidden="true"
      />
      
      {/* Mobile Drawer */}
      <div
        ref={drawerRef}
        className={`fixed top-0 left-0 h-full w-80 max-w-sm bg-white shadow-xl z-50 transform transition-transform ${className}`}
        role="dialog"
        aria-modal="true"
        aria-label="Navigation menu"
        data-testid={TESTIDS.navMobileDrawer}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Menu</h2>
          <button
            ref={firstFocusableRef}
            type="button"
            className="p-2 text-gray-400 hover:text-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500 rounded-md"
            onClick={onClose}
            aria-label="Close menu"
          >
            <X className="w-5 h-5" aria-hidden="true" />
          </button>
        </div>

        {/* Navigation Items */}
        <nav className="flex-1 px-4 py-6" role="menu">
          {visibleItems.length === 0 ? (
            <div className="text-center text-gray-500 py-8">
              <p>No navigation items available</p>
              <p className="text-sm">Please sign in to access features</p>
            </div>
          ) : (
            <div className="space-y-2">
              {visibleItems.map((item, index) => {
                const testId = `nav-mobile-item-${item.id}`;
                
                return (
                  <button
                    key={item.id}
                    type="button"
                    className="w-full text-left p-3 text-base text-gray-700 hover:bg-gray-50 focus:bg-blue-50 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-blue-500 rounded-md"
                    role="menuitem"
                    data-testid={testId}
                    onClick={() => handleItemClick(item)}
                    onFocus={() => setFocusedIndex(index)}
                    ref={index === visibleItems.length - 1 ? lastFocusableRef : null}
                  >
                    <div className="flex items-center space-x-3">
                      {item.icon && (
                        <item.icon className="w-5 h-5 text-gray-400" aria-hidden="true" />
                      )}
                      <div>
                        <div className="font-medium">{item.label}</div>
                        {item.description && (
                          <div className="text-sm text-gray-500">{item.description}</div>
                        )}
                      </div>
                      {item.external && (
                        <ExternalLink className="w-4 h-4 text-gray-400 ml-auto" aria-hidden="true" />
                      )}
                    </div>
                  </button>
                );
              })}
            </div>
          )}
        </nav>
      </div>
    </>
  );
};

/**
 * Mobile Menu Toggle Button
 */
export const MobileMenuButton = ({ 
  isOpen, 
  onClick,
  className = '' 
}) => {
  return (
    <button
      type="button"
      className={`p-2 text-gray-400 hover:text-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500 rounded-md ${className}`}
      aria-expanded={isOpen}
      aria-label={isOpen ? 'Close menu' : 'Open menu'}
      data-testid={TESTIDS.navHamburger}
      onClick={onClick}
    >
      {isOpen ? (
        <X className="w-6 h-6" aria-hidden="true" />
      ) : (
        <Menu className="w-6 h-6" aria-hidden="true" />
      )}
    </button>
  );
};

export default {
  ProductDropdownMenu,
  MobileNavigation,
  MobileMenuButton
};