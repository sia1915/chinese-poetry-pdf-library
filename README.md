# 中国古典诗词 PDF 文库

本仓库包含自动转换工具，用于把上游 `chinese-poetry/chinese-poetry` 数据集中的 JSON、文本说明、SQLite 数据库及图片整理为可下载 PDF。

## 如何生成并下载 PDF

1. 打开本仓库的 [Actions 工作流](https://github.com/sia1915/chinese-poetry-pdf-library/actions/workflows/build-pdfs.yml)。
2. 选择 **Build and publish poetry PDFs**。
3. 点击 **Run workflow**，再点击绿色的 **Run workflow** 确认。
4. 等待工作流完成（数据量较大，可能需要较长时间）。
5. 打开 [Releases 页面](https://github.com/sia1915/chinese-poetry-pdf-library/releases)。
6. 在 **Chinese Poetry PDF Library v1** 下下载 `chinese-poetry-pdf-library.zip`。

工作流会从上游仓库重新下载原始数据、逐个 JSON 生成 PDF、制作目录，并把 PDF 汇总压缩为 Release 附件。这样不需要通过聊天窗口下载或手动上传大文件。

## 当前仓库文件

- `scripts/build_pdfs.py`：批量转换脚本。
- `.github/workflows/build-pdfs.yml`：GitHub Actions 自动构建和发布工作流。
- `chinese_poetry_pdf_catalog.txt`：初始目录说明；实际完整文件目录会随构建结果放入发布压缩包。

## 内容范围

包括全唐诗、全宋诗、宋词、五代诗词、元曲、楚辞、诗经、论语、四书五经、蒙学、纳兰性德、曹操诗集、幽梦影、御定全唐詩，以及 rank、strains 等辅助数据。具体 PDF 文件数以工作流生成的发布包目录为准。

## 数据来源与许可

原始数据来自 [chinese-poetry/chinese-poetry](https://github.com/chinese-poetry/chinese-poetry)。上游仓库标注 MIT License；原始资料来自互联网，使用和再分发时仍应核查具体数据来源及权利。
