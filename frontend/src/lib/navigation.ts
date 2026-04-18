export type AppRouteMeta = {
  path: string;
  navLabel: string;
  title: string;
  subtitle: string;
  keyQuestion: string;
  realtimeMode: "sse" | "polling" | "static";
};

export const APP_ROUTES: AppRouteMeta[] = [
  {
    path: "/",
    navLabel: "Trung tâm thông tin",
    title: "Trung tâm thông tin",
    subtitle: "Bản tóm lược vận hành tổng quan theo thời gian thực",
    keyQuestion: "Đang xảy ra điều gì trên toàn hệ thống?",
    realtimeMode: "static",
  },
  {
    path: "/dashboard",
    navLabel: "Bảng điều khiển",
    title: "Bảng điều khiển vận hành",
    subtitle: "Cockpit ingest, risk/incident và luồng suy luận agent",
    keyQuestion: "Hệ thống đang sống như thế nào ngay lúc này?",
    realtimeMode: "sse",
  },
  {
    path: "/map",
    navLabel: "Bản đồ tương tác",
    title: "Bản đồ tương tác",
    subtitle: "Bản đồ trạm, risk, incident và metadata hiện hành",
    keyQuestion: "Rủi ro đang ở đâu và trạm nào cần ưu tiên?",
    realtimeMode: "static",
  },
  {
    path: "/strategy",
    navLabel: "Kế hoạch cần duyệt",
    title: "Kế hoạch cần duyệt",
    subtitle: "Xem hệ thống đề xuất gì, có an toàn không và nên duyệt hay từ chối",
    keyQuestion: "Kế hoạch nào đang chờ bạn quyết định?",
    realtimeMode: "static",
  },
  {
    path: "/logs",
    navLabel: "Nhật ký thực thi",
    title: "Nhật ký thực thi",
    subtitle: "Xem hệ thống đã làm gì, kết quả ra sao và phản hồi sau chạy",
    keyQuestion: "Lần chạy gần nhất đã diễn ra như thế nào?",
    realtimeMode: "static",
  },
  {
    path: "/notifications",
    navLabel: "Thông báo",
    title: "Thông báo vận hành",
    subtitle: "Danh sách thông báo, trạng thái gửi và các mục cần xử lý",
    keyQuestion: "Có thông báo nào đang chờ đọc hoặc cần xử lý không?",
    realtimeMode: "static",
  },
  {
    path: "/history",
    navLabel: "Lịch sử dữ liệu",
    title: "Điều tra lịch sử dữ liệu",
    subtitle: "Điều tra dữ liệu theo thời gian, station và audit trail",
    keyQuestion: "Vì sao sự kiện đã xảy ra và xu hướng đang đi đâu?",
    realtimeMode: "static",
  },
];

function normalizePath(pathname: string): string {
  if (!pathname || pathname === "/") {
    return "/";
  }
  return pathname.endsWith("/") ? pathname.slice(0, -1) : pathname;
}

export function getRouteMeta(pathname: string): AppRouteMeta {
  const normalizedPath = normalizePath(pathname);
  const sorted = [...APP_ROUTES].sort((left, right) => right.path.length - left.path.length);
  return (
    sorted.find((route) =>
      route.path === "/"
        ? normalizedPath === "/"
        : normalizedPath === route.path || normalizedPath.startsWith(`${route.path}/`),
    ) ?? APP_ROUTES[0]
  );
}

export function buildBreadcrumb(pathname: string): string[] {
  const meta = getRouteMeta(pathname);
  if (meta.path === "/") {
    return ["Trung tâm thông tin"];
  }
  return ["Vận hành", meta.navLabel];
}
