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

Nếu cần chạy nhanh theo thứ tự chuẩn, dùng đúng các lệnh sau từ thư mục gốc của repo:

```bash
docker compose up -d --build
cd backend
./.venv/Scripts/python.exe -m alembic upgrade head
./.venv/Scripts/python.exe scripts/seed.py
./.venv/Scripts/python.exe scripts/ingest_rag_samples.py
./.venv/Scripts/python.exe scripts/run_demo_simulation.py --scenario fast-approve-execute --mqtt-broker-url localhost --mqtt-broker-port 1883 --frame-pause-seconds 10 --timeout-seconds 300
curl http://localhost:8000/api/v1/plans?limit=10
curl http://localhost:8000/api/v1/execution-batches?limit=10
curl http://localhost:8000/api/v1/action-outcomes?limit=10
curl http://localhost:8000/api/v1/agent/runs?limit=10
```

Lưu ý quan trọng: trong cấu hình local Docker Compose, backend container dùng Postgres nội bộ của compose, còn `backend/.env` trên host đã được đặt để trỏ về Postgres được publish ở `localhost:5432`. Vì vậy, nếu bạn chạy migrate/seed/ingest bằng `backend/.venv`, hãy dùng trực tiếp bộ `.env` hiện tại, không cần override thủ công `DATABASE_URL`. Backend container và host scripts đều đang đọc cùng một database local.

Nếu muốn chạy kịch bản timeout auto-reject thay vì fast approve:

```bash
./.venv/Scripts/python.exe scripts/run_demo_simulation.py --scenario critical-timeout-replan --mqtt-broker-url localhost --mqtt-broker-port 1883 --frame-pause-seconds 10 --timeout-seconds 300
```

Nếu muốn demo nhánh cảnh giác rồi hồi phục dần thay vì leo thang tới critical:

```bash
./.venv/Scripts/python.exe scripts/run_demo_simulation.py --scenario warning-observe-recover --mqtt-broker-url localhost --mqtt-broker-port 1883 --frame-pause-seconds 10 --timeout-seconds 300
```

Nếu muốn bắn thử thông báo qua Zalo cho demo:

```bash
set ZALO_NOTIFICATIONS_ENABLED=true
set ZALO_OA_ACCESS_TOKEN=your-access-token
set ZALO_OA_RECIPIENT_USER_ID=your-zalo-user-id
./.venv/Scripts/python.exe scripts/send_demo_zalo_notification.py --subject "Mekong-SALT demo" --message "Tin nhắn demo qua Zalo từ backend."
```

//hiện tại ko test được zalo

Nếu dùng PowerShell:

