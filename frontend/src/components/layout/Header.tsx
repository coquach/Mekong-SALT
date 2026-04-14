import React from 'react';
import { Search, Bell, Globe, ChevronDown, Command } from 'lucide-react';

/**
 * HEADER COMPONENT
 * ----------------
 * - Hiệu ứng Glassmorphism (backdrop-blur).
 * - Thanh tìm kiếm tích hợp Shortcut hint.
 * - Khu vực User Profile với phân cấp chữ (Typography Hierarchy) cực mạnh.
 */
export const Header = () => {
  return (
    <header className="h-20 bg-white/80 backdrop-blur-md border-b border-slate-200 sticky top-0 z-40 flex items-center justify-between px-10 transition-all duration-300">
      
      {/* 1. THANH TÌM KIẾM (SEARCH BAR) */}
      <div className="relative w-[420px] group">
        <div className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-mekong-teal transition-colors duration-200">
          <Search size={18} strokeWidth={2.5} />
        </div>
        <input 
          type="text" 
          placeholder="Search insights, reports, or regions..." 
          className="w-full bg-slate-50 border-none rounded-full py-2.5 pl-12 pr-12 text-sm font-medium focus:ring-2 ring-mekong-teal/20 transition-all placeholder:text-slate-400"
        />
        {/* Shortcut Hint - Điểm nhấn UX cho chuyên gia */}
        <div className="absolute right-4 top-1/2 -translate-y-1/2 hidden lg:flex items-center gap-1 px-2 py-1 border border-slate-200 rounded-lg text-[9px] font-black text-slate-400 bg-white shadow-sm pointer-events-none">
          <Command size={10} />
          <span>K</span>
        </div>
      </div>

      {/* 2. KHU VỰC ĐIỀU KHIỂN & NGƯỜI DÙNG (RIGHT ACTIONS) */}
      <div className="flex items-center gap-6">
        
        {/* Bộ chọn Vùng (Region Selector) */}
        <button className="flex items-center gap-3 px-4 py-2.5 rounded-full border border-slate-200 bg-white text-[11px] font-black text-mekong-navy hover:bg-slate-50 hover:border-slate-300 transition-all uppercase tracking-widest shadow-sm group">
          <Globe size={14} className="text-mekong-teal group-hover:rotate-12 transition-transform duration-300" />
          <span>All Regions</span>
          <ChevronDown size={14} className="text-slate-400 group-hover:translate-y-0.5 transition-transform" />
        </button>

        {/* Thông báo (Notifications) */}
        <button className="relative p-2.5 text-slate-500 hover:bg-slate-100 hover:text-mekong-navy rounded-full transition-all group">
          <Bell size={20} strokeWidth={2} className="group-hover:rotate-12 transition-transform" />
          {/* Badge thông báo màu đỏ Critical rực rỡ */}
          <span className="absolute top-2 right-2.5 w-2 h-2 bg-mekong-critical rounded-full border-2 border-white shadow-sm ring-1 ring-mekong-critical/30 animate-pulse" />
        </button>

        {/* Phân tách Hồ sơ người dùng (User Profile Section) */}
        <div className="flex items-center gap-4 pl-6 border-l border-slate-200 ml-2">
          
          {/* Thông tin người dùng - Căn lề phải cực chuẩn */}
          <div className="text-right flex flex-col justify-center">
            <p className="text-[12px] font-black text-mekong-navy uppercase tracking-tighter leading-none mb-1">
              Tran Gia Hien
            </p>
            <p className="text-[10px] text-mekong-slate font-bold uppercase tracking-[0.15em] opacity-70">
              Chief Hydrologist
            </p>
          </div>

          {/* Avatar cao cấp - Kết hợp Ring và Shadow */}
          <div className="relative group cursor-pointer">
            <div className="w-11 h-11 rounded-full p-[2px] bg-gradient-to-tr from-slate-200 to-white shadow-md ring-1 ring-slate-200 group-hover:ring-mekong-cyan/50 transition-all duration-300">
              <div className="w-full h-full rounded-full overflow-hidden border-2 border-white bg-slate-100">
                <img 
                  src="https://i.pravatar.cc/150?u=hien_mekong" 
                  alt="Avatar người dùng" 
                  className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500"
                />
              </div>
            </div>
            
            {/* Chấm trạng thái Online màu Mint đặc trưng */}
            <div className="absolute bottom-0 right-0 w-3.5 h-3.5 bg-mekong-mint border-[3px] border-white rounded-full shadow-sm ring-1 ring-mekong-mint/20" />
            
            {/* Quick Actions Dropdown (Gợi ý mở rộng sau này) */}
            <div className="absolute top-[120%] right-0 w-48 bg-white rounded-2xl shadow-2xl border border-slate-100 p-2 opacity-0 scale-95 translate-y-2 pointer-events-none group-hover:opacity-100 group-hover:scale-100 group-hover:translate-y-0 transition-all duration-300 z-50">
               <button className="w-full text-left px-4 py-2.5 text-[11px] font-bold text-mekong-navy hover:bg-slate-50 rounded-xl transition-colors">Account Settings</button>
               <button className="w-full text-left px-4 py-2.5 text-[11px] font-bold text-mekong-critical hover:bg-red-50 rounded-xl transition-colors">Log Out System</button>
            </div>
          </div>
        </div>

      </div>
    </header>
  );
};