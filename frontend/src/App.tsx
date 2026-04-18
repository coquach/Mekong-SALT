import { Suspense, lazy, useEffect } from "react";
import { BrowserRouter, Navigate, Route, Routes, useLocation } from "react-router-dom";

import { GlobalLayout } from "./components/layout/GlobalLayout";
import { RenderErrorBoundary } from "./components/ui/RenderErrorBoundary";

const InformationHub = lazy(() => import("./pages/InformationHub"));
const Dashboard = lazy(() => import("./pages/Dashboard"));
const InteractiveMap = lazy(() => import("./pages/InteractiveMap"));
const StrategyOrchestration = lazy(() => import("./pages/StrategyOrchestration"));
const ActionLogs = lazy(() => import("./pages/ActionLogs"));
const Notifications = lazy(() => import("./pages/Notifications"));
const History = lazy(() => import("./pages/History"));

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
              <Route path="/logs" element={<ActionLogs />} />
              <Route path="/notifications" element={<Notifications />} />
              <Route path="/history" element={<History />} />
              <Route path="*" element={<Navigate to="/dashboard" replace />} />
            </Route>
          </Routes>
        </Suspense>
      </RenderErrorBoundary>
    </BrowserRouter>
  );
}

export default App;
