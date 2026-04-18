import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  AlertTriangle,
  Eye,
  Layers,
  MapPin,
  Navigation,
  RefreshCcw,
  ShieldCheck,
  TrendingUp,
} from "lucide-react";
import { useNavigate } from "react-router-dom";

import { SatelliteMap, type MapGate, type MapStation } from "../components/dashboard/SatelliteMap";
import { EmptyState, InlineError, SkeletonCards } from "../components/ui/AsyncState";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { PageHeading } from "../components/ui/PageHeading";
import { getLatestReadings, type SensorReading } from "../lib/api/dashboard";
import {
  getIncidents,
  getGates,
  getLatestRisk,
  getStations,
  type GateRead,
  type IncidentRead,
  type SensorStationRead,
} from "../lib/api/telemetry";
import { ApiError, type ErrorResponse } from "../lib/api/types";
import { formatNumber as formatNumberUtil, formatTime as formatTimeUtil, toNumber as toNumberUtil } from "../lib/format";

type RiskFilter = "all" | "critical" | "warning" | "safe";

type InteractiveMapState = {
  loading: boolean;
  error: string | null;
  stations: SensorStationRead[];
  gates: GateRead[];
  latestReadings: SensorReading[];
  incidents: IncidentRead[];
  selectedStationId: string | null;
  selectedRisk: Awaited<ReturnType<typeof getLatestRisk>> | null;
  lastRefreshAt: string | null;
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

function toNumber(value: string | number | null | undefined): number | null {
  if (value === null || value === undefined) {
    return null;
  }
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
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
    return "UNKNOWN";
  }
  return riskLevel.toUpperCase();
}

function deriveRiskLevel(salinityGl: number | null | undefined): "critical" | "warning" | "safe" {
  if (salinityGl === null || salinityGl === undefined) {
    return "safe";
  }
  if (salinityGl >= 2) {
    return "critical";
  }
  if (salinityGl >= 1) {
    return "warning";
  }
  return "safe";
}

