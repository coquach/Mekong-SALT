import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { useEffect } from 'react';

// Import Layout chính
import { GlobalLayout } from './components/layout/GlobalLayout';

// Import tất cả các Pages đã build
import { InformationHub } from './pages/InformationHub';
import { Dashboard } from './pages/Dashboard';
import { InteractiveMap } from './pages/InteractiveMap';
import { StrategyOrchestration } from './pages/StrategyOrchestration';
import { ActionLogs } from './pages/ActionLogs';
import { History } from './pages/History';

/**
 * UTILITY COMPONENT: ScrollToTop
 * Giúp tự động cuộn lên đầu trang khi chuyển Route.
 * Một chi tiết nhỏ nhưng cực kỳ quan trọng cho trải nghiệm người dùng (UX).
 */
const ScrollToTop = () => {
  const { pathname } = useLocation();
  useEffect(() => {
    window.scrollTo(0, 0);
  }, [pathname]);
  return null;
};

/**
 * APP COMPONENT
 * -------------
 * - Thiết lập hệ thống Routing sử dụng React Router v6.
 * - GlobalLayout bọc bên ngoài để giữ Sidebar và Header cố định.
 * - Các trang con (Outlet) sẽ thay đổi nội dung bên trong vùng Main.
 */
function App() {
  return (
    <BrowserRouter>
      {/* Đảm bảo mỗi lần chuyển trang đều bắt đầu từ đỉnh trang */}
      <ScrollToTop />
      
      <Routes>
        {/* Định nghĩa GlobalLayout là cha của các trang nội dung */}
        <Route element={<GlobalLayout />}>
          
          {/* 1. Trang chủ - Information Hub */}
          <Route path="/" element={<InformationHub />} />
          
          {/* 2. Trang Dashboard chính */}
          <Route path="/dashboard" element={<Dashboard />} />
          
          {/* 3. Trang Bản đồ tương tác */}
          <Route path="/map" element={<InteractiveMap />} />
          
          {/* 4. Trang logic AI (Agent Logic / Planning) */}
          <Route path="/strategy" element={<StrategyOrchestration />} />
          
          {/* 5. Trang nhật ký hành động (Action Logs) */}
          <Route path="/logs" element={<ActionLogs />} />
          
          {/* 6. Trang phân tích lịch sử (History Deep Dive) */}
          <Route path="/history" element={<History />} />

          {/* Cấu hình fallback: Nếu người dùng nhập sai URL, tự động quay về Dashboard */}
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
          
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;