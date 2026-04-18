import { Maximize2, MousePointer2 } from "lucide-react";
import { useMemo } from "react";
import { Card } from "../ui/Card";
import type { MapStation } from "./SatelliteMap";
import { formatNumber } from "../../lib/format";

type HotspotIntensity = "critical" | "warning";

type HotspotPoint = {
  stationId: string;
  stationCode: string;
  label: string;
  intensity: HotspotIntensity;
  salinityGl: number | null;
  summary: string;
  selected: boolean;
  x: number;
  y: number;
};

type HotspotSlot = {
  x: number;
  y: number;
};

const HOTSPOT_LAYOUT_BY_CODE: Record<string, HotspotSlot> = {
  "GOCONG-01": { x: 30, y: 36 },
  "GOCONG-02": { x: 54, y: 58 },
};

const HOTSPOT_LAYOUT_FALLBACK: HotspotSlot[] = [
  { x: 24, y: 30 },
  { x: 40, y: 44 },
  { x: 58, y: 34 },
  { x: 72, y: 52 },
  { x: 46, y: 68 },
  { x: 78, y: 28 },
  { x: 18, y: 58 },
  { x: 66, y: 76 },
];

interface HotspotsMapProps {
  stations: MapStation[];
  regionLabel?: string;
  title?: string;
  selectedStationId?: string | null;
  onOpenFullMap?: () => void;
}

function toNumber(value: unknown): number | null {
  if (typeof value === "number" && Number.isFinite(value)) {
    return value;
  }

  if (typeof value === "string") {
    const parsedValue = Number.parseFloat(value);
    return Number.isFinite(parsedValue) ? parsedValue : null;
  }

  return null;
}

function getIntensity(salinityGl: number | null): HotspotIntensity {
  if (salinityGl !== null && salinityGl >= 2) {
    return "critical";
  }

  return "warning";
}

function getHotspotSummary(station: MapStation, salinityGl: number | null): string {
  const role = station.stationMetadata?.operational_role;
  const notes = station.stationMetadata?.notes;
  const salinityText = salinityGl === null ? "không có số liệu" : `${salinityGl.toFixed(2)} g/L`;

  if (notes) {
    return notes;
  }

  if (role) {
    return `${role} | ${salinityText}`;
  }

  return salinityText;
}

function getHotspotLabel(station: MapStation): string {
  return station.stationMetadata?.marker?.label ?? station.name;
}

function getHotspotSlot(station: MapStation, fallbackIndex: number): HotspotSlot {
  return HOTSPOT_LAYOUT_BY_CODE[station.code] ?? HOTSPOT_LAYOUT_FALLBACK[fallbackIndex % HOTSPOT_LAYOUT_FALLBACK.length];
}

function buildHotspots(stations: MapStation[], selectedStationId?: string | null): HotspotPoint[] {
  return stations
    .slice()
    .sort((left, right) => left.code.localeCompare(right.code, "vi"))
    .map((station, index) => {
      const salinityGl = toNumber(station.latestSalinityGl);
      const intensity = getIntensity(salinityGl);
      const slot = getHotspotSlot(station, index);

      return {
        stationId: station.id,
        stationCode: station.code,
        label: getHotspotLabel(station),
        intensity,
        salinityGl,
        summary: getHotspotSummary(station, salinityGl),
        selected: selectedStationId === station.id,
        x: slot.x,
        y: slot.y,
      };
    })
    .filter(({ salinityGl }) => salinityGl !== null)
    .sort((left, right) => {
      if (left.selected !== right.selected) {
        return left.selected ? 1 : -1;
      }

      if (left.intensity !== right.intensity) {
        return left.intensity === "critical" ? 1 : -1;
      }

      return (right.salinityGl ?? 0) - (left.salinityGl ?? 0);
    });
}

function HotspotGlyph({ intensity, selected }: { intensity: HotspotIntensity; selected: boolean }) {
  const fillClassName = intensity === "critical" ? "fill-mekong-critical" : "fill-mekong-warning";
  const ringClassName = intensity === "critical" ? "stroke-mekong-critical" : "stroke-mekong-warning";

  return (
    <g>
      <circle cx="0" cy="0" r="7" className={`${fillClassName} opacity-20 animate-ping`} />
      <circle cx="0" cy="0" r="3.4" className={`${fillClassName} ${selected ? "opacity-100" : "opacity-90"}`} />
      <circle cx="0" cy="0" r={selected ? 6.5 : 5.5} className={`fill-none ${ringClassName} ${selected ? "stroke-[1.6]" : "stroke-[1.1]"}`} />
    </g>
  );
}

