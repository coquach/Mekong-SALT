import {
  Droplets,
  Gauge,
  Lock,
  Minus,
  Navigation,
  Plus,
  Radio,
  Unlock,
  Waves,
  Wind,
} from "lucide-react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import type { ReactElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { MapContainer, Marker, Popup, TileLayer, useMap } from "react-leaflet";

import type { GateRead, StationMetadata } from "../../lib/api/telemetry";

const DEFAULT_MAP_CENTER: [number, number] = [10.32, 106.45];

export interface MapStation {
  id: string;
  code: string;
  name: string;
  latitude: number;
  longitude: number;
  status?: string;
  stationType?: string;
  stationMetadata?: StationMetadata | null;
  riskLevel?: string | null;
  latestSalinityGl?: number | null;
}

export interface MapGate {
  id: string;
  code: string;
  name: string;
  latitude: number;
  longitude: number;
  gateType: string;
  status: GateRead["status"];
  gateMetadata?: GateRead["gate_metadata"];
  locationDescription?: string | null;
  lastOperatedAt?: string | null;
  station?: GateRead["station"];
}

interface SatelliteMapProps {
  layers?: {
    heatmap?: boolean;
    stations?: boolean;
    gates?: boolean;
    prediction?: boolean;
  };
  zoom?: number;
  showControls?: boolean;
  stations?: MapStation[];
  gates?: MapGate[];
  selectedStationId?: string | null;
  onSelectStation?: (stationId: string) => void;
}

const createCustomIcon = (icon: ReactElement, bgColor: string, selected = false) => {
  const html = renderToStaticMarkup(
    <div
      className={`p-2 rounded-xl border-2 shadow-2xl text-white transition-all ${
        selected ? "border-mekong-cyan scale-110 ring-4 ring-mekong-cyan/30" : "border-white"
      } ${bgColor}`}
    >
      {icon}
    </div>,
  );
  return L.divIcon({
    html,
    className: "custom-map-icon",
    iconSize: [38, 38],
    iconAnchor: [19, 19],
  });
};

type StationIconName = "droplets" | "waves" | "wind" | "gauge" | "radio";

const STATION_ICON_MAP: Record<StationIconName, ReactElement> = {
  droplets: <Droplets size={18} />,
  waves: <Waves size={18} />,
  wind: <Wind size={18} />,
  gauge: <Gauge size={18} />,
  radio: <Radio size={18} />,
};

const STATION_COLOR_MAP: Record<string, string> = {
  teal: "bg-mekong-teal",
  amber: "bg-mekong-warning",
  blue: "bg-sky-500",
  red: "bg-mekong-critical",
  navy: "bg-mekong-navy",
};

function getStationMetadataValue(station: MapStation, key: string): string | null {
  const metadata = station.stationMetadata;
  if (!metadata || typeof metadata !== "object") {
    return null;
  }
  const value = metadata[key];
  return typeof value === "string" ? value : null;
}

function getStationMetadataNumber(station: MapStation, key: string): number | null {
  const metadata = station.stationMetadata;
  if (!metadata || typeof metadata !== "object") {
    return null;
  }
  const value = metadata[key];
  if (typeof value === "number") {
    return Number.isFinite(value) ? value : null;
  }
  if (typeof value === "string") {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : null;
  }
  return null;
}

function resolveStationLabel(station: MapStation): string {
  return (
    getStationMetadataValue(station, "display_name") ??
    getStationMetadataValue(station, "displayName") ??
    station.name
  );
}

function resolveStationTagline(station: MapStation): string {
  return (
    station.stationMetadata?.marker?.label ??
    getStationMetadataValue(station, "operational_role") ??
    "Trạm quan trắc"
  );
}

function formatStationPackage(station: MapStation): string {
  const sensorPackage = station.stationMetadata?.sensor_package;
  if (!Array.isArray(sensorPackage) || sensorPackage.length === 0) {
    return "--";
  }
  return sensorPackage.join(" • ");
}

function getStationMetaDisplay(station: MapStation, key: string, fallback = "--"): string {
  return getStationMetadataValue(station, key) ?? fallback;
}

