# Pandoc 转 Word 说明

本文档用于把 `毕业设计论文初稿.md` 转换成符合学院论文模板基本格式的 Word 文档。

## 1. 推荐转换命令

在项目根目录运行：

```powershell
cd E:\project\behavior_analyze
pandoc "毕业设计论文初稿.md" `
  --from markdown+pipe_tables+yaml_metadata_block+raw_tex `
  --to docx `
  --reference-doc "论文模板-pandoc.docx" `
  -o "毕业设计论文初稿_格式修正版.docx"
python tools\fix_thesis_docx_format.py
```

最终生成文件：

```text
毕业设计论文初稿_学院格式版.docx
```

## 2. 已写入的格式

`论文模板-pandoc.docx` 已配置：

1. 正文：宋体小四，1.5 倍行距。
2. 英文：Times New Roman。
3. 一级标题：黑体三号，居中。
4. 二级标题：黑体四号。
5. 三级标题：黑体小四。
6. 页面边距：上、下 2cm，左、右 3cm。
7. 页眉、页脚距离：1.5cm。

`tools\fix_thesis_docx_format.py` 会补充：

1. 页眉：`吉林大学 计算机科学与技术学院 毕业论文`，楷体小四。
2. 页脚：右侧页码，楷体五号。
3. Word 文档内部的页眉、页脚部件声明。

## 3. 仍需在 Word/WPS 中检查的内容

1. 封面中的姓名、学号、指导教师、专业等个人信息需要手动补全。
2. 承诺书签名和日期需要按学校要求处理。
3. 目录建议在 Word/WPS 中用“引用 -> 目录”插入或更新，确保目录页码准确。
4. 图表编号和参考文献格式需要结合最终正文逐项核对。
5. 如果学院要求严格复刻原始封面版式，应以学校模板中的封面为准，把正文内容粘入模板对应位置。
