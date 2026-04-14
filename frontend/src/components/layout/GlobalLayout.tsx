import React from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Header } from './Header';

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
        <footer className="mt-auto px-10 py-8 border-t border-slate-100 bg-white/40 backdrop-blur-sm">
          <div className="max-w-[1600px] mx-auto flex flex-col md:flex-row justify-between items-center gap-6">
            
            {/* Project Branding Footer */}
            <div className="flex flex-col gap-1.5 text-center md:text-left">
              <p className="text-[10px] font-black text-mekong-navy uppercase tracking-[0.25em] opacity-60">
                © 2024 MEKONG-SALT PROJECT • Intelligence by Agent Logic V4
              </p>
              <p className="text-[9px] text-mekong-slate font-bold italic tracking-tight">
                A collaborative platform for hydrologic intelligence and salinity intrusion management.
              </p>
            </div>
            
            {/* Governance & Compliance Links */}
            <div className="flex items-center gap-8 text-[9px] font-black text-mekong-slate uppercase tracking-widest">
              <button className="hover:text-mekong-teal transition-colors duration-200">Privacy Policy</button>
              <button className="hover:text-mekong-teal transition-colors duration-200">Security Protocols</button>
              <button className="hover:text-mekong-teal transition-colors duration-200">API V2.4-STABLE</button>
              
              {/* Badge phiên bản hệ thống */}
              <div className="px-2 py-1 bg-slate-100 rounded text-mekong-navy border border-slate-200">
                NODES: 42/42 ACTIVE
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