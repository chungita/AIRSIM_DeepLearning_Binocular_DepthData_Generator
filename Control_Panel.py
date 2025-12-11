import sys
import os
import subprocess
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QMessageBox, QGridLayout,
                             QTextEdit, QDialog)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon, QPainter, QColor

class ProcessWindow(QDialog):
    """流程顯示視窗 - 不在終端機顯示任何內容"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AirSim 資料處理流程")
        self.setGeometry(200, 200, 700, 500)
        self.setModal(False)  # 非模態視窗
        
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # 標題
        title_label = QLabel("🚀 AirSim 資料處理工具集")
        title_label.setAlignment(Qt.AlignCenter)
        title_font = QFont("Microsoft YaHei", 16, QFont.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                margin: 15px;
                padding: 10px;
                background-color: #ecf0f1;
                border-radius: 8px;
                border: 2px solid #3498db;
            }
        """)
        layout.addWidget(title_label)
        
        # 流程文字顯示區域
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
        
        # 底部按鈕區域
        button_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("🔄 重新整理")
        refresh_btn.clicked.connect(self.refresh_process_info)
        refresh_btn.setStyleSheet(self.get_button_style("#3498db"))
        
        clear_btn = QPushButton("🗑️ 清空日誌")
        clear_btn.clicked.connect(self.clear_log)
        clear_btn.setStyleSheet(self.get_button_style("#95a5a6"))
        
        close_btn = QPushButton("❌ 關閉")
        close_btn.clicked.connect(self.close)
        close_btn.setStyleSheet(self.get_button_style("#e74c3c"))
        
        button_layout.addWidget(refresh_btn)
        button_layout.addWidget(clear_btn)
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
        # 初始化顯示流程說明
        self.show_process_info()
        
    def get_button_style(self, color):
        """按鈕樣式"""
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
        """將顏色變暗"""
        if factor == 0.7:  # 更亮的邊框顏色
            color_map = {
                "#3498db": "#5dade2",
                "#95a5a6": "#aab7b8", 
                "#e74c3c": "#ec7063"
            }
        elif factor == 0.8:  # 按下時的顏色
            color_map = {
                "#3498db": "#2471a3",
                "#95a5a6": "#717d7e", 
                "#e74c3c": "#a93226"
            }
        else:  # 預設 hover 顏色
            color_map = {
                "#3498db": "#2980b9",
                "#95a5a6": "#7f8c8d", 
                "#e74c3c": "#c0392b"
            }
        return color_map.get(color, color)
        
    def show_process_info(self):
        """顯示處理流程資訊"""
        process_info = """
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
        self.process_text.setPlainText(process_info)
        
    def add_log(self, message):
        """添加日誌訊息（不顯示在終端機）"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        
        # 添加到文字區域的底部
        self.process_text.append(log_message)
        
        # 自動滾動到底部
        scrollbar = self.process_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
    def clear_log(self):
        """清空日誌並重新顯示流程資訊"""
        self.process_text.clear()
        self.show_process_info()
        
    def refresh_process_info(self):
        """重新整理流程資訊"""
        self.clear_log()
        self.add_log("🔄 流程資訊已重新整理")

class ProgramButton(QPushButton):
    """自定義程式按鈕，支援不同字體大小"""
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
        """自定義繪製事件"""
        try:
            super().paintEvent(event)
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            
            # 根據語言設定字體大小
            if self.language == "en":
                # 英文版：14px 粗體
                title_font = QFont("Arial", 14, QFont.Bold)
                desc_font = QFont("Arial", 8, QFont.Normal)
            else:
                # 中文版：18px 粗體
                title_font = QFont("Arial", 18, QFont.Bold)
                desc_font = QFont("Arial", 8, QFont.Normal)
            
            # 設定程式名稱字體
            painter.setFont(title_font)
            painter.setPen(QColor(255, 255, 255))
            
            # 繪製程式名稱
            title_rect = self.rect().adjusted(10, 10, -10, -40)
            painter.drawText(title_rect, Qt.AlignCenter, self.name)
            
            # 設定描述文字字體
            painter.setFont(desc_font)
            
            # 繪製描述文字
            if self.language == "en":
                # 英文版：分兩段顯示
                desc_rect1 = self.rect().adjusted(10, 45, -10, -25)
                desc_rect2 = self.rect().adjusted(10, 60, -10, -10)
                
                # 將描述文字分為兩段
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
                # 中文版：單行顯示
                desc_rect = self.rect().adjusted(10, 50, -10, -10)
                painter.drawText(desc_rect, Qt.AlignCenter, self.description)
                
        except Exception as e:
            print(f"繪製按鈕時發生錯誤: {e}")
            # 如果繪製失敗，使用預設文字顯示
            super().paintEvent(event)

