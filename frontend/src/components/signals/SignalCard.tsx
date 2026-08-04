'use client';

import { useState } from 'react';
import { Signal } from '@/lib/api';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { formatINR, cn } from '@/lib/utils';
import { Target, Shield, TrendingUp, TrendingDown, Minus, Copy, Check, Newspaper } from 'lucide-react';

export function SignalCard({
  signal,
  compact = false,
}: {
  signal: Signal;
  onTrade?: (s: Signal) => void;
  compact?: boolean;
}) {
  const isBuy = signal.action === 'BUY';
  const isSell = signal.action === 'SELL';
  const isWait = signal.action === 'WAIT';
  const [copied, setCopied] = useState(false);

  async function copyPublish() {
    const text =
      signal.publish_text ||
      [
        `#${signal.symbol} | ${signal.action} | ${signal.confidence}%`,
        `Entry: ${signal.entry_price} | SL: ${signal.stop_loss}`,
        `T1: ${signal.target_1} | T2: ${signal.target_2} | T3: ${signal.target_3}`,
        `R:R 1:${signal.risk_reward}`,
        signal.thesis || signal.reason,
        signal.disclaimer,
      ].join('\n');
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      /* ignore */
    }
  }

  return (
    <Card hover className="relative overflow-hidden">
      {/* Top accent line */}
      <div
        className={cn(
          'absolute top-0 left-0 right-0 h-[1px]',
          isBuy && 'bg-profit/60',
          isSell && 'bg-loss/60',
          isWait && 'bg-border'
        )}
      />

      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-base font-semibold tracking-tight">{signal.symbol}</h3>
            <Badge variant={isBuy ? 'buy' : isSell ? 'sell' : 'wait'}>
              {signal.action}
            </Badge>
          </div>
          <p className="text-[11px] text-text-muted mt-0.5 uppercase tracking-wider">
            {signal.timeframe} · NSE
          </p>
        </div>
        <div className="text-right">
          <div className="text-[10px] text-text-muted uppercase tracking-wider mb-0.5">
            Confidence
          </div>
          <div
            className={cn(
              'text-xl font-semibold tabular-nums',
              signal.confidence >= 75 ? 'text-white' : 'text-text-secondary'
            )}
          >
            {signal.confidence.toFixed(0)}%
          </div>
        </div>
      </div>

      {/* Confidence bar */}
      <div className="h-1 w-full rounded-full bg-bg-secondary mb-4 overflow-hidden">
        <div
          className={cn(
            'h-full rounded-full transition-all duration-500',
            signal.confidence >= 75 ? 'bg-white' : 'bg-text-muted'
          )}
          style={{ width: `${Math.min(signal.confidence, 100)}%` }}
        />
      </div>

      {/* Always show Entry / SL / Targets when levels exist */}
      {signal.entry_price != null && signal.stop_loss != null ? (
        <>
          <div className="grid grid-cols-2 gap-2 mb-3">
            <Level label="Entry" value={formatINR(signal.entry_price)} icon={<TrendingUp size={12} />} />
            <Level
              label="Stop Loss"
              value={formatINR(signal.stop_loss)}
              icon={<Shield size={12} />}
              danger
            />
            <Level
              label="Target 1"
              value={signal.target_1 != null ? formatINR(signal.target_1) : '—'}
              icon={<Target size={12} />}
              profit
            />
            <Level
              label="R:R"
              value={signal.risk_reward != null ? `1 : ${signal.risk_reward.toFixed(1)}` : '—'}
              icon={<Minus size={12} />}
            />
          </div>

          {(signal.target_2 != null || signal.target_3 != null) && (
            <div className="flex gap-3 mb-3 text-xs text-text-secondary">
              {signal.target_2 != null && (
                <span>
                  T2 <span className="text-white font-medium">{formatINR(signal.target_2)}</span>
                </span>
              )}
              {signal.target_3 != null && (
                <span>
                  T3 <span className="text-white font-medium">{formatINR(signal.target_3)}</span>
                </span>
              )}
            </div>
          )}

          {!signal.is_tradeable && (
            <div className="rounded-button border border-border bg-bg-secondary/50 px-3 py-2 mb-2">
              <div className="flex items-center gap-2 text-text-secondary text-xs">
                <TrendingDown size={12} />
                <span>Reference levels · filters not fully passed</span>
              </div>
              {signal.rejection_reasons?.length > 0 && (
                <ul className="mt-1.5 space-y-0.5">
                  {signal.rejection_reasons.slice(0, 3).map((r, i) => (
                    <li key={i} className="text-[11px] text-text-muted">
                      · {r}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )}

          <button
            type="button"
            onClick={copyPublish}
            className="btn-primary w-full text-sm mt-1 flex items-center justify-center gap-2"
          >
            {copied ? <Check size={14} /> : <Copy size={14} />}
            {copied ? 'Copied publish pack' : 'Copy full signal to publish'}
          </button>
          <div className="mt-2 text-[10px] text-text-muted text-center">
            No broker orders · You take / publish trades yourself
          </div>
        </>
      ) : (
        <div className="rounded-button border border-border bg-bg-secondary/50 px-3 py-2.5 mb-2">
          <div className="flex items-center gap-2 text-text-secondary text-xs">
            <TrendingDown size={12} />
            <span>Insufficient data for levels</span>
          </div>
        </div>
      )}

      {/* Research body */}
      {signal.summary && (
        <p className="text-[11px] leading-relaxed text-white mt-3">{signal.summary}</p>
      )}
      <p className="text-[11px] leading-relaxed text-text-secondary mt-2">
        {signal.thesis || signal.reason}
      </p>

      {!compact && signal.history_summary && (
        <div className="mt-3 rounded-button border border-border bg-bg-secondary/40 px-2.5 py-2">
          <div className="text-[10px] uppercase tracking-wider text-text-muted mb-1">Trade history</div>
          <p className="text-[11px] text-text-secondary leading-relaxed">{signal.history_summary}</p>
        </div>
      )}

      {!compact && signal.news && signal.news.length > 0 && (
        <div className="mt-3 rounded-button border border-border bg-bg-secondary/40 px-2.5 py-2">
          <div className="flex items-center gap-1.5 text-[10px] uppercase tracking-wider text-text-muted mb-1.5">
            <Newspaper size={11} />
            Latest news · {signal.news_bias || 'NEUTRAL'}
          </div>
          <ul className="space-y-1.5">
            {signal.news.slice(0, 3).map((n, i) => (
              <li key={i} className="text-[11px] text-text-secondary leading-snug">
                <span
                  className={cn(
                    'mr-1.5 text-[10px] font-semibold',
                    n.bias === 'BULLISH' && 'text-profit',
                    n.bias === 'BEARISH' && 'text-loss',
                    (!n.bias || n.bias === 'NEUTRAL') && 'text-text-muted'
                  )}
                >
                  {n.bias || 'NEUTRAL'}
                </span>
                {n.link ? (
                  <a href={n.link} target="_blank" rel="noreferrer" className="hover:text-white underline-offset-2 hover:underline">
                    {n.title}
                  </a>
                ) : (
                  n.title
                )}
              </li>
            ))}
          </ul>
        </div>
      )}

      {!compact && signal.invalidation && (
        <div className="mt-2 text-[11px] text-text-muted leading-relaxed">
          <span className="text-text-secondary font-medium">Invalidation: </span>
          {signal.invalidation}
        </div>
      )}

      {/* Groww ₹10k plan */}
      {(signal as any).quantity > 0 && (
        <div className="mt-3 rounded-button border border-white/10 bg-white/[0.03] px-2.5 py-2">
          <div className="flex items-center justify-between mb-1">
            <div className="text-[10px] uppercase tracking-wider text-text-muted">
              Groww plan · ₹{(signal as any).capital || 10000}
            </div>
            {(signal as any).setup_grade && (
              <span className="text-[10px] font-semibold text-white">
                Grade {(signal as any).setup_grade}
              </span>
            )}
          </div>
          <div className="grid grid-cols-2 gap-1.5 text-[11px]">
            <div className="text-text-secondary">
              Qty <span className="text-white font-medium">{(signal as any).quantity}</span>
            </div>
            <div className="text-text-secondary">
              Value <span className="text-white font-medium">₹{Number((signal as any).position_value || 0).toFixed(0)}</span>
            </div>
            <div className="text-text-secondary">
              Risk <span className="text-loss font-medium">₹{Number((signal as any).risk_amount || 0).toFixed(0)}</span>
            </div>
            <div className="text-text-secondary">
              T1 ₹ <span className="text-profit font-medium">{Number((signal as any).reward_t1 || 0).toFixed(0)}</span>
            </div>
          </div>
          {(signal as any).groww_plan && (
            <pre className="mt-2 whitespace-pre-wrap text-[10px] leading-relaxed text-text-muted font-sans">
              {(signal as any).groww_plan}
            </pre>
          )}
        </div>
      )}

      {signal.is_tradeable && (
        <div className="mt-2 rounded-button border border-profit/30 bg-profit/10 px-2.5 py-1.5 text-[11px] text-profit text-center font-medium">
          TRADEABLE SETUP · Execute manually on Groww
        </div>
      )}

      <p className="text-[10px] text-text-dim mt-3 leading-relaxed">{signal.disclaimer}</p>
    </Card>
  );
}

function Level({
  label, value, icon, profit, danger,
}: {
  label: string; value: string; icon?: React.ReactNode; profit?: boolean; danger?: boolean;
}) {
  return (
    <div className="rounded-button border border-border bg-bg-secondary/60 px-2.5 py-2">
      <div className="flex items-center gap-1 text-[10px] text-text-muted uppercase tracking-wider mb-0.5">
        {icon}{label}
      </div>
      <div className={cn(
        'text-sm font-medium tabular-nums',
        profit && 'text-profit',
        danger && 'text-loss',
        !profit && !danger && 'text-white'
      )}>
        {value}
      </div>
    </div>
  );
}
