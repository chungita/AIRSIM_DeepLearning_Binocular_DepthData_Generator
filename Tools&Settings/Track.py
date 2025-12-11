import sys
import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QComboBox, QTextEdit, QMessageBox,
                             QSpinBox, QCheckBox, QGroupBox, QGridLayout, QSlider, QDoubleSpinBox, QFileDialog)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QKeySequence
import glob
import re
from collections import defaultdict

# 設定matplotlib中文字體
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

def load_settings():
    """載入設定檔"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    settings_file = os.path.join(script_dir, "Settings.txt")
    
    settings = {}
    if os.path.exists(settings_file):
        with open(settings_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if ':' in line and not line.startswith('#'):
                    key, value = line.split(':', 1)
                    settings[key.strip()] = value.strip()
    return settings

def read_mot_labels(mot_file_path):
    """
    從 MOT 格式檔案讀取標籤
    格式：frame_id, track_id, xmin, ymin, w, h, conf, x_cam, y_cam, z
    """
    tracks = defaultdict(list)
    if not os.path.exists(mot_file_path):
        return tracks
    
    with open(mot_file_path, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split(',')
            if len(parts) >= 10:
                try:
                    frame_id = int(parts[0])
                    track_id = int(parts[1])
                    x_cam = float(parts[7])
                    y_cam = float(parts[8])
                    z = float(parts[9])
                    
                    tracks[track_id].append({
                        'frame_id': frame_id,
                        'x_cam': x_cam,
                        'y_cam': y_cam,
                        'z': z
                    })
                except (ValueError, IndexError):
                    continue
    
    for track_id in tracks:
        tracks[track_id].sort(key=lambda x: x['frame_id'])
    
    return tracks

class TrackViewer(QWidget):
    def __init__(self):
        super().__init__()
        
        # 語言設定 - 從環境變數讀取，如果沒有則預設中文
        self.current_language = os.environ.get('AIRSIM_LANGUAGE', 'zh')
        self.texts = {
            "zh": {
                "title": "MOT 軌跡追蹤工具",
                "fps_label": "播放速度 (FPS):",
                "play": "播放",
                "pause": "暫停",
                "stop": "停止",
                "current_frame": "當前幀:",
                "shortcut_hint": "(A/D鍵切換幀)",
                "limit_frame_range": "限制幀範圍",
                "start_frame": "開始幀:",
                "end_frame": "結束幀:",
                "reset_range": "重置範圍",
                "auto_scale": "自動縮放",
                "x_axis": "X軸:",
                "y_axis": "Y軸:",
                "z_axis": "Z軸:",
                "mot_file": "MOT檔案:",
                "track_id": "軌跡ID:",
                "show_3d": "3D顯示",
                "show_2d": "2D顯示",
                "projection": "2D投影:",
                "xy_plane": "XY平面",
                "xz_plane": "XZ平面",
                "yz_plane": "YZ平面",
                "track_info": "軌跡資訊",
                "stats_info": "統計資訊",
                "language": "🌐 語言",
                "warning": "警告",
                "folder_not_found": "MOT標籤資料夾不存在: {folder}",
                "no_txt_files": "MOT標籤資料夾中沒有找到.txt檔案: {folder}",
                "track_id_label": "軌跡ID: {id}",
                "total_frames": "總幀數: {count}",
                "start_frame_label": "起始幀: {frame}",
                "end_frame_label": "結束幀: {frame}",
                "total_distance": "總移動距離: {distance:.2f}m",
                "start_position": "起始位置: ({x:.2f}, {y:.2f}, {z:.2f})",
                "end_position": "結束位置: ({x:.2f}, {y:.2f}, {z:.2f})",
                "total_tracks": "總軌跡數: {count}",
                "total_frames_stats": "總幀數: {count}",
                "avg_track_length": "平均軌跡長度: {length:.1f}幀",
                "max_track_length": "最長軌跡: {length}幀",
                "min_track_length": "最短軌跡: {length}幀",
                "complete_track": "完整軌跡 {id}",
                "played_track": "已播放軌跡",
                "start_point": "起始點",
                "current_position": "當前位置",
                "end_point": "結束點",
                "x_label": "X (m)",
                "y_label": "Y (m)",
                "z_label": "Z (m)",
                "3d_track_title": "3D軌跡 - ID {id} (幀 {current}/{total})",
                "2d_track_title": "2D軌跡 ({plane}) - ID {id} (幀 {current}/{total})",
                "xy_plane_title": "X-Y平面",
                "xz_plane_title": "X-Z平面",
                "yz_plane_title": "Y-Z平面",
                "download_chart": "📥 下載圖表",
                "save_chart": "儲存圖表",
                "save_success": "圖表已成功儲存至: {path}",
                "save_failed": "儲存圖表失敗: {error}",
                "select_save_location": "選擇儲存位置",
                "image_files": "圖片檔案 (*.png *.jpg *.jpeg *.pdf *.svg);;PNG檔案 (*.png);;JPEG檔案 (*.jpg);;PDF檔案 (*.pdf);;SVG檔案 (*.svg);;所有檔案 (*)",
                "enable_animation": "啟用動畫"
            },
            "en": {
                "title": "MOT Track Viewer",
                "fps_label": "Playback Speed (FPS):",
                "play": "Play",
                "pause": "Pause",
                "stop": "Stop",
                "current_frame": "Current Frame:",
                "shortcut_hint": "(A/D keys to switch frames)",
                "limit_frame_range": "Limit Frame Range",
                "start_frame": "Start Frame:",
                "end_frame": "End Frame:",
                "reset_range": "Reset Range",
                "auto_scale": "Auto Scale",
                "x_axis": "X Axis:",
                "y_axis": "Y Axis:",
                "z_axis": "Z Axis:",
                "mot_file": "MOT File:",
                "track_id": "Track ID:",
                "show_3d": "3D Display",
                "show_2d": "2D Display",
                "projection": "2D Projection:",
                "xy_plane": "XY Plane",
                "xz_plane": "XZ Plane",
                "yz_plane": "YZ Plane",
                "track_info": "Track Information",
                "stats_info": "Statistics",
                "language": "🌐 Language",
                "warning": "Warning",
                "folder_not_found": "MOT label folder does not exist: {folder}",
                "no_txt_files": "No .txt files found in MOT label folder: {folder}",
                "track_id_label": "Track ID: {id}",
                "total_frames": "Total Frames: {count}",
                "start_frame_label": "Start Frame: {frame}",
                "end_frame_label": "End Frame: {frame}",
                "total_distance": "Total Distance: {distance:.2f}m",
                "start_position": "Start Position: ({x:.2f}, {y:.2f}, {z:.2f})",
                "end_position": "End Position: ({x:.2f}, {y:.2f}, {z:.2f})",
                "total_tracks": "Total Tracks: {count}",
                "total_frames_stats": "Total Frames: {count}",
                "avg_track_length": "Average Track Length: {length:.1f} frames",
                "max_track_length": "Longest Track: {length} frames",
                "min_track_length": "Shortest Track: {length} frames",
                "complete_track": "Complete Track {id}",
                "played_track": "Played Track",
                "start_point": "Start Point",
                "current_position": "Current Position",
                "end_point": "End Point",
                "x_label": "X (m)",
                "y_label": "Y (m)",
                "z_label": "Z (m)",
                "3d_track_title": "3D Track - ID {id} (Frame {current}/{total})",
                "2d_track_title": "2D Track ({plane}) - ID {id} (Frame {current}/{total})",
                "xy_plane_title": "X-Y Plane",
                "xz_plane_title": "X-Z Plane",
                "yz_plane_title": "Y-Z Plane",
                "download_chart": "📥 Download Chart",
                "save_chart": "Save Chart",
                "save_success": "Chart successfully saved to: {path}",
                "save_failed": "Failed to save chart: {error}",
                "select_save_location": "Select Save Location",
                "image_files": "Image Files (*.png *.jpg *.jpeg *.pdf *.svg);;PNG Files (*.png);;JPEG Files (*.jpg);;PDF Files (*.pdf);;SVG Files (*.svg);;All Files (*)",
                "enable_animation": "Enable Animation"
            }
        }
        
        self.setWindowTitle(self.texts[self.current_language]["title"])
        self.setGeometry(100, 100, 1200, 800)
        self.setFocusPolicy(Qt.StrongFocus)  # 允许窗口接收键盘焦点
        
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.settings = load_settings()
        # 使用設定檔中的 Track_Input_folder 作為 MOT 標籤文件的來源資料夾
        track_input_folder = self.settings.get('Track_Input_folder', 'ProcessData')
        self.mot_label_folder = os.path.join(self.current_dir, "..", track_input_folder)
        
        self.tracks = {}
        self.selected_track_id = None
        
        # 多軌跡疊加相關變數
        self.overlay_tracks = {}  # 存儲疊加的軌跡數據
        self.overlay_track_ids = []  # 存儲疊加的軌跡ID列表
        self.track_colors = {}  # 存儲每個軌跡的顏色
        self.multi_track_mode = False  # 是否啟用多軌跡模式
        
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.update_animation_frame)
        self.current_frame_index = 0
        self.is_playing = False
        
        # 帧范围设置
        self.start_frame_index = 0
        self.end_frame_index = 0
        self.use_frame_range = False
        
        # 從設定檔讀取預設FPS
        self.default_fps = int(self.settings.get('Track_FPS', '30'))
        
        # 軸刻度設定
        self.x_min = None
        self.x_max = None
        self.y_min = None
        self.y_max = None
        self.z_min = None
        self.z_max = None
        self.auto_scale = True
        
        # 初始化軌跡顏色
        self.init_track_colors()
        
        # 初始化顏色切換相關變量
        self.current_color_index = 0
        self.color_switch_enabled = True
        
        # 初始化動畫開關
        self.animation_enabled = True
        
        self.initUI()
        self.load_mot_files()
        
    def initUI(self):
        main_layout = QVBoxLayout()
        
        fps_layout = QHBoxLayout()
        fps_layout.addWidget(QLabel(self.texts[self.current_language]["fps_label"]))
        
        self.fps_spinbox = QSpinBox()
        self.fps_spinbox.setRange(1, 120)
        self.fps_spinbox.setValue(self.default_fps)
        self.fps_spinbox.valueChanged.connect(self.on_fps_changed)
        fps_layout.addWidget(self.fps_spinbox)
        
        self.play_button = QPushButton(self.texts[self.current_language]["play"])
        self.play_button.clicked.connect(self.toggle_play)
        fps_layout.addWidget(self.play_button)
        
        self.stop_button = QPushButton(self.texts[self.current_language]["stop"])
        self.stop_button.clicked.connect(self.stop_animation)
        fps_layout.addWidget(self.stop_button)
        
        # 添加動畫開關
        self.animation_checkbox = QCheckBox(self.texts[self.current_language]["enable_animation"])
        self.animation_checkbox.setChecked(True)
        self.animation_checkbox.stateChanged.connect(self.on_animation_toggled)
        fps_layout.addWidget(self.animation_checkbox)
        
        fps_layout.addWidget(QLabel(self.texts[self.current_language]["current_frame"]))
        self.frame_slider = QSlider(Qt.Horizontal)
        self.frame_slider.setMinimum(0)
        self.frame_slider.setMaximum(0)
        self.frame_slider.valueChanged.connect(self.on_frame_slider_changed)
        fps_layout.addWidget(self.frame_slider)
        
        self.frame_label = QLabel("0/0")
        fps_layout.addWidget(self.frame_label)
        
        # 添加键盘快捷键提示
        self.shortcut_label = QLabel(self.texts[self.current_language]["shortcut_hint"])
        self.shortcut_label.setStyleSheet("color: gray; font-size: 10px;")
        fps_layout.addWidget(self.shortcut_label)
        
        fps_layout.addStretch()
        main_layout.addLayout(fps_layout)
        
        # 帧范围控制
        range_layout = QHBoxLayout()
        
        self.use_range_checkbox = QCheckBox(self.texts[self.current_language]["limit_frame_range"])
        self.use_range_checkbox.stateChanged.connect(self.on_use_range_changed)
        range_layout.addWidget(self.use_range_checkbox)
        
        range_layout.addWidget(QLabel(self.texts[self.current_language]["start_frame"]))
        self.start_frame_spinbox = QSpinBox()
        self.start_frame_spinbox.setMinimum(0)
        self.start_frame_spinbox.setMaximum(0)
        self.start_frame_spinbox.setEnabled(False)
        self.start_frame_spinbox.valueChanged.connect(self.on_frame_range_changed)
        range_layout.addWidget(self.start_frame_spinbox)
        
        range_layout.addWidget(QLabel(self.texts[self.current_language]["end_frame"]))
        self.end_frame_spinbox = QSpinBox()
        self.end_frame_spinbox.setMinimum(0)
        self.end_frame_spinbox.setMaximum(0)
        self.end_frame_spinbox.setEnabled(False)
        self.end_frame_spinbox.valueChanged.connect(self.on_frame_range_changed)
        range_layout.addWidget(self.end_frame_spinbox)
        
        self.reset_range_button = QPushButton(self.texts[self.current_language]["reset_range"])
        self.reset_range_button.setEnabled(False)
        self.reset_range_button.clicked.connect(self.reset_frame_range)
        range_layout.addWidget(self.reset_range_button)
        
        range_layout.addStretch()
        main_layout.addLayout(range_layout)
        
        # 軸刻度控制
        scale_layout = QHBoxLayout()
        
        # 自動縮放選項
        self.auto_scale_checkbox = QCheckBox(self.texts[self.current_language]["auto_scale"])
        self.auto_scale_checkbox.setChecked(True)
        self.auto_scale_checkbox.stateChanged.connect(self.on_auto_scale_changed)
        scale_layout.addWidget(self.auto_scale_checkbox)
        
        # X軸範圍
        scale_layout.addWidget(QLabel(self.texts[self.current_language]["x_axis"]))
        self.x_min_spinbox = QDoubleSpinBox()
        self.x_min_spinbox.setRange(-1000, 1000)
        self.x_min_spinbox.setValue(-10)
        self.x_min_spinbox.setDecimals(2)
        self.x_min_spinbox.setSuffix("m")
        self.x_min_spinbox.setEnabled(False)
        self.x_min_spinbox.valueChanged.connect(self.on_axis_range_changed)
        scale_layout.addWidget(self.x_min_spinbox)
        
        scale_layout.addWidget(QLabel("~"))
        
        self.x_max_spinbox = QDoubleSpinBox()
        self.x_max_spinbox.setRange(-1000, 1000)
        self.x_max_spinbox.setValue(10)
        self.x_max_spinbox.setDecimals(2)
        self.x_max_spinbox.setSuffix("m")
        self.x_max_spinbox.setEnabled(False)
        self.x_max_spinbox.valueChanged.connect(self.on_axis_range_changed)
        scale_layout.addWidget(self.x_max_spinbox)
        
        # Y軸範圍 (現在顯示Z座標)
        scale_layout.addWidget(QLabel("Z軸:"))
        self.y_min_spinbox = QDoubleSpinBox()
        self.y_min_spinbox.setRange(-1000, 1000)
        self.y_min_spinbox.setValue(0)  # Z軸通常從0開始
        self.y_min_spinbox.setDecimals(2)
        self.y_min_spinbox.setSuffix("m")
        self.y_min_spinbox.setEnabled(False)
        self.y_min_spinbox.valueChanged.connect(self.on_axis_range_changed)
        scale_layout.addWidget(self.y_min_spinbox)
        
        scale_layout.addWidget(QLabel("~"))
        
        self.y_max_spinbox = QDoubleSpinBox()
        self.y_max_spinbox.setRange(-1000, 1000)
        self.y_max_spinbox.setValue(20)  # Z軸通常到20
        self.y_max_spinbox.setDecimals(2)
        self.y_max_spinbox.setSuffix("m")
        self.y_max_spinbox.setEnabled(False)
        self.y_max_spinbox.valueChanged.connect(self.on_axis_range_changed)
        scale_layout.addWidget(self.y_max_spinbox)
        
        # Z軸範圍 (現在顯示Y座標)
        scale_layout.addWidget(QLabel("Y軸:"))
        self.z_min_spinbox = QDoubleSpinBox()
        self.z_min_spinbox.setRange(-1000, 1000)
        self.z_min_spinbox.setValue(-10)  # Y軸從-10開始
        self.z_min_spinbox.setDecimals(2)
        self.z_min_spinbox.setSuffix("m")
        self.z_min_spinbox.setEnabled(False)
        self.z_min_spinbox.valueChanged.connect(self.on_axis_range_changed)
        scale_layout.addWidget(self.z_min_spinbox)
        
        scale_layout.addWidget(QLabel("~"))
        
        self.z_max_spinbox = QDoubleSpinBox()
        self.z_max_spinbox.setRange(-1000, 1000)
        self.z_max_spinbox.setValue(10)  # Y軸到10
        self.z_max_spinbox.setDecimals(2)
        self.z_max_spinbox.setSuffix("m")
        self.z_max_spinbox.setEnabled(False)
        self.z_max_spinbox.valueChanged.connect(self.on_axis_range_changed)
        scale_layout.addWidget(self.z_max_spinbox)
        
        scale_layout.addStretch()
        main_layout.addLayout(scale_layout)
        
        control_layout = QHBoxLayout()
        
        control_layout.addWidget(QLabel(self.texts[self.current_language]["mot_file"]))
        self.mot_file_combo = QComboBox()
        self.mot_file_combo.currentTextChanged.connect(self.on_mot_file_changed)
        control_layout.addWidget(self.mot_file_combo)
        
        control_layout.addWidget(QLabel(self.texts[self.current_language]["track_id"]))
        self.track_id_combo = QComboBox()
        self.track_id_combo.currentTextChanged.connect(self.on_track_id_changed)
        control_layout.addWidget(self.track_id_combo)
        
        # 多軌跡選擇區域
        self.multi_track_group = QGroupBox("多軌跡疊加")
        multi_track_layout = QHBoxLayout()
        
        self.multi_track_checkbox = QCheckBox("啟用多軌跡疊加")
        self.multi_track_checkbox.stateChanged.connect(self.on_multi_track_changed)
        multi_track_layout.addWidget(self.multi_track_checkbox)
        
        self.add_track_btn = QPushButton("添加軌跡")
        self.add_track_btn.clicked.connect(self.add_track_to_overlay)
        self.add_track_btn.setEnabled(False)
        multi_track_layout.addWidget(self.add_track_btn)
        
        self.remove_track_btn = QPushButton("移除軌跡")
        self.remove_track_btn.clicked.connect(self.remove_track_from_overlay)
        self.remove_track_btn.setEnabled(False)
        multi_track_layout.addWidget(self.remove_track_btn)
        
        self.clear_tracks_btn = QPushButton("清空所有")
        self.clear_tracks_btn.clicked.connect(self.clear_all_tracks)
        self.clear_tracks_btn.setEnabled(False)
        multi_track_layout.addWidget(self.clear_tracks_btn)
        
        self.multi_track_group.setLayout(multi_track_layout)
        self.multi_track_group.setEnabled(True)  # 啟用多軌跡群組
        control_layout.addWidget(self.multi_track_group)
        
        self.show_3d_checkbox = QCheckBox(self.texts[self.current_language]["show_3d"])
        self.show_3d_checkbox.setChecked(True)
        self.show_3d_checkbox.stateChanged.connect(self.update_plot)
        control_layout.addWidget(self.show_3d_checkbox)

        self.show_2d_checkbox = QCheckBox(self.texts[self.current_language]["show_2d"])
        self.show_2d_checkbox.setChecked(True)
        self.show_2d_checkbox.stateChanged.connect(self.update_plot)
        control_layout.addWidget(self.show_2d_checkbox)

        control_layout.addWidget(QLabel(self.texts[self.current_language]["projection"]))
        self.projection_combo = QComboBox()
        self.projection_combo.addItems([
            self.texts[self.current_language]["xy_plane"],
            self.texts[self.current_language]["xz_plane"],
            self.texts[self.current_language]["yz_plane"]
        ])
        self.projection_combo.currentTextChanged.connect(self.update_plot)
        control_layout.addWidget(self.projection_combo)
        
        # 語言切換按鈕
        self.language_btn = QPushButton(self.texts[self.current_language]["language"])
        self.language_btn.clicked.connect(self.toggle_language)
        control_layout.addWidget(self.language_btn)
        
        # 下載圖表按鈕
        self.download_btn = QPushButton(self.texts[self.current_language]["download_chart"])
        self.download_btn.clicked.connect(self.download_chart)
        control_layout.addWidget(self.download_btn)
        
        control_layout.addStretch()
        main_layout.addLayout(control_layout)
        
        self.figure = Figure(figsize=(12, 8))
        self.canvas = FigureCanvas(self.figure)
        main_layout.addWidget(self.canvas)
        
        info_layout = QHBoxLayout()
        
        self.info_group = QGroupBox(self.texts[self.current_language]["track_info"])
        info_group_layout = QGridLayout()
        
        self.track_info_text = QTextEdit()
        self.track_info_text.setMaximumHeight(100)
        self.track_info_text.setReadOnly(True)
        info_group_layout.addWidget(self.track_info_text)
        
        self.info_group.setLayout(info_group_layout)
        info_layout.addWidget(self.info_group)
        
        self.stats_group = QGroupBox(self.texts[self.current_language]["stats_info"])
        stats_group_layout = QGridLayout()
        
        self.stats_text = QTextEdit()
        self.stats_text.setMaximumHeight(100)
        self.stats_text.setReadOnly(True)
        stats_group_layout.addWidget(self.stats_text)
        
        self.stats_group.setLayout(stats_group_layout)
        info_layout.addWidget(self.stats_group)
        
        main_layout.addLayout(info_layout)
        
        self.setLayout(main_layout)
        
        # 設置焦點策略以接收鍵盤事件
        self.setFocusPolicy(Qt.StrongFocus)
        
    def init_track_colors(self):
        """初始化軌跡顏色"""
        # 預定義的顏色列表 - 使用更鮮明、對比度更高的顏色
        self.color_palette = [
            '#FF0000', '#00FF00', '#0000FF', '#FFFF00', '#FF00FF',
            '#00FFFF', '#FF8000', '#8000FF', '#00FF80', '#FF0080',
            '#80FF00', '#0080FF', '#FF4040', '#40FF40', '#4040FF',
            '#FFA500', '#A500FF', '#00A5FF', '#FFA500', '#A5FF00'
        ]
        self.color_index = 0
        
    def get_track_color(self, track_id):
        """獲取軌跡顏色"""
        if track_id not in self.track_colors:
            # 為新軌跡分配顏色
            color_index = len(self.track_colors) % len(self.color_palette)
            self.track_colors[track_id] = self.color_palette[color_index]
        return self.track_colors[track_id]
        
    def on_multi_track_changed(self, state):
        """當多軌跡模式改變時"""
        self.multi_track_mode = state == Qt.Checked
        
        # 啟用或禁用相關按鈕
        self.add_track_btn.setEnabled(self.multi_track_mode)
        
        if not self.multi_track_mode:
            # 清空疊加軌跡
            self.clear_all_tracks()
        
        self.update_plot()
        
    def add_track_to_overlay(self):
        """添加軌跡到疊加列表"""
        if not self.selected_track_id or self.selected_track_id not in self.tracks:
            return
            
        if self.selected_track_id not in self.overlay_track_ids:
            self.overlay_track_ids.append(self.selected_track_id)
            self.overlay_tracks[self.selected_track_id] = self.tracks[self.selected_track_id]
            self.get_track_color(self.selected_track_id)  # 分配顏色
            
            # 更新按鈕狀態
            self.remove_track_btn.setEnabled(True)
            self.clear_tracks_btn.setEnabled(True)
            
            self.update_plot()
            
    def remove_track_from_overlay(self):
        """從疊加列表中移除當前軌跡"""
        if not self.selected_track_id or self.selected_track_id not in self.overlay_track_ids:
            return
            
        self.overlay_track_ids.remove(self.selected_track_id)
        del self.overlay_tracks[self.selected_track_id]
        
        # 更新按鈕狀態
        if not self.overlay_track_ids:
            self.remove_track_btn.setEnabled(False)
            self.clear_tracks_btn.setEnabled(False)
            
        self.update_plot()
        
    def clear_all_tracks(self):
        """清空所有疊加軌跡"""
        self.overlay_track_ids.clear()
        self.overlay_tracks.clear()
        
        # 更新按鈕狀態
        self.remove_track_btn.setEnabled(False)
        self.clear_tracks_btn.setEnabled(False)
        
        self.update_plot()
        
    def filter_track_by_frame_range(self, track_data):
        """根據幀範圍過濾軌跡數據"""
        if not self.use_frame_range or not track_data:
            return track_data
        
        filtered_data = []
        for point in track_data:
            frame_id = point['frame_id']
            if self.start_frame_index <= frame_id <= self.end_frame_index:
                filtered_data.append(point)
        
        return filtered_data
    
    def get_current_index_in_filtered_data(self, filtered_track_data):
        """獲取當前幀在過濾後數據中的索引"""
        if not filtered_track_data or not self.selected_track_id or self.selected_track_id not in self.tracks:
            return -1
        
        # 獲取原始軌跡數據中的當前幀ID
        original_track_data = self.tracks[self.selected_track_id]
        if self.current_frame_index >= len(original_track_data):
            return -1
        
        current_frame_id = original_track_data[self.current_frame_index]['frame_id']
        
        # 在過濾後的數據中找到對應的索引
        for i, point in enumerate(filtered_track_data):
            if point['frame_id'] == current_frame_id:
                return i
        
        return -1
        
    def toggle_language(self):
        """切換語言"""
        if self.current_language == "zh":
            self.current_language = "en"
        else:
            self.current_language = "zh"
        
        # 更新視窗標題
        self.setWindowTitle(self.texts[self.current_language]["title"])
        
        # 更新所有UI文字
        self.fps_spinbox.setPrefix(self.texts[self.current_language]["fps_label"])
        self.play_button.setText(self.texts[self.current_language]["play"])
        self.stop_button.setText(self.texts[self.current_language]["stop"])
        self.animation_checkbox.setText(self.texts[self.current_language]["enable_animation"])
        self.shortcut_label.setText(self.texts[self.current_language]["shortcut_hint"])
        
        # 更新幀範圍控制
        self.use_range_checkbox.setText(self.texts[self.current_language]["limit_frame_range"])
        self.reset_range_button.setText(self.texts[self.current_language]["reset_range"])
        
        # 更新軸刻度控制
        self.auto_scale_checkbox.setText(self.texts[self.current_language]["auto_scale"])
        
        # 更新控制區域
        self.show_3d_checkbox.setText(self.texts[self.current_language]["show_3d"])
        self.show_2d_checkbox.setText(self.texts[self.current_language]["show_2d"])
        self.language_btn.setText(self.texts[self.current_language]["language"])
        self.download_btn.setText(self.texts[self.current_language]["download_chart"])
        
        # 更新多軌跡區域
        self.multi_track_group.setTitle("多軌跡疊加" if self.current_language == "zh" else "Multi-Track Overlay")
        self.multi_track_checkbox.setText("啟用多軌跡疊加" if self.current_language == "zh" else "Enable Multi-Track Overlay")
        self.add_track_btn.setText("添加軌跡" if self.current_language == "zh" else "Add Track")
        self.remove_track_btn.setText("移除軌跡" if self.current_language == "zh" else "Remove Track")
        self.clear_tracks_btn.setText("清空所有" if self.current_language == "zh" else "Clear All")
        
        # 更新投影選項
        self.projection_combo.clear()
        self.projection_combo.addItems([
            self.texts[self.current_language]["xy_plane"],
            self.texts[self.current_language]["xz_plane"],
            self.texts[self.current_language]["yz_plane"]
        ])
        
        # 更新群組標題
        self.info_group.setTitle(self.texts[self.current_language]["track_info"])
        self.stats_group.setTitle(self.texts[self.current_language]["stats_info"])
        
        # 重新更新資訊顯示
        self.update_track_info()
        self.update_stats()
        self.update_plot()
        
    def keyPressEvent(self, event):
        """处理键盘事件"""
        if event.key() == Qt.Key_A:
            self.previous_frame()
        elif event.key() == Qt.Key_D:
            self.next_frame()
        else:
            super().keyPressEvent(event)
    
    def previous_frame(self):
        """切换到上一帧"""
        if not self.selected_track_id or self.selected_track_id not in self.tracks:
            return
            
        track_data = self.tracks[self.selected_track_id]
        if not track_data:
            return
            
        min_frame = self.start_frame_index if self.use_frame_range else 0
        if self.current_frame_index > min_frame:
            self.current_frame_index -= 1
            self.frame_slider.setValue(self.current_frame_index)
            self.update_frame_label()
            self.update_plot()
    
    def next_frame(self):
        """切换到下一帧"""
        if not self.selected_track_id or self.selected_track_id not in self.tracks:
            return
            
        track_data = self.tracks[self.selected_track_id]
        if not track_data:
            return
            
        max_frame = self.end_frame_index if self.use_frame_range else len(track_data) - 1
        if self.current_frame_index < max_frame:
            self.current_frame_index += 1
            self.frame_slider.setValue(self.current_frame_index)
            self.update_frame_label()
            self.update_plot()
    
    def update_frame_label(self):
        """更新帧标签显示"""
        if not self.selected_track_id or self.selected_track_id not in self.tracks:
            self.frame_label.setText("0/0")
            return
            
        track_data = self.tracks[self.selected_track_id]
        if self.use_frame_range:
            max_frames = self.end_frame_index
            self.frame_label.setText(f"{self.current_frame_index}/{max_frames}")
        else:
            max_frames = len(track_data) - 1
            self.frame_label.setText(f"{self.current_frame_index}/{max_frames}")
    
    def on_use_range_changed(self, state):
        """当帧范围限制选项改变时"""
        self.use_frame_range = state == Qt.Checked
        
        # 启用或禁用帧范围控制
        self.start_frame_spinbox.setEnabled(self.use_frame_range)
        self.end_frame_spinbox.setEnabled(self.use_frame_range)
        self.reset_range_button.setEnabled(self.use_frame_range)
        
        if self.use_frame_range:
            self.setup_frame_range_controls()
            self.apply_frame_range()
        else:
            self.reset_to_full_range()
        
        self.update_frame_label()
        
    def on_frame_range_changed(self):
        """当帧范围改变时"""
        if self.use_frame_range:
            self.start_frame_index = self.start_frame_spinbox.value()
            self.end_frame_index = self.end_frame_spinbox.value()
            
            # 确保开始帧不大于结束帧
            if self.start_frame_index > self.end_frame_index:
                if self.sender() == self.start_frame_spinbox:
                    self.end_frame_spinbox.setValue(self.start_frame_index)
                    self.end_frame_index = self.start_frame_index
                else:
                    self.start_frame_spinbox.setValue(self.end_frame_index)
                    self.start_frame_index = self.end_frame_index
            
            self.apply_frame_range()
            # 重新繪製圖表
            self.update_plot()
        
    def setup_frame_range_controls(self):
        """设置帧范围控件的范围"""
        if not self.selected_track_id or self.selected_track_id not in self.tracks:
            return
            
        track_data = self.tracks[self.selected_track_id]
        max_frame = len(track_data) - 1
        
        self.start_frame_spinbox.setMaximum(max_frame)
        self.end_frame_spinbox.setMaximum(max_frame)
        
        # 设置默认值
        if self.start_frame_index == 0 and self.end_frame_index == 0:
            self.start_frame_index = 0
            self.end_frame_index = max_frame
            self.start_frame_spinbox.setValue(0)
            self.end_frame_spinbox.setValue(max_frame)
    
    def apply_frame_range(self):
        """应用帧范围限制"""
        if not self.use_frame_range:
            return
            
        # 更新滑块范围
        self.frame_slider.setMinimum(self.start_frame_index)
        self.frame_slider.setMaximum(self.end_frame_index)
        
        # 确保当前帧在范围内
        if self.current_frame_index < self.start_frame_index:
            self.current_frame_index = self.start_frame_index
            self.frame_slider.setValue(self.current_frame_index)
        elif self.current_frame_index > self.end_frame_index:
            self.current_frame_index = self.end_frame_index
            self.frame_slider.setValue(self.current_frame_index)
            
        self.update_plot()
        
    def reset_to_full_range(self):
        """重置到完整范围"""
        if not self.selected_track_id or self.selected_track_id not in self.tracks:
            return
            
        track_data = self.tracks[self.selected_track_id]
        max_frame = len(track_data) - 1
        
        self.frame_slider.setMinimum(0)
        self.frame_slider.setMaximum(max_frame)
        
        self.update_plot()
        
    def reset_frame_range(self):
        """重置帧范围到全范围"""
        if not self.selected_track_id or self.selected_track_id not in self.tracks:
            return
            
        track_data = self.tracks[self.selected_track_id]
        max_frame = len(track_data) - 1
        
        self.start_frame_index = 0
        self.end_frame_index = max_frame
        self.start_frame_spinbox.setValue(0)
        self.end_frame_spinbox.setValue(max_frame)
        
        self.apply_frame_range()
        
    def on_fps_changed(self, fps):
        """當FPS改變時"""
        if self.is_playing:
            self.start_animation()
            
    def on_auto_scale_changed(self, state):
        """當自動縮放選項改變時"""
        self.auto_scale = state == Qt.Checked
        
        # 啟用或禁用軸刻度控制
        self.x_min_spinbox.setEnabled(not self.auto_scale)
        self.x_max_spinbox.setEnabled(not self.auto_scale)
        self.y_min_spinbox.setEnabled(not self.auto_scale)
        self.y_max_spinbox.setEnabled(not self.auto_scale)
        self.z_min_spinbox.setEnabled(not self.auto_scale)
        self.z_max_spinbox.setEnabled(not self.auto_scale)
        
        if not self.auto_scale:
            self.update_axis_ranges_from_data()
        
        self.update_plot()
        
    def on_axis_range_changed(self):
        """當軸範圍改變時"""
        if not self.auto_scale:
            self.x_min = self.x_min_spinbox.value()
            self.x_max = self.x_max_spinbox.value()
            self.y_min = self.y_min_spinbox.value()
            self.y_max = self.y_max_spinbox.value()
            self.z_min = self.z_min_spinbox.value()
            self.z_max = self.z_max_spinbox.value()
            self.update_plot()
            
    def update_axis_ranges_from_data(self):
        """根據當前軌跡數據更新軸範圍"""
        if self.selected_track_id is None or self.selected_track_id not in self.tracks:
            return
            
        track_data = self.tracks[self.selected_track_id]
        if not track_data:
            return
            
        x_coords = [point['x_cam'] for point in track_data]
        y_coords = [point['z'] for point in track_data]  # Y軸使用Z座標
        z_coords = [-point['y_cam'] for point in track_data]  # Z軸使用Y座標（翻轉）
        
        if x_coords:
            x_min, x_max = min(x_coords), max(x_coords)
            y_min, y_max = min(y_coords), max(y_coords)
            z_min, z_max = min(z_coords), max(z_coords)
            
            # 添加一些邊距
            x_margin = (x_max - x_min) * 0.1 if x_max != x_min else 1
            y_margin = (y_max - y_min) * 0.1 if y_max != y_min else 1
            z_margin = (z_max - z_min) * 0.1 if z_max != z_min else 1
            
            self.x_min_spinbox.setValue(x_min - x_margin)
            self.x_max_spinbox.setValue(x_max + x_margin)
            self.y_min_spinbox.setValue(y_min - y_margin)
            self.y_max_spinbox.setValue(y_max + y_margin)
            self.z_min_spinbox.setValue(z_min - z_margin)
            self.z_max_spinbox.setValue(z_max + z_margin)
        
    def toggle_play(self):
        """切換播放/暫停"""
        if self.is_playing:
            self.stop_animation()
        else:
            self.start_animation()
            
    def start_animation(self):
        """開始動畫播放"""
        if not self.selected_track_id or self.selected_track_id not in self.tracks:
            return
            
        track_data = self.tracks[self.selected_track_id]
        if not track_data:
            return
            
        self.is_playing = True
        self.play_button.setText(self.texts[self.current_language]["pause"])
        
        # 設定定時器間隔 (毫秒)
        interval = int(1000 / self.fps_spinbox.value())
        self.animation_timer.start(interval)
        
    def stop_animation(self):
        """停止動畫播放"""
        self.is_playing = False
        self.play_button.setText(self.texts[self.current_language]["play"])
        self.animation_timer.stop()
        
    def update_animation_frame(self):
        """更新動畫幀"""
        if not self.selected_track_id or self.selected_track_id not in self.tracks:
            return
            
        track_data = self.tracks[self.selected_track_id]
        if not track_data:
            return
            
        max_frame = self.end_frame_index if self.use_frame_range else len(track_data) - 1
        min_frame = self.start_frame_index if self.use_frame_range else 0
        
        self.current_frame_index += 1
        if self.current_frame_index > max_frame:
            self.current_frame_index = min_frame
            
        self.frame_slider.setValue(self.current_frame_index)
        self.update_frame_label()
        self.update_plot()
        
    def on_frame_slider_changed(self, frame_index):
        """當幀數滑桿改變時"""
        self.current_frame_index = frame_index
        self.update_frame_label()
        self.update_plot()
        
    def load_mot_files(self):
        """載入MOT標籤檔案"""
        if not os.path.exists(self.mot_label_folder):
            QMessageBox.warning(self, self.texts[self.current_language]["warning"], 
                              self.texts[self.current_language]["folder_not_found"].format(folder=self.mot_label_folder))
            return
        
        mot_files = [f for f in os.listdir(self.mot_label_folder) if f.endswith('.txt')]
        if not mot_files:
            QMessageBox.warning(self, self.texts[self.current_language]["warning"], 
                              self.texts[self.current_language]["no_txt_files"].format(folder=self.mot_label_folder))
            return
        
        self.mot_file_combo.clear()
        self.mot_file_combo.addItems(mot_files)
        
    def on_mot_file_changed(self, filename):
        """當MOT檔案選擇改變時"""
        if not filename:
            return
            
        mot_file_path = os.path.join(self.mot_label_folder, filename)
        self.tracks = read_mot_labels(mot_file_path)
        
        self.track_id_combo.clear()
        if self.tracks:
            track_ids = sorted(self.tracks.keys())
            self.track_id_combo.addItems([str(tid) for tid in track_ids])
        
        self.update_stats()
        
    def on_track_id_changed(self, track_id_str):
        """當軌跡ID選擇改變時"""
        if not track_id_str:
            self.selected_track_id = None
            self.stop_animation()
            return
            
        try:
            self.selected_track_id = int(track_id_str)
            self.update_track_info()
            # 不重置幀範圍和軸刻度，保持用戶的設定
            self.update_frame_controls_preserve_settings()
            self.update_plot()
        except ValueError:
            self.selected_track_id = None
            
    def update_frame_controls(self):
        """更新幀控制元件"""
        if not self.selected_track_id or self.selected_track_id not in self.tracks:
            self.frame_slider.setMaximum(0)
            self.frame_label.setText("0/0")
            # 重置帧范围控件
            self.start_frame_spinbox.setMaximum(0)
            self.end_frame_spinbox.setMaximum(0)
            return
            
        track_data = self.tracks[self.selected_track_id]
        max_frames = len(track_data) - 1
        
        # 设置帧范围控件的最大值
        self.start_frame_spinbox.setMaximum(max_frames)
        self.end_frame_spinbox.setMaximum(max_frames)
        
        # 重置帧范围
        self.start_frame_index = 0
        self.end_frame_index = max_frames
        self.start_frame_spinbox.setValue(0)
        self.end_frame_spinbox.setValue(max_frames)
        
        if self.use_frame_range:
            self.frame_slider.setMinimum(self.start_frame_index)
            self.frame_slider.setMaximum(self.end_frame_index)
            self.current_frame_index = self.start_frame_index
        else:
            self.frame_slider.setMinimum(0)
            self.frame_slider.setMaximum(max_frames)
            self.current_frame_index = 0
            
        self.frame_slider.setValue(self.current_frame_index)
        self.update_frame_label()
        
    def update_frame_controls_preserve_settings(self):
        """更新幀控制元件，但保持用戶的設定不變"""
        if not self.selected_track_id or self.selected_track_id not in self.tracks:
            self.frame_slider.setMaximum(0)
            self.frame_label.setText("0/0")
            return
            
        track_data = self.tracks[self.selected_track_id]
        max_frames = len(track_data) - 1
        
        # 設置幀範圍控件的最大值，但不改變當前值
        self.start_frame_spinbox.setMaximum(max_frames)
        self.end_frame_spinbox.setMaximum(max_frames)
        
        # 如果當前幀索引超出範圍，則調整到有效範圍內
        if self.current_frame_index > max_frames:
            self.current_frame_index = max_frames
            self.frame_slider.setValue(self.current_frame_index)
        
        # 更新滑塊範圍，但保持當前值
        if self.use_frame_range:
            # 確保幀範圍在有效範圍內
            if self.start_frame_index > max_frames:
                self.start_frame_index = 0
                self.start_frame_spinbox.setValue(0)
            if self.end_frame_index > max_frames:
                self.end_frame_index = max_frames
                self.end_frame_spinbox.setValue(max_frames)
            
            self.frame_slider.setMinimum(self.start_frame_index)
            self.frame_slider.setMaximum(self.end_frame_index)
            
            # 確保當前幀在範圍內
            if self.current_frame_index < self.start_frame_index:
                self.current_frame_index = self.start_frame_index
                self.frame_slider.setValue(self.current_frame_index)
            elif self.current_frame_index > self.end_frame_index:
                self.current_frame_index = self.end_frame_index
                self.frame_slider.setValue(self.current_frame_index)
        else:
            self.frame_slider.setMinimum(0)
            self.frame_slider.setMaximum(max_frames)
            
        self.update_frame_label()
        
    def update_track_info(self):
        """更新軌跡資訊顯示"""
        if self.selected_track_id is None or self.selected_track_id not in self.tracks:
            self.track_info_text.clear()
            return
            
        track_data = self.tracks[self.selected_track_id]
        if not track_data:
            self.track_info_text.clear()
            return
            
        info_text = self.texts[self.current_language]["track_id_label"].format(id=self.selected_track_id) + "\n"
        info_text += self.texts[self.current_language]["total_frames"].format(count=len(track_data)) + "\n"
        info_text += self.texts[self.current_language]["start_frame_label"].format(frame=track_data[0]['frame_id']) + "\n"
        info_text += self.texts[self.current_language]["end_frame_label"].format(frame=track_data[-1]['frame_id']) + "\n"
        
        total_distance = 0
        for i in range(1, len(track_data)):
            prev = track_data[i-1]
            curr = track_data[i]
            dx = curr['x_cam'] - prev['x_cam']
            dy = curr['y_cam'] - prev['y_cam']
            dz = curr['z'] - prev['z']
            distance = np.sqrt(dx*dx + dy*dy + dz*dz)
            total_distance += distance
            
        info_text += self.texts[self.current_language]["total_distance"].format(distance=total_distance) + "\n"
        
        start_pos = track_data[0]
        end_pos = track_data[-1]
        info_text += self.texts[self.current_language]["start_position"].format(
            x=start_pos['x_cam'], y=start_pos['y_cam'], z=start_pos['z']) + "\n"
        info_text += self.texts[self.current_language]["end_position"].format(
            x=end_pos['x_cam'], y=end_pos['y_cam'], z=end_pos['z'])
        
        self.track_info_text.setText(info_text)
        
    def update_stats(self):
        """更新統計資訊"""
        if not self.tracks:
            self.stats_text.clear()
            return
            
        total_tracks = len(self.tracks)
        total_frames = sum(len(track) for track in self.tracks.values())
        
        track_lengths = [len(track) for track in self.tracks.values()]
        avg_length = np.mean(track_lengths) if track_lengths else 0
        max_length = max(track_lengths) if track_lengths else 0
        min_length = min(track_lengths) if track_lengths else 0
        
        stats_text = self.texts[self.current_language]["total_tracks"].format(count=total_tracks) + "\n"
        stats_text += self.texts[self.current_language]["total_frames_stats"].format(count=total_frames) + "\n"
        stats_text += self.texts[self.current_language]["avg_track_length"].format(length=avg_length) + "\n"
        stats_text += self.texts[self.current_language]["max_track_length"].format(length=max_length) + "\n"
        stats_text += self.texts[self.current_language]["min_track_length"].format(length=min_length)
        
        self.stats_text.setText(stats_text)
        
    def update_plot(self):
        """更新圖表顯示"""
        self.figure.clear()
        
        # 確定要顯示的軌跡
        tracks_to_display = []
        if self.multi_track_mode and self.overlay_tracks:
            # 多軌跡模式：顯示所有疊加的軌跡
            tracks_to_display = list(self.overlay_tracks.items())
        elif self.selected_track_id is not None and self.selected_track_id in self.tracks:
            # 單軌跡模式：顯示當前選中的軌跡
            tracks_to_display = [(self.selected_track_id, self.tracks[self.selected_track_id])]
        
        if not tracks_to_display:
            self.canvas.draw()
            return
        
        show_3d = self.show_3d_checkbox.isChecked()
        show_2d = self.show_2d_checkbox.isChecked()
        
        if show_3d and show_2d:
            ax1 = self.figure.add_subplot(121, projection='3d')
            ax2 = self.figure.add_subplot(122)
        elif show_3d:
            ax1 = self.figure.add_subplot(111, projection='3d')
            ax2 = None
        else:
            ax1 = None
            ax2 = self.figure.add_subplot(111)
            
        # 繪製3D圖表
        if ax1 is not None:
            self.plot_3d_tracks(ax1, tracks_to_display)
            
        # 繪製2D圖表
        if ax2 is not None:
            self.plot_2d_tracks(ax2, tracks_to_display)
            
        self.figure.tight_layout()
        self.canvas.draw()
        
    def plot_3d_tracks(self, ax, tracks_to_display):
        """繪製3D軌跡"""
        legend_added = set()  # 避免重複添加圖例
        
        for track_id, track_data in tracks_to_display:
            if not track_data:
                continue
            
            # 根據幀範圍過濾軌跡數據
            filtered_track_data = self.filter_track_by_frame_range(track_data)
            if not filtered_track_data:
                continue
                
            x_coords = [point['x_cam'] for point in filtered_track_data]
            y_coords = [point['z'] for point in filtered_track_data]  # Y軸使用Z座標
            z_coords = [-point['y_cam'] for point in filtered_track_data]  # Z軸使用Y座標（翻轉）
            
            # 獲取軌跡顏色
            color = self.get_track_color(track_id)
            
            # 繪製過濾後的軌跡
            ax.plot(x_coords, y_coords, z_coords, color=color, linewidth=1, alpha=0.5, 
                   label=f"軌跡 {track_id}")
            
            # 如果是當前選中的軌跡且動畫啟用，繪製播放進度
            if (self.animation_enabled and track_id == self.selected_track_id and 
                self.current_frame_index > 0):
                # 計算在過濾後數據中的當前幀索引
                current_index_in_filtered = self.get_current_index_in_filtered_data(filtered_track_data)
                if current_index_in_filtered > 0:
                    ax.plot(x_coords[:current_index_in_filtered+1], y_coords[:current_index_in_filtered+1], 
                           z_coords[:current_index_in_filtered+1], color=color, linewidth=3, 
                           label="播放進度" if "播放進度" not in legend_added else "")
                    legend_added.add("播放進度")
            
            # 繪製當前位置（根據動畫開關決定是否顯示）
            if (self.animation_enabled and track_id == self.selected_track_id and 
                0 <= self.current_frame_index < len(track_data)):
                current_index_in_filtered = self.get_current_index_in_filtered_data(filtered_track_data)
                if 0 <= current_index_in_filtered < len(filtered_track_data):
                    ax.scatter(x_coords[current_index_in_filtered], y_coords[current_index_in_filtered], 
                              z_coords[current_index_in_filtered], color='red', s=150, 
                              label="當前位置" if "當前位置" not in legend_added else "")
                    legend_added.add("當前位置")
        
        ax.set_xlabel(self.texts[self.current_language]["x_label"])
        ax.set_ylabel("Z (m)")  # Y軸現在顯示Z座標
        ax.set_zlabel("Y (m)")  # Z軸現在顯示Y座標
        
        # 設定標題
        if self.multi_track_mode:
            track_ids = [str(tid) for tid, _ in tracks_to_display]
            if self.use_frame_range:
                ax.set_title(f"3D軌跡疊加 (幀 {self.start_frame_index}-{self.end_frame_index}) - ID: {', '.join(track_ids)}")
            else:
                ax.set_title(f"3D軌跡疊加 - ID: {', '.join(track_ids)}")
        else:
            track_id, track_data = tracks_to_display[0]
            if self.use_frame_range:
                filtered_data = self.filter_track_by_frame_range(track_data)
                ax.set_title(f"3D軌跡 - ID {track_id} (幀 {self.start_frame_index}-{self.end_frame_index}, 共{len(filtered_data)}點)")
            else:
                ax.set_title(self.texts[self.current_language]["3d_track_title"].format(
                    id=track_id, current=self.current_frame_index+1, total=len(track_data)))
        
        ax.legend()
        ax.grid(True)
        
        # 設定軸範圍
        if not self.auto_scale:
            ax.set_xlim(self.x_min, self.x_max)
            ax.set_ylim(self.y_min, self.y_max)
            ax.set_zlim(self.z_min, self.z_max)
            
    def plot_2d_tracks(self, ax, tracks_to_display):
        """繪製2D軌跡"""
        projection = self.projection_combo.currentText()
        legend_added = set()  # 避免重複添加圖例
        
        for track_id, track_data in tracks_to_display:
            if not track_data:
                continue
            
            # 根據幀範圍過濾軌跡數據
            filtered_track_data = self.filter_track_by_frame_range(track_data)
            if not filtered_track_data:
                continue
                
            x_coords = [point['x_cam'] for point in filtered_track_data]
            y_coords = [point['z'] for point in filtered_track_data]  # Y軸使用Z座標
            z_coords = [-point['y_cam'] for point in filtered_track_data]  # Z軸使用Y座標（翻轉）
            
            # 根據投影選擇座標
            if projection == self.texts[self.current_language]["xy_plane"]:
                x_2d = x_coords
                y_2d = y_coords
                xlabel = self.texts[self.current_language]["x_label"]
                ylabel = "Z (m)"  # Y軸現在顯示Z座標
                title_suffix = "X-Z平面"  # 更新標題
            elif projection == self.texts[self.current_language]["xz_plane"]:
                x_2d = x_coords
                y_2d = z_coords
                xlabel = self.texts[self.current_language]["x_label"]
                ylabel = "Y (m)"  # Z軸現在顯示Y座標
                title_suffix = "X-Y平面"  # 更新標題
            else:  # YZ平面
                x_2d = y_coords
                y_2d = z_coords
                xlabel = "Z (m)"  # Y軸現在顯示Z座標
                ylabel = "Y (m)"  # Z軸現在顯示Y座標
                title_suffix = "Z-Y平面"  # 更新標題
            
            # 獲取軌跡顏色
            color = self.get_track_color(track_id)
            
            # 繪製過濾後的軌跡
            ax.plot(x_2d, y_2d, color=color, linewidth=1, alpha=0.5, 
                   label=f"軌跡 {track_id}")
            
            # 如果是當前選中的軌跡且動畫啟用，繪製播放進度
            if (self.animation_enabled and track_id == self.selected_track_id and 
                self.current_frame_index > 0):
                # 計算在過濾後數據中的當前幀索引
                current_index_in_filtered = self.get_current_index_in_filtered_data(filtered_track_data)
                if current_index_in_filtered > 0:
                    ax.plot(x_2d[:current_index_in_filtered+1], y_2d[:current_index_in_filtered+1], 
                           color=color, linewidth=3, 
                           label="播放進度" if "播放進度" not in legend_added else "")
                    legend_added.add("播放進度")
            
            # 繪製當前位置（根據動畫開關決定是否顯示）
            if (self.animation_enabled and track_id == self.selected_track_id and 
                0 <= self.current_frame_index < len(track_data)):
                current_index_in_filtered = self.get_current_index_in_filtered_data(filtered_track_data)
                if 0 <= current_index_in_filtered < len(filtered_track_data):
                    ax.scatter(x_2d[current_index_in_filtered], y_2d[current_index_in_filtered], 
                              color='red', s=150, 
                              label="當前位置" if "當前位置" not in legend_added else "")
                    legend_added.add("當前位置")
        
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        
        # 設定標題
        if self.multi_track_mode:
            track_ids = [str(tid) for tid, _ in tracks_to_display]
            if self.use_frame_range:
                ax.set_title(f"2D軌跡疊加 ({title_suffix}) (幀 {self.start_frame_index}-{self.end_frame_index}) - ID: {', '.join(track_ids)}")
            else:
                ax.set_title(f"2D軌跡疊加 ({title_suffix}) - ID: {', '.join(track_ids)}")
        else:
            track_id, track_data = tracks_to_display[0]
            if self.use_frame_range:
                filtered_data = self.filter_track_by_frame_range(track_data)
                ax.set_title(f"2D軌跡 ({title_suffix}) - ID {track_id} (幀 {self.start_frame_index}-{self.end_frame_index}, 共{len(filtered_data)}點)")
            else:
                ax.set_title(self.texts[self.current_language]["2d_track_title"].format(
                    plane=title_suffix, id=track_id, current=self.current_frame_index+1, total=len(track_data)))
        
        ax.legend()
        ax.grid(True)
        
        # 設定軸範圍
        if not self.auto_scale:
            if projection == self.texts[self.current_language]["xy_plane"]:
                ax.set_xlim(self.x_min, self.x_max)
                ax.set_ylim(self.y_min, self.y_max)
            elif projection == self.texts[self.current_language]["xz_plane"]:
                ax.set_xlim(self.x_min, self.x_max)
                ax.set_ylim(self.z_min, self.z_max)
            else:  # YZ平面
                ax.set_xlim(self.y_min, self.y_max)
                ax.set_ylim(self.z_min, self.z_max)
        else:
            ax.axis('equal')
        
    def download_chart(self):
        """下載當前圖表"""
        if self.selected_track_id is None or self.selected_track_id not in self.tracks:
            QMessageBox.warning(self, self.texts[self.current_language]["warning"], 
                              "請先選擇一個軌跡")
            return
        
        # 生成預設檔案名稱
        track_id = self.selected_track_id
        current_frame = self.current_frame_index + 1
        total_frames = len(self.tracks[self.selected_track_id])
        
        # 根據顯示模式生成檔案名稱
        display_mode = []
        if self.show_3d_checkbox.isChecked():
            display_mode.append("3D")
        if self.show_2d_checkbox.isChecked():
            projection = self.projection_combo.currentText()
            if projection == self.texts[self.current_language]["xy_plane"]:
                display_mode.append("XY")
            elif projection == self.texts[self.current_language]["xz_plane"]:
                display_mode.append("XZ")
            else:
                display_mode.append("YZ")
        
        mode_str = "_".join(display_mode) if display_mode else "Chart"
        default_filename = f"Track_{track_id}_{mode_str}_Frame_{current_frame}_{total_frames}.png"
        
        # 開啟檔案儲存對話框
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self,
            self.texts[self.current_language]["select_save_location"],
            default_filename,
            self.texts[self.current_language]["image_files"]
        )
        
        if file_path:
            try:
                # 根據選擇的檔案格式儲存
                if file_path.lower().endswith('.pdf'):
                    self.figure.savefig(file_path, format='pdf', bbox_inches='tight', dpi=300)
                elif file_path.lower().endswith('.svg'):
                    self.figure.savefig(file_path, format='svg', bbox_inches='tight', dpi=300)
                elif file_path.lower().endswith(('.jpg', '.jpeg')):
                    self.figure.savefig(file_path, format='jpeg', bbox_inches='tight', dpi=300)
                else:  # 預設為PNG
                    self.figure.savefig(file_path, format='png', bbox_inches='tight', dpi=300)
                
                QMessageBox.information(self, self.texts[self.current_language]["save_chart"], 
                                      self.texts[self.current_language]["save_success"].format(path=file_path))
                
            except Exception as e:
                QMessageBox.critical(self, self.texts[self.current_language]["save_chart"], 
                                   self.texts[self.current_language]["save_failed"].format(error=str(e)))
    
    def keyPressEvent(self, event):
        """處理鍵盤事件"""
        if not self.color_switch_enabled:
            super().keyPressEvent(event)
            return
            
        key = event.key()
        
        # 按 C 鍵切換顏色
        if key == Qt.Key_C:
            self.switch_track_color()
        # 按 H 鍵顯示幫助
        elif key == Qt.Key_H:
            self.show_color_help()
        else:
            super().keyPressEvent(event)
    
    def switch_track_color(self):
        """切換軌跡顏色"""
        if not self.selected_track_id:
            self.log("請先選擇一個軌跡")
            return
            
        # 獲取當前軌跡的顏色索引
        current_color = self.get_track_color(self.selected_track_id)
        try:
            current_index = self.color_palette.index(current_color)
        except ValueError:
            current_index = 0
        
        # 切換到下一個顏色
        next_index = (current_index + 1) % len(self.color_palette)
        
        # 更新軌跡顏色
        self.track_colors[self.selected_track_id] = self.color_palette[next_index]
        
        # 重新繪製圖表
        self.update_plot()
        
        # 顯示顏色切換提示
        color_name = self.get_color_name(self.color_palette[next_index])
        self.log(f"軌跡 {self.selected_track_id} 顏色已切換為: {color_name}")
    
    def get_color_name(self, color_hex):
        """根據十六進制顏色代碼返回顏色名稱"""
        color_names = {
            '#FF0000': '紅色', '#00FF00': '綠色', '#0000FF': '藍色', 
            '#FFFF00': '黃色', '#FF00FF': '洋紅', '#00FFFF': '青色',
            '#FF8000': '橙色', '#8000FF': '紫色', '#00FF80': '青綠', 
            '#FF0080': '粉紅', '#80FF00': '黃綠', '#0080FF': '天藍',
            '#FF8080': '淺紅', '#80FF80': '淺綠', '#8080FF': '淺藍',
            '#FFFF80': '淺黃', '#FF80FF': '淺洋紅', '#80FFFF': '淺青'
        }
        return color_names.get(color_hex, color_hex)
    
    def show_color_help(self):
        """顯示顏色切換幫助"""
        help_text = """
