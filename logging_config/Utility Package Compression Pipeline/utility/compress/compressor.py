from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Iterable
from tqdm import tqdm
from .config import CompressionSettings
from .formats import compress_image

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".avif", ".bmp", ".tiff"}


def _iter_images(root: Path) -> Iterable[Path]:
    for p in root.rglob("*"):
        if p.is_file() and p.suffix.lower() in IMAGE_EXTS:
            yield p


class ImageCompressor:
    def __init__(self, cfg: CompressionSettings):
        self.cfg = cfg

    def _dst_for(self, src: Path) -> Path:
        rel = src.relative_to(self.cfg.input_dir)
        dst = self.cfg.output_dir / rel
        return dst

    def _compress_one(self, src: Path) -> Path:
        dst = self._dst_for(src)
        compress_image(src, dst, self.cfg.format, self.cfg.quality, self.cfg.lossless)
        return dst

    def run(self) -> None:
        self.cfg.output_dir.mkdir(parents=True, exist_ok=True)
        items = list(_iter_images(self.cfg.input_dir))
        if not items:
            return
        workers = self.cfg.resolved_workers()
        with ThreadPoolExecutor(max_workers=workers) as ex:
            futures = [ex.submit(self._compress_one, p) for p in items]
            for _ in tqdm(as_completed(futures), total=len(futures), desc="Compress"):
                pass
