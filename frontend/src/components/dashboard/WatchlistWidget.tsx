'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { Card, CardHeader } from '@/components/ui/Card';
import { formatPrice, formatPct, pnlClass, cn } from '@/lib/utils';
import { TableSkeleton } from '@/components/ui/Skeleton';

type Item = {
  symbol: string;
  quote?: {
    ltp: number;
    change: number;
    change_percent: number;
    volume: number;
  };
};

export function WatchlistWidget() {
  const [items, setItems] = useState<Item[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = () =>
      api.watchlists()
        .then((d) => {
          const wl = d.watchlists?.[0];
          setItems(wl?.items || []);
        })
        .catch(() => {})
        .finally(() => setLoading(false));
    load();
    const t = setInterval(load, 2000); // 2 seconds for paid Dhan API
    return () => clearInterval(t);
  }, []);

  return (
    <Card padding="md">
      <CardHeader title="Watchlist" subtitle="Live quotes" />
      {loading ? (
        <TableSkeleton rows={6} />
      ) : (
        <div className="overflow-x-auto -mx-1">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-[10px] uppercase tracking-wider text-text-muted border-b border-border">
                <th className="text-left font-medium pb-2 px-1">Symbol</th>
                <th className="text-right font-medium pb-2 px-1">LTP</th>
                <th className="text-right font-medium pb-2 px-1">Chg%</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr
                  key={item.symbol}
                  className="border-b border-border/40 hover:bg-bg-hover/50 transition-colors"
                >
                  <td className="py-2.5 px-1 font-medium">{item.symbol}</td>
                  <td className="py-2.5 px-1 text-right tabular-nums">
                    {item.quote ? formatPrice(item.quote.ltp) : '—'}
                  </td>
                  <td className={cn(
                    'py-2.5 px-1 text-right tabular-nums text-xs font-medium',
                    item.quote ? pnlClass(item.quote.change_percent) : ''
                  )}>
                    {item.quote ? formatPct(item.quote.change_percent) : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Card>
  );
}
