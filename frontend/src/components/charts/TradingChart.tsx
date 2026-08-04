'use client';

import { useEffect, useRef, useState } from 'react';
import { api } from '@/lib/api';
import { Card, CardHeader } from '@/components/ui/Card';
import { cn } from '@/lib/utils';
import { Skeleton } from '@/components/ui/Skeleton';

const TIMEFRAMES = ['1minute', '3minute', '5minute', '15minute', '30minute', '1hour'];
const TF_LABELS: Record<string, string> = {
  '1minute': '1m', '3minute': '3m', '5minute': '5m',
  '15minute': '15m', '30minute': '30m', '1hour': '1H',
};

export function TradingChart({
  symbol = 'NIFTY',
  height = 360,
}: {
  symbol?: string;
  height?: number;
}) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<any>(null);
  const seriesRef = useRef<any>(null);
  const [tf, setTf] = useState('5minute');
  const [loading, setLoading] = useState(true);
  const [sym, setSym] = useState(symbol);

  useEffect(() => {
    let disposed = false;

    async function init() {
      if (!containerRef.current) return;
      const { createChart, ColorType } = await import('lightweight-charts');
      if (disposed) return;

      if (chartRef.current) {
        chartRef.current.remove();
      }

      const chart = createChart(containerRef.current, {
        height,
        layout: {
          background: { type: ColorType.Solid, color: 'transparent' },
          textColor: '#666666',
          fontFamily: 'Inter, system-ui, sans-serif',
          fontSize: 11,
        },
        grid: {
          vertLines: { color: '#111111' },
          horzLines: { color: '#111111' },
        },
        crosshair: {
          vertLine: { color: '#333', width: 1, style: 2, labelBackgroundColor: '#222' },
          horzLine: { color: '#333', width: 1, style: 2, labelBackgroundColor: '#222' },
        },
        rightPriceScale: { borderColor: '#222' },
        timeScale: { borderColor: '#222', timeVisible: true, secondsVisible: false },
      });

      const series = chart.addCandlestickSeries({
        upColor: '#FFFFFF',
        downColor: '#666666',
        borderUpColor: '#FFFFFF',
        borderDownColor: '#666666',
        wickUpColor: '#FFFFFF',
        wickDownColor: '#666666',
      });

      chartRef.current = chart;
      seriesRef.current = series;

      const ro = new ResizeObserver(() => {
        if (containerRef.current) {
          chart.applyOptions({ width: containerRef.current.clientWidth });
        }
      });
      ro.observe(containerRef.current);

      setLoading(false);
      return () => ro.disconnect();
    }

    init();
    return () => {
      disposed = true;
      chartRef.current?.remove();
      chartRef.current = null;
    };
  }, [height]);

  useEffect(() => {
    async function load() {
      try {
        const res = await api.historical(sym, tf);
        const data = (res.data || []).map((b: any) => ({
          time: Math.floor(new Date(b.timestamp).getTime() / 1000) as any,
          open: b.open,
          high: b.high,
          low: b.low,
          close: b.close,
        }));
        if (seriesRef.current && data.length) {
          seriesRef.current.setData(data);
          chartRef.current?.timeScale().fitContent();
        }
      } catch {
        /* ignore */
      }
    }
    load();
  }, [sym, tf]);

  return (
    <Card padding="md" className="overflow-hidden">
      <CardHeader
        title={sym}
        subtitle="Live Chart"
        action={
          <div className="flex items-center gap-1">
            {TIMEFRAMES.map((t) => (
              <button
                key={t}
                onClick={() => setTf(t)}
                className={cn(
                  'px-2 py-1 text-[11px] font-medium rounded-md transition-colors',
                  tf === t ? 'bg-white text-black' : 'text-text-muted hover:text-white'
                )}
              >
                {TF_LABELS[t]}
              </button>
            ))}
          </div>
        }
      />
      {loading && <Skeleton className="w-full" style={{ height } as any} />}
      <div ref={containerRef} className="w-full" style={{ height }} />
      <div className="flex gap-2 mt-2">
        {['NIFTY', 'BANKNIFTY', 'RELIANCE', 'TCS', 'INFY'].map((s) => (
          <button
            key={s}
            onClick={() => setSym(s)}
            className={cn(
              'text-[11px] px-2 py-1 rounded-md border transition-colors',
              sym === s
                ? 'border-white text-white'
                : 'border-border text-text-muted hover:text-white hover:border-border-strong'
            )}
          >
            {s}
          </button>
        ))}
      </div>
    </Card>
  );
}
