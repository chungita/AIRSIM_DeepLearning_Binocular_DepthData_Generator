import sys
import os
import glob
import re
import numpy as np
import imageio.v2 as iio
from PIL import Image, ImageDraw, ImageFont
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLineEdit, QLabel, QTextEdit, QMessageBox, QComboBox, QCheckBox, QFileDialog)
from PyQt5.QtCore import Qt
from collections import defaultdict
import cv2

def read_pfm(file_path):
    """
    讀取 PFM 檔案並返回 numpy 陣列
    """
    try:
        data = iio.imread(file_path)
        
        if data.ndim > 2:
            return data[:, :, 0]

        return data
    except Exception as e:
        return None

def natsort_key(s):
    """
    用於自然排序的排序鍵。
    """
    return [int(c) if c.isdigit() else c.lower() for c in re.split('(\d+)', s)]

def read_yolo_labels(label_path, classes, log_func=None):
    """
    讀取 YOLO 格式的標籤檔案並返回一個偵測框列表。
    """
    labels = []
    if not os.path.exists(label_path):
        return labels
    
    with open(label_path, 'r') as f:
        lines = f.readlines()
        if not lines:
            return []

        for line in lines:
            parts = line.strip().split()
            if len(parts) == 5:
                try:
                    class_id = int(parts[0])
                    x_center = float(parts[1])
                    y_center = float(parts[2])
                    bbox_width = float(parts[3])
                    bbox_height = float(parts[4])

                    if 0 <= class_id < len(classes):
                        labels.append({
                            'class_id': class_id,
                            'class_name': classes[class_id],
                            'x_center': x_center,
                            'y_center': y_center,
                            'bbox_width': bbox_width,
                            'bbox_height': bbox_height
                        })
                    else:
                        if log_func:
                            log_func(f"警告：標籤 \'{os.path.basename(label_path)}\' 中的類別 ID \'{class_id}\' 超出範圍。")
                except ValueError as e:
                    if log_func:
                        log_func(f"警告：標籤 \'{os.path.basename(label_path)}\' 中的數值格式不正確: {line.strip()} (錯誤: {e})")
            else:
                if log_func:
                    log_func(f"警告：YOLO 標籤行欄位不足 (期望 5 個，實際 {len(parts)}): {line.strip()}")
    return labels

