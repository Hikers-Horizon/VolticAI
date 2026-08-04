'use client';

import { useState } from 'react';
import { api, Signal } from '@/lib/api';
import { SignalCard } from '@/components/signals/SignalCard';
import { SignalCardSkeleton } from '@/components/ui/Skeleton';
import { Card, CardHeader } from '@/components/ui/Card';
import { formatPct, formatPrice, pnlClass, cn } from '@/lib/utils';
import { Radar, Zap } from 'lucide-react';

type Mover = {
  symbol: string;
  ltp?: number;
  change_percent?: number;
  day_range_pct?: number;
  potential_tag?: string;
};

export default function ScannerPage() {
  const [results, setResults] = useState<Signal[]>([]);
  const [movers, setMovers] = useState<Mover[]>([]);
  const [loading, setLoading] = useState(false);
  const [meta, setMeta] = useState<any>(null);
  const [mode, setMode] = useState<'momentum' | 'standard'>('momentum');

  async function runScan() {
    setLoading(true);
    setResults([]);
    try {
      if (mode === 'momentum') {
        const d = await api.momentumScan(8, false);
        setResults(d.results || []);
        setMovers(d.movers_preview || []);
        setMeta(d);
      } else {
        const d = await api.scan();
        setResults(d.results || []);
        setMovers([]);
        setMeta(d);
      }
    } catch {
      /* ignore */
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6 animate-slide-up">
      <div className="flex items-end justify-between gap-4 flex-wrap">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Market Scanner</h1>
          <p className="text-sm text-text-secondary mt-1">
            High day-range / momentum names for aggressive intraday
          </p>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex rounded-button border border-border p-0.5">
            <button
              onClick={() => setMode('momentum')}
              className={cn(
                'px-3 py-1.5 text-xs rounded-md',
                mode === 'momentum' ? 'bg-white text-black' : 'text-text-secondary'
              )}
            >
              High volatility
            </button>
            <button
              onClick={() => setMode('standard')}
              className={cn(
                'px-3 py-1.5 text-xs rounded-md',
                mode === 'standard' ? 'bg-white text-black' : 'text-text-secondary'
              )}
            >
              Liquid large-cap
            </button>
          </div>
          <button onClick={runScan} disabled={loading} className="btn-primary flex items-center gap-2">
            {mode === 'momentum' ? <Zap size={15} /> : <Radar size={15} />}
            {loading ? 'Scanning…' : mode === 'momentum' ? 'Scan momentum' : 'Run AI Scan'}
          </button>
        </div>
      </div>

      <Card className="border-dashed">
        <p className="text-xs text-text-secondary leading-relaxed">
          <strong className="text-white">Truth:</strong> 10–20% single-day moves are uncommon.
          This ranks larger day-range / strong % move / volume stocks — higher volatility
          potential, not a guarantee. Always set SL on Groww.
        </p>
        {meta?.warning && <p className="text-xs text-warning mt-2">{meta.warning}</p>}
        {meta && (
          <p className="text-xs text-text-muted mt-2">
            Scanned {meta.scanned_count} · Signals {meta.signals_found}
            {meta.tradeable_count != null ? ` · Tradeable ${meta.tradeable_count}` : ''}
          </p>
        )}
      </Card>

      {!loading && movers.length > 0 && (
        <Card>
          <CardHeader title="Live explosive board" subtitle="Day % + range (Dhan)" />
          <table className="w-full text-sm">
            <thead>
              <tr className="text-[10px] uppercase tracking-wider text-text-muted border-b border-border">
                <th className="text-left pb-2">Symbol</th>
                <th className="text-right pb-2">LTP</th>
                <th className="text-right pb-2">Day %</th>
                <th className="text-right pb-2">Range %</th>
                <th className="text-right pb-2">Tag</th>
              </tr>
            </thead>
            <tbody>
              {movers.map((m) => (
                <tr key={m.symbol} className="border-b border-border/40">
                  <td className="py-2 font-medium">{m.symbol}</td>
                  <td className="py-2 text-right tabular-nums">
                    {m.ltp != null ? formatPrice(m.ltp) : '—'}
                  </td>
                  <td className={cn('py-2 text-right tabular-nums', pnlClass(m.change_percent || 0))}>
                    {m.change_percent != null ? formatPct(m.change_percent) : '—'}
                  </td>
                  <td className="py-2 text-right text-text-secondary tabular-nums">
                    {m.day_range_pct != null ? `${m.day_range_pct}%` : '—'}
                  </td>
                  <td className="py-2 text-right text-[11px] text-text-muted">
                    {m.potential_tag || '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}

      {loading && (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <SignalCardSkeleton key={i} />
          ))}
        </div>
      )}

      {!loading && results.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {results.map((s) => (
            <SignalCard key={s.symbol} signal={s} />
          ))}
        </div>
      )}
    </div>
  );
}
