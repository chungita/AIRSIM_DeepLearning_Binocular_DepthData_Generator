import os
import cv2
import glob
import numpy as np
import re
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QMessageBox, 
                             QFileDialog, QComboBox, QSpinBox, QTextEdit, 
                             QProgressBar, QGroupBox, QGridLayout, QCheckBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont
import sys

def load_settings():
    """
    載入 Settings.txt 設定檔案
    """
    settings_file = os.path.join(os.path.dirname(__file__), "Settings.txt")
    settings = {}
    
    if os.path.exists(settings_file):
        try:
            with open(settings_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and ':' in line:
                        key, value = line.split(':', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        if '#' in value:
                            value = value.split('#')[0].strip()
                        
                        if value.lower() == 'true':
                            value = True
                        elif value.lower() == 'false':
                            value = False
                        elif value.replace('.', '').replace('-', '').isdigit():
                            if '.' in value:
                                value = float(value)
                            else:
                                value = int(value)
                        
                        settings[key] = value
        except Exception as e:
            print(f"載入設定檔案失敗：{e}")
    
    return settings

def natural_sort_key(filename):
    """
    自然排序鍵函數，正確處理數字排序
    例如：Img0_1.png, Img0_2.png, ..., Img0_10.png, Img0_11.png
    """
    # 提取檔案名中的數字部分
    numbers = re.findall(r'\d+', filename)
    if numbers:
        # 將數字轉換為整數進行排序
        return [int(num) for num in numbers]
    else:
        # 如果沒有數字，使用字串排序
        return [filename]

def read_yolo_labels(label_path, img_w, img_h):
    """
    讀取YOLO標註檔案
    返回標註列表
    """
    labels = []
    if not os.path.exists(label_path):
        return labels
    
    try:
        with open(label_path, 'r') as f:
            lines = f.readlines()
        
        for line in lines:
            parts = line.strip().split()
            if len(parts) >= 5:
                class_id = int(parts[0])
                x_center = float(parts[1])
                y_center = float(parts[2])
                bbox_width = float(parts[3])
                bbox_height = float(parts[4])
                
                # 轉換為像素座標
                x_min = int((x_center - bbox_width / 2) * img_w)
                y_min = int((y_center - bbox_height / 2) * img_h)
                x_max = int((x_center + bbox_width / 2) * img_w)
                y_max = int((y_center + bbox_height / 2) * img_h)
                
                labels.append({
                    'class_id': class_id,
                    'x_min': x_min,
                    'y_min': y_min,
                    'x_max': x_max,
                    'y_max': y_max
                })
    except Exception as e:
        print(f"讀取YOLO標註檔案失敗：{e}")
    
    return labels

def read_mot_labels(mot_file_path, frame_num):
    """
    讀取MOT標註檔案中指定影格的標註
    返回標註列表
    """
    labels = []
    if not os.path.exists(mot_file_path):
        return labels
    
    try:
        with open(mot_file_path, 'r') as f:
            lines = f.readlines()
        
        for line in lines:
            parts = line.strip().split(',')
            if len(parts) >= 10:
                line_frame_id = int(parts[0])
                if line_frame_id == frame_num:
                    track_id = int(parts[1])
                    x = float(parts[2])
                    y = float(parts[3])
                    width = float(parts[4])
                    height = float(parts[5])
                    conf = float(parts[6])
                    x_cam = float(parts[7])
                    y_cam = float(parts[8])
                    z = float(parts[9])
                    
                    labels.append({
                        'track_id': track_id,
                        'x_min': int(x),
                        'y_min': int(y),
                        'x_max': int(x + width),
                        'y_max': int(y + height),
                        'x_cam': x_cam,
                        'y_cam': y_cam,
                        'z': z
                    })
    except Exception as e:
        print(f"讀取MOT標註檔案失敗：{e}")
    
    return labels

def get_color_for_id(track_id, color_mode="預設"):
    """
    根據ID和顏色模式獲取顏色
    """
    # 預定義顏色列表 (BGR格式)
    color_palette = [
        (0, 0, 255),    # 紅色
        (0, 255, 0),    # 綠色
        (255, 0, 0),    # 藍色
        (0, 255, 255),  # 黃色
        (255, 0, 255),  # 洋紅
        (255, 255, 0),  # 青色
        (0, 128, 255),  # 橙色
        (128, 0, 255),  # 紫色
        (0, 255, 128),  # 青綠
        (255, 0, 128),  # 粉紅
        (128, 255, 0),  # 黃綠
        (0, 128, 128),  # 深青
        (128, 128, 0),  # 橄欖
        (128, 0, 128),  # 深紫
        (192, 192, 192), # 銀色
        (128, 128, 128)  # 灰色
    ]
    
    if color_mode == "預設":
        # 使用預設顏色分配
        return color_palette[track_id % len(color_palette)]
    elif color_mode == "紅色":
        return (0, 0, 255)
    elif color_mode == "綠色":
        return (0, 255, 0)
    elif color_mode == "藍色":
        return (255, 0, 0)
    elif color_mode == "黃色":
        return (0, 255, 255)
    elif color_mode == "洋紅":
        return (255, 0, 255)
    elif color_mode == "青色":
        return (255, 255, 0)
    else:
        return color_palette[track_id % len(color_palette)]

def draw_annotations_on_frame(frame, yolo_labels=None, mot_labels=None, annotation_position="左上角", 
                            simple_mode=False, color_mode="預設"):
    """
    在影格上繪製標註
    """
    if yolo_labels is None:
        yolo_labels = []
    if mot_labels is None:
        mot_labels = []
    
    # 預定義類別名稱
    class_names = ["drone", "person", "car", "truck", "bus", "motorcycle", "bicycle"]
    
    # 繪製YOLO標註
    for label in yolo_labels:
        x_min, y_min = label['x_min'], label['y_min']
        x_max, y_max = label['x_max'], label['y_max']
        class_id = label['class_id']
        
        # 選擇顏色
        color = get_color_for_id(class_id, color_mode)
        
        # 繪製邊界框
        cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), color, 2)
        
        if not simple_mode:
            # 簡易模式只繪製框，不繪製標籤
            class_name = class_names[class_id] if class_id < len(class_names) else f"Class {class_id}"
            label_text = f"YOLO: {class_name}"
            cv2.putText(frame, label_text, (x_min, y_min - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
    
    # 繪製MOT標註
    for label in mot_labels:
        x_min, y_min = label['x_min'], label['y_min']
        x_max, y_max = label['x_max'], label['y_max']
        track_id = label['track_id']
        x_cam = label['x_cam']
        y_cam = label['y_cam']
        z = label['z']
        
        # 選擇顏色
        color = get_color_for_id(track_id, color_mode)
        
        # 繪製邊界框
        cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), color, 2)
        
        if not simple_mode:
            # 簡易模式只繪製框，不繪製標籤
            label_text = f"MOT ID:{track_id} X:{x_cam:.1f} Y:{y_cam:.1f} Z:{z:.1f}m"
            cv2.putText(frame, label_text, (x_min, y_min - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
    
    return frame

class VideoConvertorThread(QThread):
    """影片轉換執行緒"""
    progress_updated = pyqtSignal(int, int)  # current, total
    status_updated = pyqtSignal(str)
    log_updated = pyqtSignal(str)
    finished = pyqtSignal(bool, str)  # success, message
    
    def __init__(self, input_folder, output_path, fps, codec, quality, image_pattern, 
                 start_frame=None, end_frame=None, add_yolo=False, add_mot=False, 
                 yolo_folder=None, mot_folder=None, annotation_position="左上角", 
                 simple_mode=False, color_mode="預設", language="zh"):
        super().__init__()
        self.input_folder = input_folder
        self.output_path = output_path
        self.fps = fps
        self.codec = codec
        self.quality = quality
        self.image_pattern = image_pattern
        self.start_frame = start_frame
        self.end_frame = end_frame
        self.add_yolo = add_yolo
        self.add_mot = add_mot
        self.yolo_folder = yolo_folder
        self.mot_folder = mot_folder
        self.annotation_position = annotation_position
        self.simple_mode = simple_mode
        self.color_mode = color_mode
        self.language = language
        self.is_cancelled = False
        
        # 多語言文字
        self.texts = {
            "zh": {
                "start_conversion": "🔄 開始轉換影片...",
                "input_folder": "📁 輸入資料夾：",
                "output_file": "💾 輸出檔案：",
                "settings": "⚙️ 設定：FPS={fps}, 編碼器={codec}, 品質={quality}",
                "no_files_found": "在 {folder} 中找不到符合 {pattern} 的圖片檔案",
                "found_images": "📸 找到 {count} 張圖片",
                "image_size": "📐 圖片尺寸：{width}x{height}",
                "cannot_read_image": "無法讀取圖片：{file}",
                "cannot_create_video": "無法創建影片檔案，請檢查路徑和權限",
                "skip_image": "⚠️ 跳過無法讀取的圖片：{file}",
                "processing": "🔄 處理中... {current}/{total} ({progress}%)",
                "processed_images": "📸 已處理 {current}/{total} 張圖片",
                "conversion_complete": "✅ 影片轉換完成！",
                "output_file_log": "📁 輸出檔案：{file}",
                "total_processed": "📊 總共處理了 {count} 張圖片",
                "success_message": "成功轉換 {count} 張圖片為影片",
                "user_cancelled": "使用者取消轉換",
                "conversion_error": "轉換過程中發生錯誤：{error}"
            },
            "en": {
                "start_conversion": "🔄 Starting video conversion...",
                "input_folder": "📁 Input folder:",
                "output_file": "💾 Output file:",
                "settings": "⚙️ Settings: FPS={fps}, Codec={codec}, Quality={quality}",
                "no_files_found": "No image files found matching {pattern} in {folder}",
                "found_images": "📸 Found {count} images",
                "image_size": "📐 Image size: {width}x{height}",
                "cannot_read_image": "Cannot read image: {file}",
                "cannot_create_video": "Cannot create video file, please check path and permissions",
                "skip_image": "⚠️ Skipping unreadable image: {file}",
                "processing": "🔄 Processing... {current}/{total} ({progress}%)",
                "processed_images": "📸 Processed {current}/{total} images",
                "conversion_complete": "✅ Video conversion complete!",
                "output_file_log": "📁 Output file: {file}",
                "total_processed": "📊 Total processed {count} images",
                "success_message": "Successfully converted {count} images to video",
                "user_cancelled": "User cancelled conversion",
                "conversion_error": "Error occurred during conversion: {error}"
            }
        }
        
    def run(self):
        try:
            self.status_updated.emit(self.texts[self.language]["start_conversion"])
            self.log_updated.emit(f"{self.texts[self.language]['input_folder']}{self.input_folder}")
            self.log_updated.emit(f"{self.texts[self.language]['output_file']}{self.output_path}")
            self.log_updated.emit(self.texts[self.language]["settings"].format(fps=self.fps, codec=self.codec, quality=self.quality))
            
            # 尋找圖片檔案
            pattern = os.path.join(self.input_folder, self.image_pattern)
            image_files = glob.glob(pattern)
            # 使用自然排序，正確處理數字順序
            image_files.sort(key=natural_sort_key)
            
            if not image_files:
                self.finished.emit(False, self.texts[self.language]["no_files_found"].format(folder=self.input_folder, pattern=self.image_pattern))
                return
            
            # 應用影格範圍過濾
            if self.start_frame is not None or self.end_frame is not None:
                filtered_files = []
                for file_path in image_files:
                    # 從檔案名提取影格號碼
                    frame_num = self.extract_frame_number(file_path)
                    if frame_num is not None:
                        if self.start_frame is not None and frame_num < self.start_frame:
                            continue
                        if self.end_frame is not None and frame_num > self.end_frame:
                            continue
                        filtered_files.append(file_path)
                image_files = filtered_files
                
                if not image_files:
                    self.finished.emit(False, f"在指定影格範圍內沒有找到圖片檔案 (起始: {self.start_frame}, 結束: {self.end_frame})")
                    return
                
            self.log_updated.emit(self.texts[self.language]["found_images"].format(count=len(image_files)))
            
            # 記錄標註設定
            if self.add_yolo or self.add_mot:
                annotation_info = []
                if self.add_yolo and self.yolo_folder:
                    annotation_info.append(f"YOLO: {self.yolo_folder}")
                if self.add_mot and self.mot_folder:
                    annotation_info.append(f"MOT: {self.mot_folder}")
                if annotation_info:
                    self.log_updated.emit(f"🏷️ 標註設定: {', '.join(annotation_info)}")
                    self.log_updated.emit(f"📍 標註位置: {self.annotation_position}")
            
            # 讀取第一張圖片來獲取尺寸
            first_image = cv2.imread(image_files[0])
            if first_image is None:
                self.finished.emit(False, self.texts[self.language]["cannot_read_image"].format(file=image_files[0]))
                return
                
            height, width, channels = first_image.shape
            self.log_updated.emit(self.texts[self.language]["image_size"].format(width=width, height=height))
            
            # 設定影片編碼器
            fourcc = cv2.VideoWriter_fourcc(*self.codec)
            
            # 根據品質設定壓縮參數
            if self.quality == "高品質":
                compression_params = [cv2.IMWRITE_JPEG_QUALITY, 95]
            elif self.quality == "中品質":
                compression_params = [cv2.IMWRITE_JPEG_QUALITY, 80]
            else:  # 低品質
                compression_params = [cv2.IMWRITE_JPEG_QUALITY, 60]
            
            # 創建影片寫入器
            out = cv2.VideoWriter(self.output_path, fourcc, self.fps, (width, height))
            
            if not out.isOpened():
                self.finished.emit(False, self.texts[self.language]["cannot_create_video"])
                return
            
            # 處理每張圖片
            for i, image_path in enumerate(image_files):
                if self.is_cancelled:
                    self.finished.emit(False, self.texts[self.language]["user_cancelled"])
                    return
                    
                # 讀取圖片
                frame = cv2.imread(image_path)
                if frame is None:
                    self.log_updated.emit(self.texts[self.language]["skip_image"].format(file=os.path.basename(image_path)))
                    continue
                
                # 調整圖片尺寸（如果需要）
                if frame.shape[:2] != (height, width):
                    frame = cv2.resize(frame, (width, height))
                
                # 添加標註（如果啟用）
                if self.add_yolo or self.add_mot:
                    # 提取影格號碼
                    frame_num = self.extract_frame_number(image_path)
                    
                    yolo_labels = []
                    mot_labels = []
                    
                    # 讀取YOLO標註
                    if self.add_yolo and self.yolo_folder and frame_num is not None:
                        # 根據圖片檔案名生成對應的標註檔案名
                        base_name = os.path.splitext(os.path.basename(image_path))[0]
                        yolo_label_path = os.path.join(self.yolo_folder, f"{base_name}.txt")
                        yolo_labels = read_yolo_labels(yolo_label_path, width, height)
                    
                    # 讀取MOT標註
                    if self.add_mot and self.mot_folder and frame_num is not None:
                        # 尋找MOT標註檔案
                        mot_files = glob.glob(os.path.join(self.mot_folder, "*.txt"))
                        if mot_files:
                            # 使用第一個找到的MOT檔案
                            mot_labels = read_mot_labels(mot_files[0], frame_num)
                    
                    # 在影格上繪製標註
                    if yolo_labels or mot_labels:
                        frame = draw_annotations_on_frame(frame, yolo_labels, mot_labels, 
                                                        self.annotation_position, self.simple_mode, self.color_mode)
                
                # 寫入影片
                out.write(frame)
                
                # 更新進度
                progress = int((i + 1) / len(image_files) * 100)
                self.progress_updated.emit(i + 1, len(image_files))
                self.status_updated.emit(self.texts[self.language]["processing"].format(current=i + 1, total=len(image_files), progress=progress))
                
                if (i + 1) % 50 == 0:  # 每50張圖片記錄一次
                    self.log_updated.emit(self.texts[self.language]["processed_images"].format(current=i + 1, total=len(image_files)))
            
            # 釋放資源
            out.release()
            
            if not self.is_cancelled:
                self.log_updated.emit(self.texts[self.language]["conversion_complete"])
                self.log_updated.emit(self.texts[self.language]["output_file_log"].format(file=self.output_path))
                self.log_updated.emit(self.texts[self.language]["total_processed"].format(count=len(image_files)))
                self.finished.emit(True, self.texts[self.language]["success_message"].format(count=len(image_files)))
            
        except Exception as e:
            self.finished.emit(False, self.texts[self.language]["conversion_error"].format(error=str(e)))
    
    def extract_frame_number(self, file_path):
        """從檔案路徑中提取影格號碼"""
        import re
        base = os.path.splitext(os.path.basename(file_path))[0]
        m = re.search(r'(\d+)$', base)
        return int(m.group(1)) if m else None
    
    def cancel(self):
        self.is_cancelled = True

class VideoConvertor(QMainWindow):
    """影片轉換器主視窗"""
    def __init__(self):
        super().__init__()
        
        # 語言設定 - 從環境變數讀取，如果沒有則預設中文
        self.current_language = os.environ.get('AIRSIM_LANGUAGE', 'zh')
        self.texts = {
            "zh": {
                "title": "🎬 AirSim 影片轉換器",
                "input_group": "📁 輸入設定",
                "image_folder": "圖片資料夾：",
                "browse": "📂 瀏覽",
                "image_pattern": "圖片模式：",
                "output_group": "💾 輸出設定",
                "output_file": "輸出檔案：",
                "select": "💾 選擇",
                "video_group": "⚙️ 影片設定",
                "fps": "FPS：",
                "codec": "編碼器：",
                "quality": "品質：",
                "progress_group": "📊 轉換進度",
                "ready": "準備開始轉換...",
                "log_group": "📋 轉換日誌",
                "start": "🚀 開始轉換",
                "cancel": "⏹️ 取消",
                "clear_log": "🗑️ 清空日誌",
                "language": "🌐 語言",
                "quality_options": ["高品質", "中品質", "低品質"],
                "conversion_complete": "✅ 轉換完成！",
                "conversion_failed": "❌ 轉換失敗",
                "conversion_complete_title": "轉換完成",
                "conversion_failed_title": "轉換失敗",
                "conversion_end": "🏁 轉換結束：{message}",
                "cancelling": "⏹️ 正在取消轉換...",
                "ready_status": "準備開始轉換...",
                "ready_status_en": "Ready to start conversion...",
                "frame_range": "影格範圍",
                "start_frame": "起始影格：",
                "end_frame": "結束影格：",
                "use_frame_range": "使用影格範圍",
                "fps_options": "FPS選項",
                "custom_fps": "自訂FPS",
                "annotation_options": "標註選項",
                "add_yolo_labels": "添加YOLO標籤",
                "add_mot_labels": "添加MOT標籤",
                "yolo_folder": "YOLO標籤資料夾：",
                "mot_folder": "MOT標籤資料夾：",
                "browse_yolo": "📂 瀏覽YOLO",
                "browse_mot": "📂 瀏覽MOT",
                "annotation_position": "標註位置：",
                "position_top_left": "左上角",
                "position_top_right": "右上角",
                "position_bottom_left": "左下角",
                "position_bottom_right": "右下角",
                "position_center": "中央",
                "simple_mode": "簡易模式",
                "simple_mode_tooltip": "只顯示邊界框，不顯示標籤文字",
                "color_mode": "框顏色模式：",
                "color_default": "預設",
                "color_red": "紅色",
                "color_green": "綠色",
                "color_blue": "藍色",
                "color_yellow": "黃色",
                "color_magenta": "洋紅",
                "color_cyan": "青色"
            },
            "en": {
                "title": "🎬 AirSim Video Converter",
                "input_group": "📁 Input Settings",
                "image_folder": "Image Folder:",
                "browse": "📂 Browse",
                "image_pattern": "Image Pattern:",
                "output_group": "💾 Output Settings",
                "output_file": "Output File:",
                "select": "💾 Select",
                "video_group": "⚙️ Video Settings",
                "fps": "FPS:",
                "codec": "Codec:",
                "quality": "Quality:",
                "progress_group": "📊 Conversion Progress",
                "ready": "Ready to start conversion...",
                "log_group": "📋 Conversion Log",
                "start": "🚀 Start Conversion",
                "cancel": "⏹️ Cancel",
                "clear_log": "🗑️ Clear Log",
                "language": "🌐 Language",
                "quality_options": ["High Quality", "Medium Quality", "Low Quality"],
                "conversion_complete": "✅ Conversion Complete!",
                "conversion_failed": "❌ Conversion Failed",
                "conversion_complete_title": "Conversion Complete",
                "conversion_failed_title": "Conversion Failed",
                "conversion_end": "🏁 Conversion ended: {message}",
                "cancelling": "⏹️ Cancelling conversion...",
                "ready_status": "Ready to start conversion...",
                "ready_status_en": "Ready to start conversion...",
                "frame_range": "Frame Range",
                "start_frame": "Start Frame:",
                "end_frame": "End Frame:",
                "use_frame_range": "Use Frame Range",
                "fps_options": "FPS Options",
                "custom_fps": "Custom FPS",
                "annotation_options": "Annotation Options",
                "add_yolo_labels": "Add YOLO Labels",
                "add_mot_labels": "Add MOT Labels",
                "yolo_folder": "YOLO Label Folder:",
                "mot_folder": "MOT Label Folder:",
                "browse_yolo": "📂 Browse YOLO",
                "browse_mot": "📂 Browse MOT",
                "annotation_position": "Annotation Position:",
                "position_top_left": "Top Left",
                "position_top_right": "Top Right",
                "position_bottom_left": "Bottom Left",
                "position_bottom_right": "Bottom Right",
                "position_center": "Center",
                "simple_mode": "Simple Mode",
                "simple_mode_tooltip": "Show only bounding boxes, no text labels",
                "color_mode": "Box Color Mode:",
                "color_default": "Default",
                "color_red": "Red",
                "color_green": "Green",
                "color_blue": "Blue",
                "color_yellow": "Yellow",
                "color_magenta": "Magenta",
                "color_cyan": "Cyan"
            }
        }
        
        self.setWindowTitle(self.texts[self.current_language]["title"])
        self.setGeometry(200, 200, 800, 700)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
        """)
        
        # 載入設定
        self.settings = load_settings()
        
        self.convert_thread = None
        self.init_ui()
        
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 標題
        self.title_label = QLabel(self.texts[self.current_language]["title"])
        self.title_label.setAlignment(Qt.AlignCenter)
        title_font = QFont("Microsoft YaHei", 18, QFont.Bold)
        self.title_label.setFont(title_font)
        self.title_label.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                background-color: #ecf0f1;
                border: 2px solid #3498db;
                border-radius: 10px;
                padding: 15px;
                margin: 10px;
            }
        """)
        layout.addWidget(self.title_label)
        
        # 輸入設定區域
        self.input_group = QGroupBox(self.texts[self.current_language]["input_group"])
        self.input_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        input_layout = QGridLayout(self.input_group)
        
        # 輸入資料夾選擇
        input_layout.addWidget(QLabel(self.texts[self.current_language]["image_folder"]), 0, 0)
        self.input_folder_label = QLabel("未選擇資料夾" if self.current_language == "zh" else "No folder selected")
        self.input_folder_label.setStyleSheet("""
            QLabel {
                background-color: #ffffff;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                padding: 8px;
                color: #7f8c8d;
            }
        """)
        input_layout.addWidget(self.input_folder_label, 0, 1)
        
        self.browse_input_btn = QPushButton(self.texts[self.current_language]["browse"])
        self.browse_input_btn.clicked.connect(self.browse_input_folder)
        self.browse_input_btn.setStyleSheet(self.get_button_style("#3498db"))
        input_layout.addWidget(self.browse_input_btn, 0, 2)
        
        # 圖片檔案模式
        input_layout.addWidget(QLabel(self.texts[self.current_language]["image_pattern"]), 1, 0)
        self.image_pattern_combo = QComboBox()
        self.image_pattern_combo.addItems([
            "Img0_*.png",
            "Img1_*.png", 
            "Seg_*.png",
            "Depth_*.png",
            "Disparity_*.png",
            "*.png"
        ])
        self.image_pattern_combo.setStyleSheet("""
            QComboBox {
                padding: 8px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                background-color: white;
            }
        """)
        input_layout.addWidget(self.image_pattern_combo, 1, 1, 1, 2)
        
        layout.addWidget(self.input_group)
        
        # 輸出設定區域
        self.output_group = QGroupBox(self.texts[self.current_language]["output_group"])
        self.output_group.setStyleSheet(self.input_group.styleSheet())
        output_layout = QGridLayout(self.output_group)
        
        # 輸出檔案選擇
        output_layout.addWidget(QLabel(self.texts[self.current_language]["output_file"]), 0, 0)
        self.output_path_label = QLabel("未選擇輸出檔案" if self.current_language == "zh" else "No output file selected")
        self.output_path_label.setStyleSheet(self.input_folder_label.styleSheet())
        output_layout.addWidget(self.output_path_label, 0, 1)
        
        self.browse_output_btn = QPushButton(self.texts[self.current_language]["select"])
        self.browse_output_btn.clicked.connect(self.browse_output_file)
        self.browse_output_btn.setStyleSheet(self.get_button_style("#27ae60"))
        output_layout.addWidget(self.browse_output_btn, 0, 2)
        
        layout.addWidget(self.output_group)
        
        # 影片設定區域
        self.video_group = QGroupBox(self.texts[self.current_language]["video_group"])
        self.video_group.setStyleSheet(self.input_group.styleSheet())
        video_layout = QGridLayout(self.video_group)
        
        # FPS 設定
        video_layout.addWidget(QLabel(self.texts[self.current_language]["fps"]), 0, 0)
        self.fps_spinbox = QSpinBox()
        self.fps_spinbox.setRange(1, 60)
        # 從設定檔讀取預設 FPS 值
        default_fps = self.settings.get('FPS_Default', 20)
        self.fps_spinbox.setValue(default_fps)
        self.fps_spinbox.setStyleSheet("""
            QSpinBox {
                padding: 8px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                background-color: white;
            }
        """)
        video_layout.addWidget(self.fps_spinbox, 0, 1)
        
        # 編碼器選擇
        video_layout.addWidget(QLabel(self.texts[self.current_language]["codec"]), 0, 2)
        self.codec_combo = QComboBox()
        self.codec_combo.addItems(["mp4v", "XVID", "MJPG", "X264"])
        self.codec_combo.setCurrentText("mp4v")
        self.codec_combo.setStyleSheet(self.image_pattern_combo.styleSheet())
        video_layout.addWidget(self.codec_combo, 0, 3)
        
        # 品質設定
        video_layout.addWidget(QLabel(self.texts[self.current_language]["quality"]), 1, 0)
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(self.texts[self.current_language]["quality_options"])
        self.quality_combo.setCurrentText(self.texts[self.current_language]["quality_options"][0])
        self.quality_combo.setStyleSheet(self.image_pattern_combo.styleSheet())
        video_layout.addWidget(self.quality_combo, 1, 1)
        
        layout.addWidget(self.video_group)
        
        # 影格範圍設定區域
        self.frame_range_group = QGroupBox(self.texts[self.current_language]["frame_range"])
        self.frame_range_group.setStyleSheet(self.input_group.styleSheet())
        frame_range_layout = QGridLayout(self.frame_range_group)
        
        # 使用影格範圍選項
        self.use_frame_range_checkbox = QCheckBox(self.texts[self.current_language]["use_frame_range"])
        self.use_frame_range_checkbox.stateChanged.connect(self.on_frame_range_changed)
        frame_range_layout.addWidget(self.use_frame_range_checkbox, 0, 0, 1, 3)
        
        # 起始影格
        frame_range_layout.addWidget(QLabel(self.texts[self.current_language]["start_frame"]), 1, 0)
        self.start_frame_spinbox = QSpinBox()
        self.start_frame_spinbox.setRange(1, 9999)
        self.start_frame_spinbox.setValue(1)
        self.start_frame_spinbox.setEnabled(False)
        self.start_frame_spinbox.setStyleSheet(self.fps_spinbox.styleSheet())
        frame_range_layout.addWidget(self.start_frame_spinbox, 1, 1)
        
        # 結束影格
        frame_range_layout.addWidget(QLabel(self.texts[self.current_language]["end_frame"]), 1, 2)
        self.end_frame_spinbox = QSpinBox()
        self.end_frame_spinbox.setRange(1, 9999)
        self.end_frame_spinbox.setValue(100)
        self.end_frame_spinbox.setEnabled(False)
        self.end_frame_spinbox.setStyleSheet(self.fps_spinbox.styleSheet())
        frame_range_layout.addWidget(self.end_frame_spinbox, 1, 3)
        
        layout.addWidget(self.frame_range_group)
        
        # 標註選項區域
        self.annotation_group = QGroupBox(self.texts[self.current_language]["annotation_options"])
        self.annotation_group.setStyleSheet(self.input_group.styleSheet())
        annotation_layout = QGridLayout(self.annotation_group)
        
        # YOLO標籤選項
        self.add_yolo_checkbox = QCheckBox(self.texts[self.current_language]["add_yolo_labels"])
        self.add_yolo_checkbox.stateChanged.connect(self.on_yolo_changed)
        annotation_layout.addWidget(self.add_yolo_checkbox, 0, 0, 1, 2)
        
        annotation_layout.addWidget(QLabel(self.texts[self.current_language]["yolo_folder"]), 1, 0)
        self.yolo_folder_label = QLabel("未選擇YOLO資料夾" if self.current_language == "zh" else "No YOLO folder selected")
        self.yolo_folder_label.setStyleSheet(self.input_folder_label.styleSheet())
        self.yolo_folder_label.setEnabled(False)
        annotation_layout.addWidget(self.yolo_folder_label, 1, 1)
        
        self.browse_yolo_btn = QPushButton(self.texts[self.current_language]["browse_yolo"])
        self.browse_yolo_btn.clicked.connect(self.browse_yolo_folder)
        self.browse_yolo_btn.setEnabled(False)
        self.browse_yolo_btn.setStyleSheet(self.get_button_style("#f39c12"))
        annotation_layout.addWidget(self.browse_yolo_btn, 1, 2)
        
        # MOT標籤選項
        self.add_mot_checkbox = QCheckBox(self.texts[self.current_language]["add_mot_labels"])
        self.add_mot_checkbox.stateChanged.connect(self.on_mot_changed)
        annotation_layout.addWidget(self.add_mot_checkbox, 2, 0, 1, 2)
        
        annotation_layout.addWidget(QLabel(self.texts[self.current_language]["mot_folder"]), 3, 0)
        self.mot_folder_label = QLabel("未選擇MOT資料夾" if self.current_language == "zh" else "No MOT folder selected")
        self.mot_folder_label.setStyleSheet(self.input_folder_label.styleSheet())
        self.mot_folder_label.setEnabled(False)
        annotation_layout.addWidget(self.mot_folder_label, 3, 1)
        
        self.browse_mot_btn = QPushButton(self.texts[self.current_language]["browse_mot"])
        self.browse_mot_btn.clicked.connect(self.browse_mot_folder)
        self.browse_mot_btn.setEnabled(False)
        self.browse_mot_btn.setStyleSheet(self.get_button_style("#8e44ad"))
        annotation_layout.addWidget(self.browse_mot_btn, 3, 2)
        
        # 標註位置選擇
        annotation_layout.addWidget(QLabel(self.texts[self.current_language]["annotation_position"]), 4, 0)
        self.annotation_position_combo = QComboBox()
        self.annotation_position_combo.addItems([
            self.texts[self.current_language]["position_top_left"],
            self.texts[self.current_language]["position_top_right"],
            self.texts[self.current_language]["position_bottom_left"],
            self.texts[self.current_language]["position_bottom_right"],
            self.texts[self.current_language]["position_center"]
        ])
        self.annotation_position_combo.setCurrentText(self.texts[self.current_language]["position_top_left"])
        self.annotation_position_combo.setStyleSheet(self.image_pattern_combo.styleSheet())
        annotation_layout.addWidget(self.annotation_position_combo, 4, 1, 1, 2)
        
        # 簡易模式選項
        self.simple_mode_checkbox = QCheckBox(self.texts[self.current_language]["simple_mode"])
        self.simple_mode_checkbox.setToolTip(self.texts[self.current_language]["simple_mode_tooltip"])
        annotation_layout.addWidget(self.simple_mode_checkbox, 5, 0, 1, 3)
        
        # 框顏色模式選擇
        annotation_layout.addWidget(QLabel(self.texts[self.current_language]["color_mode"]), 6, 0)
        self.color_mode_combo = QComboBox()
        self.color_mode_combo.addItems([
            self.texts[self.current_language]["color_default"],
            self.texts[self.current_language]["color_red"],
            self.texts[self.current_language]["color_green"],
            self.texts[self.current_language]["color_blue"],
            self.texts[self.current_language]["color_yellow"],
            self.texts[self.current_language]["color_magenta"],
            self.texts[self.current_language]["color_cyan"]
        ])
        self.color_mode_combo.setCurrentText(self.texts[self.current_language]["color_default"])
        self.color_mode_combo.setStyleSheet(self.image_pattern_combo.styleSheet())
        annotation_layout.addWidget(self.color_mode_combo, 6, 1, 1, 2)
        
        layout.addWidget(self.annotation_group)
        
        # 進度區域
        self.progress_group = QGroupBox(self.texts[self.current_language]["progress_group"])
        self.progress_group.setStyleSheet(self.input_group.styleSheet())
        progress_layout = QVBoxLayout(self.progress_group)
        
        # 狀態標籤
        self.status_label = QLabel(self.texts[self.current_language]["ready"])
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("""
            QLabel {
                color: #34495e;
                background-color: #ffffff;
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                padding: 10px;
                font-weight: bold;
            }
        """)
        progress_layout.addWidget(self.status_label)
        
        # 進度條
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                text-align: center;
                font-weight: bold;
                font-size: 12px;
                height: 25px;
            }
            QProgressBar::chunk {
                background-color: #3498db;
                border-radius: 6px;
            }
        """)
        progress_layout.addWidget(self.progress_bar)
        
        # 控制按鈕（移到進度區域下方）
        button_layout = QHBoxLayout()
        
        self.start_btn = QPushButton(self.texts[self.current_language]["start"])
        self.start_btn.clicked.connect(self.start_conversion)
        self.start_btn.setStyleSheet(self.get_button_style("#27ae60"))
        
        self.cancel_btn = QPushButton(self.texts[self.current_language]["cancel"])
        self.cancel_btn.clicked.connect(self.cancel_conversion)
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.setStyleSheet(self.get_button_style("#e74c3c"))
        
        # 讓兩個按鈕各佔一半寬度
        button_layout.addWidget(self.start_btn, 1)
        button_layout.addWidget(self.cancel_btn, 1)
        
        progress_layout.addLayout(button_layout)
        layout.addWidget(self.progress_group)
        
        # 日誌區域
        self.log_group = QGroupBox(self.texts[self.current_language]["log_group"])
        self.log_group.setStyleSheet(self.input_group.styleSheet())
        log_layout = QVBoxLayout(self.log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #2c3e50;
                color: #ecf0f1;
                border: 1px solid #34495e;
                border-radius: 8px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 11px;
                padding: 10px;
            }
        """)
        log_layout.addWidget(self.log_text)
        
        # 清空日誌按鈕
        self.clear_log_btn = QPushButton(self.texts[self.current_language]["clear_log"])
        self.clear_log_btn.clicked.connect(self.clear_log)
        self.clear_log_btn.setStyleSheet(self.get_button_style("#95a5a6"))
        log_layout.addWidget(self.clear_log_btn)
        
        layout.addWidget(self.log_group)
        
        # 語言切換按鈕
        self.language_btn = QPushButton(self.texts[self.current_language]["language"])
        self.language_btn.clicked.connect(self.toggle_language)
        self.language_btn.setStyleSheet(self.get_button_style("#9b59b6"))
        layout.addWidget(self.language_btn)
        
        # 初始化預設路徑
        self.init_default_paths()
        
        # 初始化預設標註資料夾
        self.init_default_annotation_paths()
        
        # 初始化日誌
        self.add_log("🎬 影片轉換器已準備就緒")
        self.add_log("📝 請選擇輸入資料夾和輸出檔案")
        
    def get_button_style(self, color):
        """按鈕樣式"""
        return f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 12px;
                font-weight: bold;
                padding: 10px 20px;
                min-width: 100px;
            }}
            QPushButton:hover {{
                background-color: {self.darken_color(color)};
                border: 2px solid {self.darken_color(color, 0.7)};
            }}
            QPushButton:pressed {{
                background-color: {self.darken_color(color, 0.8)};
            }}
            QPushButton:disabled {{
                background-color: #95a5a6;
                color: #7f8c8d;
            }}
        """
        
    def darken_color(self, color, factor=0.85):
        """將顏色變暗"""
        if factor == 0.7:
            color_map = {
                "#3498db": "#5dade2",
                "#27ae60": "#58d68d",
                "#e74c3c": "#ec7063",
                "#95a5a6": "#aab7b8"
            }
        elif factor == 0.8:
            color_map = {
                "#3498db": "#2471a3",
                "#27ae60": "#1e8449",
                "#e74c3c": "#a93226",
                "#95a5a6": "#717d7e"
            }
        else:
            color_map = {
                "#3498db": "#2980b9",
                "#27ae60": "#229954",
                "#e74c3c": "#c0392b",
                "#95a5a6": "#7f8c8d"
            }
        return color_map.get(color, color)
        
    def init_default_paths(self):
        """初始化預設路徑"""
        # 設定預設輸入資料夾
        default_input = self.settings.get('Video_Input_folder', 'ProcessData')
        if os.path.exists(default_input):
            self.input_folder_label.setText(default_input)
            self.input_folder_label.setStyleSheet("""
                QLabel {
                    background-color: #d5f4e6;
                    border: 1px solid #27ae60;
                    border-radius: 4px;
                    padding: 8px;
                    color: #1e8449;
                    font-weight: bold;
                }
            """)
            self.add_log(f"📁 已設定預設輸入資料夾：{default_input}")
        
        # 設定預設輸出路徑
        default_output_folder = self.settings.get('Video_Output_folder', 'Results')
        default_name = self.settings.get('Name_Default', 'Sample_Video')
        if os.path.exists(default_output_folder):
            default_output_file = os.path.join(default_output_folder, f"{default_name}.mp4")
            self.output_path_label.setText(default_output_file)
            self.output_path_label.setStyleSheet("""
                QLabel {
                    background-color: #d5f4e6;
                    border: 1px solid #27ae60;
                    border-radius: 4px;
                    padding: 8px;
                    color: #1e8449;
                    font-weight: bold;
                }
            """)
            self.add_log(f"💾 已設定預設輸出檔案：{default_output_file}")
    
    def init_default_annotation_paths(self):
        """初始化預設標註資料夾路徑"""
        # 設定預設YOLO標籤資料夾
        default_yolo_folder = self.settings.get('Video_YOLO_Label', 'Results/YOLO_Label')
        if os.path.exists(default_yolo_folder):
            self.yolo_folder_label.setText(default_yolo_folder)
            self.yolo_folder_label.setStyleSheet("""
                QLabel {
                    background-color: #d5f4e6;
                    border: 1px solid #27ae60;
                    border-radius: 4px;
                    padding: 8px;
                    color: #1e8449;
                    font-weight: bold;
                }
            """)
            self.add_log(f"📁 已設定預設YOLO標籤資料夾：{default_yolo_folder}")
        
        # 設定預設MOT標籤資料夾
        default_mot_folder = self.settings.get('Video_MOT_Label', 'Results/MOT_Label')
        if os.path.exists(default_mot_folder):
            self.mot_folder_label.setText(default_mot_folder)
            self.mot_folder_label.setStyleSheet("""
                QLabel {
                    background-color: #d5f4e6;
                    border: 1px solid #27ae60;
                    border-radius: 4px;
                    padding: 8px;
                    color: #1e8449;
                    font-weight: bold;
                }
            """)
            self.add_log(f"📁 已設定預設MOT標籤資料夾：{default_mot_folder}")
        
    def browse_input_folder(self):
        """選擇輸入資料夾"""
        # 使用設定檔中的預設路徑作為起始目錄
        default_folder = self.settings.get('Video_Input_folder', 'ProcessData')
        if os.path.exists(default_folder):
            start_dir = default_folder
        else:
            start_dir = ""
            
        folder = QFileDialog.getExistingDirectory(self, "選擇圖片資料夾", start_dir)
        if folder:
            self.input_folder_label.setText(folder)
            self.input_folder_label.setStyleSheet("""
                QLabel {
                    background-color: #d5f4e6;
                    border: 1px solid #27ae60;
                    border-radius: 4px;
                    padding: 8px;
                    color: #1e8449;
                    font-weight: bold;
                }
            """)
            self.add_log(f"📁 已選擇輸入資料夾：{folder}")
            
    def browse_output_file(self):
        """選擇輸出檔案"""
        # 使用設定檔中的預設路徑作為起始目錄
        default_output_folder = self.settings.get('Video_Output_folder', 'Results')
        default_name = self.settings.get('Name_Default', 'Sample_Video')
        if os.path.exists(default_output_folder):
            start_dir = os.path.join(default_output_folder, f"{default_name}.mp4")
        else:
            start_dir = f"{default_name}.mp4"
            
        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            "選擇輸出影片檔案", 
            start_dir, 
            "MP4 影片 (*.mp4);;AVI 影片 (*.avi);;所有檔案 (*)"
        )
        if file_path:
            self.output_path_label.setText(file_path)
            self.output_path_label.setStyleSheet("""
                QLabel {
                    background-color: #d5f4e6;
                    border: 1px solid #27ae60;
                    border-radius: 4px;
                    padding: 8px;
                    color: #1e8449;
                    font-weight: bold;
                }
            """)
            self.add_log(f"💾 已選擇輸出檔案：{file_path}")
            
    def add_log(self, message):
        """添加日誌訊息"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        
        self.log_text.append(log_message)
        
        # 自動滾動到底部
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
    def clear_log(self):
        """清空日誌"""
        self.log_text.clear()
        self.add_log("🗑️ 日誌已清空")
        
    def toggle_language(self):
        """切換語言"""
        if self.current_language == "zh":
            self.current_language = "en"
        else:
            self.current_language = "zh"
        
        # 更新視窗標題
        self.setWindowTitle(self.texts[self.current_language]["title"])
        
        # 更新所有UI文字
        self.title_label.setText(self.texts[self.current_language]["title"])
        self.input_group.setTitle(self.texts[self.current_language]["input_group"])
        self.output_group.setTitle(self.texts[self.current_language]["output_group"])
        self.video_group.setTitle(self.texts[self.current_language]["video_group"])
        self.frame_range_group.setTitle(self.texts[self.current_language]["frame_range"])
        self.annotation_group.setTitle(self.texts[self.current_language]["annotation_options"])
        self.progress_group.setTitle(self.texts[self.current_language]["progress_group"])
        self.log_group.setTitle(self.texts[self.current_language]["log_group"])
        
        # 更新按鈕文字
        self.browse_input_btn.setText(self.texts[self.current_language]["browse"])
        self.browse_output_btn.setText(self.texts[self.current_language]["select"])
        self.start_btn.setText(self.texts[self.current_language]["start"])
        self.cancel_btn.setText(self.texts[self.current_language]["cancel"])
        self.clear_log_btn.setText(self.texts[self.current_language]["clear_log"])
        self.language_btn.setText(self.texts[self.current_language]["language"])
        
        # 更新品質選項
        self.quality_combo.clear()
        self.quality_combo.addItems(self.texts[self.current_language]["quality_options"])
        self.quality_combo.setCurrentText(self.texts[self.current_language]["quality_options"][0])
        
        # 更新簡易模式選項
        self.simple_mode_checkbox.setText(self.texts[self.current_language]["simple_mode"])
        self.simple_mode_checkbox.setToolTip(self.texts[self.current_language]["simple_mode_tooltip"])
        
        # 更新顏色模式選項
        current_color = self.color_mode_combo.currentText()
        self.color_mode_combo.clear()
        self.color_mode_combo.addItems([
            self.texts[self.current_language]["color_default"],
            self.texts[self.current_language]["color_red"],
            self.texts[self.current_language]["color_green"],
            self.texts[self.current_language]["color_blue"],
            self.texts[self.current_language]["color_yellow"],
            self.texts[self.current_language]["color_magenta"],
            self.texts[self.current_language]["color_cyan"]
        ])
        # 嘗試保持當前選擇的顏色
        if current_color in [self.texts[self.current_language]["color_default"],
                           self.texts[self.current_language]["color_red"],
                           self.texts[self.current_language]["color_green"],
                           self.texts[self.current_language]["color_blue"],
                           self.texts[self.current_language]["color_yellow"],
                           self.texts[self.current_language]["color_magenta"],
                           self.texts[self.current_language]["color_cyan"]]:
            self.color_mode_combo.setCurrentText(current_color)
        else:
            self.color_mode_combo.setCurrentText(self.texts[self.current_language]["color_default"])
        
        # 更新狀態標籤
        if not self.start_btn.isEnabled():
            self.status_label.setText(self.texts[self.current_language]["ready"])
        else:
            # 如果按鈕已啟用，顯示準備狀態
            self.status_label.setText(self.texts[self.current_language]["ready"])
        
        # 更新資料夾標籤
        if self.input_folder_label.text() in ["未選擇資料夾", "No folder selected"]:
            self.input_folder_label.setText("未選擇資料夾" if self.current_language == "zh" else "No folder selected")
        if self.output_path_label.text() in ["未選擇輸出檔案", "No output file selected"]:
            self.output_path_label.setText("未選擇輸出檔案" if self.current_language == "zh" else "No output file selected")
        
    def start_conversion(self):
        """開始轉換"""
        # 檢查輸入
        if self.input_folder_label.text() in ["未選擇資料夾", "No folder selected"]:
            warning_msg = "請先選擇輸入資料夾" if self.current_language == "zh" else "Please select input folder first"
            QMessageBox.warning(self, "警告" if self.current_language == "zh" else "Warning", warning_msg)
            return
            
        if self.output_path_label.text() in ["未選擇輸出檔案", "No output file selected"]:
            warning_msg = "請先選擇輸出檔案" if self.current_language == "zh" else "Please select output file first"
            QMessageBox.warning(self, "警告" if self.current_language == "zh" else "Warning", warning_msg)
            return
            
        if not os.path.exists(self.input_folder_label.text()):
            error_msg = "輸入資料夾不存在" if self.current_language == "zh" else "Input folder does not exist"
            QMessageBox.critical(self, "錯誤" if self.current_language == "zh" else "Error", error_msg)
            return
        
        # 獲取設定
        input_folder = self.input_folder_label.text()
        output_path = self.output_path_label.text()
        fps = self.fps_spinbox.value()
        codec = self.codec_combo.currentText()
        quality = self.quality_combo.currentText()
        image_pattern = self.image_pattern_combo.currentText()
        
        # 獲取影格範圍設定
        start_frame = None
        end_frame = None
        if self.use_frame_range_checkbox.isChecked():
            start_frame = self.start_frame_spinbox.value()
            end_frame = self.end_frame_spinbox.value()
        
        # 獲取標註設定
        add_yolo = self.add_yolo_checkbox.isChecked()
        add_mot = self.add_mot_checkbox.isChecked()
        yolo_folder = None
        mot_folder = None
        annotation_position = self.annotation_position_combo.currentText()
        simple_mode = self.simple_mode_checkbox.isChecked()
        color_mode = self.color_mode_combo.currentText()
        
        if add_yolo and self.yolo_folder_label.text() not in ["未選擇YOLO資料夾", "No YOLO folder selected"]:
            yolo_folder = self.yolo_folder_label.text()
        
        if add_mot and self.mot_folder_label.text() not in ["未選擇MOT資料夾", "No MOT folder selected"]:
            mot_folder = self.mot_folder_label.text()
        
        # 更新UI狀態
        self.start_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.progress_bar.setValue(0)
        
        # 創建並啟動轉換執行緒
        self.convert_thread = VideoConvertorThread(
            input_folder, output_path, fps, codec, quality, image_pattern,
            start_frame, end_frame, add_yolo, add_mot, yolo_folder, mot_folder, 
            annotation_position, simple_mode, color_mode, self.current_language
        )
        self.convert_thread.progress_updated.connect(self.update_progress)
        self.convert_thread.status_updated.connect(self.update_status)
        self.convert_thread.log_updated.connect(self.add_log)
        self.convert_thread.finished.connect(self.conversion_finished)
        self.convert_thread.start()
        
    def cancel_conversion(self):
        """取消轉換"""
        if self.convert_thread and self.convert_thread.isRunning():
            self.convert_thread.cancel()
            self.add_log(self.texts[self.current_language]["cancelling"])
            
    def update_progress(self, current, total):
        """更新進度條"""
        if total > 0:
            progress = int((current / total) * 100)
            self.progress_bar.setValue(progress)
            self.progress_bar.setFormat(f"{current}/{total} ({progress}%)")
            
    def update_status(self, status):
        """更新狀態標籤"""
        self.status_label.setText(status)
        
    def conversion_finished(self, success, message):
        """轉換完成"""
        self.start_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        
        if success:
            self.status_label.setText(self.texts[self.current_language]["conversion_complete"])
            self.status_label.setStyleSheet("""
                QLabel {
                    color: #27ae60;
                    background-color: #d5f4e6;
                    border: 1px solid #27ae60;
                    border-radius: 5px;
                    padding: 10px;
                    font-weight: bold;
                }
            """)
            self.progress_bar.setValue(100)
            QMessageBox.information(self, self.texts[self.current_language]["conversion_complete_title"], message)
        else:
            self.status_label.setText(self.texts[self.current_language]["conversion_failed"])
            self.status_label.setStyleSheet("""
                QLabel {
                    color: #e74c3c;
                    background-color: #fadbd8;
                    border: 1px solid #e74c3c;
                    border-radius: 5px;
                    padding: 10px;
                    font-weight: bold;
                }
            """)
            QMessageBox.critical(self, self.texts[self.current_language]["conversion_failed_title"], message)
            
        self.add_log(self.texts[self.current_language]["conversion_end"].format(message=message))
    
    def on_frame_range_changed(self, state):
        """當影格範圍選項改變時"""
        enabled = state == Qt.Checked
        self.start_frame_spinbox.setEnabled(enabled)
        self.end_frame_spinbox.setEnabled(enabled)
    
    def on_yolo_changed(self, state):
        """當YOLO標籤選項改變時"""
        enabled = state == Qt.Checked
        self.yolo_folder_label.setEnabled(enabled)
        self.browse_yolo_btn.setEnabled(enabled)
    
    def on_mot_changed(self, state):
        """當MOT標籤選項改變時"""
        enabled = state == Qt.Checked
        self.mot_folder_label.setEnabled(enabled)
        self.browse_mot_btn.setEnabled(enabled)
    
    def browse_yolo_folder(self):
        """選擇YOLO標籤資料夾"""
        # 使用設定檔中的預設路徑
        default_yolo_folder = self.settings.get('Video_YOLO_Label', 'Results/YOLO_Label')
        if os.path.exists(default_yolo_folder):
            start_dir = default_yolo_folder
        else:
            start_dir = ""
            
        folder = QFileDialog.getExistingDirectory(self, "選擇YOLO標籤資料夾", start_dir)
        if folder:
            self.yolo_folder_label.setText(folder)
            self.yolo_folder_label.setStyleSheet("""
                QLabel {
                    background-color: #d5f4e6;
                    border: 1px solid #27ae60;
                    border-radius: 4px;
                    padding: 8px;
                    color: #1e8449;
                    font-weight: bold;
                }
            """)
            self.add_log(f"📁 已選擇YOLO標籤資料夾：{folder}")
    
    def browse_mot_folder(self):
        """選擇MOT標籤資料夾"""
        # 使用設定檔中的預設路徑
        default_mot_folder = self.settings.get('Video_MOT_Label', 'Results/MOT_Label')
        if os.path.exists(default_mot_folder):
            start_dir = default_mot_folder
        else:
            start_dir = ""
            
        folder = QFileDialog.getExistingDirectory(self, "選擇MOT標籤資料夾", start_dir)
        if folder:
            self.mot_folder_label.setText(folder)
            self.mot_folder_label.setStyleSheet("""
                QLabel {
                    background-color: #d5f4e6;
                    border: 1px solid #27ae60;
                    border-radius: 4px;
                    padding: 8px;
                    color: #1e8449;
                    font-weight: bold;
                }
            """)
            self.add_log(f"📁 已選擇MOT標籤資料夾：{folder}")

def main():
    app = QApplication(sys.argv)
    
    # 設定應用程式屬性
    app.setApplicationName("AirSim 影片轉換器")
    app.setApplicationVersion("1.0")
    
    window = VideoConvertor()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
