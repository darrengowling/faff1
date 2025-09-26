/**
 * Theme Configuration
 * Defines color tokens, theme variants, and utilities for Friends of PIFA
 */

// Color palette with WCAG AA compliant contrast ratios
export const colors = {
  // Brand primary colors (blue theme)
  blue: {
    50: '#eff6ff',
    100: '#dbeafe', 
    200: '#bfdbfe',
    300: '#93c5fd',
    400: '#60a5fa',
    500: '#3b82f6',
    600: '#2563eb', // Primary brand color
    700: '#1d4ed8',
    800: '#1e40af',
    900: '#1e3a8a',
    950: '#172554'
  },

  // Neutral grays for surfaces and text
  neutral: {
    0: '#ffffff',
    50: '#fafafa',
    100: '#f5f5f5',
    200: '#e5e5e5',
    300: '#d4d4d4',
    400: '#a3a3a3',
    500: '#737373',
    600: '#525252',
    700: '#404040',
    800: '#262626',
    900: '#171717',
    950: '#0a0a0a'
  },

  // Success colors (green)
  success: {
    50: '#f0fdf4',
    100: '#dcfce7',
    200: '#bbf7d0',
    300: '#86efac',
    400: '#4ade80',
    500: '#22c55e',
    600: '#16a34a',
    700: '#15803d',
    800: '#166534',
    900: '#14532d'
  },

  // Warning colors (amber/orange)
  warning: {
    50: '#fffbeb',
    100: '#fef3c7',
    200: '#fde68a',
    300: '#fcd34d',
    400: '#fbbf24',
    500: '#f59e0b',
    600: '#d97706',
    700: '#b45309',
    800: '#92400e',
    900: '#78350f'
  },

  // Error colors (red)
  error: {
    50: '#fef2f2',
    100: '#fee2e2',
    200: '#fecaca',
    300: '#fca5a5',
    400: '#f87171',
    500: '#ef4444',
    600: '#dc2626',
    700: '#b91c1c',
    800: '#991b1b',
    900: '#7f1d1d'
  }
};

// Light theme configuration
export const lightTheme = {
  // Primary brand colors
  primary: {
    main: colors.blue[600],      // #2563eb
    light: colors.blue[500],     // #3b82f6  
    dark: colors.blue[700],      // #1d4ed8
    contrast: colors.neutral[0]   // #ffffff
  },

  // Surface colors (backgrounds, cards, etc.)
  surface: {
    primary: colors.neutral[0],   // #ffffff - main background
    secondary: colors.neutral[50], // #fafafa - cards, sections
    tertiary: colors.neutral[100], // #f5f5f5 - subtle backgrounds
    border: colors.neutral[200],   // #e5e5e5 - borders
    overlay: 'rgba(0, 0, 0, 0.1)' // overlays and shadows
  },

  // Text colors
  text: {
    primary: colors.neutral[900],   // #171717 - main text
    secondary: colors.neutral[600], // #525252 - secondary text
    tertiary: colors.neutral[500],  // #737373 - muted text
    inverse: colors.neutral[0],     // #ffffff - text on dark backgrounds
    disabled: colors.neutral[400]   // #a3a3a3 - disabled text
  },

  // Status colors
  success: {
    main: colors.success[600],      // #16a34a
    light: colors.success[100],     // #dcfce7
    dark: colors.success[700],      // #15803d
    contrast: colors.neutral[0]     // #ffffff
  },

  warning: {
    main: colors.warning[600],      // #d97706
    light: colors.warning[100],     // #fef3c7
    dark: colors.warning[700],      // #b45309
    contrast: colors.neutral[0]     // #ffffff
  },

  error: {
    main: colors.error[600],        // #dc2626
    light: colors.error[100],       // #fee2e2
    dark: colors.error[700],        // #b91c1c
    contrast: colors.neutral[0]     // #ffffff
  }
};

