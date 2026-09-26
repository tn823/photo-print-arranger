"""
Photo Print Arranger - Điểm khởi chạy ứng dụng (Hỗ trợ cả GUI và CLI)
Hỗ trợ cả in ảnh chữ nhật và in ảnh tròn dán vở Bé Ngoan.
"""
import sys
import os

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# Tắt log OpenCV để console sạch sẽ
os.environ["OPENCV_LOG_LEVEL"] = "OFF"

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
    shape_mode = "circle" if args.mode in ["circle", "tron", "be_ngoan"] else "rectangle"

    if shape_mode == "circle":
        print(f"⚙️ Chế độ: 🔴 Ảnh tròn Bé Ngoan | Đường kính: {args.diameter} cm")
        print(f"⚙️ Khổ giấy: {args.orientation} | In đầy trang: {args.fill_page} | Định dạng: {args.format}")
    else:
        print(f"⚙️ Chế độ: 🔲 Ảnh chữ nhật | {args.count} ảnh/trang | Khổ: {args.orientation} | Định dạng: {args.format}")

    out_docx = args.output
    if not out_docx:
        ori = "Ngang" if args.orientation == "landscape" else "Doc"
        if shape_mode == "circle":
            out_docx = os.path.join(
                os.path.dirname(images[0]),
                f"In_Anh_Tron_Be_Ngoan_{args.diameter}cm_{ori}.docx"
            )
        else:
            out_docx = os.path.join(
                os.path.dirname(images[0]),
                f"In_{args.count}_Anh_1_Trang_Kho_{ori}.docx"
            )
    elif not out_docx.lower().endswith(".docx"):
        out_docx += ".docx"

    export_pdf = (args.format.lower() in ["pdf", "both"])
    add_border = (args.border or shape_mode == "circle")

    def on_progress(curr, total, msg):
        pct = int((curr / total) * 100) if total > 0 else 0
        sys.stdout.write(f"\r[{pct:>3}%] {msg:<50}")
        sys.stdout.flush()

    arranger = ImageArranger(
        image_paths=images,
        output_docx=out_docx,
        shape_mode=shape_mode,
        images_per_page=args.count,
        circle_diameter_cm=args.diameter,
        fill_page=args.fill_page,
        orientation=args.orientation,
        add_border=add_border,
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
        print(f"• Bố cục      : {res['grid']}")
        print(f"• Kích thước  : {res['image_size_cm']}")
        print(f"• File Word   : {res['docx_path']}")
        if res['pdf_path']:
            print(f"• File PDF    : {res['pdf_path']}")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ Lỗi: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(
        description="Photo Print Arranger - Tự động dàn trang ảnh in ấn A4 & ảnh tròn Bé Ngoan (Word & PDF)",
        add_help=False
    )
    parser.add_argument("-i", "--input", help="Đường dẫn thư mục hoặc file ảnh")
    parser.add_argument("-m", "--mode", choices=["rect", "circle"], default="rect", help="Kiểu in: rect (chữ nhật) hoặc circle (ảnh tròn Bé Ngoan)")
    parser.add_argument("-d", "--diameter", type=float, default=4.5, help="Đường kính ảnh tròn (cm) - mặc định: 4.5")
    parser.add_argument("--fill-page", action="store_true", help="In lặp lại ảnh đầy 1 trang A4 (dành cho in 1 bé)")
    parser.add_argument("-c", "--count", type=int, default=2, help="Số ảnh trên 1 trang cho chế độ chữ nhật (Mặc định: 2)")
    parser.add_argument("-o", "--orientation", choices=["landscape", "portrait"], default="landscape", help="Khổ giấy: landscape (ngang) hoặc portrait (dọc)")
    parser.add_argument("-f", "--format", choices=["docx", "pdf", "both"], default="docx", help="Định dạng xuất: docx, pdf, both")
    parser.add_argument("-b", "--border", action="store_true", help="Thêm đường viền cắt mờ")
    parser.add_argument("--output", help="Đường dẫn file Word đầu ra")
    parser.add_argument("-h", "--help", action="store_true", help="Hiển thị trợ giúp")

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
