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
  BrainCircuit,
  SlidersHorizontal,
  Waves,
  Wind,
  History as HistoryIcon,
  Radio,
  Cpu,
  ArrowUpRight,
  ShieldCheck,
} from "lucide-react";

// Import UI Components
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Badge } from "../components/ui/Badge";

/**
 * TRANG 4: ĐIỀU PHỐI CHIẾN LƯỢC (STRATEGY ORCHESTRATION)
 * -----------------------------------------------------
 * Chức năng cốt lõi:
 * 1. Workflow Stepper: Hiển thị quy trình 5 bước (Goal -> Observation -> Planning -> Execution -> Feedback).
 * 2. Chain-of-Thought (CoT): Nhật ký suy luận chi tiết của Gemini 2.5 Pro.
 * 3. Human-in-the-loop: Nút phê duyệt kế hoạch hành động.
 * 4. Goal Settings: Điều chỉnh mục tiêu chiến lược và độ nhạy (Agility).
 */

export const StrategyOrchestration = () => {
  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-1000">
      {/* --- 1. TIÊU ĐỀ & TRẠNG THÁI NHÂN SUY LUẬN --- */}
      <div className="flex flex-col lg:flex-row justify-between items-start lg:items-end gap-6">
        <div className="space-y-3">
          <h1 className="text-4xl lg:text-5xl font-black text-mekong-navy tracking-tighter leading-none uppercase">
            Điều phối Chiến lược
          </h1>
          <p className="text-base text-mekong-slate font-medium max-w-3xl leading-relaxed">
            Hệ thống{" "}
            <span className="text-mekong-teal font-bold">Reasoning Engine</span>{" "}
            đang đánh giá kịch bản xâm nhập mặn 48 giờ dựa trên nồng độ thực tế
            và dự báo khí tượng.
          </p>
        </div>
        <div className="flex gap-4 w-full lg:w-auto">
          <div className="flex items-center gap-3 px-5 py-3 bg-white rounded-2xl border border-slate-100 shadow-sm flex-1 lg:flex-none justify-center">
            <div className="w-2.5 h-2.5 bg-mekong-mint rounded-full animate-pulse shadow-[0_0_8px_#1BAEA6]" />
            <span className="text-[11px] font-black text-mekong-navy uppercase tracking-widest">
              AI Core: Gemini 2.5 Pro Active
            </span>
          </div>
        </div>
      </div>

      {/* --- 2. QUY TRÌNH HÀNH ĐỘNG CHIẾN LƯỢC (8:4 GRID) --- */}
      <div className="grid grid-cols-12 gap-8">
        {/* KHỐI TRÁI: WORKFLOW CHIẾN LƯỢC ĐANG THỰC THI (8 CỘT) */}
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
                  Tiến trình chiến lược hiện tại
                </h3>
              </div>
              <Badge
                variant="cyan"
                className="px-4 py-1.5 font-black uppercase tracking-widest text-[10px]"
              >
                Lập kế hoạch theo mục tiêu
              </Badge>
            </div>

            {/* Workflow Visualizer */}
            <div className="relative flex justify-between items-start px-4 mb-20">
              <div className="absolute top-8 left-10 right-10 h-1 bg-slate-100 rounded-full" />
              <div
                className="absolute top-8 left-10 h-1 bg-mekong-teal rounded-full transition-all duration-1000 shadow-[0_0_10px_#1BAEA6]"
                style={{ width: "50%" }}
              />

              {[
                {
                  id: 1,
                  icon: Database,
                  label: "Thu thập",
                  status: "XONG",
                  active: false,
                },
                {
                  id: 2,
                  icon: LineChart,
                  label: "Dự báo",
                  status: "XONG",
                  active: false,
                },
                {
                  id: 3,
                  icon: BrainCircuit,
                  label: "Lập kịch bản",
                  status: "ĐANG CHẠY",
                  active: true,
                },
                {
                  id: 4,
                  icon: Zap,
                  label: "Thực thi",
                  status: "ĐỢI LỆNH",
                  active: false,
                },
                {
                  id: 5,
                  icon: RotateCcw,
                  label: "Phản hồi",
                  status: "CHỜ",
                  active: false,
                },
              ].map((step) => (
                <div
                  key={step.id}
                  className="relative z-10 flex flex-col items-center w-32"
                >
                  <div
                    className={`w-16 h-16 rounded-[22px] flex items-center justify-center transition-all duration-500 shadow-md ${
                      step.active
                        ? "bg-mekong-cyan text-mekong-navy scale-110 shadow-xl border-4 border-white"
                        : step.status === "XONG"
                          ? "bg-mekong-teal text-white"
                          : "bg-slate-100 text-slate-300"
                    }`}
                  >
                    <step.icon size={26} />
                  </div>
                  <p
                    className={`mt-6 text-[12px] font-black uppercase tracking-tighter ${step.active ? "text-mekong-navy" : "text-mekong-slate"}`}
                  >
                    {step.label}
                  </p>
                  <p
                    className={`text-[9px] font-black uppercase mt-2 tracking-widest ${step.active ? "text-mekong-teal animate-pulse" : "text-slate-400"}`}
                  >
                    {step.status}
                  </p>
                </div>
              ))}
            </div>

            {/* Chi tiết kịch bản can thiệp (Planning) */}
            <div className="p-8 bg-slate-50 rounded-[32px] border border-slate-100 space-y-6">
              <div className="flex gap-6 items-start">
                <div className="w-12 h-12 bg-white rounded-2xl flex items-center justify-center text-mekong-teal shadow-soft shrink-0">
                  <Info size={24} />
                </div>
                <div className="space-y-2">
                  <h4 className="text-[13px] font-black text-mekong-navy uppercase tracking-widest">
                    Chiến lược đề xuất #042-B
                  </h4>
                  <p className="text-[15px] text-slate-600 leading-relaxed font-semibold">
                    "Phát hiện triều cường đạt đỉnh 1.2m lúc 16:00. Tôi đề xuất
                    kích hoạt đóng cống Hòa Định lúc 15:40. Điều này giúp ngăn
                    mặn 1.5g/L nhưng vẫn đảm bảo 20 phút cho tàu bè di chuyển."
                  </p>
                </div>
              </div>
              <div className="flex gap-4 pl-[72px]">
                <Button
                  variant="navy"
                  className="h-14 px-10 rounded-2xl shadow-xl flex gap-3 group"
                >
                  <ShieldCheck size={20} /> PHÊ DUYỆT HÀNH ĐỘNG
                </Button>
                <Button
                  variant="outline"
                  className="h-14 px-8 rounded-2xl border-slate-200"
                >
                  XEM KỊCH BẢN PHỤ
                </Button>
              </div>
            </div>
          </Card>
        </div>

        {/* KHỐI PHẢI: BẢN ĐỒ CÁC NÚT NHẬN THỨC (4 CỘT) */}
        <div className="col-span-12 lg:col-span-4">
          <Card
            variant="navy"
            className="bg-[#00203F] border-none shadow-2xl h-full rounded-[40px] relative overflow-hidden flex flex-col"
          >
            <div className="absolute top-0 right-0 w-80 h-80 bg-mekong-cyan/5 rounded-full blur-[100px]" />
            <div className="relative z-10 p-10 flex-1 flex flex-col">
              <div className="flex items-center gap-4 mb-14 border-b border-white/10 pb-6">
                <div className="p-3 bg-mekong-cyan/10 rounded-2xl text-mekong-cyan border border-mekong-cyan/20">
                  <HistoryIcon size={24} />
                </div>
                <h3 className="text-lg font-black text-white uppercase tracking-tighter">
                  Trọng số Quyết định
                </h3>
              </div>

              {/* Radar/Weights Visualization Simulation */}
              <div className="space-y-8 flex-1">
                {[
                  {
                    label: "Mực nước triều",
                    weight: "90%",
                    icon: Waves,
                    color: "bg-mekong-cyan",
                  },
                  {
                    label: "Vận tốc gió",
                    weight: "65%",
                    icon: Wind,
                    color: "bg-white",
                  },
                  {
                    label: "Dữ liệu lịch sử",
                    weight: "42%",
                    icon: HistoryIcon,
                    color: "bg-slate-500",
                  },
                  {
                    label: "Cảm biến thượng nguồn",
                    weight: "88%",
                    icon: Radio,
                    color: "bg-mekong-mint",
                  },
                ].map((node, i) => (
                  <div key={i} className="space-y-3">
                    <div className="flex justify-between items-center text-white">
                      <div className="flex items-center gap-3">
                        <node.icon size={16} className="text-slate-400" />
                        <span className="text-[11px] font-black uppercase tracking-widest">
                          {node.label}
                        </span>
                      </div>
                      <span className="text-xs font-mono font-black text-mekong-cyan">
                        {node.weight}
                      </span>
                    </div>
                    <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
                      <div
                        className={`h-full ${node.color} rounded-full`}
                        style={{ width: node.weight }}
                      />
                    </div>
                  </div>
                ))}
              </div>

              <div className="mt-10 pt-8 border-t border-white/5 text-center">
                <p className="text-[10px] font-black text-slate-500 uppercase tracking-[0.3em]">
                  AI xử lý: 2.5 Gemini Pro <br></br> Latency: 1.2s | Độ tin cậy:
                  94%
                </p>
              </div>
            </div>
          </Card>
        </div>
      </div>

      {/* --- 3. NHẬT KÝ SUY LUẬN & CÀI ĐẶT MỤC TIÊU (8:4 GRID) --- */}
      <div className="grid grid-cols-12 gap-8">
        {/* CHAIN-OF-THOUGHT LOGS (8 CỘT) */}
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
                  Luồng suy luận thực tế (CoT)
                </h3>
              </div>
              <Badge variant="navy" className="font-mono text-[10px]">
                SYSTEM_V4.2_STABLE
              </Badge>
            </div>

            <div className="flex-1 p-8 space-y-4 overflow-y-auto font-mono bg-[#FAFAFB]">
              {[
                {
                  time: "14:22:10",
                  msg: "Đang phân tích dữ liệu cảm biến vùng S-04... độ mặn tăng 0.15g/L mỗi giờ.",
                  cat: "DỮ LIỆU",
                },
                {
                  time: "14:22:15",
                  msg: "Đối chiếu mô hình hạn mặn 2016... phát hiện sự tương đồng 94%.",
                  cat: "TRUY XUẤT RAG",
                },
                {
                  time: "14:22:20",
                  msg: "GIẢ LẬP: Nếu đóng cống Mỹ Tho bây giờ -> Rủi ro kẹt 4 tàu vận tải. Nếu lùi 20p -> Giảm 85% thiệt hại logistics.",
                  cat: "MÔ PHỎNG",
                },
                {
                  time: "14:22:25",
                  msg: "QUYẾT ĐỊNH: Chờ 20 phút. Đã thiết lập thông báo SMS cho đội vận hành.",
                  cat: "CHIẾN LƯỢC",
                },
              ].map((log, i) => (
                <div
                  key={i}
                  className="flex gap-4 p-4 rounded-xl bg-white border border-slate-100 group hover:shadow-md transition-all"
                >
                  <span className="text-[11px] font-black text-slate-400 opacity-60">
                    [{log.time}]
                  </span>
                  <div className="space-y-1">
                    <span className="text-[10px] font-black text-mekong-teal uppercase tracking-widest">
                      [{log.cat}]
                    </span>
                    <p className="text-[13px] font-medium text-mekong-navy leading-relaxed">
                      {log.msg}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </div>

        {/* CÀI ĐẶT MỤC TIÊU CHIẾN LƯỢC (4 CỘT) */}
        <div className="col-span-12 lg:col-span-4">
          <Card
            variant="white"
            padding="lg"
            className="rounded-[40px] bg-slate-100/50 border-none shadow-soft h-full flex flex-col justify-between"
          >
            <div className="space-y-6">
              <div className="flex items-center gap-3 text-mekong-navy mb-10">
                <SlidersHorizontal size={22} />
                <h3 className="text-base font-black uppercase tracking-widest leading-none">
                  Thiết lập Mục tiêu
                </h3>
              </div>

              {/* Ngưỡng mặn an toàn */}
              <div className="space-y-4">
                <div className="flex justify-between items-end">
                  <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest">
                    Ngưỡng mặn an toàn
                  </label>
                  <span className="text-sm font-black text-mekong-navy bg-white px-3 py-1 rounded-lg border border-slate-200">
                    0.5 g/L
                  </span>
                </div>
                <div className="relative h-2 bg-slate-200 rounded-full">
                  <div className="absolute top-0 left-0 h-full w-1/2 bg-mekong-teal rounded-full" />
                  <div className="absolute top-1/2 -translate-y-1/2 left-1/2 w-5 h-5 bg-white border-2 border-mekong-teal rounded-full shadow-lg cursor-pointer hover:scale-110 transition-all" />
                </div>
              </div>

              {/* Chế độ can thiệp */}
              <div className="space-y-4 pt-6">
                <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest">
                  Độ nhạy Can thiệp (Agility)
                </label>
                <div className="grid grid-cols-3 gap-2 bg-white p-1 rounded-2xl border border-slate-200">
                  {["An toàn", "Cân bằng", "Quyết liệt"].map((mode, i) => (
                    <button
                      key={i}
                      className={`py-3 text-[10px] font-black uppercase rounded-xl transition-all ${i === 1 ? "bg-mekong-navy text-mekong-cyan shadow-lg" : "text-slate-400 hover:text-mekong-navy"}`}
                    >
                      {mode}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            <div className="mt-10 pt-8 border-t border-slate-200">
              <Button
                variant="navy"
                className="w-full h-16 rounded-[24px] shadow-2xl flex gap-2"
              >
                <CheckCircle2 size={20} /> LƯU CÀI ĐẶT CHIẾN LƯỢC
              </Button>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default StrategyOrchestration;
