import { cn } from '@/lib/utils';

const variants = {
  default: 'bg-white/10 text-white border-white/10',
  buy: 'bg-profit/15 text-profit border-profit/25',
  sell: 'bg-loss/15 text-loss border-loss/25',
  wait: 'bg-white/5 text-text-secondary border-border',
  outline: 'bg-transparent text-text-secondary border-border',
};

export function Badge({
  children,
  variant = 'default',
  className,
}: {
  children: React.ReactNode;
  variant?: keyof typeof variants;
  className?: string;
}) {
  return (
    <span
      className={cn(
        'inline-flex items-center px-2 py-0.5 text-[11px] font-semibold tracking-wider uppercase rounded-badge border',
        variants[variant],
        className
      )}
    >
      {children}
    </span>
  );
}
