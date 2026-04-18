# Hướng Dẫn Từ Seed Đến Simulate

Tài liệu này mô tả đường chạy demo chuẩn cho backend Mekong-SALT, theo thứ tự:

1. Khởi động hạ tầng.
2. Chạy migrate.
3. Seed dữ liệu demo.
4. Nạp RAG sample corpus.
5. Xem catalog scenario.
6. Chạy simulate.
7. Kiểm tra kết quả trên UI hoặc API.

## 0) Bộ Lệnh Cần Thiết

Nếu cần chạy nhanh theo thứ tự chuẩn, dùng đúng các lệnh sau:

```bash
docker compose up -d
./.venv/Scripts/python.exe -m alembic upgrade head
./.venv/Scripts/python.exe scripts/seed.py
./.venv/Scripts/python.exe scripts/ingest_rag_samples.py
./.venv/Scripts/python.exe scripts/run_demo_simulation.py --scenario fast-approve-execute --transport mqtt --mqtt-broker-url localhost --mqtt-broker-port 1883 --frame-pause-seconds 10 --timeout-seconds 300
curl http://localhost:8000/api/v1/plans?limit=10
curl http://localhost:8000/api/v1/execution-batches?limit=10
curl http://localhost:8000/api/v1/action-outcomes?limit=10
curl http://localhost:8000/api/v1/agent/runs?limit=10
```

Nếu muốn chạy kịch bản timeout auto-reject thay vì fast approve:

```bash
./.venv/Scripts/python.exe scripts/run_demo_simulation.py --scenario critical-timeout-replan --transport mqtt --mqtt-broker-url localhost --mqtt-broker-port 1883 --frame-pause-seconds 10 --timeout-seconds 300
```

Nếu chỉ muốn xem catalog scenario trước khi chạy:

```bash
./.venv/Scripts/python.exe scripts/run_demo_scenarios.py --scenario all
```

## 1) Điều kiện trước khi chạy

Yêu cầu tối thiểu:

- Docker đã sẵn sàng.
- Có file `backend/.env`.
- MQTT broker chạy ở `localhost:1883` nếu muốn demo theo đường MQTT.
- Frontend và backend dùng cùng bộ dữ liệu demo.

Các service trong `docker compose`:

- `postgres`
- `redis`
- `mqtt` (Mosquitto)
- `backend`
- `frontend`

## 2) Khởi động hệ thống

Từ thư mục `backend`:

```bash
docker compose up -d
```

Kiểm tra các URL chính:

- Backend API: `http://localhost:8000`
- Frontend: `http://localhost:5173`
- Postgres: `localhost:5432`
- Redis: `localhost:6379`
- MQTT broker: `localhost:1883`

## 3) Chạy migrate

Migrate tạo schema và đồng bộ model với database.

```bash
./.venv/Scripts/python.exe -m alembic upgrade head
```

Nếu dùng môi trường Linux/macOS, đổi thành:

```bash
python -m alembic upgrade head
```

## 4) Seed dữ liệu demo

Seed hiện tại có cơ chế reset demo region trước khi nạp lại, nên mỗi lần chạy sẽ đưa dữ liệu demo về trạng thái sạch.

```bash
./.venv/Scripts/python.exe scripts/seed.py
```

Seed sẽ:

- Xoá dữ liệu demo cũ của region `TIEN-GIANG-GO-CONG`.
- Tạo lại region, station, gate, reading, risk, incident, plan.
- Đồng bộ metadata trạm/cống để UI và simulator có dữ liệu thật để bám.

Nếu bạn chỉ muốn seed lại dữ liệu và không chạy toàn bộ setup, dùng lệnh này là đủ.

## 5) Nạp RAG sample corpus

RAG sample corpus cần có trước khi chạy scenario liên quan đến provenance.

```bash
./.venv/Scripts/python.exe scripts/ingest_rag_samples.py
```

Lệnh này chỉ nạp các source mới hoặc source đã được sync theo `source_uri`.

## 6) Dùng script setup một lần

