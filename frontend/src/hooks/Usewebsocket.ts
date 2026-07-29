import { useEffect, useRef, useCallback } from "react";

const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL || "wss://teachsense.up.railway.app/ws";

type MessageHandler = (data: any) => void;

/**
 * Generic WebSocket hook for TeachSense live channels.
 *
 * Usage:
 *   useWebSocket("dashboard/", (data) => {
 *     if (data.type === "sessions_update") refetch();
 *   });
 *
 *   useWebSocket(`sessions/${sessionId}/`, (data) => { ... });
 *
 * Handles:
 *   - Attaching the access token as a query param (backend requires this,
 *     since WebSocket connections can't send an Authorization header)
 *   - Auto-reconnect with exponential backoff on unexpected close
 *   - Cleanup on unmount
 */
export function useWebSocket(path: string, onMessage: MessageHandler) {
  const wsRef = useRef<WebSocket | null>(null);
  const retryCountRef = useRef(0);
  const retryTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const closedByUserRef = useRef(false);

  // Keep the latest onMessage without forcing reconnect on every render
  const onMessageRef = useRef(onMessage);
  onMessageRef.current = onMessage;

  const connect = useCallback(() => {
    const token = localStorage.getItem("accessToken");
    if (!token) return;

    const url = `${WS_BASE_URL}/${path}?token=${token}`;
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      retryCountRef.current = 0;
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onMessageRef.current(data);
      } catch {
        // ignore malformed messages
      }
    };

    ws.onerror = () => {
      // onclose will fire right after; reconnect handled there
    };

    ws.onclose = (event) => {
      if (closedByUserRef.current) return;

      // 4001-ish custom close codes: don't hammer retries on auth rejection
      if (event.code === 4001 || event.code === 1008) return;

      const delay = Math.min(30000, 1000 * 2 ** retryCountRef.current);
      retryCountRef.current += 1;
      retryTimeoutRef.current = setTimeout(connect, delay);
    };
  }, [path]);

  useEffect(() => {
    closedByUserRef.current = false;
    connect();

    return () => {
      closedByUserRef.current = true;
      if (retryTimeoutRef.current) clearTimeout(retryTimeoutRef.current);
      wsRef.current?.close(1000, "Component unmounted");
    };
  }, [connect]);
}