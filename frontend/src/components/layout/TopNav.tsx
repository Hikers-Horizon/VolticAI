'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Search, Bell, User, Wifi, TrendingUp } from 'lucide-react';
import { api } from '@/lib/api';
import { cn, formatPrice, formatPct, pnlClass } from '@/lib/utils';

type SearchHit = {
  symbol: string;
  type?: string;
  ltp?: number;
  change_percent?: number;
};

export function TopNav() {
  const router = useRouter();
  const [status, setStatus] = useState<{
    status: string;
    is_open: boolean;
    india_vix?: number;
    live?: boolean;
    data_source?: string;
  } | null>(null);
  const [query, setQuery] = useState('');
  const [hits, setHits] = useState<SearchHit[]>([]);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [active, setActive] = useState(0);
  const boxRef = useRef<HTMLDivElement>(null);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    api.marketStatus().then(setStatus).catch(() => {});
    const t = setInterval(() => {
      api.marketStatus().then(setStatus).catch(() => {});
    }, 30000);
    return () => clearInterval(t);
  }, []);

  useEffect(() => {
    const onDoc = (e: MouseEvent) => {
      if (!boxRef.current?.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener('mousedown', onDoc);
    return () => document.removeEventListener('mousedown', onDoc);
  }, []);

  const runSearch = useCallback((q: string) => {
    if (timer.current) clearTimeout(timer.current);
    if (!q.trim()) {
      setHits([]);
      setOpen(false);
      setLoading(false);
      return;
    }
    setLoading(true);
    timer.current = setTimeout(async () => {
      try {
        const d = await api.search(q.trim(), 10);
        setHits(d.results || []);
        setOpen(true);
        setActive(0);
      } catch {
        setHits([]);
      } finally {
        setLoading(false);
      }
    }, 220);
  }, []);

  function go(symbol: string) {
    const sym = symbol.trim().toUpperCase();
    if (!sym) return;
    setQuery(sym);
    setOpen(false);
    router.push(`/signals?symbol=${encodeURIComponent(sym)}`);
  }

  function onKey(e: React.KeyboardEvent<HTMLInputElement>) {
    if (!open || hits.length === 0) {
      if (e.key === 'Enter' && query.trim()) go(query);
      return;
    }
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setActive((i) => Math.min(i + 1, hits.length - 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setActive((i) => Math.max(i - 1, 0));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      go(hits[active]?.symbol || query);
    } else if (e.key === 'Escape') {
      setOpen(false);
    }
  }

  return (
    <header className="sticky top-0 z-30 flex h-14 items-center justify-between border-b border-border bg-bg/80 backdrop-blur-glass px-6">
      {/* Search */}
      <div className="relative w-96" ref={boxRef}>
        <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted z-10" />
        <input
          type="text"
          value={query}
          onChange={(e) => {
            const v = e.target.value.toUpperCase();
            setQuery(v);
            runSearch(v);
          }}
          onFocus={() => hits.length > 0 && setOpen(true)}
          onKeyDown={onKey}
          placeholder="Search RELIANCE, NIFTY, TCS..."
          className="input-field pl-9 h-9 text-sm"
          autoComplete="off"
          spellCheck={false}
        />
        {loading && (
          <span className="absolute right-3 top-1/2 -translate-y-1/2 text-[10px] text-text-muted">
            …
          </span>
        )}
        {open && (
          <div className="absolute left-0 right-0 top-[calc(100%+6px)] z-50 overflow-hidden rounded-card border border-border bg-bg-card shadow-elevated animate-fade-in">
            {hits.length === 0 ? (
              <div className="px-3 py-3 text-xs text-text-muted">No symbols found</div>
            ) : (
              <ul className="max-h-80 overflow-y-auto py-1">
                {hits.map((h, i) => (
                  <li key={h.symbol}>
                    <button
                      type="button"
                      onMouseEnter={() => setActive(i)}
                      onClick={() => go(h.symbol)}
                      className={cn(
                        'flex w-full items-center justify-between px-3 py-2.5 text-left transition-colors',
                        i === active ? 'bg-bg-hover' : 'hover:bg-bg-hover/60'
                      )}
                    >
                      <div className="flex items-center gap-2 min-w-0">
                        <TrendingUp size={13} className="text-text-muted shrink-0" />
                        <div className="min-w-0">
                          <div className="text-sm font-medium truncate">{h.symbol}</div>
                          <div className="text-[10px] text-text-muted uppercase tracking-wider">
                            {h.type || 'EQ'} · NSE
                          </div>
                        </div>
                      </div>
                      <div className="text-right shrink-0 ml-3">
                        {h.ltp != null ? (
                          <>
                            <div className="text-sm tabular-nums">{formatPrice(h.ltp)}</div>
                            {h.change_percent != null && (
                              <div className={cn('text-[11px] tabular-nums', pnlClass(h.change_percent))}>
                                {formatPct(h.change_percent)}
                              </div>
                            )}
                          </>
                        ) : (
                          <span className="text-[11px] text-text-muted">Open</span>
                        )}
                      </div>
                    </button>
                  </li>
                ))}
              </ul>
            )}
            <div className="border-t border-border px-3 py-1.5 text-[10px] text-text-muted">
              ↑↓ navigate · Enter open · Esc close
            </div>
          </div>
        )}
      </div>

      {/* Right cluster */}
      <div className="flex items-center gap-4">
        {/* Market status */}
        <div className="flex items-center gap-2 rounded-button border border-border bg-bg-card px-3 py-1.5">
          <span
            className={cn(
              'h-1.5 w-1.5 rounded-full',
              status?.is_open ? 'bg-profit animate-pulse-soft' : 'bg-text-muted'
            )}
          />
          <span className="text-xs font-medium">
            {status?.status || '—'}
          </span>
          {status?.india_vix != null && (
            <span className="text-xs text-text-muted ml-1">
              VIX {status.india_vix}
            </span>
          )}
        </div>

        {/* Data provider */}
        <div className="flex items-center gap-2 rounded-button border border-border bg-bg-card px-3 py-1.5">
          <Wifi size={12} className={status?.live ? 'text-profit' : 'text-text-muted'} />
          <span className="text-xs text-text-secondary">
            {status?.live ? 'Dhan Live' : 'Dhan Offline'}
          </span>
        </div>

        {/* Notifications */}
        <button className="relative flex h-9 w-9 items-center justify-center rounded-button border border-border hover:bg-bg-hover transition-colors">
          <Bell size={15} className="text-text-secondary" />
          <span className="absolute top-1.5 right-1.5 h-1.5 w-1.5 rounded-full bg-white" />
        </button>

        {/* Profile */}
        <button className="flex h-9 w-9 items-center justify-center rounded-full border border-border bg-bg-card hover:bg-bg-hover transition-colors">
          <User size={15} className="text-text-secondary" />
        </button>
      </div>
    </header>
  );
}
