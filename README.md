# **YOLO-ClassAct**

*YOLOv11 Classroom Activity Analyzer*

基于YOLOv11的教室监控环境下学生行为识别分析系统

## 项目简介

YOLO-ClassAct 是一个基于YOLOv11的教室活动分析系统，旨在通过计算机视觉技术实时识别和分析教室中的学生行为，为教学管理和课堂质量提升提供数据支持。

## 功能特性

- 实时视频流分析
- 学生行为识别
- 视频录制与回放
- 违规行为截图记录
- 文件上传与管理
- 随机点名功能

## 文件结构

```
.
├── backend/                    # 后端服务
│   ├── file_storage/            # 用户文件存储区
│   │   ├── downloads/           # 用户下载的文件
│   │   │   └── cut/             # 截图保存区
│   │   └── uploads/             # 用户上传的文件
│   ├── utils/                   # 核心业务逻辑模块
│   │   ├── model/               # 存放.pt模型文件
│   │   ├── get_video.py         # 视频处理逻辑
│   │   ├── model_utils.py       # 模型调用逻辑，和文件下载逻辑
│   │   └── upload_handler.py    # 文件上传逻辑
│   ├── app.py                   # 主程序入口
│   └── config.py                # 配置文件
│
├── frontend/               # 前端界面
│   ├── src/                     # 源代码
│   │   └── App.vue              # 主界面
│   ├── package.json             # 项目依赖配置
│   └── ...                      # 其他前端文件
│
└── README.md                    # 项目说明文档
```

## 技术栈

### 后端技术
- Python 3.x
- Flask Web框架
- YOLOv11 模型
- uv 依赖管理工具

### 前端技术
- Vue 3
- Element Plus UI组件库
- Axios HTTP客户端
- Vite 构建工具

## 快速开始

### 后端服务启动

1. 安装 [uv](https://docs.astral.sh/uv/) 依赖管理工具：
   ```bash
   # Windows (使用 PowerShell)
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   
   # macOS/Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. 创建虚拟环境并安装依赖：
   ```bash
   cd backend
   uv venv
   uv pip install -r requirements.txt
   ```

3. 激活虚拟环境并启动服务：
   ```bash
   # Windows
   .venv\Scripts\activate
   
   # macOS/Linux
   source .venv/bin/activate
   
   python app.py
   ```

### 前端界面启动

1. 安装依赖：
   ```bash
   cd frontend
   npm install
   ```

2. 启动开发服务器：
   ```bash
   npm run dev
   ```

访问 `http://localhost:5173` 查看前端界面。

## API 接口

| 接口 | 方法 | 描述 |
|------|------|------|
| `/video_feed` | GET | 获取视频流 |
| `/stop_stream` | POST | 停止视频流 |
| `/video_stats` | GET | 获取视频统计信息 |
| `/getCamera` | GET | 获取可用摄像头列表 |
| `/upload` | POST | 文件上传 |
| `/screenshot` | POST | 截图保存 |
| `/begin_video` | POST | 开始录制视频 |
| `/stop_video` | POST | 停止录制视频 |
| `/get_video` | GET | 获取视频列表 |
| `/get_pictures` | GET | 获取违规截图列表 |
| `/random_check` | GET | 随机点名 |

## 部署

### 后端部署
使用 `uv` 管理依赖，通过以下命令安装生产环境依赖：
```bash
uv pip install -r requirements.txt --system
```

### 前端部署
构建生产版本：
```bash
npm run build
```

构建后的文件位于 `dist` 目录，可部署到任何静态文件服务器。