import { MapContainer, TileLayer, useMap } from "react-leaflet";
import { Plus, Minus, Navigation } from "lucide-react";
import "leaflet/dist/leaflet.css";

// 1. Component điều khiển nội bộ
const MapController = () => {
  const map = useMap(); // Lấy đối tượng map thật

  const handleZoomIn = () => map.zoomIn();
  const handleZoomOut = () => map.zoomOut();
  const handleRecenter = () => map.setView([10.3, 106.35], 10); // Quay về tọa độ gốc

  return (
    <div className="absolute bottom-6 right-6 z-[1000] flex flex-col gap-3">
      {/* Nút Phóng to */}
      <button
        onClick={handleZoomIn}
        className="w-12 h-12 bg-white rounded-2xl shadow-xl flex items-center justify-center text-mekong-navy hover:bg-slate-50 transition-all active:scale-90 border border-slate-100"
      >
        <Plus size={24} strokeWidth={2.5} />
      </button>

      {/* Nút Thu nhỏ */}
      <button
        onClick={handleZoomOut}
        className="w-12 h-12 bg-white rounded-2xl shadow-xl flex items-center justify-center text-mekong-navy hover:bg-slate-50 transition-all active:scale-90 border border-slate-100"
      >
        <Minus size={24} strokeWidth={2.5} />
      </button>

      {/* Nút Định vị (Navigation) */}
      <button
        onClick={handleRecenter}
        className="w-12 h-12 bg-white rounded-2xl shadow-xl flex items-center justify-center text-mekong-navy hover:bg-slate-50 transition-all active:scale-90 border border-slate-100 mt-2"
      >
        <Navigation size={22} strokeWidth={2.5} className="rotate-45" />
      </button>
    </div>
  );
};

// 2. Component Map chính
export const SatelliteMap = () => {
  const position: [number, number] = [10.3, 106.35];

  return (
    <div className="w-full h-full relative z-0">
      <MapContainer
        center={position}
        zoom={10}
        scrollWheelZoom={true}
        className="w-full h-full rounded-[36px]"
        zoomControl={false} // Tắt nút mặc định của Leaflet
      >
        <TileLayer
          url="https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}"
          attribution="&copy; Google Maps"
        />

        {/* CHÈN BỘ ĐIỀU KHIỂN VÀO ĐÂY */}
        <MapController />
      </MapContainer>
    </div>
  );
};
