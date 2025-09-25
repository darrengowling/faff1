import React from 'react';
import { useTranslation } from 'react-i18next';
import { Wifi, WifiOff, RefreshCw, AlertCircle } from 'lucide-react';
import { Badge } from './badge';

/**
 * Connection Status Indicator Component
 * Shows real-time WebSocket connection status with appropriate styling
 */
export const ConnectionStatusIndicator = ({
  const { t } = useTranslation(); 
  status, 
  reconnectAttempts = 0, 
  maxAttempts = 10,
  className = "" 
}) => {
  const getStatusConfig = () => {
    switch (status) {
      case 'connected':
        return {
          icon: Wifi,
          text: 'Connected',
          variant: 'default',
          className: 'bg-green-500 text-white'
        };
      case 'connecting':
        return {
          icon: RefreshCw,
          text: 'Connecting...',
          variant: 'secondary',
          className: 'bg-blue-500 text-white animate-pulse'
        };
      case 'reconnecting':
        return {
          icon: RefreshCw,
          text: `Reconnecting... (${reconnectAttempts}/${maxAttempts})`,
          variant: 'secondary', 
          className: 'bg-yellow-500 text-white animate-spin'
        };
      case 'offline':
        return {
          icon: WifiOff,
          text: 'Offline',
          variant: 'destructive',
          className: 'bg-red-500 text-white'
        };
      default:
        return {
          icon: AlertCircle,
          text: 'Unknown',
          variant: 'secondary',
          className: 'bg-gray-500 text-white'
        };
    }
  };

  const config = getStatusConfig();
  const Icon = config.icon;

  return (
    <Badge 
      variant={config.variant}
      className={`flex items-center space-x-1 ${config.className} ${className}`}
    >
      <Icon className="w-3 h-3" />
      <span className="text-xs">{config.text}</span>
    </Badge>
  );
};

/**
 * Presence Indicator for showing user online status
 */
export const PresenceIndicator = ({ 
  status, 
  displayName, 
  showName = true,
  className = "" 
}) => {
  const getPresenceColor = () => {
    switch (status) {
      case 'online':
        return 'bg-green-500';
      case 'away':
        return 'bg-yellow-500';
      case 'offline':
        return 'bg-gray-400';
      default:
        return 'bg-gray-300';
    }
  };

  return (
    <div className={`flex items-center space-x-2 ${className}`}>
      <div className={`w-2 h-2 rounded-full ${getPresenceColor()}`} />
      {showName && (
        <span className="text-sm text-gray-600">{displayName}</span>
      )}
    </div>
  );
};

/**
 * Connection Health Panel for debugging/admin view
 */
export const ConnectionHealthPanel = ({ 
  status, 
  reconnectAttempts,
  lastSeen,
  serverTimeOffset,
  className = "" 
}) => {
  return (
    <div className={`bg-gray-50 border rounded-lg p-3 text-xs ${className}`}>
      <div className="font-semibold text-gray-700 mb-2">Connection Health</div>
      <div className="space-y-1">
        <div className="flex justify-between">
          <span>Status:</span>
          <span className="font-medium">{status}</span>
        </div>
        <div className="flex justify-between">
          <span>Reconnect Attempts:</span>
          <span className="font-medium">{reconnectAttempts}</span>
        </div>
        <div className="flex justify-between">
          <span>Last Seen:</span>
          <span className="font-medium">
            {lastSeen ? new Date(lastSeen).toLocaleTimeString() : 'Never'}
          </span>
        </div>
        <div className="flex justify-between">
          <span>Server Offset:</span>
          <span className="font-medium">{serverTimeOffset}ms</span>
        </div>
      </div>
    </div>
  );
};

export default {
  ConnectionStatusIndicator,
  PresenceIndicator,
  ConnectionHealthPanel
};