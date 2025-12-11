import os
import shutil
import re
import glob
import numpy as np
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QSpinBox, QPushButton, QMessageBox, QComboBox, QTextEdit, 
                             QProgressBar, QMainWindow, QWidget)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont
import sys

class DataGeneratorProgressWindow(QMainWindow):
    """資料生成器進度顯示視窗"""
    def __init__(self):
        super().__init__()
        
        # 語言設定 - 從環境變數讀取，如果沒有則預設中文
        self.current_language = os.environ.get('AIRSIM_LANGUAGE', 'zh')
        self.texts = {
            "zh": {
                "title": "AirSim 資料生成器 - 處理進度",
                "progress_title": "🔄 AirSim 資料處理進度",
                "ready": "",
                "log_title": "📋 處理詳細日誌：",
                "close": "❌ 關閉",
                "language": "🌐 語言",
                "reselect_input": "🔄 重新選擇輸入源",
                "reselect_input_log": "🔄 重新選擇輸入源...",
                "start_processing": "🔄 開始重新處理資料...",
                "user_cancelled": "⚠️ 使用者取消操作或關閉視窗",
                "processing_error": "⚠️ 重新處理時發生錯誤：{error}",
                "reselect_error": "⚠️ 重新選擇輸入源時發生錯誤：{error}",
                "select_input_source": "選擇輸入源",
                "select_data_source": "請選擇資料來源：",
                "use_local_rawdata": "使用本地 RawData 資料夾",
                "images_count": "張圖片",
                "ok": "確定",
                "cancel": "取消",
                "error": "錯誤",
                "warning": "警告",
                "folder_not_found": "找不到 '{folder}' 資料夾",
                "no_processable_files": "在 '{folder}' 中找不到可處理的檔案",
                "select_processing_range": "選擇處理範圍",
                "found_images": "找到 {count} 張圖片可處理",
                "settings_default": "設定檔預設值：{value}",
                "processing_range": "處理範圍: 1 ~",
                "load_settings_failed": "⚠️ 載入設定檔案失敗：{error}",
                "user_cancelled_operation": "⚠️ 使用者取消操作或關閉視窗",
                "processing_from_airsim": "📁 將直接從 AirSim 資料夾處理資料：{source}",
                "processing_from_local": "📁 將從本地 RawData 資料夾處理資料：{folder}",
                "manual_put_rawdata": "⚠️ 請手動將原始資料放入 '{folder}' 資料夾後再執行。",
                "user_cancelled_range": "⚠️ 使用者取消處理範圍選擇",
                "processing_range_info": "🔄 將處理第 {start} 到第 {end} 張圖片",
                "clearing_folder": "🔄 清空現有的 '{folder}' 資料夾...",
                "folder_created": "✅ 已建立 '{folder}' 資料夾。",
                "files_found": "📁 找到檔案數量：Img0={img0}, Img1={img1}, Seg={seg}, PFM={pfm}",
                "processed_img_left": "✅ 已處理 {count} 個 'img_left0' 檔案。",
                "processed_img_right": "✅ 已處理 {count} 個 'img_right_0' 檔案。",
                "processed_img_seg": "✅ 已處理 {count} 個 'img_front_left_5' 檔案。",
                "processed_pfm_depth": "✅ 已處理 {count} 個 '.pfm' 檔案，並限制最大深度為 {depth}m。",
                "file_processing_error": "⚠️ 處理檔案 {file} 時發生錯誤: {error}",
                "source_folder_not_exist": "⚠️ 錯誤：來源資料夾 '{folder}' 不存在，無法複製到結果資料夾。",
                "result_folder_created": "✅ 已建立結果資料夾：'{folder}'",
                "clearing_result_folder": "🔄 清空現有結果資料夾：'{folder}'",
                "delete_file_failed": "⚠️ 刪除 {file} 失敗：{error}",
                "copying_files": "🔄 開始複製非 Seg 檔案到 '{folder}'...",
                "files_found_pattern": "📁 在 '{folder}' 找到 {pattern} 檔案：{count} 個",
                "copy_file_failed": "⚠️ 複製 {file} 失敗：{error}",
                "files_copied": "✅ 已複製 {count} 個檔案到 '{folder}'（不包含 Seg）",
                "rawdata_found_files": "📁 發現 RawData 資料夾中有 {img_count} 個圖片文件和 {pfm_count} 個 PFM 文件，開始完整處理流程...",
                "program_ended": "⚠️ 程式已結束",
                "rawdata_no_files": "📁 RawData 資料夾存在但沒有可處理的文件，打開 AirSim 資料夾選擇功能...",
                "rawdata_not_found": "📁 找不到 RawData 資料夾，打開 AirSim 資料夾選擇功能...",
                "starting_pfm_conversion": "🔄 開始執行 PFM 轉換...",
                "camera_params": "⚙️ 使用相機參數：FOV={fov}°, 解析度={width}x{height}, 基線={baseline}m, 最大深度={depth}m"
            },
            "en": {
                "title": "AirSim Data Generator - Processing Progress",
                "progress_title": "🔄 AirSim Data Processing Progress",
                "ready": "",
                "log_title": "📋 Processing Detailed Log:",
                "close": "❌ Close",
                "language": "🌐 Language",
                "reselect_input": "🔄 Reselect Input Source",
                "reselect_input_log": "🔄 Reselecting input source...",
                "start_processing": "🔄 Starting to reprocess data...",
                "user_cancelled": "⚠️ User cancelled operation or closed window",
                "processing_error": "⚠️ Error occurred during reprocessing: {error}",
                "reselect_error": "⚠️ Error occurred while reselecting input source: {error}",
                "select_input_source": "Select Input Source",
                "select_data_source": "Please select data source:",
                "use_local_rawdata": "Use local RawData folder",
                "images_count": " images",
                "ok": "OK",
                "cancel": "Cancel",
                "error": "Error",
                "warning": "Warning",
                "folder_not_found": "Folder '{folder}' not found",
                "no_processable_files": "No processable files found in '{folder}'",
                "select_processing_range": "Select Processing Range",
                "found_images": "Found {count} images to process",
                "settings_default": "Settings default value: {value}",
                "processing_range": "Processing range: 1 ~",
                "load_settings_failed": "⚠️ Failed to load settings file: {error}",
                "user_cancelled_operation": "⚠️ User cancelled operation or closed window",
                "processing_from_airsim": "📁 Processing data directly from AirSim folder: {source}",
                "processing_from_local": "📁 Processing data from local RawData folder: {folder}",
                "manual_put_rawdata": "⚠️ Please manually put raw data into '{folder}' folder and run again.",
                "user_cancelled_range": "⚠️ User cancelled processing range selection",
                "processing_range_info": "🔄 Processing images {start} to {end}",
                "clearing_folder": "🔄 Clearing existing '{folder}' folder...",
                "folder_created": "✅ Created '{folder}' folder.",
                "files_found": "📁 Files found: Img0={img0}, Img1={img1}, Seg={seg}, PFM={pfm}",
                "processed_img_left": "✅ Processed {count} 'img_left0' files.",
                "processed_img_right": "✅ Processed {count} 'img_right_0' files.",
                "processed_img_seg": "✅ Processed {count} 'img_front_left_5' files.",
                "processed_pfm_depth": "✅ Processed {count} '.pfm' files, limited max depth to {depth}m.",
                "file_processing_error": "⚠️ Error processing file {file}: {error}",
                "source_folder_not_exist": "⚠️ Error: Source folder '{folder}' does not exist, cannot copy to results folder.",
                "result_folder_created": "✅ Created results folder: '{folder}'",
                "clearing_result_folder": "🔄 Clearing existing results folder: '{folder}'",
                "delete_file_failed": "⚠️ Failed to delete {file}: {error}",
                "copying_files": "🔄 Starting to copy non-Seg files to '{folder}'...",
                "files_found_pattern": "📁 Found {pattern} files in '{folder}': {count} files",
                "copy_file_failed": "⚠️ Failed to copy {file}: {error}",
                "files_copied": "✅ Copied {count} files to '{folder}' (excluding Seg)",
                "rawdata_found_files": "📁 Found {img_count} image files and {pfm_count} PFM files in RawData folder, starting complete processing flow...",
                "program_ended": "⚠️ Program ended",
                "rawdata_no_files": "📁 RawData folder exists but has no processable files, opening AirSim folder selection...",
                "rawdata_not_found": "📁 RawData folder not found, opening AirSim folder selection...",
                "starting_pfm_conversion": "🔄 Starting PFM conversion...",
                "camera_params": "⚙️ Using camera parameters: FOV={fov}°, Resolution={width}x{height}, Baseline={baseline}m, Max Depth={depth}m"
            }
        }
        
        self.setWindowTitle(self.texts[self.current_language]["title"])
        self.setGeometry(300, 300, 800, 600)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
        """)
        
        self.init_ui()
        
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 標題
        self.title_label = QLabel(self.texts[self.current_language]["progress_title"])
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
        
        # 當前狀態標籤（隱藏）
        self.status_label = QLabel(self.texts[self.current_language]["ready"])
        self.status_label.setAlignment(Qt.AlignCenter)
        status_font = QFont("Microsoft YaHei", 12)
        self.status_label.setFont(status_font)
        self.status_label.setStyleSheet("""
            QLabel {
                color: #34495e;
                background-color: #ffffff;
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        self.status_label.hide()  # 隱藏狀態標籤
        layout.addWidget(self.status_label)
        
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
        layout.addWidget(self.progress_bar)
        
        # 重選輸入源按鈕
        self.reselect_input_btn = QPushButton(self.texts[self.current_language]["reselect_input"])
        self.reselect_input_btn.clicked.connect(self.reselect_input_source)
        self.reselect_input_btn.setStyleSheet("""
            QPushButton {
                background-color: #f39c12;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
                padding: 12px 20px;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #e67e22;
            }
            QPushButton:pressed {
                background-color: #d35400;
            }
        """)
        layout.addWidget(self.reselect_input_btn)
        
        # 詳細日誌區域
        self.log_label = QLabel(self.texts[self.current_language]["log_title"])
        log_font = QFont("Microsoft YaHei", 11, QFont.Bold)
        self.log_label.setFont(log_font)
        self.log_label.setStyleSheet("color: #2c3e50; margin-top: 10px;")
        layout.addWidget(self.log_label)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
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
        layout.addWidget(self.log_text)
        
        # 底部按鈕
        button_layout = QHBoxLayout()
        
        self.close_btn = QPushButton(self.texts[self.current_language]["close"])
        self.close_btn.clicked.connect(self.close)
        self.close_btn.setEnabled(False)  # 初始時禁用
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 12px;
                font-weight: bold;
                padding: 10px 20px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
                color: #7f8c8d;
            }
        """)
        
        # 語言切換按鈕
        self.language_btn = QPushButton(self.texts[self.current_language]["language"])
        self.language_btn.clicked.connect(self.toggle_language)
        self.language_btn.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 12px;
                font-weight: bold;
                padding: 10px 20px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
        """)
        
        button_layout.addWidget(self.language_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.close_btn)
        
        layout.addLayout(button_layout)
        
    def toggle_language(self):
        """切換語言"""
        if self.current_language == "zh":
            self.current_language = "en"
        else:
            self.current_language = "zh"
        
        # 更新視窗標題
        self.setWindowTitle(self.texts[self.current_language]["title"])
        
        # 更新UI文字
        self.title_label.setText(self.texts[self.current_language]["progress_title"])
        self.log_label.setText(self.texts[self.current_language]["log_title"])
        self.close_btn.setText(self.texts[self.current_language]["close"])
        self.language_btn.setText(self.texts[self.current_language]["language"])
        self.reselect_input_btn.setText(self.texts[self.current_language]["reselect_input"])
        
        # 更新狀態標籤（如果沒有在處理中）
        if not self.close_btn.isEnabled():
            self.status_label.setText(self.texts[self.current_language]["ready"])

    def reselect_input_source(self):
        """重新選擇輸入源"""
        try:
            # 重置進度和狀態
            self.progress_bar.setValue(0)
            self.status_label.setText(self.texts[self.current_language]["ready"])
            self.close_btn.setEnabled(False)
            
            # 清空日誌
            self.log_text.clear()
            self.add_log(self.texts[self.current_language]["reselect_input_log"])
            
            # 直接調用輸入源選擇和處理流程
            self.restart_processing()
            
        except Exception as e:
            self.add_log(self.texts[self.current_language]["reselect_error"].format(error=e))

    def restart_processing(self):
        """重新開始處理流程"""
        try:
            # 重置進度
            self.set_progress_range(0, 100)
            self.update_progress(0, 100)
            
            # 重新執行主要處理邏輯
            self.add_log(self.texts[self.current_language]["start_processing"])
            
            # 調用輸入源選擇和處理函數
            process_result = process_raw_data()
            if process_result is None:
                self.add_log(self.texts[self.current_language]["user_cancelled"])
                self.close_btn.setEnabled(True)
                return
                
            self.update_progress(60, 100)
            
            # 繼續執行 PFM 轉換
            pfm_start_msg = "🔄 開始執行 PFM 轉換..." if self.current_language == "zh" else "🔄 Starting PFM conversion..."
            self.add_log(pfm_start_msg)
            self.update_progress(65, 100)
            
            # 從設定檔案讀取相機參數
            settings = load_settings()
            FOV_degrees = settings.get('FOV_degrees', 90)
            image_width = settings.get('image_width', 640)
            image_height = settings.get('image_height', 480)
            baseline_meters = settings.get('baseline_meters', 1.0)
            max_depth = settings.get('MaxDepth', 100.0)

            camera_params_msg = f"⚙️ 使用相機參數：FOV={FOV_degrees}°, 解析度={image_width}x{image_height}, 基線={baseline_meters}m, 最大深度={max_depth}m" if self.current_language == "zh" else f"⚙️ Using camera parameters: FOV={FOV_degrees}°, Resolution={image_width}x{image_height}, Baseline={baseline_meters}m, Max Depth={max_depth}m"
            self.add_log(camera_params_msg)
            self.update_progress(70, 100)

            focal_length = (image_width / 2) / np.tan(np.deg2rad(FOV_degrees / 2))

            input_folder = "ProcessData"
            output_folder = "ProcessData"

            pfm_files = [f for f in os.listdir(input_folder) if f.startswith('DepthGT_') and f.endswith(".pfm")]
            pfm_files.sort(key=lambda x: int(x.split('_')[-1].split('.')[0]))
            
            self.update_progress(75, 100)

            for index, filename in enumerate(pfm_files):
                input_path = os.path.join(input_folder, filename)
                
                new_filename = f"Disparity_{index + 1}.pfm"
                output_path = os.path.join(output_folder, new_filename)
                depth_to_disparity(input_path, output_path, focal_length, baseline_meters, max_depth)
                
                # 更新進度
                pfm_progress = 75 + int((index + 1) / len(pfm_files) * 15)
                self.update_progress(pfm_progress, 100)
                
            pfm_complete_msg = f"✅ 已處理 {len(pfm_files)} 個 '.pfm' 檔案，完成深度到視差轉換。" if self.current_language == "zh" else f"✅ Processed {len(pfm_files)} '.pfm' files, completed depth to disparity conversion."
            self.add_log(pfm_complete_msg)
            self.update_progress(90, 100)
            
            copy_start_msg = "🔄 開始複製檔案到結果資料夾..." if self.current_language == "zh" else "🔄 Starting to copy files to results folder..."
            self.add_log(copy_start_msg)
            copy_to_results()
            self.update_progress(100, 100)
            
            complete_msg = "🎉 所有處理完成！" if self.current_language == "zh" else "🎉 All processing completed!"
            self.add_log(complete_msg)
            self.processing_complete()
            
        except Exception as e:
            self.add_log(self.texts[self.current_language]["processing_error"].format(error=e))
            self.close_btn.setEnabled(True)

    def add_log(self, message):
        """添加日誌訊息"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        
        self.log_text.append(log_message)
        
        # 自動滾動到底部
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
        # 強制更新 UI
        QApplication.processEvents()
        
    def update_status(self, status):
        """更新狀態標籤"""
        self.status_label.setText(status)
        QApplication.processEvents()
        
    def update_progress(self, current, total):
        """更新進度條"""
        if total > 0:
            progress = int((current / total) * 100)
            self.progress_bar.setValue(progress)
            self.progress_bar.setFormat(f"{current}/{total} ({progress}%)")
        QApplication.processEvents()
        
    def set_progress_range(self, minimum, maximum):
        """設定進度條範圍"""
        self.progress_bar.setRange(minimum, maximum)
        QApplication.processEvents()
        
    def processing_complete(self):
        """處理完成"""
        complete_status = "✅ 處理完成！" if self.current_language == "zh" else "✅ Processing completed!"
        self.status_label.setText(complete_status)
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
        self.progress_bar.setValue(self.progress_bar.maximum())
        self.close_btn.setEnabled(True)
        complete_log = "🎉 所有處理步驟已完成！" if self.current_language == "zh" else "🎉 All processing steps completed!"
        self.add_log(complete_log)
        QApplication.processEvents()

# 全局進度視窗實例
progress_window = None

def get_text(key, **kwargs):
    """獲取多語言文字"""
    current_language = os.environ.get('AIRSIM_LANGUAGE', 'zh')  # 從環境變數讀取
    if progress_window:
        current_language = progress_window.current_language
    
    # 語言文字
    texts = {
        "zh": {
            "load_settings_failed": "⚠️ 載入設定檔案失敗：{error}",
            "user_cancelled_operation": "⚠️ 使用者取消操作或關閉視窗",
            "processing_from_airsim": "📁 將直接從 AirSim 資料夾處理資料：{source}",
            "processing_from_local": "📁 將從本地 RawData 資料夾處理資料：{folder}",
            "manual_put_rawdata": "⚠️ 請手動將原始資料放入 '{folder}' 資料夾後再執行。",
            "user_cancelled_range": "⚠️ 使用者取消處理範圍選擇",
            "processing_range_info": "🔄 將處理第 {start} 到第 {end} 張圖片",
            "clearing_folder": "🔄 清空現有的 '{folder}' 資料夾...",
            "folder_created": "✅ 已建立 '{folder}' 資料夾。",
            "files_found": "📁 找到檔案數量：Img0={img0}, Img1={img1}, Seg={seg}, PFM={pfm}",
            "processed_img_left": "✅ 已處理 {count} 個 'img_left0' 檔案。",
            "processed_img_right": "✅ 已處理 {count} 個 'img_right_0' 檔案。",
            "processed_img_seg": "✅ 已處理 {count} 個 'img_front_left_5' 檔案。",
            "processed_pfm_depth": "✅ 已處理 {count} 個 '.pfm' 檔案，並限制最大深度為 {depth}m。",
            "file_processing_error": "⚠️ 處理檔案 {file} 時發生錯誤: {error}",
            "source_folder_not_exist": "⚠️ 錯誤：來源資料夾 '{folder}' 不存在，無法複製到結果資料夾。",
            "result_folder_created": "✅ 已建立結果資料夾：'{folder}'",
            "clearing_result_folder": "🔄 清空現有結果資料夾：'{folder}'",
            "delete_file_failed": "⚠️ 刪除 {file} 失敗：{error}",
            "copying_files": "🔄 開始複製非 Seg 檔案到 '{folder}'...",
            "files_found_pattern": "📁 在 '{folder}' 找到 {pattern} 檔案：{count} 個",
            "copy_file_failed": "⚠️ 複製 {file} 失敗：{error}",
            "files_copied": "✅ 已複製 {count} 個檔案到 '{folder}'（不包含 Seg）",
            "rawdata_found_files": "📁 發現 RawData 資料夾中有 {img_count} 個圖片文件和 {pfm_count} 個 PFM 文件，開始完整處理流程...",
            "program_ended": "⚠️ 程式已結束",
            "rawdata_no_files": "📁 RawData 資料夾存在但沒有可處理的文件，打開 AirSim 資料夾選擇功能...",
            "rawdata_not_found": "📁 找不到 RawData 資料夾，打開 AirSim 資料夾選擇功能...",
            "starting_pfm_conversion": "🔄 開始執行 PFM 轉換...",
            "camera_params": "⚙️ 使用相機參數：FOV={fov}°, 解析度={width}x{height}, 基線={baseline}m, 最大深度={depth}m"
        },
        "en": {
            "load_settings_failed": "⚠️ Failed to load settings file: {error}",
            "user_cancelled_operation": "⚠️ User cancelled operation or closed window",
            "processing_from_airsim": "📁 Processing data directly from AirSim folder: {source}",
            "processing_from_local": "📁 Processing data from local RawData folder: {folder}",
            "manual_put_rawdata": "⚠️ Please manually put raw data into '{folder}' folder and run again.",
            "user_cancelled_range": "⚠️ User cancelled processing range selection",
            "processing_range_info": "🔄 Processing images {start} to {end}",
            "clearing_folder": "🔄 Clearing existing '{folder}' folder...",
            "folder_created": "✅ Created '{folder}' folder.",
            "files_found": "📁 Files found: Img0={img0}, Img1={img1}, Seg={seg}, PFM={pfm}",
            "processed_img_left": "✅ Processed {count} 'img_left0' files.",
            "processed_img_right": "✅ Processed {count} 'img_right_0' files.",
            "processed_img_seg": "✅ Processed {count} 'img_front_left_5' files.",
            "processed_pfm_depth": "✅ Processed {count} '.pfm' files, limited max depth to {depth}m.",
            "file_processing_error": "⚠️ Error processing file {file}: {error}",
            "source_folder_not_exist": "⚠️ Error: Source folder '{folder}' does not exist, cannot copy to results folder.",
            "result_folder_created": "✅ Created results folder: '{folder}'",
            "clearing_result_folder": "🔄 Clearing existing results folder: '{folder}'",
            "delete_file_failed": "⚠️ Failed to delete {file}: {error}",
            "copying_files": "🔄 Starting to copy non-Seg files to '{folder}'...",
            "files_found_pattern": "📁 Found {pattern} files in '{folder}': {count} files",
            "copy_file_failed": "⚠️ Failed to copy {file}: {error}",
            "files_copied": "✅ Copied {count} files to '{folder}' (excluding Seg)",
            "rawdata_found_files": "📁 Found {img_count} image files and {pfm_count} PFM files in RawData folder, starting complete processing flow...",
            "program_ended": "⚠️ Program ended",
            "rawdata_no_files": "📁 RawData folder exists but has no processable files, opening AirSim folder selection...",
            "rawdata_not_found": "📁 RawData folder not found, opening AirSim folder selection...",
            "starting_pfm_conversion": "🔄 Starting PFM conversion...",
            "camera_params": "⚙️ Using camera parameters: FOV={fov}°, Resolution={width}x{height}, Baseline={baseline}m, Max Depth={depth}m"
        }
    }
    
    if key in texts[current_language]:
        return texts[current_language][key].format(**kwargs)
    else:
        return key  # 如果找不到鍵值，返回鍵值本身

def log_message(message, update_status=False):
    """全局日誌函數，優先使用進度視窗顯示"""
    global progress_window
    if progress_window:
        progress_window.add_log(message)
        if update_status:
            # 移除時間戳記和表情符號用於狀態顯示
            status = message.split('] ', 1)[-1] if '] ' in message else message
            status = status.replace('🔄 ', '').replace('✅ ', '').replace('📁 ', '').replace('⚠️ ', '')
            progress_window.update_status(status)
    else:
        # 移除表情符號用於終端機顯示
        clean_message = message.replace('🔄 ', '').replace('✅ ', '').replace('📁 ', '').replace('⚠️ ', '')
        print(clean_message)

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
            log_message(get_text("load_settings_failed", error=e))
    
    return settings

def find_airsim_data_folders():
    """
    從 AirSim 資料夾尋找資料夾
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # 修正：AirSim 資料夾在 DataGenerator 的上一級目錄
    airsim_dir = os.path.dirname(os.path.dirname(current_dir))
    
    if not os.path.exists(airsim_dir):
        return []
    
    data_folders = []
    for item in os.listdir(airsim_dir):
        item_path = os.path.join(airsim_dir, item)
        if os.path.isdir(item_path):
            if re.match(r'\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2}', item):
                images_path = os.path.join(item_path, 'images')
                if os.path.exists(images_path):
                    data_folders.append({
                        'name': item,
                        'path': item_path,
                        'images_path': images_path
                    })
    
    data_folders.sort(key=lambda x: x['name'], reverse=True)
    return data_folders

