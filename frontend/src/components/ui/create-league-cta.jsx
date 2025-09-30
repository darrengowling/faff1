/**
 * Create League CTA Component
 * 
 * Always-present CTA that renders immediately with testids,
 * even during loading states. Ensures test reliability.
 */

import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from './button';
import { Plus, Loader2 } from 'lucide-react';
import { TESTIDS } from '../../testids.ts';

const CreateLeagueCTA = ({ 
  isLoading = false, 
  onCreateLeague,
  variant = 'default',
  className = '',
  showSecondaryAction = false // New prop to show page link
}) => {
  const navigate = useNavigate();
  
  const handlePageRedirect = () => {
    navigate('/app/leagues/new');
  };

  // Always render button with testid - never hide the element
  return (
    <div className="flex items-center gap-3">
      <Button
        onClick={isLoading ? undefined : onCreateLeague}
        disabled={isLoading}
        className={className}
        variant={variant}
        data-testid={TESTIDS.createLeagueBtn}
        aria-label={
          isLoading 
            ? "Loading leagues data, create league will be available shortly" 
            : "Create a new league (opens dialog)"
        }
        title={isLoading ? "Loading…" : "Create a new league using dialog"}
      >
        {isLoading ? (
          <>
            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            Loading…
          </>
        ) : (
          <>
            <Plus className="w-4 h-4 mr-2" />
            Create League
          </>
        )}
      </Button>
      
      {showSecondaryAction && !isLoading && (
        <Button
          onClick={handlePageRedirect}
          variant="outline"
          className="text-sm"
          data-testid="create-league-page-link"
          aria-label="Create a new league (opens page)"
          title="Create a new league using dedicated page"
        >
          Open Form Page
        </Button>
      )}
    </div>
  );
};

/**
 * Primary Create League CTA for empty states
 */
export const PrimaryCreateLeagueCTA = ({ 
  isLoading = false, 
  onCreateLeague,
  className = ''
}) => {
  return (
    <div className="text-center">
      <Button
        onClick={isLoading ? undefined : onCreateLeague}
        disabled={isLoading}
        size="lg"
        className={`px-8 py-3 ${className}`}
        data-testid={TESTIDS.createLeagueBtn}
        aria-label={
          isLoading 
            ? "Loading leagues data, create league will be available shortly" 
            : "Create your first league"
        }
        title={isLoading ? "Loading…" : "Create your first league to get started"}
      >
        {isLoading ? (
          <>
            <Loader2 className="w-5 h-5 mr-2 animate-spin" />
            Loading…
          </>
        ) : (
          <>
            <Plus className="w-5 h-5 mr-2" />
            Create League
          </>
        )}
      </Button>
    </div>
  );
};

/**
 * Secondary/smaller Create League CTA
 */
export const SecondaryCreateLeagueCTA = ({ 
  isLoading = false, 
  onCreateLeague,
  className = ''
}) => {
  return (
    <Button
      onClick={isLoading ? undefined : onCreateLeague}
      disabled={isLoading}
      variant="outline"
      size="sm"
      className={className}
      data-testid={TESTIDS.createLeagueBtn}
      aria-label={
        isLoading 
          ? "Loading leagues data, create league will be available shortly" 
          : "Create another league"
      }
      title={isLoading ? "Loading…" : "Create another league"}
    >
      {isLoading ? (
        <>
          <Loader2 className="w-4 h-4 mr-1 animate-spin" />
          Loading…
        </>
      ) : (
        <>
          <Plus className="w-4 h-4 mr-1" />
          New League
        </>
      )}
    </Button>
  );
};

export default CreateLeagueCTA;