Nếu muốn chạy đủ migrate + seed + ingest trong một lệnh:

```bash
./.venv/Scripts/python.exe scripts/run_demo_setup.py
```

Script này sẽ:

- kiểm tra timeout demo,
- chạy migrate,
- seed lại dữ liệu demo,
- ingest RAG sample corpus.

Các flag hữu ích:

```bash
./.venv/Scripts/python.exe scripts/run_demo_setup.py --skip-migrations
./.venv/Scripts/python.exe scripts/run_demo_setup.py --skip-seed
./.venv/Scripts/python.exe scripts/run_demo_setup.py --skip-ingest
./.venv/Scripts/python.exe scripts/run_demo_setup.py --strict-timeout-config
```

## 7) Xem danh sách scenario

Trước khi simulate, nên xem catalog để biết scenario nào có lệnh trước/sau:

```bash
./.venv/Scripts/python.exe scripts/run_demo_scenarios.py --list
```

In chi tiết toàn bộ scenario:

```bash
./.venv/Scripts/python.exe scripts/run_demo_scenarios.py --scenario all
```

Mỗi scenario hiện được chia thành 3 phần:

- `Trước demo`: lệnh chuẩn bị state.
- `Steps`: lệnh chạy chính.
- `Sau demo`: lệnh kiểm tra kết quả.

## 8) Chạy simulate

### 8.1 Scenario khuyến nghị

Scenario dễ demo nhất là `fast-approve-execute`:

```bash
./.venv/Scripts/python.exe scripts/run_demo_simulation.py --scenario fast-approve-execute --transport mqtt --mqtt-broker-url localhost --mqtt-broker-port 1883 --frame-pause-seconds 10 --timeout-seconds 300
```

Ý nghĩa:

- sensor frames được bắn theo MQTT,
- plan được tạo từ ingest thật,
- script chờ plan pending_approval,
- operator duyệt plan qua API approval,
- backend simulate execution batch,
- script đẩy thêm một reading hậu execution để backend nhận feedback.

### 8.2 Scenario timeout auto-reject

```bash
./.venv/Scripts/python.exe scripts/run_demo_simulation.py --scenario critical-timeout-replan --transport mqtt --mqtt-broker-url localhost --mqtt-broker-port 1883 --frame-pause-seconds 10 --timeout-seconds 300
```

Scenario này dùng để demo:

- salinity leo thang,
- plan vào trạng thái `pending_approval`,
- timeout tự chuyển sang reject,
- hệ thống tạo plan mới cho nhịp tiếp theo.

### 8.3 Scenario provenance / RAG

```bash
./.venv/Scripts/python.exe scripts/run_demo_simulation.py --scenario rag-provenance-drilldown --json
```

Scenario này dùng để xem:

- trace truy hồi,
- top citations,
- knowledge context preview.

## 9) Ý nghĩa các flag của simulate

- `--scenario`: chọn kịch bản.
- `--transport mqtt|http`: chọn đường gửi dữ liệu sensor.
- `--mqtt-broker-url`: host MQTT broker.
- `--mqtt-broker-port`: port MQTT broker.
- `--frame-pause-seconds`: khoảng nghỉ giữa các frame, mặc định 10 giây.
- `--timeout-seconds`: thời gian chờ cho các bước poll, mặc định 300 giây.
- `--station-code`: ép vào một trạm cụ thể, nếu muốn demo đích danh.
- `--keep-open-incidents`: không tự đóng incident cũ trước khi bắn frame mới.
- `--no-post-execute-reading`: tắt reading hậu execution cho scenario có execute.
- `--json`: in kết quả dạng JSON.

## 10) Luồng chạy chi tiết theo thứ tự

### Bước 1: seed

```bash
./.venv/Scripts/python.exe scripts/seed.py
```

Đầu ra mong đợi:

- region demo được reset và tạo lại,
- station/gate có metadata đầy đủ,
- reading, risk, incident, plan ban đầu có sẵn.

### Bước 2: nạp RAG

```bash
./.venv/Scripts/python.exe scripts/ingest_rag_samples.py
```

