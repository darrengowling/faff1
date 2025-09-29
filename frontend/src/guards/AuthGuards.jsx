/**
 * Centralized Authentication Route Guards
 * 
 * Provides predictable auth redirects with no loops:
 * - RequireAuth: Protects authenticated routes, redirects to login with next param
 * - RedirectIfAuthed: Redirects authenticated users away from login/landing pages
 */

import React, { useState, useEffect } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../App';

/**
 * RequireAuth Wrapper
 * 
 * Protects authenticated routes by redirecting unauthenticated users to login
 * with a 'next' parameter to return them after authentication
 */
export const RequireAuth = ({ children }) => {
  const { user, loading } = useAuth();
  const location = useLocation();

  // Show loading spinner while auth state is being determined
  if (loading) {
    return (
      <div 
        className="min-h-screen flex items-center justify-center"
        data-testid="auth-loading"
        aria-live="polite"
      >
        <div className="flex flex-col items-center space-y-4">
          <div className="animate-spin w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full"></div>
          <p className="text-gray-600">Checking authentication...</p>
        </div>
      </div>
    );
  }

  // User is not authenticated, redirect to login with next parameter
  if (!user) {
    const nextUrl = encodeURIComponent(location.pathname + location.search);
    return <Navigate to={`/login?next=${nextUrl}`} replace />;
  }

  // User is authenticated, render protected content
  return children;
};

/**
 * RedirectIfAuthed Wrapper
 * 
 * Redirects authenticated users away from login/marketing pages to the app
 * Prevents authenticated users from seeing login screens
 */
export const RedirectIfAuthed = ({ children, redirectTo = '/app' }) => {
  const { user, loading } = useAuth();

  // Show loading spinner while auth state is being determined
  if (loading) {
    return (
      <div 
        className="min-h-screen flex items-center justify-center"
        data-testid="auth-loading"
        aria-live="polite"
      >
        <div className="flex flex-col items-center space-y-4">
          <div className="animate-spin w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full"></div>
          <p className="text-gray-600">Checking authentication...</p>
        </div>
      </div>
    );
  }

  // User is authenticated, redirect to app
  if (user) {
    return <Navigate to={redirectTo} replace />;
  }

  // User is not authenticated, show login/marketing content
  return children;
};