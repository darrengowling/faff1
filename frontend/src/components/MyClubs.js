import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'sonner';
import { useTranslation } from 'react-i18next';

// Import Shadcn components
import { Button } from './ui/button';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { Badge } from './ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Separator } from './ui/separator';
import { Progress } from './ui/progress';
import { EmptyState, NoClubsEmptyState, NoFixturesEmptyState, NoResultsEmptyState, LoadingEmptyState } from './ui/empty-state';
import { ScoringHelp, QuickScoringTip } from './ui/scoring-help';
import { BudgetStatus } from './ui/live-status';

// Hooks
import { useLeagueSettings } from '../hooks/useLeagueSettings';
import { useRosterSummary } from '../hooks/useRosterSummary';
import { TESTIDS } from '../testids';

// Icons
import { 
  ArrowLeft,
  Trophy,
  DollarSign,
  Calendar,
  TrendingUp,
  TrendingDown,
  Clock,
  Target,
  Wallet,
  Star,
  MapPin,
  Activity
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const MyClubs = ({ user, token }) => {
  const { t } = useTranslation();
  const { leagueId } = useParams();
  const navigate = useNavigate();
  
  // Load centralized league settings
  const { settings: leagueSettings, loading: settingsLoading } = useLeagueSettings(leagueId);
  
  // Load roster summary with server-computed remaining slots
  const { summary: rosterSummary, loading: rosterLoading } = useRosterSummary(leagueId);
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [clubsData, setClubsData] = useState(null);
  const [selectedTab, setSelectedTab] = useState('clubs');

  useEffect(() => {
    if (token && leagueId && user) {
      fetchMyClubs();
    }
  }, [token, leagueId, user]);

  const fetchMyClubs = async () => {
    try {
      setError(null);
      const response = await axios.get(`${API}/clubs/my-clubs/${leagueId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setClubsData(response.data);
    } catch (error) {
      console.error('Failed to fetch clubs:', error);
      setError('Failed to load your clubs');
      toast.error('Failed to load your clubs');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getResultColor = (points) => {
    if (points >= 4) return 'text-green-600 bg-green-50';
    if (points >= 2) return 'text-blue-600 bg-blue-50';
    if (points >= 1) return 'text-orange-600 bg-orange-50';
    return 'text-red-600 bg-red-50';
  };

  const getClubGradient = (country) => {
    const gradients = {
      'Spain': 'from-red-500 to-yellow-500',
      'England': 'from-blue-500 to-red-500',
      'Germany': 'from-black to-red-500',
      'Italy': 'from-green-500 to-white',
      'France': 'from-blue-500 to-white',
      'Netherlands': 'from-orange-500 to-blue-500'
    };
    return gradients[country] || 'from-blue-500 to-purple-500';
  };

  if (loading || settingsLoading || rosterLoading) {
    return (
      <div className="max-w-7xl mx-auto p-6">
        <LoadingEmptyState message={t('myClubs.loadingClubs')} />
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-7xl mx-auto p-6">
        <EmptyState
          icon={() => (
            <div className="w-16 h-16 mx-auto mb-4 bg-red-100 rounded-full flex items-center justify-center">
              <svg 
                className="w-8 h-8 text-red-500" 
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24"
                role="img"
                aria-label="Error warning icon"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
            </div>
          )}
          title={t('errors.failedToLoad')}
          description={error}
          action={fetchMyClubs}
          actionLabel={t('errors.tryAgain')}
        />
      </div>
    );
  }

  if (!clubsData) {
    return (
      <div className="max-w-7xl mx-auto p-6">
        <EmptyState
          icon={() => (
            <div className="w-16 h-16 mx-auto mb-4 bg-gray-100 rounded-full flex items-center justify-center">
              <svg 
                className="w-8 h-8 text-gray-400" 
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24"
                role="img"
                aria-label="Data loading icon"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2M4 13h2m13-8a2 2 0 00-2-2H7a2 2 0 00-2 2v9a2 2 0 002 2h8a2 2 0 002-2V5z" />
              </svg>
            </div>
          )}
          title={t('errors.noData')}
          description={t('errors.failedToLoadDescription', { item: 'club information' })}
          action={fetchMyClubs}
          actionLabel={t('common.refresh')}
        />
      </div>
    );
  }

  const { owned_clubs, upcoming_fixtures, recent_results, budget_info } = clubsData;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-4">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => navigate('/dashboard')}
                className="text-gray-600 hover:text-gray-900"
              >
                <ArrowLeft className="w-4 h-4 mr-2" />
                {t('common.back')}
              </Button>
              <div className="flex items-center space-x-2">
                <Trophy className="w-6 h-6 text-blue-600" />
                <h1 className="text-xl font-bold text-gray-900">{t('myClubs.title')}</h1>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <Badge variant="outline" className="text-blue-700 border-blue-200">
                {rosterSummary ? 
                  t('myClubs.clubsCount', { current: rosterSummary.ownedCount, total: rosterSummary.clubSlots }) :
                  t('myClubs.clubsCount', { current: owned_clubs.length, total: '—' })
                }
              </Badge>
              <ScoringHelp />
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
        {/* Enhanced Budget Overview with Live Status */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span>{t('myClubs.budgetRemaining')}</span>
              <ScoringHelp />
            </CardTitle>
          </CardHeader>
          <CardContent>
            <BudgetStatus
              budgetUsed={budget_info.total_spent}
              budgetTotal={leagueSettings ? leagueSettings.budgetPerManager : budget_info.budget_start}
              clubsOwned={rosterSummary ? rosterSummary.ownedCount : budget_info.clubs_owned}
              clubsMax={rosterSummary ? rosterSummary.clubSlots : (leagueSettings ? leagueSettings.clubSlots : budget_info.clubs_owned + budget_info.slots_available)}
              isLoading={rosterLoading}
            />
            
            {/* Additional stats grid */}
            <div className="grid grid-cols-2 gap-4 mt-6">
              <div className="text-center p-4 bg-green-50 rounded-lg" data-testid={TESTIDS.budgetDisplay}>
                <Wallet className="w-6 h-6 text-green-600 mx-auto mb-2" aria-hidden="true" />
                <div className="text-2xl font-bold text-green-600" data-testid={TESTIDS.budgetRemaining}>
                  {budget_info.budget_remaining}
                </div>
                <div className="text-sm text-gray-600">{t('tooltips.remaining')}</div>
              </div>
              <div className="text-center p-4 bg-orange-50 rounded-lg" data-testid={TESTIDS.slotsDisplay}>
                <Star className="w-6 h-6 text-orange-600 mx-auto mb-2" aria-hidden="true" />
                <div className="text-2xl font-bold text-orange-600" data-testid={TESTIDS.slotsRemaining}>
                  {rosterSummary ? rosterSummary.remaining : '—'}
                </div>
                <div className="text-sm text-gray-600">{t('myClubs.slotsAvailable')}</div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Main Content Tabs */}
        <Tabs value={selectedTab} onValueChange={setSelectedTab}>
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="clubs">{t('myClubs.yourClubs')}</TabsTrigger>
            <TabsTrigger value="fixtures">{t('myClubs.upcomingFixtures')}</TabsTrigger>
            <TabsTrigger value="results">{t('myClubs.recentResults')}</TabsTrigger>
          </TabsList>

          {/* My Clubs Tab */}
          <TabsContent value="clubs" className="space-y-4">
            {owned_clubs.length === 0 ? (
              <div data-testid={TESTIDS.rosterEmpty}>
                <NoClubsEmptyState 
                  onNavigateToAuction={() => navigate(`/auction/${leagueId}`)}
                />
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6" data-testid={TESTIDS.rosterList}>
                {owned_clubs.map((club) => (
                  <Card key={club.club_id} className="hover:shadow-lg transition-shadow" data-testid={TESTIDS.rosterItem}>
                    <CardHeader className="pb-4">
                      <div className="flex items-center justify-between">
                        <div className={`w-16 h-16 rounded-full bg-gradient-to-br ${getClubGradient(club.club_country)} flex items-center justify-center`}>
                          <span className="text-white font-bold text-lg">
                            {club.club_short_name}
                          </span>
                        </div>
                        <Badge variant="outline" className="ml-2">
                          <MapPin className="w-3 h-3 mr-1" />
                          {club.club_country}
                        </Badge>
                      </div>
                      <div>
                        <CardTitle className="text-lg" data-testid={TESTIDS.rosterItemName}>{club.club_name}</CardTitle>
                        <p className="text-sm text-gray-600">
                          Acquired {formatDate(club.acquired_at)}
                        </p>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3">
                        <div className="flex justify-between items-center">
                          <span className="text-gray-600">Purchase Price</span>
                          <span className="font-bold text-green-600" data-testid={TESTIDS.rosterItemPrice}>
                            {club.price_paid} credits
                          </span>
                        </div>
                        <Separator />
                        <div className="text-center">
                          <Button 
                            variant="outline" 
                            size="sm"
                            className="w-full"
                            onClick={() => {
                              // Navigate to club details or fixtures
                              setSelectedTab('fixtures');
                            }}
                          >
                            <Calendar className="w-4 h-4 mr-2" />
                            View Fixtures
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </TabsContent>

          {/* Upcoming Fixtures Tab */}
          <TabsContent value="fixtures" className="space-y-4">
            {upcoming_fixtures.length === 0 ? (
              <NoFixturesEmptyState />
            ) : (
              <div className="space-y-4">
                {upcoming_fixtures.map((fixture) => (
                  <Card key={fixture.match_id} className="hover:shadow-md transition-shadow">
                    <CardContent className="p-6">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-4">
                          <div className="text-center">
                            <div className="flex items-center space-x-3">
                              {/* Home Team */}
                              <div className="text-center">
                                <div className={`w-12 h-12 rounded-full bg-gradient-to-br ${getClubGradient(fixture.home_club?.country)} flex items-center justify-center mb-2`}>
                                  <span className="text-white font-bold text-sm">
                                    {fixture.home_club?.short_name}
                                  </span>
                                </div>
                                <p className="text-sm font-medium">{fixture.home_club?.name}</p>
                                {fixture.is_home && (
                                  <Badge variant="default" className="mt-1 text-xs">
                                    Your Club
                                  </Badge>
                                )}
                              </div>

                              <div className="text-gray-500 text-xl font-bold">VS</div>

                              {/* Away Team */}
                              <div className="text-center">
                                <div className={`w-12 h-12 rounded-full bg-gradient-to-br ${getClubGradient(fixture.away_club?.country)} flex items-center justify-center mb-2`}>
                                  <span className="text-white font-bold text-sm">
                                    {fixture.away_club?.short_name}
                                  </span>
                                </div>
                                <p className="text-sm font-medium">{fixture.away_club?.name}</p>
                                {fixture.is_away && (
                                  <Badge variant="default" className="mt-1 text-xs">
                                    Your Club
                                  </Badge>
                                )}
                              </div>
                            </div>
                          </div>
                        </div>

                        <div className="text-right">
                          <div className="flex items-center text-gray-600 mb-2">
                            <Clock className="w-4 h-4 mr-2" />
                            <span className="text-sm">{formatDate(fixture.date)}</span>
                          </div>
                          <Badge 
                            variant={fixture.status === 'scheduled' ? 'secondary' : 'default'}
                          >
                            {fixture.status.toUpperCase()}
                          </Badge>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </TabsContent>

          {/* Recent Results Tab */}
          <TabsContent value="results" className="space-y-4">
            {recent_results.length === 0 ? (
              <NoResultsEmptyState />
            ) : (
              <div className="space-y-4">
                {recent_results.map((result) => (
                  <Card key={result.match_id} className="hover:shadow-md transition-shadow">
                    <CardContent className="p-6">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-4">
                          <div className="text-center">
                            <div className="flex items-center space-x-3">
                              {/* Home Team */}
                              <div className="text-center">
                                <div className={`w-12 h-12 rounded-full bg-gradient-to-br ${getClubGradient(result.home_club?.country)} flex items-center justify-center mb-2`}>
                                  <span className="text-white font-bold text-sm">
                                    {result.home_club?.short_name}
                                  </span>
                                </div>
                                <p className="text-sm font-medium">{result.home_club?.name}</p>
                              </div>

                              {/* Score */}
                              <div className="text-center px-4">
                                <div className="text-2xl font-bold text-gray-900">
                                  {result.home_goals} - {result.away_goals}
                                </div>
                                <p className="text-xs text-gray-500">FINAL</p>
                              </div>

                              {/* Away Team */}
                              <div className="text-center">
                                <div className={`w-12 h-12 rounded-full bg-gradient-to-br ${getClubGradient(result.away_club?.country)} flex items-center justify-center mb-2`}>
                                  <span className="text-white font-bold text-sm">
                                    {result.away_club?.short_name}
                                  </span>
                                </div>
                                <p className="text-sm font-medium">{result.away_club?.name}</p>
                              </div>
                            </div>
                          </div>
                        </div>

                        <div className="text-right">
                          <div className="flex items-center justify-end mb-2">
                            <Badge className={`${getResultColor(result.points_delta)} border-0`}>
                              {result.points_delta > 0 ? (
                                <TrendingUp className="w-3 h-3 mr-1" />
                              ) : (
                                <TrendingDown className="w-3 h-3 mr-1" />
                              )}
                              <QuickScoringTip>
                                <span className="cursor-help">
                                  +{result.points_delta} pts
                                </span>
                              </QuickScoringTip>
                            </Badge>
                          </div>
                          <p className="text-sm text-gray-600">
                            Matchday {result.bucket.value}
                          </p>
                          <p className="text-xs text-gray-500">
                            {formatDate(result.match_date)}
                          </p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default MyClubs;