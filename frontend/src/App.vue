<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import './assets/icon.css'
import { Connection, VideoCamera, Cpu, VideoPlay, Bell, RefreshLeft, Camera, User, Pointer, Notebook, Compass, VideoPause } from '@element-plus/icons-vue' // 新增Stop图标导入
import { dialogProps, ElButton } from 'element-plus'
import { useDark, useToggle } from '@vueuse/core'
import axios from 'axios'
import { UploadFilled, QuestionFilled } from '@element-plus/icons-vue'

// 暗黑模式
const isDark = useDark()
const toggleDark = useToggle(isDark)

// 输入源选择
const _input = ref(null)
const _input_options = ref([])

// 系统状态
const _system = ref(true) // 系统状态

// 获取摄像头方法
const fetchCameraOptions = async () => {
  try {
    const response = await axios.get('http://127.0.0.1:5000/getCamera')
    const cameras = response.data.key // 注意这里访问的是data.key
    // console.log("acmeras:",cameras)
    // 生成摄像头选项
    const cameraOptions = cameras.map(cam => ({
      value: `${cam}`,
      label: `监视器(${cam})`
    }))
    // console.log("cameraOptions:",cameraOptions)
    // 合并选项（保持顺序）
    _input_options.value = [
      ...cameraOptions,
      { value: 'video', label: '视频' },
      { value: 'picture', label: '图片' }
    ]
    // console.log("_input_options:",_input_options.value)
  } catch (error) {
    console.error('获取摄像头失败:', error)
    // 回退到基础选项
    _input_options.value = [
      { value: 'video', label: '视频' },
      { value: 'picture', label: '图片' }
    ]
  }
  // 设置默认选项
  _input.value = _input_options.value[0]?.value
  // console.log(_input_options.value)
  // console.log(_input)

}
// 生命周期钩子
onMounted(() => {
  fetchCameraOptions()
  // 启动定时器
  intervalId.value = setInterval(() => {
    axios.get('http://127.0.0.1:5000/video_stats')
      .then(response => {
        clientStats.value = response.data;
        _system.value = true
      })
      .catch(error => {
        console.error('获取统计信息失败:', error);
        _system.value = false
      });
  }, 1000);
  toggleDark(true) // 强制启用暗黑模式
  document.documentElement.classList.add('dark') // 添加Element Plus暗黑模式需要的类
});

// 新增clientStats和intervalId变量
const clientStats = ref({ fps: 0, counts: {} });
const intervalId = ref(null);

// 新增onUnmounted钩子
onUnmounted(() => {
  if (intervalId.value) {
    clearInterval(intervalId.value);
  }
});

const dialog_pictureUpload = ref(false) // 控制图片上传弹出框
const dialog_videoUpload = ref(false) // 控制视频上传弹出框

// 控制输入源选择框状态更新
const inputSelectChange = (e) => {
  // 先停止现有流
  axios.post('http://127.0.0.1:5000/stop_stream')
    .then(() => {
      if (!e) {
        console.log('输入源选择状态更新:', _input.value)
        if (_input.value == 'video') {
          dialog_videoUpload.value = true
        } else if (_input.value == 'picture') {
          dialog_pictureUpload.value = true
        }
      }
    })
}

// 文件上传成功钩子
const uploadSuccess = (response, uploadFile, uploadFiles) => {
  console.log('文件上传成功！', response)
  // 关闭弹出窗
  dialog_pictureUpload.value = false
  dialog_videoUpload.value = false
  // 更新name，触发模型调用
  name.value = response.file_path
  console.log('name:', name.value)
}

// 截图功能
import { ElMessage } from 'element-plus'; // 新增导入

const captureScreenshot = () => { // 新增截图方法
  axios.post('http://127.0.0.1:5000/screenshot')
    .then(response => { // 修改：接收响应数据
      ElMessage.success(`截图已保存至 ${response.data}`); // 修改：显示完整路径
    })
    .catch(() => {
      ElMessage.error('截图失败，请检查服务');
    });
};