Đầu ra mong đợi:

- corpus sample được sync,
- các tài liệu SOP, guideline, threshold, casebook sẵn sàng cho planning trace.

### Bước 3: kiểm tra scenario

```bash
./.venv/Scripts/python.exe scripts/run_demo_scenarios.py --scenario fast-approve-execute
```

Đầu ra mong đợi:

- nhìn thấy rõ lệnh `Trước demo`,
- lệnh `Steps`,
- lệnh `Sau demo`.

### Bước 4: simulate

```bash
./.venv/Scripts/python.exe scripts/run_demo_simulation.py --scenario fast-approve-execute --transport mqtt --mqtt-broker-url localhost --mqtt-broker-port 1883
```

Đầu ra mong đợi:

- sensor stream được publish,
- plan xuất hiện trong trạng thái pending_approval,
- plan được approve rồi chuyển sang approved/simulated,
- execution batch được tạo,
- feedback/post-execution reading được ghi nhận.

### Bước 5: kiểm tra kết quả

Các API hay dùng để xác minh:

```bash
curl http://localhost:8000/api/v1/plans?limit=10
curl http://localhost:8000/api/v1/execution-batches?limit=10
curl http://localhost:8000/api/v1/action-outcomes?limit=10
curl http://localhost:8000/api/v1/agent/runs?limit=10
```

## 11) Gợi ý runbook nhanh nhất

Nếu bạn muốn chạy nhanh nhất từ đầu đến cuối:

```bash
docker compose up -d
./.venv/Scripts/python.exe -m alembic upgrade head
./.venv/Scripts/python.exe scripts/seed.py
./.venv/Scripts/python.exe scripts/ingest_rag_samples.py
./.venv/Scripts/python.exe scripts/run_demo_simulation.py --scenario fast-approve-execute --transport mqtt --mqtt-broker-url localhost --mqtt-broker-port 1883 --frame-pause-seconds 10 --timeout-seconds 300
```

## 12) Lưu ý vận hành

- Nếu backend chưa chạy, kiểm tra `docker compose logs backend`.
- Nếu MQTT không ingest, kiểm tra broker `localhost:1883` và topic `mekong/sensors/readings`.
- Nếu simulate bị timeout, tăng `--timeout-seconds`.
- Nếu muốn demo sạch lại từ đầu, chỉ cần chạy lại `scripts/seed.py` vì seed đã tự reset dữ liệu demo.

## 13) Ma Trận Đánh Giá Risk

Bảng này dùng để giải thích nhanh cách engine hiện tại ra quyết định:

| Tín hiệu đầu vào | Engine làm gì | Kết quả / ý nghĩa |
|---|---|---|
| Salinity dưới `1.00 dS/m` | Gán `safe` | Mức an toàn, chưa cần alert |
| Salinity từ `1.00` đến dưới `2.50 dS/m` | Gán `warning` | Bắt đầu theo dõi chặt hơn |
| Salinity từ `2.50` đến dưới `4.00 dS/m` | Gán `danger` | Cần cảnh báo và chuẩn bị phản ứng |
| Salinity từ `4.00 dS/m` trở lên | Gán `critical` | Mức nguy cấp, cần xử lý ngay |
| Trend tăng mạnh | Đẩy risk lên 1 bậc nếu đủ ngưỡng | Phản ánh salinity đang xấu nhanh hơn |
| Trend giảm | Ghi nhận trong rationale nhưng không kéo risk xuống dưới band salinity hiện tại | Tránh false negative khi nước vẫn còn mặn |
| Wind/tide mạnh | Chỉ cộng thêm khi reading đã ít nhất là `warning` | Modifier, không được override reading an toàn |
| Đánh giá theo region | Chọn reading mới nhất theo thời gian | Tránh lấy mẫu “mặn nhất” nhưng không phải mới nhất |

Một cách đọc đơn giản:

- `band salinity` là sàn.
- `trend` chỉ làm xấu thêm.
- `external context` chỉ khuếch đại.
- `mới nhất` thắng, không phải `mặn nhất`.
