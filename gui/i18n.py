"""
中文字符串常量
"""

APP_TITLE = "行为分析工作台"

# 侧边栏
NAV_IMPORT = "导入视频"
NAV_DLC = "DLC 分析"
NAV_PREPROCESS = "预处理"
NAV_ROI = "ROI 标注"
NAV_ANALYZE = "数据分析"
NAV_PLOT = "绘图设置"

NAV_LIST = [NAV_IMPORT, NAV_DLC, NAV_PREPROCESS, NAV_ROI, NAV_ANALYZE, NAV_PLOT]

# 导入视频
IMPORT_TITLE = "导入视频并设置标签"
IMPORT_SELECT_FILES = "选择视频文件"
IMPORT_SELECT_DIR = "选择视频目录"
IMPORT_VIDEO_LIST = "已导入视频列表"
IMPORT_LABEL_SECTION = "标签设置（应用到选中视频）"
IMPORT_EXPERIMENT = "实验"
IMPORT_GROUP = "组别"
IMPORT_CONDITION = "条件"
IMPORT_MOUSEID = "小鼠编号"
IMPORT_PHASE = "阶段"
IMPORT_APPLY = "应用标签到选中"
IMPORT_SAVE = "保存元数据"
IMPORT_PREVIEW = "标签预览"

# DLC 分析
DLC_TITLE = "DeepLabCut 视频分析"
DLC_MODEL_PATH = "模型路径"
DLC_SELECT_MODEL = "选择模型"
DLC_VIDEO_LIST = "待分析视频"
DLC_PARAMS = "参数"
DLC_SHUFFLE = "Shuffle"
DLC_CONFIDENCE = "置信度阈值"
DLC_START = "开始 DLC 分析"
DLC_NO_VIDEOS = "没有已打标签的视频可分析"

# 预处理
PREP_TITLE = "CSV 预处理流水线"
PREP_FIX = "修复 CSV"
PREP_GROUP = "按标签分组"
PREP_METADATA = "构建元数据"
PREP_RUN_ALL = "一键全流程"
PREP_UPDATE_MODE = "更新模式"

# ROI
ROI_TITLE = "ROI 区域标注"
ROI_OF = "OF 旷场 ROI 标注"
ROI_EPM = "EPM 高架十字 ROI"
ROI_TCT = "TCT 三箱 ROI 标注"
ROI_STATUS = "ROI 配置状态"
ROI_CONFIGURED = "已配置"
ROI_NOT_CONFIGURED = "未配置"

# 分析
ANALYZE_TITLE = "数据分析"
ANALYZE_EXPERIMENTS = "选择实验"
ANALYZE_PARAMS = "参数设置"
ANALYZE_RUN = "运行分析"
ANALYZE_TIME = "分析时长(分钟)"
ANALYZE_LIKELIHOOD = "置信度阈值"
ANALYZE_FPS = "帧率"

# 绘图
PLOT_TITLE = "绘图设置"
PLOT_EXPERIMENT = "实验"
PLOT_DATA_SOURCE = "数据源"
PLOT_CHART_TYPE = "图表类型"
PLOT_BAR = "柱状图"
PLOT_LINE = "折线图"
PLOT_COLORS = "颜色设置"
PLOT_PARAMS = "参数调节"
PLOT_GENERATE = "生成图表"
PLOT_OPEN_DIR = "打开输出目录"

# 元数据
META_TITLE = "元数据编辑"
META_RESCAN = "重新扫描"
META_SAVE = "保存"
META_ADD_COL = "添加列"

# 通用
BTN_OK = "确定"
BTN_CANCEL = "取消"
BTN_RUN = "运行"
BTN_SAVE = "保存"
STATUS_RUNNING = "运行中..."
STATUS_DONE = "完成"
STATUS_ERROR = "出错"
STATUS_IDLE = "就绪"
