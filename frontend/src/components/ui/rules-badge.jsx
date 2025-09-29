import React from 'react';
import { Badge } from './badge.jsx';
import { Info } from 'lucide-react';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from './tooltip.jsx';
import { useTranslation } from 'react-i18next';
import { TESTIDS } from '../../testids';

/**
 * Rules Badge Component
 * Displays league configuration rules in a compact format
 * 
 * @param {Object} leagueSettings - League settings from useLeagueSettings hook
 * @param {boolean} loading - Whether settings are still loading
 * @param {string} className - Additional CSS classes
 */
export const RulesBadge = ({ leagueSettings, loading = false, className = "" }) => {
  const { t } = useTranslation();
  
  if (loading || !leagueSettings) {
    return (
      <Badge variant="outline" className={`text-xs ${className}`}>
        <Info className="w-3 h-3 mr-1" />
        {t('rules.loading')}
      </Badge>
    );
  }

  const { clubSlots, budgetPerManager, leagueSize } = leagueSettings;
  
  // Format the rules text
  const rulesText = t('rules.slots', { slots: clubSlots }) + ' · ' + 
                   t('rules.budget', { budget: budgetPerManager }) + ' · ' + 
                   t('rules.min', { min: leagueSize.min }) + ' · ' + 
                   t('rules.max', { max: leagueSize.max });
  
  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <Badge variant="outline" className={`text-xs bg-blue-50 border-blue-200 text-blue-700 hover:bg-blue-100 cursor-help ${className}`} data-testid={TESTIDS.rulesBadge}>
            <Info className="w-3 h-3 mr-1" />
            {t('rules.rules')}
          </Badge>
        </TooltipTrigger>
        <TooltipContent side="bottom" className="max-w-xs">
          <div className="text-sm">
            <div className="font-medium mb-1">{t('rules.leagueRules')}</div>
            <div className="space-y-1 text-xs">
              <div>• {t('rules.clubSlotsPerManager', { slots: clubSlots })}</div>
              <div>• {t('rules.budgetPerManager', { budget: budgetPerManager })}</div>
              <div>• {t('rules.minManagers', { min: leagueSize.min })}</div>
              <div>• {t('rules.maxManagers', { max: leagueSize.max })}</div>
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
  const { t } = useTranslation();
  
  if (loading || !leagueSettings) {
    return (
      <span className={`text-xs text-gray-500 ${className}`}>
        {t('rules.loading')}
      </span>
    );
  }

  const { clubSlots, budgetPerManager, leagueSize } = leagueSettings;
  const rulesText = t('rules.slots', { slots: clubSlots }) + ' · ' + 
                   t('rules.budget', { budget: budgetPerManager }) + ' · ' + 
                   t('rules.min', { min: leagueSize.min }) + ' · ' + 
                   t('rules.max', { max: leagueSize.max });
  
  return (
    <span className={`text-xs text-gray-600 font-mono ${className}`} data-testid={TESTIDS.rulesBadge}>
      {rulesText}
    </span>
  );
};

export default RulesBadge;