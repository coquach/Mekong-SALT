import React from 'react';
import { 
  Waves, 
  Wind, 
  ArrowDownToLine, 
  TrendingUp, 
  AlertCircle, 
  Map as MapIcon, 
  Zap, 
  Search,
  Settings,
  Bell,
  Signal,
  Navigation,
  CheckCircle2,
  ChevronRight,
  History as HistoryIcon
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';

/**
 * HISTORY PAGE - NODE DEEP DIVE
 * ----------------------------
 * Phân tích lịch sử và chẩn đoán nguyên nhân xâm nhập mặn của AI.
 * Độ chính xác visual > 90% so với Figma.
 */

export const History = () => {
  return (
    <div className="space-y-8 animate-in fade-in duration-700">
      
      {/* 1. TOP NAVIGATION & BREADCRUMB */}
      <div className="flex justify-between items-center border-b border-slate-100 pb-4">
        <div className="flex items-center gap-2 text-[10px] font-black text-slate-400 uppercase tracking-widest">
          <span>Station:</span>
          <span className="text-mekong-navy">Tien River - Node 04</span>
        </div>
        <div className="flex items-center gap-6">
          <button className="text-slate-400 hover:text-mekong-teal transition-colors"><Bell size={18}/></button>
          <button className="text-slate-400 hover:text-mekong-teal transition-colors"><Signal size={18}/></button>
          <button className="text-slate-400 hover:text-mekong-teal transition-colors"><Settings size={18}/></button>
        </div>
      </div>

      {/* 2. PAGE HEADER & CURRENT STATUS */}
      <div className="flex justify-between items-start">
        <div className="space-y-3">
          <h1 className="text-5xl font-black text-mekong-navy tracking-tighter leading-none">
            Node 04 Deep Dive
          </h1>
          <p className="text-sm text-mekong-slate font-medium max-w-2xl leading-relaxed">
            Comprehensive historical analysis and AI-driven risk assessment for the Tiền River corridor.
          </p>
        </div>
        
        {/* Current Salinity Highlight Card */}
        <div className="bg-white border-l-4 border-[#BA1A1A] p-6 shadow-xl rounded-2xl flex flex-col items-end min-w-[200px]">
          <p className="text-[10px] font-black text-[#BA1A1A] uppercase tracking-[0.2em] mb-1">Current Salinity</p>
          <div className="flex items-baseline gap-2">
            <span className="text-4xl font-black text-mekong-navy tracking-tighter">2.8</span>
            <span className="text-sm font-bold text-slate-400">g/L</span>
          </div>
        </div>
      </div>

      {/* 3. TREND ANALYSIS & BENCHMARKS GRID */}
      <div className="grid grid-cols-12 gap-8">
        
        {/* Longitudinal Trend Analysis (8 columns) */}
        <div className="col-span-12 lg:col-span-8">
          <Card variant="white" padding="lg" className="h-full">
            <div className="flex justify-between items-center mb-10">
              <div>
                <CardTitle className="mb-1 text-sm">Longitudinal Trend Analysis</CardTitle>
                <CardDescription>30-Day temporal salinity variance</CardDescription>
              </div>
              <div className="flex bg-slate-100 p-1 rounded-xl">
                 {['1W', '1M', '3M'].map((t, i) => (
                   <button key={t} className={`px-4 py-1.5 text-[10px] font-black rounded-lg transition-all ${i === 1 ? 'bg-mekong-navy text-white shadow-md' : 'text-slate-400 hover:text-mekong-navy'}`}>
                     {t}
                   </button>
                 ))}
              </div>
            </div>

            {/* Custom SVG Line Chart Mockup */}
            <div className="relative h-64 w-full mt-10">
               {/* Y-Axis Labels */}
               <div className="absolute left-0 h-full flex flex-col justify-between text-[10px] font-bold text-slate-300 -translate-x-full pr-4">
                  <span>4.0</span><span>3.0</span><span>2.0</span><span>1.0</span><span>0.0</span>
               </div>
               
               {/* Grid Lines */}
               <div className="absolute inset-0 flex flex-col justify-between">
                  {[...Array(5)].map((_, i) => <div key={i} className="w-full border-t border-slate-50 border-dashed" />)}
               </div>

               {/* Danger Threshold Line */}
               <div className="absolute bottom-[50%] w-full border-t-2 border-[#BA1A1A]/30 border-dashed z-0 flex justify-end">
                  <span className="text-[9px] font-black text-[#BA1A1A] bg-white px-2 -mt-2">DANGER THRESHOLD (2.0 G/L)</span>
               </div>
               
               {/* Main Trend Line (SVG Path) */}
               <svg className="absolute inset-0 w-full h-full overflow-visible z-10" preserveAspectRatio="none">
                  <path 
                    d="M 0 180 Q 100 170 200 200 T 400 150 T 600 130 T 800 100" 
                    fill="none" 
                    stroke="url(#gradient)" 
                    strokeWidth="8" 
                    strokeLinecap="round" 
                  />
                  <defs>
                    <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="0%">
                      <stop offset="0%" stopColor="#75E7FE" />
                      <stop offset="50%" stopColor="#006877" />
                      <stop offset="100%" stopColor="#BA1A1A" />
                    </linearGradient>
                  </defs>
                  {/* Current Point */}
                  <circle cx="98%" cy="100" r="6" fill="#BA1A1A" className="animate-pulse" stroke="white" strokeWidth="2" />
               </svg>

               {/* X-Axis Labels */}
               <div className="absolute -bottom-8 left-0 w-full flex justify-between text-[10px] font-bold text-slate-400 uppercase tracking-widest px-4">
                  <span>Mar 01</span><span>Mar 08</span><span>Mar 15</span><span>Mar 22</span><span>Mar 29</span>
               </div>
            </div>
          </Card>
        </div>

        {/* Historical Benchmarks (4 columns) */}
        <div className="col-span-12 lg:col-span-4 space-y-6">
           <Card variant="white" padding="lg" className="h-full bg-slate-50/50 border-none shadow-soft">
              <div className="flex items-center gap-3 mb-8">
                 <HistoryIcon size={18} className="text-mekong-navy" />
                 <CardTitle className="text-xs">Historical Benchmarks</CardTitle>
              </div>

              <div className="space-y-6">
                 {[
                   { year: 'March 2024 (Now)', val: '2.8 g/L', color: 'text-[#BA1A1A]', bg: 'bg-white' },
                   { year: 'March 2023', val: '1.4 g/L', color: 'text-mekong-navy', bg: 'bg-transparent' },
                   { year: 'March 2022', val: '1.1 g/L', color: 'text-mekong-navy', bg: 'bg-transparent' },
                 ].map((row, i) => (
                    <div key={i} className={`flex justify-between items-center p-4 rounded-xl transition-all ${row.bg} ${row.bg !== 'bg-transparent' ? 'shadow-sm border border-slate-100' : ''}`}>
                       <span className="text-[11px] font-bold text-slate-500">{row.year}</span>
                       <span className={`text-sm font-black ${row.color}`}>{row.val}</span>
                    </div>
                 ))}
              </div>

              {/* AI Insight Box */}
              <div className="mt-10 p-5 bg-red-50 rounded-2xl border border-red-100 flex gap-4">
                 <TrendingUp size={24} className="text-[#BA1A1A] shrink-0" />
                 <p className="text-[11px] font-bold text-[#BA1A1A] leading-relaxed">
                    Current salinity is <span className="underline">100% higher</span> than the 3-year historical average for this period.
                 </p>
              </div>
           </Card>
        </div>
      </div>

      {/* 4. AI RISK ASSESSMENT & SPATIAL CORRELATION GRID */}
      <div className="grid grid-cols-12 gap-8">
        
        {/* AI Risk Assessment (4 columns) */}
        <div className="col-span-12 lg:col-span-4">
           <Card variant="navy" padding="lg" className="bg-[#00203F] h-full relative overflow-hidden">
              <div className="absolute top-0 right-0 w-48 h-48 bg-mekong-cyan/10 rounded-full blur-[80px]" />
              
              <div className="relative z-10">
                 <div className="flex items-center gap-2 mb-8">
                    <div className="w-2 h-2 rounded-full bg-mekong-cyan" />
                    <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">AI Risk Assessment</span>
                 </div>
                 <h3 className="text-2xl font-black text-white mb-8 tracking-tighter leading-tight">
                    Causal attribution for 2.8 g/L anomaly
                 </h3>

                 <div className="space-y-6">
                    {[
                      { icon: Waves, label: 'Tidal Surge', val: '+1.2m' },
                      { icon: Wind, label: 'Wind Velocity', val: '12km/h SE' },
                      { icon: ArrowDownToLine, label: 'Upstream Flow', val: '-22% vs Avg', color: 'text-[#BA1A1A]' },
                    ].map((row, i) => (
                       <div key={i} className="flex items-center justify-between border-b border-white/5 pb-4">
                          <div className="flex items-center gap-3">
                             <row.icon size={18} className="text-slate-400" />
                             <span className="text-xs font-bold text-slate-300">{row.label}</span>
                          </div>
                          <span className={`text-sm font-black ${row.color || 'text-white'}`}>{row.val}</span>
                       </div>
                    ))}
                 </div>

                 <p className="mt-12 text-[11px] font-medium text-slate-400 italic leading-relaxed">
                    "The convergence of a high tidal surge and reduced upstream flow from the Lancang basin is the primary driver of the current saline front intrusion."
                 </p>
              </div>
           </Card>
        </div>

        {/* Spatial Correlation Map (4 columns) */}
        <div className="col-span-12 lg:col-span-4">
           <Card variant="white" padding="lg" className="h-full bg-slate-50/80 border-none shadow-soft relative overflow-hidden">
              <div className="flex justify-between items-start relative z-10">
                 <div>
                    <CardTitle className="text-xs mb-1">Spatial Correlation</CardTitle>
                    <CardDescription>Neighboring sensor validation</CardDescription>
                 </div>
                 <div className="bg-white p-2 rounded-lg shadow-sm"><Navigation size={14} className="text-mekong-navy rotate-45" /></div>
              </div>

              {/* Map Illustration (Mockup) */}
              <div className="relative mt-8 h-64 flex items-center justify-center">
                 <div className="w-full h-full bg-[url('https://images.unsplash.com/photo-1542601906990-b4d3fb773b09?auto=format&fit=crop&q=80&w=1000')] bg-cover opacity-20 grayscale rounded-3xl" />
                 
                 {/* Map Pins */}
                 <div className="absolute top-[40%] right-[30%] group">
                    <div className="w-8 h-8 bg-[#BA1A1A] text-white flex items-center justify-center rounded-full text-[9px] font-black border-2 border-white shadow-xl scale-125">2.8</div>
                 </div>
                 <div className="absolute bottom-[20%] left-[30%] group">
                    <div className="w-6 h-6 bg-mekong-teal text-white flex items-center justify-center rounded-full text-[8px] font-black border-2 border-white shadow-lg">1.2</div>
                 </div>
              </div>

              <div className="mt-8 flex justify-center gap-6">
                 <div className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-[#BA1A1A]" />
                    <span className="text-[9px] font-black text-mekong-navy uppercase tracking-widest">CRITICAL</span>
                 </div>
                 <div className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-mekong-teal" />
                    <span className="text-[9px] font-black text-mekong-navy uppercase tracking-widest">NOMINAL</span>
                 </div>
              </div>
           </Card>
        </div>

        {/* AI Directives Sidebar (4 columns) */}
        <div className="col-span-12 lg:col-span-4">
           <Card variant="white" padding="none" className="h-full border-t-4 border-t-mekong-navy shadow-xl flex flex-col">
              <div className="p-8 flex-1">
                 <div className="flex items-center gap-3 mb-10">
                    <Zap size={20} className="text-mekong-navy" fill="currentColor" />
                    <h3 className="text-[13px] font-black text-mekong-navy uppercase tracking-[0.2em]">AI Directives</h3>
                 </div>

                 <div className="space-y-10">
                    {[
                      { cat: 'INFRASTRUCTURE', title: 'Extended Gate Closure recommended for next 4 tidal cycles.' },
                      { cat: 'AGRICULTURE', title: 'Halt irrigation at Station S-12 until levels recede below 1.5 g/L.' },
                      { cat: 'MONITORING', title: 'Deploy mobile salinity profiler to Ben Tre boundary coordinates.' }
                    ].map((item, i) => (
                       <div key={i} className="space-y-2">
                          <p className="text-[9px] font-black text-slate-400 uppercase tracking-widest">{item.cat}</p>
                          <h4 className="text-sm font-bold text-mekong-navy leading-snug">{item.title}</h4>
                       </div>
                    ))}
                 </div>
              </div>
              <div className="p-8 pt-0">
                 <Button variant="navy" className="w-full h-14 rounded-xl shadow-lg">Execute All Directives</Button>
              </div>
           </Card>
        </div>
      </div>

      {/* 5. BOTTOM CRITICAL ALERT BAR */}
      <div className="bg-[#BA1A1A] p-6 rounded-3xl text-white shadow-2xl flex items-center justify-between animate-pulse">
         <div className="flex items-center gap-6 pl-4">
            <AlertCircle size={32} />
            <div>
               <h4 className="text-lg font-black tracking-tighter uppercase leading-none mb-1">Threshold Breach Alert</h4>
               <p className="text-xs font-bold text-white/80 uppercase tracking-widest">2.8 g/L exceeds safety threshold for Rice Cultivation</p>
            </div>
         </div>
         <Button variant="outline" className="border-white text-white hover:bg-white hover:text-[#BA1A1A] px-10 h-12">
            Protocol Guide
         </Button>
      </div>

    </div>
  );
};

export default History;