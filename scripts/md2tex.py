#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Convert deep lecture-notes Markdown -> LaTeX (ctex + xelatex) with a strong
visual hierarchy. Each of the 8 parts maps to a distinctly styled tcolorbox:

  - 这一页在讲什么  -> muted gray banner (page orientation)
  - 核心概念        -> green concept box
  - 核心公式        -> BLUE bordered "hero" formula card (the usable formula)
  - 公式含义/符号释义 -> light subdued symbol-key box
  - 推导过程        -> GRAY, smaller, muted (de-emphasized)
  - 和前面知识的联系 -> purple logical-link box
  - 考试中怎么写    -> ORANGE callout (what to write in the exam)
  - 易错点总结      -> RED warning box

Also fixes markdown **bold** / *italic* rendering (the naive converter left raw
asterisks), respects '|' inside $...$ math when splitting table rows, and
terminates text-mode macros before CJK characters.

Usage:
    python md2tex.py <detail.md> <notes.tex> [--title "Chapter X ..."]

The document title defaults to the first '# ' line of the markdown.
"""
import argparse
import re
from pathlib import Path

# ---- part definitions: (match_key, cn_name, en_sub, box_style) ----
# Covers BOTH modes: 逐小节考试化 (12-part section / 9-part homework /
# 13-part chapter summary) AND 逐页深度 (8-part page). Order matters —
# first match wins, so specific/long keywords precede generic ones, and
# 易错点 precedes 速记 so "易错点与考试速记版" stays a pitfall box.
PART_DEFS = [
    # --- 易错点（必须在速查/速记之前）---
    ("易错点",           "易错点",   "Common mistakes",           "cbox-pitfall"),
    # --- 公式速查 / 一页速查 / 速记（章总结最前的考试速查）---
    ("公式速查",         "公式速查", "Formula cheat sheet",       "cbox-cheat"),
    ("一页速查",         "一页速查", "One-page cheat sheet",      "cbox-cheat"),
    ("考试速查",         "考试速查", "Exam cheat sheet",          "cbox-cheat"),
    ("速查",             "速查",     "Cheat sheet",              "cbox-cheat"),
    ("最终速记",         "最终速记", "Final memorization",        "cbox-cheat"),
    ("速记",             "速记",     "Memorization",             "cbox-cheat"),
    # --- 三种题型 ---
    ("判断题",           "判断题",   "True/False",               "cbox-judge"),
    ("填空题",           "填空题",   "Fill-in-the-blank",        "cbox-fill"),
    ("大题",             "大题模板", "Big-problem template",     "cbox-exam"),
    # --- 作业 / 考法 ---
    ("对应作业",         "作业考法", "Homework & exam angle",    "cbox-homework"),
    ("作业题",           "作业考法", "Homework & exam angle",    "cbox-homework"),
    # --- 答案原文（作业分析后附的 Answer 英文解答）---
    ("答案原文",         "答案原文", "Answer key (verbatim)",    "cbox-answer"),
    # --- 逐页 8 部分 ---
    ("这一页在讲什么",   "本页定位", "What this page is about",   "cbox-pos"),
    ("核心概念",         "核心概念", "Key concepts",              "cbox-concept"),
    ("核心公式",         "核心公式", "Key formula",               "cbox-formula"),
    ("公式含义",         "符号释义", "Symbol meaning",            "cbox-sym"),
    ("符号释义",         "符号释义", "Symbol meaning",            "cbox-sym"),
    # --- 推导（必要推导 / 推导过程 / 推导）---
    ("必要推导",         "推导过程", "Derivation",                "cbox-deriv"),
    ("推导过程",         "推导过程", "Derivation",                "cbox-deriv"),
    ("推导",             "推导过程", "Derivation",                "cbox-deriv"),
    # --- 主题 / 主线（逐小节）---
    ("逻辑主线",         "逻辑主线", "Logical mainline",         "cbox-link"),
    ("主线",             "主线",     "Mainline",                 "cbox-link"),
    ("共同主题",         "本节主题", "Section theme",            "cbox-link"),
    ("和前面知识的联系", "前后联系", "Logical thread",            "cbox-link"),
    ("分页重点",         "分页重点", "Per-page highlights",      "cbox-pos"),
    ("考试中怎么写",     "考试写法", "How to write in exam",      "cbox-exam"),
]
PART_ORDER = [d[0] for d in PART_DEFS]
PART_MAP = {d[0]: (d[1], d[2], d[3]) for d in PART_DEFS}

TITLE_COLOR = {
    "cbox-pos": "gray!35!black", "cbox-concept": "green!40!black",
    "cbox-formula": "blue!55!black", "cbox-sym": "blue!40!black",
    "cbox-deriv": "gray!45!black", "cbox-link": "purple!45!black",
    "cbox-exam": "orange!55!black", "cbox-pitfall": "red!55!black",
    "cbox-cheat": "orange!75!black", "cbox-judge": "yellow!45!orange",
    "cbox-fill": "cyan!50!black", "cbox-homework": "teal!50!black",
    "cbox-answer": "black!60",
}
TITLE_ICON = {
    "cbox-pos": r"$\bullet$ ", "cbox-concept": r"$\blacksquare$ ",
    "cbox-formula": r"$\bigstar$ ", "cbox-sym": r"$\circ$ ",
    "cbox-deriv": r"$\circlearrowleft$ ", "cbox-link": r"$\rightarrow$ ",
    "cbox-exam": r"$\checkmark$ ", "cbox-pitfall": r"$\blacktriangle$ ",
    "cbox-cheat": r"$\bigstar$ ", "cbox-judge": r"$\boxdot$ ",
    "cbox-fill": r"$\diamond$ ", "cbox-homework": r"$\blacktriangleright$ ",
    "cbox-answer": r"$\therefore$ ",
}

LAT = {"&": r"\&", "%": r"\%", "#": r"\#", "_": r"\_",
       "{": r"\{", "}": r"\}"}

# Unicode -> LaTeX. Text-mode macros get a trailing {} so they terminate
# cleanly before a following CJK character (e.g. ……注 -> \ldots{}\ldots{}注).
UNI2TEX = {
    "→": r"$\rightarrow$", "↔": r"$\leftrightarrow$", "⇒": r"$\Rightarrow$",
    "⇔": r"$\Leftrightarrow$", "⟺": r"$\Longleftrightarrow$",
    "⟹": r"$\Longrightarrow$", "∎": r"$\blacksquare$",
    "≠": r"$\neq$", "≡": r"$\equiv$", "≤": r"$\le$", "≥": r"$\ge$",
    "×": r"$\times$", "·": r"$\cdot$", "∑": r"$\sum$", "∫": r"$\int$",
    "∞": r"$\infty$", "π": r"$\pi$", "θ": r"$\theta$", "⋆": r"$\star$",
    "△": r"$\triangleq$", "≜": r"$\triangleq$",
    "▶": r"$\blacktriangleright$ ", "📷": "[图] ", "✓": r"$\checkmark$",
    "✗": r"$\times$", "α": r"$\alpha$", "β": r"$\beta$", "γ": r"$\gamma$",
    "λ": r"$\lambda$", "μ": r"$\mu$", "σ": r"$\sigma$", "ρ": r"$\rho$",
    "ω": r"$\omega$", "Δ": r"$\Delta$", "δ": r"$\delta$", "φ": r"$\varphi$",
    "≈": r"$\approx$", "±": r"$\pm$", "∓": r"$\mp$", "∈": r"$\in$",
    "∀": r"$\forall$", "∝": r"$\propto$", "⊙": r"$\odot$",
    "★": r"$\bigstar$", "☆": r"$\star$", "…": r"\ldots{}",
    "−": r"$-$", "′": r"$'$",
    "—": "---", "–": "--", "§": r"\S{}", "©": r"\textcopyright{}",
    "®": r"\textregistered{}", "™": r"\texttrademark{}",
    "“": "``", "”": "''", "‘": "`", "’": "'",
}
for _n in range(20):
    UNI2TEX[chr(0x2460 + _n)] = "%d. " % (_n + 1)

# Unicode -> bare LaTeX math commands (NO $...$ wrapping). Applied to the INSIDE
# of math spans ($...$ and \[..\]) so that a raw Unicode glyph sitting inside math
# (e.g. "$≈1/T_m$") is converted to a valid math command ("\approx") instead of
# being passed through raw and producing a "Missing character" error.
UNI2MATH = {
    "→": r"\rightarrow", "↔": r"\leftrightarrow", "⇒": r"\Rightarrow",
    "⇔": r"\Leftrightarrow", "⟺": r"\Longleftrightarrow", "⟹": r"\Longrightarrow",
    "≈": r"\approx", "≠": r"\neq", "≡": r"\equiv", "≤": r"\leq", "≥": r"\geq",
    "±": r"\pm", "∓": r"\mp", "×": r"\times", "·": r"\cdot", "÷": r"\div",
    "∑": r"\sum", "∏": r"\prod", "∫": r"\int", "∞": r"\infty", "∂": r"\partial",
    "∇": r"\nabla", "∈": r"\in", "∉": r"\notin", "∀": r"\forall", "∃": r"\exists",
    "∝": r"\propto", "∘": r"\circ", "⋆": r"\star", "⊙": r"\odot", "⊕": r"\oplus",
    "√": r"\sqrt ", "△": r"\triangle", "≜": r"\triangleq", "∎": r"\blacksquare",
    "α": r"\alpha", "β": r"\beta", "γ": r"\gamma", "δ": r"\delta",
    "ε": r"\varepsilon", "ζ": r"\zeta", "η": r"\eta", "θ": r"\theta",
    "λ": r"\lambda", "μ": r"\mu", "ν": r"\nu", "ξ": r"\xi", "π": r"\pi",
    "ρ": r"\rho", "σ": r"\sigma", "τ": r"\tau", "φ": r"\varphi", "ψ": r"\psi",
    "ω": r"\omega", "Γ": r"\Gamma", "Δ": r"\Delta", "Θ": r"\Theta", "Λ": r"\Lambda",
    "Σ": r"\Sigma", "Φ": r"\Phi", "Ψ": r"\Psi", "Ω": r"\Omega",
    "ℝ": r"\mathbb{R}", "ℂ": r"\mathbb{C}", "ℤ": r"\mathbb{Z}", "ℕ": r"\mathbb{N}",
}


def uni_repl(s):
    for u, tex in UNI2TEX.items():
        if u in s:
            s = s.replace(u, tex)
    return s


def uni2math(s):
    """Replace Unicode math glyphs with bare LaTeX commands (for use inside math)."""
    for u, tex in UNI2MATH.items():
        if u in s:
            s = s.replace(u, tex)
    return s


def esc_text(s):
    return "".join(LAT.get(c, c) for c in s)


def md_text(s):
    """Text fragment (no math): escape specials, **bold**, *italic*, unicode."""
    s = esc_text(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"\\textbf{\1}", s)
    s = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"\\textit{\1}", s)
    s = uni_repl(s)
    return s


def render_inline(line):
    """Split on $...$ math; text parts via md_text, math kept raw."""
    out = []
    i = 0
    buf = ""
    while i < len(line):
        if line[i] == "$":
            if buf:
                out.append(md_text(buf))
                buf = ""
            j = line.find("$", i + 1)
            if j == -1:
                buf = line[i:]
                i = len(line)
            else:
                out.append("$" + uni2math(line[i + 1:j]) + "$")
                i = j + 1
        else:
            buf += line[i]
            i += 1
    if buf:
        out.append(md_text(buf))
    return "".join(out)


def split_pipes(line):
    """Split a table row on '|' but NOT on '|' inside $...$ math."""
    cols = []
    cur = ""
    in_math = False
    for ch in line:
        if ch == "$":
            in_math = not in_math
            cur += ch
        elif ch == "|" and not in_math:
            cols.append(cur)
            cur = ""
        else:
            cur += ch
    cols.append(cur)
    return [c.strip() for c in cols]


def conv_table(rows):
    cells = []
    for r in rows:
        if re.match(r"^\|[\s:\-\|]+\|$", r):
            continue
        cells.append(split_pipes(r.strip().strip("|")))
    if not cells:
        return ""
    ncol = max(len(r) for r in cells)
    out = [r"\begin{center}\begin{tabular}{" + "l" * ncol + r"} \hline"]
    for ri, row in enumerate(cells):
        row = row + [""] * (ncol - len(row))
        out.append(" & ".join(render_inline(c) for c in row) + r" \\")
        if ri == 0:
            out.append(r"\hline")
    out.append(r"\hline\end{tabular}\end{center}")
    return "\n".join(out)


def render_block(lines):
    """Render a list of raw md lines (a box's body) to LaTeX."""
    out = []
    i = 0
    n = len(lines)
    while i < n:
        s = lines[i].strip()
        if not s:
            i += 1
            continue
        if s.startswith("$$"):
            if s.endswith("$$") and len(s) > 2:
                out.append(r"\[" + uni2math(s[2:-2].strip()) + r"\]")
                i += 1
                continue
            buf = [s[2:]]
            i += 1
            while i < n and "$$" not in lines[i]:
                buf.append(lines[i])
                i += 1
            if i < n:
                buf.append(lines[i].split("$$")[0])
                i += 1
            inner = "\n".join(b for b in buf if b.strip()).strip()
            out.append(r"\[" + uni2math(inner) + r"\]")
            continue
        if s.startswith("|") and "|" in s[1:]:
            tbl = []
            while i < n and lines[i].strip().startswith("|"):
                tbl.append(lines[i].strip())
                i += 1
            out.append(conv_table(tbl))
            continue
        if s.startswith("- ") or s.startswith("• "):
            items = []
            while i < n and (lines[i].strip().startswith("- ") or lines[i].strip().startswith("• ")):
                items.append(lines[i].strip()[2:])
                i += 1
            out.append(r"\begin{itemize}[leftmargin=14pt,topsep=2pt,itemsep=1.5pt,parsep=0pt]")
            for it in items:
                out.append("  \\item " + render_inline(it))
            out.append(r"\end{itemize}")
            continue
        if s == "---":
            out.append(r"\par\smallskip\noindent\textcolor{gray!40}{\rule{\linewidth}{0.4pt}}\par\smallskip")
            i += 1
            continue
        if s.startswith("> "):
            out.append(r"\noindent\textit{" + render_inline(s[2:]) + r"}\par")
            i += 1
            continue
        out.append(render_inline(s) + r"\par")
        i += 1
    return "\n".join(out)


def split_page_title(title):
    # Recognize a leading tag: P1 (page) or §13.1 (section) or 题 HW07-1 (homework).
    m = re.match(r"^(P\d+|§[0-9A-Za-z.]+|题\s*\S+)\s*[·\-—:]\s*(.*)$", title)
    if m:
        return m.group(1), m.group(2)
    m2 = re.match(r"^(P\d+|§[0-9A-Za-z.]+|题\s*\S+)\s+(.*)$", title)
    if m2 and m2.group(1) != title:
        return m2.group(1), m2.group(2).strip()
    return title, ""


def match_part(label):
    for key in PART_ORDER:
        if key in label:
            return key
    return None


def part_title_tex(style, name, en, sub_tex):
    col = TITLE_COLOR[style]
    icon = TITLE_ICON[style]
    size = r"\large" if style in ("cbox-formula", "cbox-cheat") else r"\small"
    en_tex = (r"\ \textit{\normalfont " + esc_text(en) + "}") if en else ""
    return (r"\textcolor{%s}{\textbf{%s %s%s%s}}%s"
            % (col, size, icon, name, en_tex, sub_tex))


def render_segmented(lines):
    """Render a block of raw md lines to LaTeX. Splits on **bold labels** that
    match a known part -> styled tcolorbox; anything else -> render_block.
    Works for any block: per-page bodies, per-section 12-part blocks, homework
    analyses, chapter-summary subsections — box detection is not gated on being
    inside a `### P` page header."""
    out = []
    while lines and lines[0].strip() in ("", "---"):
        lines.pop(0)
    while lines and lines[-1].strip() in ("", "---"):
        lines.pop()
    segs = []
    cur_key = None
    cur_label = ""
    cur_buf = []
    for ln in lines:
        s = ln.strip()
        m = re.match(r"^(?:\d+\.\s*)?\*\*(.+?)\*\*([：:].*)?$", s)
        key = None
        trailing = ""
        if m:
            label_full = m.group(1).strip()
            trailing = (m.group(2) or "").lstrip("：:").strip()
            core = re.sub(r"^\d+\.\s*", "", label_full)
            key = match_part(core)
        if key:
            segs.append((cur_key, cur_label, cur_buf))
            cur_key = key
            cur_label = core
            cur_buf = []
            if trailing:
                cur_buf.append(trailing)
        else:
            cur_buf.append(ln)
    segs.append((cur_key, cur_label, cur_buf))

    for key, label, buf in segs:
        if key is None:
            body = render_block(buf)
            if body.strip():
                out.append(body)
                out.append(r"\par\smallskip")
            continue
        name, en, style = PART_MAP[key]
        sub = ""
        idx = label.find(name)
        if idx != -1:
            sub = label[idx + len(name):].strip()
        sub_tex = (r"\ \textnormal{\textit{" + render_inline(sub) + "}}") if sub else ""
        ttl = part_title_tex(style, name, en, sub_tex)
        body = render_block(buf)
        out.append(r"\begin{%s}" % style)
        out.append(ttl + r"\par\smallskip")
        if body.strip():
            out.append(body)
        out.append(r"\end{%s}" % style)
        out.append(r"\par\medskip")
    return out


def parse_h1(md):
    for line in md.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return ""


def convert(md):
    """Walk the markdown as a sequence of header-delimited blocks. Each block's
    body is rendered by render_segmented (so **bold labels** become styled boxes
    everywhere, not only under `### P` page headers). Headers become visual bars:
    `## ` -> section bar; `### P/§/题 ...` -> page-header tag; other `### ` ->
    bold sub-heading."""
    lines = md.split("\n")
    out = []
    body = []

    def flush_body():
        nonlocal body
        if body:
            out.extend(render_segmented(body))
            body = []

    i = 0
    n = len(lines)
    while i < n:
        raw = lines[i]
        s = raw.strip()
        if s.startswith("# "):
            flush_body()  # document title; already used in \title
            i += 1
            continue
        if s.startswith("## "):
            flush_body()
            txt = s[3:].strip()
            if "逐页关键信息" in txt:
                out.append(r"\partbar{" + render_inline(txt) + "}")
            else:
                out.append(r"\secbar{" + render_inline(txt) + "}")
                out.append(r"\addcontentsline{toc}{section}{" + render_inline(txt) + "}")
            i += 1
            continue
        if s.startswith("### "):
            flush_body()
            title_raw = s[4:].strip()
            num, rest = split_page_title(title_raw)
            if num and num != title_raw:
                out.append(r"\pagehdr{" + render_inline(num) + "}{" + render_inline(rest) + "}")
            else:
                out.append(r"\par\medskip\noindent\textbf{\large "
                           + render_inline(title_raw) + r"}\par\smallskip")
            i += 1
            continue
        m_sub = re.match(r"^#{4,6}\s+(.+)$", s)
        if m_sub:
            flush_body()
            out.append(r"\par\smallskip\noindent\textbf{"
                       + render_inline(m_sub.group(1)) + r"}\par\smallskip")
            i += 1
            continue
        body.append(raw)
        i += 1
    flush_body()
    return "\n".join(out)


PREAMBLE = r"""\documentclass[11pt,a4paper]{ctexart}
\usepackage{amsmath,amssymb,amsthm}
\usepackage{mathtools}
\usepackage{bm}
\usepackage{geometry}
\geometry{a4paper, margin=2cm}
\usepackage{enumitem}
\setlist{nosep}
\usepackage[most]{tcolorbox}
\tcbuselibrary{breakable, skins}
\usepackage[colorlinks=true, linkcolor=blue!50!black,
            urlcolor=blue!60!black, bookmarksopen=true]{hyperref}

\setlength{\parskip}{3pt}
\linespread{1.08}

% ---------- visual elements ----------
\newcommand{\pagehdr}[2]{%
  \par\addvspace{12pt}\noindent
  \colorbox{blue!55!black}{\textcolor{white}{\strut\,\textbf{\sffamily\large #1}\,}}%
  \hspace{6pt}{\large\bfseries #2}\par
  \vspace{2pt}\noindent\textcolor{blue!35!black}{\rule{\linewidth}{1.2pt}}\par
  \vspace{4pt}}
\newcommand{\secbar}[1]{%
  \par\addvspace{18pt}\noindent
  \textcolor{blue!50!black}{\rule[-2pt]{5pt}{18pt}}\hspace{8pt}%
  {\Large\bfseries #1}\par
  \addvspace{3pt}\noindent\textcolor{blue!22}{\rule{\linewidth}{0.7pt}}\par
  \addvspace{6pt}}
\newcommand{\partbar}[1]{%
  \par\addvspace{8pt}\noindent
  \begin{tcolorbox}[enhanced,sharp corners,boxrule=0pt,colback=blue!8,
    colframe=blue!30,left=10pt,right=10pt,top=6pt,bottom=6pt]
  \centering\Large\bfseries\textcolor{blue!45!black}{#1}
  \end{tcolorbox}\par\addvspace{4pt}}

% ---------- 8-part boxes ----------
\newtcolorbox{cbox-pos}{enhanced,breakable,sharp corners,colback=gray!6,
  colframe=gray!55,boxrule=0pt,leftrule=3pt,left=10pt,right=8pt,top=5pt,bottom=5pt}
\newtcolorbox{cbox-concept}{enhanced,breakable,sharp corners,colback=green!4,
  colframe=green!45!black,boxrule=0pt,leftrule=3.5pt,left=10pt,right=8pt,top=5pt,bottom=5pt}
\newtcolorbox{cbox-formula}{enhanced,breakable,arc=2pt,
  colback=white,colframe=blue!55!black,boxrule=1.1pt,
  left=12pt,right=12pt,top=8pt,bottom=8pt}
\newtcolorbox{cbox-sym}{enhanced,breakable,sharp corners,colback=blue!2,
  colframe=blue!35,boxrule=0pt,leftrule=2.5pt,left=10pt,right=8pt,top=4pt,bottom=4pt,
  fontupper=\small}
\newtcolorbox{cbox-deriv}{enhanced,breakable,sharp corners,colback=gray!8,
  colframe=gray!50,boxrule=0pt,leftrule=2.5pt,left=10pt,right=8pt,top=4pt,bottom=4pt,
  fontupper=\footnotesize\color{black!70}}
\newtcolorbox{cbox-link}{enhanced,breakable,sharp corners,colback=purple!4,
  colframe=purple!45!black,boxrule=0pt,leftrule=3pt,left=10pt,right=8pt,top=5pt,bottom=5pt}
\newtcolorbox{cbox-exam}{enhanced,breakable,arc=2pt,
  colback=orange!7,colframe=orange!70!black,boxrule=0.9pt,
  left=10pt,right=10pt,top=6pt,bottom=6pt}
\newtcolorbox{cbox-pitfall}{enhanced,breakable,sharp corners,colback=red!4,
  colframe=red!60!black,boxrule=0pt,leftrule=3.5pt,left=10pt,right=8pt,top=5pt,bottom=5pt}
% ---------- exam-mode boxes ----------
\newtcolorbox{cbox-cheat}{enhanced,breakable,arc=2pt,
  colback=yellow!7,colframe=orange!80!black,boxrule=1.1pt,
  left=12pt,right=12pt,top=8pt,bottom=8pt}
\newtcolorbox{cbox-judge}{enhanced,breakable,sharp corners,colback=yellow!10,
  colframe=yellow!55!orange,boxrule=0pt,leftrule=3.5pt,left=10pt,right=8pt,top=5pt,bottom=5pt}
\newtcolorbox{cbox-fill}{enhanced,breakable,sharp corners,colback=cyan!6,
  colframe=cyan!55!black,boxrule=0pt,leftrule=3.5pt,left=10pt,right=8pt,top=5pt,bottom=5pt}
\newtcolorbox{cbox-homework}{enhanced,breakable,sharp corners,colback=teal!6,
  colframe=teal!60!black,boxrule=0pt,leftrule=3.5pt,left=10pt,right=8pt,top=5pt,bottom=5pt}
\newtcolorbox{cbox-answer}{enhanced,breakable,arc=2pt,
  colback=gray!4,colframe=gray!60,boxrule=0.6pt,
  left=10pt,right=10pt,top=6pt,bottom=6pt}

\title{\textbf{__TITLE__}}
\author{lecture-organizer}
\date{}
\begin{document}
\pagestyle{plain}
\maketitle
\thispagestyle{empty}
\tableofcontents
\thispagestyle{plain}
\newpage
"""
POSTAMBLE = r"\end{document}" + "\n"


def main():
    ap = argparse.ArgumentParser(description="Deep lecture-notes Markdown -> LaTeX")
    ap.add_argument("input", help="path to detail.md")
    ap.add_argument("output", help="path to write notes.tex")
    ap.add_argument("--title", default=None, help="document title (default: first '# ' line)")
    args = ap.parse_args()

    md = Path(args.input).read_text(encoding="utf-8")
    title = args.title or parse_h1(md) or "Lecture Notes"
    title_tex = esc_text(title)
    body = convert(md)
    tex = PREAMBLE.replace("__TITLE__", title_tex) + body + "\n\n" + POSTAMBLE
    Path(args.output).write_text(tex, encoding="utf-8")
    print("[OK] %s written (%d chars)" % (args.output, len(body)))


if __name__ == "__main__":
    main()
