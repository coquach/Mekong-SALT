# Đề xuất chỉnh proposal: Chuẩn hóa đơn vị mặn (17-04-2026)

## Mục tiêu
Đồng bộ giữa proposal (đang dùng `g/L`) và backend (đánh giá rule theo `dS/m`).

## Quy ước thống nhất
- Đơn vị chuẩn hệ thống: `dS/m`
- Đơn vị trình bày nghiệp vụ: `g/L`
- Công thức quy đổi dùng xuyên suốt: `1 dS/m ~= 0.64 g/L`

## Bảng ngưỡng thống nhất

| Mức rủi ro | Ngưỡng chuẩn (dS/m) | Tương đương (g/L) |
|---|---:|---:|
| Safe | `< 1.00` | `< 0.64` |
| Warning | `1.00 - 2.49` | `0.64 - 1.59` |
| Danger | `2.50 - 3.99` | `1.60 - 2.55` |
| Critical | `>= 4.00` | `>= 2.56` |

## Gợi ý thay câu trong proposal
- `Giữ độ mặn dưới 0.5 g/L` -> `Giữ độ mặn dưới 0.5 g/L (xấp xỉ 0.78 dS/m)`.
- `Vượt quá 2 g/L - mức nguy hiểm` -> `Vượt quá 2 g/L (xấp xỉ 3.13 dS/m) - mức nguy hiểm theo bối cảnh vận hành`.
- Bổ sung câu quy định: `Các luật đánh giá rủi ro của hệ thống được tính theo dS/m; g/L dùng cho diễn giải nghiệp vụ và báo cáo.`
