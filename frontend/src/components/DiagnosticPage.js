import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { io } from 'socket.io-client';
import { RefreshCw, CheckCircle, XCircle, AlertCircle, Wifi, WifiOff } from 'lucide-react';

/**
 * Diagnostic Page Component
 * Shows current API configuration and live Socket.IO connection status
 */
const DiagnosticPage = () => {
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  const [connectionDetails, setConnectionDetails] = useState(null);
  const [testSocket, setTestSocket] = useState(null);
  const [lastTest, setLastTest] = useState(null);
  const [isTesting, setIsTesting] = useState(false);

  // Get environment configuration
  const config = {
    // React
    apiOrigin: process.env.REACT_APP_API_ORIGIN || 'Not set',
    backendUrl: process.env.REACT_APP_BACKEND_URL || 'Not set',
    socketPath: process.env.REACT_APP_SOCKET_PATH || 'Not set',
    
    // Next.js fallbacks
    nextApiOrigin: process.env.NEXT_PUBLIC_API_ORIGIN || 'Not set',
    nextApiUrl: process.env.NEXT_PUBLIC_API_URL || 'Not set', 
    nextSocketPath: process.env.NEXT_PUBLIC_SOCKET_PATH || 'Not set',
    
    // Vite fallbacks
    viteApiOrigin: process.env.VITE_API_ORIGIN || 'Not set',
    viteApiUrl: process.env.VITE_PUBLIC_API_URL || 'Not set',
    viteSocketPath: process.env.VITE_SOCKET_PATH || 'Not set',
    
    // Window/browser info
    windowOrigin: window.location.origin,
    userAgent: navigator.userAgent,
    timestamp: new Date().toISOString()
  };

  // Get active configuration (what would actually be used)
  const activeConfig = {
    apiOrigin: config.apiOrigin !== 'Not set' ? config.apiOrigin : 
               config.nextApiOrigin !== 'Not set' ? config.nextApiOrigin :
               config.viteApiOrigin !== 'Not set' ? config.viteApiOrigin :
               'https://realtime-socket-fix.preview.emergentagent.com',
               
    socketPath: config.socketPath !== 'Not set' ? config.socketPath :
               config.nextSocketPath !== 'Not set' ? config.nextSocketPath :
               config.viteSocketPath !== 'Not set' ? config.viteSocketPath :
               '/api/socketio'
  };

  const testConnection = async () => {
    setIsesting(true);
    setConnectionStatus('testing');
    
    try {
      // Clean up existing socket
      if (testSocket) {
        testSocket.close();
      }

      console.log(`Testing Socket.IO connection to: ${activeConfig.apiOrigin} with path: ${activeConfig.socketPath}`);
      
      const socket = io(activeConfig.apiOrigin, {
        path: activeConfig.socketPath,
        transports: ['websocket', 'polling'],
        withCredentials: true,
        timeout: 10000,
        forceNew: true
      });

      setTestSocket(socket);

      // Set up event listeners
      socket.on('connect', () => {
        console.log('Diagnostic: Socket connected');
        setConnectionStatus('connected');
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
      setIsesting(false);
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
                  {activeConfig.apiOrigin}
                </div>
              </div>
              <div>
                <label className="font-medium text-gray-700">Socket Path:</label>
                <div className="bg-gray-100 p-2 rounded font-mono text-sm">
                  {activeConfig.socketPath}
                </div>
              </div>
              <div>
                <label className="font-medium text-gray-700">Window Origin:</label>
                <div className="bg-gray-100 p-2 rounded font-mono text-sm">
                  {config.windowOrigin}
                </div>
              </div>
              <div>
                <label className="font-medium text-gray-700">Full Socket URL:</label>
                <div className="bg-blue-50 p-2 rounded font-mono text-sm text-blue-800">
                  {activeConfig.apiOrigin}{activeConfig.socketPath}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

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
                  disabled={isesting}
                  className="flex items-center space-x-2"
                >
                  <RefreshCw className={`w-4 h-4 ${isesting ? 'animate-spin' : ''}`} />
                  <span>{isesting ? 'Testing...' : 'Test Connection'}</span>
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
                <h4 className="font-medium text-gray-700 mb-2">React Configuration:</h4>
                <div className="grid grid-cols-1 gap-2 text-sm">
                  <div className="flex justify-between">
                    <span>REACT_APP_API_ORIGIN:</span>
                    <code className="bg-gray-100 px-2 py-1 rounded">{config.apiOrigin}</code>
                  </div>
                  <div className="flex justify-between">
                    <span>REACT_APP_BACKEND_URL:</span>
                    <code className="bg-gray-100 px-2 py-1 rounded">{config.backendUrl}</code>
                  </div>
                  <div className="flex justify-between">
                    <span>REACT_APP_SOCKET_PATH:</span>
                    <code className="bg-gray-100 px-2 py-1 rounded">{config.socketPath}</code>
                  </div>
                </div>
              </div>

              <div>
                <h4 className="font-medium text-gray-700 mb-2">Next.js Configuration:</h4>
                <div className="grid grid-cols-1 gap-2 text-sm">
                  <div className="flex justify-between">
                    <span>NEXT_PUBLIC_API_ORIGIN:</span>
                    <code className="bg-gray-100 px-2 py-1 rounded">{config.nextApiOrigin}</code>
                  </div>
                  <div className="flex justify-between">
                    <span>NEXT_PUBLIC_API_URL:</span>
                    <code className="bg-gray-100 px-2 py-1 rounded">{config.nextApiUrl}</code>
                  </div>
                  <div className="flex justify-between">
                    <span>NEXT_PUBLIC_SOCKET_PATH:</span>
                    <code className="bg-gray-100 px-2 py-1 rounded">{config.nextSocketPath}</code>
                  </div>
                </div>
              </div>

              <div>
                <h4 className="font-medium text-gray-700 mb-2">Vite Configuration:</h4>
                <div className="grid grid-cols-1 gap-2 text-sm">
                  <div className="flex justify-between">
                    <span>VITE_API_ORIGIN:</span>
                    <code className="bg-gray-100 px-2 py-1 rounded">{config.viteApiOrigin}</code>
                  </div>
                  <div className="flex justify-between">
                    <span>VITE_PUBLIC_API_URL:</span>
                    <code className="bg-gray-100 px-2 py-1 rounded">{config.viteApiUrl}</code>
                  </div>
                  <div className="flex justify-between">
                    <span>VITE_SOCKET_PATH:</span>
                    <code className="bg-gray-100 px-2 py-1 rounded">{config.viteSocketPath}</code>
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