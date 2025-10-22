import subprocess
from pathlib import Path
from typing import Optional
from PIL import Image

try:
    import pillow_avif  # noqa: F401
except Exception:
    pillow_avif = None  # type: ignore


def _run_cmd(cmd: list[str]) -> bool:
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception:
        return False


def _ensure_parent(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)


def compress_webp(src: Path, dst: Path, quality: int, lossless: bool) -> None:
    _ensure_parent(dst)
    q = ["-q", str(quality)]
    if lossless:
        q = ["-lossless"]
    if _run_cmd(["cwebp", *q, str(src), "-o", str(dst)]):
        return
    with Image.open(src) as im:
        im.save(dst, format="WEBP", quality=quality, lossless=lossless, method=6)


def compress_png(src: Path, dst: Path, quality: int, lossless: bool) -> None:
    _ensure_parent(dst)
    if _run_cmd(["pngquant", "--force", "--output", str(dst), "--quality", f"{max(0, quality-5)}-{quality}", str(src)]):
        return
    with Image.open(src) as im:
        im.save(dst, format="PNG", optimize=True)


def compress_avif(src: Path, dst: Path, quality: int, lossless: bool) -> None:
    _ensure_parent(dst)
    cq = ["-Q", str(quality)]
    if lossless:
        cq = ["-s", "0", "-a", "end-usage=q", "-a", "cq-level=0"]
    if _run_cmd(["avifenc", *cq, str(src), str(dst)]):
        return
    with Image.open(src) as im:
        im.save(dst, format="AVIF", quality=quality, lossless=lossless)


def compress_image(src: Path, dst: Path, fmt: str, quality: int, lossless: bool) -> None:
    f = fmt.lower()
    if f == "webp":
        if dst.suffix.lower() != ".webp":
            dst = dst.with_suffix(".webp")
        compress_webp(src, dst, quality, lossless)
        return
    if f == "png":
        if dst.suffix.lower() != ".png":
            dst = dst.with_suffix(".png")
        compress_png(src, dst, quality, lossless)
        return
    if f == "avif":
        if dst.suffix.lower() != ".avif":
            dst = dst.with_suffix(".avif")
        compress_avif(src, dst, quality, lossless)
        return
    raise ValueError(f"Unsupported format: {fmt}")
