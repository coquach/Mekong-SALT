import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { 
  LayoutDashboard, 
  Map as MapIcon, 
  BrainCircuit, 
  ClipboardList, 
  History, 
  Info, 
  Circle,
  HelpCircle,
  FileText
} from 'lucide-react';

/**
 * SIDEBAR COMPONENT
 * -----------------
 * - Quản lý điều hướng chính của hệ thống.
 * - Tự động phát hiện trạng thái Active dựa trên URL.
 * - Hiển thị trạng thái hệ thống (System Health) thời gian thực.
 */

// Interface cho các mục menu
interface NavItemProps {
  icon: React.ElementType;
  label: string;
  path: string;
  isActive: boolean;
}

// Thành phần con cho từng mục menu (Atomic Component)
const NavItem = ({ icon: Icon, label, path, isActive }: NavItemProps) => {
  return (
    <Link
      to={path}
      className={`
        flex items-center gap-3 px-4 py-3.5 rounded-xl text-[12px] font-black tracking-tight transition-all duration-200
        ${isActive 
          ? 'bg-cyan-50 text-mekong-teal shadow-sm ring-1 ring-mekong-cyan/20' 
          : 'text-mekong-slate hover:bg-slate-50 hover:text-mekong-navy'
        }
      `}
    >
      <Icon 
        size={20} 
        strokeWidth={isActive ? 2.5 : 2} 
        className={isActive ? 'text-mekong-teal' : 'text-mekong-slate/80'} 
      />
      <span className="uppercase tracking-widest">{label}</span>
    </Link>
  );
};

export const Sidebar = () => {
  const { pathname } = useLocation();

  // Danh sách menu dựa trên thiết kế Figma
  const menuItems = [
    { icon: Info, label: 'Information Hub', path: '/' },
    { icon: LayoutDashboard, label: 'Dashboard', path: '/dashboard' },
    { icon: MapIcon, label: 'Interactive Map', path: '/map' },
    { icon: BrainCircuit, label: 'Agent Logic', path: '/strategy' },
    { icon: ClipboardList, label: 'Action Logs', path: '/logs' },
    { icon: History, label: 'History', path: '/history' },
  ];

  return (
    <aside className="w-64 h-screen bg-white border-r border-slate-200 fixed left-0 top-0 flex flex-col z-50 transition-all duration-300">
      
      {/* 1. LOGO & BRANDING AREA */}
      <div className="p-8 flex items-center gap-3 mb-4">
        {/* Logo Icon Box - Navy Blue chuẩn dự án */}
        <div className="bg-mekong-navy p-2.5 rounded-xl text-white shadow-lg shadow-mekong-navy/20 transform group-hover:rotate-6 transition-transform">
          <MapIcon size={24} strokeWidth={2.5} />
        </div>
        <div className="flex flex-col">
          <h1 className="font-black text-xl text-mekong-navy leading-none tracking-tighter">
            Mekong-SALT
          </h1>
          <p className="text-[9px] text-mekong-slate font-black uppercase tracking-[0.18em] mt-1 opacity-70">
            AI Salinity Management
          </p>
        </div>
      </div>

      {/* 2. NAVIGATION LINKS */}
      <nav className="flex-1 px-4 space-y-1.5 overflow-y-auto custom-scrollbar">
        {menuItems.map((item) => (
          <NavItem
            key={item.path}
            icon={item.icon}
            label={item.label}
            path={item.path}
            isActive={
              item.path === '/' 
                ? pathname === '/' 
                : pathname.startsWith(item.path)
            }
          />
        ))}
      </nav>

      {/* 3. BOTTOM UTILITIES & SYSTEM STATUS */}
      <div className="p-6 mt-auto border-t border-slate-50 space-y-5">
        
        {/* System Status Indicator Card - Chứa hiệu ứng Pulsing */}
        <div className="bg-slate-50 p-4 rounded-2xl border border-slate-100 group cursor-default hover:bg-white hover:shadow-md hover:border-mekong-mint/30 transition-all duration-300">
          <div className="flex items-center gap-2.5 mb-1.5">
            <div className="relative flex h-2 w-2">
              <Circle size={8} className="fill-mekong-mint text-mekong-mint" />
              {/* Hiệu ứng nhịp đập (Heartbeat) của AI Sentinel */}
              <div className="absolute inset-0 bg-mekong-mint rounded-full animate-ping opacity-40" />
            </div>
            <span className="text-[10px] font-black text-mekong-navy uppercase tracking-widest">
              System Status: Active
            </span>
          </div>
          <p className="text-[10px] text-mekong-slate font-bold pl-[18px] opacity-80 leading-tight">
            Sentinel nodes responding <br/> with 99.4% accuracy
          </p>
        </div>

        {/* Support & Documentation Quick Links */}
        <div className="flex flex-col gap-1.5 px-2">
          <button className="flex items-center gap-3 py-2 text-[11px] font-black text-mekong-slate hover:text-mekong-teal transition-colors group uppercase tracking-widest">
            <HelpCircle size={16} className="group-hover:scale-110 transition-transform" />
            Support
          </button>
          <button className="flex items-center gap-3 py-2 text-[11px] font-black text-mekong-slate hover:text-mekong-teal transition-colors group uppercase tracking-widest">
            <FileText size={16} className="group-hover:scale-110 transition-transform" />
            Documentation
          </button>
        </div>
      </div>
    </aside>
  );
};