'use client';

import { useEffect, useRef, useState, useCallback } from 'react';

const WS_URL = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000')
  .replace('http://', 'ws://').replace('https://', 'wss://');

export interface WSEvent {
  type: string;
  [key: string]: unknown;
}

export function useWebSocket(onEvent?: (event: WSEvent) => void) {
  const [isConnected, setIsConnected] = useState(false);
  const [lastEvent, setLastEvent] = useState<WSEvent | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const reconnectDelay = useRef(1000);
  const pollingTimer = useRef<ReturnType<typeof setInterval> | undefined>(undefined);
  const usingPolling = useRef(false);

  const handleEvent = useCallback((event: WSEvent) => {
    setLastEvent(event);
    onEvent?.(event);
  }, [onEvent]);

  // Polling fallback — fetches pending approvals count
  const startPolling = useCallback(() => {
    if (pollingTimer.current) return;
    usingPolling.current = true;
    setIsConnected(true); // treat polling as "connected"

    pollingTimer.current = setInterval(async () => {
      try {
        const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        const token = localStorage.getItem('omnisales_token');
        const headers: Record<string, string> = {};
        if (token) headers['Authorization'] = `Bearer ${token}`;

        const res = await fetch(`${API_BASE}/api/dashboard/stats`, { headers });
        if (res.ok) {
          const data = await res.json();
          handleEvent({ type: 'stats_update', ...data });
        }
      } catch {
        // Silently fail polling
      }
    }, 10000); // Poll every 10 seconds
  }, [handleEvent]);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    try {
      const ws = new WebSocket(`${WS_URL}/ws/live`);
      wsRef.current = ws;

      ws.onopen = () => {
        setIsConnected(true);
        reconnectDelay.current = 1000;
        // Stop polling if we have WS
        if (pollingTimer.current) {
          clearInterval(pollingTimer.current);
          pollingTimer.current = undefined;
          usingPolling.current = false;
        }
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type !== 'pong') {
            handleEvent(data);
          }
        } catch {
          // Non-JSON message
        }
      };

      ws.onclose = () => {
        setIsConnected(false);
        wsRef.current = null;
        // Exponential backoff reconnect
        reconnectTimer.current = setTimeout(() => {
          reconnectDelay.current = Math.min(reconnectDelay.current * 2, 30000);
          connect();
        }, reconnectDelay.current);
      };

      ws.onerror = () => {
        ws.close();
        // Fall back to polling after 3 failed attempts
        if (reconnectDelay.current > 4000) {
          startPolling();
        }
      };
    } catch {
      // WebSocket not available — use polling
      startPolling();
    }
  }, [handleEvent, startPolling]);

  useEffect(() => {
    connect();
    return () => {
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
      if (pollingTimer.current) clearInterval(pollingTimer.current);
      wsRef.current?.close();
    };
  }, [connect]);

  return { isConnected, lastEvent, usingPolling: usingPolling.current };
}
