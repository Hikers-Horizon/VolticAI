'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { Card } from '@/components/ui/Card';
import { formatPrice } from '@/lib/utils';
import { Zap, Target, ShieldAlert, ArrowUpRight, ArrowDownRight, LogOut, RefreshCw, BarChart2, Layers } from 'lucide-react';

type OptionSignal = {
  underlying: string;
  spot_price: number;
  spot_change_pct: number;
  action: string;
  option_type: string;
  strike: number;
  expiry: string;
  symbol_display: string;
  moneyness: string;
  confidence: number;
  risk_reward: string;
  entry_price: number;
  entry_range: [number, number];
  target_1: number;
  target_2: number;
  target_3: number;
  stop_loss: number;
  trailing_sl: string;
  exit_rule: string;
  lot_size: number;
  recommended_lots: string;
  reasoning: string;
};

export default function OptionsPage() {
  const [signals, setSignals] = useState<OptionSignal[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedFilter, setSelectedFilter] = useState<string>('ALL');
  const [lastUpdate, setLastUpdate] = useState<string>('');

  const loadSignals = async () => {
    setLoading(true);
    try {
      const data = await api.optionsSignals(selectedFilter === 'ALL' ? undefined : selectedFilter);
      setSignals(data.signals || []);
      setLastUpdate(new Date().toLocaleTimeString('en-IN'));
    } catch (error) {
      console.error('Failed to load options signals:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSignals();
    const interval = setInterval(loadSignals, 5000); // 5 sec live refresh
    return () => clearInterval(interval);
  }, [selectedFilter]);

  return (
    <div className="space-y-6 animate-slide-up">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">AI Options Signals</h1>
          <p className="text-sm text-text-secondary mt-1">
            High-conviction NIFTY, BANKNIFTY & Stock Options with Entry, Targets, Stop-loss & Exit strategy
          </p>
        </div>
        <div className="flex items-center gap-2 self-start sm:self-auto">
          <div className="flex items-center gap-2 px-3 py-1 rounded-badge bg-profit/10 border border-profit/30">
            <span className="h-2 w-2 rounded-full bg-profit animate-pulse"></span>
            <span className="text-xs font-semibold text-profit">UPSTOX LIVE ENGINE</span>
          </div>
          <button
            onClick={loadSignals}
            disabled={loading}
            className="btn-secondary flex items-center gap-1.5 text-xs py-1.5 px-3"
          >
            <RefreshCw size={13} className={loading ? 'animate-spin' : ''} /> Refresh
          </button>
        </div>
      </div>

      {/* Underlying Filter Tabs */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1 border-b border-border">
        {['ALL', 'NIFTY', 'BANKNIFTY', 'FINNIFTY', 'RELIANCE', 'TCS', 'HDFCBANK', 'SBIN'].map((item) => (
          <button
            key={item}
            onClick={() => setSelectedFilter(item)}
            className={`px-4 py-2 text-xs font-medium rounded-button transition-all whitespace-nowrap ${
              selectedFilter === item
                ? 'bg-white text-black font-semibold shadow-md'
                : 'bg-bg-card border border-border text-text-secondary hover:border-white/30'
            }`}
          >
            {item}
          </button>
        ))}
      </div>

      {/* Signals List */}
      {loading && signals.length === 0 ? (
        <div className="p-12 text-center text-text-muted text-sm glass rounded-card">
          <RefreshCw size={24} className="animate-spin mx-auto mb-2 text-profit" />
          Analyzing spot momentum & options chain...
        </div>
      ) : signals.length === 0 ? (
        <div className="p-12 text-center text-text-muted text-sm glass rounded-card">
          No high-confidence option setups detected currently for {selectedFilter}. Re-analyzing on next candle...
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-6">
          {signals.map((sig, idx) => {
            const isCall = sig.option_type === 'CE';
            const actionBg = isCall ? 'bg-profit/15 text-profit border-profit/30' : 'bg-loss/15 text-loss border-loss/30';
            
            return (
              <Card key={idx} className="p-6 glass border-border hover:border-white/20 transition-all">
                {/* Header Row */}
                <div className="flex flex-wrap items-center justify-between gap-3 pb-4 border-b border-border/60">
                  <div className="flex items-center gap-3">
                    <div className={`p-2.5 rounded-button border ${actionBg}`}>
                      {isCall ? <ArrowUpRight size={20} /> : <ArrowDownRight size={20} />}
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <h2 className="text-xl font-bold tracking-tight text-white">{sig.symbol_display}</h2>
                        <span className="text-xs px-2 py-0.5 rounded-badge bg-bg-hover text-text-muted border border-border">
                          {sig.moneyness}
                        </span>
                      </div>
                      <p className="text-xs text-text-secondary mt-0.5">
                        Spot: <strong className="text-white">{formatPrice(sig.spot_price)}</strong> ({sig.spot_change_pct >= 0 ? '+' : ''}{sig.spot_change_pct}%) · Expiry: {sig.expiry}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-3">
                    <div className="text-right">
                      <div className="text-xs text-text-muted">AI Confidence</div>
                      <div className="text-base font-bold text-profit">{sig.confidence}%</div>
                    </div>
                    <div className={`px-3 py-1.5 rounded-button border text-xs font-semibold uppercase ${actionBg}`}>
                      {sig.action}
                    </div>
                  </div>
                </div>

                {/* Core Levels Grid (Entry, Target 1, 2, 3, Stop Loss) */}
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3 my-5">
                  {/* Entry Zone */}
                  <div className="p-3.5 rounded-button bg-bg-card border border-border">
                    <div className="flex items-center gap-1.5 text-xs text-text-muted mb-1">
                      <Target size={13} className="text-blue-400" /> Entry Zone
                    </div>
                    <div className="text-base font-bold text-white">₹{sig.entry_price}</div>
                    <div className="text-[11px] text-text-muted mt-0.5">
                      Range: ₹{sig.entry_range[0]} - ₹{sig.entry_range[1]}
                    </div>
                  </div>

                  {/* Target 1 */}
                  <div className="p-3.5 rounded-button bg-profit/5 border border-profit/20">
                    <div className="text-xs text-profit font-medium mb-1">🎯 Target 1 (+25%)</div>
                    <div className="text-base font-bold text-profit">₹{sig.target_1}</div>
                    <div className="text-[11px] text-text-muted mt-0.5">Quick Lock Profit</div>
                  </div>

                  {/* Target 2 */}
                  <div className="p-3.5 rounded-button bg-profit/5 border border-profit/20">
                    <div className="text-xs text-profit font-medium mb-1">🚀 Target 2 (+50%)</div>
                    <div className="text-base font-bold text-profit">₹{sig.target_2}</div>
                    <div className="text-[11px] text-text-muted mt-0.5">Trend Continuation</div>
                  </div>

                  {/* Target 3 */}
                  <div className="p-3.5 rounded-button bg-profit/10 border border-profit/30">
                    <div className="text-xs text-profit font-medium mb-1">🔥 Target 3 (+90%)</div>
                    <div className="text-base font-bold text-profit">₹{sig.target_3}</div>
                    <div className="text-[11px] text-text-muted mt-0.5">Runner Target</div>
                  </div>

                  {/* Stop Loss */}
                  <div className="p-3.5 rounded-button bg-loss/5 border border-loss/20">
                    <div className="flex items-center gap-1.5 text-xs text-loss font-medium mb-1">
                      <ShieldAlert size={13} /> Stop Loss (-20%)
                    </div>
                    <div className="text-base font-bold text-loss">₹{sig.stop_loss}</div>
                    <div className="text-[11px] text-text-muted mt-0.5">Strict SL Limit</div>
                  </div>
                </div>

                {/* Trailing Rules & Exit Conditions */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-3 border-t border-border/50 text-xs">
                  <div className="flex items-start gap-2 p-3 rounded-button bg-bg-hover/80 border border-border">
                    <RefreshCw size={14} className="text-blue-400 shrink-0 mt-0.5" />
                    <div>
                      <span className="font-semibold text-white">Trailing Stop-Loss Rule:</span>
                      <p className="text-text-secondary mt-0.5">{sig.trailing_sl}</p>
                    </div>
                  </div>

                  <div className="flex items-start gap-2 p-3 rounded-button bg-bg-hover/80 border border-border">
                    <LogOut size={14} className="text-loss shrink-0 mt-0.5" />
                    <div>
                      <span className="font-semibold text-white">Exit Signal & Trigger:</span>
                      <p className="text-text-secondary mt-0.5">{sig.exit_rule}</p>
                    </div>
                  </div>
                </div>

                {/* Trade Setup Footer (Lots & Reasoning) */}
                <div className="mt-4 pt-3 border-t border-border/40 flex flex-wrap items-center justify-between gap-3 text-xs">
                  <div className="text-text-secondary">
                    <strong className="text-white">AI Analysis:</strong> {sig.reasoning}
                  </div>
                  <div className="flex items-center gap-3 shrink-0">
                    <span className="text-text-muted">R:R Ratio: <strong className="text-white">{sig.risk_reward}</strong></span>
                    <span className="text-text-muted">Position: <strong className="text-profit">{sig.recommended_lots}</strong> ({sig.lot_size * 2} Qty)</span>
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}