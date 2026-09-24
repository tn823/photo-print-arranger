"""
Giao diện Popup tinh gọn (No-Scroll) cho Photo Print Arranger
Thiết kế dạng hộp thoại nổi (Dialog/Popup) nhỏ gọn, trực quan, không cần thanh cuộn.
"""
import os
import sys
import threading
from tkinter import filedialog, messagebox

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

import customtkinter as ctk
from core.arranger import ImageArranger, get_image_files, get_auto_grid

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class ArrangerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Photo Print Arranger")
        
        # Cấu hình cửa sổ dạng popup gọn gàng, căn giữa màn hình
        win_w, win_h = 580, 560
        self.resizable(False, False)
        
        # Tính toán căn giữa màn hình
        self.update_idletasks()
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        pos_x = max(0, (screen_w - win_w) // 2)
        pos_y = max(0, (screen_h - win_h) // 2 - 30)
        self.geometry(f"{win_w}x{win_h}+{pos_x}+{pos_y}")

        # Dữ liệu nội bộ
        self.selected_images = []
        self.output_dir = ctk.StringVar(value="")
        self.output_name = ctk.StringVar(value="In_2_Anh_1_Trang_Kho_Ngang.docx")
        self.orientation = ctk.StringVar(value="Khổ Ngang")
        self.images_per_page = ctk.StringVar(value="2 ảnh")
        self.export_format = ctk.StringVar(value="Word (.docx)")
        self.add_cut_border = ctk.BooleanVar(value=False)
        self.open_after_done = ctk.BooleanVar(value=True)

        self._build_compact_ui()

    def _build_compact_ui(self):
        # Container chính không scroll
        main_box = ctk.CTkFrame(self, fg_color="transparent")
        main_box.pack(fill="both", expand=True, padx=16, pady=14)

        # 1. Header tinh gọn (Tiêu đề + Đổi theme trên cùng 1 hàng)
        top_bar = ctk.CTkFrame(main_box, fg_color="transparent")
        top_bar.pack(fill="x", pady=(0, 10))

        title_lbl = ctk.CTkLabel(
            top_bar, text="📸 Photo Print Arranger",
            font=ctk.CTkFont(size=17, weight="bold")
        )
        title_lbl.pack(side="left")

        self.theme_menu = ctk.CTkOptionMenu(
            top_bar, values=["Hệ thống", "Sáng", "Tối"],
            width=90, height=26, font=ctk.CTkFont(size=11),
            command=self._change_theme
        )
        self.theme_menu.set("Hệ thống")
        self.theme_menu.pack(side="right")

        # 2. Block 1: Nguồn ảnh
        box_input = ctk.CTkFrame(main_box, corner_radius=10)
        box_input.pack(fill="x", pady=(0, 10), padx=1, ipadx=10, ipady=8)

        input_row = ctk.CTkFrame(box_input, fg_color="transparent")
        input_row.pack(fill="x", padx=10, pady=(4, 4))

        ctk.CTkButton(
            input_row, text="📁 Chọn thư mục ảnh",
            font=ctk.CTkFont(size=12, weight="bold"),
            height=32, width=160,
            command=self._choose_folder
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            input_row, text="🖼️ Chọn file lẻ",
            font=ctk.CTkFont(size=12),
            fg_color=("gray85", "gray25"),
            text_color=("gray10", "gray90"),
            hover_color=("gray75", "gray35"),
            height=32, width=120,
            command=self._choose_files
        ).pack(side="left")

        self.lbl_input_status = ctk.CTkLabel(
            box_input, text="Chưa chọn ảnh nào. Hãy chọn thư mục ảnh để bắt đầu.",
            font=ctk.CTkFont(size=11), text_color=("gray50", "gray65"),
            anchor="w"
        )
        self.lbl_input_status.pack(fill="x", padx=10, pady=(0, 2))

        # 3. Block 2: Cấu hình bố cục & định dạng
        box_config = ctk.CTkFrame(main_box, corner_radius=10)
        box_config.pack(fill="x", pady=(0, 10), padx=1, ipadx=10, ipady=8)

        # Hàng 1: Số ảnh / trang
        r1 = ctk.CTkFrame(box_config, fg_color="transparent")
        r1.pack(fill="x", padx=10, pady=(4, 4))
        ctk.CTkLabel(r1, text="Số ảnh/trang:", font=ctk.CTkFont(size=12, weight="bold"), width=90, anchor="w").pack(side="left")

        self.seg_per_page = ctk.CTkSegmentedButton(
            r1, values=["1 ảnh", "2 ảnh", "4 ảnh", "6 ảnh", "8 ảnh", "9 ảnh"],
            variable=self.images_per_page,
            font=ctk.CTkFont(size=11, weight="bold"),
            height=28, command=self._on_layout_change
        )
        self.seg_per_page.pack(side="left", fill="x", expand=True)

        # Hàng 2: Khổ giấy & Định dạng song song (2 cột)
        r2 = ctk.CTkFrame(box_config, fg_color="transparent")
        r2.pack(fill="x", padx=10, pady=(4, 4))

        # Cột trái: Khổ giấy
        col_left = ctk.CTkFrame(r2, fg_color="transparent")
        col_left.pack(side="left", fill="x", expand=True, padx=(0, 6))
        ctk.CTkLabel(col_left, text="Khổ giấy A4:", font=ctk.CTkFont(size=11, weight="bold"), anchor="w").pack(fill="x", pady=(0, 2))
        self.seg_ori = ctk.CTkSegmentedButton(
            col_left, values=["Khổ Ngang", "Khổ Dọc"],
            variable=self.orientation,
            font=ctk.CTkFont(size=11), height=28,
            command=self._on_layout_change
        )
        self.seg_ori.pack(fill="x")

        # Cột phải: Định dạng xuất
        col_right = ctk.CTkFrame(r2, fg_color="transparent")
        col_right.pack(side="left", fill="x", expand=True, padx=(6, 0))
        ctk.CTkLabel(col_right, text="Định dạng xuất:", font=ctk.CTkFont(size=11, weight="bold"), anchor="w").pack(fill="x", pady=(0, 2))
        self.seg_fmt = ctk.CTkSegmentedButton(
            col_right, values=["Word (.docx)", "PDF (.pdf)", "Cả hai"],
            variable=self.export_format,
            font=ctk.CTkFont(size=11), height=28
        )
        self.seg_fmt.pack(fill="x")

        # Hàng 3: Tùy chọn checkbox inline
        r3 = ctk.CTkFrame(box_config, fg_color="transparent")
        r3.pack(fill="x", padx=10, pady=(6, 2))

        ctk.CTkCheckBox(
            r3, text="Viền cắt đứt mờ", variable=self.add_cut_border,
            font=ctk.CTkFont(size=11), checkbox_width=18, checkbox_height=18
        ).pack(side="left", padx=(0, 16))

        ctk.CTkCheckBox(
            r3, text="Tự mở file khi hoàn tất", variable=self.open_after_done,
            font=ctk.CTkFont(size=11), checkbox_width=18, checkbox_height=18
        ).pack(side="left")

        self.lbl_grid_info = ctk.CTkLabel(
            r3, text="Lưới: 1 hàng × 2 cột",
            font=ctk.CTkFont(size=11), text_color=("gray50", "gray65")
        )
        self.lbl_grid_info.pack(side="right")

        # 4. Block 3: Nơi lưu & Tên file
        box_out = ctk.CTkFrame(main_box, corner_radius=10)
        box_out.pack(fill="x", pady=(0, 10), padx=1, ipadx=10, ipady=8)

        out_r1 = ctk.CTkFrame(box_out, fg_color="transparent")
        out_r1.pack(fill="x", padx=10, pady=(4, 4))

        ctk.CTkLabel(out_r1, text="Lưu tại:", font=ctk.CTkFont(size=11, weight="bold"), width=60, anchor="w").pack(side="left")
        self.entry_dir = ctk.CTkEntry(
            out_r1, textvariable=self.output_dir,
            placeholder_text="Chọn thư mục lưu...", height=28, font=ctk.CTkFont(size=11)
        )
        self.entry_dir.pack(side="left", fill="x", expand=True, padx=(0, 6))

        ctk.CTkButton(
            out_r1, text="Duyệt...", width=65, height=28,
            font=ctk.CTkFont(size=11), command=self._choose_output_dir
        ).pack(side="left")

        out_r2 = ctk.CTkFrame(box_out, fg_color="transparent")
        out_r2.pack(fill="x", padx=10, pady=(0, 2))

        ctk.CTkLabel(out_r2, text="Tên file:", font=ctk.CTkFont(size=11, weight="bold"), width=60, anchor="w").pack(side="left")
        self.entry_file = ctk.CTkEntry(
            out_r2, textvariable=self.output_name,
            height=28, font=ctk.CTkFont(size=11)
        )
        self.entry_file.pack(side="left", fill="x", expand=True)

        # 5. Block 4: Thực thi & Tiến trình
        box_action = ctk.CTkFrame(main_box, corner_radius=10)
        box_action.pack(fill="x", padx=1, ipadx=10, ipady=8)

        self.btn_run = ctk.CTkButton(
            box_action, text="🚀 BẮT ĐẦU TẠO FILE IN ẤN",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=38, command=self._start_processing
        )
        self.btn_run.pack(fill="x", padx=10, pady=(6, 6))

        self.progress_bar = ctk.CTkProgressBar(box_action, height=6)
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x", padx=10, pady=(0, 4))

        self.lbl_status = ctk.CTkLabel(
            box_action, text="Sẵn sàng.",
            font=ctk.CTkFont(size=11), text_color=("gray50", "gray70")
        )
        self.lbl_status.pack(anchor="w", padx=10, pady=(0, 2))

        self._on_layout_change()

    def _change_theme(self, mode_str):
        mapping = {"Hệ thống": "System", "Sáng": "Light", "Tối": "Dark"}
        ctk.set_appearance_mode(mapping.get(mode_str, "System"))

    def _choose_folder(self):
        folder = filedialog.askdirectory(title="Chọn thư mục chứa ảnh")
        if folder:
            imgs = get_image_files(folder)
            if not imgs:
                messagebox.showwarning("Thông báo", "Không tìm thấy file ảnh (.jpg, .png, .webp) trong thư mục này.")
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
        folder_name = os.path.basename(path) or path
        self.lbl_input_status.configure(
            text=f"✅ Đã chọn {total} ảnh từ: {folder_name}",
            text_color=("#16A34A", "#4ADE80")
        )
        self._update_default_name()

    def _parse_count(self) -> int:
        val = self.images_per_page.get()
        return int(val.replace(" ảnh", "").strip())

    def _on_layout_change(self, *args):
        count = self._parse_count()
        ori_key = "landscape" if self.orientation.get() == "Khổ Ngang" else "portrait"
        rows, cols = get_auto_grid(count, ori_key)
        self.lbl_grid_info.configure(text=f"Lưới: {rows} hàng × {cols} cột")
        self._update_default_name()

    def _update_default_name(self):
        count = self._parse_count()
        ori_str = "Ngang" if self.orientation.get() == "Khổ Ngang" else "Doc"
        self.output_name.set(f"In_{count}_Anh_1_Trang_Kho_{ori_str}.docx")

    def _start_processing(self):
        if not self.selected_images:
            messagebox.showerror("Chưa chọn ảnh", "Vui lòng chọn thư mục hoặc ảnh trước khi bấm bắt đầu.")
            return

        out_dir = self.output_dir.get().strip()
        if not out_dir or not os.path.exists(out_dir):
            messagebox.showerror("Lỗi thư mục", "Vui lòng chọn thư mục lưu file hợp lệ.")
            return

        fname = self.output_name.get().strip()
        if not fname.lower().endswith(".docx"):
            fname += ".docx"

        docx_path = os.path.join(out_dir, fname)
        fmt = self.export_format.get()
        export_pdf = ("PDF" in fmt or "Cả hai" in fmt)

        self.btn_run.configure(state="disabled")
        self.progress_bar.set(0)

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
                        self.progress_bar.set(curr / total)
                    self.lbl_status.configure(text=msg)
                self.after(0, _gui_update)

            ori_key = "landscape" if self.orientation.get() == "Khổ Ngang" else "portrait"

            arranger = ImageArranger(
                image_paths=self.selected_images,
                output_docx=docx_path,
                images_per_page=self._parse_count(),
                orientation=ori_key,
                add_border=self.add_cut_border.get(),
                export_pdf=export_pdf,
                progress_callback=update_progress
            )

            result = arranger.generate()

            final_target = result["docx_path"]
            if fmt == "PDF (.pdf)" and result["pdf_path"]:
                try:
                    os.remove(docx_path)
                except Exception:
                    pass
                final_target = result["pdf_path"]

            self.after(0, lambda: self._on_success(result, final_target))

        except Exception as e:
            self.after(0, lambda: self._on_error(str(e)))

    def _on_success(self, res, final_target):
        self.btn_run.configure(state="normal")
        self.progress_bar.set(1.0)
        self.lbl_status.configure(text="✅ Hoàn tất thành công!", text_color=("#16A34A", "#4ADE80"))

        if self.open_after_done.get():
            try:
                os.startfile(final_target)
            except Exception:
                pass

        msg_text = (
            f"🎉 ĐÃ TẠO TÀI LIỆU THÀNH CÔNG!\n\n"
            f"• Số ảnh: {res['total_images']} ảnh ({res['total_pages']} trang A4)\n"
            f"• Kích thước: {res['image_size_cm']} cm/ảnh\n"
            f"• File đã lưu tại:\n{final_target}"
        )
        messagebox.showinfo("Thành công", msg_text)

    def _on_error(self, err_msg):
        self.btn_run.configure(state="normal")
        self.lbl_status.configure(text="❌ Có lỗi xảy ra.", text_color=("#DC2626", "#F87171"))
        messagebox.showerror("Lỗi xử lý", f"Đã xảy ra lỗi:\n\n{err_msg}")

def main():
    app = ArrangerApp()
    app.mainloop()

if __name__ == "__main__":
    main()
