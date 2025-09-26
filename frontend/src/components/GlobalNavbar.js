/**
 * Global Responsive Navbar Component
 * Features: Dropdown menus, mobile drawer, scroll-spy, full keyboard navigation
 */

import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { 
  Menu, X, ChevronDown, ChevronRight,
  Trophy, Users, Calendar, BarChart3, Settings,
  ArrowUp, ArrowDown, ArrowLeft, ArrowRight, Escape
} from 'lucide-react';
import { Button } from './ui/button';
import { HeaderBrand } from './ui/brand-badge';
import { IconThemeToggle } from './ui/theme-toggle';
import { useAuth } from '../App';

const GlobalNavbar = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();
  const { user } = useAuth();
  
  // State management
  const [activeSection, setActiveSection] = useState('home');
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [activeDropdown, setActiveDropdown] = useState(null);
  const [focusedIndex, setFocusedIndex] = useState(-1);
  
  // Refs for accessibility
  const mobileDrawerRef = useRef(null);
  const dropdownRef = useRef(null);
  const firstFocusableRef = useRef(null);
  const lastFocusableRef = useRef(null);

  // Navigation configuration
  const navItems = [
    {
      id: 'product',
      label: 'Product',
      type: 'dropdown',
      items: [
        { 
          id: 'auction-room', 
          label: 'Auction Room', 
          icon: Trophy,
          description: 'Live bidding experience',
          action: () => user ? navigate('/auction') : navigate('/login')
        },
        { 
          id: 'roster', 
          label: 'My Roster', 
          icon: Users,
          description: 'Manage your teams',
          action: () => user ? navigate('/clubs') : navigate('/login')
        },
        { 
          id: 'fixtures', 
          label: 'Fixtures', 
          icon: Calendar,
          description: 'Match schedules & results',
          action: () => user ? navigate('/fixtures') : navigate('/login')
        },
        { 
          id: 'leaderboard', 
          label: 'Leaderboard', 
          icon: BarChart3,
          description: 'Rankings & statistics',
          action: () => user ? navigate('/leaderboard') : navigate('/login')
        },
        { 
          id: 'admin', 
          label: 'League Admin', 
          icon: Settings,
          description: 'Manage your leagues',
          action: () => user ? navigate('/admin') : navigate('/login')
        }
      ]
    },
    {
      id: 'how',
      label: 'How it Works',
      type: 'anchor',
      action: () => scrollToSection('how')
    },
    {
      id: 'why',
      label: 'Why FoP',
      type: 'anchor', 
      action: () => scrollToSection('why')
    },
    {
      id: 'faq',
      label: 'FAQ',
      type: 'anchor',
      action: () => scrollToSection('faq')
    }
  ];

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
  const handleDropdownKeyDown = (e, items) => {
    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setFocusedIndex(prev => (prev + 1) % items.length);
        break;
      case 'ArrowUp':
        e.preventDefault();
        setFocusedIndex(prev => prev <= 0 ? items.length - 1 : prev - 1);
        break;
      case 'Enter':
      case ' ':
        e.preventDefault();
        if (focusedIndex >= 0 && items[focusedIndex]) {
          items[focusedIndex].action();
          setActiveDropdown(null);
          setFocusedIndex(-1);
        }
        break;
      case 'Escape':
        e.preventDefault();
        setActiveDropdown(null);
        setFocusedIndex(-1);
        break;
      case 'Tab':
        // Let natural tab behavior close the dropdown
        setActiveDropdown(null);
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

  // Desktop Dropdown Component
  const DesktopDropdown = ({ item, isActive }) => {
    const dropdownItems = item.items || [];
    
    return (
      <div className="relative group">
        <button
          onClick={() => setActiveDropdown(isActive ? null : item.id)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault();
              setActiveDropdown(isActive ? null : item.id);
              setFocusedIndex(0);
            }
          }}
          className={`flex items-center space-x-1 px-3 py-2 text-sm font-medium transition-colors rounded-md hover:text-blue-600 hover:bg-blue-50 ${
            isActive ? 'text-blue-600 bg-blue-50' : 'text-gray-700'
          }`}
          aria-expanded={isActive}
          aria-haspopup="true"
          id={`dropdown-trigger-${item.id}`}
          aria-controls={`dropdown-menu-${item.id}`}
        >
          <span>{item.label}</span>
          <ChevronDown className={`w-4 h-4 transition-transform ${isActive ? 'rotate-180' : ''}`} />
        </button>

        {isActive && (
          <div
            ref={dropdownRef}
            className="absolute top-full left-0 mt-1 w-64 bg-theme-surface rounded-lg shadow-lg border border-theme-surface-border py-2 z-[60]"
            role="menu"
            aria-labelledby={`dropdown-trigger-${item.id}`}
            id={`dropdown-menu-${item.id}`}
            onKeyDown={(e) => handleDropdownKeyDown(e, dropdownItems)}
          >
            {dropdownItems.map((dropdownItem, index) => (
              <button
                key={dropdownItem.id}
                onClick={() => {
                  dropdownItem.action();
                  setActiveDropdown(null);
                  setFocusedIndex(-1);
                }}
                className={`w-full flex items-start space-x-3 px-4 py-3 text-left hover:bg-gray-50 transition-colors ${
                  index === focusedIndex ? 'bg-blue-50 text-blue-600' : 'text-gray-700'
                }`}
                role="menuitem"
                tabIndex={index === focusedIndex ? 0 : -1}
                onMouseEnter={() => setFocusedIndex(index)}
              >
                <dropdownItem.icon className={`w-5 h-5 mt-0.5 flex-shrink-0 ${
                  index === focusedIndex ? 'text-blue-600' : 'text-gray-400'
                }`} />
                <div>
                  <div className="font-medium">{dropdownItem.label}</div>
                  <div className="text-xs text-gray-500 mt-0.5">{dropdownItem.description}</div>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
    );
  };

  // Mobile Nested Menu Item Component
  const MobileNestedItem = ({ item, depth = 0 }) => {
    const [expanded, setExpanded] = useState(false);
    const hasChildren = item.items && item.items.length > 0;
    const paddingLeft = depth * 16 + 16;

    if (hasChildren) {
      return (
        <div>
          <button
            onClick={() => setExpanded(!expanded)}
            className={`w-full flex items-center justify-between px-4 py-3 text-left font-medium transition-colors hover:bg-gray-50`}
            style={{ paddingLeft }}
            aria-expanded={expanded}
            aria-controls={`mobile-submenu-${item.id}`}
          >
            <span className="text-gray-900">{item.label}</span>
            <ChevronRight className={`w-5 h-5 text-gray-400 transition-transform ${expanded ? 'rotate-90' : ''}`} />
          </button>
          
          {expanded && (
            <div id={`mobile-submenu-${item.id}`} className="bg-gray-50">
              {item.items.map((subItem) => (
                <MobileNestedItem 
                  key={subItem.id} 
                  item={subItem} 
                  depth={depth + 1}
                />
              ))}
            </div>
          )}
        </div>
      );
    }

    return (
      <button
        onClick={() => {
          item.action();
          setMobileMenuOpen(false);
        }}
        className="w-full flex items-center space-x-3 px-4 py-3 text-left transition-colors hover:bg-gray-50"
        style={{ paddingLeft }}
      >
        {item.icon && <item.icon className="w-5 h-5 text-gray-400" />}
        <div>
          <div className="font-medium text-gray-900">{item.label}</div>
          {item.description && (
            <div className="text-sm text-gray-500">{item.description}</div>
          )}
        </div>
      </button>
    );
  };

  // Close dropdown when clicking outside or pressing escape
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setActiveDropdown(null);
        setFocusedIndex(-1);
      }
    };

    const handleGlobalKeyDown = (event) => {
      if (event.key === 'Escape' && activeDropdown) {
        setActiveDropdown(null);
        setFocusedIndex(-1);
      }
    };

    if (activeDropdown) {
      document.addEventListener('mousedown', handleClickOutside);
      document.addEventListener('keydown', handleGlobalKeyDown);
      return () => {
        document.removeEventListener('mousedown', handleClickOutside);
        document.removeEventListener('keydown', handleGlobalKeyDown);
      };
    }
  }, [activeDropdown]);

  return (
    <header className="fixed top-0 w-full bg-theme-surface/95 backdrop-blur-sm border-b border-theme-surface-border z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Left - Brand */}
          <HeaderBrand 
            onClick={() => navigate('/')} 
            className="cursor-pointer hover:opacity-80 transition-opacity" 
          />
          
          {/* Center - Desktop Navigation */}
          <nav className="hidden md:flex items-center space-x-2" role="navigation">
            {navItems.map((item) => {
              const isActive = item.type === 'dropdown' 
                ? activeDropdown === item.id
                : item.type === 'anchor' 
                  ? activeSection === item.id
                  : false;

              if (item.type === 'dropdown') {
                return (
                  <DesktopDropdown 
                    key={item.id} 
                    item={item} 
                    isActive={isActive}
                  />
                );
              }

              return (
                <button
                  key={item.id}
                  onClick={item.action}
                  className={`px-3 py-2 text-sm font-medium transition-colors rounded-md hover:text-blue-600 hover:bg-blue-50 ${
                    isActive ? 'text-blue-600 bg-blue-50' : 'text-gray-700'
                  }`}
                >
                  {item.label}
                </button>
              );
            })}
          </nav>

          {/* Right - Auth Actions */}
          <div className="hidden md:flex items-center space-x-3">
            {user ? (
              <div className="flex items-center space-x-3">
                <span className="text-sm text-gray-600">
                  Welcome, {user.name || user.email}
                </span>
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={() => navigate('/dashboard')}
                >
                  Dashboard
                </Button>
              </div>
            ) : (
              <>
                <Button 
                  variant="ghost" 
                  size="sm"
                  onClick={() => navigate('/login')}
                >
                  Sign In
                </Button>
                <Button 
                  size="sm"
                  onClick={() => navigate('/login')}
                >
                  Get Started
                </Button>
              </>
            )}
            
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
            className="bg-white w-full max-w-sm h-full shadow-lg overflow-y-auto"
            id="mobile-navigation"
            role="navigation"
            aria-label="Mobile navigation menu"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Mobile Navigation Items */}
            <div className="py-4">
              {navItems.map((item) => (
                <MobileNestedItem key={item.id} item={item} />
              ))}
              
              {/* Mobile Auth Actions */}
              <div className="border-t border-gray-200 mt-4 pt-4 px-4 space-y-3">
                {user ? (
                  <div className="space-y-3">
                    <div className="text-sm text-gray-600 px-0">
                      Welcome, {user.name || user.email}
                    </div>
                    <Button 
                      variant="outline" 
                      className="w-full"
                      onClick={() => {
                        navigate('/dashboard');
                        setMobileMenuOpen(false);
                      }}
                    >
                      Dashboard
                    </Button>
                  </div>
                ) : (
                  <div className="space-y-3">
                    <Button 
                      variant="ghost" 
                      className="w-full"
                      onClick={() => {
                        navigate('/login');
                        setMobileMenuOpen(false);
                      }}
                    >
                      Sign In
                    </Button>
                    <Button 
                      className="w-full"
                      onClick={() => {
                        navigate('/login');
                        setMobileMenuOpen(false);
                      }}
                    >
                      Get Started
                    </Button>
                  </div>
                )}
                
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