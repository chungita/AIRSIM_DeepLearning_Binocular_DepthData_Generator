import sys
import os
import subprocess
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QMessageBox, QGridLayout,
                             QTextEdit, QDialog)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon, QPainter, QColor

class ProcessWindow(QDialog):
    """Process display window - no console output"""
    def __init__(self, parent=None, language="zh"):
        super().__init__(parent)
        self.language = language
        
        # Multi-language window titles
        self.titles = {
            "zh": "AirSim 資料處理流程",
            "en": "AirSim Data Processing Workflow"
        }
        
        self.setWindowTitle(self.titles[self.language])
        self.setGeometry(200, 200, 700, 500)
        self.setModal(False)  # Non-modal window
        
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Multi-language titles
        self.label_titles = {
            "zh": "🚀 AirSim 資料處理工具集",
            "en": "🚀 AirSim Data Processing Toolkit"
        }
        
        # Title
        self.title_label = QLabel(self.label_titles[self.language])
        self.title_label.setAlignment(Qt.AlignCenter)
        title_font = QFont("Microsoft YaHei", 16, QFont.Bold)
        self.title_label.setFont(title_font)
        self.title_label.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                margin: 15px;
                padding: 10px;
                background-color: #ecf0f1;
                border-radius: 8px;
                border: 2px solid #3498db;
            }
        """)
        layout.addWidget(self.title_label)
        
        # Process text display area
        self.process_text = QTextEdit()
        self.process_text.setReadOnly(True)
        self.process_text.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                font-family: 'Microsoft YaHei', 'Consolas', monospace;
                font-size: 12px;
                padding: 15px;
                line-height: 1.6;
            }
        """)
        layout.addWidget(self.process_text)
        
        # Bottom button area
        button_layout = QHBoxLayout()
        
        # Multi-language button texts
        self.button_texts = {
            "zh": {
                "refresh": "🔄 重新整理",
                "clear": "🗑️ 清空日誌",
                "close": "❌ 關閉"
            },
            "en": {
                "refresh": "🔄 Refresh",
                "clear": "🗑️ Clear Log",
                "close": "❌ Close"
            }
        }
        
        self.refresh_btn = QPushButton(self.button_texts[self.language]["refresh"])
        self.refresh_btn.clicked.connect(self.refresh_process_info)
        self.refresh_btn.setStyleSheet(self.get_button_style("#3498db"))
        
        self.clear_btn = QPushButton(self.button_texts[self.language]["clear"])
        self.clear_btn.clicked.connect(self.clear_log)
        self.clear_btn.setStyleSheet(self.get_button_style("#95a5a6"))
        
        self.close_btn = QPushButton(self.button_texts[self.language]["close"])
        self.close_btn.clicked.connect(self.close)
        self.close_btn.setStyleSheet(self.get_button_style("#e74c3c"))
        
        button_layout.addWidget(self.refresh_btn)
        button_layout.addWidget(self.clear_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.close_btn)
        
        layout.addLayout(button_layout)
        
        # Initialize and display process guide
        self.show_process_info()
    
    def update_language(self, language):
        """Update window language"""
        self.language = language
        self.setWindowTitle(self.titles[self.language])
        self.title_label.setText(self.label_titles[self.language])
        self.refresh_btn.setText(self.button_texts[self.language]["refresh"])
        self.clear_btn.setText(self.button_texts[self.language]["clear"])
        self.close_btn.setText(self.button_texts[self.language]["close"])
        self.show_process_info()
        
    def get_button_style(self, color):
        """Button style"""
        return f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 11px;
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
        """
        
    def darken_color(self, color, factor=0.85):
        """Darken color"""
        if factor == 0.7:  # Brighter border color
            color_map = {
                "#3498db": "#5dade2",
                "#95a5a6": "#aab7b8", 
                "#e74c3c": "#ec7063"
            }
        elif factor == 0.8:  # Color when pressed
            color_map = {
                "#3498db": "#2471a3",
                "#95a5a6": "#717d7e", 
                "#e74c3c": "#a93226"
            }
        else:  # Default hover color
            color_map = {
                "#3498db": "#2980b9",
                "#95a5a6": "#7f8c8d", 
                "#e74c3c": "#c0392b"
            }
        return color_map.get(color, color)
        
    def show_process_info(self):
        """Display process flow information"""
        process_info_zh = """
