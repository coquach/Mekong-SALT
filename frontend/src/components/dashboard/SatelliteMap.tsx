import { MapContainer, TileLayer, Marker, Popup, useMap } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { Plus, Minus, Navigation, Lock, Radio, Info } from "lucide-react";
import { renderToStaticMarkup } from "react-dom/server";

// --- DATA: VỊ TRÍ THẬT TẠI KHU VỰC TIỀN GIANG / BẾN TRE ---
const MAP_CENTER: [number, number] = [10.32, 106.45]; // Trung tâm vùng dự án

const STATIONS = [
  {
    id: "S-04",
    name: "Trạm Hai Tân (Main)",
    coord: [10.352, 106.365] as [number, number],
    status: "critical",
  },
  {
    id: "S-01",
    name: "Trạm Cửa Tiểu (Estuary)",
    coord: [10.26, 106.65] as [number, number],
    status: "warning",
  },
  {
    id: "S-08",
    name: "Trạm Hàm Luông",
    coord: [10.18, 106.52] as [number, number],
    status: "optimal",
  },
  {
    id: "S-12",
    name: "Trạm Mỹ Thuận Bridge",
    coord: [10.275, 105.955] as [number, number],
    status: "optimal",
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

// Helper tạo Icon chuyên nghiệp
const createCustomIcon = (icon: React.ReactNode, bgColor: string) => {
  const html = renderToStaticMarkup(
    <div
      className={`p-2 rounded-xl border-2 border-white shadow-2xl text-white transition-all hover:scale-125 ${bgColor}`}
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

const MapController = () => {
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
        onClick={() => map.setView(MAP_CENTER, 11)}
        className="w-10 h-10 bg-white rounded-xl shadow-xl flex items-center justify-center text-mekong-navy hover:bg-slate-50 border border-slate-100 mt-1 transition-all active:scale-90"
      >
        <Navigation size={18} className="rotate-45" />
      </button>
    </div>
  );
};

interface SatelliteMapProps {
  layers?: {
    heatmap?: boolean;
    stations?: boolean;
    gates?: boolean;
    prediction?: boolean;
  };
  zoom?: number;
  showControls?: boolean;
}

export const SatelliteMap = ({
  layers = { heatmap: false, stations: true, gates: true, prediction: false },
  zoom = 11,
  showControls = true,
}: SatelliteMapProps) => {
  return (
    <div className="w-full h-full relative group">
      <MapContainer
        center={MAP_CENTER}
        zoom={zoom}
        scrollWheelZoom={false}
        className="w-full h-full z-0"
        zoomControl={false}
      >
        <TileLayer
          url="https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}"
          attribution="&copy; Google Earth"
        />

        {/* RENDER STATIONS */}
        {layers.stations &&
          STATIONS.map((s) => (
            <Marker
              key={s.id}
              position={s.coord}
              icon={createCustomIcon(
                <Radio size={18} />,
                s.status === "critical"
                  ? "bg-mekong-critical"
                  : s.status === "warning"
                    ? "bg-mekong-warning"
                    : "bg-mekong-teal",
              )}
            >
              <Popup className="custom-popup">
                <div className="p-2 space-y-1">
                  <h4 className="font-black text-mekong-navy text-xs uppercase">
                    {s.name}
                  </h4>
                  <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">
                    Type: Salinity Sensor
                  </p>
                  <div className="pt-1 flex items-center gap-1 text-[10px] font-black text-mekong-teal uppercase">
                    <Info size={12} /> Click for Deep Dive
                  </div>
                </div>
              </Popup>
            </Marker>
          ))}

        {/* RENDER GATES */}
        {layers.gates &&
          GATES.map((g) => (
            <Marker
              key={g.id}
              position={g.coord}
              icon={createCustomIcon(<Lock size={18} />, "bg-mekong-navy")}
            >
              <Popup>
                <div className="p-2">
                  <h4 className="font-black text-mekong-navy text-xs uppercase">
                    {g.name}
                  </h4>
                  <p
                    className={`text-[10px] font-black uppercase mt-1 ${g.state === "Closed" ? "text-mekong-critical" : "text-mekong-teal"}`}
                  >
                    State: {g.state}
                  </p>
                </div>
              </Popup>
            </Marker>
          ))}

        {showControls && <MapController />}
      </MapContainer>

      {/* Overlay mờ nhẹ toàn bản đồ để map chìm xuống dưới UI Dashboard */}
      <div className="absolute inset-0 pointer-events-none bg-mekong-navy/10 z-[1] transition-opacity group-hover:opacity-0" />
    </div>
  );
};
