import { Terminal, Download, ChevronRight } from 'lucide-react';

/**
 * REASONING LOG COMPONENT
 * -----------------------
 * - Hiển thị nhật ký suy luận thời gian thực của AI.
 * - Sử dụng Typography Monospace để tạo cảm giác kỹ thuật (Technical feel).
 * - Phân loại các bước xử lý: DATA_INGEST, PREDICTIVE_SYNC, CORE_PROCESS...
 */

interface LogEntry {
  id: string;
  timestamp: string;
  category: 'CORE_PROCESS' | 'DATA_INGEST' | 'PREDICTIVE_SYNC' | 'DECISION_BRANCH';
  message: string;
}

const mockLogs: LogEntry[] = [
  {
    id: '1',
    timestamp: '14:22:10',
    category: 'CORE_PROCESS',
    message: 'Wind speed increased to 6 Bft, accelerating salt wedge intrusion by 12%... adjustment made to closure timing.'
  },
  {
    id: '2',
    timestamp: '14:18:05',
    category: 'DATA_INGEST',
    message: 'Receiving high-res satellite bathymetry. Calculating riverbed friction coefficients for upstream propagation model.'
  },
  {
    id: '3',
    timestamp: '14:15:52',
    category: 'PREDICTIVE_SYNC',
    message: 'Historical patterns from 2016 drought event matched with 94.2% confidence. Adjusting threshold for Gate-09 sensitivity.'
  },
  {
    id: '4',
    timestamp: '14:10:30',
    category: 'DECISION_BRANCH',
    message: 'Gate-12 manual override detected. Re-routing salt flow simulation to account for non-compliant leakage at section Delta-4.'
  }
];

export const ReasoningLog = () => {
  return (
    <div className="bg-white rounded-[32px] p-8 border border-slate-200 shadow-soft flex flex-col h-full animate-in fade-in duration-700">
      
      {/* 1. Header: Tiêu đề và nút Export */}
      <div className="flex justify-between items-center mb-8">
        <div className="flex items-center gap-3">
          <div className="bg-slate-100 p-2 rounded-lg text-mekong-navy">
            <Terminal size={18} />
          </div>
          <h3 className="text-sm font-black text-mekong-navy uppercase tracking-widest">
            Live Reasoning Log
          </h3>
        </div>
        
        <button className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-slate-200 text-[10px] font-black text-mekong-slate hover:text-mekong-teal hover:bg-slate-50 transition-all uppercase tracking-widest">
          <Download size={14} />
          Export Log
        </button>
      </div>

      {/* 2. Log Content: Khu vực danh sách dòng log */}
      <div className="flex-1 space-y-4 overflow-y-auto pr-2 custom-scrollbar">
        {mockLogs.map((log) => (
          <div 
            key={log.id} 
            className="group flex gap-4 p-4 rounded-2xl bg-slate-50 border border-slate-100 hover:border-mekong-teal/20 transition-all"
          >
            {/* Timestamp - Font Mono chuẩn kỹ thuật */}
            <span className="text-[11px] font-mono font-bold text-slate-400 mt-0.5">
              [{log.timestamp}]
            </span>

            <div className="flex-1 space-y-1">
              {/* Category Label */}
              <div className="flex items-center gap-2">
                <span className={`text-[10px] font-mono font-black uppercase tracking-tighter ${
                  log.category === 'CORE_PROCESS' ? 'text-mekong-navy' :
                  log.category === 'DATA_INGEST' ? 'text-mekong-teal' :
                  log.category === 'PREDICTIVE_SYNC' ? 'text-mekong-mint' : 'text-amber-600'
                }`}>
                  {log.category.replace('_', ' ')}:
                </span>
              </div>

              {/* Message - Nội dung suy luận */}
              <p className="text-[11px] font-mono text-slate-600 leading-relaxed group-hover:text-mekong-navy transition-colors">
                {log.message}
              </p>
            </div>

            <ChevronRight size={14} className="text-slate-300 opacity-0 group-hover:opacity-100 transition-opacity mt-1" />
          </div>
        ))}
      </div>

      {/* 3. Footer: Trạng thái dòng chảy dữ liệu */}
      <div className="mt-6 pt-6 border-t border-slate-50 flex justify-between items-center">
        <div className="flex items-center gap-3">
          <div className="flex gap-1">
            <div className="w-1 h-3 bg-mekong-teal rounded-full animate-pulse" />
            <div className="w-1 h-3 bg-mekong-teal/60 rounded-full animate-pulse delay-75" />
            <div className="w-1 h-3 bg-mekong-teal/30 rounded-full animate-pulse delay-150" />
          </div>
          <span className="text-[9px] font-black text-mekong-slate uppercase tracking-widest">
            SALT-Agent Stream: Active
          </span>
        </div>
        <p className="text-[9px] font-bold text-slate-400 italic">
          v4.2.1-stable-engine
        </p>
      </div>
    </div>
  );
};
