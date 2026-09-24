<div align="center">

# 📸 Photo Print Arranger
### Công cụ tự động dàn trang in ảnh & photocopy khổ A4 chuẩn tỉ lệ

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![UI](https://img.shields.io/badge/GUI-CustomTkinter-0ea5e9?logo=windows&logoColor=white)](https://github.com/TomSchimansky/CustomTkinter)
[![Output](https://img.shields.io/badge/Output-Word%20%7C%20PDF-22c55e?logo=microsoftword&logoColor=white)](https://github.com/)
[![Platform](https://img.shields.io/badge/Platform-Windows-0284c7?logo=windows)](https://microsoft.com)
[![License](https://img.shields.io/badge/License-MIT-gray)](LICENSE)

*Giải pháp nhanh chóng, chính xác giúp sắp xếp hàng loạt ảnh vào trang giấy A4 mà không bị méo hình, không giảm độ phân giải, tự động căn lề và sẵn sàng mang in ấn hoặc photocopy.*

---

</div>

## 📌 Tại sao cần Photo Print Arranger?

Khi in ảnh thủ công bằng Word hoặc công cụ in mặc định:
- ❌ Ảnh thường bị kéo giãn tỉ lệ, méo mặt nhân vật/chủ thể.
- ❌ Kích thước giữa các ảnh không đều nhau, phải căn chỉnh thủ công từng ảnh rất mất thời gian.
- ❌ Dễ bị nhảy trang trắng khi in ấn.

**Photo Print Arranger** giải quyết triệt để vấn đề trên chỉ với **1 cú click chuột**.

---

## ✨ Tính năng cốt lõi

| Tính năng | Chi tiết |
| :--- | :--- |
| **Khóa chuẩn tỉ lệ (Aspect Ratio)** | Giữ nguyên 100% tỉ lệ gốc của ảnh, tuyệt đối không bị bóp méo. |
| **Đồng nhất kích thước** | Tự động tính toán toán học để mọi ảnh trên tài liệu có **kích thước bằng nhau 100%**. |
| **Bảo toàn chất lượng (Lossless)** | Nhúng trực tiếp file ảnh gốc độ phân giải cao vào file Word, không qua nén giảm chất lượng. |
| **Bố cục đa dạng** | Hỗ trợ chia `1`, `2`, `4`, `6`, `8`, `9`, `12` ảnh/trang theo **Khổ Ngang (Landscape)** hoặc **Khổ Dọc (Portrait)**. |
| **Xuất đa định dạng** | Xuất trực tiếp file **Word (`.docx`)**, **PDF (`.pdf`)** hoặc **Cả hai**. |
| **Giao diện Popup hiện đại** | Thiết kế dạng hộp thoại nhỏ gọn, bo góc chuẩn Windows 11, tự động căn giữa màn hình, không cần cuộn trang. |
| **Đường viền cắt thông minh** | Tùy chọn bật viền đứt mờ (dashed border) giúp định hình vết cắt kéo thẳng thắn, chính xác. |

---

## 📐 Bảng quy cách bố cục in ấn trên giấy A4

| Số ảnh / trang | Chiều giấy | Bố cục lưới | Kích thước mỗi ảnh | Ứng dụng thực tế |
| :---: | :---: | :---: | :---: | :--- |
| **1 ảnh** | Ngang / Dọc | $1 \times 1$ | Toàn trang A4 | Bằng khen, chứng chỉ, poster nhỏ |
| **2 ảnh** *(Khuyên dùng)* | **Ngang** | $1 \times 2$ | **$\sim 13.5 \times 18.0\text{ cm}$** | Chuẩn khổ ảnh $13 \times 18\text{ cm}$ (cắt đôi tờ A4 là được 2 ảnh cực nét) |
| **2 ảnh** | **Dọc** | $2 \times 1$ | **$\sim 9.6 \times 12.8\text{ cm}$** | Kẹp bìa hồ sơ, học bạ dọc |
| **4 ảnh** | Ngang / Dọc | $2 \times 2$ | **$\sim 9.0 \times 12.0\text{ cm}$** | Ảnh lưu niệm tập thể, ảnh thẻ lớn ($9 \times 12$) |
| **6 ảnh** | Ngang | $2 \times 3$ | **$\sim 6.0 \times 8.0\text{ cm}$** | Ảnh minh họa giáo trình, phiếu theo dõi |
| **8 ảnh** | Ngang | $2 \times 4$ | **$\sim 4.5 \times 6.0\text{ cm}$** | Thẻ học sinh, thẻ nhân viên |

---

## 🚀 Hướng dẫn cài đặt

### 1. Yêu cầu hệ thống
- Hệ điều hành: **Windows 10 / 11**
- **Python 3.10** trở lên
- Microsoft Word (nếu sử dụng tính năng tự động xuất sang file PDF)

### 2. Cài đặt thư viện
Mở Terminal hoặc Command Prompt tại thư mục dự án và chạy:

```bash
pip install -r requirements.txt
```

---

## 🖥️ Hướng dẫn sử dụng

### Cách 1: Sử dụng Giao diện Popup (Khuyên dùng)
- Click đúp vào file **`run.bat`** (hoặc chạy lệnh `python main.py`).
- Thao tác nhanh qua 4 bước:
  1. **Chọn nguồn ảnh**: Bấm `📁 Chọn thư mục ảnh` (hoặc `🖼️ Chọn file lẻ`).
  2. **Chọn bố cục**: Chọn số ảnh/trang (`2 ảnh`), khổ giấy (`Khổ Ngang` / `Khổ Dọc`), định dạng xuất (`Word` / `PDF`).
  3. **Vị trí lưu**: Mặc định lưu cùng thư mục với ảnh gốc.
  4. **Thực thi**: Bấm **`🚀 BẮT ĐẦU TẠO FILE IN ẤN`**.

---

### Cách 2: Sử dụng qua Dòng lệnh (CLI)
Dành cho người dùng thích tự động hóa hoặc tích hợp vào hệ thống:

```bash
# Cú pháp cơ bản:
python main.py -i "<Đường_dẫn_thư_mục_ảnh>" [tùy_chọn]

# Ví dụ 1: Gom toàn bộ ảnh, 2 ảnh/trang, khổ ngang, xuất Word
python main.py -i "E:\DOWNLOADS\image" -c 2 -o landscape -f docx

# Ví dụ 2: 4 ảnh/trang, khổ dọc, thêm viền cắt mờ, xuất cả Word & PDF
python main.py -i "E:\DOWNLOADS\image" -c 4 -o portrait -b -f both

# Xem tất cả các tham số hỗ trợ
python main.py --help
```

#### Bảng tham số CLI:
| Tham số | Viết tắt | Giá trị mặc định | Giải thích |
| :--- | :---: | :---: | :--- |
| `--input` | `-i` | *(Bắt buộc)* | Đường dẫn đến thư mục hoặc file ảnh cần xử lý |
| `--count` | `-c` | `2` | Số ảnh trên 1 trang A4 (`1`, `2`, `4`, `6`, `8`, `9`...) |
| `--orientation` | `-o` | `landscape` | Chiều giấy: `landscape` (ngang) hoặc `portrait` (dọc) |
| `--format` | `-f` | `docx` | Định dạng xuất: `docx`, `pdf`, `both` (cả hai) |
| `--border` | `-b` | `False` | Thêm viền đứt mờ để hỗ trợ cắt rời ảnh |
| `--output` | | `Tự động` | Đường dẫn file kết quả xuất ra |

---

## 📁 Cấu trúc dự án

```text
photo-print-arranger/
├── core/
│   ├── __init__.py
│   └── arranger.py       # Thuật toán tính toán lưới A4 & xuất văn bản Word/PDF
├── app.py                # Giao diện Popup CustomTkinter (No-scroll, Auto-centered)
├── main.py               # Điểm khởi chạy linh hoạt (tự động nhận diện GUI/CLI)
├── run.bat               # File click đúp chạy nhanh trên Windows
├── requirements.txt      # Danh sách thư viện phụ thuộc
├── .gitignore            # Cấu hình bỏ qua file rác khi đẩy lên Git
└── README.md             # Tài liệu dự án chi tiết
```

---

## 🛠️ Công nghệ sử dụng

- **[Python](https://www.python.org/)**: Ngôn ngữ lập trình chính.
- **[CustomTkinter](https://github.com/TomSchimansky/CustomTkinter)**: Thiết kế giao diện hiện đại, bo góc mềm mại, tự động theo dõi chế độ Sáng/Tối.
- **[python-docx](https://python-docx.readthedocs.io/)**: Tạo và định dạng văn bản Microsoft Word chuẩn OpenXML.
- **[Pillow (PIL)](https://python-pillow.org/)**: Đọc và tính toán tỉ lệ khung hình ảnh gốc chính xác.
- **[pywin32](https://github.com/mhammond/pywin32)**: Tự động hóa Microsoft Word để chuyển đổi PDF chất lượng cao.

---

## 🐙 Hướng dẫn lưu trữ lên GitHub

Khởi tạo và đẩy dự án lên repository cá nhân của bạn:

```bash
cd E:\linhtinh\photo-print-arranger
git branch -M main
git remote add origin https://github.com/<tai-khoan-cua-ban>/photo-print-arranger.git
git push -u origin main
```

---

## 📄 License
Phát hành theo giấy phép **MIT License**. Tự do sử dụng, chỉnh sửa và đóng góp!
