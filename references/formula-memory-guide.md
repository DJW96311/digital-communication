# 公式记忆模式（模式三）· 工作流指南

> 配合 `templates/formula-memory.tex` 使用。模式三以**模式一/二产出的 `detail.md` 为输入**，把一章公式整理成**可打印、可默写**的"公式族"PDF。和"考试复习笔记"是两回事：笔记讲"怎么想、怎么考"，公式记忆手册讲"怎么记、怎么默"。

## 0. 一句话定位

> **PPT 定结构，detail.md 定公式真相，公式族定记忆。** 一切以"能默写出来"为唯一标准。

## 1. 输入 / 输出

- **输入**：`lecture-organizer-workspace/<ch>/detail.md`（模式一/二的产物，公式已从 PPT 视觉提取并校对过）。公式**逐字采用**，不改写不简化。
- **输出**：`formula-memory-workspace/<ch>/notes.tex` → `notes.pdf`（独立工作区，每章一个子文件夹）。与 `lecture-organizer-workspace/` 平级。
- **若 `detail.md` 不存在**：先跑模式一产出它；或当章节提示用户确认来源。

## 2. 核心理念：公式族，不是公式大全

不要罗列孤立公式。把一章公式归并成少数几个**公式族**，每族由**一条主公式**串起来：

```
主公式 ──▶ 变形 ──▶ 特殊情况 ──▶ 常见结论
```

能由主公式现场推出的，标 `\ketui`（可推），**不让用户死背**。只有"记不住就丢分"的端点公式标 `\bibei`（必背）。这样把记忆负担压到最小。

## 3. 八段结构（每章 PDF 固定顺序）

1. **一、本章公式记忆总览**：一两句主线/转换链 + 公式族概览（用阿拉伯数字 1 2 3）+ 三句口诀。
2. **二、公式族卡片**：每族一个 `familybox`。
3. **三、必背公式极简版**：红框，编号列出全部 `\bibei`。
4. **四、Self-test questions（英文）**：`tabularx` 两列（Question / Answer=`\dotfill`），**按公式族分组**，每族 3–5 题、覆盖四类题型（见 §5）。
5. **五、Answers**：`\clearpage` **另起一页**；与第四节行项一一对应，答案列 `\af{公式}`/`\at{文字}`。
6. **六、易混公式对照**：`tabularx` 三列（易混点 / 正确 / 常见错误）。
7. **七、Worked problems（作业 + PPT 例题 + 变体）**：每题一个 `probbox`，含 Problem / Solution / Variant（见 §7）。
8. **八、本章公式总账（速记）**：灰框，一句话回顾族/必背/易混/跨章关联。

> 八段全部入册。"下次怎么提示"那种会话用的内容**不入 PDF**。

## 4. 公式族卡片解剖（familybox 内部）

每个 `familybox{公式族 N · <族名>}` 内必含：

- `\core{记忆核心}`：一句话点破这条族靠什么主公式串起来（这是最大价值）。
- **主公式**（端点）+ 标注：`\fld{主公式 \bibei}{...}`，重要者用 `\boxed{}` 居中。
- **推导链**：主公式 → 变形 → 特殊情况 → 常见结论。
- **常见结论** + **易混点**（本族最易记错处）。
- 每个公式字段后挂标注徽章：
  - `\bibei`（红，**必背**）：考试高频、记不住必丢分的端点公式。
  - `\ketui`（蓝，**可推**）：能由必背现场推出，不要求死背。
  - `\gainian`（灰，**概念**）：只需理解含义，不要求默写。

## 5. 四条排版铁律（违反必编译失败或丢字形，全部踩过坑）

### A. tabularx 单元格里【禁用】`\bm` / `\boldsymbol`
在 `tabularx` 的测宽遍里，`\bm`/`\boldsymbol`（靠 `\mathchar` 技巧）会崩溃，报 `Improper alphabetic constant` / `Use of \@@array doesn't match`。
- **答案单元格强调一律用颜色宏**：`\af{...}`（数学，`\textcolor`+`\ensuremath`）/ `\at{...}`（文字，`\textcolor`+`\textbf`）。这两个宏在模板导言区已定义，颜色安全。
- 公式族卡片正文（非 tabularx）里**可以**用 `\bm`，但默认不必。

### B. 【禁用】圆圈数字 ①②③④⑤
Latin Modern 字体无此字形，xeCJK 不路由 → **显示成空白**（PDF 里"公式族 ·实信号"中间是空的）。
- 公式族编号、列表一律用**普通阿拉伯数字** 1 2 3 4 5。

