import type { ReactNode } from "react";
import { useLocation } from "react-router-dom";
import { ChevronRight } from "lucide-react";

import { buildBreadcrumb, getRouteMeta } from "../../lib/navigation";
import { RealtimeBadge } from "./RealtimeBadge";

interface PageHeadingProps {
  className?: string;
  trailing?: ReactNode;
}

export function PageHeading({ className = "", trailing }: PageHeadingProps) {
  const { pathname } = useLocation();
  const route = getRouteMeta(pathname);
  const breadcrumb = buildBreadcrumb(pathname);

  return (
    <section className={`space-y-4 ${className}`.trim()}>
      <div className="relative overflow-hidden rounded-card border border-slate-200 bg-white p-5 shadow-soft md:p-6">
        <div className="pointer-events-none absolute -right-16 -top-14 h-40 w-40 rounded-full bg-mekong-cyan/20 blur-3xl" />
        <div className="pointer-events-none absolute -bottom-20 left-24 h-40 w-40 rounded-full bg-mekong-teal/15 blur-3xl" />

        <div className="relative z-10 flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
          <div className="space-y-2">
            <nav
              aria-label="Điều hướng trang"
              className="flex flex-wrap items-center gap-1 text-[10px] font-black uppercase tracking-[0.18em] text-slate-400"
            >
              {breadcrumb.map((label, index) => (
                <span key={`${label}-${index}`} className="inline-flex items-center gap-1">
                  {index > 0 ? <ChevronRight size={12} /> : null}
                  {label}
                </span>
              ))}
            </nav>
            <h1 className="text-2xl font-black tracking-tight text-mekong-navy md:text-4xl">
              {route.title}
            </h1>
            <p className="max-w-3xl text-sm font-medium text-slate-600 md:text-base">
              {route.subtitle}
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <RealtimeBadge mode={route.realtimeMode} />
            {trailing}
          </div>
        </div>
      </div>
    </section>
  );
}
