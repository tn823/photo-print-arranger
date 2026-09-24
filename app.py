"""
Giao diện đồ họa hiện đại cho Photo Print Arranger
Sử dụng CustomTkinter: thiết kế bo góc, hỗ trợ Dark/Light mode chuẩn Windows 11.
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

# Cấu hình giao diện CustomTkinter
ctk.set_appearance_mode("System")  # Tự động đồng bộ Dark/Light với Windows
ctk.set_default_color_theme("blue") # Tone màu xanh công nghệ thanh lịch

class ArrangerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Photo Print Arranger - Dàn Trang In Ảnh A4")
        self.geometry("680x820")
        self.minsize(620, 750)

        # Dữ liệu nội bộ
        self.selected_images = []
        self.output_dir = ctk.StringVar(value="")
        self.output_name = ctk.StringVar(value="In_2_Anh_1_Trang_Kho_Ngang.docx")
        self.orientation = ctk.StringVar(value="Khổ Ngang")
        self.images_per_page = ctk.StringVar(value="2 ảnh")
        self.export_format = ctk.StringVar(value="Word (.docx)")
        self.add_cut_border = ctk.BooleanVar(value=False)
        self.open_after_done = ctk.BooleanVar(value=True)

        self._build_ui()

    def _build_ui(self):
        # Khung chứa chính có thanh cuộn mượt mà
        scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=16)

        # 1. Header & Theme Switcher
        header_frame = ctk.CTkFrame(scroll_frame, corner_radius=12)
        header_frame.pack(fill="x", pady=(0, 14), ipady=4)

        title_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_box.pack(side="left", padx=16, pady=12)

        lbl_title = ctk.CTkLabel(
            title_box, text="📸 Photo Print Arranger",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        lbl_title.pack(anchor="w")

        lbl_subtitle = ctk.CTkLabel(
            title_box,
            text="Tự động xếp ảnh vào trang A4 chuẩn in ấn • Giữ trọn độ nét và tỉ lệ",
            font=ctk.CTkFont(size=12),
            text_color=("gray50", "gray70")
        )
        lbl_subtitle.pack(anchor="w")

        # Nút đổi giao diện Sáng / Tối
        theme_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        theme_box.pack(side="right", padx=16, pady=12)

        ctk.CTkLabel(theme_box, text="Chế độ:", font=ctk.CTkFont(size=11)).pack(anchor="e")
        self.theme_menu = ctk.CTkOptionMenu(
            theme_box, values=["Hệ thống", "Sáng (Light)", "Tối (Dark)"],
            width=115, height=28, font=ctk.CTkFont(size=11),
            command=self._change_appearance_mode
        )
        self.theme_menu.set("Hệ thống")
        self.theme_menu.pack(anchor="e", pady=(2, 0))

        # 2. Card 1: Chọn nguồn ảnh
        card_input = ctk.CTkFrame(scroll_frame, corner_radius=12)
        card_input.pack(fill="x", pady=(0, 14), padx=2, ipadx=12, ipady=12)

        ctk.CTkLabel(
            card_input, text="1. Chọn nguồn ảnh",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=14, pady=(4, 8))

        btn_row = ctk.CTkFrame(card_input, fg_color="transparent")
        btn_row.pack(fill="x", padx=14, pady=(0, 8))

        ctk.CTkButton(
            btn_row, text="📁 Chọn thư mục ảnh...",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=38, width=190,
            command=self._choose_folder
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            btn_row, text="🖼️ Chọn các file ảnh lẻ...",
            font=ctk.CTkFont(size=13),
            fg_color=("gray85", "gray25"),
            text_color=("gray10", "gray90"),
            hover_color=("gray75", "gray35"),
            height=38, width=170,
            command=self._choose_files
        ).pack(side="left")

        self.lbl_input_status = ctk.CTkLabel(
            card_input,
            text="Chưa có ảnh nào được chọn. Hãy bấm nút trên để tải ảnh.",
            font=ctk.CTkFont(size=12),
            text_color=("gray50", "gray65")
        )
        self.lbl_input_status.pack(anchor="w", padx=14)

        # 3. Card 2: Bố cục & Định dạng
        card_layout = ctk.CTkFrame(scroll_frame, corner_radius=12)
        card_layout.pack(fill="x", pady=(0, 14), padx=2, ipadx=12, ipady=12)

        ctk.CTkLabel(
            card_layout, text="2. Tùy chọn bố cục in ấn",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=14, pady=(4, 10))

        # Số ảnh trên 1 trang (Segmented Button đẹp mắt)
        ctk.CTkLabel(
            card_layout, text="Số ảnh trên mỗi trang A4:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", padx=14, pady=(0, 4))

        self.seg_per_page = ctk.CTkSegmentedButton(
            card_layout,
            values=["1 ảnh", "2 ảnh", "4 ảnh", "6 ảnh", "8 ảnh", "9 ảnh"],
            variable=self.images_per_page,
            font=ctk.CTkFont(size=12, weight="bold"),
            height=34,
            command=self._on_layout_change
        )
        self.seg_per_page.pack(fill="x", padx=14, pady=(0, 4))

        self.lbl_grid_info = ctk.CTkLabel(
            card_layout, text="Bố cục gợi ý: 1 hàng × 2 cột (kích thước ~13.5 × 18 cm)",
            font=ctk.CTkFont(size=11), text_color=("gray50", "gray65")
        )
        self.lbl_grid_info.pack(anchor="w", padx=14, pady=(0, 12))

        # Chiều khổ giấy A4
        ctk.CTkLabel(
            card_layout, text="Chiều giấy A4:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", padx=14, pady=(0, 4))

        self.seg_orientation = ctk.CTkSegmentedButton(
            card_layout,
            values=["Khổ Ngang", "Khổ Dọc"],
            variable=self.orientation,
            font=ctk.CTkFont(size=12),
            height=32,
            command=self._on_layout_change
        )
        self.seg_orientation.pack(fill="x", padx=14, pady=(0, 12))

        # Định dạng xuất
        ctk.CTkLabel(
            card_layout, text="Định dạng xuất:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", padx=14, pady=(0, 4))

        self.seg_format = ctk.CTkSegmentedButton(
            card_layout,
            values=["Word (.docx)", "PDF (.pdf)", "Cả hai (.docx + .pdf)"],
            variable=self.export_format,
            font=ctk.CTkFont(size=12),
            height=32
        )
        self.seg_format.pack(fill="x", padx=14, pady=(0, 12))

        # Tùy chọn viền cắt & mở file
        opt_box = ctk.CTkFrame(card_layout, fg_color="transparent")
        opt_box.pack(fill="x", padx=14, pady=(2, 4))

        ctk.CTkCheckBox(
            opt_box, text="Thêm đường viền đứt mờ (tiện dùng kéo cắt rời từng ảnh)",
            variable=self.add_cut_border,
            font=ctk.CTkFont(size=12)
        ).pack(anchor="w", pady=(0, 6))

        ctk.CTkCheckBox(
            opt_box, text="Tự động mở file tài liệu sau khi tạo xong",
            variable=self.open_after_done,
            font=ctk.CTkFont(size=12)
        ).pack(anchor="w")

        # 4. Card 3: Nơi lưu & Tên file
        card_output = ctk.CTkFrame(scroll_frame, corner_radius=12)
        card_output.pack(fill="x", pady=(0, 14), padx=2, ipadx=12, ipady=12)

        ctk.CTkLabel(
            card_output, text="3. Vị trí lưu kết quả",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=14, pady=(4, 8))

        out_path_row = ctk.CTkFrame(card_output, fg_color="transparent")
        out_path_row.pack(fill="x", padx=14, pady=(0, 8))

        self.entry_out_dir = ctk.CTkEntry(
            out_path_row, textvariable=self.output_dir,
            placeholder_text="Chọn thư mục lưu file...",
            height=34, font=ctk.CTkFont(size=12)
        )
        self.entry_out_dir.pack(side="left", fill="x", expand=True, padx=(0, 8))

        ctk.CTkButton(
            out_path_row, text="Duyệt...", width=90, height=34,
            command=self._choose_output_dir
        ).pack(side="left")

        name_row = ctk.CTkFrame(card_output, fg_color="transparent")
        name_row.pack(fill="x", padx=14)

        ctk.CTkLabel(name_row, text="Tên file:", font=ctk.CTkFont(size=12)).pack(side="left", padx=(0, 8))
        self.entry_name = ctk.CTkEntry(
            name_row, textvariable=self.output_name,
            height=34, font=ctk.CTkFont(size=12)
        )
        self.entry_name.pack(side="left", fill="x", expand=True)

        # 5. Card 4: Nút thực thi & Tiến trình
        card_action = ctk.CTkFrame(scroll_frame, corner_radius=12)
        card_action.pack(fill="x", pady=(0, 10), padx=2, ipadx=12, ipady=12)

        self.btn_run = ctk.CTkButton(
            card_action,
            text="🚀 BẮT ĐẦU TẠO FILE IN ẤN",
            font=ctk.CTkFont(size=15, weight="bold"),
            height=46,
            command=self._start_processing
        )
        self.btn_run.pack(fill="x", padx=14, pady=(6, 10))

        self.progress_bar = ctk.CTkProgressBar(card_action, height=10)
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x", padx=14, pady=(0, 8))

        self.lbl_progress_status = ctk.CTkLabel(
            card_action, text="Sẵn sàng thực hiện.",
            font=ctk.CTkFont(size=12),
            text_color=("gray50", "gray70")
        )
        self.lbl_progress_status.pack(anchor="w", padx=14, pady=(0, 4))

        self._on_layout_change()

    def _change_appearance_mode(self, mode_str):
        mapping = {
            "Hệ thống": "System",
            "Sáng (Light)": "Light",
            "Tối (Dark)": "Dark"
        }
        ctk.set_appearance_mode(mapping.get(mode_str, "System"))

    def _choose_folder(self):
        folder = filedialog.askdirectory(title="Chọn thư mục chứa ảnh")
        if folder:
            imgs = get_image_files(folder)
            if not imgs:
                messagebox.showwarning("Thông báo", "Không tìm thấy file ảnh (.jpg, .png, .webp) nào trong thư mục này.")
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
        folder = filedialog.askdirectory(title="Chọn thư mục lưu kết quả")
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

        info_text = f"Bố cục lưới: {rows} hàng × {cols} cột trên trang A4 {self.orientation.get()}"
        self.lbl_grid_info.configure(text=info_text)
        self._update_default_name()

    def _update_default_name(self):
        count = self._parse_count()
        ori_str = "Ngang" if self.orientation.get() == "Khổ Ngang" else "Doc"
        self.output_name.set(f"In_{count}_Anh_1_Trang_Kho_{ori_str}.docx")

    def _start_processing(self):
        if not self.selected_images:
            messagebox.showerror("Chưa chọn ảnh", "Vui lòng chọn thư mục hoặc danh sách ảnh trước khi bắt đầu.")
            return

        out_dir = self.output_dir.get().strip()
        if not out_dir or not os.path.exists(out_dir):
            messagebox.showerror("Thư mục lưu không hợp lệ", "Vui lòng chỉ định thư mục lưu kết quả tồn tại.")
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
                    self.lbl_progress_status.configure(text=msg)
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
        self.lbl_progress_status.configure(text="✅ Đã hoàn tất thành công!", text_color=("#16A34A", "#4ADE80"))

        if self.open_after_done.get():
            try:
                os.startfile(final_target)
            except Exception:
                pass

        msg_text = (
            f"🎉 ĐÃ TẠO TÀI LIỆU THÀNH CÔNG!\n\n"
            f"• Số ảnh đã ghép: {res['total_images']}\n"
            f"• Tổng số trang A4: {res['total_pages']} trang\n"
            f"• Kích thước mỗi ảnh: {res['image_size_cm']} cm\n"
            f"• File đã lưu tại:\n{final_target}"
        )
        messagebox.showinfo("Thành công", msg_text)

    def _on_error(self, err_msg):
        self.btn_run.configure(state="normal")
        self.lbl_progress_status.configure(text="❌ Đã xảy ra lỗi.", text_color=("#DC2626", "#F87171"))
        messagebox.showerror("Lỗi xử lý", f"Đã xảy ra lỗi:\n\n{err_msg}")

def main():
    app = ArrangerApp()
    app.mainloop()

if __name__ == "__main__":
    main()