// 新增录制状态管理
const isRecording = ref(false)

const toggleRecording = async () => {
  try {
    if (_input.value != 'picture') {
      if (isRecording.value) {
        await axios.post('http://127.0.0.1:5000/stop_video')
      } else {
        await axios.post('http://127.0.0.1:5000/begin_video')
      }
      isRecording.value = !isRecording.value
      if (isRecording.value) {
        ElMessage.success('录制已开始');
      } else {
        ElMessage.success('录制已结束,可在视频回放中查看');
      }
    } else {
      ElMessage.error('图片输入无法录制')
    }
  } catch (error) {
    console.error('操作失败:', error)
    ElMessage.error('无法控制录制状态')
  }
}

// -------------------------------------------------------------------------------------------

// 模型选择
const _model = ref('n')
const _model_options = [
  { value: 'n', label: 'yolo11-n ——快速模式' },
  { value: 'm', label: 'yolo11-m ——均衡模式' },
  { value: 'x', label: 'yolo11-x ——精准模式' },
  { value: 'p', label: '人数统计模式' },
]

// -------------------------------------------------------------------------------------------

// 模型参数设置
const model_confidence = ref(50) // 置信度
const model_type = ref(['bend', 'bow_head', 'turn_head', 'Using_phone'])      // 识别的类别
const if_save = ref(false)      // 是否保存违规图像
const dialog_modelSetting = ref(false) // 控制模型设置弹出框

// 定义响应式变量
const name = ref('0')  // 替换为实际名称值

// 计算属性生成动态URL
const videoFeedUrl = computed(() => {
  const timestamp = Date.now();

  // 创建 URL 参数对象
  const params = new URLSearchParams();

  // 添加非数组参数
  params.append('type', _input.value); // 输入源类型
  params.append('name', name.value); // 输入源路径（如果是图片或视频就需要）
  params.append('t', timestamp); // 时间戳
  params.append('model', _model.value); // 模型类型
  params.append('model_confidence', model_confidence.value); // 模型置信度
  params.append('if_save', if_save.value); // 是否保存违规图像

  // 遍历数组，逐个添加 model_type 参数 识别的类型
  model_type.value.forEach(item => {
    params.append('model_type', item); // 自动处理 URL 编码
  });

  return `http://127.0.0.1:5000/video_feed?${params.toString()}`;
});

// 视频回放和违规记录
const dialog_videoPlayer = ref(false)
const dialog_picturePlayer = ref(false)

// 视频回放列表
const videoTableData = ref([])

// 违规记录列表
const pictureTableData = ref([])

// 视频回放按钮逻辑：打开dialog并向后台请求数据
const handleVideoPlayback = async () => {
  dialog_videoPlayer.value = true;
  try {
    // 请求后台数据
    const response = await axios.get('http://127.0.0.1:5000/get_video');
    videoTableData.value = response.data;
  } catch (error) {
    console.log(error)
    ElMessage.error('视频数据获取失败');
  }
};

// 视频播放
const dialogVideoPlayer = ref(false) // 视频播放器
const currentVideoUrl = ref('') // 当前视频的URL
const handlePlayVideo = (filePath) => {
  // 对路径进行URL编码
  const encodedPath = encodeURIComponent(filePath)
  currentVideoUrl.value = `http://127.0.0.1:5000/play_video/${encodedPath}`
  dialogVideoPlayer.value = true
}

// 处理错误
const handleVideoError = (e) => {
  console.log(e)
  ElMessage.error('视频播放失败，请检查文件格式或路径')
  dialogVideoPlayer.value = false
}

// 违规记录
// 获取违规记录
const handlePicturePlayback = async () => {
  dialog_picturePlayer.value = true;
  try {
    const response = await axios.get('http://127.0.0.1:5000/get_pictures');
    pictureTableData.value = response.data;
  } catch (error) {
    ElMessage.error('违规记录获取失败');
  }
};

