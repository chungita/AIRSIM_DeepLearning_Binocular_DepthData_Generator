import os
import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QLabel, QComboBox,
                             QFileDialog, QMessageBox, QScrollArea, QShortcut)
from PyQt5.QtGui import QPixmap, QPainter, QPen, QColor, QImage, QKeySequence, QFont, QPainterPath
from PyQt5.QtCore import Qt, QSize, QRect, pyqtSignal, QRectF
import numpy as np
import cv2
import re


def read_pfm(file_path):
    """
    讀取 PFM 檔案，回傳 numpy array (height, width) 或 (height, width, 3)
    """
    with open(file_path, 'rb') as f:
        header = f.readline().decode('utf-8').strip()
        if header not in ('PF', 'Pf'):
            raise Exception('不是有效的 PFM 檔案')
        dims = f.readline().decode('utf-8').strip()
        while dims.startswith('#'):
            dims = f.readline().decode('utf-8').strip()
        parts = re.findall(r'-?\d+', dims)
        if len(parts) < 2:
            raise Exception('PFM 無法解析寬高')
        width, height = int(parts[0]), int(parts[1])
        scale = float(f.readline().decode('utf-8').strip())
        endian = '<' if scale < 0 else '>'
        data = np.fromfile(f, endian + 'f4')
        expected = width * height * (3 if header == 'PF' else 1)
        if data.size != expected:
            if data.size > expected:
                data = data[:expected]
            else:
                raise Exception(f'PFM 資料長度不正確: got {data.size}, expected {expected}')
        if header == 'PF':
            return np.reshape(data, (height, width, 3))
        else:
            return np.reshape(data, (height, width))

class LabelingMode:
    MANUAL = "人工標註"
    BULK = "批量標註"

class SelectedColorsWidget(QWidget):
    color_deleted = pyqtSignal(list)
    preview_all_requested = pyqtSignal(bool)
    reset_all_requested = pyqtSignal()
    apply_all_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_preview_active = False
        self.current_language = os.environ.get('AIRSIM_LANGUAGE', 'zh')
        
        # 多語言文字
        self.texts = {
            "zh": {
                "title": "批量標註工具",
                "preview": "👁️ 預覽",
                "close_preview": "關閉預覽",
                "reset": "重置",
                "colors_list_title": "已選擇的批量標註色塊:",
                "no_selection": "無",
                "delete": "🗑️ 刪除",
                "pixels": "像素:",
                "apply_all": "開始批量標註",
                "preview_tooltip": "開關預覽功能，顯示所有已選顏色對應的標註框。",
                "reset_tooltip": "清空所有已選擇的批量標註色塊。"
            },
            "en": {
                "title": "Bulk Labeling Tool",
                "preview": "👁️ Preview",
                "close_preview": "Close Preview",
                "reset": "Reset",
                "colors_list_title": "Selected Bulk Labeling Colors:",
                "no_selection": "None",
                "delete": "🗑️ Delete",
                "pixels": "Pixels:",
                "apply_all": "Start Bulk Labeling",
                "preview_tooltip": "Toggle preview function to show all selected color annotation boxes.",
                "reset_tooltip": "Clear all selected bulk labeling color blocks."
            }
        }
        
        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignTop)

        self.label_title = QLabel(self.texts[self.current_language]["title"])
        self.label_title.setFont(QFont("Arial", 14, QFont.Bold))
        self.label_title.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.label_title)

        button_layout = QHBoxLayout()
        self.preview_btn = QPushButton(self.texts[self.current_language]["preview"])
        self.preview_btn.setCheckable(True)
        self.preview_btn.clicked.connect(self.toggle_preview)
        self.preview_btn.setToolTip(self.texts[self.current_language]["preview_tooltip"])
        self.reset_bulk_btn = QPushButton(self.texts[self.current_language]["reset"])
        self.reset_bulk_btn.clicked.connect(self.reset_all_requested.emit)
        self.reset_bulk_btn.setToolTip(self.texts[self.current_language]["reset_tooltip"])
        button_layout.addWidget(self.preview_btn)
        button_layout.addWidget(self.reset_bulk_btn)
        self.layout.addLayout(button_layout)
        
        self.colors_list_title = QLabel(self.texts[self.current_language]["colors_list_title"])
        self.colors_list_title.setFont(QFont("Arial", 12, QFont.Bold))
        self.layout.addWidget(self.colors_list_title)

        self.colors_list_layout = QVBoxLayout()
        self.layout.addLayout(self.colors_list_layout)

        self.colors_list = []

        self.apply_all_btn = QPushButton(self.texts[self.current_language]["apply_all"])
        self.apply_all_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        self.apply_all_btn.clicked.connect(self.apply_all_requested.emit)
        self.layout.addWidget(self.apply_all_btn)

    def toggle_preview(self, checked):
        self.is_preview_active = checked
        self.preview_all_requested.emit(self.is_preview_active)
        if self.is_preview_active:
            self.preview_btn.setText(self.texts[self.current_language]["close_preview"])
        else:
            self.preview_btn.setText(self.texts[self.current_language]["preview"])

    def update_colors(self, colors_info):
        while self.colors_list_layout.count() > 0:
            item = self.colors_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                while item.layout().count() > 0:
                    sub_item = item.layout().takeAt(0)
                    if sub_item.widget():
                        sub_item.widget().deleteLater()

        self.colors_list = colors_info
        
        if not self.colors_list:
            no_selection_label = QLabel(self.texts[self.current_language]["no_selection"])
            no_selection_label.setStyleSheet("color: gray;")
            self.colors_list_layout.addWidget(no_selection_label)
        else:
            grouped_by_class = {}
            for color_info in self.colors_list:
                class_name = color_info['class_name']
                if class_name not in grouped_by_class:
                    grouped_by_class[class_name] = []
                grouped_by_class[class_name].append(color_info)
            
            for class_name, colors in grouped_by_class.items():
                class_label = QLabel(f"➡️ **類別: {class_name}**")
                # 根據語言調整字體大小
                if self.current_language == "en":
                    class_font_size = 8
                else:
                    class_font_size = 10
                class_label.setFont(QFont("Arial", class_font_size, QFont.Bold))
                self.colors_list_layout.addWidget(class_label)
                
                for color_info in colors:
                    color = color_info['color']
                    
                    color_hbox = QHBoxLayout()
                    color_hbox.setSpacing(5)
                    color_hbox.setContentsMargins(0,0,0,0)
                    
                    color_pixmap = QPixmap(120, 25)
                    color_pixmap.fill(Qt.transparent)
                    painter = QPainter(color_pixmap)
                    painter.setRenderHint(QPainter.Antialiasing)
                    
                    path = QPainterPath()
                    rect = QRectF(0, 0, 119, 24)
                    radius = 8.0
                    path.addRoundedRect(rect, radius, radius)
                    
                    painter.fillPath(path, QColor(color[2], color[1], color[0]))
                    painter.end()
                    
                    color_icon_label = QLabel()
                    color_icon_label.setPixmap(color_pixmap)
                    color_icon_label.setFixedSize(60, 25)
                    
                    delete_btn = QPushButton(self.texts[self.current_language]["delete"])
                    delete_btn.clicked.connect(lambda _, c=color, cn=class_name: self.delete_color(c, cn))
                    delete_btn.setFixedSize(80, 30)
                    # 根據語言調整按鈕字體大小
                    if self.current_language == "en":
                        delete_btn.setFont(QFont("Arial", 8))
                    else:
                        delete_btn.setFont(QFont("Arial", 9))

                    color_hbox.addStretch(1)
                    pixel_count = color_info.get('pixel_count', None)
                    if pixel_count is not None:
                        count_label = QLabel(f"{self.texts[self.current_language]['pixels']} {pixel_count}")
                        count_label.setStyleSheet("color: #888;")
                        # 根據語言調整像素計數字體大小
                        if self.current_language == "en":
                            count_label.setFont(QFont("Arial", 8))
                        else:
                            count_label.setFont(QFont("Arial", 9))
                        color_hbox.addWidget(count_label, 0, Qt.AlignRight | Qt.AlignVCenter)

                    color_hbox.addWidget(color_icon_label)
                    color_hbox.addWidget(delete_btn)
                    
                    self.colors_list_layout.addLayout(color_hbox)
        
        self.adjustSize()
        self.update()

    def set_language(self, language):
        """設置語言"""
        self.current_language = language
        
        # 根據語言調整字體大小
        if language == "en":
            title_font_size = 12
            list_title_font_size = 7
            button_font_size = 9
        else:
            title_font_size = 14
            list_title_font_size = 12
            button_font_size = 10
        
        # 更新標題字體
        title_font = QFont("Arial", title_font_size, QFont.Bold)
        self.label_title.setFont(title_font)
        self.label_title.setText(self.texts[self.current_language]["title"])
        
        # 更新列表標題字體
        list_title_font = QFont("Arial", list_title_font_size, QFont.Bold)
        self.colors_list_title.setFont(list_title_font)
        self.colors_list_title.setText(self.texts[self.current_language]["colors_list_title"])
        
        # 更新按鈕字體
        button_font = QFont("Arial", button_font_size)
        self.preview_btn.setFont(button_font)
        self.reset_bulk_btn.setFont(button_font)
        self.apply_all_btn.setFont(button_font)
        
        # 更新按鈕文字
        if self.is_preview_active:
            self.preview_btn.setText(self.texts[self.current_language]["close_preview"])
        else:
            self.preview_btn.setText(self.texts[self.current_language]["preview"])
        
        self.reset_bulk_btn.setText(self.texts[self.current_language]["reset"])
        self.apply_all_btn.setText(self.texts[self.current_language]["apply_all"])
        
        # 更新工具提示
        self.preview_btn.setToolTip(self.texts[self.current_language]["preview_tooltip"])
        self.reset_bulk_btn.setToolTip(self.texts[self.current_language]["reset_tooltip"])
        
        # 重新更新顏色列表以更新文字
        self.update_colors(self.colors_list)

    def delete_color(self, color, class_name):
        original_list = list(self.colors_list)
        new_list = [item for item in original_list if not (item['color'] == color and item['class_name'] == class_name)]
        
        if len(new_list) < len(original_list):
            self.colors_list = new_list
            self.color_deleted.emit(self.colors_list)
            self.update_colors(self.colors_list)
            # 已刪除該設定

