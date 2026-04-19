import { Link, useLocation } from "react-router-dom";
import {
  Bell,
  BookOpen,
  BrainCircuit,
  Circle,
  ClipboardList,
  FileText,
  HelpCircle,
  History,
  Info,
  LayoutDashboard,
  Map as MapIcon,
} from "lucide-react";

import { APP_ROUTES } from "../../lib/navigation";

function prefetchRoute(path: string): void {
  if (path === "/dashboard") {
    void import("../../pages/Dashboard");
    return;
  }
  if (path === "/map") {
    void import("../../pages/InteractiveMap");
    return;
  }
  if (path === "/strategy") {
    void import("../../pages/StrategyOrchestration");
    return;
  }
  if (path === "/logs") {
    void import("../../pages/ActionLogs");
    return;
  }
  if (path === "/notifications") {
    void import("../../pages/Notifications");
    return;
  }
  if (path === "/history") {
    void import("../../pages/History");
    return;
  }
  if (path === "/memory-cases") {
    void import("../../pages/MemoryCases");
  }
}

interface NavItemProps {
  icon: React.ElementType;
  label: string;
  path: string;
  isActive: boolean;
}

const NavItem = ({ icon: Icon, label, path, isActive }: NavItemProps) => {
  return (
    <Link
      to={path}
      onMouseEnter={() => prefetchRoute(path)}
      onFocus={() => prefetchRoute(path)}
      aria-current={isActive ? "page" : undefined}
      className={`flex items-center gap-3 rounded-xl px-4 py-3.5 text-[12px] font-black tracking-tight transition-all duration-200 ${
        isActive
          ? "bg-cyan-50 text-mekong-teal shadow-sm ring-1 ring-mekong-cyan/20"
          : "text-mekong-slate hover:bg-slate-50 hover:text-mekong-navy"
      }`}
    >
      <Icon
        size={20}
        strokeWidth={isActive ? 2.5 : 2}
        className={isActive ? "text-mekong-teal" : "text-mekong-slate/80"}
      />
      <span className="uppercase tracking-widest">{label}</span>
    </Link>
  );
};

export const Sidebar = () => {
  const { pathname } = useLocation();

  const routeIcons: Record<string, React.ElementType> = {
    "/": Info,
    "/dashboard": LayoutDashboard,
    "/map": MapIcon,
    "/strategy": BrainCircuit,
    "/logs": ClipboardList,
    "/notifications": Bell,
    "/history": History,
    "/memory-cases": BookOpen,
  };

  const menuItems = APP_ROUTES.map((route) => ({
    path: route.path,
    label: route.navLabel,
    icon: routeIcons[route.path] ?? Info,
  }));

  return (
    <aside className="fixed left-0 top-0 z-50 hidden h-screen w-72 flex-col border-r border-slate-200 bg-white transition-all duration-300 lg:flex">
      <div className="group mb-4 flex items-center gap-3 p-8">
        <div className="rounded-xl bg-mekong-navy p-2.5 text-white shadow-lg shadow-mekong-navy/20 transition-transform group-hover:rotate-6">
          <MapIcon size={24} strokeWidth={2.5} />
        </div>
        <div className="flex flex-col">
          <h1 className="text-xl font-black leading-none tracking-tighter text-mekong-navy">Mekong-SALT</h1>
          <p className="mt-1 text-[9px] font-black uppercase tracking-[0.18em] text-mekong-slate opacity-70">
            Quản lý độ mặn bằng AI
          </p>
        </div>
      </div>

      <nav className="flex-1 space-y-1.5 overflow-y-auto px-4 custom-scrollbar" aria-label="Main navigation">
        {menuItems.map((item) => (
          <NavItem
            key={item.path}
            icon={item.icon}
            label={item.label}
            path={item.path}
            isActive={item.path === "/" ? pathname === "/" : pathname.startsWith(item.path)}
          />
        ))}
      </nav>

      <div className="mt-auto space-y-5 border-t border-slate-50 p-6">
        <div className="group cursor-default rounded-2xl border border-slate-100 bg-slate-50 p-4 transition-all duration-300 hover:border-mekong-mint/30 hover:bg-white hover:shadow-md">
          <div className="mb-1.5 flex items-center gap-2.5">
            <div className="relative flex h-2 w-2">
              <Circle size={8} className="fill-mekong-mint text-mekong-mint" />
              <div className="absolute inset-0 animate-ping rounded-full bg-mekong-mint opacity-40" />
            </div>
            <span className="text-[10px] font-black uppercase tracking-widest text-mekong-navy">
              Hệ thống: Hoạt động
            </span>
          </div>
          <p className="pl-4.5 text-[10px] font-bold leading-tight text-mekong-slate opacity-80">
            Các nút cảm biến phản hồi <br /> với độ chính xác 99.4%
          </p>
        </div>

        <div className="flex flex-col gap-1.5 px-2">
          <button type="button" className="flex items-center gap-3 py-2 text-[11px] font-black uppercase tracking-widest text-mekong-slate transition-colors hover:text-mekong-teal">
            <HelpCircle size={16} className="transition-transform group-hover:scale-110" />
            Trợ giúp
          </button>
          <button type="button" className="flex items-center gap-3 py-2 text-[11px] font-black uppercase tracking-widest text-mekong-slate transition-colors hover:text-mekong-teal">
            <FileText size={16} className="transition-transform group-hover:scale-110" />
            Tài liệu hướng dẫn
          </button>
        </div>
      </div>
    </aside>
  );
};
