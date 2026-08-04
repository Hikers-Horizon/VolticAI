import { useEffect, useRef, useState } from 'react';

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';

type Quote = {
  symbol: string;
  ltp: number;
  change: number;
  change_percent: number;
  volume: number;
  high?: number;
  low?: number;
  open?: number;
};

export function useWebSocket(symbols: string[]) {
  const [quotes, setQuotes] = useState<Record<string, Quote>>({});
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();

  useEffect(() => {
    if (symbols.length === 0) return;

    function connect() {
      const ws = new WebSocket(`${WS_URL}/ws/quotes`);
      wsRef.current = ws;

      ws.onopen = () => {
        setConnected(true);
        // Subscribe to symbols
        ws.send(JSON.stringify({
          action: 'subscribe',
          symbols: symbols,
        }));
      };

      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          if (msg.type === 'quotes' && msg.data) {
            const newQuotes: Record<string, Quote> = {};
            msg.data.forEach((q: Quote) => {
              newQuotes[q.symbol] = q;
            });
            setQuotes((prev) => ({ ...prev, ...newQuotes }));
          }
        } catch (error) {
          console.error('WS parse error:', error);
        }
      };

      ws.onerror = (error) => {
        console.error('WS error:', error);
      };

      ws.onclose = () => {
        setConnected(false);
        // Auto-reconnect after 3 seconds
        reconnectTimeoutRef.current = setTimeout(() => {
          connect();
        }, 3000);
      };
    }

    connect();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [symbols.join(',')]);

  return { quotes, connected };
}
