import React from "react";
import {
  Share2,
  Download,
  ClipboardList,
  Filter,
  CheckCircle2,
  MapPin,
  Activity,
  Zap,
  Waves,
  RefreshCcw,
  BrainCircuit,
  ArrowUpRight,
  TrendingUp,
  Database,
  Search,
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

export const ActionLogs = () => {
  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-1000">
      {/* 1. PHẦN ĐẦU TRANG (HEADER) */}
      <div className="flex flex-col lg:flex-row justify-between items-start lg:items-end gap-6">
        <div className="space-y-3">
          <h1 className="text-4xl lg:text-5xl font-black text-mekong-navy tracking-tighter leading-none uppercase">
            Trung tâm Can thiệp & Học tập
          </h1>
          <p className="text-base text-mekong-slate font-medium max-w-3xl leading-relaxed">
            Hệ thống kiểm toán toàn diện các hành động điều tiết cống tự động
            của AI, vòng lặp phản hồi sinh thái và tối ưu hóa mô hình đệ quy cho
            khu vực Đồng bằng sông Cửu Long.
          </p>
        </div>
        <div className="flex gap-4 w-full lg:w-auto">
          <Button
            variant="outline"
            className="flex-1 lg:flex-none h-14 px-8 border-slate-200 bg-white"
          >
            <Share2 size={18} className="mr-2" /> Chia sẻ báo cáo
          </Button>
          <Button
            variant="navy"
            className="flex-1 lg:flex-none h-14 px-8 shadow-xl shadow-mekong-navy/20"
          >
            <Download size={18} className="mr-2" /> Xuất dữ liệu Sở NN&PTNT
          </Button>
        </div>
      </div>

      {/* 2. KHỐI PHÂN TÍCH & PHẢN HỒI */}
      <div className="grid grid-cols-12 gap-8">
        {/* CỘT TRÁI: HỌC TẬP & THIỆT HẠI ĐÃ TRÁNH (4 cột) */}
        <div className="col-span-12 lg:col-span-4 space-y-8">
          {/* Nhật ký Học tập của AI */}
          <Card
            variant="white"
            className="border-l-4 border-l-mekong-navy shadow-soft rounded-[32px] p-8"
          >
            <div className="flex gap-5 items-start">
              <div className="p-3 bg-slate-50 rounded-2xl text-mekong-navy">
                <BrainCircuit size={24} />
              </div>
              <div className="space-y-4">
                <div>
                  <p className="text-[10px] font-black text-slate-400 uppercase tracking-[0.25em] mb-2">
                    Nhật ký học tập gần đây
                  </p>
                  <p className="text-[15px] font-bold text-mekong-navy leading-relaxed italic">
                    "Hệ thống ghi nhận: Gió cấp 6 yêu cầu đóng cống sớm hơn 15%
                    để duy trì mục tiêu độ mặn."
                  </p>
                </div>
                <div className="flex justify-between items-center pt-2">
                  <Badge variant="cyan" className="px-3">
                    Tối ưu hóa đệ quy
                  </Badge>
                  <span className="text-[10px] font-black text-slate-400">
                    2 giờ trước
                  </span>
                </div>
              </div>
            </div>
          </Card>

          {/* Thiệt hại đã tránh được */}
          <Card
            variant="navy"
            padding="none"
            className="bg-mekong-navy text-white rounded-[40px] overflow-hidden min-h-[340px] flex flex-col p-10 shadow-2xl relative border border-white/5"
          >
            <div className="absolute -right-16 -bottom-16 w-64 h-64 bg-mekong-cyan/10 rounded-full blur-[100px] pointer-events-none" />

            <div className="relative z-10 space-y-2 flex-1">
              <p className="text-[11px] font-black text-slate-400 uppercase tracking-[0.3em] mb-6">
                Thiệt hại đã tránh được (30 ngày)
              </p>
              <div className="flex items-baseline gap-3">
                <span className="text-6xl font-black text-mekong-cyan tracking-tighter drop-shadow-lg">
                  105 Tỷ
                </span>
                <span className="text-xl font-bold text-slate-500 uppercase tracking-widest">
                  VNĐ
                </span>
              </div>
              <p className="text-[15px] text-slate-300 font-medium leading-relaxed pt-4 opacity-90">
                Ước tính{" "}
                <span className="text-white font-bold">1,420 Hecta</span> lúa đã
                được bảo vệ khỏi sự xâm nhập mặn trong chu kỳ vừa qua.
              </p>
            </div>

            <div className="relative z-10 flex items-end gap-2.5 h-24 mt-10">
              {[40, 65, 35, 80, 55, 100, 70].map((h, i) => (
                <div
                  key={i}
                  className={`flex-1 rounded-t-xl transition-all duration-700 hover:scale-110 ${i === 5 ? "bg-mekong-cyan shadow-[0_0_20px_#75E7FE]" : "bg-white/20 hover:bg-white/40"}`}
                  style={{ height: `${h}%` }}
                />
              ))}
            </div>
          </Card>
        </div>

        {/* CỘT PHẢI: PHÂN TÍCH PHẢN HỒI VÒNG LẶP KÍN (8 cột) */}
        <div className="col-span-12 lg:col-span-8">
          <Card
            variant="white"
            padding="lg"
            className="h-full rounded-[40px] shadow-soft border border-slate-100 flex flex-col"
          >
            <div className="flex justify-between items-center mb-12">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-mekong-teal/10 rounded-2xl text-mekong-teal border border-mekong-teal/20">
                  <RefreshCcw size={24} className="animate-spin-slow" />
                </div>
                <div>
                  <h3 className="text-lg font-black text-mekong-navy uppercase tracking-tighter leading-none">
                    Phân tích phản hồi vòng lặp kín
                  </h3>
                  <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mt-2">
                    Xác thực mô hình thời gian thực
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2 px-4 py-2 bg-slate-50 rounded-full border border-slate-100 shadow-sm">
                <div className="w-2 h-2 bg-mekong-mint rounded-full animate-pulse" />
                <span className="text-[10px] font-black text-mekong-navy uppercase tracking-widest">
                  Đang kiểm toán
                </span>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 flex-1">
              {[
                {
                  node: "Cống Hòa Định",
                  status: "Đạt mục tiêu",
                  color: "text-mekong-mint",
                  bg: "bg-mekong-mint/10",
                  desc: "Độ mặn duy trì dưới ngưỡng 0.5 g/L bất chấp triều cường cao hơn dự báo.",
                  eff: "92%",
                },
                {
                  node: "Cống Xuân Hòa",
                  status: "Đang xử lý",
                  color: "text-mekong-cyan",
                  bg: "bg-mekong-cyan/10",
                  desc: "Nồng độ oxy đang ổn định tại điểm nút số 42 sau quá trình xả nước đẩy mặn.",
                  eff: "88%",
                },
              ].map((item, i) => (
                <div
                  key={i}
                  className="p-8 rounded-[36px] bg-slate-50/50 border border-slate-100 flex flex-col justify-between group hover:bg-white hover:shadow-xl transition-all duration-500"
                >
                  <div>
                    <div className="flex justify-between items-start mb-8">
                      <h5 className="text-[12px] font-black text-mekong-navy uppercase tracking-[0.2em]">
                        {item.node}
                      </h5>
                      <span
                        className={`text-[10px] font-black px-3 py-1 rounded-lg uppercase ${item.bg} ${item.color}`}
                      >
                        {item.status}
                      </span>
                    </div>
                    <p className="text-[15px] font-bold text-mekong-navy mb-12 leading-relaxed">
                      {item.desc}
                    </p>
                  </div>
                  <div className="space-y-4">
                    <div className="flex justify-between items-end">
                      <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">
                        Hiệu suất vận hành
                      </span>
                      <span
                        className={`text-2xl font-black ${item.color} tracking-tighter`}
                      >
                        {item.eff}
                      </span>
                    </div>
                    <div className="h-2 bg-slate-200 rounded-full overflow-hidden shadow-inner">
                      <div
                        className={`h-full ${item.color.replace("text", "bg")} transition-all duration-1000 shadow-sm`}
                        style={{ width: item.eff }}
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </div>

      {/* 3. BẢNG CHI TIẾT LỊCH SỬ CAN THIỆP */}
      <section className="bg-white rounded-[48px] border border-slate-200 shadow-soft overflow-hidden">
        <div className="bg-mekong-navy px-10 py-8 text-white flex flex-col md:flex-row justify-between items-center gap-6">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-white/5 rounded-2xl border border-white/10 text-mekong-cyan shadow-xl">
              <ClipboardList size={26} />
            </div>
            <div>
              <h3 className="text-xl font-black uppercase tracking-tighter leading-none">
                Lịch sử can thiệp chi tiết
              </h3>
              <p className="text-[10px] text-slate-400 font-bold uppercase tracking-[0.2em] mt-2 opacity-80">
                Nhật ký kiểm toán đầy đủ về vận hành cống tự động bằng AI
              </p>
            </div>
          </div>
          <div className="flex gap-3 w-full md:w-auto">
            <div className="relative flex-1 md:w-64">
              <Search
                className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500"
                size={16}
              />
              <input
                type="text"
                placeholder="Tìm kiếm nhật ký..."
                className="w-full bg-white/5 border border-white/10 rounded-xl py-2.5 pl-12 pr-4 text-xs font-bold text-white focus:bg-white/10 outline-none transition-all"
              />
            </div>
            <Button
              variant="outline"
              className="border-white/20 text-white hover:bg-white/10 px-6 h-11 text-[11px]"
            >
              <Filter size={14} className="mr-2" /> BỘ LỌC
            </Button>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50/50 border-b border-slate-100">
                <th className="px-10 py-6 text-[11px] font-black text-slate-400 uppercase tracking-widest">
                  Thời gian
                </th>
                <th className="px-10 py-6 text-[11px] font-black text-slate-400 uppercase tracking-widest">
                  Vị trí / Điểm nút
                </th>
                <th className="px-10 py-6 text-[11px] font-black text-slate-400 uppercase tracking-widest">
                  Hành động
                </th>
                <th className="px-10 py-6 text-[11px] font-black text-slate-400 uppercase tracking-widest">
                  Độ tin cậy AI
                </th>
                <th className="px-10 py-6 text-[11px] font-black text-slate-400 uppercase tracking-widest text-center">
                  Xác minh
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-50">
              {[
                {
                  date: "24 Tháng 3, 2024",
                  time: "14:22:10 GMT+7",
                  loc: "Cống Cầu Mỹ Thuận",
                  action: "Đóng cống ngăn mặn",
                  conf: "98.4%",
                  status: "verified",
                },
                {
                  date: "24 Tháng 3, 2024",
                  time: "12:05:44 GMT+7",
                  loc: "Nút Bình Đại #08",
                  action: "Bơm đẩy mặn",
                  conf: "94.1%",
                  status: "verified",
                },
                {
                  date: "24 Tháng 3, 2024",
                  time: "09:15:22 GMT+7",
                  loc: "Đập tràn Trà Vinh",
                  action: "Xả tràn cấu trúc",
                  conf: "89.9%",
                  status: "pending",
                },
              ].map((row, i) => (
                <tr
                  key={i}
                  className="hover:bg-slate-50/30 transition-all group cursor-pointer"
                >
                  <td className="px-10 py-8">
                    <p className="text-sm font-black text-mekong-navy mb-1 group-hover:text-mekong-teal transition-colors">
                      {row.date}
                    </p>
                    <p className="text-[10px] font-mono text-slate-400 font-bold">
                      {row.time}
                    </p>
                  </td>
                  <td className="px-10 py-8">
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-slate-50 rounded-lg text-mekong-teal group-hover:scale-110 transition-transform">
                        <MapPin size={16} />
                      </div>
                      <span className="text-[15px] font-bold text-mekong-navy tracking-tight">
                        {row.loc}
                      </span>
                    </div>
                  </td>
                  <td className="px-10 py-8">
                    <Badge
                      variant="navy"
                      className="bg-mekong-navy/5 text-mekong-navy border-none px-4 py-2 font-black tracking-widest"
                    >
                      {row.action}
                    </Badge>
                  </td>
                  <td className="px-10 py-8">
                    <div className="flex flex-col gap-2 w-32">
                      <div className="flex justify-between text-[11px] font-black text-mekong-teal leading-none">
                        <span>{row.conf}</span>
                        <TrendingUp size={12} />
                      </div>
                      <div className="h-1.5 w-full bg-slate-100 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-mekong-teal rounded-full"
                          style={{ width: row.conf }}
                        />
                      </div>
                    </div>
                  </td>
                  <td className="px-10 py-8 text-center">
                    {row.status === "verified" ? (
                      <div className="w-10 h-10 rounded-full bg-mekong-mint/10 flex items-center justify-center text-mekong-mint mx-auto shadow-sm">
                        <CheckCircle2 size={20} strokeWidth={2.5} />
                      </div>
                    ) : (
                      <div className="w-10 h-10 rounded-full bg-amber-50 flex items-center justify-center text-amber-500 mx-auto animate-pulse">
                        <RefreshCcw size={18} strokeWidth={2.5} />
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Thanh phân trang */}
        <div className="bg-slate-50 px-10 py-6 flex justify-between items-center border-t border-slate-100">
          <span className="text-[11px] font-black text-slate-400 uppercase tracking-widest">
            Hiển thị 1-15 trong tổng số 2,482 bản ghi
          </span>
          <div className="flex gap-4">
            <button className="px-4 py-2 rounded-lg bg-white border border-slate-200 text-[10px] font-black uppercase tracking-widest hover:bg-slate-50 disabled:opacity-30 transition-all">
              Trang trước
            </button>
            <button className="px-4 py-2 rounded-lg bg-mekong-navy text-white text-[10px] font-black uppercase tracking-widest hover:shadow-lg transition-all">
              Trang tiếp theo
            </button>
          </div>
        </div>
      </section>

      {/* 4. BIỂU ĐỒ HIỆU SUẤT & BẢN ĐỒ MẬT ĐỘ DƯỚI CÙNG */}
      <div className="grid grid-cols-12 gap-8 pb-10">
        {/* Hiệu suất hệ thống (Hàng tuần) */}
        <Card
          variant="white"
          padding="lg"
          className="col-span-12 lg:col-span-7 h-[420px] rounded-[40px] flex flex-col justify-between border-none shadow-soft"
        >
          <div className="flex justify-between items-start">
            <div className="space-y-1">
              <h3 className="text-lg font-black text-mekong-navy uppercase tracking-tighter">
                Hiệu suất hệ thống
              </h3>
              <p className="text-[11px] text-slate-400 font-black uppercase tracking-widest opacity-80">
                Độ chính xác dự báo mặn so với cảm biến thực tế.
              </p>
            </div>
            <div className="flex gap-6">
              <div className="flex items-center gap-2">
                <div className="w-2.5 h-2.5 rounded-full bg-mekong-teal" />{" "}
                <span className="text-[10px] font-black uppercase text-slate-400">
                  Thực tế
                </span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-2.5 h-2.5 rounded-full bg-mekong-navy" />{" "}
                <span className="text-[10px] font-black uppercase text-slate-400">
                  Dự báo AI
                </span>
              </div>
            </div>
          </div>

          <div className="flex-1 relative mt-10 mb-6 flex items-end gap-3 px-2">
            <div className="absolute inset-0 flex flex-col justify-between pointer-events-none">
              {[...Array(5)].map((_, i) => (
                <div
                  key={i}
                  className="w-full border-t border-slate-50 border-dashed"
                />
              ))}
            </div>

            {[40, 60, 45, 90, 75, 85, 95].map((h, i) => (
              <div
                key={i}
                className="flex-1 relative flex flex-col items-center gap-1 group"
              >
                <div
                  className="w-full bg-mekong-teal opacity-10 rounded-t-lg absolute bottom-0 transition-all group-hover:opacity-20"
                  style={{ height: `${h}%` }}
                />
                <div
                  className="w-2/3 bg-mekong-navy rounded-t-lg absolute bottom-0 transition-all"
                  style={{ height: `${h - 10}%` }}
                />
                <span className="absolute -bottom-8 text-[10px] font-black text-slate-400 uppercase">
                  Ngày {i + 1}
                </span>
              </div>
            ))}
          </div>
        </Card>

        {/* Bản đồ mật độ can thiệp */}
        <Card
          variant="navy"
          padding="lg"
          className="col-span-12 lg:col-span-5 bg-[#00203F] text-white rounded-[40px] flex flex-col justify-between border-none shadow-2xl relative overflow-hidden"
        >
          <div className="absolute top-0 left-0 w-full h-full bg-[radial-gradient(circle_at_50%_50%,rgba(117,231,254,0.05),transparent)] pointer-events-none" />

          <div className="relative z-10 space-y-1">
            <h3 className="text-lg font-black uppercase tracking-tighter">
              Bản đồ mật độ can thiệp
            </h3>
            <p className="text-[11px] text-slate-500 font-bold uppercase tracking-widest opacity-80 leading-relaxed">
              Sự tập trung của các hành động điều tiết dựa trên áp lực mặn vùng.
            </p>
          </div>

          <div className="relative z-10 grid grid-cols-10 gap-1.5 my-12 px-2">
            {Array.from({ length: 50 }).map((_, i) => {
              const opacity = Math.random();
              const isHigh = opacity > 0.7;
              return (
                <div
                  key={i}
                  className={`aspect-square rounded-sm transition-all duration-700 hover:scale-125 hover:z-20 cursor-pointer shadow-sm ${isHigh ? "shadow-mekong-cyan/40 ring-1 ring-mekong-cyan/30" : ""}`}
                  style={{
                    backgroundColor: `rgba(117, 231, 254, ${opacity > 0.3 ? opacity : 0.05})`,
                  }}
                  title={`Mức độ: ${Math.round(opacity * 100)}%`}
                />
              );
            })}
          </div>

          <div className="relative z-10 flex justify-between items-center text-[10px] font-black text-slate-500 uppercase tracking-[0.3em] border-t border-white/5 pt-6">
            <span className="flex items-center gap-2">
              <MapPin size={12} /> CỬA SÔNG VEN BIỂN
            </span>
            <span className="flex items-center gap-2">
              THƯỢNG NGUỒN DELTA <ArrowUpRight size={12} />
            </span>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default ActionLogs;
