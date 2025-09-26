/**
 * Global Responsive Navbar Component
 * Features: Dropdown menus, mobile drawer, scroll-spy, full keyboard navigation
 */

import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { 
  Menu, X, ChevronDown, ChevronRight, Plus,
  Trophy, Users, Calendar, BarChart3, Settings,
  ArrowUp, ArrowDown, ArrowLeft, ArrowRight, Escape
} from 'lucide-react';
import { Button } from './ui/button';
import { HeaderBrand } from './ui/brand-badge';
import { IconThemeToggle } from './ui/theme-toggle';
import { useAuth } from '../App';
import { 
  ProductDropdownMenu, 
  MobileNavigation,
  MobileMenuButton 
} from './navigation/EnhancedNavigationMenu';
import { TESTIDS } from '../testids.js';

const GlobalNavbar = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();
  const { user } = useAuth();
  
  // State management
  const [activeSection, setActiveSection] = useState('home');
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [productDropdownOpen, setProductDropdownOpen] = useState(false);
  const [focusedIndex, setFocusedIndex] = useState(-1);
  
  // Refs for accessibility
  const mobileDrawerRef = useRef(null);
  const dropdownRef = useRef(null);
  const firstFocusableRef = useRef(null);
  const lastFocusableRef = useRef(null);

  // Handle navigation item clicks for anchor scrolling
  const handleNavItemClick = (item) => {
    if (item.href.startsWith('/#')) {
      const sectionId = item.href.substring(2); // Remove /#
      scrollToSection(sectionId);
    }
    setMobileMenuOpen(false);
  };

  // Handle product dropdown toggle
  const handleProductDropdownToggle = () => {
    setProductDropdownOpen(!productDropdownOpen);
    if (!productDropdownOpen) {
      setFocusedIndex(0);
    } else {
      setFocusedIndex(-1);
    }
  };

  // Scroll-spy functionality
  useEffect(() => {
    if (location.pathname !== '/') return;

    const handleScroll = () => {
      const sections = ['home', 'how', 'why', 'features', 'safety', 'faq', 'cta'];
      const scrollPosition = window.scrollY + 100;

      for (let i = sections.length - 1; i >= 0; i--) {
        const section = document.getElementById(sections[i]);
        if (section && section.offsetTop <= scrollPosition) {
          setActiveSection(sections[i]);
          break;
        }
      }
    };

    window.addEventListener('scroll', handleScroll);
    handleScroll(); // Initial call
    return () => window.removeEventListener('scroll', handleScroll);
  }, [location.pathname]);

  // Smooth scroll to section
  const scrollToSection = (sectionId) => {
    if (location.pathname !== '/') {
      navigate('/');
      // Wait for navigation then scroll
      setTimeout(() => {
        const element = document.getElementById(sectionId);
        if (element) {
          element.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
      }, 100);
    } else {
      const element = document.getElementById(sectionId);
      if (element) {
        element.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    }
    setMobileMenuOpen(false);
  };

  // Keyboard navigation for dropdowns
  const handleDropdownKeyDown = (e) => {
    const productDropdownItems = 5; // We know there are 5 items in product dropdown
    
    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setFocusedIndex(prev => (prev + 1) % productDropdownItems);
        break;
      case 'ArrowUp':
        e.preventDefault();
        setFocusedIndex(prev => prev <= 0 ? productDropdownItems - 1 : prev - 1);
        break;
      case 'Enter':
      case ' ':
        e.preventDefault();
        // The NavigationMenu component handles this
        break;
      case 'Escape':
        e.preventDefault();
        setProductDropdownOpen(false);
        setFocusedIndex(-1);
        break;
      case 'Tab':
        // Let natural tab behavior close the dropdown
        setProductDropdownOpen(false);
        setFocusedIndex(-1);
        break;
    }
  };

  // Mobile drawer focus trap
  useEffect(() => {
    if (mobileMenuOpen) {
      const drawer = mobileDrawerRef.current;
      if (drawer) {
        const focusableElements = drawer.querySelectorAll(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        
        if (focusableElements.length > 0) {
          firstFocusableRef.current = focusableElements[0];
          lastFocusableRef.current = focusableElements[focusableElements.length - 1];
          firstFocusableRef.current.focus();
        }
      }

      const handleKeyDown = (e) => {
        if (e.key === 'Escape') {
          setMobileMenuOpen(false);
        }
        
        if (e.key === 'Tab') {
          if (e.shiftKey) {
            if (document.activeElement === firstFocusableRef.current) {
              e.preventDefault();
              lastFocusableRef.current.focus();
            }
          } else {
            if (document.activeElement === lastFocusableRef.current) {
              e.preventDefault();
              firstFocusableRef.current.focus();
            }
          }
        }
      };

      document.addEventListener('keydown', handleKeyDown);
      return () => document.removeEventListener('keydown', handleKeyDown);
    }
  }, [mobileMenuOpen]);

  // Close dropdown when clicking outside or pressing escape
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setProductDropdownOpen(false);
        setFocusedIndex(-1);
      }
    };

    const handleGlobalKeyDown = (event) => {
      if (event.key === 'Escape' && productDropdownOpen) {
        setProductDropdownOpen(false);
        setFocusedIndex(-1);
      }
    };

    if (productDropdownOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      document.addEventListener('keydown', handleGlobalKeyDown);
      return () => {
        document.removeEventListener('mousedown', handleClickOutside);
        document.removeEventListener('keydown', handleGlobalKeyDown);
      };
    }
  }, [productDropdownOpen]);

  return (
    <header className="fixed top-0 w-full bg-theme-surface/95 backdrop-blur-sm border-b border-theme-surface-border z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Left - Brand */}
          <HeaderBrand 
            onClick={() => navigate('/')} 
            className="cursor-pointer hover:opacity-80 transition-opacity"
            data-testid={TESTIDS.navBrand}
          />
          
          {/* Center - Desktop Navigation */}
          <nav className="hidden md:flex items-center space-x-2" role="navigation">
            {/* Primary Navigation Links */}
            <PrimaryNavigation onItemClick={handleNavItemClick} />
            
            {/* Product Dropdown */}
            <ProductDropdownMenu
              isOpen={productDropdownOpen}
              onToggle={handleProductDropdownToggle}
              focusedIndex={focusedIndex}
              onFocusChange={setFocusedIndex}
              onKeyDown={handleDropdownKeyDown}
            />
          </nav>

          {/* Right - Auth Actions */}
          <div className="hidden md:flex items-center space-x-3">
            {/* Create League Button (when authenticated) */}
            {user && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => navigate('/app/leagues/new')}
                className="text-blue-600 border-blue-600 hover:bg-blue-50"
                data-testid={TESTIDS.navCreateLeagueBtn}
              >
                <Plus className="w-4 h-4 mr-1" />
                New League
              </Button>
            )}
            
            <AuthNavigation variant="desktop" />
            
            {/* Theme Toggle */}
            <IconThemeToggle className="hidden md:flex" />
          </div>

          {/* Mobile Menu Button */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-md transition-colors"
            aria-label="Toggle navigation menu"
            aria-expanded={mobileMenuOpen}
            aria-controls="mobile-navigation"
            data-testid={TESTIDS.navHamburger}
          >
            {mobileMenuOpen ? (
              <X className="w-6 h-6" />
            ) : (
              <Menu className="w-6 h-6" />
            )}
          </button>
        </div>
      </div>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div 
          className="md:hidden fixed inset-0 top-16 bg-black bg-opacity-50 z-40"
          onClick={() => setMobileMenuOpen(false)}
          aria-hidden="true"
        >
          <div
            ref={mobileDrawerRef}
            className="bg-theme-surface w-full max-w-sm h-full shadow-lg overflow-y-auto"
            id="mobile-navigation"
            role="navigation"
            aria-label="Mobile navigation menu"
            onClick={(e) => e.stopPropagation()}
            data-testid={TESTIDS.navMobileDrawer}
          >
            {/* Mobile Navigation Items */}
            <div className="py-4">
              <MobileNavigation onItemClick={handleNavItemClick} />
              
              {/* Mobile Auth Actions */}
              <div className="border-t border-gray-200 mt-4 pt-4 px-4 space-y-3">
                <AuthNavigation 
                  variant="mobile" 
                  onItemClick={(item) => {
                    handleNavItemClick(item);
                    setMobileMenuOpen(false);
                  }} 
                />
                
                {/* Mobile Theme Toggle */}
                <div className="flex items-center justify-between px-0">
                  <span className="text-sm text-gray-600">Theme</span>
                  <IconThemeToggle />
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Screen reader skip link */}
      <a 
        href="#main-content" 
        className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 bg-blue-600 text-white px-4 py-2 rounded-md z-50"
      >
        Skip to main content
      </a>
    </header>
  );
};

export default GlobalNavbar;