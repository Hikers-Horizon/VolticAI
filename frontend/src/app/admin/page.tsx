'use client';

import { useEffect, useState } from 'react';
import { Card, CardHeader } from '@/components/ui/Card';
import { api } from '@/lib/api';
import { Save, Eye, EyeOff, CheckCircle2, XCircle } from 'lucide-react';

type Provider = 'dhan' | 'upstox';

type Credentials = {
  provider: Provider;
  dhan_client_id: string;
  dhan_access_token: string;
  dhan_api_key: string;
  dhan_api_secret: string;
  upstox_api_key: string;
  upstox_api_secret: string;
  upstox_access_token: string;
};

export default function AdminPage() {
  const [provider, setProvider] = useState<Provider>('dhan');
  const [creds, setCreds] = useState<Credentials>({
    provider: 'dhan',
    dhan_client_id: '',
    dhan_access_token: '',
    dhan_api_key: '',
    dhan_api_secret: '',
    upstox_api_key: '',
    upstox_api_secret: '',
    upstox_access_token: '',
  });
  const [show, setShow] = useState<Record<string, boolean>>({});
  const [status, setStatus] = useState<any>(null);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');

  useEffect(() => {
    loadStatus();
  }, []);

  const loadStatus = async () => {
    try {
      const data = await api.provider();
      setStatus(data);
      setProvider(data.provider || 'dhan');
    } catch (error) {
      console.error('Failed to load provider status', error);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    setMessage('');
    try {
      const response = await fetch('http://localhost:8000/api/v1/admin/credentials', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...creds, provider }),
      });
      if (response.ok) {
        setMessage('✓ Credentials saved successfully! Restart backend to apply.');
        setTimeout(() => loadStatus(), 1000);
      } else {
        setMessage('✗ Failed to save credentials');
      }
    } catch (error) {
      setMessage('✗ Error saving credentials');
    } finally {
      setSaving(false);
    }
  };

  const toggleShow = (field: string) => {
    setShow((prev) => ({ ...prev, [field]: !prev[field] }));
  };

  return (
    <div className="space-y-6 animate-slide-up">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Admin Dashboard</h1>
        <p className="text-sm text-text-secondary mt-1">Configure market data providers</p>
      </div>

      {/* Current Status */}
      {status && (
        <Card className="glass p-5">
          <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
            Current Provider Status
            {status.ok ? <CheckCircle2 size={16} className="text-profit" /> : <XCircle size={16} className="text-loss" />}
          </h3>
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div>
              <div className="text-text-muted text-xs mb-1">Provider</div>
              <div className="font-medium uppercase">{status.provider}</div>
            </div>
            <div>
              <div className="text-text-muted text-xs mb-1">Status</div>
              <div className={status.ok ? 'text-profit' : 'text-loss'}>
                {status.ok ? 'Connected' : status.last_error || 'Disconnected'}
              </div>
            </div>
          </div>
        </Card>
      )}

      {/* Provider Selection */}
      <Card>
        <CardHeader title="Select Provider" />
        <div className="p-5 pt-0">
          <div className="flex gap-3">
            <button
              onClick={() => setProvider('dhan')}
              className={`flex-1 px-4 py-3 rounded-button border transition-all ${
                provider === 'dhan'
                  ? 'bg-white text-black border-white'
                  : 'bg-bg-card border-border text-text-secondary hover:border-white/30'
              }`}
            >
              <div className="font-semibold">Dhan</div>
              <div className="text-xs mt-1 opacity-80">HTTP Polling • ₹499/mo</div>
            </button>
            <button
              onClick={() => setProvider('upstox')}
              className={`flex-1 px-4 py-3 rounded-button border transition-all ${
                provider === 'upstox'
                  ? 'bg-white text-black border-white'
                  : 'bg-bg-card border-border text-text-secondary hover:border-white/30'
              }`}
            >
              <div className="font-semibold">Upstox</div>
              <div className="text-xs mt-1 opacity-80">WebSocket • Free</div>
            </button>
          </div>
        </div>
      </Card>

      {/* Credentials Form */}
      <Card>
        <CardHeader title={`${provider === 'dhan' ? 'Dhan' : 'Upstox'} API Credentials`} />
        <div className="p-5 pt-0 space-y-4">
          {provider === 'dhan' && (
            <>
              <InputField label="Client ID" value={creds.dhan_client_id} onChange={(v: string) => setCreds({ ...creds, dhan_client_id: v })} />
              <InputField label="Access Token (JWT)" value={creds.dhan_access_token} onChange={(v: string) => setCreds({ ...creds, dhan_access_token: v })} show={show.dhan_token} onToggle={() => toggleShow('dhan_token')} secret />
              <InputField label="API Key" value={creds.dhan_api_key} onChange={(v: string) => setCreds({ ...creds, dhan_api_key: v })} />
              <InputField label="API Secret" value={creds.dhan_api_secret} onChange={(v: string) => setCreds({ ...creds, dhan_api_secret: v })} show={show.dhan_secret} onToggle={() => toggleShow('dhan_secret')} secret />
            </>
          )}
          {provider === 'upstox' && (
            <>
              <InputField label="API Key" value={creds.upstox_api_key} onChange={(v: string) => setCreds({ ...creds, upstox_api_key: v })} />
              <InputField label="API Secret" value={creds.upstox_api_secret} onChange={(v: string) => setCreds({ ...creds, upstox_api_secret: v })} show={show.upstox_secret} onToggle={() => toggleShow('upstox_secret')} secret />
              <InputField label="Access Token" value={creds.upstox_access_token} onChange={(v: string) => setCreds({ ...creds, upstox_access_token: v })} show={show.upstox_token} onToggle={() => toggleShow('upstox_token')} secret />
            </>
          )}
        </div>
      </Card>

      {message && <div className={`text-sm px-4 py-2 rounded-button ${message.startsWith('✓') ? 'bg-profit/10 text-profit' : 'bg-loss/10 text-loss'}`}>{message}</div>}

      <button onClick={handleSave} disabled={saving} className="btn-primary flex items-center gap-2">
        <Save size={16} />
        {saving ? 'Saving...' : 'Save Credentials'}
      </button>
    </div>
  );
}

function InputField({ label, value, onChange, secret, show, onToggle }: any) {
  return (
    <div>
      <label className="text-xs text-text-muted mb-1.5 block">{label}</label>
      <div className="relative">
        <input type={secret && !show ? 'password' : 'text'} value={value} onChange={(e) => onChange(e.target.value)} className="input-field w-full pr-10" placeholder={`Enter ${label.toLowerCase()}`} />
        {secret && (
          <button type="button" onClick={onToggle} className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted hover:text-white">
            {show ? <EyeOff size={16} /> : <Eye size={16} />}
          </button>
        )}
      </div>
    </div>
  );
}
