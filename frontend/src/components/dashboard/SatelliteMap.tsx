import { Lock, Minus, Navigation, Plus, Radio } from "lucide-react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import type { ReactElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { MapContainer, Marker, Popup, TileLayer, useMap } from "react-leaflet";

const DEFAULT_MAP_CENTER: [number, number] = [10.32, 106.45];

const FALLBACK_STATIONS: MapStation[] = [
  {
    id: "S-04",
    code: "S-04",
    name: "Trạm Hai Tân (Main)",
    latitude: 10.352,
    longitude: 106.365,
    riskLevel: "critical",
    latestSalinityGl: 1.9,
  },
  {
    id: "S-01",
    code: "S-01",
    name: "Trạm Cửa Tiểu",
    latitude: 10.26,
    longitude: 106.65,
    riskLevel: "warning",
    latestSalinityGl: 1.2,
  },
  {
    id: "S-08",
    code: "S-08",
    name: "Trạm Hàm Luông",
    latitude: 10.18,
    longitude: 106.52,
    riskLevel: "safe",
    latestSalinityGl: 0.5,
  },
];

const GATES = [
  {
    id: "G-04",
    name: "Cống Hòa Định",
    coord: [10.362, 106.345] as [number, number],
    state: "Closed",
  },
  {
    id: "G-09",
    name: "Cống Xuân Hòa",
    coord: [10.315, 106.48] as [number, number],
    state: "Closed",
  },
  {
    id: "G-02",
    name: "Cống Thới Tân",
    coord: [10.38, 106.31] as [number, number],
    state: "Open",
  },
  {
    id: "G-15",
    name: "Cống Phú Đông",
    coord: [10.25, 106.61] as [number, number],
    state: "Closed",
  },
];

export interface MapStation {
  id: string;
  code: string;
  name: string;
  latitude: number;
  longitude: number;
  status?: string;
  riskLevel?: string | null;
  latestSalinityGl?: number | null;
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

function resolveStationColor(station: MapStation): string {
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
    <div className="absolute bottom-6 right-6 z-[1000] flex flex-col gap-2">
      <button
        onClick={() => map.zoomIn()}
        className="w-10 h-10 bg-white rounded-xl shadow-xl flex items-center justify-center text-mekong-navy hover:bg-slate-50 border border-slate-100 transition-all active:scale-90"
      >
        <Plus size={20} />
      </button>
      <button
        onClick={() => map.zoomOut()}
        className="w-10 h-10 bg-white rounded-xl shadow-xl flex items-center justify-center text-mekong-navy hover:bg-slate-50 border border-slate-100 transition-all active:scale-90"
      >
        <Minus size={20} />
      </button>
      <button
        onClick={() => map.setView(DEFAULT_MAP_CENTER, 11)}
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
  selectedStationId = null,
  onSelectStation,
}: SatelliteMapProps) {
  const stationsToRender = stations && stations.length > 0 ? stations : FALLBACK_STATIONS;

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
          stationsToRender.map((station) => (
            <Marker
              key={station.id}
              position={[station.latitude, station.longitude]}
              icon={createCustomIcon(
                <Radio size={18} />,
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
                <div className="p-2 space-y-1">
                  <h4 className="font-black text-mekong-navy text-xs uppercase">{station.name}</h4>
                  <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">
                    Code: {station.code}
                  </p>
                  <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">
                    Salinity: {station.latestSalinityGl ?? "--"} g/L
                  </p>
                </div>
              </Popup>
            </Marker>
          ))}

        {layers.gates &&
          GATES.map((gate) => (
            <Marker key={gate.id} position={gate.coord} icon={createCustomIcon(<Lock size={18} />, "bg-mekong-navy")}>
              <Popup>
                <div className="p-2">
                  <h4 className="font-black text-mekong-navy text-xs uppercase">{gate.name}</h4>
                  <p
                    className={`text-[10px] font-black uppercase mt-1 ${
                      gate.state === "Closed" ? "text-mekong-critical" : "text-mekong-teal"
                    }`}
                  >
                    State: {gate.state}
                  </p>
                </div>
              </Popup>
            </Marker>
          ))}

        {showControls ? <MapController /> : null}
      </MapContainer>

      <div className="absolute inset-0 pointer-events-none bg-mekong-navy/10 z-[1] transition-opacity group-hover:opacity-0" />
    </div>
  );
}
