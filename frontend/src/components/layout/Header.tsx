import { useEffect, useMemo, useRef, useState } from "react";
import {
  Bell,
  Check,
  ChevronDown,
  ChevronRight,
  MapPin,
  Search,
  Sparkles,
} from "lucide-react";
import { useLocation, useNavigate } from "react-router-dom";

import avatarImage from "../../assets/hien.jpg";
import { apiGet } from "../../lib/api/http";
import { buildBreadcrumb, getRouteMeta } from "../../lib/navigation";
import { getDashboardSummary } from "../../lib/api/dashboard";
import { Badge } from "../ui/Badge";
import { RealtimeBadge } from "../ui/RealtimeBadge";

interface NotificationRead {
  id: string;
  created_at: string;
  sent_at: string | null;
  recipient: string;
  subject: string | null;
  message: string;
  status: string;
}

interface NotificationCollection {
  items: NotificationRead[];
  count: number;
}

const regions = [
  "Tiền Giang",
  "Bến Tre",
  "Sóc Trăng",
  "Long An",
  "Trà Vinh",
  "Tất cả khu vực",
];

export const Header = () => {
  const navigate = useNavigate();
  const { pathname } = useLocation();
  const [isRegionMenuOpen, setIsRegionMenuOpen] = useState(false);
  const [isNotificationMenuOpen, setIsNotificationMenuOpen] = useState(false);
  const [selectedRegion, setSelectedRegion] = useState("Tiền Giang");
  const [notificationCount, setNotificationCount] = useState(0);
  const [notifications, setNotifications] = useState<NotificationRead[]>([]);
  const notificationMenuRef = useRef<HTMLDivElement | null>(null);

  const routeMeta = getRouteMeta(pathname);
  const breadcrumb = useMemo(() => buildBreadcrumb(pathname), [pathname]);

  useEffect(() => {
    let mounted = true;
    const controller = new AbortController();

    const loadNotifications = async () => {
      try {
        const [summary, notificationCollection] = await Promise.all([
          getDashboardSummary(controller.signal),
          apiGet<NotificationCollection>("/notifications", {
            query: { limit: 5 },
            signal: controller.signal,
          }),
        ]);
        if (!mounted) {
          return;
        }
        setNotificationCount(summary.active_notifications ?? notificationCollection.count ?? 0);
        setNotifications(notificationCollection.items);
      } catch {
        if (mounted) {
          setNotificationCount(0);
          setNotifications([]);
        }
      }
    };

    void loadNotifications();
    return () => {
      mounted = false;
      controller.abort();
    };
  }, []);

  useEffect(() => {
    const handlePointerDown = (event: MouseEvent) => {
      if (
        notificationMenuRef.current &&
        event.target instanceof Node &&
        !notificationMenuRef.current.contains(event.target)
      ) {
        setIsNotificationMenuOpen(false);
      }
    };

    window.addEventListener("mousedown", handlePointerDown);
    return () => window.removeEventListener("mousedown", handlePointerDown);
  }, []);

  const handleRegionSelect = (region: string) => {
    setSelectedRegion(region);
    setIsRegionMenuOpen(false);
    navigate("/map");
  };

  return (
    <header className="sticky top-0 z-40 border-b border-slate-200 bg-white/85 backdrop-blur-xl">
      <div className="grid grid-cols-1 gap-4 px-6 py-4 xl:grid-cols-[minmax(0,1fr)_auto] xl:items-center xl:px-10">
        <div className="min-w-0 space-y-3">
          <nav
            aria-label="Điều hướng nhanh"
            className="flex flex-wrap items-center gap-1 text-[10px] font-black uppercase tracking-[0.18em] text-slate-400"
          >
            {breadcrumb.map((label, index) => (
              <span key={`${label}-${index}`} className="inline-flex items-center gap-1">
                {index > 0 ? <ChevronRight size={11} /> : null}
                {label}
              </span>
            ))}
          </nav>

          <div className="flex flex-wrap items-center gap-2">
            <h2 className="text-lg font-black tracking-tight text-mekong-navy lg:text-xl">
              {routeMeta.title}
            </h2>
            <RealtimeBadge mode={routeMeta.realtimeMode} className="text-[9px]" />
            <Badge variant="neutral" className="text-[9px]">
              {selectedRegion}
            </Badge>
          </div>

          <div className="relative max-w-xl">
            <Search size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="search"
              placeholder="Tìm trạm, sự cố, kế hoạch, hành động..."
              className="w-full rounded-xl border border-slate-200 bg-slate-50 py-2.5 pl-11 pr-30 text-sm font-semibold text-mekong-navy outline-none transition-all focus:border-mekong-teal/40 focus:bg-white focus:ring-4 ring-mekong-teal/10"
            />
            <button className="absolute right-1.5 top-1/2 -translate-y-1/2 rounded-lg bg-linear-to-r from-mekong-navy to-mekong-teal px-3 py-1.5 text-[10px] font-black uppercase tracking-[0.14em] text-white shadow-md transition-all hover:brightness-110">
              <span className="inline-flex items-center gap-1">
                <Sparkles size={11} className="text-mekong-cyan" />
                Tìm nhanh
              </span>
            </button>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3 xl:justify-end">
          <div className="relative" ref={notificationMenuRef}>
            <button
              type="button"
              onClick={() => setIsNotificationMenuOpen((value) => !value)}
              className="relative rounded-xl border border-slate-200 bg-white p-2.5 text-slate-500 transition-colors hover:border-red-200 hover:bg-red-50 hover:text-mekong-critical"
              aria-label="Mở thông báo"
            >
              <Bell size={18} />
              {notificationCount > 0 ? (
                <span className="absolute right-1.5 top-1.5 min-w-4 rounded-full bg-mekong-critical px-1 text-[9px] font-black leading-4 text-white">
                  {notificationCount > 9 ? "9+" : notificationCount}
                </span>
              ) : null}
            </button>

            {isNotificationMenuOpen ? (
              <div className="absolute right-0 z-30 mt-2 w-96 rounded-2xl border border-slate-200 bg-white p-3 shadow-2xl">
                <div className="flex items-center justify-between gap-3 border-b border-slate-100 pb-2">
                  <div>
                    <p className="text-[10px] font-black uppercase tracking-[0.16em] text-slate-400">
                      Thông báo
                    </p>
                    <p className="mt-1 text-sm font-black text-mekong-navy">
                      {notificationCount} mục chưa xử lý
                    </p>
                  </div>
                  <Badge variant="neutral" className="text-[9px]">
                    Live
                  </Badge>
                </div>

                <div className="max-h-80 space-y-2 overflow-y-auto py-3 custom-scrollbar">
                  {notifications.length > 0 ? (
                    notifications.map((notification) => (
                      <button
                        key={notification.id}
                        type="button"
                        className="w-full rounded-xl border border-slate-100 bg-slate-50 px-3 py-2.5 text-left transition-colors hover:border-mekong-teal/20 hover:bg-white"
                      >
                        <div className="flex items-start justify-between gap-3">
                          <div className="min-w-0">
                            <p className="text-[11px] font-black uppercase tracking-[0.14em] text-mekong-navy line-clamp-1">
                              {notification.subject ?? "Thông báo vận hành"}
                            </p>
                            <p className="mt-1 text-[12px] font-medium leading-relaxed text-slate-600 line-clamp-2">
                              {notification.message}
                            </p>
                          </div>
                          <Badge variant={notification.status === "sent" ? "optimal" : "warning"} className="text-[8px]">
                            {notification.status}
                          </Badge>
                        </div>
                        <div className="mt-2 flex items-center justify-between gap-2 text-[10px] font-bold uppercase tracking-[0.14em] text-slate-400">
                          <span>{notification.recipient}</span>
                          <span>{notification.sent_at ?? notification.created_at}</span>
                        </div>
                      </button>
                    ))
                  ) : (
                    <p className="py-6 text-center text-sm font-semibold text-slate-500">
                      Không có thông báo mới.
                    </p>
                  )}
                </div>

                <button
                  type="button"
                  className="w-full rounded-xl bg-mekong-navy px-3 py-2 text-[10px] font-black uppercase tracking-[0.14em] text-white transition-colors hover:bg-mekong-teal"
                  onClick={() => setIsNotificationMenuOpen(false)}
                >
                  Đóng
                </button>
              </div>
            ) : null}
          </div>

          <div className="relative">
            <button
              type="button"
              onClick={() => setIsRegionMenuOpen((value) => !value)}
              className="inline-flex items-center gap-3 rounded-xl bg-linear-to-r from-mekong-teal to-[#0b7e8f] px-4 py-2.5 text-xs font-black uppercase tracking-[0.14em] text-white shadow-lg shadow-mekong-teal/25 transition-all hover:brightness-110"
              aria-haspopup="menu"
            >
              <MapPin size={15} />
              <span>{selectedRegion}</span>
              <ChevronDown
                size={14}
                className={`transition-transform ${isRegionMenuOpen ? "rotate-180" : ""}`}
              />
            </button>

            {isRegionMenuOpen ? (
              <div className="absolute right-0 z-20 mt-2 w-60 rounded-2xl border border-slate-200 bg-white p-2 shadow-2xl">
                {regions.map((region) => (
                  <button
                    key={region}
                    onClick={() => handleRegionSelect(region)}
                    className={`flex w-full items-center justify-between rounded-xl px-3 py-2 text-left text-xs font-black uppercase tracking-[0.14em] transition-colors ${
                      selectedRegion === region
                        ? "bg-mekong-navy text-white"
                        : "text-mekong-navy hover:bg-slate-50"
                    }`}
                  >
                    {region}
                    {selectedRegion === region ? <Check size={14} /> : null}
                  </button>
                ))}
              </div>
            ) : null}
          </div>

          <div className="inline-flex items-center gap-3 rounded-xl border border-slate-200 bg-white px-3 py-2 shadow-sm">
            <img
              src={avatarImage}
              alt="Ảnh đại diện người vận hành"
              className="h-9 w-9 rounded-lg object-cover ring-2 ring-slate-100"
            />
            <div className="hidden text-right xl:block">
              <p className="text-[11px] font-black uppercase tracking-[0.12em] text-mekong-navy">
                Trần Gia Hiển
              </p>
              <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-mekong-teal">
                Quản trị trưởng
              </p>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};
