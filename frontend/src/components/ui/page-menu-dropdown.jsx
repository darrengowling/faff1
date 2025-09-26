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

const PageMenuDropdown = ({ selectedLeague, className = '' }) => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [isOpen, setIsOpen] = useState(false);
  const [focusedIndex, setFocusedIndex] = useState(-1);
  const [lastSelection, setLastSelection] = useState('');
  
  const dropdownRef = useRef(null);
  const triggerRef = useRef(null);

  // Menu items with context-aware navigation
  const menuItems = [
    {
      id: 'auction',
      label: t('nav.auction', 'Auction Room'),
      icon: Trophy,
      description: 'Join live bidding session',
      action: () => selectedLeague ? navigate(`/auction/${selectedLeague.id}`) : null,
      enabled: !!selectedLeague
    },
    {
      id: 'roster',
      label: t('nav.myClubs', 'My Roster'),
      icon: Users,
      description: 'View your clubs and budget',
      action: () => selectedLeague ? navigate(`/clubs/${selectedLeague.id}`) : null,
      enabled: !!selectedLeague
    },
    {
      id: 'fixtures',
      label: t('nav.fixtures', 'Fixtures'),
      icon: Calendar,
      description: 'Match schedules and results',
      action: () => selectedLeague ? navigate(`/fixtures/${selectedLeague.id}`) : null,
      enabled: !!selectedLeague
    },
    {
      id: 'leaderboard',
      label: t('nav.leaderboard', 'Leaderboard'),
      icon: BarChart3,
      description: 'Rankings and statistics',
      action: () => selectedLeague ? navigate(`/leaderboard/${selectedLeague.id}`) : null,
      enabled: !!selectedLeague
    },
    {
      id: 'settings',
      label: t('nav.admin', 'League Settings'),
      icon: Settings,
      description: 'Manage league configuration',
      action: () => selectedLeague ? navigate(`/admin/${selectedLeague.id}`) : null,
      enabled: !!selectedLeague
    }
  ];

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
      
      // Announce navigation to screen readers
      const message = `Navigating to ${item.label}`;
      announceToScreenReader(message);
    }
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
    const enabledItems = menuItems.filter(item => item.enabled);
    
    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        if (!isOpen) {
          setIsOpen(true);
          setFocusedIndex(0);
        } else {
          setFocusedIndex(prev => 
            prev < enabledItems.length - 1 ? prev + 1 : 0
          );
        }
        break;
        
      case 'ArrowUp':
        e.preventDefault();
        if (isOpen) {
          setFocusedIndex(prev => 
            prev > 0 ? prev - 1 : enabledItems.length - 1
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
          handleSelect(enabledItems[focusedIndex]);
        }
        break;
        
      case 'Escape':
        e.preventDefault();
        setIsOpen(false);
        setFocusedIndex(-1);
        triggerRef.current?.focus();
        break;
        
      case 'Tab':
        if (isOpen) {
          setIsOpen(false);
          setFocusedIndex(-1);
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
      announceToScreenReader(`Go to menu opened. ${menuItems.filter(item => item.enabled).length} options available.`);
    }
  }, [isOpen]);

  const enabledItems = menuItems.filter(item => item.enabled);
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
        aria-label={selectedLeague ? "Navigate to league sections" : "Select a league first to navigate"}
        disabled={!selectedLeague}
      >
        <div className="flex items-center space-x-2">
          <Navigation className="w-4 h-4 text-blue-600" />
          <span className="font-medium">
            {selectedLeague ? 'Go to...' : 'Select League First'}
          </span>
        </div>
        <ChevronDown className={`w-4 h-4 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </Button>

      {isOpen && selectedLeague && (
        <div
          className="absolute top-full left-0 mt-1 w-full bg-white rounded-lg shadow-lg border border-gray-200 py-2 z-50 min-w-64"
          role="menu"
          aria-label="Navigation menu"
        >
          {enabledItems.map((item, index) => {
            const Icon = item.icon;
            const isFocused = index === focusedIndex;
            const isLastSelection = item.id === lastSelection;
            
            return (
              <button
                key={item.id}
                onClick={() => handleSelect(item)}
                onMouseEnter={() => setFocusedIndex(index)}
                className={`w-full flex items-start space-x-3 px-4 py-3 text-left hover:bg-blue-50 transition-colors ${
                  isFocused ? 'bg-blue-50 text-blue-700' : 'text-gray-700'
                } ${isLastSelection ? 'bg-blue-25 border-l-2 border-blue-500' : ''}`}
                role="menuitem"
                tabIndex={isFocused ? 0 : -1}
                aria-describedby={`menu-item-${item.id}-desc`}
              >
                <Icon className={`w-5 h-5 mt-0.5 flex-shrink-0 ${
                  isFocused ? 'text-blue-600' : 'text-gray-400'
                }`} />
                <div className="flex-1">
                  <div className="font-medium flex items-center">
                    {item.label}
                    {isLastSelection && (
                      <span className="ml-2 text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full">
                        Last visited
                      </span>
                    )}
                  </div>
                  <div 
                    id={`menu-item-${item.id}-desc`}
                    className="text-xs text-gray-500 mt-0.5"
                  >
                    {item.description}
                  </div>
                </div>
              </button>
            );
          })}
        </div>
      )}

      {/* Screen reader status */}
      <div className="sr-only" aria-live="polite" aria-atomic="true">
        {isOpen ? `Navigation menu opened with ${enabledItems.length} options` : ''}
      </div>
    </div>
  );
};

export default PageMenuDropdown;