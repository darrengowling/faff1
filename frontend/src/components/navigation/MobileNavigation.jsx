/**
 * Stable Mobile Navigation Component
 * 
 * Provides stable testids and data-href attributes for reliable testing
 */

import React from 'react';
import { TESTIDS } from '../../testing/testids.ts';

const MobileNavigation = ({ onItemClick }) => {
  const navigationItems = [
    {
      id: 'home',
      label: 'Home', 
      href: '#home',
      testid: 'nav-item-home'
    },
    {
      id: 'how',
      label: 'How It Works',
      href: '#how', 
      testid: 'nav-item-how'
    },
    {
      id: 'why',
      label: 'Why Choose Us',
      href: '#why',
      testid: 'nav-item-why'  
    },
    {
      id: 'features',
      label: 'Features',
      href: '#features',
      testid: 'nav-item-features'
    },
    {
      id: 'safety', 
      label: 'Safety',
      href: '#safety',
      testid: 'nav-item-safety'
    },
    {
      id: 'faq',
      label: 'FAQ', 
      href: '#faq',
      testid: 'nav-item-faq'
    }
  ];

  const handleItemClick = (item, event) => {
    event.preventDefault();
    
    // Scroll to target section
    const target = document.querySelector(item.href);
    if (target) {
      target.scrollIntoView({ 
        behavior: 'smooth',
        block: 'start' 
      });
    }
    
    // Update hash without triggering navigation
    if (typeof window !== 'undefined') {
      window.history.replaceState(null, '', item.href);
    }
    
    // Notify parent to close drawer and update count
    onItemClick?.(item);
  };

  return (
    <div className="space-y-2">
      {navigationItems.map((item) => (
        <a
          key={item.id}
          href={item.href}
          data-testid={item.testid}
          data-href={item.href}
          onClick={(e) => handleItemClick(item, e)}
          className="block py-2 px-0 text-theme-text-secondary hover:text-theme-text transition-colors rounded-md hover:bg-theme-bg-tertiary"
        >
          {item.label}
        </a>
      ))}
    </div>
  );
};

export default MobileNavigation;