// Dark theme configuration
export const darkTheme = {
  // Primary brand colors (adjusted for dark mode)
  primary: {
    main: colors.blue[500],      // #3b82f6 - slightly lighter for better contrast
    light: colors.blue[400],     // #60a5fa
    dark: colors.blue[600],      // #2563eb
    contrast: colors.neutral[900] // #171717
  },

  // Surface colors for dark mode
  surface: {
    primary: colors.neutral[900],   // #171717 - main dark background
    secondary: colors.neutral[800], // #262626 - cards, sections
    tertiary: colors.neutral[750],  // Custom: #1f1f1f - subtle backgrounds
    border: colors.neutral[700],    // #404040 - borders
    overlay: 'rgba(255, 255, 255, 0.1)' // light overlays for dark mode
  },

  // Text colors for dark mode
  text: {
    primary: colors.neutral[100],   // #f5f5f5 - main text on dark
    secondary: colors.neutral[300], // #d4d4d4 - secondary text
    tertiary: colors.neutral[400],  // #a3a3a3 - muted text
    inverse: colors.neutral[900],   // #171717 - text on light backgrounds
    disabled: colors.neutral[500]   // #737373 - disabled text
  },

  // Status colors (adjusted for dark mode visibility)
  success: {
    main: colors.success[500],      // #22c55e - more vibrant for dark backgrounds
    light: colors.success[900],     // #14532d - dark background variant
    dark: colors.success[400],      // #4ade80 - lighter variant
    contrast: colors.neutral[900]   // #171717
  },

  warning: {
    main: colors.warning[500],      // #f59e0b - more vibrant for dark backgrounds
    light: colors.warning[900],     // #78350f - dark background variant
    dark: colors.warning[400],      // #fbbf24 - lighter variant
    contrast: colors.neutral[900]   // #171717
  },

  error: {
    main: colors.error[500],        // #ef4444 - more vibrant for dark backgrounds
    light: colors.error[900],       // #7f1d1d - dark background variant
    dark: colors.error[400],        // #f87171 - lighter variant
    contrast: colors.neutral[900]   // #171717
  }
};

// Add custom neutral-750 for better dark mode gradients
darkTheme.surface.tertiary = '#1f1f1f';

// Theme modes
export const themes = {
  light: lightTheme,
  dark: darkTheme
};

// CSS custom properties generator
export const generateCSSVariables = (theme) => {
  return {
    // Primary colors
    '--color-primary': theme.primary.main,
    '--color-primary-light': theme.primary.light,
    '--color-primary-dark': theme.primary.dark,
    '--color-primary-contrast': theme.primary.contrast,

    // Surface colors
    '--color-surface-primary': theme.surface.primary,
    '--color-surface-secondary': theme.surface.secondary,
    '--color-surface-tertiary': theme.surface.tertiary,
    '--color-surface-border': theme.surface.border,
    '--color-surface-overlay': theme.surface.overlay,

    // Text colors
    '--color-text-primary': theme.text.primary,
    '--color-text-secondary': theme.text.secondary,
    '--color-text-tertiary': theme.text.tertiary,
    '--color-text-inverse': theme.text.inverse,
    '--color-text-disabled': theme.text.disabled,

    // Status colors
    '--color-success': theme.success.main,
    '--color-success-light': theme.success.light,
    '--color-success-dark': theme.success.dark,
    '--color-success-contrast': theme.success.contrast,

    '--color-warning': theme.warning.main,
    '--color-warning-light': theme.warning.light,
    '--color-warning-dark': theme.warning.dark,
    '--color-warning-contrast': theme.warning.contrast,

    '--color-error': theme.error.main,
    '--color-error-light': theme.error.light,
    '--color-error-dark': theme.error.dark,
    '--color-error-contrast': theme.error.contrast,
  };
};

// Tailwind color extensions
export const tailwindTheme = {
  extend: {
    colors: {
      // Theme-aware colors using CSS variables
      'theme-primary': 'var(--color-primary)',
      'theme-primary-light': 'var(--color-primary-light)',
      'theme-primary-dark': 'var(--color-primary-dark)',
      'theme-primary-contrast': 'var(--color-primary-contrast)',

      'theme-surface': 'var(--color-surface-primary)',
      'theme-surface-secondary': 'var(--color-surface-secondary)',
      'theme-surface-tertiary': 'var(--color-surface-tertiary)',
      'theme-surface-border': 'var(--color-surface-border)',

      'theme-text': 'var(--color-text-primary)',
      'theme-text-secondary': 'var(--color-text-secondary)',
      'theme-text-tertiary': 'var(--color-text-tertiary)',
      'theme-text-inverse': 'var(--color-text-inverse)',

      'theme-success': 'var(--color-success)',
      'theme-warning': 'var(--color-warning)',
      'theme-error': 'var(--color-error)',
    }
  }
};

export default { colors, themes, lightTheme, darkTheme, generateCSSVariables, tailwindTheme };