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
  Sparkles,
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

export function InformationHub() {
  const navigate = useNavigate();

  return (
    <div className="space-y-12 animate-in fade-in slide-in-from-bottom-4 duration-1000">
      <section className="relative overflow-hidden bg-mekong-navy rounded-[40px] px-8 lg:px-16 h-145 flex items-center text-white shadow-2xl border border-white/5">
        <div className="absolute inset-0 z-0 select-none">
          <img
            src={heroBackground}
            alt="Mekong Delta"
            className="w-full h-full object-cover opacity-40 mix-blend-luminosity grayscale-[0.3]"
          />
          <div className="absolute inset-0 bg-linear-to-r from-mekong-navy via-mekong-navy/80 to-transparent" />
        </div>

        <div className="relative z-10 grid grid-cols-12 gap-10 items-center w-full">
          <div className="col-span-12 lg:col-span-8 flex flex-col justify-center space-y-8 min-w-0">
            <div className="flex flex-wrap items-center gap-5">
              <Badge
                variant="critical"
                className="bg-mekong-critical text-white border border-white/10 py-2 px-6 text-[12px] font-black uppercase tracking-[0.2em] shadow-lg animate-pulse"
              >
                CẢNH BÁO ĐỈNH MẶN
              </Badge>
              <div className="flex items-center gap-3 text-[14px] font-black text-mekong-cyan uppercase tracking-widest drop-shadow-md">
                <BrainCircuit size={18} className="text-mekong-mint" />
                NHẬN ĐỊNH TỪ AGENTIC AI
              </div>
            </div>

            <div className="space-y-4">
              <h1 className="text-5xl lg:text-[4.8rem] font-black leading-[1.1] tracking-tighter drop-shadow-2xl">
                Nguy cơ xâm nhập: <br />
                <span className="text-mekong-cyan">Sông Tiền - Ngày 09/05</span>
              </h1>
              <p className="text-lg lg:text-xl text-slate-200 max-w-2xl leading-relaxed font-medium opacity-90">
                Dựa trên mô hình dự đoán <span className="text-white font-bold underline decoration-mekong-cyan">SALT-Agent</span>,
                đỉnh mặn có thể đạt đến <span className="text-white font-bold">2 g/L</span> và mặn sẽ lấn sâu đến 35km vào đất liền.
                Hệ thống ở các khu vực chịu ảnh hưởng đã tự động lập kế hoạch đóng cống ngăn mặn và bơm nước ngọt vào ruộng để phòng tránh thiên tai.
              </p>
            </div>

            <div className="flex flex-wrap gap-5 pt-2">
              <Button
                variant="cyan"
                className="px-10 h-14 text-[12px] font-black shadow-xl"
                onClick={() => navigate("/strategy")}
              >
                XEM CHIẾN LƯỢC CỦA AI
              </Button>
              <Button
                variant="outline"
                className="px-10 h-14 text-[12px] font-black border-white/20 text-white hover:bg-white/5 backdrop-blur-sm"
              >
                TẢI BÁO CÁO DỰ BÁO
              </Button>
            </div>
          </div>

          <div className="col-span-12 lg:col-span-4 flex justify-end">
            <div className="bg-white/5 backdrop-blur-3xl rounded-4xl p-8 lg:p-10 border border-white/10 shadow-2xl w-full max-w-105 transition-all hover:bg-white/8">
              <div className="flex justify-between items-center mb-10">
                <div className="flex items-center gap-2">
                  <Target size={16} className="text-mekong-mint" />
                  <p className="text-[11px] font-black uppercase tracking-[0.3em] text-slate-300">
                    MỤC TIÊU CỦA AGENT
                  </p>
                </div>
                <Badge className="bg-mekong-mint/20 text-mekong-mint border-none text-[10px] font-black">
                  NGĂN XÂM NHẬP
                </Badge>
              </div>

              <div className="flex flex-col mb-10">
                <span className="text-sm font-bold text-mekong-mint uppercase tracking-widest mb-2">
                  Độ mặn hiện tại
                </span>
                <div className="flex items-baseline gap-3">
                  <span className="text-8xl font-black tracking-tighter leading-none text-white drop-shadow-2xl">1</span>
                  <span className="text-2xl font-black text-slate-500 uppercase">g/L</span>
                </div>
              </div>

              <div className="space-y-4 pt-6 border-t border-white/10">
                <p className="text-[13px] font-black text-slate-500 uppercase tracking-[0.25em] mb-4">
                  LOGIC ĐANG THỰC THI
                </p>
                {[
                  {
                    step: "Giám sát 24/7",
                    desc: "Thu thập dữ liệu vệ tinh & IoT",
                    status: "LIVE",
                    color: "text-mekong-mint",
                  },
                  {
                    step: "Lập kế hoạch",
                    desc: "Sẵn sàng đóng cống Mỹ Tho",
                    status: "READY",
                    color: "text-mekong-cyan",
                  },
                  {
                    step: "Phản hồi",
                    desc: "Tự động học từ sai số mặn",
                    status: "ACTIVE",
                    color: "text-mekong-mint",
                  },
                ].map((item, index) => (
                  <div key={index} className="flex justify-between items-center py-1">
                    <div className="flex flex-col">
                      <span className="text-[13px] font-bold text-slate-200">{item.step}</span>
                      <span className="text-[13px] text-slate-500 font-medium">{item.desc}</span>
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
        <div className="col-span-12 lg:col-span-8 space-y-12">
          <section>
            <div className="flex justify-between items-end mb-10">
              <div className="space-y-3">
                <h2 className="text-3xl font-black text-mekong-navy tracking-tighter uppercase leading-none flex items-center gap-3">
                  Tình báo Thủy văn & Chỉ thị
                </h2>
                <div className="w-12 h-1.5 bg-mekong-teal rounded-full shadow-sm" />
              </div>

              <button className="flex items-center gap-2 text-[11px] font-black text-mekong-teal uppercase tracking-[0.2em] hover:translate-x-1 transition-all">
                Xem kho dữ liệu DARD <ArrowRight size={14} />
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 lg:gap-10">
              <Card padding="none" className="rounded-[40px] overflow-hidden border-none bg-white shadow-soft group cursor-pointer">
                <div className="h-60 overflow-hidden relative">
                  <img
                    src={irrigationCard}
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700"
                    alt="Irrigation Schedule"
                  />
                  <div className="absolute top-6 left-6 flex gap-2">
                    <span className="bg-white px-3 py-1 rounded-lg text-[10px] font-black text-mekong-navy uppercase tracking-widest shadow-sm">
                      Chỉ thị DARD
                    </span>
                  </div>
                </div>

                <CardContent className="p-7 lg:p-8 space-y-3">
                  <p className="text-[10px] font-black text-mekong-teal uppercase tracking-[0.2em]">SỞ NN&PTNT • 2 GIỜ TRƯỚC</p>
                  <h3 className="text-[20px] font-black text-mekong-navy leading-[1.2] tracking-tight group-hover:text-mekong-teal transition-colors uppercase">
                    Cập nhật lịch vận hành cống vùng ngọt hóa Gò Công
                  </h3>
                  <p className="text-[14px] text-slate-500 font-medium leading-relaxed line-clamp-2">
                    Lịch trình lấy nước ngọt mới dựa trên chu kỳ triều kém đã được phê duyệt cho các huyện Tiền Giang...
                  </p>
                  <div className="flex justify-between items-center pt-4 mt-4 border-t border-slate-50">
                    <div className="flex items-center gap-2">
                      <Zap size={14} className="text-mekong-teal" />
                      <span className="text-[10px] font-black text-mekong-navy uppercase tracking-widest">
                        Hành động khuyên dùng
                      </span>
                    </div>
                    <button className="p-2 -mr-2 rounded-full hover:bg-slate-50 transition-colors group" aria-label="Lưu bài viết">
                      <Bookmark size={20} strokeWidth={2.5} className="text-slate-400 group-hover:text-mekong-navy" />
                    </button>
                  </div>
                </CardContent>
              </Card>

              <Card padding="none" className="rounded-[40px] overflow-hidden border-none bg-white shadow-soft group cursor-pointer">
                <div className="h-60 overflow-hidden relative">
                  <img
                    src={newActionCard}
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700"
                    alt="AI Sluice Control"
                  />
                  <div className="absolute top-5 left-5">
                    <Badge className="bg-white/95 text-mekong-navy font-black border-none shadow-sm">
                      Hệ thống tự trị
                    </Badge>
                  </div>
                </div>

                <CardContent className="p-7 lg:p-8 space-y-3">
                  <p className="text-[10px] font-black text-mekong-teal uppercase tracking-[0.2em]">AGENT LOGIC • 5 GIỜ TRƯỚC</p>
                  <h3 className="text-[20px] font-black text-mekong-navy leading-[1.2] tracking-tight group-hover:text-mekong-teal transition-colors uppercase">
                    AI hoàn thành tối ưu hóa đóng mở cống tại Nút S-08
                  </h3>
                  <p className="text-[14px] text-slate-500 font-medium leading-relaxed line-clamp-2">
                    Thông qua PLC, SALT-Agent đã điều phối thành công việc ngăn mặn lấn sâu mà không gây gián đoạn tàu thuyền...
                  </p>
                  <div className="flex justify-between items-center pt-4 mt-4 border-t border-slate-50">
                    <div className="flex items-center gap-2">
                      <Sparkles size={14} className="text-mekong-teal" />
                      <span className="text-[10px] font-black text-mekong-teal uppercase tracking-widest">
                        Tự tối ưu bởi AI
                      </span>
                    </div>
                    <button className="p-2 -mr-2 rounded-full hover:bg-slate-50 transition-colors group" aria-label="Lưu bài viết">
                      <Bookmark size={20} strokeWidth={2.5} className="text-slate-400 group-hover:text-mekong-navy" />
                    </button>
                  </div>
                </CardContent>
              </Card>
            </div>
          </section>

          <section className="relative overflow-hidden bg-mekong-navy rounded-[40px] p-10 lg:p-14 text-white shadow-2xl border border-white/5">
            <div className="absolute top-0 right-0 w-125 h-125 bg-mekong-cyan/5 rounded-full blur-[120px] pointer-events-none" />

            <div className="relative z-10 flex items-center gap-6 mb-20">
              <div className="p-4 bg-white/5 rounded-2xl border border-white/10 text-mekong-cyan shadow-xl">
                <Microscope size={40} strokeWidth={2.5} />
              </div>
              <div className="space-y-2">
                <h2 className="text-4xl lg:text-5xl font-black uppercase tracking-tighter leading-none">
                  Kho tri thức thích ứng
                </h2>
                <p className="text-[12px] font-black text-slate-400 uppercase tracking-[0.3em] opacity-80">
                  Nghiên cứu & Giải pháp nông nghiệp bền vững
                </p>
              </div>
            </div>

            <div className="relative z-10 space-y-16">
              {[
                {
                  tag: "Kỹ thuật canh tác",
                  time: "12 PHÚT ĐỌC",
                  title: "Sử dụng cảm biến đất để điều tiết tưới tiêu trong mùa hạn mặn",
                  desc: "Hướng dẫn tích hợp IoT vào ruộng vườn để AI có thể giúp bạn tự động tưới vào khung giờ độ mặn thấp nhất.",
                  img: researchOne,
                },
                {
                  tag: "Giống cây trồng",
                  time: "8 PHÚT ĐỌC",
                  title: "Phát triển giống lúa ST25 chịu mặn tại vùng ven biển Bến Tre",
                  desc: "Báo cáo thực địa về các hộ nông dân thí điểm thành công mô hình lúa - tôm thích ứng biến đổi khí hậu.",
                  img: researchTwo,
                },
              ].map((item, index) => (
                <div key={index} className="grid grid-cols-12 gap-12 group cursor-pointer border-b border-white/5 pb-16 last:border-none last:pb-0">
                  <div className="col-span-12 md:col-span-4 h-60 rounded-4xl overflow-hidden shadow-2xl relative">
                    <img src={item.img} className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-700" alt="Research" />
                    <div className="absolute inset-0 bg-linear-to-t from-mekong-navy/70 to-transparent" />
                  </div>

                  <div className="col-span-12 md:col-span-8 flex flex-col justify-center space-y-6">
                    <div className="flex items-center gap-6">
                      <span className="text-[13px] font-black text-mekong-cyan uppercase tracking-[0.25em]">{item.tag}</span>
                      <div className="flex items-center gap-2 text-[12px] font-black text-slate-500 uppercase tracking-widest">
                        <Clock size={14} strokeWidth={3} />
                        <span>{item.time}</span>
                      </div>
                    </div>
                    <h3 className="text-[32px] lg:text-[34px] font-black leading-[1.15] tracking-tight group-hover:text-mekong-cyan transition-colors">
                      {item.title}
                    </h3>
                    <p className="text-[17px] text-slate-400 font-medium leading-relaxed opacity-90 line-clamp-2">
                      {item.desc}
                    </p>
                    <div className="pt-2 flex items-center gap-3 text-mekong-cyan text-[13px] font-black uppercase tracking-widest opacity-0 -translate-x-4 group-hover:opacity-100 group-hover:translate-x-0 transition-all duration-500">
                      Đọc chi tiết giải pháp <ArrowUpRight size={16} />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </section>
        </div>

        <div className="col-span-12 lg:col-span-4 space-y-8">
          <aside className="space-y-8">
            <div className="space-y-3 mb-8 px-2">
              <h2 className="text-xl font-black text-mekong-navy uppercase tracking-[0.15em]">
                Sự kiện & Hội thảo
              </h2>
              <div className="w-12 h-1.5 bg-mekong-teal rounded-full shadow-sm" />
            </div>

            <div className="space-y-5">
              {[
                {
                  date: "30 THÁNG 03",
                  title: "Tập huấn AI cho Nông dân",
                  desc: "Cách cài đặt nhận thông báo mặn cá nhân hóa qua Zalo/SMS.",
                  loc: "Trung tâm Mỹ Tho",
                  icon: Calendar,
                  color: "bg-mekong-teal",
                  textColor: "text-mekong-teal",
                },
                {
                  date: "12 THÁNG 04",
                  title: "Diễn tập vận hành cống",
                  desc: "Phối hợp cùng Sở NN&PTNT kiểm tra hệ thống PLC tự động.",
                  loc: "Bến Tre Hub",
                  icon: AlertTriangle,
                  color: "bg-mekong-critical",
                  textColor: "text-mekong-critical",
                },
              ].map((event, index) => (
                <Card
                  key={index}
                  padding="none"
                  className="rounded-4xl border border-slate-100 bg-white shadow-soft transition-all duration-500 group cursor-pointer overflow-hidden relative"
                >
                  <div className={`absolute top-0 left-0 w-2 h-full ${event.color} transition-all duration-500 group-hover:w-3`} />
                  <div className="p-7 pl-9 space-y-4">
                    <div className="flex justify-between items-center">
                      <span className="bg-slate-50 text-slate-500 px-3 py-1 rounded-xl text-[10px] font-black tracking-widest border border-slate-100">
                        {event.date}
                      </span>
                      <event.icon size={18} className={`${event.textColor} opacity-60`} />
                    </div>
                    <div className="space-y-1.5">
                      <h4 className="text-[17px] font-black text-mekong-navy leading-tight group-hover:text-mekong-teal transition-colors">
                        {event.title}
                      </h4>
                      <p className="text-[13px] text-slate-500 font-medium leading-relaxed opacity-85">
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

          <Card variant="white" className="bg-[#ECFEFF] border-none shadow-sm relative overflow-hidden p-10 rounded-4xl">
            <div className="absolute -right-10 -bottom-10 w-48 h-48 bg-mekong-cyan/30 rounded-full blur-3xl" />
            <div className="relative z-10 space-y-4">
              <h3 className="text-sm font-black text-mekong-navy uppercase tracking-[0.2em]">
                Nhận tin khẩn cấp
              </h3>
              <p className="text-xs text-mekong-slate font-medium leading-relaxed">
                Agent sẽ gửi cảnh báo mặn chính xác cho tọa độ ruộng vườn của bạn qua điện thoại.
              </p>
              <div className="space-y-3 pt-2">
                <input
                  type="email"
                  placeholder="Địa chỉ Email hoặc SĐT"
                  className="w-full bg-white border-none rounded-xl px-4 py-3.5 text-xs font-bold text-mekong-navy focus:ring-2 ring-mekong-teal/20 shadow-sm"
                />
                <Button variant="navy" className="w-full h-12 shadow-xl shadow-mekong-navy/10">
                  ĐĂNG KÝ NGAY
                </Button>
              </div>
            </div>
          </Card>

          <div className="mt-6 pt-6 border-t border-slate-200 space-y-8 animate-in fade-in duration-500">
            <div className="grid grid-cols-2 gap-6">
              <div className="space-y-4">
                <p className="text-[12px] font-black text-mekong-navy uppercase tracking-[0.2em] border-b border-slate-100 pb-2">
                  Tài nguyên
                </p>
                <ul className="space-y-2">
                  {['Tài liệu API', 'Dữ liệu mở', 'Quỹ nghiên cứu'].map((item) => (
                    <li key={item} className="text-[14px] font-bold text-slate-500 hover:text-mekong-teal hover:translate-x-1 transition-all cursor-pointer flex items-center gap-2 group">
                      <div className="w-1 h-1 rounded-full bg-slate-300 group-hover:bg-mekong-teal transition-colors" />
                      {item}
                    </li>
                  ))}
                </ul>
              </div>

              <div className="space-y-4">
                <p className="text-[12px] font-black text-mekong-navy uppercase tracking-[0.2em] border-b border-slate-100 pb-2">
                  Kết nối
                </p>
                <ul className="space-y-2">
                  {['Bộ Tài nguyên & Môi trường', 'Hỗ trợ kỹ thuật', 'Cổng thông tin đối tác'].map((item) => (
                    <li key={item} className="text-[14px] font-bold text-slate-500 hover:text-mekong-teal hover:translate-x-1 transition-all cursor-pointer flex items-center gap-2 group">
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
                Nền tảng cộng tác về trí tuệ thủy văn, kết hợp dữ liệu cảm biến trực tiếp và AI để bảo vệ tương lai nông nghiệp Đồng bằng sông Cửu Long.
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
}

export default InformationHub;