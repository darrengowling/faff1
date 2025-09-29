import React from 'react';
import { Link } from 'react-router-dom';

interface BackToHomeLinkProps {
  className?: string;
  onClick?: () => void;
}

export default function BackToHomeLink({ className = '', onClick }: BackToHomeLinkProps) {
  return (
    <Link
      to="/"
      data-testid="back-to-home-link"
      aria-label="Back to Home"
      className={`inline-flex items-center gap-2 text-sm underline underline-offset-2 ${className}`}
      onClick={onClick}
    >
      ← Back to Home
    </Link>
  );
}