# Proposal Unit Alignment (2026-04-17)

This note standardizes salinity units between the AGentFlow proposal narrative (`g/L`) and backend implementation (`dS/m`).

## 1) Canonical Unit Decision

- Backend canonical unit: `dS/m`
- Communication/display unit: `g/L` (derived)
- Conversion used consistently in code and docs:
	- `1 dS/m ~= 0.64 g/L`
	- `1 g/L ~= 1.56 dS/m`

## 2) Unified Threshold Table

| Risk band | Canonical threshold (dS/m) | Equivalent (g/L) |
|---|---:|---:|
| Safe | `< 1.00` | `< 0.64` |
| Warning | `1.00 - 2.49` | `0.64 - 1.59` |
| Danger | `2.50 - 3.99` | `1.60 - 2.55` |
| Critical | `>= 4.00` | `>= 2.56` |

## 3) Proposal Text Patch Guidance

When proposal sections mention only `g/L`, append canonical `dS/m` equivalents.

- Example objective sentence:
	- Before: `Giữ độ mặn dưới 0.5 g/L`
	- After: `Giữ độ mặn dưới 0.5 g/L (xấp xỉ 0.78 dS/m)`
- Example alert sentence:
	- Before: `Vượt quá 2 g/L - mức nguy hiểm`
	- After: `Vượt quá 2 g/L (xấp xỉ 3.13 dS/m) - mức nguy hiểm theo ngữ cảnh nghiệp vụ`
- Engine-policy statement to add:
	- `Các rule trong hệ thống được đánh giá theo dS/m; g/L chỉ dùng để trình bày và trao đổi nghiệp vụ.`

## 4) Scope of Backend Update

- Goal thresholds accept both `dS/m` and `g/L` input; system normalizes to `dS/m`.
- Sensor ingestion accepts salinity by `dS/m` or `g/L`; system normalizes to `dS/m`.
- Risk, dashboard, feedback, planning snapshots expose both units for traceability.
- Deterministic risk rules continue to evaluate by canonical thresholds in `dS/m`.
