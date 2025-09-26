/**
 * Theme Provider
 * React Context for theme management with dark mode support and persistence
 */

import React, { createContext, useContext, useEffect, useState } from 'react';
import { themes, generateCSSVariables } from './theme-config';

// Create Theme Context
const ThemeContext = createContext({
  theme: 'light',
  isDark: false,
  toggleTheme: () => {},
  setTheme: () => {},
});

// Custom hook to use theme
export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};

// Theme Provider Component
export const ThemeProvider = ({ children }) => {
  const [theme, setThemeState] = useState('light');
  const [isInitialized, setIsInitialized] = useState(false);

  // Initialize theme from localStorage or system preference
  useEffect(() => {
    const initializeTheme = () => {
      try {
        // Check localStorage first
        const savedTheme = localStorage.getItem('theme-preference');
        
        if (savedTheme && (savedTheme === 'light' || savedTheme === 'dark')) {
          setThemeState(savedTheme);
        } else {
          // Check system preference
          const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
          setThemeState(prefersDark ? 'dark' : 'light');
        }
      } catch (error) {
        console.warn('Theme initialization failed, using light theme:', error);
        setThemeState('light');
      }
      
      setIsInitialized(true);
    };

    initializeTheme();
  }, []);

  // Apply CSS variables when theme changes
  useEffect(() => {
    if (!isInitialized) return;

    const applyTheme = () => {
      try {
        const themeConfig = themes[theme];
        const cssVariables = generateCSSVariables(themeConfig);
        
        // Apply CSS variables to root
        const root = document.documentElement;
        Object.entries(cssVariables).forEach(([property, value]) => {
          root.style.setProperty(property, value);
        });

        // Apply theme class to body for additional styling
        document.body.className = document.body.className.replace(/theme-\w+/g, '');
        document.body.classList.add(`theme-${theme}`);

        // Update meta theme-color for mobile browsers
        const metaThemeColor = document.querySelector('meta[name="theme-color"]');
        if (metaThemeColor) {
          metaThemeColor.content = themeConfig.surface.primary;
        } else {
          const meta = document.createElement('meta');
          meta.name = 'theme-color';
          meta.content = themeConfig.surface.primary;
          document.head.appendChild(meta);
        }
      } catch (error) {
        console.error('Failed to apply theme:', error);
      }
    };

    applyTheme();
  }, [theme, isInitialized]);

  // Save theme preference to localStorage
  const setTheme = (newTheme) => {
    try {
      if (newTheme === 'light' || newTheme === 'dark') {
        setThemeState(newTheme);
        localStorage.setItem('theme-preference', newTheme);
      }
    } catch (error) {
      console.error('Failed to save theme preference:', error);
    }
  };

  // Toggle between light and dark themes
  const toggleTheme = () => {
    const newTheme = theme === 'light' ? 'dark' : 'light';
    setTheme(newTheme);
  };

  // Listen for system theme changes
  useEffect(() => {
    if (!isInitialized) return;

    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    
    const handleSystemThemeChange = (e) => {
      // Only update if user hasn't manually set a preference
      const savedTheme = localStorage.getItem('theme-preference');
      if (!savedTheme) {
        setThemeState(e.matches ? 'dark' : 'light');
      }
    };

    mediaQuery.addEventListener('change', handleSystemThemeChange);
    
    return () => {
      mediaQuery.removeEventListener('change', handleSystemThemeChange);
    };
  }, [isInitialized]);

  // Prevent flash of unstyled content
  if (!isInitialized) {
    return (
      <div className="theme-loading">
        {/* Minimal loading state with inline styles to prevent FOUC */}
        <style>{`
          .theme-loading {
            background: #ffffff;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
          }
          @media (prefers-color-scheme: dark) {
            .theme-loading {
              background: #171717;
              color: #f5f5f5;
            }
          }
        `}</style>
        <div className="animate-spin w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full"></div>
      </div>
    );
  }

  const contextValue = {
    theme,
    isDark: theme === 'dark',
    toggleTheme,
    setTheme,
    isInitialized
  };

  return (
    <ThemeContext.Provider value={contextValue}>
      {children}
    </ThemeContext.Provider>
  );
};

// Theme-aware utility component for conditional rendering
export const ThemeAware = ({ light, dark, children }) => {
  const { isDark } = useTheme();
  
  if (light && dark) {
    return isDark ? dark : light;
  }
  
  return children;
};

export default ThemeProvider;