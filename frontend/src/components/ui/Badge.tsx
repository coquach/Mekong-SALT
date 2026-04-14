import React from 'react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * Hàm utility để gộp class Tailwind thông minh
 */
function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Các biến thể màu sắc dựa trên Logic của dự án:
 * - CRITICAL: Cảnh báo xâm nhập mặn nghiêm trọng.
 * - OPTIMAL: Độ mặn trong ngưỡng an toàn.
 * - WARNING: Cảnh báo sớm.
 * - INFO: Thông tin hệ thống.
 * - NEUTRAL: Các nhãn thông thường.
 */
type BadgeVariant = 'critical' | 'optimal' | 'warning' | 'info' | 'neutral' | 'cyan';

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant;
  dot?: boolean; // Tùy chọn hiển thị dấu chấm trạng thái bên trong
}

export const Badge = ({ 
  children, 
  variant = 'neutral', 
  dot = false,
  className, 
  ...props 
}: BadgeProps) => {

  const variants = {
    critical: 'bg-red-50 text-mekong-critical border-red-100 shadow-sm shadow-red-100/50',
    optimal: 'bg-mekong-mint/10 text-mekong-mint border-mekong-mint/20 shadow-sm shadow-mekong-mint/10',
    warning: 'bg-amber-50 text-amber-600 border-amber-100 shadow-sm shadow-amber-100/50',
    info: 'bg-blue-50 text-mekong-info border-blue-100 shadow-sm shadow-blue-100/50',
    neutral: 'bg-slate-100 text-mekong-slate border-slate-200 shadow-sm',
    cyan: 'bg-mekong-cyan/10 text-mekong-teal border-mekong-cyan/20 shadow-sm shadow-mekong-cyan/10',
  };

  const dotColors = {
    critical: 'bg-mekong-critical',
    optimal: 'bg-mekong-mint',
    warning: 'bg-amber-500',
    info: 'bg-mekong-info',
    neutral: 'bg-mekong-slate',
    cyan: 'bg-mekong-teal',
  };

  return (
    <span
      className={cn(
        // Cấu trúc nền tảng: Typography Hierarchy cực mạnh
        'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg border',
        'text-[10px] font-black uppercase tracking-[0.15em] leading-none',
        'transition-all duration-300 select-none whitespace-nowrap',
        variants[variant],
        className
      )}
      {...props}
    >
      {dot && (
        <span className={cn('w-1.5 h-1.5 rounded-full animate-pulse', dotColors[variant])} />
      )}
      {children}
    </span>
  );
};