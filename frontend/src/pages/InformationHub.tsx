import {
  AlertTriangle,
  ArrowRight,
  ArrowUpRight,
  Bookmark,
  BrainCircuit,
  Calendar,
  Clock,
  MapPin,
  Microscope,
  Target,
  Zap,
} from "lucide-react";
import { useNavigate } from "react-router-dom";

import heroBackground from "../assets/hero-bg.png";
import irrigationCard from "../assets/new-1.png";
import newActionCard from "../assets/new-2.png";
import researchOne from "../assets/research-1.jpg";
import researchTwo from "../assets/research-2.jpg";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { Card, CardContent } from "../components/ui/Card";

const quickLogic = [
  {
    step: "Giám sát 24/7",
    desc: "Thu thập dữ liệu vệ tinh và IoT.",
    status: "LIVE",
    color: "text-mekong-mint",
  },
  {
    step: "Lập kế hoạch",
    desc: "Sinh plan và chờ phê duyệt.",
    status: "READY",
    color: "text-mekong-cyan",
  },
  {
    step: "Phản hồi",
    desc: "Học từ feedback sau thực thi.",
    status: "ACTIVE",
    color: "text-mekong-mint",
  },
] as const;

const researchCards = [
  {
    tag: "Kỹ thuật canh tác",
    time: "12 phút đọc",
    title: "Tưới tiêu thích ứng trong mùa hạn mặn",
    desc: "Áp dụng cảm biến và quy tắc cảnh báo để điều tiết tưới nước đúng thời điểm.",
    img: researchOne,
  },
  {
    tag: "Giống cây trồng",
    time: "8 phút đọc",
    title: "Giống lúa chịu mặn cho vùng ven biển",
    desc: "Tổng hợp các mô hình thực nghiệm phù hợp cho vùng có rủi ro xâm nhập mặn cao.",
    img: researchTwo,
  },
] as const;

const events = [
  {
    date: "30 THÁNG 03",
    title: "Tập huấn AI cho nông dân",
    desc: "Cách nhận cảnh báo mặn qua Zalo/SMS.",
    loc: "Trung tâm Mỹ Tho",
    icon: Calendar,
    color: "bg-mekong-teal",
    textColor: "text-mekong-teal",
  },
  {
    date: "12 THÁNG 04",
    title: "Diễn tập vận hành cống",
    desc: "Phối hợp kiểm tra luồng phê duyệt và mô phỏng.",
    loc: "Bến Tre Hub",
    icon: AlertTriangle,
    color: "bg-mekong-critical",
    textColor: "text-mekong-critical",
  },
] as const;

