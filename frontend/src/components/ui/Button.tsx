import React from 'react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { Loader2 } from 'lucide-react';

/**
 * Utility để gộp class Tailwind gọn gàng
 */
function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Các biến thể Button dựa trên thiết kế:
 * - NAVY: Nút chính của hệ thống.
 * - CYAN: Nút hành động nổi bật (Call to Action).
 * - TEAL: Nút thành công/an toàn.
 * - OUTLINE: Nút phụ.
 * - GHOST: Nút tối giản.
 * - DANGER: Nút cảnh báo/dừng khẩn cấp.
 */
type ButtonVariant = 'navy' | 'cyan' | 'teal' | 'outline' | 'ghost' | 'danger';
type ButtonSize = 'sm' | 'md' | 'lg' | 'icon';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  isLoading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ 
    className, 
    variant = 'navy', 
    size = 'md', 
    isLoading = false, 
    leftIcon, 
    rightIcon, 
    children, 
    disabled, 
    ...props 
  }, ref) => {

    // 1. Cấu trúc nền tảng của Button
    const baseStyles = 'inline-flex items-center justify-center rounded-xl font-black uppercase tracking-[0.15em] transition-all duration-300 active:scale-95 disabled:opacity-50 disabled:pointer-events-none select-none';

    // 2. Định nghĩa các biến thể màu sắc (Variants)
    const variants = {
      navy: 'bg-mekong-navy text-white hover:bg-mekong-deep hover:shadow-lg shadow-mekong-navy/20',
      cyan: 'bg-mekong-cyan text-mekong-navy hover:shadow-xl hover:shadow-mekong-cyan/30 border border-mekong-cyan/50',
      teal: 'bg-mekong-teal text-white hover:bg-opacity-90 shadow-md shadow-mekong-teal/20',
      outline: 'bg-transparent border-2 border-slate-200 text-mekong-navy hover:bg-slate-50 hover:border-slate-300',
      ghost: 'bg-transparent text-mekong-slate hover:bg-slate-100 hover:text-mekong-navy',
      danger: 'bg-mekong-critical text-white hover:bg-red-700 shadow-md shadow-red-200/50',
    };

    // 3. Định nghĩa kích thước (Sizes)
    const sizes = {
      sm: 'px-4 py-2 text-[10px]',
      md: 'px-6 py-3 text-[11px]',
      lg: 'px-10 py-4 text-[13px]',
      icon: 'p-3',
    };

    return (
      <button
        ref={ref}
        disabled={disabled || isLoading}
        className={cn(baseStyles, variants[variant], sizes[size], className)}
        {...props}
      >
        {/* Loading State: Icon xoay mượt mà */}
        {isLoading && <Loader2 size={16} className="mr-2 animate-spin" />}
        
        {/* Left Icon: Nếu có và không đang loading */}
        {!isLoading && leftIcon && <span className="mr-2 opacity-90">{leftIcon}</span>}
        
        {/* Nội dung chữ */}
        <span className="relative z-10">{children}</span>

        {/* Right Icon: Nếu có và không đang loading */}
        {!isLoading && rightIcon && <span className="ml-2 opacity-90">{rightIcon}</span>}
        
        {/* Hiệu ứng Shine nhẹ khi là nút Cyan (Tùy chọn tăng tính AI-Tech) */}
        {variant === 'cyan' && (
          <div className="absolute inset-0 bg-white/10 opacity-0 group-hover:opacity-100 transition-opacity rounded-xl" />
        )}
      </button>
    );
  }
);

Button.displayName = 'Button';