═══════════════════════════════════════════════════════════════════════════════════

🎯 AirSim 資料處理完整流程指南

═══════════════════════════════════════════════════════════════════════════════════

📋 處理步驟概覽：

┌────────────────────────────────────────────────────────────────────────────────┐
│ 1️⃣ 資料生成器 (DataGenerator.py)                                                │
│    ├─ 🔄 處理 AirSim 原始資料                                                   │
│    ├─ 🖼️ 生成深度圖 (DepthGT_*.pfm)                                            │
│    ├─ 📊 生成視差圖 (Disparity_*.pfm)                                           │
│    ├─ 📁 整理左右相機圖片 (Img0_*, Img1_*)                                      │
│    ├─ 🎨 處理語意分割圖 (Seg_*)                                                 │
│    └─ 📤 複製結果到輸出資料夾                                                    │
│                                                                                │
│ 2️⃣ 圖片標註工具 (Img_Labeler.py)                                               │
│    ├─ ✏️ 人工標註模式：手動繪製邊界框                                            │
│    ├─ 🤖 批量標註模式：基於顏色自動偵測                                          │
│    ├─ 📝 生成 YOLO 格式標籤檔案                                                 │
│    ├─ 🎯 生成 MOT 格式標籤（含 3D 座標）                                         │
│    └─ 💾 儲存標註結果和統計資訊                                                  │
│                                                                                │
│ 3️⃣ 檢視與驗證工具                                                               │
│    ├─ 🔍 圖片檢視器 (PIC_Read.py)：查看各類圖片                                 │
│    ├─ 🏷️ 標籤檢視器 (Label_Show.py)：驗證標註結果                               │
│    └─ 📈 軌跡追蹤 (Track.py)：顯示物體移動軌跡                                  │
│                                                                                │
│ 4️⃣ 輸出與展示                                                                   │
│    └─ 🎬 GIF 生成器 (gifer.py)：製作動畫展示                                    │
└────────────────────────────────────────────────────────────────────────────────┘

🔧 建議處理順序：

1. 📂 準備原始資料：將 AirSim 資料放入 RawData 資料夾
2. ⚙️ 檢查設定檔：確認 Settings.txt 中的參數設定
3. 🚀 執行資料生成器：處理原始資料並生成深度/視差圖
4. 🎨 執行圖片標註：手動或自動標註物體
5. ✅ 檢視驗證結果：使用各種檢視工具確認品質
6. 📊 生成最終輸出：匯出標籤和製作展示動畫

📁 重要資料夾結構：

• RawData/           ← 原始 AirSim 資料
• ProcessData/       ← 處理後的圖片和深度資料  
• Results/
  ├─ Img/           ← 最終圖片輸出
  ├─ YOLO_Label/    ← YOLO 格式標籤檔案
  └─ MOT_Label/     ← MOT 格式標籤檔案

⚙️ 重要設定檔案：

• Settings.txt       ← 主要設定檔（相機參數、路徑等）
• predefined_classes.txt ← 預定義的物體類別

💡 使用小技巧：

• 深度圖顯示異常時，檢查 MaxDepth 設定
• 標註效果不佳時，調整顏色閾值參數  
• 批量處理前，先用小範圍測試
• 定期備份重要的標註結果

═══════════════════════════════════════════════════════════════════════════════════

✨ 系統狀態：準備就緒，可以開始處理！

