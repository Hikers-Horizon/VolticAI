'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { Card, CardHeader } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';

export default function SettingsPage() {
  const [clientId, setClientId] = useState('');
  const [token, setToken] = useState('');
  const [status, setStatus] = useState<any>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [sample, setSample] = useState<any>(null);

  const refresh = () =>
    api
      .dhanStatus()
      .then((s) => {
        setStatus(s);
        if (s?.client_id && !clientId) setClientId(String(s.client_id));
      })
      .catch(() => {});

  useEffect(() => {
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function connect() {
    setLoading(true);
    setMsg(null);
    setSample(null);
    try {
      const res = await api.setDhan({ client_id: clientId, access_token: token });
      setMsg(res.message);
      if (res.sample) setSample(res.sample);
      refresh();
    } catch (e: any) {
      setMsg(e.message || 'Failed');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6 animate-slide-up max-w-2xl">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Settings</h1>
        <p className="text-sm text-text-secondary mt-1">
          Live Dhan Data API · Analysis only
        </p>
      </div>

      <div className="rounded-card border border-border bg-bg-card/60 px-4 py-3 text-xs text-text-secondary leading-relaxed">
        <strong className="text-white">No trading.</strong> Never places buy/sell
        orders. Live Dhan data and AI analysis only. Recommendations are probabilistic.
      </div>

      <Card>
        <CardHeader
          title="Dhan Live Data"
          subtitle="web.dhan.co → DhanHQ Trading APIs"
          action={
            status?.ok ? (
              <Badge variant="buy">Live</Badge>
            ) : status?.configured ? (
              <Badge variant="sell">Token expired</Badge>
            ) : (
              <Badge variant="wait">Not connected</Badge>
            )
          }
        />
        <div className="space-y-3">
          {status?.blocked && (
            <div className="text-xs text-warning border border-warning/30 rounded-button px-3 py-2 leading-relaxed">
              {status.blocked}
              <div className="text-text-muted mt-1">
                Open web.dhan.co → Profile → DhanHQ Trading APIs → Generate access
                token (copy full JWT) → paste below. Tokens last ~24 hours.
              </div>
            </div>
          )}
          <div>
            <label className="text-[10px] uppercase tracking-wider text-text-muted">
              Client ID
            </label>
            <input
              className="input-field mt-1 text-sm font-mono"
              placeholder="Dhan client id (e.g. 1112957731)"
              value={clientId}
              onChange={(e) => setClientId(e.target.value)}
            />
          </div>
          <div>
            <label className="text-[10px] uppercase tracking-wider text-text-muted">
              Access Token (FULL JWT — use copy icon)
            </label>
            <textarea
              className="input-field mt-1 text-sm font-mono min-h-[100px] resize-y"
              placeholder="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9...."
              value={token}
              onChange={(e) => setToken(e.target.value)}
            />
          </div>
          <button
            onClick={connect}
            disabled={loading || !clientId || !token}
            className="btn-primary w-full"
          >
            {loading ? 'Connecting…' : 'Connect Live Data'}
          </button>
          {msg && (
            <div className="text-xs text-text-secondary border border-border rounded-button px-3 py-2">
              {msg}
            </div>
          )}
          {sample && (
            <div className="text-xs text-profit border border-profit/20 rounded-button px-3 py-2">
              Live: {sample.symbol} LTP ₹{sample.ltp}
            </div>
          )}
        </div>
      </Card>
    </div>
  );
}
