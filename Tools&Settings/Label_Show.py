import os
import cv2
import numpy as np
import screeninfo
import re
def read_pfm_simple(file_path):
    try:
        with open(file_path, 'rb') as f:
            header = f.readline().decode('utf-8').strip()
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
    except Exception as e:
        print(f"讀取 PFM 檔案 {file_path} 失敗: {e}")
        return None

def load_settings():
    settings = {}
    settings_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Settings.txt")
    if os.path.exists(settings_file):
        with open(settings_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if ':' in line:
                    k, v = line.split(':', 1)
                elif '=' in line:
                    k, v = line.split('=', 1)
                else:
                    continue
                settings[k.strip()] = v.strip()
    return settings

settings = load_settings()
# PFM_FLIPUD = settings.get("PFM_flipud", "True").lower() == "true"  # 已停用反轉功能

image_list = []
current_index = 0
window_name = "Label Visualization"
predefined_classes = []
view_mode = "YOLO"
mot_lines = []

CATEGORIES = ["Img0 RGB", "Depth", "Disparity"]

current_category_idx = 0

script_dir = os.path.dirname(os.path.abspath(__file__))

# 調整資料夾路徑以適應新的檔案結構 (your_script_name.py 在 Display 資料夾下，這些在上一層)
yolo_folder = os.path.join(script_dir, "..","Results", "YOLO_Label")
mot_folder = os.path.join(script_dir, "..", "Results", "MOT_Label")
image_folder = os.path.join(script_dir, "..", "ProcessData")
classes_file = os.path.join(script_dir, "predefined_classes.txt")

WINDOW_WIDTH = int(settings.get("image_width", 1024))
WINDOW_HEIGHT = int(settings.get("image_height", 768))

def natural_sort_key(s):
    """
    用於自然排序的鍵函數，將字串中的數字部分轉換為整數以便正確排序。
    """
    return [int(text) if text.isdigit() else text.lower() for text in re.split('(\d+)', s)]

def visualize_yolo_boxes(image_path, label_path):
    """
    讀取圖片和 YOLO 標註，並在圖片上畫出標註框。
    參數:
        image_path (str): 圖片檔案的路徑。
        label_path (str): YOLO 標註檔案的路徑。
    回傳:
        numpy.ndarray: 畫有標註框的圖片，如果圖片無法讀取則為 None。
    """
    image = cv2.imread(image_path)
    if image is None:
        print(f"無法讀取圖像檔案：{image_path}")
        return None

    h, w, _ = image.shape
    
    if not os.path.exists(label_path):
        print(f"找不到標註檔案：{label_path}")
        return image
        
    with open(label_path, 'r') as f:
        lines = f.readlines()
    
    img_with_boxes = image.copy()

    for line in lines:
        parts = line.strip().split()
        if len(parts) < 5:
            continue
        
        class_id = int(parts[0])
        x_center, y_center, bbox_width, bbox_height = map(float, parts[1:])

        x_min = int((x_center - bbox_width / 2) * w)
        y_min = int((y_center - bbox_height / 2) * h)
        x_max = int((x_center + bbox_width / 2) * w)
        y_max = int((y_center + bbox_height / 2) * h)
        
        label = predefined_classes[class_id] if class_id < len(predefined_classes) else f"Class {class_id}"
        
        color = (int((class_id * 30 + 50) % 255), int((class_id * 60 + 100) % 255), int((class_id * 90 + 150) % 255))
        
        cv2.rectangle(img_with_boxes, (x_min, y_min), (x_max, y_max), color, 2)
        cv2.putText(img_with_boxes, label, (x_min, y_min - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)
    
    progress_text = f"Image {current_index + 1}/{len(image_list)} [YOLO]"
    cv2.putText(img_with_boxes, progress_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

    return img_with_boxes

def visualize_mot_boxes(image_path, frame_num, mot_lines):
    """
    在圖片上繪製 MOT 標註框，包含距離資訊
    """
    image = cv2.imread(image_path)
    if image is None:
        print(f"錯誤：無法載入圖片 {image_path}")
        return None
    
    boxes_drawn = 0
    for line in mot_lines:
        parts = line.strip().split(',') # 將這裡的 .split() 改為 .split(',')
        if len(parts) >= 10:  # MOT 格式：frame_id, track_id, x, y, w, h, conf, x_cam, y_cam, z
            try:
                line_frame_id = int(parts[0])
                
                if line_frame_id == frame_num:
                    track_id = int(parts[1])
                    x = float(parts[2]) 
                    y = float(parts[3])
                    width = float(parts[4])
                    height = float(parts[5])
                    class_id = int(parts[6]) # class_id 是第 7 個欄位 (索引 6)

                    x_cam = float(parts[7])
                    y_cam = float(parts[8]) 
                    z = float(parts[9])

                    x1 = int(x)
                    y1 = int(y)
                    x2 = int(x + width)
                    y2 = int(y + height)

                    color = (0, 255, 0)
                    cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)

                    label_text = f"ID:{track_id} X:{x_cam:.2f}m Y:{y_cam:.2f}m Z:{z:.2f}m"
                    cv2.putText(image, label_text, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                    boxes_drawn += 1
            except ValueError as ve:
                print(f"解析 MOT 標註行時發生錯誤: {line.strip()} - {ve}")
        else:
            print(f"MOT 標註行格式不正確 (期望 10 個欄位，實際 {len(parts)}): {line.strip()}")
            
    if boxes_drawn == 0:
        print(f"影格 {frame_num} 未繪製任何 MOT 框。")
    else:
        print(f"影格 {frame_num} 已繪製 {boxes_drawn} 個 MOT 框。")

    progress_text = f"Image {current_index + 1}/{len(image_list)} [MOT]"
    cv2.putText(image, progress_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

    return image

def display_current_image():
    """
    顯示目前索引對應的圖片，並應用縮放以填滿視窗。
    """
    if not image_list:
        return

    base_name = image_list[current_index]
    image_path = os.path.join(image_folder, base_name + ".png")

    img_to_show = None
    if view_mode == "YOLO":
        label_path = os.path.join(yolo_folder, base_name + ".txt")
        img_to_show = visualize_yolo_boxes(image_path, label_path)
    elif view_mode == "MOT": # 將這裡的 else 改為 elif view_mode == "MOT"
        m = re.search(r'(\d+)$', base_name)
        if m:
            frame_num = int(m.group(1))
        else:
            frame_num = current_index + 1 
        img_to_show = visualize_mot_boxes(image_path, frame_num, mot_lines)
    else:
        current_category = CATEGORIES[current_category_idx]
        image_name_prefix = current_category.split(' ')[0] # 例如 'Depth' 或 'Disparity'
        
        if image_name_prefix == "Depth":
            pfm_file_name = f"DepthGT_{base_name.split('_')[-1]}.pfm"
        elif image_name_prefix == "Disparity":
            pfm_file_name = f"Disparity_{base_name.split('_')[-1]}.pfm"
        else:
            return

        pfm_path = os.path.join(image_folder, pfm_file_name)
        if os.path.exists(pfm_path):
            try:
                pfm_data = read_pfm_simple(pfm_path)
                if pfm_data is not None:
                    data = pfm_data
                    img_to_show = cv2.normalize(data, None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8U)
                    img_to_show = cv2.applyColorMap(img_to_show, cv2.COLORMAP_JET)
                    cv2.putText(img_to_show, f"{current_category}: {pfm_file_name}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                else:
                    print(f"無法讀取 PFM 檔案數據: {pfm_path}")
            except Exception as e:
                print(f"處理 PFM 檔案 {pfm_path} 時發生錯誤: {e}")
        else:
            print(f"未找到 PFM 檔案: {pfm_path}")

    if img_to_show is not None:
        h, w, _ = img_to_show.shape

        scale_w = WINDOW_WIDTH / w
        scale_h = WINDOW_HEIGHT / h
        scale = min(scale_w, scale_h)

        new_w = int(w * scale)
        new_h = int(h * scale)

        resized_img = cv2.resize(img_to_show, (new_w, new_h), interpolation=cv2.INTER_LINEAR)

        if new_w < WINDOW_WIDTH or new_h < WINDOW_HEIGHT:
            canvas = np.zeros((WINDOW_HEIGHT, WINDOW_WIDTH, 3), dtype=np.uint8)
            x_offset = (WINDOW_WIDTH - new_w) // 2
            y_offset = (WINDOW_HEIGHT - new_h) // 2
            canvas[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = resized_img
            cv2.imshow(window_name, canvas)
        else:
            cv2.imshow(window_name, resized_img)

def main():
    """
    主函式，初始化並啟動顯示迴圈。
    """
    global image_list, predefined_classes, current_index, view_mode, mot_lines, window_name

    if not os.path.exists(classes_file):
        print(f"錯誤：找不到類別檔案 {classes_file}。請確認檔案是否存在。")
        return
    with open(classes_file, 'r') as f:
        predefined_classes = [line.strip() for line in f.readlines()]
    print("已讀取的類別：", predefined_classes)
    
    print(f"\n--- 偵錯資訊 ---")
    print(f"腳本所在目錄: {script_dir}")
    print(f"預期的 YOLO 資料夾路徑: {yolo_folder}")
    print(f"預期的 MOT 資料夾路徑: {mot_folder}")
    print(f"預期的圖片資料夾路徑: {image_folder}")
    print(f"預期的類別檔案路徑: {classes_file}")

    if not os.path.exists(image_folder):
        print(f"錯誤: 圖片資料夾不存在於預期路徑: {image_folder}")
        return
    if not os.path.exists(yolo_folder):
        print(f"警告: YOLO 資料夾不存在於預期路徑: {yolo_folder}")
    if not os.path.exists(mot_folder):
        print(f"警告: MOT 資料夾不存在於預期路徑: {mot_folder}")

    mot_lines = []
    
    print(f"嘗試讀取 MOT 標註檔案...")
    print(f"MOT 資料夾路徑: {mot_folder}")
    print(f"MOT 資料夾是否存在: {os.path.exists(mot_folder)}")
    
    if os.path.exists(mot_folder):
        mot_txt_files = [f for f in os.listdir(mot_folder) if f.endswith('.txt')]
        print(f"MOT 資料夾內容 (僅 .txt 檔案): {mot_txt_files}")

        if mot_txt_files:
            if "Img0.txt" in mot_txt_files:
                mot_file_to_load = os.path.join(mot_folder, "Img0.txt")
            else:
                mot_file_to_load = os.path.join(mot_folder, mot_txt_files[0])
            
            print(f"實際嘗試載入的 MOT 檔案: {mot_file_to_load}")

            try:
                with open(mot_file_to_load, 'r', encoding='utf-8') as f:
                    mot_lines = f.readlines()
                print(f"成功載入 MOT 標註，共 {len(mot_lines)} 行")
                if len(mot_lines) > 0:
                    print(f"第一行內容: {mot_lines[0].strip()}")
            except Exception as e:
                print(f"讀取 MOT 檔案 '{mot_file_to_load}' 時發生錯誤: {e}")
        else:
            print(f"在 '{mot_folder}' 中未找到任何 .txt 標註檔案。")
    else:
        print(f"警告: MOT 資料夾不存在: {mot_folder}")

    image_files_in_dir = [f for f in os.listdir(image_folder) if f.endswith(".png") and f.startswith("Img0_")]
    yolo_files_in_dir = [f for f in os.listdir(yolo_folder)] if os.path.exists(yolo_folder) else []

    print(f"在 {yolo_folder} 找到的 .txt 檔案: {yolo_files_in_dir[:5]} (最多顯示5個)")
    print(f"在 {image_folder} 找到的 Img0_*.png 檔案: {image_files_in_dir[:5]} (最多顯示5個)")
    print(f"--- 偵錯資訊結束 ---\n")

    image_files = [os.path.splitext(f)[0] for f in image_files_in_dir]
    image_list = sorted(image_files, key=natural_sort_key)
    
    if not image_list:
        print("在指定資料夾中找不到任何圖片。")
        return

    print(f"共找到 {len(image_list)} 張圖片。顯示順序 (前5個): {image_list[:5]} (最多顯示5個)")

    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, WINDOW_WIDTH, WINDOW_HEIGHT)

    try:
        monitors = screeninfo.get_monitors()
        if monitors:
            main_monitor = monitors[0]
            screen_w = main_monitor.width
            screen_h = main_monitor.height
            
            x_pos = (screen_w - WINDOW_WIDTH) // 2
            y_pos = (screen_h - WINDOW_HEIGHT) // 2
            cv2.moveWindow(window_name, x_pos, y_pos)
        else:
            print("無法取得螢幕資訊，將使用預設位置。")
    except Exception as e:
        print(f"發生錯誤：{e}，請確認是否已安裝 screeninfo 套件。")
        print("您可使用 'pip install screeninfo' 指令進行安裝。")
        print("將使用預設位置。")
    
    display_current_image()
    
    while True:
        key = cv2.waitKey(1)

        try:
            if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
                break
        except cv2.error:
            # 窗口已被關閉或不存在
            break
        
        if key == 27:
            break
        elif key == ord('a'):
            current_index = (current_index - 1 + len(image_list)) % len(image_list)
            display_current_image()
        elif key == ord('d'):
            current_index = (current_index + 1) % len(image_list)
            display_current_image()
        elif key == ord('y'):
            view_mode = "YOLO"
            display_current_image()
        elif key == ord('m'):
            view_mode = "MOT"
            display_current_image()

    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
