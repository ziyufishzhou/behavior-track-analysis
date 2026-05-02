"""
行为分析项目 — 全局实验参数配置

各实验脚本从此处读取参数，避免分散在各文件中。
"""

# ==================== 通用参数 ====================
FPS = 30                          # 视频帧率
LIKELIHOOD_THRESHOLD = 0.6        # DLC 置信度阈值（低于此值的坐标视为无效）

# ==================== OF (Open Field) ====================
OF_ANALYSIS_MINUTES = 15          # 分析时长（分钟）
OF_ARENA_SIZE_CM = 50.0           # 旷场实际边长 (cm)

# ==================== EPM (Elevated Plus Maze) ====================
EPM_ANALYSIS_MINUTES = 15         # 分析时长（分钟）
EPM_TOTAL_TIME_S = 900            # 总分析时间（秒）

# ==================== TCT (Three-Chamber Test) ====================
TCT_ANALYSIS_MINUTES = 10         # 分析时长（分钟）

# ==================== CSV 修复参数 ====================
FIX_IMG_WIDTH = 1280
FIX_IMG_HEIGHT = 720
FIX_MID_X = 640
FIX_MID_Y = 360
FIX_EMPTY_THRESHOLD = 0.3         # 空笼判定阈值
FIX_CONFIDENCE_THRESHOLD = 0.9    # 置信度门槛
