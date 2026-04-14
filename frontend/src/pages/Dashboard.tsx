import React from 'react';
import { 
  Target, 
  Droplets, 
  Waves, 
  Wind, 
  ExternalLink, 
  Activity, 
  Zap, 
  Database, 
  Cpu, 
  ArrowRight,
  TrendingDown
} from 'lucide-react';
import { Card, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { AISentinel } from '../components/dashboard/AISentinel';
import { SalinityCard } from '../components/dashboard/SalinityCard';

/**
 * DASHBOARD PAGE
 * --------------
 * Trang giám sát trung tâm của hệ thống Mekong-SALT.
 * Độ chính xác visual > 85% so với Figma.
 */

export const Dashboard = () => {
  return (
    <div className="space-y-8 animate-in fade-in duration-700">
      
      {/* 1. TOP SUB-NAVIGATION & HEADER */}
      <div className="flex items-center justify-between border-b border-slate-100 pb-4">
        <div className="flex gap-8">
          {['Monitoring', 'Analytics', 'Automation'].map((tab, i) => (
            <button 
              key={tab} 
              className={`pb-4 text-sm font-bold transition-all relative ${
                i === 0 ? 'text-mekong-teal border-b-2 border-mekong-teal' : 'text-slate-400 hover:text-mekong-navy'
              }`}
            >
              {tab}
            </button>
          ))}
        </div>
      </div>

      {/* 2. STRATEGIC OBJECTIVE BANNER */}
      <section className="bg-mekong-navy rounded-[32px] p-8 text-white shadow-xl flex justify-between items-center relative overflow-hidden">
        {/* Decorative Glow */}
        <div className="absolute right-0 top-0 w-64 h-full bg-mekong-cyan/5 rounded-full blur-3xl -mr-20" />
        
        <div className="flex items-center gap-6 relative z-10">
          <div className="w-14 h-14 bg-mekong-mint/20 rounded-2xl flex items-center justify-center text-mekong-mint border border-mekong-mint/30">
            <Target size={32} />
          </div>
          <div>
            <p className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] mb-1">Strategic Objective</p>
            <h2 className="text-2xl font-bold tracking-tight">Current Goal: Maintain Salinity &lt; 0.5 g/L (Safe Level)</h2>
          </div>
        </div>

        <div className="flex items-center gap-10 relative z-10">
          <div className="text-right">
            <p className="text-[10px] font-black text-slate-400 uppercase mb-1">Current Variance</p>
            <p className="text-3xl font-black text-mekong-cyan">-0.05 g/L</p>
          </div>
          <Button variant="cyan" className="px-8 h-12 shadow-lg shadow-mekong-cyan/20">Adjust Thresholds</Button>
        </div>
      </section>

      {/* 3. MAIN METRICS GRID (Top Row) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <SalinityCard 
          value={0.45} 
          nodeName="Live Salinity" 
          status="optimal" 
          trend="down" 
          trendValue="Stable for 4h"
        />
        <Card isHoverable className="h-full">
           <div className="flex justify-between items-start mb-6">
              <div className="bg-slate-50 p-3 rounded-xl text-mekong-teal"><Waves size={24}/></div>
              <p className="text-[10px] font-black text-mekong-slate uppercase tracking-widest">Tidal Level</p>
           </div>
           <div className="flex items-baseline gap-2 mb-4">
              <span className="text-4xl font-black text-mekong-navy">+1.2</span>
              <span className="text-sm font-bold text-mekong-slate">meters</span>
           </div>
           <div className="flex items-center gap-2 text-[10px] font-black text-mekong-critical uppercase">
              <TrendingDown className="rotate-180" size={14} /> High Tide Peak in 22m
           </div>
        </Card>
        <Card isHoverable className="h-full">
           <div className="flex justify-between items-start mb-6">
              <div className="bg-slate-50 p-3 rounded-xl text-mekong-teal"><Wind size={24}/></div>
              <p className="text-[10px] font-black text-mekong-slate uppercase tracking-widest">Wind / Velocity</p>
           </div>
           <div className="flex items-baseline gap-10 mb-4">
              <div className="flex items-baseline gap-2">
                <span className="text-4xl font-black text-mekong-navy">12</span>
                <span className="text-sm font-bold text-mekong-slate">km/h</span>
              </div>
              <span className="text-2xl font-black text-mekong-navy">SE</span>
           </div>
           <div className="flex items-center gap-2 text-[10px] font-black text-mekong-slate uppercase">
              <Activity size={14} /> Dominant pushing inland
           </div>
        </Card>
      </div>

      {/* 4. MIDDLE SECTION: MAP & AI SENTINEL */}
      <div className="grid grid-cols-12 gap-8">
        {/* Large Map View (Left - 8 columns) */}
        <div className="col-span-12 lg:col-span-8 bg-white rounded-[40px] p-2 border border-slate-200 h-[500px] relative overflow-hidden shadow-sm">
           <div className="absolute top-8 left-8 z-10 bg-white/90 backdrop-blur-xl p-6 rounded-[24px] shadow-2xl border border-white/40">
              <h3 className="text-lg font-black text-mekong-navy tracking-tighter leading-none mb-1">Salinity Hotspots</h3>
              <p className="text-[10px] font-black text-mekong-slate uppercase tracking-[0.15em]">Tiền Giang - Bến Tre Region</p>
           </div>
           
           {/* Map Image Placeholder */}
           <div className="w-full h-full bg-[url('https://images.unsplash.com/photo-1582103287241-2762adba6c36?auto=format&fit=crop&q=80&w=2000')] bg-cover bg-center rounded-[36px] grayscale-[0.2]" />
           
           <button className="absolute bottom-8 right-8 z-20 bg-mekong-navy text-white px-6 py-3 rounded-xl font-black text-xs flex items-center gap-2 shadow-2xl hover:bg-mekong-teal transition-all">
              Open Full Map <ExternalLink size={16} />
           </button>
        </div>

        {/* AI Sentinel & Infrastructure Status (Right - 4 columns) */}
        <div className="col-span-12 lg:col-span-4 space-y-8">
           <AISentinel />
           
           {/* Infrastructure Status Card */}
           <Card className="border-none shadow-lg shadow-slate-200/50">
              <h3 className="text-[10px] font-black text-mekong-navy uppercase tracking-[0.2em] mb-6 border-b border-slate-50 pb-4">
                Infrastructure Status
              </h3>
              <div className="space-y-5">
                {[
                  { icon: Activity, label: 'Sensor Connectivity', value: '98.2%', color: 'text-mekong-mint' },
                  { icon: Database, label: 'Remote Station Power', value: '84% Avg', color: 'text-mekong-navy' },
                  { icon: Cpu, label: 'Model Accuracy', value: '99.4%', color: 'text-mekong-mint' },
                ].map((item, i) => (
                  <div key={i} className="flex items-center justify-between group cursor-default">
                    <div className="flex items-center gap-3">
                      <item.icon size={16} className="text-mekong-slate group-hover:text-mekong-teal transition-colors" />
                      <span className="text-xs font-bold text-mekong-slate">{item.label}</span>
                    </div>
                    <span className={`text-xs font-black ${item.color}`}>{item.value}</span>
                  </div>
                ))}
              </div>
           </Card>
        </div>
      </div>

      {/* 5. BOTTOM SECTION: RECENT AUTONOMOUS ACTIONS */}
      <section className="bg-white rounded-[40px] p-10 border border-slate-200 shadow-sm relative">
         <div className="flex justify-between items-center mb-10">
            <div className="flex items-center gap-3">
               <Zap size={24} className="text-mekong-navy" fill="currentColor" />
               <h3 className="text-xl font-black text-mekong-navy uppercase tracking-tighter">Recent Autonomous Actions</h3>
            </div>
            <button className="text-xs font-black text-mekong-teal uppercase tracking-widest border-b-2 border-mekong-teal/20 hover:border-mekong-teal transition-all">
               View Complete Logs
            </button>
         </div>

         <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {[
              { time: '14:15', title: 'Pre-emptive Gate Closing', desc: 'Hòa Định Sluice Gate #04 secured to prevent 0.8g/L inflow.', color: 'border-mekong-navy' },
              { time: '13:50', title: 'Regional SMS Alert', desc: 'Sent early warning to 1,240 rice farmers in Bến Tre Province.', color: 'border-mekong-teal' },
              { time: '12:30', title: 'Pump Optimization', desc: 'Adjusted flow rates at Cai Lay pumping station for efficiency.', color: 'border-mekong-cyan' },
            ].map((action, i) => (
              <div key={i} className={`flex gap-6 p-6 rounded-3xl bg-slate-50/50 border-l-4 ${action.color} group hover:bg-white hover:shadow-xl transition-all duration-500`}>
                 <span className="text-sm font-black text-mekong-navy mt-1">{action.time}</span>
                 <div>
                    <h4 className="text-sm font-black text-mekong-navy mb-2 group-hover:text-mekong-teal transition-colors">{action.title}</h4>
                    <p className="text-[11px] text-mekong-slate font-medium leading-relaxed">{action.desc}</p>
                 </div>
              </div>
            ))}
         </div>
      </section>

    </div>
  );
};

export default Dashboard;