export function HotspotsMap({
  stations,
  regionLabel = "Tiền Giang - Bến Tre Region",
  title = "Hotspot salinity map",
  selectedStationId,
  onOpenFullMap,
}: HotspotsMapProps) {
  const hotspots = useMemo(() => buildHotspots(stations, selectedStationId), [stations, selectedStationId]);

  const hotspotCount = hotspots.length;
  const criticalCount = hotspots.filter((hotspot) => hotspot.intensity === "critical").length;

  return (
    <Card
      variant="white"
      padding="none"
      className="h-112.5 relative overflow-hidden group border-2 border-transparent hover:border-mekong-cyan/20 transition-all duration-500"
    >
      <div className="absolute inset-0 bg-slate-900">
        <img
          src="https://images.unsplash.com/photo-1582103287241-2762adba6c36?auto=format&fit=crop&q=80&w=2000"
          alt="Mekong Delta Satellite"
          className="w-full h-full object-cover opacity-80 mix-blend-luminosity group-hover:mix-blend-normal group-hover:opacity-100 transition-all duration-700"
        />
        <div className="absolute inset-0 bg-linear-to-t from-mekong-navy/40 to-transparent pointer-events-none" />
      </div>

      <div className="absolute top-6 left-6 z-30 animate-in fade-in slide-in-from-left-4 duration-700">
        <div className="bg-white/90 backdrop-blur-xl p-6 rounded-3xl shadow-2xl border border-white/40 ring-1 ring-black/5">
          <h3 className="text-lg font-black text-mekong-navy leading-none tracking-tighter mb-1">{title}</h3>
          <p className="text-[10px] font-black text-mekong-slate uppercase tracking-[0.2em] opacity-80">{regionLabel}</p>
          <div className="flex items-center gap-4 mt-4 pt-4 border-t border-slate-100">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-mekong-critical rounded-full" />
              <span className="text-[9px] font-bold text-mekong-slate uppercase tracking-wider">Critical</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-mekong-warning rounded-full" />
              <span className="text-[9px] font-bold text-mekong-slate uppercase tracking-wider">Monitoring</span>
            </div>
          </div>
        </div>
      </div>

      <div className="absolute top-6 right-6 z-30 bg-mekong-navy/90 backdrop-blur-md text-white rounded-shell px-4 py-3 shadow-2xl border border-white/10">
        <p className="text-[9px] font-black uppercase tracking-[0.2em] text-white/60">Hotspots</p>
        <p className="mt-1 text-xl font-black tracking-tighter leading-none">{hotspotCount}</p>
        <p className="mt-1 text-[9px] font-bold uppercase tracking-[0.18em] text-white/60">{criticalCount} critical</p>
      </div>

      <svg
        viewBox="0 0 100 100"
        preserveAspectRatio="none"
        className="absolute inset-0 h-full w-full z-20"
        aria-label="Hotspot map markers"
        role="img"
      >
        {hotspots.map((hotspot) => (
          <g
            key={hotspot.stationId}
            transform={`translate(${hotspot.x} ${hotspot.y})`}
            className="cursor-pointer"
            aria-label={`${hotspot.label}, ${hotspot.summary}`}
          >
            <HotspotGlyph intensity={hotspot.intensity} selected={hotspot.selected} />
            <text x="8" y="-2" className="fill-white text-[3px] font-black uppercase tracking-[0.18em] drop-shadow-lg">
              {hotspot.label}
            </text>
            <text x="8" y="2.8" className="fill-slate-200 text-[2.4px] font-bold drop-shadow-lg">
              {hotspot.stationCode} · {formatNumber(hotspot.salinityGl, 2)} g/L
            </text>
          </g>
        ))}
      </svg>

      <div className="absolute inset-0 pointer-events-none overflow-hidden opacity-20">
        <div className="w-full h-20 bg-linear-to-b from-transparent via-mekong-cyan/40 to-transparent absolute top-0 animate-[scan_4s_linear_infinite]" />
      </div>

      <div className="absolute bottom-6 left-6 flex items-center gap-2 text-white/60 bg-black/20 backdrop-blur-sm px-3 py-1.5 rounded-full text-[9px] font-bold uppercase tracking-widest border border-white/10 pointer-events-none z-30">
        <MousePointer2 size={12} />
        Hotspot derived from station salinity
      </div>

      {onOpenFullMap ? (
        <button
          type="button"
          className="absolute bottom-6 right-6 z-30 bg-mekong-navy text-white px-6 py-3 rounded-xl font-black text-xs flex items-center gap-3 shadow-2xl hover:bg-mekong-teal hover:scale-105 active:scale-95 transition-all duration-300 group"
          onClick={onOpenFullMap}
          aria-label="Open full hotspot map"
        >
          <span>OPEN FULL MAP</span>
          <Maximize2 size={16} className="group-hover:rotate-90 transition-transform duration-500" />
        </button>
      ) : null}
    </Card>
  );
}
