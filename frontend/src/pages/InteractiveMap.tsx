import React, { useState } from 'react';
import { 
  Layers, 
  Maximize2, 
  Download, 
  AlertTriangle, 
  Plus, 
  Minus, 
  Navigation, 
  X, 
  Zap, 
  Lock,
  Radio,
  ChevronRight
} from 'lucide-react';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';

/**
 * INTERACTIVE MAP PAGE
 * --------------------
 * Giao diện bản đồ với các lớp điều khiển nổi (Floating UI).
 * Độ chính xác visual > 85% so với Figma.
 */

// Component con cho các nút gạt (Toggle Switch)
const MapToggle = ({ label, active, onClick }: { label: string, active: boolean, onClick: () => void }) => (
  <div className="flex items-center justify-between py-2.5">
    <span className="text-[11px] font-bold text-mekong-navy uppercase tracking-widest">{label}</span>
    <button 
      onClick={onClick}
      className={`w-10 h-5 rounded-full relative transition-all duration-300 ${active ? 'bg-mekong-mint' : 'bg-slate-200'}`}
    >
      <div className={`absolute top-1 w-3 h-3 bg-white rounded-full transition-all ${active ? 'right-1' : 'left-1'}`} />
    </button>
  </div>
);

export const InteractiveMap = () => {
  const [layers, setLayers] = useState({
    heatmap: true,
    stations: true,
    gates: true,
    prediction: false
  });

  return (
    <div className="relative w-full h-[calc(100vh-140px)] rounded-[40px] overflow-hidden shadow-2xl border border-slate-200 bg-slate-900">
      
      {/* 1. MAP BACKGROUND (Satellite Image Overlay) */}
      <div className="absolute inset-0 z-0">
        <img 
          src="https://images.unsplash.com/photo-1582103287241-2762adba6c36?auto=format&fit=crop&q=80&w=2000" 
          className="w-full h-full object-cover opacity-80 grayscale-[0.3]" 
          alt="Mekong Delta Satellite" 
        />
        {/* Lớp phủ màu mặn (Heatmap Mockup) */}
        <div className="absolute inset-0 bg-gradient-to-t from-orange-500/20 via-transparent to-transparent mix-blend-overlay" />
      </div>

      {/* 2. TOP LEFT: LAYER CONTROLS & LEGEND */}
      <div className="absolute top-8 left-8 z-20 space-y-4">
        <Card variant="glass" padding="sm" className="w-64 rounded-3xl">
          <div className="flex items-center gap-3 mb-4 border-b border-slate-200/20 pb-3">
            <Layers size={18} className="text-mekong-navy" />
            <h3 className="text-sm font-black text-mekong-navy uppercase tracking-widest">Layer Controls</h3>
          </div>
          <div className="space-y-1">
            <MapToggle label="Salinity Heatmap" active={layers.heatmap} onClick={() => setLayers({...layers, heatmap: !layers.heatmap})} />
            <MapToggle label="Sensor Stations" active={layers.stations} onClick={() => setLayers({...layers, stations: !layers.stations})} />
            <MapToggle label="Irrigation Gates" active={layers.gates} onClick={() => setLayers({...layers, gates: !layers.gates})} />
            <MapToggle label="Tidal Prediction Model" active={layers.prediction} onClick={() => setLayers({...layers, prediction: !layers.prediction})} />
          </div>
        </Card>

        <Card variant="glass" padding="sm" className="w-64 rounded-2xl">
          <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-3">Salinity (g/L)</p>
          <div className="flex h-2 rounded-full overflow-hidden mb-2">
            <div className="flex-1 bg-mekong-mint" />
            <div className="flex-1 bg-yellow-400" />
            <div className="flex-1 bg-orange-500" />
            <div className="flex-1 bg-mekong-critical" />
          </div>
          <div className="flex justify-between text-[9px] font-black text-slate-500 uppercase tracking-widest px-1">
            <span>0.5</span><span>1.0</span><span>2.0</span><span>4.0+</span>
          </div>
        </Card>
      </div>

      {/* 3. TOP RIGHT: UTILITY BUTTONS & AI LOGIC */}
      <div className="absolute top-8 right-8 z-20 space-y-4 flex flex-col items-end">
        <div className="flex flex-col gap-3">
          <Button variant="outline" className="bg-white/90 backdrop-blur-md border-none shadow-xl w-48 h-12 rounded-xl text-xs">
            <Maximize2 size={16} className="mr-3" /> Manual Override
          </Button>
          <Button variant="outline" className="bg-white/90 backdrop-blur-md border-none shadow-xl w-48 h-12 rounded-xl text-xs">
            <Download size={16} className="mr-3" /> Export Map State
          </Button>
          <Button variant="danger" className="bg-[#BA1A1A]/90 backdrop-blur-md border-none shadow-xl w-48 h-12 rounded-xl text-xs text-white">
            <AlertTriangle size={16} className="mr-3" /> Report Sensor Error
          </Button>
        </div>

        <Card variant="navy" padding="sm" className="w-64 rounded-3xl border-white/10 bg-[#00203F]/90 backdrop-blur-xl">
          <div className="flex items-center gap-2 mb-4 text-mekong-cyan">
            <Zap size={18} fill="currentColor" />
            <h3 className="text-[10px] font-black uppercase tracking-[0.2em]">Auto-Gate Logic</h3>
          </div>
          <div className="space-y-4">
            <div className="flex justify-between items-center group cursor-pointer">
              <span className="text-[11px] font-bold text-slate-400 group-hover:text-white transition-colors">Thới Tân Gate</span>
              <span className="text-[10px] font-black text-mekong-mint uppercase tracking-widest">Ready</span>
            </div>
            <div className="flex justify-between items-center group cursor-pointer">
              <span className="text-[11px] font-bold text-slate-400 group-hover:text-white transition-colors">Phú Đông Gate</span>
              <span className="text-[10px] font-black text-yellow-400 uppercase tracking-widest">Monitoring</span>
            </div>
          </div>
        </Card>
      </div>

      {/* 4. MAP MARKERS (Static Mockups) */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-10">
         {/* Sensor Marker */}
         <div className="absolute -top-10 -left-20 bg-[#BA1A1A]/20 p-2 rounded-2xl animate-pulse">
            <div className="bg-[#BA1A1A] p-2.5 rounded-xl text-white shadow-2xl border border-white/20">
               <Radio size={24} />
            </div>
         </div>
         {/* Gate Marker */}
         <div className="flex flex-col items-center gap-2">
            <div className="bg-[#00203F] p-3 rounded-2xl text-white shadow-2xl border-2 border-white/20 ring-4 ring-[#00203F]/20">
               <Lock size={24} />
            </div>
            <span className="bg-[#00203F] px-3 py-1 rounded-lg text-[9px] font-black text-white uppercase tracking-widest shadow-xl">Closed</span>
         </div>
      </div>

      {/* 5. BOTTOM RIGHT: ZOOM CONTROLS */}
      <div className="absolute bottom-10 right-10 z-20 flex flex-col gap-3">
        <button className="bg-white/90 backdrop-blur-md p-3 rounded-xl shadow-2xl hover:bg-white transition-all"><Plus size={20} className="text-mekong-navy" /></button>
        <button className="bg-white/90 backdrop-blur-md p-3 rounded-xl shadow-2xl hover:bg-white transition-all"><Minus size={20} className="text-mekong-navy" /></button>
        <button className="bg-white/90 backdrop-blur-md p-3 rounded-xl shadow-2xl hover:bg-white transition-all mt-2"><Navigation size={20} className="text-mekong-navy rotate-45" /></button>
      </div>

      {/* 6. BOTTOM PANEL: STATION DETAILS (Detailed Overlay) */}
      <div className="absolute bottom-8 left-8 right-32 z-30">
        <Card variant="glass" padding="lg" className="rounded-[40px] shadow-glass border-white/50 backdrop-blur-2xl">
          <div className="flex justify-between items-start mb-10">
            <div>
              <div className="flex items-center gap-4 mb-2">
                <h2 className="text-3xl font-black text-mekong-navy tracking-tighter uppercase leading-none">Station: Hai Tân</h2>
                <Badge variant="warning" dot className="bg-amber-50 text-amber-600 border-amber-200">Rising Salinity</Badge>
              </div>
              <p className="text-sm font-bold text-mekong-slate uppercase tracking-widest opacity-80">
                Mỹ Tho River Entrance | Coord: 10.352, 106.365
              </p>
            </div>
            <button className="p-3 bg-slate-100/50 hover:bg-slate-200/50 rounded-full transition-all"><X size={24} className="text-mekong-navy" /></button>
          </div>

          <div className="grid grid-cols-12 gap-6 items-end">
            {/* Metrics */}
            <div className="col-span-12 lg:col-span-6 grid grid-cols-2 gap-4">
               {[
                 { label: 'Live Reading', value: '2.45', unit: 'g/L', color: 'text-mekong-teal' },
                 { label: 'Tidal Level', value: '+1.2', unit: 'm', color: 'text-mekong-teal' },
                 { label: 'Wind Velocity', value: '14.2', unit: 'km/h', color: 'text-mekong-navy' },
                 { label: 'AI Peak Prediction', value: '3.10', unit: 'g/L', color: 'text-mekong-navy', sub: 'Expected in 4h 20m', bg: 'bg-[#006877]/5 border-mekong-teal/10' }
               ].map((m, i) => (
                 <div key={i} className={`p-6 rounded-3xl border border-slate-100 bg-white/50 shadow-sm ${m.bg}`}>
                    <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-3">{m.label}</p>
                    <div className="flex items-baseline gap-1">
                       <span className={`text-2xl font-black ${m.color} tracking-tighter`}>{m.value}</span>
                       <span className="text-[10px] font-black text-slate-400 uppercase">{m.unit}</span>
                    </div>
                    {m.sub && <p className="text-[9px] font-bold text-mekong-teal mt-2 italic">{m.sub}</p>}
                 </div>
               ))}
            </div>

            {/* Visual Chart Placeholder (Right part of the card) */}
            <div className="col-span-12 lg:col-span-6 h-40 flex items-end gap-3 px-4 relative">
               {[30, 45, 38, 55, 75, 85, 95, 80].map((h, i) => (
                 <div 
                   key={i} 
                   style={{ height: `${h}%` }} 
                   className={`flex-1 rounded-t-xl transition-all duration-700 ${i > 3 ? 'bg-mekong-mint shadow-[0_0_15px_rgba(45,212,191,0.3)]' : 'bg-slate-200'}`} 
                 />
               ))}
               <div className="absolute right-0 bottom-full mb-4 bg-white px-3 py-1.5 rounded-lg border border-slate-100 shadow-sm text-[9px] font-black text-mekong-navy uppercase tracking-widest">
                  24H History & AI Forecast
               </div>
               {/* Dash line for forecast */}
               <div className="absolute bottom-[40%] left-0 w-full h-0 border-t-2 border-dashed border-slate-300 -z-10" />
            </div>
          </div>
        </Card>
      </div>

    </div>
  );
};

export default InteractiveMap;