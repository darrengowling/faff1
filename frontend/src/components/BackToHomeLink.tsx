import React from 'react';
import { Link } from 'react-router-dom';
import { TESTIDS } from '../testids';

interface BackToHomeLinkProps {
  className?: string;
  testId?: string;           // default only for primary placement
  to?: string;              // caller can override based on session
  onClick?: React.MouseEventHandler<HTMLAnchorElement>;
}

export default function BackToHomeLink({
  className = '',
  testId = 'back-to-home-link',           // default only for primary placement
  to = '/app',                            // caller can override based on session
  onClick,
}: BackToHomeLinkProps) {
  return (
    <Link
      to={to}
      data-testid={testId}
      aria-label="Back to Home"
      className={`inline-flex items-center gap-2 text-sm underline underline-offset-2 ${className}`}
      onClick={onClick}
    >
      ← Back to Home
    </Link>
  );
}