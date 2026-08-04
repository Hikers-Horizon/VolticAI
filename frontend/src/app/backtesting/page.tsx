'use client';

import { useState } from 'react';
import { Card, CardHeader } from '@/components/ui/Card';
import { formatPct, cn } from '@/lib/utils';
import { FlaskConical } from 'lucide-react';

export default function BacktestingPage() {
  const [symbol, setSymbol] = useState('NIFTY');
  const [timeframe, setTimeframe] = useState('5minute');
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<any>(null);

  async function run() {
    setRunning(true);
    // Simulated backtest — wire to backend engine later
    await new Promise((r) => setTimeout(r, 1500));
    setResult({
      symbol,
      timeframe,
      trades: 42,
      win_rate: 58.5,
      profit_factor: 1.85,
      total_return: 12.4,
      max_drawdown: -4.2,
      sharpe: 1.42,
      avg_rr: 2.1,
    });
    setRunning(false);
  }

  return (
    <div className="space-y-6 animate-slide-up">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Backtesting</h1>
        <p className="text-sm text-text-secondary mt-1">
          Test AI strategy rules on historical bars
        </p>
      </div>

      <div className="grid grid-cols-12 gap-4">
        <div className="col-span-4">
          <Card>
            <CardHeader title="Configuration" />
            <div className="space-y-3">
              <div>
                <label className="text-[10px] uppercase tracking-wider text-text-muted">Symbol</label>
                <input
                  className="input-field mt-1 text-sm"
                  value={symbol}
                  onChange={(e) => setSymbol(e.target.value.toUpperCase())}
                />
              </div>
              <div>
                <label className="text-[10px] uppercase tracking-wider text-text-muted">Timeframe</label>
                <select
                  className="input-field mt-1 text-sm"
                  value={timeframe}
                  onChange={(e) => setTimeframe(e.target.value)}
                >
                  {['1minute', '3minute', '5minute', '15minute', '30minute', '1hour'].map((t) => (
                    <option key={t} value={t}>{t}</option>
                  ))}
                </select>
              </div>
              <div className="text-xs text-text-muted border border-border rounded-button p-3">
                Strategy: AI multi-factor (EMA + VWAP + RSI + Supertrend)
                <br />
                Filters: Conf ≥ 75%, RR ≥ 1:2
              </div>
              <button onClick={run} disabled={running} className="btn-primary w-full flex items-center justify-center gap-2">
                <FlaskConical size={14} />
                {running ? 'Running…' : 'Run Backtest'}
              </button>
            </div>
          </Card>
        </div>

        <div className="col-span-8">
          {!result && !running && (
            <Card className="flex flex-col items-center justify-center py-24 text-text-muted">
              <FlaskConical size={32} className="mb-3 opacity-40" />
              <p className="text-sm">Configure and run a backtest</p>
            </Card>
          )}
          {running && (
            <Card className="flex items-center justify-center py-24">
              <div className="text-sm text-text-secondary animate-pulse-soft">Simulating trades…</div>
            </Card>
          )}
          {result && !running && (
            <div className="space-y-4">
              <div className="grid grid-cols-4 gap-3">
                <Metric label="Total Return" value={formatPct(result.total_return)} positive={result.total_return > 0} />
                <Metric label="Win Rate" value={`${result.win_rate}%`} />
                <Metric label="Profit Factor" value={String(result.profit_factor)} />
                <Metric label="Max DD" value={formatPct(result.max_drawdown)} positive={false} />
                <Metric label="Trades" value={String(result.trades)} />
                <Metric label="Sharpe" value={String(result.sharpe)} />
                <Metric label="Avg R:R" value={`1:${result.avg_rr}`} />
                <Metric label="Symbol" value={result.symbol} />
              </div>
              <Card>
                <p className="text-xs text-text-secondary leading-relaxed">
                  Simulated results for demonstration. Connect historical broker data for production-grade
                  backtests. Past performance does not guarantee future results.
                </p>
              </Card>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function Metric({ label, value, positive }: { label: string; value: string; positive?: boolean }) {
  return (
    <Card>
      <div className="text-[10px] uppercase tracking-wider text-text-muted">{label}</div>
      <div className={cn(
        'text-lg font-semibold mt-1 tabular-nums',
        positive === true && 'text-profit',
        positive === false && 'text-loss'
      )}>
        {value}
      </div>
    </Card>
  );
}
