/**
 * Create League CTA Component
 * 
 * Always-present CTA that renders immediately with testids,
 * even during loading states. Ensures test reliability.
 */

import React from 'react';
import { Button } from './button';
import { Plus, Loader2 } from 'lucide-react';
import { TESTIDS } from '../../testids.ts';

const CreateLeagueCTA = ({ 
  isLoading = false, 
  onCreateLeague,
  variant = 'default',
  className = ''
}) => {
  // Always render button with testid - never hide the element
  return (
    <Button
      onClick={isLoading ? undefined : onCreateLeague}
      disabled={isLoading}
      className={className}
      variant={variant}
      data-testid={TESTIDS.homeCreateLeagueBtn}
      aria-label={
        isLoading 
          ? "Loading leagues data, create league will be available shortly" 
          : "Create a new league"
      }
      title={isLoading ? "Loading…" : "Create a new league to get started"}
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
        data-testid={TESTIDS.homeCreateLeagueBtn}
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
      data-testid={TESTIDS.homeCreateLeagueBtn}
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