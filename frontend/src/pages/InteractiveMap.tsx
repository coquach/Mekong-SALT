import React, { useState } from "react";
import {
  Layers,
  Maximize2,
  AlertTriangle,
  Zap,
  X,
  TrendingUp,
  MapPin,
  ChevronRight,
  Eye,
  ShieldCheck,
  Navigation,
} from "lucide-react";
import { Card, CardContent } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Badge } from "../components/ui/Badge";
import { SatelliteMap } from "../components/dashboard/SatelliteMap";
import { useNavigate } from "react-router-dom";

/**
 * TRANG 3: BẢN ĐỒ TƯƠNG TÁC (INTERACTIVE MAP) - AGENTIC VERSION
 * -----------------------------------------------------------
 * Chức năng Agentic:
 * 1. Layer Dự báo Proactive: Hiển thị vùng mặn dự kiến xâm nhập trong 45 phút tới.
 * 2. Gate Autonomy: Hiển thị trạng thái đóng/mở tự động của các cống PLC.
 * 3. Human-in-the-loop: Cho phép người dùng ghi đè (Manual Override) lệnh của AI.
 */

const LayerSwitch = ({ label, active, onToggle, icon: Icon }: any) => (
  <div
    className="flex items-center justify-between py-3 cursor-pointer group"
    onClick={onToggle}
  >
    <div className="flex items-center gap-3">
      <Icon
        size={16}
        className={active ? "text-mekong-teal" : "text-slate-400"}
      />
      <span
        className={`text-[11px] font-black uppercase tracking-widest transition-colors ${active ? "text-mekong-navy" : "text-slate-400"}`}
      >
        {label}
      </span>
    </div>
    <div
      className={`w-9 h-5 rounded-full relative transition-all ${active ? "bg-mekong-mint" : "bg-slate-200"}`}
    >
      <div
        className={`absolute top-1 w-3 h-3 bg-white rounded-full transition-all ${active ? "right-1" : "left-1"}`}
      />
    </div>
  </div>
);

