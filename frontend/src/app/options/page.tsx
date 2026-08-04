'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { Card } from '@/components/ui/Card';
import { pnlClass } from '@/lib/utils';
import { Zap, AlertCircle, ArrowUpRight, ArrowDownRight } from 'lucide-react';

type OptionSignal = {
  underlying: string;
  spot: number;
  change_pct: number;
  signal: string;
  strike: number;
  option_type: string;
  symbol_display: string;
  conviction: string;
  reasoning: string;
};

export default function OptionsPage() {
  const [signals, setSignals] = useState<OptionSignal[]>([]);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState<string>('');

  const load = async () => {
    setLoading(true);
    try {
      const [nifty, banknifty] = await Promise.all([api.quote('NIFTY'), api.quote('BANKNIFTY')]);
      const now = new Date().toLocaleTimeString('en-IN');
      setLastUpdate(now);
      const results: OptionSignal[] = [];
      if (nifty.ltp) results.push(generateSignal('NIFTY', nifty.ltp, nifty.change_percent || 0, 50));
      if (banknifty.ltp) results.push(generateSignal('BANKNIFTY', banknifty.ltp, banknifty.change_percent || 0, 100));
      setSignals(results);
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    const interval = setInterval(load, 2000); // 2 seconds for instant options updates
    return () => clearInterval(interval);
  }, []);

  function generateSignal(underlying: string, spot: number, changePct: number, strikeStep: number): OptionSignal {
    const atmStrike = Math.round(spot / strikeStep) * strikeStep;
    let signal = 'WAIT';
    let optionType = 'CE';
    let conviction = 'NEUTRAL';
    let reasoning = 'Flat market — wait for clear direction';

    if (changePct > 0.8) {
      signal = 'BUY_CE';
      optionType = 'CE';
      conviction = Math.abs(changePct) > 1.5 ? 'HIGH' : 'MODERATE';
      reasoning = `${underlying} up ${changePct.toFixed(2)}% — strong bullish`;
    } else if (changePct < -0.8) {
      signal = 'BUY_PE';
      optionType = 'PE';
      conviction = Math.abs(changePct) > 1.5 ? 'HIGH' : 'MODERATE';
      reasoning = `${underlying} down ${changePct.toFixed(2)}% — strong bearish`;
    } else if (changePct > 0.3) {
      signal = 'BUY_CE';
      optionType = 'CE';
      conviction = 'LOW';
      reasoning = `${underlying} up ${changePct.toFixed(2)}% — mild bullish`;
    } else if (changePct < -0.3) {
      signal = 'BUY_PE';
      optionType = 'PE';
      conviction = 'LOW';
      reasoning = `${underlying} down ${changePct.toFixed(2)}% — mild bearish`;
    }

    return {
      underlying, spot, change_pct: changePct, signal, strike: atmStrike,
      option_type: optionType, symbol_display: `${underlying} ${atmStrike} ${optionType}`,
      conviction, reasoning
    };
  }

  return (
    <div className="space-y-6 animate-slide-up">
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Options Signals</h1>
          <p className="text-sm text-text-secondary mt-1">Fast NIFTY/BANKNIFTY options · 2-sec refresh</p>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-2 px-2.5 py-1 rounded-badge bg-profit/10 border border-profit/30">
            <span className="h-1.5 w-1.5 rounded-full bg-profit animate-pulse"></span>
            <span className="text-xs font-medium text-profit">LIVE</span>
          </div>
          <button onClick={load} className="btn-secondary flex items-center gap-2 text-sm" disabled={loading}>
            <Zap size={14} /> Refresh
          </button>
        </div>
      </div>

      <div className="glass p-4 border-dashed">
        <div className="flex items-start gap-2">
          <AlertCircle size={16} className="text-text-secondary mt-0.5" />
          <p className="text-xs text-text-secondary">
            <strong className="text-white">HIGH RISK:</strong> Options lose 100% fast. Max ₹1000-₹2000. Set SL. Exit by 3:15 PM.
          </p>
        </div>
      </div>

      {lastUpdate && <div className="text-xs text-text-muted">Last: {lastUpdate}</div>}

      <div className="grid gap-4">
        {signals.map((sig) => (
          <Card key={sig.underlying} className="glass p-5">
            <div className="flex items-start justify-between mb-4">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <h3 className="text-lg font-semibold">{sig.underlying}</h3>
                  <span className={pnlClass(sig.change_pct, 'text-xs font-medium')}>
                    {sig.change_pct > 0 ? '+' : ''}{sig.change_pct.toFixed(2)}%
                  </span>
                </div>
                <div className="text-sm text-text-muted">Spot: ₹{sig.spot.toFixed(2)}</div>
              </div>
              <div className={`px-3 py-1 rounded-badge text-xs font-semibold uppercase ${
                sig.conviction === 'HIGH' ? 'bg-profit/20 text-profit border border-profit/40' :
                sig.conviction === 'MODERATE' ? 'bg-white/10 text-white border border-border' :
                'bg-text-muted/10 text-text-muted border border-text-muted/30'
              }`}>
                {sig.conviction}
              </div>
            </div>

            {sig.signal !== 'WAIT' ? (
              <div className="space-y-3">
                <div className="flex items-center gap-2 p-3 rounded-lg bg-bg-hover border border-border">
                  {sig.option_type === 'CE' ? <ArrowUpRight className="text-profit" size={20} /> : <ArrowDownRight className="text-loss" size={20} />}
                  <div>
                    <div className="text-sm font-medium text-text-secondary">Signal</div>
                    <div className="text-lg font-semibold">{sig.symbol_display}</div>
                  </div>
                </div>
                <div className="text-sm text-text-secondary">{sig.reasoning}</div>
                <div className="grid grid-cols-3 gap-3 pt-2">
                  <div>
                    <div className="text-[10px] uppercase text-text-muted mb-1">Entry</div>
                    <div className="text-sm font-medium">Market</div>
                  </div>
                  <div>
                    <div className="text-[10px] uppercase text-text-muted mb-1">Target</div>
                    <div className="text-sm font-medium text-profit">+50%</div>
                  </div>
                  <div>
                    <div className="text-[10px] uppercase text-text-muted mb-1">SL</div>
                    <div className="text-sm font-medium text-loss">-30%</div>
                  </div>
                </div>
                <div className="pt-3 border-t border-border text-xs text-text-muted">
                  💡 Groww: Search "{sig.symbol_display}" → Buy market → SL -30% → Exit +50% or 3:15 PM
                </div>
              </div>
            ) : (
              <div className="text-center py-4 text-text-muted text-sm">{sig.reasoning}</div>
            )}
          </Card>
        ))}
      </div>
    </div>
  );
}