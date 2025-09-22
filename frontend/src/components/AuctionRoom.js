import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { io } from 'socket.io-client';
import { toast } from 'sonner';

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
  const { auctionId } = useParams();
  const navigate = useNavigate();
  
  // WebSocket connection
  const [socket, setSocket] = useState(null);
  const [connected, setConnected] = useState(false);
  
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
      
      // Calculate time remaining
      if (data.lot.timer_ends_at) {
        const endTime = new Date(data.lot.timer_ends_at);
        const now = new Date();
        const remaining = Math.max(0, Math.floor((endTime - now) / 1000));
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

  // Timer countdown
  useEffect(() => {
    if (timeRemaining > 0 && currentLot?.status === 'open') {
      const timer = setInterval(() => {
        setTimeRemaining(prev => Math.max(0, prev - 1));
      }, 1000);

      return () => clearInterval(timer);
    }
  }, [timeRemaining, currentLot?.status]);

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

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
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
                <h1 className="text-xl font-bold">UCL Auction</h1>
              </div>
              <Badge variant={connected ? 'default' : 'destructive'}>
                {connected ? 'LIVE' : 'DISCONNECTED'}
              </Badge>
            </div>
            <div className="flex items-center space-x-4">
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

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
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
                  {/* Club Details */}
                  <div className="flex items-center justify-center">
                    <div className="w-32 h-32 bg-gradient-to-br from-blue-600 to-purple-600 rounded-full flex items-center justify-center">
                      <span className="text-3xl font-bold text-white">
                        {currentLot.club.short_name}
                      </span>
                    </div>
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

                  {/* Timer Bar */}
                  {currentLot.status === 'open' && timeRemaining > 0 && (
                    <div className="space-y-2">
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
                      <div className="flex items-center space-x-2">
                        <Input
                          type="number"
                          value={bidAmount}
                          onChange={(e) => setBidAmount(parseInt(e.target.value) || 0)}
                          min={(currentLot.current_bid || 0) + (auctionState?.settings?.min_increment || 1)}
                          max={userBudget}
                          className="bg-gray-700 border-gray-600 text-white"
                          placeholder="Enter bid amount"
                        />
                        <Button
                          onClick={handlePlaceBid}
                          disabled={bidding || bidAmount <= currentLot.current_bid || bidAmount > userBudget}
                          className="bg-green-600 hover:bg-green-700"
                        >
                          {bidding ? 'Bidding...' : 'Place Bid'}
                        </Button>
                      </div>

                      {/* Quick Bid Buttons */}
                      <div className="flex space-x-2">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleQuickBid(1)}
                          className="border-gray-600 text-gray-300"
                        >
                          +1
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleQuickBid(5)}
                          className="border-gray-600 text-gray-300"
                        >
                          +5
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleQuickBid(10)}
                          className="border-gray-600 text-gray-300"
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
                <CardTitle className="text-white flex items-center">
                  <Wallet className="w-5 h-5 mr-2" />
                  Your Wallet
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
    </div>
  );
};

export default AuctionRoom;