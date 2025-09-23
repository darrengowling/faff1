import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'sonner';

// Import Shadcn components
import { Button } from './ui/button';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { Badge } from './ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Separator } from './ui/separator';
import { Progress } from './ui/progress';
import { EmptyState, NoClubsEmptyState, NoFixturesEmptyState, NoResultsEmptyState, LoadingEmptyState } from './ui/empty-state';
import { ScoringTooltip } from './ui/tooltip';

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
  const { leagueId } = useParams();
  const navigate = useNavigate();
  
  const [loading, setLoading] = useState(true);
  const [clubsData, setClubsData] = useState(null);
  const [selectedTab, setSelectedTab] = useState('clubs');

  useEffect(() => {
    if (token && leagueId && user) {
      fetchMyClubs();
    }
  }, [token, leagueId, user]);

  const fetchMyClubs = async () => {
    try {
      const response = await axios.get(`${API}/clubs/my-clubs/${leagueId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setClubsData(response.data);
    } catch (error) {
      console.error('Failed to fetch clubs:', error);
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

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full"></div>
      </div>
    );
  }

  if (!clubsData) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Card className="w-full max-w-md">
          <CardContent className="text-center p-8">
            <Trophy className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">Failed to Load</h3>
            <p className="text-gray-600">Unable to load your clubs data.</p>
            <Button className="mt-4" onClick={() => navigate('/dashboard')}>
              Back to Dashboard
            </Button>
          </CardContent>
        </Card>
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
                Back
              </Button>
              <div className="flex items-center space-x-2">
                <Trophy className="w-6 h-6 text-blue-600" />
                <h1 className="text-xl font-bold text-gray-900">My Clubs</h1>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <Badge variant="outline" className="text-blue-700 border-blue-200">
                {owned_clubs.length} / {budget_info.clubs_owned + budget_info.slots_available} Clubs
              </Badge>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
        {/* Budget Overview */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center">
              <Wallet className="w-5 h-5 mr-2" />
              Budget Overview
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center p-4 bg-green-50 rounded-lg">
                <DollarSign className="w-6 h-6 text-green-600 mx-auto mb-2" />
                <div className="text-2xl font-bold text-green-600">
                  {budget_info.budget_remaining}
                </div>
                <div className="text-sm text-gray-600">Remaining</div>
              </div>
              <div className="text-center p-4 bg-blue-50 rounded-lg">
                <Target className="w-6 h-6 text-blue-600 mx-auto mb-2" />
                <div className="text-2xl font-bold text-blue-600">
                  {budget_info.total_spent}
                </div>
                <div className="text-sm text-gray-600">Spent</div>
              </div>
              <div className="text-center p-4 bg-purple-50 rounded-lg">
                <Trophy className="w-6 h-6 text-purple-600 mx-auto mb-2" />
                <div className="text-2xl font-bold text-purple-600">
                  {budget_info.clubs_owned}
                </div>
                <div className="text-sm text-gray-600">Clubs Owned</div>
              </div>
              <div className="text-center p-4 bg-orange-50 rounded-lg">
                <Star className="w-6 h-6 text-orange-600 mx-auto mb-2" />
                <div className="text-2xl font-bold text-orange-600">
                  {budget_info.slots_available}
                </div>
                <div className="text-sm text-gray-600">Slots Left</div>
              </div>
            </div>
            
            {/* Budget Progress Bar */}
            <div className="mt-4">
              <div className="flex justify-between text-sm text-gray-600 mb-2">
                <span>Budget Usage</span>
                <span>{Math.round((budget_info.total_spent / budget_info.budget_start) * 100)}%</span>
              </div>
              <Progress 
                value={(budget_info.total_spent / budget_info.budget_start) * 100}
                className="h-2"
              />
            </div>
          </CardContent>
        </Card>

        {/* Main Content Tabs */}
        <Tabs value={selectedTab} onValueChange={setSelectedTab}>
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="clubs">My Clubs</TabsTrigger>
            <TabsTrigger value="fixtures">Upcoming Fixtures</TabsTrigger>
            <TabsTrigger value="results">Recent Results</TabsTrigger>
          </TabsList>

          {/* My Clubs Tab */}
          <TabsContent value="clubs" className="space-y-4">
            {owned_clubs.length === 0 ? (
              <Card>
                <CardContent className="text-center py-12">
                  <Trophy className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">No Clubs Owned Yet</h3>
                  <p className="text-gray-600">You haven't purchased any clubs in this league yet.</p>
                </CardContent>
              </Card>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {owned_clubs.map((club) => (
                  <Card key={club.club_id} className="hover:shadow-lg transition-shadow">
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
                        <CardTitle className="text-lg">{club.club_name}</CardTitle>
                        <p className="text-sm text-gray-600">
                          Acquired {formatDate(club.acquired_at)}
                        </p>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3">
                        <div className="flex justify-between items-center">
                          <span className="text-gray-600">Purchase Price</span>
                          <span className="font-bold text-green-600">
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
              <Card>
                <CardContent className="text-center py-12">
                  <Calendar className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">No Upcoming Fixtures</h3>
                  <p className="text-gray-600">Your clubs don't have any upcoming matches scheduled.</p>
                </CardContent>
              </Card>
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
              <Card>
                <CardContent className="text-center py-12">
                  <Activity className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">No Recent Results</h3>
                  <p className="text-gray-600">Your clubs haven't played any matches yet.</p>
                </CardContent>
              </Card>
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
                              +{result.points_delta} pts
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