import { useEffect, useMemo, useRef, useState } from "react";
import {
  AlertTriangle,
  Eye,
  Layers,
  MapPin,
  Navigation,
  ShieldCheck,
  TrendingUp,
} from "lucide-react";
import { useNavigate } from "react-router-dom";

import { SatelliteMap, type MapStation } from "../components/dashboard/SatelliteMap";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { getLatestReadings, type SensorReading } from "../lib/api/dashboard";
import {
  getIncidents,
  getLatestRisk,
  getStations,
  type IncidentRead,
  type SensorStationRead,
} from "../lib/api/telemetry";
import { ApiError, type ErrorResponse } from "../lib/api/types";

type InteractiveMapState = {
  loading: boolean;
  error: string | null;
  stations: SensorStationRead[];
  latestReadings: SensorReading[];
  incidents: IncidentRead[];
  selectedStationId: string | null;
  selectedRisk: Awaited<ReturnType<typeof getLatestRisk>> | null;
};

function parseApiError(error: unknown): string {
  if (error instanceof ApiError) {
    return error.message;
  }
  if (error && typeof error === "object") {
    const maybeError = error as ErrorResponse;
    if (typeof maybeError.message === "string") {
      return maybeError.message;
    }
  }
  return "Không tải được dữ liệu bản đồ.";
}

function toNumber(value: string | number): number {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : 0;
}

function formatValue(value: string | number | null | undefined, digits = 2): string {
  if (value === null || value === undefined) {
    return "--";
  }
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) {
    return "--";
  }
  return numeric.toFixed(digits);
}

function formatRiskLabel(riskLevel: string | null | undefined): string {
  if (!riskLevel) {
    return "unknown";
  }
  return riskLevel.toUpperCase();
}

