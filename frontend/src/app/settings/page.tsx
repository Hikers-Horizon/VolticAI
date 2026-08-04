'use client';

import { useEffect, useState } from 'react';
import { Card, CardHeader } from '@/components/ui/Card';
import { Bell, DollarSign, Clock, TrendingUp, Save } from 'lucide-react';

type Settings = {
  capital: number;
  riskPerTrade: number;
  maxPositions: number;
  autoRefreshInterval: number;
  notifications: boolean;
  soundAlerts: boolean;
  darkMode: boolean;
};

export default function SettingsPage() {
  const [settings, setSettings] = useState<Settings>({
    capital: 10000,
    riskPerTrade: 2,
    maxPositions: 3,
    autoRefreshInterval: 2,
    notifications: true,
    soundAlerts: false,
    darkMode: true,
  });
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    // Load settings from localStorage
    const stored = localStorage.getItem('user_settings');
    if (stored) {
      try {
        setSettings(JSON.parse(stored));
      } catch (e) {
        console.error('Failed to load settings');
      }
    }
  }, []);

  const handleSave = () => {
    localStorage.setItem('user_settings', JSON.stringify(settings));
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  const updateSetting = (key: keyof Settings, value: any) => {
    setSettings({ ...settings, [key]: value });
  };

  return (
    <div className="space-y-6 animate-slide-up max-w-3xl">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Settings</h1>
        <p className="text-sm text-text-secondary mt-1">Customize your trading preferences</p>
      </div>

      {/* Trading Settings */}
      <Card>
        <CardHeader title="Trading Preferences" />
        <div className="p-5 pt-0 space-y-4">
          <div>
            <label className="flex items-center gap-2 text-sm font-medium mb-2">
              <DollarSign size={16} className="text-text-secondary" />
              Trading Capital (₹)
            </label>
            <input
              type="number"
              value={settings.capital}
              onChange={(e) => updateSetting('capital', Number(e.target.value))}
              className="input-field w-full"
              placeholder="10000"
            />
            <p className="text-xs text-text-muted mt-1">Used for position size calculations</p>
          </div>

          <div>
            <label className="flex items-center gap-2 text-sm font-medium mb-2">
              <TrendingUp size={16} className="text-text-secondary" />
              Risk Per Trade (%)
            </label>
            <input
              type="number"
              value={settings.riskPerTrade}
              onChange={(e) => updateSetting('riskPerTrade', Number(e.target.value))}
              className="input-field w-full"
              placeholder="2"
              min="0.5"
              max="5"
              step="0.5"
            />
            <p className="text-xs text-text-muted mt-1">Maximum risk per position (recommended: 1-2%)</p>
          </div>

          <div>
            <label className="flex items-center gap-2 text-sm font-medium mb-2">
              <TrendingUp size={16} className="text-text-secondary" />
              Max Concurrent Positions
            </label>
            <input
              type="number"
              value={settings.maxPositions}
              onChange={(e) => updateSetting('maxPositions', Number(e.target.value))}
              className="input-field w-full"
              placeholder="3"
              min="1"
              max="10"
            />
            <p className="text-xs text-text-muted mt-1">Maximum number of open positions at once</p>
          </div>
        </div>
      </Card>

      {/* Display Settings */}
      <Card>
        <CardHeader title="Display & Notifications" />
        <div className="p-5 pt-0 space-y-4">
          <div>
            <label className="flex items-center gap-2 text-sm font-medium mb-2">
              <Clock size={16} className="text-text-secondary" />
              Auto-Refresh Interval (seconds)
            </label>
            <select
              value={settings.autoRefreshInterval}
              onChange={(e) => updateSetting('autoRefreshInterval', Number(e.target.value))}
              className="input-field w-full"
            >
              <option value="1">1 second (Fast)</option>
              <option value="2">2 seconds (Recommended)</option>
              <option value="3">3 seconds</option>
              <option value="5">5 seconds</option>
              <option value="10">10 seconds</option>
            </select>
            <p className="text-xs text-text-muted mt-1">How often watchlist and dashboard refresh</p>
          </div>

          <div className="flex items-center justify-between py-2">
            <div className="flex items-center gap-2">
              <Bell size={16} className="text-text-secondary" />
              <div>
                <div className="text-sm font-medium">Browser Notifications</div>
                <div className="text-xs text-text-muted">Get alerts for trade signals</div>
              </div>
            </div>
            <button
              onClick={() => updateSetting('notifications', !settings.notifications)}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                settings.notifications ? 'bg-profit' : 'bg-bg-hover'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  settings.notifications ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          </div>

          <div className="flex items-center justify-between py-2">
            <div className="flex items-center gap-2">
              <Bell size={16} className="text-text-secondary" />
              <div>
                <div className="text-sm font-medium">Sound Alerts</div>
                <div className="text-xs text-text-muted">Play sound for important signals</div>
              </div>
            </div>
            <button
              onClick={() => updateSetting('soundAlerts', !settings.soundAlerts)}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                settings.soundAlerts ? 'bg-profit' : 'bg-bg-hover'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  settings.soundAlerts ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          </div>
        </div>
      </Card>

      {/* Save Button */}
      {saved && (
        <div className="text-sm px-4 py-2 rounded-button bg-profit/10 text-profit">
          ✓ Settings saved successfully!
        </div>
      )}

      <button onClick={handleSave} className="btn-primary flex items-center gap-2">
        <Save size={16} />
        Save Settings
      </button>

      {/* Info */}
      <div className="rounded-card border border-border bg-bg-card/60 px-4 py-3 text-xs text-text-secondary leading-relaxed">
        <strong className="text-white">Analysis Only Platform.</strong> Never places buy/sell orders automatically.
        All recommendations are for analysis purposes. Execute trades manually on your broker app.
      </div>
    </div>
  );
}
