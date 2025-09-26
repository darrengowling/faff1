/**
 * Dashboard Content Component
 * 
 * Main dashboard content without header/footer - designed to work with AppLayout
 * Extracted from EnhancedHomeScreen for layout separation
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { 
  Trophy, Users, Plus, Mail, Eye, Play, Gavel, 
  Calendar, DollarSign, Target, Crown
} from 'lucide-react';
import { Button } from './ui/button';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Separator } from './ui/separator';
import { useAuth } from '../App';
import PageMenuDropdown from './ui/page-menu-dropdown';
import QuickActionCards from './ui/quick-action-cards';
import LeagueSwitcher from './ui/league-switcher';
import { TESTIDS } from '../testids.ts';

const DashboardContent = ({ 
  leagues = [], 
  onCreateLeague, 
  onViewLeague, 
  onStartAuction,
  onViewAuction,
  loading = false 
}) => {
  const { t } = useTranslation();
  const { user } = useAuth();
  const navigate = useNavigate();
  
  const [selectedLeague, setSelectedLeague] = useState(null);

  // Auto-select first league if only one exists
  useEffect(() => {
    if (leagues.length === 1 && !selectedLeague) {
      setSelectedLeague(leagues[0]);
    }
  }, [leagues, selectedLeague]);

  // Load saved league selection
  useEffect(() => {
    const savedLeagueId = localStorage.getItem('selectedLeagueId');
    if (savedLeagueId && leagues.length > 0) {
      const saved = leagues.find(l => l.id === savedLeagueId);
      if (saved) {
        setSelectedLeague(saved);
      }
    }
  }, [leagues]);

  // Save league selection
  const handleLeagueChange = (league) => {
    setSelectedLeague(league);
    localStorage.setItem('selectedLeagueId', league.id);
  };

  // Find active auctions
  const activeAuctions = leagues.filter(league => 
    league.status === 'active' || league.auction_status === 'active'
  );

  // Handle quick actions
  const handleResumeAuction = (league) => {
    if (league) {
      navigate(`/auction/${league.id}`);
    }
  };

  const handleJoinViaInvite = () => {
    // You can implement an invite dialog or navigate to invite page
    const inviteCode = prompt('Enter your invitation code:');
    if (inviteCode) {
      navigate(`/invite?code=${inviteCode}`);
    }
  };

  if (loading) {
    return (
      <div className="min-h-96 flex items-center justify-center">
        <div className="animate-spin w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full"></div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
      {/* Top Section: League Switcher & Page Menu */}
      <div className="mb-8">
        <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-4">
          {/* League Switcher (only show if multiple leagues) */}
          {leagues.length > 1 && (
            <div className="lg:w-80">
              <label className="block text-sm font-medium text-theme-text-secondary mb-2">
                Active League
              </label>
              <LeagueSwitcher
                leagues={leagues}
                selectedLeague={selectedLeague}
                onLeagueChange={handleLeagueChange}
                user={user}
              />
            </div>
          )}

          {/* Page Menu Dropdown */}
          <div className="lg:w-80">
            <label className="block text-sm font-medium text-theme-text-secondary mb-2">
              Quick Navigation
            </label>
            <PageMenuDropdown
              selectedLeague={selectedLeague}
            />
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="mb-8">
        <h2 className="text-xl font-semibold text-theme-text mb-4">
          Quick Actions
        </h2>
        <QuickActionCards
          onCreateLeague={onCreateLeague}
          onJoinViaInvite={handleJoinViaInvite}
          activeAuctions={activeAuctions}
          onResumeAuction={handleResumeAuction}
        />
      </div>

      {/* Current League Info (if one is selected) */}
      {selectedLeague && (
        <div className="mb-8">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold text-theme-text">
              Current League
            </h2>
            <Button
              variant="outline"
              size="sm"
              onClick={() => onViewLeague(selectedLeague)}
            >
              <Eye className="w-4 h-4 mr-2" />
              Manage League
            </Button>
          </div>

          <Card className="bg-theme-surface border-theme-surface-border">
            <CardHeader>
              <div className="flex justify-between items-start">
                <div>
                  <CardTitle className="text-lg text-theme-text">{selectedLeague.name}</CardTitle>
                  <p className="text-sm text-theme-text-secondary flex items-center mt-1">
                    <Calendar className="w-3 h-3 mr-1" />
                    {selectedLeague.season}
                  </p>
                </div>
                <div className="flex flex-col items-end space-y-1">
                  {selectedLeague.commissioner_id === user.id && (
                    <Badge variant="outline" className="bg-yellow-50 text-yellow-700 border-yellow-200">
                      <Crown className="w-3 h-3 mr-1" />
                      Commissioner
                    </Badge>
                  )}
                  <Badge variant={selectedLeague.status === 'ready' ? 'default' : 'secondary'}>
                    {selectedLeague.status}
                  </Badge>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-theme-text-secondary flex items-center">
                    <Users className="w-3 h-3 mr-1" />
                    Members
                  </span>
                  <span className="font-medium text-theme-text">{selectedLeague.member_count}</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-theme-text-secondary flex items-center">
                    <DollarSign className="w-3 h-3 mr-1" />
                    Budget
                  </span>
                  <span className="font-medium text-theme-text">{selectedLeague.settings?.budget_per_manager || 'N/A'} credits</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-theme-text-secondary flex items-center">
                    <Target className="w-3 h-3 mr-1" />
                    Club Slots
                  </span>
                  <span className="font-medium text-theme-text">{selectedLeague.settings?.club_slots_per_manager || 'N/A'}</span>
                </div>
              </div>
              
              <Separator className="mb-4" />
              
              <div className="flex space-x-2">
                <Button 
                  className="flex-1" 
                  variant="outline"
                  onClick={() => onViewLeague(selectedLeague)}
                >
                  <Eye className="w-4 h-4 mr-2" />
                  Manage League
                </Button>
                {selectedLeague.status === 'ready' && selectedLeague.commissioner_id === user.id && (
                  <Button
                    size="sm"
                    onClick={() => onStartAuction(selectedLeague.id)}
                    className="bg-green-600 hover:bg-green-700"
                    data-testid={TESTIDS.startAuctionBtn}
                  >
                    <Play className="w-4 h-4 mr-1" />
                    Start Auction
                  </Button>
                )}
                {selectedLeague.status === 'active' && (
                  <Button
                    size="sm"
                    onClick={() => onViewAuction(selectedLeague.id)}
                    className="bg-blue-600 hover:bg-blue-700"
                  >
                    <Gavel className="w-4 h-4 mr-1" />
                    Join Auction
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* All Leagues Overview */}
      <div>
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold text-theme-text">
            All Leagues ({leagues.length})
          </h2>
          <Button onClick={onCreateLeague}>
            <Plus className="w-4 h-4 mr-2" />
            Create League
          </Button>
        </div>

        {leagues.length === 0 ? (
          <Card className="text-center py-12 bg-theme-surface border-theme-surface-border">
            <CardContent>
              <Trophy className="w-16 h-16 text-theme-text-tertiary mx-auto mb-4" />
              <h3 className="text-lg font-medium text-theme-text mb-2">No Leagues Yet</h3>
              <p className="text-theme-text-secondary mb-4">
                {t('dashboard.createFirstLeague', 'Create your first league to get started')}
              </p>
              <Button onClick={onCreateLeague}>
                <Plus className="w-4 h-4 mr-2" />
                Create League
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {leagues.map((league) => (
              <Card 
                key={league.id} 
                className={`hover:shadow-lg transition-shadow cursor-pointer bg-theme-surface border-theme-surface-border ${
                  selectedLeague?.id === league.id ? 'ring-2 ring-theme-primary bg-blue-25' : ''
                }`}
                onClick={() => handleLeagueChange(league)}
              >
                <CardHeader>
                  <div className="flex justify-between items-start">
                    <div>
                      <CardTitle className="text-lg text-theme-text">{league.name}</CardTitle>
                      <p className="text-sm text-theme-text-secondary flex items-center mt-1">
                        <Calendar className="w-3 h-3 mr-1" />
                        {league.season}
                      </p>
                    </div>
                    <div className="flex flex-col items-end space-y-1">
                      {league.commissioner_id === user.id && (
                        <Badge variant="outline" className="bg-yellow-50 text-yellow-700 border-yellow-200">
                          <Crown className="w-3 h-3 mr-1" />
                          Commissioner
                        </Badge>
                      )}
                      <Badge variant={league.status === 'ready' ? 'default' : 'secondary'}>
                        {league.status}
                      </Badge>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-theme-text-secondary flex items-center">
                        <Users className="w-3 h-3 mr-1" />
                        Members
                      </span>
                      <span className="font-medium text-theme-text">{league.member_count}</span>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-theme-text-secondary flex items-center">
                        <DollarSign className="w-3 h-3 mr-1" />
                        Budget
                      </span>
                      <span className="font-medium text-theme-text">{league.settings?.budget_per_manager || 'N/A'} credits</span>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-theme-text-secondary flex items-center">
                        <Target className="w-3 h-3 mr-1" />
                        Club Slots
                      </span>
                      <span className="font-medium text-theme-text">{league.settings?.club_slots_per_manager || 'N/A'}</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default DashboardContent;