class ImageLabeler(QWidget):
    image_changed = pyqtSignal(QPixmap, list)
    colors_updated = pyqtSignal(list)
    
    def __init__(self):
        super().__init__()
        self.input_dir = "ProcessData"
        self.yolo_output_dir = "YOLO_Label"
        self.mot_output_dir = "MOT_Label"
        self.label_img_prefix = "Seg"
        self.output_name_prefix = "Img0"
        self.clear_output_folder = False
        
        self.FOV_degrees = 90
        self.image_width = 640
        self.image_height = 480
        self.baseline_meters = 1.0
        self.focal_length = (self.image_width / 2) / np.tan(np.deg2rad(self.FOV_degrees / 2))

        self.images = []
        self.current_image_index = 0
        self.original_image_cv2 = None
        self.boxes_by_image = {}
        self.current_boxes = []
        self.selected_box_index = None
        self.class_list = []
        self.selected_class_id = 0
        self.labeling_mode = LabelingMode.MANUAL
        self.bulk_labeling_list = []
        self.preview_boxes = []
        self.is_preview_active = False
        self.labeling_format = 'ALL'
        self.all_labels_for_mot = {}
        self.next_mot_id = 1
        self.pixel_threshold = 0
        self.color_tolerance = 3
        
        self.load_settings()
        self.load_classes()

    def load_settings(self):
        settings_file = os.path.join(os.path.dirname(__file__), "Settings.txt")
        if os.path.exists(settings_file):
            with open(settings_file, "r", encoding="utf-8") as f:
                for line in f:
                    if ':' in line:
                        key, value = line.strip().split(':', 1)
                        if key == "Input_folder":
                            self.input_dir = value
                        elif key == "YOLO_Label_folder":
                            self.yolo_output_dir = value
                        elif key == "MOT_Label_folder":
                            self.mot_output_dir = value
                        elif key == "Label_Img":
                            self.label_img_prefix = value
                        elif key == "Output_Name":
                            self.output_name_prefix = value
                        elif key == "Clear_Output_Folder":
                            self.clear_output_folder = (value.lower() == "true")
                        elif key == "FOV_degrees":
                            self.FOV_degrees = float(value)
                        elif key == "image_width":
                            self.image_width = int(value)
                        elif key == "image_height":
                            self.image_height = int(value)
                        elif key == "Threshold":
                            try:
                                self.pixel_threshold = int(value)
                            except:
                                self.pixel_threshold = 0
        # 使用預設設定

        self.focal_length = (self.image_width / 2) / np.tan(np.deg2rad(self.FOV_degrees / 2))

    def create_color_mask(self, image, target_color):
        """
        創建顏色遮罩，包含所有相似顏色的像素
        """
        color_to_find = np.array(target_color)
        lower_bound = np.clip(color_to_find - self.color_tolerance, 0, 255)
        upper_bound = np.clip(color_to_find + self.color_tolerance, 0, 255)
        return np.all((image >= lower_bound) & (image <= upper_bound), axis=-1)

    def load_classes(self):
        class_file = os.path.join(os.path.dirname(__file__), "predefined_classes.txt")
        if not os.path.exists(class_file):
            print("錯誤: 找不到 predefined_classes.txt")
            return
        with open(class_file, "r", encoding="utf-8") as f:
            self.class_list = [line.strip() for line in f if line.strip()]
        if not self.class_list:
            print("錯誤: predefined_classes.txt 為空")

    def load_images(self):
        if not os.path.exists(self.input_dir):
            print(f"錯誤: 輸入資料夾不存在: {self.input_dir}")
            return
        
        self.images = [f for f in os.listdir(self.input_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg')) and f.startswith(self.label_img_prefix)]
        self.images.sort(key=lambda f: int(re.sub(r'[^0-9]', '', f)) if re.sub(r'[^0-9]', '', f) else 0)
        
        if self.images:
            self.load_image()

    def load_image(self):
        if not self.images:
            return
        
        img_name = self.images[self.current_image_index]
        img_path = os.path.join(self.input_dir, img_name)
        
        self.original_image_cv2 = cv2.imread(img_path)
        if self.original_image_cv2 is None:
            print(f"錯誤: 無法載入圖片: {img_path}")
            return
            
        self.current_boxes = self.boxes_by_image.get(img_name, [])
        self.selected_box_index = None
        self.update_image_display()

    def update_image_display(self):
        if self.original_image_cv2 is not None:
            if self.is_preview_active:
                self.generate_preview_boxes()
                self.colors_updated.emit(self.get_bulk_list_with_counts())
            else:
                self.preview_boxes.clear()
            self.emit_image_changed()
    
    def emit_image_changed(self):
        if self.original_image_cv2 is not None:
            h, w, ch = self.original_image_cv2.shape
            bytes_per_line = ch * w
            q_img = QImage(self.original_image_cv2.data, w, h, bytes_per_line, QImage.Format_BGR888)
            pixmap = QPixmap.fromImage(q_img)
            combined_boxes = self.current_boxes + self.preview_boxes
            self.image_changed.emit(pixmap, combined_boxes)

    def on_click(self, pos):
        if self.original_image_cv2 is None or self.selected_class_id is None:
            return

        x, y = pos.width(), pos.height()
        
        h, w, _ = self.original_image_cv2.shape
        if not (0 <= x < w and 0 <= y < h):
            return

        if self.labeling_mode == LabelingMode.BULK:
            clicked_color = self.original_image_cv2[y, x].tolist()
            clicked_class_name = self.class_list[self.selected_class_id]
            
            seg_mask = np.all(self.original_image_cv2 == clicked_color, axis=-1)
            num, labels, stats, centroids = cv2.connectedComponentsWithStats(seg_mask.astype(np.uint8), connectivity=8)
            seed_cx, seed_cy = x, y
            for comp_id in range(1, num):
                x0, y0, w, h, area = stats[comp_id]
                if x0 <= x < x0+w and y0 <= y < y0+h:
                    cX, cY = centroids[comp_id]
                    seed_cx, seed_cy = float(cX), float(cY)
                    break

            self.bulk_labeling_list.append({
                'color': clicked_color,
                'class_id': self.selected_class_id,
                'class_name': clicked_class_name,
                'seed_cx': seed_cx, 'seed_cy': seed_cy,
                'last_cx': seed_cx, 'last_cy': seed_cy,
                'last_width': 0,
                'last_height': 0
            })
            if self.is_preview_active:
                self.colors_updated.emit(self.get_bulk_list_with_counts())
            else:
                self.colors_updated.emit(self.bulk_labeling_list)
            self.update_image_display()
        else:
            existing_box_index = -1
            for i, box in enumerate(self.current_boxes):
                box_rect = QRect(box[0], box[1], box[2]-box[0], box[3]-box[1])
                if box_rect.contains(x, y):
                    existing_box_index = i
                    break
            
            if existing_box_index != -1:
                self.current_boxes.pop(existing_box_index)
                self.selected_box_index = None
                self.emit_image_changed()
                return

            if self.selected_box_index is not None and not self.current_boxes[self.selected_box_index][6]:
                self.current_boxes.pop(self.selected_box_index)
                self.selected_box_index = None

            clicked_color = self.original_image_cv2[y, x]
            mask = np.all(self.original_image_cv2 == clicked_color, axis=-1)
            coords = np.argwhere(mask)
            
            if coords.size == 0:
                return

            ymin, xmin = coords.min(axis=0)
            ymax, xmax = coords.max(axis=0)
            
            self.current_boxes.append((xmin, ymin, xmax, ymax, self.selected_class_id, -1, False))
            self.selected_box_index = len(self.current_boxes) - 1
            self.emit_image_changed()
            
    def clear_single_boxes(self):
        self.current_boxes = [box for box in self.current_boxes if box[6]]
        self.selected_box_index = None
        self.emit_image_changed()

    def confirm_box(self):
        if self.selected_box_index is not None and not self.current_boxes[self.selected_box_index][6]:
            box = list(self.current_boxes[self.selected_box_index])
            box[5] = self.next_mot_id
            self.next_mot_id += 1
            box[6] = True
            self.current_boxes[self.selected_box_index] = tuple(box)
            self.selected_box_index = None
            self.emit_image_changed()
    
    def cancel_box(self):
        if self.selected_box_index is not None and not self.current_boxes[self.selected_box_index][6]:
            self.current_boxes.pop(self.selected_box_index)
            self.selected_box_index = None
            self.emit_image_changed()
    
    def reset_bulk_labeling(self):
        """
        重置批量標註設定
        """
        self.bulk_labeling_list.clear()
        self.preview_boxes.clear()
        self.update_preview()

    def delete_bulk_color(self, new_colors_list):
        self.bulk_labeling_list = new_colors_list
        if self.is_preview_active:
            self.colors_updated.emit(self.get_bulk_list_with_counts())
        else:
            self.colors_updated.emit(self.bulk_labeling_list)
        self.update_image_display()

    def set_preview_mode(self, is_active):
        self.is_preview_active = is_active
        if self.is_preview_active:
            self.colors_updated.emit(self.get_bulk_list_with_counts())
        else:
            self.colors_updated.emit(self.bulk_labeling_list)
        self.update_image_display()
    
    def generate_preview_boxes(self):
        self.preview_boxes.clear()
        if self.original_image_cv2 is None:
            return
        
        for item in self.bulk_labeling_list:
            mask = self.create_color_mask(self.original_image_cv2, item['color'])

            pixel_count = int(np.count_nonzero(mask))
            if pixel_count < self.pixel_threshold:
                continue

            # 找到所有匹配顏色的像素座標，計算包含所有像素的最小邊界框
            coords = np.argwhere(mask)
            if coords.size > 0:
                ymin, xmin = coords.min(axis=0)
                ymax, xmax = coords.max(axis=0)
                self.preview_boxes.append((xmin, ymin, xmax, ymax, item['class_id'], -1, True))

    def save_labels(self):
        if self.original_image_cv2 is None:
            return
        
        img_name = self.images[self.current_image_index]
        
        confirmed_boxes = [box for box in self.current_boxes if box[6]]
        self.boxes_by_image[img_name] = confirmed_boxes

        self.all_labels_for_mot[self.current_image_index] = confirmed_boxes

        if self.labeling_format == 'YOLO' or self.labeling_format == 'ALL':
            if not os.path.exists(self.yolo_output_dir):
                os.makedirs(self.yolo_output_dir)
            img_number_match = re.search(r'\d+', img_name)
            if img_number_match:
                img_number = img_number_match.group(0)
                txt_name = f"{self.output_name_prefix}_{img_number}.txt"
                txt_path = os.path.join(self.yolo_output_dir, txt_name)
                
                with open(txt_path, "w") as f:
                    if confirmed_boxes:
                        h, w, _ = self.original_image_cv2.shape
                        for xmin, ymin, xmax, ymax, cls_id, _, _ in confirmed_boxes:
                            x_center = ((xmin + xmax) / 2) / w
                            y_center = ((ymin + ymax) / 2) / h
                            bbox_w = (xmax - xmin) / w
                            bbox_h = (ymax - ymin) / h
                            f.write(f"{cls_id} {x_center:.6f} {y_center:.6f} {bbox_w:.6f} {bbox_h:.6f}\n")
    
    def next_image(self):
        """
        載入下一張圖片。
        """
        if self.current_image_index < len(self.images) - 1:
            if self.labeling_mode == LabelingMode.MANUAL:
                self.save_labels()

            self.current_image_index += 1
            self.load_image()
            self.current_boxes = self.boxes_by_image.get(self.images[self.current_image_index], [])
            self.selected_box_index = None
            self.update_image_display()
        # 已是最後一張圖片

    def previous_image(self):
        self.save_labels()
        if self.current_image_index > 0:
            self.current_image_index -= 1
            self.load_image()
        # 已是第一張圖片

    def save_mot_file(self):
        if self.labeling_format in ['MOT', 'ALL']:
            if not os.path.exists(self.mot_output_dir):
                os.makedirs(self.mot_output_dir)
            
            mot_path = os.path.join(self.mot_output_dir, "Img0.txt")
            lines = []
            cx = self.image_width / 2.0
            cy = self.image_height / 2.0
            f_len = self.focal_length

            for frame_idx, boxes in self.all_labels_for_mot.items():
                frame_num = frame_idx
                if frame_idx < len(self.images):
                    img_name = self.images[frame_idx]
                    m = re.search(r'\d+', img_name)
                    if m:
                        frame_num = int(m.group(0))

                depth_num_match = re.search(r'\d+', self.images[frame_idx])
                depth_num = int(depth_num_match.group(0)) if depth_num_match else frame_idx

                seg_path = os.path.join(self.input_dir, f"Seg_{depth_num}.png")
                depth_path = os.path.join(self.input_dir, f"DepthGT_{depth_num}.pfm")

                seg_img = None
                if os.path.exists(seg_path):
                    seg_bgr = cv2.imread(seg_path)
                    if seg_bgr is not None:
                        seg_img = cv2.cvtColor(seg_bgr, cv2.COLOR_BGR2RGB)

                depth = None
                if os.path.exists(depth_path):
                    try:
                        depth = read_pfm(depth_path)
                        if depth.ndim == 3:
                            depth = depth[:, :, 0]
                    except Exception as e:
                        print(f"讀取深度失敗 {depth_path}: {e}")
                        depth = None

                for xmin, ymin, xmax, ymax, cls_id, mot_id, _ in boxes:
                    width = xmax - xmin
                    height = ymax - ymin
                    conf = 1

                    z = 0.0
                    x_cam = 0.0
                    y_cam = 0.0

                    if seg_img is not None and depth is not None:
                        u = xmin + width / 2.0
                        v = ymin + height / 2.0
                        h_d, w_d = depth.shape[:2]
                        
                        if depth.shape[:2] != seg_img.shape[:2]:
                            h_s, w_s = seg_img.shape[:2]
                            u_idx = int(round(u * w_d / w_s))
                            v_idx = int(round(v * h_d / h_s))
                        else:
                            u_idx = int(round(u))
                            v_idx = int(round(v))

                        u_idx = max(0, min(w_d - 1, u_idx))
                        v_idx = max(0, min(h_d - 1, v_idx))

                        z_val = depth[v_idx, u_idx]
                        if np.isfinite(z_val) and z_val > 1e-6:
                            z = float(z_val)
                        else:
                            if depth.shape[:2] != seg_img.shape[:2]:
                                h_s, w_s = seg_img.shape[:2]
                                depth_xmin = int(round(xmin * w_d / w_s))
                                depth_ymin = int(round(ymin * h_d / h_s))
                                depth_xmax = int(round(xmax * w_d / w_s))
                                depth_ymax = int(round(ymax * h_d / h_s))
                            else:
                                depth_xmin, depth_ymin = int(xmin), int(ymin)
                                depth_xmax, depth_ymax = int(xmax), int(ymax)
                            
                            depth_xmin = max(0, min(w_d - 1, depth_xmin))
                            depth_ymin = max(0, min(h_d - 1, depth_ymin))
                            depth_xmax = max(0, min(w_d - 1, depth_xmax))
                            depth_ymax = max(0, min(h_d - 1, depth_ymax))
                            
                            if depth_xmax > depth_xmin and depth_ymax > depth_ymin:
                                roi_depth = depth[depth_ymin:depth_ymax+1, depth_xmin:depth_xmax+1]
                                valid_depths = roi_depth[(roi_depth > 1e-6) & np.isfinite(roi_depth)]
                                
                                if len(valid_depths) > 0:
                                    z = float(np.median(valid_depths))
                                else:
                                    z = 0.0
                            else:
                                z = 0.0

                    u = xmin + width / 2.0
                    v = ymin + height / 2.0
                    if z > 0:
                        x_cam = (u - cx) * z / f_len
                        y_cam = (v - cy) * z / f_len
                    else:
                        x_cam = 0.0
                        y_cam = 0.0

                    lines.append(f"{frame_num},{mot_id},{xmin},{ymin},{width},{height},1,{x_cam:.6f},{y_cam:.6f},{z:.6f}\n")

            with open(mot_path, "w", encoding="utf-8") as f:
                f.writelines(lines)
            QMessageBox.information(self, "儲存完成", f"MOT 格式檔案已儲存至 {self.mot_output_dir}。")
            self.all_labels_for_mot.clear()
            self.next_mot_id = 1

    def apply_bulk_labeling(self):
        if not self.bulk_labeling_list:
            print("警告: 請先在圖片上點選要標註的色塊")
            return
        if not os.path.exists(self.yolo_output_dir):
            os.makedirs(self.yolo_output_dir)
        if not os.path.exists(self.mot_output_dir):
            os.makedirs(self.mot_output_dir)

        for d in [self.yolo_output_dir, self.mot_output_dir]:
            if os.path.exists(d):
                for filename in os.listdir(d):
                    if filename.endswith(".txt"):
                        try:
                            os.remove(os.path.join(d, filename))
                        except OSError:
                            pass

        all_mot_lines = []
        mot_id_by_color = {}
        next_mot_id = 1
        
        for i, img_name in enumerate(self.images):
            img_path = os.path.join(self.input_dir, img_name)
            img = cv2.imread(img_path)
            if img is None:
                continue
            
            m = re.search(r'(\d+)', img_name)
            frame_num = int(m.group(0)) if m else (i + 1)
            seg_path = os.path.join(self.input_dir, f"{self.label_img_prefix}_{frame_num}.png")
            seg_img = None
            if os.path.exists(seg_path):
                try:
                    seg_img = cv2.imread(seg_path)
                    if seg_img is None:
                        print(f"警告: 無法載入分割圖片 {seg_path}。將使用空 mask。")
                except Exception as e:
                    print(f"載入分割圖片 {seg_path} 時發生錯誤: {e}。將使用空 mask。")
            else:
                print(f"警告: 未找到分割圖片 {seg_path}。將使用空 mask。")
            
            labels_to_save_yolo = []
            labels_to_save_mot = []
            
            for item in self.bulk_labeling_list:
                color_to_find = np.array(item['color'])
                cls_id = item['class_id']
                color_key = (cls_id, tuple(item['color']))
                if color_key not in mot_id_by_color:
                    mot_id_by_color[color_key] = next_mot_id
                    next_mot_id += 1
                mot_id = mot_id_by_color[color_key]
                
                mask_all = self.create_color_mask(seg_img, item['color'])

                pixel_count = int(np.count_nonzero(mask_all))
                if pixel_count < self.pixel_threshold:
                    continue

                # 直接使用所有匹配像素的最小邊界框
                coords = np.argwhere(mask_all)
                if coords.size > 0:
                    ymin, xmin = coords.min(axis=0)
                    ymax, xmax = coords.max(axis=0)
                    
                    item['last_width'] = xmax - xmin
                    item['last_height'] = ymax - ymin

                    if self.labeling_format in ['YOLO', 'ALL']:
                        h, w = img.shape[:2]
                        x_center = ((xmin + xmax) / 2) / w
                        y_center = ((ymin + ymax) / 2) / h
                        bbox_w = (xmax - xmin) / w
                        bbox_h = (ymax - ymin) / h
                        labels_to_save_yolo.append(f"{cls_id} {x_center:.6f} {y_center:.6f} {bbox_w:.6f} {bbox_h:.6f}\n")

                    z = 0.0
                    depth_path = os.path.join(self.input_dir, f"DepthGT_{frame_num}.pfm")
                    if os.path.exists(depth_path):
                        depth = read_pfm(depth_path)
                        if depth.ndim == 3:
                            depth = depth[:, :, 0]
                        
                        seg_height, seg_width = seg_img.shape[:2]
                        # 使用統一的相機參數，而不是基於分割圖的尺寸
                        cx = self.image_width / 2.0
                        cy = self.image_height / 2.0
                        f_len = self.focal_length

                        roi_seg = seg_img[ymin:ymax+1, xmin:xmax+1]
                        color_mask_roi = self.create_color_mask(roi_seg, item['color'])
                        
                        h_d, w_d = depth.shape[:2]
                        z = 0.0
                        
                        if np.any(color_mask_roi):
                            target_coords = np.where(color_mask_roi)
                            
                            abs_y_coords = target_coords[0] + ymin
                            abs_x_coords = target_coords[1] + xmin
                            
                            if depth.shape[:2] != seg_img.shape[:2]:
                                h_s, w_s = seg_img.shape[:2]
                                depth_x_coords = np.round(abs_x_coords * w_d / w_s).astype(int)
                                depth_y_coords = np.round(abs_y_coords * h_d / h_s).astype(int)
                            else:
                                depth_x_coords = abs_x_coords
                                depth_y_coords = abs_y_coords
                            
                            depth_x_coords = np.clip(depth_x_coords, 0, w_d - 1)
                            depth_y_coords = np.clip(depth_y_coords, 0, h_d - 1)
                            
                            depth_values = depth[depth_y_coords, depth_x_coords]
                            valid_depths = depth_values[(depth_values > 1e-6) & np.isfinite(depth_values)]
                            
                            if len(valid_depths) > 0:
                                z = float(np.median(valid_depths))
                            else:
                                u_box = (xmin + xmax) / 2.0
                                v_box = (ymin + ymax) / 2.0
                                
                                if depth.shape[:2] != seg_img.shape[:2]:
                                    h_s, w_s = seg_img.shape[:2]
                                    u_idx = int(round(u_box * w_d / w_s))
                                    v_idx = int(round(v_box * h_d / h_s))
                                else:
                                    u_idx = int(round(u_box))
                                    v_idx = int(round(v_box))
                                
                                u_idx = max(0, min(w_d - 1, u_idx))
                                v_idx = max(0, min(h_d - 1, v_idx))
                                
                                z_val = depth[v_idx, u_idx]
                                if np.isfinite(z_val) and z_val > 1e-6:
                                    z = float(z_val)

                    cx = self.image_width / 2.0
                    cy = self.image_height / 2.0
                    f_len = self.focal_length
                    
                    u_box = (xmin + xmax) / 2.0
                    v_box = (ymin + ymax) / 2.0
                    
                    # 如果分割圖和設定尺寸不同，需要映射座標到設定尺寸
                    if seg_img.shape[:2] != (self.image_height, self.image_width):
                        h_s, w_s = seg_img.shape[:2]
                        u_cam = u_box * self.image_width / w_s
                        v_cam = v_box * self.image_height / h_s
                    else:
                        u_cam = u_box
                        v_cam = v_box
                    
                    x_cam = (u_cam - cx) * z / f_len if z > 0 else 0.0
                    y_cam = (v_cam - cy) * z / f_len if z > 0 else 0.0

                    labels_to_save_mot.append(f"{frame_num},{mot_id},{xmin},{ymin},{xmax-xmin},{ymax-ymin},1,{x_cam:.6f},{y_cam:.6f},{z:.6f}\n")
 
            if self.labeling_format in ['YOLO', 'ALL']:
                img_number_match = re.search(r'\d+', img_name)
                if img_number_match:
                    img_number = img_number_match.group(0)
                    txt_name = f"{self.output_name_prefix}_{img_number}.txt"
                    txt_path = os.path.join(self.yolo_output_dir, txt_name)
                    with open(txt_path, "w") as f:
                        if labels_to_save_yolo:
                            f.writelines(labels_to_save_yolo)
                            
            if labels_to_save_mot:
                all_mot_lines.extend(labels_to_save_mot)
 
        if all_mot_lines:
            mot_path = os.path.join(self.mot_output_dir, "Img0.txt")
            with open(mot_path, "w", encoding="utf-8") as f:
                f.writelines(all_mot_lines)
         
        QMessageBox.information(self, "批量標註", "批量標註完成！")
        self.bulk_labeling_list.clear()
        self.colors_updated.emit(self.bulk_labeling_list)
        self.load_image()

    def get_bulk_list_with_counts(self):
        if self.original_image_cv2 is None:
            return list(self.bulk_labeling_list)
        result = []
        for item in self.bulk_labeling_list:
            mask = self.create_color_mask(self.original_image_cv2, item['color'])
            
            count = int(np.count_nonzero(mask))
            new_item = dict(item)
            new_item['pixel_count'] = count
            result.append(new_item)
        return result

class ImageWidget(QLabel):
    box_requested = pyqtSignal(QSize)
    confirm_box = pyqtSignal()

    def __init__(self, labeler, parent=None):
        super().__init__(parent)
        self.labeler = labeler
        self.pixmap = None
        self.boxes = []
        self.setMouseTracking(True)
        self.setScaledContents(True)
        self.scale_factor = 1.0
        self.initial_font_size = 10
        self.show_labels = True

    def set_image(self, pixmap, boxes):
        self.pixmap = pixmap
        self.boxes = boxes
        self.setFixedSize(self.pixmap.size() * self.scale_factor)
        self.update()

    def set_show_labels(self, visible):
        self.show_labels = visible
        self.update()

    def mousePressEvent(self, event):
        if self.pixmap is None:
            return

        local_x = int(event.x() / self.scale_factor)
        local_y = int(event.y() / self.scale_factor)

        if event.button() == Qt.LeftButton:
            if 0 <= local_x < self.pixmap.width() and 0 <= local_y < self.pixmap.height():
                self.box_requested.emit(QSize(local_x, local_y))
        elif event.button() == Qt.RightButton:
            self.confirm_box.emit()
    
    def wheelEvent(self, event):
        if self.pixmap is None:
            return
        
        delta = event.angleDelta().y()
        old_scale_factor = self.scale_factor
        
        if delta > 0:
            self.scale_factor *= 1.1
        else:
            self.scale_factor /= 1.1
        
        scroll_area = self.parent().parent()
        if scroll_area:
            min_scale_w = scroll_area.viewport().width() / self.pixmap.width()
            min_scale_h = scroll_area.viewport().height() / self.pixmap.height()
            min_scale = min(min_scale_w, min_scale_h)
            self.scale_factor = max(self.scale_factor, min_scale)

        if self.scale_factor != old_scale_factor:
            self.setFixedSize(self.pixmap.size() * self.scale_factor)
            
            if scroll_area:
                h_bar = scroll_area.horizontalScrollBar()
                v_bar = scroll_area.verticalScrollBar()
                
                mouse_pos = event.pos()
                new_x = mouse_pos.x() * (self.scale_factor / old_scale_factor)
                new_y = mouse_pos.y() * (self.scale_factor / old_scale_factor)
                
                h_bar.setValue(int(h_bar.value() + new_x - mouse_pos.x()))
                v_bar.setValue(int(v_bar.value() + new_y - mouse_pos.y()))
            
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        if self.pixmap is not None:
            scaled_pixmap = self.pixmap.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            painter.drawPixmap(self.rect(), scaled_pixmap)

            boxes_to_draw = []
            if self.labeler.labeling_mode == LabelingMode.BULK and self.labeler.is_preview_active:
                boxes_to_draw = self.labeler.preview_boxes
            else:
                boxes_to_draw = self.labeler.current_boxes

            drawn_label_rects = []
            image_rect = self.rect()

            for (xmin, ymin, xmax, ymax, cls_id, mot_id, confirmed) in boxes_to_draw:
                pen_color = QColor(0, 255, 0) if confirmed else QColor(255, 0, 0)
                pen = QPen(pen_color)
                pen.setWidth(int(2 * self.scale_factor) if self.scale_factor > 1 else 2)
                painter.setPen(pen)

                scaled_xmin = int(xmin * self.scale_factor)
                scaled_ymin = int(ymin * self.scale_factor)
                scaled_xmax = int(xmax * self.scale_factor)
                scaled_ymax = int(ymax * self.scale_factor)

                painter.drawRect(QRect(scaled_xmin, scaled_ymin, scaled_xmax - scaled_xmin, scaled_ymax - scaled_ymin))
                
                if self.show_labels and confirmed:
                    class_name = self.labeler.class_list[cls_id]
                    label_text = f"{class_name} (ID:{mot_id})" if mot_id != -1 else class_name
                    font = painter.font()
                    font.setPointSize(max(self.initial_font_size, int(self.initial_font_size * self.scale_factor)))
                    painter.setFont(font)

                    label_size = painter.fontMetrics().size(Qt.TextSingleLine, label_text)
                    label_rect = QRect()
                    
                    label_rect.setRect(scaled_xmin, scaled_ymin - label_size.height() - 5, label_size.width() + 10, label_size.height() + 5)
                    
                    overlap = False
                    for existing_rect in drawn_label_rects:
                        if existing_rect.intersects(label_rect):
                            overlap = True
                            break
                    if overlap or label_rect.top() < image_rect.top():
                        label_rect.setRect(scaled_xmin, scaled_ymax + 5, label_size.width() + 10, label_size.height() + 5)
                        overlap = False
                        for existing_rect in drawn_label_rects:
                            if existing_rect.intersects(label_rect):
                                overlap = True
                                break
                        if overlap or label_rect.bottom() > image_rect.bottom():
                            label_rect.setRect(scaled_xmax - label_size.width() - 10, scaled_ymax + 5, label_size.width() + 10, label_size.height() + 5)

                    if label_rect.left() < image_rect.left():
                        label_rect.moveLeft(image_rect.left())
                    if label_rect.right() > image_rect.right():
                        label_rect.moveRight(image_rect.right())

                    painter.setPen(Qt.NoPen)
                    painter.setBrush(QColor(0, 0, 0, 150))
                    painter.drawRoundedRect(label_rect, 5, 5)
                    
                    painter.setPen(QPen(QColor(255, 255, 255)))
                    painter.drawText(label_rect.adjusted(5, 2, -5, -2), Qt.AlignVCenter | Qt.AlignLeft, label_text)

                    drawn_label_rects.append(label_rect)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # 語言設定 - 從環境變數讀取，如果沒有則預設中文
        self.current_language = os.environ.get('AIRSIM_LANGUAGE', 'zh')
        self.texts = {
            "zh": {
                "title": "Segmentation → YOLO 標註工具",
                "show_labels": "顯示標籤",
                "manual_mode": "人工標註",
                "bulk_mode": "批量標註",
                "select_input": "選擇輸入資料夾",
                "select_output": "選擇輸出資料夾",
                "yolo": "YOLO",
                "mot": "MOT",
                "all": "ALL",
                "prev_image": "上一張 (A)",
                "next_image": "下一張 (D)",
                "language": "🌐 語言",
                "mode_switch": "模式切換",
                "bulk_mode_msg": "已切換為批量標註模式，請點擊圖片上的色塊來選定顏色。",
                "manual_mode_msg": "已切換為人工標註模式。",
                "format_switch": "標註格式",
                "format_msg": "已切換標註格式為: {format}",
                "select_input_folder": "選擇輸入資料夾",
                "select_output_folder": "選擇輸出資料夾"
            },
            "en": {
                "title": "Segmentation → YOLO Labeling Tool",
                "show_labels": "Show Labels",
                "manual_mode": "Manual",
                "bulk_mode": "Bulk",
                "select_input": "Select Input Folder",
                "select_output": "Select Output Folder",
                "yolo": "YOLO",
                "mot": "MOT",
                "all": "ALL",
                "prev_image": "Previous (A)",
                "next_image": "Next (D)",
                "language": "🌐 Language",
                "mode_switch": "Mode Switch",
                "bulk_mode_msg": "Switched to bulk labeling mode, please click on color blocks in the image to select colors.",
                "manual_mode_msg": "Switched to manual labeling mode.",
                "format_switch": "Labeling Format",
                "format_msg": "Switched labeling format to: {format}",
                "select_input_folder": "Select Input Folder",
                "select_output_folder": "Select Output Folder"
            }
        }
        
        self.setWindowTitle(self.texts[self.current_language]["title"])
        self.setGeometry(100, 100, 1024, 768)

        self.labeler = ImageLabeler()
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        main_layout = QHBoxLayout(self.central_widget)
        left_panel_layout = QVBoxLayout()
        
        self._setup_ui(left_panel_layout)
        
        self.selected_colors_widget = SelectedColorsWidget()
        self.selected_colors_widget.setFixedWidth(250)
        
        main_layout.addLayout(left_panel_layout, 1)
        main_layout.addWidget(self.selected_colors_widget)
        
        self._connect_signals()
        self._setup_shortcuts()
        
        self.labeler.load_images()
        self.update_image_combo()
        
        self.selected_colors_widget.hide()
        
        self.show()
    
    def showEvent(self, event):
        super().showEvent(event)
        self.fit_image_to_view()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.fit_image_to_view()

    def fit_image_to_view(self):
        if self.labeler.original_image_cv2 is None:
            return
        
        h, w, ch = self.labeler.original_image_cv2.shape
        q_img = QImage(self.labeler.original_image_cv2.data, w, h, ch * w, QImage.Format_BGR888)
        pixmap = QPixmap.fromImage(q_img)
        
        pixmap_size = pixmap.size()
        viewport_size = self.scroll_area.viewport().size()
        
        if viewport_size.width() > 0 and viewport_size.height() > 0 and pixmap_size.width() > 0 and pixmap_size.height() > 0:
            scale_w = viewport_size.width() / pixmap_size.width()
            scale_h = viewport_size.height() / pixmap_size.height()
            self.image_widget.scale_factor = min(scale_w, scale_h)

        self.image_widget.set_image(pixmap, self.labeler.current_boxes + self.labeler.preview_boxes)

    def _setup_ui(self, layout):
        top_bar = QHBoxLayout()

        self.show_labels_btn = QPushButton(self.texts[self.current_language]["show_labels"])
        self.show_labels_btn.setCheckable(True)
        self.show_labels_btn.setChecked(True)
        self.show_labels_btn.clicked.connect(self.toggle_labels_visibility)

        self.mode_combo = QComboBox()
        self.mode_combo.addItem(self.texts[self.current_language]["manual_mode"])
        self.mode_combo.addItem(self.texts[self.current_language]["bulk_mode"])
        self.mode_combo.currentIndexChanged.connect(self.toggle_mode)

        self.btn_input = QPushButton(self.texts[self.current_language]["select_input"])
        self.btn_input.clicked.connect(self.select_input_folder)
        
        self.btn_output = QPushButton(self.texts[self.current_language]["select_output"])
        self.btn_output.clicked.connect(self.select_output_folder)

        self.format_combo = QComboBox()
        self.format_combo.addItem(self.texts[self.current_language]["yolo"])
        self.format_combo.addItem(self.texts[self.current_language]["mot"])
        self.format_combo.addItem(self.texts[self.current_language]["all"])
        self.format_combo.setCurrentText(self.texts[self.current_language]["all"])
        self.format_combo.currentIndexChanged.connect(self.select_format)
        
        self.class_combo = QComboBox()
        self.class_combo.addItems(self.labeler.class_list)
        self.class_combo.currentIndexChanged.connect(self.select_class)
        self.image_combo = QComboBox()
        self.image_combo.currentIndexChanged.connect(self.select_image)
        self.btn_prev = QPushButton(self.texts[self.current_language]["prev_image"])
        self.btn_prev.clicked.connect(self.labeler.previous_image)
        self.btn_next = QPushButton(self.texts[self.current_language]["next_image"])
        self.btn_next.clicked.connect(self.labeler.next_image)
        
        # 語言切換按鈕
        self.language_btn = QPushButton(self.texts[self.current_language]["language"])
        self.language_btn.clicked.connect(self.toggle_language)

        top_bar.addWidget(self.show_labels_btn)
        top_bar.addWidget(self.mode_combo)
        top_bar.addWidget(self.btn_input)
        top_bar.addWidget(self.btn_output)
        top_bar.addWidget(self.format_combo)
        top_bar.addWidget(self.class_combo)
        top_bar.addWidget(self.image_combo)
        top_bar.addWidget(self.btn_prev)
        top_bar.addWidget(self.btn_next)
        top_bar.addWidget(self.language_btn)
        layout.addLayout(top_bar)
        
        self.image_widget = ImageWidget(self.labeler)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setAlignment(Qt.AlignCenter)
        self.scroll_area.setWidget(self.image_widget)
        layout.addWidget(self.scroll_area)
    
    def _connect_signals(self):
        self.labeler.image_changed.connect(self.update_ui)
        self.image_widget.box_requested.connect(self.labeler.on_click)
        self.image_widget.confirm_box.connect(self.labeler.confirm_box)
        self.labeler.colors_updated.connect(self.selected_colors_widget.update_colors)
        
        self.selected_colors_widget.color_deleted.connect(self.labeler.delete_bulk_color)
        
        self.selected_colors_widget.preview_all_requested.connect(self.labeler.set_preview_mode)
        self.selected_colors_widget.reset_all_requested.connect(self.labeler.reset_bulk_labeling)
        self.selected_colors_widget.apply_all_requested.connect(self.labeler.apply_bulk_labeling)

    def _setup_shortcuts(self):
        QShortcut(QKeySequence(Qt.Key_Escape), self).activated.connect(self.labeler.cancel_box)
        QShortcut(QKeySequence(Qt.Key_A), self).activated.connect(self.labeler.previous_image)
        QShortcut(QKeySequence(Qt.Key_D), self).activated.connect(self.labeler.next_image)
    
    def toggle_language(self):
        """切換語言"""
        if self.current_language == "zh":
            self.current_language = "en"
        else:
            self.current_language = "zh"
        
        # 更新視窗標題
        self.setWindowTitle(self.texts[self.current_language]["title"])
        
        # 更新按鈕文字
        self.show_labels_btn.setText(self.texts[self.current_language]["show_labels"])
        self.btn_input.setText(self.texts[self.current_language]["select_input"])
        self.btn_output.setText(self.texts[self.current_language]["select_output"])
        self.btn_prev.setText(self.texts[self.current_language]["prev_image"])
        self.btn_next.setText(self.texts[self.current_language]["next_image"])
        self.language_btn.setText(self.texts[self.current_language]["language"])
        
        # 保存當前模式選擇
        current_mode_index = self.mode_combo.currentIndex()
        current_format_index = self.format_combo.currentIndex()
        
        # 更新下拉選單
        self.mode_combo.clear()
        self.mode_combo.addItem(self.texts[self.current_language]["manual_mode"])
        self.mode_combo.addItem(self.texts[self.current_language]["bulk_mode"])
        self.mode_combo.setCurrentIndex(current_mode_index)  # 保持當前選擇
        
        self.format_combo.clear()
        self.format_combo.addItem(self.texts[self.current_language]["yolo"])
        self.format_combo.addItem(self.texts[self.current_language]["mot"])
        self.format_combo.addItem(self.texts[self.current_language]["all"])
        self.format_combo.setCurrentIndex(current_format_index)  # 保持當前選擇
        
        # 更新批量標註工具列語言
        self.selected_colors_widget.set_language(self.current_language)

    def toggle_mode(self, index):
        if index == 1:
            self.labeler.labeling_mode = LabelingMode.BULK
            self.selected_colors_widget.show()
            # 已切換為批量標註模式
        else:
            self.labeler.labeling_mode = LabelingMode.MANUAL
            self.selected_colors_widget.hide()
            # 已切換為人工標註模式

        self.labeler.clear_single_boxes()

        if self.labeler.original_image_cv2 is not None:
            self.labeler.update_image_display()

    def select_format(self, index):
        selected_format = self.format_combo.itemText(index)
        self.labeler.labeling_format = selected_format
        # 已切換標註格式
    
    def toggle_labels_visibility(self):
        self.image_widget.set_show_labels(self.show_labels_btn.isChecked())

    def select_input_folder(self):
        folder = QFileDialog.getExistingDirectory(self, self.texts[self.current_language]["select_input_folder"])
        if folder:
            self.labeler.input_dir = folder
            self.labeler.load_images()
            self.update_image_combo()

    def select_output_folder(self):
        folder = QFileDialog.getExistingDirectory(self, self.texts[self.current_language]["select_output_folder"])
        if folder:
            self.labeler.yolo_output_dir = folder
            self.labeler.mot_output_dir = os.path.join(folder, "MOT_Label")

    def select_class(self, index):
        self.labeler.selected_class_id = index
        
    def select_image(self, index):
        if self.labeler.current_image_index == index:
            return
            
        self.labeler.save_labels()
        self.labeler.current_image_index = index
        self.labeler.load_image()

    def update_image_combo(self):
        self.image_combo.blockSignals(True)
        self.image_combo.clear()
        self.image_combo.addItems(self.labeler.images)
        if self.labeler.current_image_index < self.image_combo.count():
            self.image_combo.setCurrentIndex(self.labeler.current_image_index)
        self.image_combo.blockSignals(False)
        
    def update_ui(self, pixmap, boxes):
        self.image_widget.set_image(pixmap, boxes)
        self.update_image_combo()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec_())
