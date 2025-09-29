import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../App';
import { TESTIDS } from '../testids';
import { TestableRouterLink } from './testable/TestableComponents.tsx';

interface BackToHomeLinkProps {
  className?: string;
  onClick?: () => void;
}

export default function BackToHomeLink({ className = '', onClick }: BackToHomeLinkProps) {
  const { user } = useAuth();
  
  // Compute destination based on session state
  const destination = user ? '/app' : '/';
  
  return (
    <TestableRouterLink
      to={destination}
      data-testid={TESTIDS.backToHome}
      data-dest={destination}
      aria-label="Back to Home"
      className={`inline-flex items-center gap-2 text-sm underline underline-offset-2 ${className}`}
      onClick={onClick}
    >
      ← Back to Home
    </TestableRouterLink>
  );
}