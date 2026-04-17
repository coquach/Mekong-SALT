import { Maximize2, MousePointer2 } from "lucide-react";
import { Card } from "../ui/Card";

// Thành phần con cho các điểm Hotspot nhấp nháy trên bản đồ
const HotspotMarker = ({
  top,
  left,
  label,
  intensity = "critical",
}: {
  top: string;
  left: string;
  label: string;
  intensity?: "critical" | "warning";
}) => (
  <div className="absolute group z-20" style={{ top, left }}>
    {/* Hiệu ứng sóng lan tỏa (Pulse) */}
    <div
      className={`absolute -inset-4 rounded-full opacity-40 animate-ping ${
        intensity === "critical" ? "bg-mekong-critical" : "bg-mekong-warning"
      }`}
    />

    {/* Điểm tâm điểm */}
    <div
      className={`relative w-4 h-4 rounded-full border-2 border-white shadow-lg ${
        intensity === "critical" ? "bg-mekong-critical" : "bg-mekong-warning"
      }`}
    />

    {/* Label hiện ra khi hover vào điểm */}
    <div className="absolute left-6 top-1/2 -translate-y-1/2 bg-mekong-navy/90 backdrop-blur-md text-white px-3 py-1.5 rounded-lg text-[10px] font-black uppercase tracking-widest opacity-0 group-hover:opacity-100 transition-all duration-300 pointer-events-none whitespace-nowrap shadow-xl border border-white/10">
      {label}
    </div>
  </div>
);

export const HotspotsMap = () => {
  return (
    <Card
      variant="white"
      padding="none"
      className="h-[450px] relative overflow-hidden group border-2 border-transparent hover:border-mekong-cyan/20 transition-all duration-500"
    >
      {/* 1. Nền bản đồ vệ tinh (Stylized Satellite Map) */}
      <div className="absolute inset-0 bg-slate-900">
        <img
          src="https://images.unsplash.com/photo-1582103287241-2762adba6c36?auto=format&fit=crop&q=80&w=2000"
          alt="Mekong Delta Satellite"
          className="w-full h-full object-cover opacity-80 mix-blend-luminosity group-hover:mix-blend-normal group-hover:opacity-100 transition-all duration-700"
        />
        {/* Lớp phủ mờ để các điểm Hotspot nổi bật hơn */}
        <div className="absolute inset-0 bg-gradient-to-t from-mekong-navy/40 to-transparent pointer-events-none" />
      </div>

      {/* 2. Floating Info Card (Top Left) - Thiết kế Glassmorphism chuẩn Figma */}
      <div className="absolute top-6 left-6 z-30 animate-in fade-in slide-in-from-left-4 duration-700">
        <div className="bg-white/90 backdrop-blur-xl p-6 rounded-[24px] shadow-2xl border border-white/40 ring-1 ring-black/5">
          <h3 className="text-lg font-black text-mekong-navy leading-none tracking-tighter mb-1">
            Salinity Hotspots
          </h3>
          <p className="text-[10px] font-black text-mekong-slate uppercase tracking-[0.2em] opacity-80">
            Tiền Giang - Bến Tre Region
          </p>

          {/* Legend nhỏ bên trong info card */}
          <div className="flex items-center gap-4 mt-4 pt-4 border-t border-slate-100">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-mekong-critical rounded-full" />
              <span className="text-[9px] font-bold text-mekong-slate uppercase tracking-wider">
                Critical
              </span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-mekong-warning rounded-full" />
              <span className="text-[9px] font-bold text-mekong-slate uppercase tracking-wider">
                Monitoring
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* 3. Các điểm Hotspots giả định dựa trên địa lý */}
      <HotspotMarker
        top="45%"
        left="42%"
        label="Hòa Định Sluice Gate"
        intensity="critical"
      />
      <HotspotMarker
        top="60%"
        left="55%"
        label="Bến Tre Station 04"
        intensity="warning"
      />
      <HotspotMarker
        top="35%"
        left="68%"
        label="Tiền Giang Estuary"
        intensity="critical"
      />

      {/* 4. Mouse Indicator Tooltip (Tùy chọn - Tăng tính công nghệ) */}
      <div className="absolute bottom-6 left-6 flex items-center gap-2 text-white/60 bg-black/20 backdrop-blur-sm px-3 py-1.5 rounded-full text-[9px] font-bold uppercase tracking-widest border border-white/10 pointer-events-none">
        <MousePointer2 size={12} />
        Click to inspect node
      </div>

      {/* 5. Nút mở rộng bản đồ (Open Full Map) */}
      <button className="absolute bottom-6 right-6 z-30 bg-mekong-navy text-white px-6 py-3 rounded-xl font-black text-xs flex items-center gap-3 shadow-2xl hover:bg-mekong-teal hover:scale-105 active:scale-95 transition-all duration-300 group">
        <span>OPEN FULL MAP</span>
        <Maximize2
          size={16}
          className="group-hover:rotate-90 transition-transform duration-500"
        />
      </button>

      {/* 6. Scan Line Effect - Chạy dọc màn hình tạo cảm giác radar/AI */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden opacity-20">
        <div className="w-full h-20 bg-gradient-to-b from-transparent via-mekong-cyan/40 to-transparent absolute top-0 animate-[scan_4s_linear_infinite]" />
      </div>
    </Card>
  );
};

// CSS Animation (Bạn hãy thêm cái này vào index.css hoặc dùng Tailwind keyframes trong config)
// @keyframes scan {
//   from { transform: translateY(-100%); }
//   to { transform: translateY(500%); }
// }
