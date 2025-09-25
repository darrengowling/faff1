import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { io } from 'socket.io-client';
import { toast } from 'sonner';
import axios from 'axios';
import { useTranslation } from 'react-i18next';
import { getBrandName } from '../brand';

// Import UX components
import { EmptyState, AuctionNotStartedEmptyState, LoadingEmptyState } from './ui/empty-state';
import { BiddingControls } from './ui/bidding-controls';
import { AuctionToasts, handleAuctionUpdate } from './ui/auction-toasts';
import { AuctionTooltip, ScoringTooltip } from './ui/tooltip';
import { AuctionMechanicsHelp, BiddingTips, BudgetConstraintHelp } from './ui/auction-help';
import { ConnectionStatusIndicator, PresenceIndicator } from './ui/connection-status';
import { RulesBadge, CompactRules } from './ui/rules-badge';
import { 
  LotCloseConfirmation, 
  UndoCountdown, 
  LotStatusIndicator, 
  CommissionerLotControls 
} from './ui/lot-closing';

// Hooks
import { useLeagueSettings } from '../hooks/useLeagueSettings';

// Import Shadcn components
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { Badge } from './ui/badge';
import { Progress } from './ui/progress';
import { Separator } from './ui/separator';
import { ScrollArea } from './ui/scroll-area';

