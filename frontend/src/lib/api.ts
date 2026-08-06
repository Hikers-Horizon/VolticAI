const getApiUrl = () => {
  if (process.env.NEXT_PUBLIC_API_URL) return process.env.NEXT_PUBLIC_API_URL;
  if (typeof window !== 'undefined') {
    return `${window.location.protocol}//${window.location.hostname}:8000`;
  }
  return 'http://localhost:8000';
};

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${getApiUrl()}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    cache: 'no-store',
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Request failed');
  }
  return res.json();
}

export const api = {
  // Market
  marketStatus: () => request<any>('/api/v1/market/status'),
  quote: (symbol: string) => request<any>(`/api/v1/market/quote/${symbol}`),
  quotes: (symbols: string[]) =>
    request<any>(`/api/v1/market/quotes?${symbols.map((s) => `symbols=${s}`).join('&')}`),
  historical: (symbol: string, interval = '5minute') =>
    request<any>(`/api/v1/market/historical/${symbol}?interval=${interval}`),
  topGainers: (limit = 10) => request<any>(`/api/v1/market/top-gainers?limit=${limit}`),
  topLosers: (limit = 10) => request<any>(`/api/v1/market/top-losers?limit=${limit}`),
  explosive: (limit = 15) => request<any>(`/api/v1/market/explosive?limit=${limit}`),
  indices: () => request<any>('/api/v1/market/indices'),
  breadth: () => request<any>('/api/v1/market/breadth'),
  optionsChain: (symbol: string) => request<any>(`/api/v1/market/options-chain/${symbol}`),
  search: (q: string, limit = 12) =>
    request<any>(`/api/v1/market/search?q=${encodeURIComponent(q)}&limit=${limit}`),

  // Signals (fast=true → 8 liquid names for snappy dashboard)
  signals: (tradeableOnly = false, fast = true) =>
    request<any>(`/api/v1/signals/?tradeable_only=${tradeableOnly}&fast=${fast}`),
  analyze: (symbol: string, timeframe = '5minute') =>
    request<any>(`/api/v1/signals/analyze/${symbol}?timeframe=${timeframe}`),
  scan: () => request<any>('/api/v1/signals/scanner/scan'),
  momentumScan: (limit = 8, tradeableOnly = false) =>
    request<any>(
      `/api/v1/signals/scanner/momentum?limit=${limit}&tradeable_only=${tradeableOnly}`
    ),
  optionsSignals: (underlying?: string, limit = 8) =>
    request<any>(
      `/api/v1/signals/scanner/options?${underlying ? `underlying=${underlying}&` : ''}limit=${limit}`
    ),

  // Watchlist
  watchlists: () => request<any>('/api/v1/watchlist/'),
  addToWatchlist: (id: number, symbol: string) =>
    request<any>(`/api/v1/watchlist/${id}/symbols?symbol=${symbol}`, { method: 'POST' }),
  removeFromWatchlist: (id: number, symbol: string) =>
    request<any>(`/api/v1/watchlist/${id}/symbols/${symbol}`, { method: 'DELETE' }),

  // Portfolio
  portfolio: () => request<any>('/api/v1/portfolio/'),
  performance: () => request<any>('/api/v1/portfolio/performance'),

  // Orders disabled
  orders: () => request<any>('/api/v1/orders/'),
  brokers: () => request<any>('/api/v1/orders/brokers'),

  // Settings / Dhan
  dhanStatus: () => request<any>('/api/v1/settings/dhan'),
  setDhan: (body: { client_id: string; access_token: string }) =>
    request<any>('/api/v1/settings/dhan', { method: 'POST', body: JSON.stringify(body) }),
  provider: () => request<any>('/api/v1/market/provider'),
  saveCredentials: (body: any) =>
    request<any>('/api/v1/admin/credentials', { method: 'POST', body: JSON.stringify(body) }),
};

export type Signal = {
  symbol: string;
  action: 'BUY' | 'SELL' | 'WAIT';
  confidence: number;
  entry_price?: number;
  stop_loss?: number;
  target_1?: number;
  target_2?: number;
  target_3?: number;
  risk_reward?: number;
  timeframe: string;
  reason: string;
  is_tradeable: boolean;
  rejection_reasons: string[];
  disclaimer: string;
  publish_text?: string;
  thesis?: string;
  summary?: string;
  history_summary?: string;
  news_bias?: string;
  invalidation?: string;
  quantity?: number;
  capital?: number;
  setup_grade?: string;
  position_value?: number;
  risk_amount?: number;
  reward_t1?: number;
  news?: { title: string; link?: string; bias?: string }[];
  factors?: { name: string; score: number; weight: number; detail: string }[];
};

export type Quote = {
  symbol: string;
  ltp: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  change: number;
  change_percent: number;
  bid?: number;
  ask?: number;
};
