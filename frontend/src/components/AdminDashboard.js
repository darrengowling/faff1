import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'sonner';

// Import Shadcn components
import { Button } from './ui/button';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { Badge } from './ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Separator } from './ui/separator';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from './ui/dialog';
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from './ui/alert-dialog';

// Icons
import { 
  ArrowLeft,
  Shield,
  Settings,
  Users,
  Gavel,
  Eye,
  Play,
  Pause,
  RotateCcw,
  UserMinus,
  UserCheck,
  FileText,
  AlertTriangle,
  Clock,
  DollarSign,
  Target,
  Activity,
  Search,
  Filter,
  Download,
  RefreshCw
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const AdminDashboard = ({ user, token }) => {
  const { leagueId } = useParams();
  const navigate = useNavigate();
  
  const [loading, setLoading] = useState(true);
  const [league, setLeague] = useState(null);
  const [members, setMembers] = useState([]);
  const [auction, setAuction] = useState(null);
  const [adminLogs, setAdminLogs] = useState([]);
  const [bidAudit, setBidAudit] = useState([]);
  const [selectedTab, setSelectedTab] = useState('overview');
  
  // Form states
  const [settingsForm, setSettingsForm] = useState({});
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (token && leagueId && user) {
      fetchAdminData();
    }
  }, [token, leagueId, user]);

  const fetchAdminData = async () => {
    try {
      setLoading(true);
      
      // Get league details
      const leagueResponse = await axios.get(`${API}/leagues/${leagueId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setLeague(leagueResponse.data);
      setSettingsForm(leagueResponse.data.settings);
      
      // Get league members
      const membersResponse = await axios.get(`${API}/leagues/${leagueId}/members`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setMembers(membersResponse.data);
      
      // Get admin logs
      const logsResponse = await axios.get(`${API}/admin/leagues/${leagueId}/logs`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setAdminLogs(logsResponse.data.logs || []);
      
      // Get bid audit
      const auditResponse = await axios.get(`${API}/admin/leagues/${leagueId}/bid-audit`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setBidAudit(auditResponse.data.bids || []);
      
    } catch (error) {
      console.error('Failed to fetch admin data:', error);
      if (error.response?.status === 403) {
        toast.error('Commissioner access required');
        navigate('/dashboard');
      } else {
        toast.error('Failed to load admin data');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSettingsUpdate = async () => {
    try {
      setSaving(true);
      
      const response = await axios.put(
        `${API}/admin/leagues/${leagueId}/settings`,
        settingsForm,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      if (response.data.success) {
        toast.success('League settings updated successfully');
        await fetchAdminData(); // Refresh data
      }
    } catch (error) {
      console.error('Failed to update settings:', error);
      toast.error(error.response?.data?.detail || 'Failed to update settings');
    } finally {
      setSaving(false);
    }
  };

  const handleMemberAction = async (memberId, action) => {
    try {
      const response = await axios.post(
        `${API}/admin/leagues/${leagueId}/members/manage`,
        { member_id: memberId, action },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      if (response.data.success) {
        toast.success(`Member ${action} successfully`);
        await fetchAdminData(); // Refresh data
      }
    } catch (error) {
      console.error(`Failed to ${action} member:`, error);
      toast.error(error.response?.data?.detail || `Failed to ${action} member`);
    }
  };

  const handleAuctionAction = async (action, auctionId) => {
    try {
      const response = await axios.post(
        `${API}/admin/auctions/${auctionId}/manage?action=${action}&league_id=${leagueId}`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      if (response.data.success) {
        toast.success(`Auction ${action} successfully`);
        await fetchAdminData(); // Refresh data
      }
    } catch (error) {
      console.error(`Failed to ${action} auction:`, error);
      toast.error(error.response?.data?.detail || `Failed to ${action} auction`);
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getActionIcon = (action) => {
    const iconMap = {
      'update_league_settings': <Settings className="w-4 h-4" />,
      'kick_member': <UserMinus className="w-4 h-4" />,
      'approve_member': <UserCheck className="w-4 h-4" />,
      'start_auction': <Play className="w-4 h-4" />,
      'pause_auction': <Pause className="w-4 h-4" />,
      'resume_auction': <RotateCcw className="w-4 h-4" />,
      'reorder_nominations': <Activity className="w-4 h-4" />
    };
    return iconMap[action] || <Activity className="w-4 h-4" />;
  };

  const getActionColor = (action) => {
    const colorMap = {
      'update_league_settings': 'text-blue-600',
      'kick_member': 'text-red-600',
      'approve_member': 'text-green-600',
      'start_auction': 'text-green-600',
      'pause_auction': 'text-yellow-600',
      'resume_auction': 'text-blue-600',
      'reorder_nominations': 'text-purple-600'
    };
    return colorMap[action] || 'text-gray-600';
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full"></div>
      </div>
    );
  }

  if (!league) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Card className="w-full max-w-md">
          <CardContent className="text-center p-8">
            <Shield className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">Access Denied</h3>
            <p className="text-gray-600">You don't have administrator access to this league.</p>
            <Button className="mt-4" onClick={() => navigate('/dashboard')}>
              Back to Dashboard
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

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
                <Shield className="w-6 h-6 text-red-600" />
                <h1 className="text-xl font-bold text-gray-900">Admin Dashboard</h1>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <Badge variant="outline" className="text-red-700 border-red-200">
                Commissioner Panel
              </Badge>
              <Badge variant="outline" className="text-blue-700 border-blue-200">
                {league.name}
              </Badge>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
        {/* Quick Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <Card>
            <CardContent className="p-4 text-center">
              <Users className="w-8 h-8 text-blue-600 mx-auto mb-2" />
              <div className="text-2xl font-bold text-blue-600">{members.length}</div>
              <div className="text-sm text-gray-600">Members</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <Activity className="w-8 h-8 text-green-600 mx-auto mb-2" />
              <div className="text-2xl font-bold text-green-600">{adminLogs.length}</div>
              <div className="text-sm text-gray-600">Admin Actions</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <Gavel className="w-8 h-8 text-purple-600 mx-auto mb-2" />
              <div className="text-2xl font-bold text-purple-600">{bidAudit.length}</div>
              <div className="text-sm text-gray-600">Total Bids</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <Clock className="w-8 h-8 text-orange-600 mx-auto mb-2" />
              <div className="text-2xl font-bold text-orange-600">
                {league.status?.toUpperCase() || 'SETUP'}
              </div>
              <div className="text-sm text-gray-600">League Status</div>
            </CardContent>
          </Card>
        </div>

        {/* Main Content Tabs */}
        <Tabs value={selectedTab} onValueChange={setSelectedTab}>
          <TabsList className="grid w-full grid-cols-5">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="settings">League Settings</TabsTrigger>
            <TabsTrigger value="members">Member Management</TabsTrigger>
            <TabsTrigger value="auction">Auction Control</TabsTrigger>
            <TabsTrigger value="audit">Audit & Logs</TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* League Summary */}
              <Card>
                <CardHeader>
                  <CardTitle>League Summary</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Season:</span>
                    <span className="font-medium">{league.season}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Status:</span>
                    <Badge variant={league.status === 'ready' ? 'default' : 'secondary'}>
                      {league.status}
                    </Badge>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Members:</span>
                    <span className="font-medium">
                      {league.member_count}/{league.settings.max_managers}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Budget per Manager:</span>
                    <span className="font-medium">{league.settings.budget_per_manager}M</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Club Slots:</span>
                    <span className="font-medium">{league.settings.club_slots_per_manager}</span>
                  </div>
                </CardContent>
              </Card>

              {/* Recent Activity */}
              <Card>
                <CardHeader>
                  <CardTitle>Recent Admin Activity</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {adminLogs.slice(0, 5).map((log) => (
                      <div key={log.id} className="flex items-center space-x-3 p-2 bg-gray-50 rounded">
                        <div className={`${getActionColor(log.action)}`}>
                          {getActionIcon(log.action)}
                        </div>
                        <div className="flex-1">
                          <div className="text-sm font-medium">
                            {log.action.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                          </div>
                          <div className="text-xs text-gray-500">
                            {formatDate(log.created_at)}
                          </div>
                        </div>
                      </div>
                    ))}
                    {adminLogs.length === 0 && (
                      <p className="text-gray-500 text-sm">No admin actions yet</p>
                    )}
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* League Settings Tab */}
          <TabsContent value="settings" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>League Settings</CardTitle>
                <p className="text-gray-600">
                  Modify core league settings. Changes will be logged for audit.
                </p>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Configuration Status Alert */}
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <div className="flex items-start space-x-3">
                    <AlertTriangle className="w-5 h-5 text-blue-600 mt-0.5" />
                    <div>
                      <div className="font-medium text-blue-800">Configuration Constraints</div>
                      <div className="text-sm text-blue-700 mt-1 space-y-1">
                        <div>• Budget can only be changed when auction is scheduled/paused and no purchases exist</div>
                        <div>• Club slots can decrease only if all managers have ≤ new limit</div>
                        <div>• League size maximum must be ≥ current member count</div>
                      </div>
                    </div>
                  </div>
                </div>
                <div className="space-y-6">
                  {/* Core Configuration */}
                  <div>
                    <h4 className="font-medium mb-4 text-blue-900 flex items-center">
                      <DollarSign className="w-4 h-4 mr-2" />
                      Core League Settings
                    </h4>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div>
                        <Label htmlFor="budget">Budget per Manager (50-500M)</Label>
                        <Input
                          id="budget"
                          type="number"
                          min="50"
                          max="500"
                          value={settingsForm.budget_per_manager || ''}
                          onChange={(e) => setSettingsForm({
                            ...settingsForm,
                            budget_per_manager: parseInt(e.target.value)
                          })}
                        />
                        <div className="text-xs text-gray-500 mt-1">
                          Can only change before any club purchases
                        </div>
                      </div>
                      <div>
                        <Label htmlFor="clubSlots">Club Slots per Manager (1-10)</Label>
                        <Input
                          id="clubSlots"
                          type="number"
                          min="1"
                          max="10"
                          value={settingsForm.club_slots_per_manager || ''}
                          onChange={(e) => setSettingsForm({
                            ...settingsForm,
                            club_slots_per_manager: parseInt(e.target.value)
                          })}
                        />
                        <div className="text-xs text-gray-500 mt-1">
                          Can only decrease if all managers have ≤ new limit
                        </div>
                      </div>
                      <div>
                        <Label htmlFor="minIncrement">Minimum Bid Increment</Label>
                        <Input
                          id="minIncrement"
                          type="number"
                          min="1"
                          value={settingsForm.min_increment || ''}
                          onChange={(e) => setSettingsForm({
                            ...settingsForm,
                            min_increment: parseInt(e.target.value)
                          })}
                        />
                      </div>
                    </div>
                  </div>

                  {/* League Size Configuration */}
                  <div>
                    <h4 className="font-medium mb-4 text-green-900 flex items-center">
                      <Users className="w-4 h-4 mr-2" />
                      League Size Settings
                    </h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <Label htmlFor="minManagers">Minimum Managers (2-8)</Label>
                        <Input
                          id="minManagers"
                          type="number"
                          min="2"
                          max="8"
                          value={settingsForm.min_managers || ''}
                          onChange={(e) => setSettingsForm({
                            ...settingsForm,
                            min_managers: parseInt(e.target.value)
                          })}
                        />
                      </div>
                      <div>
                        <Label htmlFor="maxManagers">Maximum Managers (2-8)</Label>
                        <Input
                          id="maxManagers"
                          type="number"
                          min="2"
                          max="8"
                          value={settingsForm.max_managers || ''}
                          onChange={(e) => setSettingsForm({
                            ...settingsForm,
                            max_managers: parseInt(e.target.value)
                          })}
                        />
                        <div className="text-xs text-gray-500 mt-1">
                          Must be ≥ current member count ({league.member_count})
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Auction Timing Configuration */}
                  <div>
                    <h4 className="font-medium mb-4 text-purple-900 flex items-center">
                      <Clock className="w-4 h-4 mr-2" />
                      Auction Timing Settings
                    </h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <Label htmlFor="antiSnipe">Anti-snipe Seconds</Label>
                        <Input
                          id="antiSnipe"
                          type="number"
                          min="0"
                          max="120"
                          value={settingsForm.anti_snipe_seconds || ''}
                          onChange={(e) => setSettingsForm({
                            ...settingsForm,
                            anti_snipe_seconds: parseInt(e.target.value)
                          })}
                        />
                        <div className="text-xs text-gray-500 mt-1">
                          Timer extension when bid placed in final seconds
                        </div>
                      </div>
                      <div>
                        <Label htmlFor="bidTimer">Bid Timer Seconds</Label>
                        <Input
                          id="bidTimer"
                          type="number"
                          min="30"
                          max="300"
                          value={settingsForm.bid_timer_seconds || ''}
                          onChange={(e) => setSettingsForm({
                            ...settingsForm,
                            bid_timer_seconds: parseInt(e.target.value)
                          })}
                        />
                        <div className="text-xs text-gray-500 mt-1">
                          Default timer duration for each lot
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
                
                <Separator />
                
                <div>
                  <h4 className="font-medium mb-3">Scoring Rules</h4>
                  <div className="grid grid-cols-3 gap-4">
                    <div>
                      <Label htmlFor="clubGoal">Points per Goal</Label>
                      <Input
                        id="clubGoal"
                        type="number"
                        value={settingsForm.scoring_rules?.club_goal || ''}
                        onChange={(e) => setSettingsForm({
                          ...settingsForm,
                          scoring_rules: {
                            ...settingsForm.scoring_rules,
                            club_goal: parseInt(e.target.value)
                          }
                        })}
                      />
                    </div>
                    <div>
                      <Label htmlFor="clubWin">Points per Win</Label>
                      <Input
                        id="clubWin"
                        type="number"
                        value={settingsForm.scoring_rules?.club_win || ''}
                        onChange={(e) => setSettingsForm({
                          ...settingsForm,
                          scoring_rules: {
                            ...settingsForm.scoring_rules,
                            club_win: parseInt(e.target.value)
                          }
                        })}
                      />
                    </div>
                    <div>
                      <Label htmlFor="clubDraw">Points per Draw</Label>
                      <Input
                        id="clubDraw"
                        type="number"
                        value={settingsForm.scoring_rules?.club_draw || ''}
                        onChange={(e) => setSettingsForm({
                          ...settingsForm,
                          scoring_rules: {
                            ...settingsForm.scoring_rules,
                            club_draw: parseInt(e.target.value)
                          }
                        })}
                      />
                    </div>
                  </div>
                </div>
                
                <div className="flex justify-end">
                  <Button onClick={handleSettingsUpdate} disabled={saving}>
                    {saving ? (
                      <>
                        <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                        Saving...
                      </>
                    ) : (
                      <>
                        <Settings className="w-4 h-4 mr-2" />
                        Save Settings
                      </>
                    )}
                  </Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Member Management Tab */}
          <TabsContent value="members" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Member Management</CardTitle>
                <p className="text-gray-600">
                  Manage league members. All actions are logged for audit.
                </p>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {members.map((member) => (
                    <div key={member.user_id} className="flex items-center justify-between p-4 border rounded-lg">
                      <div className="flex items-center space-x-4">
                        <div className="w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center">
                          <Users className="w-5 h-5 text-white" />
                        </div>
                        <div>
                          <div className="font-medium">{member.display_name}</div>
                          <div className="text-sm text-gray-600">{member.email}</div>
                        </div>
                        <Badge variant={member.role === 'commissioner' ? 'default' : 'secondary'}>
                          {member.role}
                        </Badge>
                      </div>
                      
                      {member.role !== 'commissioner' && (
                        <div className="flex space-x-2">
                          <AlertDialog>
                            <AlertDialogTrigger asChild>
                              <Button variant="outline" size="sm" className="text-red-600 hover:text-red-700">
                                <UserMinus className="w-4 h-4 mr-1" />
                                Kick
                              </Button>
                            </AlertDialogTrigger>
                            <AlertDialogContent>
                              <AlertDialogHeader>
                                <AlertDialogTitle>Kick Member?</AlertDialogTitle>
                                <AlertDialogDescription>
                                  Are you sure you want to kick {member.display_name}? This action will:
                                  <ul className="list-disc list-inside mt-2">
                                    <li>Remove them from the league</li>
                                    <li>Delete their roster and clubs</li>
                                    <li>Cannot be undone</li>
                                  </ul>
                                </AlertDialogDescription>
                              </AlertDialogHeader>
                              <AlertDialogFooter>
                                <AlertDialogCancel>Cancel</AlertDialogCancel>
                                <AlertDialogAction
                                  onClick={() => handleMemberAction(member.user_id, 'kick')}
                                  className="bg-red-600 hover:bg-red-700"
                                >
                                  Kick Member
                                </AlertDialogAction>
                              </AlertDialogFooter>
                            </AlertDialogContent>
                          </AlertDialog>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Auction Control Tab */}
          <TabsContent value="auction" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Auction Control</CardTitle>
                <p className="text-gray-600">
                  Control auction state and manage nominations.
                </p>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                  <div>
                    <div className="font-medium">Auction Status</div>
                    <div className="text-sm text-gray-600">
                      Current league status: <Badge>{league.status}</Badge>
                    </div>
                  </div>
                  <div className="flex space-x-2">
                    {league.status === 'ready' && (
                      <Button 
                        onClick={() => handleAuctionAction('start', league.id)}
                        className="bg-green-600 hover:bg-green-700"
                      >
                        <Play className="w-4 h-4 mr-2" />
                        Start Auction
                      </Button>
                    )}
                    {league.status === 'active' && (
                      <Button 
                        onClick={() => handleAuctionAction('pause', league.id)}
                        variant="outline"
                      >
                        <Pause className="w-4 h-4 mr-2" />
                        Pause Auction
                      </Button>
                    )}
                    {league.status === 'paused' && (
                      <Button 
                        onClick={() => handleAuctionAction('resume', league.id)}
                        className="bg-blue-600 hover:bg-blue-700"
                      >
                        <RotateCcw className="w-4 h-4 mr-2" />
                        Resume Auction
                      </Button>
                    )}
                  </div>
                </div>
                
                <div className="p-4 border border-yellow-200 bg-yellow-50 rounded-lg">
                  <div className="flex items-start space-x-3">
                    <AlertTriangle className="w-5 h-5 text-yellow-600 mt-0.5" />
                    <div>
                      <div className="font-medium text-yellow-800">Admin Controls Active</div>
                      <div className="text-sm text-yellow-700 mt-1">
                        All auction control actions are logged for audit. Timer extensions follow monotonicity rules.
                        Budget and ownership constraints are enforced automatically.
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Audit & Logs Tab */}
          <TabsContent value="audit" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Admin Logs */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <FileText className="w-5 h-5 mr-2" />
                    Admin Action Log
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3 max-h-96 overflow-y-auto">
                    {adminLogs.map((log) => (
                      <div key={log.id} className="p-3 border rounded-lg">
                        <div className="flex items-start justify-between">
                          <div className="flex items-center space-x-2">
                            <div className={`${getActionColor(log.action)}`}>
                              {getActionIcon(log.action)}
                            </div>
                            <div>
                              <div className="font-medium text-sm">
                                {log.action.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                              </div>
                              <div className="text-xs text-gray-500">
                                {formatDate(log.created_at)}
                              </div>
                            </div>
                          </div>
                        </div>
                        {log.metadata && (
                          <div className="mt-2 text-xs text-gray-600 bg-gray-50 p-2 rounded">
                            <pre>{JSON.stringify(log.metadata, null, 2)}</pre>
                          </div>
                        )}
                      </div>
                    ))}
                    {adminLogs.length === 0 && (
                      <p className="text-gray-500 text-sm">No admin actions logged yet</p>
                    )}
                  </div>
                </CardContent>
              </Card>

              {/* Bid Audit */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <Gavel className="w-5 h-5 mr-2" />
                    Bid Audit Trail
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3 max-h-96 overflow-y-auto">
                    {bidAudit.slice(0, 10).map((bid) => (
                      <div key={bid.bid_id} className="p-3 border rounded-lg">
                        <div className="flex items-center justify-between">
                          <div>
                            <div className="font-medium text-sm">
                              {bid.user_name} → {bid.club_short_name}
                            </div>
                            <div className="text-xs text-gray-500">
                              {formatDate(bid.placed_at)}
                            </div>
                          </div>
                          <div className="text-right">
                            <div className="font-bold text-green-600">
                              {bid.amount}M
                            </div>
                            <Badge variant="outline" className="text-xs">
                              {bid.status}
                            </Badge>
                          </div>
                        </div>
                      </div>
                    ))}
                    {bidAudit.length === 0 && (
                      <p className="text-gray-500 text-sm">No bids recorded yet</p>
                    )}
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default AdminDashboard;