'use client';

import { Suspense, useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { api, Signal } from '@/lib/api';
import { SignalCard } from '@/components/signals/SignalCard';
import { SignalCardSkeleton } from '@/components/ui/Skeleton';
import { cn } from '@/lib/utils';
import { RefreshCw } from 'lucide-react';

export default function SignalsPage() {
  return (
    <Suspense fallback={<div className="p-6 text-sm text-text-muted">Loading signals…</div>}>
      <SignalsInner />
    </Suspense>
  );
}

function SignalsInner() {
  const searchParams = useSearchParams();
  const focusSymbol = (searchParams.get('symbol') || '').toUpperCase();

  const [signals, setSignals] = useState<Signal[]>([]);
  const [focus, setFocus] = useState<Signal | null>(null);
  const [loading, setLoading] = useState(true);
  const [tradeableOnly, setTradeableOnly] = useState(false);
  const [disclaimer] = useState(
    'AI recommendations are probabilistic and not guaranteed. Analysis only — no order execution.'
  );

  const load = async () => {
    setLoading(true);
    try {
      const tasks: Promise<any>[] = [api.signals(tradeableOnly, true)];
      if (focusSymbol) {
        tasks.push(api.analyze(focusSymbol).catch(() => null));
      }
      const [d, focused] = await Promise.all(tasks);
      setSignals(d.signals || []);
      if (focused && focused.symbol) setFocus(focused as Signal);
      else setFocus(null);
    } catch {
      /* ignore */
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tradeableOnly, focusSymbol]);

  return (
    <div className="space-y-6 animate-slide-up">
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">AI Signals</h1>
          <p className="text-sm text-text-secondary mt-1">
            {focusSymbol
              ? `Focused analysis · ${focusSymbol}`
              : 'Multi-factor analysis for NSE intraday setups'}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <label className="flex items-center gap-2 text-xs text-text-secondary cursor-pointer">
            <input
              type="checkbox"
              checked={tradeableOnly}
              onChange={(e) => setTradeableOnly(e.target.checked)}
              className="rounded border-border"
            />
            Tradeable only (75%+)
          </label>
          <button onClick={load} className="btn-ghost flex items-center gap-2 text-xs h-9">
            <RefreshCw size={13} className={cn(loading && 'animate-spin')} />
            Refresh
          </button>
        </div>
      </div>

      <div className="rounded-card border border-border bg-bg-card/50 px-4 py-3 text-xs text-text-secondary">
        {disclaimer}
      </div>

      {/* Search-focused stock analysis */}
      {focusSymbol && (
        <div className="space-y-2">
          <div className="text-xs uppercase tracking-wider text-text-muted">
            Search result · {focusSymbol}
          </div>
          {loading && !focus ? (
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
              <SignalCardSkeleton />
            </div>
          ) : focus ? (
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
              <SignalCard key={`focus-${focus.symbol}`} signal={focus} />
            </div>
          ) : (
            <div className="text-sm text-text-muted py-4">
              Could not analyze {focusSymbol}. Try another NSE symbol.
            </div>
          )}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {loading
          ? Array.from({ length: 6 }).map((_, i) => <SignalCardSkeleton key={i} />)
          : signals
              .filter((s) => !focusSymbol || s.symbol !== focusSymbol)
              .map((s) => (
                <SignalCard key={`${s.symbol}-${s.action}`} signal={s} />
              ))}
      </div>

      {!loading && signals.length === 0 && (
        <div className="text-center py-20 text-text-muted text-sm">
          No signals match current filters. Markets may be choppy or volume is low.
        </div>
      )}
    </div>
  );
}
