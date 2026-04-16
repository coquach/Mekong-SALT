import React from "react";
import {
  ArrowRight,
  Calendar,
  MapPin,
  Bookmark,
  Microscope,
  Mail,
  ShieldCheck,
  Search,
  Sparkles,
  ChevronRight,
  TrendingUp,
  Clock,
  Monitor, // <-- Thêm Monitor vào đây
  AlertTriangle,
  Users,
  ArrowUpRight, // <-- Thêm AlertTriangle vào đâ
} from "lucide-react";

// Import UI Components đã build ở các bước trước
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Badge } from "../components/ui/Badge";

/**
 * REFACTORED INFORMATION HUB
 * --------------------------
 * Section 1: Hero Alert with Blended Background Image
 * Section 2: Main Grid (8 cols News/Research | 4 cols Sidebar)
 */

export const InformationHub = () => {
  return (
    <div className="space-y-12 animate-in fade-in slide-in-from-bottom-4 duration-1000">
      {/* --- SECTION 1: HERO ALERT SECTION --- */}
      {/* --- HERO ALERT SECTION: COMPACT WIDGET & CLEARER BG --- */}
      <section className="relative overflow-hidden bg-mekong-navy rounded-[40px] px-8 lg:px-16 h-[560px] flex items-center text-white shadow-2xl border border-white/5">
        {/* 1. LỚP HÌNH ẢNH NỀN: Tăng độ rõ lên 40% (opacity-40) */}
        <div className="absolute inset-0 z-0 select-none">
          <img
            src="/src/assets/hero-bg.png"
            alt="Mekong Delta"
            className="w-full h-full object-cover opacity-40 mix-blend-luminosity grayscale-[0.3]"
          />
          {/* Gradient mờ nhẹ hơn để tôn ảnh nền nhưng vẫn đảm bảo đọc được chữ */}
          <div className="absolute inset-0 bg-gradient-to-r from-mekong-navy via-mekong-navy/70 to-transparent" />
        </div>

        <div className="relative z-10 grid grid-cols-12 gap-10 items-center w-full">
          {/* --- BÊN TRÁI: NỘI DUNG (Mở rộng không gian lên 8 cột) --- */}
          <div className="col-span-12 lg:col-span-8 flex flex-col justify-center space-y-8 min-w-0">
            <div className="flex items-center gap-5">
              {/* Badge Urgent Alert - Đã sửa lỗi blur, sắc nét và thẩm mỹ hơn */}
              <Badge
                variant="critical"
                className="bg-mekong-critical text-white border border-white/10 py-2 px-6 text-[12px] font-black uppercase tracking-[0.2em] shadow-[0_4px_12px_rgba(0,0,0,0.3)] ring-1 ring-white/5"
              >
                URGENT ALERT
              </Badge>
              <div className="flex items-center gap-3 text-[14px] font-black text-mekong-cyan uppercase tracking-widest drop-shadow-md">
                <div className="w-2.5 h-2.5 bg-mekong-mint rounded-full animate-pulse shadow-[0_0_10px_#1BAEA6]" />
                TIỀN RIVER MONITORING
              </div>
            </div>

            <div className="space-y-4">
              <h1 className="text-5xl lg:text-[5.2rem] font-black leading-[1] tracking-tighter drop-shadow-2xl">
                Upcoming Salt Peak: <br />
                <span className="text-mekong-cyan drop-shadow-[0_0_30px_rgba(117,231,254,0.2)]">
                  May 9, 2026
                </span>
              </h1>
              <p className="text-lg lg:text-xl text-slate-200 max-w-2xl leading-relaxed font-medium opacity-90 drop-shadow-md">
                Agent models predict a salinity surge of up to{" "}
                <span className="text-white font-bold underline decoration-mekong-cyan underline-offset-4">
                  4.2g/L
                </span>{" "}
                at the Mỹ Tho station. Local farmers are advised to seal sluice
                gates.
              </p>
            </div>

            <div className="flex flex-wrap gap-5 pt-2">
              <Button
                variant="cyan"
                className="px-10 h-14 text-[12px] font-black shadow-lg"
              >
                VIEW ACTION PLAN
              </Button>
              <Button
                variant="outline"
                className="px-10 h-14 text-[12px] font-black border-white/20 text-white hover:bg-white/5 backdrop-blur-sm"
              >
                DOWNLOAD REPORT
              </Button>
            </div>
          </div>

          {/* --- BÊN PHẢI: WIDGET (Hẹp lại còn 4 cột, thu nhỏ padding) --- */}
          <div className="col-span-12 lg:col-span-4 flex justify-end">
            {/* Khung nhỏ lại (max-w-[420px]) và padding gọn gàng (p-8 lg:p-10) */}
            <div className="bg-white/[0.05] backdrop-blur-3xl rounded-[32px] p-8 lg:p-10 border border-white/10 shadow-[0_25px_50px_-12px_rgba(0,0,0,0.5)] ring-1 ring-white/10 w-full max-w-[420px] transition-all duration-500 hover:bg-white/[0.08]">
              <div className="flex justify-between items-center mb-10">
                <p className="text-[11px] font-black uppercase tracking-[0.3em] text-slate-400">
                  CURRENT SALINITY
                </p>
                <div className="bg-mekong-critical/30 text-white px-3 py-1.5 rounded-lg flex items-center gap-1.5 text-[12px] font-black shadow-lg">
                  <TrendingUp size={14} strokeWidth={3} /> +12%
                </div>
              </div>

              {/* Số 2.8 khít khung hơn */}
              <div className="flex items-baseline gap-3 mb-10">
                <span className="text-8xl lg:text-[8.5rem] font-black tracking-tighter leading-none text-white drop-shadow-2xl">
                  2.8
                </span>
                <span className="text-2xl font-black text-slate-500 uppercase tracking-widest opacity-60">
                  g/L
                </span>
              </div>

              {/* Danh sách trạm gọn gàng */}
              <div className="space-y-4 pt-6 border-t border-white/10">
                <p className="text-[10px] font-black text-slate-500 uppercase tracking-[0.25em] mb-4">
                  LIVE RIVER NODE STATUS
                </p>
                {[
                  {
                    name: "Station #082 - Tiền Giang",
                    status: "OPTIMAL",
                    color: "text-mekong-mint",
                  },
                  {
                    name: "Station #045 - Mỹ Tho",
                    status: "CRITICAL",
                    color: "text-mekong-critical",
                  },
                  {
                    name: "Station #109 - Chợ Lách",
                    status: "MONITORING",
                    color: "text-mekong-cyan",
                  },
                ].map((node, i) => (
                  <div
                    key={i}
                    className="flex justify-between items-center py-1 group/item cursor-pointer"
                  >
                    <span className="text-[14px] font-bold text-slate-200 group-hover/item:text-white transition-colors">
                      {node.name}
                    </span>
                    <span
                      className={`text-[10px] font-black uppercase tracking-widest ${node.color}`}
                    >
                      {node.status}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* --- MAIN LAYOUT GRID: NEWS & SIDEBAR --- */}
      <div className="grid grid-cols-12 gap-10">
        {/* LEFT AREA: LATEST UPDATES & RESEARCH (8 Columns) */}
        <div className="col-span-12 lg:col-span-8 space-y-12">
          {/* --- LATEST UPDATES SECTION: COMPACT & CUSTOM IMAGES --- */}
          <section>
            {/* --- LATEST UPDATES HEADER WITH DECORATIVE LINE --- */}
            <div className="flex justify-between items-end mb-10">
              <div className="space-y-3">
                {" "}
                {/* Bọc tiêu đề và đường gạch vào 1 khối để căn chỉnh */}
                <h2 className="text-3xl font-black text-mekong-navy tracking-tighter uppercase leading-none">
                  Latest Updates
                </h2>
                {/* Đường gạch Teal đặc trưng - Giống hệt bên Upcoming Events */}
                <div className="w-12 h-1.5 bg-mekong-teal rounded-full shadow-sm" />
              </div>

              <button className="flex items-center gap-2 text-[11px] font-black text-mekong-teal uppercase tracking-[0.2em] hover:translate-x-1 transition-all">
                View All News <ArrowRight size={14} />
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 lg:gap-10">
              {/* CARD 1: DIRECTIVES */}
              <Card
                padding="none"
                className="rounded-[40px] overflow-hidden border-none bg-white shadow-soft group cursor-pointer"
              >
                <div className="h-60 overflow-hidden relative">
                  <img
                    src="/src/assets/new-1.png" // <-- Thay bằng tên file ảnh thứ nhất của bạn
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700"
                    alt="Irrigation Schedule"
                  />
                  <div className="absolute top-6 left-6 flex gap-2">
                    <span className="bg-white px-3 py-1 rounded-lg text-[10px] font-black text-mekong-navy uppercase tracking-widest shadow-sm">
                      Directives
                    </span>
                    <span className="bg-red-500/80 backdrop-blur-sm px-3 py-1 rounded-lg text-[10px] font-black text-white uppercase tracking-widest shadow-sm">
                      Local
                    </span>
                  </div>
                </div>

                <CardContent className="p-7 lg:p-8 space-y-3">
                  {" "}
                  {/* Giảm padding từ 10 xuống 7/8 */}
                  <p className="text-[10px] font-black text-mekong-teal uppercase tracking-[0.2em]">
                    GOVERNMENT • 2 HOURS AGO
                  </p>
                  <h3 className="text-[20px] font-black text-mekong-navy leading-[1.2] tracking-tight group-hover:text-mekong-teal transition-colors uppercase">
                    New Irrigation Schedule for Bến Tre Province Released
                  </h3>
                  <p className="text-[14px] text-slate-500 font-medium leading-relaxed line-clamp-2">
                    Official decree from the Ministry of Agriculture outlines
                    specific hours for gate operation during peak tide cycles...
                  </p>
                  {/* Card Footer: Đã thu hẹp khoảng cách */}
                  <div className="flex justify-between items-center pt-4 mt-4 border-t border-slate-50">
                    <div className="w-9 h-9 rounded-full border-2 border-white shadow-md overflow-hidden bg-slate-100">
                      <img
                        src="https://i.pravatar.cc/150?u=gov"
                        alt="Author"
                        className="w-full h-full object-cover"
                      />
                    </div>
                    {/* Icon Bookmark - Đã fix lỗi mờ, sắc nét hơn */}
                    <button className="p-2 -mr-2 rounded-full hover:bg-slate-50 transition-colors group">
                      <Bookmark
                        size={20}
                        strokeWidth={2.5} // Tăng độ dày nét vẽ để icon rõ hơn
                        className="text-slate-400 group-hover:text-mekong-navy transition-colors"
                      />
                    </button>
                  </div>
                </CardContent>
              </Card>

              {/* CARD 2: INTELLIGENCE */}
              <Card
                padding="none"
                className="rounded-[40px] overflow-hidden border-none bg-white shadow-soft group cursor-pointer"
              >
                <div className="h-60 overflow-hidden relative">
                  <img
                    src="/src/assets/new-2.png" // <-- Thay bằng tên file ảnh thứ hai của bạn
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700"
                    alt="AI Sluice Control"
                  />
                  <div className="absolute top-5 left-5">
                    <Badge className="bg-white/95 text-mekong-navy font-black border-none shadow-sm">
                      Intelligence
                    </Badge>
                  </div>
                </div>

                <CardContent className="p-7 lg:p-8 space-y-3">
                  <p className="text-[10px] font-black text-mekong-teal uppercase tracking-[0.2em]">
                    SALT AGENT • 5 HOURS AGO
                  </p>
                  <h3 className="text-[20px] font-black text-mekong-navy leading-[1.2] tracking-tight group-hover:text-mekong-teal transition-colors uppercase">
                    Autonomous Sluice Control System Goes Live in Sóc Trăng
                  </h3>
                  <p className="text-[14px] text-slate-500 font-medium leading-relaxed line-clamp-2">
                    The new AI-driven infrastructure automatically closes gates
                    based on live salinity sensor readings...
                  </p>

                  {/* Card Footer: Đã thu hẹp khoảng cách */}
                  <div className="flex justify-between items-center pt-4 mt-4 border-t border-slate-50">
                    <div className="flex items-center gap-2">
                      <Sparkles size={14} className="text-mekong-teal" />
                      <span className="text-[10px] font-black text-mekong-teal uppercase tracking-widest">
                        AI Generated Insight
                      </span>
                    </div>
                    {/* Icon Bookmark - Đã fix lỗi mờ, sắc nét hơn */}
                    <button className="p-2 -mr-2 rounded-full hover:bg-slate-50 transition-colors group">
                      <Bookmark
                        size={20}
                        strokeWidth={2.5} // Tăng độ dày nét vẽ để icon rõ hơn
                        className="text-slate-400 group-hover:text-mekong-navy transition-colors"
                      />
                    </button>
                  </div>
                </CardContent>
              </Card>
            </div>
          </section>

          {/* SCIENTIFIC INSIGHTS: Dark Section */}
          {/* --- SECTION: SCIENTIFIC INSIGHTS (HIGH-END DARK VARIANT) --- */}
          {/* --- SECTION: SCIENTIFIC INSIGHTS (ENHANCED TYPOGRAPHY) --- */}
          <section className="relative overflow-hidden bg-mekong-navy rounded-[40px] p-10 lg:p-14 text-white shadow-2xl border border-white/5">
            {/* Ánh sáng nền (Giữ nguyên) */}
            <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-mekong-cyan/5 rounded-full blur-[120px] pointer-events-none" />

            {/* Header Section */}
            <div className="relative z-10 flex items-center gap-6 mb-20">
              {" "}
              {/* Tăng margin bottom lên 20 */}
              <div className="p-4 bg-white/5 rounded-2xl border border-white/10 text-mekong-cyan shadow-xl">
                <Microscope size={40} strokeWidth={2.5} />
              </div>
              <div className="space-y-2">
                <h2 className="text-4xl lg:text-5xl font-black uppercase tracking-tighter leading-none">
                  Scientific Insights
                </h2>
                <p className="text-[12px] font-black text-slate-400 uppercase tracking-[0.3em] opacity-80">
                  Long-form research & delta hydrologic models
                </p>
              </div>
            </div>

            {/* List of Research Items */}
            <div className="relative z-10 space-y-16">
              {" "}
              {/* Tăng khoảng cách giữa các bài viết lên 16 */}
              {[
                {
                  tag: "Research Paper",
                  time: "12 MIN READ",
                  title:
                    "Modeling the Impact of Upstream Damming on Delta Salinity Dynamics",
                  desc: "A comprehensive study utilizing SALT's proprietary hydrologic agents to forecast long-term changes in riverbed morphology and saline front movement.",
                  img: "/src/assets/research-1.jpg",
                },
                {
                  tag: "Delta Model V2.4",
                  time: "8 MIN READ",
                  title:
                    "Adaptive Agriculture: Transitioning to Salt-Tolerant Rice Varieties",
                  desc: "How farmers in Tiền Giang are successfully piloting ST25 rice hybrids in brackish water environments using real-time AI irrigation schedules.",
                  img: "/src/assets/research-2.jpg",
                },
              ].map((item, idx) => (
                <div
                  key={idx}
                  className="grid grid-cols-12 gap-12 group cursor-pointer border-b border-white/5 pb-16 last:border-none last:pb-0"
                >
                  {/* Khối Hình ảnh (Mở rộng chiều cao một chút để cân bằng với chữ to) */}
                  <div className="col-span-12 md:col-span-4 h-60 rounded-[32px] overflow-hidden shadow-2xl border border-white/10 ring-1 ring-white/5 relative">
                    <img
                      src={item.img}
                      className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-700"
                      alt="Research"
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-mekong-navy/70 to-transparent" />
                  </div>

                  {/* Khối Nội dung - PHÓNG TO CHỮ */}
                  <div className="col-span-12 md:col-span-8 flex flex-col justify-center space-y-6">
                    <div className="flex items-center gap-6">
                      {/* Nhãn Tag to hơn (13px) */}
                      <span className="text-[13px] font-black text-mekong-cyan uppercase tracking-[0.25em]">
                        {item.tag}
                      </span>
                      {/* Thời gian đọc to hơn (12px) */}
                      <div className="flex items-center gap-2 text-[12px] font-black text-slate-500 uppercase tracking-widest">
                        <Clock size={14} strokeWidth={3} />
                        <span>{item.time}</span>
                      </div>
                    </div>

                    {/* TIÊU ĐỀ PHÓNG TO (32px) */}
                    <h3 className="text-[32px] lg:text-[34px] font-black leading-[1.15] tracking-tight group-hover:text-mekong-cyan transition-colors duration-300">
                      {item.title}
                    </h3>

                    {/* MÔ TẢ PHÓNG TO (17px) */}
                    <p className="text-[17px] text-slate-400 font-medium leading-relaxed opacity-90 max-w-4xl line-clamp-2 group-hover:opacity-100 transition-opacity">
                      {item.desc}
                    </p>

                    <div className="pt-2 flex items-center gap-3 text-mekong-cyan text-[13px] font-black uppercase tracking-widest opacity-0 -translate-x-4 group-hover:opacity-100 group-hover:translate-x-0 transition-all duration-500">
                      Read Full Analysis <ArrowUpRight size={16} />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </section>
        </div>

        {/* RIGHT AREA: EVENTS & STAY INFORMED (4 Columns) */}
        <div className="col-span-12 lg:col-span-4 space-y-8">
          {/* --- UPCOMING EVENTS: PROFESSIONAL REFINEMENT --- */}
          {/* --- UPCOMING EVENTS: PROFESSIONAL STRIPE VERSION --- */}
          <aside className="space-y-8">
            {/* Section Header */}
            <div className="space-y-3 mb-8 px-2">
              <h2 className="text-xl font-black text-mekong-navy uppercase tracking-[0.15em]">
                Upcoming Events
              </h2>
              <div className="w-12 h-1.5 bg-mekong-teal rounded-full shadow-sm shadow-mekong-teal/20" />
            </div>

            {/* Event List */}
            <div className="space-y-5">
              {[
                {
                  date: "MARCH 30",
                  title: "Farmer Training Workshop",
                  desc: "Salinity mitigation techniques for small-scale fruit orchards.",
                  loc: "Mỹ Tho Community Center",
                  icon: Calendar,
                  color: "bg-mekong-teal", // Màu thanh dọc
                  textColor: "text-mekong-teal",
                },
                {
                  date: "APRIL 05",
                  title: "Stakeholder Summit 2024",
                  desc: "Annual review of Mekong-SALT hydrologic accuracy.",
                  loc: "Virtual / Hybrid (HCM City)",
                  icon: Users,
                  color: "bg-mekong-cyan",
                  textColor: "text-mekong-cyan",
                },
                {
                  date: "APRIL 12",
                  title: "Emergency Drill: Peak Flow",
                  desc: "Testing rapid response protocols for sluice gate coordination.",
                  loc: "Bến Tre Operations Hub",
                  icon: AlertTriangle,
                  color: "bg-mekong-critical",
                  textColor: "text-mekong-critical",
                },
              ].map((event, idx) => (
                <Card
                  key={idx}
                  padding="none"
                  className="rounded-[32px] border border-slate-100 bg-white shadow-soft hover:shadow-[0_20px_40px_-12px_rgba(0,0,0,0.08)] transition-all duration-500 group cursor-pointer overflow-hidden relative"
                >
                  {/* THANH MÀU DỌC - CHẠY KHÍT CARD */}
                  <div
                    className={`absolute top-0 left-0 w-2 h-full ${event.color} transition-all duration-500 group-hover:w-3`}
                  />

                  {/* NỘI DUNG CARD - Có padding-left (pl-8) để né thanh màu */}
                  <div className="p-7 pl-9 space-y-4">
                    <div className="flex justify-between items-center">
                      <span className="bg-slate-50 text-slate-500 px-3 py-1 rounded-xl text-[10px] font-black tracking-widest border border-slate-100">
                        {event.date}
                      </span>
                      <event.icon
                        size={18}
                        className={`${event.textColor} opacity-60 group-hover:opacity-100 transition-opacity`}
                      />
                    </div>

                    <div className="space-y-1.5">
                      <h4 className="text-[17px] font-black text-mekong-navy leading-tight group-hover:text-mekong-teal transition-colors">
                        {event.title}
                      </h4>
                      <p className="text-[13px] text-slate-500 font-medium leading-relaxed opacity-85">
                        {event.desc}
                      </p>
                    </div>

                    <div
                      className={`flex items-center gap-2 pt-1 text-[10px] font-black uppercase tracking-[0.2em] ${event.textColor}`}
                    >
                      <MapPin size={14} strokeWidth={2.5} />
                      <span>{event.loc}</span>
                    </div>
                  </div>
                </Card>
              ))}
            </div>

            {/* Button chuyên nghiệp */}
            <button className="w-full py-4 bg-slate-50/50 border border-slate-200 rounded-2xl text-[12px] font-black text-mekong-navy uppercase tracking-[0.25em] hover:bg-white hover:shadow-md hover:border-mekong-teal/30 transition-all active:scale-[0.98]">
              View Full Calendar
            </button>
          </aside>

          {/* Newsletter Card: Light Cyan BG */}
          <Card
            variant="white"
            className="bg-[#ECFEFF] border-none shadow-sm relative overflow-hidden p-10"
          >
            <div className="absolute -right-10 -bottom-10 w-48 h-48 bg-mekong-cyan/30 rounded-full blur-3xl" />
            <div className="relative z-10 space-y-4">
              <h3 className="text-sm font-black text-mekong-navy uppercase tracking-[0.2em]">
                Stay Informed
              </h3>
              <p className="text-xs text-mekong-slate font-medium leading-relaxed">
                Receive weekly salinity forecasts and critical river alerts
                directly in your inbox.
              </p>
              <div className="space-y-3 pt-2">
                <input
                  type="email"
                  placeholder="Email address"
                  className="w-full bg-white border-none rounded-xl px-4 py-3.5 text-xs font-bold text-mekong-navy focus:ring-2 ring-mekong-teal/20 shadow-sm"
                />
                <Button
                  variant="navy"
                  className="w-full h-12 shadow-xl shadow-mekong-navy/10"
                >
                  Subscribe
                </Button>
              </div>
            </div>
          </Card>

          {/* --- SIDEBAR FOOTER: COMPACT VERSION --- */}
          <div className="mt-6 pt-6 border-t border-slate-200 space-y-8 animate-in fade-in duration-500">
            {/* 1. HAI CỘT LIÊN KẾT (Đã thu hẹp gap và margin) */}
            <div className="grid grid-cols-2 gap-6">
              {/* Cột Resources */}
              <div className="space-y-4">
                <p className="text-[12px] font-black text-mekong-navy uppercase tracking-[0.2em] border-b border-slate-100 pb-2">
                  RESOURCES
                </p>
                <ul className="space-y-2">
                  {["API Documentation", "Open Data", "Research Grants"].map(
                    (item) => (
                      <li
                        key={item}
                        className="text-[14px] font-bold text-slate-500 hover:text-mekong-teal hover:translate-x-1 transition-all cursor-pointer flex items-center gap-2 group"
                      >
                        <div className="w-1 h-1 rounded-full bg-slate-300 group-hover:bg-mekong-teal transition-colors" />
                        {item}
                      </li>
                    ),
                  )}
                </ul>
              </div>

              {/* Cột Connect */}
              <div className="space-y-4">
                <p className="text-[12px] font-black text-mekong-navy uppercase tracking-[0.2em] border-b border-slate-100 pb-2">
                  CONNECT
                </p>
                <ul className="space-y-2">
                  {["Ministry of Water", "Tech Support", "Partner Portal"].map(
                    (item) => (
                      <li
                        key={item}
                        className="text-[14px] font-bold text-slate-500 hover:text-mekong-teal hover:translate-x-1 transition-all cursor-pointer flex items-center gap-2 group"
                      >
                        <div className="w-1 h-1 rounded-full bg-slate-300 group-hover:bg-mekong-teal transition-colors" />
                        {item}
                      </li>
                    ),
                  )}
                </ul>
              </div>
            </div>

            {/* 2. THÔNG TIN DỰ ÁN (Branding Block - Thu nhỏ padding) */}
            <div className="space-y-3 px-4 py-5 bg-slate-50 rounded-2xl border border-slate-100 relative overflow-hidden group">
              <div className="absolute top-0 left-0 w-1 h-full bg-mekong-teal opacity-60" />

              <p className="text-[12px] font-black text-mekong-navy uppercase tracking-[0.2em]">
                MEKONG-SALT PROJECT
              </p>
              <p className="text-[13px] text-slate-500 font-semibold leading-relaxed opacity-90">
                A collaborative platform for hydrologic intelligence, bringing
                together live sensor data and agentic AI to protect the Mekong
                Delta's agricultural future.
              </p>

              <div className="pt-1">
                <span className="text-[9px] font-black bg-white px-2 py-0.5 rounded border border-slate-200 text-slate-400 uppercase tracking-widest inline-block">
                  System v4.2.1
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default InformationHub;
