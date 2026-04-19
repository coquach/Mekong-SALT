import { Suspense, lazy, useEffect } from "react";
import { BrowserRouter, Link, Route, Routes, useLocation } from "react-router-dom";

import { GlobalLayout } from "./components/layout/GlobalLayout";
import { RenderErrorBoundary } from "./components/ui/RenderErrorBoundary";

const InformationHub = lazy(() => import("./pages/InformationHub"));
const Dashboard = lazy(() => import("./pages/Dashboard"));
const InteractiveMap = lazy(() => import("./pages/InteractiveMap"));
const StrategyOrchestration = lazy(() => import("./pages/StrategyOrchestration"));
const ActionLogs = lazy(() => import("./pages/ActionLogs"));
const Notifications = lazy(() => import("./pages/Notifications"));
const History = lazy(() => import("./pages/History"));
const RunGraphDetail = lazy(() => import("./pages/RunGraphDetail.tsx"));
const MemoryCases = lazy(() => import("./pages/MemoryCases"));

const RouteFallback = () => (
  <div className="mx-auto w-full max-w-425 px-4 py-6 lg:px-10">
    <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-soft">
      <div className="space-y-3">
        <div className="h-3 w-24 rounded-full bg-slate-200" />
        <div className="h-8 w-2/3 rounded-full bg-slate-200" />
        <div className="h-3 w-full rounded-full bg-slate-100" />
        <div className="h-3 w-5/6 rounded-full bg-slate-100" />
      </div>
    </div>
  </div>
);

const ScrollToTop = () => {
  const { pathname } = useLocation();

  useEffect(() => {
    window.scrollTo(0, 0);
  }, [pathname]);

  return null;
};

const NotFoundPage = () => (
  <div className="mx-auto w-full max-w-425 px-4 py-10 lg:px-10">
    <div className="rounded-3xl border border-slate-200 bg-white p-8 shadow-soft">
      <div className="space-y-4">
        <p className="text-[10px] font-black uppercase tracking-[0.18em] text-slate-400">404</p>
        <h1 className="text-3xl font-black tracking-tight text-mekong-navy">Không tìm thấy trang</h1>
        <p className="max-w-2xl text-sm font-medium leading-relaxed text-slate-600">
          Đường dẫn này không khớp với bất kỳ trang nào trong frontend hiện tại.
        </p>
        <Link
          to="/dashboard"
          className="inline-flex items-center rounded-xl bg-mekong-navy px-4 py-2 text-[10px] font-black uppercase tracking-[0.14em] text-white transition-colors hover:bg-mekong-teal"
        >
          Quay về dashboard
        </Link>
      </div>
    </div>
  </div>
);

function App() {
  return (
    <BrowserRouter>
      <ScrollToTop />

      <RenderErrorBoundary fallback={<RouteFallback />}>
        <Suspense fallback={<RouteFallback />}>
          <Routes>
            <Route element={<GlobalLayout />}>
              <Route path="/" element={<InformationHub />} />
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/map" element={<InteractiveMap />} />
              <Route path="/strategy" element={<StrategyOrchestration />} />
              <Route path="/strategy/runs/:runId" element={<RunGraphDetail />} />
              <Route path="/memory-cases" element={<MemoryCases />} />
            <Route path="/logs" element={<ActionLogs />} />
            <Route path="/notifications" element={<Notifications />} />
            <Route path="/history" element={<History />} />
            <Route path="*" element={<NotFoundPage />} />
          </Route>
        </Routes>
      </Suspense>
      </RenderErrorBoundary>
    </BrowserRouter>
  );
}

export default App;
