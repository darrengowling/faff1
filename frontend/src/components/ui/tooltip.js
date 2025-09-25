import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';

// Enhanced tooltip component with rich content support
export const Tooltip = ({ 
  children, 
  content, 
  position = "top",
  className = "",
  disabled = false,
  delay = 300
}) => {
  const [isVisible, setIsVisible] = useState(false);
  const [timeoutId, setTimeoutId] = useState(null);

  const showTooltip = () => {
    if (disabled) return;
    
    const id = setTimeout(() => {
      setIsVisible(true);
    }, delay);
    setTimeoutId(id);
  };

  const hideTooltip = () => {
    if (timeoutId) {
      clearTimeout(timeoutId);
      setTimeoutId(null);
    }
    setIsVisible(false);
  };

  const positionClasses = {
    top: "bottom-full left-1/2 transform -translate-x-1/2 mb-2",
    bottom: "top-full left-1/2 transform -translate-x-1/2 mt-2",
    left: "right-full top-1/2 transform -translate-y-1/2 mr-2",
    right: "left-full top-1/2 transform -translate-y-1/2 ml-2"
  };

  const arrowClasses = {
    top: "top-full left-1/2 transform -translate-x-1/2 border-l-transparent border-r-transparent border-b-transparent border-t-gray-900",
    bottom: "bottom-full left-1/2 transform -translate-x-1/2 border-l-transparent border-r-transparent border-t-transparent border-b-gray-900",
    left: "left-full top-1/2 transform -translate-y-1/2 border-t-transparent border-b-transparent border-r-transparent border-l-gray-900",
    right: "right-full top-1/2 transform -translate-y-1/2 border-t-transparent border-b-transparent border-l-transparent border-r-gray-900"
  };

  return (
    <div 
      className={`relative inline-block ${className}`}
      onMouseEnter={showTooltip}
      onMouseLeave={hideTooltip}
      onFocus={showTooltip}
      onBlur={hideTooltip}
    >
      {children}
      {isVisible && (
        <div className={`absolute z-50 ${positionClasses[position]} animate-in fade-in-0 zoom-in-95 duration-300`}>
          <div className="bg-gray-900 text-white text-sm rounded-md px-3 py-2 max-w-xs shadow-lg">
            {content}
          </div>
          <div className={`absolute w-0 h-0 border-4 ${arrowClasses[position]}`} />
        </div>
      )}
    </div>
  );
};

// Specialized scoring tooltip with examples
export const ScoringTooltip = ({ children, className = "" }) => {
  const { t } = useTranslation();
  const scoringContent = (
    <div className="space-y-2">
      <div className="font-semibold text-white">{t('tooltips.scoringSystem')}</div>
      <div className="space-y-1 text-xs">
        <div>
          <span className="font-medium text-green-300">Goals:</span> +1 point each
        </div>
        <div>
          <span className="font-medium text-blue-300">Wins:</span> +3 points
        </div>
        <div>
          <span className="font-medium text-yellow-300">Draws:</span> +1 point
        </div>
      </div>
      <div className="border-t border-gray-700 pt-2 mt-2">
        <div className="font-medium text-white text-xs mb-1">Examples:</div>
        <div className="space-y-1 text-xs">
          <div>2-1 Win: 2 goals + 3 win = <span className="text-green-400 font-medium">5 points</span></div>
          <div>2-2 Draw: 2 goals + 1 draw = <span className="text-yellow-400 font-medium">3 points</span></div>
          <div>0-1 Loss: 0 goals + 0 = <span className="text-red-400 font-medium">0 points</span></div>
        </div>
      </div>
    </div>
  );

  return (
    <Tooltip content={scoringContent} position="right" className={className} delay={200}>
      {children}
    </Tooltip>
  );
};

// Budget constraint tooltip
export const BudgetTooltip = ({ remaining, slotsLeft, minIncrement, children }) => {
  const budgetContent = (
    <div className="space-y-2">
      <div className="font-semibold text-white">Budget Status</div>
      <div className="space-y-1 text-xs">
        <div>Remaining: <span className="text-green-400 font-medium">{remaining}M</span></div>
        <div>Slots Left: <span className="text-blue-400 font-medium">{slotsLeft}</span></div>
        <div>Min Reserve Needed: <span className="text-yellow-400 font-medium">{slotsLeft * minIncrement}M</span></div>
      </div>
      <div className="border-t border-gray-700 pt-2 text-xs text-gray-300">
        You must keep enough budget to fill remaining slots at minimum bid
      </div>
    </div>
  );

  return (
    <Tooltip content={budgetContent} position="top" delay={100}>
      {children}
    </Tooltip>
  );
};

// Auction mechanics tooltip
export const AuctionTooltip = ({ children }) => {
  const { t } = useTranslation();
  const auctionContent = (
    <div className="space-y-2">
      <div className="font-semibold text-white">Auction Rules</div>
      <div className="space-y-1 text-xs">
        <div>• Minimum increment: 1M</div>
        <div>• Anti-snipe: Timer extends if bid placed in last 30 seconds</div>
        <div>• Budget constraint: Must keep enough for remaining slots</div>
        <div>• One owner per club</div>
      </div>
    </div>
  );

  return (
    <Tooltip content={auctionContent} position="bottom" delay={200}>
      {children}
    </Tooltip>
  );
};