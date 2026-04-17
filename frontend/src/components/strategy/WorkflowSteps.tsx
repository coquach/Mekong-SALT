import React from 'react';
import { 
  Database, 
  LineChart, 
  Settings2, 
  Zap, 
  RotateCcw, 
  CheckCircle2,
  Info
} from 'lucide-react';

/**
 * WORKFLOW STEPS COMPONENT
 * ------------------------
 * - Hiển thị quy trình 5 bước của SALT-Agent.
 * - Trạng thái: COMPLETED, ACTIVE NOW, QUEUED, PENDING.
 * - Tích hợp khung thông tin chi tiết cho bước đang hoạt động.
 */

interface Step {
  id: number;
  label: string;
  status: 'COMPLETED' | 'ACTIVE' | 'QUEUED' | 'PENDING';
  icon: React.ElementType;
}

const steps: Step[] = [
  { id: 1, label: 'Data Acquisition', status: 'COMPLETED', icon: Database },
  { id: 2, label: 'Prediction', status: 'COMPLETED', icon: LineChart },
  { id: 3, label: 'Mitigation', status: 'ACTIVE', icon: Settings2 },
  { id: 4, label: 'Execution', status: 'QUEUED', icon: Zap },
  { id: 5, label: 'Feedback Loop', status: 'PENDING', icon: RotateCcw },
];

export const WorkflowSteps = () => {
  return (
    <div className="bg-white rounded-[32px] p-8 lg:p-10 border border-slate-200 shadow-soft relative overflow-hidden">
      
      {/* Header của Workflow */}
      <div className="flex justify-between items-center mb-16">
        <h3 className="text-sm font-black text-mekong-navy uppercase tracking-widest">
          Current Strategy Workflow
        </h3>
        <span className="text-[10px] font-black px-3 py-1 bg-mekong-cyan/10 text-mekong-teal rounded-full border border-mekong-cyan/20 uppercase tracking-widest">
          Goal-Driven Planning
        </span>
      </div>

      {/* Workflow Visualization */}
      <div className="relative flex justify-between items-start px-4">
        
        {/* Đường kẻ kết nối (Connecting Line) */}
        <div className="absolute top-8 left-10 right-10 h-0.5 bg-slate-100 -z-0" />
        <div 
          className="absolute top-8 left-10 h-0.5 bg-mekong-teal transition-all duration-1000 -z-0" 
          style={{ width: '50%' }} // Chạy đến bước thứ 3 (Active)
        />

        {steps.map((step) => {
          const isActive = step.status === 'ACTIVE';
          const isCompleted = step.status === 'COMPLETED';
          
          return (
            <div key={step.id} className="relative z-10 flex flex-col items-center group w-32">
              {/* Icon Container */}
              <div className={`
                w-16 h-16 rounded-[20px] flex items-center justify-center transition-all duration-500 shadow-sm
                ${isActive ? 'bg-mekong-cyan text-mekong-navy scale-110 shadow-lg shadow-mekong-cyan/30 ring-4 ring-mekong-cyan/10' : 
                  isCompleted ? 'bg-mekong-mint/10 text-mekong-mint border border-mekong-mint/20' : 
                  'bg-slate-50 text-slate-300 border border-slate-100'}
              `}>
                <step.icon size={28} strokeWidth={isActive ? 2.5 : 2} />
                
                {/* Checkmark cho bước đã hoàn thành */}
                {isCompleted && (
                  <div className="absolute -top-1 -right-1 bg-white rounded-full">
                    <CheckCircle2 size={18} className="text-mekong-mint fill-white" />
                  </div>
                )}
              </div>

              {/* Text Labels */}
              <div className="mt-6 text-center">
                <p className={`text-[11px] font-black uppercase tracking-tighter mb-1 transition-colors ${
                  isActive ? 'text-mekong-navy' : isCompleted ? 'text-mekong-slate' : 'text-slate-300'
                }`}>
                  {step.label}
                </p>
                <p className={`text-[9px] font-bold uppercase tracking-widest transition-colors ${
                  isActive ? 'text-mekong-teal animate-pulse' : 
                  isCompleted ? 'text-mekong-mint' : 'text-slate-300'
                }`}>
                  {step.status === 'ACTIVE' ? 'Active Now' : step.status.toLowerCase()}
                </p>
              </div>
            </div>
          );
        })}
      </div>

      {/* 3. Chi tiết bước Active (Contextual Info Box) */}
      <div className="mt-16 p-6 bg-cyan-50/50 rounded-[24px] border border-cyan-100 flex gap-6 items-start animate-in fade-in slide-in-from-top-4 duration-1000">
        <div className="w-12 h-12 bg-white rounded-2xl flex items-center justify-center text-mekong-teal shadow-sm border border-cyan-100 flex-shrink-0">
          <Info size={24} />
        </div>
        <div className="space-y-1">
          <h4 className="font-black text-mekong-navy text-xs uppercase tracking-widest">
            Active Intervention Strategy #042-B
          </h4>
          <p className="text-[11px] text-mekong-slate leading-relaxed font-medium">
            Agent has identified a high-risk window between <span className="text-mekong-navy font-bold">14:00 and 16:30</span>. 
            SMS alerts will be dispatched to 14 regional gate operators at 13:40. 
            Automated closure of Sluice-7 will commence at 14:00 exactly to buffer the salt wedge intrusion.
          </p>
        </div>
      </div>

      {/* Decor: Ánh sáng mờ ở góc Card */}
      <div className="absolute -right-20 -bottom-20 w-64 h-64 bg-mekong-cyan/5 rounded-full blur-[80px] pointer-events-none" />
    </div>
  );
};