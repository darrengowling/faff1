/**
 * Brand Configuration
 * Centralized branding system for Friends of PIFA
 */

export interface BrandConfig {
  name: string;
  shortName: string;
  tagline: string;
  description: string;
  colors: {
    primary: string;
    secondary: string;
    accent: string;
    background: string;
    text: string;
  };
  logo: {
    src: string;
    alt: string;
    width: number;
    height: number;
  };
  favicon: {
    ico: string;
    png: string;
    apple: string;
  };
  social: {
    siteName: string;
    description: string;
    image: string;
  };
}

// Get brand name from environment or fallback
const getBrandName = (): string => {
  if (typeof window !== 'undefined') {
    // Client-side: Check for build-time injected variables
    return (window as any).__BRAND_NAME__ || 'Friends of PIFA';
  }
  
  // Build-time: Use environment variable or fallback
  return process.env.REACT_APP_BRAND_NAME || process.env.APP_BRAND_NAME || 'Friends of PIFA';
};

export const brandConfig: BrandConfig = {
  name: getBrandName(),
  shortName: 'PIFA',
  tagline: 'Football Auctions with Friends',
  description: 'Create and manage football club auctions with your friends in the most exciting competitions.',
  
  colors: {
    primary: '#2563eb', // Blue-600
    secondary: '#7c3aed', // Violet-600  
    accent: '#059669', // Emerald-600
    background: '#f8fafc', // Slate-50
    text: '#1e293b', // Slate-800
  },
  
  logo: {
    src: '/logo.png', // Placeholder - to be replaced with actual logo
    alt: `${getBrandName()} Logo`,
    width: 40,
    height: 40,
  },
  
  favicon: {
    ico: '/favicon.ico',
    png: '/favicon-32x32.png', 
    apple: '/apple-touch-icon.png',
  },
  
  social: {
    siteName: getBrandName(),
    description: 'Football Auctions with Friends - Create and manage exciting football club auctions',
    image: '/og-image.png', // Placeholder - to be replaced with actual image
  },
};

// Utility functions for easy access
export const getBrandName = () => brandConfig.name;
export const getBrandShortName = () => brandConfig.shortName;
export const getBrandTagline = () => brandConfig.tagline;
export const getBrandColors = () => brandConfig.colors;

// Theme utilities
export const getBrandTheme = () => ({
  primary: brandConfig.colors.primary,
  secondary: brandConfig.colors.secondary,
  accent: brandConfig.colors.accent,
});

// SEO utilities  
export const getBrandMeta = () => ({
  title: brandConfig.name,
  description: brandConfig.description,
  siteName: brandConfig.social.siteName,
  image: brandConfig.social.image,
});

export default brandConfig;