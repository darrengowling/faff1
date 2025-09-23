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
import { ScrollArea } from './ui/scroll-area';

// Icons
import { 
  ArrowLeft,
  Calendar,
  Clock,
  Trophy,
  Users,
  MapPin,
  Star,
  CheckCircle,
  XCircle,
  Minus
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Fixtures = ({ user, token }) => {
  const { leagueId } = useParams();
  const navigate = useNavigate();
  
  const [loading, setLoading] = useState(true);
  const [fixturesData, setFixturesData] = useState(null);
  const [selectedStage, setSelectedStage] = useState('group_stage');

  useEffect(() => {
    if (token && leagueId) {
      fetchFixtures();
    }
  }, [token, leagueId]);

  const fetchFixtures = async () => {
    try {
      const response = await axios.get(`${API}/fixtures/${leagueId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setFixturesData(response.data);
    } catch (error) {
      console.error('Failed to fetch fixtures:', error);
      toast.error('Failed to load fixtures');
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

  const getMatchResult = (homeGoals, awayGoals) => {
    if (homeGoals > awayGoals) return 'home';
    if (awayGoals > homeGoals) return 'away';
    return 'draw';
  };

  const getResultIcon = (result) => {
    switch (result) {
      case 'home':
      case 'away':
        return <CheckCircle className="w-4 h-4 text-green-600" />;
      case 'draw':
        return <Minus className="w-4 h-4 text-yellow-600" />;
      default:
        return <Clock className="w-4 h-4 text-gray-400" />;
    }
  };

  const renderOwnershipBadges = (owners) => {
    if (!owners || owners.length === 0) {
      return <span className="text-xs text-gray-400">No owner</span>;
    }

    return (
      <div className="flex flex-wrap gap-1">
        {owners.map((owner, index) => (
          <Badge
            key={owner.user_id}
            variant={owner.user_id === user?.id ? 'default' : 'secondary'}
            className="text-xs"
          >
            <Users className="w-3 h-3 mr-1" />
            {owner.display_name}
            {owner.user_id === user?.id && <Star className="w-3 h-3 ml-1" />}
          </Badge>
        ))}
      </div>
    );
  };

  const renderFixture = (fixture) => {
    const hasResult = fixture.home_goals !== undefined && fixture.away_goals !== undefined;
    const result = hasResult ? getMatchResult(fixture.home_goals, fixture.away_goals) : null;
    
    return (
      <Card key={fixture.match_id} className="hover:shadow-md transition-shadow">
        <CardContent className="p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-2">
              <Calendar className="w-4 h-4 text-gray-500" />
              <span className="text-sm text-gray-600">{formatDate(fixture.date)}</span>
            </div>
            <div className="flex items-center space-x-2">
              {getResultIcon(result)}
              <Badge variant={hasResult ? 'default' : 'secondary'}>
                {hasResult ? 'FINAL' : fixture.status.toUpperCase()}
              </Badge>
            </div>
          </div>

          <div className="flex items-center justify-center space-x-6">
            {/* Home Team */}
            <div className="flex-1 text-center">
              <div className={`w-16 h-16 rounded-full bg-gradient-to-br ${getClubGradient(fixture.home_club?.country)} flex items-center justify-center mx-auto mb-3`}>
                <span className="text-white font-bold text-lg">
                  {fixture.home_club?.short_name}
                </span>
              </div>
              <h3 className="font-semibold text-gray-900 mb-1">
                {fixture.home_club?.name}
              </h3>
              <div className="flex items-center justify-center mb-2">
                <MapPin className="w-3 h-3 text-gray-400 mr-1" />
                <span className="text-xs text-gray-500">{fixture.home_club?.country}</span>
              </div>
              {renderOwnershipBadges(fixture.home_owners)}
            </div>

            {/* Score or VS */}
            <div className="text-center px-4">
              {hasResult ? (
                <div className="text-3xl font-bold text-gray-900">
                  {fixture.home_goals} - {fixture.away_goals}
                </div>
              ) : (
                <div className="text-2xl font-bold text-gray-400">VS</div>
              )}
            </div>

            {/* Away Team */}
            <div className="flex-1 text-center">
              <div className={`w-16 h-16 rounded-full bg-gradient-to-br ${getClubGradient(fixture.away_club?.country)} flex items-center justify-center mx-auto mb-3`}>
                <span className="text-white font-bold text-lg">
                  {fixture.away_club?.short_name}
                </span>
              </div>
              <h3 className="font-semibold text-gray-900 mb-1">
                {fixture.away_club?.name}
              </h3>
              <div className="flex items-center justify-center mb-2">
                <MapPin className="w-3 h-3 text-gray-400 mr-1" />
                <span className="text-xs text-gray-500">{fixture.away_club?.country}</span>
              </div>
              {renderOwnershipBadges(fixture.away_owners)}
            </div>
          </div>
        </CardContent>
      </Card>
    );
  };

  const getStageTitle = (stage) => {
    const titles = {
      'group_stage': 'Group Stage',
      'round_of_16': 'Round of 16',
      'quarter_finals': 'Quarter Finals',
      'semi_finals': 'Semi Finals',
      'final': 'Final'
    };
    return titles[stage] || stage;
  };

  const getStageDescription = (stage) => {
    const descriptions = {
      'group_stage': 'Clubs compete in groups for qualification to knockout rounds',
      'round_of_16': 'First knockout round - Winner takes all',
      'quarter_finals': 'Quarter-final stage - 8 teams remain',
      'semi_finals': 'Semi-final stage - 4 teams battle for the final',
      'final': 'The ultimate match - Champions League Final'
    };
    return descriptions[stage] || '';
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full"></div>
      </div>
    );
  }

  if (!fixturesData) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Card className="w-full max-w-md">
          <CardContent className="text-center p-8">
            <Calendar className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No Fixtures Available</h3>
            <p className="text-gray-600">Unable to load fixtures for this league.</p>
            <Button className="mt-4" onClick={() => navigate('/dashboard')}>
              Back to Dashboard
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  const { grouped_fixtures, season } = fixturesData;

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
                <h1 className="text-xl font-bold text-gray-900">UCL Fixtures & Results</h1>
              </div>
            </div>
            <Badge variant="outline" className="text-blue-700 border-blue-200">
              Season {season}
            </Badge>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
        {/* Competition Stages */}
        <Tabs value={selectedStage} onValueChange={setSelectedStage}>
          <TabsList className="grid w-full grid-cols-5">
            <TabsTrigger value="group_stage">Group Stage</TabsTrigger>
            <TabsTrigger value="round_of_16">Round of 16</TabsTrigger>
            <TabsTrigger value="quarter_finals">Quarter Finals</TabsTrigger>
            <TabsTrigger value="semi_finals">Semi Finals</TabsTrigger>
            <TabsTrigger value="final">Final</TabsTrigger>
          </TabsList>

          {Object.keys(grouped_fixtures).map((stage) => (
            <TabsContent key={stage} value={stage} className="space-y-6">
              {/* Stage Header */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <Trophy className="w-5 h-5 mr-2" />
                    {getStageTitle(stage)}
                  </CardTitle>
                  <p className="text-gray-600">{getStageDescription(stage)}</p>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center justify-between text-sm text-gray-600">
                    <span>Total Matches: {grouped_fixtures[stage]?.length || 0}</span>
                    <span>
                      Completed: {grouped_fixtures[stage]?.filter(f => f.home_goals !== undefined).length || 0}
                    </span>
                  </div>
                </CardContent>
              </Card>

              {/* Fixtures */}
              {grouped_fixtures[stage]?.length > 0 ? (
                <div className="space-y-4">
                  {grouped_fixtures[stage].map(renderFixture)}
                </div>
              ) : (
                <Card>
                  <CardContent className="text-center py-12">
                    <Calendar className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-gray-900 mb-2">
                      No {getStageTitle(stage)} Fixtures
                    </h3>
                    <p className="text-gray-600">
                      No fixtures scheduled for this stage yet.
                    </p>
                  </CardContent>
                </Card>
              )}
            </TabsContent>
          ))}
        </Tabs>

        {/* Ownership Legend */}
        <Card className="mt-8">
          <CardHeader>
            <CardTitle className="flex items-center">
              <Users className="w-5 h-5 mr-2" />
              Ownership Legend
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="flex items-center space-x-2">
                <Badge variant="default" className="text-xs">
                  <Users className="w-3 h-3 mr-1" />
                  Manager Name
                  <Star className="w-3 h-3 ml-1" />
                </Badge>
                <span className="text-sm text-gray-600">Your club</span>
              </div>
              <div className="flex items-center space-x-2">
                <Badge variant="secondary" className="text-xs">
                  <Users className="w-3 h-3 mr-1" />
                  Manager Name
                </Badge>
                <span className="text-sm text-gray-600">Other manager's club</span>
              </div>
              <div className="flex items-center space-x-2">
                <span className="text-xs text-gray-400">No owner</span>
                <span className="text-sm text-gray-600">Unowned club</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Fixtures;