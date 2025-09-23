import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'sonner';
import { EmptyState, LoadingEmptyState } from './ui/empty-state';
import { ScoringTooltip } from './ui/tooltip';

// Import Shadcn components
import { Button } from './ui/button';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { Badge } from './ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Progress } from './ui/progress';
import { Separator } from './ui/separator';

// Icons
import { 
  ArrowLeft,
  Trophy,
  Medal,
  Crown,
  Target,
  TrendingUp,
  Star,
  Award,
  BarChart3,
  Users,
  Calendar
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Leaderboard = ({ user, token }) => {
  const { leagueId } = useParams();
  const navigate = useNavigate();
  
  const [loading, setLoading] = useState(true);
  const [leaderboardData, setLeaderboardData] = useState(null);
  const [selectedView, setSelectedView] = useState('overall');

  useEffect(() => {
    if (token && leagueId) {
      fetchLeaderboard();
    }
  }, [token, leagueId]);

  const fetchLeaderboard = async () => {
    try {
      const response = await axios.get(`${API}/leaderboard/${leagueId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setLeaderboardData(response.data);
    } catch (error) {
      console.error('Failed to fetch leaderboard:', error);
      toast.error('Failed to load leaderboard');
    } finally {
      setLoading(false);
    }
  };

  const getPositionIcon = (position) => {
    switch (position) {
      case 1:
        return <Crown className="w-5 h-5 text-yellow-500" />;
      case 2:
        return <Medal className="w-5 h-5 text-gray-400" />;
      case 3:
        return <Award className="w-5 h-5 text-amber-600" />;
      default:
        return <span className="w-5 h-5 flex items-center justify-center text-gray-600 font-bold">{position}</span>;
    }
  };

  const getPositionColor = (position) => {
    switch (position) {
      case 1:
        return 'bg-yellow-50 border-yellow-200';
      case 2:
        return 'bg-gray-50 border-gray-200';
      case 3:
        return 'bg-amber-50 border-amber-200';
      default:
        return 'bg-white border-gray-200';
    }
  };

  const calculateAverage = (total, matches) => {
    return matches > 0 ? (total / matches).toFixed(1) : '0.0';
  };

  const renderWeeklyBreakdown = (weeklyData) => {
    if (!weeklyData || Object.keys(weeklyData).length === 0) {
      return (
        <Card>
          <CardContent className="text-center py-8">
            <Calendar className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600">No weekly data available yet</p>
          </CardContent>
        </Card>
      );
    }

    return (
      <div className="space-y-4">
        {Object.entries(weeklyData)
          .sort(([a], [b]) => {
            const aNum = parseInt(a.split('_')[1]);
            const bNum = parseInt(b.split('_')[1]);
            return aNum - bNum;
          })
          .map(([key, data]) => (
            <Card key={key}>
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <span className="flex items-center">
                    <Target className="w-5 h-5 mr-2" />
                    Matchday {data.matchday}
                  </span>
                  <Badge variant="outline">
                    {data.total_matches} matches
                  </Badge>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-gray-600">Total Points Awarded</span>
                    <span className="font-bold text-blue-600">{data.total_points}</span>
                  </div>
                  
                  <Separator />
                  
                  <div>
                    <h4 className="font-medium mb-3">Top Performers</h4>
                    <div className="space-y-2">
                      {data.top_performers.slice(0, 3).map((performer, index) => {
                        const manager = leaderboardData?.leaderboard.find(
                          m => m.user_id === performer.user_id
                        );
                        return (
                          <div key={performer.user_id} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                            <div className="flex items-center space-x-2">
                              {index === 0 && <Star className="w-4 h-4 text-yellow-500" />}
                              <span className="font-medium">
                                {manager?.display_name || 'Unknown Manager'}
                              </span>
                              {performer.user_id === user?.id && (
                                <Badge variant="default" className="text-xs">You</Badge>
                              )}
                            </div>
                            <div className="text-right">
                              <span className="font-bold text-green-600">+{performer.points}</span>
                              <span className="text-xs text-gray-500 ml-2">
                                ({performer.matches} matches)
                              </span>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
          <LoadingEmptyState message="Loading leaderboard..." />
        </div>
      </div>
    );
  }

  if (!leaderboardData) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
          <EmptyState
            icon={() => (
              <div className="w-16 h-16 mx-auto mb-4 bg-red-100 rounded-full flex items-center justify-center">
                <Trophy className="w-8 h-8 text-red-500" />
              </div>
            )}
            title="Failed to Load"
            description="Unable to load leaderboard data. Please try refreshing the page."
            action={() => navigate('/dashboard')}
            actionLabel="Back to Dashboard"
          />
        </div>
      </div>
    );
  }

  const { leaderboard, weekly_breakdown, total_managers } = leaderboardData;
  const currentUserPosition = leaderboard.find(manager => manager.user_id === user?.id);

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
                <Trophy className="w-6 h-6 text-yellow-600" />
                <h1 className="text-xl font-bold text-gray-900">Leaderboard</h1>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <Badge variant="outline" className="text-blue-700 border-blue-200">
                <Users className="w-3 h-3 mr-1" />
                {total_managers} Managers
              </Badge>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
        {/* Your Position Summary */}
        {currentUserPosition && (
          <Card className="mb-6 bg-gradient-to-r from-blue-50 to-indigo-50 border-blue-200">
            <CardHeader>
              <CardTitle className="flex items-center">
                <Star className="w-5 h-5 mr-2 text-blue-600" />
                Your Position
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-600">
                    #{currentUserPosition.position}
                  </div>
                  <div className="text-sm text-gray-600">Position</div>
                </div>
                <div className="text-center">
                  <ScoringTooltip>
                    <div className="text-2xl font-bold text-green-600 cursor-help">
                      {currentUserPosition.total_points}
                    </div>
                  </ScoringTooltip>
                  <div className="text-sm text-gray-600">Total Points</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-purple-600">
                    {currentUserPosition.matches_played}
                  </div>
                  <div className="text-sm text-gray-600">Matches</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-orange-600">
                    {calculateAverage(currentUserPosition.total_points, currentUserPosition.matches_played)}
                  </div>
                  <div className="text-sm text-gray-600">Avg/Match</div>
                </div>
              </div>
              
              {/* Progress to leader */}
              {currentUserPosition.position > 1 && (
                <div className="mt-4">
                  <div className="flex justify-between text-sm text-gray-600 mb-2">
                    <span>Points behind leader</span>
                    <span>{leaderboard[0].total_points - currentUserPosition.total_points} points</span>
                  </div>
                  <Progress 
                    value={(currentUserPosition.total_points / leaderboard[0].total_points) * 100}
                    className="h-2"
                  />
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* Main Content */}
        <Tabs value={selectedView} onValueChange={setSelectedView}>
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="overall">Overall Standings</TabsTrigger>
            <TabsTrigger value="weekly">Weekly Breakdown</TabsTrigger>
          </TabsList>

          {/* Overall Standings */}
          <TabsContent value="overall" className="space-y-4">
            {leaderboard.length === 0 ? (
              <Card>
                <CardContent className="text-center py-12">
                  <BarChart3 className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">No Points Yet</h3>
                  <p className="text-gray-600">No points have been scored in this league yet.</p>
                </CardContent>
              </Card>
            ) : (
              <div className="space-y-3">
                {leaderboard.map((manager) => (
                  <Card 
                    key={manager.user_id} 
                    className={`transition-all hover:shadow-md ${getPositionColor(manager.position)} ${
                      manager.user_id === user?.id ? 'ring-2 ring-blue-400' : ''
                    }`}
                  >
                    <CardContent className="p-6">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-4">
                          <div className="flex items-center justify-center w-12 h-12 rounded-full bg-white border-2 border-gray-200">
                            {getPositionIcon(manager.position)}
                          </div>
                          <div>
                            <div className="flex items-center space-x-2">
                              <h3 className="font-semibold text-gray-900">
                                {manager.display_name}
                              </h3>
                              {manager.user_id === user?.id && (
                                <Badge variant="default" className="text-xs">You</Badge>
                              )}
                            </div>
                            <p className="text-sm text-gray-600">{manager.email}</p>
                          </div>
                        </div>

                        <div className="text-right">
                          <div className="flex items-center space-x-6">
                            {/* Total Points */}
                            <div className="text-center">
                              <ScoringTooltip>
                                <div className="text-2xl font-bold text-green-600 cursor-help">
                                  {manager.total_points}
                                </div>
                              </ScoringTooltip>
                              <div className="text-xs text-gray-500">Total Points</div>
                            </div>

                            {/* Matches Played */}
                            <div className="text-center">
                              <div className="text-lg font-semibold text-blue-600">
                                {manager.matches_played}
                              </div>
                              <div className="text-xs text-gray-500">Matches</div>
                            </div>

                            {/* Average Points */}
                            <div className="text-center">
                              <div className="text-lg font-semibold text-purple-600">
                                {calculateAverage(manager.total_points, manager.matches_played)}
                              </div>
                              <div className="text-xs text-gray-500">Avg/Match</div>
                            </div>

                            {/* Budget Remaining */}
                            <div className="text-center">
                              <div className="text-lg font-semibold text-orange-600">
                                {manager.budget_remaining}
                              </div>
                              <div className="text-xs text-gray-500">Budget Left</div>
                            </div>
                          </div>
                        </div>
                      </div>

                      {/* Progress bar for points relative to leader */}
                      {manager.position > 1 && (
                        <div className="mt-4">
                          <Progress 
                            value={(manager.total_points / leaderboard[0].total_points) * 100}
                            className="h-1"
                          />
                        </div>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </TabsContent>

          {/* Weekly Breakdown */}
          <TabsContent value="weekly" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <TrendingUp className="w-5 h-5 mr-2" />
                  Matchday Performance
                </CardTitle>
                <p className="text-gray-600">
                  Points scored by all managers across different matchdays
                </p>
              </CardHeader>
            </Card>
            
            {renderWeeklyBreakdown(weekly_breakdown)}
          </TabsContent>
        </Tabs>

        {/* League Stats Summary */}
        <Card className="mt-8">
          <CardHeader>
            <CardTitle className="flex items-center">
              <BarChart3 className="w-5 h-5 mr-2" />
              League Statistics
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center p-3 bg-blue-50 rounded-lg">
                <div className="text-xl font-bold text-blue-600">
                  {leaderboard.reduce((sum, m) => sum + m.total_points, 0)}
                </div>
                <div className="text-sm text-gray-600">Total Points</div>
              </div>
              <div className="text-center p-3 bg-green-50 rounded-lg">
                <div className="text-xl font-bold text-green-600">
                  {leaderboard.reduce((sum, m) => sum + m.matches_played, 0)}
                </div>
                <div className="text-sm text-gray-600">Total Matches</div>
              </div>
              <div className="text-center p-3 bg-purple-50 rounded-lg">
                <div className="text-xl font-bold text-purple-600">
                  {leaderboard.length > 0 ? 
                    calculateAverage(
                      leaderboard.reduce((sum, m) => sum + m.total_points, 0),
                      leaderboard.reduce((sum, m) => sum + m.matches_played, 0)
                    ) : '0.0'
                  }
                </div>
                <div className="text-sm text-gray-600">League Avg</div>
              </div>
              <div className="text-center p-3 bg-orange-50 rounded-lg">
                <div className="text-xl font-bold text-orange-600">
                  {Object.keys(weekly_breakdown).length}
                </div>
                <div className="text-sm text-gray-600">Matchdays</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Leaderboard;