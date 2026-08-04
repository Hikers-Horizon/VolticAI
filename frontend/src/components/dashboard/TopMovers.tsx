'use client';

import { useEffect, useState } from 'react';
import { api, Quote } from '@/lib/api';
import { Card, CardHeader } from '@/components/ui/Card';
import { formatPrice, formatPct, pnlClass, cn } from '@/lib/utils';
import { TableSkeleton } from '@/components/ui/Skeleton';

export function TopMovers() {
  const [gainers, setGainers] = useState<Quote[]>([]);
  const [losers, setLosers] = useState<Quote[]>([]);
  const [tab, setTab] = useState<'gainers' | 'losers'>('gainers');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([api.topGainers(8), api.topLosers(8)])
      .then(([g, l]) => {
        setGainers(g.gainers || []);
        setLosers(l.losers || []);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const list = tab === 'gainers' ? gainers : losers;

  return (
    <Card>
      <CardHeader
        title="Top Movers"
        action={
          <div className="flex gap-1 rounded-button border border-border p-0.5">
            {(['gainers', 'losers'] as const).map((t) => (
              <button
                key={t}
                onClick={() => setTab(t)}
                className={cn(
                  'px-2.5 py-1 text-[11px] font-medium rounded-md capitalize transition-colors',
                  tab === t ? 'bg-white text-black' : 'text-text-secondary hover:text-white'
                )}
              >
                {t}
              </button>
            ))}
          </div>
        }
      />
      {loading ? (
        <TableSkeleton rows={6} />
      ) : (
        <div className="space-y-1">
          {list.map((q) => (
            <div
              key={q.symbol}
              className="flex items-center justify-between px-2 py-2 rounded-button hover:bg-bg-hover transition-colors"
            >
              <span className="text-sm font-medium">{q.symbol}</span>
              <div className="flex items-center gap-4">
                <span className="text-sm tabular-nums text-text-secondary">
                  {formatPrice(q.ltp)}
                </span>
                <span className={cn('text-xs font-medium tabular-nums w-16 text-right', pnlClass(q.change_percent))}>
                  {formatPct(q.change_percent)}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}
