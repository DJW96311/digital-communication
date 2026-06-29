#!/usr/bin/env python3
"""把一个课件文件(PDF 或 PPTX)逐页渲染成图片，并抽取文字。

用途：为"逐页整理关键信息"准备视觉素材。PPTX 通过 PowerPoint COM
先导出为 PDF，再用 PyMuPDF 渲染；PDF 直接用 PyMuPDF 渲染。

输出布局（--outdir 下）：
    pages/0001.png        第 1 页图片（视觉提取用）
    pages/0002.png        ...
    text/0001.txt         第 1 页抽取的文字（辅助）
    manifest.json         每页的图片路径、文字路径、字符数

设计取舍：
- 图片用 150 DPI（--dpi 可调）。这是"看得清公式又不至于太大"的平衡点。
- PPTX→PDF 用 PowerPoint 的 Export(ssmaTrue, ppFixedFormatTypePDF)，
  这是 Windows 上最保真的路径。导出后关掉 PowerPoint 进程，避免锁文件。
- 文字抽取是"辅助"——很多公式是图片，文字层常常残缺，主信号仍是图片。

用法：
    python render_slides.py <input.pdf|.pptx> --outdir <dir> [--dpi 150] [--dpi-images 200]
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path

# --- Windows GBK 控制台兼容：强制 UTF-8 输出 ---
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


def pptx_to_pdf(pptx_path: Path, out_pdf: Path) -> Path:
    """用 PowerPoint COM 把 .pptx 导出为 .pdf。需要 Windows + Office。"""
    import win32com.client  # 延迟导入，非 Windows 或无 Office 时给出清晰报错

    pptx_path = pptx_path.resolve()
    out_pdf = out_pdf.resolve()
    powerpoint = None
    presentation = None
    try:
        # DispatchEx 起独立进程，比 Dispatch 更稳，少受已有实例干扰
        powerpoint = win32com.client.DispatchEx("PowerPoint.Application")
        # 头部无窗口运行；某些版本必须可见才能导出，保留默认
        try:
            presentation = powerpoint.Presentations.Open(
                str(pptx_path), WithWindow=False
            )
        except Exception:
            # 回退：带窗口打开
            presentation = powerpoint.Presentations.Open(str(pptx_path))
        # 32 = ppFixedFormatTypePDF
        presentation.SaveAs(str(out_pdf), 32)
        return out_pdf
    finally:
        if presentation is not None:
            try:
                presentation.Close()
            except Exception:
                pass
        if powerpoint is not None:
            try:
                powerpoint.Quit()
            except Exception:
                pass
        # 给 COM 一点时间释放文件锁
        time.sleep(0.5)


def render_pdf(pdf_path: Path, outdir: Path, dpi: int, text_dpi: int = 72) -> list:
    """用 PyMuPDF 把 PDF 逐页渲染成图片 + 抽取文字。返回 manifest 条目列表。"""
    import fitz

    pages_dir = outdir / "pages"
    text_dir = outdir / "text"
    pages_dir.mkdir(parents=True, exist_ok=True)
    text_dir.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(str(pdf_path))
    # zoom = dpi / 72（PDF 默认 72 DPI）
    zoom = dpi / 72.0
    matrix = fitz.Matrix(zoom, zoom)

    manifest = []
    for i in range(doc.page_count):
        page = doc.load_page(i)
        # 图片
        pix = page.get_pixmap(matrix=matrix, alpha=False)
        img_name = f"{i + 1:04d}.png"
        img_path = pages_dir / img_name
        pix.save(str(img_path))

        # 文字（辅助）
        text = page.get_text("text") or ""
        txt_name = f"{i + 1:04d}.txt"
        txt_path = text_dir / txt_name
        txt_path.write_text(text, encoding="utf-8")

        manifest.append(
            {
                "page": i + 1,
                "image": str(img_path.relative_to(outdir)),
                "text_file": str(txt_path.relative_to(outdir)),
                "char_count": len(text),
                "text_preview": text.strip()[:200],
            }
        )
    doc.close()
    return manifest


def main():
    ap = argparse.ArgumentParser(description="逐页渲染课件为图片+文字")
    ap.add_argument("input", help="输入文件 (.pdf / .pptx / .ppt)")
    ap.add_argument("--outdir", required=True, help="输出目录")
    ap.add_argument("--dpi", type=int, default=150, help="图片 DPI（默认150）")
    ap.add_argument(
        "--keep-pdf",
        action="store_true",
        help="PPTX 导出的中间 PDF 保留在 outdir/source.pdf",
    )
    args = ap.parse_args()

    src = Path(args.input).resolve()
    outdir = Path(args.outdir).resolve()
    outdir.mkdir(parents=True, exist_ok=True)

    if not src.exists():
        print(f"[ERROR] 文件不存在: {src}", file=sys.stderr)
        sys.exit(1)

    ext = src.suffix.lower()
    t0 = time.time()

    if ext == ".pdf":
        pdf_to_render = src
    elif ext in (".pptx", ".ppt"):
        intermediate = outdir / "_source.pdf"
        print(f"[INFO] PPTX -> PDF (PowerPoint COM) ...", file=sys.stderr)
        pptx_to_pdf(src, intermediate)
        pdf_to_render = intermediate
    else:
        print(f"[ERROR] 不支持的格式: {ext}（仅 .pdf/.pptx/.ppt）", file=sys.stderr)
        sys.exit(1)

    print(f"[INFO] 渲染 {pdf_to_render.name} -> {outdir} @ {args.dpi}DPI ...", file=sys.stderr)
    manifest = render_pdf(pdf_to_render, outdir, args.dpi)

    # 清理中间 PDF
    if ext in (".pptx", ".ppt") and not args.keep_pdf:
        try:
            (outdir / "_source.pdf").unlink()
        except Exception:
            pass

    (outdir / "manifest.json").write_text(
        json.dumps(
            {
                "source": str(src),
                "source_name": src.name,
                "page_count": len(manifest),
                "dpi": args.dpi,
                "rendered_in_seconds": round(time.time() - t0, 1),
                "pages": manifest,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    # stdout 只打印一行摘要，便于上游脚本解析
    print(json.dumps({"outdir": str(outdir), "page_count": len(manifest)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