// Icons
import { 
  Timer, 
  DollarSign, 
  Users, 
  Crown, 
  Gavel, 
  Send,
  Pause,
  Play,
  Trophy,
  Target,
  Wallet,
  MessageCircle,
  ArrowLeft
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const AuctionRoom = ({ user, token }) => {
  const { t } = useTranslation();
  const { auctionId } = useParams();
  const navigate = useNavigate();
  
  // WebSocket connection with reconnect logic
  const [socket, setSocket] = useState(null);
  const [connected, setConnected] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState('connecting'); // 'connecting', 'connected', 'reconnecting', 'offline'
  const [reconnectAttempts, setReconnectAttempts] = useState(0);
  const [maxReconnectAttempts] = useState(10);
  
  // Server time synchronization state
  const [serverTimeOffset, setServerTimeOffset] = useState(0);
  const [lastServerTime, setLastServerTime] = useState(null);
  
  // Presence tracking
  const [presentUsers, setPresentUsers] = useState([]);
  const [userPresence, setUserPresence] = useState({});
  
  // League settings for rules display  
  const { settings: leagueSettings, loading: settingsLoading } = useLeagueSettings(auctionState?.league_id);
  
  // Auction state
  const [auctionState, setAuctionState] = useState(null);
  const [currentLot, setCurrentLot] = useState(null);
  const [managers, setManagers] = useState([]);
  const [timeRemaining, setTimeRemaining] = useState(0);
  const [auctionStatus, setAuctionStatus] = useState('waiting');
  
  // Bidding state
  const [bidAmount, setBidAmount] = useState(0);
  const [bidding, setBidding] = useState(false);
  const [userBudget, setUserBudget] = useState(0);
  const [userSlots, setUserSlots] = useState(0);
  
  // Chat state
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const chatScrollRef = useRef(null);
  
  // Lot closing state
  const [showCloseConfirmation, setShowCloseConfirmation] = useState(false);
  const [selectedLotForClose, setSelectedLotForClose] = useState(null);
  const [lotClosingLoading, setLotClosingLoading] = useState(false);
  const [undoActions, setUndoActions] = useState([]);

  // UI state
  const [showChat, setShowChat] = useState(true);
  const [isCommissioner, setIsCommissioner] = useState(false);

  // Initialize WebSocket connection
  useEffect(() => {
    if (!token || !auctionId) return;

    const newSocket = io(BACKEND_URL, {
      auth: { token },
      transports: ['websocket', 'polling']
    });

    newSocket.on('connect', () => {
      console.log('Connected to auction server');
      setConnected(true);
      
      // Join auction room
      newSocket.emit('join_auction', { auction_id: auctionId });
    });

    newSocket.on('disconnect', () => {
      console.log('Disconnected from auction server');
      setConnected(false);
    });

    newSocket.on('auction_state', (state) => {
      console.log('Auction state received:', state);
      setAuctionState(state);
      setManagers(state.managers || []);
      
      // Find user's budget and slots
      const userManager = state.managers?.find(m => m.user_id === user.id);
      if (userManager) {
        setUserBudget(userManager.budget_remaining);
        setUserSlots(userManager.club_slots);
      }
    });

    // Server time synchronization
    newSocket.on('time_sync', (data) => {
      const clientReceiveTime = Date.now();
      const serverTime = new Date(data.server_now).getTime();
      
      // Calculate round-trip time and offset
      const roundTripTime = clientReceiveTime - (lastServerTime || clientReceiveTime);
      const estimatedServerTime = serverTime + (roundTripTime / 2);
      const offset = estimatedServerTime - clientReceiveTime;
      
      // Update offset only if drift is significant (>150ms)
      if (Math.abs(offset - serverTimeOffset) > 150) {
        setServerTimeOffset(offset);
        console.log('Time sync updated - offset:', offset, 'ms');
      }
      
      setLastServerTime(clientReceiveTime);
      
      // Update current lot timer if provided
      if (data.current_lot && data.current_lot.timer_ends_at) {
        const serverNow = clientReceiveTime + serverTimeOffset;
        const timerEndsAt = new Date(data.current_lot.timer_ends_at).getTime();
        const remaining = Math.max(0, Math.floor((timerEndsAt - serverNow) / 1000));
        
        // Only update if significant difference to prevent jitter
        if (Math.abs(remaining - timeRemaining) > 1) {
          setTimeRemaining(remaining);
        }
      }
    });

    newSocket.on('lot_update', (data) => {
      console.log('Lot update:', data);
      setCurrentLot(data.lot);
      
      // Update bid amount to minimum next bid
      if (data.lot.current_bid > 0) {
        const minBid = data.lot.current_bid + (auctionState?.settings?.min_increment || 1);
        setBidAmount(minBid);
      } else {
        setBidAmount(auctionState?.settings?.min_increment || 1);
      }
      
      // Calculate time remaining using server-authoritative timing
      if (data.lot.timer_ends_at) {
        const serverNow = Date.now() + serverTimeOffset;
        const timerEndsAt = new Date(data.lot.timer_ends_at).getTime();
        const remaining = Math.max(0, Math.floor((timerEndsAt - serverNow) / 1000));
        setTimeRemaining(remaining);
      }
    });

    newSocket.on('bid_result', (result) => {
      setBidding(false);
      if (result.success) {
        toast.success(`Bid placed: ${result.amount} credits`);
      } else {
        toast.error(`Bid failed: ${result.error}`);
      }
    });

    newSocket.on('chat_message', (message) => {
      setChatMessages(prev => [...prev, message]);
      
      // Auto-scroll chat
      setTimeout(() => {
        if (chatScrollRef.current) {
          chatScrollRef.current.scrollTop = chatScrollRef.current.scrollHeight;
        }
      }, 100);
    });

    newSocket.on('auction_paused', (data) => {
      setAuctionStatus('paused');
      toast.info('Auction paused by commissioner');
    });

    newSocket.on('auction_resumed', (data) => {
      setAuctionStatus('live');
      toast.info('Auction resumed');
    });

    newSocket.on('auction_ended', (data) => {
      setAuctionStatus('completed');
      toast.success('Auction completed!');
    });

    newSocket.on('user_joined', (data) => {
      toast.info(`${data.user.display_name} joined the auction`);
    });

    newSocket.on('user_left', (data) => {
      toast.info(`${data.user.display_name} left the auction`);
    });

    setSocket(newSocket);

    return () => {
      newSocket.close();
    };
  }, [token, auctionId, user.id, auctionState?.settings]);

  // Server-authoritative timer countdown
  useEffect(() => {
    if (timeRemaining > 0 && currentLot?.status === 'open') {
      const timer = setInterval(() => {
        // Use server time for calculations
        const serverNow = Date.now() + serverTimeOffset;
        
        if (currentLot?.timer_ends_at) {
          const timerEndsAt = new Date(currentLot.timer_ends_at).getTime();
          const remaining = Math.max(0, Math.floor((timerEndsAt - serverNow) / 1000));
          setTimeRemaining(remaining);
        } else {
          // Fallback to countdown if no server timer
          setTimeRemaining(prev => Math.max(0, prev - 1));
        }
      }, 1000);

      return () => clearInterval(timer);
    }
  }, [timeRemaining, currentLot?.status, currentLot?.timer_ends_at, serverTimeOffset]);

  // Check if user is commissioner
  useEffect(() => {
    if (auctionState && user) {
      // This would need to be determined from auction/league data
      // For now, simplified check
      setIsCommissioner(false); // Will be set properly with full auction data
    }
  }, [auctionState, user]);

  const handlePlaceBid = async () => {
    if (!socket || !currentLot || bidding) return;
    
    if (bidAmount <= currentLot.current_bid) {
      toast.error('Bid must be higher than current bid');
      return;
    }

    if (bidAmount > userBudget) {
      toast.error('Insufficient budget');
      return;
    }

    setBidding(true);
    
    socket.emit('place_bid', {
      auction_id: auctionId,
      lot_id: currentLot.id,
      amount: bidAmount
    });
  };

  const handleQuickBid = (increment) => {
    const newAmount = (currentLot?.current_bid || 0) + increment;
    setBidAmount(newAmount);
  };

  const handleSendChat = (e) => {
    e.preventDefault();
    if (!socket || !chatInput.trim()) return;

    socket.emit('send_chat_message', {
      auction_id: auctionId,
      message: chatInput.trim()
    });

    setChatInput('');
  };

  const handlePauseResume = async () => {
    if (!isCommissioner) return;

    try {
      const endpoint = auctionStatus === 'live' ? 'pause' : 'resume';
      const response = await fetch(`${BACKEND_URL}/api/auction/${auctionId}/${endpoint}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error('Failed to pause/resume auction');
      }
    } catch (error) {
      toast.error('Failed to pause/resume auction');
    }
  };

  // Lot closing functions
  const handleCloseLot = async (lot) => {
    setSelectedLotForClose(lot);
    setShowCloseConfirmation(true);
  };

  const handleConfirmClose = async (reason, forced) => {
    if (!selectedLotForClose) return;

    setLotClosingLoading(true);
    try {
      const response = await axios.post(
        `${process.env.REACT_APP_BACKEND_URL}/lots/${selectedLotForClose._id}/close`,
        { reason, forced },
        { headers: { Authorization: `Bearer ${token}` }}
      );

      if (response.data.success) {
        toast.success(response.data.message);
        setShowCloseConfirmation(false);
        
        // Add to undo actions
        setUndoActions(prev => [...prev, {
          action_id: response.data.action_id,
          undo_deadline: response.data.undo_deadline,
          lot_id: selectedLotForClose._id
        }]);
      }
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Failed to close lot';
      toast.error(errorMessage);
    } finally {
      setLotClosingLoading(false);
    }
  };

  const handleUndoLotClose = async (actionId) => {
    try {
      const response = await axios.post(
        `${process.env.REACT_APP_BACKEND_URL}/lots/undo/${actionId}`,
        {},
        { headers: { Authorization: `Bearer ${token}` }}
      );

      if (response.data.success) {
        toast.success(response.data.message);
        
        // Remove from undo actions
        setUndoActions(prev => prev.filter(action => action.action_id !== actionId));
      }
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Failed to undo lot close';
      toast.error(errorMessage);
    }
  };

  const handleUndoExpired = (actionId) => {
    // Remove expired undo action
    setUndoActions(prev => prev.filter(action => action.action_id !== actionId));
  };

  // Get server-synchronized time
  const getServerTime = () => {
    return Date.now() + serverTimeOffset;
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // Connection management functions
  const getReconnectDelay = (attempts) => {
    // Exponential backoff: 1s → 2s → 4s → 8s → 10s (max)
    const delay = Math.min(1000 * Math.pow(2, attempts), 10000);
    return delay + Math.random() * 1000; // Add jitter
  };

  const connectWebSocket = useCallback(async () => {
    if (socket) {
      socket.close();
    }

    try {
      setConnectionStatus('connecting');
      
      // Get Socket.IO configuration from environment (cross-origin pattern)
      const origin = (typeof window !== 'undefined' && window.import?.meta?.env?.VITE_PUBLIC_API_URL) || 
                     process.env.NEXT_PUBLIC_API_URL ||
                     (typeof window !== 'undefined' && window.import?.meta?.env?.VITE_PUBLIC_API_URL) ||
                     process.env.REACT_APP_API_ORIGIN ||
                     'https://pifa-friends.preview.emergentagent.com';
                       
      const path = (typeof window !== 'undefined' && window.import?.meta?.env?.VITE_SOCKET_PATH) ||
                   process.env.NEXT_PUBLIC_SOCKET_PATH ||
                   '/api/socketio';
                   
      const transports = ((typeof window !== 'undefined' && window.import?.meta?.env?.VITE_SOCKET_TRANSPORTS) || 
                         process.env.NEXT_PUBLIC_SOCKET_TRANSPORTS || 
                         'polling,websocket').split(',');
      
      console.log(`Socket.IO connecting to: ${origin} with path: ${path}, transports: ${transports}`);
      
      const newSocket = io(origin, {
        auth: { token },
        path,
        transports,
        withCredentials: true,
        timeout: 10000,
        forceNew: true
      });

      // Connection status events
      newSocket.on('connect', () => {
        console.log('WebSocket connected');
        setConnected(true);
        setConnectionStatus('connected');
        setReconnectAttempts(0);
        
        // Join auction room
        newSocket.emit('join_auction', { auction_id: auctionId });
      });

      newSocket.on('disconnect', (reason) => {
        console.log('WebSocket disconnected:', reason);
        setConnected(false);
        
        if (reason === 'io server disconnect') {
          // Server initiated disconnect, don't reconnect
          setConnectionStatus('offline');
        } else {
          // Client-side disconnect, attempt reconnect
          setConnectionStatus('reconnecting');
          attemptReconnect();
        }
      });

      newSocket.on('connect_error', (error) => {
        console.log('WebSocket connection error:', error);
        setConnected(false);
        setConnectionStatus('reconnecting');
        attemptReconnect();
      });

      // Enhanced connection status handler
      newSocket.on('connection_status', (data) => {
        console.log('Connection status:', data);
        if (data.status === 'connected') {
          setConnectionStatus('connected');
        } else if (data.status === 'auth_failed') {
          setConnectionStatus('offline');
          toast.error('Authentication failed. Please refresh and log in again.');
        }
      });

      // Auction state snapshot handler
      newSocket.on('auction_snapshot', (snapshot) => {
        console.log('Received auction snapshot:', snapshot);
        restoreStateFromSnapshot(snapshot);
      });

      // Presence tracking handlers
      newSocket.on('presence_list', (data) => {
        setPresentUsers(data.users || []);
        const presenceMap = {};
        data.users?.forEach(user => {
          presenceMap[user.user_id] = user.status;
        });
        setUserPresence(presenceMap);
      });

      newSocket.on('user_presence', (data) => {
        setUserPresence(prev => ({
          ...prev,
          [data.user_id]: data.status
        }));
        
        if (data.status === 'online') {
          toast.info(`${data.display_name} joined the auction`);
        } else if (data.status === 'offline') {
          toast.info(`${data.display_name} left the auction`);
        }
      });

      // Heartbeat system
      const heartbeatInterval = setInterval(() => {
        if (newSocket.connected) {
          newSocket.emit('heartbeat', { timestamp: Date.now() });
        }
      }, 30000); // Every 30 seconds

      newSocket.on('heartbeat_ack', (data) => {
        // Update server time offset
        const serverTime = new Date(data.server_time).getTime();
        const clientTime = Date.now();
        const offset = serverTime - clientTime;
        
        if (Math.abs(offset - serverTimeOffset) > 150) {
          setServerTimeOffset(offset);
        }
      });

      // Store cleanup function
      newSocket._cleanup = () => {
        clearInterval(heartbeatInterval);
      };

      setSocket(newSocket);
      return newSocket;

    } catch (error) {
      console.error('Failed to create WebSocket:', error);
      setConnectionStatus('offline');
      return null;
    }
  }, [token, auctionId, serverTimeOffset]);

  const attemptReconnect = useCallback(() => {
    if (reconnectAttempts >= maxReconnectAttempts) {
      setConnectionStatus('offline');
      toast.error('Connection lost. Please refresh the page.');
      return;
    }

    const delay = getReconnectDelay(reconnectAttempts);
    console.log(`Reconnecting in ${delay}ms (attempt ${reconnectAttempts + 1}/${maxReconnectAttempts})`);
    
    setTimeout(() => {
      setReconnectAttempts(prev => prev + 1);
      connectWebSocket();
    }, delay);
  }, [reconnectAttempts, maxReconnectAttempts, connectWebSocket]);

  const restoreStateFromSnapshot = (snapshot) => {
    try {
      if (snapshot.error) {
        toast.error(`State sync failed: ${snapshot.error}`);
        return;
      }

      // Restore auction state
      if (snapshot.auction) {
        setAuctionState(snapshot.auction);
        setAuctionStatus(snapshot.auction.status);
      }

      // Restore current lot
      if (snapshot.current_lot) {
        setCurrentLot(snapshot.current_lot);
        
        // Update timer if lot is active
        if (snapshot.current_lot.timer_ends_at) {
          const serverNow = Date.now() + serverTimeOffset;
          const timerEndsAt = new Date(snapshot.current_lot.timer_ends_at).getTime();
          const remaining = Math.max(0, Math.floor((timerEndsAt - serverNow) / 1000));
          setTimeRemaining(remaining);
        }
      }

      // Restore user state
      if (snapshot.user_state) {
        setUserBudget(snapshot.user_state.budget_remaining);
        setUserSlots(snapshot.user_state.max_slots);
      }

      // Restore participants
      if (snapshot.participants) {
        setManagers(snapshot.participants);
      }

      // Restore presence
      if (snapshot.presence) {
        setPresentUsers(snapshot.presence);
      }

      // Update server time offset
      if (snapshot.server_time) {
        const serverTime = new Date(snapshot.server_time).getTime();
        const clientTime = Date.now();
        const offset = serverTime - clientTime;
        setServerTimeOffset(offset);
      }

      console.log('State restored from snapshot');
      toast.success('Connection restored');

    } catch (error) {
      console.error('Failed to restore state from snapshot:', error);
      toast.error('Failed to sync auction state');
    }
  };

  const getLotStatusColor = (status) => {
    switch (status) {
      case 'open': return 'bg-green-500';
      case 'going_once': return 'bg-yellow-500';
      case 'going_twice': return 'bg-orange-500';
      case 'sold': return 'bg-blue-500';
      case 'unsold': return 'bg-gray-500';
      default: return 'bg-gray-300';
    }
  };

  const getLotStatusText = (status) => {
    switch (status) {
      case 'open': return 'BIDDING OPEN';
      case 'going_once': return 'GOING ONCE!';
      case 'going_twice': return 'GOING TWICE!';
      case 'sold': return 'SOLD!';
      case 'unsold': return 'UNSOLD';
      default: return 'WAITING';
    }
  };

  if (!connected) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <Card className="w-full max-w-md">
          <CardContent className="text-center p-8">
            <div className="animate-spin w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full mx-auto mb-4"></div>
            <p className="text-gray-600">Connecting to auction...</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-4">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => navigate('/dashboard')}
                className="text-gray-300 hover:text-white"
              >
                <ArrowLeft className="w-4 h-4 mr-2" />
                Back
              </Button>
              <div className="flex items-center space-x-2">
                <Trophy className="w-6 h-6 text-yellow-500" />
                <h1 className="text-xl font-bold">{t('nav.appName', { brandName: getBrandName() })}</h1>
              </div>
              <Badge variant={connected ? 'default' : 'destructive'}>
                {connected ? 'LIVE' : 'DISCONNECTED'}
              </Badge>
            </div>
            <div className="flex items-center space-x-4">
              {/* Rules Badge */}
              <RulesBadge 
                leagueSettings={leagueSettings}
                loading={settingsLoading}
                className="mr-2"
              />
              
              {/* Connection Status */}
              <ConnectionStatusIndicator 
                status={connectionStatus}
                reconnectAttempts={reconnectAttempts}
                maxAttempts={maxReconnectAttempts}
                className="mr-4"
              />
              
              {/* Help components for learnability */}
              <AuctionMechanicsHelp />
              <BiddingTips />
              
              {isCommissioner && (
                <Button
                  size="sm"
                  onClick={handlePauseResume}
                  variant={auctionStatus === 'live' ? 'destructive' : 'default'}
                >
                  {auctionStatus === 'live' ? (
                    <>
                      <Pause className="w-4 h-4 mr-2" />
                      Pause
                    </>
                  ) : (
                    <>
                      <Play className="w-4 h-4 mr-2" />
                      Resume
                    </>
                  )}
                </Button>
              )}
              <Button
                size="sm"
                variant="outline"
                onClick={() => setShowChat(!showChat)}
              >
                <MessageCircle className="w-4 h-4 mr-2" />
                Chat
              </Button>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 content-with-bottom-nav">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Main Auction Area */}
          <div className="lg:col-span-3 space-y-6">
            {/* Current Lot */}
            {currentLot ? (
              <Card className="bg-gray-800 border-gray-700">
                <CardHeader>
                  <div className="flex justify-between items-center">
                    <div className="flex items-center space-x-3">
                      <div className={`w-4 h-4 rounded-full ${getLotStatusColor(currentLot.status)} animate-pulse`}></div>
                      <CardTitle className="text-2xl text-white">
                        {currentLot.club.name}
                      </CardTitle>
                      <Badge variant="outline" className="text-gray-300">
                        {currentLot.club.country}
                      </Badge>
                    </div>
                    <Badge 
                      className={`text-white font-bold ${getLotStatusColor(currentLot.status)}`}
                    >
                      {getLotStatusText(currentLot.status)}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent className="space-y-6">
                  {/* Current Lot Display */}
                  <div className="text-center mb-6">
                    <div className="w-32 h-32 bg-gradient-to-br from-blue-600 to-purple-600 rounded-full flex items-center justify-center mx-auto mb-4">
                      <span className="text-3xl font-bold text-white">
                        {currentLot.club.short_name}
                      </span>
                    </div>
                    
                    {/* Lot Status and Commissioner Controls */}
                    <div className="flex items-center justify-center space-x-3 mb-4">
                      <h2 className="text-2xl font-bold text-white">{currentLot.club.name}</h2>
                      <LotStatusIndicator status={currentLot.status} />
                    </div>
                    
                    {/* Commissioner Lot Controls */}
                    <CommissionerLotControls
                      lot={currentLot}
                      isCommissioner={isCommissioner}
                      onCloseLot={handleCloseLot}
                      onUndoAction={handleUndoLotClose}
                      undoActions={undoActions.filter(action => action.lot_id === currentLot._id)}
                      loading={lotClosingLoading}
                      className="mb-4"
                    />
                  </div>

                  {/* Bid Information */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="text-center p-4 bg-gray-700 rounded-lg">
                      <div className="text-3xl font-bold text-green-400">
                        {currentLot.current_bid || 0}
                      </div>
                      <div className="text-sm text-gray-400">Current Bid</div>
                    </div>
                    <div className="text-center p-4 bg-gray-700 rounded-lg">
                      <div className="text-3xl font-bold text-blue-400">
                        {currentLot.top_bidder?.display_name || 'No Bids'}
                      </div>
                      <div className="text-sm text-gray-400">Top Bidder</div>
                    </div>
                    <div className="text-center p-4 bg-gray-700 rounded-lg">
                      <div className="text-3xl font-bold text-orange-400">
                        {formatTime(timeRemaining)}
                      </div>
                      <div className="text-sm text-gray-400">Time Left</div>
                    </div>
                  </div>

                  {/* Timer Bar - Sticky on mobile */}
                  {currentLot.status === 'open' && timeRemaining > 0 && (
                    <div className="space-y-2 auction-timer mobile-sticky">
                      <Progress 
                        value={(timeRemaining / (auctionState?.settings?.bid_timer_seconds || 60)) * 100}
                        className="h-3"
                      />
                      <div className="flex justify-between text-sm text-gray-400">
                        <span>Time Remaining</span>
                        <span className={timeRemaining < 10 ? 'text-red-400 font-bold' : ''}>
                          {formatTime(timeRemaining)}
                        </span>
                      </div>
                    </div>
                  )}

                  {/* Bidding Interface */}
                  {currentLot.status === 'open' && (
                    <div className="space-y-4">
                      {/* Main Bidding Controls - Mobile optimized */}
                      <div className="flex items-center space-x-2 thumb-zone">
                        <Input
                          type="number"
                          value={bidAmount}
                          onChange={(e) => setBidAmount(parseInt(e.target.value) || 0)}
                          min={(currentLot.current_bid || 0) + (auctionState?.settings?.min_increment || 1)}
                          max={userBudget}
                          className="bg-gray-700 border-gray-600 text-white text-lg"
                          placeholder="Enter bid amount"
                        />
                        <Button
                          onClick={handlePlaceBid}
                          disabled={bidding || bidAmount <= currentLot.current_bid || bidAmount > userBudget}
                          className="bg-green-600 hover:bg-green-700 touch-target min-w-[120px]"
                          size="lg"
                          data-primary="true"
                        >
                          {bidding ? 'Bidding...' : 'Place Bid'}
                        </Button>
                      </div>

                      {/* Quick Bid Buttons */}
                      {/* Quick Bid Buttons - Mobile optimized */}
                      <div className="flex space-x-2 mobile-button-group">
                        <Button
                          size="lg"
                          variant="outline"
                          onClick={() => handleQuickBid(1)}
                          className="border-gray-600 text-gray-300 touch-target flex-1"
                        >
                          +1
                        </Button>
                        <Button
                          size="lg"
                          variant="outline"
                          onClick={() => handleQuickBid(5)}
                          className="border-gray-600 text-gray-300 touch-target flex-1"
                        >
                          +5
                        </Button>
                        <Button
                          size="lg"
                          variant="outline"
                          onClick={() => handleQuickBid(10)}
                          className="border-gray-600 text-gray-300 touch-target flex-1"
                        >
                          +10
                        </Button>
                      </div>

                      {/* Budget Warning */}
                      {bidAmount > userBudget && (
                        <div className="text-red-400 text-sm">
                          ⚠️ Insufficient budget (You have {userBudget} credits)
                        </div>
                      )}
                    </div>
                  )}
                </CardContent>
              </Card>
            ) : (
              <Card className="bg-gray-800 border-gray-700">
                <CardContent className="text-center py-16">
                  <Timer className="w-16 h-16 text-gray-500 mx-auto mb-4" />
                  <h3 className="text-xl font-medium text-gray-400 mb-2">Auction Loading</h3>
                  <p className="text-gray-500">Waiting for auction to begin...</p>
                </CardContent>
              </Card>
            )}
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* User Wallet */}
            <Card className="bg-gray-800 border-gray-700">
              <CardHeader>
                <CardTitle className="text-white flex items-center justify-between">
                  <div className="flex items-center">
                    <Wallet className="w-5 h-5 mr-2" />
                    Your Wallet
                  </div>
                  <BudgetConstraintHelp 
                    remaining={userBudget} 
                    slotsLeft={userSlots} 
                    minIncrement={auctionState?.settings?.min_increment || 1}
                  />
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-gray-400">Budget:</span>
                  <span className="text-green-400 font-bold">{userBudget} credits</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Slots Used:</span>
                  <span className="text-blue-400 font-bold">0 / {userSlots}</span>
                </div>
                <Separator className="bg-gray-700" />
                <div className="text-sm text-gray-500">
                  Remember: You must be able to fill remaining slots at minimum price!
                </div>
              </CardContent>
            </Card>

            {/* Managers List */}
            <Card className="bg-gray-800 border-gray-700">
              <CardHeader>
                <CardTitle className="text-white flex items-center">
                  <Users className="w-5 h-5 mr-2" />
                  Managers ({managers.length})
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {managers.map((manager) => (
                    <div key={manager.user_id} className="flex items-center justify-between p-2 bg-gray-700 rounded">
                      <div className="flex items-center space-x-2">
                        <PresenceIndicator 
                          status={userPresence[manager.user_id] || 'offline'}
                          showName={false}
                          className="mr-1"
                        />
                        <div className="w-6 h-6 bg-blue-600 rounded-full flex items-center justify-center">
                          <span className="text-xs text-white font-bold">
                            {manager.display_name[0].toUpperCase()}
                          </span>
                        </div>
                        <span className="text-white text-sm">{manager.display_name}</span>
                        {manager.user_id === currentLot?.top_bidder?.id && (
                          <Crown className="w-4 h-4 text-yellow-500" />
                        )}
                      </div>
                      <div className="text-right">
                        <div className="text-green-400 text-sm font-medium">
                          {manager.budget_remaining}
                        </div>
                        <div className="text-gray-500 text-xs">credits</div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Chat */}
            {showChat && (
              <Card className="bg-gray-800 border-gray-700">
                <CardHeader>
                  <CardTitle className="text-white flex items-center">
                    <MessageCircle className="w-5 h-5 mr-2" />
                    Chat
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <ScrollArea 
                    className="h-40 pr-4"
                    ref={chatScrollRef}
                  >
                    <div className="space-y-2">
                      {chatMessages.map((message, index) => (
                        <div key={index} className="text-sm">
                          <span className="text-blue-400 font-medium">
                            {message.user.display_name}:
                          </span>
                          <span className="text-gray-300 ml-2">
                            {message.message}
                          </span>
                        </div>
                      ))}
                      {chatMessages.length === 0 && (
                        <div className="text-gray-500 text-center py-4">
                          No messages yet...
                        </div>
                      )}
                    </div>
                  </ScrollArea>
                  <form onSubmit={handleSendChat} className="flex space-x-2">
                    <Input
                      value={chatInput}
                      onChange={(e) => setChatInput(e.target.value)}
                      placeholder="Type a message..."
                      className="bg-gray-700 border-gray-600 text-white"
                      maxLength={500}
                    />
                    <Button 
                      type="submit" 
                      size="sm"
                      disabled={!chatInput.trim()}
                    >
                      <Send className="w-4 h-4" />
                    </Button>
                  </form>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </div>
      
      {/* Lot Close Confirmation Dialog */}
      <LotCloseConfirmation
        isOpen={showCloseConfirmation}
        onClose={() => {
          setShowCloseConfirmation(false);
          setSelectedLotForClose(null);
        }}
        onConfirm={handleConfirmClose}
        lotDetails={selectedLotForClose ? {
          club_name: selectedLotForClose.club?.name || 'Unknown Club',
          current_bid: selectedLotForClose.current_bid || 0,
          leading_bidder: selectedLotForClose.leading_bidder_name || null,
          timer_active: selectedLotForClose.timer_ends_at ? 
            new Date(selectedLotForClose.timer_ends_at) > new Date() : false
        } : null}
        loading={lotClosingLoading}
      />
    </div>
  );
};

export default AuctionRoom;