"""PyQt6 QThreadPool 기반 배치 변환 워커.

각 작업(ConversionTask)은 자기 자신의 HwpConverter(=자기 자신의 한/글 COM 인스턴스)를
만들어 스레드 안에서만 사용한다. 동시 실행 개수는 QThreadPool.setMaxThreadCount 로 제한한다.
"""

from __future__ import annotations

import os
import traceback
from dataclasses import dataclass, field

from PyQt6.QtCore import QObject, QRunnable, pyqtSignal

from .converter import HwpConverter
from .privacy import strip_document_metadata, strip_image_exif


@dataclass
class ConvertOptions:
    output_dir: str | None = None  # None이면 원본과 같은 폴더
    strip_exif: bool = True
    strip_doc_metadata: bool = False
    delete_source: bool = False
    password: str = ""


@dataclass
class TaskResult:
    index: int
    src_path: str
    pdf_path: str | None
    success: bool
    message: str = ""


class WorkerSignals(QObject):
    started = pyqtSignal(int)
    finished = pyqtSignal(object)  # TaskResult


class ConversionTask(QRunnable):
    def __init__(self, index: int, src_path: str, options: ConvertOptions):
        super().__init__()
        self.index = index
        self.src_path = src_path
        self.options = options
        self.signals = WorkerSignals()

    def _pdf_path(self) -> str:
        base = os.path.splitext(os.path.basename(self.src_path))[0] + ".pdf"
        out_dir = self.options.output_dir or os.path.dirname(self.src_path)
        return os.path.join(out_dir, base)

    def run(self) -> None:
        self.signals.started.emit(self.index)
        pdf_path = self._pdf_path()
        converter = HwpConverter()
        try:
            converter.convert(self.src_path, pdf_path)

            if self.options.strip_exif:
                strip_image_exif(pdf_path)
            if self.options.strip_doc_metadata:
                strip_document_metadata(pdf_path)
            if self.options.password:
                from .privacy import set_password

                set_password(pdf_path, self.options.password)
            if self.options.delete_source:
                try:
                    os.remove(self.src_path)
                except OSError:
                    pass

            self.signals.finished.emit(
                TaskResult(self.index, self.src_path, pdf_path, True, "완료")
            )
        except Exception as e:  # noqa: BLE001
            msg = f"{e}\n{traceback.format_exc(limit=2)}"
            self.signals.finished.emit(
                TaskResult(self.index, self.src_path, None, False, str(e) or msg)
            )
        finally:
            converter.close()
