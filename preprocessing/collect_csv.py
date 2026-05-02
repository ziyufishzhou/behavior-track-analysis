import os
import shutil
from config.paths import VIDEO_DIR, RAW_CSV_DIR

# ================= 配置区 =================
video_root_dir = str(VIDEO_DIR)
output_summary_dir = str(RAW_CSV_DIR)
# ==========================================

if not os.path.exists(output_summary_dir):
    os.makedirs(output_summary_dir)

def collect_dlc_csv():
    print(f"📂 开始从 {video_root_dir} 提取 CSV 结果...")
    count = 0

    for root, dirs, files in os.walk(video_root_dir):
        for file in files:
            # 识别 DLC 生成的 csv (通常带有 DLC_resnet... 等字样)
            if file.endswith(".csv") and "DLC" in file:
                source_path = os.path.join(root, file)

                # 构造一个简洁的目标文件名：保留原始视频名，去掉那一长串模型后缀
                # 比如：mouse01DLC_Resnet50...csv -> mouse01_result.csv
                video_name = file.split("DLC")[0]
                new_filename = f"{video_name}_result.csv"
                dest_path = os.path.join(output_summary_dir, new_filename)

                # 执行复制
                shutil.copy2(source_path, dest_path)
                print(f"✅ 已提取: {new_filename}")
                count += 1

    print(f"\n✨ 提取完成！共找到 {count} 个结果文件。")
    print(f"📍 汇总路径: {output_summary_dir}")

if __name__ == "__main__":
    collect_dlc_csv()
