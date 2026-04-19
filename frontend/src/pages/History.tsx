import { useMemo, useRef, useState } from "react";
import {
  AlertCircle,
  Bell,
  History as HistoryIcon,
  RefreshCcw,
  Search,
  Target,
  Waves,
} from "lucide-react";

import { EmptyState, InlineError, SkeletonBlock, SkeletonCards } from "../components/ui/AsyncState";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { PageHeading } from "../components/ui/PageHeading";
import { type RiskLatestResponse, type SensorReading } from "../lib/api/dashboard";
import { getApiErrorMessage } from "../lib/api/error";
import { useLivePageRefresh } from "../lib/hooks/useLivePageRefresh";
import {
  getAuditLogs,
  getIncidents,
  getLatestRisk,
  getReadingHistory,
  getStations,
  type AuditLogRead,
  type IncidentRead,
  type SensorStationRead,
} from "../lib/api/telemetry";
import { ApiError } from "../lib/api/types";
import { formatDateTime as formatDateTimeUtil, formatNumber as formatNumberUtil, formatTime as formatTimeUtil, toNumber as toNumberUtil } from "../lib/format";

type HistoryState = {
  loading: boolean;
  stationLoading: boolean;
  error: string | null;
  stations: SensorStationRead[];
  selectedStationId: string | null;
  readings: SensorReading[];
  risk: RiskLatestResponse | null;
  incidents: IncidentRead[];
  auditLogs: AuditLogRead[];
  lastRefreshAt: string | null;
};

async function loadStationContext(
  stationCode: string,
  signal?: AbortSignal,
): Promise<{ readings: SensorReading[]; risk: RiskLatestResponse | null }> {
  const [history, risk] = await Promise.all([
    getReadingHistory({ station_code: stationCode, limit: 300 }, signal),
    getLatestRisk({ station_code: stationCode }, signal).catch((error: unknown) => {
      if (error instanceof ApiError && error.statusCode === 404) {
        return null;
      }
      throw error;
    }),
  ]);

  const sortedReadings = [...history.items].sort(
    (left, right) =>
      new Date(right.recorded_at).getTime() - new Date(left.recorded_at).getTime(),
  );

  return {
    readings: sortedReadings,
    risk,
  };
}