export const InteractiveMap = () => {
  const [layers, setLayers] = useState({
    heatmap: true,
    stations: true,
    gates: true,
    prediction: true, // Lớp dự báo Proactive
  });

  const navigate = useNavigate(); // Khởi tạo hàm này

  return (
    <div className="relative w-full h-[calc(100vh-120px)] rounded-[48px] overflow-hidden bg-slate-900 shadow-2xl border border-white/10">
      {/* --- BẢN ĐỒ VỆ TINH TÍCH HỢP LỚP DỮ LIỆU AGENT --- */}
      <SatelliteMap layers={layers} zoom={15} showControls={true} />

      {/* --- GÓC TRÊN TRÁI: ĐIỀU KHIỂN LỚP NHẬN THỨC (COGNITIVE LAYERS) --- */}
      <div className="absolute top-8 left-8 z-20 space-y-4 w-72">
        <Card
          variant="glass"
          className="p-6 rounded-[32px] border-white/40 shadow-glass backdrop-blur-2xl"
        >
          <div className="flex items-center gap-3 mb-6 border-b border-mekong-navy/10 pb-4">
            <Layers size={18} className="text-mekong-navy" />
            <h3 className="text-sm font-black text-mekong-navy uppercase tracking-widest">
              Lớp Nhận Thức AI
            </h3>
          </div>
          <div className="space-y-1">
            <LayerSwitch
              label="Bản đồ nhiệt mặn"
              active={layers.heatmap}
              icon={Eye}
              onToggle={() =>
                setLayers({ ...layers, heatmap: !layers.heatmap })
              }
            />
            <LayerSwitch
              label="Trạm Cảm Biến IoT"
              active={layers.stations}
              icon={MapPin}
              onToggle={() =>
                setLayers({ ...layers, stations: !layers.stations })
              }
            />
            <LayerSwitch
              label="Hạ tầng Cống PLC"
              active={layers.gates}
              icon={ShieldCheck}
              onToggle={() => setLayers({ ...layers, gates: !layers.gates })}
            />
            <LayerSwitch
              label="Vùng mặn dự báo (45p)"
              active={layers.prediction}
              icon={TrendingUp}
              onToggle={() =>
                setLayers({ ...layers, prediction: !layers.prediction })
              }
            />
          </div>
        </Card>

        {/* Chú giải độ mặn bám sát Proposal */}
        <Card
          variant="glass"
          className="p-3.5 rounded-2xl border-white/35 shadow-md w-64"
        >
          <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-3 italic">
            Chỉ số xâm nhập (g/L)
          </p>
          <div className="flex h-2 rounded-full overflow-hidden mb-2">
            <div className="flex-1 bg-mekong-mint" /> {/* < 0.5 g/L */}
            <div className="flex-1 bg-yellow-400" />
            <div className="flex-1 bg-orange-500" />
            <div className="flex-1 bg-mekong-critical" /> {/* > 2.0 g/L */}
          </div>
          <div className="flex justify-between text-[9px] font-black text-slate-400 uppercase">
            <span>0.5 (An toàn)</span>
            <span>2.0 (Nguy hiểm)</span>
          </div>
        </Card>
      </div>

      {/* --- GÓC TRÊN PHẢI: HÀNH ĐỘNG TỰ TRỊ & GHI ĐÈ --- */}
      <div className="absolute top-8 right-8 z-20 flex flex-col items-end gap-5 w-80">
        {/* MANUAL OVERRIDE (Human-in-the-loop) */}
        <div className="flex flex-col gap-3 w-full">
          <button className="group flex items-center justify-between bg-white/90 backdrop-blur-md px-5 py-3.5 rounded-2xl shadow-xl hover:bg-white transition-all border border-white/20">
            <div className="flex items-center gap-3">
              <Maximize2
                size={18}
                className="text-mekong-navy group-hover:rotate-45 transition-transform"
              />
              <span className="text-[11px] font-black text-mekong-navy uppercase tracking-[0.2em]">
                Ghi đè Hệ thống
              </span>
            </div>
            <Badge variant="cyan" className="text-[9px] border-slate-200">
              BẬT
            </Badge>
          </button>

          <button className="group flex items-center gap-3 bg-mekong-critical text-white px-5 py-3.5 rounded-2xl shadow-2xl hover:bg-red-700 transition-all border border-white/10">
            <AlertTriangle
              size={18}
              strokeWidth={2.5}
              className="group-hover:animate-bounce"
            />
            <span className="text-[11px] font-black uppercase tracking-[0.2em]">
              Báo lỗi cảm biến
            </span>
          </button>
        </div>

        {/* LOGIC CỐNG TỰ ĐỘNG (AUTO-GATE STATUS) */}
        <Card
          variant="navy"
          padding="none"
          className="w-full rounded-[32px] bg-[#00203F]/95 backdrop-blur-xl border border-white/10 shadow-2xl overflow-hidden group"
        >
          <div className="p-6 relative z-10">
            <div className="flex items-center gap-3 mb-8 text-mekong-cyan">
              <Zap size={20} fill="currentColor" className="animate-pulse" />
              <h3 className="text-[10px] font-black uppercase tracking-[0.3em] leading-none">
                Trạng thái Logic Cống
              </h3>
            </div>

            <div className="space-y-5">
              {[
                {
                  label: "Cống Hai Tân",
                  status: "ĐANG ĐÓNG",
                  variant: "critical" as const,
                },
                {
                  label: "Cống Cây Cồng",
                  status: "SẴN SÀNG",
                  variant: "optimal" as const,
                },
                {
                  label: "Nút S-12",
                  status: "ĐANG XẢ",
                  variant: "warning" as const,
                },
              ].map((item, i) => (
                <div key={i} className="flex items-center justify-between">
                  <span className="text-[13px] font-bold text-slate-400">
                    {item.label}
                  </span>
                  <Badge
                    variant={item.variant}
                    className="text-[9px] py-1 px-3 min-w-[100px] text-center justify-center font-black"
                  >
                    {item.status}
                  </Badge>
                </div>
              ))}
            </div>
          </div>
          <div className="h-1 w-full bg-gradient-to-r from-transparent via-mekong-cyan/20 to-transparent" />
        </Card>
      </div>

      {/* --- DƯỚI CÙNG: CHI TIẾT ĐIỂM QUAN TRẮC (DEEP DIVE) --- */}
      <div className="absolute bottom-5 left-8 right-32 z-30">
        <Card
          variant="glass"
          className="rounded-[40px] p-10 shadow-glass border-white/60 backdrop-blur-3xl ring-1 ring-black/5 animate-in slide-in-from-bottom-10"
        >
          <div className="flex justify-between items-start mb-8">
            <div className="space-y-1">
              <div className="flex items-center gap-4">
                <h2 className="text-4xl font-black text-mekong-navy tracking-tighter uppercase leading-none">
                  Trạm: Hai Tân
                </h2>
                <Badge variant="critical" dot className="py-1.5 px-4">
                  Cảnh báo mặn tăng nhanh
                </Badge>
              </div>
              <p className="text-sm font-bold text-mekong-slate uppercase tracking-widest opacity-70">
                Khu vực: Sông Mỹ Tho | Tọa độ: 10.352, 106.365
              </p>
            </div>
            <button className="p-3 hover:bg-slate-200/50 rounded-full transition-all">
              <X size={24} className="text-mekong-navy" />
            </button>
          </div>

          <div className="grid grid-cols-12 gap-8 items-end">
            {/* THÔNG SỐ THỰC ĐỊA */}
            <div className="col-span-6 grid grid-cols-2 gap-4">
              {[
                {
                  label: "Chỉ số hiện tại",
                  val: "1",
                  unit: "g/L",
                  color: "text-mekong-critical",
                },
                {
                  label: "Thủy triều",
                  val: "+1.2",
                  unit: "m",
                  color: "text-mekong-teal",
                },
                {
                  label: "Vận tốc gió",
                  val: "Cấp 6",
                  unit: "Gió chướng",
                  color: "text-mekong-navy",
                },
                {
                  label: "Dự báo đỉnh (45p)",
                  val: "1.4",
                  unit: "g/L",
                  color: "text-mekong-critical",
                  bg: "bg-red-50/50",
                },
              ].map((m, i) => (
                <div
                  key={i}
                  className={`p-6 rounded-3xl border border-white/40 bg-white/40 shadow-sm ${m.bg}`}
                >
                  <p className="text-[9px] font-black text-slate-500 uppercase tracking-widest mb-3">
                    {m.label}
                  </p>
                  <div className="flex items-baseline gap-2">
                    <span
                      className={`text-3xl font-black ${m.color} tracking-tighter`}
                    >
                      {m.val}
                    </span>
                    <span className="text-[10px] font-bold text-slate-400 uppercase">
                      {m.unit}
                    </span>
                  </div>
                </div>
              ))}
            </div>

            {/* KẾ HOẠCH HÀNH ĐỘNG CỦA AGENT CHO TRẠM NÀY */}
            <div className="col-span-6 bg-mekong-navy p-8 rounded-[32px] border border-white/10 text-white relative overflow-hidden">
              <div className="flex items-center gap-3 mb-6">
                <Navigation
                  size={20}
                  className="text-mekong-cyan animate-bounce"
                />
                <h3 className="text-sm font-black uppercase tracking-widest">
                  Kế hoạch can thiệp của Agent
                </h3>
              </div>
              <div className="space-y-4">
                <p className="text-[13px] text-blue-100/80 leading-relaxed italic">
                  "Dựa trên nồng độ 1 g/L và gió cấp 6, tôi sẽ kích hoạt đóng
                  cống Hai Tân sau 20 phút nữa để chủ tàu thuyền kịp di chuyển
                  ra khỏi vị trí nguy hiểm."
                </p>
                <div className="flex gap-4 pt-2">
                  <Button
                    variant="cyan"
                    className="h-10 text-[10px] font-black flex-1 shadow-lg"
                  >
                    PHÊ DUYỆT LỘ TRÌNH
                  </Button>
                  <Button
                    variant="outline"
                    className="h-10 text-[10px] font-black flex-1 border-white/20 text-white"
                    onClick={() => navigate("/strategy")}
                  >
                    CHI TIẾT LOGIC
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default InteractiveMap;
