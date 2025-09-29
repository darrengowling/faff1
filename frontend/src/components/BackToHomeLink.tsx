import React from 'react';
import { Link } from 'react-router-dom';

export default function BackToHomeLink({ className = '' }: { className?: string }) {
  return (
    <Link
      to="/app"
      data-testid="back-to-home-link"
      aria-label="Back to Home"
      className={`inline-flex items-center gap-2 text-sm underline underline-offset-2 ${className}`}
    >
      ← Back to Home
    </Link>
  );
}