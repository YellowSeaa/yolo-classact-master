'''
---------------------------------------------------------------------------------------


主函数 python app.py
只包含路由


---------------------------------------------------------------------------------------
'''

from flask import Flask, Response, jsonify, request, abort
from utils.model_utils import find_available_cameras, generate_frames, get_video_stats, capture_screenshot, begin_rec, stop_rec, stop_stream, random_check
from utils.upload_handler import handle_file_upload
from flask_cors import CORS
from utils.get_video import get_videos, play_video, get_pictures, show_picture, show_picture_check
app = Flask(__name__)
# r'/*' 是通配符，让本服务器所有的 URL 都允许跨域请求
CORS(app)

# 获取视频流
@app.route('/video_feed', methods=['GET'])
def video_feed():
    # 自动打包所有GET参数为字典（自动处理单值和多值参数）
    params = {
        key: values if len(values) > 1 else values[0]
        for key, values in request.args.lists()
    }
    # 添加类型转换示例（根据需求可选）
    # 将置信度转换为浮点
    if 'model_confidence' in params:
        try:
            params['model_confidence'] = float(params['model_confidence'])
        except ValueError:
            params['model_confidence'] = 0.5  # 默认值

    return Response(generate_frames(params),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/stop_stream', methods=['POST'])
def stop_stream1():
    '''停止视频流'''
    stop_stream()
    return jsonify(success=True)
# 获取统计信息
@app.route('/video_stats')
def get_stats():
    return jsonify(get_video_stats())  # 直接返回全局变量

@app.route('/getCamera')
def getCamera_api():
    # 获取本机摄像头信息
    value = find_available_cameras()
    data = {'key': value}
    return jsonify(data)

@app.route('/upload', methods=['POST'])
def upload_route():
    """文件上传路由"""
    return handle_file_upload()

@app.route('/screenshot', methods=['POST'])
def screenshot_route():
    """截图路由"""
    if capture_screenshot() == -1:
        abort(400) # 返回http错误码
    return jsonify(capture_screenshot())

# 录制视频功能
@app.route('/begin_video', methods=['POST'])
def begin_video():
    begin_rec()
    return jsonify({'message': '开始录制'})

@app.route('/stop_video', methods=['POST'])
def stop_video():
    stop_rec()
    return jsonify({'message': '结束录制'})

# 视频回放功能
@app.route('/get_video', methods=['GET'])
def get_video1():
    return get_videos(app)

# 视频播放
@app.route('/play_video/<path:encoded_path>')
def play_video1(encoded_path):
    print(encoded_path)
    return play_video(encoded_path)

# 违规记录功能
@app.route('/get_pictures', methods=['GET'])
def get_pictures_route():
    return get_pictures(app)

@app.route('/show_picture/<filename>')
def show_picture_route(filename):
    return show_picture(filename)

@app.route('/show_picture_check/<filename>')
def show_picture_route_check(filename):
    return show_picture_check(filename)

# 随机抽取
@app.route('/random_check', methods=['GET'])
def random_check_route():
    return random_check()

if __name__ == '__main__':
    app.run(debug=True)
