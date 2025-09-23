import { toast } from 'sonner';
import { CheckCircle, XCircle, Clock, Gavel, AlertTriangle, Trophy, Zap } from 'lucide-react';

// Enhanced toast notifications for auction events with rich styling and icons

export const AuctionToasts = {
  // Successful bid placed
  bidPlaced: (clubName, amount) => {
    toast.success(
      <div className="flex items-center space-x-3">
        <Gavel className="w-5 h-5 text-green-600" />
        <div>
          <div className="font-semibold">Bid Placed!</div>
          <div className="text-sm text-gray-600">
            {amount}M bid on {clubName}
          </div>
        </div>
      </div>,
      {
        duration: 3000,
        className: "border-l-4 border-green-500"
      }
    );
  },

  // Outbid notification
  outbid: (clubName, newAmount, bidderName) => {
    toast.error(
      <div className="flex items-center space-x-3">
        <XCircle className="w-5 h-5 text-red-600" />
        <div>
          <div className="font-semibold">You've been outbid!</div>
          <div className="text-sm text-gray-600">
            {bidderName} bid {newAmount}M on {clubName}
          </div>
        </div>
      </div>,
      {
        duration: 5000,
        className: "border-l-4 border-red-500",
        action: {
          label: "View Auction",
          onClick: () => window.location.hash = '#auction'
        }
      }
    );
  },

  // Club sold notification
  clubSold: (clubName, finalPrice, winner, isWinner = false) => {
    if (isWinner) {
      toast.success(
        <div className="flex items-center space-x-3">
          <Trophy className="w-5 h-5 text-yellow-600" />
          <div>
            <div className="font-semibold">Congratulations!</div>
            <div className="text-sm text-gray-600">
              You won {clubName} for {finalPrice}M
            </div>
          </div>
        </div>,
        {
          duration: 6000,
          className: "border-l-4 border-yellow-500"
        }
      );
    } else {
      toast.info(
        <div className="flex items-center space-x-3">
          <Gavel className="w-5 h-5 text-blue-600" />
          <div>
            <div className="font-semibold">Club Sold</div>
            <div className="text-sm text-gray-600">
              {winner} won {clubName} for {finalPrice}M
            </div>
          </div>
        </div>,
        {
          duration: 4000,
          className: "border-l-4 border-blue-500"
        }
      );
    }
  },

  // Timer extended (anti-snipe)
  timerExtended: (clubName, newEndTime) => {
    toast.warning(
      <div className="flex items-center space-x-3">
        <Clock className="w-5 h-5 text-orange-600" />
        <div>
          <div className="font-semibold">Timer Extended!</div>
          <div className="text-sm text-gray-600">
            Anti-snipe activated for {clubName}
          </div>
        </div>
      </div>,
      {
        duration: 3000,
        className: "border-l-4 border-orange-500"
      }
    );
  },

  // Invalid bid feedback
  invalidBid: (reason) => {
    const reasons = {
      'insufficient_budget': 'Insufficient budget for this bid',
      'below_minimum': 'Bid must be higher than current bid + minimum increment',
      'auction_closed': 'This auction lot is no longer active',
      'already_owner': 'You already own a club in this league',
      'budget_constraint': 'Would leave insufficient budget for remaining slots'
    };

    toast.error(
      <div className="flex items-center space-x-3">
        <AlertTriangle className="w-5 h-5 text-red-600" />
        <div>
          <div className="font-semibold">Invalid Bid</div>
          <div className="text-sm text-gray-600">
            {reasons[reason] || reason}
          </div>
        </div>
      </div>,
      {
        duration: 4000,
        className: "border-l-4 border-red-500"
      }
    );
  },

  // Auction started
  auctionStarted: (leagueName) => {
    toast.success(
      <div className="flex items-center space-x-3">
        <Zap className="w-5 h-5 text-green-600" />
        <div>
          <div className="font-semibold">Auction Started!</div>
          <div className="text-sm text-gray-600">
            {leagueName} auction is now live
          </div>
        </div>
      </div>,
      {
        duration: 5000,
        className: "border-l-4 border-green-500",
        action: {
          label: "Join Now",
          onClick: () => window.location.hash = '#auction'
        }
      }
    );
  },

  // Auction paused
  auctionPaused: () => {
    toast.warning(
      <div className="flex items-center space-x-3">
        <Clock className="w-5 h-5 text-orange-600" />
        <div>
          <div className="font-semibold">Auction Paused</div>
          <div className="text-sm text-gray-600">
            The commissioner has paused the auction
          </div>
        </div>
      </div>,
      {
        duration: 4000,
        className: "border-l-4 border-orange-500"
      }
    );
  },

  // Auction resumed
  auctionResumed: () => {
    toast.info(
      <div className="flex items-center space-x-3">
        <Zap className="w-5 h-5 text-blue-600" />
        <div>
          <div className="font-semibold">Auction Resumed</div>
          <div className="text-sm text-gray-600">
            Bidding is active again
          </div>
        </div>
      </div>,
      {
        duration: 3000,
        className: "border-l-4 border-blue-500"
      }
    );
  },

  // Budget warning
  budgetWarning: (remaining, slotsLeft) => {
    toast.warning(
      <div className="flex items-center space-x-3">
        <AlertTriangle className="w-5 h-5 text-yellow-600" />
        <div>
          <div className="font-semibold">Budget Warning</div>
          <div className="text-sm text-gray-600">
            Only {remaining}M left for {slotsLeft} slots
          </div>
        </div>
      </div>,
      {
        duration: 5000,
        className: "border-l-4 border-yellow-500"
      }
    );
  },

  // New lot started
  newLotStarted: (clubName, nominator) => {
    toast.info(
      <div className="flex items-center space-x-3">
        <Gavel className="w-5 h-5 text-blue-600" />
        <div>
          <div className="font-semibold">New Lot</div>
          <div className="text-sm text-gray-600">
            {clubName} nominated by {nominator}
          </div>
        </div>
      </div>,
      {
        duration: 4000,
        className: "border-l-4 border-blue-500"
      }
    );
  },

  // Match result points
  pointsAwarded: (clubName, points, matchResult) => {
    toast.success(
      <div className="flex items-center space-x-3">
        <Trophy className="w-5 h-5 text-green-600" />
        <div>
          <div className="font-semibold">Points Earned!</div>
          <div className="text-sm text-gray-600">
            {clubName}: +{points} pts ({matchResult})
          </div>
        </div>
      </div>,
      {
        duration: 4000,
        className: "border-l-4 border-green-500"
      }
    );
  }
};

