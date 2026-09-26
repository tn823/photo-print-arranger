"""
Giao diện Popup tinh gọn (No-Scroll) cho Photo Print Arranger
Hỗ trợ cả chế độ in ảnh Chữ nhật truyền thống và in ảnh Tròn dán vở Bé Ngoan (sử dụng AI nhận diện khuôn mặt).
"""
import os
import sys
import threading
from typing import Dict, List, Optional
from tkinter import filedialog, messagebox

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# Tắt log OpenCV để console sạch sẽ
os.environ["OPENCV_LOG_LEVEL"] = "OFF"

import customtkinter as ctk
from core.arranger import ImageArranger, get_image_files, get_auto_grid, get_circle_grid
from core.face_cropper import CircleCropConfig
from core.crop_editor import CircleCropEditor

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class ArrangerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Photo Print Arranger - Dàn trang in ảnh A4 & Bé Ngoan")
        
        # Cấu hình cửa sổ dạng popup gọn gàng, căn giữa màn hình
        win_w, win_h = 610, 610
        self.resizable(False, False)
        
        # Tính toán căn giữa màn hình
        self.update_idletasks()
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        pos_x = max(0, (screen_w - win_w) // 2)
        pos_y = max(0, (screen_h - win_h) // 2 - 30)
        self.geometry(f"{win_w}x{win_h}+{pos_x}+{pos_y}")

        # Dữ liệu nội bộ
        self.selected_images: List[str] = []
        self.output_dir = ctk.StringVar(value="")
        self.output_name = ctk.StringVar(value="In_Anh_Tron_Be_Ngoan_4.5cm.docx")
        
        # Kiểu in: Tròn (Bé ngoan) hoặc Chữ nhật (Tiêu chuẩn)
        self.print_mode = ctk.StringVar(value="🔴 Ảnh tròn Bé Ngoan")
        self.circle_diameter = ctk.StringVar(value="4.5 cm (Chuẩn vở ⭐)")
        self.circle_fill_page = ctk.BooleanVar(value=True)
        self.custom_crop_configs: Dict[str, CircleCropConfig] = {}

        self.orientation = ctk.StringVar(value="Khổ Dọc")
        self.images_per_page = ctk.StringVar(value="2 ảnh")
        self.export_format = ctk.StringVar(value="Word (.docx)")
        self.add_cut_border = ctk.BooleanVar(value=True)
        self.open_after_done = ctk.BooleanVar(value=True)

        self._build_compact_ui()

    def _build_compact_ui(self):
        main_box = ctk.CTkFrame(self, fg_color="transparent")
        main_box.pack(fill="both", expand=True, padx=16, pady=12)

        # 1. Header (Tiêu đề + Đổi theme)
        top_bar = ctk.CTkFrame(main_box, fg_color="transparent")
        top_bar.pack(fill="x", pady=(0, 8))

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

        # 2. Block 1: Chọn nguồn ảnh
        box_input = ctk.CTkFrame(main_box, corner_radius=10)
        box_input.pack(fill="x", pady=(0, 8), padx=1, ipadx=10, ipady=6)

        input_row = ctk.CTkFrame(box_input, fg_color="transparent")
        input_row.pack(fill="x", padx=10, pady=(4, 2))

        ctk.CTkButton(
            input_row, text="📁 Chọn thư mục ảnh",
            font=ctk.CTkFont(size=12, weight="bold"),
            height=30, width=155,
            command=self._choose_folder
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            input_row, text="🖼️ Chọn file lẻ",
            font=ctk.CTkFont(size=12),
            fg_color=("gray85", "gray25"),
            text_color=("gray10", "gray90"),
            hover_color=("gray75", "gray35"),
            height=30, width=115,
            command=self._choose_files
        ).pack(side="left")

        self.lbl_input_status = ctk.CTkLabel(
            box_input, text="Chưa chọn ảnh nào. Hãy chọn thư mục hoặc ảnh để bắt đầu.",
            font=ctk.CTkFont(size=11), text_color=("gray50", "gray65"),
            anchor="w"
        )
        self.lbl_input_status.pack(fill="x", padx=10, pady=(0, 2))

        # 3. Block 2: Cấu hình chế độ & bố cục in ấn
        box_config = ctk.CTkFrame(main_box, corner_radius=10)
        box_config.pack(fill="x", pady=(0, 8), padx=1, ipadx=10, ipady=6)

        # Hàng 1: Chuyển đổi Kiểu in (Ảnh tròn Bé Ngoan vs Ảnh chữ nhật)
        mode_row = ctk.CTkFrame(box_config, fg_color="transparent")
        mode_row.pack(fill="x", padx=10, pady=(4, 4))

        ctk.CTkLabel(
            mode_row, text="Kiểu in ảnh:",
            font=ctk.CTkFont(size=11, weight="bold"), width=85, anchor="w"
        ).pack(side="left")

        self.seg_mode = ctk.CTkSegmentedButton(
            mode_row,
            values=["🔴 Ảnh tròn Bé Ngoan", "🔲 Ảnh chữ nhật chuẩn"],
            variable=self.print_mode,
            font=ctk.CTkFont(size=11, weight="bold"),
            height=28, command=self._on_mode_change
        )
        self.seg_mode.pack(side="left", fill="x", expand=True)

        # Vùng động chứa tùy chọn tương ứng với kiểu in
        self.frame_mode_options = ctk.CTkFrame(box_config, fg_color="transparent")
        self.frame_mode_options.pack(fill="x", padx=10, pady=(2, 2))

        self._build_mode_options()

        # Hàng Khổ giấy & Định dạng xuất (2 cột song song)
        r_paper = ctk.CTkFrame(box_config, fg_color="transparent")
        r_paper.pack(fill="x", padx=10, pady=(4, 4))

        col_left = ctk.CTkFrame(r_paper, fg_color="transparent")
        col_left.pack(side="left", fill="x", expand=True, padx=(0, 6))
        ctk.CTkLabel(col_left, text="Khổ giấy A4:", font=ctk.CTkFont(size=11, weight="bold"), anchor="w").pack(fill="x", pady=(0, 1))
        self.seg_ori = ctk.CTkSegmentedButton(
            col_left, values=["Khổ Dọc", "Khổ Ngang"],
            variable=self.orientation,
            font=ctk.CTkFont(size=11), height=26,
            command=self._on_layout_change
        )
        self.seg_ori.pack(fill="x")

        col_right = ctk.CTkFrame(r_paper, fg_color="transparent")
        col_right.pack(side="left", fill="x", expand=True, padx=(6, 0))
        ctk.CTkLabel(col_right, text="Định dạng xuất:", font=ctk.CTkFont(size=11, weight="bold"), anchor="w").pack(fill="x", pady=(0, 1))
        self.seg_fmt = ctk.CTkSegmentedButton(
            col_right, values=["Word (.docx)", "PDF (.pdf)", "Cả hai"],
            variable=self.export_format,
            font=ctk.CTkFont(size=11), height=26
        )
        self.seg_fmt.pack(fill="x")

        # Hàng Checkbox tùy chọn
        r_chk = ctk.CTkFrame(box_config, fg_color="transparent")
        r_chk.pack(fill="x", padx=10, pady=(4, 2))

        self.chk_border = ctk.CTkCheckBox(
            r_chk, text="Viền tròn mờ cắt kéo", variable=self.add_cut_border,
            font=ctk.CTkFont(size=11), checkbox_width=17, checkbox_height=17
        )
        self.chk_border.pack(side="left", padx=(0, 14))

        ctk.CTkCheckBox(
            r_chk, text="Tự mở file khi xong", variable=self.open_after_done,
            font=ctk.CTkFont(size=11), checkbox_width=17, checkbox_height=17
        ).pack(side="left")

        self.lbl_grid_info = ctk.CTkLabel(
            r_chk, text="Lưới: 5 hàng × 4 cột (20 ảnh/trang)",
            font=ctk.CTkFont(size=11), text_color=("gray50", "gray65")
        )
        self.lbl_grid_info.pack(side="right")

        # 4. Block 3: Nơi lưu & Tên file
        box_out = ctk.CTkFrame(main_box, corner_radius=10)
        box_out.pack(fill="x", pady=(0, 8), padx=1, ipadx=10, ipady=6)

        out_r1 = ctk.CTkFrame(box_out, fg_color="transparent")
        out_r1.pack(fill="x", padx=10, pady=(2, 2))

        ctk.CTkLabel(out_r1, text="Lưu tại:", font=ctk.CTkFont(size=11, weight="bold"), width=55, anchor="w").pack(side="left")
        self.entry_dir = ctk.CTkEntry(
            out_r1, textvariable=self.output_dir,
            placeholder_text="Chọn thư mục lưu...", height=26, font=ctk.CTkFont(size=11)
        )
        self.entry_dir.pack(side="left", fill="x", expand=True, padx=(0, 6))

        ctk.CTkButton(
            out_r1, text="Duyệt...", width=60, height=26,
            font=ctk.CTkFont(size=11), command=self._choose_output_dir
        ).pack(side="left")

        out_r2 = ctk.CTkFrame(box_out, fg_color="transparent")
        out_r2.pack(fill="x", padx=10, pady=(2, 2))

        ctk.CTkLabel(out_r2, text="Tên file:", font=ctk.CTkFont(size=11, weight="bold"), width=55, anchor="w").pack(side="left")
        self.entry_file = ctk.CTkEntry(
            out_r2, textvariable=self.output_name,
            height=26, font=ctk.CTkFont(size=11)
        )
        self.entry_file.pack(side="left", fill="x", expand=True)

        # 5. Block 4: Thực thi & Tiến trình
        box_action = ctk.CTkFrame(main_box, corner_radius=10)
        box_action.pack(fill="x", padx=1, ipadx=10, ipady=6)

        self.btn_run = ctk.CTkButton(
            box_action, text="🚀 BẮT ĐẦU TẠO FILE IN ẤN",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=36, command=self._start_processing
        )
        self.btn_run.pack(fill="x", padx=10, pady=(4, 4))

        self.progress_bar = ctk.CTkProgressBar(box_action, height=5)
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x", padx=10, pady=(0, 3))

        self.lbl_status = ctk.CTkLabel(
            box_action, text="Sẵn sàng.",
            font=ctk.CTkFont(size=11), text_color=("gray50", "gray70")
        )
        self.lbl_status.pack(anchor="w", padx=10, pady=(0, 2))

        self._on_layout_change()

    def _build_mode_options(self):
        """Xây dựng các tùy chọn theo kiểu in hiện tại."""
        for widget in self.frame_mode_options.winfo_children():
            widget.destroy()

        is_circle = ("tròn" in self.print_mode.get().lower())

        if is_circle:
            # Tùy chọn cho chế độ ảnh tròn Bé Ngoan
            row_diam = ctk.CTkFrame(self.frame_mode_options, fg_color="transparent")
            row_diam.pack(fill="x", pady=(2, 3))

            ctk.CTkLabel(
                row_diam, text="Đường kính:",
                font=ctk.CTkFont(size=11, weight="bold"), width=85, anchor="w"
            ).pack(side="left")

            self.seg_diameter = ctk.CTkSegmentedButton(
                row_diam,
                values=["3.5 cm", "4.0 cm", "4.5 cm (Chuẩn vở ⭐)", "5.0 cm"],
                variable=self.circle_diameter,
                font=ctk.CTkFont(size=10, weight="bold"),
                height=26, command=self._on_layout_change
            )
            self.seg_diameter.pack(side="left", fill="x", expand=True)

            # Hàng căn chỉnh ảnh tròn & In lặp lại
            row_tool = ctk.CTkFrame(self.frame_mode_options, fg_color="transparent")
            row_tool.pack(fill="x", pady=(2, 2))

            self.chk_fill = ctk.CTkCheckBox(
                row_tool, text="In đầy 1 trang A4 (Cho 1 bé)",
                variable=self.circle_fill_page,
                font=ctk.CTkFont(size=11), checkbox_width=17, checkbox_height=17,
                command=self._on_layout_change
            )
            self.chk_fill.pack(side="left")

            self.btn_open_crop = ctk.CTkButton(
                row_tool, text="✂️ Xem & Căn chỉnh ảnh tròn (AI)",
                font=ctk.CTkFont(size=11, weight="bold"),
                fg_color="#0284C7", hover_color="#0369A1",
                height=26, width=195,
                command=self._open_circle_crop_editor
            )
            self.btn_open_crop.pack(side="right")

            self.chk_border.configure(text="Viền tròn mờ cắt kéo")
        else:
            # Tùy chọn cho chế độ chữ nhật truyền thống
            row_rect = ctk.CTkFrame(self.frame_mode_options, fg_color="transparent")
            row_rect.pack(fill="x", pady=(2, 2))

            ctk.CTkLabel(
                row_rect, text="Số ảnh/trang:",
                font=ctk.CTkFont(size=11, weight="bold"), width=85, anchor="w"
            ).pack(side="left")

            self.seg_per_page = ctk.CTkSegmentedButton(
                row_rect,
                values=["1 ảnh", "2 ảnh", "4 ảnh", "6 ảnh", "8 ảnh", "9 ảnh"],
                variable=self.images_per_page,
                font=ctk.CTkFont(size=11, weight="bold"),
                height=26, command=self._on_layout_change
            )
            self.seg_per_page.pack(side="left", fill="x", expand=True)

            self.chk_border.configure(text="Viền ô chữ nhật mờ")

    def _on_mode_change(self, *args):
        is_circle = ("tròn" in self.print_mode.get().lower())
        if is_circle:
            self.orientation.set("Khổ Dọc")
            self.add_cut_border.set(True)
        else:
            self.orientation.set("Khổ Ngang")
            self.add_cut_border.set(False)

        self._build_mode_options()
        self._on_layout_change()

    def _parse_diameter_cm(self) -> float:
        val = self.circle_diameter.get()
        # Lấy số đầu tiên
        for token in val.split():
            try:
                return float(token)
            except ValueError:
                continue
        return 4.5

    def _parse_rect_count(self) -> int:
        val = self.images_per_page.get()
        return int(val.replace(" ảnh", "").strip())

    def _on_layout_change(self, *args):
        is_circle = ("tròn" in self.print_mode.get().lower())
        ori_key = "landscape" if self.orientation.get() == "Khổ Ngang" else "portrait"

        if is_circle:
            d_cm = self._parse_diameter_cm()
            rows, cols = get_circle_grid(d_cm, ori_key)
            per_page = rows * cols
            self.lbl_grid_info.configure(text=f"Lưới: {rows} hàng × {cols} cột ({per_page} ảnh/trang)")
            ori_tag = "Doc" if ori_key == "portrait" else "Ngang"
            self.output_name.set(f"In_Anh_Tron_Be_Ngoan_{d_cm}cm_{ori_tag}.docx")
        else:
            count = self._parse_rect_count()
            rows, cols = get_auto_grid(count, ori_key)
            self.lbl_grid_info.configure(text=f"Lưới: {rows} hàng × {cols} cột")
            ori_tag = "Ngang" if ori_key == "landscape" else "Doc"
            self.output_name.set(f"In_{count}_Anh_1_Trang_Kho_{ori_tag}.docx")

    def _open_circle_crop_editor(self):
        if not self.selected_images:
            messagebox.showinfo("Thông báo", "Vui lòng chọn ảnh trước khi bấm xem và căn chỉnh.")
            return

        d_cm = self._parse_diameter_cm()

        def on_saved(configs):
            self.custom_crop_configs.update(configs)
            total_saved = len(self.custom_crop_configs)
            self.lbl_status.configure(
                text=f"✅ Đã lưu cấu hình căn chỉnh {total_saved} ảnh.",
                text_color=("#16A34A", "#4ADE80")
            )

        CircleCropEditor(
            self,
            image_paths=self.selected_images,
            current_configs=self.custom_crop_configs,
            circle_diameter_cm=d_cm,
            on_save_callback=on_saved
        )

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
        self._on_layout_change()

    def _start_processing(self):
        if not self.selected_images:
            messagebox.showerror("Chưa chọn ảnh", "Vui lòng chọn thư mục hoặc file ảnh trước khi bấm bắt đầu.")
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
            is_circle = ("tròn" in self.print_mode.get().lower())

            if is_circle:
                d_cm = self._parse_diameter_cm()
                arranger = ImageArranger(
                    image_paths=self.selected_images,
                    output_docx=docx_path,
                    shape_mode='circle',
                    circle_diameter_cm=d_cm,
                    circle_configs=self.custom_crop_configs,
                    fill_page=self.circle_fill_page.get(),
                    orientation=ori_key,
                    add_border=self.add_cut_border.get(),
                    export_pdf=export_pdf,
                    progress_callback=update_progress
                )
            else:
                arranger = ImageArranger(
                    image_paths=self.selected_images,
                    output_docx=docx_path,
                    shape_mode='rectangle',
                    images_per_page=self._parse_rect_count(),
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
            f"• Bố cục: {res['grid']}\n"
            f"• Kích thước: {res['image_size_cm']}\n"
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
