# HzzMonet Blacklist

Hệ thống tự động hóa tổng hợp, chuẩn hóa và tối ưu danh sách chặn tên miền (Ad & Tracker Blocklist) từ các nguồn danh tiếng kết hợp bộ quy tắc cá nhân hóa.

Workflow chạy định kỳ mỗi ngày lúc **00:00 UTC** thông qua GitHub Actions để cập nhật các tên miền mới nhất từ các nguồn upstream.

---

## 📌 Liên kết đăng ký (Subscription URLs)

Bạn có thể thêm trực tiếp các liên kết raw bên dưới vào **AdGuard Home**, **Pi-hole**, **NextDNS**, **AdGuard App** hoặc **Brave/uBlock Origin**:

| Định dạng | Định dạng cú pháp | Phù hợp với | Đường dẫn Raw URL |
| :--- | :--- | :--- | :--- |
| **Adblock / AdGuard** | `\|\|example.com^` | AdGuard Home, NextDNS, uBlock Origin | `https://raw.githubusercontent.com/hzzmonetvn/blacklist/main/blacklist.txt` |
| **Hosts Format** | `0.0.0.0 example.com` | Pi-hole, /etc/hosts, DNSmasq | `https://raw.githubusercontent.com/hzzmonetvn/blacklist/main/hosts.txt` |
| **Plain Domains** | `example.com` | Tường lửa, Mikrotik, Router | `https://raw.githubusercontent.com/hzzmonetvn/blacklist/main/domains.txt` |

---

## ⚙️ Cấu trúc thư mục

```text
├── .github/workflows/
│   └── update-blacklist.yml  # Kịch bản GitHub Actions tự động build & commit
├── scripts/
│   └── build.py              # Engine xử lý: tải, parse, dedup, lọc whitelist
├── sources.txt               # Danh sách URL các nguồn upstream
├── custom.txt                # Danh sách domain bạn tự chặn thêm
├── whitelist.txt             # Danh sách domain ngoại lệ không bao giờ bị chặn
├── blacklist.txt             # Kết quả xuất bản: Adblock syntax
├── hosts.txt                 # Kết quả xuất bản: Hosts format
└── domains.txt               # Kết quả xuất bản: Danh sách domain thuần
```

---

## 🛠️ Hướng dẫn tùy chỉnh

### 1. Thêm nguồn chặn mới (`sources.txt`)
Mỗi dòng là một đường dẫn URL chứa danh sách chặn (hỗ trợ cả định dạng Adblock lẫn định dạng Hosts). Dòng bắt đầu bằng `#` được coi là ghi chú.
```text
https://example.com/blocklist.txt
```

### 2. Thêm domain chặn thủ công (`custom.txt`)
Thêm các domain bạn muốn chặn riêng cho bản thân:
```text
||bad-domain.com^
tracking-service.net
```

### 3. Loại trừ domain (Whitelist - `whitelist.txt`)
Nếu một dịch vụ quan trọng (ngân hàng, thanh toán, cổng xác thực) bị các nguồn upstream chặn nhầm, hãy thêm vào file này để loại trừ hoàn toàn khỏi danh sách đầu ra:
```text
@@||ds-analytics.digibank.vn^$important
example-payment.vn
```

---

## 👤 Tác giả
* **hzzmonetvn** (`https://github.com/hzzmonetvn`)
