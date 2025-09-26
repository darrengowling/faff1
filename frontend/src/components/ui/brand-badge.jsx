/**
 * Brand Badge Component
 * Reusable branding component for headers, footers, and auth screens
 */

import React from 'react';
import { brandConfig, getBrandName, getBrandTagline } from '../../brand';
import { Users } from 'lucide-react';

export const BrandBadge = ({
  variant = 'full',
  size = 'md',
  className = '',
  showTagline = false,
  onClick
}) => {
  const brandName = getBrandName();
  const tagline = getBrandTagline();
  
  // Size configurations
  const sizeConfig = {
    sm: {
      iconSize: 'w-4 h-4',
      textSize: 'text-sm',
      taglineSize: 'text-xs',
      spacing: 'space-x-1',
      padding: 'px-2 py-1'
    },
    md: {
      iconSize: 'w-5 h-5',
      textSize: 'text-base',
      taglineSize: 'text-xs', 
      spacing: 'space-x-2',
      padding: 'px-3 py-2'
    },
    lg: {
      iconSize: 'w-6 h-6',
      textSize: 'text-lg',
      taglineSize: 'text-sm',
      spacing: 'space-x-3',
      padding: 'px-4 py-3'
    }
  };
  
  const config = sizeConfig[size];
  
  // Brand icon (using Users as placeholder - can be replaced with actual logo)
  const BrandIcon = () => (
    <div className={`${config.iconSize} flex items-center justify-center bg-blue-600 rounded-full`}>
      <Users className={`${config.iconSize === 'w-4 h-4' ? 'w-3 h-3' : config.iconSize === 'w-5 h-5' ? 'w-4 h-4' : 'w-5 h-5'} text-white`} />
    </div>
  );
  
  // Full variant with icon and text
  if (variant === 'full') {
    return (
      <div 
        className={`flex items-center ${config.spacing} ${onClick ? 'cursor-pointer hover:opacity-80 transition-opacity' : ''} ${className}`}
        onClick={onClick}
        role={onClick ? 'button' : undefined}
        tabIndex={onClick ? 0 : undefined}
      >
        <BrandIcon />
        <div className="flex flex-col">
          <span className={`font-bold text-gray-900 ${config.textSize}`}>
            {brandName}
          </span>
          {showTagline && (
            <span className={`text-gray-600 ${config.taglineSize}`}>
              {tagline}
            </span>
          )}
        </div>
      </div>
    );
  }
  
  // Compact variant with just text
  if (variant === 'compact') {
    return (
      <div 
        className={`${onClick ? 'cursor-pointer hover:opacity-80 transition-opacity' : ''} ${className}`}
        onClick={onClick}
        role={onClick ? 'button' : undefined}
        tabIndex={onClick ? 0 : undefined}
      >
        <span className={`font-bold text-gray-900 ${config.textSize}`}>
          {brandName}
        </span>
        {showTagline && (
          <div className={`text-gray-600 ${config.taglineSize}`}>
            {tagline}
          </div>
        )}
      </div>
    );
  }
  
  // Icon-only variant
  if (variant === 'icon-only') {
    return (
      <div 
        className={`${onClick ? 'cursor-pointer hover:opacity-80 transition-opacity' : ''} ${className}`}
        onClick={onClick}
        role={onClick ? 'button' : undefined}
        tabIndex={onClick ? 0 : undefined}
        title={brandName}
        aria-label={brandName}
      >
        <BrandIcon />
      </div>
    );
  }
  
  return null;
};

// Specialized variants for common use cases
export const HeaderBrand = ({ onClick, className }) => (
  <BrandBadge 
    variant="full" 
    size="md" 
    onClick={onClick}
    className={className}
  />
);

export const FooterBrand = ({ className }) => (
  <BrandBadge 
    variant="full" 
    size="sm" 
    showTagline={true}
    className={className}
  />
);

export const AuthBrand = ({ className }) => (
  <BrandBadge 
    variant="full" 
    size="lg" 
    showTagline={true}
    className={className}
  />
);

export const CompactBrand = ({ className }) => (
  <BrandBadge 
    variant="compact" 
    size="md"
    className={className}
  />
);

export const FooterBrand = ({ className }) => (
  <BrandBadge 
    variant="full" 
    size="sm"
    showTagline={false}
    className={className}
  />
);

export default BrandBadge;