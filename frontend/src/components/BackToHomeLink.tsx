import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../App';
import { TESTIDS } from '../testids';

const BackToHomeLink = ({ className = '', children = 'Back to Home', ...props }) => {
  const { user } = useAuth();
  const location = useLocation();
  
  // Determine destination based on authentication state
  const destination = user ? '/app' : '/';
  
  return (
    <Link 
      to={destination}
      className={className}
      data-testid={TESTIDS.backToHome}
      data-dest={destination}
      {...props}
    >
      {children}
    </Link>
  );
};

export default BackToHomeLink;