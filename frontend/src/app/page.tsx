'use client';

import { useEffect, useState } from 'react';
import { api, Signal } from '@/lib/api';
import { MarketOverview } from '@/components/dashboard/MarketOverview';
import { TopMovers } from '@/components/dashboard/TopMovers';
import { WatchlistWidget } from '@/components/dashboard/WatchlistWidget';
import { TradingChart } from '@/components/charts/TradingChart';
import { SignalCard } from '@/components/signals/SignalCard';
import { SignalCardSkeleton } from '@/components/ui/Skeleton';
import { Card, CardHeader } from '@/components/ui/Card';
import { cn } from '@/lib/utils';

export default function DashboardPage() {
  const [signals, setSignals] = useState<Signal[]>([]);
  const [loadingSignals, setLoadingSignals] = useState(true);
  const [breadth, setBreadth] = useState<any>(null);
  useEffect(() => {
    // Parallel load — signals (fast 8) + breadth together
    Promise.all([
      api.signals(false, true),
      api.breadth().catch(() => null),
    ])
      .then(([sig, br]) => {
        setSignals(sig.signals || []);
        if (br) setBreadth(br);
      })
      .catch(() => {})
      .finally(() => setLoadingSignals(false));
  }, []);

  const tradeable = signals.filter((s) => s.is_tradeable);
  const displaySignals = tradeable.length > 0 ? tradeable.slice(0, 4) : signals.slice(0, 4);

  return (
    <div className="space-y-6 animate-slide-up">
      {/* Header */}
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Dashboard</h1>
          <p className="text-sm text-text-secondary mt-1">
            AI-powered intraday intelligence · NSE
          </p>
        </div>
        <p className="text-[11px] text-text-muted max-w-xs text-right leading-relaxed">
          Live Upstox Data · AI Signals Engine
        </p>
      </div>

      {/* Top row: indices + breadth */}
      <div className="grid grid-cols-12 gap-4">
        <div className="col-span-6">
          <MarketOverview />
        </div>
        <div className="col-span-6">
          <Card>
            <CardHeader title="Market Breadth" subtitle="NSE Advance / Decline" />
            {breadth ? (
              <div className="space-y-3">
                <div className="flex gap-1 h-2 rounded-full overflow-hidden">
                  <div
                    className="bg-white rounded-full"
                    style={{
                      width: `${(breadth.advances / (breadth.advances + breadth.declines)) * 100}%`,
                    }}
                  />
                  <div className="bg-text-dim flex-1 rounded-full" />
                </div>
                <div className="grid grid-cols-3 gap-2 text-center">
                  <MiniStat label="Advances" value={breadth.advances} />
                  <MiniStat label="Declines" value={breadth.declines} />
                  <MiniStat label="A/D Ratio" value={breadth.advance_decline_ratio?.toFixed(2)} />
                </div>
                <div className="grid grid-cols-2 gap-2 text-center">
                  <MiniStat label="New Highs" value={breadth.new_highs} />
                  <MiniStat label="New Lows" value={breadth.new_lows} />
                </div>
              </div>
            ) : (
              <div className="h-24" />
            )}
          </Card>
        </div>
      </div>

      {/* Movers + Chart */}
      <div className="grid grid-cols-12 gap-4">
        <div className="col-span-4 space-y-4">
          <TopMovers />
        </div>
        <div className="col-span-8">
          <TradingChart symbol="NIFTY" height={340} />
        </div>
      </div>

      {/* AI Signals + Watchlist */}
      <div className="grid grid-cols-12 gap-4">
        <div className="col-span-8">
          <div className="flex items-center justify-between mb-3">
            <div>
              <h2 className="text-sm font-medium">AI Recommendations</h2>
              <p className="text-[11px] text-text-muted mt-0.5">
                Min confidence 75% · Min R:R 1:2
              </p>
            </div>
            <span className="text-xs text-text-muted">
              {tradeable.length} tradeable / {signals.length} analyzed
            </span>
          </div>
          <div className="grid grid-cols-2 gap-3">
            {loadingSignals
              ? Array.from({ length: 4 }).map((_, i) => <SignalCardSkeleton key={i} />)
              : displaySignals.map((s) => (
                  <SignalCard key={s.symbol} signal={s} />
                ))}
          </div>
        </div>
        <div className="col-span-4">
          <WatchlistWidget />
        </div>
      </div>
    </div>
  );
}

function MiniStat({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-button border border-border bg-bg-secondary/40 px-2 py-2">
      <div className="text-[10px] text-text-muted uppercase tracking-wider">{label}</div>
      <div className="text-sm font-semibold mt-0.5 tabular-nums">{value}</div>
    </div>
  );
}
