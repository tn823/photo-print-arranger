"""
Photo Print Arranger - Điểm khởi chạy ứng dụng (Hỗ trợ cả GUI và CLI)
"""
import sys
import os

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

import argparse

# Thêm đường dẫn thư mục hiện tại vào sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.arranger import ImageArranger, get_image_files

def run_cli(args):
    print("=" * 60)
    print("📸 PHOTO PRINT ARRANGER (CLI Mode)")
    print("=" * 60)

    images = get_image_files(args.input)
    if not images:
        print(f"❌ Không tìm thấy ảnh hợp lệ nào trong: {args.input}")
        sys.exit(1)

    print(f"✅ Đã tìm thấy {len(images)} ảnh.")
    print(f"⚙️ Cấu hình: {args.count} ảnh/trang | Khổ {args.orientation} | Định dạng: {args.format}")

    out_docx = args.output
    if not out_docx:
        ori = "Ngang" if args.orientation == "landscape" else "Doc"
        out_docx = os.path.join(
            os.path.dirname(images[0]),
            f"In_{args.count}_Anh_1_Trang_Kho_{ori}.docx"
        )
    elif not out_docx.lower().endswith(".docx"):
        out_docx += ".docx"

    export_pdf = (args.format.lower() in ["pdf", "both"])

    def on_progress(curr, total, msg):
        pct = int((curr / total) * 100) if total > 0 else 0
        sys.stdout.write(f"\r[{pct:>3}%] {msg:<50}")
        sys.stdout.flush()

    arranger = ImageArranger(
        image_paths=images,
        output_docx=out_docx,
        images_per_page=args.count,
        orientation=args.orientation,
        add_border=args.border,
        export_pdf=export_pdf,
        progress_callback=on_progress
    )

    print("\n⏳ Đang xử lý tài liệu...")
    try:
        res = arranger.generate()
        print("\n" + "=" * 60)
        print("🎉 HOÀN TẤT THÀNH CÔNG!")
        print(f"• Tổng số ảnh : {res['total_images']}")
        print(f"• Số trang A4 : {res['total_pages']}")
        print(f"• Kích thước  : {res['image_size_cm']} cm/ảnh")
        print(f"• File Word   : {res['docx_path']}")
        if res['pdf_path']:
            print(f"• File PDF    : {res['pdf_path']}")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ Lỗi: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(
        description="Photo Print Arranger - Tự động dàn trang ảnh in ấn A4 (Word & PDF)",
        add_help=False
    )
    parser.add_argument("-i", "--input", help="Đường dẫn thư mục hoặc file ảnh")
    parser.add_argument("-c", "--count", type=int, default=2, help="Số ảnh trên 1 trang (Mặc định: 2)")
    parser.add_argument("-o", "--orientation", choices=["landscape", "portrait"], default="landscape", help="Khổ giấy: landscape (ngang) hoặc portrait (dọc)")
    parser.add_argument("-f", "--format", choices=["docx", "pdf", "both"], default="docx", help="Định dạng xuất: docx, pdf, both")
    parser.add_argument("-b", "--border", action="store_true", help="Thêm đường viền cắt mờ")
    parser.add_argument("--output", help="Đường dẫn file Word đầu ra")
    parser.add_argument("-h", "--help", action="store_true", help="Hiển thị trợ giúp")

    # Nếu không có tham số nào được truyền vào -> Khởi động giao diện GUI
    if len(sys.argv) == 1:
        from app import main as run_gui
        run_gui()
        return

    parsed_args, _ = parser.parse_known_args()
    if parsed_args.help:
        parser.print_help()
        return

    if parsed_args.input:
        run_cli(parsed_args)
    else:
        from app import main as run_gui
        run_gui()

if __name__ == "__main__":
    main()
