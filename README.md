# lecture-organizer

> 把 **PPT/PDF 课件** + **作业题与答案** 融合成**面向考试**的复习材料，并能进一步整理成可打印默写的**公式记忆手册**。
>
> 为公式密集型工科课程（数字通信、信号处理、通信原理……）设计。

核心理念一句话：**PPT 定知识结构，作业定考法，题型定输出。**

## 三种模式

| 模式 | 触发 | 产出 |
|---|---|---|
| **一 · 考试复习（默认）** | "整理这一章""结合作业复习""判断题/填空题/大题""公式速查" | 逐小节考试化笔记（12 部分）+ 作业反向分析 + 整章速查，md→tex→pdf |
| **二 · 逐页深度** | "逐页""每一页都讲" | 每页 8 部分深挖（备用） |
| **三 · 公式记忆** | "整理成公式族""公式记忆手册""可默写""必背/可推/概念" | 可打印默写的公式族 PDF（七段：总览/公式族卡片/必背/默写空表/默写答案/易混/总账） |

模式三以模式一/二产出的 `detail.md` 为输入（公式已校对），是下游模式。

## 特性

- **视觉提取**：课件公式多为图片，PDF 文字层常被打散（`|z|=√a2+b2`）。脚本把课件渲染成逐页 PNG，**以图为准**提取，不信任文字层。
- **作业定考法**：把每道作业题反向映射到知识点和题型（判断/填空/大题），并附**答案原文**。
- **公式族（模式三）**：不做公式大全——一族由一条主公式串起（`主公式→变形→特殊情况→结论`），能现场推出的标"可推"不死背，把记忆负担压到最小。
- **XeLaTeX + ctex**：中文公式 PDF，配色盒子固化在转换器里。

## 依赖

- **Python**（建议用 [uv](https://docs.astral.sh/uv/) 管理）：`pymupdf` / `pywin32` / `python-pptx` / `pillow`（见 `requirements.txt`）。
- **MiKTeX / xelatex**：中文 PDF 编译（需 `ctex` + `xeCJK`）。
- **Windows**：PPTX→PDF 用 PowerPoint COM（macOS/Linux 请先把 PPTX 另存为 PDF）。

## 安装

```bash
git clone https://github.com/DJW96311/digital-communication.git
cd digital-communication
uv venv --python 3.14 .venv
uv pip install --python .venv/Scripts/python.exe -r requirements.txt
```

之后 `<VENV_PY>` = `.venv/Scripts/python.exe`，`<SKILL_DIR>` = 仓库根目录（即本 skill 目录）。

## 快速开始

```
课程目录/
├── ppt/                 # 课件（PDF/PPTX，命名可混乱）
├── homework&answer/     # 作业 + 答案（homework0N.pdf + Answer0N.pdf）
└── lecture-organizer/   # 本 skill
```

模式一（考试复习）见 `SKILL.md` 的完整工作流（扫描→识别章节→匹配作业→逐小节→作业分析→整章速查→md/tex/pdf）。

模式三（公式记忆）：

```bash
# 半自动起骨架（拷导言区 + 取标题 + 抽候选公式）
<VENV_PY> <SKILL_DIR>/scripts/build_formula_memory.py "<detail.md>" \
    --chapter "<章标题>" --outdir <输出目录> --compile
# 然后人工/代理：分组进公式族、挂 必背/可推/概念、补易混与跨章关联
```

## 排版铁律（模式三，违反必编译失败/丢字形）

1. `tabularx` 单元格里**禁用** `\bm`/`\boldsymbol`（测宽遍崩溃）→ 答案强调用颜色宏 `\af{}`/`\at{}`。
2. **禁用**圆圈数字 ①②③④⑤（丢字形）→ 用阿拉伯数字 1 2 3。
3. 正文裸 Unicode `⇒` 丢字形 → 写 `$\Rightarrow$`。

详见 `references/formula-memory-guide.md`。

## 目录结构

```
lecture-organizer/
├── SKILL.md                          # skill 主指令（三模式工作流）
├── requirements.txt
├── scripts/
│   ├── render_slides.py              # 课件→逐页 PNG（视觉提取）
│   ├── md2tex.py                     # detail.md → notes.tex（配色盒子）
│   ├── compile_pdf.py                # xelatex 编译（两遍）
│   ├── crop_figure.py                # 按需裁图（备用）
│   └── build_formula_memory.py       # 模式三：半自动生成公式记忆骨架
├── templates/
│   ├── minimal.tex                   # 最小编译自检模板
│   └── formula-memory.tex            # 模式三黄金模板（导言区 + 七段骨架）
└── references/
    ├── formula-guide.md              # 公式转写对照 + 易错点
    └── formula-memory-guide.md       # 模式三七段结构 / 标注标准 / 四条铁律
```

## 许可证

MIT（见 `LICENSE`）。
