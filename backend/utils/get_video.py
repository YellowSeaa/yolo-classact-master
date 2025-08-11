import re
from flask import jsonify, send_from_directory, abort
from datetime import datetime
from pathlib import Path, PurePath
from urllib.parse import unquote

# 获取视频
def get_videos(app):
    # 构建目录路径对象
    print(1)
    base_dir = Path(app.root_path)
    target_dir = base_dir / 'file_storage' / 'downloads' / 'video'
    
    # 验证目录存在性
    if not target_dir.exists() or not target_dir.is_dir():
        # return -1
        return jsonify({'error': 'Directory not found'}), 404
    
    avi_files = []
    pattern = re.compile(r'^(\d{8})_\d+\.mp4$')  # 文件名模式
    
    try:
        # 遍历目录项（自动过滤隐藏文件）
        for file_path in target_dir.iterdir():
            # 仅处理文件且匹配模式
            if file_path.is_file() and pattern.match(file_path.name):
                # 提取日期部分
                date_str = file_path.stem.split('_')[0]
                date_obj = datetime.strptime(date_str, "%Y%m%d")
                
                # 构建相对路径（使用PurePath确保跨平台兼容）
                relative_path = PurePath(file_path.relative_to(base_dir))
                
                avi_files.append({
                    'date': date_obj.strftime("%Y-%m-%d"),
                    '_sort_key': date_obj,  # 排序专用字段
                    'address': relative_path.as_posix()  # 统一正斜杠格式
                })

        # 按日期降序排序（最新在前）
        sorted_files = sorted(
            avi_files,
            key=lambda x: x['_sort_key'],
            reverse=True
        )
        
        # 移除临时排序字段
        final_data = [{k: v for k, v in item.items() if k != '_sort_key'} 
                     for item in sorted_files]
        
        return jsonify(final_data)
    # except:
    #     return -1
    except ValueError as ve:
        return jsonify({'error': f'Path error: {str(ve)}'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 视频播放
def play_video(encoded_path):
    # 解码路径
    file_path = unquote(encoded_path)
    file_path = file_path.split('/')[-1]
    print(file_path)
    
    # 验证路径安全性（防止路径穿越攻击）
    video_dir = Path("file_storage/downloads/video").resolve()
    target_path = (video_dir / file_path).resolve()
    print(f'target_path:{target_path}')
    print(f'video_dir:{video_dir}')
    
    if not str(target_path).startswith(str(video_dir)):
        abort(403)  # 禁止访问非视频目录下的文件
    
    return send_from_directory(video_dir, file_path)

# 获取图片
def get_pictures(app):
    base_dir = Path(app.root_path)
    target_dir = base_dir / 'file_storage' / 'downloads' / 'save'
    
    if not target_dir.exists():
        return jsonify({'error': 'Directory not found'}), 404

    pic_files = []
    pattern = re.compile(r'^auto_save_(\d{8})_(\d{6})\.jpg$')

    try:
        for file_path in target_dir.iterdir():
            if match := pattern.match(file_path.name):
                date_str, time_str = match.groups()
                date_obj = datetime.strptime(f"{date_str}{time_str}", "%Y%m%d%H%M%S")
                
                pic_files.append({
                    'date': date_obj.strftime("%Y-%m-%d"),
                    'time': date_obj.strftime("%H:%M:%S"),
                    'filename': file_path.name,
                    '_sort': date_obj.timestamp()
                })

        sorted_files = sorted(pic_files, key=lambda x: x['_sort'], reverse=True)
        return jsonify([{k:v for k,v in item.items() if k != '_sort'} for item in sorted_files])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def show_picture(filename):
    pic_dir = Path("file_storage/downloads/save").resolve()
    target = (pic_dir / filename).resolve()
    
    if not str(target).startswith(str(pic_dir)):
        abort(403)
    
    if not target.exists():  # 新增文件存在性检查
        abort(404)
    
    return send_from_directory(pic_dir, filename)  # 补全返回语句

def show_picture_check(filename):
    pic_dir = Path("file_storage/downloads/cut").resolve()
    target = (pic_dir / filename).resolve()
    
    if not str(target).startswith(str(pic_dir)):
        abort(403)
    
    if not target.exists():  # 新增文件存在性检查
        abort(404)
    
    return send_from_directory(pic_dir, filename)  # 补全返回语句