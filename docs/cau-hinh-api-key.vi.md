# Hướng dẫn lấy và cấu hình khóa API nhà cung cấp (Lexora AI)

Tài liệu này hướng dẫn cách **lấy khóa API** và đưa vào Lexora AI cho từng nhà cung cấp. Bản tiếng Anh tương ứng: [provider-api-key-guide.md](provider-api-key-guide.md).

**Lưu ý an toàn**

- Không dán khóa bí mật vào chat, ticket hay mã nguồn công khai.
- Ưu tiên chỉ trong tệp **`.env` cục bộ** trên máy bạn hoặc màn hình **Cài đặt** của ứng dụng.
- Đổi khóa ngay nếu nghi ngờ bị lộ.

---

## OpenAI

Cổng truy cập: [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)

Các bước:

1. Đăng nhập **OpenAI Platform**.
2. Mở mục **API keys**.
3. **Create new secret key** và sao chép.

Biến môi trường bắt buộc: `OPENAI_API_KEY`

Ví dụ `.env`:

```env
OPENAI_API_KEY=mã_của_bạn
```

---

## Azure OpenAI

Cổng truy cập: [https://portal.azure.com](https://portal.azure.com)

Các bước:

1. Tạo hoặc mở resource **Azure OpenAI**.
2. Vào **Keys and Endpoint** — sao chép điểm cuối (endpoint) và một trong hai khóa.
3. Trong **Azure AI Foundry Studio** hoặc giao diện triển khai mô hình của resource, đảm bảo có **deployment** đúng kiểu mô hình bạn muốn dùng và ghi nhớ **tên deployment**.

Biến bắt buộc:

- `AZURE_OPENAI_ENDPOINT`
- `AZURE_OPENAI_DEPLOYMENT`
- `AZURE_OPENAI_KEY` hoặc `AZURE_OPENAI_API_KEY`

Ví dụ:

```env
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=tên-deployment
AZURE_OPENAI_KEY=mã_của_bạn
```

---

## Azure AI Foundry

Cổng truy cập: [https://ai.azure.com](https://ai.azure.com)

Các bước:

1. Mở **dự án Foundry** của bạn.
2. Trong **Settings** / resource, lấy **endpoint** và **API key**.
3. Ghi nhận **tên mô hình** dùng cho infer.

Biến bắt buộc:

- `AZURE_AI_FOUNDRY_ENDPOINT`
- `AZURE_AI_FOUNDRY_API_KEY`
- `AZURE_AI_FOUNDRY_MODEL`

Ví dụ:

```env
AZURE_AI_FOUNDRY_ENDPOINT=https://endpoint-của-bạn/
AZURE_AI_FOUNDRY_API_KEY=mã_của_bạn
AZURE_AI_FOUNDRY_MODEL=tên-model
```

---

## Gemini

Cổng truy cập: [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)

Các bước:

1. Đăng nhập **Google AI Studio**.
2. Tạo **API key** và sao chép.

Biến bắt buộc: `GOOGLE_API_KEY`

Tùy chọn: `GEMINI_MODEL` — id mô hình (mặc định có thể là `gemini-2.0-flash` tùy phiên bản Lexora; đổi nếu vùng hoặc tài khoản không hỗ trợ).

Ví dụ:

```env
GOOGLE_API_KEY=mã_của_bạn
# GEMINI_MODEL=gemini-2.5-flash
```

---

## Anthropic (Claude)

Cổng truy cập: [https://console.anthropic.com/settings/keys](https://console.anthropic.com/settings/keys)

Các bước:

1. Đăng nhập **Anthropic Console**.
2. Tạo **API key**.

Biến bắt buộc: `ANTHROPIC_API_KEY`

Ví dụ:

```env
ANTHROPIC_API_KEY=mã_của_bạn
```

---

## Qwen (DashScope)

Cổng truy cập: [https://dashscope.console.aliyun.com/](https://dashscope.console.aliyun.com/)

Các bước:

1. Đăng nhập **DashScope**.
2. Tạo **API key**.

Biến được chấp nhận: `DASHSCOPE_API_KEY` hoặc `QWEN_API_KEY`

Ví dụ:

```env
DASHSCOPE_API_KEY=mã_của_bạn
```

---

## Mẫu `.env` gộp (điền phần bạn dùng)

```env
OPENAI_API_KEY=

AZURE_OPENAI_ENDPOINT=
AZURE_OPENAI_DEPLOYMENT=
AZURE_OPENAI_KEY=

AZURE_AI_FOUNDRY_ENDPOINT=
AZURE_AI_FOUNDRY_API_KEY=
AZURE_AI_FOUNDRY_MODEL=

GOOGLE_API_KEY=
ANTHROPIC_API_KEY=

DASHSCOPE_API_KEY=
# QWEN_API_KEY=
```

---

## Kiểm tra nhanh bằng CLI

Chạy từ thư mục gốc kho `lexora-ai` sau khi đã cấu hình `.env`. Dùng một EPUB mẫu (ví dụ IDPF) đặt trong `samples/` — thay đường dẫn phù hợp.

```powershell
python -m lexora.cli translate .\samples\accessible_epub_3.epub .\samples\out-openai.epub --target vi --service openai --limit-docs 1
python -m lexora.cli translate .\samples\accessible_epub_3.epub .\samples\out-azure-openai.epub --target vi --service azure-openai --limit-docs 1
python -m lexora.cli translate .\samples\accessible_epub_3.epub .\samples\out-azure-foundry.epub --target vi --service azure-foundry --limit-docs 1
python -m lexora.cli translate .\samples\accessible_epub_3.epub .\samples\out-gemini.epub --target vi --service gemini --limit-docs 1
python -m lexora.cli translate .\samples\accessible_epub_3.epub .\samples\out-anthropic.epub --target vi --service anthropic --limit-docs 1
python -m lexora.cli translate .\samples\accessible_epub_3.epub .\samples\out-qwen.epub --target vi --service qwen --limit-docs 1
```

Chi tiết mẫu EPUB và bản quyền: [testing-epub-samples.md](testing-epub-samples.md).