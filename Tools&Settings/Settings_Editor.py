import sys
import os
import json
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QMessageBox, 
                             QSpinBox, QDoubleSpinBox, QGroupBox, QGridLayout)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

class SettingsEditor(QMainWindow):
    """设置编辑器 - 同步修改图片分辨率和 FOV 设置
    Settings Editor - Synchronize ee resolution and FOV settings"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("相機設定編輯器 / Camera Settings Editor")
        self.setGeometry(300, 300, 600, 600)
        self.setFixedSize(600, 600)
        
        # 文件路径
        self.settings_txt_path = "Tools&Settings/Settings.txt"
        self.airsim_json_path = "../settings.json"
        
        self.init_ui()
        self.load_current_settings()
        
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(25, 25, 25, 25)
        
        # 标题
        title_label = QLabel("📷 相機參數設定 / Camera Settings")
        title_label.setAlignment(Qt.AlignCenter)
        title_font = QFont("Arial", 14, QFont.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                margin: 5px;
                padding: 12px;
                background-color: #ecf0f1;
                border-radius: 8px;
                border: 2px solid #3498db;
                min-height: 30px;
            }
        """)
        layout.addWidget(title_label)
        
        # 设置输入区域
        settings_group = QGroupBox("影像解析度與視野設定 / Resolution & FOV Settings")
        settings_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 20px;
                border: 2px solid #95a5a6;
                border-radius: 8px;
                margin-top: 20px;
                padding: 10px 15px 15px 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 10px;
                padding: 10px 10px;
            }
        """)
        
        settings_layout = QGridLayout()
        settings_layout.setSpacing(20)
        settings_layout.setContentsMargins(15, 15, 15, 15)
        
        # 图片宽度
        width_label = QLabel("影像寬度 / Image Width (px):")
        width_label.setStyleSheet("font-size: 15px; font-weight: bold; min-height: 25px;")
        self.width_spinbox = QSpinBox()
        self.width_spinbox.setRange(320, 3840)
        self.width_spinbox.setSingleStep(10)
        self.width_spinbox.setValue(640)
        self.width_spinbox.setStyleSheet(self.get_spinbox_style())
        
        # 图片高度
        height_label = QLabel("影像高度 / Image Height (px):")
        height_label.setStyleSheet("font-size: 15px; font-weight: bold; min-height: 25px;")
        self.height_spinbox = QSpinBox()
        self.height_spinbox.setRange(240, 2160)
        self.height_spinbox.setSingleStep(10)
        self.height_spinbox.setValue(480)
        self.height_spinbox.setStyleSheet(self.get_spinbox_style())
        
        # FOV
        fov_label = QLabel("視野角度 / FOV (degrees):")
        fov_label.setStyleSheet("font-size: 15px; font-weight: bold; min-height: 25px;")
        self.fov_spinbox = QSpinBox()
        self.fov_spinbox.setRange(30, 120)
        self.fov_spinbox.setSingleStep(5)
        self.fov_spinbox.setValue(90)
        self.fov_spinbox.setStyleSheet(self.get_spinbox_style())
        
        # 基线距离
        baseline_label = QLabel("基線距離 / Baseline (meters):")
        baseline_label.setStyleSheet("font-size: 15px; font-weight: bold; min-height: 25px;")
        self.baseline_spinbox = QDoubleSpinBox()
        self.baseline_spinbox.setRange(0.01, 10.0)
        self.baseline_spinbox.setSingleStep(0.01)
        self.baseline_spinbox.setDecimals(2)
        self.baseline_spinbox.setValue(0.2)
        self.baseline_spinbox.setStyleSheet(self.get_spinbox_style())
        
        # 添加到布局
        settings_layout.addWidget(width_label, 0, 0)
        settings_layout.addWidget(self.width_spinbox, 0, 1)
        settings_layout.addWidget(height_label, 1, 0)
        settings_layout.addWidget(self.height_spinbox, 1, 1)
        settings_layout.addWidget(fov_label, 2, 0)
        settings_layout.addWidget(self.fov_spinbox, 2, 1)
        settings_layout.addWidget(baseline_label, 3, 0)
        settings_layout.addWidget(self.baseline_spinbox, 3, 1)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        layout.addStretch()
        
        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        
        save_btn = QPushButton("💾 保存設定 / Save Settings")
        save_btn.clicked.connect(self.save_settings)
        save_btn.setStyleSheet(self.get_button_style("#27ae60"))
        
        reset_btn = QPushButton("🔄 重新載入 / Reload")
        reset_btn.clicked.connect(self.load_current_settings)
        reset_btn.setStyleSheet(self.get_button_style("#3498db"))
        
        close_btn = QPushButton("❌ 關閉 / Close")
        close_btn.clicked.connect(self.close)
        close_btn.setStyleSheet(self.get_button_style("#e74c3c"))
        
        button_layout.addWidget(save_btn)
        button_layout.addWidget(reset_btn)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
    def get_spinbox_style(self):
        """SpinBox 样式"""
        return """
            QSpinBox, QDoubleSpinBox {
                padding: 5px 10px;
                font-size: 12px;
                font-weight: bold;
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                background-color: white;
                min-width: 180px;
                min-height: 18px;
            }
            QSpinBox:focus, QDoubleSpinBox:focus {
                border: 2px solid #3498db;
            }
        """
        
    def get_button_style(self, color):
        """按钮样式"""
        hover_color = {
            "#27ae60": "#229954",
            "#3498db": "#2980b9",
            "#e74c3c": "#c0392b"
        }
        
        return f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 10px;
                font-weight: bold;
                padding: 4px 10px;
                min-width: 150px;
                min-height: 40px;
            }}
            QPushButton:hover {{
                background-color: {hover_color.get(color, color)};
            }}
            QPushButton:pressed {{
                background-color: {hover_color.get(color, color)};
                padding: 15px 21px 13px 23px;
            }}
        """
    
    def load_current_settings(self):
        """读取当前设置 / Load current settings"""
        try:
            # 读取 Settings.txt
            if os.path.exists(self.settings_txt_path):
                with open(self.settings_txt_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith('image_width:'):
                            width = int(line.split(':')[1].strip())
                            self.width_spinbox.setValue(width)
                        elif line.startswith('image_height:'):
                            height = int(line.split(':')[1].strip())
                            self.height_spinbox.setValue(height)
                        elif line.startswith('FOV_degrees:'):
                            fov = int(line.split(':')[1].strip())
                            self.fov_spinbox.setValue(fov)
                        elif line.startswith('baseline_meters:'):
                            # 移除注释并获取数值
                            baseline_str = line.split(':')[1].split('#')[0].strip()
                            baseline = float(baseline_str)
                            self.baseline_spinbox.setValue(baseline)
                            
                print("✅ 已載入當前設定 / Current settings loaded")
            else:
                QMessageBox.warning(self, "警告 / Warning", 
                                  f"找不到 Settings.txt\nSettings.txt not found")
                
        except Exception as e:
            QMessageBox.critical(self, "錯誤 / Error", 
                               f"讀取設定失敗 / Failed to load settings:\n{str(e)}")
    
    def save_settings(self):
        """保存设置到两个文件 / Save settings to both files"""
        try:
            width = self.width_spinbox.value()
            height = self.height_spinbox.value()
            fov = self.fov_spinbox.value()
            baseline = self.baseline_spinbox.value()
            
            # 1. 更新 Settings.txt
            self.update_settings_txt(width, height, fov, baseline)
            
            # 2. 更新 AirSim settings.json
            self.update_airsim_json(width, height, fov)
            
            QMessageBox.information(self, "成功 / Success", 
                                  f"✅ 設定已保存！/ Settings saved!\n\n"
                                  f"解析度 / Resolution: {width} x {height}\n"
                                  f"視野角度 / FOV: {fov}°\n"
                                  f"基線距離 / Baseline: {baseline} m\n\n"
                                  f"已同步更新 / Synced to:\n"
                                  f"• Settings.txt\n"
                                  f"• AirSim settings.json")
            
        except Exception as e:
            QMessageBox.critical(self, "錯誤 / Error", 
                               f"保存設定失敗 / Failed to save settings:\n{str(e)}")
    
    def update_settings_txt(self, width, height, fov, baseline):
        """更新 Settings.txt / Update Settings.txt"""
        if not os.path.exists(self.settings_txt_path):
            raise FileNotFoundError(f"找不到文件 / File not found: {self.settings_txt_path}")
        
        # 读取所有行
        with open(self.settings_txt_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 更新对应的行
        updated_lines = []
        for line in lines:
            if line.strip().startswith('FOV_degrees:'):
                updated_lines.append(f'FOV_degrees:{fov}\n')
            elif line.strip().startswith('image_width:'):
                updated_lines.append(f'image_width:{width}\n')
            elif line.strip().startswith('image_height:'):
                updated_lines.append(f'image_height:{height}\n')
            elif line.strip().startswith('baseline_meters:'):
                updated_lines.append(f'baseline_meters:{baseline}  # 請根據你的相機配置修改此值\n')
            else:
                updated_lines.append(line)
        
        # 写回文件
        with open(self.settings_txt_path, 'w', encoding='utf-8') as f:
            f.writelines(updated_lines)
        
        print(f"✅ 已更新 Settings.txt / Updated Settings.txt")
    
    def update_airsim_json(self, width, height, fov):
        """更新 AirSim settings.json / Update AirSim settings.json"""
        if not os.path.exists(self.airsim_json_path):
            raise FileNotFoundError(f"找不到文件 / File not found: {self.airsim_json_path}")
        
        # 读取 JSON
        with open(self.airsim_json_path, 'r', encoding='utf-8') as f:
            settings = json.load(f)
        
        # 更新 CameraDefaults
        if "CameraDefaults" in settings and "CaptureSettings" in settings["CameraDefaults"]:
            for capture in settings["CameraDefaults"]["CaptureSettings"]:
                capture["Width"] = width
                capture["Height"] = height
                capture["FOV_Degrees"] = fov
        
        # 更新所有车辆类型的相机设置
        if "Vehicles" in settings:
            for vehicle_name, vehicle_config in settings["Vehicles"].items():
                # 检查每个车辆是否有 Cameras 配置
                if "Cameras" in vehicle_config:
                    for camera_name, camera_config in vehicle_config["Cameras"].items():
                        if "CaptureSettings" in camera_config:
                            for capture in camera_config["CaptureSettings"]:
                                capture["Width"] = width
                                capture["Height"] = height
                                capture["FOV_Degrees"] = fov
        
        # 写回 JSON (保持格式化)
        with open(self.airsim_json_path, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 已更新 AirSim settings.json / Updated AirSim settings.json")

def main():
    app = QApplication(sys.argv)
    
    app.setApplicationName("AirSim Settings Editor")
    app.setApplicationVersion("1.0")
    
    window = SettingsEditor()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()

