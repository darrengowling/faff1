/**
 * Sticky In-Page Navigation Component
 * Features: Section tabs, scroll-spy, smooth scrolling, hash updates, accessibility
 */

import React, { useState, useEffect, useRef } from 'react';
import { useLocation } from 'react-router-dom';
import { TESTIDS } from '../testids.js';

const StickyPageNav = () => {
  const location = useLocation();
  const [activeSection, setActiveSection] = useState('home');
  const [isVisible, setIsVisible] = useState(false);
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false);
  const navRef = useRef(null);
  const observerRef = useRef(null);

  // Navigation sections configuration
  const sections = [
    { id: 'home', label: 'Home', icon: '🏠', testId: TESTIDS.inPageTabHome },
    { id: 'how', label: 'How it Works', icon: '⚙️', testId: TESTIDS.inPageTabHow },
    { id: 'why', label: 'Why FoP', icon: '💡', testId: TESTIDS.inPageTabWhy },
    { id: 'features', label: 'Features', icon: '🚀', testId: TESTIDS.inPageTabFeatures },
    { id: 'safety', label: 'Fair Play', icon: '🛡️', testId: TESTIDS.inPageTabFair },
    { id: 'faq', label: 'FAQ', icon: '❓', testId: TESTIDS.inPageTabFaq }
  ];

  // Check for reduced motion preference
  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    setPrefersReducedMotion(mediaQuery.matches);
    
    const handleChange = (e) => setPrefersReducedMotion(e.matches);
    mediaQuery.addEventListener('change', handleChange);
    
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, []);

  // Intersection Observer for scroll spy
  useEffect(() => {
    if (location.pathname !== '/') return;

    const sectionElements = sections.map(section => ({
      id: section.id,
      element: document.getElementById(section.id)
    })).filter(item => item.element);

    if (sectionElements.length === 0) return;

    // Calculate offset to account for sticky headers
    const getOffset = () => {
      const globalNavbar = document.querySelector('header');
      const stickyNav = navRef.current;
      return (globalNavbar?.offsetHeight || 64) + (stickyNav?.offsetHeight || 64) + 20;
    };

    const observerOptions = {
      root: null,
      rootMargin: `-${getOffset()}px 0px -50% 0px`,
      threshold: [0, 0.1, 0.5, 1]
    };

    observerRef.current = new IntersectionObserver((entries) => {
      let mostVisible = null;
      let maxRatio = 0;

      entries.forEach((entry) => {
        if (entry.isIntersecting && entry.intersectionRatio > maxRatio) {
          maxRatio = entry.intersectionRatio;
          mostVisible = entry.target.id;
        }
      });

      if (mostVisible) {
        setActiveSection(mostVisible);
        // Update browser hash without triggering scroll
        if (window.location.hash !== `#${mostVisible}`) {
          window.history.replaceState(null, null, `#${mostVisible}`);
        }
      }
    }, observerOptions);

    sectionElements.forEach(({ element }) => {
      observerRef.current.observe(element);
    });

    return () => {
      if (observerRef.current) {
        observerRef.current.disconnect();
      }
    };
  }, [location.pathname, sections]);

  // Show/hide sticky nav based on scroll position
  useEffect(() => {
    if (location.pathname !== '/') return;

    const handleScroll = () => {
      const heroSection = document.getElementById('home');
      if (heroSection) {
        const heroBottom = heroSection.offsetTop + heroSection.offsetHeight - 200;
        const shouldShow = window.scrollY > heroBottom;
        setIsVisible(shouldShow);
      }
    };

    handleScroll(); // Initial call
    window.addEventListener('scroll', handleScroll, { passive: true });
    
    return () => window.removeEventListener('scroll', handleScroll);
  }, [location.pathname]);

  // Smooth scroll to section with proper offset
  const scrollToSection = (sectionId) => {
    const element = document.getElementById(sectionId);
    if (!element) return;

    // Calculate offset for proper positioning
    const globalNavbar = document.querySelector('header');
    const stickyNav = navRef.current;
    const offset = (globalNavbar?.offsetHeight || 64) + (stickyNav?.offsetHeight || 64) + 10;
    
    const elementPosition = element.offsetTop - offset;
    
    // Update hash immediately for better UX
    window.history.pushState(null, null, `#${sectionId}`);
    
    if (prefersReducedMotion) {
      // Instant scroll for reduced motion
      window.scrollTo(0, elementPosition);
    } else {
      // Smooth scroll
      window.scrollTo({
        top: elementPosition,
        behavior: 'smooth'
      });
    }
  };

  // Handle keyboard navigation
  const handleKeyDown = (e, sectionId) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      scrollToSection(sectionId);
    }
    
    // Arrow key navigation
    if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
      e.preventDefault();
      const currentIndex = sections.findIndex(s => s.id === sectionId);
      let nextIndex;
      
      if (e.key === 'ArrowLeft') {
        nextIndex = currentIndex > 0 ? currentIndex - 1 : sections.length - 1;
      } else {
        nextIndex = currentIndex < sections.length - 1 ? currentIndex + 1 : 0;
      }
      
      const nextButton = navRef.current?.querySelector(`[data-section="${sections[nextIndex].id}"]`);
      nextButton?.focus();
    }
  };

  // Don't render on non-landing pages
  if (location.pathname !== '/') return null;

  return (
    <nav
      ref={navRef}
      className={`sticky top-16 bg-white/95 backdrop-blur-sm border-b border-gray-200 z-40 transition-all duration-300 ${
        isVisible ? 'translate-y-0 opacity-100' : '-translate-y-full opacity-0'
      }`}
      role="navigation"
      aria-label="Page sections navigation"
      style={{ pointerEvents: 'none' }}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-center">
          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center space-x-1 py-3">
            {sections.map((section, index) => (
              <button
                key={section.id}
                data-section={section.id}
                onClick={() => scrollToSection(section.id)}
                onKeyDown={(e) => handleKeyDown(e, section.id)}
                className={`px-4 py-2 text-sm font-medium rounded-lg transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${
                  activeSection === section.id
                    ? 'bg-blue-100 text-blue-700 shadow-sm'
                    : 'text-gray-600 hover:text-blue-600 hover:bg-blue-50'
                }`}
                style={{ pointerEvents: 'auto' }}
                tabIndex={0}
                role="tab"
                aria-selected={activeSection === section.id}
                aria-controls={section.id}
                data-testid={section.testId}
              >
                <span className="flex items-center space-x-2">
                  <span className="text-base" role="img" aria-hidden="true">
                    {section.icon}
                  </span>
                  <span>{section.label}</span>
                </span>
              </button>
            ))}
          </div>

          {/* Mobile Navigation - Horizontal Scroll */}
          <div className="md:hidden flex items-center py-3 w-full">
            <div className="flex items-center space-x-2 overflow-x-auto scrollbar-hide px-2">
              {sections.map((section, index) => (
                <button
                  key={section.id}
                  data-section={section.id}
                  onClick={() => scrollToSection(section.id)}
                  onKeyDown={(e) => handleKeyDown(e, section.id)}
                  className={`flex-shrink-0 px-3 py-2 text-xs font-medium rounded-lg transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 whitespace-nowrap ${
                    activeSection === section.id
                      ? 'bg-blue-100 text-blue-700 shadow-sm'
                      : 'text-gray-600 hover:text-blue-600 hover:bg-blue-50'
                  }`}
                  tabIndex={0}
                  role="tab"
                  aria-selected={activeSection === section.id}
                  aria-controls={section.id}
                >
                  <span className="flex items-center space-x-1.5">
                    <span className="text-sm" role="img" aria-hidden="true">
                      {section.icon}
                    </span>
                    <span className="hidden sm:inline">{section.label}</span>
                    <span className="sm:hidden">
                      {section.label.split(' ')[0]}
                    </span>
                  </span>
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Progress Indicator */}
      <div className="absolute bottom-0 left-0 h-0.5 bg-blue-600 transition-all duration-300"
           style={{
             width: `${((sections.findIndex(s => s.id === activeSection) + 1) / sections.length) * 100}%`
           }}
           role="progressbar"
           aria-valuenow={sections.findIndex(s => s.id === activeSection) + 1}
           aria-valuemin={1}
           aria-valuemax={sections.length}
           aria-label="Section progress"
      />

      {/* Screen Reader Instructions */}
      <div className="sr-only" aria-live="polite">
        Currently viewing: {sections.find(s => s.id === activeSection)?.label}
      </div>
    </nav>
  );
};

export default StickyPageNav;