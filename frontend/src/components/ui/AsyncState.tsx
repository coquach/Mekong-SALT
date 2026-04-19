import type { ReactNode } from "react";
import { AlertTriangle, RefreshCcw } from "lucide-react";

import { Button } from "./Button";

interface InlineErrorProps {
  message: string;
  title?: string;
  onRetry?: () => void;
}

export function InlineError({ message, title = "Không thể tải dữ liệu", onRetry }: InlineErrorProps) {
  return (
    <div
      className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-red-900"
      role="alert"
      aria-live="polite"
    >
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <p className="text-xs font-black uppercase tracking-[0.16em] text-red-700">{title}</p>
          <p className="mt-1 text-sm font-semibold leading-relaxed">{message}</p>
        </div>
        {onRetry ? (
          <Button
            variant="outline"
            className="h-9 rounded-xl border-red-200 bg-white px-3 text-[10px] text-red-700 hover:bg-red-100"
            onClick={onRetry}
          >
            <RefreshCcw size={14} />
            Thử lại
          </Button>
        ) : null}
      </div>
    </div>
  );
}

interface EmptyStateProps {
  title: string;
  description: string;
  actionLabel?: string;
  onAction?: () => void;
}

export function EmptyState({ title, description, actionLabel, onAction }: EmptyStateProps) {
  return (
    <div className="rounded-3xl border border-dashed border-slate-300 bg-slate-50/70 p-6 text-center">
      <div className="mx-auto flex h-11 w-11 items-center justify-center rounded-2xl bg-white text-slate-500 shadow-sm">
        <AlertTriangle size={18} />
      </div>
      <p className="mt-3 text-sm font-black text-mekong-navy">{title}</p>
      <p className="mt-2 text-sm font-medium leading-relaxed text-slate-500">{description}</p>
      {actionLabel && onAction ? (
        <Button
          variant="outline"
          className="mt-4 h-10 rounded-xl border-slate-200 bg-white px-4 text-[10px]"
          onClick={onAction}
        >
          {actionLabel}
        </Button>
      ) : null}
    </div>
  );
}

interface SkeletonBlockProps {
  className?: string;
}

export function SkeletonBlock({ className = "" }: SkeletonBlockProps) {
  return <div className={`animate-pulse rounded-2xl bg-slate-200/80 ${className}`.trim()} />;
}

interface SkeletonCardsProps {
  count?: number;
}

export function SkeletonCards({ count = 3 }: SkeletonCardsProps) {
  const items = Array.from({ length: count }, (_, index) => index);
  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
      {items.map((item) => (
        <div key={item} className="rounded-3xl border border-slate-200 bg-white p-5 shadow-soft">
          <SkeletonBlock className="h-3 w-24" />
          <SkeletonBlock className="mt-4 h-10 w-2/3" />
          <SkeletonBlock className="mt-6 h-3 w-full" />
        </div>
      ))}
    </div>
  );
}

interface SectionStateProps {
  loading: boolean;
  error: string | null;
  onRetry?: () => void;
  skeleton?: ReactNode;
  children: ReactNode;
}

export function SectionState({ loading, error, onRetry, skeleton, children }: SectionStateProps) {
  if (loading) {
    return <>{skeleton ?? <SkeletonCards />}</>;
  }
  if (error) {
    return <InlineError message={error} onRetry={onRetry} />;
  }
  return <>{children}</>;
}
