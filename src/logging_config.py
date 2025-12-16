import logging
from pathlib import Path


def setup_logging(level: int = logging.INFO) -> None:
    log_path = Path(__file__).resolve().parent.parent / "data" / "app.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_path, encoding="utf-8"),
        ],
    )
