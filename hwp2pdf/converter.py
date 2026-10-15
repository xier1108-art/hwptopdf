"""LibreOffice(soffice) + H2Orestart 확장을 이용한 HWP/HWPX -> PDF 변환기.

한컴오피스의 자동화(HwpAutomation) API는 에디션에 따라 아예 빠져 있는 경우가 많아
(예: 교육용 에디션) 신뢰할 수 없다. 대신 LibreOffice에 HWP/HWPX 가져오기 확장인
H2Orestart(https://github.com/ebandal/H2Orestart)를 설치해 헤드리스로 변환한다.

동시 변환을 지원하기 위해, LibreOffice의 사용자 프로필(확장이 설치되어 있는 상태)을
매 변환마다 임시 폴더로 복사해서 각자 독립된 프로필로 실행한다 (기본 프로필은 동시에
하나의 soffice 프로세스만 허용하기 때문).

원본 파일명은 절대 soffice에 그대로 넘기지 않는다. "보고서 .hwp"처럼 확장자 바로 앞에
공백이 있는 파일은 soffice가 아무 메시지 없이 열지 못하는 문제가 있어서, 항상 임시 폴더에
"input.hwp" 같은 고정된 ASCII 이름으로 복사한 뒤 변환하고 결과만 원하는 위치로 옮긴다.
"""

from __future__ import annotations

import glob
import os
import shutil
import subprocess
import tempfile

SOFFICE_CANDIDATES = [
    r"C:\Program Files\LibreOffice\program\soffice.exe",
    r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
]

BASE_PROFILE_DIR = os.path.join(
    os.environ.get("APPDATA", ""), "LibreOffice", "4"
)

BUNDLED_JRE_ROOT = os.path.join(
    os.environ.get("LOCALAPPDATA", ""), "Programs", "hwptopdf-jre"
)


class ConversionSetupError(RuntimeError):
    """LibreOffice/확장/Java 설치가 안 되어 있을 때 발생."""


def find_soffice() -> str:
    for path in SOFFICE_CANDIDATES:
        if os.path.exists(path):
            return path
    found = shutil.which("soffice.exe") or shutil.which("soffice")
    if found:
        return found
    raise ConversionSetupError(
        "LibreOffice(soffice.exe)를 찾을 수 없습니다. LibreOffice를 설치해주세요.\n"
        "(https://www.libreoffice.org/download/download-libreoffice/)"
    )


def find_java_home() -> str | None:
    matches = glob.glob(os.path.join(BUNDLED_JRE_ROOT, "*"))
    for m in matches:
        if os.path.exists(os.path.join(m, "bin", "java.exe")):
            return m
    return None


def _check_extension_installed() -> None:
    user_ext_dir = os.path.join(BASE_PROFILE_DIR, "user", "uno_packages")
    if not os.path.isdir(user_ext_dir):
        raise ConversionSetupError(
            "H2Orestart(HWP 가져오기) 확장이 설치되어 있지 않습니다.\n"
            "setup\\install_libreoffice_extension.py 를 실행해주세요."
        )


class HwpConverter:
    """워커 스레드마다 하나씩 생성해서 사용한다."""

    def __init__(self):
        self._soffice = find_soffice()
        self._java_home = find_java_home()
        _check_extension_installed()
        self._profile_dir = tempfile.mkdtemp(prefix="hwp2pdf_profile_")
        shutil.copytree(
            os.path.join(BASE_PROFILE_DIR, "user"),
            os.path.join(self._profile_dir, "user"),
        )

    def convert(self, src_path: str, pdf_path: str) -> None:
        src_path = os.path.abspath(src_path)
        pdf_path = os.path.abspath(pdf_path)
        if not os.path.isfile(src_path):
            raise RuntimeError(f"원본 파일을 찾을 수 없습니다: {src_path}")

        work_dir = tempfile.mkdtemp(prefix="hwp2pdf_job_")
        try:
            ext = os.path.splitext(src_path)[1].strip().lower() or ".hwp"
            staged = os.path.join(work_dir, "input" + ext)
            produced = os.path.join(work_dir, "input.pdf")
            shutil.copyfile(src_path, staged)

            output = ""
            # LibreOffice가 간헐적으로(특히 새 프로필 첫 실행 시) 실패하는 경우가 있어 1회 재시도한다.
            for _ in range(2):
                output = self._run_soffice(staged, work_dir)
                if os.path.isfile(produced) and os.path.getsize(produced) > 0:
                    break
            else:
                detail = output or "LibreOffice가 문서를 열지 못했습니다 (손상되었거나 암호가 걸린 문서일 수 있음)"
                raise RuntimeError(f"PDF 변환에 실패했습니다: {detail}")

            os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
            shutil.copyfile(produced, pdf_path)
        finally:
            shutil.rmtree(work_dir, ignore_errors=True)

    def _run_soffice(self, src: str, out_dir: str) -> str:
        """soffice로 src를 out_dir에 PDF로 변환하고, 의미 있는 출력 메시지만 반환한다."""
        env = os.environ.copy()
        if self._java_home:
            env["JAVA_HOME"] = self._java_home

        profile_uri = "file:///" + self._profile_dir.replace("\\", "/")
        cmd = [
            self._soffice,
            "--headless",
            "--norestore",
            f"-env:UserInstallation={profile_uri}",
            "--convert-to",
            "pdf",
            "--outdir",
            out_dir,
            src,
        ]
        try:
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                encoding="cp949",
                errors="replace",
                timeout=180,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
        except subprocess.TimeoutExpired:
            return "변환 시간이 초과되었습니다 (180초)"

        lines = (result.stdout + "\n" + result.stderr).splitlines()
        # 매번 찍히는 무의미한 경고는 제외
        lines = [
            ln.strip() for ln in lines
            if ln.strip() and "platform independent libraries" not in ln
        ]
        return " / ".join(lines)

    def close(self) -> None:
        shutil.rmtree(self._profile_dir, ignore_errors=True)
