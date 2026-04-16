import React from "react";
import { Outlet } from "react-router-dom";
import { Sidebar } from "./Sidebar";
import { Header } from "./Header";

/**
 * GLOBAL LAYOUT COMPONENT
 * -----------------------
 * Bố cục chuẩn Dashboard:
 * - Sidebar: Cố định bên trái (Fixed 256px).
 * - Header: Sticky bên trên cùng, có hiệu ứng blur.
 * - Main: Vùng cuộn chứa nội dung các trang (Outlet).
 */
export const GlobalLayout = () => {
  return (
    <div className="flex min-h-screen bg-mekong-bg font-sans selection:bg-mekong-cyan selection:text-mekong-navy antialiased">
      {/* 1. SIDEBAR - Cố định bên trái */}
      {/* Độ rộng w-64 tương đương 256px, khớp với ml-64 của phần Main */}
      <Sidebar />

      {/* 2. MAIN CONTENT WRAPPER */}
      <div className="flex-1 ml-64 flex flex-col min-w-0">
        {/* 3. HEADER - Sticky (dính) trên cùng khi cuộn trang */}
        <Header />

        {/* 4. CONTENT AREA - Nơi render các Pages (Dashboard, Map, v.v.) */}
        <main className="flex-1 p-8 lg:p-10 relative overflow-x-hidden">
          {/* Container giới hạn độ rộng để UI không bị loãng trên màn hình Ultrawide */}
          <div className="max-w-[1600px] mx-auto w-full">
            {/* 
              Hiệu ứng Entry Animation cho toàn bộ trang con:
              Sử dụng tailwindcss-animate để tạo cảm giác trang "trồi" lên mượt mà.
            */}
            <div className="animate-in fade-in slide-in-from-bottom-3 duration-700 ease-out fill-mode-both">
              <Outlet />
            </div>
          </div>
        </main>

        {/* 5. GLOBAL FOOTER - Tinh tế và chuyên nghiệp */}
        {/* --- GLOBAL FOOTER: ENHANCED TEXT SIZE --- */}
        <footer className="mt-auto px-10 py-10 border-t border-slate-200 bg-white/50 backdrop-blur-md">
          <div className="max-w-[1600px] mx-auto flex flex-col lg:flex-row justify-between items-center gap-8">
            {/* BÊN TRÁI: COPYRIGHT & TAGLINE (Đã phóng to) */}
            <div className="flex flex-col gap-2 text-center lg:text-left">
              <p className="text-[13px] font-black text-mekong-navy uppercase tracking-[0.2em] opacity-70">
                © 2024 MEKONG-SALT PROJECT • Intelligence by Agent Logic V4
              </p>
              <p className="text-[12px] text-mekong-slate font-bold italic tracking-wide opacity-80">
                A collaborative platform for hydrologic intelligence and
                salinity intrusion management.
              </p>
            </div>

            {/* BÊN PHẢI: LINKS & NODES STATUS (Đã phóng to) */}
            <div className="flex flex-wrap justify-center items-center gap-10">
              {/* Các đường Link chính sách */}
              <div className="flex gap-8 text-[12px] font-black text-mekong-navy uppercase tracking-widest">
                <button className="hover:text-mekong-teal transition-colors duration-200">
                  Privacy Policy
                </button>
                <button className="hover:text-mekong-teal transition-colors duration-200">
                  Security Protocols
                </button>
                <button className="hover:text-mekong-teal transition-colors duration-200 opacity-60">
                  API V2.4-STABLE
                </button>
              </div>

              {/* Badge trạng thái Node - Phóng to và thêm Shadow nhẹ */}
              <div className="px-4 py-2 bg-white rounded-xl text-[11px] font-black text-mekong-navy border border-slate-200 shadow-sm flex items-center gap-2">
                <div className="w-2 h-2 bg-mekong-mint rounded-full animate-pulse" />
                <span className="uppercase tracking-widest">
                  Nodes: 42/42 Active
                </span>
              </div>
            </div>
          </div>
        </footer>
      </div>

      {/* 6. BACKGROUND DECORATION (Tùy chọn) 
          Thêm một chút gradient mờ ở góc màn hình để tăng tính thẩm mỹ 
      */}
      <div className="fixed -bottom-40 -right-40 w-[600px] h-[600px] bg-mekong-cyan/5 rounded-full blur-[120px] pointer-events-none -z-10" />
    </div>
  );
};