export function InteractiveMap() {
  const [layers, setLayers] = useState({
    heatmap: true,
    stations: true,
    gates: true,
    prediction: true,
  });
  const [state, setState] = useState<InteractiveMapState>({
    loading: true,
    error: null,
    stations: [],
    latestReadings: [],
    incidents: [],
    selectedStationId: null,
    selectedRisk: null,
  });
  const navigate = useNavigate();
  const riskRequestIdRef = useRef(0);
  const riskAbortControllerRef = useRef<AbortController | null>(null);

  useEffect(() => {
    const abortController = new AbortController();

    const loadData = async () => {
      setState((previous) => ({ ...previous, loading: true, error: null }));
      try {
        const [stations, latestReadings, incidents] = await Promise.all([
          getStations({ limit: 300 }, abortController.signal),
          getLatestReadings({ limit: 500 }, abortController.signal),
          getIncidents({ limit: 30 }, abortController.signal),
        ]);

        const selectedStationId = stations.items[0]?.id ?? null;
        let selectedRisk = null;
        if (stations.items[0]) {
          try {
            selectedRisk = await getLatestRisk(
              { station_code: stations.items[0].code },
              abortController.signal,
            );
          } catch (error) {
            if (!(error instanceof ApiError && error.statusCode === 404)) {
              throw error;
            }
          }
        }

        setState({
          loading: false,
          error: null,
          stations: stations.items,
          latestReadings: latestReadings.items,
          incidents: incidents.items,
          selectedStationId,
          selectedRisk,
        });
      } catch (error) {
        if (abortController.signal.aborted) {
          return;
        }
        setState((previous) => ({
          ...previous,
          loading: false,
          error: parseApiError(error),
        }));
      }
    };

    void loadData();
    return () => {
      abortController.abort();
      riskAbortControllerRef.current?.abort();
    };
  }, []);

  const readingsByStationId = useMemo(() => {
    const map = new Map<string, SensorReading>();
    state.latestReadings.forEach((reading) => {
      map.set(reading.station_id, reading);
    });
    return map;
  }, [state.latestReadings]);

  const mapStations = useMemo<MapStation[]>(
    () =>
      state.stations.map((station) => {
        const reading = readingsByStationId.get(station.id);
        return {
          id: station.id,
          code: station.code,
          name: station.name,
          latitude: toNumber(station.latitude),
          longitude: toNumber(station.longitude),
          status: station.status,
          latestSalinityGl:
            reading?.salinity_gl !== null && reading?.salinity_gl !== undefined
              ? Number(reading.salinity_gl)
              : null,
          riskLevel: state.selectedRisk?.assessment.station_id === station.id
            ? state.selectedRisk.assessment.risk_level
            : null,
        };
      }),
    [state.stations, readingsByStationId, state.selectedRisk],
  );

  const selectedStation = useMemo(
    () => state.stations.find((station) => station.id === state.selectedStationId) ?? null,
    [state.stations, state.selectedStationId],
  );

  const selectedReading = useMemo(
    () => (selectedStation ? readingsByStationId.get(selectedStation.id) ?? null : null),
    [selectedStation, readingsByStationId],
  );

  const handleSelectStation = async (stationId: string) => {
    const station = state.stations.find((item) => item.id === stationId);
    setState((previous) => ({ ...previous, selectedStationId: stationId }));
    if (!station) {
      return;
    }
    riskAbortControllerRef.current?.abort();
    const riskAbortController = new AbortController();
    riskAbortControllerRef.current = riskAbortController;
    const requestId = ++riskRequestIdRef.current;

    try {
      const risk = await getLatestRisk(
        { station_code: station.code },
        riskAbortController.signal,
      );
      if (requestId !== riskRequestIdRef.current || riskAbortController.signal.aborted) {
        return;
      }
      setState((previous) => ({ ...previous, selectedRisk: risk, error: null }));
    } catch (error) {
      if (requestId !== riskRequestIdRef.current || riskAbortController.signal.aborted) {
        return;
      }
      if (error instanceof ApiError && error.statusCode === 404) {
        setState((previous) => ({ ...previous, selectedRisk: null }));
        return;
      }
      setState((previous) => ({ ...previous, error: parseApiError(error) }));
    }
  };

  const criticalIncidents = useMemo(
    () => state.incidents.filter((item) => item.severity === "critical" && item.status !== "closed"),
    [state.incidents],
  );

  return (
    <div className="space-y-6">
      {state.error ? (
        <div className="rounded-2xl border border-red-200 bg-red-50 px-5 py-3 text-sm font-bold text-red-700">
          {state.error}
        </div>
      ) : null}

      <div className="relative w-full h-[calc(100vh-220px)] rounded-[48px] overflow-hidden bg-slate-900 shadow-2xl border border-white/10">
        <SatelliteMap
          layers={layers}
          zoom={11}
          showControls
          stations={mapStations}
          selectedStationId={state.selectedStationId}
          onSelectStation={(stationId) => {
            void handleSelectStation(stationId);
          }}
        />

        <div className="absolute top-8 left-8 z-20 space-y-4 w-80">
          <Card variant="glass" className="p-6 rounded-[32px] border-white/40 shadow-glass backdrop-blur-2xl">
            <div className="flex items-center gap-3 mb-6 border-b border-mekong-navy/10 pb-4">
              <Layers size={18} className="text-mekong-navy" />
              <h3 className="text-sm font-black text-mekong-navy uppercase tracking-widest">Lớp nhận thức AI</h3>
            </div>
            <div className="space-y-1">
              {[
                { key: "heatmap", label: "Bản đồ nhiệt mặn", icon: Eye },
                { key: "stations", label: "Trạm cảm biến IoT", icon: MapPin },
                { key: "gates", label: "Hạ tầng cống PLC", icon: ShieldCheck },
                { key: "prediction", label: "Vùng mặn dự báo", icon: TrendingUp },
              ].map((item) => (
                <button
                  key={item.key}
                  className="w-full flex items-center justify-between py-2.5"
                  onClick={() =>
                    setLayers((previous) => ({
                      ...previous,
                      [item.key]: !previous[item.key as keyof typeof previous],
                    }))
                  }
                >
                  <div className="flex items-center gap-2.5">
                    <item.icon size={16} className="text-mekong-teal" />
                    <span className="text-[11px] font-black uppercase tracking-widest text-mekong-navy">{item.label}</span>
                  </div>
                  <Badge variant={layers[item.key as keyof typeof layers] ? "optimal" : "warning"} className="text-[9px] uppercase">
                    {layers[item.key as keyof typeof layers] ? "on" : "off"}
                  </Badge>
                </button>
              ))}
            </div>
          </Card>

          <Card variant="glass" className="p-4 rounded-2xl border-white/35 shadow-md">
            <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-3 italic">
              Trạm trên bản đồ: {state.stations.length}
            </p>
            <div className="space-y-2 max-h-36 overflow-y-auto pr-1">
              {state.stations.slice(0, 8).map((station) => (
                <button
                  key={station.id}
                  className="w-full flex items-center justify-between text-left text-[11px] font-bold text-mekong-navy hover:text-mekong-teal"
                  onClick={() => {
                    void handleSelectStation(station.id);
                  }}
                >
                  <span>{station.code} - {station.name}</span>
                  {state.selectedStationId === station.id ? <Navigation size={13} /> : null}
                </button>
              ))}
            </div>
          </Card>
        </div>

        <div className="absolute top-8 right-8 z-20 w-80">
          <Card variant="navy" padding="lg" className="bg-[#00203F]/95 text-white rounded-[32px] border border-white/10 shadow-2xl">
            <h3 className="text-[12px] font-black uppercase tracking-[0.2em] mb-4">Sự cố đang mở</h3>
            <div className="space-y-3">
              {criticalIncidents.slice(0, 3).map((incident) => (
                <div key={incident.id} className="rounded-xl bg-white/5 border border-white/10 p-3">
                  <div className="flex justify-between items-center">
                    <span className="text-[10px] font-black text-mekong-cyan uppercase tracking-widest">
                      {incident.severity}
                    </span>
                    <span className="text-[10px] font-bold text-slate-300 uppercase">{incident.status}</span>
                  </div>
                  <p className="text-[12px] font-semibold mt-2 line-clamp-2">{incident.title}</p>
                </div>
              ))}
              {criticalIncidents.length === 0 ? (
                <p className="text-[12px] font-semibold text-slate-300">Không có incident critical đang mở.</p>
              ) : null}
            </div>
          </Card>
        </div>
      </div>

      <Card variant="white" padding="lg" className="rounded-[40px] shadow-soft border border-slate-100">
        <div className="flex justify-between items-start gap-4">
          <div>
            <h3 className="text-lg font-black text-mekong-navy uppercase tracking-tight">
              {selectedStation ? `${selectedStation.code} - ${selectedStation.name}` : "Chưa chọn trạm"}
            </h3>
            <p className="text-[11px] font-bold text-slate-500 uppercase tracking-widest mt-1">
              Trạng thái: {selectedStation?.status ?? "--"} • Risk: {formatRiskLabel(state.selectedRisk?.assessment.risk_level)}
            </p>
          </div>
          <div className="flex gap-3">
            <Badge variant="warning" className="uppercase">
              Loading: {state.loading ? "yes" : "no"}
            </Badge>
            <Button variant="outline" className="h-10 px-4 text-[11px]" onClick={() => navigate("/strategy")}>
              Chi tiết logic
            </Button>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mt-6">
          {[
            { label: "Độ mặn hiện tại", value: `${formatValue(selectedReading?.salinity_gl)} g/L` },
            { label: "Mực nước", value: `${formatValue(selectedReading?.water_level_m)} m` },
            { label: "Tốc độ gió", value: `${formatValue(selectedReading?.wind_speed_mps)} m/s` },
            { label: "Xu hướng", value: state.selectedRisk?.assessment.trend_direction ?? "--" },
          ].map((metric) => (
            <div key={metric.label} className="rounded-2xl border border-slate-200 p-4 bg-slate-50/60">
              <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2">{metric.label}</p>
              <p className="text-[18px] font-black text-mekong-navy">{metric.value}</p>
            </div>
          ))}
        </div>

        {state.selectedRisk?.assessment.summary ? (
          <div className="mt-5 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 flex items-start gap-3">
            <AlertTriangle size={18} className="text-mekong-critical mt-0.5" />
            <p className="text-[13px] font-semibold text-red-900">{state.selectedRisk.assessment.summary}</p>
          </div>
        ) : null}
      </Card>
    </div>
  );
}

export default InteractiveMap;
