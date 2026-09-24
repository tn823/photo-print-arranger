"""
Giao diện đồ họa (GUI) Photo Print Arranger
Xây dựng trên nền Tkinter/ttk hiện đại, mượt mà trên Windows.
"""
import os
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

import threading
import subprocess
from tkinter import (
    Tk, ttk, StringVar, IntVar, BooleanVar, messagebox, filedialog
)

from core.arranger import ImageArranger, get_image_files, get_auto_grid

class ArrangerGUI:
    def __init__(self, root: Tk):
        self.root = root
        self.root.title("Photo Print Arranger - Dàn trang in ảnh tự động")
        self.root.geometry("640 x 740".replace(" ", ""))
        self.root.minsize(580, 680)

        # Trạng thái
        self.selected_images = []
        self.output_dir = StringVar(value="")
        self.output_name = StringVar(value="In_Anh_A4.docx")
        self.orientation = StringVar(value="landscape")
        self.images_per_page = IntVar(value=2)
        self.export_format = StringVar(value="docx") # 'docx', 'pdf', 'both'
        self.add_cut_border = BooleanVar(value=False)
        self.open_after_done = BooleanVar(value=True)

        self._setup_style()
        self._build_ui()

    def _setup_style(self):
        style = ttk.Style(self.root)
        style.theme_use("clam")

        # Màu sắc hiện đại
        bg_main = "#F1F5F9"
        card_bg = "#FFFFFF"
        primary_color = "#2563EB"
        text_dark = "#0F172A"

        self.root.configure(bg=bg_main)

        style.configure(".", font=("Segoe UI", 10), background=bg_main, foreground=text_dark)
        style.configure("Card.TFrame", background=card_bg, relief="solid", borderwidth=1)
        style.configure("Header.TLabel", font=("Segoe UI", 14, "bold"), foreground="#1E293B", background=card_bg)
        style.configure("SubHeader.TLabel", font=("Segoe UI", 9), foreground="#64748B", background=card_bg)
        style.configure("Section.TLabel", font=("Segoe UI", 10, "bold"), foreground="#334155", background=card_bg)
        style.configure("Info.TLabel", font=("Segoe UI", 9), foreground="#475569", background=card_bg)

        style.configure(
            "Primary.TButton",
            font=("Segoe UI", 11, "bold"),
            background=primary_color,
            foreground="#FFFFFF",
            padding=(10, 8),
            borderwidth=0
        )
        style.map(
            "Primary.TButton",
            background=[("active", "#1D4ED8"), ("disabled", "#94A3B8")]
        )

        style.configure(
            "Secondary.TButton",
            font=("Segoe UI", 9),
            background="#E2E8F0",
            foreground="#1E293B",
            padding=(8, 4),
            borderwidth=0
        )
        style.map(
            "Secondary.TButton",
            background=[("active", "#CBD5E1")]
        )

    def _build_ui(self):
        container = ttk.Frame(self.root, padding=16)
        container.pack(fill="both", expand=True)

        # 1. Header Card
        header_card = ttk.Frame(container, style="Card.TFrame", padding=12)
        header_card.pack(fill="x", pady=(0, 10))

        ttk.Label(header_card, text="📸 Photo Print Arranger", style="Header.TLabel").pack(anchor="w")
        ttk.Label(
            header_card,
            text="Tự động ghép ảnh vào khổ A4 chuẩn in ấn: cùng kích thước, giữ trọn tỉ lệ và độ nét gốc.",
            style="SubHeader.TLabel"
        ).pack(anchor="w", pady=(2, 0))

        # 2. Input Images Card
        input_card = ttk.Frame(container, style="Card.TFrame", padding=12)
        input_card.pack(fill="x", pady=(0, 10))

        ttk.Label(input_card, text="1. Chọn nguồn ảnh", style="Section.TLabel").pack(anchor="w", pady=(0, 6))

        btn_row = ttk.Frame(input_card, style="Card.TFrame")
        btn_row.pack(fill="x", pady=(0, 6))

        ttk.Button(
            btn_row, text="📁 Chọn thư mục ảnh...", style="Secondary.TButton", command=self._choose_folder
        ).pack(side="left", padx=(0, 8))

        ttk.Button(
            btn_row, text="🖼️ Chọn các file ảnh...", style="Secondary.TButton", command=self._choose_files
        ).pack(side="left")

        self.lbl_input_status = ttk.Label(
            input_card, text="Chưa chọn ảnh nào. Hãy bấm nút phía trên để chọn.", style="Info.TLabel"
        )
        self.lbl_input_status.pack(anchor="w", pady=(4, 0))

        # 3. Settings Card
        settings_card = ttk.Frame(container, style="Card.TFrame", padding=12)
        settings_card.pack(fill="x", pady=(0, 10))

        ttk.Label(settings_card, text="2. Tùy chọn bố cục in ấn", style="Section.TLabel").pack(anchor="w", pady=(0, 8))

        # Row: Số ảnh / trang
        r1 = ttk.Frame(settings_card, style="Card.TFrame")
        r1.pack(fill="x", pady=4)
        ttk.Label(r1, text="Số ảnh mỗi trang:", width=18, style="Info.TLabel").pack(side="left")
        
        per_page_combo = ttk.Combobox(
            r1, textvariable=self.images_per_page,
            values=[1, 2, 3, 4, 6, 8, 9, 12],
            state="readonly", width=8
        )
        per_page_combo.pack(side="left")
        per_page_combo.bind("<<ComboboxSelected>>", self._on_config_change)

        self.lbl_grid_hint = ttk.Label(r1, text="(Gợi ý: 2 ảnh cạnh nhau)", style="SubHeader.TLabel")
        self.lbl_grid_hint.pack(side="left", padx=(10, 0))

        # Row: Khổ giấy
        r2 = ttk.Frame(settings_card, style="Card.TFrame")
        r2.pack(fill="x", pady=4)
        ttk.Label(r2, text="Chiều giấy A4:", width=18, style="Info.TLabel").pack(side="left")

        ttk.Radiobutton(
            r2, text="Khổ Ngang (Landscape)", value="landscape",
            variable=self.orientation, command=self._on_config_change
        ).pack(side="left", padx=(0, 12))

        ttk.Radiobutton(
            r2, text="Khổ Dọc (Portrait)", value="portrait",
            variable=self.orientation, command=self._on_config_change
        ).pack(side="left")

        # Row: Định dạng xuất
        r3 = ttk.Frame(settings_card, style="Card.TFrame")
        r3.pack(fill="x", pady=4)
        ttk.Label(r3, text="Định dạng xuất:", width=18, style="Info.TLabel").pack(side="left")

        ttk.Radiobutton(
            r3, text="Word (.docx)", value="docx", variable=self.export_format
        ).pack(side="left", padx=(0, 12))

        ttk.Radiobutton(
            r3, text="PDF (.pdf)", value="pdf", variable=self.export_format
        ).pack(side="left", padx=(0, 12))

        ttk.Radiobutton(
            r3, text="Cả hai (.docx + .pdf)", value="both", variable=self.export_format
        ).pack(side="left")

        # Checkboxes
        r4 = ttk.Frame(settings_card, style="Card.TFrame")
        r4.pack(fill="x", pady=(6, 0))

        ttk.Checkbutton(
            r4, text="Thêm đường viền cắt đứt mờ (dễ dùng kéo cắt)", variable=self.add_cut_border
        ).pack(anchor="w")

        ttk.Checkbutton(
            r4, text="Tự động mở file/thư mục khi hoàn tất", variable=self.open_after_done
        ).pack(anchor="w", pady=(2, 0))

        # 4. Output Destination Card
        out_card = ttk.Frame(container, style="Card.TFrame", padding=12)
        out_card.pack(fill="x", pady=(0, 10))

        ttk.Label(out_card, text="3. Nơi lưu & Tên file", style="Section.TLabel").pack(anchor="w", pady=(0, 6))

        out_row = ttk.Frame(out_card, style="Card.TFrame")
        out_row.pack(fill="x")

        self.txt_out_dir = ttk.Entry(out_row, textvariable=self.output_dir)
        self.txt_out_dir.pack(side="left", fill="x", expand=True, padx=(0, 6))

        ttk.Button(out_row, text="Duyệt...", style="Secondary.TButton", command=self._choose_output_dir).pack(side="left")

        name_row = ttk.Frame(out_card, style="Card.TFrame")
        name_row.pack(fill="x", pady=(6, 0))
        ttk.Label(name_row, text="Tên file:", width=10, style="Info.TLabel").pack(side="left")
        ttk.Entry(name_row, textvariable=self.output_name, width=35).pack(side="left")

        # 5. Action & Progress Card
        action_card = ttk.Frame(container, style="Card.TFrame", padding=12)
        action_card.pack(fill="both", expand=True)

        self.btn_run = ttk.Button(
            action_card, text="🚀 BẮT ĐẦU TẠO FILE IN ẤN",
            style="Primary.TButton", command=self._start_processing
        )
        self.btn_run.pack(fill="x", pady=(0, 8))

        self.progress_bar = ttk.Progressbar(action_card, mode="determinate")
        self.progress_bar.pack(fill="x", pady=(0, 6))

        self.lbl_progress_status = ttk.Label(action_card, text="Sẵn sàng.", style="Info.TLabel")
        self.lbl_progress_status.pack(anchor="w")

        self._on_config_change()

    def _choose_folder(self):
        folder = filedialog.askdirectory(title="Chọn thư mục chứa ảnh")
        if folder:
            imgs = get_image_files(folder)
            if not imgs:
                messagebox.showwarning("Thông báo", "Không tìm thấy ảnh hợp lệ (.jpg, .png, .webp) trong thư mục này.")
                return
            self.selected_images = imgs
            self.output_dir.set(folder)
            self._update_input_summary(folder)

    def _choose_files(self):
        files = filedialog.askopenfilenames(
            title="Chọn các file ảnh",
            filetypes=[("Hình ảnh", "*.jpg *.jpeg *.png *.bmp *.webp"), ("Tất cả", "*.*")]
        )
        if files:
            imgs = get_image_files(files)
            if imgs:
                self.selected_images = imgs
                first_dir = os.path.dirname(imgs[0])
                if not self.output_dir.get():
                    self.output_dir.set(first_dir)
                self._update_input_summary(first_dir)

    def _choose_output_dir(self):
        folder = filedialog.askdirectory(title="Chọn nơi lưu kết quả")
        if folder:
            self.output_dir.set(folder)

    def _update_input_summary(self, path):
        total = len(self.selected_images)
        self.lbl_input_status.config(
            text=f"✅ Đã chọn {total} ảnh từ: {os.path.basename(path) or path}",
            foreground="#16A34A"
        )
        self._update_default_name()

    def _on_config_change(self, event=None):
        per_page = self.images_per_page.get()
        ori = self.orientation.get()
        rows, cols = get_auto_grid(per_page, ori)
        self.lbl_grid_hint.config(text=f"(Bố cục lưới: {rows} hàng × {cols} cột)")
        self._update_default_name()

    def _update_default_name(self):
        count = self.images_per_page.get()
        ori = "Ngang" if self.orientation.get() == "landscape" else "Doc"
        self.output_name.set(f"In_{count}_Anh_1_Trang_Kho_{ori}.docx")

    def _start_processing(self):
        if not self.selected_images:
            messagebox.showerror("Lỗi", "Vui lòng chọn ít nhất 1 ảnh để tiến hành tạo file.")
            return

        out_dir = self.output_dir.get().strip()
        if not out_dir or not os.path.exists(out_dir):
            messagebox.showerror("Lỗi", "Vui lòng chọn thư mục lưu kết quả hợp lệ.")
            return

        fname = self.output_name.get().strip()
        if not fname.lower().endswith(".docx"):
            fname += ".docx"

        docx_path = os.path.join(out_dir, fname)
        fmt = self.export_format.get()
        export_pdf = (fmt in ["pdf", "both"])

        self.btn_run.config(state="disabled")
        self.progress_bar["value"] = 0

        # Chạy trong luồng phụ để UI không bị đơ
        threading.Thread(
            target=self._worker_process,
            args=(docx_path, export_pdf, fmt),
            daemon=True
        ).start()

    def _worker_process(self, docx_path, export_pdf, fmt):
        try:
            def update_progress(curr, total, msg):
                def _gui_update():
                    if total > 0:
                        pct = int((curr / total) * 100)
                        self.progress_bar["value"] = pct
                    self.lbl_progress_status.config(text=msg)
                self.root.after(0, _gui_update)

            arranger = ImageArranger(
                image_paths=self.selected_images,
                output_docx=docx_path,
                images_per_page=self.images_per_page.get(),
                orientation=self.orientation.get(),
                add_border=self.add_cut_border.get(),
                export_pdf=export_pdf,
                progress_callback=update_progress
            )

            result = arranger.generate()

            # Nếu người dùng chỉ muốn PDF, có thể xóa file docx trung gian
            final_target = result["docx_path"]
            if fmt == "pdf" and result["pdf_path"]:
                try:
                    os.remove(docx_path)
                except Exception:
                    pass
                final_target = result["pdf_path"]

            self.root.after(0, lambda: self._on_success(result, final_target))

        except Exception as e:
            self.root.after(0, lambda: self._on_error(str(e)))

    def _on_success(self, res, final_target):
        self.btn_run.config(state="normal")
        self.progress_bar["value"] = 100
        msg_text = (
            f"🎉 Hoàn tất thành công!\n\n"
            f"• Tổng số ảnh: {res['total_images']}\n"
            f"• Số trang: {res['total_pages']} trang\n"
            f"• Kích thước mỗi ảnh: ~{res['image_size_cm']} cm (giữ nguyên tỉ lệ)\n"
            f"• File đã lưu tại: {final_target}"
        )
        self.lbl_progress_status.config(text="Đã hoàn tất!")

        if self.open_after_done.get():
            try:
                os.startfile(final_target)
            except Exception:
                pass

        messagebox.showinfo("Thành công", msg_text)

    def _on_error(self, err_msg):
        self.btn_run.config(state="normal")
        self.lbl_progress_status.config(text="Đã xảy ra lỗi.")
        messagebox.showerror("Lỗi xử lý", f"Đã xảy ra lỗi trong quá trình tạo tài liệu:\n\n{err_msg}")

def main():
    root = Tk()
    app = ArrangerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
