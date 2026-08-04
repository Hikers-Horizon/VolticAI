'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { Card, CardHeader } from '@/components/ui/Card';
import { formatPrice, formatPct, formatVolume, pnlClass, cn } from '@/lib/utils';
import { TableSkeleton } from '@/components/ui/Skeleton';
import { Plus, X } from 'lucide-react';

export default function WatchlistPage() {
  const [items, setItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [symbol, setSymbol] = useState('');
  const wlId = 1;

  const load = () =>
    api.watchlists()
      .then((d) => setItems(d.watchlists?.[0]?.items || []))
      .catch(() => {})
      .finally(() => setLoading(false));

  useEffect(() => {
    load();
    const t = setInterval(load, 2000); // 2 seconds - fast refresh with paid Dhan API
    return () => clearInterval(t);
  }, []);

  async function add() {
    if (!symbol.trim()) return;
    await api.addToWatchlist(wlId, symbol.trim().toUpperCase());
    setSymbol('');
    load();
  }

  async function remove(sym: string) {
    await api.removeFromWatchlist(wlId, sym);
    load();
  }

  return (
    <div className="space-y-6 animate-slide-up">
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Watchlist</h1>
          <p className="text-sm text-text-secondary mt-1">Live quotes · 2-sec refresh</p>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-badge bg-profit/10 border border-profit/30">
          <span className="h-2 w-2 rounded-full bg-profit animate-pulse"></span>
          <span className="text-xs font-medium text-profit">LIVE</span>
        </div>
      </div>

      <Card>
        <CardHeader
          title="Default Watchlist"
          action={
            <div className="flex gap-2">
              <input
                value={symbol}
                onChange={(e) => setSymbol(e.target.value.toUpperCase())}
                onKeyDown={(e) => e.key === 'Enter' && add()}
                placeholder="Add symbol"
                className="input-field h-9 w-36 text-sm"
              />
              <button onClick={add} className="btn-primary h-9 px-3 flex items-center gap-1 text-sm">
                <Plus size={14} /> Add
              </button>
            </div>
          }
        />

        {loading ? (
          <TableSkeleton rows={8} />
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-[10px] uppercase tracking-wider text-text-muted border-b border-border">
                <th className="text-left font-medium pb-3">Symbol</th>
                <th className="text-right font-medium pb-3">LTP</th>
                <th className="text-right font-medium pb-3">Open</th>
                <th className="text-right font-medium pb-3">High</th>
                <th className="text-right font-medium pb-3">Low</th>
                <th className="text-right font-medium pb-3">Change</th>
                <th className="text-right font-medium pb-3">Volume</th>
                <th className="pb-3" />
              </tr>
            </thead>
            <tbody>
              {items.map((item) => {
                const q = item.quote;
                return (
                  <tr key={item.symbol} className="border-b border-border/40 hover:bg-bg-hover/40">
                    <td className="py-3 font-medium">{item.symbol}</td>
                    <td className="py-3 text-right tabular-nums font-medium">
                      {q ? formatPrice(q.ltp) : '—'}
                    </td>
                    <td className="py-3 text-right tabular-nums text-text-secondary">
                      {q ? formatPrice(q.open) : '—'}
                    </td>
                    <td className="py-3 text-right tabular-nums text-text-secondary">
                      {q ? formatPrice(q.high) : '—'}
                    </td>
                    <td className="py-3 text-right tabular-nums text-text-secondary">
                      {q ? formatPrice(q.low) : '—'}
                    </td>
                    <td className={cn('py-3 text-right tabular-nums font-medium', q ? pnlClass(q.change_percent) : '')}>
                      {q ? formatPct(q.change_percent) : '—'}
                    </td>
                    <td className="py-3 text-right tabular-nums text-text-secondary">
                      {q ? formatVolume(q.volume) : '—'}
                    </td>
                    <td className="py-3 text-right">
                      <button
                        onClick={() => remove(item.symbol)}
                        className="p-1.5 rounded-md hover:bg-bg-hover text-text-muted hover:text-white"
                      >
                        <X size={14} />
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </Card>
    </div>
  );
}
