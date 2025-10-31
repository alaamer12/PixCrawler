from pathlib import Path
from .config import CompressionSettings
from .compressor import ImageCompressor
from .archiver import Archiver


def run() -> None:
    cfg = CompressionSettings()
    compressor = ImageCompressor(cfg)
    compressor.run()
    arc = cfg.archive()
    if arc.enable:
        archiver = Archiver(cfg.output_dir)
        out = Path(arc.output)
        kind = arc.type
        archiver.create(out, arc.tar, kind, arc.level)


if __name__ == "__main__":
    run()
