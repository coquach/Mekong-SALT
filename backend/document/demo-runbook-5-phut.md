# Backlog Triển Khai 5 Phút

Mục tiêu của backlog này là chạy được full stack, giữ device-first MQTT làm
đường demo chính, và vẫn phơi được toàn bộ hệ thống từ ingest đến
feedback/memory.

## 1) Topology Duy Nhất (Docker Compose)

Services:

- `postgres`
- `redis`
- `mqtt` (Mosquitto)
- `backend`
- `frontend`

Yêu cầu runtime:

- `docker compose up -d` khởi động full stack.
- `backend` phụ thuộc healthcheck của `postgres`, `redis`, và `mqtt`.
- Mặc định runtime: `IOT_INGEST_MODE=mqtt`, `MQTT_ENABLED=true`.

## 2) Feature Flags Mặc Định Cho Demo Lõi

- `PUBSUB_ENABLED=false`
- `EARTH_ENGINE_ENABLED=false`
- `ACTIVE_MONITORING_ENABLED=true`
- `ACTIVE_MONITORING_MODE=active`

Giữ sẵn env để bật lại Pub/Sub và Earth Engine khi cần pitch mở rộng.

## 3) Surface FE Theo 6 Màn Hình Pitch

1. `Information Hub`: mở màn.
2. `Dashboard`: summary, timeline, latest risk/readings, ingest metrics,
	 notifications teaser.
3. `Interactive Map`: station, risk, incident, selected station.
4. `Strategy`: goals, pending plan, approve/reject.
5. `Action Logs`: execution batches, outcomes, latest feedback.
6. `History`: readings history, audit, risk context.

## 4) Runbook Demo 5 Phút

### 4.1 Khởi động

Từ thư mục `backend`:

```bash
docker compose up -d
```

Services mong đợi:

- Backend API: `http://localhost:8000`
- Frontend: `http://localhost:5173`
- Postgres: `localhost:5432`
- Redis: `localhost:6379`
- MQTT broker: `localhost:1883`

### 4.2 Seed dữ liệu nền

```bash
alembic upgrade head
python scripts/seed.py
```

### 4.3 Luồng trình diễn

1. Mở `Information Hub`.
2. Sang `Dashboard`.
3. Bơm frame MQTT bằng script simulation:

```bash
./.venv/Scripts/python.exe scripts/run_demo_simulation.py --scenario fast-approve-execute --transport mqtt --mqtt-broker-url localhost --mqtt-broker-port 1883
```

4. Sang `Interactive Map` để xem risk/incident đổi theo station.
5. Sang `Strategy` để duyệt plan.
6. Sang `Action Logs` để xem execution/feedback.
7. Sang `History` để chốt forensic + audit trail.

## 5) Definition of Done

- `docker compose up -d` chạy full stack không lỗi.
- MQTT ingest tạo được reading/risk/incident.
- Approval -> execution -> feedback đi hết vòng.
- FE 6 màn hiển thị đúng dữ liệu live từ BE.
- Runbook demo chạy end-to-end trong `<= 5 phút`.

## 6) Ghi Chú Vận Hành

- Nếu frontend không gọi được backend, kiểm tra `VITE_API_BASE_URL`.
- Nếu MQTT không ingest, kiểm tra topic `mekong/sensors/readings` và broker
	`localhost:1883`.
- Nếu dashboard đứng yên, mở lại stream `GET /api/v1/dashboard/stream`.
