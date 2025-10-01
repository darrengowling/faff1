import { io, Socket } from "socket.io-client";

export function createSocket(API_ORIGIN: string) {
  const transports = (import.meta.env.VITE_SOCKET_TRANSPORTS ?? "polling,websocket").split(",");
  const socket: Socket = io(API_ORIGIN, {
    path: "/api/socket.io",
    transports,
    withCredentials: true,
    reconnection: true,
  });

  function joinAndSync(leagueId: string) {
    sessionStorage.setItem("leagueId", leagueId);
    socket.emit("join_league", { leagueId });
    socket.emit("request_sync", { leagueId });
  }

  socket.on("connect", () => {
    console.log("✅ Socket.IO connected");
    const id = sessionStorage.getItem("leagueId");
    if (id) {
      console.log(`🔄 Auto-rejoining league: ${id}`);
      joinAndSync(id);
    }
  });
  
  socket.on("reconnect", () => {
    console.log("🔄 Socket.IO reconnected");
    const id = sessionStorage.getItem("leagueId");
    if (id) {
      console.log(`🔄 Auto-rejoining league after reconnect: ${id}`);
      joinAndSync(id);
    }
  });

  return { socket, joinAndSync };
}

// Utility function to get the current API origin
export function getApiOrigin(): string {
  return (typeof window !== 'undefined' && window.import?.meta?.env?.VITE_BACKEND_URL) ||
         (typeof import !== 'undefined' && import.meta?.env?.VITE_BACKEND_URL) ||
         process.env.REACT_APP_BACKEND_URL || 
         'https://leaguemate-1.preview.emergentagent.com';
}