import { Outlet } from "react-router-dom";

import { Header } from "./Header";
import { Sidebar } from "./Sidebar";

export const GlobalLayout = () => {
  return (
    <div className="relative flex min-h-screen bg-mekong-bg text-mekong-navy antialiased">
      <Sidebar />

      <div className="ml-0 flex min-h-screen min-w-0 flex-1 flex-col lg:ml-72">
        <Header />

        <main className="relative flex-1 overflow-x-hidden px-4 pb-8 pt-4 lg:px-10 lg:pb-10 lg:pt-6">
          <div className="pointer-events-none absolute left-0 top-0 -z-10 h-96 w-96 rounded-full bg-mekong-cyan/12 blur-[110px]" />
          <div className="pointer-events-none absolute -bottom-32 right-0 -z-10 h-112 w-md rounded-full bg-mekong-teal/12 blur-[130px]" />

          <div className="mx-auto w-full max-w-425">
            <div className="animate-in fill-mode-both slide-in-from-bottom-2 fade-in duration-500">
              <Outlet />
            </div>
          </div>
        </main>

        <footer className="hidden border-t border-slate-200 bg-white/70 px-6 py-4 lg:block lg:px-10">
          <div className="mx-auto flex w-full max-w-425 flex-col gap-2 text-[11px] font-semibold text-slate-500 md:flex-row md:items-center md:justify-between">
            <p className="uppercase tracking-[0.14em]">Mekong-SALT • Trung tâm điều hành</p>
            <p className="uppercase tracking-[0.14em]">Nút trực tuyến: 42/42 • API v2.4</p>
          </div>
        </footer>
      </div>
    </div>
  );
};