```powershell
$env:ZALO_NOTIFICATIONS_ENABLED = "true"
$env:ZALO_OA_ACCESS_TOKEN = "your-access-token"
$env:ZALO_OA_RECIPIENT_USER_ID = "your-zalo-user-id"
./.venv/Scripts/python.exe scripts/send_demo_zalo_notification.py --subject "Mekong-SALT demo" --message "Tin nhắn demo qua Zalo từ backend."
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

Từ thư mục gốc:

```bash
docker compose up -d --build
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
cd backend
./.venv/Scripts/python.exe -m alembic upgrade head
```

Nếu dùng môi trường Linux/macOS, đổi thành:

```bash
python -m alembic upgrade head
```

## 4) Seed dữ liệu demo

Seed hiện tại có cơ chế reset demo region trước khi nạp lại, nên mỗi lần chạy sẽ đưa dữ liệu demo về trạng thái sạch.

Nếu bạn đang chạy demo local bằng Docker Compose, chỉ cần dùng `backend/.env` hiện tại rồi seed trực tiếp.

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

Nếu môi trường local chưa có Vertex AI credentials, bước ingest có thể báo lỗi embedding. Trong trường hợp đó, core demo vẫn chạy được, nhưng scenario provenance / RAG drilldown chỉ đầy đủ khi corpus đã được ingest thành công trong đúng database của compose.

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

Script này sẽ tự dùng cấu hình trong `backend/.env`, nên không cần set `DATABASE_URL` bằng tay cho đường chạy chuẩn.

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

### Bảng kịch bản đầy đủ

| Scenario | Khi nào dùng | Lệnh chính | Điểm nhấn demo |
|---|---|---|---|
| `fast-approve-execute` | Muốn thể hiện luồng chuẩn end-to-end trong thời gian ngắn | `./.venv/Scripts/python.exe scripts/run_demo_simulation.py --scenario fast-approve-execute --mqtt-broker-url localhost --mqtt-broker-port 1883 --frame-pause-seconds 10 --timeout-seconds 300` | Salinity nền, trend tăng, approval, execution mô phỏng, feedback |
| `critical-timeout-replan` | Muốn thể hiện cơ chế auto-reject và lập plan mới | `./.venv/Scripts/python.exe scripts/run_demo_simulation.py --scenario critical-timeout-replan --mqtt-broker-url localhost --mqtt-broker-port 1883 --frame-pause-seconds 10 --timeout-seconds 300` | Escalation lên critical theo sensor-first engine, nhiều nhịp trend hơn, timeout, replan |
| `warning-observe-recover` | Muốn thể hiện posture cảnh giác và phục hồi an toàn | `./.venv/Scripts/python.exe scripts/run_demo_simulation.py --scenario warning-observe-recover --mqtt-broker-url localhost --mqtt-broker-port 1883 --frame-pause-seconds 10 --timeout-seconds 300` | Warning band, trend ổn định qua nhiều nhịp, recovery window |
| `rag-provenance-drilldown` | Muốn soi trace truy hồi và nguồn tri thức | `./.venv/Scripts/python.exe scripts/run_demo_simulation.py --scenario rag-provenance-drilldown --json` | Citations, knowledge context, trace provenance, trend window đầy hơn |

## 8) Chạy simulate

### 8.1 Scenario khuyến nghị

Scenario dễ demo nhất là `fast-approve-execute`:

```bash
./.venv/Scripts/python.exe scripts/run_demo_simulation.py --scenario fast-approve-execute --mqtt-broker-url localhost --mqtt-broker-port 1883 --frame-pause-seconds 10 --timeout-seconds 300
```

Ý nghĩa:

- sensor frames được bắn theo MQTT,
- plan được tạo từ ingest thật,
- risk engine bám salinity nền, trend gần đây qua nhiều frame và weather/tide mới,
- script chờ plan pending_approval,
- operator duyệt plan qua API approval,
- backend simulate execution batch,
- script đẩy thêm một reading hậu execution để backend nhận feedback.

### 8.2 Scenario timeout auto-reject

```bash
./.venv/Scripts/python.exe scripts/run_demo_simulation.py --scenario critical-timeout-replan --mqtt-broker-url localhost --mqtt-broker-port 1883 --frame-pause-seconds 10 --timeout-seconds 300
```

Scenario này dùng để demo:

- salinity leo thang qua band danger/critical,
- thêm một nhịp trung gian để trend window ổn định hơn trước khi chạm critical,
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

### 8.4 Scenario warning observe / recovery

```bash
./.venv/Scripts/python.exe scripts/run_demo_simulation.py --scenario warning-observe-recover --mqtt-broker-url localhost --mqtt-broker-port 1883 --frame-pause-seconds 10 --timeout-seconds 300
```

Scenario này dùng để demo:

- mức cảnh báo trung gian thay vì chỉ critical escalation,
- thêm một frame warning nữa để window trend rõ hơn,
- posture quan sát thận trọng trước khi phục hồi,
- luồng recovery window và rule quyết định bảo thủ,
- MQTT publisher chỉ cần broker sẵn sàng để bắn sensor frames.

### 8.5 Kịch bản full demo đề xuất

Nếu bạn muốn demo đầy đủ trong một buổi trình bày, nên chạy theo thứ tự sau:

1. **Fast approve execute** để mở màn bằng luồng chuẩn.

```bash
./.venv/Scripts/python.exe scripts/run_demo_simulation.py --scenario fast-approve-execute --mqtt-broker-url localhost --mqtt-broker-port 1883 --frame-pause-seconds 10 --timeout-seconds 300
```

2. **Critical timeout replan** để cho thấy hệ thống biết tự xử lý khi plan bị kẹt approval.

```bash
./.venv/Scripts/python.exe scripts/run_demo_simulation.py --scenario critical-timeout-replan --mqtt-broker-url localhost --mqtt-broker-port 1883 --frame-pause-seconds 10 --timeout-seconds 300
```

3. **Warning observe recover** để nhấn mạnh posture bảo thủ và recovery an toàn.

```bash
./.venv/Scripts/python.exe scripts/run_demo_simulation.py --scenario warning-observe-recover --mqtt-broker-url localhost --mqtt-broker-port 1883 --frame-pause-seconds 10 --timeout-seconds 300
```

4. **RAG provenance drilldown** để kết bằng phần giải thích bằng chứng và nguồn tri thức.

```bash
./.venv/Scripts/python.exe scripts/run_demo_simulation.py --scenario rag-provenance-drilldown --json
```

Trình tự này giúp câu chuyện demo đi theo logic:

- data -> risk -> plan -> approval -> execution,
- escalation -> timeout -> recovery,
- cuối cùng là provenance và reasoning trace.

## 9) Ý nghĩa các flag của simulate

- `--scenario`: chọn kịch bản.
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
./.venv/Scripts/python.exe scripts/run_demo_simulation.py --scenario fast-approve-execute --mqtt-broker-url localhost --mqtt-broker-port 1883
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
docker compose up -d --build
cd backend
./.venv/Scripts/python.exe -m alembic upgrade head
./.venv/Scripts/python.exe scripts/seed.py
./.venv/Scripts/python.exe scripts/ingest_rag_samples.py
./.venv/Scripts/python.exe scripts/run_demo_simulation.py --scenario fast-approve-execute --mqtt-broker-url localhost --mqtt-broker-port 1883 --frame-pause-seconds 10 --timeout-seconds 300
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

