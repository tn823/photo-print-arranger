# 📸 Photo Print Arranger

Ứng dụng Python tự động dàn trang ảnh in ấn & photocopy khổ giấy **A4** (xuất ra file **Word `.docx`** hoặc **PDF `.pdf`**).

---

## ✨ Tính năng nổi bật

- **Tự động chia đều**: Tự động tính toán kích thước tối ưu cho từng ảnh trên trang A4.
- **Không bóp méo hình (Preserve Aspect Ratio)**: Khóa chuẩn tỉ lệ khung hình gốc của ảnh.
- **Kích thước đồng nhất**: Tất cả ảnh trên tài liệu đều có cùng một kích thước bằng nhau 100%.
- **Giữ trọn chất lượng gốc (Lossless)**: Nhúng file ảnh gốc trực tiếp vào văn bản, không nén hay giảm độ phân giải.
- **Tùy chọn linh hoạt**:
  - Số ảnh trên 1 trang: `1`, `2`, `3`, `4`, `6`, `8`, `9`, `12`...
  - Chiều giấy: **Khổ Ngang (Landscape)** hoặc **Khổ Dọc (Portrait)**.
  - Định dạng xuất: **Word (.docx)**, **PDF (.pdf)** hoặc **Cả hai**.
  - Tùy chọn thêm viền cắt đứt mờ để tiện dùng kéo cắt rời từng ảnh.
- **2 Chế độ sử dụng**: Có sẵn **Giao diện đồ họa (GUI)** trực quan và **Dòng lệnh (CLI)** cho tác vụ tự động.

---

## 🚀 Cài đặt

1. Đảm bảo máy tính đã cài đặt **Python 3.10+**.
2. Cài đặt các thư viện phụ thuộc:
```bash
pip install -r requirements.txt
```

---

## 🖥️ Cách sử dụng

### 1. Sử dụng Giao diện đồ họa (GUI)
- Click đúp vào file **`run.bat`** (trên Windows).
- Hoặc chạy lệnh:
```bash
python main.py
```
- Các bước thao tác trên giao diện:
  1. Bấm **Chọn thư mục ảnh** (hoặc chọn nhiều ảnh lẻ).
  2. Chọn số lượng ảnh mỗi trang (ví dụ: `2` ảnh/trang).
  3. Chọn chiều giấy (**Khổ Ngang** hoặc **Khổ Dọc**).
  4. Chọn định dạng xuất (**Word**, **PDF** hoặc **Cả hai**).
  5. Bấm **🚀 Bắt đầu tạo file in ấn**.

---

### 2. Sử dụng qua Dòng lệnh (CLI)
Dành cho người thích gõ lệnh hoặc tích hợp vào script tự động:

```bash
# Gom toàn bộ ảnh trong thư mục, mỗi trang 2 ảnh khổ ngang, xuất file Word
python main.py -i "E:\DOWNLOADS\image" -c 2 -o landscape -f docx

# Mỗi trang 4 ảnh khổ dọc, xuất cả file Word và PDF
python main.py -i "E:\DOWNLOADS\image" -c 4 -o portrait -f both

# Thêm đường viền cắt mờ
python main.py -i "E:\DOWNLOADS\image" -c 2 -b -f docx
```

#### Các tham số dòng lệnh:
- `-i`, `--input`: Đường dẫn thư mục hoặc file ảnh (bắt buộc trong CLI).
- `-c`, `--count`: Số ảnh trên 1 trang (Mặc định: `2`).
- `-o`, `--orientation`: Khổ giấy: `landscape` (ngang) hoặc `portrait` (dọc).
- `-f`, `--format`: Định dạng xuất: `docx`, `pdf`, `both` (Mặc định: `docx`).
- `-b`, `--border`: Thêm đường viền đứt màu xám hỗ trợ cắt ảnh.
- `--output`: Đường dẫn tùy chỉnh tên file đầu ra.

---

## 📁 Cấu trúc thư mục

```text
photo-print-arranger/
├── core/
│   ├── __init__.py
│   └── arranger.py      # Bộ máy tính toán kích thước và sinh tài liệu Word/PDF
├── app.py               # Giao diện đồ họa Tkinter hiện đại
├── main.py              # Điểm khởi chạy (GUI hoặc CLI)
├── run.bat              # File click đúp chạy nhanh trên Windows
├── requirements.txt     # Danh sách thư viện phụ thuộc
├── .gitignore           # Bỏ qua các file rác khi đẩy lên Git
└── README.md            # Tài liệu hướng dẫn sử dụng
```

---

## 🐙 Đẩy lên GitHub (Git Setup)

Để lưu trữ dự án này lên GitHub cá nhân của bạn:

```bash
cd E:\linhtinh\photo-print-arranger
git init
git add .
git commit -m "Initial commit: Photo Print Arranger app"
git branch -M main
git remote add origin https://github.com/<tai-khoan-cua-ban>/photo-print-arranger.git
git push -u origin main
```