═══════════════════════════════════════════════════════════════════════════════════
        """
        
        process_info_en = """
═══════════════════════════════════════════════════════════════════════════════════

🎯 AirSim Data Processing Complete Workflow Guide

═══════════════════════════════════════════════════════════════════════════════════

📋 Processing Steps Overview:

┌────────────────────────────────────────────────────────────────────────────────┐
│ 1️⃣ Data Generator (DataGenerator.py)                                            │
│    ├─ 🔄 Process AirSim raw data                                               │
│    ├─ 🖼️ Generate depth maps (DepthGT_*.pfm)                                   │
│    ├─ 📊 Generate disparity maps (Disparity_*.pfm)                             │
│    ├─ 📁 Organize left/right camera images (Img0_*, Img1_*)                    │
│    ├─ 🎨 Process semantic segmentation images (Seg_*)                          │
│    └─ 📤 Copy results to output folder                                         │
│                                                                                │
│ 2️⃣ Image Labeler (Img_Labeler.py)                                              │
│    ├─ ✏️ Manual annotation mode: draw bounding boxes manually                  │
│    ├─ 🤖 Batch annotation mode: automatic color-based detection               │
│    ├─ 📝 Generate YOLO format label files                                      │
│    ├─ 🎯 Generate MOT format labels (with 3D coordinates)                      │
│    └─ 💾 Save annotation results and statistics                                │
│                                                                                │
│ 3️⃣ View & Verification Tools                                                    │
│    ├─ 🔍 Image Viewer (PIC_Read.py): view various image types                 │
│    ├─ 🏷️ Label Viewer (Label_Show.py): verify annotation results              │
│    └─ 📈 Track Analyzer (Track.py): display object trajectories               │
│                                                                                │
│ 4️⃣ Output & Presentation                                                        │
│    └─ 🎬 GIF Generator (gifer.py): create animation demos                     │
└────────────────────────────────────────────────────────────────────────────────┘

🔧 Recommended Processing Order:

1. 📂 Prepare raw data: Place AirSim data in RawData folder
2. ⚙️ Check settings: Verify parameters in Settings.txt
3. 🚀 Run data generator: Process raw data and generate depth/disparity maps
4. 🎨 Run image labeler: Manually or automatically annotate objects
5. ✅ View verification results: Use various viewers to confirm quality
6. 📊 Generate final output: Export labels and create demo animations

📁 Important Folder Structure:

• RawData/           ← Raw AirSim data
• ProcessData/       ← Processed images and depth data
• Results/
  ├─ Img/           ← Final image output
  ├─ YOLO_Label/    ← YOLO format label files
  └─ MOT_Label/     ← MOT format label files

⚙️ Important Configuration Files:

• Settings.txt       ← Main settings (camera parameters, paths, etc.)
• predefined_classes.txt ← Predefined object classes

💡 Usage Tips:

• If depth map display is abnormal, check MaxDepth setting
• If annotation results are poor, adjust color threshold parameters
• Test with small range before batch processing
• Regularly backup important annotation results

═══════════════════════════════════════════════════════════════════════════════════

✨ System Status: Ready to start processing!

═══════════════════════════════════════════════════════════════════════════════════
        """
        
        process_info = process_info_zh if self.language == "zh" else process_info_en
        self.process_text.setPlainText(process_info)
        
    def add_log(self, message):
        """Add log message (no console output)"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        
        # Add to bottom of text area
        self.process_text.append(log_message)
        
        # Auto-scroll to bottom
        scrollbar = self.process_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
    def clear_log(self):
        """Clear log and redisplay process information"""
        self.process_text.clear()
        self.show_process_info()
        
    def refresh_process_info(self):
        """Refresh process information"""
        self.clear_log()
        refresh_msg = "🔄 流程資訊已重新整理" if self.language == "zh" else "🔄 Process information refreshed"
        self.add_log(refresh_msg)