export function InteractiveMap() {
  const [layers, setLayers] = useState({
    heatmap: true,
    stations: true,
    gates: true,
    prediction: true,
  });
  const [riskFilter, setRiskFilter] = useState<RiskFilter>("all");
  const [state, setState] = useState<InteractiveMapState>({
    loading: true,
    error: null,
    stations: [],
    gates: [],
    latestReadings: [],
    incidents: [],
    selectedStationId: null,
    selectedRisk: null,
    lastRefreshAt: null,
  });
  const navigate = useNavigate();
  const riskRequestIdRef = useRef(0);
  const riskAbortControllerRef = useRef<AbortController | null>(null);
  const selectedStationIdRef = useRef<string | null>(null);
  const isBootstrapping = state.loading && state.stations.length === 0 && state.gates.length === 0;

  useEffect(() => {
    selectedStationIdRef.current = state.selectedStationId;
  }, [state.selectedStationId]);

  const readingsByStationId = useMemo(() => {
    const map = new Map<string, SensorReading>();
    state.latestReadings.forEach((reading) => {
      map.set(reading.station_id, reading);
    });
    return map;
  }, [state.latestReadings]);

  const requestSelectedRisk = useCallback(async (stationCode: string | null) => {
    riskAbortControllerRef.current?.abort();

    if (!stationCode) {
      setState((previous) => ({ ...previous, selectedRisk: null }));
      return;
    }

    const riskAbortController = new AbortController();
    riskAbortControllerRef.current = riskAbortController;
    const requestId = ++riskRequestIdRef.current;

    try {
      const risk = await getLatestRisk({ station_code: stationCode }, riskAbortController.signal);
      if (requestId !== riskRequestIdRef.current || riskAbortController.signal.aborted) {
        return;
      }
      setState((previous) => ({
        ...previous,
        selectedRisk: risk,
        error: null,
        lastRefreshAt: new Date().toISOString(),
      }));
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
  }, []);

  const refreshData = useCallback(async (
    options?: {
      signal?: AbortSignal;
      showLoading?: boolean;
      stationIdOverride?: string | null;
    },
  ) => {
    const signal = options?.signal;
    const showLoading = options?.showLoading ?? false;
    const stationIdOverride = options?.stationIdOverride;

    if (showLoading) {
      setState((previous) => ({ ...previous, loading: true, error: null }));
    }

    try {
      const [stationsResult, gatesResult, latestReadingsResult, incidentsResult] = await Promise.allSettled([
        getStations({ limit: 300 }, signal),
        getGates({ limit: 100 }, signal),
        getLatestReadings({ limit: 500 }, signal),
        getIncidents({ limit: 30 }, signal),
      ]);

      const stations = stationsResult.status === "fulfilled" ? stationsResult.value : { items: [], count: 0 };
      const gates = gatesResult.status === "fulfilled" ? gatesResult.value : { items: [], count: 0 };
      const latestReadings =
        latestReadingsResult.status === "fulfilled" ? latestReadingsResult.value : { items: [], count: 0 };
      const incidents = incidentsResult.status === "fulfilled" ? incidentsResult.value : { items: [], count: 0 };

      const firstFailure = [stationsResult, gatesResult, latestReadingsResult, incidentsResult].find(
        (result): result is PromiseRejectedResult => result.status === "rejected",
      );

      const selectedStationIdCandidate =
        stationIdOverride ??
        selectedStationIdRef.current ??
        stations.items[0]?.id ??
        null;
      const selectedStation =
        stations.items.find((station) => station.id === selectedStationIdCandidate) ??
        stations.items[0] ??
        null;
      const selectedStationId = selectedStation?.id ?? null;

      setState((previous) => ({
        ...previous,
        loading: false,
        error: firstFailure ? parseApiError(firstFailure.reason) : null,
        stations: stations.items,
        gates: gates.items,
        latestReadings: latestReadings.items,
        incidents: incidents.items,
        selectedStationId,
        selectedRisk:
          previous.selectedRisk?.assessment.station_id === selectedStationId ? previous.selectedRisk : null,
        lastRefreshAt: new Date().toISOString(),
      }));

      void requestSelectedRisk(selectedStation?.code ?? null);
    } catch (error) {
      if (signal?.aborted) {
        return;
      }
      setState((previous) => ({
        ...previous,
        loading: false,
        error: parseApiError(error),
      }));
    }
  }, [requestSelectedRisk]);

  useEffect(() => {
    const abortController = new AbortController();
    void refreshData({ signal: abortController.signal, showLoading: true });
    return () => {
      abortController.abort();
      riskAbortControllerRef.current?.abort();
    };
  }, [refreshData]);

  useEffect(() => {
    const intervalId = window.setInterval(() => {
      void refreshData({ showLoading: false });
    }, 20_000);
    return () => window.clearInterval(intervalId);
  }, [refreshData]);

  const mapStations = useMemo<MapStation[]>(
    () =>
      state.stations.flatMap((station) => {
        const reading = readingsByStationId.get(station.id);
        const latestSalinityGl =
          reading?.salinity_gl !== null && reading?.salinity_gl !== undefined
            ? Number(reading.salinity_gl)
            : null;
        const derivedRisk = deriveRiskLevel(latestSalinityGl);
        const latitude = toNumberUtil(station.latitude);
        const longitude = toNumber(station.longitude);

        if (latitude === null || longitude === null) {
          return [] as MapStation[];
        }

        return [
          {
            id: station.id,
            code: station.code,
            name: station.name,
            latitude,
            longitude,
            status: station.status,
            stationType: station.station_type,
            stationMetadata: station.station_metadata,
            latestSalinityGl,
            riskLevel:
              state.selectedRisk?.assessment.station_id === station.id
                ? state.selectedRisk.assessment.risk_level
                : derivedRisk,
          },
        ];
      }),
    [state.stations, readingsByStationId, state.selectedRisk],
  );

  const mapGates = useMemo<MapGate[]>(
    () =>
      state.gates.flatMap((gate) => {
          const latitude = toNumberUtil(gate.latitude);
          const longitude = toNumber(gate.longitude);
          if (latitude === null || longitude === null) {
            return [] as MapGate[];
          }

          return [
            {
            id: gate.id,
            code: gate.code,
            name: gate.name,
            latitude,
            longitude,
            gateType: gate.gate_type,
            status: gate.status,
            gateMetadata: gate.gate_metadata,
            locationDescription: gate.location_description,
            lastOperatedAt: gate.last_operated_at,
            station: gate.station,
            },
          ];
        }),
    [state.gates],
  );

  const filteredMapStations = useMemo(() => {
    if (riskFilter === "all") {
      return mapStations;
    }
    return mapStations.filter((station) => {
      const level = `${station.riskLevel ?? ""}`.toLowerCase();
      if (riskFilter === "critical") {
        return level === "critical" || level === "danger";
      }
      if (riskFilter === "warning") {
        return level === "warning";
      }
      return level === "safe" || level === "";
    });
  }, [mapStations, riskFilter]);

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
    selectedStationIdRef.current = stationId;
    setState((previous) => ({ ...previous, selectedStationId: stationId }));
    if (!station) {
      void requestSelectedRisk(null);
      return;
    }

    void requestSelectedRisk(station.code);
  };

  const criticalIncidents = useMemo(
    () => state.incidents.filter((item) => item.severity === "critical" && item.status !== "closed"),
    [state.incidents],
  );

  return (
    <div className="space-y-6">
      <PageHeading
        trailing={
          <Badge variant="neutral" className="text-[9px]">
            Đồng bộ lúc {formatTimeUtil(state.lastRefreshAt)}
          </Badge>
        }
      />

      {state.error ? (
        <InlineError
          title="Lỗi dữ liệu bản đồ"
          message={state.error}
          onRetry={() => {
            void refreshData({ showLoading: true });
          }}
        />
      ) : null}

      {isBootstrapping ? (
        <SkeletonCards count={3} />
      ) : null}

      <div className="relative w-full h-[calc(100vh-300px)] min-h-150 rounded-[40px] overflow-hidden bg-slate-900 shadow-2xl border border-white/10">
        <SatelliteMap
          layers={layers}
          zoom={11}
          showControls
          stations={filteredMapStations}
          gates={mapGates}
          selectedStationId={state.selectedStationId}
          onSelectStation={(stationId) => {
            void handleSelectStation(stationId);
          }}
        />

        {isBootstrapping ? (
          <div className="absolute inset-0 z-10 flex items-center justify-center bg-slate-950/35 backdrop-blur-[2px]">
            <div className="w-full max-w-md rounded-3xl border border-white/10 bg-slate-950/80 px-6 py-5 text-white shadow-2xl">
              <div className="flex items-center gap-3">
                <div className="h-10 w-10 animate-pulse rounded-2xl bg-mekong-cyan/20" />
                <div>
                  <p className="text-[10px] font-black uppercase tracking-[0.18em] text-slate-400">
                    Đang tải bản đồ
                  </p>
                  <p className="mt-1 text-sm font-semibold text-slate-200">
                    Station và gate đang được đồng bộ, bản đồ sẽ hiển thị marker ngay khi dữ liệu sẵn sàng.
                  </p>
                </div>
              </div>
            </div>
          </div>
        ) : null}

        <div className="absolute top-6 left-6 z-20 space-y-4 w-80">
          <Card variant="glass" className="p-5 rounded-3xl border-white/40 shadow-glass backdrop-blur-2xl">
            <div className="flex items-center gap-3 mb-4 border-b border-mekong-navy/10 pb-3">
              <Layers size={17} className="text-mekong-navy" />
              <h3 className="text-xs font-black text-mekong-navy uppercase tracking-widest">Lớp bản đồ</h3>
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
                  className="w-full flex items-center justify-between rounded-xl px-2 py-2.5 hover:bg-white/70 transition-colors"
                  onClick={() =>
                    setLayers((previous) => ({
                      ...previous,
                      [item.key]: !previous[item.key as keyof typeof previous],
                    }))
                  }
                >
                  <div className="flex items-center gap-2.5">
                    <item.icon size={15} className="text-mekong-teal" />
                    <span className="text-[11px] font-black uppercase tracking-widest text-mekong-navy">{item.label}</span>
                  </div>
                  <Badge variant={layers[item.key as keyof typeof layers] ? "optimal" : "warning"} className="text-[9px] uppercase">
                    {layers[item.key as keyof typeof layers] ? "bật" : "tắt"}
                  </Badge>
                </button>
              ))}
            </div>
          </Card>

          <Card variant="glass" className="p-4 rounded-2xl border-white/35 shadow-md">
            <div className="flex items-center justify-between gap-2">
              <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest">
                Chú giải • {filteredMapStations.length}/{mapStations.length} trạm
              </p>
              <Button
                variant="ghost"
                className="h-7 rounded-lg px-2 text-[9px]"
                onClick={() => {
                  void refreshData({ showLoading: false });
                }}
              >
                <RefreshCcw size={12} />
              </Button>
            </div>
            <div className="mt-3 flex flex-wrap gap-2">
              {[
                { key: "all" as const, label: "Tất cả", badge: "neutral" as const },
                { key: "critical" as const, label: "Nguy cấp", badge: "critical" as const },
                { key: "warning" as const, label: "Cảnh báo", badge: "warning" as const },
                { key: "safe" as const, label: "An toàn", badge: "optimal" as const },
              ].map((item) => (
                <button key={item.key} onClick={() => setRiskFilter(item.key)}>
                  <Badge
                    variant={riskFilter === item.key ? item.badge : "neutral"}
                    className={riskFilter === item.key ? "ring-1 ring-mekong-navy/15" : "opacity-80"}
                  >
                    {item.label}
                  </Badge>
                </button>
              ))}
            </div>
            <div className="mt-3 space-y-2 max-h-28 overflow-y-auto custom-scrollbar pr-1">
              {filteredMapStations.slice(0, 8).map((station) => (
                <button
                  key={station.id}
                  className="w-full flex items-center justify-between rounded-lg px-2 py-1.5 text-left text-[11px] font-bold text-mekong-navy hover:bg-white/70 hover:text-mekong-teal"
                  onClick={() => {
                    void handleSelectStation(station.id);
                  }}
                >
                  <span className="flex flex-col items-start gap-0.5">
                    <span>{station.code} - {station.stationMetadata?.display_name ?? station.name}</span>
                    <span className="text-[9px] font-black uppercase tracking-widest text-slate-400">
                      {station.stationMetadata?.marker?.label ?? station.stationMetadata?.operational_role ?? station.stationType}
                    </span>
                  </span>
                  {state.selectedStationId === station.id ? <Navigation size={13} /> : null}
                </button>
              ))}
            </div>
          </Card>
        </div>

        <div className="absolute top-6 right-6 z-20 w-80">
          <Card variant="navy" padding="lg" className="bg-[#00203F]/95 text-white rounded-4xl border border-white/10 shadow-2xl">
            <h3 className="text-[11px] font-black uppercase tracking-[0.2em] mb-4">Incidents đang mở</h3>
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
                <EmptyState
                  title="Không có incident critical mở"
                  description="Map vẫn tiếp tục cập nhật mỗi 20 giây để phát hiện biến động mới."
                />
              ) : null}
            </div>
          </Card>
        </div>
      </div>

      <Card variant="white" padding="lg" className="rounded-4xl shadow-soft border border-slate-100">
        <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
          <div>
            <h3 className="text-lg font-black text-mekong-navy uppercase tracking-tight">
              {selectedStation
                ? `${selectedStation.code} - ${selectedStation.station_metadata?.display_name ?? selectedStation.name}`
                : "Chưa chọn trạm"}
            </h3>
            <p className="text-[11px] font-bold text-slate-500 uppercase tracking-widest mt-1">
              Trạng thái: {selectedStation?.status ?? "--"} • Rủi ro: {formatRiskLabel(state.selectedRisk?.assessment.risk_level)}
            </p>
            <p className="text-[11px] font-bold text-slate-400 uppercase tracking-widest mt-1">
              {selectedStation?.station_metadata?.marker?.label ?? selectedStation?.station_metadata?.operational_role ?? "Trạm quan trắc"}
            </p>
            <p className="text-[11px] font-bold text-slate-400 uppercase tracking-widest mt-1">
              {selectedStation?.station_metadata?.reference_water_body ?? "--"}
            </p>
          </div>
          <div className="flex gap-3">
            <Badge variant={state.loading ? "warning" : "optimal"} className="uppercase">
              {state.loading ? "syncing..." : "synced"}
            </Badge>
            <Button variant="outline" className="h-10 px-4 text-[11px]" onClick={() => navigate("/strategy")}>
              Mở trang chiến lược
            </Button>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mt-6">
          {[
            { label: "Độ mặn hiện tại", value: `${formatNumberUtil(toNumberUtil(selectedReading?.salinity_gl))} g/L` },
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
