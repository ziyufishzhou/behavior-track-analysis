# Behavior Analyze

面向啮齿动物行为实验的数据分析工作台。项目基于 DeepLabCut 输出的姿态估计结果，支持 OF、EPM、TCT 三类实验的数据预处理、ROI 标注、行为指标计算、统计绘图和结果导出。

## 功能

- 视频导入与实验标签管理。
- DeepLabCut 视频分析任务启动。
- DLC CSV 收集、修复、按标签分组和 metadata 生成。
- OF、EPM、TCT 三类实验 ROI 标注与指标计算。
- 汇总结果统计绘图。
- Web 项目状态面板，用于检查视频、CSV、ROI、metadata 和分析结果是否就绪。

## 环境

推荐使用 Conda：

```powershell
conda env create -f environment.yml
conda activate behavioranalyze
```

如果环境已经存在，也可以安装或更新依赖：

```powershell
pip install -r requirements.txt
```

DeepLabCut 可以放在独立 Conda 环境中。首次运行 DLC 分析前，需要在 Web 页面的“DLC 分析”中填写 DLC 环境的 `python.exe` 路径。

## 本地配置

项目默认使用项目内的 `video/` 作为视频目录。也可以在 Web 的“导入视频”页面修改视频根目录，配置会保存到：

```text
data/app_settings.json
```

可参考：

```text
config/app_settings.example.json
.env.example
```

常用环境变量：

```text
BEHAVIOR_ANALYZE_ENV
BEHAVIOR_ANALYZE_VIDEO_DIR
BEHAVIOR_ANALYZE_SERVER_PYTHON
BEHAVIOR_ANALYZE_DLC_PYTHON
```

## 启动

推荐启动方式：

```powershell
python start_web.py
```

也可以双击：

```text
start_web.py
```

浏览器访问：

```text
http://127.0.0.1:5000
```

## 使用流程

1. 打开“项目状态”，检查当前视频目录、metadata、CSV、ROI 和输出结果状态。
2. 打开“导入视频”，设置视频根目录，刷新视频列表。
3. 为视频填写 Experiment、Group、Condition、MouseID、Phase 等标签并保存。
4. 打开“DLC 分析”，设置 DLC 模型目录和 DLC Python 路径，运行视频分析。
5. 打开“预处理”，依次运行收集 CSV、修复 CSV、按标签分组、生成 metadata，或直接运行完整预处理。
6. 打开“ROI 标注”，完成 OF、EPM、TCT 对应区域标注。
7. 打开“数据分析”，计算行为学指标。
8. 打开“绘图设置”，根据 summary 文件生成统计图。

## 健康检查

可以运行轻量检查脚本，确认核心模块、路径配置和 Web 关键接口是否正常：

```powershell
python scripts/verify_project.py
```

通过时会看到：

```text
[OK] project health check passed
```

## 目录

- `config/`：项目路径、应用设置和参数配置。
- `preprocessing/`：CSV 收集、修复、分组和 metadata 生成。
- `experiments/`：OF、EPM、TCT 三类实验分析与 ROI 工具。
- `plotting/`：统计绘图模块。
- `web/`：Flask Web 工作台。
- `gui/`、`gui_qt/`：桌面 GUI 相关代码。
- `doc/`：论文、模板、参考文献、图表和项目修改记录。
- `data/`：中间数据和应用设置，本地生成，不建议提交。
- `video/`：默认视频目录，本地数据，不建议提交。
- `output/`：分析和绘图结果，本地生成，不建议提交。
- `models/`：DLC 模型目录，本地模型文件，不建议提交。

## 常见问题

如果页面能打开但视频列表为空，先检查“导入视频”里的视频根目录是否正确。

如果 DLC 不能运行，先检查“DLC 分析”里的 DLC Python 路径是否指向安装了 DeepLabCut 的环境。

如果分析失败，先检查“项目状态”中的 metadata、CSV 和 ROI 是否都已就绪。
