/**
 * Page Menu Dropdown Component
 * A prominent "Go to..." dropdown with keyboard navigation, accessibility, and context-aware destinations
 */

import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { 
  ChevronDown, Trophy, Users, Calendar, BarChart3, Settings,
  Navigation, HelpCircle, Plus, UserPlus
} from 'lucide-react';
import { Button } from './button';
import { useAuth } from '../../App';
import { 
  productDropdownNavigation, 
  dashboardActions, 
  getVisibleItems, 
  getEnabledItems, 
  buildHref 
} from '../../navigation/navRegistry.js';
import { TESTIDS } from '../../testids.js';

const PageMenuDropdown = ({ selectedLeague, className = '' }) => {
  const { t } = useTranslation();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [isOpen, setIsOpen] = useState(false);
  const [focusedIndex, setFocusedIndex] = useState(-1);
  const [lastSelection, setLastSelection] = useState('');
  const [showTooltip, setShowTooltip] = useState(null);
  
  const dropdownRef = useRef(null);
  const triggerRef = useRef(null);

  // Create app state for navigation registry
  const appState = {
    selectedLeague,
    leagues: selectedLeague ? [selectedLeague] : [],
    isAuthenticated: !!user,
    user
  };

  // Get navigation items from registry
  const registryItems = productDropdownNavigation;
  const fallbackItems = dashboardActions; // Always available options

  // Convert registry items to menu format with enhanced context awareness
  const createMenuItems = () => {
    const items = [];
    
    // Add primary navigation items (league-specific)
    registryItems.forEach(navItem => {
      const isVisible = navItem.visible(user, appState);
      const isEnabled = navItem.enabled(user, appState);
      const href = buildHref(navItem, appState);
      
      items.push({
        id: navItem.id,
        label: navItem.label,
        icon: navItem.icon,
        description: navItem.description || 'Navigate to this section',
        href,
        visible: isVisible,
        enabled: isEnabled,
        action: () => {
          if (isEnabled) {
            navigate(href);
          }
        },
        tooltip: !isEnabled && isVisible 
          ? "Start or join a league to access this section" 
          : null,
        priority: 'primary'
      });
    });

    // Add fallback options if no primary items are enabled
    const enabledPrimary = items.filter(item => item.enabled && item.visible);
    
    if (enabledPrimary.length === 0) {
      fallbackItems.forEach(navItem => {
        const isVisible = navItem.visible(user, appState);
        const isEnabled = navItem.enabled(user, appState);
        const href = buildHref(navItem, appState);
        
        items.push({
          id: navItem.id,
          label: navItem.label,
          icon: navItem.icon,
          description: navItem.description || 'Quick action',
          href,
          visible: isVisible,
          enabled: isEnabled,
          action: () => {
            if (isEnabled) {
              if (navItem.id === 'create-league') {
                // Trigger create league dialog
                const createButton = document.querySelector('button:has-text("Create League")');
                if (createButton) {
                  createButton.click();
                } else {
                  navigate('/app');
                }
              } else {
                navigate(href);
              }
            }
          },
          tooltip: null,
          priority: 'fallback'
        });
      });
    }

    return items;
  };

  const menuItems = createMenuItems();
  const visibleItems = menuItems.filter(item => item.visible);
  const enabledItems = visibleItems.filter(item => item.enabled);

  // Load last selection from localStorage
  useEffect(() => {
    const saved = localStorage.getItem('pageMenuLastSelection');
    if (saved) {
      setLastSelection(saved);
    }
  }, []);

  // Save selection to localStorage
  const saveSelection = (itemId) => {
    setLastSelection(itemId);
    localStorage.setItem('pageMenuLastSelection', itemId);
  };

  // Handle menu item selection
  const handleSelect = (item) => {
    if (item.enabled && item.action) {
      item.action();
      saveSelection(item.id);
      setIsOpen(false);
      setFocusedIndex(-1);
      setShowTooltip(null);
      
      // Announce navigation to screen readers
      const message = `Navigating to ${item.label}`;
      announceToScreenReader(message);
    }
  };

  // Handle tooltip display for disabled items
  const handleItemHover = (item, index) => {
    setFocusedIndex(index);
    if (!item.enabled && item.tooltip) {
      setShowTooltip({ text: item.tooltip, itemId: item.id });
    } else {
      setShowTooltip(null);
    }
  };

  // Handle tooltip hide
  const handleItemLeave = () => {
    setShowTooltip(null);
  };

  // Screen reader announcement
  const announceToScreenReader = (message) => {
    const announcement = document.createElement('div');
    announcement.setAttribute('aria-live', 'polite');
    announcement.setAttribute('aria-atomic', 'true');
    announcement.className = 'sr-only';
    announcement.textContent = message;
    document.body.appendChild(announcement);
    
    setTimeout(() => {
      document.body.removeChild(announcement);
    }, 1000);
  };

  // Keyboard navigation
  const handleKeyDown = (e) => {
    const currentEnabledItems = enabledItems;
    
    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        if (!isOpen) {
          setIsOpen(true);
          setFocusedIndex(0);
        } else {
          setFocusedIndex(prev => 
            prev < currentEnabledItems.length - 1 ? prev + 1 : 0
          );
        }
        break;
        
      case 'ArrowUp':
        e.preventDefault();
        if (isOpen) {
          setFocusedIndex(prev => 
            prev > 0 ? prev - 1 : currentEnabledItems.length - 1
          );
        }
        break;
        
      case 'Enter':
      case ' ':
        e.preventDefault();
        if (!isOpen) {
          setIsOpen(true);
          setFocusedIndex(0);
        } else if (focusedIndex >= 0) {
          handleSelect(currentEnabledItems[focusedIndex]);
        }
        break;
        
      case 'Escape':
        e.preventDefault();
        setIsOpen(false);
        setFocusedIndex(-1);
        setShowTooltip(null);
        triggerRef.current?.focus();
        break;
        
      case 'Tab':
        if (isOpen) {
          setIsOpen(false);
          setFocusedIndex(-1);
          setShowTooltip(null);
        }
        break;
    }
  };

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
        setFocusedIndex(-1);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [isOpen]);

  // Announce dropdown state changes to screen readers
  useEffect(() => {
    if (isOpen) {
      announceToScreenReader(`Go to menu opened. ${enabledItems.length} options available.`);
    }
  }, [isOpen, enabledItems.length]);

  const hasSelection = lastSelection && enabledItems.some(item => item.id === lastSelection);

  return (
    <div ref={dropdownRef} className={`relative ${className}`}>
      <Button
        ref={triggerRef}
        onClick={() => setIsOpen(!isOpen)}
        onKeyDown={handleKeyDown}
        variant="outline"
        className="w-full justify-between min-w-48 bg-white border-2 hover:border-blue-300 focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
        aria-expanded={isOpen}
        aria-haspopup="menu"
        aria-label={enabledItems.length > 0 ? "Navigate to available sections" : "Create or join a league to access navigation"}
        disabled={enabledItems.length === 0}
        data-testid={TESTIDS.homeGotoDropdown}
      >
        <div className="flex items-center space-x-2">
          <Navigation className="w-4 h-4 text-blue-600" />
          <span className="font-medium">
            {enabledItems.length > 0 ? 'Go to...' : 'No Options Available'}
          </span>
        </div>
        <ChevronDown className={`w-4 h-4 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </Button>

      {isOpen && enabledItems.length > 0 && (
        <div
          className="absolute top-full left-0 mt-1 w-full bg-white rounded-lg shadow-lg border border-gray-200 py-2 z-50 min-w-64"
          role="menu"
          aria-label="Navigation menu"
        >
          {visibleItems.map((item, index) => {
            const Icon = item.icon;
            const isFocused = index === focusedIndex && item.enabled;
            const isLastSelection = item.id === lastSelection;
            const showItemTooltip = showTooltip?.itemId === item.id;
            
            return (
              <div key={item.id} className="relative">
                <button
                  onClick={() => handleSelect(item)}
                  onMouseEnter={() => handleItemHover(item, index)}
                  onMouseLeave={handleItemLeave}
                  disabled={!item.enabled}
                  className={`w-full flex items-start space-x-3 px-4 py-3 text-left transition-colors ${
                    item.enabled 
                      ? `hover:bg-blue-50 cursor-pointer ${isFocused ? 'bg-blue-50 text-blue-700' : 'text-gray-700'}`
                      : 'text-gray-400 cursor-not-allowed bg-gray-25'
                  } ${isLastSelection && item.enabled ? 'bg-blue-25 border-l-2 border-blue-500' : ''}`}
                  role="menuitem"
                  tabIndex={isFocused ? 0 : -1}
                  aria-describedby={`menu-item-${item.id}-desc`}
                  aria-disabled={!item.enabled}
                >
                  <Icon className={`w-5 h-5 mt-0.5 flex-shrink-0 ${
                    item.enabled 
                      ? (isFocused ? 'text-blue-600' : 'text-gray-400')
                      : 'text-gray-300'
                  }`} />
                  <div className="flex-1">
                    <div className="font-medium flex items-center">
                      {item.label}
                      {isLastSelection && item.enabled && (
                        <span className="ml-2 text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full">
                          Last visited
                        </span>
                      )}
                      {!item.enabled && (
                        <HelpCircle className="w-4 h-4 ml-2 text-gray-400" />
                      )}
                    </div>
                    <div 
                      id={`menu-item-${item.id}-desc`}
                      className="text-xs text-gray-500 mt-0.5"
                    >
                      {item.enabled ? item.description : (item.tooltip || 'Not available')}
                    </div>
                  </div>
                </button>
                
                {/* Tooltip for disabled items */}
                {showItemTooltip && item.tooltip && (
                  <div className="absolute left-full top-0 ml-2 z-60 bg-gray-900 text-white text-xs rounded px-2 py-1 whitespace-nowrap shadow-lg">
                    {item.tooltip}
                    <div className="absolute right-full top-1/2 transform -translate-y-1/2 border-4 border-transparent border-r-gray-900"></div>
                  </div>
                )}
              </div>
            );
          })}
          
          {/* Always show create league option if no primary options are available */}
          {enabledItems.length === 0 && (
            <div className="px-4 py-6 text-center">
              <div className="text-gray-500 text-sm mb-3">
                No league selected. Create or join a league to access navigation options.
              </div>
              <Button
                size="sm"
                onClick={() => {
                  setIsOpen(false);
                  // Trigger create league action
                  const createButton = document.querySelector('button:has-text("Create League")');
                  if (createButton) {
                    createButton.click();
                  }
                }}
                className="bg-blue-600 hover:bg-blue-700 text-white"
              >
                <Plus className="w-4 h-4 mr-1" />
                Create League
              </Button>
            </div>
          )}
        </div>
      )}

      {/* Screen reader status */}
      <div className="sr-only" aria-live="polite" aria-atomic="true">
        {isOpen ? `Navigation menu opened with ${enabledItems.length} enabled options and ${visibleItems.length - enabledItems.length} disabled options` : ''}
      </div>
      
      {/* Tooltip container for screen readers */}
      {showTooltip && (
        <div className="sr-only" aria-live="polite">
          {showTooltip.text}
        </div>
      )}
    </div>
  );
};

export default PageMenuDropdown;