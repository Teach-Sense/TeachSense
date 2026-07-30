import { useEffect, useRef, useCallback } from "react";

const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL || "wss://teachsense.up.railway.app/ws";

type MessageHandler = (data: any) => void;

export function useWebSocket(path: string, onMessage: MessageHandler) {
  const wsRef = useRef<WebSocket | null>(null);
  const retryCountRef = useRef(0);
  const retryTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const closedByUserRef = useRef(false);

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
      // onclose fires right after; reconnect handled there
    };

    ws.onclose = (event) => {
      if (closedByUserRef.current) return;
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