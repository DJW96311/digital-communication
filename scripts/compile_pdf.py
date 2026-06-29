#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Compile a .tex file to .pdf with xelatex (two passes for cross-refs).

Design notes:
- Fixed to xelatex (required for ctex / Chinese).
- Two passes: first builds .aux, second resolves ref/label/citation. Lecture
  notes have many cross-references ("see Example 2.3"), so two passes are needed.
- -interaction=nonstopmode -halt-on-error: stop on error, don't hang on prompts.
- On failure: print the first '!' error in the .log with surrounding context,
  and keep the .log for debugging. Don't swallow errors silently — locating
  the problem matters when compilation breaks.

Usage:
    python compile_pdf.py input.tex [--outdir DIR] [--runs 2]

Success -> exit 0, PDF path printed to stdout as JSON.
"""
import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


def find_error_context(log_text):
    """Extract the first '!' error and a few surrounding lines for humans."""
    lines = log_text.splitlines()
    for i, line in enumerate(lines):
        if line.startswith("!"):
            start = max(0, i - 2)
            end = min(len(lines), i + 6)
            return "\n".join(lines[start:end])
    return "(no '!' error line found in log)"


def run_xelatex(tex_path, outdir):
    """Run xelatex once. Returns (ok, log_text)."""
    cmd = [
        "xelatex",
        "-interaction=nonstopmode",
        "-halt-on-error",
        "-output-directory=" + str(outdir),
        tex_path.name,
    ]
    proc = subprocess.run(
        cmd,
        cwd=str(tex_path.parent),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    log_path = outdir / (tex_path.stem + ".log")
    if log_path.exists():
        log_text = log_path.read_text(encoding="utf-8", errors="replace")
    else:
        log_text = proc.stdout
    return proc.returncode == 0, log_text


def main():
    ap = argparse.ArgumentParser(description="xelatex compile .tex -> .pdf (two passes)")
    ap.add_argument("input", help="path to .tex file")
    ap.add_argument("--outdir", default=None, help="output directory (default: same as .tex)")
    ap.add_argument("--runs", type=int, default=2, help="number of passes (default 2)")
    args = ap.parse_args()

    tex = Path(args.input).resolve()
    outdir = Path(args.outdir).resolve() if args.outdir else tex.parent
    outdir.mkdir(parents=True, exist_ok=True)

    if not tex.exists():
        print(json.dumps({"ok": False, "error": "tex file not found: " + str(tex)}), file=sys.stderr)
        sys.exit(1)

    log_text = ""
    for run in range(1, args.runs + 1):
        ok, log_text = run_xelatex(tex, outdir)
        if not ok:
            ctx = find_error_context(log_text)
            print("[FAIL] pass " + str(run) + "/" + str(args.runs) + " failed.\nError context:\n" + ctx, file=sys.stderr)
            print("[INFO] full log: " + str(outdir / (tex.stem + ".log")), file=sys.stderr)
            print(json.dumps({"ok": False, "error": "xelatex compile failed", "run_failed": run}), file=sys.stderr)
            sys.exit(2)

    pdf = outdir / (tex.stem + ".pdf")
    if not pdf.exists():
        print(json.dumps({"ok": False, "error": "compile returned success but PDF not produced"}), file=sys.stderr)
        sys.exit(3)

    print(json.dumps({"ok": True, "pdf": str(pdf), "pdf_bytes": pdf.stat().st_size}, ensure_ascii=False))


if __name__ == "__main__":
    main()
