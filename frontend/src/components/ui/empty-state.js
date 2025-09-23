import React from 'react';
import { Button } from './button';
import { Card, CardContent } from './card';

// Enhanced empty state component with consistent styling and actions
export const EmptyState = ({ 
  icon: Icon, 
  title, 
  description, 
  action, 
  actionLabel, 
  className = "",
  variant = "default" // default, large, compact
}) => {
  const sizeClasses = {
    default: "py-12",
    large: "py-16",
    compact: "py-8"
  };

  const iconSizes = {
    default: "w-16 h-16",
    large: "w-24 h-24", 
    compact: "w-12 h-12"
  };

  return (
    <Card className={`${className}`}>
      <CardContent className={`text-center ${sizeClasses[variant]}`}>
        {Icon && (
          <Icon className={`${iconSizes[variant]} text-gray-400 mx-auto mb-4`} />
        )}
        <h3 className="text-lg font-semibold text-gray-900 mb-2">{title}</h3>
        <p className="text-gray-600 mb-4 max-w-md mx-auto">{description}</p>
        {action && actionLabel && (
          <Button onClick={action} className="mt-2">
            {actionLabel}
          </Button>
        )}
      </CardContent>
    </Card>
  );
};

// Specific empty state variants for common scenarios
export const NoClubsEmptyState = ({ onNavigateToAuction }) => (
  <EmptyState
    icon={() => (
      <div className="w-16 h-16 mx-auto mb-4 bg-gray-100 rounded-full flex items-center justify-center">
        <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
        </svg>
      </div>
    )}
    title="No Clubs Owned Yet"
    description="You haven't acquired any clubs yet. Join the auction to build your Champions League squad and compete for points!"
    action={onNavigateToAuction}
    actionLabel="Go to Auction"
  />
);

export const NoFixturesEmptyState = () => (
  <EmptyState
    icon={() => (
      <div className="w-16 h-16 mx-auto mb-4 bg-gray-100 rounded-full flex items-center justify-center">
        <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
        </svg>
      </div>
    )}
    title="No Fixtures Scheduled"
    description="The Champions League fixtures haven't been loaded yet. Check back soon for the match schedule!"
  />
);

export const NoResultsEmptyState = () => (
  <EmptyState
    icon={() => (
      <div className="w-16 h-16 mx-auto mb-4 bg-gray-100 rounded-full flex items-center justify-center">
        <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v4a2 2 0 01-2 2h-2a2 2 0 00-2-2z" />
        </svg>
      </div>
    )}
    title="No Results Yet"
    description="Match results will appear here once games are completed and scores are recorded."
  />
);

export const AuctionNotStartedEmptyState = ({ canStart, onStartAuction }) => (
  <EmptyState
    icon={() => (
      <div className="w-16 h-16 mx-auto mb-4 bg-blue-100 rounded-full flex items-center justify-center">
        <svg className="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      </div>
    )}
    title="Auction Not Started"
    description={canStart 
      ? "The auction is ready to begin! Start bidding to acquire Champions League clubs for your squad."
      : "The auction hasn't started yet. The commissioner will begin the auction when all managers are ready."
    }
    action={canStart ? onStartAuction : undefined}
    actionLabel={canStart ? "Start Auction" : undefined}
  />
);

export const NoMembersEmptyState = ({ onInviteMembers }) => (
  <EmptyState
    icon={() => (
      <div className="w-16 h-16 mx-auto mb-4 bg-gray-100 rounded-full flex items-center justify-center">
        <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z" />
        </svg>
      </div>
    )}
    title="No Members Yet"
    description="Invite friends to join your league! You need at least 4 managers to start the auction."
    action={onInviteMembers}
    actionLabel="Invite Members"
  />
);

export const LoadingEmptyState = ({ message = "Loading..." }) => (
  <EmptyState
    icon={() => (
      <div className="w-16 h-16 mx-auto mb-4">
        <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600"></div>
      </div>
    )}
    title={message}
    description="Please wait while we fetch your data."
    variant="compact"
  />
);