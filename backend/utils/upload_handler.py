'''
---------------------------------------------------------------------------------------


文件上传逻辑


---------------------------------------------------------------------------------------
'''

import os
from datetime import datetime
from flask import request, jsonify

# 安全存储路径的基础目录
BASE_STORAGE_PATH = os.path.join('file_storage', 'uploads')

def handle_file_upload():
    """处理文件上传的核心函数"""
    # 检查文件是否存在
    if 'file' not in request.files:
        return jsonify({'code': 400, 'message': 'No file part'}), 400
    
    file = request.files['file']
    
    # 检查是否选择了文件
    if file.filename == '':
        return jsonify({'code': 400, 'message': 'No selected file'}), 400

    try:
        # 生成时间戳文件名
        file_ext = os.path.splitext(file.filename)[1]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        new_filename = f"{timestamp}{file_ext}"

        # 创建存储目录（如果不存在）
        os.makedirs(BASE_STORAGE_PATH, exist_ok=True)

        # 构建完整保存路径
        save_path = os.path.join(BASE_STORAGE_PATH, new_filename)
        
        # 保存文件
        file.save(save_path)

        # 返回标准化路径（使用正斜杠保持跨平台兼容性）
        return jsonify({
            'code': 200,
            'message': 'File uploaded successfully',
            'file_path': save_path.replace('\\', '/')
        })

    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'File upload failed: {str(e)}'
        }), 500
