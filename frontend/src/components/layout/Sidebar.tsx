'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import {
  LayoutDashboard,
  Star,
  Radar,
  Sparkles,
  GitBranch,
  BookOpen,
  FlaskConical,
  Settings,
} from 'lucide-react';

const NAV = [
  { href: '/', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/watchlist', label: 'Watchlist', icon: Star },
  { href: '/scanner', label: 'Market Scanner', icon: Radar },
  { href: '/signals', label: 'AI Signals', icon: Sparkles },
  { href: '/options', label: 'Options Chain', icon: GitBranch },
  { href: '/journal', label: 'Journal', icon: BookOpen },
  { href: '/backtesting', label: 'Backtesting', icon: FlaskConical },
  { href: '/settings', label: 'Settings', icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="fixed left-0 top-0 z-40 flex h-screen w-[220px] flex-col border-r border-border bg-bg-secondary">
      {/* Logo */}
      <div className="flex h-14 items-center gap-2.5 px-5 border-b border-border">
        <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-white">
          <span className="text-xs font-bold text-black">AI</span>
        </div>
        <div>
          <div className="text-sm font-semibold tracking-tight">TradeAI</div>
          <div className="text-[10px] text-text-muted tracking-wider uppercase">Intraday</div>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto py-4 px-3 space-y-0.5">
        {NAV.map(({ href, label, icon: Icon }) => {
          const active = pathname === href || (href !== '/' && pathname.startsWith(href));
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                'flex items-center gap-3 rounded-button px-3 py-2.5 text-[13px] font-medium transition-all duration-150',
                active
                  ? 'bg-white text-black'
                  : 'text-text-secondary hover:bg-bg-hover hover:text-white'
              )}
            >
              <Icon size={16} strokeWidth={active ? 2.2 : 1.8} />
              {label}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="border-t border-border p-4">
        <div className="rounded-button border border-border bg-bg-card px-3 py-2.5">
          <div className="text-[10px] uppercase tracking-wider text-text-muted mb-1">Mode</div>
          <div className="flex items-center gap-2">
            <span className="h-1.5 w-1.5 rounded-full bg-profit animate-pulse-soft" />
            <span className="text-xs font-medium text-white">Live Data · Analysis</span>
          </div>
          <div className="text-[10px] text-text-muted mt-1">No buy / sell</div>
        </div>
      </div>
    </aside>
  );
}
