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
import { AISentinel } from "../components/dashboard/AISentinel";
import { SatelliteMap } from "../components/dashboard/SatelliteMap";

/**
 * TRANG BẢNG ĐIỀU KHIỂN (DASHBOARD)
 * --------------------------------------
 * Bố cục đã được tinh chỉnh:
 * - Phần 1: Mục tiêu chiến lược (Banner rộng)
 * - Phần 2: Chỉ số quan trọng (3 cột)
 * - Phần 3: Bản đồ (8 cột) & Trợ lý AI (4 cột)
 * - Phần 4: Nhật ký hành động & Hạ tầng
 */

export const Dashboard = () => {
  return (
    <div className="space-y-10 animate-in fade-in slide-in-from-bottom-4 duration-1000">
      {/* --- PHẦN 1: MỤC TIÊU CHIẾN LƯỢC --- */}
      <section className="relative overflow-hidden bg-[#00203F] rounded-[32px] p-7 lg:p-9 text-white shadow-2xl border border-white/10 group transition-all duration-500 hover:border-mekong-cyan/30">
        <div className="absolute top-0 right-0 w-[500px] h-full bg-mekong-cyan/[0.03] rounded-full blur-[120px] pointer-events-none" />

        <div className="relative z-10 flex flex-col lg:flex-row items-center justify-between gap-8">
          {/* KHỐI 1: MỤC TIÊU CHIẾN LƯỢC */}
          <div className="flex items-center gap-6 flex-1 min-w-0">
            <div className="relative flex-shrink-0">
              <div className="w-14 h-14 bg-white/5 rounded-2xl flex items-center justify-center text-mekong-cyan border border-white/10 shadow-inner group-hover:border-mekong-cyan/50 transition-all duration-500">
                <Target
                  size={28}
                  strokeWidth={2.5}
                  className="drop-shadow-[0_0_8px_rgba(117,231,254,0.4)]"
                />
              </div>
              <div className="absolute -top-1 -right-1 w-3 h-3 bg-mekong-mint rounded-full border-2 border-[#00203F] animate-pulse" />
            </div>

            <div className="space-y-1.5 truncate">
              <p className="text-[10px] font-black text-slate-400 uppercase tracking-[0.25em] opacity-80 leading-none">
                Mục tiêu chiến lược
              </p>
              <div className="flex items-center gap-3">
                <h2 className="text-xl lg:text-2xl font-black tracking-tight whitespace-nowrap">
                  Duy trì độ mặn{" "}
                  <span className="text-mekong-mint ml-1">&lt; 0.5 g/L</span>
                </h2>
                <Badge className="bg-mekong-mint/10 text-mekong-mint border-mekong-mint/20 text-[9px] py-0.5 px-2 italic font-bold">
                  Ngưỡng an toàn
                </Badge>
              </div>
            </div>
          </div>

          {/* KHỐI 2: CHỈ SỐ BIẾN THIÊN */}
          <div className="flex flex-col items-center lg:items-end lg:px-12 border-l border-white/5">
            <p className="text-[10px] font-black text-slate-500 uppercase tracking-[0.2em] mb-1">
              Biến thiên hiện tại
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

          {/* KHỐI 3: NÚT ĐIỀU CHỈNH */}
          <div className="flex-shrink-0">
            <button className="flex items-center gap-3 bg-mekong-cyan text-mekong-navy px-8 h-14 rounded-2xl font-black text-[12px] uppercase tracking-widest shadow-[0_12px_24px_-8px_rgba(117,231,254,0.4)] hover:shadow-[0_16px_32px_-8px_rgba(117,231,254,0.5)] hover:scale-[1.02] active:scale-95 transition-all duration-300 group/btn">
              <SlidersHorizontal
                size={16}
                strokeWidth={3}
                className="opacity-80 group-hover/btn:rotate-180 transition-transform duration-500"
              />
              <span>Cài đặt ngưỡng</span>
            </button>
          </div>
        </div>
      </section>

      {/* --- PHẦN 2: CÁC CHỈ SỐ THỜI GIAN THỰC --- */}
      <div className="grid grid-cols-12 gap-8">
        {/* CARD 1: ĐỘ MẶN TRỰC TIẾP */}
        <Card
          isHoverable
          className="col-span-12 lg:col-span-4 p-8 border-none shadow-[0_8px_30px_rgb(0,0,0,0.04)] group relative overflow-hidden bg-white min-h-[280px] flex flex-col justify-between"
        >
          <div className="absolute -top-10 -right-10 w-40 h-40 bg-mekong-mint/10 rounded-full blur-3xl group-hover:bg-mekong-mint/20 transition-colors duration-500" />

          <div className="relative z-10 flex justify-between items-start">
            <div className="flex items-center gap-4">
              <div className="bg-mekong-teal/10 p-3 rounded-2xl text-mekong-teal border border-mekong-teal/20 shadow-sm group-hover:scale-110 transition-transform">
                <Droplets size={24} strokeWidth={2.5} />
              </div>
              <div className="space-y-0.5">
                <p className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] leading-none">
                  Độ mặn trực tiếp
                </p>
                <Badge
                  variant="optimal"
                  className="bg-mekong-mint/10 text-mekong-mint border-none px-2 py-0.5 text-[9px] font-bold"
                >
                  ĐIỂM QUAN TRẮC S-04
                </Badge>
              </div>
            </div>
            <div className="flex items-center gap-1.5 px-2 py-1 bg-slate-50 rounded-full border border-slate-100">
              <div className="w-1.5 h-1.5 bg-mekong-mint rounded-full animate-pulse shadow-[0_0_8px_#1BAEA6]" />
              <span className="text-[9px] font-black text-mekong-navy uppercase tracking-tighter">
                TRỰC TIẾP
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
                Ổn định trong 4 giờ
              </span>
            </div>
            <div className="text-[9px] font-black text-mekong-teal bg-mekong-teal/5 px-2 py-1 rounded border border-mekong-teal/10 uppercase">
              Độ chính xác 99.2%
            </div>
          </div>
        </Card>

        {/* CARD 2: MỰC NƯỚC THỦY TRIỀU */}
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
                  Mực nước thủy triều
                </p>
                <Badge className="bg-slate-100 text-slate-500 border-none px-2 py-0.5 text-[9px] font-bold">
                  TRẠM SỐ #02
                </Badge>
              </div>
            </div>
          </div>

          <div className="flex items-baseline gap-3">
            <span className="text-7xl font-black text-mekong-navy tracking-tighter leading-none">
              +1.2
            </span>
            <span className="text-xl font-black text-slate-400 uppercase tracking-widest">
              mét
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
                  Đỉnh triều cường
                </span>
                <span className="text-[9px] font-bold opacity-70">
                  Dự kiến trong 22 phút tới
                </span>
              </div>
            </div>
          </div>
        </Card>

        {/* CARD 3: GIÓ & TỐC ĐỘ DÒNG CHẢY */}
        <Card
          isHoverable
          className="col-span-12 lg:col-span-4 p-8 border-none shadow-[0_8px_30px_rgb(0,0,0,0.04)] group bg-white min-h-[280px] flex flex-col justify-between relative overflow-hidden"
        >
          <div className="absolute inset-0 opacity-[0.03] pointer-events-none bg-[radial-gradient(#00203f_1px,transparent_1px)] [background-size:16px_16px]" />

          <div className="relative z-10 flex justify-between items-start">
            <div className="flex items-center gap-4">
              <div className="bg-slate-100 p-3 rounded-2xl text-mekong-navy border border-slate-200 group-hover:scale-110 transition-transform">
                <Wind size={24} strokeWidth={2.5} />
              </div>
              <p className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] leading-none">
                Gió & Tốc độ gió
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
                ĐN
              </span>
              <span className="text-[9px] font-black text-slate-400 uppercase tracking-widest">
                Hướng gió
              </span>
            </div>
          </div>

          <div className="relative z-10 pt-6 border-t border-slate-50 flex items-center gap-2">
            <Compass size={14} strokeWidth={2.5} className="text-slate-400" />
            <span className="text-[11px] font-bold text-slate-500 uppercase tracking-widest leading-none">
              Gió mạnh đẩy mặn vào nội đồng
            </span>
          </div>
        </Card>
      </div>

      {/* --- PHẦN 3: BẢN ĐỒ VÀ TRỢ LÝ AI --- */}
      <div className="grid grid-cols-12 gap-8 items-start">
        <div className="col-span-12 lg:col-span-8">
          <Card
            padding="none"
            className="h-[520px] relative overflow-hidden rounded-[40px] shadow-soft group border-none"
          >
            <div className="absolute top-8 left-8 z-10 bg-white/90 backdrop-blur-xl p-6 rounded-[28px] shadow-2xl border border-white/50 ring-1 ring-black/5">
              <h3 className="text-lg font-black text-mekong-navy tracking-tighter leading-none mb-1">
                Điểm nóng xâm nhập mặn
              </h3>
              <p className="text-[10px] font-black text-mekong-slate uppercase tracking-[0.15em]">
                KHU VỰC TIỀN GIANG - BẾN TRE
              </p>
            </div>

            <div className="w-full h-full">
              <SatelliteMap zoom={12} showControls={false} />
            </div>

            <div className="absolute inset-0 bg-mekong-navy/10 pointer-events-none z-[1]" />

            <button className="absolute bottom-8 left-8 z-10 bg-mekong-navy text-white px-6 py-3 rounded-xl font-black text-xs flex items-center gap-2 shadow-2xl hover:bg-mekong-teal transition-all active:scale-95">
              MỞ BẢN ĐỒ TOÀN CẢNH <ExternalLink size={16} />
            </button>
          </Card>
        </div>

        <div className="col-span-12 lg:col-span-4 space-y-8">
          <AISentinel />
        </div>
      </div>

      {/* --- PHẦN 4: NHẬT KÝ HÀNH ĐỘNG & TRẠNG THÁI HẠ TẦNG --- */}
      <div className="grid grid-cols-12 gap-8 items-stretch">
        {/* KHỐI 1: NHẬT KÝ HÀNH ĐỘNG TỰ ĐỘNG */}
        <Card
          variant="white"
          className="col-span-12 lg:col-span-8 p-6 lg:p-8 border-none shadow-soft flex flex-col rounded-[32px]"
        >
          <div className="flex justify-between items-center mb-6">
            <div className="flex items-center gap-3">
              <div className="p-2.5 bg-mekong-navy rounded-xl text-mekong-cyan shadow-md shadow-mekong-navy/20">
                <Zap size={20} fill="currentColor" />
              </div>
              <h3 className="text-lg font-black text-mekong-navy uppercase tracking-tighter leading-none">
                Nhật ký vận hành tự động
              </h3>
            </div>
            <button className="text-[10px] font-black text-mekong-teal uppercase tracking-widest flex items-center gap-1.5 hover:text-mekong-navy transition-colors border-b border-mekong-teal/20 pb-0.5">
              Xem toàn bộ nhật ký <ArrowUpRight size={12} />
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {[
              {
                time: "14:15",
                title: "Đóng cống ngăn mặn",
                desc: "Cống Hòa Định #04 đã đóng để ngăn mặn 0.8g/L xâm nhập vùng nông nghiệp.",
                color: "border-mekong-navy",
              },
              {
                time: "13:50",
                title: "Cảnh báo SMS vùng",
                desc: "Cảnh báo khẩn cấp đã gửi tới 1,240 hộ nông dân đăng ký tại Bến Tre.",
                color: "border-mekong-teal",
              },
              {
                time: "12:30",
                title: "Tối ưu trạm bơm",
                desc: "Điều chỉnh lưu lượng tại trạm bơm Cai Lậy để tối ưu hóa nguồn nước ngọt.",
                color: "border-mekong-cyan",
              },
            ].map((action, i) => (
              <div
                key={i}
                className={`flex flex-col justify-between gap-6 p-8 rounded-[32px] bg-slate-50/50 border-l-[8px] ${action.color} min-h-[220px] group hover:bg-white hover:shadow-2xl hover:translate-y--1 transition-all duration-500 cursor-pointer relative overflow-hidden`}
              >
                <div className="flex justify-between items-center relative z-10">
                  <span className="text-[12px] font-black text-slate-400 uppercase tracking-[0.2em]">
                    {action.time}
                  </span>
                  <div className="w-2 h-2 rounded-full bg-slate-200 group-hover:bg-mekong-teal animate-pulse" />
                </div>

                <div className="space-y-3 relative z-10">
                  <h4 className="text-[17px] font-black text-mekong-navy group-hover:text-mekong-teal transition-colors leading-none uppercase tracking-tight">
                    {action.title}
                  </h4>
                  <p className="text-[13px] text-slate-500 font-semibold leading-relaxed opacity-90">
                    {action.desc}
                  </p>
                </div>

                <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity duration-500">
                  <span className="text-[9px] font-black text-mekong-teal uppercase tracking-widest">
                    Xem chi tiết kiểm thử
                  </span>
                  <ArrowUpRight size={12} className="text-mekong-teal" />
                </div>
              </div>
            ))}
          </div>
        </Card>

        {/* KHỐI 2: TRẠNG THÁI HẠ TẦNG */}
        <Card
          variant="white"
          className="col-span-12 lg:col-span-4 p-6 lg:p-8 border-none shadow-soft rounded-[32px] flex flex-col"
        >
          <div className="flex items-center gap-3 mb-6 border-b border-slate-50 pb-4">
            <ListChecks size={20} className="text-mekong-navy" />
            <h3 className="text-xs font-black text-mekong-navy uppercase tracking-[0.15em]">
              Trạng thái hạ tầng
            </h3>
          </div>

          <div className="flex-1 flex flex-col justify-center space-y-5">
            {[
              {
                icon: Activity,
                label: "Kết nối cảm biến",
                val: "98.2%",
                color: "text-mekong-mint",
              },
              {
                icon: Database,
                label: "Năng lượng trạm xa",
                val: "84% Trung bình",
                color: "text-mekong-navy",
              },
              {
                icon: Cpu,
                label: "Độ chính xác mô hình",
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

          <div className="mt-10 pt-8 border-t border-slate-50 flex flex-col items-center justify-center gap-4">
            <div className="flex items-center gap-4 px-6 py-2.5 bg-slate-50 rounded-full border border-slate-100 shadow-inner group cursor-default hover:bg-white transition-all duration-500">
              <div className="relative flex items-center justify-center w-3 h-3">
                <div className="absolute inset-0 bg-mekong-mint rounded-full animate-ping opacity-40 scale-150" />
                <div className="relative w-2.5 h-2.5 bg-mekong-mint rounded-full animate-pulse shadow-[0_0_12px_rgba(27,234,166,0.6)]" />
              </div>

              <span className="text-[12px] font-black text-mekong-navy uppercase tracking-[0.4em] leading-none select-none">
                Hệ thống:{" "}
                <span className="text-mekong-teal drop-shadow-sm">Ổn định</span>
              </span>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default Dashboard;
