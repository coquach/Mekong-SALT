# Mekong-SALT

Mekong-SALT là monorepo cho bài toán giám sát mặn, điều phối tác tử, phê duyệt và mô phỏng thực thi cho hệ thống thủy lợi. Repo này gồm backend FastAPI, frontend React + Vite, và bộ Docker Compose đầy đủ để chạy demo cục bộ từ một lệnh ở thư mục gốc.

## Cấu Trúc

- `backend/`: FastAPI backend, Alembic migrations, worker, demo scripts và tài liệu backend.
- `frontend/`: UI React + Vite cho dashboard, bản đồ, điều phối và log vận hành.
- `docker-compose.yml`: topology local cho PostgreSQL, Redis, MQTT, backend và frontend.
- `Dockerfile`: image backend dùng chung cho Docker Compose.

## Luồng Tài Liệu

Đọc theo thứ tự này để nắm nhanh toàn bộ dự án:

1. [README.md](README.md): tổng quan repo, cách chạy nhanh, và điểm vào chính.
2. [backend/README.md](backend/README.md): hướng dẫn backend, worker, API boundary, và local setup.
3. [demo-runbook-5-phut.md](demo-runbook-5-phut.md): runbook chạy demo từ seed đến simulate.
4. [backend/document/backend-db-erd.md](backend/document/backend-db-erd.md): sơ đồ dữ liệu backend.
5. [backend/document/rag-operations-guide.md](backend/document/rag-operations-guide.md): cách vận hành RAG và nguồn tri thức.
6. [backend/document/phase-rollout-pubsub-mqtt-gee-frontend.md](backend/document/phase-rollout-pubsub-mqtt-gee-frontend.md): kế hoạch rollout theo pha.
7. [backend/document/proposal_unit_alignment.md](backend/document/proposal_unit_alignment.md): chuẩn hóa cách nói về đơn vị và ngữ cảnh nghiệp vụ.

## Yêu Cầu

- Python 3.11+
- Node.js 20+
- Docker Desktop hoặc Docker Engine + Docker Compose plugin

## Cấu Hình

Backend đọc cấu hình từ `backend/.env`.

1. Sao chép `backend/.env.example` thành `backend/.env`.
2. Chỉnh các giá trị API key, DB URL, MQTT, Redis, Gemini, Zalo nếu cần.
3. Nếu chạy frontend riêng ngoài Docker, bảo đảm `VITE_API_BASE_URL` trỏ tới backend đang chạy, mặc định là `http://localhost:8000/api/v1`.

Docker Compose sẽ dùng `backend/.env` làm nền và override các biến hạ tầng cho container runtime như `DATABASE_URL`, `REDIS_URL`, `MQTT_*`, và các cờ demo cần thiết.

## Chạy Full Stack Bằng Docker

Từ thư mục gốc của repo:

```bash
docker compose up -d --build
```

Sau khi khởi động:

- Frontend: `http://localhost:5173`
- Backend health: `http://localhost:8000/api/v1/health`
- Backend API: `http://localhost:8000/api/v1`

Lệnh hữu ích:

```bash
docker compose logs -f backend
docker compose logs -f frontend
docker compose down
docker compose down -v
```

## Chạy Local Backend

Từ thư mục `backend/`:

```bash
py -3.13 -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
alembic upgrade head
./.venv/Scripts/python.exe -m uvicorn main:app --reload
```

Seed dữ liệu demo:

```bash
./.venv/Scripts/python.exe scripts/seed.py
```

Chạy demo MQTT cục bộ:

```bash
./.venv/Scripts/python.exe scripts/run_demo_simulation.py --scenario fast-approve-execute --transport mqtt --mqtt-broker-url localhost --mqtt-broker-port 1883
```

## Chạy Local Frontend

Từ thư mục `frontend/`:

```bash
npm ci
npm run dev
```

Frontend mặc định chạy ở `http://localhost:5173`.

## Workflow Chính

