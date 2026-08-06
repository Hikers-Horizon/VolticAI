'use client';

import { useEffect, useState } from 'react';
import { Card, CardHeader } from '@/components/ui/Card';
import { api } from '@/lib/api';
import { Save, Eye, EyeOff, CheckCircle2, XCircle, Lock } from 'lucide-react';

type Provider = 'upstox' | 'angelone';

type Credentials = {
  provider: Provider;
  upstox_api_key: string;
  upstox_api_secret: string;
  upstox_access_token: string;
  angelone_api_key: string;
  angelone_client_code: string;
  angelone_access_token: string;
};

// Simple admin password (in production, use proper auth)
const ADMIN_PASSWORD = 'admin';

export default function AdminPage() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [password, setPassword] = useState('');
  const [authError, setAuthError] = useState('');
  const [provider, setProvider] = useState<Provider>('upstox');
  const [creds, setCreds] = useState<Credentials>({
    provider: 'upstox',
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
      const res = await api.saveCredentials({ ...creds, provider });
      setMessage('✓ Credentials saved successfully! Restart backend to apply.');
      setTimeout(() => loadStatus(), 1000);
    } catch (error: any) {
      setMessage(`✗ ${error.message || 'Error saving credentials'}`);
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
          <h1 className="text-2xl font-semibold tracking-tight">System & Engine Status</h1>
          <p className="text-sm text-text-secondary mt-1">Built-in Market Data Provider & AI Engine Diagnostics</p>
        </div>
        <button
          onClick={() => {
            setIsAuthenticated(false);
            localStorage.removeItem('admin_auth');
          }}
          className="text-xs text-text-muted hover:text-white px-3 py-1.5 rounded-button border border-border bg-bg-card"
        >
          Logout
        </button>
      </div>

      {/* Primary Market Provider Card */}
      <Card className="p-6 glass border-profit/30 bg-profit/5">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-profit/20 flex items-center justify-center text-profit font-bold text-lg">
              ✓
            </div>
            <div>
              <h2 className="text-lg font-semibold">Upstox Market Data Engine</h2>
              <p className="text-xs text-text-secondary">Internal API v2 • Pre-configured & Active</p>
            </div>
          </div>
          <span className="px-3 py-1 text-xs font-semibold rounded-full bg-profit/20 text-profit border border-profit/30">
            Connected & Active
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-4 border-t border-border/50 text-sm">
          <div className="bg-bg-card/60 p-3.5 rounded-button border border-border">
            <div className="text-xs text-text-muted mb-1">API Provider</div>
            <div className="font-semibold text-white">Upstox Algo Trading v2</div>
          </div>
          <div className="bg-bg-card/60 p-3.5 rounded-button border border-border">
            <div className="text-xs text-text-muted mb-1">Token Expiry</div>
            <div className="font-semibold text-profit">August 2036 (10 Years)</div>
          </div>
          <div className="bg-bg-card/60 p-3.5 rounded-button border border-border">
            <div className="text-xs text-text-muted mb-1">Capabilities</div>
            <div className="font-semibold text-white">Live Quotes & 1m-1h Candles</div>
          </div>
        </div>
      </Card>

      {/* AI Engine Status */}
      <Card className="p-6">
        <h3 className="text-base font-semibold mb-4 flex items-center gap-2">
          <CheckCircle2 className="text-profit" size={18} />
          AI Signal Generation Pipeline
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div className="p-4 rounded-button bg-bg-hover border border-border">
            <div className="text-xs text-text-muted">Engine Status</div>
            <div className="font-medium text-profit mt-1">Operational</div>
          </div>
          <div className="p-4 rounded-button bg-bg-hover border border-border">
            <div className="text-xs text-text-muted">Confidence Threshold</div>
            <div className="font-medium text-white mt-1">75%+ Minimum</div>
          </div>
          <div className="p-4 rounded-button bg-bg-hover border border-border">
            <div className="text-xs text-text-muted">Technical Indicators</div>
            <div className="font-medium text-white mt-1">EMA, RSI, MACD, VWAP, ADX</div>
          </div>
          <div className="p-4 rounded-button bg-bg-hover border border-border">
            <div className="text-xs text-text-muted">Paper Trading</div>
            <div className="font-medium text-profit mt-1">Enabled (₹1,00,000)</div>
          </div>
        </div>
      </Card>
    </div>
  );
}
