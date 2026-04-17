import React from "react";
import {
  Waves,
  Wind,
  ArrowDownToLine,
  TrendingUp,
  AlertCircle,
  Zap,
  Bell,
  CheckCircle2,
  History as HistoryIcon,
  ArrowUpRight,
  Target,
  Clock,
  ChevronRight,
  Info,
  Sliders,
  BrainCircuit,
  Search,
} from "lucide-react";

// Import UI Components
import { Card, CardContent } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Badge } from "../components/ui/Badge";

/**
 * TRANG 6: PHÁP Y DỮ LIỆU & LỊCH SỬ (FORENSICS & HISTORY)
 * ------------------------------------------------------
 * Chức năng Agentic:
 * 1. Causal Attribution: AI phân tích nguyên nhân gốc rễ (Tide vs Wind vs Flow).
 * 2. Historical Benchmarks: Đối chiếu dữ liệu mặn 20 năm từ kho RAG.
 * 3. Prediction vs. Reality: So sánh dự báo của Agent với số liệu cảm biến thực tế.
 * 4. Emergency Protocol: Kích hoạt quy trình khẩn cấp nếu phát hiện vi phạm ngưỡng lịch sử.
 */

export const History = () => {
  return (
    <div className="space-y-10 animate-in fade-in slide-in-from-bottom-4 duration-1000">
      {/* --- 1. TIÊU ĐỀ & DANH TÍNH NÚT QUAN TRẮC --- */}
      <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-6 border-b border-slate-200 pb-8">
        <div className="flex items-center gap-5">
          <div className="w-14 h-14 bg-mekong-navy rounded-[20px] flex items-center justify-center text-white shadow-xl ring-4 ring-slate-100">
            <HistoryIcon size={28} strokeWidth={2.5} />
          </div>
          <div className="space-y-1">
            <div className="flex items-center gap-3 text-[11px] font-black text-slate-400 uppercase tracking-[0.3em]">
              <span className="bg-slate-100 px-2 py-0.5 rounded">
                Nút truyền tin S-04
              </span>
              <span className="text-mekong-teal italic">Lưu vực Sông Tiền</span>
            </div>
            <h1 className="text-4xl lg:text-5xl font-black text-mekong-navy tracking-tighter uppercase leading-none">
              Pháp y & Lịch sử Dữ liệu
            </h1>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className="relative">
            <Search
              className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
              size={16}
            />
            <input
              type="text"
              placeholder="Tìm sự kiện lịch sử..."
              className="pl-10 pr-4 py-2.5 bg-slate-100 border-none rounded-xl text-sm font-bold text-mekong-navy focus:ring-2 ring-mekong-teal/20 w-64 transition-all"
            />
          </div>
          <Button
            variant="outline"
            className="h-11 rounded-xl border-slate-200 bg-white"
          >
            <Bell size={18} />
          </Button>
        </div>
      </div>

      {/* --- 2. PHÂN TÍCH NGUYÊN NHÂN GỐC RỄ (CAUSAL ATTRIBUTION) --- */}
      <div className="grid grid-cols-12 gap-8">
        {/* KHỐI TRÁI: BIỂU ĐỒ XU HƯỚNG (8 CỘT) */}
        <div className="col-span-12 lg:col-span-8">
          <Card
            variant="white"
            className="h-full rounded-[40px] shadow-soft relative overflow-hidden flex flex-col p-8 lg:p-10"
          >
            <div className="flex justify-between items-center mb-12">
              <div className="space-y-1">
                <h3 className="text-xl font-black text-mekong-navy uppercase tracking-tighter">
                  Phân tích Xu hướng dài hạn
                </h3>
                <p className="text-[11px] text-slate-400 font-bold uppercase tracking-widest opacity-70">
                  So sánh Dự báo AI vs Thực tế cảm biến
                </p>
              </div>
              <div className="flex bg-slate-50 p-1.5 rounded-xl border border-slate-100">
                {["1 Tuần", "1 Tháng", "3 Tháng"].map((period, i) => (
                  <button
                    key={i}
                    className={`px-5 py-2 text-[10px] font-black rounded-lg transition-all ${i === 1 ? "bg-mekong-navy text-white shadow-lg" : "text-slate-400 hover:text-mekong-navy"}`}
                  >
                    {period}
                  </button>
                ))}
              </div>
            </div>

            {/* MÔ PHỎNG BIỂU ĐỒ CAO CẤP */}
            <div className="relative flex-1 min-h-[350px] w-full px-4 group">
              {/* Đường ngưỡng nguy hiểm lúa ST25 (Mục 5.2.1 Proposal) */}
              <div className="absolute bottom-[40%] w-full border-t-2 border-mekong-critical/30 border-dashed z-10 flex justify-end">
                <span className="bg-red-50 text-mekong-critical text-[9px] font-black px-3 py-1 rounded-bl-lg uppercase tracking-widest">
                  Ngưỡng sốc mặn ST25 (2.0 g/L)
                </span>
              </div>

              <svg
                className="w-full h-full overflow-visible"
                viewBox="0 0 1000 300"
              >
                <defs>
                  <linearGradient
                    id="actualGrad"
                    x1="0%"
                    y1="0%"
                    x2="0%"
                    y2="100%"
                  >
                    <stop offset="0%" stopColor="#006877" stopOpacity="0.2" />
                    <stop offset="100%" stopColor="#006877" stopOpacity="0" />
                  </linearGradient>
                </defs>
                {/* Đường biểu đồ thực tế */}
                <path
                  d="M 0 250 Q 150 240 300 180 T 500 200 T 750 140 T 1000 80"
                  fill="none"
                  stroke="#006877"
                  strokeWidth="4"
                />
                <path
                  d="M 0 250 Q 150 240 300 180 T 500 200 T 750 140 T 1000 80 L 1000 300 L 0 300 Z"
                  fill="url(#actualGrad)"
                />
                {/* Đường dự báo của AI (Dotted) */}
                <path
                  d="M 0 260 Q 150 250 300 190 T 500 210 T 750 150 T 1000 90"
                  fill="none"
                  stroke="#2DD4BF"
                  strokeWidth="2"
                  strokeDasharray="6 4"
                />

                {/* Nút mặn hiện tại */}
                <circle
                  cx="1000"
                  cy="80"
                  r="6"
                  fill="#BA1A1A"
                  className="animate-pulse"
                />
              </svg>

              <div className="flex justify-between mt-6 text-[10px] font-black text-slate-400 uppercase tracking-widest">
                <span>01 Tháng 03</span>
                <span>15 Tháng 03</span>
                <span className="text-mekong-navy">Hôm nay (2.8 g/L)</span>
              </div>
            </div>
          </Card>
        </div>

        {/* KHỐI PHẢI: PHÂN TÍCH NGUYÊN NHÂN AI (4 CỘT) */}
        <div className="col-span-12 lg:col-span-4 space-y-8">
          <Card
            variant="navy"
            className="bg-[#00203F] text-white rounded-[40px] p-8 shadow-2xl relative overflow-hidden h-full flex flex-col border border-white/5"
          >
            <div className="absolute top-0 right-0 w-64 h-64 bg-mekong-cyan/10 rounded-full blur-[80px]" />
            <div className="relative z-10 flex-1">
              <div className="flex items-center gap-3 mb-10">
                <BrainCircuit size={22} className="text-mekong-cyan" />
                <h3 className="text-sm font-black uppercase tracking-[0.2em]">
                  Pháp y rủi ro AI
                </h3>
              </div>
              <h4 className="text-2xl font-black mb-8 leading-tight uppercase">
                Phân tích tác nhân <br /> gây đỉnh mặn 2.8 g/L
              </h4>

              <div className="space-y-6">
                {[
                  {
                    label: "Triều cường đột biến",
                    val: "+1.2m",
                    icon: Waves,
                    color: "text-mekong-cyan",
                  },
                  {
                    label: "Vận tốc gió chướng",
                    val: "Cấp 6",
                    icon: Wind,
                    color: "text-white",
                  },
                  {
                    label: "Dòng chảy thượng nguồn",
                    val: "-22%",
                    icon: ArrowDownToLine,
                    color: "text-mekong-critical",
                  },
                ].map((item, i) => (
                  <div
                    key={i}
                    className="flex items-center justify-between py-2 border-b border-white/5"
                  >
                    <div className="flex items-center gap-3">
                      <item.icon size={18} className="text-slate-400" />
                      <span className="text-[11px] font-bold text-slate-300 uppercase">
                        {item.label}
                      </span>
                    </div>
                    <span className={`text-lg font-black ${item.color}`}>
                      {item.val}
                    </span>
                  </div>
                ))}
              </div>
            </div>
            <div className="relative z-10 pt-8 mt-auto border-t border-white/5">
              <p className="text-[13px] text-blue-100/70 italic leading-relaxed">
                "Dữ liệu lịch sử 20 năm cho thấy sự kết hợp giữa gió cấp 6 và
                dòng chảy yếu này tương đồng 92% với đợt hạn mặn lịch sử 2016."
              </p>
            </div>
          </Card>
        </div>
      </div>

      {/* --- 3. ĐỐI CHIẾU LỊCH SỬ & CHỈ THỊ (GRID 6:6) --- */}
      <div className="grid grid-cols-12 gap-8 items-stretch">
        {/* ĐIỂM CHUẨN LỊCH SỬ (RAG DATA) */}
        <div className="col-span-12 lg:col-span-6">
          <Card
            variant="white"
            className="rounded-[40px] shadow-soft p-10 border border-slate-100 h-full flex flex-col"
          >
            <div className="flex items-center gap-4 mb-10">
              <div className="p-3 bg-mekong-navy rounded-2xl text-white">
                <Target size={22} />
              </div>
              <h3 className="text-base font-black text-mekong-navy uppercase tracking-widest">
                Điểm chuẩn lịch sử (Mar)
              </h3>
            </div>

            <div className="space-y-6 flex-1">
              {[
                {
                  year: "Tháng 03, 2024 (Nay)",
                  val: "2.8 g/L",
                  color: "text-mekong-critical",
                  active: true,
                },
                {
                  year: "Tháng 03, 2023",
                  val: "1.4 g/L",
                  color: "text-mekong-navy",
                  active: false,
                },
                {
                  year: "Tháng 03, 2022",
                  val: "1.1 g/L",
                  color: "text-mekong-navy",
                  active: false,
                },
              ].map((row, i) => (
                <div
                  key={i}
                  className={`flex justify-between items-center p-6 rounded-[24px] border transition-all ${row.active ? "bg-white shadow-xl border-red-100 scale-105" : "bg-slate-50 border-transparent opacity-60"}`}
                >
                  <span className="text-[11px] font-black text-slate-500 uppercase tracking-widest">
                    {row.year}
                  </span>
                  <span className={`text-2xl font-black ${row.color}`}>
                    {row.val}
                  </span>
                </div>
              ))}
            </div>

            <div className="mt-10 p-6 bg-amber-50 rounded-3xl border border-amber-100 flex gap-4">
              <AlertCircle size={24} className="text-amber-600 shrink-0" />
              <p className="text-[14px] font-bold text-amber-900 leading-relaxed">
                Độ mặn hiện tại cao hơn{" "}
                <span className="text-mekong-critical font-black underline">
                  100%
                </span>{" "}
                so với trung bình lịch sử 3 năm gần nhất.
              </p>
            </div>
          </Card>
        </div>

        {/* CHỈ THỊ HÀNH ĐỘNG TỪ TRÍ NHỚ AI */}
        <div className="col-span-12 lg:col-span-6">
          <Card
            variant="white"
            className="rounded-[40px] shadow-soft p-10 border border-slate-100 h-full flex flex-col relative overflow-hidden"
          >
            <div className="absolute top-0 right-0 w-40 h-40 bg-mekong-teal/5 rounded-full -mr-20 -mt-20" />
            <div className="flex items-center gap-4 mb-10 text-mekong-navy">
              <Zap size={22} fill="currentColor" />
              <h3 className="text-[14px] font-black uppercase tracking-widest">
                Chỉ thị từ Trí nhớ AI
              </h3>
            </div>

            <div className="space-y-10 flex-1 relative">
              <div className="absolute top-2 left-2 bottom-8 w-px border-l-2 border-dashed border-slate-200" />
              {[
                {
                  cat: "Hạ tầng",
                  msg: "Đề xuất duy trì đóng cống thêm 4 chu kỳ triều.",
                },
                {
                  cat: "Nông nghiệp",
                  msg: "Dừng lấy nước ngọt cho Phân khu S-12 ngay lập tức.",
                },
                {
                  cat: "Vận tải",
                  msg: "Điều phối 4 tàu vận tải di chuyển về thượng lưu trong 30p.",
                },
              ].map((item, i) => (
                <div key={i} className="relative pl-10 group cursor-pointer">
                  <div className="absolute top-1.5 left-0 w-4 h-4 rounded-full bg-white border-2 border-slate-300 group-hover:border-mekong-teal transition-all" />
                  <div className="space-y-1">
                    <p className="text-[10px] font-black text-slate-400 uppercase">
                      {item.cat}
                    </p>
                    <h4 className="text-[16px] font-bold text-mekong-navy leading-snug group-hover:text-mekong-teal transition-colors">
                      {item.msg}
                    </h4>
                  </div>
                </div>
              ))}
            </div>

            <button className="mt-10 w-full h-16 bg-mekong-navy text-white rounded-[24px] font-black text-[13px] uppercase tracking-[0.2em] flex items-center justify-center gap-3 hover:shadow-2xl transition-all active:scale-95">
              KÍCH HOẠT GIAO THỨC KHẨN CẤP <ArrowUpRight size={20} />
            </button>
          </Card>
        </div>
      </div>

      {/* --- 4. HỆ THỐNG CẢNH BÁO VI PHẠM (THRESHOLD BREACH) --- */}
      <section className="bg-mekong-critical p-10 rounded-[48px] text-white shadow-2xl flex flex-col md:flex-row justify-between items-center gap-8 relative overflow-hidden animate-pulse">
        <div className="absolute inset-0 bg-black/10 pointer-events-none" />
        <div className="flex items-center gap-8 relative z-10">
          <div className="w-20 h-20 bg-white/20 rounded-[28px] flex items-center justify-center border border-white/40">
            <AlertCircle size={48} />
          </div>
          <div className="space-y-1">
            <h4 className="text-3xl font-black tracking-tighter uppercase leading-none">
              Phát hiện vượt ngưỡng an toàn
            </h4>
            <p className="text-[14px] font-black text-white/80 uppercase tracking-[0.2em]">
              Cảnh báo: 2.8 g/L đe dọa trực tiếp vùng lúa ST25 Tiền Giang
            </p>
          </div>
        </div>
        <Button
          variant="outline"
          className="border-white text-white hover:bg-white hover:text-mekong-critical px-12 h-16 text-[13px] font-black shadow-xl backdrop-blur-md"
        >
          THỰC THI TOÀN BỘ CHỈ THỊ
        </Button>
      </section>
    </div>
  );
};

export default History;
