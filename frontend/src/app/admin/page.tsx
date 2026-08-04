'use client';

import { useEffect, useState } from 'react';
import { Card, CardHeader } from '@/components/ui/Card';
import { api } from '@/lib/api';
import { Save, Eye, EyeOff, CheckCircle2, XCircle, Lock } from 'lucide-react';

type Provider = 'dhan' | 'upstox' | 'angelone';

type Credentials = {
  provider: Provider;
  dhan_client_id: string;
  dhan_access_token: string;
  dhan_api_key: string;
  dhan_api_secret: string;
  upstox_api_key: string;
  upstox_api_secret: string;
  upstox_access_token: string;
  angelone_api_key: string;
  angelone_client_code: string;
  angelone_access_token: string;
};

// Simple admin password (in production, use proper auth)
const ADMIN_PASSWORD = 'volticai2026'; // Change this to your secure password

export default function AdminPage() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [password, setPassword] = useState('');
  const [authError, setAuthError] = useState('');
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
    angelone_api_key: '',
    angelone_client_code: '',
    angelone_access_token: '',
  });
  const [show, setShow] = useState<Record<string, boolean>>({});
  const [status, setStatus] = useState<any>(null);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');
  const [angelPassword, setAngelPassword] = useState('');
  const [angelTotp, setAngelTotp] = useState('');
  const [generatingToken, setGeneratingToken] = useState(false);
  const [tokenError, setTokenError] = useState('');
  const [tokenSuccess, setTokenSuccess] = useState('');

  const handleLogin = () => {
    if (password === ADMIN_PASSWORD) {
      setIsAuthenticated(true);
      setAuthError('');
      localStorage.setItem('admin_auth', 'true');
    } else {
      setAuthError('Invalid password');
    }
  };

  useEffect(() => {
    // Check if already authenticated
    const auth = localStorage.getItem('admin_auth');
    if (auth === 'true') {
      setIsAuthenticated(true);
    }
  }, []);

  useEffect(() => {
    if (isAuthenticated) {
      loadStatus();
    }
  }, [isAuthenticated]);

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

  const generateAngelToken = async () => {
    setGeneratingToken(true);
    setTokenError('');
    setTokenSuccess('');

    try {
      const response = await fetch('https://apiconnect.angelbroking.com/rest/auth/angelbroking/user/v1/loginByPassword', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
          'X-UserType': 'USER',
          'X-SourceID': 'WEB',
          'X-ClientLocalIP': '0.0.0.0',
          'X-ClientPublicIP': '0.0.0.0',
          'X-MACAddress': '00:00:00:00:00:00',
          'X-PrivateKey': creds.angelone_api_key,
        },
        body: JSON.stringify({
          clientcode: creds.angelone_client_code,
          password: angelPassword,
          totp: angelTotp,
        }),
      });

      const data = await response.json();

      if (data.status && data.data && data.data.jwtToken) {
        setCreds({ ...creds, angelone_access_token: data.data.jwtToken });
        setTokenSuccess('✓ Token generated successfully!');
        setAngelPassword('');
        setAngelTotp('');
      } else {
        setTokenError(data.message || 'Failed to generate token');
      }
    } catch (error: any) {
      setTokenError('Error: ' + (error.message || 'Network error'));
    } finally {
      setGeneratingToken(false);
    }
  };

  // Login screen
  if (!isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Card className="glass p-8 w-full max-w-md">
          <div className="text-center mb-6">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-white/10 mb-4">
              <Lock size={32} className="text-white" />
            </div>
            <h1 className="text-2xl font-semibold tracking-tight">Admin Access</h1>
            <p className="text-sm text-text-secondary mt-1">Enter password to continue</p>
          </div>
          <div className="space-y-4">
            <div>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleLogin()}
                placeholder="Enter admin password"
                className="input-field w-full"
                autoFocus
              />
              {authError && <p className="text-xs text-loss mt-2">{authError}</p>}
            </div>
            <button onClick={handleLogin} className="btn-primary w-full">
              Unlock Dashboard
            </button>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-slide-up">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Admin Dashboard</h1>
          <p className="text-sm text-text-secondary mt-1">Configure market data providers</p>
        </div>
        <button
          onClick={() => {
            setIsAuthenticated(false);
            localStorage.removeItem('admin_auth');
          }}
          className="text-xs text-text-muted hover:text-white"
        >
          Logout
        </button>
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
          <div className="grid grid-cols-3 gap-3">
            <button
              onClick={() => setProvider('dhan')}
              className={`px-4 py-3 rounded-button border transition-all ${
                provider === 'dhan'
                  ? 'bg-white text-black border-white'
                  : 'bg-bg-card border-border text-text-secondary hover:border-white/30'
              }`}
            >
              <div className="font-semibold">Dhan</div>
              <div className="text-xs mt-1 opacity-80">HTTP • ₹499/mo</div>
            </button>
            <button
              onClick={() => setProvider('upstox')}
              className={`px-4 py-3 rounded-button border transition-all ${
                provider === 'upstox'
                  ? 'bg-white text-black border-white'
                  : 'bg-bg-card border-border text-text-secondary hover:border-white/30'
              }`}
            >
              <div className="font-semibold">Upstox</div>
              <div className="text-xs mt-1 opacity-80">WebSocket • Free</div>
            </button>
            <button
              onClick={() => setProvider('angelone')}
              className={`px-4 py-3 rounded-button border transition-all ${
                provider === 'angelone'
                  ? 'bg-white text-black border-white'
                  : 'bg-bg-card border-border text-text-secondary hover:border-white/30'
              }`}
            >
              <div className="font-semibold">Angel One</div>
              <div className="text-xs mt-1 opacity-80">WebSocket • Free</div>
            </button>
          </div>
        </div>
      </Card>

      {/* Credentials Form */}
      <Card>
        <CardHeader title={`${provider === 'dhan' ? 'Dhan' : provider === 'upstox' ? 'Upstox' : 'Angel One'} API Credentials`} />
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
          {provider === 'angelone' && (
            <>
              <InputField label="API Key" value={creds.angelone_api_key} onChange={(v: string) => setCreds({ ...creds, angelone_api_key: v })} placeholder="eS47mncq" />
              <InputField label="Client Code" value={creds.angelone_client_code} onChange={(v: string) => setCreds({ ...creds, angelone_client_code: v })} placeholder="Your Angel One Client ID (e.g., A123456)" />

              <div className="border border-border rounded-button p-4 bg-bg-hover space-y-3">
                <div className="text-sm font-medium">Generate Access Token</div>
                <InputField label="Password" value={angelPassword} onChange={setAngelPassword} secret placeholder="Your Angel One password" />
                <InputField label="TOTP (6-digit code)" value={angelTotp} onChange={setAngelTotp} placeholder="From Google Authenticator" />
                <button
                  onClick={generateAngelToken}
                  disabled={!creds.angelone_api_key || !creds.angelone_client_code || !angelPassword || !angelTotp || generatingToken}
                  className="btn-secondary w-full text-sm"
                >
                  {generatingToken ? 'Generating Token...' : 'Generate Access Token'}
                </button>
                {tokenError && <div className="text-xs text-loss">{tokenError}</div>}
                {tokenSuccess && <div className="text-xs text-profit">{tokenSuccess}</div>}
              </div>

              <InputField label="Access Token (Auto-generated above)" value={creds.angelone_access_token} onChange={(v: string) => setCreds({ ...creds, angelone_access_token: v })} show={show.angel_token} onToggle={() => toggleShow('angel_token')} secret placeholder="Will be auto-filled after generation" />

              <div className="text-xs text-text-muted bg-bg-card/60 p-3 rounded-button">
                <strong className="text-white">How it works:</strong><br/>
                1. Enter your Angel One login credentials above<br/>
                2. Click "Generate Access Token"<br/>
                3. Token will be auto-filled and saved<br/>
                4. Keep your TOTP app ready (token expires daily)
              </div>
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
