#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""Semi-auto generate a formula-memory notes.tex skeleton from a detail.md.

(lecture-organizer 模式三的辅助脚本。) 把机械活干掉，让人/代理专注判断：

- 从 templates/formula-memory.tex 原样拷贝已验证的导言区（不会抄错；宏
  \bibei/\ketui/\gainian/\af/\at/familybox/\core/\secbar 全部就绪）。
- 自动取章节标题（detail.md 首个 `# ` 行）。
- 从 detail.md 抽取所有 `$$...$$` 公式，作为"候选公式"列在注释里（保证覆盖，
  不漏公式）；简单的公式还会预填进 必背极简 / 默写空表 / 默写答案。

不做（需要判断）：把公式分组成族、写记忆核心、挂 必背/可推/概念 标签、补易混点
和跨章关联。生成的骨架开箱可编译；代理随后填这些。

Usage:
    python build_formula_memory.py <detail.md> --chapter "<标题>"
        [--subtitle "..."] [--outdir <dir>] [--template <path>] [--compile]

Success -> exit 0，notes.tex 路径以 JSON 打印到 stdout。仅用标准库，任意 python 可跑。
"""
import argparse
import json
import re
import sys
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_TEMPLATE = SCRIPT_DIR.parent / "templates" / "formula-memory.tex"


def extract_preamble(template_path):
    """返回模板中从开头到并包含 \\begin{document} 的文本。"""
    text = template_path.read_text(encoding="utf-8")
    marker = "\\begin{document}"
    idx = text.find(marker)
    if idx == -1:
        raise RuntimeError("模板缺少 \\begin{document}：" + str(template_path))
    return text[: idx + len(marker)] + "\n"


def extract_title(detail_text, override):
    if override:
        return override.strip()
    m = re.search(r"^#\s+(.+)$", detail_text, re.MULTILINE)
    return m.group(1).strip() if m else "（未识别章节标题，请手填）"


def extract_formulas(detail_text):
    """收集 $$...$$ 公式（主）；太少则补 inline $...$。去重、去空白。"""
    raw = re.findall(r"\$\$(.+?)\$\$", detail_text, re.DOTALL)
    formulas, seen = [], set()
    for f in raw:
        f = re.sub(r"\s+", " ", f).strip()
        key = f.replace(" ", "")
        if len(f) < 3 or key in seen:
            continue
        seen.add(key)
        formulas.append(f)
    if len(formulas) < 3:
        for m in re.finditer(r"(?<!\$)\$(?!\$)([^\$\n]{4,}?)\$(?!\$)", detail_text):
            f = re.sub(r"\s+", " ", m.group(1)).strip()
            key = f.replace(" ", "")
            if key in seen:
                continue
            seen.add(key)
            formulas.append(f)
    return formulas


def is_inline_safe(f):
    """能否安全放进 $...$（无多行环境、无 \\ 换行、不过长）。"""
    return ("\\begin" not in f) and ("\\\\" not in f) and (len(f) <= 90)


def tex_escape_text(s):
    """极简转义：纯文本标题进 LaTeX 文本模式。"""
    for a, b in (("&", r"\&"), ("%", r"\%"), ("#", r"\#"), ("_", r"\_")):
        s = s.replace(a, b)
    return s


def build_body(title, subtitle, formulas):
    esc_title = tex_escape_text(title)
    esc_sub = tex_escape_text(subtitle) if subtitle else r"公式族 \,$\cdot$\, 默写"
    seed = [f for f in formulas if is_inline_safe(f)]
    n_all, n_seed = len(formulas), len(seed)
    L = []

    L.append("% ===== 由 build_formula_memory.py 生成的骨架 =====")
    L.append("% 下一步（需人工/代理判断）：")
    L.append("%   1. 按 %候选公式 把公式分进 \\familybox 公式族卡片（每族一条主公式+记忆核心）。")
    L.append("%   2. 给每个公式字段挂 \\bibei/\\ketui/\\gainian；把第三节必背筛到 7-12 条真必背。")
    L.append("%   3. 默写空表/答案表按必背精简（行项一一对应），答案列用 \\af{公式}/\\at{文字}。")
    L.append("%   4. 补 六易混对照、七总账（跨章关联点明是哪族延伸）。")

    # 标题块
    L.append("")
    L.append(r"\begin{center}")
    L.append(r"{\Huge\bfseries\textcolor{blue!40!black}{数字通信 \,$\cdot$\, 公式记忆手册}}\\[3pt]")
    L.append("{\\Large " + esc_title + "}\\\\[2pt]")
    L.append("{\\small\\textcolor{gray}{" + esc_sub + "}}")
    L.append(r"\end{center}")
    L.append(r"\vspace{2pt}")
    L.append(r"\noindent\textcolor{blue!30}{\rule{\linewidth}{1.2pt}}")

    # 一 总览
    L.append("")
    L.append(r"\secbar{一、本章公式记忆总览}")
    L.append(r"% TODO：一两句主线/转换链 + 公式族概览（阿拉伯数字 1 2 3）+ 三句口诀。")

    # 二 公式族卡片 + 候选公式注释清单
    L.append("")
    L.append(r"\secbar{二、公式族卡片}")
    L.append("% 候选公式（共 " + str(n_all) + " 条，从 detail.md 的 $$...$$ 提取，待分组为 4-8 族）：")
    for i, f in enumerate(formulas, 1):
        flag = "" if is_inline_safe(f) else "  [复杂/多行，勿直接塞进 $...$]"
        L.append("%   [" + str(i) + "] $" + f + "$" + flag)
    L.append(r"\begin{familybox}{公式族 1 · <族名>}")
    L.append(r"\core{<一句话记忆核心：这条族靠什么主公式串起来。>}")
    L.append(r"\fld{主公式 \bibei}{<端点公式>}")
    L.append(r"\fld{推导链}{<主公式 $\Rightarrow$ 变形 $\Rightarrow$ 特殊情况>}")
    L.append(r"\fld{常见结论 \bibei}{<关键结论>}")
    L.append(r"\fld{易混点}{<本族最易记错处>}")
    L.append(r"\end{familybox}")
    L.append(r"% TODO：复制上面的 familybox，把候选公式分成 N 族。")

    # 三 必背极简（预填简单候选）
    L.append("")
    L.append(r"\begin{tcolorbox}[enhanced, breakable, sharp corners,")
    L.append(r"  colback=red!2, colframe=red!55!black, boxrule=0.6pt,")
    L.append(r"  title={\bfseries\sffamily 三、必背公式极简版（候选，请筛到 7-12 条）},")
    L.append(r"  colbacktitle=red!60!black, coltitle=white,")
    L.append(r"  left=10pt, right=10pt, top=4pt, bottom=4pt]")
    L.append(r"\renewcommand{\arraystretch}{1.45}")
    L.append(r"\noindent\begin{tabularx}{\linewidth}{@{}>{\bfseries\color{red!60!black}}c X@{}}")
    L.append(r"\toprule")
    L.append(r"\rmfamily\color{black}\textbf{\#} & \textbf{必背公式（候选）} \\")
    L.append(r"\midrule")
    rows = seed if seed else ["<主公式 1>", "<主公式 2>"]
    for i, f in enumerate(rows, 1):
        L.append(str(i) + r" & $" + f + r"$ \\")
    L.append(r"\bottomrule")
    L.append(r"\end{tabularx}")
    L.append(r"\end{tcolorbox}")

    # 四 默写空表
    src = seed if seed else ["公式 1", "公式 2"]
    L.append("")
    L.append(r"\secbar{四、默写空表（遮右栏默写）}")
    L.append(r"\renewcommand{\arraystretch}{1.7}")
    L.append(r"\noindent\begin{tabularx}{\linewidth}{@{}c p{7.8cm} X@{}}")
    L.append(r"\toprule")
    L.append(r"\textbf{\#} & \textbf{默写项} & \textbf{你的答案} \\")
    L.append(r"\midrule")
    for i in range(1, len(src) + 1):
        L.append(str(i) + r" & <默写项 " + str(i) + r"> & \dotfill \\")
    L.append(r"\bottomrule")
    L.append(r"\end{tabularx}")
    L.append(r"\renewcommand{\arraystretch}{1.0}")

    # 五 默写答案
    L.append("")
    L.append(r"\clearpage")
    L.append(r"\secbar{五、默写答案（对答案用）}")
    L.append(r"\renewcommand{\arraystretch}{1.6}")
    L.append(r"\noindent\begin{tabularx}{\linewidth}{@{}c p{7.8cm} X@{}}")
    L.append(r"\toprule")
    L.append(r"\textbf{\#} & \textbf{默写项} & \textbf{答案} \\")
    L.append(r"\midrule")
    for i, f in enumerate(src, 1):
        L.append(str(i) + r" & <默写项 " + str(i) + r"> & \af{" + f + r"} \\")
    L.append(r"\bottomrule")
    L.append(r"\end{tabularx}")
    L.append(r"\renewcommand{\arraystretch}{1.0}")
    L.append(r"% TODO：把答案列改用 \af{公式}/\at{文字} 高亮；按必背精简，与空表一一对应。")

    # 六 易混
    L.append("")
    L.append(r"\secbar{六、易混公式对照}")
    L.append(r"\renewcommand{\arraystretch}{1.5}")
    L.append(r"\noindent\begin{tabularx}{\linewidth}{@{}>{\raggedright\arraybackslash}p{4.0cm} >{\raggedright\arraybackslash}X >{\raggedright\arraybackslash}X@{}}")
    L.append(r"\toprule")
    L.append(r"\textbf{易混点} & \textbf{正确} & \textbf{常见错误} \\")
    L.append(r"\midrule")
    L.append(r"<易混点> & <正确> & <常见错误> \\")
    L.append(r"\bottomrule")
    L.append(r"\end{tabularx}")
    L.append(r"\renewcommand{\arraystretch}{1.0}")

    # 七 总账
    L.append("")
    L.append(r"\begin{tcolorbox}[enhanced, breakable, sharp corners,")
    L.append(r"  colback=gray!4, colframe=gray!55, boxrule=0.5pt,")
    L.append(r"  title={\bfseries\sffamily 七、本章公式总账（速记）},")
    L.append(r"  colbacktitle=gray!35!black, coltitle=white,")
    L.append(r"  left=10pt, right=10pt, top=4pt, bottom=4pt]")
    L.append(r"\textbf{章节}：" + esc_title + r"\hfill\textbf{进度}：骨架待填")
    L.append(r"\smallskip")
    L.append(r"\textbf{与其他章节关联}：<TODO：点明是哪族延伸，不重复推导>。")
    L.append(r"\end{tcolorbox}")

    L.append("")
    L.append(r"\vspace{6pt}")
    L.append(r"\begin{center}\small\textcolor{gray}{数字通信公式记忆手册 \,$\cdot$\, " + esc_title + r" \,$\cdot$\, 供打印默写}\end{center}")
    L.append("")
    L.append(r"\end{document}")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser(description="半自动生成公式记忆 notes.tex 骨架（lecture-organizer 模式三）")
    ap.add_argument("detail", help="模式一/二产出的 detail.md 路径")
    ap.add_argument("--chapter", default=None, help="章节标题（默认取 detail.md 首个 # 标题）")
    ap.add_argument("--subtitle", default=None, help="副标题关键词")
    ap.add_argument("--outdir", default=None, help="输出目录（默认 <root>/formula-memory-workspace/<detail 所在目录名>/）")
    ap.add_argument("--template", default=None, help="模板路径（默认 templates/formula-memory.tex）")
    ap.add_argument("--compile", action="store_true", help="生成后跑 xelatex 两遍自检")
    args = ap.parse_args()

    detail = Path(args.detail).resolve()
    if not detail.exists():
        print(json.dumps({"ok": False, "error": "detail.md 不存在：" + str(detail)}), file=sys.stderr)
        sys.exit(1)

    template = Path(args.template).resolve() if args.template else DEFAULT_TEMPLATE
    if not template.exists():
        print(json.dumps({"ok": False, "error": "模板不存在：" + str(template)}), file=sys.stderr)
        sys.exit(1)

    if args.outdir:
        outdir = Path(args.outdir).resolve()
    else:
        outdir = detail.parent.parent.parent / "formula-memory-workspace" / detail.parent.name
    outdir.mkdir(parents=True, exist_ok=True)

    detail_text = detail.read_text(encoding="utf-8")
    title = extract_title(detail_text, args.chapter)
    formulas = extract_formulas(detail_text)

    tex_text = extract_preamble(template) + "\n" + build_body(title, args.subtitle, formulas)
    out_tex = outdir / "notes.tex"
    out_tex.write_text(tex_text, encoding="utf-8")

    result = {"ok": True, "tex": str(out_tex), "formulas_extracted": len(formulas), "chapter": title}

    if args.compile:
        import subprocess
        for run in (1, 2):
            p = subprocess.run(
                ["xelatex", "-interaction=nonstopmode", "notes.tex"],
                cwd=str(outdir), capture_output=True, text=True, encoding="utf-8", errors="replace",
            )
            if p.returncode != 0:
                result["compile_ok"] = False
                result["compile_run_failed"] = run
                print(json.dumps(result, ensure_ascii=False), file=sys.stderr)
                sys.exit(2)
        result["compile_ok"] = True
        result["pdf"] = str(outdir / "notes.pdf")

    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
