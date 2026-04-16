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

// Import các UI Components
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
      {/* 1. PHẦN ĐẦU TRANG (HEADER) */}
      <div className="flex flex-col lg:flex-row justify-between items-start lg:items-end gap-6">
        <div className="space-y-3">
          <h1 className="text-4xl lg:text-5xl font-black text-mekong-navy tracking-tighter leading-none uppercase">
            Điều phối Chiến lược
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
              Nhân logic: Đang hoạt động
            </span>
          </div>
          <Button
            variant="navy"
            className="flex-1 lg:flex-none h-14 px-8 shadow-xl shadow-mekong-navy/20"
          >
            <Settings2 size={18} className="mr-2" /> Tối ưu kế hoạch
          </Button>
        </div>
      </div>

      {/* 2. KHỐI QUY TRÌNH CHÍNH & BẢN ĐỒ TƯ DUY */}
      <div className="grid grid-cols-12 gap-8">
        {/* Cột trái: Tiến trình công việc (8 cột) */}
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
                  Quy trình chiến lược hiện tại
                </h3>
              </div>
              <Badge
                variant="cyan"
                className="bg-mekong-cyan/10 text-mekong-teal border-none px-4 py-1.5 font-black uppercase tracking-widest text-[10px]"
              >
                Lập kế hoạch theo mục tiêu
              </Badge>
            </div>

            {/* Trực quan hóa tiến trình Workflow */}
            <div className="relative flex justify-between items-start px-4 mb-20">
              {/* Đường kẻ nền kết nối */}
              <div className="absolute top-8 left-10 right-10 h-1 bg-slate-50 rounded-full" />
              {/* Đường tiến độ */}
              <div
                className="absolute top-8 left-10 h-1 bg-mekong-teal rounded-full transition-all duration-1000 shadow-[0_0_10px_#006877]"
                style={{ width: "45%" }}
              />

              {[
                {
                  id: 1,
                  icon: Database,
                  label: "Thu thập dữ liệu",
                  sub: "Cảm biến & API Mesh",
                  status: "HOÀN THÀNH",
                  color: "teal",
                },
                {
                  id: 2,
                  icon: LineChart,
                  label: "Dự báo",
                  sub: "Đỉnh mặn sau 45p",
                  status: "HOÀN THÀNH",
                  color: "teal",
                },
                {
                  id: 3,
                  icon: Settings2,
                  label: "Giảm thiểu",
                  sub: "Đóng cống phòng ngừa",
                  status: "ĐANG CHẠY",
                  active: true,
                  color: "cyan",
                },
                {
                  id: 4,
                  icon: Zap,
                  label: "Thực thi",
                  sub: "SMS → Đóng cống",
                  status: "ĐANG CHỜ",
                  color: "slate",
                },
                {
                  id: 5,
                  icon: RotateCcw,
                  label: "Phản hồi",
                  sub: "Đánh giá kết quả",
                  status: "CHƯA CHẠY",
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
                        : step.status === "HOÀN THÀNH"
                          ? "bg-mekong-teal text-white"
                          : "bg-slate-100 text-slate-300"
                    }`}
                  >
                    <step.icon size={26} strokeWidth={step.active ? 2.5 : 2} />
                  </div>
                  <div className="mt-6 text-center space-y-1">
                    <p
                      className={`text-[12px] font-black uppercase tracking-tighter ${step.active ? "text-mekong-navy" : "text-mekong-navy/60"}`}
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
                          : step.status === "HOÀN THÀNH"
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

            {/* Thẻ phụ: Chi tiết chiến lược */}
            <div className="p-8 bg-slate-50 rounded-[32px] border border-slate-100 flex gap-6 items-start relative group hover:bg-slate-100/50 transition-all">
              <div className="w-12 h-12 bg-white rounded-2xl flex items-center justify-center text-mekong-teal shadow-soft border border-slate-200">
                <Info size={24} />
              </div>
              <div className="space-y-2">
                <h4 className="text-[13px] font-black text-mekong-navy uppercase tracking-widest">
                  Chiến lược can thiệp kích hoạt #042-B
                </h4>
                <p className="text-[14px] text-slate-500 leading-relaxed font-semibold opacity-90">
                  Agent đã xác định cửa sổ rủi ro cao trong khoảng{" "}
                  <span className="text-mekong-navy font-black">
                    14:00 - 16:30
                  </span>
                  . Cảnh báo SMS sẽ được gửi đến 14 điều hành viên lúc 13:40.
                  Quy trình đóng cống Sluice-7 tự động sẽ bắt đầu lúc 14:00 để
                  ngăn mặn xâm nhập nội đồng.
                </p>
              </div>
            </div>
          </Card>
        </div>

        {/* Cột phải: Bản đồ các nút nhận thức (4 cột) */}
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
                  Bản đồ nút nhận thức
                </h3>
                <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest mt-2">
                  Mạng lưới kết nối tư duy AI
                </p>
              </div>
            </div>

            {/* Sơ đồ tương tác trung tâm */}
            <div className="relative h-64 flex items-center justify-center">
              {/* Lõi trung tâm */}
              <div className="w-20 h-20 bg-mekong-cyan rounded-[24px] flex items-center justify-center text-mekong-navy z-20 shadow-[0_0_40px_rgba(117,231,254,0.4)] border-4 border-white animate-pulse">
                <Cpu size={32} strokeWidth={2.5} />
              </div>

              {/* Vị trí các nút ngoại vi */}
              {[
                {
                  icon: Waves,
                  label: "THỦY TRIỀU",
                  pos: "-top-4 left-1/2 -translate-x-1/2",
                },
                { icon: Wind, label: "GIÓ", pos: "top-1/4 -right-2" },
                { icon: Radio, label: "CẢM BIẾN", pos: "top-1/4 -left-2" },
                {
                  icon: HistoryIcon,
                  label: "LỊCH SỬ",
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

              {/* Đường lưới kết nối SVG */}
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
                  Mật độ xử lý
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

      {/* 3. NỘI DUNG PHÍA DƯỚI: NHẬT KÝ & CÀI ĐẶT */}
      <div className="grid grid-cols-12 gap-8">
        {/* Nhật ký suy luận trực tiếp (8 cột) */}
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
                  Nhật ký suy luận hệ thống
                </h3>
              </div>
              <Button
                variant="outline"
                className="h-10 text-[10px] font-black border-slate-200 px-4"
              >
                <Download size={14} className="mr-2" /> XUẤT NHẬT KÝ
              </Button>
            </div>

            <div className="flex-1 p-8 space-y-4 overflow-y-auto font-mono bg-[#FAFAFB] custom-scrollbar">
              {[
                {
                  t: "14:22:10",
                  cat: "LÕI_HỆ_THỐNG",
                  msg: "Vận tốc gió tăng lên 6 Bft, đẩy nhanh sự xâm nhập của nêm mặn thêm 12%... hệ thống đã điều chỉnh thời gian đóng cống sớm hơn.",
                  color: "border-l-mekong-teal text-mekong-navy",
                },
                {
                  t: "14:18:05",
                  cat: "NHẬN_DỮ_LIỆU",
                  msg: "Đang tiếp nhận dữ liệu đo đạc vệ tinh độ phân giải cao. Tính toán lại hệ số ma sát lòng sông cho mô hình lan truyền.",
                  color: "border-l-slate-300 text-slate-500",
                },
                {
                  t: "14:15:52",
                  cat: "DỰ_BÁO_ĐỒNG_BỘ",
                  msg: "Dữ liệu lịch sử từ đợt hạn mặn 2016 khớp 94.2%. Đang điều chỉnh ngưỡng nhạy cảm cho Cống Gate-09.",
                  color: "border-l-slate-300 text-slate-500",
                },
                {
                  t: "14:10:30",
                  cat: "NHÁNH_QUYẾT_ĐỊNH",
                  msg: "Phát hiện ghi đè thủ công tại Gate-12. Đang tính toán lại luồng xâm nhập mặn dự kiến qua khu vực Delta-4.",
                  color: "border-l-mekong-navy text-mekong-navy",
                },
                {
                  t: "14:05:00",
                  cat: "TRẠNG_THÁI_HỆ_THỐNG",
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

        {/* Cài đặt mục tiêu chiến lược (4 cột) */}
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
                  Cài đặt mục tiêu
                </h3>
              </div>
              <p className="text-[12px] text-slate-500 font-medium leading-relaxed italic pl-9">
                Các chuyên viên quản lý được ủy quyền có thể điều chỉnh các tham
                số cơ sở của AI.
              </p>
            </div>

            <div className="space-y-10 flex-1">
              {/* Ngưỡng độ mặn Slider */}
              <div className="space-y-4">
                <div className="flex justify-between items-end">
                  <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest">
                    Ngưỡng độ mặn
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
                    Mục tiêu: Mùa xuống giống
                  </span>
                  <span>1.0 g/L</span>
                </div>
              </div>

              {/* Lựa chọn độ linh hoạt */}
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest">
                    Độ nhạy can thiệp
                  </label>
                  <span className="text-[10px] font-black text-mekong-teal uppercase tracking-widest">
                    Cao (Chủ động)
                  </span>
                </div>
                <div className="grid grid-cols-3 gap-1 bg-white p-1 rounded-2xl border border-slate-200 shadow-inner">
                  <button className="py-2.5 text-[9px] font-black uppercase text-slate-400 hover:text-mekong-navy">
                    Thận trọng
                  </button>
                  <button className="py-2.5 text-[9px] font-black uppercase bg-mekong-navy text-mekong-cyan rounded-xl shadow-lg">
                    Cân bằng
                  </button>
                  <button className="py-2.5 text-[9px] font-black uppercase text-slate-400 hover:text-mekong-navy">
                    Quyết liệt
                  </button>
                </div>
              </div>
            </div>

            <div className="mt-10 pt-8 border-t border-slate-200">
              <Button
                variant="navy"
                className="w-full h-16 rounded-[24px] shadow-2xl flex gap-2"
              >
                <CheckCircle2 size={20} /> Lưu các thay đổi
              </Button>
            </div>
          </Card>
        </div>
      </div>

      {/* 4. THANH TỔNG HỢP DƯỚI CÙNG */}
      <Card
        variant="white"
        padding="md"
        className="border-none shadow-soft rounded-[32px] group overflow-hidden"
      >
        <div className="relative flex flex-col md:flex-row justify-between items-center gap-8">
          <div className="flex items-center gap-6 flex-1">
            <div className="w-20 h-20 bg-slate-100 rounded-3xl flex items-center justify-center p-4 relative overflow-hidden group-hover:bg-mekong-teal/5 transition-all">
              <div className="absolute inset-0 bg-mekong-teal/10 flex items-center justify-center text-mekong-teal">
                <MapPin size={32} />
              </div>
            </div>
            <div className="space-y-1">
              <h4 className="text-xl font-black text-mekong-navy tracking-tighter uppercase leading-none">
                Nút hạ lưu Sóc Trăng
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
                Độ mặn TB
              </p>
              <p className="text-3xl font-black text-mekong-critical tracking-tighter leading-none">
                0.52
              </p>
            </div>
            <div className="space-y-1">
              <p className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] leading-none">
                Trạm hoạt động
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
