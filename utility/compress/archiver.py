from pathlib import Path
import tarfile
import tempfile
import zipfile
import os
import zstandard as zstd


class Archiver:
    def __init__(self, root: Path):
        self.root = root

    def _tar_dir(self, tar_path: Path) -> None:
        with tarfile.open(tar_path, "w", dereference=True) as tf:
            tf.add(self.root, arcname=".")

    def _compress_zstd(self, src: Path, dst: Path, level: int) -> None:
        cparams = zstd.ZstdCompressionParameters.from_level(level=level, threads=-1)
        compressor = zstd.ZstdCompressor(compression_params=cparams)
        with open(src, "rb") as f_in, open(dst, "wb") as f_out:
            compressor.copy_stream(f_in, f_out)

    def create(self, output: Path, use_tar: bool, kind: str, level: int) -> Path:
        output.parent.mkdir(parents=True, exist_ok=True)
        if kind == "zip" or not use_tar:
            with zipfile.ZipFile(output.with_suffix(".zip"), "w", compression=zipfile.ZIP_DEFLATED) as zf:
                for base, _, files in os.walk(self.root):
                    for name in files:
                        p = Path(base) / name
                        zf.write(p, arcname=str(p.relative_to(self.root)))
            return output.with_suffix(".zip")
        with tempfile.TemporaryDirectory() as td:
            tar_path = Path(td) / "data.tar"
            self._tar_dir(tar_path)
            if kind == "zstd":
                out = output if output.suffix else output.with_suffix(".zst")
                self._compress_zstd(tar_path, out, level)
                return out
            return tar_path
