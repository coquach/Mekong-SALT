import React from "react";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// 1. Định nghĩa các giá trị Variant cho phép
type BadgeVariant =
  | "critical"
  | "optimal"
  | "warning"
  | "info"
  | "neutral"
  | "cyan"
  | "navy";

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant;
  dot?: boolean;
}

export const Badge = ({
  children,
  variant = "neutral",
  dot = false,
  className,
  ...props
}: BadgeProps) => {
  // 2. Ép kiểu Record để TypeScript hiểu rằng mọi Key trong BadgeVariant đều phải có Style
  const variants: Record<BadgeVariant, string> = {
    critical:
      "bg-red-50 text-mekong-critical border-red-100 shadow-sm shadow-red-100/50",
    optimal:
      "bg-mekong-mint/10 text-mekong-mint border-mekong-mint/20 shadow-sm shadow-mekong-mint/10",
    warning:
      "bg-amber-50 text-amber-600 border-amber-100 shadow-sm shadow-amber-100/50",
    info: "bg-blue-50 text-mekong-info border-blue-100 shadow-sm shadow-blue-100/50",
    neutral: "bg-slate-100 text-mekong-slate border-slate-200 shadow-sm",
    cyan: "bg-mekong-cyan/10 text-mekong-teal border-mekong-cyan/20 shadow-sm shadow-mekong-cyan/10",
    // ĐẢM BẢO DÒNG NÀY CÓ MẶT:
    navy: "bg-mekong-navy/10 text-mekong-navy border-mekong-navy/20 shadow-sm shadow-mekong-navy/5",
  };

  const dotColors: Record<BadgeVariant, string> = {
    critical: "bg-mekong-critical",
    optimal: "bg-mekong-mint",
    warning: "bg-amber-500",
    info: "bg-mekong-info",
    neutral: "bg-mekong-slate",
    cyan: "bg-mekong-teal",
    navy: "bg-mekong-navy",
  };

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg border",
        "text-[10px] font-black uppercase tracking-[0.15em] leading-none",
        "transition-all duration-300 select-none whitespace-nowrap",
        variants[variant], // TypeScript sẽ không còn báo lỗi any ở đây nữa
        className,
      )}
      {...props}
    >
      {dot && (
        <span
          className={cn(
            "w-1.5 h-1.5 rounded-full animate-pulse",
            dotColors[variant],
          )}
        />
      )}
      {children}
    </span>
  );
};
