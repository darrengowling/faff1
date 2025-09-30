/**
 * Hash Spy Hook - Mobile Navigation Stabilization
 * 
 * Monitors which section is ≥50% visible and updates history.replaceState
 * with 100ms debounce to prevent flaky navigation states
 */

import { useState, useEffect, useRef, useCallback } from 'react';

export const useHashSpy = (sections = ['#home', '#how', '#why', '#features', '#safety', '#faq']) => {
  const [currentHash, setCurrentHash] = useState('');
  const debounceTimer = useRef(null);
  
  // Debounced function to update hash
  const updateHash = useCallback((newHash) => {
    if (debounceTimer.current) {
      clearTimeout(debounceTimer.current);
    }
    
    debounceTimer.current = setTimeout(() => {
      if (newHash !== currentHash) {
        setCurrentHash(newHash);
        
        // Update browser history without triggering navigation
        if (typeof window !== 'undefined' && window.history.replaceState) {
          const newUrl = newHash ? `${window.location.pathname}${newHash}` : window.location.pathname;
          window.history.replaceState(null, '', newUrl);
        }
        
        // Update nav-current-hash marker element
        const hashMarker = document.querySelector('[data-testid="nav-current-hash"]');
        if (hashMarker) {
          hashMarker.textContent = newHash || '';
        }
      }
    }, 100); // 100ms debounce as required
  }, [currentHash]);

  // Check which section is ≥50% visible
  const checkVisibleSection = useCallback(() => {
    if (typeof window === 'undefined') return;

    const viewportHeight = window.innerHeight;
    const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
    let mostVisibleSection = '';
    let maxVisibleRatio = 0;

    sections.forEach((sectionId) => {
      const element = document.querySelector(sectionId);
      if (!element) return;

      const rect = element.getBoundingClientRect();
      const elementTop = scrollTop + rect.top;
      const elementBottom = elementTop + rect.height;
      
      // Calculate visible portion
      const visibleTop = Math.max(scrollTop, elementTop);
      const visibleBottom = Math.min(scrollTop + viewportHeight, elementBottom);
      const visibleHeight = Math.max(0, visibleBottom - visibleTop);
      
      const visibleRatio = visibleHeight / rect.height;
      
      // Section is ≥50% visible and more visible than others
      if (visibleRatio >= 0.5 && visibleRatio > maxVisibleRatio) {
        maxVisibleRatio = visibleRatio;
        mostVisibleSection = sectionId;
      }
    });

    updateHash(mostVisibleSection);
  }, [sections, updateHash]);

  useEffect(() => {
    // Set initial hash from URL
    if (typeof window !== 'undefined') {
      setCurrentHash(window.location.hash || '');
    }

    // Add scroll listener
    const handleScroll = () => checkVisibleSection();
    
    if (typeof window !== 'undefined') {
      window.addEventListener('scroll', handleScroll, { passive: true });
      window.addEventListener('resize', handleScroll, { passive: true });
      
      // Check initial state
      checkVisibleSection();
    }

    return () => {
      if (typeof window !== 'undefined') {
        window.removeEventListener('scroll', handleScroll);
        window.removeEventListener('resize', handleScroll);
      }
      
      if (debounceTimer.current) {
        clearTimeout(debounceTimer.current);
      }
    };
  }, [checkVisibleSection]);

  // Force update hash (useful for navigation)
  const setHash = useCallback((hash) => {
    updateHash(hash);
  }, [updateHash]);

  return {
    currentHash,
    setHash
  };
};

export default useHashSpy;