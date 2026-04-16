import React from "react";
import {
  Target,
  Waves,
  Wind,
  Droplets,
  Maximize2,
  Zap,
  Activity,
  Database,
  Cpu,
  ExternalLink,
  TrendingUp,
  ListChecks,
  ArrowUpRight,
  SlidersHorizontal,
  Compass,
} from "lucide-react";

// Import UI Components đã tối ưu
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Badge } from "../components/ui/Badge";
import { AISentinel } from "../components/dashboard/AISentinel";
import { SatelliteMap } from "../components/dashboard/SatelliteMap";

/**
 * DASHBOARD PAGE - REFACTORED FROM FIGMA
 * --------------------------------------
 * Tối ưu bố cục:
 * - Section 1: Strategic Banner (Full width)
 * - Section 2: Metrics Grid (3 columns)
 * - Section 3: Map (8 cols) & Sidebar (4 cols)
 * - Section 4: Action Logs (Full width)
 */

export const Dashboard = () => {
  return (
    <div className="space-y-10 animate-in fade-in slide-in-from-bottom-4 duration-1000">
      {/* --- STRATEGIC OBJECTIVE: RE-STRUCTURED & PRO LOOK --- */}
      <section className="relative overflow-hidden bg-[#00203F] rounded-[32px] p-7 lg:p-9 text-white shadow-2xl border border-white/10 group transition-all duration-500 hover:border-mekong-cyan/30">
        {/* Hiệu ứng tia sáng kỹ thuật (Tech Glow Overlay) */}
        <div className="absolute top-0 right-0 w-[500px] h-full bg-mekong-cyan/[0.03] rounded-full blur-[120px] pointer-events-none" />

        <div className="relative z-10 flex flex-col lg:flex-row items-center justify-between gap-8">
          {/* KHỐI 1: MỤC TIÊU CHIẾN LƯỢC (Bên trái) */}
          <div className="flex items-center gap-6 flex-1 min-w-0">
            <div className="relative flex-shrink-0">
              {/* Container Icon tinh tế hơn */}
              <div className="w-14 h-14 bg-white/5 rounded-2xl flex items-center justify-center text-mekong-cyan border border-white/10 shadow-inner group-hover:border-mekong-cyan/50 transition-all duration-500">
                <Target
                  size={28}
                  strokeWidth={2.5}
                  className="drop-shadow-[0_0_8px_rgba(117,231,254,0.4)]"
                />
              </div>
              {/* Chấm xanh nhỏ báo hiệu trạng thái Live */}
              <div className="absolute -top-1 -right-1 w-3 h-3 bg-mekong-mint rounded-full border-2 border-[#00203F] animate-pulse" />
            </div>

            <div className="space-y-1.5 truncate">
              <p className="text-[10px] font-black text-slate-400 uppercase tracking-[0.25em] opacity-80 leading-none">
                Strategic Objective
              </p>
              <div className="flex items-center gap-3">
                <h2 className="text-xl lg:text-2xl font-black tracking-tight whitespace-nowrap">
                  Maintain Salinity{" "}
                  <span className="text-mekong-mint ml-1">&lt; 0.5 g/L</span>
                </h2>
                {/* Badge Safe Level nhỏ gọn chuyên nghiệp */}
                <Badge className="bg-mekong-mint/10 text-mekong-mint border-mekong-mint/20 text-[9px] py-0.5 px-2 italic font-bold">
                  Safe Level
                </Badge>
              </div>
            </div>
          </div>

          {/* KHỐI 2: CHỈ SỐ BIẾN THIÊN (Căn giữa) */}
          <div className="flex flex-col items-center lg:items-end lg:px-12 border-l border-white/5">
            <p className="text-[10px] font-black text-slate-500 uppercase tracking-[0.2em] mb-1">
              Current Variance
            </p>
            <div className="flex items-baseline gap-2">
              <span className="text-4xl font-black text-mekong-cyan tracking-tighter drop-shadow-[0_0_15px_rgba(117,231,254,0.3)]">
                -0.05
              </span>
              <span className="text-[11px] font-black text-slate-400 uppercase tracking-widest">
                g/L
              </span>
            </div>
          </div>

          {/* KHỐI 3: NÚT BẤM ĐIỀU CHỈNH (Bên phải - Đã sửa lỗi icon) */}
          <div className="flex-shrink-0">
            <button className="flex items-center gap-3 bg-mekong-cyan text-mekong-navy px-8 h-14 rounded-2xl font-black text-[12px] uppercase tracking-widest shadow-[0_12px_24px_-8px_rgba(117,231,254,0.4)] hover:shadow-[0_16px_32px_-8px_rgba(117,231,254,0.5)] hover:scale-[1.02] active:scale-95 transition-all duration-300 group/btn">
              {/* Icon Sliders đã được căn chỉnh khoảng cách hợp lý */}
              <SlidersHorizontal
                size={16}
                strokeWidth={3}
                className="opacity-80 group-hover/btn:rotate-180 transition-transform duration-500"
              />
              <span>Adjust Thresholds</span>
            </button>
          </div>
        </div>
      </section>

      {/* 2. MAIN METRICS GRID (Dựa trên khối h-44 trong Figma) */}
      {/* --- TOP METRICS ROW: ULTRA PROFESSIONAL DESIGN --- */}
      <div className="grid grid-cols-12 gap-8">
        {/* CARD 1: LIVE SALINITY - Phong cách Teal an toàn */}
        <Card
          isHoverable
          className="col-span-12 lg:col-span-4 p-8 border-none shadow-[0_8px_30px_rgb(0,0,0,0.04)] group relative overflow-hidden bg-white min-h-[280px] flex flex-col justify-between"
        >
          {/* Hiệu ứng tia sáng mờ ở góc (Decorative Glow) */}
          <div className="absolute -top-10 -right-10 w-40 h-40 bg-mekong-mint/10 rounded-full blur-3xl group-hover:bg-mekong-mint/20 transition-colors duration-500" />

          <div className="relative z-10 flex justify-between items-start">
            <div className="flex items-center gap-4">
              <div className="bg-mekong-teal/10 p-3 rounded-2xl text-mekong-teal border border-mekong-teal/20 shadow-sm group-hover:scale-110 transition-transform">
                <Droplets size={24} strokeWidth={2.5} />
              </div>
              <div className="space-y-0.5">
                <p className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] leading-none">
                  Live Salinity
                </p>
                <Badge
                  variant="optimal"
                  className="bg-mekong-mint/10 text-mekong-mint border-none px-2 py-0.5 text-[9px] font-bold"
                >
                  NODE S-04
                </Badge>
              </div>
            </div>
            {/* Badge trạng thái "Sống" */}
            <div className="flex items-center gap-1.5 px-2 py-1 bg-slate-50 rounded-full border border-slate-100">
              <div className="w-1.5 h-1.5 bg-mekong-mint rounded-full animate-pulse shadow-[0_0_8px_#1BAEA6]" />
              <span className="text-[9px] font-black text-mekong-navy uppercase tracking-tighter">
                LIVE
              </span>
            </div>
          </div>

          <div className="relative z-10 flex items-baseline gap-3">
            <span className="text-7xl font-black text-mekong-navy tracking-tighter leading-none drop-shadow-sm">
              0.45
            </span>
            <span className="text-xl font-black text-slate-400 uppercase tracking-widest leading-none">
              g/L
            </span>
          </div>

          <div className="relative z-10 pt-6 border-t border-slate-50 flex justify-between items-center">
            <div className="flex items-center gap-2">
              <Activity size={14} className="text-mekong-teal" />
              <span className="text-[11px] font-bold text-slate-500 uppercase tracking-widest">
                Stable for 4h
              </span>
            </div>
            <div className="text-[9px] font-black text-mekong-teal bg-mekong-teal/5 px-2 py-1 rounded border border-mekong-teal/10 uppercase">
              99.2% Accuracy
            </div>
          </div>
        </Card>

        {/* CARD 2: TIDAL LEVEL - Phong cách Alerting chuyên nghiệp */}
        <Card
          isHoverable
          className="col-span-12 lg:col-span-4 p-8 border-none shadow-[0_8px_30px_rgb(0,0,0,0.04)] group bg-white min-h-[280px] flex flex-col justify-between border-t-4 border-t-mekong-critical/20"
        >
          <div className="flex justify-between items-start">
            <div className="flex items-center gap-4">
              <div className="bg-slate-100 p-3 rounded-2xl text-mekong-navy border border-slate-200 group-hover:scale-110 transition-transform">
                <Waves size={24} strokeWidth={2.5} />
              </div>
              <div className="space-y-0.5">
                <p className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] leading-none">
                  Tidal Level
                </p>
                <Badge className="bg-slate-100 text-slate-500 border-none px-2 py-0.5 text-[9px] font-bold">
                  STATION #02
                </Badge>
              </div>
            </div>
          </div>

          <div className="flex items-baseline gap-3">
            <span className="text-7xl font-black text-mekong-navy tracking-tighter leading-none">
              +1.2
            </span>
            <span className="text-xl font-black text-slate-400 uppercase tracking-widest">
              meters
            </span>
          </div>

          <div className="pt-6 border-t border-slate-50">
            <div className="flex items-center gap-2.5 px-3 py-2 bg-red-50 rounded-2xl border border-red-100/50 text-mekong-critical shadow-sm">
              <TrendingUp
                size={16}
                strokeWidth={3}
                className="animate-bounce"
              />
              <div className="flex flex-col">
                <span className="text-[11px] font-black uppercase tracking-widest leading-none">
                  High Tide Peak
                </span>
                <span className="text-[9px] font-bold opacity-70">
                  Estimated in 22 minutes
                </span>
              </div>
            </div>
          </div>
        </Card>

        {/* CARD 3: WIND / VELOCITY - Phong cách Scientific Grid */}
        <Card
          isHoverable
          className="col-span-12 lg:col-span-4 p-8 border-none shadow-[0_8px_30px_rgb(0,0,0,0.04)] group bg-white min-h-[280px] flex flex-col justify-between relative overflow-hidden"
        >
          {/* Grid trang trí cực mờ (Subtle Background Grid) */}
          <div className="absolute inset-0 opacity-[0.03] pointer-events-none bg-[radial-gradient(#00203f_1px,transparent_1px)] [background-size:16px_16px]" />

          <div className="relative z-10 flex justify-between items-start">
            <div className="flex items-center gap-4">
              <div className="bg-slate-100 p-3 rounded-2xl text-mekong-navy border border-slate-200 group-hover:scale-110 transition-transform">
                <Wind size={24} strokeWidth={2.5} />
              </div>
              <p className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] leading-none">
                Wind / Velocity
              </p>
            </div>
          </div>

          <div className="relative z-10 flex items-center gap-10">
            <div className="flex items-baseline gap-2">
              <span className="text-7xl font-black text-mekong-navy tracking-tighter leading-none">
                12
              </span>
              <span className="text-sm font-black text-slate-400 uppercase">
                km/h
              </span>
            </div>
            <div className="h-14 w-px bg-slate-100" />
            <div className="flex flex-col">
              <span className="text-4xl font-black text-mekong-navy tracking-tighter">
                SE
              </span>
              <span className="text-[9px] font-black text-slate-400 uppercase tracking-widest">
                Direction
              </span>
            </div>
          </div>

          <div className="relative z-10 pt-6 border-t border-slate-50 flex items-center gap-2">
            <Compass size={14} strokeWidth={2.5} className="text-slate-400" />
            <span className="text-[11px] font-bold text-slate-500 uppercase tracking-widest leading-none">
              Dominant pushing inland
            </span>
          </div>
        </Card>
      </div>

      {/* 3. CENTER GRID: MAP & AI SIDEBAR */}
      <div className="grid grid-cols-12 gap-8 items-start">
        {/* LEFT: HOTSPOTS MAP (Dựa trên khối h-80 trong Figma) */}
        {/* --- PHẦN MAP TRÊN DASHBOARD --- */}
        <div className="col-span-12 lg:col-span-8">
          <Card
            padding="none"
            className="h-[520px] relative overflow-hidden rounded-[40px] shadow-soft group border-none"
          >
            {/* 1. Floating Info Header (Kính mờ) */}
            <div className="absolute top-8 left-8 z-10 bg-white/90 backdrop-blur-xl p-6 rounded-[28px] shadow-2xl border border-white/50 ring-1 ring-black/5">
              <h3 className="text-lg font-black text-mekong-navy tracking-tighter leading-none mb-1">
                Salinity Hotspots
              </h3>
              <p className="text-[10px] font-black text-mekong-slate uppercase tracking-[0.15em]">
                TIỀN GIANG - BẾN TRE REGION
              </p>
            </div>

            {/* 2. GỌI COMPONENT BẢN ĐỒ VỆ TINH THẬT Ở ĐÂY */}
            <Card
              padding="none"
              className="h-[520px] relative overflow-hidden rounded-[40px] shadow-soft group border-none"
            >
              {/* Header và các thành phần khác giữ nguyên */}
              <div className="w-full h-full">
                <SatelliteMap />
              </div>
            </Card>

            {/* 3. Lớp phủ mờ trang trí (Overlay) để đồng bộ màu sắc dự án */}
            <div className="absolute inset-0 bg-mekong-navy/10 pointer-events-none z-[1]" />

            {/* 4. Nút Open Full Map */}
            <button className="absolute bottom-8 left-8 z-10 bg-mekong-navy text-white px-6 py-3 rounded-xl font-black text-xs flex items-center gap-2 shadow-2xl hover:bg-mekong-teal transition-all active:scale-95">
              OPEN FULL MAP <ExternalLink size={16} />
            </button>
          </Card>
        </div>

        {/* RIGHT: AI SENTINEL & STATUS (Dựa trên khối sky-950 p-6 trong Figma) */}
        <div className="col-span-12 lg:col-span-4 space-y-8">
          <AISentinel />
        </div>
      </div>

      {/* --- BOTTOM SECTION: COMPACT & PROFESSIONAL LAYOUT --- */}
      <div className="grid grid-cols-12 gap-8 items-stretch">
        {/* KHỐI 1: RECENT AUTONOMOUS ACTIONS (Chiếm 8 cột) */}
        <Card
          variant="white"
          className="col-span-12 lg:col-span-8 p-6 lg:p-8 border-none shadow-soft flex flex-col rounded-[32px]"
        >
          {/* Header Section - Đã thu gọn mb-10 xuống mb-6 */}
          <div className="flex justify-between items-center mb-6">
            <div className="flex items-center gap-3">
              <div className="p-2.5 bg-mekong-navy rounded-xl text-mekong-cyan shadow-md shadow-mekong-navy/20">
                <Zap size={20} fill="currentColor" />
              </div>
              <h3 className="text-lg font-black text-mekong-navy uppercase tracking-tighter leading-none">
                Recent Autonomous Actions
              </h3>
            </div>
            <button className="text-[10px] font-black text-mekong-teal uppercase tracking-widest flex items-center gap-1.5 hover:text-mekong-navy transition-colors border-b border-mekong-teal/20 pb-0.5">
              View Complete Logs <ArrowUpRight size={12} />
            </button>
          </div>

          {/* Danh sách hành động - Đã thu hẹp khoảng cách để khít hơn */}
          {/* --- RECENT AUTONOMOUS ACTIONS: MAXIMIZED CARDS --- */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {[
              {
                time: "14:15",
                title: "Gate Closing",
                desc: "Hòa Định Sluice Gate #04 secured to prevent 0.8g/L inflow into the agricultural zone.",
                color: "border-mekong-navy",
                glow: "shadow-mekong-navy/10",
              },
              {
                time: "13:50",
                title: "Regional SMS Alert",
                desc: "Emergency warning sent to 1,240 registered rice farmers in the Bến Tre region.",
                color: "border-mekong-teal",
                glow: "shadow-mekong-teal/10",
              },
              {
                time: "12:30",
                title: "Pump Optimization",
                desc: "Flow rates adjusted at Cai Lay pumping station for maximum freshwater efficiency.",
                color: "border-mekong-cyan",
                glow: "shadow-mekong-cyan/10",
              },
            ].map((action, i) => (
              <div
                key={i}
                className={`
        flex flex-col justify-between gap-6 p-8 rounded-[32px] bg-slate-50/50 
        border-l-[8px] ${action.color} min-h-[220px]
        group hover:bg-white hover:shadow-2xl hover:translate-y--1
        transition-all duration-500 cursor-pointer relative overflow-hidden
      `}
              >
                {/* Header của Card con: Time & Status dot */}
                <div className="flex justify-between items-center relative z-10">
                  <span className="text-[12px] font-black text-slate-400 uppercase tracking-[0.2em]">
                    {action.time}
                  </span>
                  <div className="w-2 h-2 rounded-full bg-slate-200 group-hover:bg-mekong-teal animate-pulse" />
                </div>

                {/* Body: Nội dung được phóng to */}
                <div className="space-y-3 relative z-10">
                  <h4 className="text-[17px] font-black text-mekong-navy group-hover:text-mekong-teal transition-colors leading-none uppercase tracking-tight">
                    {action.title}
                  </h4>
                  <p className="text-[13px] text-slate-500 font-semibold leading-relaxed opacity-90">
                    {action.desc}
                  </p>
                </div>

                {/* Footer trang trí nhỏ để tăng độ chuyên nghiệp */}
                <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity duration-500">
                  <span className="text-[9px] font-black text-mekong-teal uppercase tracking-widest">
                    View Audit Trail
                  </span>
                  <ArrowUpRight size={12} className="text-mekong-teal" />
                </div>

                {/* Decorative Glow khi hover */}
                <div
                  className={`absolute -right-10 -bottom-10 w-32 h-32 rounded-full blur-3xl opacity-0 group-hover:opacity-20 transition-opacity ${action.color.replace("border", "bg")}`}
                />
              </div>
            ))}
          </div>
        </Card>

        {/* KHỐI 2: INFRASTRUCTURE STATUS (Chiếm 4 cột) */}
        <Card
          variant="white"
          className="col-span-12 lg:col-span-4 p-6 lg:p-8 border-none shadow-soft rounded-[32px] flex flex-col"
        >
          <div className="flex items-center gap-3 mb-6 border-b border-slate-50 pb-4">
            <ListChecks size={20} className="text-mekong-navy" />
            <h3 className="text-xs font-black text-mekong-navy uppercase tracking-[0.15em]">
              Infrastructure Status
            </h3>
          </div>

          {/* Nội dung Status - Đã thu gọn khoảng cách giữa các hàng */}
          <div className="flex-1 flex flex-col justify-center space-y-5">
            {[
              {
                icon: Activity,
                label: "Sensor Connectivity",
                val: "98.2%",
                color: "text-mekong-mint",
              },
              {
                icon: Database,
                label: "Remote Station Power",
                val: "84% Avg",
                color: "text-mekong-navy",
              },
              {
                icon: Cpu,
                label: "Model Accuracy",
                val: "99.4%",
                color: "text-mekong-mint",
              },
            ].map((item, i) => (
              <div
                key={i}
                className="flex items-center justify-between group cursor-default"
              >
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-slate-50 rounded-lg text-slate-400 group-hover:text-mekong-teal transition-all">
                    <item.icon size={27} strokeWidth={2.5} />
                  </div>
                  <span className="text-[12px] font-bold text-slate-500">
                    {item.label}
                  </span>
                </div>
                <span
                  className={`text-[13px] font-black ${item.color} tracking-tighter`}
                >
                  {item.val}
                </span>
              </div>
            ))}
          </div>

          {/* Footer trang trí siêu nhỏ */}
          {/* --- FOOTER: ĐÃ ĐƯỢC LÀM TO VÀ ẤN TƯỢNG HƠN --- */}
          <div className="mt-10 pt-8 border-t border-slate-50 flex flex-col items-center justify-center gap-4">
            {/* Khối trạng thái dạng Pill (Viên thuốc) cao cấp */}
            <div className="flex items-center gap-4 px-6 py-2.5 bg-slate-50 rounded-full border border-slate-100 shadow-inner group cursor-default hover:bg-white transition-all duration-500">
              {/* Hiệu ứng Đèn tín hiệu AI (Double Pulse) */}
              <div className="relative flex items-center justify-center w-3 h-3">
                {/* Vòng tròn tỏa sáng lan rộng */}
                <div className="absolute inset-0 bg-mekong-mint rounded-full animate-ping opacity-40 scale-150" />
                {/* Chấm tâm điểm nhấp nháy nhịp thở */}
                <div className="relative w-2.5 h-2.5 bg-mekong-mint rounded-full animate-pulse shadow-[0_0_12px_rgba(27,234,166,0.6)]" />
              </div>

              {/* Text: To hơn, dãn chữ cực rộng (0.4em) tạo sự sang trọng */}
              <span className="text-[12px] font-black text-mekong-navy uppercase tracking-[0.4em] leading-none select-none">
                System Health:{" "}
                <span className="text-mekong-teal drop-shadow-sm">Nominal</span>
              </span>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default Dashboard;