function toNumber(value: string | number | null | undefined): number | null {
  if (value === null || value === undefined) {
    return null;
  }
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function getGateMetadataValue(gate: MapGate, key: string): string | null {
  const metadata = gate.gateMetadata;
  if (!metadata || typeof metadata !== "object") {
    return null;
  }
  const value = metadata[key];
  return typeof value === "string" ? value : null;
}

function resolveGateLabel(gate: MapGate): string {
  return getGateMetadataValue(gate, "display_name") ?? gate.name;
}

function resolveGateTagline(gate: MapGate): string {
  return (
    gate.gateMetadata?.marker?.label ??
    getGateMetadataValue(gate, "operational_role") ??
    gate.gateType ??
    "Cống"
  );
}

function resolveGateColor(gate: MapGate): string {
  const markerColor = gate.gateMetadata?.marker?.color;
  if (typeof markerColor === "string") {
    return STATION_COLOR_MAP[markerColor] ?? "bg-mekong-navy";
  }

  if (gate.status === "open") {
    return "bg-mekong-teal";
  }
  if (gate.status === "transitioning") {
    return "bg-mekong-warning";
  }
  if (gate.status === "maintenance") {
    return "bg-slate-500";
  }
  return "bg-mekong-navy";
}

function resolveGateStatusLabel(status: MapGate["status"]): string {
  if (status === "open") {
    return "Đang mở";
  }
  if (status === "transitioning") {
    return "Đang chuyển trạng thái";
  }
  if (status === "maintenance") {
    return "Bảo trì";
  }
  return "Đang đóng";
}

function resolveGateIcon(gate: MapGate): ReactElement {
  return gate.status === "open" ? <Unlock size={18} /> : <Lock size={18} />;
}

function formatGateStationLink(gate: MapGate): string {
  if (!gate.station) {
    return "--";
  }
  return `${gate.station.code} · ${gate.station.name}`;
}

function resolveStationIconName(station: MapStation): StationIconName {
  const marker = station.stationMetadata?.marker;
  if (marker?.icon === "droplets" || marker?.icon === "waves" || marker?.icon === "wind" || marker?.icon === "gauge" || marker?.icon === "radio") {
    return marker.icon;
  }

  const stationType = station.stationType?.toLowerCase() ?? "";
  if (stationType.includes("wind") || stationType.includes("meteor")) {
    return "wind";
  }
  if (stationType.includes("level") || stationType.includes("tide")) {
    return "waves";
  }
  if (stationType.includes("flow") || stationType.includes("pressure")) {
    return "gauge";
  }
  if (stationType.includes("salinity")) {
    return "droplets";
  }
  return "radio";
}

function resolveStationColor(station: MapStation): string {
  const marker = station.stationMetadata?.marker;
  if (typeof marker?.color === "string") {
    return STATION_COLOR_MAP[marker.color] ?? "bg-mekong-teal";
  }

  const risk = station.riskLevel?.toLowerCase();
  if (risk === "critical" || risk === "danger") {
    return "bg-mekong-critical";
  }
  if (risk === "warning") {
    return "bg-mekong-warning";
  }
  if (station.latestSalinityGl !== null && station.latestSalinityGl !== undefined) {
    if (station.latestSalinityGl >= 2.0) {
      return "bg-mekong-critical";
    }
    if (station.latestSalinityGl >= 1.0) {
      return "bg-mekong-warning";
    }
  }
  return "bg-mekong-teal";
}

function MapController() {
  const map = useMap();
  return (
    <div className="absolute bottom-6 right-6 z-1000 flex flex-col gap-2">
      <button
        onClick={() => map.zoomIn()}
        title="Phóng to bản đồ"
        aria-label="Phóng to bản đồ"
        className="w-10 h-10 bg-white rounded-xl shadow-xl flex items-center justify-center text-mekong-navy hover:bg-slate-50 border border-slate-100 transition-all active:scale-90"
      >
        <Plus size={20} />
      </button>
      <button
        onClick={() => map.zoomOut()}
        title="Thu nhỏ bản đồ"
        aria-label="Thu nhỏ bản đồ"
        className="w-10 h-10 bg-white rounded-xl shadow-xl flex items-center justify-center text-mekong-navy hover:bg-slate-50 border border-slate-100 transition-all active:scale-90"
      >
        <Minus size={20} />
      </button>
      <button
        onClick={() => map.setView(DEFAULT_MAP_CENTER, 11)}
        title="Đưa bản đồ về trung tâm"
        aria-label="Đưa bản đồ về trung tâm"
        className="w-10 h-10 bg-white rounded-xl shadow-xl flex items-center justify-center text-mekong-navy hover:bg-slate-50 border border-slate-100 mt-1 transition-all active:scale-90"
      >
        <Navigation size={18} className="rotate-45" />
      </button>
    </div>
  );
}

export function SatelliteMap({
  layers = { heatmap: false, stations: true, gates: true, prediction: false },
  zoom = 11,
  showControls = true,
  stations,
  gates,
  selectedStationId = null,
  onSelectStation,
}: SatelliteMapProps) {
  const stationsToRender = stations ?? [];
  const gatesToRender = gates ?? [];
  const validStationsToRender = stationsToRender.filter(
    (station) => Number.isFinite(station.latitude) && Number.isFinite(station.longitude),
  );
  const validGatesToRender = gatesToRender.filter(
    (gate) => Number.isFinite(gate.latitude) && Number.isFinite(gate.longitude),
  );

  return (
    <div className="w-full h-full relative group">
      <MapContainer
        center={DEFAULT_MAP_CENTER}
        zoom={zoom}
        scrollWheelZoom={false}
        className="w-full h-full z-0"
        zoomControl={false}
      >
        <TileLayer
          url="https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}"
          attribution="&copy; Google Earth"
        />

        {layers.stations &&
          validStationsToRender.map((station) => (
            <Marker
              key={station.id}
              position={[station.latitude, station.longitude]}
              icon={createCustomIcon(
                STATION_ICON_MAP[resolveStationIconName(station)],
                resolveStationColor(station),
                selectedStationId === station.id,
              )}
              eventHandlers={
                onSelectStation
                  ? {
                      click: () => onSelectStation(station.id),
                    }
                  : undefined
              }
            >
              <Popup className="custom-popup">
                <div className="p-2 space-y-2 min-w-55">
                  <div className="space-y-0.5">
                    <h4 className="font-black text-mekong-navy text-xs uppercase">
                      {resolveStationLabel(station)}
                    </h4>
                    <p className="text-[10px] font-black text-mekong-teal uppercase tracking-widest">
                      {resolveStationTagline(station)}
                    </p>
                  </div>

                  <div className="grid grid-cols-2 gap-x-3 gap-y-1 text-[10px] font-bold text-slate-500 uppercase tracking-widest">
                    <p>Code: {station.code}</p>
                    <p>Vai trò: {getStationMetaDisplay(station, "operational_role")}</p>
                    <p>Chủ quản: {getStationMetaDisplay(station, "owner")}</p>
                    <p>Vận hành: {getStationMetaDisplay(station, "operator")}</p>
                    <p>Phạm vi: {getStationMetadataNumber(station, "coverage_radius_km") ?? "--"} km</p>
                    <p>Chu kỳ: {getStationMetadataNumber(station, "calibration_cycle_days") ?? "--"} ngày</p>
                  </div>

                  <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">
                    Gói cảm biến: {formatStationPackage(station)}
                  </p>
                  <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">
                    Nguồn nước: {getStationMetaDisplay(station, "reference_water_body")}
                  </p>
                  <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">
                    Salinity: {station.latestSalinityGl ?? "--"} g/L
                  </p>
                </div>
              </Popup>
            </Marker>
          ))}

        {layers.gates &&
          validGatesToRender.map((gate) => {
            const latitude = toNumber(gate.latitude);
            const longitude = toNumber(gate.longitude);
            if (latitude === null || longitude === null) {
              return null;
            }

            return (
              <Marker
                key={gate.id}
                position={[latitude, longitude]}
                icon={createCustomIcon(resolveGateIcon(gate), resolveGateColor(gate))}
              >
                <Popup>
                  <div className="p-2 space-y-2 min-w-55">
                    <div className="space-y-0.5">
                      <h4 className="font-black text-mekong-navy text-xs uppercase">{resolveGateLabel(gate)}</h4>
                      <p className="text-[10px] font-black text-mekong-teal uppercase tracking-widest">
                        {resolveGateTagline(gate)}
                      </p>
                    </div>
                    <div className="grid grid-cols-2 gap-x-3 gap-y-1 text-[10px] font-bold text-slate-500 uppercase tracking-widest">
                      <p>Code: {gate.code}</p>
                      <p>Trạng thái: {resolveGateStatusLabel(gate.status)}</p>
                      <p>Liên kết: {formatGateStationLink(gate)}</p>
                      <p>Loại cống: {gate.gateType ?? "--"}</p>
                    </div>
                    {gate.locationDescription ? (
                      <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">
                        Vị trí: {gate.locationDescription}
                      </p>
                    ) : null}
                    <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">
                      Điều khiển: {getGateMetadataValue(gate, "controller") ?? "--"}
                    </p>
                    <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">
                      Kênh điều khiển: {getGateMetadataValue(gate, "control_channel") ?? "--"}
                    </p>
                    <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">
                      Lần vận hành gần nhất: {gate.lastOperatedAt ?? "--"}
                    </p>
                  </div>
                </Popup>
              </Marker>
            );
          })}

        {showControls ? <MapController /> : null}
      </MapContainer>

      <div className="absolute inset-0 pointer-events-none bg-mekong-navy/10 z-1 transition-opacity group-hover:opacity-0" />
    </div>
  );
}
