"""
Module tự động nhận diện khuôn mặt và cắt ảnh tròn chuẩn dán vở Bé Ngoan.
Sử dụng mô hình AI YuNet (OpenCV) siêu nhẹ, chính xác cao cho ảnh trẻ em.
"""
import os
import math
from typing import Tuple, Optional, Dict, Any
from dataclasses import dataclass
from PIL import Image, ImageDraw, ImageOps
import numpy as np

# Đường dẫn mô hình YuNet ONNX
MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
YUNET_MODEL_PATH = os.path.join(MODEL_DIR, "face_detection_yunet_2023mar.onnx")

@dataclass
class CircleCropConfig:
    center_x: float  # Tọa độ X tâm hình tròn (pixel gốc)
    center_y: float  # Tọa độ Y tâm hình tròn (pixel gốc)
    diameter: float  # Đường kính hình tròn (pixel gốc)

    def to_crop_box(self) -> Tuple[int, int, int, int]:
        half = self.diameter / 2.0
        return (
            int(round(self.center_x - half)),
            int(round(self.center_y - half)),
            int(round(self.center_x + half)),
            int(round(self.center_y + half)),
        )

class FaceDetector:
    _detector = None
    _initialized = False

    @classmethod
    def get_detector(cls):
        if not cls._initialized:
            cls._initialized = True
            if os.path.exists(YUNET_MODEL_PATH):
                try:
                    import cv2
                    cls._detector = cv2.FaceDetectorYN.create(
                        YUNET_MODEL_PATH, "", (320, 320),
                        score_threshold=0.6,
                        nms_threshold=0.3
                    )
                except Exception as e:
                    print(f"Không thể khởi tạo YuNet FaceDetector: {e}")
                    cls._detector = None
        return cls._detector

    @classmethod
    def detect_primary_face(cls, pil_img: Image.Image) -> Optional[Tuple[int, int, int, int, float]]:
        """
        Nhận diện khuôn mặt chính trong ảnh PIL.
        Trả về (x, y, w, h, score) theo kích thước ảnh gốc.
        """
        detector = cls.get_detector()
        if detector is None:
            return None

        try:
            import cv2
            # Chuyển PIL Image sang BGR numpy array
            rgb_img = pil_img.convert("RGB")
            orig_w, orig_h = rgb_img.size
            if orig_w <= 0 or orig_h <= 0:
                return None

            # Giảm kích thước ảnh xuống tối đa 640px để nhận diện cực nhanh mà vẫn chính xác
            max_side = 640
            scale = 1.0
            if max(orig_w, orig_h) > max_side:
                scale = max_side / float(max(orig_w, orig_h))
                new_w = max(32, int(orig_w * scale))
                new_h = max(32, int(orig_h * scale))
                resized_pil = rgb_img.resize((new_w, new_h), Image.Resampling.BILINEAR)
            else:
                new_w, new_h = orig_w, orig_h
                resized_pil = rgb_img

            np_img = np.array(resized_pil)
            bgr_img = cv2.cvtColor(np_img, cv2.COLOR_RGB2BGR)

            detector.setInputSize((new_w, new_h))
            ret, faces = detector.detect(bgr_img)

            if faces is None or len(faces) == 0:
                return None

            # Sắp xếp chọn mặt to nhất và rõ nhất (thường là bé ở trung tâm)
            best_face = None
            best_score = -1.0
            center_x, center_y = new_w / 2.0, new_h / 2.0

            for f in faces:
                fx, fy, fw, fh = f[0], f[1], f[2], f[3]
                score = f[-1]
                # Đánh giá ưu tiên độ tin cậy khuôn mặt người thật (score cao)
                # tránh chọn nhầm tranh vẽ hoạt hình trên tường
                dist = math.hypot((fx + fw / 2.0) - center_x, (fy + fh / 2.0) - center_y)
                dist_penalty = 1.0 - (dist / max(new_w, new_h)) * 0.35
                rank = (score ** 4) * math.sqrt(fw * fh) * dist_penalty

                if rank > best_score:
                    best_score = rank
                    best_face = (fx, fy, fw, fh, score)

            if best_face:
                inv_scale = 1.0 / scale
                fx, fy, fw, fh, score = best_face
                return (
                    int(round(fx * inv_scale)),
                    int(round(fy * inv_scale)),
                    int(round(fw * inv_scale)),
                    int(round(fh * inv_scale)),
                    float(score)
                )
            return None
        except Exception as e:
            print(f"Lỗi khi nhận diện khuôn mặt: {e}")
            return None


