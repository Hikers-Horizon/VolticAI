'use client';

import { useEffect, useState } from 'react';
import { api, Quote } from '@/lib/api';
import { Card, CardHeader } from '@/components/ui/Card';
import { formatPrice, formatPct, pnlClass, cn } from '@/lib/utils';
import { TableSkeleton } from '@/components/ui/Skeleton';

export function MarketOverview() {
  const [indices, setIndices] = useState<Quote[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = () =>
      api.indices()
        .then((d) => setIndices(d.indices || []))
        .catch(() => {})
        .finally(() => setLoading(false));
    load();
    const t = setInterval(load, 10000);
    return () => clearInterval(t);
  }, []);

  return (
    <Card>
      <CardHeader title="Market Overview" subtitle="Major indices" />
      {loading ? (
        <TableSkeleton rows={3} />
      ) : (
        <div className="space-y-2">
          {indices.map((idx) => (
            <div
              key={idx.symbol}
              className="flex items-center justify-between rounded-button border border-border/60 bg-bg-secondary/40 px-3 py-2.5 hover:bg-bg-hover transition-colors"
            >
              <div>
                <div className="text-sm font-medium">{idx.symbol}</div>
                <div className="text-[10px] text-text-muted">NSE</div>
              </div>
              <div className="text-right">
                <div className="text-sm font-semibold tabular-nums">
                  {formatPrice(idx.ltp)}
                </div>
                <div className={cn('text-xs tabular-nums', pnlClass(idx.change_percent))}>
                  {formatPct(idx.change_percent)} ({formatPrice(idx.change)})
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}
