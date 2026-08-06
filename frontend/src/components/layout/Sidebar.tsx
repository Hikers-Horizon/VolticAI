'use client';

import { useState } from 'react';
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
  ShieldCheck,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';

const NAV = [
  { href: '/', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/watchlist', label: 'Watchlist', icon: Star },
  { href: '/scanner', label: 'Market Scanner', icon: Radar },
  { href: '/signals', label: 'AI Signals', icon: Sparkles },
  { href: '/options', label: 'Options Chain', icon: GitBranch },
  { href: '/journal', label: 'Journal', icon: BookOpen },
  { href: '/backtesting', label: 'Backtesting', icon: FlaskConical },
  { href: '/admin', label: 'Admin', icon: ShieldCheck },
  { href: '/settings', label: 'Settings', icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);

  // Update CSS variable for main content margin
  if (typeof document !== 'undefined') {
    document.documentElement.style.setProperty('--sidebar-width', collapsed ? '60px' : '220px');
  }

  return (
    <aside className={cn(
      "fixed left-0 top-0 z-40 flex h-screen flex-col border-r border-border bg-bg-secondary transition-all duration-300",
      collapsed ? "w-[60px]" : "w-[220px]"
    )}>
      {/* Logo */}
      <div className="flex h-14 items-center gap-2.5 px-5 border-b border-border relative">
        {!collapsed && (
          <>
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-white">
              <span className="text-xs font-bold text-black">AI</span>
            </div>
            <div>
              <div className="text-sm font-semibold tracking-tight">TradeAI</div>
              <div className="text-[10px] text-text-muted tracking-wider uppercase">Intraday</div>
            </div>
          </>
        )}
        {collapsed && (
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-white mx-auto">
            <span className="text-xs font-bold text-black">AI</span>
          </div>
        )}

        {/* Toggle Button */}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className={cn(
            "absolute -right-3 top-1/2 -translate-y-1/2 h-6 w-6 rounded-full border border-border bg-bg-secondary hover:bg-bg-hover flex items-center justify-center transition-colors",
            "hover:border-white/20"
          )}
        >
          {collapsed ? <ChevronRight size={14} /> : <ChevronLeft size={14} />}
        </button>
      </div>

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto py-4 px-3 space-y-0.5">
        {NAV.map(({ href, label, icon: Icon }) => {
          const active = pathname === href || (href !== '/' && pathname.startsWith(href));
          return (
            <Link
              key={href}
              href={href}
              title={collapsed ? label : undefined}
              className={cn(
                'flex items-center gap-3 rounded-button px-3 py-2.5 text-[13px] font-medium transition-all duration-150',
                active
                  ? 'bg-white text-black'
                  : 'text-text-secondary hover:bg-bg-hover hover:text-white',
                collapsed && 'justify-center'
              )}
            >
              <Icon size={16} strokeWidth={active ? 2.2 : 1.8} />
              {!collapsed && label}
            </Link>
          );
        })}
      </nav>


    </aside>
  );
}
