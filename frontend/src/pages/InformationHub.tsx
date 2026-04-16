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
  Monitor,
  AlertTriangle,
  Users,
  ArrowUpRight,
} from "lucide-react";

// Import các UI Components
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
 * TRUNG TÂM THÔNG TIN MEKONG-SALT
 * --------------------------
 * Phần 1: Cảnh báo khẩn cấp (Hero)
 * Phần 2: Tin tức & Nghiên cứu khoa học (8 cột)
 * Phần 3: Sự kiện & Đăng ký bản tin (4 cột)
 */

export const InformationHub = () => {
  return (
    <div className="space-y-12 animate-in fade-in slide-in-from-bottom-4 duration-1000">
      {/* --- PHẦN 1: SECTION CẢNH BÁO ANH HÙNG (HERO) --- */}
      <section className="relative overflow-hidden bg-mekong-navy rounded-[40px] px-8 lg:px-16 h-[560px] flex items-center text-white shadow-2xl border border-white/5">
        {/* Lớp hình ảnh nền */}
        <div className="absolute inset-0 z-0 select-none">
          <img
            src="/src/assets/hero-bg.png"
            alt="Mekong Delta"
            className="w-full h-full object-cover opacity-40 mix-blend-luminosity grayscale-[0.3]"
          />
          <div className="absolute inset-0 bg-gradient-to-r from-mekong-navy via-mekong-navy/70 to-transparent" />
        </div>

        <div className="relative z-10 grid grid-cols-12 gap-10 items-center w-full">
          {/* BÊN TRÁI: NỘI DUNG CHÍNH */}
          <div className="col-span-12 lg:col-span-8 flex flex-col justify-center space-y-8 min-w-0">
            <div className="flex items-center gap-5">
              <Badge
                variant="critical"
                className="bg-mekong-critical text-white border border-white/10 py-2 px-6 text-[12px] font-black uppercase tracking-[0.2em] shadow-[0_4px_12px_rgba(0,0,0,0.3)]"
              >
                CẢNH BÁO KHẨN
              </Badge>
              <div className="flex items-center gap-3 text-[14px] font-black text-mekong-cyan uppercase tracking-widest drop-shadow-md">
                <div className="w-2.5 h-2.5 bg-mekong-mint rounded-full animate-pulse shadow-[0_0_10px_#1BAEA6]" />
                GIÁM SÁT LƯU VỰC SÔNG TIỀN
              </div>
            </div>

            <div className="space-y-4">
              <h1 className="text-5xl lg:text-[5.2rem] font-black leading-[1] tracking-tighter drop-shadow-2xl">
                Dự báo Đỉnh mặn: <br />
                <span className="text-mekong-cyan drop-shadow-[0_0_30px_rgba(117,231,254,0.2)]">
                  Ngày 09 tháng 05, 2026
                </span>
              </h1>
              <p className="text-lg lg:text-xl text-slate-200 max-w-2xl leading-relaxed font-medium opacity-90 drop-shadow-md">
                Mô hình AI dự báo độ mặn sẽ tăng mạnh lên đến{" "}
                <span className="text-white font-bold underline decoration-mekong-cyan underline-offset-4">
                  4.2g/L
                </span>{" "}
                tại trạm Mỹ Tho. Khuyến nghị nông dân địa phương đóng các cống
                ngăn mặn.
              </p>
            </div>

            <div className="flex flex-wrap gap-5 pt-2">
              <Button
                variant="cyan"
                className="px-10 h-14 text-[12px] font-black shadow-lg"
              >
                XEM KẾ HOẠCH HÀNH ĐỘNG
              </Button>
              <Button
                variant="outline"
                className="px-10 h-14 text-[12px] font-black border-white/20 text-white hover:bg-white/5 backdrop-blur-sm"
              >
                TẢI BÁO CÁO CHI TIẾT
              </Button>
            </div>
          </div>

          {/* BÊN PHẢI: WIDGET CHỈ SỐ LIVE */}
          <div className="col-span-12 lg:col-span-4 flex justify-end">
            <div className="bg-white/[0.05] backdrop-blur-3xl rounded-[32px] p-8 lg:p-10 border border-white/10 shadow-[0_25px_50px_-12px_rgba(0,0,0,0.5)] ring-1 ring-white/10 w-full max-w-[420px] transition-all duration-500 hover:bg-white/[0.08]">
              <div className="flex justify-between items-center mb-10">
                <p className="text-[11px] font-black uppercase tracking-[0.3em] text-slate-400">
                  ĐỘ MẶN HIỆN TẠI
                </p>
                <div className="bg-mekong-critical/30 text-white px-3 py-1.5 rounded-lg flex items-center gap-1.5 text-[12px] font-black shadow-lg">
                  <TrendingUp size={14} strokeWidth={3} /> +12%
                </div>
              </div>

              <div className="flex items-baseline gap-3 mb-10">
                <span className="text-8xl lg:text-[8.5rem] font-black tracking-tighter leading-none text-white drop-shadow-2xl">
                  2.8
                </span>
                <span className="text-2xl font-black text-slate-500 uppercase tracking-widest opacity-60">
                  g/L
                </span>
              </div>

              <div className="space-y-4 pt-6 border-t border-white/10">
                <p className="text-[10px] font-black text-slate-500 uppercase tracking-[0.25em] mb-4">
                  TRẠNG THÁI CÁC TRẠM QUAN TRẮC
                </p>
                {[
                  {
                    name: "Trạm #082 - Tiền Giang",
                    status: "TỐI ƯU",
                    color: "text-mekong-mint",
                  },
                  {
                    name: "Trạm #045 - Mỹ Tho",
                    status: "NGUY CẤP",
                    color: "text-mekong-critical",
                  },
                  {
                    name: "Trạm #109 - Chợ Lách",
                    status: "THEO DÕI",
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

      {/* --- BỐ CỤC CHÍNH: TIN TỨC & THANH BÊN --- */}
      <div className="grid grid-cols-12 gap-10">
        {/* KHU VỰC BÊN TRÁI: CẬP NHẬT MỚI NHẤT & NGHIÊN CỨU (8 Cột) */}
        <div className="col-span-12 lg:col-span-8 space-y-12">
          <section>
            <div className="flex justify-between items-end mb-10">
              <div className="space-y-3">
                <h2 className="text-3xl font-black text-mekong-navy tracking-tighter uppercase leading-none">
                  Cập Nhật Mới Nhất
                </h2>
                <div className="w-12 h-1.5 bg-mekong-teal rounded-full shadow-sm" />
              </div>

              <button className="flex items-center gap-2 text-[11px] font-black text-mekong-teal uppercase tracking-[0.2em] hover:translate-x-1 transition-all">
                Xem tất cả tin tức <ArrowRight size={14} />
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 lg:gap-10">
              {/* TIN TỨC 1: CHỈ THỊ */}
              <Card
                padding="none"
                className="rounded-[40px] overflow-hidden border-none bg-white shadow-soft group cursor-pointer"
              >
                <div className="h-60 overflow-hidden relative">
                  <img
                    src="/src/assets/new-1.png"
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700"
                    alt="Irrigation Schedule"
                  />
                  <div className="absolute top-6 left-6 flex gap-2">
                    <span className="bg-white px-3 py-1 rounded-lg text-[10px] font-black text-mekong-navy uppercase tracking-widest shadow-sm">
                      Chỉ thị
                    </span>
                    <span className="bg-red-500/80 backdrop-blur-sm px-3 py-1 rounded-lg text-[10px] font-black text-white uppercase tracking-widest shadow-sm">
                      Địa phương
                    </span>
                  </div>
                </div>

                <CardContent className="p-7 lg:p-8 space-y-3">
                  <p className="text-[10px] font-black text-mekong-teal uppercase tracking-[0.2em]">
                    CHÍNH QUYỀN • 2 GIỜ TRƯỚC
                  </p>
                  <h3 className="text-[20px] font-black text-mekong-navy leading-[1.2] tracking-tight group-hover:text-mekong-teal transition-colors uppercase">
                    Ban hành lịch điều tiết nước mới cho tỉnh Bến Tre
                  </h3>
                  <p className="text-[14px] text-slate-500 font-medium leading-relaxed line-clamp-2">
                    Nghị định chính thức từ Bộ Nông nghiệp quy định khung giờ
                    vận hành cống trong các chu kỳ triều cường cao điểm...
                  </p>
                  <div className="flex justify-between items-center pt-4 mt-4 border-t border-slate-50">
                    <div className="w-9 h-9 rounded-full border-2 border-white shadow-md overflow-hidden bg-slate-100">
                      <img
                        src="https://i.pravatar.cc/150?u=gov"
                        alt="Author"
                        className="w-full h-full object-cover"
                      />
                    </div>
                    <button className="p-2 -mr-2 rounded-full hover:bg-slate-50 transition-colors group">
                      <Bookmark
                        size={20}
                        strokeWidth={2.5}
                        className="text-slate-400 group-hover:text-mekong-navy transition-colors"
                      />
                    </button>
                  </div>
                </CardContent>
              </Card>

              {/* TIN TỨC 2: CÔNG NGHỆ AI */}
              <Card
                padding="none"
                className="rounded-[40px] overflow-hidden border-none bg-white shadow-soft group cursor-pointer"
              >
                <div className="h-60 overflow-hidden relative">
                  <img
                    src="/src/assets/new-2.png"
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700"
                    alt="AI Sluice Control"
                  />
                  <div className="absolute top-5 left-5">
                    <Badge className="bg-white/95 text-mekong-navy font-black border-none shadow-sm">
                      Trí tuệ nhân tạo
                    </Badge>
                  </div>
                </div>

                <CardContent className="p-7 lg:p-8 space-y-3">
                  <p className="text-[10px] font-black text-mekong-teal uppercase tracking-[0.2em]">
                    SALT AGENT • 5 GIỜ TRƯỚC
                  </p>
                  <h3 className="text-[20px] font-black text-mekong-navy leading-[1.2] tracking-tight group-hover:text-mekong-teal transition-colors uppercase">
                    Vận hành hệ thống cống tự động hóa tại Sóc Trăng
                  </h3>
                  <p className="text-[14px] text-slate-500 font-medium leading-relaxed line-clamp-2">
                    Cơ sở hạ tầng mới điều khiển bởi AI sẽ tự động đóng mở cống
                    dựa trên dữ liệu cảm biến độ mặn thời gian thực...
                  </p>

                  <div className="flex justify-between items-center pt-4 mt-4 border-t border-slate-50">
                    <div className="flex items-center gap-2">
                      <Sparkles size={14} className="text-mekong-teal" />
                      <span className="text-[10px] font-black text-mekong-teal uppercase tracking-widest">
                        Phân tích từ AI
                      </span>
                    </div>
                    <button className="p-2 -mr-2 rounded-full hover:bg-slate-50 transition-colors group">
                      <Bookmark
                        size={20}
                        strokeWidth={2.5}
                        className="text-slate-400 group-hover:text-mekong-navy transition-colors"
                      />
                    </button>
                  </div>
                </CardContent>
              </Card>
            </div>
          </section>

          {/* SECTION: NGHIÊN CỨU KHOA HỌC (DARK VARIANT) */}
          <section className="relative overflow-hidden bg-mekong-navy rounded-[40px] p-10 lg:p-14 text-white shadow-2xl border border-white/5">
            <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-mekong-cyan/5 rounded-full blur-[120px] pointer-events-none" />

            <div className="relative z-10 flex items-center gap-6 mb-20">
              <div className="p-4 bg-white/5 rounded-2xl border border-white/10 text-mekong-cyan shadow-xl">
                <Microscope size={40} strokeWidth={2.5} />
              </div>
              <div className="space-y-2">
                <h2 className="text-4xl lg:text-5xl font-black uppercase tracking-tighter leading-none">
                  Góc Nhìn Khoa Học
                </h2>
                <p className="text-[12px] font-black text-slate-400 uppercase tracking-[0.3em] opacity-80">
                  Nghiên cứu chuyên sâu & Mô hình thủy văn Delta
                </p>
              </div>
            </div>

            <div className="relative z-10 space-y-16">
              {[
                {
                  tag: "Báo cáo nghiên cứu",
                  time: "12 PHÚT ĐỌC",
                  title:
                    "Mô phỏng tác động của các đập thượng nguồn lên động lực mặn vùng cửa sông",
                  desc: "Một nghiên cứu toàn diện sử dụng các tác nhân thủy văn độc quyền của SALT để dự báo thay đổi dài hạn của hình thái lòng sông và sự di chuyển của ranh mặn.",
                  img: "/src/assets/research-1.jpg",
                },
                {
                  tag: "Mô hình Delta V2.4",
                  time: "8 PHÚT ĐỌC",
                  title:
                    "Nông nghiệp thích ứng: Chuyển đổi sang các giống lúa chịu mặn",
                  desc: "Cách nông dân Tiền Giang thí điểm thành công giống lúa lai ST25 trong môi trường nước lợ bằng lịch tưới tiêu AI thời gian thực.",
                  img: "/src/assets/research-2.jpg",
                },
              ].map((item, idx) => (
                <div
                  key={idx}
                  className="grid grid-cols-12 gap-12 group cursor-pointer border-b border-white/5 pb-16 last:border-none last:pb-0"
                >
                  <div className="col-span-12 md:col-span-4 h-60 rounded-[32px] overflow-hidden shadow-2xl border border-white/10 ring-1 ring-white/5 relative">
                    <img
                      src={item.img}
                      className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-700"
                      alt="Research"
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-mekong-navy/70 to-transparent" />
                  </div>

                  <div className="col-span-12 md:col-span-8 flex flex-col justify-center space-y-6">
                    <div className="flex items-center gap-6">
                      <span className="text-[13px] font-black text-mekong-cyan uppercase tracking-[0.25em]">
                        {item.tag}
                      </span>
                      <div className="flex items-center gap-2 text-[12px] font-black text-slate-500 uppercase tracking-widest">
                        <Clock size={14} strokeWidth={3} />
                        <span>{item.time}</span>
                      </div>
                    </div>

                    <h3 className="text-[32px] lg:text-[34px] font-black leading-[1.15] tracking-tight group-hover:text-mekong-cyan transition-colors duration-300">
                      {item.title}
                    </h3>

                    <p className="text-[17px] text-slate-400 font-medium leading-relaxed opacity-90 max-w-4xl line-clamp-2 group-hover:opacity-100 transition-opacity">
                      {item.desc}
                    </p>

                    <div className="pt-2 flex items-center gap-3 text-mekong-cyan text-[13px] font-black uppercase tracking-widest opacity-0 -translate-x-4 group-hover:opacity-100 group-hover:translate-x-0 transition-all duration-500">
                      Đọc phân tích đầy đủ <ArrowUpRight size={16} />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </section>
        </div>

        {/* KHU VỰC BÊN PHẢI: SỰ KIỆN & THÔNG TIN (4 Cột) */}
        <div className="col-span-12 lg:col-span-4 space-y-8">
          <aside className="space-y-8">
            <div className="space-y-3 mb-8 px-2">
              <h2 className="text-xl font-black text-mekong-navy uppercase tracking-[0.15em]">
                Sự Kiện Sắp Tới
              </h2>
              <div className="w-12 h-1.5 bg-mekong-teal rounded-full shadow-sm shadow-mekong-teal/20" />
            </div>

            <div className="space-y-5">
              {[
                {
                  date: "30 THÁNG 3",
                  title: "Tập huấn cho Nông dân",
                  desc: "Kỹ thuật giảm thiểu độ mặn cho các vườn cây ăn trái quy mô nhỏ.",
                  loc: "Trung tâm Cộng đồng Mỹ Tho",
                  icon: Calendar,
                  color: "bg-mekong-teal",
                  textColor: "text-mekong-teal",
                },
                {
                  date: "05 THÁNG 4",
                  title: "Hội nghị Thượng đỉnh 2024",
                  desc: "Đánh giá thường niên về độ chính xác thủy văn Mekong-SALT.",
                  loc: "Trực tuyến / Hybrid (TP. HCM)",
                  icon: Users,
                  color: "bg-mekong-cyan",
                  textColor: "text-mekong-cyan",
                },
                {
                  date: "12 THÁNG 4",
                  title: "Diễn tập Khẩn cấp: Đỉnh Triều",
                  desc: "Kiểm tra quy trình phản ứng nhanh trong điều phối cống ngăn mặn.",
                  loc: "Trạm Điều hành Bến Tre",
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
                  <div
                    className={`absolute top-0 left-0 w-2 h-full ${event.color} transition-all duration-500 group-hover:w-3`}
                  />

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

            <button className="w-full py-4 bg-slate-50/50 border border-slate-200 rounded-2xl text-[12px] font-black text-mekong-navy uppercase tracking-[0.25em] hover:bg-white hover:shadow-md hover:border-mekong-teal/30 transition-all active:scale-[0.98]">
              Xem toàn bộ lịch trình
            </button>
          </aside>

          {/* ĐĂNG KÝ BẢN TIN */}
          <Card
            variant="white"
            className="bg-[#ECFEFF] border-none shadow-sm relative overflow-hidden p-10"
          >
            <div className="absolute -right-10 -bottom-10 w-48 h-48 bg-mekong-cyan/30 rounded-full blur-3xl" />
            <div className="relative z-10 space-y-4">
              <h3 className="text-sm font-black text-mekong-navy uppercase tracking-[0.2em]">
                Nhận tin dự báo
              </h3>
              <p className="text-xs text-mekong-slate font-medium leading-relaxed">
                Nhận dự báo độ mặn hàng tuần và các cảnh báo sông ngòi khẩn cấp
                trực tiếp qua email của bạn.
              </p>
              <div className="space-y-3 pt-2">
                <input
                  type="email"
                  placeholder="Địa chỉ email của bạn"
                  className="w-full bg-white border-none rounded-xl px-4 py-3.5 text-xs font-bold text-mekong-navy focus:ring-2 ring-mekong-teal/20 shadow-sm"
                />
                <Button
                  variant="navy"
                  className="w-full h-12 shadow-xl shadow-mekong-navy/10"
                >
                  Đăng ký ngay
                </Button>
              </div>
            </div>
          </Card>

          {/* THANH BÊN FOOTER */}
          <div className="mt-6 pt-6 border-t border-slate-200 space-y-8 animate-in fade-in duration-500">
            <div className="grid grid-cols-2 gap-6">
              <div className="space-y-4">
                <p className="text-[12px] font-black text-mekong-navy uppercase tracking-[0.2em] border-b border-slate-100 pb-2">
                  Tài nguyên
                </p>
                <ul className="space-y-2">
                  {["Tài liệu API", "Dữ liệu mở", "Quỹ nghiên cứu"].map(
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

              <div className="space-y-4">
                <p className="text-[12px] font-black text-mekong-navy uppercase tracking-[0.2em] border-b border-slate-100 pb-2">
                  Kết nối
                </p>
                <ul className="space-y-2">
                  {[
                    "Bộ Tài nguyên & Môi trường",
                    "Hỗ trợ kỹ thuật",
                    "Cổng thông tin đối tác",
                  ].map((item) => (
                    <li
                      key={item}
                      className="text-[14px] font-bold text-slate-500 hover:text-mekong-teal hover:translate-x-1 transition-all cursor-pointer flex items-center gap-2 group"
                    >
                      <div className="w-1 h-1 rounded-full bg-slate-300 group-hover:bg-mekong-teal transition-colors" />
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            <div className="space-y-3 px-4 py-5 bg-slate-50 rounded-2xl border border-slate-100 relative overflow-hidden group">
              <div className="absolute top-0 left-0 w-1 h-full bg-mekong-teal opacity-60" />

              <p className="text-[12px] font-black text-mekong-navy uppercase tracking-[0.2em]">
                DỰ ÁN MEKONG-SALT
              </p>
              <p className="text-[13px] text-slate-500 font-semibold leading-relaxed opacity-90">
                Nền tảng cộng tác về trí tuệ thủy văn, kết hợp dữ liệu cảm biến
                trực tiếp và AI để bảo vệ tương lai nông nghiệp Đồng bằng sông
                Cửu Long.
              </p>

              <div className="pt-1">
                <span className="text-[9px] font-black bg-white px-2 py-0.5 rounded border border-slate-200 text-slate-400 uppercase tracking-widest inline-block">
                  Hệ thống v4.2.1
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