🎨 軌跡顏色切換功能
═══════════════════════════════════════════════════════════════════════════════════
⌨️  快捷鍵說明：
   • 按 C 鍵：切換當前選中軌跡的顏色
   • 按 H 鍵：顯示此幫助信息

🎯 使用方式：
   1. 選擇要更改顏色的軌跡
   2. 按 C 鍵循環切換顏色
   3. 顏色會立即在圖表中更新

🌈 可用顏色：
   紅色、綠色、藍色、黃色、洋紅、青色、橙色、紫色、青綠、粉紅等

💡 提示：
   • 顏色切換只影響當前選中的軌跡
   • 多軌跡疊加模式下，每個軌跡可以有不同的顏色
   • 按 H 鍵隨時查看此幫助
        """
        self.log(help_text)
    
    def log(self, message):
        """簡單的日誌方法，在軌跡信息區域顯示消息"""
        # 在軌跡信息區域顯示狀態消息
        current_text = self.track_info_text.toPlainText()
        if current_text:
            self.track_info_text.setText(f"{current_text}\n{message}")
        else:
            self.track_info_text.setText(message)
    
    def on_animation_toggled(self, state):
        """當動畫開關改變時"""
        self.animation_enabled = state == Qt.Checked
        
        if not self.animation_enabled:
            # 關閉動畫時停止播放
            self.stop_animation()
        
        # 重新繪製圖表（會根據動畫開關決定是否顯示當前位置）
        self.update_plot()
        
        # 顯示狀態提示
        status = "已啟用" if self.animation_enabled else "已關閉"
        self.log(f"動畫功能{status}")
        
def main():
    # 設定應用程式編碼
    import locale
    try:
        locale.setlocale(locale.LC_ALL, 'zh_TW.UTF-8')
    except:
        try:
            locale.setlocale(locale.LC_ALL, 'zh_CN.UTF-8')
        except:
            pass
    
    app = QApplication(sys.argv)
    viewer = TrackViewer()
    viewer.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
