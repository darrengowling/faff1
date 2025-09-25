/**
 * League Switcher Component
 * Dropdown to switch between multiple leagues with context awareness
 */

import React, { useState, useRef, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { 
  ChevronDown, Trophy, Crown, Users, Check, ChevronsUpDown
} from 'lucide-react';
import { Button } from './button';
import { Badge } from './badge';

const LeagueSwitcher = ({ 
  leagues = [], 
  selectedLeague, 
  onLeagueChange,
  user,
  className = '' 
}) => {
  const { t } = useTranslation();
  const [isOpen, setIsOpen] = useState(false);
  const [focusedIndex, setFocusedIndex] = useState(-1);
  
  const dropdownRef = useRef(null);
  const triggerRef = useRef(null);

  // Don't render if only one or no leagues
  if (leagues.length <= 1) {
    return null;
  }

  // Sort leagues: selected first, then by role (commissioner first), then alphabetically
  const sortedLeagues = [...leagues].sort((a, b) => {
    if (selectedLeague && a.id === selectedLeague.id) return -1;
    if (selectedLeague && b.id === selectedLeague.id) return 1;
    
    const aIsCommissioner = a.commissioner_id === user?.id;
    const bIsCommissioner = b.commissioner_id === user?.id;
    
    if (aIsCommissioner && !bIsCommissioner) return -1;
    if (!aIsCommissioner && bIsCommissioner) return 1;
    
    return a.name.localeCompare(b.name);
  });

  // Handle league selection
  const handleSelect = (league) => {
    onLeagueChange(league);
    setIsOpen(false);
    setFocusedIndex(-1);
    
    // Announce to screen readers
    const message = `Switched to ${league.name}`;
    announceToScreenReader(message);
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
    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        if (!isOpen) {
          setIsOpen(true);
          setFocusedIndex(0);
        } else {
          setFocusedIndex(prev => 
            prev < sortedLeagues.length - 1 ? prev + 1 : 0
          );
        }
        break;
        
      case 'ArrowUp':
        e.preventDefault();
        if (isOpen) {
          setFocusedIndex(prev => 
            prev > 0 ? prev - 1 : sortedLeagues.length - 1
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
          handleSelect(sortedLeagues[focusedIndex]);
        }
        break;
        
      case 'Escape':
        e.preventDefault();
        setIsOpen(false);
        setFocusedIndex(-1);
        triggerRef.current?.focus();
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

  const getLeagueDisplayName = (league) => {
    const isCommissioner = league.commissioner_id === user?.id;
    return `${league.name}${isCommissioner ? ' (Commissioner)' : ''}`;
  };

  const getLeagueStatus = (league) => {
    if (league.status === 'active') return { label: 'Live', variant: 'default', color: 'bg-green-600' };
    if (league.status === 'ready') return { label: 'Ready', variant: 'secondary', color: 'bg-blue-600' };
    return { label: league.status, variant: 'outline', color: 'bg-gray-400' };
  };

  return (
    <div ref={dropdownRef} className={`relative ${className}`}>
      <Button
        ref={triggerRef}
        onClick={() => setIsOpen(!isOpen)}
        onKeyDown={handleKeyDown}
        variant="outline"
        className="w-full justify-between min-w-64 bg-white hover:bg-gray-50 border-gray-300"
        aria-expanded={isOpen}
        aria-haspopup="listbox"
        aria-label="Switch league"
      >
        <div className="flex items-center space-x-3 min-w-0">
          <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center flex-shrink-0">
            <Trophy className="w-4 h-4 text-white" />
          </div>
          <div className="flex-1 text-left min-w-0">
            <div className="font-medium text-gray-900 truncate">
              {selectedLeague ? selectedLeague.name : 'Select League'}
            </div>
            {selectedLeague && (
              <div className="text-xs text-gray-500 flex items-center space-x-2">
                <span>{selectedLeague.member_count} members</span>
                {selectedLeague.commissioner_id === user?.id && (
                  <span className="flex items-center">
                    <Crown className="w-3 h-3 mr-1" />
                    Commissioner
                  </span>
                )}
              </div>
            )}
          </div>
        </div>
        <ChevronsUpDown className="w-4 h-4 text-gray-400 flex-shrink-0" />
      </Button>

      {isOpen && (
        <div
          className="absolute top-full left-0 mt-1 w-full bg-white rounded-lg shadow-lg border border-gray-200 py-2 z-50 max-h-64 overflow-y-auto"
          role="listbox"
          aria-label="Select league"
        >
          <div className="px-3 py-2 text-xs font-medium text-gray-500 border-b border-gray-100">
            Select League ({leagues.length})
          </div>
          
          {sortedLeagues.map((league, index) => {
            const isFocused = index === focusedIndex;
            const isSelected = selectedLeague?.id === league.id;
            const isCommissioner = league.commissioner_id === user?.id;
            const status = getLeagueStatus(league);
            
            return (
              <button
                key={league.id}
                onClick={() => handleSelect(league)}
                onMouseEnter={() => setFocusedIndex(index)}
                className={`w-full flex items-center space-x-3 px-3 py-3 text-left hover:bg-gray-50 transition-colors ${
                  isFocused ? 'bg-blue-50' : ''
                } ${isSelected ? 'bg-blue-25 border-l-2 border-blue-500' : ''}`}
                role="option"
                aria-selected={isSelected}
                tabIndex={isFocused ? 0 : -1}
              >
                {/* League Icon */}
                <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0">
                  <Trophy className="w-4 h-4 text-blue-600" />
                </div>

                {/* League Info */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center space-x-2">
                    <span className="font-medium text-gray-900 truncate">
                      {league.name}
                    </span>
                    {isCommissioner && (
                      <Crown className="w-3 h-3 text-amber-500 flex-shrink-0" />
                    )}
                    {isSelected && (
                      <Check className="w-4 h-4 text-blue-600 flex-shrink-0" />
                    )}
                  </div>
                  <div className="flex items-center space-x-2 mt-1">
                    <span className="text-xs text-gray-500">
                      {league.member_count} members
                    </span>
                    <Badge 
                      variant={status.variant}
                      className="text-xs px-1.5 py-0.5"
                    >
                      {status.label}
                    </Badge>
                  </div>
                </div>
              </button>
            );
          })}
        </div>
      )}

      {/* Screen reader status */}
      <div className="sr-only" aria-live="polite">
        {selectedLeague ? `Currently selected: ${getLeagueDisplayName(selectedLeague)}` : 'No league selected'}
      </div>
    </div>
  );
};

export default LeagueSwitcher;