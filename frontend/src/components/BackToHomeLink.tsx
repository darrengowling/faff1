import React from 'react';
import { Link } from 'react-router-dom';
import { TESTIDS } from '../testids';
import { useAuth } from '../App';

interface BackToHomeLinkProps {
  className?: string;
  testId?: string;           // default only for primary placement
  to?: string;              // caller can override based on session
  onClick?: React.MouseEventHandler<HTMLAnchorElement>;
}

export default function BackToHomeLink({
  className = '',
  testId = 'back-to-home-link',           // default only for primary placement
  to,                                     // if not provided, will be determined by auth state
  onClick,
}: BackToHomeLinkProps) {
  const { user } = useAuth();
  
  // Determine destination based on authentication state if not explicitly provided
  const destination = to || (user ? '/app' : '/');
  
  return (
    <Link
      to={destination}
      data-testid={testId}
      data-dest={destination}
      aria-label="Back to Home"
      className={`inline-flex items-center gap-2 text-sm underline underline-offset-2 ${className}`}
      onClick={onClick}
    >
      ← Back to Home
    </Link>
  );
}