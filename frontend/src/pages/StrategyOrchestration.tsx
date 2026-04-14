import React from 'react';
import { 
  Database, 
  LineChart, 
  Settings2, 
  Zap, 
  RotateCcw, 
  CheckCircle2,
  Info,
  Terminal,
  Download,
  BrainCircuit,
  SlidersHorizontal,
  ChevronRight,
  Waves,
  Wind,
  History as HistoryIcon,
  Radio,
  MapPin
} from 'lucide-react';
import { Card, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';

/**
 * STRATEGY ORCHESTRATION (PLANNING) PAGE
 * -------------------------------------
 * Hiển thị quy trình tư duy và cấu hình Agility của AI.
 * Độ chính xác visual > 85% so với Figma.
 */

export const StrategyOrchestration = () => {
  return (
    <div className="space-y-8 animate-in fade-in duration-700">
      
      {/* 1. TOP HEADER SECTION */}
      <div className="flex justify-between items-end">
        <div className="space-y-2">
          <h1 className="text-4xl font-black text-mekong-navy tracking-tighter">Strategy Orchestration</h1>
          <p className="text-sm text-mekong-slate font-medium max-w-2xl leading-relaxed">
            The SALT-Agent is currently evaluating the 48-hour tidal forecast against real-time wind stress variables in the Soc Trang delta region.
          </p>
        </div>
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2 px-4 py-2 bg-mekong-mint/10 rounded-full border border-mekong-mint/20">
            <div className="w-2 h-2 bg-mekong-mint rounded-full animate-pulse" />
            <span className="text-[10px] font-black text-mekong-navy uppercase tracking-widest">Reasoning Engine: Active</span>
          </div>
          <Button variant="navy" className="h-12 px-8 flex gap-2">
             <Settings2 size={16} /> Optimize Plan
          </Button>
        </div>
      </div>

      {/* 2. MAIN WORKFLOW & COGNITIVE MAPPING GRID */}
      <div className="grid grid-cols-12 gap-8">
        
        {/* Left Column: Workflow (8 cols) */}
        <div className="col-span-12 lg:col-span-8">
           <Card variant="white" padding="lg" className="h-full border-l-4 border-l-mekong-teal rounded-3xl relative overflow-hidden">
              <div className="flex justify-between items-center mb-16">
                 <h3 className="text-[11px] font-black text-mekong-navy uppercase tracking-[0.2em]">Current Strategy Workflow</h3>
                 <Badge variant="cyan" className="bg-[#75E7FE]/10 text-mekong-teal border-none px-3 py-1">Goal-Driven Planning</Badge>
              </div>

              {/* Stepper Visualization */}
              <div className="relative flex justify-between items-start px-4">
                 <div className="absolute top-8 left-10 right-10 h-0.5 bg-slate-100" />
                 <div className="absolute top-8 left-10 h-0.5 bg-mekong-teal transition-all duration-1000" style={{ width: '45%' }} />
                 
                 {[
                   { id: 1, icon: Database, label: 'Data Acquisition', sub: 'Sensor & API Mesh', status: 'COMPLETED' },
                   { id: 2, icon: LineChart, label: 'Prediction', sub: 'Peak salinity in 45m', status: 'COMPLETED' },
                   { id: 3, icon: Settings2, label: 'Mitigation', sub: 'Pre-emptive closure', status: 'ACTIVE NOW', active: true },
                   { id: 4, icon: Zap, label: 'Execution', sub: 'SMS → Close Gate', status: 'QUEUED' },
                   { id: 5, icon: RotateCcw, label: 'Feedback Loop', sub: 'Evaluating result', status: 'PENDING' },
                 ].map((step) => (
                   <div key={step.id} className="relative z-10 flex flex-col items-center group w-32">
                      <div className={`w-16 h-16 rounded-2xl flex items-center justify-center transition-all duration-500 ${
                        step.active ? 'bg-mekong-cyan text-mekong-navy scale-110 shadow-lg shadow-mekong-cyan/30' : 
                        step.status === 'COMPLETED' ? 'bg-mekong-mint/10 text-mekong-mint border border-mekong-mint/20' : 
                        'bg-slate-50 text-slate-300'
                      }`}>
                         <step.icon size={28} />
                      </div>
                      <div className="mt-6 text-center space-y-1">
                         <p className={`text-[11px] font-black uppercase tracking-tighter ${step.active ? 'text-mekong-navy' : 'text-mekong-slate'}`}>{step.label}</p>
                         <p className="text-[9px] text-slate-400 font-medium">{step.sub}</p>
                         <p className={`text-[9px] font-black uppercase mt-2 tracking-widest ${step.active ? 'text-mekong-teal' : 'text-slate-300'}`}>{step.status}</p>
                      </div>
                   </div>
                 ))}
              </div>

              {/* Intervention Strategy Info Box */}
              <div className="mt-20 p-8 bg-slate-50 rounded-[32px] border border-slate-100 flex gap-6 items-start">
                 <div className="w-12 h-12 bg-white rounded-full flex items-center justify-center text-mekong-teal shadow-sm border border-slate-200">
                    <Info size={24} />
                 </div>
                 <div className="space-y-2">
                    <h4 className="text-sm font-black text-mekong-navy uppercase tracking-widest">Active Intervention Strategy #042-B</h4>
                    <p className="text-xs text-mekong-slate leading-relaxed font-medium">
                       Agent has identified a high-risk window between <span className="text-mekong-navy font-bold">14:00 and 16:30</span>. SMS alerts will be dispatched to 14 regional gate operators at 13:40. Automated closure of Sluice-7 will commence at 14:00 exactly to buffer the salt wedge.
                    </p>
                 </div>
              </div>
           </Card>
        </div>

        {/* Right Column: Cognitive Node Mapping (4 cols) */}
        <div className="col-span-12 lg:col-span-4">
           <Card variant="navy" padding="lg" className="h-full bg-[#00203F] border-none shadow-2xl relative">
              <div className="flex items-center gap-3 mb-10 text-white">
                 <BrainCircuit className="text-mekong-cyan" size={24} />
                 <h3 className="text-lg font-bold tracking-tight">Cognitive Node Mapping</h3>
              </div>

              {/* Circular Node Sơ đồ */}
              <div className="relative h-[300px] flex items-center justify-center">
                 {/* Central Node */}
                 <div className="w-20 h-20 bg-mekong-cyan rounded-2xl flex items-center justify-center text-mekong-navy z-20 shadow-[0_0_40px_rgba(117,231,254,0.4)]">
                    <BrainCircuit size={32} />
                 </div>
                 
                 {/* Peripheral Nodes (Mockup positions) */}
                 {[
                   { icon: Waves, label: 'TIDE', pos: 'top-0 left-1/2 -translate-x-1/2' },
                   { icon: Radio, label: 'SENSOR', pos: 'bottom-1/4 left-4' },
                   { icon: Wind, label: 'WIND', pos: 'bottom-1/4 right-4' },
                   { icon: HistoryIcon, label: 'HISTORY', pos: 'bottom-4 left-1/2 -translate-x-1/2' },
                 ].map((node, i) => (
                   <div key={i} className={`absolute ${node.pos} flex flex-col items-center gap-2`}>
                      <div className="w-10 h-10 bg-white/5 border border-white/10 rounded-xl flex items-center justify-center text-slate-400 group hover:text-mekong-cyan transition-colors">
                         <node.icon size={18} />
                      </div>
                      <span className="text-[8px] font-black text-slate-500 uppercase tracking-widest">{node.label}</span>
                   </div>
                 ))}

                 {/* Kết nối mờ ảo (SVG lines mockup) */}
                 <svg className="absolute inset-0 w-full h-full opacity-20" viewBox="0 0 400 300">
                    <line x1="200" y1="150" x2="200" y2="50" stroke="white" strokeWidth="1" strokeDasharray="4" />
                    <line x1="200" y1="150" x2="80" y2="220" stroke="white" strokeWidth="1" strokeDasharray="4" />
                    <line x1="200" y1="150" x2="320" y2="220" stroke="white" strokeWidth="1" strokeDasharray="4" />
                 </svg>
              </div>

              <div className="mt-10 space-y-4">
                 <div className="flex justify-between items-end">
                    <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest">Processing Density</p>
                    <p className="text-sm font-mono text-mekong-cyan">88 Gflops</p>
                 </div>
                 <div className="h-1 bg-white/10 rounded-full overflow-hidden">
                    <div className="h-full bg-mekong-cyan w-4/5 rounded-full" />
                 </div>
              </div>
           </Card>
        </div>
      </div>

      {/* 3. LOGS & GOAL SETTINGS GRID */}
      <div className="grid grid-cols-12 gap-8">
        
        {/* Reasoning Log (8 cols) */}
        <div className="col-span-12 lg:col-span-8">
           <Card variant="white" padding="lg">
              <div className="flex justify-between items-center mb-8">
                 <div className="flex items-center gap-3">
                    <Terminal size={20} className="text-mekong-navy" />
                    <h3 className="text-sm font-black text-mekong-navy uppercase tracking-widest">Live Reasoning Log</h3>
                 </div>
                 <button className="text-[10px] font-black text-mekong-slate uppercase tracking-widest flex items-center gap-2 hover:text-mekong-teal">
                    <Download size={14} /> Export Log
                 </button>
              </div>

              <div className="space-y-4 font-mono">
                 {[
                   { t: '[14:22:10]', cat: 'CORE_PROCESS', msg: 'Wind speed increased to 6 Bft, accelerating salt wedge intrusion by 12%... adjustment made to closure timing.' },
                   { t: '[14:18:05]', cat: 'DATA_INGEST', msg: 'Receiving high-res satellite bathymetry. Calculating riverbed friction coefficients for upstream propagation model.' },
                   { t: '[14:15:52]', cat: 'PREDICTIVE_SYNC', msg: 'Historical patterns from 2016 drought event matched with 94.2% confidence. Adjusting threshold for Gate-09 sensitivity.' },
                   { t: '[14:10:30]', cat: 'DECISION_BRANCH', msg: 'Gate-12 manual override detected. Re-routing salt flow simulation to account for non-compliant leakage at section Delta-4.' }
                 ].map((log, i) => (
                   <div key={i} className="flex gap-4 p-4 bg-slate-50 rounded-2xl group hover:bg-slate-100 transition-colors">
                      <span className="text-[10px] text-slate-400 font-bold whitespace-nowrap">{log.t}</span>
                      <p className="text-[11px] leading-relaxed">
                         <span className="font-black text-mekong-navy">{log.cat}:</span> <span className="text-slate-600">{log.msg}</span>
                      </p>
                   </div>
                 ))}
              </div>
           </Card>
        </div>

        {/* Goal Settings (4 cols) */}
        <div className="col-span-12 lg:col-span-4">
           <Card variant="white" padding="lg" className="h-full border-none shadow-xl bg-slate-50/50">
              <div className="flex items-center gap-3 mb-8">
                 <SlidersHorizontal size={20} className="text-mekong-navy" />
                 <h3 className="text-sm font-black text-mekong-navy uppercase tracking-widest">Strategic Goal Settings</h3>
              </div>

              <div className="space-y-8">
                 <div>
                    <div className="flex justify-between items-baseline mb-4">
                       <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest">Salinity Threshold</label>
                       <span className="text-sm font-black text-mekong-navy">0.3 g/L</span>
                    </div>
                    <div className="relative h-2 bg-slate-200 rounded-full mb-2">
                       <div className="absolute top-0 left-0 h-full w-1/3 bg-mekong-teal rounded-full" />
                       <div className="absolute top-1/2 -translate-y-1/2 left-1/3 w-4 h-4 bg-white border-2 border-mekong-teal rounded-full shadow-md" />
                    </div>
                    <div className="flex justify-between text-[8px] font-bold text-slate-400 uppercase tracking-widest">
                       <span>0.1 g/L</span>
                       <span>Target: Maintain during planting season</span>
                       <span>1.0 g/L</span>
                    </div>
                 </div>

                 <div className="space-y-4">
                    <div className="flex justify-between items-baseline">
                       <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest">Intervention Agility</label>
                       <span className="text-[10px] font-black text-mekong-teal uppercase tracking-widest">High (Proactive)</span>
                    </div>
                    <div className="grid grid-cols-3 gap-1 bg-white p-1 rounded-xl border border-slate-200">
                       <button className="py-2 text-[9px] font-black uppercase text-slate-400">Conservative</button>
                       <button className="py-2 text-[9px] font-black uppercase bg-mekong-teal text-white rounded-lg shadow-md">Balanced</button>
                       <button className="py-2 text-[9px] font-black uppercase text-slate-400">Aggressive</button>
                    </div>
                 </div>

                 <Button variant="navy" className="w-full h-12 flex gap-2">
                    <CheckCircle2 size={16} /> Commit Strategy Overrides
                 </Button>
              </div>
           </Card>
        </div>
      </div>

      {/* 4. SUMMARY FOOTER BAR */}
      <Card variant="white" padding="md" className="border-none shadow-soft">
         <div className="flex justify-between items-center">
            <div className="flex items-center gap-6">
               <div className="w-16 h-16 bg-slate-100 rounded-2xl flex items-center justify-center p-2">
                  {/* Map Pin Icon Mockup */}
                  <MapPin size={28} className="text-mekong-teal" />
               </div>
               <div>
                  <h4 className="text-lg font-black text-mekong-navy tracking-tighter leading-none mb-1">Soc Trang Estuary Nodes</h4>
                  <p className="text-xs text-mekong-slate font-medium">Currently monitoring 4 critical sluice gates in the southern sector. Predictive accuracy: 98.4%.</p>
               </div>
            </div>
            <div className="flex gap-12 text-right">
               <div>
                  <p className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] mb-1">Avg Salinity</p>
                  <p className="text-2xl font-black text-mekong-critical">0.52</p>
               </div>
               <div>
                  <p className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] mb-1">Nodes Up</p>
                  <p className="text-2xl font-black text-mekong-navy">42/42</p>
               </div>
            </div>
         </div>
      </Card>

    </div>
  );
};

export default StrategyOrchestration;