'''
---------------------------------------------------------------------------------------


模型调用逻辑


---------------------------------------------------------------------------------------
'''

import cv2
from ultralytics import YOLO
from pathlib import Path  # 处理跨平台路径问题
import time  # 新增时间模块用于FPS计算
from datetime import datetime
import shutil
import os
import random
from flask import jsonify

# 模型目录
model_p = YOLO(Path("utils") / 'model' / "persons.pt") # 人数统计模型
model_n = YOLO(Path("utils") / 'model' / "yolo11n.pt")
model_m = YOLO(Path("utils") / 'model' / "yolo11m.pt")
model_x = YOLO(Path("utils") / 'model' / "yolo11x.pt")

client_stats = {'fps': 0, 'counts': {}, 'store': 0, 'persons':0}  # 直接存储统计信息
current_frame = None # 用于截图和录制视频
is_recording = False # 标记是否正在录制
video_writer = None # OpenCV视频写入器实例
video_filename = None # 动态生成的视频路径
stream_active = True # 控制视频流中断
now_frame = None # 未处理的图像

# 保存目录
SAVE_SAVE_DIR = Path("file_storage") / "downloads" / "save" # 保存目录
SAVE_SAVE_DIR.mkdir(parents=True, exist_ok=True)

SAVE_DIR = Path("file_storage") / "downloads" / "cut" # 截图目录
SAVE_DIR.mkdir(parents=True, exist_ok=True)

VIDEO_SAVE_DIR = Path("file_storage") / "downloads" / "video" # 视频目录
VIDEO_SAVE_DIR.mkdir(parents=True, exist_ok=True)  

# 获取本机摄像头列表
def find_available_cameras(limit=10):
    available_cameras = []
    for i in range(limit):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            available_cameras.append(i)
            cap.release()
    return available_cameras

def process_frame(frame, model, params):
    # 人数统计
    if(params['model']=='p'):
        res = model.predict(frame, 
                            conf=params['model_confidence']/100.0, 
                            classes=[0])
        res_plotted = res[0].plot()        
        # 更新统计人数
        client_stats['persons'] = len(res[0].boxes)
        return res_plotted
    
    # 在这里对视频帧进行处理
    res = model.predict(frame, 
                       conf=params['model_confidence']/100.0, 
                       classes=names_to_ids(params['model_type']))
    res_plotted = res[0].plot()
    
    # 更新分类统计
    client_stats['counts'] = {} # 重置统计信息
    for result in res:
        boxes = result.boxes
        for cls in boxes.cls:
            class_id = int(cls)
            class_name = model.names[class_id]
            client_stats['counts'][class_name] = client_stats['counts'].get(class_name, 0) + 1
    
    return res_plotted

# 定义分类转换函数（分类名称 > 分类id）
def names_to_ids(target_names):
    names_mapping = {
        0: 'Using_phone',
        1: 'bend',
        2: 'bow_head',
        3: 'hand-raising',
        4: 'turn_head'
    }
    name_to_id = {v: k for k, v in names_mapping.items()}
    class_ids = []
    invalid_names = []
    for name in target_names:
        if name in name_to_id:
            class_ids.append(name_to_id[name])
        else:
            invalid_names.append(name)
    if invalid_names:
        print(f"警告：以下类别名称不存在于模型中: {invalid_names}")
    return class_ids

