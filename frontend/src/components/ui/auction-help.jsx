import React from 'react';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from './tooltip.jsx';
import { HelpCircle, Timer, DollarSign, Users, Shield, Target, TrendingUp, AlertTriangle } from 'lucide-react';

/**
 * Comprehensive auction mechanics explanation component
 * Provides detailed guidance for new users on how the auction system works
 */
export const AuctionMechanicsHelp = ({ className = "" }) => {
  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <div className={`inline-flex items-center text-blue-500 hover:text-blue-600 cursor-help ${className}`}>
            <HelpCircle className="w-4 h-4 mr-1" aria-hidden="true" />
            <span className="text-sm">How it works</span>
          </div>
        </TooltipTrigger>
        <TooltipContent 
          className="bg-gray-900 text-white text-sm p-4 rounded-lg shadow-xl max-w-sm"
          side="bottom"
        >
          <div className="space-y-3">
            <div className="font-semibold text-blue-300 border-b border-gray-700 pb-2">
              🏆 UCL Auction Guide
            </div>
            
            <div className="space-y-2">
              <div className="flex items-start space-x-2">
                <Timer className="w-4 h-4 text-orange-400 mt-0.5 flex-shrink-0" />
                <div>
                  <div className="font-medium text-orange-300">Timer System</div>
                  <div className="text-xs text-gray-300">
                    Each club has a bidding timer. New bids extend the timer to prevent sniping.
                  </div>
                </div>
              </div>
              
              <div className="flex items-start space-x-2">
                <DollarSign className="w-4 h-4 text-green-400 mt-0.5 flex-shrink-0" />
                <div>
                  <div className="font-medium text-green-300">Budget Management</div>
                  <div className="text-xs text-gray-300">
                    You must keep enough budget to fill all remaining club slots at minimum price.
                  </div>
                </div>
              </div>
              
              <div className="flex items-start space-x-2">
                <Users className="w-4 h-4 text-blue-400 mt-0.5 flex-shrink-0" />
                <div>
                  <div className="font-medium text-blue-300">Club Ownership</div>
                  <div className="text-xs text-gray-300">
                    Each club can only be owned by one manager. Plan your strategy accordingly.
                  </div>
                </div>
              </div>
              
              <div className="flex items-start space-x-2">
                <Target className="w-4 h-4 text-purple-400 mt-0.5 flex-shrink-0" />
                <div>
                  <div className="font-medium text-purple-300">Scoring System</div>
                  <div className="text-xs text-gray-300">
                    Goals (+1), Wins (+3), Draws (+1). Higher scores = better leaderboard position.
                  </div>
                </div>
              </div>
            </div>
            
            <div className="border-t border-gray-700 pt-2">
              <div className="text-xs text-gray-400">
                💡 Tip: Bid strategically - expensive clubs need to perform well to justify their cost!
              </div>
            </div>
          </div>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
};

/**
 * Quick bidding tips for mobile users
 */
export const BiddingTips = ({ className = "" }) => {
  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <div className={`inline-flex items-center text-yellow-500 hover:text-yellow-600 cursor-help ${className}`}>
            <TrendingUp className="w-4 h-4 mr-1" aria-hidden="true" />
            <span className="text-sm">Bidding Tips</span>
          </div>
        </TooltipTrigger>
        <TooltipContent 
          className="bg-gray-900 text-white text-sm p-4 rounded-lg shadow-xl max-w-sm"
          side="bottom"
        >
          <div className="space-y-3">
            <div className="font-semibold text-yellow-300 border-b border-gray-700 pb-2">
              💰 Smart Bidding Strategy
            </div>
            
            <div className="space-y-2 text-xs">
              <div className="flex items-center space-x-2">
                <span className="text-green-400">✓</span>
                <span>Use quick bid buttons (+1, +5, +10) for faster bidding</span>
              </div>
              <div className="flex items-center space-x-2">
                <span className="text-green-400">✓</span>
                <span>Monitor your budget - keep reserves for remaining slots</span>
              </div>
              <div className="flex items-center space-x-2">
                <span className="text-green-400">✓</span>
                <span>Bid early on clubs you really want - prices tend to rise</span>
              </div>
              <div className="flex items-center space-x-2">
                <span className="text-red-400">✗</span>
                <span>Don't bid at the last second - timer extends automatically</span>
              </div>
              <div className="flex items-center space-x-2">
                <span className="text-red-400">✗</span>
                <span>Avoid overspending on one club - balance is key</span>
              </div>
            </div>
            
            <div className="border-t border-gray-700 pt-2">
              <div className="text-xs text-gray-400">
                ⚡ Pro tip: Watch other managers' budgets to predict their bidding limits!
              </div>
            </div>
          </div>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
};

/**
 * Budget constraint explanation
 */
export const BudgetConstraintHelp = ({ remaining, slotsLeft, minIncrement = 1, className = "" }) => {
  const minReserveNeeded = slotsLeft * minIncrement;
  const canSpend = Math.max(0, remaining - minReserveNeeded);
  
  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <div className={`inline-flex items-center text-amber-500 hover:text-amber-600 cursor-help ${className}`}>
            <Shield className="w-4 h-4 mr-1" aria-hidden="true" />
            <span className="text-sm">Budget Rules</span>
          </div>
        </TooltipTrigger>
        <TooltipContent 
          className="bg-gray-900 text-white text-sm p-4 rounded-lg shadow-xl max-w-sm"
          side="bottom"
        >
          <div className="space-y-3">
            <div className="font-semibold text-amber-300 border-b border-gray-700 pb-2">
              💳 Your Budget Status
            </div>
            
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-gray-300">Total Remaining:</span>
                <span className="text-green-400 font-medium">{remaining}M</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-300">Slots Left:</span>
                <span className="text-blue-400 font-medium">{slotsLeft}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-300">Must Reserve:</span>
                <span className="text-red-400 font-medium">{minReserveNeeded}M</span>
              </div>
              <div className="border-t border-gray-700 pt-2 flex justify-between">
                <span className="text-gray-300 font-medium">Can Spend Now:</span>
                <span className="text-yellow-400 font-bold">{canSpend}M</span>
              </div>
            </div>
            
            <div className="bg-gray-800 p-2 rounded text-xs">
              <div className="flex items-start space-x-2">
                <AlertTriangle className="w-3 h-3 text-yellow-400 mt-0.5 flex-shrink-0" />
                <div className="text-gray-300">
                  You must keep at least <span className="text-red-400 font-medium">{minIncrement}M per remaining slot</span> to ensure you can buy clubs for all positions.
                </div>
              </div>
            </div>
          </div>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
};

export default { AuctionMechanicsHelp, BiddingTips, BudgetConstraintHelp };