export function History() {
  const [state, setState] = useState<HistoryState>(() => {
    return {
      loading: true,
      stationLoading: false,
      error: null,
      stations: [],
      selectedStationId: null,
      readings: [],
      risk: null,
      incidents: [],
      auditLogs: [],
      lastRefreshAt: null,
    };
  });
  const stationContextRequestIdRef = useRef(0);
  const stationContextAbortControllerRef = useRef<AbortController | null>(null);
  const pageLoadRequestIdRef = useRef(0);

  const loadPageData = async (
    params?: {
      selectedStationId?: string | null;
      signal?: AbortSignal;
      showLoading?: boolean;
    },
  ) => {
    const selectedStationId = params?.selectedStationId ?? state.selectedStationId ?? null;
    const signal = params?.signal;
    const showLoading = params?.showLoading ?? false;
    const requestId = ++pageLoadRequestIdRef.current;

    stationContextAbortControllerRef.current?.abort();
    stationContextRequestIdRef.current += 1;
    if (showLoading) {
      setState((previous) => ({ ...previous, loading: true, error: null }));
    }

    try {
      const [stationsResponse, incidentsResponse, auditResponse] = await Promise.all([
        getStations({ limit: 300 }, signal),
        getIncidents({ limit: 100 }, signal),
        getAuditLogs({ limit: 100 }, signal),
      ]);

      const stations = stationsResponse.items;
      const selectedStation =
        stations.find((station) => station.id === selectedStationId) ??
        stations[0] ??
        null;

      let readings: SensorReading[] = [];
      let risk: RiskLatestResponse | null = null;
      if (selectedStation) {
        const stationData = await loadStationContext(selectedStation.code, signal);
        readings = stationData.readings;
        risk = stationData.risk;
      }

      if (requestId !== pageLoadRequestIdRef.current || signal?.aborted) {
        return;
      }

      setState((previous) => ({
        ...previous,
        loading: false,
        stationLoading: false,
        error: null,
        stations,
        selectedStationId: selectedStation?.id ?? null,
        readings,
        risk,
        incidents: incidentsResponse.items,
        auditLogs: auditResponse.items,
        lastRefreshAt: new Date().toISOString(),
      }));

    } catch (error) {
      if (signal?.aborted || requestId !== pageLoadRequestIdRef.current) {
        return;
      }
      setState((previous) => ({
        ...previous,
        loading: false,
        stationLoading: false,
        error: getApiErrorMessage(error, "Không tải được dữ liệu lịch sử."),
      }));
    }
  };

  useLivePageRefresh({
    refresh: loadPageData,
    pollIntervalMs: 15_000,
  });

  const selectedStation = useMemo(
    () => state.stations.find((station) => station.id === state.selectedStationId) ?? null,
    [state.stations, state.selectedStationId],
  );

  const latestReading = state.readings[0] ?? null;
  const oldestReading = state.readings[state.readings.length - 1] ?? null;

  const salinityValues = useMemo(
    () =>
      state.readings
        .map((reading) => toNumberUtil(reading.salinity_gl))
        .filter((value): value is number => value !== null),
    [state.readings],
  );

  const averageSalinity = useMemo(() => {
    if (salinityValues.length === 0) {
      return null;
    }
    const total = salinityValues.reduce((sum, value) => sum + value, 0);
    return total / salinityValues.length;
  }, [salinityValues]);

  const maxSalinity = useMemo(() => {
    if (salinityValues.length === 0) {
      return null;
    }
    return Math.max(...salinityValues);
  }, [salinityValues]);

  const trendDelta = useMemo(() => {
    const latest = toNumberUtil(latestReading?.salinity_gl);
    const oldest = toNumberUtil(oldestReading?.salinity_gl);
    if (latest === null || oldest === null) {
      return null;
    }
    return latest - oldest;
  }, [latestReading, oldestReading]);

  const openIncidents = useMemo(
    () =>
      state.incidents.filter(
        (incident) => incident.status !== "resolved" && incident.status !== "closed",
      ),
    [state.incidents],
  );

  const handleStationChange = async (stationId: string) => {
    if (stationId === state.selectedStationId) {
      return;
    }
    const station = state.stations.find((item) => item.id === stationId);
    if (!station) {
      return;
    }

    setState((previous) => ({
      ...previous,
      selectedStationId: stationId,
      stationLoading: true,
      error: null,
    }));

    pageLoadRequestIdRef.current += 1;
    stationContextAbortControllerRef.current?.abort();
    const stationContextAbortController = new AbortController();
    stationContextAbortControllerRef.current = stationContextAbortController;
    const requestId = ++stationContextRequestIdRef.current;

    try {
      const stationData = await loadStationContext(
        station.code,
        stationContextAbortController.signal,
      );
      if (
        requestId !== stationContextRequestIdRef.current ||
        stationContextAbortController.signal.aborted
      ) {
        return;
      }
      setState((previous) => ({
        ...previous,
        stationLoading: false,
        readings: stationData.readings,
        risk: stationData.risk,
      }));
    } catch (error) {
      if (
        requestId !== stationContextRequestIdRef.current ||
        stationContextAbortController.signal.aborted
      ) {
        return;
      }
      setState((previous) => ({
        ...previous,
        stationLoading: false,
        error: getApiErrorMessage(error, "Không tải được dữ liệu lịch sử."),
      }));
    }
  };

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-1000">
      <PageHeading
        trailing={
          <Badge variant="neutral" className="text-[9px]">
            Đồng bộ lúc {formatTimeUtil(state.lastRefreshAt)}
          </Badge>
        }
      />

      {state.error ? (
        <InlineError
          title="Lỗi điều tra lịch sử"
          message={state.error}
          onRetry={() => {
            void loadPageData({ selectedStationId: state.selectedStationId });
          }}
        />
      ) : null}

      {state.loading && state.stations.length === 0 ? <SkeletonCards count={3} /> : null}

      <div className={`flex flex-col lg:flex-row justify-between items-start lg:items-center gap-6 border-b border-slate-200 pb-8 ${state.loading && state.stations.length === 0 ? "hidden" : ""}`}>
        <div className="flex items-center gap-5">
          <div className="w-14 h-14 bg-mekong-navy rounded-shell flex items-center justify-center text-white shadow-xl ring-4 ring-slate-100">
            <HistoryIcon size={28} strokeWidth={2.5} />
          </div>
          <div className="space-y-1">
            <div className="flex items-center gap-3 text-[11px] font-black text-slate-400 uppercase tracking-[0.3em]">
              <span className="bg-slate-100 px-2 py-0.5 rounded">
                Nguồn: API backend
              </span>
              <span className="text-mekong-teal italic">
                /readings/history, /risk/latest, /audit/logs
              </span>
            </div>
            <h1 className="text-4xl lg:text-5xl font-black text-mekong-navy tracking-tighter uppercase leading-none">
              Điều tra dữ liệu lịch sử
            </h1>
          </div>
        </div>

        <div className="flex items-center gap-3 w-full lg:w-auto">
          <div className="relative flex-1 lg:flex-none">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={16} />
            <select
              value={state.selectedStationId ?? ""}
              onChange={(event) => {
                void handleStationChange(event.target.value);
              }}
              aria-label="Chọn trạm quan sát"
              title="Chọn trạm quan sát"
              className="pl-10 pr-9 py-2.5 bg-slate-100 border-none rounded-xl text-sm font-bold text-mekong-navy focus:ring-2 ring-mekong-teal/20 min-w-65"
              disabled={state.loading || state.stations.length === 0}
            >
              {state.stations.map((station) => (
                <option key={station.id} value={station.id}>
                  {station.code} - {station.name}
                </option>
              ))}
            </select>
          </div>

          <Button
            variant="outline"
            className="h-11 rounded-xl border-slate-200 bg-white px-4"
            onClick={() => {
              void loadPageData({ selectedStationId: state.selectedStationId });
            }}
          >
            <RefreshCcw size={16} className="mr-2" />
            Làm mới
          </Button>

          <Button variant="outline" className="h-11 rounded-xl border-slate-200 bg-white">
            <Bell size={18} />
          </Button>
        </div>
      </div>

      <div className={`grid grid-cols-12 gap-6 ${state.loading && state.stations.length === 0 ? "hidden" : ""}`}>
        <Card variant="white" className="col-span-12 lg:col-span-4 rounded-4xl p-6 shadow-soft border border-slate-100">
          <div className="flex items-center gap-3 mb-5">
            <div className="p-2.5 bg-mekong-teal/10 rounded-xl text-mekong-teal border border-mekong-teal/20">
              <Waves size={18} />
            </div>
            <h3 className="text-sm font-black text-mekong-navy uppercase tracking-widest">Ảnh chụp độ mặn</h3>
          </div>
          <div className="space-y-3">
            <div className="flex items-end gap-2">
              <span className="text-5xl font-black text-mekong-navy tracking-tight">
                {formatNumberUtil(toNumberUtil(latestReading?.salinity_gl), 2)}
              </span>
              <span className="text-sm font-black text-slate-400 uppercase mb-1">g/L</span>
            </div>
            <p className="text-[11px] font-bold text-slate-500 uppercase tracking-widest">
              Ghi nhận: {formatDateTimeUtil(latestReading?.recorded_at ?? null)}
            </p>
             <Badge variant="warning" className="uppercase text-[10px]">
              Rủi ro: {state.risk?.assessment.risk_level ?? "unknown"}
            </Badge>
          </div>
        </Card>

        <Card variant="white" className="col-span-12 lg:col-span-4 rounded-4xl p-6 shadow-soft border border-slate-100">
          <div className="flex items-center gap-3 mb-5">
            <Target size={18} className="text-mekong-navy" />
            <h3 className="text-sm font-black text-mekong-navy uppercase tracking-widest">Thống kê lịch sử</h3>
          </div>
          <div className="space-y-3 text-[13px] font-semibold text-slate-600">
            <div className="flex justify-between">
              <span>Độ mặn trung bình</span>
              <span className="font-black text-mekong-navy">{formatNumberUtil(averageSalinity, 2)} g/L</span>
            </div>
            <div className="flex justify-between">
              <span>Độ mặn cao nhất</span>
              <span className="font-black text-mekong-navy">{formatNumberUtil(maxSalinity, 2)} g/L</span>
            </div>
            <div className="flex justify-between">
              <span>Độ lệch (mới nhất - cũ nhất)</span>
              <span className="font-black text-mekong-navy">{formatNumberUtil(trendDelta, 2)} g/L</span>
            </div>
            <div className="flex justify-between">
              <span>Số mẫu</span>
              <span className="font-black text-mekong-navy">{state.readings.length}</span>
            </div>
          </div>
        </Card>

        <Card variant="white" className="col-span-12 lg:col-span-4 rounded-4xl p-6 shadow-soft border border-slate-100">
          <div className="flex items-center gap-3 mb-5">
            <AlertCircle size={18} className="text-mekong-critical" />
            <h3 className="text-sm font-black text-mekong-navy uppercase tracking-widest">Ngữ cảnh sự cố</h3>
          </div>
          <div className="space-y-4 text-[13px] font-semibold text-slate-600">
            <div className="grid grid-cols-2 gap-3">
              <div className="rounded-2xl bg-slate-50/70 border border-slate-100 p-3">
                <p className="text-[9px] font-black uppercase tracking-[0.16em] text-slate-400">Sự cố đang mở</p>
                <p className="mt-1 text-lg font-black text-mekong-critical">{openIncidents.length}</p>
              </div>
              <div className="rounded-2xl bg-slate-50/70 border border-slate-100 p-3">
                <p className="text-[9px] font-black uppercase tracking-[0.16em] text-slate-400">Tổng sự cố</p>
                <p className="mt-1 text-lg font-black text-mekong-navy">{state.incidents.length}</p>
              </div>
            </div>

            <div className="rounded-3xl border border-slate-200 bg-slate-50/80 p-4">
              <div className="flex items-center justify-between gap-3">
                <p className="text-[9px] font-black uppercase tracking-[0.18em] text-slate-400">Đánh giá rủi ro gần nhất</p>
                <Badge variant={state.stationLoading ? "warning" : "optimal"} className="text-[9px] uppercase">
                  {state.stationLoading ? "Đang đánh giá..." : "Đã đồng bộ"}
                </Badge>
              </div>

              {state.stationLoading ? (
                <div className="mt-4 space-y-3">
                  <SkeletonBlock className="h-5 w-32" />
                  <SkeletonBlock className="h-4 w-full" />
                  <SkeletonBlock className="h-4 w-5/6" />
                  <SkeletonBlock className="h-4 w-3/4" />
                </div>
              ) : state.risk?.assessment ? (
                <div className="mt-4 space-y-3">
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge variant="warning" className="text-[9px] uppercase">
                      {state.risk.assessment.risk_level}
                    </Badge>
                    <span className="text-[10px] font-black uppercase tracking-[0.16em] text-slate-400">
                      {formatDateTimeUtil(state.risk.assessment.assessed_at)}
                    </span>
                  </div>
                  <p className="text-sm font-black text-mekong-navy uppercase tracking-[0.08em]">
                    {state.risk.assessment.summary}
                  </p>
                </div>
              ) : (
                <EmptyState
                  title="Chưa có đánh giá rủi ro"
                  description="Chọn trạm hoặc chờ backend tạo assessment mới để xem summary đầy đủ ở đây."
                />
              )}
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="rounded-2xl bg-slate-50/70 border border-slate-100 p-3">
                <p className="text-[9px] font-black uppercase tracking-[0.16em] text-slate-400">Nhật ký audit</p>
                <p className="mt-1 text-lg font-black text-mekong-navy">{state.auditLogs.length}</p>
              </div>
              <div className="rounded-2xl bg-slate-50/70 border border-slate-100 p-3">
                <p className="text-[9px] font-black uppercase tracking-[0.16em] text-slate-400">Trạng thái trạm</p>
                <p className="mt-1 text-lg font-black text-mekong-navy">{selectedStation?.status ?? "--"}</p>
              </div>
            </div>
          </div>
        </Card>
      </div>

      <div className={`grid grid-cols-12 gap-8 items-start ${state.loading && state.stations.length === 0 ? "hidden" : ""}`}>
        <Card variant="white" className="col-span-12 lg:col-span-8 rounded-4xl p-8 shadow-soft border border-slate-100">
          <div className="flex justify-between items-center mb-6">
            <div>
              <h3 className="text-lg font-black text-mekong-navy uppercase tracking-tight">Lịch sử số liệu</h3>
              <p className="text-[11px] font-bold text-slate-500 uppercase tracking-widest mt-1">
                {selectedStation
                  ? `${selectedStation.code} - ${selectedStation.name}`
                  : "Chưa chọn trạm"}
              </p>
            </div>
            <Badge className="uppercase text-[10px]" variant={state.stationLoading ? "warning" : "optimal"}>
              {state.stationLoading ? "Đang tải trạm..." : "Đã đồng bộ"}
            </Badge>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-50/70 border-b border-slate-100">
                  <th className="px-4 py-3 text-[10px] font-black text-slate-400 uppercase tracking-widest">Thời điểm ghi nhận</th>
                  <th className="px-4 py-3 text-[10px] font-black text-slate-400 uppercase tracking-widest">Độ mặn (g/L)</th>
                  <th className="px-4 py-3 text-[10px] font-black text-slate-400 uppercase tracking-widest">Mực nước (m)</th>
                  <th className="px-4 py-3 text-[10px] font-black text-slate-400 uppercase tracking-widest">Gió (m/s)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50">
                {state.readings.slice(0, 20).map((reading) => (
                  <tr key={reading.id} className="hover:bg-slate-50/40 transition-colors">
                    <td className="px-4 py-4 text-[13px] font-semibold text-mekong-navy">
                      {formatDateTimeUtil(reading.recorded_at)}
                    </td>
                    <td className="px-4 py-4 text-[13px] font-black text-mekong-navy">
                      {formatNumberUtil(toNumberUtil(reading.salinity_gl), 2)}
                    </td>
                    <td className="px-4 py-4 text-[13px] font-semibold text-slate-600">
                      {formatNumberUtil(toNumberUtil(reading.water_level_m), 2)}
                    </td>
                    <td className="px-4 py-4 text-[13px] font-semibold text-slate-600">
                      {formatNumberUtil(toNumberUtil(reading.wind_speed_mps), 2)}
                    </td>
                  </tr>
                ))}
                {state.readings.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="px-4 py-6">
                      <EmptyState
                        title="Chưa có dữ liệu lịch sử cho trạm này"
                        description="Thử chọn trạm khác hoặc đợi chu kỳ ghi nhận tiếp theo."
                      />
                    </td>
                  </tr>
                ) : null}
              </tbody>
            </table>
          </div>
        </Card>

        <Card variant="white" className="col-span-12 lg:col-span-4 rounded-4xl p-6 shadow-soft border border-slate-100">
          <h3 className="text-sm font-black text-mekong-navy uppercase tracking-widest mb-4">Dòng thời gian audit</h3>
          <div className="space-y-3 max-h-130 overflow-y-auto pr-1">
            {state.auditLogs.slice(0, 15).map((log) => (
              <div key={log.id} className="rounded-2xl border border-slate-200 bg-slate-50/70 p-4">
                <div className="flex items-center justify-between gap-3">
                  <Badge className="uppercase text-[9px]">{log.event_type}</Badge>
                  <span className="text-[10px] font-black text-slate-400">
                    {formatDateTimeUtil(log.occurred_at)}
                  </span>
                </div>
                <p className="mt-2 text-[13px] font-semibold text-slate-700 leading-relaxed">{log.summary}</p>
                <p className="mt-2 text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                  Actor: {log.actor_name}
                </p>
              </div>
            ))}
            {state.auditLogs.length === 0 ? (
              <EmptyState
                title="Chưa có audit log"
                description="Audit trail sẽ xuất hiện khi backend ghi nhận event vận hành."
              />
            ) : null}
          </div>
        </Card>
      </div>
    </div>
  );
}

export default History;