### C. 正文里裸 Unicode 箭头 `⇒` 也会丢字形
- 正文要写箭头就用 `$\Rightarrow$`（包进数学模式）。

### D. 双参数宏别误用单参数形式
如 `\inner{x}{y}` 是双参数宏；若写成 `\inner{x}` 会把后续中文吞进 math 模式，报缺字形。用宏时参数个数要对。

## 6. 英文多元提问（第四节空表 / 第五节答案）

- **语言**：提问一律**英文**（公式/符号仍用 LaTeX 数学）；答案可数学（语言中性）或短英文。
- **分组**：按公式族分组，每族前用 `\famhdr{Family N · Name}`。
- **四类题型**（每族 3–5 题，尽量覆盖多类），行首挂彩色标签宏：
  - `\qF` **F=Formula**：默写主公式。
  - `\qC` **C=Concept**：定义 / 性质 / 物理含义 / T-F 判断。
  - `\qV` **V=Variant**：套到具体信号或情形（变式）。
  - `\qD` **D=Derivation**：一步关键推导。
- **空表（四）**：`tabularx` 两列 `p{11cm} X`（Question / Answer=`\dotfill`）；行内填空用 `\uf` 或 `\uf[1.5cm]`。
- **答案表（五）**：`\clearpage` 另起页，**行项与空表一一对应**；答案列数学用 `\af{...}`、文字/判断用 `\at{...}`。
- 覆盖全部 `\bibei` 必背 + 高频 `\ketui`；每族 3–5 题，全章约 15–25 题。

## 7. 跨章关联（不重复推导）

若本章公式是前面章节某族的延伸（如 §2.7 带通过程低通等效是 §2.1 转换链的延伸；Ch13 Rayleigh 分布接 §2.3 高斯族；Ch4 检测接 §2.2 信号空间），在**总账（七）**里一句话点明"是哪个族的延伸"，**不重复推导**。

## 8. 构建与自检（必须全过才算完成）

```bash
cd formula-memory-workspace/<ch>
xelatex -interaction=nonstopmode notes.tex      # 跑两遍
xelatex -interaction=nonstopmode notes.tex
```

自检（grep 日志）：
- exit 0
- `^!` 致命错误 = **0**
- `no .* in font` 缺字形警告 = **0**（>0 说明又触犯了铁律 B/C/D）
- `Overfull` = 0 或极少（长公式用 `align`/`multiline` 折行）
- 页数合理（一般 4–8 页，厚章可达 10 页）

失败就改 `notes.tex` 直到全过。

## 9. 多章批量（并行）

一章一个子代理，每个：读 `lecture-organizer-workspace/<ch>/detail.md` + 抄 `templates/formula-memory.tex` 导言区 → 填八段 → 编译自检。注意并发触发 MiKTeX lock 时 `sleep 6` 重试。已验证可一次性铺满全书（9 章实例见 `formula-memory-workspace/`）。

## 10. 大题演练（第七节：作业 HW + PPT 例题 EX + 变体）

把"作业题"和"PPT 例题"都按统一流程整理：**英文题干 → 英文规范解答 → 变体及参考答案**。每题一个橙色 `probbox`，内含三段：

- `\prob` **Problem**：英文题干，**逐字**取自作业题或 PPT 例题。
- `\sol` **Solution**：英文规范解答，关键步骤不跳步。
- `\var` **Variant**：基于该题自拟 1 个变体 + 参考答案（`\textbf{Ans:}` 给出）。

要点：

- 题目标题用 `HW N`（作业）或 `EX`（PPT/教材例题）前缀区分，如 `\probbox{HW 1 · <标题>}`、`\probbox{EX · <标题>}`。
- **素材源**：作业题 + 规范解答 ← `detail.md` 的作业分析节（含「答案原文」，已是规范英文，逐字采用）；PPT 例题 ← `lecture-organizer-workspace/<ch>-render/pages/*.png`（视觉提取，文字层不可信，见 [[pdf-extraction-packaging-gotchas]]）。
- **无配套作业的章节**（如 Ch13 / Ch15）：第七节只用 `EX`（PPT 例题）。
- 作业覆盖范围：`homework01–08` 仅覆盖 **Ch1–5**（见 [[lecture-organizer-skill]] 的作业覆盖说明）；其余章节的作业匹配不准就停下问，绝不硬凑。
