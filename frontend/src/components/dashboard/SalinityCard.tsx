import { Droplets, TrendingUp, TrendingDown, Minus, Info } from 'lucide-react';
import { Card } from '../ui/Card';
import { Badge } from '../ui/Badge';

interface SalinityCardProps {
  value: number;
  unit?: string;
  nodeName: string;
  trend?: 'up' | 'down' | 'stable';
  trendValue?: string;
  status?: 'optimal' | 'critical' | 'warning';
  lastUpdated?: string;
}

export const SalinityCard = ({
  value,
  unit = 'g/L',
  nodeName,
  trend = 'stable',
  trendValue,
  status = 'optimal',
  lastUpdated = 'Stable for 4h'
}: SalinityCardProps) => {
  
  // Xác định icon và màu sắc dựa trên xu hướng (trend)
  const TrendIcon = {
    up: TrendingUp,
    down: TrendingDown,
    stable: Minus
  }[trend];

  const trendColor = {
    up: 'text-mekong-critical',
    down: 'text-mekong-mint',
    stable: 'text-mekong-slate'
  }[trend];

  return (
    <Card 
      variant="white" 
      isHoverable 
      className="group flex flex-col justify-between h-full min-h-[220px]"
    >
      {/* 1. Header: Icon & Label */}
      <div className="flex justify-between items-start mb-6">
        <div className={cn(
          "p-3 rounded-2xl transition-all duration-300 group-hover:scale-110 shadow-sm",
          status === 'critical' ? 'bg-red-50 text-mekong-critical' : 'bg-slate-50 text-mekong-teal'
        )}>
          <Droplets size={24} strokeWidth={2.5} />
        </div>
        <div className="text-right">
          <p className="text-[10px] font-black text-mekong-slate uppercase tracking-[0.2em] mb-1">
            {nodeName}
          </p>
          <Badge variant={status}>{status}</Badge>
        </div>
      </div>

      {/* 2. Main Metric Section */}
      <div className="flex flex-col">
        <div className="flex items-baseline gap-2">
          <span className={cn(
            "text-5xl font-black tracking-tighter transition-colors duration-300",
            status === 'critical' ? 'text-mekong-critical' : 'text-mekong-navy'
          )}>
            {value.toFixed(2)}
          </span>
          <span className="text-sm font-bold text-mekong-slate uppercase tracking-widest">
            {unit}
          </span>
        </div>

        {/* Trend Indicator */}
        {trendValue && (
          <div className={cn("flex items-center gap-1 mt-1 font-black text-[10px] uppercase tracking-widest", trendColor)}>
            <TrendIcon size={14} strokeWidth={3} />
            {trendValue}
          </div>
        )}
      </div>

      {/* 3. Footer: Status Message & Time */}
      <div className="mt-8 pt-6 border-t border-slate-50 flex justify-between items-center">
        <div className="flex items-center gap-2">
          <div className={cn(
            "w-2 h-2 rounded-full animate-pulse",
            status === 'critical' ? 'bg-mekong-critical' : 'bg-mekong-mint'
          )} />
          <span className="text-[10px] font-black text-mekong-navy uppercase tracking-tighter">
            {lastUpdated}
          </span>
        </div>
        
        <button className="text-slate-300 hover:text-mekong-teal transition-colors">
          <Info size={14} />
        </button>
      </div>

      {/* Hiệu ứng trang trí nhỏ khi ở trạng thái Critical */}
      {status === 'critical' && (
        <div className="absolute top-0 left-0 w-full h-1 bg-mekong-critical opacity-20" />
      )}
    </Card>
  );
};

// Hàm bổ trợ xử lý class
function cn(...inputs: any[]) {
  return inputs.filter(Boolean).join(' ');
}
