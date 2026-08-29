"""
compressor_wrapper.py
=====================
Aggressive PDF compressor — mirrors the Colab script exactly.

Pipeline (per PDF):
  1. Ghostscript  -dPDFSETTINGS=/ebook  →  temp_gs.pdf   (lossy, ~75 % drop)
  2. qpdf --linearize --recompress-flate →  output.pdf    (lossless clean-up)
  3. If output > input, revert to original.

Ghostscript is REQUIRED. qpdf is optional (step 2 is skipped if absent).
"""

import os
import subprocess
import shutil
from concurrent.futures import ThreadPoolExecutor


# ── DEPENDENCY DETECTION ──────────────────────────────────────────────────────

def get_gs_executable():
    """Return the first working Ghostscript binary name, or None."""
    for exe in ("gswin64c", "gswin32c", "gs"):
        try:
            subprocess.run(
                [exe, "--version"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True
            )
            return exe
        except (subprocess.SubprocessError, FileNotFoundError):
            continue
    return None


def get_gs_version(exe):
    try:
        r = subprocess.run(
            [exe, "--version"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True
        )
        return r.stdout.strip()
    except Exception:
        return "detected"


def check_qpdf():
    try:
        subprocess.run(
            ["qpdf", "--version"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True
        )
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


def get_qpdf_version():
    try:
        r = subprocess.run(
            ["qpdf", "--version"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True
        )
        return r.stdout.split("\n")[0].strip()
    except Exception:
        return "detected"


def check_dependencies():
    """Return a dict describing the status of Ghostscript and qpdf."""
    gs_exe = get_gs_executable()
    qpdf_ok = check_qpdf()
    return {
        "ghostscript": {
            "available":   gs_exe is not None,
            "executable":  gs_exe,
            "version":     get_gs_version(gs_exe) if gs_exe else "Not found"
        },
        "qpdf": {
            "available": qpdf_ok,
            "version":   get_qpdf_version() if qpdf_ok else "Not found"
        }
    }


# ── GHOSTSCRIPT ARGS (matches Colab script exactly) ──────────────────────────

def _gs_args(gs_exe, output_file, input_file):
    return [
        gs_exe,
        "-sDEVICE=pdfwrite",
        "-dCompatibilityLevel=1.4",
        "-dPDFSETTINGS=/ebook",      # 150 dpi images, JPEG medium — big size drop
        "-dNOPAUSE",
        "-dBATCH",
        "-dQUIET",
        f"-sOutputFile={output_file}",
        input_file
    ]


# ── SINGLE-FILE COMPRESSOR ───────────────────────────────────────────────────

def compress_pdf_aggressive(input_path, output_path, gs_exe):
    """
    Compress one PDF exactly as the original Colab script does:
      1. Ghostscript /ebook preset  →  temp file
      2. qpdf linearize + recompress  →  final output
      3. Revert to original if output ended up larger.

    Returns (success: bool, message: str)
    """
    temp_gs = output_path + ".gs.pdf"

    # ── Step 1: Ghostscript ───────────────────────────────────────────────────
    try:
        subprocess.run(
            _gs_args(gs_exe, temp_gs, input_path),
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
    except subprocess.CalledProcessError as e:
        # Ghostscript failed — copy original unmodified (matches Colab fallback)
        shutil.copy(input_path, output_path)
        if os.path.exists(temp_gs):
            os.remove(temp_gs)
        return False, f"Ghostscript failed: {e}"

    # ── Step 2: qpdf (optional) ───────────────────────────────────────────────
    if check_qpdf():
        try:
            subprocess.run([
                "qpdf",
                "--linearize",
                "--recompress-flate",
                "--compression-level=9",
                "--object-streams=generate",
                temp_gs,
                output_path
            ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            msg = "Ghostscript /ebook + qpdf"
        except Exception as qe:
            shutil.move(temp_gs, output_path)
            msg = f"Ghostscript /ebook (qpdf failed: {qe})"
    else:
        shutil.move(temp_gs, output_path)
        msg = "Ghostscript /ebook (qpdf not installed)"

    # Clean up temp file
    if os.path.exists(temp_gs):
        os.remove(temp_gs)

    # ── Step 3: Revert if output is larger (matches Colab script) ────────────
    before = os.path.getsize(input_path)
    after  = os.path.getsize(output_path)
    if after > before:
        shutil.copy(input_path, output_path)
        return True, f"{msg} — reverted (output was larger than input)"

    saved_pct = (before - after) / before * 100
    return True, f"{msg} — saved {saved_pct:.1f}%"


# ── BULK PARALLEL COMPRESSOR ─────────────────────────────────────────────────

def compress_bulk(pdf_files, gs_exe=None, max_workers=None, progress_callback=None):
    """
    Compress a list of PDFs in parallel (mirrors Colab ThreadPoolExecutor).

    Args:
        pdf_files:         list of {"input": str, "output": str, "name": str}
        gs_exe:            Ghostscript executable (auto-detected if None)
        max_workers:       thread pool size (defaults to cpu_count)
        progress_callback: optional callable(idx, total, result_dict)

    Returns:
        (compressed_count: int, results: list[dict])

    Raises:
        RuntimeError if Ghostscript is not available.
    """
    if not gs_exe:
        gs_exe = get_gs_executable()
    if not gs_exe:
        raise RuntimeError(
            "Ghostscript is not installed. "
            "Install it from https://ghostscript.com/releases/gsdnld.html "
            "and add its bin/ folder to your system PATH, then restart Streamlit."
        )

    if not max_workers:
        max_workers = os.cpu_count() or 2

    total             = len(pdf_files)
    compressed_count  = 0
    results           = []

    def process_file(item):
        inp  = item["input"]
        out  = item["output"]
        name = item["name"]
        try:
            before_kb = os.path.getsize(inp) / 1024.0
            success, msg = compress_pdf_aggressive(inp, out, gs_exe)
            after_kb  = os.path.getsize(out) / 1024.0
            saved_pct = ((before_kb - after_kb) / before_kb * 100) if before_kb > 0 else 0
            return {
                "name": name, "success": success,
                "before": before_kb, "after": after_kb,
                "saved": saved_pct, "msg": msg
            }
        except Exception as e:
            return {
                "name": name, "success": False,
                "before": 0, "after": 0, "saved": 0, "msg": str(e)
            }

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for idx, res in enumerate(executor.map(process_file, pdf_files), start=1):
            if res["success"]:
                compressed_count += 1
            results.append(res)
            if progress_callback:
                progress_callback(idx, total, res)

    return compressed_count, results