class ControlPanel(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_language = "zh"  # 預設中文
        self.setWindowTitle("資料處理工具集")
        self.setGeometry(100, 100, 650, 700)
        self.setFixedSize(650, 700)  # 設定固定大小，無法調整
        
        # 多語言文字
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
        
        # 設定程式列表
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
        
        # 初始化流程視窗
        self.process_window = None
        
        self.init_ui()
        
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setAlignment(Qt.AlignCenter)
        
        # 標題
        self.title_label = QLabel(self.texts[self.current_language]["title"])
        self.title_label.setAlignment(Qt.AlignCenter)
        title_font = QFont("Arial", 20, QFont.Bold)
        self.title_label.setFont(title_font)
        self.title_label.setStyleSheet("color: #2c3e50; margin: 20px; font-weight: bold;")
        layout.addWidget(self.title_label)
        
        # 說明文字
        self.info_label = QLabel(self.texts[self.current_language]["select_tool"])
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setStyleSheet("color: #34495e; margin-bottom: 20px; font-size: 16px; font-weight: bold;")
        layout.addWidget(self.info_label)
        
        # 程式按鈕區域
        buttons_widget = QWidget()
        buttons_layout = QGridLayout(buttons_widget)
        buttons_layout.setSpacing(15)
        buttons_layout.setAlignment(Qt.AlignCenter)
        
        # 創建程式按鈕
        self.program_buttons = {}
        row = 0
        col = 0
        for name, info in self.programs[self.current_language].items():
            button = self.create_program_button(name, info)
            self.program_buttons[name] = button
            buttons_layout.addWidget(button, row, col)
            
            col += 1
            if col >= 2:  # 每行兩個按鈕
                col = 0
                row += 1
                
        layout.addWidget(buttons_widget)
        
        # 底部工具按鈕
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
        """創建程式啟動按鈕"""
        button = ProgramButton(name, info['description'], self.current_language)
        
        # 連接點擊事件
        button.clicked.connect(lambda: self.launch_program(name, info['file']))
        
        return button
        
    def get_program_button_style(self):
        """程式按鈕樣式"""
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
        """工具按鈕樣式"""
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
        """啟動指定程式"""
        try:
            if not os.path.exists(file_path):
                QMessageBox.critical(self, "錯誤", f"找不到程式檔案：{file_path}")
                return
                
            # 設定環境變數傳遞語言設定
            env = os.environ.copy()
            env['AIRSIM_LANGUAGE'] = self.current_language
            
            # 使用 subprocess 啟動程式
            if sys.platform == "win32":
                subprocess.Popen([sys.executable, file_path], 
                               creationflags=subprocess.CREATE_NO_WINDOW,
                               env=env)
            else:
                subprocess.Popen([sys.executable, file_path], env=env)
            
            # 記錄啟動事件到流程視窗（不在終端機顯示）
            if self.process_window:
                self.process_window.add_log(f"🚀 已啟動程式：{name}")
            
            # 移除成功提示對話框，改為靜默啟動
            
        except Exception as e:
            QMessageBox.critical(self, "啟動失敗", f"無法啟動 {name}：\n{str(e)}")
            
    def show_process_window(self):
        """顯示流程說明視窗（不在終端機顯示）"""
        try:
            if self.process_window is None:
                self.process_window = ProcessWindow(self)
            
            # 顯示視窗
            self.process_window.show()
            self.process_window.raise_()  # 提到最前面
            self.process_window.activateWindow()  # 激活視窗
            
            # 在流程視窗中記錄開啟事件（不在終端機顯示）
            self.process_window.add_log("📋 流程說明視窗已開啟")
            
        except Exception as e:
            # 只在有錯誤時顯示訊息框，不在終端機顯示
            QMessageBox.warning(self, "警告", f"無法開啟流程視窗：{str(e)}")
            
    def open_settings(self):
        """開啟設定編輯器 / Open Settings Editor"""
        try:
            settings_editor_path = "Tools&Settings/Settings_Editor.py"
            if not os.path.exists(settings_editor_path):
                QMessageBox.critical(self, "錯誤 / Error", 
                                   f"找不到設定編輯器 / Settings editor not found:\n{settings_editor_path}")
                return
                
            # 設定環境變數傳遞語言設定
            env = os.environ.copy()
            env['AIRSIM_LANGUAGE'] = self.current_language
            
            # 使用 subprocess 啟動設定編輯器
            if sys.platform == "win32":
                subprocess.Popen([sys.executable, settings_editor_path], 
                               creationflags=subprocess.CREATE_NO_WINDOW,
                               env=env)
            else:
                subprocess.Popen([sys.executable, settings_editor_path], env=env)
            
            # 記錄啟動事件到流程視窗
            if self.process_window:
                self.process_window.add_log("⚙️ 已啟動設定編輯器 / Settings editor launched")
            
        except Exception as e:
            QMessageBox.critical(self, "錯誤 / Error", 
                               f"無法啟動設定編輯器 / Failed to launch settings editor:\n{str(e)}")
            
    def open_folder(self):
        """開啟當前資料夾"""
        try:
            current_dir = os.getcwd()
            if sys.platform == "win32":
                os.startfile(current_dir)
            else:
                subprocess.Popen(["xdg-open", current_dir])
        except Exception as e:
            QMessageBox.critical(self, "錯誤", f"無法開啟資料夾：\n{str(e)}")
    
    def toggle_language(self):
        """切換語言"""
        # 切換語言
        if self.current_language == "zh":
            self.current_language = "en"
        else:
            self.current_language = "zh"
        
        # 更新界面文字
        self.setWindowTitle(self.texts[self.current_language]["title"])
        self.title_label.setText(self.texts[self.current_language]["title"])
        self.info_label.setText(self.texts[self.current_language]["select_tool"])
        
        # 更新按鈕文字
        self.process_btn.setText(self.texts[self.current_language]["process_guide"])
        self.settings_btn.setText(self.texts[self.current_language]["edit_settings"])
        self.folder_btn.setText(self.texts[self.current_language]["open_folder"])
        self.language_btn.setText(self.texts[self.current_language]["language"])
        
        # 重新創建程式按鈕
        self.recreate_program_buttons()
    
    def recreate_program_buttons(self):
        """重新創建程式按鈕"""
        # 清除現有按鈕
        for button in self.program_buttons.values():
            button.deleteLater()
        self.program_buttons.clear()
        
        # 找到按鈕區域的布局
        central_widget = self.centralWidget()
        if central_widget:
            main_layout = central_widget.layout()
            if main_layout:
                # 找到按鈕區域的 widget
                for i in range(main_layout.count()):
                    item = main_layout.itemAt(i)
                    if item and item.widget():
                        widget = item.widget()
                        if hasattr(widget, 'layout') and widget.layout():
                            buttons_layout = widget.layout()
                            if isinstance(buttons_layout, QGridLayout):
                                # 清除布局
                                while buttons_layout.count():
                                    child = buttons_layout.takeAt(0)
                                    if child.widget():
                                        child.widget().deleteLater()
                                
                                # 重新添加按鈕
                                row = 0
                                col = 0
                                for name, info in self.programs[self.current_language].items():
                                    button = ProgramButton(name, info['description'], self.current_language)
                                    button.clicked.connect(lambda checked, n=name, f=info['file']: self.launch_program(n, f))
                                    self.program_buttons[name] = button
                                    buttons_layout.addWidget(button, row, col)
                                    
                                    col += 1
                                    if col >= 2:  # 每行兩個按鈕
                                        col = 0
                                        row += 1
                                break

def main():
    app = QApplication(sys.argv)
    
    # 設定應用程式屬性
    app.setApplicationName("AirSim 控制面板")
    app.setApplicationVersion("1.0")
    
    window = ControlPanel()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
