import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Button } from './button';
import { AlertTriangle, Clock, X, CheckCircle } from 'lucide-react';
import { Badge } from './badge';
import { toast } from 'sonner';

/**
 * Lot Close Confirmation Dialog
 * Shows confirmation with 10-second undo countdown
 */
export const LotCloseConfirmation = ({
  const { t } = useTranslation(); 
  isOpen, 
  onClose, 
  onConfirm, 
  lotDetails,
  loading = false 
}) => {
  const [reason, setReason] = useState('');
  const [forced, setForced] = useState(false);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold flex items-center">
            <AlertTriangle className="w-5 h-5 text-orange-500 mr-2" />
            Close Lot
          </h3>
          <Button variant="ghost" size="sm" onClick={onClose}>
            <X className="w-4 h-4" />
          </Button>
        </div>
        
        <div className="space-y-4">
          <div className="bg-gray-50 p-3 rounded">
            <div className="font-medium">{lotDetails?.club_name || 'Unknown Club'}</div>
            <div className="text-sm text-gray-600">
              Current bid: {lotDetails?.current_bid || 0}M
            </div>
            {lotDetails?.leading_bidder && (
              <div className="text-sm text-gray-600">
                Leading: {lotDetails.leading_bidder}
              </div>
            )}
          </div>
          
          <div>
            <label className="block text-sm font-medium mb-2">
              Reason (optional)
            </label>
            <input
              type="text"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="e.g., Time limit reached"
              className="w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          
          {lotDetails?.timer_active && (
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="forced"
                checked={forced}
                onChange={(e) => setForced(e.target.checked)}
                className="rounded"
              />
              <label htmlFor="forced" className="text-sm text-orange-600">
                Force close (timer still active)
              </label>
            </div>
          )}
          
          <div className="bg-blue-50 p-3 rounded">
            <div className="text-sm text-blue-800">
              <strong>Note:</strong> You'll have 10 seconds to undo this action after closing.
            </div>
          </div>
          
          <div className="flex space-x-3">
            <Button
              variant="outline"
              onClick={onClose}
              disabled={loading}
              className="flex-1"
            >
              Cancel
            </Button>
            <Button
              onClick={() => onConfirm(reason, forced)}
              disabled={loading}
              className="flex-1 bg-red-600 hover:bg-red-700"
            >
              {loading ? 'Closing...' : 'Close Lot'}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

/**
 * Undo Countdown Timer
 * Shows live countdown with undo button
 */
export const UndoCountdown = ({ 
  actionId, 
  deadline, 
  onUndo, 
  onExpired,
  className = ""
}) => {
  const [timeLeft, setTimeLeft] = useState(0);
  const [isUndoing, setIsUndoing] = useState(false);

  useEffect(() => {
    if (!deadline) return;

    const updateTimer = () => {
      const now = Date.now();
      const endTime = new Date(deadline).getTime();
      const remaining = Math.max(0, Math.floor((endTime - now) / 1000));
      
      setTimeLeft(remaining);
      
      if (remaining === 0) {
        onExpired();
      }
    };

    // Update immediately and then every second
    updateTimer();
    const interval = setInterval(updateTimer, 1000);

    return () => clearInterval(interval);
  }, [deadline, onExpired]);

  const handleUndo = async () => {
    if (isUndoing) return;
    
    setIsUndoing(true);
    try {
      await onUndo(actionId);
    } finally {
      setIsUndoing(false);
    }
  };

  if (timeLeft === 0) return null;

  return (
    <div className={`bg-yellow-50 border border-yellow-200 rounded-lg p-4 ${className}`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Clock className="w-5 h-5 text-yellow-600" />
          <div>
            <div className="font-medium text-yellow-800">
              Lot closing in progress
            </div>
            <div className="text-sm text-yellow-600">
              {timeLeft} seconds left to undo
            </div>
          </div>
        </div>
        
        <Button
          onClick={handleUndo}
          disabled={isUndoing}
          variant="outline"
          size="sm"
          className="border-yellow-600 text-yellow-700 hover:bg-yellow-100"
        >
          {isUndoing ? 'Undoing...' : 'Undo'}
        </Button>
      </div>
      
      {/* Progress bar */}
      <div className="mt-3 w-full bg-yellow-200 rounded-full h-2">
        <div 
          className="bg-yellow-600 h-2 rounded-full transition-all duration-1000"
          style={{ width: `${(timeLeft / 10) * 100}%` }}
        />
      </div>
    </div>
  );
};

/**
 * Lot Status Indicator
 * Shows current lot status with appropriate styling
 */
export const LotStatusIndicator = ({ status, className = "" }) => {
  const getStatusConfig = () => {
    switch (status) {
      case 'open':
        return {
          text: 'Open',
          className: 'bg-green-100 text-green-800',
          icon: null
        };
      case 'pre_closed':
        return {
          text: 'Closing...',
          className: 'bg-yellow-100 text-yellow-800 animate-pulse',
          icon: Clock
        };
      case 'sold':
        return {
          text: 'Sold',
          className: 'bg-blue-100 text-blue-800',
          icon: CheckCircle
        };
      case 'unsold':
        return {
          text: 'Unsold',
          className: 'bg-gray-100 text-gray-800',
          icon: X
        };
      default:
        return {
          text: status || 'Unknown',
          className: 'bg-gray-100 text-gray-800',
          icon: null
        };
    }
  };

  const config = getStatusConfig();
  const Icon = config.icon;

  return (
    <Badge className={`${config.className} ${className}`}>
      {Icon && <Icon className="w-3 h-3 mr-1" />}
      {config.text}
    </Badge>
  );
};

/**
 * Commissioner Controls for Lot Management
 * Shows close/undo buttons for commissioners
 */
export const CommissionerLotControls = ({
  lot,
  isCommissioner,
  onCloseLot,
  onUndoAction,
  undoActions = [],
  loading = false,
  className = ""
}) => {
  if (!isCommissioner) return null;

  const canClose = lot.status === 'open';
  const hasActiveUndo = undoActions.length > 0;
  const isPreClosed = lot.status === 'pre_closed';

  return (
    <div className={`space-y-2 ${className}`}>
      {canClose && !hasActiveUndo && (
        <Button
          onClick={() => onCloseLot(lot)}
          disabled={loading}
          variant="outline"
          size="sm"
          className="border-red-300 text-red-700 hover:bg-red-50"
        >
          Close Lot
        </Button>
      )}
      
      {hasActiveUndo && undoActions.map(action => (
        <UndoCountdown
          key={action.action_id}
          actionId={action.action_id}
          deadline={action.undo_deadline}
          onUndo={onUndoAction}
          onExpired={() => {
            toast.info('Lot closing finalized');
          }}
        />
      ))}
      
      {isPreClosed && !hasActiveUndo && (
        <div className="bg-gray-100 p-2 rounded text-sm text-gray-600">
          Lot closed - finalizing...
        </div>
      )}
    </div>
  );
};

export default {
  LotCloseConfirmation,
  UndoCountdown,
  LotStatusIndicator,
  CommissionerLotControls
};