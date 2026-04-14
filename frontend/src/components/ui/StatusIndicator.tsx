import React from 'react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * Utility để gộp class Tailwind gọn gàng
 */
function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Các trạng thái chính của hệ thống Mekong-SALT:
 * - ACTIVE: Hệ thống đang chạy bình thường (Màu Mint).
 * - WARNING: Có dấu hiệu xâm nhập mặn (Màu Amber).
 * - CRITICAL: Xâm nhập mặn vượt ngưỡng (Màu Red).
 * - OFFLINE: Mất kết nối sensor (Màu Slate).
 */
type StatusType = 'active' | 'warning' | 'critical' | 'offline';

interface StatusIndicatorProps extends React.HTMLAttributes<HTMLDivElement> {
  label: string;
  status?: StatusType;
  showPulse?: boolean; // Tùy chọn tắt/mở hiệu ứng lan tỏa
}

export const StatusIndicator = ({
  label,
  status = 'active',
  showPulse = true,
  className,
  ...props
}: StatusIndicatorProps) => {

  // Ánh xạ màu sắc chuẩn Figma cho các trạng thái
  const colors = {
    active: 'bg-mekong-mint',
    warning: 'bg-amber-500',
    critical: 'bg-mekong-critical',
    offline: 'bg-slate-400',
  };

  return (
    <div 
      className={cn('flex items-center gap-2.5 select-none', className)} 
      {...props}
    >
      {/* Container của dấu chấm trạng thái */}
      <div className="relative flex items-center justify-center w-2.5 h-2.5">
        
        {/* 1. Vòng tròn lan tỏa (Pulse effect) - Chỉ hiển thị nếu không phải offline */}
        {showPulse && status !== 'offline' && (
          <span className={cn(
            'absolute inline-flex h-full w-full rounded-full opacity-40 animate-ping',
            colors[status]
          )} />
        )}

        {/* 2. Dấu chấm trung tâm (Solid dot) */}
        <span className={cn(
          'relative inline-flex rounded-full h-2 w-2 shadow-sm border border-white/20',
          colors[status],
          status !== 'offline' && 'animate-pulse' // Hiệu ứng nhịp thở nhẹ cho chấm trung tâm
        )} />
      </div>

      {/* 3. Label văn bản - Typography Hierarchy chuẩn Enterprise */}
      <span className={cn(
        'text-[10px] font-black uppercase tracking-[0.2em] leading-none',
        status === 'offline' ? 'text-slate-400' : 'text-mekong-navy'
      )}>
        {label}
      </span>
    </div>
  );
};