def select_input_source():
    """
    顯示對話框讓使用者選擇輸入源
    """
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    settings = load_settings()
    input_airsim = settings.get('Input_Airsim', False)
    
    dialog = QDialog()
    # 獲取當前語言設定
    current_language = os.environ.get('AIRSIM_LANGUAGE', 'zh')  # 從環境變數讀取
    if progress_window:
        current_language = progress_window.current_language
    
    # 語言文字
    texts = {
        "zh": {
            "select_input_source": "選擇輸入源",
            "select_data_source": "請選擇資料來源：",
            "use_local_rawdata": "使用本地 RawData 資料夾",
            "images_count": "張圖片",
            "ok": "確定",
            "cancel": "取消",
            "warning": "警告",
            "no_airsim_folders": "在 AirSim 資料夾中找不到符合格式的資料夾"
        },
        "en": {
            "select_input_source": "Select Input Source",
            "select_data_source": "Please select data source:",
            "use_local_rawdata": "Use local RawData folder",
            "images_count": " images",
            "ok": "OK",
            "cancel": "Cancel",
            "warning": "Warning",
            "no_airsim_folders": "No folders matching the format found in AirSim folder"
        }
    }
    
    dialog.setWindowTitle(texts[current_language]["select_input_source"])
    dialog.setFixedSize(400, 200)
    
    layout = QVBoxLayout()
    
    info_label = QLabel(texts[current_language]["select_data_source"])
    layout.addWidget(info_label)
    
    combo = QComboBox()
    
    combo.addItem(texts[current_language]["use_local_rawdata"], "local")
    
    if input_airsim:
        airsim_folders = find_airsim_data_folders()
        if airsim_folders:
            for folder in airsim_folders:
                images_count = len([f for f in os.listdir(folder['images_path']) if f.endswith('.png')])
                display_text = f"{folder['name']} ({images_count//3} {texts[current_language]['images_count']})"
                combo.addItem(display_text, folder['images_path'])
    
    layout.addWidget(combo)
    
    button_layout = QHBoxLayout()
    ok_button = QPushButton(texts[current_language]["ok"])
    cancel_button = QPushButton(texts[current_language]["cancel"])
    
    ok_button.clicked.connect(dialog.accept)
    cancel_button.clicked.connect(dialog.reject)
    
    button_layout.addWidget(ok_button)
    button_layout.addWidget(cancel_button)
    layout.addLayout(button_layout)
    
    dialog.setLayout(layout)
    
    result = dialog.exec_()
    
    if result == QDialog.Accepted:
        return combo.currentData()
    else:
        return None