// 查看图片
const currentPictureUrl = ref('')
const dialogPictureViewer = ref(false)
const handleViewPicture = (filename) => {
  currentPictureUrl.value = `http://127.0.0.1:5000/show_picture/${encodeURIComponent(filename)}`
  dialogPictureViewer.value = true
}

// 举手统计
const if_hand = ref(false)
const handlehandriceCount = async () => {
  // 和人数统计功能互斥
  if (if_people.value) {
    ElMessage.error('人数统计功能开启中，请先关闭')
    return
  }

  if_hand.value = !if_hand.value
  if (if_hand.value) {
    if (!model_type.value.includes('hand-raising')) {
      model_type.value = [...model_type.value, 'hand-raising']
    }
    ElMessage.success('开始统计举手次数')
  } else {
    model_type.value = model_type.value.filter(item => item !== 'hand-raising')
    ElMessage.success('停止统计举手次数')
  }
}
// 人数统计按钮
const if_people = ref(false)
const last_model = ref('n') // 功能开启前选择的模型类型
const handlePeopleCount = () => {
  // 和举手功能互斥
  if (if_hand.value) {
    ElMessage.error('举手统计功能开启中，请先关闭')
    return
  }

  if_people.value = !if_people.value
  if (if_people.value) {
    last_model.value = _model.value
    _model.value = 'p'
  } else {
    _model.value = last_model.value
  }
}

// 随机抽查功能
const dialogRandomCheck = ref(false)
const randomCheckImage = ref('')

// 随机抽查功能
const handleRandomCheck = async () => {
  try {
    const response = await axios.get('http://127.0.0.1:5000/random_check')
    randomCheckImage.value = `http://127.0.0.1:5000/show_picture_check/${encodeURIComponent(response.data)}`
    dialogRandomCheck.value = true
  } catch (error) {
    ElMessage.error('抽查失败：' + error.response?.data?.error || '服务异常')
  }
}
</script>