export function InformationHub() {
  const navigate = useNavigate();

  return (
    <div className="space-y-12 animate-in fade-in slide-in-from-bottom-4 duration-1000">
      <section className="relative overflow-hidden rounded-[40px] border border-white/5 bg-mekong-navy px-6 py-10 text-white shadow-2xl lg:px-16 lg:py-16">
        <div className="absolute inset-0 z-0 select-none">
          <img
            src={heroBackground}
            alt="Mekong Delta"
            className="h-full w-full object-cover opacity-40 mix-blend-luminosity grayscale-[0.3]"
          />
          <div className="absolute inset-0 bg-linear-to-r from-mekong-navy via-mekong-navy/80 to-transparent" />
        </div>

        <div className="relative z-10 grid w-full grid-cols-12 items-center gap-10">
          <div className="col-span-12 flex min-w-0 flex-col justify-center space-y-8 lg:col-span-8">
            <div className="flex flex-wrap items-center gap-4">
              <Badge
                variant="critical"
                className="animate-pulse border border-white/10 bg-mekong-critical px-6 py-2 text-[12px] font-black uppercase tracking-[0.2em] text-white shadow-lg"
              >
                Cảnh báo đỉnh mặn
              </Badge>
              <div className="flex items-center gap-3 text-[14px] font-black uppercase tracking-widest text-mekong-cyan drop-shadow-md">
                <BrainCircuit size={18} className="text-mekong-mint" />
                Nhận định từ Agentic AI
              </div>
            </div>

            <div className="space-y-4">
              <h1 className="text-5xl font-black leading-[1.1] tracking-tighter drop-shadow-2xl lg:text-[4.8rem]">
                Nguy cơ xâm nhập mặn
                <br />
                <span className="text-mekong-cyan">đang tăng trên trục Sông Tiền</span>
              </h1>
              <p className="max-w-2xl text-lg font-medium leading-relaxed text-slate-200 opacity-90 lg:text-xl">
                Màn hình này dẫn bạn nhanh vào dashboard vận hành, bản đồ và lịch sử để kiểm tra rủi ro, kế hoạch và hành động gần nhất.
              </p>
            </div>

            <div className="flex flex-wrap gap-5 pt-2">
              <Button
                variant="cyan"
                className="h-14 px-10 text-[12px] font-black shadow-xl"
                onClick={() => navigate("/dashboard")}
                onMouseEnter={() => void import("./Dashboard")}
                onFocus={() => void import("./Dashboard")}
              >
                Xem dashboard
              </Button>
              <Button
                variant="outline"
                className="h-14 px-10 text-[12px] font-black border-white/20 text-white backdrop-blur-sm hover:bg-white/5"
                onClick={() => navigate("/history")}
                onMouseEnter={() => void import("./History")}
                onFocus={() => void import("./History")}
              >
                Xem lịch sử
              </Button>
            </div>
          </div>

          <div className="col-span-12 flex justify-end lg:col-span-4">
            <div className="w-full max-w-105 rounded-4xl border border-white/10 bg-white/5 p-8 shadow-2xl backdrop-blur-3xl lg:p-10">
              <div className="mb-10 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Target size={16} className="text-mekong-mint" />
                  <p className="text-[11px] font-black uppercase tracking-[0.3em] text-slate-300">
                    Mục tiêu của agent
                  </p>
                </div>
                <Badge className="border-none bg-mekong-mint/20 text-[10px] font-black text-mekong-mint">
                  Ngăn xâm nhập
                </Badge>
              </div>

              <div className="mb-10 flex flex-col">
                <span className="mb-2 text-sm font-bold uppercase tracking-widest text-mekong-mint">
                  Độ mặn hiện tại
                </span>
                <div className="flex items-baseline gap-3">
                  <span className="text-8xl font-black leading-none tracking-tighter text-white drop-shadow-2xl">1</span>
                  <span className="text-2xl font-black uppercase text-slate-500">g/L</span>
                </div>
              </div>

              <div className="space-y-4 border-t border-white/10 pt-6">
                <p className="mb-4 text-[13px] font-black uppercase tracking-[0.25em] text-slate-500">
                  Logic đang thực thi
                </p>
                {quickLogic.map((item) => (
                  <div key={item.step} className="flex items-center justify-between gap-4 py-1">
                    <div className="flex flex-col">
                      <span className="text-[13px] font-bold text-slate-200">{item.step}</span>
                      <span className="text-[13px] font-medium text-slate-500">{item.desc}</span>
                    </div>
                    <span className={`text-[13px] font-black uppercase tracking-widest ${item.color}`}>
                      {item.status}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      <div className="grid grid-cols-12 gap-10">
        <div className="col-span-12 space-y-12 lg:col-span-8">
          <section>
            <div className="mb-10 flex items-end justify-between">
              <div className="space-y-3">
                <h2 className="flex items-center gap-3 text-3xl font-black uppercase leading-none tracking-tighter text-mekong-navy">
                  Tình báo thủy văn & chỉ thị
                </h2>
                <div className="h-1.5 w-12 rounded-full bg-mekong-teal shadow-sm" />
              </div>

              <button
                type="button"
                className="flex items-center gap-2 text-[11px] font-black uppercase tracking-[0.2em] text-mekong-teal transition-all hover:translate-x-1"
                onClick={() => navigate("/history")}
              >
                Xem kho dữ liệu DARD <ArrowRight size={14} />
              </button>
            </div>

            <div className="grid grid-cols-1 gap-8 lg:gap-10 md:grid-cols-2">
              {[
                {
                  image: irrigationCard,
                  label: "Chỉ thị DARD",
                  time: "2 giờ trước",
                  title: "Cập nhật lịch vận hành cống vùng ngọt",
                  desc: "Lịch trình lấy nước ngọt mới đã được phê duyệt cho các khu vực cần ưu tiên.",
                },
                {
                  image: newActionCard,
                  label: "Hệ thống tự trị",
                  time: "5 giờ trước",
                  title: "AI hoàn tất tối ưu đóng mở cống tại nút S-08",
                  desc: "Quy trình mô phỏng đã đẩy trạng thái cống sang chế độ an toàn và ghi nhận trace.",
                },
              ].map((card) => (
                <Card key={card.title} padding="none" className="group cursor-pointer overflow-hidden rounded-[40px] border-none bg-white shadow-soft">
                  <div className="relative h-60 overflow-hidden">
                    <img
                      src={card.image}
                      className="h-full w-full object-cover transition-transform duration-700 group-hover:scale-105"
                      alt={card.title}
                    />
                    <div className="absolute top-6 left-6 flex gap-2">
                      <span className="rounded-lg bg-white px-3 py-1 text-[10px] font-black uppercase tracking-widest text-mekong-navy shadow-sm">
                        {card.label}
                      </span>
                    </div>
                  </div>

                  <CardContent className="space-y-3 p-7 lg:p-8">
                    <p className="text-[10px] font-black uppercase tracking-[0.2em] text-mekong-teal">
                      {card.time}
                    </p>
                    <h3 className="text-[20px] font-black uppercase leading-[1.2] tracking-tight text-mekong-navy transition-colors group-hover:text-mekong-teal">
                      {card.title}
                    </h3>
                    <p className="text-[14px] font-medium leading-relaxed text-slate-500">
                      {card.desc}
                    </p>
                    <div className="mt-4 flex items-center justify-between border-t border-slate-50 pt-4">
                      <div className="flex items-center gap-2">
                        <Zap size={14} className="text-mekong-teal" />
                        <span className="text-[10px] font-black uppercase tracking-widest text-mekong-navy">
                          Hành động khuyến nghị
                        </span>
                      </div>
                      <button type="button" className="rounded-full p-2 transition-colors hover:bg-slate-50" aria-label="Lưu bài viết">
                        <Bookmark size={20} strokeWidth={2.5} className="text-slate-400 transition-colors group-hover:text-mekong-navy" />
                      </button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </section>

          <section className="relative overflow-hidden rounded-[40px] border border-white/5 bg-mekong-navy p-10 text-white shadow-2xl lg:p-14">
            <div className="absolute top-0 right-0 h-125 w-125 rounded-full bg-mekong-cyan/5 blur-[120px] pointer-events-none" />

            <div className="relative z-10 mb-20 flex items-center gap-6">
              <div className="rounded-2xl border border-white/10 bg-white/5 p-4 text-mekong-cyan shadow-xl">
                <Microscope size={40} strokeWidth={2.5} />
              </div>
              <div className="space-y-2">
                <h2 className="text-4xl font-black uppercase leading-none tracking-tighter lg:text-5xl">
                  Kho tri thức thích ứng
                </h2>
                <p className="text-[12px] font-black uppercase tracking-[0.3em] text-slate-400 opacity-80">
                  Nghiên cứu và giải pháp nông nghiệp bền vững
                </p>
              </div>
            </div>

            <div className="relative z-10 space-y-16">
              {researchCards.map((item) => (
                <div key={item.title} className="group grid grid-cols-12 gap-12 border-b border-white/5 pb-16 last:border-none last:pb-0">
                  <div className="relative col-span-12 h-60 overflow-hidden rounded-4xl shadow-2xl md:col-span-4">
                    <img src={item.img} className="h-full w-full object-cover transition-transform duration-700 group-hover:scale-110" alt={item.title} />
                    <div className="absolute inset-0 bg-linear-to-t from-mekong-navy/70 to-transparent" />
                  </div>

                  <div className="col-span-12 flex flex-col justify-center space-y-6 md:col-span-8">
                    <div className="flex items-center gap-6">
                      <span className="text-[13px] font-black uppercase tracking-[0.25em] text-mekong-cyan">{item.tag}</span>
                      <div className="flex items-center gap-2 text-[12px] font-black uppercase tracking-widest text-slate-500">
                        <Clock size={14} strokeWidth={3} />
                        <span>{item.time}</span>
                      </div>
                    </div>
                    <h3 className="text-[32px] font-black leading-[1.15] tracking-tight transition-colors group-hover:text-mekong-cyan lg:text-[34px]">
                      {item.title}
                    </h3>
                    <p className="text-[17px] font-medium leading-relaxed text-slate-400 opacity-90 line-clamp-2">
                      {item.desc}
                    </p>
                    <div className="flex items-center gap-3 text-[13px] font-black uppercase tracking-widest text-mekong-cyan opacity-0 -translate-x-4 transition-all duration-500 group-hover:opacity-100 group-hover:translate-x-0">
                      Đọc chi tiết giải pháp <ArrowUpRight size={16} />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </section>
        </div>

        <div className="col-span-12 space-y-8 lg:col-span-4">
          <aside className="space-y-8">
            <div className="mb-8 space-y-3 px-2">
              <h2 className="text-xl font-black uppercase tracking-[0.15em] text-mekong-navy">
                Sự kiện & hội thảo
              </h2>
              <div className="h-1.5 w-12 rounded-full bg-mekong-teal shadow-sm" />
            </div>

            <div className="space-y-5">
              {events.map((event) => (
                <Card
                  key={event.title}
                  padding="none"
                  className="group cursor-pointer overflow-hidden rounded-4xl border border-slate-100 bg-white shadow-soft transition-all duration-500"
                >
                  <div className={`absolute top-0 left-0 h-full w-2 ${event.color} transition-all duration-500 group-hover:w-3`} />
                  <div className="space-y-4 p-7 pl-9">
                    <div className="flex items-center justify-between">
                      <span className="rounded-xl border border-slate-100 bg-slate-50 px-3 py-1 text-[10px] font-black tracking-widest text-slate-500">
                        {event.date}
                      </span>
                      <event.icon size={18} className={`${event.textColor} opacity-60`} />
                    </div>
                    <div className="space-y-1.5">
                      <h4 className="text-[17px] font-black leading-tight text-mekong-navy transition-colors group-hover:text-mekong-teal">
                        {event.title}
                      </h4>
                      <p className="text-[13px] font-medium leading-relaxed text-slate-500 opacity-85">
                        {event.desc}
                      </p>
                    </div>
                    <div className={`flex items-center gap-2 pt-1 text-[10px] font-black uppercase tracking-[0.2em] ${event.textColor}`}>
                      <MapPin size={14} strokeWidth={2.5} />
                      <span>{event.loc}</span>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          </aside>

          <Card variant="white" className="relative overflow-hidden rounded-4xl border-none bg-[#ECFEFF] p-10 shadow-sm">
            <div className="absolute -right-10 -bottom-10 h-48 w-48 rounded-full bg-mekong-cyan/30 blur-3xl" />
            <div className="relative z-10 space-y-4">
              <h3 className="text-sm font-black uppercase tracking-[0.2em] text-mekong-navy">
                Nhận tin khẩn cấp
              </h3>
              <p className="text-xs font-medium leading-relaxed text-mekong-slate">
                Agent sẽ gửi cảnh báo phù hợp tới người vận hành qua kênh liên lạc đã đăng ký.
              </p>
              <div className="space-y-3 pt-2">
                <input
                  type="email"
                  placeholder="Địa chỉ Email hoặc SĐT"
                  className="w-full rounded-xl border-none bg-white px-4 py-3.5 text-xs font-bold text-mekong-navy shadow-sm ring-mekong-teal/20 focus:ring-2"
                />
                <Button variant="navy" className="h-12 w-full shadow-xl shadow-mekong-navy/10">
                  Đăng ký ngay
                </Button>
              </div>
            </div>
          </Card>

          <div className="mt-6 space-y-8 border-t border-slate-200 pt-6">
            <div className="grid grid-cols-2 gap-6">
              <div className="space-y-4">
                <p className="border-b border-slate-100 pb-2 text-[12px] font-black uppercase tracking-[0.2em] text-mekong-navy">
                  Tài nguyên
                </p>
                <ul className="space-y-2">
                  {["Tài liệu API", "Dữ liệu mở", "Quỹ nghiên cứu"].map((item) => (
                    <li
                      key={item}
                      className="group flex cursor-pointer items-center gap-2 text-[14px] font-bold text-slate-500 transition-all hover:translate-x-1 hover:text-mekong-teal"
                    >
                      <div className="h-1 w-1 rounded-full bg-slate-300 transition-colors group-hover:bg-mekong-teal" />
                      {item}
                    </li>
                  ))}
                </ul>
              </div>

              <div className="space-y-4">
                <p className="border-b border-slate-100 pb-2 text-[12px] font-black uppercase tracking-[0.2em] text-mekong-navy">
                  Kết nối
                </p>
                <ul className="space-y-2">
                  {["Bộ Tài nguyên & Môi trường", "Hỗ trợ kỹ thuật", "Cổng thông tin đối tác"].map((item) => (
                    <li
                      key={item}
                      className="group flex cursor-pointer items-center gap-2 text-[14px] font-bold text-slate-500 transition-all hover:translate-x-1 hover:text-mekong-teal"
                    >
                      <div className="h-1 w-1 rounded-full bg-slate-300 transition-colors group-hover:bg-mekong-teal" />
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            <div className="group relative overflow-hidden rounded-2xl border border-slate-100 bg-slate-50 px-4 py-5">
              <div className="absolute top-0 left-0 h-full w-1 bg-mekong-teal opacity-60" />
              <p className="text-[12px] font-black uppercase tracking-[0.2em] text-mekong-navy">
                Dự án Mekong-SALT
              </p>
              <p className="text-[13px] font-semibold leading-relaxed text-slate-500 opacity-90">
                Nền tảng cộng tác về trí tuệ thủy văn, kết hợp dữ liệu cảm biến và AI để hỗ trợ ra quyết định vận hành.
              </p>
              <div className="pt-1">
                <span className="inline-block rounded border border-slate-200 bg-white px-2 py-0.5 text-[9px] font-black uppercase tracking-widest text-slate-400">
                  Hệ thống v4.2.1
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default InformationHub;
