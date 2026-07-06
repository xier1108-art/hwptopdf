from __future__ import annotations

import os
import subprocess

from PyQt6.QtCore import Qt, QThreadPool
from PyQt6.QtGui import QDragEnterEvent, QDropEvent
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .privacy import merge_pdfs
from .worker import ConversionTask, ConvertOptions, TaskResult

SUPPORTED_EXTS = (".hwp", ".hwpx")

STATUS_WAIT = "대기"
STATUS_RUN = "변환 중"
STATUS_DONE = "완료"
STATUS_FAIL = "실패"


class FileTable(QTableWidget):
    def __init__(self, parent=None):
        super().__init__(0, 2, parent)
        self.setHorizontalHeaderLabels(["파일", "상태"])
        self.horizontalHeader().setStretchLastSection(False)
        self.horizontalHeader().resizeSection(1, 100)
        self.horizontalHeader().setSectionResizeMode(
            0, self.horizontalHeader().ResizeMode.Stretch
        )
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setAcceptDrops(True)
        self.setColumnWidth(0, 480)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dragMoveEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:
        paths = [url.toLocalFile() for url in event.mimeData().urls()]
        window = self.window()
        if isinstance(window, MainWindow):
            window.add_paths(paths)
        event.acceptProposedAction()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HWP → PDF 변환기")
        self.resize(760, 620)
        self.setAcceptDrops(True)

        self.files: list[str] = []
        self.pool = QThreadPool.globalInstance()
        self.pending = 0
        self.produced_pdfs: list[str | None] = []

        self._build_ui()

    # ---------- UI 구성 ----------
    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        hint = QLabel("변환할 .hwp / .hwpx 파일을 여기로 드래그 앤 드롭하세요.")
        hint.setStyleSheet("color: gray;")
        layout.addWidget(hint)

        self.table = FileTable()
        layout.addWidget(self.table)

        btn_row = QHBoxLayout()
        add_btn = QPushButton("파일 추가")
        add_btn.clicked.connect(self.browse_files)
        clear_btn = QPushButton("목록 지우기")
        clear_btn.clicked.connect(self.clear_files)
        remove_btn = QPushButton("선택 삭제")
        remove_btn.clicked.connect(self.remove_selected)
        btn_row.addWidget(add_btn)
        btn_row.addWidget(remove_btn)
        btn_row.addWidget(clear_btn)
        btn_row.addStretch(1)
        layout.addLayout(btn_row)

        # 출력 옵션
        out_group = QGroupBox("출력 폴더")
        out_layout = QHBoxLayout(out_group)
        self.out_dir_edit = QLineEdit()
        self.out_dir_edit.setPlaceholderText("비워두면 원본과 같은 폴더에 저장")
        out_browse = QPushButton("찾아보기")
        out_browse.clicked.connect(self.browse_out_dir)
        out_layout.addWidget(self.out_dir_edit)
        out_layout.addWidget(out_browse)
        layout.addWidget(out_group)

        # 변환 옵션
        opt_group = QGroupBox("옵션")
        opt_layout = QVBoxLayout(opt_group)

        row1 = QHBoxLayout()
        self.exif_check = QCheckBox("이미지 EXIF/개인정보 메타데이터 제거 (GPS 위치, 촬영기기 등)")
        self.exif_check.setChecked(True)
        row1.addWidget(self.exif_check)
        opt_layout.addLayout(row1)

        row2 = QHBoxLayout()
        self.meta_check = QCheckBox("PDF 문서 속성(작성자/제목/편집기록) 제거")
        row2.addWidget(self.meta_check)
        opt_layout.addLayout(row2)

        row3 = QHBoxLayout()
        self.delete_src_check = QCheckBox("변환 후 원본 HWP 파일 삭제")
        row3.addWidget(self.delete_src_check)
        opt_layout.addLayout(row3)

        row4 = QHBoxLayout()
        self.merge_check = QCheckBox("변환된 PDF를 하나로 병합")
        row4.addWidget(self.merge_check)
        opt_layout.addLayout(row4)

        row5 = QHBoxLayout()
        self.pw_check = QCheckBox("PDF 열람 암호 설정")
        self.pw_edit = QLineEdit()
        self.pw_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.pw_edit.setPlaceholderText("암호 입력")
        self.pw_edit.setEnabled(False)
        self.pw_check.toggled.connect(self.pw_edit.setEnabled)
        row5.addWidget(self.pw_check)
        row5.addWidget(self.pw_edit)
        opt_layout.addLayout(row5)

        row6 = QHBoxLayout()
        self.open_folder_check = QCheckBox("완료 후 결과 폴더 열기")
        self.open_folder_check.setChecked(True)
        row6.addWidget(self.open_folder_check)
        row6.addStretch(1)
        row6.addWidget(QLabel("동시 변환 개수:"))
        self.concurrency_spin = QSpinBox()
        self.concurrency_spin.setRange(1, 6)
        self.concurrency_spin.setValue(2)
        row6.addWidget(self.concurrency_spin)
        opt_layout.addLayout(row6)

        layout.addWidget(opt_group)

        # 진행 상태
        self.progress = QProgressBar()
        layout.addWidget(self.progress)
        self.status_label = QLabel("")
        layout.addWidget(self.status_label)

        # 실행 버튼
        run_row = QHBoxLayout()
        self.start_btn = QPushButton("변환 시작")
        self.start_btn.clicked.connect(self.start_conversion)
        run_row.addStretch(1)
        run_row.addWidget(self.start_btn)
        layout.addLayout(run_row)

    # ---------- 드래그앤드롭 (창 전체) ----------
    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:
        paths = [url.toLocalFile() for url in event.mimeData().urls()]
        self.add_paths(paths)
        event.acceptProposedAction()

    # ---------- 파일 목록 관리 ----------
    def add_paths(self, paths: list[str]) -> None:
        collected: list[str] = []
        for p in paths:
            if os.path.isdir(p):
                for root, _dirs, names in os.walk(p):
                    for n in names:
                        if n.lower().endswith(SUPPORTED_EXTS):
                            collected.append(os.path.join(root, n))
            elif p.lower().endswith(SUPPORTED_EXTS):
                collected.append(p)

        for path in collected:
            if path in self.files:
                continue
            self.files.append(path)
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(path))
            self.table.setItem(row, 1, QTableWidgetItem(STATUS_WAIT))

        if not collected:
            QMessageBox.information(self, "안내", "지원하는 .hwp / .hwpx 파일을 찾지 못했습니다.")

    def browse_files(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self, "변환할 파일 선택", "", "HWP 파일 (*.hwp *.hwpx)"
        )
        if paths:
            self.add_paths(paths)

    def browse_out_dir(self) -> None:
        d = QFileDialog.getExistingDirectory(self, "출력 폴더 선택")
        if d:
            self.out_dir_edit.setText(d)

    def clear_files(self) -> None:
        self.files.clear()
        self.table.setRowCount(0)

    def remove_selected(self) -> None:
        rows = sorted({idx.row() for idx in self.table.selectedIndexes()}, reverse=True)
        for row in rows:
            del self.files[row]
            self.table.removeRow(row)

    # ---------- 변환 실행 ----------
    def start_conversion(self) -> None:
        if not self.files:
            QMessageBox.warning(self, "안내", "변환할 파일을 먼저 추가하세요.")
            return

        out_dir = self.out_dir_edit.text().strip() or None
        options = ConvertOptions(
            output_dir=out_dir,
            strip_exif=self.exif_check.isChecked(),
            strip_doc_metadata=self.meta_check.isChecked(),
            delete_source=self.delete_src_check.isChecked(),
            password=self.pw_edit.text() if self.pw_check.isChecked() else "",
        )

        self.pool.setMaxThreadCount(self.concurrency_spin.value())
        self.start_btn.setEnabled(False)
        self.progress.setValue(0)
        self.progress.setMaximum(len(self.files))
        self.pending = len(self.files)
        self.produced_pdfs = [None] * len(self.files)

        for row in range(self.table.rowCount()):
            self.table.setItem(row, 1, QTableWidgetItem(STATUS_WAIT))

        for i, path in enumerate(self.files):
            task = ConversionTask(i, path, options)
            task.signals.started.connect(self._on_started)
            task.signals.finished.connect(self._on_finished)
            self.pool.start(task)

    def _on_started(self, index: int) -> None:
        self.table.setItem(index, 1, QTableWidgetItem(STATUS_RUN))

    def _on_finished(self, result: TaskResult) -> None:
        status = STATUS_DONE if result.success else STATUS_FAIL
        item = QTableWidgetItem(status)
        if not result.success:
            item.setToolTip(result.message)
        self.table.setItem(result.index, 1, item)
        if result.success:
            self.produced_pdfs[result.index] = result.pdf_path

        self.pending -= 1
        done_count = len(self.files) - self.pending
        self.progress.setValue(done_count)

        if self.pending == 0:
            self._on_all_done()

    def _on_all_done(self) -> None:
        self.start_btn.setEnabled(True)
        ok_pdfs = [p for p in self.produced_pdfs if p]
        fail_count = len(self.files) - len(ok_pdfs)
        self.status_label.setText(f"완료: {len(ok_pdfs)}개 성공, {fail_count}개 실패")

        out_dir = self.out_dir_edit.text().strip() or (
            os.path.dirname(self.files[0]) if self.files else "."
        )

        if self.merge_check.isChecked() and len(ok_pdfs) > 1:
            merged_path = os.path.join(out_dir, "병합본.pdf")
            try:
                merge_pdfs(ok_pdfs, merged_path)
            except Exception as e:  # noqa: BLE001
                QMessageBox.warning(self, "병합 실패", str(e))

        if self.open_folder_check.isChecked() and os.path.isdir(out_dir):
            subprocess.Popen(["explorer", os.path.normpath(out_dir)])