<template>
  <div class="common-layout">
    <!-- 视频上传弹出框 -->
    <el-dialog v-model="dialog_videoUpload" title="视频上传" width="800">
      <el-upload class="upload-demo" drag action="http://127.0.0.1:5000/upload" accept=".mp4,.avi,.mov"
        :on-success="uploadSuccess">
        <el-icon class="el-icon--upload"><upload-filled /></el-icon>
        <div class="el-upload__text">
          拖动文件到此，或 <em>点击上传</em>
        </div>
        <template #tip>
          <div class="el-upload__tip">
            支持格式：.mp4, .avi, .mov
          </div>
        </template>
      </el-upload>
    </el-dialog>

    <!-- 图片上传弹出框 -->
    <el-dialog v-model="dialog_pictureUpload" title="图片上传" width="800">
      <el-upload class="upload-demo" drag action="http://127.0.0.1:5000/upload" accept=".jpg,.jpeg,.png,.svg"
        :on-success="uploadSuccess">
        <el-icon class="el-icon--upload"><upload-filled /></el-icon>
        <div class="el-upload__text">
          拖动文件到此，或 <em>点击上传</em>
        </div>
        <template #tip>
          <div class="el-upload__tip">
            支持格式：.jpg, .jpeg, .png, .svg
          </div>
        </template>
      </el-upload>
    </el-dialog>

    <!-- 模型设置弹出框 -->
    <el-dialog v-model="dialog_modelSetting" title="警报设置" width="800">
      <el-row><el-text style="margin-top: 10px;margin-bottom: 10px;font-size:medium;">置信度</el-text></el-row>
      <el-row>
        <el-slider v-model="model_confidence" show-input />
      </el-row>
      <el-row><el-text style="margin-top: 20px;margin-bottom: 10px;font-size:medium;">警报类别</el-text></el-row>
      <el-row>
        <el-checkbox-group v-model="model_type">
          <el-checkbox label="趴桌子" value="bend" />
          <el-checkbox label="低头" value="bow_head" />
          <el-checkbox label="扭头" value="turn_head" />
          <el-checkbox label="玩手机" value="Using_phone" />
        </el-checkbox-group>
      </el-row>
      <el-row style="margin-top: 20px;">
        <el-switch v-model="if_save" />
        <el-text style="margin-left: 10px;">是否保存违规图像</el-text>
        <el-popover placement="right" :width="200" trigger="hover" content="开启后，有人员出现违规行为，会将图像保存至“违规记录”中。只对摄像头和视频输入有效。">
          <template #reference>
            <el-icon style="margin-left: 5px;margin-top: 9px;">
              <QuestionFilled />
            </el-icon>
          </template>
        </el-popover>
      </el-row>
      <template #footer>
        <div class="dialog-footer">
          <el-button type="primary" @click="dialog_modelSetting = false">
            确定
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 视频回放弹出框 -->
    <el-dialog v-model="dialog_videoPlayer" title="视频回放" width="800">
      <el-table :data="videoTableData" height="250" style="width: 100%">
        <el-table-column prop="date" label="日期" width="150" />
        <el-table-column prop="address" label="地址" width="450" />
        <el-table-column fixed="right" label="操作" min-width="120">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="handlePlayVideo(row.address)">
              播放
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>

    <!-- 新增视频播放对话框 -->
    <el-dialog v-model="dialogVideoPlayer" title="视频播放" width="800">
      <video controls autoplay style="width: 100%" :src="currentVideoUrl" @error="handleVideoError">
        您的浏览器不支持视频播放
      </video>
    </el-dialog>

    <!-- 违规记录弹出框 -->
    <el-dialog v-model="dialog_picturePlayer" title="违规记录" width="800">
      <el-table :data="pictureTableData" height="250" style="width: 100%">
        <el-table-column prop="date" label="日期" width="300" />
        <el-table-column prop="time" label="时间" width="300" />
        <el-table-column fixed="right" label="操作" min-width="120">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="handleViewPicture(row.filename)">
              查看
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>

    <!-- 图片查看对话框 -->
    <el-dialog v-model="dialogPictureViewer" title="违规截图">
      <img :src="currentPictureUrl" style="width: 100%;object-fit: cover" />
    </el-dialog>

    <!-- 随机抽查对话框 -->
    <el-dialog v-model="dialogRandomCheck" title="随机抽查" width="400">
      <img :src="randomCheckImage" style="width: 100%; max-height: 500px;object-fit: cover" />
    </el-dialog>

    <el-container style="height: 100vh;">
      <el-main width="75%">
        <div class="left_main">
          <img style="width: 100%; height: 100%" :src="videoFeedUrl" />
        </div>
      </el-main>
      <el-aside width="25%">
        <div class="right_col">
          <div class="func_block">
            <el-row><el-text style="margin-top: 20px;margin-bottom: 10px;">输入源选择</el-text></el-row>
            <el-row><el-select v-model="_input" placeholder="Select" style="width: 100%"
                @visible-change="inputSelectChange">
                <el-option v-for="item in _input_options" :key="item.value" :label="item.label" :value="item.value" />
              </el-select></el-row>
          </div>
          <div class="func_block">
            <el-row><el-text style="margin-bottom: 10px;">模型选择</el-text></el-row>
            <el-row><el-select v-model="_model" placeholder="Select" style="width: 100%" :disabled="if_people">
                <el-option v-for="item in _model_options" :key="item.value" :label="item.label" :value="item.value" />
              </el-select></el-row>
          </div>
          <div class="func_block">
            <el-row>
              <el-col :span="12" class="monitor_col">
                <el-button text @click="toggleRecording"> <!-- 绑定点击事件 -->
                  <div class="monitor_button" :style="{ color: isRecording ? 'red' : '' }">
                    <el-icon>
                      <component :is="isRecording ? VideoPause : VideoPlay" />
                    </el-icon>
                    <span class="monitor_text">{{ isRecording ? '停止录制' : '开始录制' }}</span>
                  </div>
                </el-button>
              </el-col>
              <el-col :span="12" class="monitor_col">
                <el-button text @click="dialog_modelSetting = true">
                  <div class="monitor_button">
                    <el-icon>
                      <Bell />
                    </el-icon>
                    <span class="monitor_text">警报设置</span>
                  </div>
                </el-button>
              </el-col>
            </el-row>
            <el-row>
              <el-col :span="12" class="monitor_col">
                <el-button text @click="handleVideoPlayback">
                  <div class="monitor_button">
                    <el-icon>
                      <RefreshLeft />
                    </el-icon>
                    <span class="monitor_text">视频回放</span>
                  </div>
                </el-button>
              </el-col>
              <el-col :span="12" class="monitor_col">
                <el-button text @click="captureScreenshot"> <!-- 绑定点击事件 -->
                  <div class="monitor_button">
                    <el-icon>
                      <Camera />
                    </el-icon>
                    <span class="monitor_text">截图</span>
                  </div>
                </el-button>
              </el-col>
            </el-row>
          </div>
          <div class="func_block teach_block">
            <el-row style="margin-left: 5%;"><el-text>违规统计</el-text></el-row>
            <el-row class="statistics_block_large">
              <el-col :span="5" class="statistics_block">
                <el-row><el-text>趴桌</el-text></el-row>
                <el-row><el-text style="color:#3176FF;margin-bottom: 5px;">{{ clientStats.counts.bend || 0
                    }}人</el-text></el-row>
              </el-col>
              <el-col :span="5" class="statistics_block">
                <el-row><el-text>低头</el-text></el-row>
                <el-row><el-text style="color:#3176FF;margin-bottom: 5px;">{{ clientStats.counts.bow_head || 0
                    }}人</el-text></el-row>
              </el-col>
              <el-col :span="5" class="statistics_block">
                <el-row><el-text>扭头</el-text></el-row>
                <el-row><el-text style="color:#3176FF;margin-bottom: 5px;">{{ clientStats.counts.turn_head || 0
                    }}人</el-text></el-row>
              </el-col>
              <el-col :span="5" class="statistics_block">
                <el-row><el-text>手机</el-text></el-row>
                <el-row><el-text style="color:#3176FF;margin-bottom: 5px;">{{ clientStats.counts.Using_phone || 0
                    }}人</el-text></el-row>
              </el-col>
            </el-row>
          </div>
          <div class="func_block teach_block">
            <el-row style="margin-left: 5%;"><el-text>教学助手</el-text></el-row>
            <el-row>
              <el-col :span="12" class="monitor_col">
                <el-button @click="handlePeopleCount" :style="{ border: if_people ? '2px solid white' : '' }">
                  <div class="monitor_button">
                    <el-icon>
                      <User />
                    </el-icon>
                    <span class="monitor_text">人数统计</span>
                    <span class="num_text">
                      {{ if_people ?
                        '当前' + (clientStats.persons || '0') + '人' :
                        '功能未开启'
                      }}
                    </span>
                  </div>
                </el-button>
              </el-col>
              <el-col :span="12" class="monitor_col">
                <el-button @click="handlehandriceCount" :style="{ border: if_hand ? '2px solid white' : '' }">
                  <div class="monitor_button">
                    <el-icon>
                      <Pointer />
                    </el-icon>
                    <span class="monitor_text">举手检测</span>
                    <span class="num_text">
                      {{ if_hand ?
                        (clientStats.counts['hand-raising'] || '0') + '人举手' :
                        '功能未开启'
                      }}
                    </span>
                  </div>
                </el-button>
              </el-col>
            </el-row>
            <el-row>
              <el-col :span="12" class="monitor_col">
                <el-button @click="handleRandomCheck">
                  <div class="monitor_button">
                    <el-icon>
                      <Compass />
                    </el-icon>
                    <span class="monitor_text">随机抽查</span>
                  </div>
                </el-button>
              </el-col>
              <el-col :span="12" class="monitor_col">
                <el-button @click="handlePicturePlayback">
                  <div class="monitor_button">
                    <el-icon>
                      <Notebook />
                    </el-icon>
                    <span class="monitor_text">违规记录</span>
                  </div>
                </el-button>
              </el-col>
            </el-row>
          </div>
          <div class="func_block state_block">
            <el-row>
              <el-col :span="12" style="margin-top:0px"><el-text>系统状态</el-text></el-col>
              <el-col :span="12" style="margin-top:0px" class="col_right"><el-text
                  :style="{ color: _system ? 'green' : 'red' }">{{ _system ? '正常运行' : '连接出错' }}</el-text></el-col>
            </el-row>
            <el-row>
              <el-col :span="12"><el-text>存储空间</el-text></el-col>
              <el-col :span="12" class="col_right"><el-text>已用{{ clientStats.store }}%</el-text></el-col>
            </el-row>
            <el-row>
              <el-col :span="12"><el-text>视频帧率</el-text></el-col>
              <el-col :span="12" class="col_right">
                <el-icon style="margin-right: 5px;">
                  <VideoCamera />
                </el-icon>
                <el-text>{{ clientStats.fps }}FPS</el-text>
              </el-col>
            </el-row>
          </div>
          <div v-show="false">
            <span @click.stop="toggleDark()">暗黑模式</span>
            <el-switch size="small" v-model="isDark" />
          </div>
        </div>

      </el-aside>
    </el-container>

  </div>

