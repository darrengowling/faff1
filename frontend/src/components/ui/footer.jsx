/**
 * Footer Component
 * Comprehensive footer with brand, manifesto, disclaimers, and legal links
 */

import React from 'react';
import { useTranslation } from 'react-i18next';
import { 
  Heart, ExternalLink, Shield, Users, Trophy 
} from 'lucide-react';
import { BrandBadge, FooterBrand } from './brand-badge';
import { getBrandName } from '../../brand';
import { FooterNavigation } from '../navigation/NavigationMenu';

const Footer = ({ variant = 'default', className = '' }) => {
  const { t } = useTranslation();
  const currentYear = new Date().getFullYear();

  // Different variants for different contexts
  const isMinimal = variant === 'minimal';
  const isLanding = variant === 'landing';
  const isInApp = variant === 'in-app';

  if (isMinimal) {
    return (
      <footer className={`bg-gray-50 border-t border-gray-200 py-4 ${className}`}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col sm:flex-row items-center justify-between text-sm text-gray-600">
            <div className="flex items-center space-x-2">
              <span>{t('footer.copyright', { year: currentYear, brandName: getBrandName() })}</span>
            </div>
            <div className="flex items-center space-x-4 mt-2 sm:mt-0">
              <span className="text-xs">{t('footer.disclaimer')}</span>
            </div>
          </div>
        </div>
      </footer>
    );
  }

  return (
    <footer className={`bg-white border-t border-gray-200 ${className}`}>
      {/* Main footer content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          
          {/* Brand Section */}
          <div className="lg:col-span-1">
            <FooterBrand className="mb-4" />
            <p className="text-sm text-gray-600 mb-4">
              {t('branding.subtag')}
            </p>
            <div className="flex items-start space-x-2 text-sm text-gray-700">
              <Shield className="w-4 h-4 mt-0.5 text-blue-600 flex-shrink-0" />
              <span>{t('footer.manifesto')}</span>
            </div>
          </div>

          {/* Disclaimers Section */}
          <div className="lg:col-span-2">
            <h3 className="font-semibold text-gray-900 mb-4">Fair Play Commitment</h3>
            <div className="space-y-3 text-sm text-gray-600">
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex items-start space-x-2">
                  <Trophy className="w-4 h-4 mt-0.5 text-blue-600 flex-shrink-0" />
                  <div>
                    <p className="font-medium text-blue-900 mb-1">{t('footer.disclaimer')}</p>
                    <p className="text-blue-700">{t('footer.legal.noWagering')}</p>
                  </div>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                <Users className="w-4 h-4 text-gray-500" />
                <span>{t('footer.legal.forFun')}</span>
              </div>
              <div className="text-xs text-gray-500">
                {t('footer.legal.ageRestriction')}
              </div>
            </div>
          </div>

          {/* Links Section */}
          <div className="lg:col-span-1">
            <h3 className="font-semibold text-gray-900 mb-4">Legal & Support</h3>
            <div className="space-y-2">
              <FooterNavigation className="space-y-2" />
            </div>
          </div>
        </div>
      </div>

      {/* Bottom bar */}
      <div className="bg-gray-50 border-t border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex flex-col sm:flex-row items-center justify-between text-sm text-gray-600">
            <div className="flex items-center space-x-4">
              <span>{t('footer.copyright', { year: currentYear, brandName: getBrandName() })}</span>
              {!isInApp && (
                <span className="hidden sm:inline-flex items-center space-x-1">
                  <span>{t('footer.madeWith')}</span>
                </span>
              )}
            </div>
            <div className="flex items-center space-x-4 mt-2 sm:mt-0">
              <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded-full">
                100% Free to Play
              </span>
              <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded-full">
                No Real Money
              </span>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
};

// Specialized footer variants
export const LandingFooter = ({ className }) => (
  <Footer variant="landing" className={className} />
);

export const InAppFooter = ({ className }) => (
  <Footer variant="in-app" className={className} />
);

export const MinimalFooter = ({ className }) => (
  <Footer variant="minimal" className={className} />
);

export default Footer;