import React from "react";
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
  Waves,
  Wind,
  History as HistoryIcon,
  Radio,
  MapPin,
  Cpu,
  ArrowUpRight,
} from "lucide-react";

// Import UI Components đã build
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Badge } from "../components/ui/Badge";

export const StrategyOrchestration = () => {
  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-1000">
      {/* 1. PAGE HEADER SECTION */}
      <div className="flex flex-col lg:flex-row justify-between items-start lg:items-end gap-6">
        <div className="space-y-3">
          <h1 className="text-4xl lg:text-5xl font-black text-mekong-navy tracking-tighter leading-none uppercase">
            Strategy Orchestration
          </h1>
          <p className="text-base text-mekong-slate font-medium max-w-3xl leading-relaxed">
            Hệ thống SALT-Agent đang đánh giá dự báo thủy triều 48 giờ cùng các
            biến số áp lực gió thời gian thực tại khu vực hạ lưu Sông Hậu.
          </p>
        </div>
        <div className="flex gap-4 w-full lg:w-auto">
          <div className="flex items-center gap-3 px-5 py-3 bg-white rounded-2xl border border-slate-100 shadow-sm flex-1 lg:flex-none justify-center">
            <div className="w-2 h-2 bg-mekong-mint rounded-full animate-pulse shadow-[0_0_8px_#1BAEA6]" />
            <span className="text-[11px] font-black text-mekong-navy uppercase tracking-widest">
              Reasoning Engine: Active
            </span>
          </div>
          <Button
            variant="navy"
            className="flex-1 lg:flex-none h-14 px-8 shadow-xl shadow-mekong-navy/20"
          >
            <Settings2 size={18} className="mr-2" /> Optimize Plan
          </Button>
        </div>
      </div>

      {/* 2. MAIN WORKFLOW & MAPPING GRID */}
      <div className="grid grid-cols-12 gap-8">
        {/* Left Column: Workflow Stepper (8 cols) */}
        <div className="col-span-12 lg:col-span-8">
          <Card
            variant="white"
            padding="lg"
            className="h-full border-l-[6px] border-l-mekong-teal rounded-[40px] shadow-soft relative overflow-hidden"
          >
            <div className="flex justify-between items-center mb-16">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-mekong-navy rounded-xl text-white shadow-lg">
                  <Zap size={18} fill="currentColor" />
                </div>
                <h3 className="text-[13px] font-black text-mekong-navy uppercase tracking-[0.2em]">
                  Current Strategy Workflow
                </h3>
              </div>
              <Badge
                variant="cyan"
                className="bg-mekong-cyan/10 text-mekong-teal border-none px-4 py-1.5 font-black uppercase tracking-widest text-[10px]"
              >
                Goal-Driven Planning
              </Badge>
            </div>

            {/* Workflow Stepper Visualization */}
            <div className="relative flex justify-between items-start px-4 mb-20">
              {/* Background Connecting Line */}
              <div className="absolute top-8 left-10 right-10 h-1 bg-slate-50 rounded-full" />
              {/* Progress Line */}
              <div
                className="absolute top-8 left-10 h-1 bg-mekong-teal rounded-full transition-all duration-1000 shadow-[0_0_10px_#006877]"
                style={{ width: "45%" }}
              />

              {[
                {
                  id: 1,
                  icon: Database,
                  label: "Data Acquisition",
                  sub: "Sensor & API Mesh",
                  status: "COMPLETED",
                  color: "teal",
                },
                {
                  id: 2,
                  icon: LineChart,
                  label: "Prediction",
                  sub: "Peak salinity in 45m",
                  status: "COMPLETED",
                  color: "teal",
                },
                {
                  id: 3,
                  icon: Settings2,
                  label: "Mitigation",
                  sub: "Pre-emptive closure",
                  status: "ACTIVE NOW",
                  active: true,
                  color: "cyan",
                },
                {
                  id: 4,
                  icon: Zap,
                  label: "Execution",
                  sub: "SMS → Close Gate",
                  status: "QUEUED",
                  color: "slate",
                },
                {
                  id: 5,
                  icon: RotateCcw,
                  label: "Feedback Loop",
                  sub: "Evaluating result",
                  status: "PENDING",
                  color: "slate",
                },
              ].map((step) => (
                <div
                  key={step.id}
                  className="relative z-10 flex flex-col items-center group w-32"
                >
                  <div
                    className={`w-16 h-16 rounded-[22px] flex items-center justify-center transition-all duration-500 shadow-md ${
                      step.active
                        ? "bg-mekong-cyan text-mekong-navy scale-110 shadow-xl shadow-mekong-cyan/30 border-4 border-white"
                        : step.status === "COMPLETED"
                          ? "bg-mekong-teal text-white"
                          : "bg-slate-100 text-slate-300"
                    }`}
                  >
                    <step.icon size={26} strokeWidth={step.active ? 2.5 : 2} />
                  </div>
                  <div className="mt-6 text-center space-y-1">
                    <p
                      className={`text-[12px] font-black uppercase tracking-tighter ${step.active ? "text-mekong-navy" : "text-mekong-slate"}`}
                    >
                      {step.label}
                    </p>
                    <p className="text-[10px] text-slate-400 font-bold uppercase tracking-widest">
                      {step.sub}
                    </p>
                    <p
                      className={`text-[9px] font-black uppercase mt-3 tracking-[0.2em] px-2 py-0.5 rounded-full ${
                        step.active
                          ? "bg-mekong-navy text-mekong-cyan animate-pulse"
                          : step.status === "COMPLETED"
                            ? "text-mekong-teal bg-mekong-teal/5"
                            : "text-slate-300"
                      }`}
                    >
                      {step.status}
                    </p>
                  </div>
                </div>
              ))}
            </div>

            {/* Sub-Card: Strategy Details */}
            <div className="p-8 bg-slate-50 rounded-[32px] border border-slate-100 flex gap-6 items-start relative group hover:bg-slate-100/50 transition-all">
              <div className="w-12 h-12 bg-white rounded-2xl flex items-center justify-center text-mekong-teal shadow-soft border border-slate-200">
                <Info size={24} />
              </div>
              <div className="space-y-2">
                <h4 className="text-[13px] font-black text-mekong-navy uppercase tracking-widest">
                  Active Intervention Strategy #042-B
                </h4>
                <p className="text-[14px] text-slate-500 leading-relaxed font-semibold opacity-90">
                  Agent đã xác định cửa sổ rủi ro cao trong khoảng{" "}
                  <span className="text-mekong-navy font-black">
                    14:00 - 16:30
                  </span>
                  . Cảnh báo SMS sẽ được gửi đến 14 điều hành viên lúc 13:40.
                  Quy trình đóng cống Sluice-7 tự động sẽ bắt đầu lúc 14:00 để
                  ngăn mặn xâm nhập.
                </p>
              </div>
            </div>
          </Card>
        </div>

        {/* Right Column: Cognitive Node Mapping (4 cols) */}
        <div className="col-span-12 lg:col-span-4">
          <Card
            variant="navy"
            padding="lg"
            className="bg-[#00203F] border-none shadow-2xl h-full rounded-[40px] relative overflow-hidden flex flex-col justify-between"
          >
            <div className="absolute top-0 right-0 w-80 h-80 bg-mekong-cyan/5 rounded-full blur-[100px] pointer-events-none" />

            <div className="relative z-10 flex items-center gap-4 mb-10">
              <div className="p-3 bg-mekong-cyan/10 rounded-2xl border border-mekong-cyan/20 text-mekong-cyan">
                <BrainCircuit size={28} />
              </div>
              <div>
                <h3 className="text-lg font-black text-white uppercase tracking-tighter leading-none">
                  Cognitive Node Mapping
                </h3>
                <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest mt-2">
                  Neural Connection Web
                </p>
              </div>
            </div>

            {/* Interactive Diagram Center */}
            <div className="relative h-64 flex items-center justify-center">
              {/* Central Core */}
              <div className="w-20 h-20 bg-mekong-cyan rounded-[24px] flex items-center justify-center text-mekong-navy z-20 shadow-[0_0_40px_rgba(117,231,254,0.4)] border-4 border-white animate-pulse">
                <Cpu size={32} strokeWidth={2.5} />
              </div>

              {/* Peripheral Nodes Positioning */}
              {[
                {
                  icon: Waves,
                  label: "TIDE",
                  pos: "-top-4 left-1/2 -translate-x-1/2",
                },
                { icon: Wind, label: "WIND", pos: "top-1/4 -right-2" },
                { icon: Radio, label: "SENSOR", pos: "top-1/4 -left-2" },
                {
                  icon: HistoryIcon,
                  label: "HISTORY",
                  pos: "-bottom-4 left-1/2 -translate-x-1/2",
                },
              ].map((node, i) => (
                <div
                  key={i}
                  className={`absolute ${node.pos} flex flex-col items-center gap-2 group cursor-pointer`}
                >
                  <div className="w-12 h-12 bg-white/5 border border-white/10 rounded-2xl flex items-center justify-center text-slate-400 group-hover:bg-mekong-cyan group-hover:text-mekong-navy transition-all duration-300">
                    <node.icon size={20} />
                  </div>
                  <span className="text-[9px] font-black text-slate-500 uppercase tracking-[0.2em]">
                    {node.label}
                  </span>
                </div>
              ))}

              {/* Connecting Grid Lines SVG */}
              <svg
                className="absolute inset-0 w-full h-full opacity-10 pointer-events-none"
                viewBox="0 0 400 300"
              >
                <circle
                  cx="200"
                  cy="150"
                  r="100"
                  stroke="white"
                  strokeWidth="1"
                  fill="none"
                  strokeDasharray="8 8"
                />
                <line
                  x1="200"
                  y1="150"
                  x2="200"
                  y2="50"
                  stroke="white"
                  strokeWidth="1.5"
                />
                <line
                  x1="200"
                  y1="150"
                  x2="300"
                  y2="100"
                  stroke="white"
                  strokeWidth="1.5"
                />
                <line
                  x1="200"
                  y1="150"
                  x2="100"
                  y2="100"
                  stroke="white"
                  strokeWidth="1.5"
                />
              </svg>
            </div>

            <div className="relative z-10 pt-10 border-t border-white/5 space-y-4">
              <div className="flex justify-between items-end">
                <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest">
                  Processing Density
                </p>
                <span className="text-sm font-mono font-black text-mekong-cyan shadow-sm shadow-mekong-cyan/20 px-2 py-0.5 rounded bg-white/5">
                  88 Gflops
                </span>
              </div>
              <div className="h-1.5 bg-white/10 rounded-full overflow-hidden">
                <div className="h-full bg-gradient-to-r from-mekong-teal to-mekong-cyan w-4/5 rounded-full shadow-[0_0_12px_#75E7FE]" />
              </div>
            </div>
          </Card>
        </div>
      </div>

      {/* 3. LOWER CONTENT: LOGS & SETTINGS */}
      <div className="grid grid-cols-12 gap-8">
        {/* Live Reasoning Terminal (8 cols) */}
        <div className="col-span-12 lg:col-span-8">
          <Card
            variant="white"
            padding="none"
            className="rounded-[40px] shadow-soft border border-slate-200 overflow-hidden h-[450px] flex flex-col"
          >
            <div className="p-8 border-b border-slate-100 flex justify-between items-center bg-slate-50/50">
              <div className="flex items-center gap-3 text-mekong-navy">
                <Terminal size={22} />
                <h3 className="text-base font-black uppercase tracking-widest">
                  Live Reasoning Log
                </h3>
              </div>
              <Button
                variant="outline"
                className="h-10 text-[10px] font-black border-slate-200 px-4"
              >
                <Download size={14} className="mr-2" /> EXPORT LOG
              </Button>
            </div>

            <div className="flex-1 p-8 space-y-4 overflow-y-auto font-mono bg-[#FAFAFB] custom-scrollbar">
              {[
                {
                  t: "14:22:10",
                  cat: "CORE_PROCESS",
                  msg: "Vận tốc gió tăng lên 6 Bft, đẩy nhanh sự xâm nhập của nêm mặn thêm 12%... hệ thống đã điều chỉnh thời gian đóng cống sớm hơn.",
                  color: "border-l-mekong-teal text-mekong-navy",
                },
                {
                  t: "14:18:05",
                  cat: "DATA_INGEST",
                  msg: "Đang tiếp nhận dữ liệu đo đạc vệ tinh độ phân giải cao. Tính toán lại hệ số ma sát lòng sông cho mô hình lan truyền thượng nguồn.",
                  color: "border-l-slate-300 text-slate-500",
                },
                {
                  t: "14:15:52",
                  cat: "PREDICTIVE_SYNC",
                  msg: "Dữ liệu lịch sử từ đợt hạn mặn 2016 khớp 94.2%. Đang điều chỉnh ngưỡng nhạy cảm cho Gate-09.",
                  color: "border-l-slate-300 text-slate-500",
                },
                {
                  t: "14:10:30",
                  cat: "DECISION_BRANCH",
                  msg: "Phát hiện ghi đè thủ công tại Gate-12. Đang tính toán lại luồng xâm nhập mặn dự kiến qua khu vực Delta-4.",
                  color: "border-l-mekong-navy text-mekong-navy",
                },
                {
                  t: "14:05:00",
                  cat: "SYSTEM_HEARTBEAT",
                  msg: "Tất cả 142 node cảm biến đang báo cáo trong tham số độ trễ định danh (45ms).",
                  color: "border-l-slate-300 text-slate-500",
                },
              ].map((log, i) => (
                <div
                  key={i}
                  className={`p-5 rounded-2xl bg-white border border-slate-100 border-l-[5px] ${log.color} group hover:shadow-md transition-all`}
                >
                  <div className="flex gap-4 items-start">
                    <span className="text-[11px] font-bold text-slate-400 opacity-60 leading-tight">
                      [{log.t}]
                    </span>
                    <div className="space-y-1.5 flex-1">
                      <p className="text-[11px] font-black uppercase tracking-widest">
                        {log.cat}
                      </p>
                      <p className="text-[13px] font-medium leading-relaxed">
                        {log.msg}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </div>

        {/* Strategic Goal Settings (4 cols) */}
        <div className="col-span-12 lg:col-span-4">
          <Card
            variant="white"
            padding="lg"
            className="rounded-[40px] bg-slate-100/50 border-none shadow-soft h-full flex flex-col justify-between"
          >
            <div className="space-y-2 mb-10">
              <div className="flex items-center gap-3 text-mekong-navy">
                <SlidersHorizontal size={22} />
                <h3 className="text-base font-black uppercase tracking-widest leading-none">
                  Strategic Goal Settings
                </h3>
              </div>
              <p className="text-[12px] text-slate-500 font-medium leading-relaxed italic pl-9">
                Các quan chức DARD được ủy quyền có thể ghi đè các tham số cơ sở
                của AI.
              </p>
            </div>

            <div className="space-y-10 flex-1">
              {/* Slider Mockup */}
              <div className="space-y-4">
                <div className="flex justify-between items-end">
                  <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest">
                    Salinity Threshold
                  </label>
                  <span className="text-sm font-black text-mekong-navy bg-white px-3 py-1 rounded-lg border border-slate-200">
                    0.3 g/L
                  </span>
                </div>
                <div className="relative h-2 bg-slate-200 rounded-full">
                  <div className="absolute top-0 left-0 h-full w-1/3 bg-mekong-teal rounded-full" />
                  <div className="absolute top-1/2 -translate-y-1/2 left-1/3 w-5 h-5 bg-white border-2 border-mekong-teal rounded-full shadow-lg cursor-pointer hover:scale-110 transition-transform" />
                </div>
                <div className="flex justify-between text-[9px] font-black text-slate-400 uppercase tracking-widest">
                  <span>0.1 g/L</span>
                  <span className="text-mekong-teal/60 italic">
                    Target: Planting season
                  </span>
                  <span>1.0 g/L</span>
                </div>
              </div>

              {/* Agility Selector */}
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest">
                    Intervention Agility
                  </label>
                  <span className="text-[10px] font-black text-mekong-teal uppercase tracking-widest">
                    High (Proactive)
                  </span>
                </div>
                <div className="grid grid-cols-3 gap-1 bg-white p-1 rounded-2xl border border-slate-200 shadow-inner">
                  <button className="py-2.5 text-[9px] font-black uppercase text-slate-400 hover:text-mekong-navy">
                    Conservative
                  </button>
                  <button className="py-2.5 text-[9px] font-black uppercase bg-mekong-navy text-mekong-cyan rounded-xl shadow-lg">
                    Balanced
                  </button>
                  <button className="py-2.5 text-[9px] font-black uppercase text-slate-400 hover:text-mekong-navy">
                    Aggressive
                  </button>
                </div>
              </div>
            </div>

            <div className="mt-10 pt-8 border-t border-slate-200">
              <Button
                variant="navy"
                className="w-full h-16 rounded-[24px] shadow-2xl flex gap-2"
              >
                <CheckCircle2 size={20} /> Commit Overrides
              </Button>
            </div>
          </Card>
        </div>
      </div>

      {/* 4. BOTTOM SUMMARY BAR */}
      <Card
        variant="white"
        padding="md"
        className="border-none shadow-soft rounded-[32px] group overflow-hidden"
      >
        <div className="relative flex flex-col md:flex-row justify-between items-center gap-8">
          <div className="flex items-center gap-6 flex-1">
            <div className="w-20 h-20 bg-slate-100 rounded-3xl flex items-center justify-center p-4 relative overflow-hidden group-hover:bg-mekong-teal/5 transition-all">
              <img
                src="https://placehold.co/96x96"
                className="w-full h-full object-cover rounded-xl grayscale group-hover:grayscale-0 transition-all opacity-40 group-hover:opacity-100"
              />
              <div className="absolute inset-0 bg-mekong-teal/10 flex items-center justify-center text-mekong-teal">
                <MapPin size={32} />
              </div>
            </div>
            <div className="space-y-1">
              <h4 className="text-xl font-black text-mekong-navy tracking-tighter uppercase leading-none">
                Soc Trang Estuary Nodes
              </h4>
              <p className="text-[13px] text-slate-500 font-semibold max-w-xl">
                Hiện đang giám sát 4 cống thủy lợi trọng yếu tại khu vực phía
                Nam. Độ chính xác dự báo trong chu kỳ hiện tại:{" "}
                <span className="text-mekong-teal font-black">98.4%</span>.
              </p>
            </div>
          </div>

          <div className="flex gap-12 text-right border-l border-slate-100 pl-12 h-16 items-center">
            <div className="space-y-1">
              <p className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] leading-none">
                Avg Salinity
              </p>
              <p className="text-3xl font-black text-mekong-critical tracking-tighter leading-none">
                0.52
              </p>
            </div>
            <div className="space-y-1">
              <p className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] leading-none">
                Nodes Up
              </p>
              <p className="text-3xl font-black text-mekong-navy tracking-tighter leading-none">
                42/42
              </p>
            </div>
            <div className="pl-6">
              <ArrowUpRight
                size={24}
                className="text-slate-200 group-hover:text-mekong-teal transition-all"
              />
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
};

export default StrategyOrchestration;
