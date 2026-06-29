# 公式转写与 LaTeX 易错指南

写 `notes.tex` 时参考。重点是从**图片**（视觉真相）把公式转写成干净的 LaTeX，并避开一堆会让编译炸的坑。

## 0. 最容易炸的：LaTeX 特殊字符（务必先看）

课件标题、变量名、文件名里常出现这些字符，在 LaTeX 正文里有特殊含义，**直接写会编译失败**：

| 字符 | 含义 | 怎么写 |
|---|---|---|
| `_` | 下标 | `\_`（或在数学模式里当真正的下标用 `x_i`） |
| `#` | 宏参数 | `\#` |
| `&` | 表格/对齐 | `\&` |
| `%` | 注释 | `\%` |
| `$` | 数学模式 | `\$` |
| `{` `}` | 分组 | `\{` `\}` |
| `\` | 命令前缀 | `\textbackslash{}` |
| `~` | 不间断空格 | `\textasciitilde{}` |

> 真实教训：占位符 `CHAPTER_TITLE_PLACEHOLDER` 里的 `_` 曾导致 `\tableofcontents` 处报 "Missing $ inserted"。正文里的下划线同理——要么转义，要么确认它确实在数学模式里当下标。

## 1. 信号/通信常见公式转写对照

从课件图片识别后，按此对照写：

### 傅里叶变换族
```latex
% 正变换
X(f) = \int_{-\infty}^{\infty} x(t)\, e^{-j2\pi ft}\, dt
% 逆变换
x(t) = \int_{-\infty}^{\infty} X(f)\, e^{j2\pi ft}\, df
% 冲激函数
\delta(t), \quad \delta(f - f_0)
% sinc
\operatorname{sinc}(x) = \frac{\sin(\pi x)}{\pi x}
```

### 概率与统计
```latex
E[X] = \int_{-\infty}^{\infty} x\, p_X(x)\, dx
\operatorname{Var}(X) = E[X^2] - (E[X])^2
% Q 函数（误码率常用）
Q(x) = \frac{1}{\sqrt{2\pi}} \int_{x}^{\infty} e^{-t^2/2}\, dt
= \tfrac{1}{2}\operatorname{erfc}\!\left(\frac{x}{\sqrt{2}}\right)
% 高斯 PDF
p_X(x) = \frac{1}{\sqrt{2\pi}\sigma} \exp\!\left(-\frac{(x-\mu)^2}{2\sigma^2}\right)
```

### 误码率（BER，考试高频）
```latex
% BPSK / QPSK 相干解调
P_b = Q\!\left(\sqrt{\frac{2E_b}{N_0}}\right)
% M-ASK / M-PSK / M-QAM 的通用形式视具体调制而定
```

### 采样与量化
```latex
% Nyquist 采样定理
f_s \geq 2 f_{\max}
% 量化信噪比（均匀量化）
\mathrm{SNR}_q = 3 \cdot 4^{2b}  \quad (\text{b 比特})
```

## 2. 排版技巧

- **行内**用 `$ ... $`，**独立成行带编号**用 `\begin{equation} ... \end{equation}`，**多行对齐**用 `align`：
  ```latex
  \begin{align}
    y(t) &= x(t) * h(t) \\
         &= \int x(\tau) h(t-\tau)\, d\tau
  \end{align}
  ```
- 微分符号加细空格：`\,dt`、`\,df`（比 `dt` 好看）。
- 期望/方差等算子用 `\operatorname{}`（直立，不是斜体）：`\operatorname{Var}(X)`。
- 向量/矩阵加粗：`\bm{x}`、`\bm{H}`（已加载 `bm` 包）。
- 分段函数：
  ```latex
  f(x) = \begin{cases} 1, & |x| < \tfrac{1}{2} \\ 0, & \text{否则} \end{cases}
  ```
- 单位冲激、阶跃：`\delta(t)`、`u(t)`（或 `u_{-1}(t)` 视课件记法）。

## 3. 从图片识别公式时的注意事项

- **不信任文字层**：`text/*.txt` 常把上下标、根号打散（如 `√ a2` 实为 $\sqrt{a^2}$）。以 `pages/*.png` 图片为准。
- **下标/上标**：课件里 `X(f)` 下的小字、角标要正确识别为 `_{}` / `^{}`。
- **求和/积分上下限**：看清楚是 $0$ 到 $N$ 还是 $-\infty$ 到 $\infty$。
- **黑体 vs 斜体**：课件里加粗的字母通常是向量/矩阵 → 用 `\bm{}`；普通变量斜体即可。
- **实在看不清**：宁可在笔记里注明"（此处课件公式不清晰，建议对照原 PPT 第 N 页）"，不要瞎猜一个错的公式——错的公式比没有更害人。

## 4. 复杂图/表的退路

- 电路框图、信号流程图、星座图(constellation diagram)这类**图示**，不要试图用 LaTeX 重画（容易错且耗时）。在 `.tex` 里用文字描述其含义即可，必要时提示用户对照原课件该页。
- 纯数据小表可以用 `tabular`；大表/复杂表保持简述。
