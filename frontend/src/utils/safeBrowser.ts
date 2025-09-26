/**
 * Safe Browser Utilities for SSR and Test Environment Compatibility
 * 
 * Provides browser detection and safe window/document access
 * that won't crash during server-side rendering or test environments
 */

/**
 * Check if code is running in a browser environment
 * @returns true if window object is available
 */
export const isBrowser = (): boolean => {
  return typeof window !== 'undefined';
};

/**
 * Check if code is running in a DOM environment
 * @returns true if document object is available
 */
export const isDOM = (): boolean => {
  return typeof document !== 'undefined';
};

/**
 * Safely get a URL search parameter
 * @param key - The parameter key to retrieve
 * @returns The parameter value or null if not found/not in browser
 */
export const getSearchParam = (key: string): string | null => {
  if (!isBrowser()) return null;
  
  try {
    return new URLSearchParams(window.location.search).get(key);
  } catch (error) {
    console.warn(`Failed to get search param '${key}':`, error);
    return null;
  }
};

/**
 * Safely get the current pathname
 * @returns The current pathname or '/' if not in browser
 */
export const getPathname = (): string => {
  if (!isBrowser()) return '/';
  
  try {
    return window.location.pathname;
  } catch (error) {
    console.warn('Failed to get pathname:', error);
    return '/';
  }
};

/**
 * Safely get the current hostname
 * @returns The current hostname or 'localhost' if not in browser
 */
export const getHostname = (): string => {
  if (!isBrowser()) return 'localhost';
  
  try {
    return window.location.hostname;
  } catch (error) {
    console.warn('Failed to get hostname:', error);
    return 'localhost';
  }
};

/**
 * Safely check if localStorage is available
 * @returns true if localStorage is accessible
 */
export const hasLocalStorage = (): boolean => {
  if (!isBrowser()) return false;
  
  try {
    const test = '__localStorage_test__';
    window.localStorage.setItem(test, 'test');
    window.localStorage.removeItem(test);
    return true;
  } catch (error) {
    return false;
  }
};

/**
 * Safely get an item from localStorage
 * @param key - The localStorage key
 * @returns The stored value or null if not found/not available
 */
export const getLocalStorageItem = (key: string): string | null => {
  if (!hasLocalStorage()) return null;
  
  try {
    return window.localStorage.getItem(key);
  } catch (error) {
    console.warn(`Failed to get localStorage item '${key}':`, error);
    return null;
  }
};

/**
 * Safely set an item in localStorage
 * @param key - The localStorage key
 * @param value - The value to store
 * @returns true if successful, false otherwise
 */
export const setLocalStorageItem = (key: string, value: string): boolean => {
  if (!hasLocalStorage()) return false;
  
  try {
    window.localStorage.setItem(key, value);
    return true;
  } catch (error) {
    console.warn(`Failed to set localStorage item '${key}':`, error);
    return false;
  }
};

/**
 * Safely remove an item from localStorage
 * @param key - The localStorage key to remove
 * @returns true if successful, false otherwise
 */
export const removeLocalStorageItem = (key: string): boolean => {
  if (!hasLocalStorage()) return false;
  
  try {
    window.localStorage.removeItem(key);
    return true;
  } catch (error) {
    console.warn(`Failed to remove localStorage item '${key}':`, error);
    return false;
  }
};

/**
 * Safely get user agent string
 * @returns User agent string or empty string if not available
 */
export const getUserAgent = (): string => {
  if (!isBrowser()) return '';
  
  try {
    return window.navigator.userAgent || '';
  } catch (error) {
    console.warn('Failed to get user agent:', error);
    return '';
  }
};

/**
 * Check if running on mobile device (basic detection)
 * @returns true if likely mobile device
 */
export const isMobile = (): boolean => {
  const userAgent = getUserAgent().toLowerCase();
  return /android|webos|iphone|ipad|ipod|blackberry|iemobile|opera mini/.test(userAgent);
};

export default {
  isBrowser,
  isDOM,
  getSearchParam,
  getPathname,
  getHostname,
  hasLocalStorage,
  getLocalStorageItem,
  setLocalStorageItem,
  removeLocalStorageItem,
  getUserAgent,
  isMobile
};