import React, { useState } from "react";
import {
  Layers,
  Maximize2,
  Download,
  AlertTriangle,
  Zap,
  X,
  TrendingUp,
  Activity,
  Waves,
  Wind,
  Cpu,
  ChevronRight,
} from "lucide-react";
import { Card, CardContent } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Badge } from "../components/ui/Badge";
import { SatelliteMap } from "../components/dashboard/SatelliteMap";

const LayerSwitch = ({ label, active, onToggle }: any) => (
  <div
    className="flex items-center justify-between py-2 cursor-pointer group"
    onClick={onToggle}
  >
    <span
      className={`text-[11px] font-black uppercase tracking-widest transition-colors ${active ? "text-mekong-navy" : "text-slate-400"}`}
    >
      {label}
    </span>
    <div
      className={`w-9 h-5 rounded-full relative transition-all ${active ? "bg-mekong-mint" : "bg-slate-200"}`}
    >
      <div
        className={`absolute top-1 w-3 h-3 bg-white rounded-full transition-all ${active ? "right-1" : "left-1"}`}
      />
    </div>
  </div>
);

export const InteractiveMap = () => {
  const [layers, setLayers] = useState({
    heatmap: true,
    stations: true,
    gates: true,
    prediction: false,
  });

  return (
    <div className="relative w-full h-[calc(100vh-120px)] rounded-[48px] overflow-hidden bg-slate-900 shadow-2xl border border-white/10">
      {/* --- MAP CHÍNH --- */}
      <SatelliteMap layers={layers} zoom={15} showControls={true} />

      {/* --- TOP LEFT: LAYER CONTROLS --- */}
      <div className="absolute top-8 left-8 z-20 space-y-4 w-72">
        <Card
          variant="glass"
          className="p-6 rounded-[32px] border-white/40 shadow-glass backdrop-blur-2xl"
        >
          <div className="flex items-center gap-3 mb-6 border-b border-mekong-navy/10 pb-4">
            <Layers size={18} className="text-mekong-navy" />
            <h3 className="text-sm font-black text-mekong-navy uppercase tracking-widest">
              Layer Controls
            </h3>
          </div>
          <div className="space-y-1">
            <LayerSwitch
              label="Salinity Heatmap"
              active={layers.heatmap}
              onToggle={() =>
                setLayers({ ...layers, heatmap: !layers.heatmap })
              }
            />
            <LayerSwitch
              label="Sensor Stations"
              active={layers.stations}
              onToggle={() =>
                setLayers({ ...layers, stations: !layers.stations })
              }
            />
            <LayerSwitch
              label="Irrigation Gates"
              active={layers.gates}
              onToggle={() => setLayers({ ...layers, gates: !layers.gates })}
            />
            <LayerSwitch
              label="Tidal Prediction"
              active={layers.prediction}
              onToggle={() =>
                setLayers({ ...layers, prediction: !layers.prediction })
              }
            />
          </div>
        </Card>

        {/* Legend */}
        <Card
          variant="glass"
          className="p-5 rounded-2xl border-white/40 shadow-md"
        >
          <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-3">
            Salinity Index (g/L)
          </p>
          <div className="flex h-2 rounded-full overflow-hidden mb-2">
            <div className="flex-1 bg-mekong-mint" />
            <div className="flex-1 bg-yellow-400" />
            <div className="flex-1 bg-orange-500" />
            <div className="flex-1 bg-mekong-critical" />
          </div>
          <div className="flex justify-between text-[9px] font-black text-slate-400 uppercase tracking-widest">
            <span>0.5</span>
            <span>1.0</span>
            <span>2.0</span>
            <span>4.0+</span>
          </div>
        </Card>
      </div>

      {/* --- TOP RIGHT: ACTIONS & AUTO-GATE --- */}
      <div className="absolute top-8 right-8 z-20 flex flex-col items-end gap-5 w-80">
        {/* 1. KHỐI NÚT HÀNH ĐỘNG (Standardized Buttons) */}
        <div className="flex flex-col gap-3 w-full">
          {/* Nút Manual Override - Phong cách Kính mờ trắng */}
          <button className="group flex items-center justify-between bg-white/90 backdrop-blur-md px-5 py-3.5 rounded-2xl shadow-xl hover:bg-white transition-all active:scale-[0.98] border border-white/20">
            <div className="flex items-center gap-3">
              <Maximize2
                size={18}
                className="text-mekong-navy group-hover:rotate-45 transition-transform"
              />
              <span className="text-[11px] font-black text-mekong-navy uppercase tracking-[0.2em]">
                Manual Override
              </span>
            </div>
            <ChevronRight
              size={14}
              className="text-slate-300 opacity-0 group-hover:opacity-100 -translate-x-2 group-hover:translate-x-0 transition-all"
            />
          </button>

          {/* Nút Report Error - Màu đỏ cảnh báo sắc nét */}
          <button className="group flex items-center gap-3 bg-mekong-critical text-white px-5 py-3.5 rounded-2xl shadow-2xl shadow-red-900/30 hover:bg-red-700 transition-all active:scale-[0.98] border border-white/10">
            <AlertTriangle
              size={18}
              strokeWidth={2.5}
              className="group-hover:animate-bounce"
            />
            <span className="text-[11px] font-black uppercase tracking-[0.2em]">
              Report Sensor Error
            </span>
          </button>
        </div>

        {/* 2. KHỐI AUTO-GATE LOGIC (Logic Status Panel) */}
        <Card
          variant="navy"
          padding="none"
          className="w-full rounded-[32px] bg-[#00203F]/90 backdrop-blur-xl border border-white/10 shadow-2xl overflow-hidden group"
        >
          {/* Decorative Glow */}
          <div className="absolute -right-10 -top-10 w-32 h-32 bg-mekong-cyan/10 rounded-full blur-2xl pointer-events-none" />

          <div className="p-6 relative z-10">
            {/* Header Panel */}
            <div className="flex items-center gap-3 mb-8 text-mekong-cyan">
              <Zap size={20} fill="currentColor" className="animate-pulse" />
              <h3 className="text-[10px] font-black uppercase tracking-[0.3em] leading-none">
                Auto-Gate Logic
              </h3>
            </div>

            {/* List Items - Đã fix lỗi dính chữ và căn lề */}
            <div className="space-y-5">
              {[
                {
                  label: "Hai Tân Node",
                  status: "READY",
                  variant: "optimal" as const,
                },
                {
                  label: "Phú Đông Gate",
                  status: "MONITORING",
                  variant: "warning" as const,
                },
              ].map((item, i) => (
                <div
                  key={i}
                  className="flex items-center justify-between group/item"
                >
                  <span className="text-[13px] font-bold text-slate-400 group-hover/item:text-slate-200 transition-colors">
                    {item.label}
                  </span>
                  {/* Sử dụng Badge chuẩn để đảm bảo kích thước khít 100% */}
                  <Badge
                    variant={item.variant}
                    className={`text-[9px] py-1 px-3 min-w-[90px] text-center justify-center font-black tracking-widest ${
                      item.variant === "optimal"
                        ? "bg-mekong-mint/10 text-mekong-mint"
                        : "bg-amber-500/10 text-amber-500"
                    }`}
                  >
                    {item.status}
                  </Badge>
                </div>
              ))}
            </div>
          </div>

          {/* Footer trang trí siêu mỏng */}
          <div className="h-1 w-full bg-gradient-to-r from-transparent via-mekong-cyan/20 to-transparent" />
        </Card>
      </div>

      {/* --- BOTTOM PANEL: STATION DEEP DIVE --- */}
      <div className="absolute bottom-8 left-8 right-32 z-30">
        <Card
          variant="glass"
          className="rounded-[40px] p-10 shadow-glass border-white/60 backdrop-blur-3xl ring-1 ring-black/5 animate-in slide-in-from-bottom-10 duration-700"
        >
          <div className="flex justify-between items-start mb-8">
            <div className="space-y-1">
              <div className="flex items-center gap-4">
                <h2 className="text-4xl font-black text-mekong-navy tracking-tighter uppercase leading-none">
                  Station: Hai Tân
                </h2>
                <Badge variant="critical" dot className="py-1.5 px-4">
                  Rising Salinity
                </Badge>
              </div>
              <p className="text-sm font-bold text-mekong-slate uppercase tracking-widest opacity-70">
                Mỹ Tho River Entrance | Coord: 10.352, 106.365
              </p>
            </div>
            <button className="p-3 hover:bg-slate-200/50 rounded-full transition-all">
              <X size={24} className="text-mekong-navy" />
            </button>
          </div>

          <div className="grid grid-cols-12 gap-8 items-end">
            <div className="col-span-6 grid grid-cols-2 gap-4">
              {[
                {
                  label: "Live Reading",
                  val: "2.45",
                  unit: "g/L",
                  color: "text-mekong-teal",
                },
                {
                  label: "Tidal Level",
                  val: "+1.2",
                  unit: "m",
                  color: "text-mekong-teal",
                },
                {
                  label: "Wind Velocity",
                  val: "14.2",
                  unit: "km/h",
                  color: "text-mekong-navy",
                },
                {
                  label: "Peak Forecast",
                  val: "3.10",
                  unit: "g/L",
                  color: "text-mekong-navy",
                  bg: "bg-slate-100/50",
                },
              ].map((m, i) => (
                <div
                  key={i}
                  className={`p-6 rounded-3xl border border-white/40 bg-white/40 shadow-sm ${m.bg}`}
                >
                  <p className="text-[9px] font-black text-slate-500 uppercase tracking-widest mb-3">
                    {m.label}
                  </p>
                  <div className="flex items-baseline gap-2">
                    <span
                      className={`text-3xl font-black ${m.color} tracking-tighter`}
                    >
                      {m.val}
                    </span>
                    <span className="text-[10px] font-bold text-slate-400 uppercase">
                      {m.unit}
                    </span>
                  </div>
                </div>
              ))}
            </div>

            {/* Visual Forecast Chart */}
            <div className="col-span-6 h-48 flex items-end gap-3 px-6 relative bg-white/20 rounded-[32px] border border-white/20 p-8">
              {[20, 35, 30, 50, 75, 90, 85, 80].map((h, i) => (
                <div
                  key={i}
                  style={{ height: `${h}%` }}
                  className={`flex-1 rounded-t-xl transition-all duration-700 ${i > 3 ? "bg-mekong-mint shadow-[0_0_15px_#1BAEA6]" : "bg-slate-300"}`}
                />
              ))}
              <div className="absolute top-6 right-8 bg-mekong-navy text-white px-3 py-1.5 rounded-lg text-[9px] font-black uppercase tracking-widest">
                24H History & Forecast
              </div>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default InteractiveMap;
