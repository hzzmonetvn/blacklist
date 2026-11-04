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
| **YouTube Adblock (AdGuard)** | `\|\|domain^$dnsrewrite=IP` | AdGuard Home (Filters / Custom rules) | `https://raw.githubusercontent.com/hzzmonetvn/blacklist/main/youtube-rewrite.txt` |
| **YouTube Adblock (Hosts)** | `IP domain` | /etc/hosts, Dnsmasq, Router | `https://raw.githubusercontent.com/hzzmonetvn/blacklist/main/youtube-hosts.txt` |

---

## ⚙️ Cấu trúc thư mục

```text
├── .github/workflows/
│   └── update-blacklist.yml  # Kịch bản GitHub Actions tự động build & commit
├── scripts/
│   └── build.py              # Engine xử lý: tải, parse, dedup, lọc whitelist & rewrite
├── sources.txt               # Danh sách URL các nguồn upstream
├── custom.txt                # Danh sách domain bạn tự chặn thêm
├── whitelist.txt             # Danh sách domain ngoại lệ không bao giờ bị chặn
├── rewrites.txt              # Cấu hình DNS rewrite (IP domain hoặc Adblock syntax)
├── blacklist.txt             # Kết quả xuất bản: Adblock syntax (||example.com^)
├── hosts.txt                 # Kết quả xuất bản: Hosts format (0.0.0.0 example.com)
├── domains.txt               # Kết quả xuất bản: Danh sách domain thuần
├── youtube-rewrite.txt       # Danh sách DNS rewrite chặn quảng cáo YouTube (AdGuard syntax)
└── youtube-hosts.txt         # Danh sách DNS rewrite chặn quảng cáo YouTube (Hosts format)
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

### 4. Quản lý DNS Rewrite / Chặn quảng cáo YouTube (`rewrites.txt`)
Cơ chế chặn quảng cáo YouTube trên Smart TV & Thiết bị di động hoạt động bằng cách điều hướng các tên miền YouTube (`youtube.com`, `googlevideo.com`, `youtubei.googleapis.com`) qua SNI Reverse Proxy tại Albania (`91.239.7.227`) - vùng không phân phối quảng cáo YouTube của Google:
* **`youtube-rewrite.txt`**: Cú pháp Adblock `$dnsrewrite` dành cho AdGuard Home (`Filters -> DNS blocklists` hoặc `Custom filtering rules`).
* **`youtube-hosts.txt`**: Cú pháp Hosts (`91.239.7.227 domain`) dành cho hệ thống router, Dnsmasq hoặc file hosts.

> ⚠️ **Lưu ý quan trọng khi dùng YouTube Rewrite:**
> 1. Do Albania không thuộc vùng cấp phép dịch vụ YouTube Music, việc áp dụng rewrite này sẽ làm **YouTube Music không phát được nhạc** (`Video không có sẵn`).
> 2. Trên AdGuard Home, khuyến nghị chỉ gán quy tắc rewrite này cho thiết bị Smart TV trong phần **Client settings**, tránh gán cho điện thoại nếu thường xuyên nghe YouTube Music.

---

## 👤 Tác giả
* **hzzmonetvn** (`https://github.com/hzzmonetvn`)
