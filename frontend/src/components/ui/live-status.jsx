import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Badge } from './badge';
import { Clock, DollarSign, Trophy } from 'lucide-react';

/**
 * Live Status Components
 * 
 * Provides accessible real-time status updates with ARIA live regions
 * Addresses usability issue: "System status visibility - timer, budget, bids"
 */

export const AuctionStatus = ({ 
  timeRemaining, 
  currentBid, 
  budgetRemaining, 
  isActive = false,
  className = "" 
}) => {
  const [lastAnnouncement, setLastAnnouncement] = useState('');
  
  // Generate announcement for screen readers
  const generateAnnouncement = () => {
    if (!isActive) return '';
    
    const parts = [];
    if (timeRemaining !== undefined) {
      parts.push(`${timeRemaining} seconds remaining`);
    }
    if (currentBid !== undefined) {
      parts.push(`Current bid ${currentBid} million`);
    }
    if (budgetRemaining !== undefined) {
      parts.push(`Budget remaining ${budgetRemaining} million`);
    }
    
    return parts.join(', ');
  };

  // Update announcements periodically
  useEffect(() => {
    if (isActive) {
      const announcement = generateAnnouncement();
      if (announcement !== lastAnnouncement) {
        setLastAnnouncement(announcement);
      }
    }
  }, [timeRemaining, currentBid, budgetRemaining, isActive, lastAnnouncement]);

  return (
    <div className={`space-y-2 ${className}`} role="region" aria-label="Auction status">
      {/* Screen reader announcements */}
      <div 
        aria-live="polite" 
        aria-atomic="true"
        className="sr-only"
      >
        {lastAnnouncement}
      </div>
      
      {/* Visual status indicators */}
      <div className="flex items-center space-x-4">
        {timeRemaining !== undefined && (
          <div className="flex items-center space-x-2">
            <Clock className="w-4 h-4 text-orange-500" aria-hidden="true" />
            <div>
              <div className="text-lg font-bold text-orange-500">
                {timeRemaining}s
              </div>
              <div className="text-xs text-gray-500">Remaining</div>
            </div>
          </div>
        )}
        
        {currentBid !== undefined && (
          <div className="flex items-center space-x-2">
            <Trophy className="w-4 h-4 text-green-500" aria-hidden="true" />
            <div>
              <div className="text-lg font-bold text-green-500">
                £{currentBid}M
              </div>
              <div className="text-xs text-gray-500">Current Bid</div>
            </div>
          </div>
        )}
        
        {budgetRemaining !== undefined && (
          <div className="flex items-center space-x-2">
            <DollarSign className="w-4 h-4 text-blue-500" aria-hidden="true" />
            <div>
              <div className="text-lg font-bold text-blue-500">
                £{budgetRemaining}M
              </div>
              <div className="text-xs text-gray-500">Budget Left</div>
            </div>
          </div>
        )}
      </div>
      
      {/* Status indicator */}
      {isActive && (
        <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
          <div className="w-2 h-2 bg-green-500 rounded-full mr-2 animate-pulse" aria-hidden="true"></div>
          Live Auction
        </Badge>
      )}
    </div>
  );
};

export const BidNotification = ({ 
  message, 
  type = 'info', 
  onDismiss,
  autoDisappear = true 
}) => {
  useEffect(() => {
    if (autoDisappear && onDismiss) {
      const timer = setTimeout(onDismiss, 5000);
      return () => clearTimeout(timer);
    }
  }, [autoDisappear, onDismiss]);

  const typeStyles = {
    success: 'bg-green-100 border-green-200 text-green-800',
    warning: 'bg-yellow-100 border-yellow-200 text-yellow-800', 
    error: 'bg-red-100 border-red-200 text-red-800',
    info: 'bg-blue-100 border-blue-200 text-blue-800'
  };

  return (
    <div 
      role="alert" 
      aria-live="assertive"
      className={`p-3 border rounded-lg ${typeStyles[type]} animate-in slide-in-from-top duration-300`}
    >
      {message}
    </div>
  );
};