1. Sensor hoặc MQTT broker đẩy dữ liệu vào backend.
2. Worker đánh giá risk, tạo incident và sinh plan nếu cần.
3. Plan đi qua approval policy và execution mô phỏng.
4. Frontend đọc summary, trace, map station/gate và log vận hành.

## Quyết định quan trọng: cách đánh giá risk

Hệ thống không dùng risk “mơ hồ” theo cảm tính. Risk được đánh giá bằng **rule deterministic** để đảm bảo ổn định, dễ giải thích, và dễ demo.

### Nguyên tắc đánh giá

- Đơn vị canonical để lưu và so sánh là `dS/m`.
- Reading mới nhất là nguồn chính để quyết định risk.
- Trend chỉ làm xấu thêm hoặc giữ nguyên mức risk, không kéo giảm một cách tuỳ ý.
- External context như thời tiết, tide, hoặc Earth Engine chỉ là yếu tố bổ trợ.
- Nếu dữ liệu AI hoặc context ngoài lỗi, hệ thống vẫn ra quyết định từ rule cốt lõi.

### Risk scoring matrix

| Band | Điều kiện salinity | Ý nghĩa vận hành | Hành động hệ thống |
|---|---|---|---|
| Safe | `< 1.00 dS/m` | Mức an toàn | Chỉ cập nhật dashboard |
| Warning | `>= 1.00` và `< 2.50 dS/m` | Bắt đầu cần theo dõi chặt | Ghi risk warning, chuẩn bị context |
| Danger | `>= 2.50` và `< 4.00 dS/m` | Nguy cơ cao | Tạo incident và draft plan |
| Critical | `>= 4.00 dS/m` | Nguy cấp | Ưu tiên cao, cần approval nhanh |

### Yếu tố điều chỉnh risk

| Yếu tố | Tác động |
|---|---|
| Trend tăng nhanh | Có thể đẩy risk lên 1 band nếu vượt ngưỡng hỗ trợ |
| Trend giảm | Ghi trong rationale, nhưng không tự động kéo risk xuống dưới band salinity |
| Wind / tide mạnh | Tăng mức cảnh giác khi reading đã ở band warning trở lên |
| Confidence thấp | Tăng mức cần review của operator |
| Dữ liệu thiếu / lỗi | Hệ thống fallback về trạng thái safe-observe hoặc yêu cầu kiểm tra |

### Công thức diễn giải nội bộ

Risk cuối cùng được hiểu theo logic:

`final_risk = max(risk_from_salinity, risk_from_trend_modifier, risk_from_context_modifier)`

Trong đó:

- `risk_from_salinity` là band chính.
- `risk_from_trend_modifier` chỉ có tác dụng làm xấu thêm.
- `risk_from_context_modifier` chỉ có tác dụng khuếch đại khi context đủ tin cậy.

### Vì sao chọn cách này

- Dễ trình bày cho judge vì rule rõ ràng.
- Dễ kiểm thử bằng seed data và demo scenarios.
- Giảm hallucination và giảm sai lệch giữa frontend, API, và worker.
- Phù hợp với một hệ thống vận hành thực tế, nơi độ ổn định quan trọng hơn “AI đoán mò”.

## API Chính

- Sensor ingest: `/api/v1/sensors/ingest`
- Reading query: `/api/v1/readings/*`
- Plan query: `/api/v1/plans/*`
- Agent observability: `/api/v1/agent/runs*`
- Dashboard: `/api/v1/dashboard/*`
- Approvals: `/api/v1/approvals/*`
- Feedback: `/api/v1/feedback/*`

## Tài Liệu Phụ Trợ

- Backend chi tiết: [backend/README.md](backend/README.md)
- Runbook demo: [demo-runbook-5-phut.md](demo-runbook-5-phut.md)
- ERD backend: [backend/document/backend-db-erd.md](backend/document/backend-db-erd.md)
- RAG guide: [backend/document/rag-operations-guide.md](backend/document/rag-operations-guide.md)
- Rollout plan: [backend/document/phase-rollout-pubsub-mqtt-gee-frontend.md](backend/document/phase-rollout-pubsub-mqtt-gee-frontend.md)