def read_pfm(file_path):
    """
    從 PFM 檔案讀取數據，返回一個 NumPy 陣列。
    """
    with open(file_path, 'rb') as file:
        color = file.readline().decode('utf-8').strip()
        if color not in ['PF', 'Pf']:
            raise Exception('不是有效的 PFM 檔案！')

        width, height = re.findall(r'\d+', file.readline().decode('utf-8'))
        width, height = int(width), int(height)

        scale = float(file.readline().decode('utf-8').strip())
        if scale < 0:
            data = np.fromfile(file, '<f4')
        else:
            data = np.fromfile(file, '>f4')

        shape = (height, width, 3) if color == 'PF' else (height, width)
        return np.reshape(data, shape)

def write_pfm(file_path, image, scale=-1.0):
    """
    將 NumPy 陣列儲存為 PFM 檔案。
    """
    image = image.astype(np.float32)

    with open(file_path, 'wb') as f:
        header = 'Pf\n' if image.ndim == 2 else 'PF\n'
        f.write(header.encode('ascii'))

        height, width = image.shape[:2]
        f.write(f'{width} {height}\n'.encode('ascii'))

        f.write(f'{scale}\n'.encode('ascii'))
        image.tofile(f)

def get_processing_range(raw_data_folder='RawData'):
    """
    顯示對話框讓使用者選擇處理範圍
    """
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    # 獲取當前語言設定
    current_language = os.environ.get('AIRSIM_LANGUAGE', 'zh')  # 從環境變數讀取
    if progress_window:
        current_language = progress_window.current_language
    
    # 語言文字
    texts = {
        "zh": {
            "error": "錯誤",
            "folder_not_found": "找不到 '{folder}' 資料夾",
            "no_processable_files": "在 '{folder}' 中找不到可處理的檔案",
            "select_processing_range": "選擇處理範圍",
            "found_images": "找到 {count} 張圖片可處理",
            "settings_default": "設定檔預設值：{value}",
            "processing_range": "處理範圍: 1 ~",
            "ok": "確定",
            "cancel": "取消"
        },
        "en": {
            "error": "Error",
            "folder_not_found": "Folder '{folder}' not found",
            "no_processable_files": "No processable files found in '{folder}'",
            "select_processing_range": "Select Processing Range",
            "found_images": "Found {count} images to process",
            "settings_default": "Settings default value: {value}",
            "processing_range": "Processing range: 1 ~",
            "ok": "OK",
            "cancel": "Cancel"
        }
    }
    
    if not os.path.exists(raw_data_folder):
        QMessageBox.warning(None, texts[current_language]["error"], texts[current_language]["folder_not_found"].format(folder=raw_data_folder))
        return None, None
    
    all_files = os.listdir(raw_data_folder)
    # 使用更通用的匹配模式：img_*_left_0, img_*_right_0, img_*_left_5
    img_left_files = [f for f in all_files if ('_left_0' in f and f.startswith('img_') and f.endswith('.png'))]
    img_right_files = [f for f in all_files if ('_right_0' in f and f.startswith('img_') and f.endswith('.png'))]
    img_seg_files = [f for f in all_files if ('_left_5' in f and f.startswith('img_') and f.endswith('.png'))]
    pfm_files = [f for f in all_files if f.endswith('.pfm')]
    
    max_images = max(len(img_left_files), len(img_right_files), len(img_seg_files), len(pfm_files))
    
    if max_images == 0:
        QMessageBox.warning(None, texts[current_language]["error"], texts[current_language]["no_processable_files"].format(folder=raw_data_folder))
        return None, None
    
    # 從設定檔讀取預設的Frame_Num值
    settings = load_settings()
    default_frame_num = settings.get('Frame_Num', 600)  # 預設600，如果讀取失敗
    
    dialog = QDialog()
    dialog.setWindowTitle(texts[current_language]["select_processing_range"])
    dialog.setFixedSize(350, 180)
    
    layout = QVBoxLayout()
    
    info_label = QLabel(texts[current_language]["found_images"].format(count=max_images))
    layout.addWidget(info_label)
    
    # 顯示從設定檔讀取的預設值
    default_info = QLabel(texts[current_language]["settings_default"].format(value=default_frame_num))
    default_info.setStyleSheet("color: #7f8c8d; font-size: 10px;")
    layout.addWidget(default_info)
    
    range_layout = QHBoxLayout()
    range_layout.addWidget(QLabel(texts[current_language]["processing_range"]))
    
    spinbox = QSpinBox()
    spinbox.setMinimum(1)
    spinbox.setMaximum(int(max_images))
    # 使用設定檔中的Frame_Num作為預設值，但不能超過實際找到的檔案數量
    spinbox.setValue(min(default_frame_num, int(max_images)))
    range_layout.addWidget(spinbox)
    
    layout.addLayout(range_layout)
    
    button_layout = QHBoxLayout()
    ok_button = QPushButton(texts[current_language]["ok"])
    cancel_button = QPushButton(texts[current_language]["cancel"])
    
    ok_button.clicked.connect(dialog.accept)
    cancel_button.clicked.connect(dialog.reject)
    
    button_layout.addWidget(ok_button)
    button_layout.addWidget(cancel_button)
    layout.addLayout(button_layout)
    
    dialog.setLayout(layout)
    
    result = dialog.exec_()
    
    if result == QDialog.Accepted:
        return 1, spinbox.value()
    else:
        return None, None

