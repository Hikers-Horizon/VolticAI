'use client';

import { useState } from 'react';
import { Card, CardHeader } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';

type Entry = {
  id: number;
  title: string;
  symbol?: string;
  notes: string;
  emotion: string;
  rating: number;
  pnl?: number;
  date: string;
};

const EMOTIONS = ['disciplined', 'confident', 'fearful', 'greedy', 'fomo'];

export default function JournalPage() {
  const [entries, setEntries] = useState<Entry[]>([
    {
      id: 1,
      title: 'NIFTY VWAP reclaim long',
      symbol: 'NIFTY',
      notes: 'Waited for retest of VWAP after breakout. Good discipline on SL.',
      emotion: 'disciplined',
      rating: 4,
      pnl: 1250,
      date: new Date().toISOString().slice(0, 10),
    },
  ]);
  const [title, setTitle] = useState('');
  const [notes, setNotes] = useState('');
  const [emotion, setEmotion] = useState('disciplined');
  const [symbol, setSymbol] = useState('');

  function addEntry() {
    if (!title.trim()) return;
    setEntries([
      {
        id: Date.now(),
        title,
        symbol: symbol || undefined,
        notes,
        emotion,
        rating: 3,
        date: new Date().toISOString().slice(0, 10),
      },
      ...entries,
    ]);
    setTitle('');
    setNotes('');
    setSymbol('');
  }

  return (
    <div className="space-y-6 animate-slide-up">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Trading Journal</h1>
        <p className="text-sm text-text-secondary mt-1">
          Track setups, emotions, and lessons
        </p>
      </div>

      <div className="grid grid-cols-12 gap-4">
        <div className="col-span-4">
          <Card>
            <CardHeader title="New Entry" />
            <div className="space-y-3">
              <input
                className="input-field text-sm"
                placeholder="Title"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
              />
              <input
                className="input-field text-sm"
                placeholder="Symbol (optional)"
                value={symbol}
                onChange={(e) => setSymbol(e.target.value.toUpperCase())}
              />
              <textarea
                className="input-field text-sm min-h-[100px] resize-none"
                placeholder="Notes, lessons learned..."
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
              />
              <div>
                <div className="text-[10px] uppercase tracking-wider text-text-muted mb-1.5">
                  Emotion
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {EMOTIONS.map((em) => (
                    <button
                      key={em}
                      onClick={() => setEmotion(em)}
                      className={`px-2.5 py-1 text-[11px] rounded-badge border capitalize transition-colors ${
                        emotion === em
                          ? 'bg-white text-black border-white'
                          : 'border-border text-text-secondary hover:text-white'
                      }`}
                    >
                      {em}
                    </button>
                  ))}
                </div>
              </div>
              <button onClick={addEntry} className="btn-primary w-full text-sm">
                Save Entry
              </button>
            </div>
          </Card>
        </div>

        <div className="col-span-8 space-y-3">
          {entries.map((e) => (
            <Card key={e.id} hover>
              <div className="flex items-start justify-between mb-2">
                <div>
                  <h3 className="text-sm font-medium">{e.title}</h3>
                  <div className="flex items-center gap-2 mt-1">
                    {e.symbol && <Badge>{e.symbol}</Badge>}
                    <Badge variant="outline">{e.emotion}</Badge>
                    <span className="text-[11px] text-text-muted">{e.date}</span>
                  </div>
                </div>
                {e.pnl != null && (
                  <span className={e.pnl >= 0 ? 'text-profit text-sm font-medium' : 'text-loss text-sm font-medium'}>
                    {e.pnl >= 0 ? '+' : ''}₹{e.pnl}
                  </span>
                )}
              </div>
              <p className="text-xs text-text-secondary leading-relaxed">{e.notes}</p>
              <div className="mt-2 flex gap-0.5">
                {Array.from({ length: 5 }).map((_, i) => (
                  <span
                    key={i}
                    className={`text-xs ${i < e.rating ? 'text-white' : 'text-text-dim'}`}
                  >
                    ★
                  </span>
                ))}
              </div>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
}