def generate_frames(params):
    global current_frame, stream_active, now_frame # 添加全局变量

    stream_active = True  # 每次调用重置状态

    # 选择使用的模型
    if params['model'] == 'm':
        model = model_m
    elif params['model'] == 'x':
        model = model_x
    elif params['model'] == 'n':
        model = model_n
    else:
        model = model_p

    # 输入源确认
    if params['type'] == 'video':
        # 视频
        print(f"视频路径:{params['name']}")
        cap = cv2.VideoCapture(params['name'])
    elif params['type'] == 'picture':
        # 读取图片文件
        frame = cv2.imread(params['name'])
        if frame is None:
            raise ValueError(f"无法加载图片: {params['name']}")
        
        now_frame = frame.copy() # 保存当前未处理图像
        # 处理图片帧
        processed_frame = process_frame(frame, model, params)
        current_frame = processed_frame.copy()  # 更新当前图片，用于截图功能
        
        # 编码为JPEG格式
        ret, buffer = cv2.imencode('.jpg', processed_frame)
        if not ret:
            raise ValueError("图片编码失败")
        frame_data = buffer.tobytes()
        
        # 持续生成同一帧（保持流连接）
        while True:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_data + b'\r\n')
            return  # 提前返回避免进入后续循环
    else:
        # 摄像头
        cap = cv2.VideoCapture(int(params['type']))
    
    # 初始化FPS统计
    start_time = time.time()
    frame_count = 0

    # 视频流处理
    try:
        while stream_active:
            ret, frame = cap.read()
            if not ret:
                break

            now_frame = frame.copy() # 保存当前未处理图像
            processed_frame = process_frame(frame, model, params)
            # 用于视频录制 -----------------------------------------------------------------------
            global is_recording, video_writer, video_filename
            # 录制逻辑
            if is_recording:
                if video_writer is None:
                    print('初始化视频写入器')
                    # 初始化视频写入器
                    frame_height, frame_width = processed_frame.shape[:2]
                    fourcc = cv2.VideoWriter_fourcc(*'XVID')  # 编解码器
                    fps = 20  # 假设帧率，可根据需要调整
                    video_writer = cv2.VideoWriter(str(video_filename), fourcc, fps, (frame_width, frame_height))
                    if not video_writer.isOpened():
                        print("无法初始化视频写入器")
                        is_recording = False
                        video_writer = None
                if video_writer is not None:
                    print('写入视频帧')
                    video_writer.write(processed_frame)
            # ------------------------------------------------------------------------------------

            # 更新FPS统计
            frame_count += 1
            current_time = time.time()
            if current_time - start_time >= 1:
                client_stats['fps'] = int(frame_count / (current_time - start_time))
                frame_count = 0
                start_time = current_time

            # 新增5秒保存逻辑
            if params['if_save'] == 'true':  # 检查保存开关
                print('保存功能生效')
                current_time = time.time()
                # 初始赋值last_save_time（使用闭包变量）
                try: 
                    last_save_time 
                except NameError: 
                    last_save_time = time.time() - 5  # 确保首次触发

                if current_time - last_save_time >= 5:
                    print('5s 已到，保存功能启动')
                    # 检查是否有检测结果
                    if client_stats['counts']:
                        # 保存当前帧
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"auto_save_{timestamp}.jpg"
                        save_path = SAVE_SAVE_DIR / filename
                        cv2.imwrite(str(save_path), current_frame)
                        print(f"已保存当前帧到: {save_path}")
                        last_save_time = current_time

            # 转换为JPEG并生成帧
            ret, buffer = cv2.imencode('.jpg', processed_frame)

            current_frame = processed_frame.copy()  # 更新当前图片，用于截图功能

            frame_data = buffer.tobytes()
            yield (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + frame_data + b'\r\n')
    finally:
        cap.release()
        print("摄像头资源已释放")

# 视频流终止
def stop_stream():
    global stream_active
    stream_active = False
    print("已发送终止信号")

def get_video_stats():
    # 获取视频统计信息
    global client_stats

    # 根据操作系统选择系统盘路径
    if os.name == 'nt':
        path = 'C:\\'  # Windows系统默认检查C盘
    else:
        path = '/'     # Linux/macOS系统检查根目录
    
    # 获取磁盘使用情况
    usage = shutil.disk_usage(path)
    # 计算使用率百分比并四舍五入取整
    used_percent = (usage.used / usage.total) * 100
    client_stats['store'] = int(round(used_percent))

    return client_stats

# 截图功能 -------------------------------------------------------------------------------------------------------------------

def capture_screenshot():
    # 从model_utils获取当前帧（需确保model_utils已维护该变量）
    
    frame = current_frame
    # print(f'current1:{current_frame.shape}')
    if frame is None:
        print("No frame available.")
        return -1
    
    # 生成带时间戳的文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"screenshot_{timestamp}.jpg"
    save_path = SAVE_DIR / filename
    
    # 保存图片到指定路径
    cv2.imwrite(str(save_path), frame)
    
    # 返回绝对路径给前端
    return str(save_path.absolute())

# 录制功能 -------------------------------------------------------------------------------------------------------------------
def begin_rec():
    global is_recording, video_writer, video_filename
    if is_recording:
        print("Recording is already in progress.")
        return
    # 生成带时间戳的唯一文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    video_filename = VIDEO_SAVE_DIR / f"{timestamp}.mp4"
    is_recording = True
    video_writer = None  # 重置写入器以确保重新初始化
    print(f"开始录制: {video_filename}")
    return video_filename

def stop_rec():
    global is_recording, video_writer
    if not is_recording:
        print("No active recording.")
        return
    # 停止录制并释放资源
    is_recording = False
    if video_writer is not None:
        video_writer.release()
        video_writer = None
    print(f"视频已保存至: {video_filename}")
    return video_filename

# 随机抽查功能 -------------------------------------------------------------------------------------------------------------------
def random_check():
    global now_frame
    model = YOLO(Path("utils") / 'model' / "persons.pt")
    res = model.predict(now_frame, 
                    conf=0.5, 
                    classes=[0])   
            
    # 保存原始检测框信息
    boxes = []
    for box in res[0].boxes:
        x1, y1, x2, y2 = box.xyxy[0].tolist()
        boxes.append((x1, y1, x2, y2))
    try:
        if now_frame is None:
                return jsonify({"error": "没有可用的视频帧"}), 400
            
        # 获取最近一次的人数统计结果
        if boxes == []:
            return jsonify({"error": "没有检测到人员"}), 400
            
        # 随机选择一个检测框
        selected_box = random.choice(boxes)
        x1, y1, x2, y2 = map(int, selected_box)
        
        # 截取区域
        cropped = now_frame[y1:y2, x1:x2]
        
        # 保存图片
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"random_check_{timestamp}.jpg"
        save_path = Path("file_storage/downloads/cut") / filename
        cv2.imwrite(str(save_path), cropped)
        
        return jsonify(filename)
    except Exception as e:
        return jsonify({"error": str(e)}), 500