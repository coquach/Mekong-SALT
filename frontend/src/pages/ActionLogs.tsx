import React from "react";
import {
  Share2,
  Download,
  Search,
  ClipboardList,
  Filter,
  CheckCircle2,
  AlertCircle,
  MapPin,
  Activity,
  Zap,
  Waves,
  RefreshCcw,
  BrainCircuit,
} from "lucide-react";
import { Card, CardContent } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Badge } from "../components/ui/Badge";

/**
 * ACTION LOGS - INTERVENTION & LEARNING HUB
 * -----------------------------------------
 * Nhật ký kiểm toán và phân tích phản hồi vòng lặp kín của AI.
 * Độ chính xác visual > 90% so với Figma.
 */

export const ActionLogs = () => {
  return (
    <div className="space-y-8 animate-in fade-in duration-700">
      {/* 1. TOP HEADER SECTION */}
      <div className="flex justify-between items-end">
        <div className="space-y-2">
          <h1 className="text-4xl font-black text-mekong-navy tracking-tighter leading-none">
            Intervention & Learning Hub
          </h1>
          <p className="text-sm text-mekong-slate font-medium max-w-2xl leading-relaxed">
            System-wide audit of AI-driven sluice gate actions, ecological
            feedback loops, and recursive model optimizations for the Mekong
            Delta region.
          </p>
        </div>
        <div className="flex gap-4">
          <Button
            variant="outline"
            className="h-12 px-6 flex gap-2 border-slate-200"
          >
            <Share2 size={16} /> Share Report
          </Button>
          <Button variant="navy" className="h-12 px-6 flex gap-2">
            <Download size={16} /> Export to DARD
          </Button>
        </div>
      </div>

      {/* 2. TOP ANALYTICS GRID */}
      <div className="grid grid-cols-12 gap-8">
        {/* Left Stats (4 cols) */}
        <div className="col-span-12 lg:col-span-4 space-y-6">
          {/* Recent Learning Log */}
          <Card
            variant="white"
            className="border-l-4 border-l-mekong-navy rounded-3xl"
          >
            <div className="flex items-start gap-4">
              <div className="p-2 bg-slate-50 rounded-xl text-mekong-navy mt-1">
                <BrainCircuit size={20} />
              </div>
              <div className="space-y-4 flex-1">
                <div>
                  <h4 className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2">
                    Recent Learning Log
                  </h4>
                  <p className="text-[13px] font-medium text-mekong-navy leading-relaxed italic">
                    "Agent learned: Wind at level 6 requires 15% earlier gate
                    closure to maintain goal."
                  </p>
                </div>
                <div className="flex justify-between items-center">
                  <Badge
                    variant="cyan"
                    className="bg-mekong-cyan/10 text-mekong-teal border-none"
                  >
                    Recursive Optimization
                  </Badge>
                  <span className="text-[9px] font-bold text-slate-400 uppercase tracking-widest">
                    2 hours ago
                  </span>
                </div>
              </div>
            </div>
          </Card>

          {/* Avoided Damages Card */}
          <Card
            variant="navy"
            padding="lg"
            className="bg-[#00203F] text-white overflow-hidden relative min-h-[300px] flex flex-col justify-between"
          >
            <div className="absolute top-0 right-0 w-48 h-48 bg-mekong-cyan/10 rounded-full blur-[80px]" />
            <div className="relative z-10">
              <p className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] mb-4">
                Avoided Damages (30D)
              </p>
              <div className="flex items-baseline gap-2">
                <span className="text-5xl font-black text-mekong-cyan tracking-tighter">
                  $4.2M
                </span>
                <span className="text-xl font-bold text-slate-400 uppercase">
                  USD
                </span>
              </div>
              <p className="text-xs text-slate-300 mt-4 leading-relaxed font-medium">
                Estimated 1,420 Hectares of rice protected from salinity
                intrusion.
              </p>
            </div>

            {/* Bar Chart Mockup */}
            <div className="relative z-10 flex items-end gap-2 h-20 mt-8">
              {[40, 65, 30, 80, 50, 95, 75].map((h, i) => (
                <div
                  key={i}
                  className={`flex-1 rounded-t-lg transition-all duration-500 hover:bg-mekong-cyan ${i === 5 ? "bg-mekong-cyan" : "bg-white/20"}`}
                  style={{ height: `${h}%` }}
                />
              ))}
            </div>
          </Card>
        </div>

        {/* Right Feedback Analysis (8 cols) */}
        <div className="col-span-12 lg:col-span-8">
          <Card
            variant="white"
            padding="lg"
            className="h-full border border-slate-100 shadow-soft"
          >
            <div className="flex justify-between items-center mb-10">
              <div className="flex items-center gap-3">
                <RefreshCcw
                  size={20}
                  className="text-mekong-teal animate-spin-slow"
                />
                <h3 className="text-sm font-black text-mekong-navy uppercase tracking-widest">
                  Closed-Loop Feedback Analysis
                </h3>
              </div>
              <Badge className="bg-slate-50 text-slate-500 border-slate-200">
                Real-time Validation
              </Badge>
            </div>

            <div className="grid grid-cols-2 gap-8">
              {[
                {
                  node: "Hòa Định Gate",
                  status: "Goal Achieved",
                  color: "text-mekong-mint",
                  bg: "bg-mekong-mint/10",
                  desc: "Salinity maintained < 0.5 g/L despite high tide surge.",
                  eff: "92%",
                },
                {
                  node: "Cống Xuân Hòa",
                  status: "In Progress",
                  color: "text-mekong-cyan",
                  bg: "bg-mekong-cyan/10",
                  desc: "Oxygen levels stabilizing at Node 42 after flushing.",
                  eff: "88%",
                },
              ].map((item, i) => (
                <div
                  key={i}
                  className="p-8 rounded-[32px] bg-slate-50/50 border border-slate-100 group hover:shadow-xl transition-all duration-500"
                >
                  <div className="flex justify-between items-start mb-6">
                    <h5 className="text-[11px] font-black text-mekong-navy uppercase tracking-widest">
                      {item.node}
                    </h5>
                    <span
                      className={`text-[9px] font-black px-2 py-0.5 rounded uppercase ${item.bg} ${item.color}`}
                    >
                      {item.status}
                    </span>
                  </div>
                  <p className="text-sm font-bold text-mekong-navy mb-10 leading-relaxed min-h-[40px]">
                    {item.desc}
                  </p>
                  <div className="space-y-3">
                    <div className="flex justify-between items-end">
                      <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">
                        Efficiency
                      </span>
                      <span className={`text-xl font-black ${item.color}`}>
                        {item.eff}
                      </span>
                    </div>
                    <div className="h-1.5 bg-slate-200 rounded-full overflow-hidden">
                      <div
                        className={`h-full ${item.color.replace("text", "bg")} transition-all duration-1000`}
                        style={{ width: item.eff }}
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </div>

      {/* 3. DETAILED INTERVENTION TABLE */}
      <section className="bg-white rounded-[40px] border border-slate-200 shadow-soft overflow-hidden">
        {/* Table Header Wrapper */}
        <div className="bg-mekong-navy p-6 text-white flex justify-between items-center">
          <div className="flex items-center gap-3">
            <ClipboardList size={20} className="text-mekong-cyan" />
            <h3 className="text-sm font-black uppercase tracking-widest">
              Detailed Intervention History
            </h3>
          </div>
          <button className="flex items-center gap-2 px-4 py-2 bg-white/10 rounded-lg text-[10px] font-black uppercase tracking-widest hover:bg-white/20 transition-all">
            <Filter size={14} /> Filter by Agent Confidence
          </button>
        </div>

        {/* Actual Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead className="bg-slate-50/50 border-b border-slate-100">
              <tr className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]">
                <th className="px-10 py-6">Timestamp</th>
                <th className="px-10 py-6">Location / Node</th>
                <th className="px-10 py-6">Action Taken</th>
                <th className="px-10 py-6">Trigger Event</th>
                <th className="px-10 py-6">AI Confidence</th>
                <th className="px-10 py-6">Verification</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-50">
              {[
                {
                  t: "Mar 24, 2024",
                  sub: "14:22:10 GMT+7",
                  loc: "Mỹ Thuận Bridge Sluice",
                  action: "Gate Closure",
                  trigger: "Salinity > 2.1 g/L (Node S-12)",
                  triggerIcon: Activity,
                  conf: "98.4%",
                  status: "verified",
                },
                {
                  t: "Mar 24, 2024",
                  sub: "12:05:44 GMT+7",
                  loc: "Bình Đại Node #08",
                  action: "Desalinization Pump Activate",
                  trigger: "Abnormal High Tide (Predicted)",
                  triggerIcon: Waves,
                  conf: "94.1%",
                  status: "verified",
                },
                {
                  t: "Mar 24, 2024",
                  sub: "09:15:22 GMT+7",
                  loc: "Trà Vinh Diversion Wall",
                  action: "Structural Bypass",
                  trigger: "TDS Surge Prediction > 400ppm",
                  triggerIcon: Zap,
                  conf: "89.9%",
                  status: "pending",
                },
              ].map((row, i) => (
                <tr
                  key={i}
                  className="hover:bg-slate-50/50 transition-colors group"
                >
                  <td className="px-10 py-8">
                    <p className="text-sm font-black text-mekong-navy mb-1">
                      {row.t}
                    </p>
                    <p className="text-[10px] font-mono text-slate-400">
                      {row.sub}
                    </p>
                  </td>
                  <td className="px-10 py-8">
                    <div className="flex items-center gap-2">
                      <MapPin size={16} className="text-mekong-teal" />
                      <span className="text-sm font-black text-mekong-navy">
                        {row.loc}
                      </span>
                    </div>
                  </td>
                  <td className="px-10 py-8">
                    <span className="px-4 py-2 bg-slate-100 rounded-xl text-[10px] font-black text-mekong-navy uppercase tracking-widest">
                      {row.action}
                    </span>
                  </td>
                  <td className="px-10 py-8">
                    <div className="flex items-center gap-3">
                      <row.triggerIcon size={16} className="text-slate-400" />
                      <span className="text-[11px] font-medium text-slate-500 leading-tight max-w-[150px]">
                        {row.trigger}
                      </span>
                    </div>
                  </td>
                  <td className="px-10 py-8">
                    <div className="flex flex-col gap-2">
                      <div className="h-1 w-24 bg-slate-100 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-mekong-teal"
                          style={{ width: row.conf }}
                        />
                      </div>
                      <span className="text-[11px] font-black text-mekong-teal">
                        {row.conf}
                      </span>
                    </div>
                  </td>
                  <td className="px-10 py-8 text-center">
                    {row.status === "verified" ? (
                      <div className="w-8 h-8 rounded-full bg-mekong-mint/10 flex items-center justify-center text-mekong-mint mx-auto">
                        <CheckCircle2 size={18} />
                      </div>
                    ) : (
                      <div className="w-8 h-8 rounded-full border-2 border-slate-100 flex items-center justify-center text-slate-300 mx-auto">
                        <RefreshCcw size={16} />
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination Mockup */}
        <div className="bg-slate-50/50 px-10 py-6 border-t border-slate-100 flex justify-between items-center text-[10px] font-black text-slate-400 uppercase tracking-widest">
          <span>Displaying 1-15 of 2,482 logs</span>
          <div className="flex gap-4">
            <button className="hover:text-mekong-navy">Prev</button>
            <button className="hover:text-mekong-navy">Next</button>
          </div>
        </div>
      </section>

      {/* 4. BOTTOM PERFORMANCE GRID */}
      <div className="grid grid-cols-12 gap-8">
        {/* System Performance Chart Placeholder */}
        <Card
          variant="white"
          className="col-span-12 lg:col-span-7 h-[350px] flex flex-col justify-between"
        >
          <div className="flex justify-between items-start">
            <div>
              <h3 className="text-sm font-black text-mekong-navy uppercase tracking-widest mb-1">
                System Performance (Weekly)
              </h3>
              <p className="text-[10px] text-slate-400 font-medium uppercase tracking-wider">
                Salinity prediction accuracy vs. actual sensors.
              </p>
            </div>
            <div className="flex gap-4">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-mekong-teal" />{" "}
                <span className="text-[9px] font-black uppercase text-slate-400">
                  Actual
                </span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-mekong-navy" />{" "}
                <span className="text-[9px] font-black uppercase text-slate-400">
                  AI Prediction
                </span>
              </div>
            </div>
          </div>

          {/* Chart Grid Lines Mockup */}
          <div className="flex-1 border-b border-l border-slate-100 mt-8 mb-6 relative">
            <div className="absolute bottom-0 left-0 w-full h-[60%] border-t border-slate-50" />
            <div className="absolute bottom-0 left-0 w-full h-[30%] border-t border-slate-50" />
          </div>

          <div className="flex justify-between px-4 text-[9px] font-black text-slate-400 uppercase tracking-widest">
            <span>Mon</span>
            <span>Tue</span>
            <span>Wed</span>
            <span>Thu</span>
            <span>Fri</span>
            <span>Sat</span>
            <span>Sun</span>
          </div>
        </Card>

        {/* Density Map (5 cols) */}
        <Card
          variant="navy"
          className="col-span-12 lg:col-span-5 bg-[#00203F] text-white flex flex-col justify-between"
        >
          <div>
            <h3 className="text-sm font-black uppercase tracking-widest mb-1">
              Intervention Density Map
            </h3>
            <p className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">
              Concentration of AI interventions based on regional salinity
              pressure.
            </p>
          </div>

          {/* Grid Map Mockup */}
          <div className="grid grid-cols-10 gap-1 my-10 px-2">
            {Array.from({ length: 50 }).map((_, i) => {
              const opacity = Math.random();
              return (
                <div
                  key={i}
                  className="aspect-square rounded-sm transition-all duration-700 hover:ring-1 ring-mekong-cyan"
                  style={{
                    backgroundColor: `rgba(117, 231, 254, ${opacity > 0.3 ? opacity : 0.1})`,
                  }}
                />
              );
            })}
          </div>

          <div className="flex justify-between text-[9px] font-black text-slate-500 uppercase tracking-[0.2em] border-t border-white/5 pt-4">
            <span>Coastal Inlets</span>
            <span>Upper Delta</span>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default ActionLogs;
