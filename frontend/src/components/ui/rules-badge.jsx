import React from 'react';
import { Badge } from './badge.jsx';
import { Info } from 'lucide-react';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from './tooltip.jsx';
import { useTranslation } from 'react-i18next';

/**
 * Rules Badge Component
 * Displays league configuration rules in a compact format
 * 
 * @param {Object} leagueSettings - League settings from useLeagueSettings hook
 * @param {boolean} loading - Whether settings are still loading
 * @param {string} className - Additional CSS classes
 */
export const RulesBadge = ({ leagueSettings, loading = false, className = "" }) => {
  if (loading || !leagueSettings) {
    return (
      <Badge variant="outline" className={`text-xs ${className}`}>
        <Info className="w-3 h-3 mr-1" />
        Loading rules...
      </Badge>
    );
  }

  const { clubSlots, budgetPerManager, leagueSize } = leagueSettings;
  
  // Format the rules text
  const rulesText = `Slots: ${clubSlots} · Budget: ${budgetPerManager} · Min: ${leagueSize.min} · Max: ${leagueSize.max}`;
  
  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <Badge variant="outline" className={`text-xs bg-blue-50 border-blue-200 text-blue-700 hover:bg-blue-100 cursor-help ${className}`}>
            <Info className="w-3 h-3 mr-1" />
            Rules
          </Badge>
        </TooltipTrigger>
        <TooltipContent side="bottom" className="max-w-xs">
          <div className="text-sm">
            <div className="font-medium mb-1">League Rules</div>
            <div className="space-y-1 text-xs">
              <div>• Club Slots per Manager: <strong>{clubSlots}</strong></div>
              <div>• Budget per Manager: <strong>${budgetPerManager}M</strong></div>
              <div>• Min Managers: <strong>{leagueSize.min}</strong></div>
              <div>• Max Managers: <strong>{leagueSize.max}</strong></div>
            </div>
          </div>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
};

/**
 * Compact Rules Display
 * Shows the full rules text inline (for headers/status bars)
 */
export const CompactRules = ({ leagueSettings, loading = false, className = "" }) => {
  if (loading || !leagueSettings) {
    return (
      <span className={`text-xs text-gray-500 ${className}`}>
        Loading rules...
      </span>
    );
  }

  const { clubSlots, budgetPerManager, leagueSize } = leagueSettings;
  const rulesText = `Slots: ${clubSlots} · Budget: ${budgetPerManager} · Min: ${leagueSize.min} · Max: ${leagueSize.max}`;
  
  return (
    <span className={`text-xs text-gray-600 font-mono ${className}`}>
      {rulesText}
    </span>
  );
};

export default RulesBadge;