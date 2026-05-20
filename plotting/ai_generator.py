"""AI 图表生成 — Claude Vision 分析示例图 → 生成 matplotlib 代码"""
import os
import base64
import json
import mimetypes


def is_available():
    return bool(os.environ.get('ANTHROPIC_API_KEY'))


def _encode_image(image_path):
    mime = mimetypes.guess_type(image_path)[0] or 'image/png'
    with open(image_path, 'rb') as f:
        data = base64.b64encode(f.read()).decode()
    return f"data:{mime};base64,{data}"


def _build_prompt(experiment, columns):
    return f"""You are an expert scientific figure designer. Analyze the uploaded example figure and generate matplotlib Python code to create a similar-style chart.

Context:
- Experiment: {experiment}
- Data columns available: {columns}
- Must use: plt.style.use(["science", "no-latex", "nature", "bright"]) with these rcParams overrides:
  font.family=sans-serif, font.sans-serif=["Arial"], font.size=7, axes.labelsize=7,
  xtick.labelsize=6, ytick.labelsize=6, figure.figsize=(89/25.4, 2.45),
  axes.linewidth=0.75, pdf.fonttype=42, savefig.bbox="tight"

Requirements:
1. Read data from the variable `df` (pandas DataFrame already loaded)
2. Save figure to `output_path` (string variable already defined)
3. Include appropriate statistical tests (scipy.stats)
4. Use Prism-style significance brackets (not just text above bars)
5. Return ONLY Python code, no markdown fences or explanations
6. The code must be self-contained and runnable
7. Use `from plotting.rc_params import apply_cns_style` and call `apply_cns_style()` at the start
8. Close the figure with `plt.close()` at the end
"""


def analyze_and_generate(image_path, data_path, experiment, output_dir):
    """分析示例图并生成 matplotlib 代码"""
    try:
        import anthropic
    except ImportError:
        print("[ERROR] anthropic 包未安装。请运行: pip install anthropic")
        return None

    if not is_available():
        print("[ERROR] ANTHROPIC_API_KEY 环境变量未设置")
        return None

    # 读取数据列信息
    import pandas as pd
    if data_path and os.path.isfile(data_path):
        df_sample = pd.read_excel(data_path, nrows=5)
        columns = list(df_sample.columns)
        dtype_info = {col: str(df_sample[col].dtype) for col in columns}
    else:
        columns = []
        dtype_info = {}

    # 编码图片
    image_data = _encode_image(image_path)

    # 调用 Claude Vision
    client = anthropic.Anthropic()
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {"type": "base64", "media_type": "image/png", "data": image_data.split(",")[1]}
                },
                {
                    "type": "text",
                    "text": _build_prompt(experiment, json.dumps({"columns": columns, "dtypes": dtype_info}))
                }
            ]
        }]
    )

    code = response.content[0].text.strip()
    # 清理可能的 markdown 代码围栏
    if code.startswith("```python"):
        code = code[len("```python"):]
    if code.startswith("```"):
        code = code[3:]
    if code.endswith("```"):
        code = code[:-3]
    code = code.strip()

    print("AI 生成的代码:")
    print(code)
    print("\n" + "=" * 60)

    # 执行生成代码
    output_path = os.path.join(output_dir, f"AI_Generated_{experiment}.pdf")
    png_path = os.path.join(output_dir, f"AI_Generated_{experiment}.png")

    try:
        import matplotlib
        matplotlib.use('Agg')
        df = pd.read_excel(data_path)
        exec_globals = {
            'df': df, 'output_path': output_path, 'png_path': png_path,
            'pd': pd, 'np': __import__('numpy'), 'plt': __import__('matplotlib.pyplot'),
            'sns': __import__('seaborn'), 'scipy': __import__('scipy'),
            'os': os, 'json': json,
        }
        exec(code, exec_globals)
        print(f"AI 生成图表已保存: {output_path}")

        # 保存代码
        code_path = os.path.join(output_dir, f"AI_Generated_{experiment}.py")
        with open(code_path, 'w', encoding='utf-8') as f:
            f.write(code)
        print(f"AI 生成代码已保存: {code_path}")
        return True

    except Exception as e:
        print(f"[ERROR] 执行 AI 生成代码失败: {e}")
        # 保存代码以便手动调试
        code_path = os.path.join(output_dir, f"AI_Generated_{experiment}_FAILED.py")
        with open(code_path, 'w', encoding='utf-8') as f:
            f.write(code)
        return None
