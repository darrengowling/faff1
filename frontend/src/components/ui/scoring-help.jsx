import React from 'react';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from './tooltip.jsx';
import { HelpCircle, Trophy, Target } from 'lucide-react';

/**
 * Scoring Help Component
 * 
 * Provides clear explanation of the scoring system with examples
 * Addresses usability issue: "Clear mental model - What do I own? How do I win?"
 */

export const ScoringHelp = ({ className = "" }) => {
  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <button 
            className={`inline-flex items-center text-gray-600 hover:text-gray-800 transition-colors ${className}`}
            aria-label="How scoring works"
          >
            <HelpCircle className="w-4 h-4 mr-1" aria-hidden="true" />
            <span className="text-sm">How scoring works</span>
          </button>
        </TooltipTrigger>
        <TooltipContent 
          side="top" 
          className="max-w-xs p-4 bg-white border shadow-lg rounded-lg"
          sideOffset={5}
        >
          <div className="space-y-3">
            <div className="font-semibold text-gray-900 flex items-center">
              <Trophy className="w-4 h-4 mr-2 text-yellow-500" aria-hidden="true" />
              Scoring System
            </div>
            
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span>Per Goal:</span>
                <span className="font-medium text-green-600">+1 point</span>
              </div>
              <div className="flex justify-between">
                <span>Win:</span>
                <span className="font-medium text-green-600">+3 points</span>
              </div>
              <div className="flex justify-between">
                <span>Draw:</span>
                <span className="font-medium text-blue-600">+1 point</span>
              </div>
              <div className="flex justify-between">
                <span>Loss:</span>
                <span className="font-medium text-gray-500">+0 points</span>
              </div>
            </div>
            
            <div className="border-t pt-3">
              <div className="font-medium text-gray-900 mb-2">Examples:</div>
              <div className="space-y-1 text-xs text-gray-700">
                <div className="flex justify-between">
                  <span>Manchester City 2-2 Real Madrid</span>
                  <span className="font-medium">3 pts each</span>
                </div>
                <div className="text-xs text-gray-500">
                  (2 goals + 1 draw = 3 points)
                </div>
                
                <div className="flex justify-between mt-2">
                  <span>Liverpool 3-1 Barcelona</span>
                  <span className="font-medium">6 pts | 1 pt</span>
                </div>
                <div className="text-xs text-gray-500">
                  Liverpool: 3 goals + 3 win = 6 pts<br/>
                  Barcelona: 1 goal + 0 loss = 1 pt
                </div>
              </div>
            </div>
          </div>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
};

export const QuickScoringTip = ({ className = "" }) => {
  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <div className={`inline-flex items-center text-gray-500 hover:text-gray-700 cursor-help ${className}`}>
            <Target className="w-3 h-3 mr-1" aria-hidden="true" />
            <span className="text-xs">Scoring</span>
          </div>
        </TooltipTrigger>
        <TooltipContent className="bg-gray-900 text-white text-xs p-2 rounded">
          Goals +1, Win +3, Draw +1
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
};

export default ScoringHelp;