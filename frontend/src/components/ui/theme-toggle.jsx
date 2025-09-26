/**
 * Theme Toggle Component
 * Accessible toggle button for switching between light and dark modes
 */

import React, { useState } from 'react';
import { Sun, Moon, Monitor } from 'lucide-react';
import { useTheme } from '../../theme/ThemeProvider';
import { Button } from './button';

const ThemeToggle = ({ variant = 'icon', className = '' }) => {
  const { theme, isDark, toggleTheme } = useTheme();
  const [isTransitioning, setIsTransitioning] = useState(false);

  const handleToggle = () => {
    if (isTransitioning) return;

    setIsTransitioning(true);
    
    // Add transition effect
    document.documentElement.style.transition = 'background-color 0.3s ease, color 0.3s ease';
    
    toggleTheme();

    // Remove transition after animation
    setTimeout(() => {
      document.documentElement.style.transition = '';
      setIsTransitioning(false);
    }, 300);
  };

  // Announce theme change to screen readers
  const announceThemeChange = () => {
    const newTheme = isDark ? 'light' : 'dark';
    const message = `Switched to ${newTheme} mode`;
    
    // Create screen reader announcement
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

  const handleClick = () => {
    handleToggle();
    announceThemeChange();
  };

  const getIcon = () => {
    if (isTransitioning) {
      return <Monitor className="w-4 h-4" />;
    }
    return isDark ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />;
  };

  const getLabel = () => {
    return isDark ? 'Switch to light mode' : 'Switch to dark mode';
  };

  if (variant === 'icon') {
    return (
      <Button
        variant="ghost"
        size="sm"
        onClick={handleClick}
        disabled={isTransitioning}
        className={`theme-toggle transition-all duration-300 hover:bg-theme-surface-tertiary ${className}`}
        aria-label={getLabel()}
        title={getLabel()}
      >
        <div className="transition-transform duration-300 hover:scale-110">
          {getIcon()}
        </div>
      </Button>
    );
  }

  if (variant === 'button') {
    return (
      <Button
        variant="outline"
        size="sm"
        onClick={handleClick}
        disabled={isTransitioning}
        className={`theme-toggle ${className}`}
        aria-label={getLabel()}
      >
        <div className="flex items-center space-x-2">
          {getIcon()}
          <span className="text-sm">
            {isDark ? 'Light Mode' : 'Dark Mode'}
          </span>
        </div>
      </Button>
    );
  }

  if (variant === 'switch') {
    return (
      <button
        onClick={handleClick}
        disabled={isTransitioning}
        className={`theme-toggle-switch relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-theme-primary focus:ring-offset-2 ${
          isDark ? 'bg-theme-primary' : 'bg-gray-200'
        } ${className}`}
        role="switch"
        aria-checked={isDark}
        aria-label={getLabel()}
      >
        {/* Switch track */}
        <span className="sr-only">{getLabel()}</span>
        
        {/* Switch thumb */}
        <span
          className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform duration-300 ${
            isDark ? 'translate-x-6' : 'translate-x-1'
          }`}
        >
          {/* Icon inside thumb */}
          <span className="flex h-full w-full items-center justify-center">
            {isDark ? (
              <Moon className="w-2 h-2 text-theme-primary" />
            ) : (
              <Sun className="w-2 h-2 text-gray-400" />
            )}
          </span>
        </span>
      </button>
    );
  }

  return null;
};

// Specialized variants for different use cases
export const IconThemeToggle = ({ className }) => (
  <ThemeToggle variant="icon" className={className} />
);

export const ButtonThemeToggle = ({ className }) => (
  <ThemeToggle variant="button" className={className} />
);

export const SwitchThemeToggle = ({ className }) => (
  <ThemeToggle variant="switch" className={className} />
);

export default ThemeToggle;