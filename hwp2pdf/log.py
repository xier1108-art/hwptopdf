"""변환 로그 파일 설정.

exe는 콘솔 창 없이 실행되므로, 실패 원인을 나중에 확인할 수 있도록 파일에 남긴다.
"""

from __future__ import annotations

import logging
import os
from logging.handlers import RotatingFileHandler

LOG_DIR = os.path.join(os.environ.get("LOCALAPPDATA", "."), "hwptopdf", "logs")
LOG_PATH = os.path.join(LOG_DIR, "hwptopdf.log")


def setup_logging() -> None:
    os.makedirs(LOG_DIR, exist_ok=True)
    handler = RotatingFileHandler(
        LOG_PATH, maxBytes=1_000_000, backupCount=3, encoding="utf-8"
    )
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(handler)