class ProgramButton(QPushButton):
    """Custom program button with different font sizes"""
    def __init__(self, name, description, language="zh", parent=None):
        super().__init__(parent)
        self.name = name
        self.description = description
        self.language = language
        self.setFixedSize(250, 100)
        self.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 10px;
                text-align: center;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #2980b9;
                border: 2px solid #1f4e79;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
        """)
    
    def paintEvent(self, event):
        """Custom paint event"""
        try:
            super().paintEvent(event)
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            
            # Set font size based on language
            if self.language == "en":
                # English version: 14px bold
                title_font = QFont("Arial", 14, QFont.Bold)
                desc_font = QFont("Arial", 8, QFont.Normal)
            else:
                # Chinese version: 18px bold
                title_font = QFont("Arial", 18, QFont.Bold)
                desc_font = QFont("Arial", 8, QFont.Normal)
            
            # Set program name font
            painter.setFont(title_font)
            painter.setPen(QColor(255, 255, 255))
            
            # Draw program name
            title_rect = self.rect().adjusted(10, 10, -10, -40)
            painter.drawText(title_rect, Qt.AlignCenter, self.name)
            
            # Set description text font
            painter.setFont(desc_font)
            
            # Draw description text
            if self.language == "en":
                # English version: display in two lines
                desc_rect1 = self.rect().adjusted(10, 45, -10, -25)
                desc_rect2 = self.rect().adjusted(10, 60, -10, -10)
                
                # Split description into two lines
                words = self.description.split()
                if len(words) > 5:
                    mid = len(words) // 2
                    line1 = " ".join(words[:mid])
                    line2 = " ".join(words[mid:])
                    painter.drawText(desc_rect1, Qt.AlignCenter, line1)
                    painter.drawText(desc_rect2, Qt.AlignCenter, line2)
                else:
                    painter.drawText(desc_rect1, Qt.AlignCenter, self.description)
            else:
                # Chinese version: single line display
                desc_rect = self.rect().adjusted(10, 50, -10, -10)
                painter.drawText(desc_rect, Qt.AlignCenter, self.description)
                
        except Exception as e:
            print(f"Error drawing button: {e}")
            # If drawing fails, use default text display
            super().paintEvent(event)

class ControlPanel(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_language = "zh"  # Default Chinese
        self.setWindowTitle("資料處理工具集")
        self.setGeometry(100, 100, 650, 700)
        self.setFixedSize(650, 700)  # Set fixed size, cannot be resized
        
        # Multi-language text
        self.texts = {
            "zh": {
                "title": "資料處理工具集",
                "select_tool": "選擇要啟動的工具：",
                "process_info": "📊 處理資訊",
                "process_guide": "📋 流程說明",
                "edit_settings": "📝 編輯設定",
                "open_folder": "📁 開啟資料夾",
                "exit": "❌ 退出",
                "language": "🌐 語言",
                "programs": {
                    "資料生成器": {"description": "處理 AirSim 原始資料"},
                    "圖片標註工具": {"description": "標註圖片，生成格式標籤"},
                    "圖片檢視器": {"description": "檢視深度圖、視差圖和原始圖片"},
                    "標籤檢視器": {"description": "檢視和驗證標註結果"},
                    "軌跡追蹤": {"description": "顯示物體軌跡和追蹤結果"},
                    "GIF 生成器": {"description": "將圖片序列製作成 GIF 動畫"},
                    "影片轉換器": {"description": "將圖片序列轉換為影片檔案"}
                }
            },
            "en": {
                "title": "Airsim Data Toolkit",
                "select_tool": "Select a tool to launch:",
                "process_info": "📊 Process Info",
                "process_guide": "📋 Process Guide",
                "edit_settings": "📝 Edit Settings",
                "open_folder": "📁 Open Folder",
                "exit": "❌ Exit",
                "language": "🌐 Language",
                "programs": {
                    "Data Generator": {"description": "Process AirSim raw data"},
                    "Image Labeler": {"description": "Label images and generate YOLO and MOT format labels"},
                    "Image Viewer": {"description": "View depth maps, disparity maps and original images"},
                    "Label Viewer": {"description": "View and verify labeling results"},
                    "Track Analyzer": {"description": "Display object trajectories and tracking results"},
                    "GIF Generator": {"description": "Create GIF animations from image sequences"},
                    "Video Converter": {"description": "Convert image sequences to video files"}
                }
            }
        }
        
        # Set program list
        self.programs = {
            "zh": {
                "資料生成器": {
                    "file": "Tools&Settings/DataGenerator.py",
                    "description": "處理 AirSim 原始資料"
                },
                "圖片標註工具": {
                    "file": "Tools&Settings/Img_Labeler.py", 
                    "description": "標註圖片，生成格式標籤"
                },
                "圖片檢視器": {
                    "file": "Tools&Settings/PIC_Read.py",
                    "description": "檢視深度圖、視差圖和原始圖片"
                },
                "標籤檢視器": {
                    "file": "Tools&Settings/Label_Show.py",
                    "description": "檢視和驗證標註結果"
                },
                "軌跡追蹤": {
                    "file": "Tools&Settings/Track.py",
                    "description": "顯示物體軌跡和追蹤結果"
                },
                "GIF 生成器": {
                    "file": "Tools&Settings/gifer.py",
                    "description": "將圖片序列製作成 GIF 動畫"
                },
                "影片轉換器": {
                    "file": "Tools&Settings/Video_Convertor.py",
                    "description": "將圖片序列轉換為影片檔案"
                }
            },
            "en": {
                "Data Generator": {
                    "file": "Tools&Settings/DataGenerator.py",
                    "description": "Process AirSim raw data"
                },
                "Image Labeler": {
                    "file": "Tools&Settings/Img_Labeler.py", 
                    "description": "Label images and generate YOLO and MOT format labels"
                },
                "Image Viewer": {
                    "file": "Tools&Settings/PIC_Read.py",
                    "description": "View depth maps, disparity maps and original images"
                },
                "Label Viewer": {
                    "file": "Tools&Settings/Label_Show.py",
                    "description": "View and verify labeling results"
                },
                "Track Analyzer": {
                    "file": "Tools&Settings/Track.py",
                    "description": "Display object trajectories and tracking results"
                },
                "GIF Generator": {
                    "file": "Tools&Settings/gifer.py",
                    "description": "Create GIF animations from image sequences"
                },
                "Video Converter": {
                    "file": "Tools&Settings/Video_Convertor.py",
                    "description": "Convert image sequences to video files"
                }
            }
        }
        
        # Initialize process window
        self.process_window = None
        
        self.init_ui()
        
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setAlignment(Qt.AlignCenter)
        
        # Title
        self.title_label = QLabel(self.texts[self.current_language]["title"])
        self.title_label.setAlignment(Qt.AlignCenter)
        title_font = QFont("Arial", 20, QFont.Bold)
        self.title_label.setFont(title_font)
        self.title_label.setStyleSheet("color: #2c3e50; margin: 20px; font-weight: bold;")
        layout.addWidget(self.title_label)
        
        # Instruction text
        self.info_label = QLabel(self.texts[self.current_language]["select_tool"])
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setStyleSheet("color: #34495e; margin-bottom: 20px; font-size: 16px; font-weight: bold;")
        layout.addWidget(self.info_label)
        
        # Program button area
        buttons_widget = QWidget()
        buttons_layout = QGridLayout(buttons_widget)
        buttons_layout.setSpacing(15)
        buttons_layout.setAlignment(Qt.AlignCenter)
        
        # Create program buttons
        self.program_buttons = {}
        row = 0
        col = 0
        for name, info in self.programs[self.current_language].items():
            button = self.create_program_button(name, info)
            self.program_buttons[name] = button
            buttons_layout.addWidget(button, row, col)
            
            col += 1
            if col >= 2:  # Two buttons per row
                col = 0
                row += 1
                
        layout.addWidget(buttons_widget)
        
        # Bottom tool buttons
        bottom_layout = QHBoxLayout()
        bottom_layout.setAlignment(Qt.AlignCenter)
        
        self.process_btn = QPushButton(self.texts[self.current_language]["process_guide"])
        self.process_btn.clicked.connect(self.show_process_window)
        self.process_btn.setStyleSheet(self.get_tool_button_style())
        
        self.settings_btn = QPushButton(self.texts[self.current_language]["edit_settings"])
        self.settings_btn.clicked.connect(self.open_settings)
        self.settings_btn.setStyleSheet(self.get_tool_button_style())
        
        self.folder_btn = QPushButton(self.texts[self.current_language]["open_folder"])
        self.folder_btn.clicked.connect(self.open_folder)
        self.folder_btn.setStyleSheet(self.get_tool_button_style())
        
        self.language_btn = QPushButton(self.texts[self.current_language]["language"])
        self.language_btn.clicked.connect(self.toggle_language)
        self.language_btn.setStyleSheet(self.get_tool_button_style())
        
        bottom_layout.addWidget(self.process_btn)
        bottom_layout.addWidget(self.settings_btn)
        bottom_layout.addWidget(self.folder_btn)
        bottom_layout.addWidget(self.language_btn)
        
        layout.addLayout(bottom_layout)
        layout.addStretch()
        
    def create_program_button(self, name, info):
        """Create program launch button"""
        button = ProgramButton(name, info['description'], self.current_language)
        
        # Connect click event
        button.clicked.connect(lambda: self.launch_program(name, info['file']))
        
        return button
        
    def get_program_button_style(self):
        """Program button style"""
        return """
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 10px;
                text-align: center;
                padding: 10px;
                font-size: 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
                border: 2px solid #1f4e79;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
        """
        
    def get_tool_button_style(self):
        """Tool button style"""
        return """
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 13px;
                font-weight: bold;
                padding: 8px 15px;
                min-width: 120px;
                min-height: 18px;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """
        
        
    def launch_program(self, name, file_path):
        """Launch specified program"""
        try:
            if not os.path.exists(file_path):
                QMessageBox.critical(self, "錯誤", f"找不到程式檔案：{file_path}")
                return
                
            # Set environment variable to pass language setting
            env = os.environ.copy()
            env['AIRSIM_LANGUAGE'] = self.current_language
            
            # Launch program using subprocess
            if sys.platform == "win32":
                subprocess.Popen([sys.executable, file_path], 
                               creationflags=subprocess.CREATE_NO_WINDOW,
                               env=env)
            else:
                subprocess.Popen([sys.executable, file_path], env=env)
            
            # Log launch event to process window (no console output)
            if self.process_window:
                self.process_window.add_log(f"🚀 已啟動程式：{name}")
            
            # Remove success dialog, use silent launch instead
            
        except Exception as e:
            QMessageBox.critical(self, "啟動失敗", f"無法啟動 {name}：\n{str(e)}")
            
    def show_process_window(self):
        """Display process guide window (no console output)"""
        try:
            if self.process_window is None:
                self.process_window = ProcessWindow(self, self.current_language)
            else:
                # Update language if window already exists
                self.process_window.update_language(self.current_language)
            
            # Show window
            self.process_window.show()
            self.process_window.raise_()  # Bring to front
            self.process_window.activateWindow()  # Activate window
            
            # Log open event in process window (no console output)
            self.process_window.add_log("📋 流程說明視窗已開啟")
            
        except Exception as e:
            # Only show message box on error, no console output
            QMessageBox.warning(self, "警告", f"無法開啟流程視窗：{str(e)}")
            
    def open_settings(self):
        """開啟設定編輯器 / Open Settings Editor"""
        try:
            settings_editor_path = "Tools&Settings/Settings_Editor.py"
            if not os.path.exists(settings_editor_path):
                QMessageBox.critical(self, "錯誤 / Error", 
                                   f"找不到設定編輯器 / Settings editor not found:\n{settings_editor_path}")
                return
                
            # Set environment variable to pass language setting
            env = os.environ.copy()
            env['AIRSIM_LANGUAGE'] = self.current_language
            
            # Launch settings editor using subprocess
            if sys.platform == "win32":
                subprocess.Popen([sys.executable, settings_editor_path], 
                               creationflags=subprocess.CREATE_NO_WINDOW,
                               env=env)
            else:
                subprocess.Popen([sys.executable, settings_editor_path], env=env)
            
            # Log launch event to process window
            if self.process_window:
                self.process_window.add_log("⚙️ 已啟動設定編輯器 / Settings editor launched")
            
        except Exception as e:
            QMessageBox.critical(self, "錯誤 / Error", 
                               f"無法啟動設定編輯器 / Failed to launch settings editor:\n{str(e)}")
            
    def open_folder(self):
        """Open current folder"""
        try:
            current_dir = os.getcwd()
            if sys.platform == "win32":
                os.startfile(current_dir)
            else:
                subprocess.Popen(["xdg-open", current_dir])
        except Exception as e:
            QMessageBox.critical(self, "錯誤", f"無法開啟資料夾：\n{str(e)}")
    
    def toggle_language(self):
        """Toggle language"""
        # Toggle language
        if self.current_language == "zh":
            self.current_language = "en"
        else:
            self.current_language = "zh"
        
        # Update UI text
        self.setWindowTitle(self.texts[self.current_language]["title"])
        self.title_label.setText(self.texts[self.current_language]["title"])
        self.info_label.setText(self.texts[self.current_language]["select_tool"])
        
        # Update button text
        self.process_btn.setText(self.texts[self.current_language]["process_guide"])
        self.settings_btn.setText(self.texts[self.current_language]["edit_settings"])
        self.folder_btn.setText(self.texts[self.current_language]["open_folder"])
        self.language_btn.setText(self.texts[self.current_language]["language"])
        
        # Recreate program buttons
        self.recreate_program_buttons()
        
        # Update process window language if it exists
        if self.process_window is not None:
            self.process_window.update_language(self.current_language)
    
    def recreate_program_buttons(self):
        """Recreate program buttons"""
        # Clear existing buttons
        for button in self.program_buttons.values():
            button.deleteLater()
        self.program_buttons.clear()
        
        # Find button area layout
        central_widget = self.centralWidget()
        if central_widget:
            main_layout = central_widget.layout()
            if main_layout:
                # Find button area widget
                for i in range(main_layout.count()):
                    item = main_layout.itemAt(i)
                    if item and item.widget():
                        widget = item.widget()
                        if hasattr(widget, 'layout') and widget.layout():
                            buttons_layout = widget.layout()
                            if isinstance(buttons_layout, QGridLayout):
                                # Clear layout
                                while buttons_layout.count():
                                    child = buttons_layout.takeAt(0)
                                    if child.widget():
                                        child.widget().deleteLater()
                                
                                # Re-add buttons
                                row = 0
                                col = 0
                                for name, info in self.programs[self.current_language].items():
                                    button = ProgramButton(name, info['description'], self.current_language)
                                    button.clicked.connect(lambda checked, n=name, f=info['file']: self.launch_program(n, f))
                                    self.program_buttons[name] = button
                                    buttons_layout.addWidget(button, row, col)
                                    
                                    col += 1
                                    if col >= 2:  # Two buttons per row
                                        col = 0
                                        row += 1
                                break

def main():
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("AirSim 控制面板")
    app.setApplicationVersion("1.0")
    
    window = ControlPanel()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
