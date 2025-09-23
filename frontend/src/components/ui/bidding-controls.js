import React, { useState, useEffect, useRef } from 'react';
import { Button } from './button';
import { Input } from './input';
import { Label } from './label';
import { Tooltip, BudgetTooltip } from './tooltip';
import { AuctionToasts } from './auction-toasts';
import { Plus, Minus, Zap, DollarSign, Keyboard } from 'lucide-react';

// Enhanced bidding controls with accessibility and keyboard shortcuts
export const BiddingControls = ({
  lotId,
  clubName,
  currentBid,
  minIncrement,
  userBudget,
  remainingSlots,
  isActiveUser,
  onPlaceBid,
  disabled = false,
  className = ""
}) => {
  const [bidAmount, setBidAmount] = useState(currentBid + minIncrement);
  const [isPlacing, setIsPlacing] = useState(false);
  const [customBid, setCustomBid] = useState('');
  const [useCustomBid, setUseCustomBid] = useState(false);
  const inputRef = useRef(null);
  const buttonRef = useRef(null);

  // Update bid amount when current bid changes
  useEffect(() => {
    if (!useCustomBid) {
      setBidAmount(currentBid + minIncrement);
    }
  }, [currentBid, minIncrement, useCustomBid]);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyPress = (e) => {
      // Only trigger if not typing in an input
      if (e.target.tagName === 'INPUT') return;
      
      switch (e.key) {
        case 'b':
        case 'B':
          if (!disabled && isActiveUser) {
            e.preventDefault();
            handlePlaceBid();
          }
          break;
        case '+':
        case '=':
          e.preventDefault();
          increaseBid();
          break;
        case '-':
          e.preventDefault();
          decreaseBid();
          break;
        case 'c':
        case 'C':
          e.preventDefault();
          toggleCustomBid();
          break;
        default:
          break;
      }
    };

    if (isActiveUser) {
      document.addEventListener('keydown', handleKeyPress);
      return () => document.removeEventListener('keydown', handleKeyPress);
    }
  }, [bidAmount, disabled, isActiveUser, useCustomBid]);

  const increaseBid = () => {
    const newAmount = useCustomBid 
      ? Math.max(currentBid + minIncrement, parseInt(customBid) + minIncrement)
      : bidAmount + minIncrement;
    
    if (useCustomBid) {
      setCustomBid(newAmount.toString());
    } else {
      setBidAmount(newAmount);
    }
  };

  const decreaseBid = () => {
    const minBid = currentBid + minIncrement;
    const newAmount = useCustomBid
      ? Math.max(minBid, parseInt(customBid) - minIncrement)
      : Math.max(minBid, bidAmount - minIncrement);
    
    if (useCustomBid) {
      setCustomBid(newAmount.toString());
    } else {
      setBidAmount(newAmount);
    }
  };

  const toggleCustomBid = () => {
    setUseCustomBid(!useCustomBid);
    if (!useCustomBid) {
      setCustomBid(bidAmount.toString());
      // Focus custom input after state update
      setTimeout(() => inputRef.current?.focus(), 100);
    } else {
      setBidAmount(parseInt(customBid) || currentBid + minIncrement);
    }
  };

  const handlePlaceBid = async () => {
    const finalBid = useCustomBid ? parseInt(customBid) : bidAmount;
    
    // Validation
    if (finalBid < currentBid + minIncrement) {
      AuctionToasts.invalidBid('below_minimum');
      return;
    }

    if (finalBid > userBudget.remaining) {
      AuctionToasts.invalidBid('insufficient_budget');
      return;
    }

    // Budget constraint check
    const budgetAfterBid = userBudget.remaining - finalBid;
    const minReserveNeeded = remainingSlots * minIncrement;
    if (budgetAfterBid < minReserveNeeded) {
      AuctionToasts.invalidBid('budget_constraint');
      return;
    }

    setIsPlacing(true);
    
    try {
      await onPlaceBid(lotId, finalBid);
      // Success handled by parent component
    } catch (error) {
      AuctionToasts.invalidBid(error.message || 'Failed to place bid');
    } finally {
      setIsPlacing(false);
    }
  };

  const handleCustomBidChange = (e) => {
    const value = e.target.value.replace(/[^0-9]/g, ''); // Only numbers
    setCustomBid(value);
  };

  const getValidationState = () => {
    const finalBid = useCustomBid ? parseInt(customBid) : bidAmount;
    
    if (isNaN(finalBid) || finalBid < currentBid + minIncrement) {
      return { 
        valid: false, 
        message: `Minimum bid: ${currentBid + minIncrement}M` 
      };
    }
    
    if (finalBid > userBudget.remaining) {
      return { 
        valid: false, 
        message: `Exceeds budget: ${userBudget.remaining}M` 
      };
    }

    const budgetAfterBid = userBudget.remaining - finalBid;
    const minReserveNeeded = remainingSlots * minIncrement;
    if (budgetAfterBid < minReserveNeeded) {
      return { 
        valid: false, 
        message: `Need ${minReserveNeeded}M reserve for ${remainingSlots} slots` 
      };
    }

    return { valid: true, message: '' };
  };

  const validation = getValidationState();
  const finalBid = useCustomBid ? parseInt(customBid) : bidAmount;

  if (!isActiveUser) {
    return (
      <div className={`p-4 bg-gray-50 rounded-lg border ${className}`}>
        <div className="text-center text-gray-600">
          <DollarSign className="w-8 h-8 mx-auto mb-2 text-gray-400" />
          <p className="font-medium">Auction Inactive</p>
          <p className="text-sm">Wait for the current lot to complete</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Keyboard shortcuts hint */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
        <div className="flex items-center space-x-2 text-blue-800">
          <Keyboard className="w-4 h-4" />
          <span className="text-sm font-medium">Keyboard Shortcuts</span>
        </div>
        <div className="text-xs text-blue-600 mt-1 space-y-1">
          <div><kbd className="px-1 py-0.5 bg-blue-100 rounded text-blue-800">B</kbd> Place bid</div>
          <div><kbd className="px-1 py-0.5 bg-blue-100 rounded text-blue-800">+/-</kbd> Adjust amount</div>
          <div><kbd className="px-1 py-0.5 bg-blue-100 rounded text-blue-800">C</kbd> Custom bid</div>
        </div>
      </div>

      {/* Current bid display */}
      <div className="bg-gray-50 rounded-lg p-3">
        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-600">Current Bid</span>
          <span className="text-lg font-bold text-gray-900">{currentBid}M</span>
        </div>
        <div className="flex justify-between items-center mt-1">
          <span className="text-sm text-gray-600">Minimum Next</span>
          <span className="text-sm font-semibold text-blue-600">
            {currentBid + minIncrement}M
          </span>
        </div>
      </div>

      {/* Bid amount controls */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <Label htmlFor="bid-amount" className="text-sm font-medium">
            Your Bid
          </Label>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={toggleCustomBid}
            className="text-xs"
          >
            {useCustomBid ? 'Quick Bid' : 'Custom Bid'}
          </Button>
        </div>

        {useCustomBid ? (
          <div className="relative">
            <Input
              ref={inputRef}
              id="bid-amount"
              type="text"
              value={customBid}
              onChange={handleCustomBidChange}
              placeholder={`Min: ${currentBid + minIncrement}`}
              className={`pr-8 ${!validation.valid ? 'border-red-500' : ''}`}
              disabled={disabled}
              aria-describedby="bid-validation"
            />
            <span className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-500 text-sm">
              M
            </span>
          </div>
        ) : (
          <div className="flex items-center space-x-2">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={decreaseBid}
              disabled={disabled || bidAmount <= currentBid + minIncrement}
              aria-label="Decrease bid amount"
            >
              <Minus className="w-4 h-4" />
            </Button>
            
            <div className="flex-1 text-center">
              <span className="text-2xl font-bold text-gray-900">
                {bidAmount}M
              </span>
            </div>
            
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={increaseBid}
              disabled={disabled}
              aria-label="Increase bid amount"
            >
              <Plus className="w-4 h-4" />
            </Button>
          </div>
        )}

        {/* Validation message */}
        {!validation.valid && (
          <div 
            id="bid-validation"
            className="text-xs text-red-600 bg-red-50 border border-red-200 rounded px-2 py-1"
            role="alert"
          >
            {validation.message}
          </div>
        )}
      </div>

      {/* Budget status */}
      <BudgetTooltip 
        remaining={userBudget.remaining}
        slotsLeft={remainingSlots}
        minIncrement={minIncrement}
      >
        <div className="bg-gray-50 rounded-lg p-3 cursor-help">
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-600">Budget Remaining</span>
            <span className="font-semibold text-green-600">
              {userBudget.remaining}M
            </span>
          </div>
          <div className="flex justify-between items-center mt-1">
            <span className="text-sm text-gray-600">After This Bid</span>
            <span className={`text-sm font-medium ${
              userBudget.remaining - finalBid >= remainingSlots * minIncrement 
                ? 'text-green-600' 
                : 'text-red-600'
            }`}>
              {userBudget.remaining - (isNaN(finalBid) ? 0 : finalBid)}M
            </span>
          </div>
        </div>
      </BudgetTooltip>

      {/* Place bid button */}
      <Button
        ref={buttonRef}
        onClick={handlePlaceBid}
        disabled={disabled || !validation.valid || isPlacing}
        className="w-full"
        size="lg"
      >
        {isPlacing ? (
          <div className="flex items-center space-x-2">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
            <span>Placing Bid...</span>
          </div>
        ) : (
          <div className="flex items-center space-x-2">
            <Zap className="w-4 h-4" />
            <span>Place Bid: {isNaN(finalBid) ? '0' : finalBid}M</span>
          </div>
        )}
      </Button>

      {/* Quick bid shortcuts */}
      <div className="grid grid-cols-3 gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={() => {
            const quickBid = currentBid + minIncrement;
            if (useCustomBid) {
              setCustomBid(quickBid.toString());
            } else {
              setBidAmount(quickBid);
            }
          }}
          disabled={disabled}
        >
          Min ({currentBid + minIncrement}M)
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={() => {
            const quickBid = currentBid + (minIncrement * 3);
            if (useCustomBid) {
              setCustomBid(quickBid.toString());
            } else {
              setBidAmount(quickBid);
            }
          }}
          disabled={disabled}
        >
          +{minIncrement * 3}M
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={() => {
            const quickBid = currentBid + (minIncrement * 5);
            if (useCustomBid) {
              setCustomBid(quickBid.toString());
            } else {
              setBidAmount(quickBid);
            }
          }}
          disabled={disabled}
        >
          +{minIncrement * 5}M
        </Button>
      </div>
    </div>
  );
};