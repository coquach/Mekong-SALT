import { useEffect, useState } from "react";
import { BrainCircuit, CheckCircle2, Circle, Zap, Loader2 } from "lucide-react";

// Thành phần con cho mỗi dòng suy luận của AI
const ReasoningLog = ({
  time,
  text,
  isDone = false,
  isActive = false,
}: {
  time: string;
  text: string;
  isDone?: boolean;
  isActive?: boolean;
}) => (
  <div
    className={`flex gap-4 group transition-all duration-500 ${isActive ? "scale-105" : "opacity-80"}`}
  >
    <span className="text-[10px] font-mono text-slate-500 mt-1 whitespace-nowrap">
      {time}
    </span>
    <div className="flex-1">
      <p
        className={`text-[13px] leading-relaxed italic ${isActive ? "text-mekong-cyan font-bold" : "text-slate-300"}`}
      >
        {text}
      </p>
      <div className="flex items-center gap-2 mt-2">
        {isDone ? (
          <CheckCircle2 size={14} className="text-mekong-mint" />
        ) : isActive ? (
          <Loader2 size={14} className="text-mekong-cyan animate-spin" />
        ) : (
          <Circle size={14} className="text-slate-600" />
        )}
      </div>
    </div>
  </div>
);

export const AISentinel = () => {
  const [seconds, setSeconds] = useState(12);

  // Hiệu ứng đếm ngược để giao diện trông "sống động" hơn
  useEffect(() => {
    const timer = setInterval(() => {
      setSeconds((prev) => (prev > 1 ? prev - 1 : 12));
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="bg-mekong-navy rounded-[32px] p-8 text-white flex flex-col h-full shadow-2xl relative overflow-hidden border border-white/5">
      {/* 1. Hiệu ứng Glow nền tạo cảm giác công nghệ cao */}
      <div className="absolute -right-20 -top-20 w-64 h-64 bg-mekong-cyan/10 rounded-full blur-[100px] pointer-events-none" />
      <div className="absolute -left-20 -bottom-20 w-64 h-64 bg-mekong-mint/10 rounded-full blur-[100px] pointer-events-none" />

      {/* 2. Phần Đầu (Header) */}
      <div className="flex items-center gap-4 mb-10 relative z-10">
        <div className="p-3 bg-mekong-cyan/10 rounded-2xl text-mekong-cyan border border-mekong-cyan/20 ring-4 ring-mekong-cyan/5">
          <BrainCircuit size={28} strokeWidth={2.5} />
        </div>
        <div>
          <h3 className="text-lg font-black tracking-tight leading-none">
            Hệ thống Giám sát AI Mekong
          </h3>
          <div className="flex items-center gap-2 mt-2">
            <div className="relative flex">
              <div className="w-2 h-2 rounded-full bg-mekong-mint animate-pulse" />
              <div className="absolute inset-0 bg-mekong-mint rounded-full animate-ping opacity-40" />
            </div>
            <span className="text-[10px] font-black text-mekong-mint uppercase tracking-[0.2em]">
              Đang trong tiến trình suy luận
            </span>
          </div>
        </div>
      </div>

      {/* 3. Khu vực Nhật ký Suy luận (Reasoning Logs) */}
      <div className="flex-1 space-y-8 overflow-y-auto pr-2 custom-scrollbar relative z-10">
        <ReasoningLog
          time="14:28"
          text='"Đang phân tích dữ liệu cảm biến thượng nguồn Hòa Định... đối chiếu với dự báo thủy triều Vũng Tàu."'
          isDone
        />
        <ReasoningLog
          time="14:29"
          text='"Xác suất vượt ngưỡng tại Trạm 04 Bến Tre đang tăng lên 78% sau 45 phút nữa."'
          isDone
        />

        {/* Nhật ký đang xử lý */}
        <div className="pt-2 border-t border-white/10">
          <div className="flex items-center gap-2 mb-4 text-mekong-cyan">
            <Zap size={14} fill="currentColor" />
            <span className="text-[10px] font-black uppercase tracking-widest">
              Đang thiết lập kế hoạch giảm thiểu:
            </span>
          </div>
          <div className="space-y-4 pl-4 border-l-2 border-mekong-cyan/20">
            <div className="flex items-start gap-3">
              <CheckCircle2 size={16} className="text-mekong-mint mt-0.5" />
              <p className="text-xs font-medium text-slate-300">
                Kích hoạt quy trình đóng cống tại Nút 09.
              </p>
            </div>
            <div className="flex items-start gap-3">
              <Loader2
                size={16}
                className="text-mekong-cyan mt-0.5 animate-spin"
              />
              <p className="text-xs font-bold text-mekong-cyan">
                Gửi thông báo SMS đến các hợp tác xã nông nghiệp địa phương.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* 4. Phần Tiến độ & Đếm ngược */}
      <div className="mt-10 pt-8 border-t border-white/10 relative z-10">
        {/* Thanh tiến độ tùy chỉnh */}
        <div className="relative h-1.5 w-full bg-white/10 rounded-full overflow-hidden mb-4">
          <div
            className="absolute top-0 left-0 h-full bg-gradient-to-r from-mekong-teal to-mekong-cyan rounded-full transition-all duration-1000 shadow-[0_0_12px_rgba(117,231,254,0.6)]"
            style={{ width: `${(12 - seconds) * 8.33}%` }}
          />
        </div>

        <div className="flex justify-between items-center">
          <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest">
            Đánh giá tiếp theo trong{" "}
            <span className="text-white">{seconds} giây</span>
          </p>
          <div className="flex gap-1">
            {[1, 2, 3].map((i) => (
              <div
                key={i}
                className={`w-1 h-1 rounded-full ${i <= 2 ? "bg-mekong-cyan" : "bg-slate-700"}`}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
