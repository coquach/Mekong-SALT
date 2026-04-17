import { useState } from "react";
import {
  Search,
  Bell,
  ChevronDown,
  Sparkles,
  MapPin,
  Check,
} from "lucide-react";
import { useNavigate } from "react-router-dom";

export const Header = () => {
  const navigate = useNavigate();
  const [isOpen, setIsOpen] = useState(false);
  const [selectedRegion, setSelectedRegion] = useState("Tiền Giang");

  const regions = [
    "Tiền Giang",
    "Bến Tre",
    "Sóc Trăng",
    "Long An",
    "Trà Vinh",
    "Tất cả khu vực",
  ];

  const handleRegionSelect = (region: string) => {
    setSelectedRegion(region);
    setIsOpen(false);
    navigate("/map");
  };

  return (
    <header className="h-24 bg-white/90 backdrop-blur-xl border-b border-slate-200 sticky top-0 z-40 flex items-center justify-between px-10 transition-all">
      {/* 1. THANH TÌM KIẾM DÀI (MAX-W-[600PX]) */}
      <div className="relative flex-1 max-w-[600px] group mr-8">
        <div className="absolute left-5 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-mekong-teal transition-colors">
          <Search size={20} strokeWidth={2.5} />
        </div>
        <input
          type="text"
          placeholder="Tìm kiếm dữ liệu trạm, báo cáo đỉnh mặn, kịch bản AI..."
          className="w-full bg-slate-100 border-2 border-transparent rounded-2xl py-3.5 pl-14 pr-12 text-sm font-bold focus:bg-white focus:border-mekong-teal/30 focus:ring-4 ring-mekong-teal/10 transition-all outline-none placeholder:text-slate-400 shadow-inner"
        />
        <button className="absolute right-2 top-1/2 -translate-y-1/2 bg-mekong-navy text-white px-4 py-1.5 rounded-full text-[10px] font-black uppercase tracking-widest hover:bg-mekong-teal transition-all flex items-center gap-2 shadow-md">
          <Sparkles size={12} className="text-mekong-cyan" />
          <span>Tìm kiếm</span>
        </button>
      </div>

      {/* 2. KHU VỰC ĐIỀU KHIỂN & NÚT KHU VỰC NỔI BẬT */}
      <div className="flex items-center gap-6">
        {/* NÚT CHỌN KHU VỰC - THIẾT KẾ NỔI BẬT (PRIMARY STYLE) */}
        <div className="relative">
          <button
            onClick={() => setIsOpen(!isOpen)}
            className={`
              flex items-center gap-4 px-6 py-3 rounded-2xl transition-all uppercase tracking-[0.1em] group
              ${
                isOpen
                  ? "bg-mekong-navy text-white shadow-2xl scale-105"
                  : "bg-mekong-teal text-white shadow-lg shadow-mekong-teal/30 hover:bg-mekong-teal/90 hover:-translate-y-0.5 active:scale-95"
              }
            `}
          >
            <div className="bg-white/20 p-1.5 rounded-lg">
              <MapPin size={18} className="text-white animate-pulse" />
            </div>
            <div className="flex flex-col items-start leading-none">
              <span
                className={`text-[9px] font-black mb-1 ${isOpen ? "text-mekong-cyan" : "text-cyan-100"}`}
              >
                TRẠM ĐANG ĐO
              </span>
              <span className="text-[13px] font-black">{selectedRegion}</span>
            </div>
            <ChevronDown
              size={16}
              className={`transition-transform duration-500 ${isOpen ? "rotate-180 text-mekong-cyan" : "text-white/70"}`}
            />
          </button>

          {/* DROPDOWN MENU - THIẾT KẾ CAO CẤP */}
          {isOpen && (
            <>
              <div
                className="fixed inset-0 z-10"
                onClick={() => setIsOpen(false)}
              ></div>
              <div className="absolute top-[120%] right-0 w-64 bg-white rounded-[24px] shadow-[0_20px_50px_rgba(0,0,0,0.15)] border border-slate-100 p-2.5 z-20 animate-in fade-in slide-in-from-top-2 duration-300">
                <div className="px-4 py-3 mb-2 bg-slate-50 rounded-xl">
                  <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">
                    Phạm vi giám sát
                  </p>
                </div>
                <div className="space-y-1">
                  {regions.map((region) => (
                    <button
                      key={region}
                      onClick={() => handleRegionSelect(region)}
                      className={`
                        w-full flex items-center justify-between px-4 py-3 rounded-xl text-[13px] font-black transition-all
                        ${
                          selectedRegion === region
                            ? "bg-mekong-navy text-white shadow-lg"
                            : "text-mekong-navy hover:bg-cyan-50 hover:text-mekong-teal"
                        }
                      `}
                    >
                      {region}
                      {selectedRegion === region && (
                        <Check
                          size={16}
                          className="text-mekong-cyan"
                          strokeWidth={3}
                        />
                      )}
                    </button>
                  ))}
                </div>
              </div>
            </>
          )}
        </div>

        {/* THÔNG BÁO & USER */}
        <div className="flex items-center gap-4 pl-6 border-l-2 border-slate-100">
          <button className="relative p-3 bg-slate-50 text-slate-500 hover:bg-red-50 hover:text-mekong-critical rounded-2xl transition-all group shadow-sm">
            <Bell
              size={22}
              className="group-hover:rotate-12 transition-transform"
            />
            <span className="absolute top-2.5 right-2.5 w-2.5 h-2.5 bg-mekong-critical rounded-full border-2 border-white animate-pulse" />
          </button>

          <div className="flex items-center gap-3 ml-2 group cursor-pointer">
            <div className="text-right hidden xl:block">
              <p className="text-[12px] font-black text-mekong-navy uppercase tracking-tighter leading-none mb-1">
                Trần Gia Hiển
              </p>
              <p className="text-[10px] text-mekong-teal font-black uppercase opacity-80">
                Chief Admin
              </p>
            </div>
            <div className="relative">
              <div className="w-12 h-12 rounded-2xl border-2 border-white shadow-md overflow-hidden ring-2 ring-slate-100 group-hover:ring-mekong-teal transition-all">
                <img
                  src="../src/assets/hien.jpg"
                  alt="Avatar"
                  className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500"
                />
              </div>
              <div className="absolute -bottom-1 -right-1 w-4 h-4 bg-mekong-mint border-2 border-white rounded-full"></div>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};
