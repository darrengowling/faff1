import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card.jsx';
import { Badge } from './ui/badge.jsx';
import { Button } from './ui/button.jsx';
import { io } from 'socket.io-client';
import { RefreshCw, CheckCircle, XCircle, AlertCircle, Wifi, WifiOff } from 'lucide-react';

/**
 * Diagnostic Page Component
 * Shows current API configuration and live Socket.IO connection status
 */
const DiagnosticPage = () => {
  const { t } = useTranslation();
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  const [connectionDetails, setConnectionDetails] = useState(null);
  const [sessionId, setSessionId] = useState(null);
  const [actualTransport, setActualTransport] = useState(null);
  const [testSocket, setTestSocket] = useState(null);
  const [lastTest, setLastTest] = useState(null);
  const [isTesting, setIsTesting] = useState(false);

  // Get environment configuration
  const config = {
    // React (legacy)
    reactApiOrigin: process.env.REACT_APP_API_ORIGIN || 'Not set',
    reactBackendUrl: process.env.REACT_APP_BACKEND_URL || 'Not set',
    reactSocketPath: process.env.REACT_APP_SOCKET_PATH || 'Not set',
    
    // Cross-origin pattern (Next.js)
    nextApiUrl: process.env.NEXT_PUBLIC_API_URL || 'Not set',
    nextSocketPath: process.env.NEXT_PUBLIC_SOCKET_PATH || 'Not set',
    nextSocketTransports: process.env.NEXT_PUBLIC_SOCKET_TRANSPORTS || 'Not set',
    
    // Cross-origin pattern (Vite)
    viteApiUrl: (typeof window !== 'undefined' && window.import?.meta?.env?.VITE_PUBLIC_API_URL) || 'Not set',
    viteSocketPath: (typeof window !== 'undefined' && window.import?.meta?.env?.VITE_SOCKET_PATH) || 'Not set',
    viteSocketTransports: (typeof window !== 'undefined' && window.import?.meta?.env?.VITE_SOCKET_TRANSPORTS) || 'Not set',
    
    // Window/browser info
    windowOrigin: window.location.origin,
    userAgent: navigator.userAgent,
    timestamp: new Date().toISOString()
  };

  // Get active configuration using cross-origin pattern
  const activeConfig = {
    origin: config.viteApiUrl !== 'Not set' ? config.viteApiUrl :
            config.nextApiUrl !== 'Not set' ? config.nextApiUrl :
            config.reactApiOrigin !== 'Not set' ? config.reactApiOrigin :
            'https://auction-platform-6.preview.emergentagent.com',
               
    path: config.viteSocketPath !== 'Not set' ? config.viteSocketPath :
          config.nextSocketPath !== 'Not set' ? config.nextSocketPath :
          '/api/socketio',
          
    transports: (config.viteSocketTransports !== 'Not set' ? config.viteSocketTransports :
                config.nextSocketTransports !== 'Not set' ? config.nextSocketTransports :
                'polling,websocket').split(',')
  };

  const testConnection = async () => {
    setIsTesting(true);
    setConnectionStatus('testing');
    
    try {
      // Clean up existing socket
      if (testSocket) {
        testSocket.close();
      }

      console.log(`Testing Socket.IO connection to: ${activeConfig.origin} with path: ${activeConfig.path}, transports: ${activeConfig.transports}`);
      
      const socket = io(activeConfig.origin, {
        path: activeConfig.path,
        transports: activeConfig.transports,
        withCredentials: true,
        timeout: 10000,
        forceNew: true
      });

      setTestSocket(socket);

      // Set up event listeners
      socket.on('connect', () => {
        console.log('Diagnostic: Socket connected');
        setConnectionStatus('connected');
        setSessionId(socket.id);
        setActualTransport(socket.io.engine.transport.name);
        setConnectionDetails({
          socketId: socket.id,
          transport: socket.io.engine.transport.name,
          connected: socket.connected,
          connectedAt: new Date().toISOString()
        });
      });

      socket.on('connect_error', (error) => {
        console.log('Diagnostic: Socket connection error:', error);
        setConnectionStatus('error');
        setSessionId(null);
        setActualTransport(null);
        setConnectionDetails({
          error: error.message,
          errorAt: new Date().toISOString()
        });
      });

      socket.on('disconnect', (reason) => {
        console.log('Diagnostic: Socket disconnected:', reason);
        setConnectionStatus('disconnected');
        setConnectionDetails(prev => ({
          ...prev,
          disconnectedAt: new Date().toISOString(),
          disconnectReason: reason
        }));
      });

      // Timeout handling
      setTimeout(() => {
        if (connectionStatus === 'testing') {
          setConnectionStatus('timeout');
          setConnectionDetails({
            error: 'Connection timeout (10s)',
            errorAt: new Date().toISOString()
          });
        }
      }, 10000);

      setLastTest(new Date().toISOString());
      
    } catch (error) {
      console.error('Diagnostic: Connection test error:', error);
      setConnectionStatus('error');
      setConnectionDetails({
        error: error.message,
        errorAt: new Date().toISOString()
      });
    } finally {
      setIsTesting(false);
    }
  };

  const disconnectTest = () => {
    if (testSocket) {
      testSocket.close();
      setTestSocket(null);
    }
    setConnectionStatus('disconnected');
    setConnectionDetails(null);
  };

  useEffect(() => {
    return () => {
      if (testSocket) {
        testSocket.close();
      }
    };
  }, [testSocket]);

  const getStatusIcon = (status) => {
    switch (status) {
      case 'connected':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'testing':
        return <RefreshCw className="w-5 h-5 text-blue-500 animate-spin" />;
      case 'error':
      case 'timeout':
        return <XCircle className="w-5 h-5 text-red-500" />;
      default:
        return <WifiOff className="w-5 h-5 text-gray-400" />;
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'connected':
        return <Badge className="bg-green-500 text-white">Connected</Badge>;
      case 'testing':
        return <Badge className="bg-blue-500 text-white">Testing...</Badge>;
      case 'error':
        return <Badge className="bg-red-500 text-white">Error</Badge>;
      case 'timeout':
        return <Badge className="bg-orange-500 text-white">Timeout</Badge>;
      default:
        return <Badge className="bg-gray-500 text-white">Disconnected</Badge>;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-4xl mx-auto space-y-6">
        
        {/* Header */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Wifi className="w-6 h-6" />
              <span>Socket.IO Diagnostic Page</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-gray-600">
              This page shows the current API configuration and allows testing Socket.IO connectivity.
            </p>
          </CardContent>
        </Card>

        {/* Active Configuration */}
        <Card>
          <CardHeader>
            <CardTitle>Active Configuration</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="font-medium text-gray-700">API Origin:</label>
                <div className="bg-gray-100 p-2 rounded font-mono text-sm">
                  {activeConfig.origin}
                </div>
              </div>
              <div>
                <label className="font-medium text-gray-700">Socket Path:</label>
                <div className="bg-gray-100 p-2 rounded font-mono text-sm">
                  {activeConfig.path}
                </div>
              </div>
              <div>
                <label className="font-medium text-gray-700">Transports:</label>
                <div className="bg-gray-100 p-2 rounded font-mono text-sm">
                  {activeConfig.transports.join(', ')}
                </div>
              </div>
              <div>
                <label className="font-medium text-gray-700">Full Socket URL:</label>
                <div className="bg-blue-50 p-2 rounded font-mono text-sm text-blue-800">
                  {activeConfig.origin}{activeConfig.path}
                </div>
              </div>
              <div>
                <label className="font-medium text-gray-700">Window Origin:</label>
                <div className="bg-gray-100 p-2 rounded font-mono text-sm">
                  {config.windowOrigin}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Polling-Only Banner */}
        {actualTransport === 'polling' && connectionStatus === 'connected' && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
            <div className="flex items-center">
              <AlertCircle className="h-5 w-5 text-yellow-600 mr-2" />
              <div>
                <h4 className="text-yellow-800 font-medium">Polling-Only Connection</h4>
                <p className="text-yellow-700 text-sm">
                  WebSocket upgrade failed. Connection is using HTTP polling which may impact performance.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Connection Test */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span>Live Connection Status</span>
              {getStatusBadge(connectionStatus)}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center space-x-4">
                {getStatusIcon(connectionStatus)}
                <span className="font-medium">
                  Status: {connectionStatus.charAt(0).toUpperCase() + connectionStatus.slice(1)}
                </span>
              </div>

              {/* Session ID and Transport Info */}
              {sessionId && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="font-medium text-gray-700">Session ID (SID):</label>
                    <div className="bg-green-50 p-2 rounded font-mono text-sm text-green-800">
                      {sessionId}
                    </div>
                  </div>
                  <div>
                    <label className="font-medium text-gray-700">Active Transport:</label>
                    <div className="bg-blue-50 p-2 rounded font-mono text-sm text-blue-800">
                      {actualTransport}
                    </div>
                  </div>
                </div>
              )}

              {connectionDetails && (
                <div className="bg-gray-50 p-4 rounded">
                  <h4 className="font-medium mb-2">Connection Details:</h4>
                  <pre className="text-sm text-gray-700">
                    {JSON.stringify(connectionDetails, null, 2)}
                  </pre>
                </div>
              )}

              <div className="flex space-x-3">
                <Button 
                  onClick={testConnection} 
                  disabled={isTesting}
                  className="flex items-center space-x-2"
                >
                  <RefreshCw className={`w-4 h-4 ${isTesting ? 'animate-spin' : ''}`} />
                  <span>{isTesting ? 'Testing...' : 'Test Connection'}</span>
                </Button>
                
                {testSocket && (
                  <Button 
                    onClick={disconnectTest} 
                    variant="outline"
                  >
                    Disconnect
                  </Button>
                )}
              </div>

              {lastTest && (
                <div className="text-sm text-gray-500">
                  Last test: {new Date(lastTest).toLocaleString()}
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Environment Variables Details */}
        <Card>
          <CardHeader>
            <CardTitle>Environment Variables</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <h4 className="font-medium text-gray-700 mb-2">React Configuration (Legacy):</h4>
                <div className="grid grid-cols-1 gap-2 text-sm">
                  <div className="flex justify-between">
                    <span>REACT_APP_API_ORIGIN:</span>
                    <code className="bg-gray-100 px-2 py-1 rounded">{config.reactApiOrigin}</code>
                  </div>
                  <div className="flex justify-between">
                    <span>REACT_APP_BACKEND_URL:</span>
                    <code className="bg-gray-100 px-2 py-1 rounded">{config.reactBackendUrl}</code>
                  </div>
                  <div className="flex justify-between">
                    <span>REACT_APP_SOCKET_PATH:</span>
                    <code className="bg-gray-100 px-2 py-1 rounded">{config.reactSocketPath}</code>
                  </div>
                </div>
              </div>

              <div>
                <h4 className="font-medium text-gray-700 mb-2">Cross-Origin Configuration (Next.js):</h4>
                <div className="grid grid-cols-1 gap-2 text-sm">
                  <div className="flex justify-between">
                    <span>NEXT_PUBLIC_API_URL:</span>
                    <code className="bg-gray-100 px-2 py-1 rounded">{config.nextApiUrl}</code>
                  </div>
                  <div className="flex justify-between">
                    <span>NEXT_PUBLIC_SOCKET_PATH:</span>
                    <code className="bg-gray-100 px-2 py-1 rounded">{config.nextSocketPath}</code>
                  </div>
                  <div className="flex justify-between">
                    <span>NEXT_PUBLIC_SOCKET_TRANSPORTS:</span>
                    <code className="bg-gray-100 px-2 py-1 rounded">{config.nextSocketTransports}</code>
                  </div>
                </div>
              </div>

              <div>
                <h4 className="font-medium text-gray-700 mb-2">Cross-Origin Configuration (Vite):</h4>
                <div className="grid grid-cols-1 gap-2 text-sm">
                  <div className="flex justify-between">
                    <span>VITE_PUBLIC_API_URL:</span>
                    <code className="bg-gray-100 px-2 py-1 rounded">{config.viteApiUrl}</code>
                  </div>
                  <div className="flex justify-between">
                    <span>VITE_SOCKET_PATH:</span>
                    <code className="bg-gray-100 px-2 py-1 rounded">{config.viteSocketPath}</code>
                  </div>
                  <div className="flex justify-between">
                    <span>VITE_SOCKET_TRANSPORTS:</span>
                    <code className="bg-gray-100 px-2 py-1 rounded">{config.viteSocketTransports}</code>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Browser Info */}
        <Card>
          <CardHeader>
            <CardTitle>Browser Information</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span>User Agent:</span>
                <code className="bg-gray-100 px-2 py-1 rounded text-xs max-w-md truncate">
                  {config.userAgent}
                </code>
              </div>
              <div className="flex justify-between">
                <span>Timestamp:</span>
                <code className="bg-gray-100 px-2 py-1 rounded">{config.timestamp}</code>
              </div>
            </div>
          </CardContent>
        </Card>

      </div>
    </div>
  );
};

export default DiagnosticPage;