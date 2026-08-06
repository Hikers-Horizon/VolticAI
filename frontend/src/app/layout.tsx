import type { Metadata } from 'next';
import './globals.css';
import { Sidebar } from '@/components/layout/Sidebar';
import { TopNav } from '@/components/layout/TopNav';

export const metadata: Metadata = {
  title: 'Voltic AI — Premium Intraday Trading',
  description: 'AI-powered intraday trading platform for Indian markets',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark" style={{ '--sidebar-width': '220px' } as any}>
      <body className="bg-bg text-white antialiased">
        <Sidebar />
        <div className="min-h-screen flex flex-col transition-all duration-300" style={{ marginLeft: 'var(--sidebar-width, 220px)' }}>
          <TopNav />
          <main className="flex-1 p-6">{children}</main>
        </div>
      </body>
    </html>
  );
}