// Utility function to show appropriate toast based on WebSocket auction updates
export const handleAuctionUpdate = (update, currentUserId) => {
  const { type, data } = update;

  switch (type) {
    case 'bid_placed':
      if (data.bidder_id === currentUserId) {
        AuctionToasts.bidPlaced(data.club_name, data.amount);
      }
      break;
      
    case 'outbid':
      if (data.previous_bidder_id === currentUserId) {
        AuctionToasts.outbid(data.club_name, data.new_amount, data.new_bidder_name);
      }
      break;
      
    case 'lot_sold':
      AuctionToasts.clubSold(
        data.club_name, 
        data.final_price, 
        data.winner_name,
        data.winner_id === currentUserId
      );
      break;
      
    case 'timer_extended':
      AuctionToasts.timerExtended(data.club_name, data.new_end_time);
      break;
      
    case 'auction_started':
      AuctionToasts.auctionStarted(data.league_name);
      break;
      
    case 'auction_paused':
      AuctionToasts.auctionPaused();
      break;
      
    case 'auction_resumed':
      AuctionToasts.auctionResumed();
      break;
      
    case 'new_lot':
      AuctionToasts.newLotStarted(data.club_name, data.nominator_name);
      break;
      
    default:
      // Generic update notification
      break;
  }
};