def process_raw_data(raw_data_folder='RawData', processed_data_folder='ProcessData'):
    """
    處理原始資料夾中的檔案，並將處理後的檔案移動到 ProcessData 資料夾。
    """
    settings = load_settings()
    processed_data_folder = settings.get('output_folder_Seg', 'ProcessData')

    input_source = select_input_source()
    if input_source is None:
        log_message(get_text("user_cancelled_operation"))
        return None
    
    source_for_processing = raw_data_folder
    if input_source != "local":
        log_message(get_text("processing_from_airsim", source=input_source), update_status=True)
        source_for_processing = input_source # 直接使用 AirSim 的 images 資料夾作為來源
    else:
        log_message(get_text("processing_from_local", folder=raw_data_folder), update_status=True)
        if os.path.exists(raw_data_folder):
            shutil.rmtree(raw_data_folder)
        os.makedirs(raw_data_folder)
        log_message(get_text("manual_put_rawdata", folder=raw_data_folder))
        return None # 在此處返回，讓使用者準備 RawData 資料夾

    # 注意：get_processing_range 現在需要從 source_for_processing 來計算最大圖片數
    start_idx, end_idx = get_processing_range(source_for_processing)
    if start_idx is None:
        log_message(get_text("user_cancelled_range"))
        return None
    
    log_message(get_text("processing_range_info", start=start_idx, end=end_idx), update_status=True)
    
    if os.path.exists(processed_data_folder):
        log_message(get_text("clearing_folder", folder=processed_data_folder), update_status=True)
        shutil.rmtree(processed_data_folder)
    
    os.makedirs(processed_data_folder)
    log_message(get_text("folder_created", folder=processed_data_folder))

    all_files = os.listdir(source_for_processing)

    img_left_files = []
    img_right_files = []
    img_left_Seg_files = []
    pfm_files = []

    for file in all_files:
        # 使用更通用的匹配模式：img_*_left_0, img_*_right_0, img_*_left_5
        if '_left_0' in file and file.startswith('img_') and file.endswith('.png'):
            img_left_files.append(file)
        elif '_right_0' in file and file.startswith('img_') and file.endswith('.png'):
            img_right_files.append(file)
        elif '_left_5' in file and file.startswith('img_') and file.endswith('.png'):
            img_left_Seg_files.append(file)
        elif file.endswith('.pfm'):
            pfm_files.append(file)

    log_message(get_text("files_found", img0=len(img_left_files), img1=len(img_right_files), seg=len(img_left_Seg_files), pfm=len(pfm_files)))

    img_left_files.sort(key=lambda x: int(x.split('_')[-1].split('.')[0]))
    img_left_files = img_left_files[start_idx-1:end_idx]
    for i, old_name in enumerate(img_left_files):
        new_name = f'Img0_{start_idx + i}.png'
        shutil.copy(os.path.join(source_for_processing, old_name), os.path.join(processed_data_folder, new_name))
    
    log_message(get_text("processed_img_left", count=len(img_left_files)))

    img_right_files.sort(key=lambda x: int(x.split('_')[-1].split('.')[0]))
    img_right_files = img_right_files[start_idx-1:end_idx]
    for i, old_name in enumerate(img_right_files):
        new_name = f'Img1_{start_idx + i}.png'
        shutil.copy(os.path.join(source_for_processing, old_name), os.path.join(processed_data_folder, new_name))
        
    log_message(get_text("processed_img_right", count=len(img_right_files)))

    img_left_Seg_files.sort(key=lambda x: int(x.split('_')[-1].split('.')[0]))
    img_left_Seg_files = img_left_Seg_files[start_idx-1:end_idx]
    for i, old_name in enumerate(img_left_Seg_files):
        new_name = f'Seg_{start_idx + i}.png'
        shutil.copy(os.path.join(source_for_processing, old_name), os.path.join(processed_data_folder, new_name))
        
    log_message(get_text("processed_img_seg", count=len(img_left_Seg_files)))

    pfm_files.sort(key=lambda x: int(x.split('_')[-1].split('.')[0]))
    pfm_files = pfm_files[start_idx-1:end_idx]
    
    # 讀取設定檔中的MaxDepth參數
    max_depth = settings.get('MaxDepth', 100.0)
    
    for i, old_name in enumerate(pfm_files):
        input_path = os.path.join(source_for_processing, old_name)
        new_name = f'DepthGT_{start_idx + i}.pfm'
        output_path = os.path.join(processed_data_folder, new_name)
        
        # 讀取原始深度圖
        pfm_data = read_pfm(input_path)
        
        # 限制最小深度值
        pfm_data[pfm_data < 1e-6] = 1e-6
        
        # 限制最大深度值為MaxDepth
        pfm_data[pfm_data > max_depth] = max_depth
        
        # 寫入處理後的深度圖到ProcessData
        write_pfm(output_path, pfm_data)
        
    log_message(get_text("processed_pfm_depth", count=len(pfm_files), depth=max_depth))

    # 如果 input_source != "local"，則直接從 AirSim 資料夾處理，不影響 RawData

    return True

