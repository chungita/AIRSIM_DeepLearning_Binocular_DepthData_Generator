import sys
import os
import re
import numpy as np
import cv2
from PIL import Image
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QComboBox, QPushButton, QMessageBox)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QImage
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

# 設定中文字體，解決中文顯示亂碼問題
import matplotlib
matplotlib.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False

def load_settings():
    """
    從 Settings.txt 讀取設定
    """
    settings_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Settings.txt")
    settings = {}
    
    if os.path.exists(settings_file):
        try:
            with open(settings_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    if ':' in line:
                        key, value = line.split(':', 1)
                    elif '=' in line:
                        key, value = line.split('=', 1)
                    else:
                        continue
                    settings[key.strip()] = value.strip()
        except Exception as e:
            print(f"Error reading settings file: {e}")
    
    return settings

def read_pfm(file_path):
    """
    Reads a PFM file and returns the data and scale factor.
    """
    with open(file_path, 'rb') as file:
        header = file.readline().rstrip().decode('utf-8')
        color = header == 'PF'
        
        temp_str = file.readline().rstrip().decode('utf-8')
        dim_match = re.match(r'^(\d+)\s(\d+)\s*$', temp_str)
        if not dim_match:
            raise Exception('Malformed PFM header.')
        width, height = map(int, dim_match.groups())
        
        scale = float(file.readline().rstrip().decode('utf-8'))
        endian = '<' if scale < 0 else '>'
        scale = abs(scale)
        
        data = np.fromfile(file, endian + 'f')
        shape = (height, width, 3) if color else (height, width)
        
        if data.size != width * height * (3 if color else 1):
            raise Exception('Inconsistent PFM data size.')
        
        data = np.reshape(data, shape)
        return data, scale

def read_png(file_path):
    """
    Reads a PNG file and returns the data.
    """
    try:
        img = Image.open(file_path)
        data = np.array(img)
        return data, 1.0
    except Exception as e:
        print(f"Error reading PNG file {file_path}: {e}")
        return None, 1.0

def find_min_max_no_inf(data):
    """
    Finds the min and max values in the data, ignoring infinity and NaN.
    """
    finite_data = data[np.isfinite(data)]
    if finite_data.size == 0:
        return None, None
    return np.min(finite_data), np.max(finite_data)

class ImageViewerWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.settings = load_settings()
        self.image_files = []
        self.current_index = 0
        self.colorbar = None
        self.im = None
        self.current_data = None  # 儲存當前圖片數據用於鼠標追蹤
        self.current_language = os.environ.get('AIRSIM_LANGUAGE', 'zh')
        
        # 從設定讀取可用的圖片類型
        self.available_types = self.get_available_image_types()
        self.current_image_type = self.available_types[0] if self.available_types else 'Depth'
        
        self.init_ui()
        # 初始化時設定一次佈局
        self.figure.tight_layout()
        self.load_images()
        self.update_display()
        
    def get_available_image_types(self):
        """
        從設定中解析可用的圖片類型
        """
        pic_img_read = self.settings.get('PIC_Img_read', 'Depth')
        
        # 如果設定包含逗號，則分割成列表
        if ',' in pic_img_read:
            types = [t.strip() for t in pic_img_read.split(',')]
        else:
            types = [pic_img_read.strip()]
        
        types = [t for t in types if t]
        
        return types
    
    def set_language(self, language):
        """設置語言"""
        self.current_language = language
        
        # 更新按鈕文字
        self.prev_btn.setText(self.texts[self.current_language]["prev_image"])
        self.next_btn.setText(self.texts[self.current_language]["next_image"])
        self.type_switch_label.setText(self.texts[self.current_language]["type_switch"])
        self.pixel_value_label.setText(f"{self.texts[self.current_language]['pixel_value']} --")
        
        # 更新狀態標籤
        if not self.image_files:
            self.status_label.setText(self.texts[self.current_language]["no_files"])
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # 創建工具列容器，設定固定高度
        control_widget = QWidget()
        control_widget.setFixedHeight(60)  # 固定工具列高度為60像素
        self.control_layout = QHBoxLayout(control_widget)
        
        # 創建文字字典
        self.texts = {
            "zh": {
                "image_type": "圖片類型:",
                "prev_image": "上一張 (A)",
                "next_image": "下一張 (D)",
                "type_switch": "類型切換: W/S",
                "no_files": "沒有檔案",
                "pixel_value": "像素值:",
                "no_files_found": "沒有找到 {type} 檔案",
                "error": "錯誤",
                "folder_not_found": "找不到資料夾: {folder}",
                "unknown_type": "未知的圖片類型: {type}",
                "unsupported_format": "不支援的檔案格式: {ext}",
                "processing_error": "處理檔案時發生錯誤:\n檔案: {file}\n錯誤: {error}"
            },
            "en": {
                "image_type": "Image Type:",
                "prev_image": "Previous (A)",
                "next_image": "Next (D)",
                "type_switch": "Type Switch: W/S",
                "no_files": "No Files",
                "pixel_value": "Pixel Value:",
                "no_files_found": "No {type} files found",
                "error": "Error",
                "folder_not_found": "Folder not found: {folder}",
                "unknown_type": "Unknown image type: {type}",
                "unsupported_format": "Unsupported file format: {ext}",
                "processing_error": "Error processing file:\nFile: {file}\nError: {error}"
            }
        }
        
        self.control_layout.addWidget(QLabel(self.texts[self.current_language]["image_type"]))
        self.type_combo = QComboBox()
        self.type_combo.addItems(self.available_types)
        
        # 設定 ComboBox 不接受鍵盤焦點，避免搶奪焦點
        self.type_combo.setFocusPolicy(Qt.NoFocus)
        
        self.type_combo.blockSignals(True)
        self.type_combo.setCurrentText(self.current_image_type)
        self.type_combo.blockSignals(False)
        self.type_combo.currentTextChanged.connect(self.on_type_changed)
        
        self.control_layout.addWidget(self.type_combo)
        
        self.prev_btn = QPushButton(self.texts[self.current_language]["prev_image"])
        self.prev_btn.clicked.connect(self.prev_image)
        self.control_layout.addWidget(self.prev_btn)
        
        self.next_btn = QPushButton(self.texts[self.current_language]["next_image"])
        self.next_btn.clicked.connect(self.next_image)
        self.control_layout.addWidget(self.next_btn)
        
        self.type_switch_label = QLabel(self.texts[self.current_language]["type_switch"])
        self.control_layout.addWidget(self.type_switch_label)
        
        self.status_label = QLabel("")
        self.control_layout.addWidget(self.status_label)
        
        # 添加像素數值顯示標籤
        self.pixel_value_label = QLabel(f"{self.texts[self.current_language]['pixel_value']} --")
        self.pixel_value_label.setMinimumWidth(120)
        self.control_layout.addWidget(self.pixel_value_label)
        
        self.control_layout.addStretch()
        
        # 將工具列添加到主布局，不設定拉伸因子（預設為0，固定大小）
        layout.addWidget(control_widget)
        
        self.figure = Figure(figsize=(12, 8))
        self.canvas = FigureCanvas(self.figure)
        
        self.ax = self.figure.add_axes([0.1, 0.1, 0.75, 0.8])  # [left, bottom, width, height]
        
        # 將圖片畫布添加到主布局，設定拉伸因子為1（會隨視窗大小變化）
        layout.addWidget(self.canvas, 1)
        self.setLayout(layout)
        
        # 連接鼠標移動事件
        self.canvas.mpl_connect('motion_notify_event', self.on_mouse_move)
        
    def on_mouse_move(self, event):
        """
        處理鼠標移動事件，顯示當前像素的數值
        """
        if (event.inaxes != self.ax or self.current_data is None or 
            event.xdata is None or event.ydata is None):
            self.pixel_value_label.setText(f"{self.texts[self.current_language]['pixel_value']} --")
            return
            
        # 只在深度圖和視差圖時顯示數值
        if self.current_image_type.lower() not in ['depth', 'disparity']:
            self.pixel_value_label.setText(f"{self.texts[self.current_language]['pixel_value']} --")
            return
            
        try:
            # 取得鼠標位置的像素座標
            x = int(round(event.xdata))
            y = int(round(event.ydata))
            
            # 檢查座標是否在圖片範圍內
            if (0 <= x < self.current_data.shape[1] and 0 <= y < self.current_data.shape[0]):
                pixel_value = self.current_data[y, x]
                
                # 格式化顯示數值
                if np.isfinite(pixel_value):
                    self.pixel_value_label.setText(f"{self.texts[self.current_language]['pixel_value']} {pixel_value:.3f}")
                else:
                    self.pixel_value_label.setText(f"{self.texts[self.current_language]['pixel_value']} inf/nan")
            else:
                self.pixel_value_label.setText(f"{self.texts[self.current_language]['pixel_value']} --")
                
        except (IndexError, ValueError):
            self.pixel_value_label.setText(f"{self.texts[self.current_language]['pixel_value']} --")
        
    def on_type_changed(self, image_type):
        """
        當圖片類型改變時的回調函數
        """
        self.current_image_type = image_type
        self.current_index = 0
        self.load_images()
        if self.image_files and self.current_index >= len(self.image_files):
            self.current_index = 0
        self.update_display()
        
    def switch_image_type(self, direction):
        """
        切換圖片類型，保持當前序列號
        direction: 1 為下一個類型，-1 為上一個類型
        """
        if not self.available_types:
            return
            
        current_sequence = self.current_index
        
        try:
            current_type_index = self.available_types.index(self.current_image_type)
        except ValueError:
            current_type_index = 0
            
        new_type_index = (current_type_index + direction) % len(self.available_types)
        new_image_type = self.available_types[new_type_index]
        
        self.current_image_type = new_image_type
        
        self.type_combo.blockSignals(True)
        self.type_combo.setCurrentText(new_image_type)
        self.type_combo.blockSignals(False)
        
        self.load_images()
        
        if self.image_files and current_sequence < len(self.image_files):
            self.current_index = current_sequence
        else:
            self.current_index = max(0, len(self.image_files) - 1) if self.image_files else 0
            
        self.update_display()
        
    def load_images(self):
        """
        根據當前選擇的圖片類型載入圖片檔案
        """
        # 從設定讀取資料夾路徑
        data_folder = self.settings.get('Pic_Input_folder', 'Results/Img')
        data_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", data_folder)
        
        if not os.path.exists(data_folder):
            QMessageBox.warning(self, self.texts[self.current_language]["error"], 
                              self.texts[self.current_language]["folder_not_found"].format(folder=data_folder))
            self.image_files = []
            return
        
        try:
            all_files = os.listdir(data_folder)
        except Exception as e:
            all_files = []
        
        type_map = {
            'disparity': {'prefix': 'Disparity_', 'ext': '.pfm'},
            'depth':     {'prefix': 'DepthGT_',     'ext': '.pfm'},
            'img0':      {'prefix': 'Img0_',      'ext': '.png'},
            'img1':      {'prefix': 'Img1_',      'ext': '.png'},
        }
        
        t = self.current_image_type.lower()
        cfg = type_map.get(t, None)
        if not cfg:
            QMessageBox.warning(self, self.texts[self.current_language]["error"], 
                              self.texts[self.current_language]["unknown_type"].format(type=self.current_image_type))
            self.image_files = []
            return
        
        prefix = cfg['prefix']
        ext = cfg['ext']
        
        candidates = [f for f in all_files if f.lower().endswith(ext)]
        
        picked = []
        
        strict_match = [f for f in candidates if os.path.splitext(f)[0].lower().startswith(prefix.lower())]
        
        if not strict_match:
            if t == 'depth':
                depthgt_match = [f for f in candidates if 'depthgt' in f.lower()]
                if depthgt_match:
                    picked = depthgt_match
                else:
                    depth_match = [f for f in candidates if 'depth' in f.lower()]
                    picked = depth_match
            else:
                picked = [f for f in candidates if t in f.lower()]
        else:
            picked = strict_match
        
        self.image_files = [os.path.join(data_folder, f) for f in picked]
        
        def natural_key(name):
            parts = re.split(r'(\d+)', os.path.basename(name))
            return [int(p) if p.isdigit() else p.lower() for p in parts]
        
        self.image_files.sort(key=natural_key)
        
    def update_display(self):
        """
        更新顯示的圖片
        """
        
        if not self.image_files:
            self.ax.clear()
            self.ax.text(0.5, 0.5, self.texts[self.current_language]["no_files_found"].format(type=self.current_image_type), 
                        ha='center', va='center', transform=self.ax.transAxes)
            self.canvas.draw()
            self.status_label.setText(self.texts[self.current_language]["no_files"])
            self.pixel_value_label.setText(f"{self.texts[self.current_language]['pixel_value']} --")
            self.current_data = None
            return
        
        if self.current_index >= len(self.image_files):
            self.current_index = 0
        if self.current_index < 0:
            self.current_index = 0
            
        current_file = self.image_files[self.current_index]
        file_ext = os.path.splitext(current_file)[1].lower()
        
        try:
            if file_ext == '.pfm':
                data, scale = read_pfm(current_file)
                if data is None:
                    return
                if data.ndim == 3:
                    data = data[:, :, 0]
            elif file_ext == '.png':
                data, scale = read_png(current_file)
                if data is None:
                    return
            else:
                error_msg = self.texts[self.current_language]["unsupported_format"].format(ext=file_ext)
                QMessageBox.warning(self, self.texts[self.current_language]["error"], error_msg)
                return
            
            # 儲存當前圖片數據供鼠標追蹤使用
            self.current_data = data
            
            self.ax.clear()
            
            # 設定顯示參數
            filename = os.path.basename(current_file)
            
            if file_ext == '.pfm':
                min_val, max_val = find_min_max_no_inf(data)
                
                if min_val is not None:
                    visual_max = max_val
                    if filename.lower().startswith("depth"):
                        visual_max = max_val if max_val is not None and max_val < 150 else 150
                        data[~np.isfinite(data)] = visual_max
                        title = f'Depth - {filename} (範圍: {min_val:.3f} - {visual_max:.3f})'
                        cmap = 'jet'
                    elif filename.lower().startswith("disparity"):
                        data[~np.isfinite(data)] = 0
                        title = f'Disparity - {filename} (範圍: {min_val:.3f} - {visual_max:.3f})'
                        cmap = 'jet'
                    else:
                        title = f'{filename} (範圍: {min_val:.3f} - {visual_max:.3f})'
                        cmap = 'jet'
                else:
                    title = filename
                    cmap = 'jet'
                    visual_max = 1.0
            elif file_ext == '.png':
                title = f'{self.current_image_type} - {filename}'
                if data.ndim == 3:
                    cmap = None
                    visual_max = 255
                else:
                    cmap = 'gray'
                    visual_max = 255
            
            if cmap is None:
                # 彩色圖片，不設定 vmin/vmax
                self.im = self.ax.imshow(data)
            else:
                self.im = self.ax.imshow(data, cmap=cmap, vmin=0, vmax=visual_max)
            
            # 設定標題和標籤
            self.ax.set_title(title, fontsize=12)
            self.ax.set_xlabel('Pixel X')
            self.ax.set_ylabel('Pixel Y')
            
            self.status_label.setText(f"{filename} ({self.current_index + 1}/{len(self.image_files)})")
            
            self.canvas.draw()
            
        except Exception as e:
            QMessageBox.critical(self, self.texts[self.current_language]["error"], 
                               self.texts[self.current_language]["processing_error"].format(file=current_file, error=str(e)))
            
    def prev_image(self):
        """
        顯示上一張圖片
        """
        if not self.image_files:
            return
            
        if self.current_index > 0:
            self.current_index -= 1
            self.update_display()
            
    def next_image(self):
        """
        顯示下一張圖片
        """
        if not self.image_files:
            return
            
        if self.current_index < len(self.image_files) - 1:
            self.current_index += 1
            self.update_display()
            
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # 語言設定 - 從環境變數讀取，如果沒有則預設中文
        self.current_language = os.environ.get('AIRSIM_LANGUAGE', 'zh')
        self.texts = {
            "zh": {
                "title": "圖片檢視器",
                "image_type": "圖片類型:",
                "prev_image": "上一張 (A)",
                "next_image": "下一張 (D)",
                "type_switch": "類型切換: W/S",
                "no_files": "沒有檔案",
                "pixel_value": "像素值:",
                "no_files_found": "沒有找到 {type} 檔案",
                "error": "錯誤",
                "folder_not_found": "找不到資料夾: {folder}",
                "unknown_type": "未知的圖片類型: {type}",
                "unsupported_format": "不支援的檔案格式: {ext}",
                "processing_error": "處理檔案時發生錯誤:\n檔案: {file}\n錯誤: {error}",
                "language": "🌐 語言"
            },
            "en": {
                "title": "Image Viewer",
                "image_type": "Image Type:",
                "prev_image": "Previous (A)",
                "next_image": "Next (D)",
                "type_switch": "Type Switch: W/S",
                "no_files": "No Files",
                "pixel_value": "Pixel Value:",
                "no_files_found": "No {type} files found",
                "error": "Error",
                "folder_not_found": "Folder not found: {folder}",
                "unknown_type": "Unknown image type: {type}",
                "unsupported_format": "Unsupported file format: {ext}",
                "processing_error": "Error processing file:\nFile: {file}\nError: {error}",
                "language": "🌐 Language"
            }
        }
        
        self.setWindowTitle(self.texts[self.current_language]["title"])
        self.setGeometry(100, 100, 1200, 800)
        
        self.image_viewer = ImageViewerWidget()
        self.setCentralWidget(self.image_viewer)
        
        # 設定焦點策略，確保能接收鍵盤事件
        self.setFocusPolicy(Qt.StrongFocus)
        self.setFocus()
        
        # 添加語言切換按鈕
        self.add_language_button()

    def add_language_button(self):
        """添加語言切換按鈕到工具列"""
        # 創建語言切換按鈕
        self.language_btn = QPushButton(self.texts[self.current_language]["language"])
        self.language_btn.clicked.connect(self.toggle_language)
        
        # 將按鈕添加到圖片檢視器的工具列
        self.image_viewer.control_layout.addWidget(self.language_btn)

    def toggle_language(self):
        """切換語言"""
        if self.current_language == "zh":
            self.current_language = "en"
        else:
            self.current_language = "zh"
        
        # 更新視窗標題
        self.setWindowTitle(self.texts[self.current_language]["title"])
        
        # 更新語言按鈕文字
        self.language_btn.setText(self.texts[self.current_language]["language"])
        
        # 更新圖片檢視器的語言
        self.image_viewer.set_language(self.current_language)

    def keyPressEvent(self, event):
        """
        在 MainWindow 層級處理鍵盤事件，確保不被 ComboBox 攔截
        """
        if event.key() == Qt.Key_A or event.key() == Qt.Key_Left:
            self.image_viewer.prev_image()
        elif event.key() == Qt.Key_D or event.key() == Qt.Key_Right:
            self.image_viewer.next_image()
        elif event.key() == Qt.Key_W or event.key() == Qt.Key_Up:
            self.image_viewer.switch_image_type(-1)
        elif event.key() == Qt.Key_S or event.key() == Qt.Key_Down:
            self.image_viewer.switch_image_type(1)
        elif event.key() == Qt.Key_Q or event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()