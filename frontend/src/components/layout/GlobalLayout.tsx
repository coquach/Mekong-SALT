import { Outlet } from "react-router-dom";
import { Sidebar } from "./Sidebar";
import { Header } from "./Header";

/**
 * THÀNH PHẦN BỐ CỤC CHUNG (GLOBAL LAYOUT)
 * -----------------------
 * Thiết lập cấu trúc chuẩn cho Dashboard:
 * - Sidebar: Cố định bên trái (Rộng 256px).
 * - Header: Dính (Sticky) phía trên cùng, có hiệu ứng làm mờ hậu cảnh.
 * - Main: Vùng chứa nội dung chính, có hỗ trợ cuộn trang (Outlet).
 */
export const GlobalLayout = () => {
  return (
    <div className="flex min-h-screen bg-mekong-bg font-sans selection:bg-mekong-cyan selection:text-mekong-navy antialiased">
      {/* 1. THANH BÊN (SIDEBAR) - Cố định bên trái */}
      {/* Độ rộng w-64 tương đương 256px, khớp với ml-64 của phần Nội dung chính */}
      <Sidebar />

      {/* 2. KHUNG CHỨA NỘI DUNG CHÍNH */}
      <div className="flex-1 ml-72 flex flex-col min-w-0">
        {/* 3. THANH ĐẦU TRANG (HEADER) - Sticky phía trên cùng */}
        <Header />

        {/* 4. VÙNG HIỂN THỊ NỘI DUNG - Nơi render các trang con (Bảng điều khiển, Bản đồ, v.v.) */}
        <main className="flex-1 p-8 lg:p-10 relative overflow-x-hidden">
          {/* Container giới hạn độ rộng để đảm bảo thẩm mỹ trên màn hình siêu rộng (Ultrawide) */}
          <div className="max-w-[1600px] mx-auto w-full">
            {/* 
              Hiệu ứng chuyển cảnh (Entry Animation):
              Sử dụng tailwindcss-animate để tạo cảm giác nội dung trồi lên mượt mà khi chuyển trang.
            */}
            <div className="animate-in fade-in slide-in-from-bottom-3 duration-700 ease-out fill-mode-both">
              <Outlet />
            </div>
          </div>
        </main>

        {/* 5. CHÂN TRANG HỆ THỐNG (GLOBAL FOOTER) */}
        <footer className="mt-auto px-10 py-10 border-t border-slate-200 bg-white/50 backdrop-blur-md">
          <div className="max-w-[1600px] mx-auto flex flex-col lg:flex-row justify-between items-center gap-8">
            {/* BÊN TRÁI: BẢN QUYỀN & KHẨU HIỆU */}
            <div className="flex flex-col gap-2 text-center lg:text-left">
              <p className="text-[13px] font-black text-mekong-navy uppercase tracking-[0.2em] opacity-70">
                © 2024 DỰ ÁN MEKONG-SALT • Vận hành bởi Logic AI V4
              </p>
              <p className="text-[12px] text-mekong-slate font-bold italic tracking-wide opacity-80">
                Nền tảng cộng tác về trí tuệ thủy văn và quản lý xâm nhập mặn
                vùng Đồng bằng sông Cửu Long.
              </p>
            </div>

            {/* BÊN PHẢI: LIÊN KẾT & TRẠNG THÁI HỆ THỐNG */}
            <div className="flex flex-wrap justify-center items-center gap-10">
              {/* Các liên kết chính sách và kỹ thuật */}
              <div className="flex gap-8 text-[12px] font-black text-mekong-navy uppercase tracking-widest">
                <button className="hover:text-mekong-teal transition-colors duration-200">
                  Chính sách Bảo mật
                </button>
                <button className="hover:text-mekong-teal transition-colors duration-200">
                  Giao thức An ninh
                </button>
                <button className="hover:text-mekong-teal transition-colors duration-200 opacity-60">
                  API V2.4-ỔN ĐỊNH
                </button>
              </div>

              {/* Trạng thái các Nút cảm biến (Node Status) */}
              <div className="px-4 py-2 bg-white rounded-xl text-[11px] font-black text-mekong-navy border border-slate-200 shadow-sm flex items-center gap-2">
                <div className="w-2 h-2 bg-mekong-mint rounded-full animate-pulse" />
                <span className="uppercase tracking-widest">
                  Trạm: 42/42 Đang hoạt động
                </span>
              </div>
            </div>
          </div>
        </footer>
      </div>

      {/* 6. TRANG TRÍ NỀN (BACKGROUND DECORATION) 
          Thêm hiệu ứng gradient mờ ở góc màn hình để tăng tính công nghệ và thẩm mỹ 
      */}
      <div className="fixed -bottom-40 -right-40 w-[600px] h-[600px] bg-mekong-cyan/5 rounded-full blur-[120px] pointer-events-none -z-10" />
    </div>
  );
};