def depth_to_disparity(depth_image_path, disparity_image_path, focal_length, baseline, max_depth=100.0):
    """
    將深度 PFM 檔案轉換為視差 PFM 檔案。
    """
    try:
        depth_image = read_pfm(depth_image_path)
        
        # 限制最小深度值
        depth_image[depth_image < 1e-6] = 1e-6
        
        # 限制最大深度值
        depth_image[depth_image > max_depth] = max_depth

        # 使用相機內參計算視差圖
        disparity_image = (focal_length * baseline) / depth_image
        
        write_pfm(disparity_image_path, disparity_image)
    except Exception as e:
        log_message(get_text("file_processing_error", file=depth_image_path, error=e))

def copy_to_results():
    """
    將處理後的檔案（除了 Seg）複製到第二個輸出資料夾 (Results\\Img)
    """
    settings = load_settings()
    
    source_folder_for_copy = settings.get('output_folder_Seg', 'ProcessData')
    output_folder_for_non_seg = settings.get('output_folder', 'Results\\Img')
    
    if not os.path.exists(source_folder_for_copy):
        log_message(get_text("source_folder_not_exist", folder=source_folder_for_copy))
        return
    
    if not os.path.exists(output_folder_for_non_seg):
        os.makedirs(output_folder_for_non_seg)
        log_message(get_text("result_folder_created", folder=output_folder_for_non_seg))
    else:
        log_message(get_text("clearing_result_folder", folder=output_folder_for_non_seg), update_status=True)
        for filename in os.listdir(output_folder_for_non_seg):
            file_path = os.path.join(output_folder_for_non_seg, filename)
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                log_message(get_text("delete_file_failed", file=filename, error=e))
    
    file_types_without_seg = [
        ("DepthGT_*.pfm", "Depth_"),
        ("Disparity_*.pfm", "Disparity_"),
        ("Img0_*.png", "Img0_"),
        ("Img1_*.png", "Img1_")
    ]
    
    total_copied = 0
    
    log_message(get_text("copying_files", folder=output_folder_for_non_seg), update_status=True)
    for pattern, prefix in file_types_without_seg:
        import glob
        files = glob.glob(os.path.join(source_folder_for_copy, pattern))
        log_message(get_text("files_found_pattern", folder=source_folder_for_copy, pattern=pattern, count=len(files)))
        files.sort(key=lambda x: int(x.split('_')[-1].split('.')[0]))
        
        for file_path in files:
            filename = os.path.basename(file_path)
            dest_path = os.path.join(output_folder_for_non_seg, filename)
            try:
                shutil.copy2(file_path, dest_path)
                total_copied += 1
            except Exception as e:
                log_message(get_text("copy_file_failed", file=filename, error=e))
    
    log_message(get_text("files_copied", count=total_copied, folder=output_folder_for_non_seg))

