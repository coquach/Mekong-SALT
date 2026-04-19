import React from 'react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * Utility để gộp class Tailwind chuẩn xác, tránh xung đột CSS
 */
function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'white' | 'navy' | 'glass' | 'outline';
  padding?: 'none' | 'sm' | 'md' | 'lg';
  isHoverable?: boolean;
}

/**
 * THÀNH PHẦN CARD CHÍNH (ROOT)
 */
const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ className, variant = 'white', padding = 'md', isHoverable = false, children, ...props }, ref) => {
    
    // Định nghĩa phong cách dựa trên 7 hình ảnh thiết kế
    const variants = {
      // Card tiêu chuẩn trên Dashboard
      white: 'bg-white border border-slate-100 shadow-[0_4px_20px_-2px_rgba(0,0,0,0.05)]',
      
      // Card cho planning trace & avoided damages (Màu tối, sâu)
      navy: 'bg-[#00203F] text-white border border-white/5 shadow-2xl overflow-hidden relative',
      
      // Card cho các lớp phủ trên bản đồ (Glassmorphism)
      glass: 'bg-white/80 backdrop-blur-xl border border-white/40 shadow-[0_8px_32px_0_rgba(0,0,0,0.1)]',
      
      // Card cho các vùng chờ hoặc placeholder
      outline: 'bg-transparent border-2 border-slate-200 border-dashed',
    };

    const paddings = {
      none: 'p-0',
      sm: 'p-4',
      md: 'p-6 lg:p-8', // Responsive padding cho desktop
      lg: 'p-10 lg:p-12',
    };

    return (
      <div
        ref={ref}
        className={cn(
          // Bo góc lớn (32px) là đặc trưng của thiết kế này
          'rounded-[24px] lg:rounded-[32px] transition-all duration-300 relative',
          variants[variant],
          paddings[padding],
          isHoverable && 'hover:translate-y-[-6px] hover:shadow-xl cursor-pointer active:scale-[0.98]',
          className
        )}
        {...props}
      >
        {/* Hiệu ứng ánh sáng xanh (Glow) cho variant Navy - Đặc trưng AI Tech */}
        {variant === 'navy' && (
          <div className="absolute -right-20 -bottom-20 w-64 h-64 bg-[#75E7FE]/10 rounded-full blur-[80px] pointer-events-none" />
        )}
        
        {children}
      </div>
    );
  }
);
Card.displayName = 'Card';

/**
 * THÀNH PHẦN CARD HEADER (Tiêu đề và icon)
 */
const CardHeader = ({ className, children, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
  <div className={cn('flex items-center justify-between mb-6', className)} {...props}>
    {children}
  </div>
);

/**
 * THÀNH PHẦN CARD TITLE
 */
const CardTitle = ({ className, children, ...props }: React.HTMLAttributes<HTMLHeadingElement>) => (
  <h3
    className={cn(
      // Font Black (900), viết hoa, tracking chặt (tighter)
      'text-lg font-black text-inherit leading-none uppercase tracking-tighter',
      className
    )}
    {...props}
  >
    {children}
  </h3>
);

/**
 * THÀNH PHẦN CARD DESCRIPTION (Nhãn phụ)
 */
const CardDescription = ({ className, children, ...props }: React.HTMLAttributes<HTMLParagraphElement>) => (
  <p
    className={cn(
      // Font cực nhỏ, đậm, giãn chữ (widest) - Phong cách Enterprise
      'text-[10px] font-black text-slate-500 uppercase tracking-widest opacity-80',
      className
    )}
    {...props}
  >
    {children}
  </p>
);

/**
 * THÀNH PHẦN CARD CONTENT (Vùng chứa dữ liệu chính)
 */
const CardContent = ({ className, children, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
  <div className={cn('relative z-10', className)} {...props}>
    {children}
  </div>
);

/**
 * THÀNH PHẦN CARD FOOTER (Trạng thái, thời gian)
 */
const CardFooter = ({ className, children, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
  <div 
    className={cn(
      'flex items-center pt-6 mt-6 border-t border-slate-50/10', 
      className
    )} 
    {...props}
  >
    {children}
  </div>
);

export { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter };
