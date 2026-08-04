'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { Card, CardHeader } from '@/components/ui/Card';
import { Skeleton } from '@/components/ui/Skeleton';

export function PortfolioWidget() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .provider()
      .then(setData)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <Card>
        <Skeleton className="h-4 w-24 mb-4" />
        <Skeleton className="h-8 w-32" />
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader title="Data Feed" subtitle="Dhan · Analysis only" />
      <div className="space-y-3">
        <div className="flex items-center gap-2">
          <span
            className={`h-2 w-2 rounded-full ${
              data?.configured ? 'bg-profit' : 'bg-loss'
            }`}
          />
          <span className="text-sm font-medium">
            {data?.configured ? 'Live Dhan Connected' : 'Connect Dhan in Settings'}
          </span>
        </div>
        <p className="text-xs text-text-secondary leading-relaxed">
          No portfolio or orders. Live market data and AI signals only.
        </p>
        <div className="rounded-button border border-border bg-bg-secondary/50 px-2.5 py-2 text-[11px] text-text-muted">
          Mode: live_data_analysis_only · Trading disabled
        </div>
      </div>
    </Card>
  );
}
