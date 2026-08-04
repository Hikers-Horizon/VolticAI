'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { Card, CardHeader } from '@/components/ui/Card';
import { formatINR, formatPct, formatPrice, pnlClass, cn } from '@/lib/utils';
import { TableSkeleton } from '@/components/ui/Skeleton';
import { Badge } from '@/components/ui/Badge';

export default function PortfolioPage() {
  const [portfolio, setPortfolio] = useState<any>(null);
  const [orders, setOrders] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const [p, o] = await Promise.all([api.portfolio(), api.orders()]);
        setPortfolio(p);
        setOrders(o.orders || []);
      } catch {
        /* ignore */
      } finally {
        setLoading(false);
      }
    };
    load();
    const t = setInterval(load, 4000);
    return () => clearInterval(t);
  }, []);

  return (
    <div className="space-y-6 animate-slide-up">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Portfolio</h1>
        <p className="text-sm text-text-secondary mt-1">
          {portfolio?.is_paper !== false ? 'Paper trading account' : 'Live account'}
        </p>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-4 gap-4">
        <SummaryCard
          label="Total Capital"
          value={formatINR(portfolio?.total_capital ?? 0)}
          loading={loading}
        />
        <SummaryCard
          label="Available"
          value={formatINR(portfolio?.available_capital ?? 0)}
          loading={loading}
        />
        <SummaryCard
          label="Today's P&L"
          value={`${(portfolio?.today_pnl ?? 0) >= 0 ? '+' : ''}${formatINR(portfolio?.today_pnl ?? 0)}`}
          sub={formatPct(portfolio?.today_pnl_percent ?? 0)}
          pnl={portfolio?.today_pnl}
          loading={loading}
        />
        <SummaryCard
          label="Open Positions"
          value={String(portfolio?.open_positions ?? 0)}
          loading={loading}
        />
      </div>

      {/* Positions */}
      <Card>
        <CardHeader title="Open Positions" />
        {loading ? (
          <TableSkeleton />
        ) : !portfolio?.positions?.length ? (
          <p className="text-sm text-text-muted py-8 text-center">
            No open positions. Execute a paper trade from AI Signals.
          </p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-[10px] uppercase tracking-wider text-text-muted border-b border-border">
                <th className="text-left pb-3 font-medium">Symbol</th>
                <th className="text-left pb-3 font-medium">Side</th>
                <th className="text-right pb-3 font-medium">Qty</th>
                <th className="text-right pb-3 font-medium">Avg</th>
                <th className="text-right pb-3 font-medium">LTP</th>
                <th className="text-right pb-3 font-medium">P&L</th>
                <th className="text-right pb-3 font-medium">P&L %</th>
              </tr>
            </thead>
            <tbody>
              {portfolio.positions.map((p: any) => (
                <tr key={p.id} className="border-b border-border/40">
                  <td className="py-3 font-medium">{p.symbol}</td>
                  <td className="py-3">
                    <Badge variant={p.side === 'BUY' ? 'buy' : 'sell'}>{p.side}</Badge>
                  </td>
                  <td className="py-3 text-right tabular-nums">{p.quantity}</td>
                  <td className="py-3 text-right tabular-nums">{formatPrice(p.avg_price)}</td>
                  <td className="py-3 text-right tabular-nums">{formatPrice(p.ltp)}</td>
                  <td className={cn('py-3 text-right tabular-nums font-medium', pnlClass(p.pnl))}>
                    {formatINR(p.pnl)}
                  </td>
                  <td className={cn('py-3 text-right tabular-nums', pnlClass(p.pnl_percent))}>
                    {formatPct(p.pnl_percent)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>

      {/* Orders */}
      <Card>
        <CardHeader title="Order History" subtitle="Paper fills" />
        {orders.length === 0 ? (
          <p className="text-sm text-text-muted py-6 text-center">No orders yet</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-[10px] uppercase tracking-wider text-text-muted border-b border-border">
                <th className="text-left pb-3 font-medium">Order ID</th>
                <th className="text-left pb-3 font-medium">Symbol</th>
                <th className="text-left pb-3 font-medium">Side</th>
                <th className="text-right pb-3 font-medium">Qty</th>
                <th className="text-right pb-3 font-medium">Price</th>
                <th className="text-left pb-3 font-medium">Status</th>
              </tr>
            </thead>
            <tbody>
              {[...orders].reverse().map((o: any) => (
                <tr key={o.order_id} className="border-b border-border/40">
                  <td className="py-2.5 text-xs text-text-muted font-mono">{o.order_id}</td>
                  <td className="py-2.5 font-medium">{o.symbol}</td>
                  <td className="py-2.5">
                    <Badge variant={o.side === 'BUY' ? 'buy' : 'sell'}>{o.side}</Badge>
                  </td>
                  <td className="py-2.5 text-right tabular-nums">{o.quantity}</td>
                  <td className="py-2.5 text-right tabular-nums">{formatPrice(o.avg_price || o.price)}</td>
                  <td className="py-2.5 text-xs text-text-secondary">{o.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>
    </div>
  );
}

function SummaryCard({
  label, value, sub, pnl, loading,
}: {
  label: string; value: string; sub?: string; pnl?: number; loading?: boolean;
}) {
  return (
    <Card>
      <div className="text-[10px] uppercase tracking-wider text-text-muted mb-2">{label}</div>
      {loading ? (
        <div className="skeleton h-7 w-24" />
      ) : (
        <>
          <div className={cn('text-xl font-semibold tabular-nums', pnl !== undefined && pnlClass(pnl))}>
            {value}
          </div>
          {sub && <div className={cn('text-xs mt-0.5', pnl !== undefined && pnlClass(pnl))}>{sub}</div>}
        </>
      )}
    </Card>
  );
}
