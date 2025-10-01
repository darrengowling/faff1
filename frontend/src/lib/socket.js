import { io, Socket } from "socket.io-client";

function resolveSocketPath(): string {
  const forced = import.meta.env.VITE_FORCE_SOCKET_PATH; // optional override
  if (forced === "/socket.io" || forced === "/api/socket.io") return forced;
  // Default to /api/socket.io (no-ingress-needed path)
  return "/api/socket.io";
}

export function createSocket(API_ORIGIN: string): Socket {
  let path = resolveSocketPath();
  const transports = (import.meta.env.VITE_SOCKET_TRANSPORTS ?? "polling,websocket").split(",");
  
  console.log(`🔌 Creating Socket.IO connection to ${API_ORIGIN}`);
  console.log(`📡 Path: ${path} | Transports: ${transports.join(', ')}`);
  
  let socket: Socket = io(API_ORIGIN, {
    path,
    transports,
    withCredentials: true,
    reconnection: true,
  });

  // Simple fallback: if handshake fails or we get HTML, retry with the other path
  let triedFallback = false;
  function tryFallback() {
    if (triedFallback) return;
    triedFallback = true;
    
    const alt = path === "/api/socket.io" ? "/socket.io" : "/api/socket.io";
    console.log(`⚠️ Socket.IO connection failed on ${path}, trying fallback: ${alt}`);
    
    socket.disconnect();
    socket = io(API_ORIGIN, {
      path: alt,
      transports: (import.meta.env.VITE_SOCKET_TRANSPORTS ?? "polling,websocket").split(","),
      withCredentials: true,
      reconnection: true,
    });
    
    path = alt; // Update the path for future reference
  }

  socket.on("connect_error", (error) => {
    console.error("Socket.IO connect_error:", error);
    tryFallback();
  });
  
  socket.io.on("error", (error) => {
    console.error("Socket.IO engine error:", error);
    tryFallback();
  });

  socket.on("connect", () => {
    const transport = socket.io.engine?.transport?.name || 'unknown';
    console.log(`✅ Socket.IO connected successfully on path: ${path} using ${transport} transport`);
    
    // Auto-rejoin league room and sync state on connect
    const leagueId = sessionStorage.getItem("leagueId");
    if (leagueId) {
      console.log(`🔄 Rejoining league room: ${leagueId}`);
      socket.emit("join_league", { leagueId });
      socket.emit("request_sync", { leagueId });
    }
  });

  socket.on("reconnect", () => {
    const transport = socket.io.engine?.transport?.name || 'unknown';
    console.log(`🔄 Socket.IO reconnected using ${transport} transport`);
    
    // Auto-rejoin league room and sync state on reconnect
    const leagueId = sessionStorage.getItem("leagueId");
    if (leagueId) {
      console.log(`🔄 Rejoining league room after reconnect: ${leagueId}`);
      socket.emit("join_league", { leagueId });
      socket.emit("request_sync", { leagueId });
    }
  });

  socket.on("upgrade", () => {
    const transport = socket.io.engine?.transport?.name || 'unknown';
    console.log(`⬆️ Socket.IO upgraded to ${transport} transport`);
  });

  return socket;
}

// Utility function to get the current API origin
export function getApiOrigin(): string {
  // Support both Vite and Create React App environment variables
  return (typeof window !== 'undefined' && window.import?.meta?.env?.VITE_BACKEND_URL) ||
         (typeof import !== 'undefined' && import.meta?.env?.VITE_BACKEND_URL) ||
         process.env.REACT_APP_BACKEND_URL || 
         'https://leaguemate-1.preview.emergentagent.com';
}