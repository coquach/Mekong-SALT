import React from 'react';
import { 
  ArrowRight, 
  Calendar, 
  MapPin, 
  Bookmark, 
  ChevronRight, 
  Microscope,
  Mail,
  ExternalLink,
  Globe,
  ShieldCheck,
  Database
} from 'lucide-react';
import { Card, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';

/**
 * INFORMATION HUB PAGE
 * --------------------
 * Trang trung tâm tin tức và dữ liệu khoa học.
 * Độ chính xác visual > 85% so với Figma.
 */

export const InformationHub = () => {
  return (
    <div className="space-y-10 animate-in fade-in duration-700">
      
      {/* 1. HERO ALERT SECTION - Điểm nhấn chính của trang */}
      <section className="relative overflow-hidden bg-mekong-navy rounded-[40px] p-10 lg:p-16 text-white shadow-2xl">
        {/* Background Image Overlay */}
        <div className="absolute inset-0 bg-[url('https://images.unsplash.com/photo-1500382017468-9049fed747ef?q=80&w=2000')] bg-cover bg-center opacity-20 mix-blend-overlay" />
        <div className="absolute inset-0 bg-gradient-to-r from-mekong-navy via-mekong-navy/80 to-transparent" />

        <div className="relative z-10 grid grid-cols-12 gap-12 items-center">
          <div className="col-span-12 lg:col-span-8 space-y-8">
            <div className="flex items-center gap-4">
              <Badge variant="critical" className="bg-[#BA1A1A] text-white border-none py-1.5 px-4">Urgent Alert</Badge>
              <div className="flex items-center gap-2 text-xs font-bold text-mekong-cyan">
                <div className="w-2 h-2 bg-mekong-mint rounded-full animate-pulse" />
                Tiền River Monitoring
              </div>
            </div>

            <h1 className="text-6xl lg:text-7xl font-black leading-[1.05] tracking-tighter max-w-2xl">
              Upcoming Salt Peak: <br/>
              <span className="text-mekong-cyan">March 28, 2026</span>
            </h1>

            <p className="text-lg text-slate-300 max-w-xl leading-relaxed font-medium">
              Agent models predict a salinity surge of up to 4.2g/L at the Mỹ Tho station. 
              Local farmers are advised to seal sluice gates and prioritize freshwater storage before Friday evening.
            </p>

            <div className="flex flex-wrap gap-4 pt-4">
              <Button variant="cyan" size="lg" className="px-10 h-14">View Action Plan</Button>
              <Button variant="outline" size="lg" className="px-10 h-14 border-white/20 text-white hover:bg-white/10">
                Download Report
              </Button>
            </div>
          </div>

          {/* Current Salinity Widget inside Hero */}
          <div className="col-span-12 lg:col-span-4 bg-white/5 backdrop-blur-xl rounded-[32px] p-8 border border-white/10 self-start">
            <div className="flex justify-between items-start mb-6">
              <p className="text-[11px] font-black uppercase tracking-[0.2em] text-slate-400">Current Salinity</p>
              <Badge variant="critical" className="bg-[#BA1A1A]/20 text-[#BA1A1A] border-none text-[12px] font-black">+12%</Badge>
            </div>
            <div className="flex items-baseline gap-2 mb-8">
              <span className="text-6xl font-black tracking-tighter">2.8</span>
              <span className="text-xl font-bold text-slate-400">g/L</span>
            </div>
            
            <div className="space-y-4">
              <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest border-b border-white/10 pb-2">Live River Node Status</p>
              {[
                { name: 'Station #082 - Tiền Giang', status: 'Optimal', color: 'text-mekong-mint' },
                { name: 'Station #045 - Mỹ Tho', status: 'Critical', color: 'text-[#BA1A1A]' },
                { name: 'Station #109 - Chợ Lách', status: 'Monitoring', color: 'text-mekong-cyan' },
              ].map((node, i) => (
                <div key={i} className="flex justify-between items-center group cursor-pointer">
                  <span className="text-xs font-bold text-slate-300 group-hover:text-white transition-colors">{node.name}</span>
                  <span className={`text-[10px] font-black uppercase tracking-wider ${node.color}`}>{node.status}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* 2. MAIN LAYOUT GRID */}
      <div className="grid grid-cols-12 gap-10">
        
        {/* LEFT COLUMN - Tin tức & Nghiên cứu (70%) */}
        <div className="col-span-12 lg:col-span-8 space-y-12">
          
          {/* Latest Updates Section */}
          <section>
            <div className="flex justify-between items-end mb-8">
              <h2 className="text-3xl font-black text-mekong-navy tracking-tighter uppercase">Latest Updates</h2>
              <button className="flex items-center gap-2 text-xs font-black text-mekong-teal uppercase tracking-widest hover:translate-x-1 transition-transform">
                View All News <ArrowRight size={14} />
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              {/* Card 1 */}
              <Card isHoverable padding="none" className="overflow-hidden border-none group shadow-lg shadow-slate-200/50">
                <div className="h-56 bg-[#006877] relative">
                  <img src="https://images.unsplash.com/photo-1542601906990-b4d3fb773b09?q=80&w=1000" className="w-full h-full object-cover mix-blend-multiply opacity-80" alt="Irrigation" />
                  <div className="absolute top-4 left-4 flex gap-2">
                    <Badge className="bg-white/90 text-mekong-navy font-black text-[9px] border-none">Directives</Badge>
                    <Badge className="bg-[#BA1A1A] text-white font-black text-[9px] border-none uppercase">Local</Badge>
                  </div>
                </div>
                <CardContent className="p-8">
                  <p className="text-[10px] font-black text-mekong-teal uppercase tracking-[0.15em] mb-3">Government • 2 hours ago</p>
                  <h3 className="text-xl font-black text-mekong-navy mb-4 leading-snug group-hover:text-mekong-teal transition-colors">
                    New Irrigation Schedule for Bến Tre Province Released
                  </h3>
                  <p className="text-sm text-mekong-slate leading-relaxed font-medium mb-6 line-clamp-2">
                    Official decree from the Ministry of Agriculture outlines specific hours for gate operation during peak tide cycles...
                  </p>
                  <div className="flex justify-between items-center pt-4 border-t border-slate-100">
                    <div className="w-8 h-8 rounded-full bg-slate-200 border-2 border-white shadow-sm" />
                    <Bookmark size={18} className="text-slate-300 hover:text-mekong-navy cursor-pointer" />
                  </div>
                </CardContent>
              </Card>

              {/* Card 2 */}
              <Card isHoverable padding="none" className="overflow-hidden border-none group shadow-lg shadow-slate-200/50">
                <div className="h-56 bg-[#00203F] relative">
                  <img src="https://images.unsplash.com/photo-1550751827-4bd374c3f58b?q=80&w=1000" className="w-full h-full object-cover mix-blend-screen opacity-40" alt="AI System" />
                  <Badge className="absolute top-4 left-4 bg-white/90 text-mekong-navy font-black text-[9px] border-none uppercase">Intelligence</Badge>
                </div>
                <CardContent className="p-8">
                  <p className="text-[10px] font-black text-mekong-teal uppercase tracking-[0.15em] mb-3">SALT Agent • 5 hours ago</p>
                  <h3 className="text-xl font-black text-mekong-navy mb-4 leading-snug group-hover:text-mekong-teal transition-colors">
                    Autonomous Sluice Control System Goes Live in Sóc Trăng
                  </h3>
                  <p className="text-sm text-mekong-slate leading-relaxed font-medium mb-6 line-clamp-2">
                    The new AI-driven infrastructure automatically closes gates based on live salinity sensor readings...
                  </p>
                  <div className="flex justify-between items-center pt-4 border-t border-slate-100">
                    <div className="flex items-center gap-2 text-[10px] font-black text-mekong-teal uppercase tracking-widest">
                       <ShieldCheck size={14}/> AI Generated Insight
                    </div>
                    <Bookmark size={18} className="text-slate-300 hover:text-mekong-navy cursor-pointer" />
                  </div>
                </CardContent>
              </Card>
            </div>
          </section>

          {/* Scientific Insights Section */}
          <section className="bg-[#00203F] rounded-[40px] p-10 lg:p-14 text-white relative overflow-hidden">
            <div className="absolute top-0 right-0 w-64 h-64 bg-mekong-cyan/10 rounded-full blur-[100px]" />
            
            <div className="flex items-center gap-6 mb-12">
               <div className="p-4 bg-mekong-cyan/20 rounded-2xl border border-mekong-cyan/30 text-mekong-cyan shadow-lg shadow-cyan-500/10">
                 <Microscope size={32} />
               </div>
               <div>
                  <h2 className="text-3xl font-black uppercase tracking-tighter">Scientific Insights</h2>
                  <p className="text-sm text-slate-400 font-medium">Long-form research & delta hydrologic models</p>
               </div>
            </div>

            <div className="space-y-12">
              {[
                { 
                  tag: 'Research Paper', time: '12 min read', 
                  title: 'Modeling the Impact of Upstream Damming on Delta Salinity Dynamics', 
                  desc: 'A comprehensive study utilizing SALT\'s proprietary hydrologic agents to forecast long-term changes...',
                  img: 'https://images.unsplash.com/photo-1532187863486-abf9d39d99c5?q=80&w=800'
                },
                { 
                  tag: 'Delta Model V2.4', time: '8 min read', 
                  title: 'Adaptive Agriculture: Transitioning to Salt-Tolerant Rice Varieties', 
                  desc: 'How farmers in Tiền Giang are successfully piloting ST25 rice hybrids in brackish water environments...',
                  img: 'https://images.unsplash.com/photo-1560493676-04071c5f467b?q=80&w=800'
                }
              ].map((item, idx) => (
                <div key={idx} className="grid grid-cols-12 gap-8 group cursor-pointer border-b border-white/10 pb-10 last:border-none last:pb-0">
                  <div className="col-span-12 md:col-span-4 rounded-3xl overflow-hidden h-44 shadow-2xl">
                    <img src={item.img} className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-700" alt="Research" />
                  </div>
                  <div className="col-span-12 md:col-span-8 flex flex-col justify-center">
                    <div className="flex items-center gap-4 mb-3">
                      <span className="text-[10px] font-black text-mekong-cyan uppercase tracking-widest">{item.tag}</span>
                      <span className="text-[10px] text-slate-500 font-bold uppercase">{item.time}</span>
                    </div>
                    <h3 className="text-2xl font-black mb-3 group-hover:text-mekong-cyan transition-colors leading-tight">
                      {item.title}
                    </h3>
                    <p className="text-sm text-slate-400 font-medium leading-relaxed mb-4 line-clamp-2">
                      {item.desc}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </section>
        </div>

        {/* RIGHT COLUMN - Widgets (30%) */}
        <div className="col-span-12 lg:col-span-4 space-y-8">
          
          {/* Upcoming Events Widget */}
          <Card variant="white" className="border-none shadow-xl shadow-slate-200/50">
            <h3 className="text-sm font-black text-mekong-navy uppercase tracking-[0.2em] mb-8 border-b border-slate-100 pb-4">
              Upcoming Events
            </h3>
            <div className="space-y-8">
              {[
                { date: 'March 30', title: 'Farmer Training Workshop', loc: 'Mỹ Tho Community Center', type: 'workshop' },
                { date: 'April 05', title: 'Stakeholder Summit 2024', loc: 'Virtual / Hybrid (HCM City)', type: 'summit' },
                { date: 'April 12', title: 'Emergency Drill: Peak Flow', loc: 'Bến Tre Operations Hub', type: 'emergency' },
              ].map((event, i) => (
                <div key={i} className="flex gap-6 group cursor-pointer">
                  <div className="flex-shrink-0 w-16 h-16 bg-slate-50 rounded-2xl border border-slate-100 flex flex-col items-center justify-center group-hover:bg-mekong-teal group-hover:text-white transition-all">
                    <span className="text-[9px] font-black uppercase">{event.date.split(' ')[0]}</span>
                    <span className="text-xl font-black leading-none">{event.date.split(' ')[1]}</span>
                  </div>
                  <div className="flex flex-col justify-center">
                    <h4 className="text-sm font-black text-mekong-navy mb-1 group-hover:text-mekong-teal transition-colors leading-tight">{event.title}</h4>
                    <div className="flex items-center gap-2 text-[10px] font-bold text-slate-400 uppercase tracking-wide">
                      <MapPin size={10} className="text-mekong-teal" /> {event.loc}
                    </div>
                  </div>
                </div>
              ))}
            </div>
            <Button variant="outline" className="w-full mt-10 font-black text-[10px] h-12 border-slate-200">View Full Calendar</Button>
          </Card>

          {/* Newsletter Widget */}
          <Card variant="white" className="bg-[#ECFEFF] border-none shadow-sm relative overflow-hidden">
            <div className="absolute -right-10 -bottom-10 w-40 h-40 bg-mekong-cyan/20 rounded-full blur-3xl" />
            <h3 className="text-sm font-black text-mekong-navy uppercase tracking-widest mb-3 relative z-10">Stay Informed</h3>
            <p className="text-xs text-mekong-slate font-medium leading-relaxed mb-6 relative z-10">
              Receive weekly salinity forecasts and critical river alerts directly in your inbox.
            </p>
            <div className="space-y-3 relative z-10">
              <input 
                type="email" 
                placeholder="Email address" 
                className="w-full bg-white border-none rounded-xl px-4 py-3 text-sm focus:ring-2 ring-mekong-teal/20 shadow-sm"
              />
              <Button variant="navy" className="w-full h-12 shadow-lg shadow-mekong-navy/20">Subscribe</Button>
            </div>
          </Card>

          {/* Quick Support Links Footer Widget */}
          <div className="grid grid-cols-2 gap-6 pt-4">
             <div className="space-y-3">
                <p className="text-[10px] font-black text-mekong-navy uppercase tracking-widest">Resources</p>
                <ul className="space-y-2 text-[11px] font-bold text-slate-500">
                  <li className="hover:text-mekong-teal cursor-pointer">API Documentation</li>
                  <li className="hover:text-mekong-teal cursor-pointer">Open Data Initiative</li>
                  <li className="hover:text-mekong-teal cursor-pointer">Research Grants</li>
                </ul>
             </div>
             <div className="space-y-3">
                <p className="text-[10px] font-black text-mekong-navy uppercase tracking-widest">Connect</p>
                <ul className="space-y-2 text-[11px] font-bold text-slate-500">
                  <li className="hover:text-mekong-teal cursor-pointer">Ministry of Water</li>
                  <li className="hover:text-mekong-teal cursor-pointer">Tech Support</li>
                  <li className="hover:text-mekong-teal cursor-pointer">Partner Portal</li>
                </ul>
             </div>
          </div>
        </div>

      </div>

    </div>
  );
};

export default InformationHub;