</template>

<style scoped>
.common-layout {
  margin: 0;
  padding: 0;
  width: 100%;
  height: 100vh;
  /* background-color: #2A2A2A; */
}

.left_main {
  width: 100%;
  height: auto;
  display: flex;
  justify-content: center;
  /* 水平居中 */
  align-items: center;
  /* 垂直居中 */
  height: 100%;
  /* 或者设置为具体的高度 */
}

.right_col {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: #333333;
  padding-left: 10px;
  padding-right: 10px;
}

.func_block {
  width: auto;
  height: auto;
  margin-bottom: 15px;
}

.statistics_block_large {
  background-color: #2A2A2A;
  /* padding: 2px; */
  border-radius: 12px;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  /* 设置间距 */

  .statistics_block {
    text-align: center;
    margin-top: 10px;
    background-color: black;
    border-radius: 12px;
    width: calc(25% - 10px);
    /* 每个块占25%，减去间距 */
    box-sizing: border-box;
    /* 包含padding和border在宽度内 */

    .el-text {
      width: 100%;
      margin-top: 5px;
    }
  }
}

.teach_block {
  background-color: #2A2A2A;
  padding: 10px;
  border-radius: 12px;

  .el-button {
    border-radius: 12px;
  }
}

.state_block {
  background-color: #2A2A2A;
  padding: 10px;
  border-radius: 12px;
  margin-top: auto;
  /* 自动推到底部 */

  .el-col {
    margin-top: 12px;
    padding-left: 12px;
    padding-right: 12px;
  }

  .el-row {
    display: flex;
    justify-content: space-between;

    /* 两个列分别推到最左和最右 */
    .col_right {
      display: flex;
      align-items: center;
      /* Flexbox 的垂直居中 */
      justify-content: flex-end;
      /* Flexbox 的水平居中，即向右对齐 */
      text-align: right;
      /* 文本向右对齐 */
    }
  }
}

.monitor_col {
  text-align: center;
  margin-top: 10px;

  .el-button {
    height: 100px;
    width: 90%;
    /* margin-left: 100px; */
  }

  .monitor_button {
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    width: 100%;
    /* margin-left: 0px !important; */

    .el-icon {
      width: 16px;
      height: 16px;
    }

    .monitor_text {
      margin-top: 5px;
      font-size: 14px;
      display: flex;
      align-items: center;
      text-align: center;
    }

    .num_text {
      margin-top: 15px;
      font-size: 12px;
      color: #3176FF;
    }
  }
}

.el-button [class*=el-icon]+span {
  margin-left: 0px !important;
}
</style>
