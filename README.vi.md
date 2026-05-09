# Lexora AI (Tiếng Việt)

Lexora AI là công cụ dịch ebook mã nguồn mở (EPUB, MOBI, Word, Markdown) hỗ trợ nhiều nhà cung cấp AI. Có **ứng dụng để bàn (Flet)** và **CLI**.

Tài liệu tiếng Anh đầy đủ: [README.md](README.md).

---

## Cài đặt trên Windows (bản phát hành GitHub)

Bản được khuyến nghị: vào **[Releases](https://github.com/Lexora-Labs/lexora-ai/releases)** và tải gói phù hợp phiên bản Windows x64.


| Tệp tải về                   | Mô tả                                                                                                                                                                               |
| ---------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `LexoraAI-windows-amd64.zip` | Gói nén chứa `LexoraAI.exe` và thư mục `_internal`: giải nén vào thư mục bất kỳ (ví dụ `Desktop\LexoraAI`), sau đó chạy `LexoraAI.exe`. Thích hợp nếu **Windows SmartScreen** chặt. |
| `LexoraAI-windows-amd64.msi` | **Cài đặt MSI** vào máy (thường dưới `C:\Program Files\Lexora Labs\Lexora AI\`): phù hợp máy được quản trị rõ ràng, có shortcut Start Menu sau khi cài.                             |


### SmartScreen và bảo mật

Bản không ký chứng thư số có thể bị **Windows Defender SmartScreen** cảnh báo lần đầu. Nếu bạn tin nguồn tải (GitHub chính thức), chọn **Thông tin thêm → Chạy bất kỳ** để khởi động. Chứng thư và chữ ký mã không nằm trong phạm vi tài liệu này.

### Sau khi cài (Windows)

1. Mở **Lexora AI** từ **Start Menu**, shortcut máy tính, hoặc `LexoraAI.exe`.
2. Mở **Cài đặt (Settings)** và thêm ít nhất một **khóa API** nhà cung cấp đang dùng — hoặc đặt tệp `.env` cạnh ứng dụng như trong [README.md](README.md#configuration). Hướng dẫn chi tiết từng nhà cung cấp: **[docs/cau-hinh-api-key.vi.md](docs/cau-hinh-api-key.vi.md)**.
3. Dùng màn hình **Dịch (Translate)** để chọn sách và chạy việc; theo dõi **Việc (Jobs)** để biết tiến độ.

![Cài đặt - giao diện tiếng Việt](https://github.com/Lexora-Labs/lexora-ai/blob/main/docs/screenshots/settings-vi.png?raw=true)

**Dữ liệu và cấu hình cục bộ** của người dùng được lưu ở `%LOCALAPPDATA%\Lexora Labs\Lexora AI\` để không cần ghi vào Program Files sau khi cài MSI (tránh `Access denied`). Thư viện xuất mặc định và thông tin chi tiết hành vi lưu trữ vẫn giống bản README tiếng Anh.

---

## Chạy từ mã nguồn (Windows)

Giống bản README chính, dùng Python 3 và môi trường ảo:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -e .

python run_ui.py
python run_ui.py --no-browser
```

Gói giao diện dùng **Flet 0.23+** để có **biểu tượng Lexora trên cửa sổ / thanh tác vụ**. Tệp gốc: `lexora-ai-icon.ico` ở thư mục gốc kho chứa; bản MSI/EXE vẫn nhúng qua PyInstaller và WiX như trước.

---

## Tài liệu liên quan

- Tiếng Anh chi tiết: [README.md](README.md)
- Khóa API & nhà cung cấp: [docs/cau-hinh-api-key.vi.md](docs/cau-hinh-api-key.vi.md)
- Đóng gói Windows/WiX: [docs/windows-build-and-packaging.md](docs/windows-build-and-packaging.md)
- Giới hạn và lộ trình: các mục *Limitations* và *Roadmap* trong README tiếng Anh.