if __name__ == '__main__':
    # 創建 QApplication
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    # 創建並顯示進度視窗
    progress_window = DataGeneratorProgressWindow()
    globals()['progress_window'] = progress_window
    progress_window.show()
    
    # 設定總步驟數（大致估計）
    progress_window.set_progress_range(0, 100)
    progress_window.update_progress(0, 100)
    
    try:
        raw_data_folder = "RawData"
        progress_window.update_progress(5, 100)
        
        if os.path.exists(raw_data_folder):
            all_files = os.listdir(raw_data_folder)
            # 檢查是否有符合新格式的圖片檔案
            img_left_files = [f for f in all_files if ('_left_0' in f and f.startswith('img_') and f.endswith('.png'))]
            img_right_files = [f for f in all_files if ('_right_0' in f and f.startswith('img_') and f.endswith('.png'))]
            img_seg_files = [f for f in all_files if ('_left_5' in f and f.startswith('img_') and f.endswith('.png'))]
            img_files = img_left_files + img_right_files + img_seg_files
            pfm_files = [f for f in all_files if f.endswith('.pfm')]
            
            if img_files or pfm_files:
                log_message(get_text("rawdata_found_files", img_count=len(img_files), pfm_count=len(pfm_files)), update_status=True)
                progress_window.update_progress(10, 100)
                
                process_result = process_raw_data()
                if process_result is None:
                    log_message(get_text("program_ended"))
                    progress_window.close_btn.setEnabled(True)
                    app.exec_()
                    sys.exit(0)
                    
                progress_window.update_progress(60, 100)
            else:
                log_message(get_text("rawdata_no_files"), update_status=True)
                progress_window.update_progress(10, 100)
                
                process_result = process_raw_data()
                if process_result is None:
                    log_message(get_text("program_ended"))
                    progress_window.close_btn.setEnabled(True)
                    app.exec_()
                    sys.exit(0)
                    
                progress_window.update_progress(60, 100)
        else:
            log_message(get_text("rawdata_not_found"), update_status=True)
            progress_window.update_progress(10, 100)
            
            process_result = process_raw_data()
            if process_result is None:
                log_message(get_text("program_ended"))
                progress_window.close_btn.setEnabled(True)
                app.exec_()
                sys.exit(0)
                
            progress_window.update_progress(60, 100)
        
        log_message(get_text("starting_pfm_conversion"), update_status=True)
        progress_window.update_progress(65, 100)
        
        # 從設定檔案讀取相機參數
        settings = load_settings()
        FOV_degrees = settings.get('FOV_degrees', 90)
        image_width = settings.get('image_width', 640)
        image_height = settings.get('image_height', 480)
        baseline_meters = settings.get('baseline_meters', 1.0)
        max_depth = settings.get('MaxDepth', 100.0)  # 添加 MaxDepth 參數

        log_message(get_text("camera_params", fov=FOV_degrees, width=image_width, height=image_height, baseline=baseline_meters, depth=max_depth))
        progress_window.update_progress(70, 100)

        focal_length = (image_width / 2) / np.tan(np.deg2rad(FOV_degrees / 2))

        input_folder = "ProcessData"
        output_folder = "ProcessData"

        pfm_files = [f for f in os.listdir(input_folder) if f.startswith('DepthGT_') and f.endswith(".pfm")]
        pfm_files.sort(key=lambda x: int(x.split('_')[-1].split('.')[0]))
        
        progress_window.update_progress(75, 100)

        for index, filename in enumerate(pfm_files):
            input_path = os.path.join(input_folder, filename)
            
            new_filename = f"Disparity_{index + 1}.pfm"
            output_path = os.path.join(output_folder, new_filename)
            depth_to_disparity(input_path, output_path, focal_length, baseline_meters, max_depth)
            
            # 更新進度
            pfm_progress = 75 + int((index + 1) / len(pfm_files) * 15)
            progress_window.update_progress(pfm_progress, 100)
            
        pfm_complete_msg = f"✅ 已處理 {len(pfm_files)} 個 '.pfm' 檔案，完成深度到視差轉換。" if progress_window.current_language == "zh" else f"✅ Processed {len(pfm_files)} '.pfm' files, completed depth to disparity conversion."
        log_message(pfm_complete_msg)
        progress_window.update_progress(90, 100)
        
        copy_msg = "🔄 開始複製檔案到結果資料夾..." if progress_window.current_language == "zh" else "🔄 Starting to copy files to results folder..."
        log_message(copy_msg, update_status=True)
        copy_to_results()
        progress_window.update_progress(100, 100)
        
        complete_msg = "🎉 所有處理完成！" if progress_window.current_language == "zh" else "🎉 All processing completed!"
        log_message(complete_msg, update_status=True)
        progress_window.processing_complete()
        
    except Exception as e:
        error_msg = f"⚠️ 處理過程中發生錯誤：{e}" if progress_window.current_language == "zh" else f"⚠️ Error occurred during processing: {e}"
        log_message(error_msg)
        progress_window.close_btn.setEnabled(True)
    
    # 執行 QApplication 事件循環
    app.exec_()