export const MemberCountStatus = ({ 
  currentCount, 
  minRequired, 
  maxAllowed,
  className = "" 
}) => {
  const isReady = currentCount >= minRequired;
  const isFull = currentCount >= maxAllowed;
  
  return (
    <div className={`flex items-center space-x-2 ${className}`}>
      <div 
        className={`text-lg font-bold ${
          isReady ? 'text-green-600' : 'text-orange-600'
        }`}
      >
        {currentCount}/{maxAllowed}
      </div>
      <div className="text-sm text-gray-600">managers</div>
      
      {/* Live region for status changes */}
      <div aria-live="polite" className="sr-only">
        {isReady 
          ? `Ready to start: ${currentCount} of ${maxAllowed} managers joined`
          : `Need more managers: ${currentCount} of ${minRequired} minimum required`
        }
      </div>
      
      {/* Visual status indicator */}
      {!isReady && (
        <Badge variant="outline" className="bg-orange-50 text-orange-700 border-orange-200">
          Need {minRequired - currentCount} more
        </Badge>
      )}
      
      {isReady && !isFull && (
        <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
          Ready to start
        </Badge>
      )}
      
      {isFull && (
        <Badge variant="outline" className="bg-gray-50 text-gray-700 border-gray-200">
          Full
        </Badge>
      )}
    </div>
  );
};

export const BudgetStatus = ({
  budgetUsed, 
  budgetTotal, 
  clubsOwned, 
  clubsMax,
  isLoading = false,  // Add loading prop
  className = "" 
}) => {
  const { t } = useTranslation();
  const budgetRemaining = budgetTotal - budgetUsed;
  const budgetPercentage = (budgetUsed / budgetTotal) * 100;
  const slotsRemaining = clubsMax - clubsOwned;
  
  return (
    <div className={`space-y-3 ${className}`} role="region" aria-label="Budget and slots status">
      {/* Budget bar */}
      <div>
        <div className="flex justify-between text-sm mb-1">
          <span>Budget Used</span>
          <span className="font-medium" data-testid={TESTIDS.budgetUsed}>£{budgetUsed}M / £{budgetTotal}M</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div 
            className={`h-2 rounded-full transition-all duration-300 ${
              budgetPercentage > 90 ? 'bg-red-500' :
              budgetPercentage > 70 ? 'bg-yellow-500' : 'bg-green-500'
            }`}
            style={{ width: `${budgetPercentage}%` }}
            role="progressbar"
            aria-valuenow={budgetUsed}
            aria-valuemin={0}
            aria-valuemax={budgetTotal}
            aria-label={`Budget used: ${budgetUsed} of ${budgetTotal} million`}
          ></div>
        </div>
      </div>
      
      {/* Club slots */}
      <div className="flex justify-between items-center">
        <span className="text-sm text-gray-600">Club Slots</span>
        <div className="flex items-center space-x-2">
          {isLoading ? (
            <div className="flex items-center space-x-2">
              <span className="font-medium">—/—</span>
              <Badge variant="outline" className="text-xs">
                — available
              </Badge>
            </div>
          ) : (
            <>
              <span className="font-medium">{clubsOwned}/{clubsMax}</span>
              {slotsRemaining > 0 && (
                <Badge variant="outline" className="text-xs">
                  {slotsRemaining} available
                </Badge>
              )}
              {slotsRemaining === 0 && (
                <Badge variant="outline" className="text-xs bg-red-50 text-red-700 border-red-200">
                  Full
                </Badge>
              )}
            </>
          )}
        </div>
      </div>
      
      {/* Live announcements for budget changes */}
      <div aria-live="polite" className="sr-only">
        Budget remaining: £{budgetRemaining}M, Club slots available: {slotsRemaining}
      </div>
    </div>
  );
};

export default AuctionStatus;