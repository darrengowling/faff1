/**
 * useScrollSpy Hook
 * 
 * Deterministic scroll spy that updates URL hash based on section visibility
 * Uses Intersection Observer for accurate threshold detection
 */

import { useEffect, useRef, useState } from 'react';

const useScrollSpy = ({ threshold = 0.5, debounceMs = 100 } = {}) => {
  const [activeSection, setActiveSection] = useState('');
  const debounceTimer = useRef(null);
  const observer = useRef(null);
  const sectionsRef = useRef(new Map());

  useEffect(() => {
    // Clear existing debounce timer
    if (debounceTimer.current) {
      clearTimeout(debounceTimer.current);
    }

    // Debounced function to update URL hash
    const updateUrlHash = (sectionId) => {
      debounceTimer.current = setTimeout(() => {
        if (sectionId && window.location.hash !== `#${sectionId}`) {
          // Use history.replaceState to update hash without triggering navigation
          window.history.replaceState(null, null, `#${sectionId}`);
          setActiveSection(sectionId);
        }
      }, debounceMs);
    };

    // Intersection Observer callback
    const handleIntersection = (entries) => {
      entries.forEach((entry) => {
        const sectionId = entry.target.id;
        const isVisible = entry.intersectionRatio >= threshold;
        
        // Track section visibility
        sectionsRef.current.set(sectionId, {
          element: entry.target,
          isVisible,
          intersectionRatio: entry.intersectionRatio,
          boundingRect: entry.boundingClientRect
        });
      });

      // Find the most visible section that meets threshold
      let mostVisibleSection = null;
      let highestRatio = 0;

      sectionsRef.current.forEach((sectionData, sectionId) => {
        if (sectionData.isVisible && sectionData.intersectionRatio > highestRatio) {
          highestRatio = sectionData.intersectionRatio;
          mostVisibleSection = sectionId;
        }
      });

      // Update URL hash if we have a visible section
      if (mostVisibleSection) {
        updateUrlHash(mostVisibleSection);
      }
    };

    // Create Intersection Observer
    observer.current = new IntersectionObserver(handleIntersection, {
      threshold: [0, 0.25, 0.5, 0.75, 1.0], // Multiple thresholds for accurate detection
      rootMargin: `-64px 0px -64px 0px` // Account for header height
    });

    // Observe all anchor sections
    const anchorSections = document.querySelectorAll('.anchor-section');
    anchorSections.forEach((section) => {
      if (section.id) {
        observer.current.observe(section);
        sectionsRef.current.set(section.id, {
          element: section,
          isVisible: false,
          intersectionRatio: 0,
          boundingRect: null
        });
      }
    });

    return () => {
      if (observer.current) {
        observer.current.disconnect();
      }
      if (debounceTimer.current) {
        clearTimeout(debounceTimer.current);
      }
      sectionsRef.current.clear();
    };
  }, [threshold, debounceMs]);

  // Return current active section and utility functions
  return {
    activeSection,
    getSectionData: (sectionId) => sectionsRef.current.get(sectionId),
    getAllSections: () => Array.from(sectionsRef.current.keys()),
    isVisible: (sectionId) => sectionsRef.current.get(sectionId)?.isVisible || false,
    getVisibilityRatio: (sectionId) => sectionsRef.current.get(sectionId)?.intersectionRatio || 0
  };
};

export default useScrollSpy;