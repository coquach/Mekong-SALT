import React from "react";
import {
  Waves,
  Wind,
  ArrowDownToLine,
  TrendingUp,
  AlertCircle,
  Zap,
  Bell,
  Signal,
  Navigation,
  CheckCircle2,
  History as HistoryIcon,
  ArrowUpRight,
  Target,
  Clock,
  ChevronRight,
  MousePointer2,
  Info,
  Sliders,
} from "lucide-react";

// Import UI Components đã tối ưu ở các bước trước
import { Card, CardContent } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Badge } from "../components/ui/Badge";

export const History = () => {
  return (
    <div className="space-y-10 animate-in fade-in slide-in-from-bottom-4 duration-1000">
      {/* --- 1. TOP NAVIGATION & NODE IDENTITY --- */}
      <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-6 border-b border-slate-200 pb-8">
        <div className="flex items-center gap-5">
          <div className="w-14 h-14 bg-mekong-navy rounded-[20px] flex items-center justify-center text-white shadow-xl ring-4 ring-slate-100">
            <Target size={28} strokeWidth={2.5} />
          </div>
          <div className="space-y-1">
            <div className="flex items-center gap-3 text-[11px] font-black text-slate-400 uppercase tracking-[0.3em]">
              <span className="bg-slate-100 px-2 py-0.5 rounded">
                Telemetry Node
              </span>
              <span className="text-mekong-teal">Tien River / Region S-04</span>
            </div>
            <h1 className="text-4xl lg:text-5xl font-black text-mekong-navy tracking-tighter uppercase leading-none">
              Node 04 Deep Dive
            </h1>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className="flex bg-slate-100 p-1.5 rounded-[20px] border border-slate-200 shadow-inner">
            {["Overview", "Forensics", "Forecast"].map((t, i) => (
              <button
                key={t}
                className={`px-6 py-2.5 text-[11px] font-black uppercase tracking-widest rounded-xl transition-all ${i === 1 ? "bg-white text-mekong-navy shadow-md" : "text-slate-500 hover:text-mekong-navy"}`}
              >
                {t}
              </button>
            ))}
          </div>
          <button className="p-3.5 bg-white border border-slate-200 rounded-2xl text-slate-400 hover:text-mekong-teal transition-all shadow-sm group">
            <Bell
              size={22}
              className="group-hover:rotate-12 transition-transform"
            />
          </button>
        </div>
      </div>

      {/* --- 2. SUMMARY DASHETTE --- */}
      <div className="flex justify-between items-start">
        <p className="text-base lg:text-lg text-mekong-slate font-medium max-w-2xl leading-relaxed">
          Phân tích lịch sử toàn diện và đánh giá rủi ro dựa trên AI cho hành
          lang Sông Tiền. Hệ thống đang đối chiếu dữ liệu cảm biến với mô hình
          thủy văn đệ quy v4.2.
        </p>

        {/* Current Readout Card */}
        <div className="bg-white border border-slate-100 p-6 shadow-xl rounded-[28px] flex items-center gap-8 min-w-[320px] relative overflow-hidden group">
          <div className="absolute top-0 left-0 w-2 h-full bg-mekong-critical" />
          <div className="space-y-1">
            <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">
              Live Salinity
            </p>
            <div className="flex items-baseline gap-2">
              <span className="text-5xl font-black text-mekong-navy tracking-tighter">
                2.8
              </span>
              <span className="text-lg font-black text-slate-400 uppercase">
                g/L
              </span>
            </div>
          </div>
          <div className="ml-auto text-right space-y-2">
            <div className="bg-red-50 text-mekong-critical px-3 py-1 rounded-lg text-[11px] font-black flex items-center gap-1 shadow-sm border border-red-100">
              <TrendingUp size={14} strokeWidth={3} /> +100%
            </div>
            <p className="text-[9px] font-bold text-slate-400 uppercase tracking-widest">
              Vs. Baseline
            </p>
          </div>
        </div>
      </div>

      {/* --- 3. TREND ANALYSIS & BENCHMARKS --- */}
      <div className="grid grid-cols-12 gap-8 items-stretch">
        {/* AREA CHART BLOCK (8 columns) */}
        <div className="col-span-12 lg:col-span-8">
          <Card
            variant="white"
            padding="lg"
            className="h-full rounded-[40px] shadow-soft relative overflow-hidden flex flex-col"
          >
            <div className="flex justify-between items-center mb-12">
              <div className="space-y-1">
                <h3 className="text-xl font-black text-mekong-navy uppercase tracking-tighter">
                  Longitudinal Trend Analysis
                </h3>
                <p className="text-[11px] text-slate-400 font-bold uppercase tracking-widest opacity-70">
                  30-Day temporal salinity variance
                </p>
              </div>
              <div className="flex bg-slate-50 p-1.5 rounded-xl border border-slate-100">
                {["1W", "1M", "3M"].map((period, i) => (
                  <button
                    key={period}
                    className={`px-5 py-2 text-[10px] font-black rounded-lg transition-all ${i === 1 ? "bg-mekong-navy text-white shadow-lg" : "text-slate-400 hover:text-mekong-navy"}`}
                  >
                    {period}
                  </button>
                ))}
              </div>
            </div>

            {/* HIGH-END SVG AREA CHART */}
            <div className="relative flex-1 min-h-[320px] w-full px-4 group mt-4">
              <div className="absolute left-0 h-full flex flex-col justify-between text-[11px] font-black text-slate-300 pr-6 pb-8">
                <span>4.0</span>
                <span>3.0</span>
                <span>2.0</span>
                <span>1.0</span>
                <span>0.0</span>
              </div>
              <div className="absolute inset-0 flex flex-col justify-between pointer-events-none pl-10 pb-8">
                {[...Array(5)].map((_, i) => (
                  <div
                    key={i}
                    className="w-full border-t border-slate-100/60"
                  />
                ))}
              </div>

              {/* Danger Zone Indicator */}
              <div className="absolute bottom-[52%] w-full pl-10 border-t-2 border-mekong-critical/30 border-dashed z-10 flex justify-end items-start pointer-events-none">
                <div className="bg-red-50/90 backdrop-blur-sm px-4 py-1.5 rounded-xl border border-red-100 shadow-sm -mt-4 mr-6">
                  <span className="text-[10px] font-black text-mekong-critical uppercase tracking-[0.2em]">
                    Danger Threshold (2.0 g/L)
                  </span>
                </div>
              </div>

              {/* Chart Graphics */}
              <div className="absolute inset-0 pl-10 h-full pb-8">
                <svg
                  className="w-full h-full overflow-visible"
                  preserveAspectRatio="none"
                  viewBox="0 0 1000 300"
                >
                  <defs>
                    <linearGradient
                      id="lineGrad"
                      x1="0%"
                      y1="0%"
                      x2="100%"
                      y2="0%"
                    >
                      <stop offset="0%" stopColor="#2DD4BF" />
                      <stop offset="60%" stopColor="#006877" />
                      <stop offset="100%" stopColor="#BA1A1A" />
                    </linearGradient>
                    <linearGradient
                      id="areaGrad"
                      x1="0%"
                      y1="0%"
                      x2="0%"
                      y2="100%"
                    >
                      <stop
                        offset="0%"
                        stopColor="#006877"
                        stopOpacity="0.15"
                      />
                      <stop offset="100%" stopColor="#006877" stopOpacity="0" />
                    </linearGradient>
                    <filter
                      id="softGlow"
                      x="-20%"
                      y="-20%"
                      width="140%"
                      height="140%"
                    >
                      <feGaussianBlur stdDeviation="5" result="blur" />
                      <feComposite
                        in="SourceGraphic"
                        in2="blur"
                        operator="over"
                      />
                    </filter>
                  </defs>
                  <path
                    d="M 0 220 Q 150 230 300 190 T 500 170 T 750 140 T 1000 100 L 1000 300 L 0 300 Z"
                    fill="url(#areaGrad)"
                  />
                  <path
                    d="M 0 220 Q 150 230 300 190 T 500 170 T 750 140 T 1000 100"
                    fill="none"
                    stroke="url(#lineGrad)"
                    strokeWidth="10"
                    strokeLinecap="round"
                    filter="url(#softGlow)"
                    className="animate-in slide-in-from-left-full duration-[2000ms] ease-out"
                  />
                  <g className="animate-pulse">
                    <circle
                      cx="1000"
                      cy="100"
                      r="14"
                      fill="#BA1A1A"
                      fillOpacity="0.2"
                    />
                    <circle
                      cx="1000"
                      cy="100"
                      r="7"
                      fill="#BA1A1A"
                      stroke="white"
                      strokeWidth="3"
                    />
                  </g>
                </svg>
              </div>

              {/* Timeline labels */}
              <div className="absolute bottom-0 left-0 w-full pl-10 flex justify-between text-[11px] font-black text-slate-400 uppercase tracking-[0.3em]">
                <span>Mar 01</span>
                <span className="opacity-30">Mar 10</span>
                <span>Mar 20</span>
                <span className="text-mekong-navy">Mar 29 (Live)</span>
              </div>
            </div>
          </Card>
        </div>

        {/* HISTORICAL BENCHMARKS (4 columns) */}
        <div className="col-span-12 lg:col-span-4">
          <Card
            variant="white"
            padding="lg"
            className="h-full bg-slate-50/50 border-none shadow-soft rounded-[40px] flex flex-col justify-between"
          >
            <div>
              <div className="flex items-center gap-4 mb-10">
                <div className="p-3 bg-mekong-navy rounded-2xl text-white shadow-lg">
                  <HistoryIcon size={22} />
                </div>
                <h3 className="text-sm font-black text-mekong-navy uppercase tracking-widest leading-none">
                  Historical Benchmarks
                </h3>
              </div>

              <div className="space-y-6">
                {[
                  {
                    year: "March 2024 (Now)",
                    val: "2.8 g/L",
                    color: "text-mekong-critical",
                    active: true,
                  },
                  {
                    year: "March 2023",
                    val: "1.4 g/L",
                    color: "text-mekong-navy",
                    active: false,
                  },
                  {
                    year: "March 2022",
                    val: "1.1 g/L",
                    color: "text-mekong-navy",
                    active: false,
                  },
                ].map((row, i) => (
                  <div
                    key={i}
                    className={`flex justify-between items-center p-5 rounded-[24px] border transition-all duration-300 ${row.active ? "bg-white shadow-xl border-red-100 scale-105" : "bg-white/40 border-slate-200 hover:bg-white"}`}
                  >
                    <span className="text-[11px] font-black text-slate-500 uppercase tracking-widest">
                      {row.year}
                    </span>
                    <span
                      className={`text-xl font-black ${row.color} tracking-tighter`}
                    >
                      {row.val}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            <div className="mt-10 p-6 bg-mekong-critical/5 rounded-[32px] border border-mekong-critical/10 flex gap-4 relative overflow-hidden group">
              <div className="absolute top-0 right-0 p-4 opacity-5 rotate-12 group-hover:rotate-0 transition-transform duration-700">
                <TrendingUp size={80} />
              </div>
              <TrendingUp
                size={32}
                className="text-mekong-critical shrink-0"
                strokeWidth={2.5}
              />
              <p className="text-[14px] font-bold text-mekong-critical leading-relaxed">
                Độ mặn hiện tại đang cao hơn{" "}
                <span className="underline decoration-2 underline-offset-4 font-black">
                  100%
                </span>{" "}
                so với trung bình lịch sử 3 năm qua.
              </p>
            </div>
          </Card>
        </div>
      </div>

      {/* --- AI DIAGNOSTICS & DIRECTIVES ROW (8 : 4 Ratio or 1:1 depending on preference) --- */}
      <div className="grid grid-cols-12 gap-8 items-stretch">
        {/* KHỐI 1: AI RISK FORENSICS (CAUSAL ATTRIBUTION) - 6 Columns */}
        <div className="col-span-12 lg:col-span-6">
          <Card
            variant="navy"
            padding="none"
            className="bg-[#00203F] text-white rounded-[40px] shadow-2xl h-full relative overflow-hidden flex flex-col border border-white/5"
          >
            <div className="absolute top-0 right-0 w-80 h-80 bg-mekong-cyan/5 rounded-full blur-[100px] pointer-events-none" />

            {/* Header Block */}
            <div className="p-10 pb-6 relative z-10">
              <div className="flex items-center gap-3 mb-10">
                <div className="w-2 h-2 bg-mekong-cyan rounded-full animate-pulse shadow-[0_0_10px_#75E7FE]" />
                <span className="text-[11px] font-black text-slate-400 uppercase tracking-[0.4em]">
                  AI Risk Forensics
                </span>
              </div>
              <h3 className="text-3xl font-black text-white mb-12 tracking-tighter leading-tight uppercase max-w-md">
                Causal attribution <br /> for 2.8 g/L anomaly
              </h3>

              {/* Metrics List */}
              <div className="space-y-8">
                {[
                  {
                    icon: Waves,
                    label: "Tidal Surge",
                    val: "+1.2m",
                    color: "text-mekong-cyan",
                  },
                  {
                    icon: Wind,
                    label: "Wind Velocity",
                    val: "12km/h SE",
                    color: "text-white",
                  },
                  {
                    icon: ArrowDownToLine,
                    label: "Upstream Flow",
                    val: "-22% vs Avg",
                    color: "text-mekong-critical",
                  },
                ].map((row, i) => (
                  <div
                    key={i}
                    className="flex items-center justify-between py-2 border-b border-white/5 group cursor-default"
                  >
                    <div className="flex items-center gap-5">
                      <div className="p-3 bg-white/5 rounded-2xl text-slate-400 group-hover:text-mekong-cyan group-hover:bg-white/10 transition-all border border-white/5 shadow-inner">
                        <row.icon size={22} strokeWidth={2.5} />
                      </div>
                      <span className="text-[14px] font-black text-slate-300 uppercase tracking-widest">
                        {row.label}
                      </span>
                    </div>
                    <span
                      className={`text-2xl font-black ${row.color} tracking-tighter`}
                    >
                      {row.val}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Bottom Insight Quote */}
            <div className="mt-auto p-8 bg-white/[0.03] backdrop-blur-md border-t border-white/5 relative z-10">
              <div className="flex gap-5 items-start">
                <Info
                  size={24}
                  className="text-mekong-cyan shrink-0 mt-1 opacity-80"
                />
                <p className="text-[14px] text-blue-100/70 font-semibold leading-relaxed italic pr-4">
                  "Sự hội tụ của triều cường cực đại và lưu lượng nước ngọt
                  thượng nguồn suy giảm kỷ lục là tác nhân chính gây ra nêm mặn
                  hiện tại."
                </p>
              </div>
            </div>
          </Card>
        </div>

        {/* KHỐI 2: AI ACTIVE DIRECTIVES - 6 Columns */}
        <div className="col-span-12 lg:col-span-6">
          <Card
            variant="white"
            padding="none"
            className="rounded-[40px] shadow-2xl border border-slate-100 flex flex-col h-full overflow-hidden relative"
          >
            {/* Thanh màu Navy ở đỉnh Card tạo sự phân cấp */}
            <div className="h-2 w-full bg-mekong-navy opacity-90" />

            <div className="p-10 flex-1 flex flex-col">
              {/* Header Panel */}
              <div className="flex items-center gap-4 text-mekong-navy mb-14">
                <div className="p-2.5 bg-mekong-cyan/10 rounded-xl text-mekong-teal border border-mekong-cyan/20">
                  <Zap size={22} fill="currentColor" />
                </div>
                <h3 className="text-[14px] font-black uppercase tracking-[0.25em] leading-none">
                  AI Active Directives
                </h3>
              </div>

              {/* Timeline Style List */}
              <div className="space-y-12 relative flex-1">
                {/* Vertical Dotted Line */}
                <div className="absolute top-2 left-1.5 bottom-8 w-px border-l-2 border-dashed border-slate-200" />

                {[
                  {
                    cat: "INFRASTRUCTURE",
                    msg: "Đề xuất đóng cống hoàn toàn thêm 4 chu kỳ triều.",
                    icon: Sliders,
                  },
                  {
                    cat: "AGRICULTURE",
                    msg: "Dừng mọi hoạt động lấy nước tại Phân khu S-12.",
                    icon: Waves,
                  },
                  {
                    cat: "MONITORING",
                    msg: "Triển khai thiết bị quan trắc lưu động đến tọa độ Cửa Tiểu.",
                    icon: Signal,
                  },
                ].map((item, i) => (
                  <div key={i} className="relative pl-12 group cursor-pointer">
                    {/* Bullet Point */}
                    <div className="absolute top-1 left-0 w-3.5 h-3.5 rounded-full bg-white border-2 border-slate-200 group-hover:border-mekong-teal group-hover:bg-mekong-teal transition-all shadow-sm" />

                    <div className="space-y-2">
                      <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest flex items-center gap-2 group-hover:text-mekong-teal transition-colors">
                        <item.icon size={12} strokeWidth={3} /> {item.cat}
                      </p>
                      <h4 className="text-[17px] font-bold text-mekong-navy leading-snug group-hover:text-mekong-teal transition-colors">
                        {item.msg}
                      </h4>
                    </div>
                  </div>
                ))}
              </div>

              {/* Call to Action Button */}
              <div className="mt-14">
                <button className="w-full h-16 bg-[#00203F] text-white rounded-[24px] font-black text-[13px] uppercase tracking-[0.3em] flex items-center justify-center gap-4 shadow-xl hover:shadow-mekong-navy/30 hover:scale-[1.01] active:scale-95 transition-all group">
                  <span>Execute All Directives</span>
                  <ArrowUpRight
                    size={20}
                    className="group-hover:translate-x-1 group-hover:-translate-y-1 transition-transform"
                  />
                </button>
              </div>
            </div>
          </Card>
        </div>
      </div>

      {/* --- 5. SYSTEM BREACH BANNER --- */}
      <section className="bg-mekong-critical p-10 rounded-[48px] text-white shadow-[0_30px_60px_-12px_rgba(186,26,26,0.4)] flex flex-col md:flex-row justify-between items-center gap-8 animate-pulse relative overflow-hidden group">
        <div className="absolute inset-0 bg-[url('https://www.transparenttextures.com/patterns/carbon-fibre.png')] opacity-10 pointer-events-none" />
        <div className="flex items-center gap-8 relative z-10">
          <div className="w-20 h-20 bg-white/20 rounded-[24px] flex items-center justify-center border border-white/40 shadow-inner group-hover:scale-110 transition-transform">
            <AlertCircle size={48} />
          </div>
          <div className="space-y-1">
            <h4 className="text-3xl font-black tracking-tighter uppercase leading-none">
              Threshold Breach Detected
            </h4>
            <p className="text-[14px] font-black text-white/90 uppercase tracking-[0.2em]">
              CẢNH BÁO: ĐỘ MẶN 2.8 g/L VƯỢT NGƯỠNG AN TOÀN CHO LÚA ST25
            </p>
          </div>
        </div>
        <Button
          variant="outline"
          className="border-white text-white hover:bg-white hover:text-mekong-critical px-12 h-16 text-[13px] font-black relative z-10 shadow-2xl backdrop-blur-md"
        >
          ACTIVATE EMERGENCY PROTOCOL
        </Button>
      </section>
    </div>
  );
};

export default History;
