/**
 * Quick Action Cards Component
 * Displays quick actions: Create League, Join via Invite, Resume Auction
 */

import React from 'react';
import { useTranslation } from 'react-i18next';
import { 
  Plus, UserPlus, Play, Trophy, Users, Mail, ArrowRight
} from 'lucide-react';
import { Card, CardContent } from './card';
import { Button } from './button';
import { TESTIDS } from '../../testids';

const QuickActionCards = ({ 
  onCreateLeague, 
  onJoinViaInvite, 
  activeAuctions = [],
  onResumeAuction,
  className = '' 
}) => {
  const { t } = useTranslation();

  const quickActions = [
    {
      id: 'create-league',
      title: 'Create a League',
      description: 'Start a new football auction with friends',
      icon: Plus,
      iconBg: 'bg-blue-100',
      iconColor: 'text-blue-600',
      action: onCreateLeague,
      buttonText: 'Create Now',
      buttonVariant: 'default',
      enabled: true
    },
    {
      id: 'join-invite',
      title: 'Join via Invite',
      description: 'Enter with an invitation code or link',
      icon: UserPlus,
      iconBg: 'bg-green-100',
      iconColor: 'text-green-600',
      action: onJoinViaInvite,
      buttonText: 'Join League',
      buttonVariant: 'outline',
      enabled: true
    }
  ];

  // Add Resume Auction card if there are active auctions
  if (activeAuctions.length > 0) {
    const auctionAction = {
      id: 'resume-auction',
      title: 'Resume Auction',
      description: `${activeAuctions.length} active auction${activeAuctions.length > 1 ? 's' : ''} waiting`,
      icon: Play,
      iconBg: 'bg-orange-100',
      iconColor: 'text-orange-600',
      action: () => onResumeAuction(activeAuctions[0]), // Resume first active auction
      buttonText: 'Resume Now',
      buttonVariant: 'default',
      enabled: true,
      urgent: true
    };
    
    // Insert at the beginning for priority
    quickActions.unshift(auctionAction);
  }

  return (
    <div className={`grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 ${className}`}>
      {quickActions.map((action) => {
        const Icon = action.icon;
        
        return (
          <Card 
            key={action.id}
            className={`group hover:shadow-lg transition-all duration-200 cursor-pointer border-2 hover:border-blue-200 ${
              action.urgent ? 'ring-2 ring-orange-200 border-orange-200' : ''
            }`}
            onClick={action.enabled ? action.action : undefined}
          >
            <CardContent className="p-6">
              <div className="flex flex-col items-center text-center space-y-4">
                {/* Icon */}
                <div className={`w-16 h-16 rounded-full ${action.iconBg} flex items-center justify-center group-hover:scale-110 transition-transform`}>
                  <Icon className={`w-8 h-8 ${action.iconColor}`} />
                </div>

                {/* Content */}
                <div className="space-y-2">
                  <h3 className="text-lg font-semibold text-gray-900">
                    {action.title}
                  </h3>
                  <p className="text-sm text-gray-600">
                    {action.description}
                  </p>
                </div>

                {/* Action Button */}
                <Button
                  variant={action.buttonVariant}
                  className={`w-full group-hover:shadow-md transition-all ${
                    action.urgent ? 'bg-orange-600 hover:bg-orange-700 text-white' : ''
                  }`}
                  onClick={(e) => {
                    e.stopPropagation(); // Prevent card click
                    if (action.enabled && action.action) {
                      action.action();
                    }
                  }}
                  disabled={!action.enabled}
                  data-testid={action.id === 'join-invite' ? TESTIDS.joinLeagueButton : undefined}
                >
                  <span className="flex items-center space-x-2">
                    <span>{action.buttonText}</span>
                    <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                  </span>
                </Button>
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
};

// Enhanced Quick Actions with additional features
export const EnhancedQuickActions = ({ 
  leagues = [], 
  user,
  onCreateLeague,
  onJoinViaInvite,
  onResumeAuction,
  className = ''
}) => {
  const { t } = useTranslation();

  // Find active auctions
  const activeAuctions = leagues.filter(league => 
    league.status === 'active' || league.auction_status === 'active'
  );

  // Find leagues ready to start (for commissioners)
  const readyToStart = leagues.filter(league => 
    league.status === 'ready' && league.commissioner_id === user?.id
  );

  // Build actions array
  const actions = [
    {
      id: 'create-league',
      title: t('dashboard.createLeague', 'Create a League'),
      description: 'Start a new football auction with friends',
      icon: Plus,
      iconBg: 'bg-blue-100',
      iconColor: 'text-blue-600',
      action: onCreateLeague,
      buttonText: 'Create Now',
      buttonVariant: 'default',
      priority: 1
    },
    {
      id: 'join-invite',
      title: 'Join via Invite',
      description: 'Enter with an invitation code or link',
      icon: UserPlus,
      iconBg: 'bg-green-100',
      iconColor: 'text-green-600',
      action: onJoinViaInvite,
      buttonText: 'Join League',
      buttonVariant: 'outline',
      priority: 2
    }
  ];

  // Add Resume Auction (highest priority)
  if (activeAuctions.length > 0) {
    actions.unshift({
      id: 'resume-auction',
      title: 'Resume Auction',
      description: `${activeAuctions.length} active auction${activeAuctions.length > 1 ? 's' : ''} waiting`,
      icon: Play,
      iconBg: 'bg-orange-100',
      iconColor: 'text-orange-600',
      action: () => onResumeAuction(activeAuctions[0]),
      buttonText: 'Resume Now',
      buttonVariant: 'default',
      urgent: true,
      priority: 0
    });
  }

  // Add Start Auction for ready leagues
  if (readyToStart.length > 0) {
    actions.push({
      id: 'start-auction',
      title: 'Start Auction',
      description: `${readyToStart.length} league${readyToStart.length > 1 ? 's' : ''} ready to auction`,
      icon: Trophy,
      iconBg: 'bg-purple-100',
      iconColor: 'text-purple-600',
      action: () => onResumeAuction(readyToStart[0]), // Reuse resume function
      buttonText: 'Start Now',
      buttonVariant: 'outline',
      priority: 1.5
    });
  }

  // Sort by priority
  actions.sort((a, b) => a.priority - b.priority);

  return (
    <QuickActionCards
      onCreateLeague={onCreateLeague}
      onJoinViaInvite={onJoinViaInvite}
      activeAuctions={activeAuctions}
      onResumeAuction={onResumeAuction}
      className={className}
    />
  );
};

export default QuickActionCards;