def calculate_smart_circle(
    pil_img: Image.Image,
    face_box: Optional[Tuple[int, int, int, int, float]] = None
) -> CircleCropConfig:
    """
    Tự động tính toán tâm và đường kính hình tròn tối ưu:
    - Nếu phát hiện mặt bé: Căn chỉnh lấy trọn đầu, tóc và phần vai áo (tỉ lệ chân dung).
    - Nếu không phát hiện mặt: Căn giữa thông minh (lệch nhẹ lên 1/3 trên để lấy người).
    """
    orig_w, orig_h = pil_img.size
    min_side = min(orig_w, orig_h)

    if face_box is None:
        face_box = FaceDetector.detect_primary_face(pil_img)

    if face_box:
        fx, fy, fw, fh, _ = face_box
        # Tâm mặt bé
        face_cx = fx + fw / 2.0
        face_cy = fy + fh / 2.0

        # Tỉ lệ vàng chân dung tròn cho bé:
        # Đường kính vòng tròn khoảng 2.5 - 2.6 lần chiều cao/rộng mặt
        # để vừa vặn trọn vẹn đầu, nơ/mũ/bím tóc hai bên và cổ áo/vai của bé
        face_size = max(fw, fh)
        desired_d = face_size * 2.55

        # Dịch nhẹ tâm vòng tròn xuống dưới (~8% chiều cao mặt)
        # để mặt bé không bị cọ vào mép trên, nơ cài tóc có khoảng trống thoáng
        circle_cy = face_cy + (fh * 0.08)
        circle_cx = face_cx

        # Giới hạn đường kính không vượt quá kích thước nhỏ nhất của ảnh
        if desired_d > min_side:
            desired_d = float(min_side)
        elif desired_d < 80:
            desired_d = min(min_side, 200.0)

        # Căn chỉnh tâm để không bị tràn ra ngoài biên ảnh
        half_d = desired_d / 2.0
        circle_cx = max(half_d, min(orig_w - half_d, circle_cx))
        circle_cy = max(half_d, min(orig_h - half_d, circle_cy))

        return CircleCropConfig(
            center_x=float(circle_cx),
            center_y=float(circle_cy),
            diameter=float(desired_d)
        )

    # Trường hợp không phát hiện được mặt: Căn giữa thông minh
    default_d = min_side * 0.85
    half_d = default_d / 2.0
    circle_cx = orig_w / 2.0
    # Thường chủ thể nằm hơi lệch lên trên tâm một chút
    circle_cy = orig_h * 0.42
    circle_cy = max(half_d, min(orig_h - half_d, circle_cy))

    return CircleCropConfig(
        center_x=float(circle_cx),
        center_y=float(circle_cy),
        diameter=float(default_d)
    )


def crop_circle_image(
    pil_img: Image.Image,
    crop_config: CircleCropConfig,
    output_size_px: int = 800,
    add_guide_border: bool = True,
    guide_color: Tuple[int, int, int, int] = (175, 175, 175, 255),
    guide_width: int = 2
) -> Image.Image:
    """
    Cắt ảnh thành hình tròn hoàn hảo với viền mịn màng (anti-aliased)
    và đường chỉ cắt kéo mờ hướng dẫn phụ huynh/cô giáo cắt dán.
    """
    # Đảm bảo ảnh ở hệ màu RGB hoặc RGBA và xoay đúng chiều EXIF
    pil_img = ImageOps.exif_transpose(pil_img)
    orig_w, orig_h = pil_img.size

    cx, cy, d = crop_config.center_x, crop_config.center_y, crop_config.diameter
    half = d / 2.0
    left = cx - half
    top = cy - half
    right = cx + half
    bottom = cy + half

    # Nếu vùng cắt tràn ra ngoài ảnh gốc -> Tạo canvas trắng đệm
    pad_left = max(0, int(math.ceil(-left)))
    pad_top = max(0, int(math.ceil(-top)))
    pad_right = max(0, int(math.ceil(right - orig_w)))
    pad_bottom = max(0, int(math.ceil(bottom - orig_h)))

    if pad_left > 0 or pad_top > 0 or pad_right > 0 or pad_bottom > 0:
        new_w = orig_w + pad_left + pad_right
        new_h = orig_h + pad_top + pad_bottom
        padded_img = Image.new("RGB", (new_w, new_h), (255, 255, 255))
        padded_img.paste(pil_img.convert("RGB"), (pad_left, pad_top))
        crop_box = (
            int(round(left + pad_left)),
            int(round(top + pad_top)),
            int(round(right + pad_left)),
            int(round(bottom + pad_top)),
        )
        cropped_square = padded_img.crop(crop_box)
    else:
        crop_box = (int(round(left)), int(round(top)), int(round(right)), int(round(bottom)))
        cropped_square = pil_img.crop(crop_box)

    # Resize về kích thước mong muốn với thuật toán Lanczos sắc nét
    square_img = cropped_square.resize((output_size_px, output_size_px), Image.Resampling.LANCZOS).convert("RGBA")

    # Tạo mask tròn khử răng cưa (2x supersampling)
    hi_size = output_size_px * 2
    hi_mask = Image.new("L", (hi_size, hi_size), 0)
    d_mask = ImageDraw.Draw(hi_mask)
    d_mask.ellipse((0, 0, hi_size - 1, hi_size - 1), fill=255)
    smooth_mask = hi_mask.resize((output_size_px, output_size_px), Image.Resampling.LANCZOS)

    # Áp dụng mask
    result = Image.new("RGBA", (output_size_px, output_size_px), (255, 255, 255, 0))
    result.paste(square_img, (0, 0), mask=smooth_mask)

    # Thêm đường viền cắt kéo siêu nét
    if add_guide_border:
        hi_guide = Image.new("RGBA", (hi_size, hi_size), (0, 0, 0, 0))
        d_guide = ImageDraw.Draw(hi_guide)
        hi_w = max(2, guide_width * 2)
        d_guide.ellipse(
            (hi_w // 2, hi_w // 2, hi_size - 1 - hi_w // 2, hi_size - 1 - hi_w // 2),
            outline=guide_color,
            width=hi_w
        )
        smooth_guide = hi_guide.resize((output_size_px, output_size_px), Image.Resampling.LANCZOS)
        result = Image.alpha_composite(result, smooth_guide)

    return result