def read_mot_labels(mot_file_path, classes, log_func=None):
    """
    從 MOT 格式檔案讀取標籤。
    格式：frame_id, track_id, xmin, ymin, w, h, conf, x_cam, y_cam, z (共 10 個欄位)
    """
    labels_by_frame = defaultdict(list)
    if not os.path.exists(mot_file_path):
        if log_func:
            log_func(f"警告：MOT 標籤檔案不存在: {mot_file_path}")
        return labels_by_frame
    
    with open(mot_file_path, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split(',')
            if len(parts) >= 10: 
                try:
                    frame_id = int(parts[0])
                    track_id = int(parts[1])
                    xmin = float(parts[2])
                    ymin = float(parts[3])
                    width = float(parts[4])
                    height = float(parts[5])
                    conf = float(parts[6]) # conf 是第 7 個欄位 (索引 6)
                    
                    x_cam = float(parts[7])
                    y_cam = float(parts[8])
                    z = float(parts[9])

                    # 由於檔案中不包含 class_id，這裡設定為通用或空字串
                    class_name = "" # 或者你可以設定一個預設的類別名稱，例如 "Object"
                    
                    labels_by_frame[frame_id].append({
                        'track_id': track_id,
                        'class_name': class_name, # class_name 現在是通用或空字串
                        'xmin': xmin,
                        'ymin': ymin,
                        'xmax': xmin + width,
                        'ymax': ymin + height,
                        'x_cam': x_cam,
                        'y_cam': y_cam,
                        'z': z
                    })
                except (ValueError, IndexError) as e:
                    if log_func:
                        log_func(f"警告：MOT 標籤檔案中有一行格式不正確，已跳過: {line.strip()} (錯誤: {e})")
            else:
                if log_func:
                    log_func(f"警告：MOT 標籤行欄位不足 (期望至少 10 個，實際 {len(parts)}): {line.strip()}")
    return labels_by_frame

def draw_yolo_labels(image, labels, img_w, img_h): # 添加 img_w, img_h 參數
    """
    在 PIL 圖片上繪製 YOLO 偵測框和類別名稱。
    labels: [ {class_id, class_name, x_center, y_center, bbox_width, bbox_height}, ... ]
    """
    draw = ImageDraw.Draw(image)
    
    try:
        font = ImageFont.truetype("arial.ttf", 15)
    except IOError:
        font = ImageFont.load_default()

    for label in labels:
        class_name = label['class_name']
        x_center = label['x_center']
        y_center = label['y_center']
        bbox_width = label['bbox_width']
        bbox_height = label['bbox_height']

        x1 = int((x_center - bbox_width / 2) * img_w)
        y1 = int((y_center - bbox_height / 2) * img_h)
        x2 = int((x_center + bbox_width / 2) * img_w)
        y2 = int((y_center + bbox_height / 2) * img_h)
        
        draw.rectangle([x1, y1, x2, y2], outline="red", width=2)
        
        text = f"{class_name}"
        text_bbox = draw.textbbox((x1, y1), text, font=font)
        text_w = text_bbox[2] - text_bbox[0]
        text_h = text_bbox[3] - text_bbox[1]
        
        draw.rectangle([x1, y1 - text_h - 2, x1 + text_w, y1], fill="red")
        draw.text((x1, y1 - text_h - 2), text, font=font, fill="white")
    
    return image

def draw_mot_labels(image, labels, img_w, img_h): # 添加 img_w, img_h 參數
    """
    在 PIL 圖片上繪製 MOT 偵測框和詳細資訊。
    labels: [ {track_id, class_name, xmin, ymin, xmax, ymax, x_cam, y_cam, z}, ... ]
    """
    draw = ImageDraw.Draw(image)
    
    try:
        font = ImageFont.truetype("arial.ttf", 12)
    except IOError:
        font = ImageFont.load_default()

    for label in labels:
        track_id = label['track_id']
        # class_name = label['class_name'] # 這個變數在這裡可能不再需要，因為輸出格式中沒有 class_name
        xmin = int(label['xmin'])
        ymin = int(label['ymin'])
        xmax = int(label['xmax'])
        ymax = int(label['ymax'])
        x_cam = label['x_cam']
        y_cam = label['y_cam']
        z = label['z']
        
        draw.rectangle([xmin, ymin, xmax, ymax], outline="blue", width=2)
        
        text = f"ID:{track_id} X:{x_cam:.2f} Y:{y_cam:.2f} Z:{z:.2f}m"
        text_bbox = draw.textbbox((xmin, ymin), text, font=font)
        text_w = text_bbox[2] - text_bbox[0]
        text_h = text_bbox[3] - text_bbox[1]
        
        draw.rectangle([xmin, ymin - text_h - 2, xmin + text_w, ymin], fill="blue")
        draw.text((xmin, ymin - text_h - 2), text, font=font, fill="white")
    
    return image

def create_gif(image_paths, output_path, fps, log_func, add_yolo=False, yolo_label_folder=None, add_mot=False, mot_label_file=None, img_type=None, classes=None):
    """
    讀取一系列圖片，選擇性地加上標籤，然後將它們保存為一個 GIF。
    """
    images = []
    
    mot_labels_by_frame = {}
    if add_mot and mot_label_file:
        mot_labels_by_frame = read_mot_labels(mot_label_file, classes, log_func)

    for i, path in enumerate(image_paths):
        if path.endswith('.pfm'):
            pfm_data = read_pfm(path)
            if pfm_data is not None and isinstance(pfm_data, np.ndarray):
                try:
                    filename = os.path.basename(path)
                    
                    pfm_data = np.flipud(pfm_data)
                    
                    if filename.startswith('DepthGT'):
                        img_np_norm = cv2.normalize(pfm_data, None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8U)
                        img_np_color = cv2.applyColorMap(img_np_norm, cv2.COLORMAP_JET)
                    elif filename.startswith('Disparity'):
                        img_np_norm = cv2.normalize(pfm_data, None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8U)
                        img_np_color = cv2.applyColorMap(img_np_norm, cv2.COLORMAP_JET)
                    else:
                        img_np_norm = cv2.normalize(pfm_data, None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8U)
                        img_np_color = cv2.applyColorMap(img_np_norm, cv2.COLORMAP_JET)
                    
                    img = Image.fromarray(cv2.cvtColor(img_np_color, cv2.COLOR_BGR2RGB))
                except cv2.error as e:
                    log_func(f"normalize 失敗 {path}: {e}")
                    continue
            else:
                log_func(f"警告：無法讀取 PFM 檔案 \'{os.path.basename(path)}\'，已跳過。")
                continue
        else:
            img = Image.open(path).convert('RGB')
        
        if img is None:
            log_func(f"警告：無法讀取檔案 \'{os.path.basename(path)}\'，已跳過。")
            continue
        
        img_w, img_h = img.size
        
        base = os.path.splitext(os.path.basename(path))[0]
        m = re.search(r'(\d+)$', base)
        frame_number = int(m.group(1)) if m else (i + 1) # 確保 frame_number 從 1 開始
        
        has_yolo_labels = False
        if add_yolo and frame_number is not None:
            label_base = f"Img1_{frame_number}" if img_type == 'Img1' else f"Img0_{frame_number}"
            yolo_label_path = os.path.join(yolo_label_folder, label_base + '.txt')
            
            yolo_labels_for_frame = read_yolo_labels(yolo_label_path, classes, log_func)
            
            if yolo_labels_for_frame:
                img = draw_yolo_labels(img, yolo_labels_for_frame, img_w, img_h)
                has_yolo_labels = True
        
        has_mot_labels = False
        if add_mot:
            if frame_number in mot_labels_by_frame and mot_labels_by_frame[frame_number]:
                img = draw_mot_labels(img, mot_labels_by_frame[frame_number], img_w, img_h)
                has_mot_labels = True

        images.append(img)
        
    if not images:
        log_func("沒有可以處理的有效圖片，無法生成 GIF。")
        return

    images[0].save(output_path, save_all=True, append_images=images[1:], optimize=True, duration=int(1000/fps), loop=0)

class GIFMakerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GIF 製作工具 (PyQt5)")
        self.setGeometry(100, 100, 700, 400)
        
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 載入設定
        self.load_settings()
        
        # 使用項目根目錄作為基礎路徑
        project_root = os.path.dirname(self.current_dir)  # 上一級目錄（項目根目錄）
        self.output_folder = os.path.join(project_root, "Results")
        # 這些路徑現在從 load_settings() 方法中設置
        self.yolo_label_folder = self.gif_yolo_folder
        self.mot_label_folder = self.gif_mot_folder
        self.classes_file = os.path.join(self.current_dir, "predefined_classes.txt")
        self.classes = []
        
        self.initUI_before_log() 
        
        self.load_classes()
        
        self.initUI_after_log()
        self.check_folders()

    def load_settings(self):
        """
        從 Settings.txt 載入設定
        """
        settings_file = os.path.join(self.current_dir, "Settings.txt")
        
        # 設置預設值 - 使用項目根目錄作為基礎路徑
        project_root = os.path.dirname(self.current_dir)  # 上一級目錄（項目根目錄）
        self.input_folder = os.path.join(project_root, "ProcessData")
        self.gif_mot_folder = os.path.join(project_root, "Results", "MOT_Label")
        self.gif_yolo_folder = os.path.join(project_root, "Results", "YOLO_Label")
        self.frame_length = 900  # 預設最大幀數
        self.default_fps = 30  # 預設FPS
        
        if os.path.exists(settings_file):
            with open(settings_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and ':' in line:
                        # 處理註解 - 分割 # 之前的部分
                        if '#' in line:
                            line = line.split('#')[0].strip()
                        
                        if ':' not in line:
                            continue
                            
                        key, value = line.split(':', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        if key == "GIF_Input_folder":
                            self.input_folder = os.path.join(project_root, value)
                        elif key == "GIF_MOT_folder":
                            self.gif_mot_folder = os.path.join(project_root, value)
                        elif key == "GIF_YOLO_folder":
                            self.gif_yolo_folder = os.path.join(project_root, value)
                        elif key == "Frame_Length":
                            try:
                                self.frame_length = int(value)
                            except ValueError:
                                self.frame_length = 900  # 如果轉換失敗，使用預設值
                        elif key == "default_FPS":
                            try:
                                self.default_fps = int(value)
                            except ValueError:
                                self.default_fps = 30  # 如果轉換失敗，使用預設值

    def initUI_before_log(self):
        """
        初始化那些在 log 函數被調用前必須存在的 UI 元素。
        """
        main_layout = QVBoxLayout()
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        main_layout.addWidget(self.output_text)
        self.setLayout(main_layout) # 這裡先設置佈局，以便 log 函數可以工作

    def initUI_after_log(self):
        """
        初始化在 log 函數被調用後才需要存在的 UI 元素，並連接信號。
        """
        main_layout = self.layout() 
        main_control_layout = QHBoxLayout()

        main_control_layout.addWidget(QLabel("讀取資料夾:"))
        self.input_folder_label = QLabel()
        self.input_folder_label.setStyleSheet("color: blue; font-weight: bold;")
        self.input_folder_label.setText(os.path.basename(self.input_folder))
        self.input_folder_label.setToolTip(f"完整路徑: {self.input_folder}\n點擊按鈕更改資料夾")
        main_control_layout.addWidget(self.input_folder_label)
        
        self.change_folder_btn = QPushButton("📁")
        self.change_folder_btn.setFixedSize(30, 25)
        self.change_folder_btn.setToolTip("選擇不同的輸入資料夾")
        self.change_folder_btn.clicked.connect(self.change_input_folder)
        main_control_layout.addWidget(self.change_folder_btn)
        
        self.refresh_btn = QPushButton("🔄")
        self.refresh_btn.setFixedSize(30, 25)
        self.refresh_btn.setToolTip("刷新輸入設定和幀範圍")
        self.refresh_btn.clicked.connect(self.refresh_input)
        main_control_layout.addWidget(self.refresh_btn)

        main_control_layout.addStretch(1)
        main_control_layout.addWidget(QLabel("FPS:"))
        self.fps_entry = QLineEdit(str(self.default_fps))
        self.fps_entry.setFixedWidth(40)
        main_control_layout.addWidget(self.fps_entry)

        main_control_layout.addStretch(1)
        main_control_layout.addWidget(QLabel("選擇圖片種類:"))
        self.type_combo = QComboBox()
        self.image_types = ['All', 'Disparity', 'Depth', 'Img0', 'Img1', 'Seg']
        self.type_combo.addItems(self.image_types)
        main_control_layout.addWidget(self.type_combo)

        main_control_layout.addStretch(1)
        self.output_name_label = QLabel("輸出檔名:")
        self.output_name_entry = QLineEdit()
        main_control_layout.addWidget(self.output_name_label)
        main_control_layout.addWidget(self.output_name_entry)

        main_control_layout.addStretch(1)
        self.yolo_checkbox = QCheckBox("新增 YOLO 標籤")
        self.mot_checkbox = QCheckBox("新增 MOT 標籤")
        main_control_layout.addWidget(self.yolo_checkbox)
        main_control_layout.addWidget(self.mot_checkbox)

        main_control_layout.addWidget(QLabel("起始幀:"))
        self.start_entry = QLineEdit("")
        self.start_entry.setFixedWidth(60)
        main_control_layout.addWidget(self.start_entry)

        main_control_layout.addWidget(QLabel("結束幀:"))
        self.end_entry = QLineEdit("")
        self.end_entry.setFixedWidth(60)
        main_control_layout.addWidget(self.end_entry)

        main_control_layout.addWidget(QLabel("最大幀數:"))
        self.frame_length_label = QLabel(str(self.frame_length))
        self.frame_length_label.setStyleSheet("color: green; font-weight: bold;")
        self.frame_length_label.setToolTip(f"從 Settings.txt 讀取的 Frame_Length 設定\n當前值: {self.frame_length}")
        main_control_layout.addWidget(self.frame_length_label)

        main_control_layout.addStretch(1)
        self.process_btn = QPushButton("確認輸出")
        main_control_layout.addWidget(self.process_btn)

        main_layout.insertLayout(0, main_control_layout)

        self.type_combo.currentIndexChanged.connect(self.update_filename_input)
        self.process_btn.clicked.connect(self.start_processing)
        self.yolo_checkbox.stateChanged.connect(self.on_yolo_checked)
        self.mot_checkbox.stateChanged.connect(self.on_mot_checked)
        
        self.update_filename_input(0)
        
    def initUI(self): # 將原來的 initUI 重新命名為 initUI_after_log 或直接刪除，因為現在拆分了
        pass

    def load_classes(self):
        """
        載入 predefined_classes.txt 中的類別名稱。
        """
        if os.path.exists(self.classes_file):
            try:
                with open(self.classes_file, 'r', encoding='utf-8') as f:
                    self.classes = [line.strip() for line in f if line.strip()]
                self.log(f"已載入 {len(self.classes)} 個類別：{self.classes}")
            except Exception as e:
                self.log(f"錯誤：載入類別檔案 {self.classes_file} 失敗: {e}")
                self.classes = []
        else:
            self.log(f"警告：找不到類別檔案: {self.classes_file}。標籤將無法顯示正確的類別名稱。")
            self.classes = []

    def log(self, msg):
        pass
    def on_yolo_checked(self, state):
        pass

    def on_mot_checked(self, state):
        pass

    def update_filename_input(self, index):
        selected_type = self.image_types[index]
        if selected_type == 'All':
            self.output_name_entry.setDisabled(True)
            self.output_name_entry.setText("")
        else:
            self.output_name_entry.setDisabled(False)
            self.output_name_entry.setText(selected_type)
        self.set_default_range_for_type(selected_type)

    def log(self, message):
        self.output_text.append(message)
        QApplication.processEvents()

    def change_input_folder(self):
        """
        讓用戶選擇新的輸入資料夾
        """
        folder = QFileDialog.getExistingDirectory(
            self, 
            "選擇輸入資料夾", 
            self.input_folder,
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        
        if folder:
            self.input_folder = folder
            self.input_folder_label.setText(os.path.basename(self.input_folder))
            self.input_folder_label.setToolTip(f"完整路徑: {self.input_folder}\n點擊按鈕更改資料夾")
            self.log(f"已更改輸入資料夾為: {self.input_folder}")
            
            # 重新設定預設範圍
            current_type = self.type_combo.currentText()
            self.set_default_range_for_type(current_type)

    def refresh_input(self):
        """
        刷新輸入設定：重新載入 Settings.txt 並更新界面
        """
        self.log("正在刷新輸入設定...")
        
        # 重新載入設定
        self.load_settings()
        
        # 更新路徑變數
        self.yolo_label_folder = self.gif_yolo_folder
        self.mot_label_folder = self.gif_mot_folder
        
        # 更新界面顯示
        self.input_folder_label.setText(os.path.basename(self.input_folder))
        self.input_folder_label.setToolTip(f"完整路徑: {self.input_folder}\n點擊按鈕更改資料夾")
        
        # 更新 Frame_Length 標籤
        self.frame_length_label.setText(str(self.frame_length))
        self.frame_length_label.setToolTip(f"從 Settings.txt 讀取的 Frame_Length 設定\n當前值: {self.frame_length}")
        
        # 更新 FPS 輸入框
        self.fps_entry.setText(str(self.default_fps))
        
        # 重新載入類別
        self.load_classes()
        
        # 重新檢查資料夾
        self.check_folders()
        
        # 重新設定預設範圍
        current_type = self.type_combo.currentText()
        self.set_default_range_for_type(current_type)
        
        self.log(f"刷新完成！輸入資料夾: {self.input_folder}, Frame_Length: {self.frame_length}, default_FPS: {self.default_fps}")

    def check_folders(self):
        """
        檢查必要的資料夾是否存在。
        """
        if not os.path.exists(self.input_folder):
            self.log(f"警告：輸入資料夾不存在: {self.input_folder}")
        if not os.path.exists(self.output_folder):
            self.log(f"警告：輸出資料夾不存在: {self.output_folder}")
        
        if not os.path.exists(self.yolo_label_folder):
            self.log(f"警告：YOLO 標籤資料夾不存在: {self.yolo_label_folder}")
        else:
            yolo_files = [f for f in os.listdir(self.yolo_label_folder) if f.endswith('.txt')]
            if yolo_files:
                self.log(f"已從 '{self.yolo_label_folder}' 讀取到 {len(yolo_files)} 個 YOLO 標籤檔案。")
            else:
                self.log(f"'{self.yolo_label_folder}' 中未找到 YOLO 標籤檔案。")

        if not os.path.exists(self.mot_label_folder):
            self.log(f"警告：MOT 標籤資料夾不存在: {self.mot_label_folder}")
        else:
            mot_files = [f for f in os.listdir(self.mot_label_folder) if f.endswith('.txt')]
            if mot_files:
                self.log(f"已從 '{self.mot_label_folder}' 讀取到 {len(mot_files)} 個 MOT 標籤檔案。")
            else:
                self.log(f"'{self.mot_label_folder}' 中未找到 MOT 標籤檔案。")

        if os.path.exists(self.classes_file):
            try:
                with open(self.classes_file, 'r', encoding='utf-8') as f:
                    self.classes = [line.strip() for line in f.readlines()]
                self.log(f"已從 '{self.classes_file}' 讀取 {len(self.classes)} 個類別。")
            except Exception as e:
                self.log(f"錯誤：無法讀取類別檔案 '{self.classes_file}'。錯誤訊息：{e}")
                # self.add_yolo_btn.setEnabled(not is_all_selected)
        else:
            self.log(f"警告：找不到類別檔案 '{self.classes_file}'。YOLO 和 MOT 標籤功能已停用。")
            # self.add_yolo_btn.setEnabled(not is_all_selected)

    def get_fps(self):
        try:
            fps = int(self.fps_entry.text())
            if fps <= 0:
                QMessageBox.critical(self, "無效輸入", "幀率必須大於 0。")
                return None
            return fps
        except ValueError:
            QMessageBox.critical(self, "無效輸入", "請輸入一個有效的整數作為幀率。")
            return None

    def get_frame_range(self):
        """
        讀取並驗證起始/結束幀。空字串代表不限制。
        回傳: (start:int|None, end:int|None) 或 None 代表驗證失敗。
        """
        s_txt = self.start_entry.text().strip()
        e_txt = self.end_entry.text().strip()
        start = None if s_txt == "" else s_txt
        end = None if e_txt == "" else e_txt
        try:
            if start is not None:
                start = int(start)
                if start < 0:
                    raise ValueError
            if end is not None:
                end = int(end)
                if end < 0:
                    raise ValueError
            if start is not None and end is not None and start > end:
                QMessageBox.critical(self, "無效輸入", "起始幀不能大於結束幀。")
                return None
            return (start, end)
        except ValueError:
            QMessageBox.critical(self, "無效輸入", "起始/結束幀需為非負整數。")
            return None

    def get_image_paths(self, selected_type, start_frame, end_frame):
        """
        根據選擇的類型和幀範圍取得圖片路徑
        """
        if selected_type == 'Depth':
            search_pattern = 'DepthGT*.pfm'
        elif selected_type == 'Disparity':
            search_pattern = 'Disparity*.pfm'
        else:
            search_pattern = f'{selected_type}*.png'
        
        image_paths = glob.glob(os.path.join(self.input_folder, search_pattern))
        
        if not image_paths:
            return []
        
        image_paths.sort(key=natsort_key)
        
        if start_frame is not None or end_frame is not None:
            filtered_paths = []
            for path in image_paths:
                frame_num = self.extract_frame_number(path)
                if frame_num is not None:
                    if start_frame is not None and frame_num < start_frame:
                        continue
                    if end_frame is not None and frame_num > end_frame:
                        continue
                    filtered_paths.append(path)
            image_paths = filtered_paths
        
        # 應用 Frame_Length 限制
        if hasattr(self, 'frame_length') and self.frame_length > 0:
            if len(image_paths) > self.frame_length:
                self.log(f"警告：找到 {len(image_paths)} 幀，但 Frame_Length 設定為 {self.frame_length}，將限制為前 {self.frame_length} 幀。")
                image_paths = image_paths[:self.frame_length]
        
        return image_paths

    def extract_frame_number(self, path):
        """
        從檔案路徑中提取幀號
        """
        base = os.path.splitext(os.path.basename(path))[0]
        m = re.search(r'(\d+)$', base)
        return int(m.group(1)) if m else None

    def set_default_range_for_type(self, img_type):
        if img_type == 'All':
            return self.set_default_range_for_all()
        if img_type == 'Depth':
            pattern = 'DepthGT*.pfm'
        elif img_type == 'Disparity':
            pattern = 'Disparity*.pfm'
        else:
            pattern = f'{img_type}*.png'
        paths = glob.glob(os.path.join(self.input_folder, pattern))
        if not paths:
            self.start_entry.setText("")
            self.end_entry.setText("")
            return
        paths.sort(key=natsort_key)
        nums = [self.extract_frame_number(p) for p in paths]
        nums = [n for n in nums if n is not None]
        if not nums:
            self.start_entry.setText("")
            self.end_entry.setText("")
            return
        
        start_frame = min(nums)
        # 結束幀設置為起始幀 + Frame_Length - 1，但不超過實際最大幀數
        max_available_frame = max(nums)
        end_frame = min(start_frame + self.frame_length - 1, max_available_frame)
        
        self.start_entry.setText(str(start_frame))
        self.end_entry.setText(str(end_frame))

    def set_default_range_for_all(self):
        types = ['Disparity', 'Depth', 'Img0', 'Img1', 'Seg']
        nums = []
        for t in types:
            if t == 'Depth':
                pattern = 'DepthGT*.pfm'
            elif t == 'Disparity':
                pattern = 'Disparity*.pfm'
            else:
                pattern = f'{t}*.png'
            paths = glob.glob(os.path.join(self.input_folder, pattern))
            paths.sort(key=natsort_key)
            nums.extend([self.extract_frame_number(p) for p in paths])
        nums = [n for n in nums if n is not None]
        if not nums:
            self.start_entry.setText("")
            self.end_entry.setText("")
            return
            
        start_frame = min(nums)
        # 結束幀設置為起始幀 + Frame_Length - 1，但不超過實際最大幀數
        max_available_frame = max(nums)
        end_frame = min(start_frame + self.frame_length - 1, max_available_frame)
        
        self.start_entry.setText(str(start_frame))
        self.end_entry.setText(str(end_frame))

    def get_mot_file_path(self, img_type):
        """
        根據圖片類型取得對應的 MOT 檔案路徑
        """
        if img_type == 'Img1':
            mot_filename = 'Img1.txt'
        else:
            mot_filename = 'Img0.txt'
        return os.path.join(self.mot_label_folder, mot_filename)

    def start_processing(self):
        """
        開始處理 GIF 製作
        """
        add_yolo = self.yolo_checkbox.isChecked()
        add_mot = self.mot_checkbox.isChecked()
        
        if add_yolo and add_mot:
            self.log("同時產生 YOLO 和 MOT 標註的 GIF 檔案...")
            
            self.log("正在產生 YOLO 標註版本...")
            self.create_single_gif(add_yolo=True, add_mot=False)
            
            self.log("正在產生 MOT 標註版本...")
            self.create_single_gif(add_yolo=False, add_mot=True)
            
            self.log("兩個 GIF 檔案都已產生完成！")
        else:
            self.create_single_gif(add_yolo=add_yolo, add_mot=add_mot)

    def create_single_gif(self, add_yolo=False, add_mot=False):
        """
        創建單一 GIF
        """
        selected_type = self.type_combo.currentText()
        
        fps = self.get_fps()
        if fps is None:
            return
        
        frame_range = self.get_frame_range()
        if frame_range is None:
            return
        
        start_frame, end_frame = frame_range
        
        if selected_type == "All":
            image_types = ["Depth", "Disparity", "Img0", "Img1", "Seg"]
            for img_type in image_types:
                self.log(f"正在處理 {img_type} 類型...")
                self.create_gif_for_single_type(img_type, start_frame, end_frame, fps, add_yolo, add_mot)
            return
        
        self.create_gif_for_single_type(selected_type, start_frame, end_frame, fps, add_yolo, add_mot)

    def create_gif_for_single_type(self, img_type, start_frame, end_frame, fps, add_yolo, add_mot):
        """
        為單一圖片類型創建 GIF
        """
        image_paths = self.get_image_paths(img_type, start_frame, end_frame)
        if not image_paths:
            self.log(f"錯誤：找不到 '{img_type}' 類型的圖片檔案。")
            return
        
        output_name = self.output_name_entry.text().strip()
        if not output_name:
            output_name = img_type
        
        suffix = ""
        if add_yolo and add_mot:
            suffix = "_YOLO_MOT"
        elif add_yolo:
            suffix = "_YOLO"
        elif add_mot:
            suffix = "_MOT"
        
        initial_gif_name = f"{output_name}{suffix}.gif"
        output_gif_name = initial_gif_name
        count = 1
        while os.path.exists(os.path.join(self.output_folder, output_gif_name)):
            name_without_ext, ext = os.path.splitext(initial_gif_name)
            output_gif_name = f"{name_without_ext}_{count}{ext}"
            count += 1
        
        output_gif_path = os.path.join(self.output_folder, output_gif_name)
        
        create_gif(image_paths, output_gif_path, fps=fps, log_func=self.log,
                   add_yolo=add_yolo, yolo_label_folder=self.yolo_label_folder,
                   add_mot=add_mot, mot_label_file=self.get_mot_file_path(img_type),
                   img_type=img_type, classes=self.classes)
        
        self.log(f"{img_type} GIF 已儲存至：{output_gif_path}")

    def on_single_gif(self):
        """
        保留原有方法名稱以維持相容性，但實際呼叫 create_single_gif
        """
        add_yolo = self.yolo_checkbox.isChecked()
        add_mot = self.mot_checkbox.isChecked()
        self.create_single_gif(add_yolo=add_yolo, add_mot=add_mot)

    def on_multiple_gif(self, fps):
        """
        處理多個 GIF 的生成（保留方法以維持相容性）
        """
        self.log("\n--- 正在執行多個 GIF 模式 ---")
        pass

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = GIFMakerApp()
    ex.show()
    sys.exit(app.exec_())