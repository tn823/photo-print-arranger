"""
Cửa sổ tương tác Căn chỉnh & Xem trước ảnh tròn Bé Ngoan (Circle Crop Editor).
Cho phép người dùng kéo thả, thu phóng và dùng AI nhận diện khuôn mặt bé để căn ảnh trọng tâm nhất.
"""
import os
import math
from typing import List, Dict, Optional, Callable
from PIL import Image, ImageTk, ImageDraw, ImageOps
import customtkinter as ctk
from tkinter import Canvas

from core.face_cropper import (
    CircleCropConfig,
    FaceDetector,
    calculate_smart_circle,
    crop_circle_image
)

class CircleCropEditor(ctk.CTkToplevel):
    def __init__(
        self,
        parent,
        image_paths: List[str],
        current_configs: Optional[Dict[str, CircleCropConfig]] = None,
        circle_diameter_cm: float = 4.5,
        on_save_callback: Optional[Callable[[Dict[str, CircleCropConfig]], None]] = None
    ):
        super().__init__(parent)

        self.title("✂️ Căn chỉnh & Xem trước ảnh tròn dán vở Bé Ngoan")
        self.image_paths = [p for p in image_paths if os.path.exists(p)]
        if not self.image_paths:
            self.destroy()
            return

        self.configs: Dict[str, CircleCropConfig] = dict(current_configs or {})
        self.circle_diameter_cm = circle_diameter_cm
        self.on_save_callback = on_save_callback

        self.current_idx = 0
        self.current_pil: Optional[Image.Image] = None
        self.cached_disp_img: Optional[Image.Image] = None
        self.canvas_scale = 1.0
        self.canvas_offset_x = 0
        self.canvas_offset_y = 0

        # Kích thước canvas
        self.canvas_w = 460
        self.canvas_h = 460

        # Biến kéo chuột
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.is_dragging = False

        # Cấu hình cửa sổ popup
        win_w, win_h = 760, 580
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        # Căn giữa màn hình
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        px = max(0, (sw - win_w) // 2)
        py = max(0, (sh - win_h) // 2 - 20)
        self.geometry(f"{win_w}x{win_h}+{px}+{py}")

        self._build_ui()
        self._load_current_image()

    def _build_ui(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=14, pady=12)

        # Cột trái: Canvas & Điều hướng ảnh (480px)
        left_frame = ctk.CTkFrame(container, fg_color="transparent")
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))

        # Thanh điều hướng ảnh
        nav_bar = ctk.CTkFrame(left_frame, fg_color="transparent")
        nav_bar.pack(fill="x", pady=(0, 8))

        self.btn_prev = ctk.CTkButton(
            nav_bar, text="◀ Ảnh trước", width=90, height=28,
            font=ctk.CTkFont(size=11), command=self._prev_image
        )
        self.btn_prev.pack(side="left")

        self.lbl_nav_info = ctk.CTkLabel(
            nav_bar, text="Ảnh 1 / 1",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.lbl_nav_info.pack(side="left", fill="x", expand=True, padx=8)

        self.btn_next = ctk.CTkButton(
            nav_bar, text="Ảnh tiếp ▶", width=90, height=28,
            font=ctk.CTkFont(size=11), command=self._next_image
        )
        self.btn_next.pack(side="right")

        # Khung chứa Canvas
        canvas_box = ctk.CTkFrame(left_frame, corner_radius=8, fg_color=("gray90", "gray15"))
        canvas_box.pack(fill="both", expand=True)

        self.canvas = Canvas(
            canvas_box, width=self.canvas_w, height=self.canvas_h,
            bg="#18181B", highlightthickness=0, cursor="fleur"
        )
        self.canvas.pack(padx=8, pady=8)

        # Binds cho Canvas
        self.canvas.bind("<ButtonPress-1>", self._on_drag_start)
        self.canvas.bind("<B1-Motion>", self._on_drag_motion)
        self.canvas.bind("<ButtonRelease-1>", self._on_drag_end)
        self.canvas.bind("<MouseWheel>", self._on_mouse_wheel)

        lbl_hint = ctk.CTkLabel(
            left_frame,
            text="💡 Kéo chuột để di chuyển tâm • Lăn chuột để phóng to/thu nhỏ",
            font=ctk.CTkFont(size=11), text_color=("gray50", "gray60")
        )
        lbl_hint.pack(pady=(6, 0))

        # Cột phải: Xem trước nhãn dán & Công cụ điều khiển (250px)
        right_frame = ctk.CTkFrame(container, width=250, corner_radius=10)
        right_frame.pack(side="right", fill="y", ipadx=8, ipady=8)
        right_frame.pack_propagate(False)

        # Card Xem trước nhãn dán
        ctk.CTkLabel(
            right_frame, text="🔍 Nhãn dán thực tế (Preview)",
            font=ctk.CTkFont(size=12, weight="bold"), anchor="w"
        ).pack(fill="x", padx=10, pady=(4, 4))

        preview_card = ctk.CTkFrame(right_frame, fg_color=("white", "gray20"), corner_radius=8)
        preview_card.pack(fill="x", padx=10, pady=(0, 10), ipady=6)

        self.lbl_preview_sticker = ctk.CTkLabel(preview_card, text="", width=150, height=150)
        self.lbl_preview_sticker.pack(pady=4)

        self.lbl_size_info = ctk.CTkLabel(
            preview_card, text=f"Kích thước in: {self.circle_diameter_cm} cm",
            font=ctk.CTkFont(size=11), text_color=("gray50", "gray70")
        )
        self.lbl_size_info.pack(pady=(0, 4))

        # Card Công cụ điều khiển
        ctk.CTkLabel(
            right_frame, text="⚙️ Công cụ AI & Căn chỉnh",
            font=ctk.CTkFont(size=12, weight="bold"), anchor="w"
        ).pack(fill="x", padx=10, pady=(0, 4))

        self.btn_auto_face = ctk.CTkButton(
            right_frame, text="🤖 Tự động tìm mặt bé (AI)",
            font=ctk.CTkFont(size=11, weight="bold"), height=30,
            fg_color="#0284C7", hover_color="#0369A1",
            command=self._auto_detect_current
        )
        self.btn_auto_face.pack(fill="x", padx=10, pady=(0, 6))

        self.btn_reset_center = ctk.CTkButton(
            right_frame, text="🔄 Đặt lại giữa ảnh",
            font=ctk.CTkFont(size=11), height=28,
            fg_color=("gray85", "gray30"), text_color=("gray10", "gray90"),
            hover_color=("gray75", "gray40"),
            command=self._reset_to_center
        )
        self.btn_reset_center.pack(fill="x", padx=10, pady=(0, 8))

        # Zoom Slider
        zoom_header = ctk.CTkFrame(right_frame, fg_color="transparent")
        zoom_header.pack(fill="x", padx=10, pady=(0, 2))
        ctk.CTkLabel(zoom_header, text="Kích thước vòng tròn:", font=ctk.CTkFont(size=11), anchor="w").pack(side="left")
        self.lbl_zoom_val = ctk.CTkLabel(zoom_header, text="100%", font=ctk.CTkFont(size=11, weight="bold"))
        self.lbl_zoom_val.pack(side="right")

        zoom_row = ctk.CTkFrame(right_frame, fg_color="transparent")
        zoom_row.pack(fill="x", padx=10, pady=(0, 8))

        ctk.CTkButton(
            zoom_row, text="-", width=26, height=24, font=ctk.CTkFont(size=13, weight="bold"),
            command=lambda: self._adjust_zoom(-0.08)
        ).pack(side="left")

        self.slider_zoom = ctk.CTkSlider(
            zoom_row, from_=0.3, to=2.0, height=16,
            command=self._on_slider_zoom
        )
        self.slider_zoom.set(1.0)
        self.slider_zoom.pack(side="left", fill="x", expand=True, padx=6)

        ctk.CTkButton(
            zoom_row, text="+", width=26, height=24, font=ctk.CTkFont(size=13, weight="bold"),
            command=lambda: self._adjust_zoom(0.08)
        ).pack(side="right")

        self.lbl_ai_status = ctk.CTkLabel(
            right_frame, text="🎯 AI đang nhận diện...",
            font=ctk.CTkFont(size=11), text_color="#10B981", anchor="w"
        )
        self.lbl_ai_status.pack(fill="x", padx=10, pady=(0, 8))

        # Khoảng đệm
        spacer = ctk.CTkFrame(right_frame, fg_color="transparent")
        spacer.pack(fill="both", expand=True)

        # Các nút Lưu & Áp dụng
        if len(self.image_paths) > 1:
            ctk.CTkButton(
                right_frame, text="⚡ Căn tự động TẤT CẢ ảnh",
                font=ctk.CTkFont(size=11), height=30,
                fg_color=("gray80", "gray35"), text_color=("gray10", "gray95"),
                hover_color=("gray70", "gray45"),
                command=self._auto_detect_all
            ).pack(fill="x", padx=10, pady=(0, 6))

        ctk.CTkButton(
            right_frame, text="✅ Lưu & Áp dụng",
            font=ctk.CTkFont(size=12, weight="bold"), height=36,
            fg_color="#16A34A", hover_color="#15803D",
            command=self._save_and_close
        ).pack(fill="x", padx=10, pady=(0, 4))

    def _get_current_path(self) -> str:
        return self.image_paths[self.current_idx]

    def _load_current_image(self):
        img_path = self._get_current_path()
        total = len(self.image_paths)
        fname = os.path.basename(img_path)
        self.lbl_nav_info.configure(text=f"Ảnh {self.current_idx + 1} / {total}: {fname}")

        self.btn_prev.configure(state="normal" if self.current_idx > 0 else "disabled")
        self.btn_next.configure(state="normal" if self.current_idx < total - 1 else "disabled")

        try:
            raw_img = Image.open(img_path)
            self.current_pil = ImageOps.exif_transpose(raw_img)
        except Exception as e:
            self.lbl_ai_status.configure(text=f"❌ Không mở được ảnh: {e}", text_color="#EF4444")
            return

        orig_w, orig_h = self.current_pil.size
        # Tính scale để vừa với canvas
        scale_x = self.canvas_w / float(orig_w)
        scale_y = self.canvas_h / float(orig_h)
        self.canvas_scale = min(scale_x, scale_y)

        disp_w = max(10, int(orig_w * self.canvas_scale))
        disp_h = max(10, int(orig_h * self.canvas_scale))
        self.canvas_offset_x = (self.canvas_w - disp_w) // 2
        self.canvas_offset_y = (self.canvas_h - disp_h) // 2

        self.cached_disp_img = self.current_pil.resize(
            (disp_w, disp_h), Image.Resampling.BILINEAR
        ).convert("RGBA")

        # Lấy hoặc tạo config crop cho ảnh hiện tại
        if img_path not in self.configs:
            cfg = calculate_smart_circle(self.current_pil)
            self.configs[img_path] = cfg
            self.lbl_ai_status.configure(text="🎯 Đã tìm vị trí tối ưu", text_color="#10B981")
        else:
            self.lbl_ai_status.configure(text="✔️ Đã có cấu hình lưu", text_color="#3B82F6")

        cfg = self.configs[img_path]
        # Cập nhật slider zoom
        base_d = min(orig_w, orig_h) * 0.85
        ratio = cfg.diameter / base_d if base_d > 0 else 1.0
        self.slider_zoom.set(max(0.3, min(2.0, ratio)))
        self.lbl_zoom_val.configure(text=f"{int(ratio * 100)}%")

        self._render_canvas()
        self._render_sticker_preview()

    def _render_canvas(self):
        if self.cached_disp_img is None or self.current_pil is None:
            return

        img_path = self._get_current_path()
        cfg = self.configs.get(img_path)
        if not cfg:
            return

        disp_w, disp_h = self.cached_disp_img.size

        # Tạo lớp overlay tối màu bao quanh hình tròn
        overlay = Image.new("RGBA", (disp_w, disp_h), (0, 0, 0, 160))
        d_overlay = ImageDraw.Draw(overlay)

        cx_disp = cfg.center_x * self.canvas_scale
        cy_disp = cfg.center_y * self.canvas_scale
        r_disp = (cfg.diameter / 2.0) * self.canvas_scale

        # Khoét rỗng vòng tròn để hiện rõ phần ảnh được giữ lại
        d_overlay.ellipse(
            (cx_disp - r_disp, cy_disp - r_disp, cx_disp + r_disp, cy_disp + r_disp),
            fill=(0, 0, 0, 0),
            outline=(255, 255, 255, 240),
            width=2
        )

        # Vẽ tâm chữ thập nhỏ mờ
        cross_len = 10
        d_overlay.line(
            (cx_disp - cross_len, cy_disp, cx_disp + cross_len, cy_disp),
            fill=(255, 255, 255, 180), width=1
        )
        d_overlay.line(
            (cx_disp, cy_disp - cross_len, cx_disp, cy_disp + cross_len),
            fill=(255, 255, 255, 180), width=1
        )

        combined = Image.alpha_composite(self.cached_disp_img, overlay)

        # Chèn lên nền đen canvas
        full_canvas_img = Image.new("RGB", (self.canvas_w, self.canvas_h), (24, 24, 27))
        full_canvas_img.paste(combined.convert("RGB"), (self.canvas_offset_x, self.canvas_offset_y))

        self.tk_canvas_img = ImageTk.PhotoImage(full_canvas_img)
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor="nw", image=self.tk_canvas_img)

    def _render_sticker_preview(self):
        if self.current_pil is None:
            return
        img_path = self._get_current_path()
        cfg = self.configs.get(img_path)
        if not cfg:
            return

        sticker_pil = crop_circle_image(
            self.current_pil, cfg,
            output_size_px=140,
            add_guide_border=True
        )

        # Đặt trên nền trắng để nhìn giống như khi dán lên giấy
        bg = Image.new("RGBA", (140, 140), (255, 255, 255, 255))
        preview_comp = Image.alpha_composite(bg, sticker_pil)

        self.tk_sticker_img = ImageTk.PhotoImage(preview_comp)
        self.lbl_preview_sticker.configure(image=self.tk_sticker_img)

    def _on_drag_start(self, event):
        self.drag_start_x = event.x
        self.drag_start_y = event.y
        self.is_dragging = True

    def _on_drag_motion(self, event):
        if not self.is_dragging or self.current_pil is None:
            return

        dx_canvas = event.x - self.drag_start_x
        dy_canvas = event.y - self.drag_start_y

        self.drag_start_x = event.x
        self.drag_start_y = event.y

        img_path = self._get_current_path()
        cfg = self.configs.get(img_path)
        if not cfg:
            return

        # Đảo chiều kéo: Kéo ảnh đi thì tâm vùng cắt dịch chuyển tương ứng
        orig_w, orig_h = self.current_pil.size
        delta_x = dx_canvas / self.canvas_scale
        delta_y = dy_canvas / self.canvas_scale

        cfg.center_x += delta_x
        cfg.center_y += delta_y

        # Giới hạn nhẹ để tâm không bị trôi đi quá xa
        cfg.center_x = max(0.0, min(float(orig_w), cfg.center_x))
        cfg.center_y = max(0.0, min(float(orig_h), cfg.center_y))

        self._render_canvas()
        self._render_sticker_preview()

    def _on_drag_end(self, event):
        self.is_dragging = False

    def _on_mouse_wheel(self, event):
        delta = 0.06 if event.delta > 0 else -0.06
        self._adjust_zoom(delta)

    def _adjust_zoom(self, delta: float):
        cur_val = self.slider_zoom.get()
        new_val = max(0.3, min(2.0, cur_val + delta))
        self.slider_zoom.set(new_val)
        self._on_slider_zoom(new_val)

    def _on_slider_zoom(self, value):
        if self.current_pil is None:
            return
        img_path = self._get_current_path()
        cfg = self.configs.get(img_path)
        if not cfg:
            return

        orig_w, orig_h = self.current_pil.size
        base_d = min(orig_w, orig_h) * 0.85
        cfg.diameter = max(60.0, base_d * float(value))

        self.lbl_zoom_val.configure(text=f"{int(float(value) * 100)}%")
        self._render_canvas()
        self._render_sticker_preview()

    def _auto_detect_current(self):
        if self.current_pil is None:
            return
        img_path = self._get_current_path()
        cfg = calculate_smart_circle(self.current_pil)
        self.configs[img_path] = cfg

        orig_w, orig_h = self.current_pil.size
        base_d = min(orig_w, orig_h) * 0.85
        ratio = cfg.diameter / base_d if base_d > 0 else 1.0
        self.slider_zoom.set(max(0.3, min(2.0, ratio)))
        self.lbl_zoom_val.configure(text=f"{int(ratio * 100)}%")

        self.lbl_ai_status.configure(text="🎯 Đã tìm thấy mặt bé", text_color="#10B981")
        self._render_canvas()
        self._render_sticker_preview()

    def _reset_to_center(self):
        if self.current_pil is None:
            return
        img_path = self._get_current_path()
        orig_w, orig_h = self.current_pil.size
        default_d = min(orig_w, orig_h) * 0.85
        self.configs[img_path] = CircleCropConfig(
            center_x=orig_w / 2.0,
            center_y=orig_h / 2.0,
            diameter=default_d
        )
        self.slider_zoom.set(1.0)
        self.lbl_zoom_val.configure(text="100%")
        self.lbl_ai_status.configure(text="🔄 Đã căn giữa ảnh", text_color="#3B82F6")
        self._render_canvas()
        self._render_sticker_preview()

    def _auto_detect_all(self):
        count = len(self.image_paths)
        for p in self.image_paths:
            try:
                with Image.open(p) as img:
                    transposed = ImageOps.exif_transpose(img)
                    self.configs[p] = calculate_smart_circle(transposed)
            except Exception:
                continue

        self.lbl_ai_status.configure(text=f"⚡ Đã căn chỉnh xong {count} ảnh!", text_color="#10B981")
        self._load_current_image()

    def _prev_image(self):
        if self.current_idx > 0:
            self.current_idx -= 1
            self._load_current_image()

    def _next_image(self):
        if self.current_idx < len(self.image_paths) - 1:
            self.current_idx += 1
            self._load_current_image()

    def _save_and_close(self):
        if self.on_save_callback:
            self.on_save_callback(self.configs)
        self.destroy()
