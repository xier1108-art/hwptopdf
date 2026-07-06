"""LibreOffice에 HWP/HWPX 가져오기 확장(H2Orestart)을 설치하는 1회성 설정 스크립트.

사전 조건: LibreOffice가 이미 설치되어 있어야 한다 (관리자 권한 필요, 수동 설치).
이 스크립트 자체는 관리자 권한이 필요 없다 (사용자 프로필에만 설치).

하는 일:
1. 포터블 JRE(Java)를 %LOCALAPPDATA%\\Programs\\hwptopdf-jre 에 다운로드/설치
   (H2Orestart 확장이 Java로 만들어져 있어서 필요함)
2. H2Orestart.oxt 확장을 다운로드해서 unopkg으로 LibreOffice 사용자 프로필에 설치
"""

from __future__ import annotations

import glob
import os
import subprocess
import sys
import urllib.request
import zipfile

SOFFICE_CANDIDATES = [
    r"C:\Program Files\LibreOffice\program",
    r"C:\Program Files (x86)\LibreOffice\program",
]

JRE_URL = "https://api.adoptium.net/v3/binary/latest/21/ga/windows/x64/jre/hotspot/normal/eclipse"
H2ORESTART_URL = "https://github.com/ebandal/H2Orestart/releases/latest/download/H2Orestart.oxt"

JRE_ROOT = os.path.join(os.environ["LOCALAPPDATA"], "Programs", "hwptopdf-jre")
DOWNLOAD_DIR = os.path.join(os.environ["TEMP"], "hwp2pdf_setup")


def find_program_dir() -> str:
    for path in SOFFICE_CANDIDATES:
        if os.path.exists(os.path.join(path, "soffice.exe")):
            return path
    print("LibreOffice를 찾을 수 없습니다. 먼저 https://www.libreoffice.org 에서 설치해주세요.")
    sys.exit(1)


def ensure_jre() -> str:
    matches = glob.glob(os.path.join(JRE_ROOT, "*", "bin", "java.exe"))
    if matches:
        print(f"JRE 이미 설치됨: {matches[0]}")
        return os.path.dirname(os.path.dirname(matches[0]))

    print("JRE(Java) 다운로드 중...")
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    zip_path = os.path.join(DOWNLOAD_DIR, "jre.zip")
    urllib.request.urlretrieve(JRE_URL, zip_path)

    print("JRE 압축 해제 중...")
    os.makedirs(JRE_ROOT, exist_ok=True)
    with zipfile.ZipFile(zip_path) as z:
        z.extractall(JRE_ROOT)

    matches = glob.glob(os.path.join(JRE_ROOT, "*", "bin", "java.exe"))
    if not matches:
        print("JRE 설치에 실패했습니다.")
        sys.exit(1)
    return os.path.dirname(os.path.dirname(matches[0]))


def ensure_extension(program_dir: str, java_home: str) -> None:
    print("H2Orestart 확장 다운로드 중...")
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    oxt_path = os.path.join(DOWNLOAD_DIR, "H2Orestart.oxt")
    urllib.request.urlretrieve(H2ORESTART_URL, oxt_path)

    env = os.environ.copy()
    env["JAVA_HOME"] = java_home

    print("확장 설치 중...")
    subprocess.run(
        [os.path.join(program_dir, "unopkg.com"), "remove", "ebandal.libreoffice.H2Orestart"],
        env=env,
        capture_output=True,
    )
    result = subprocess.run(
        [os.path.join(program_dir, "unopkg.com"), "add", oxt_path, "--suppress-license"],
        env=env,
        capture_output=True,
        text=True,
    )
    print(result.stdout)
    print(result.stderr)

    check = subprocess.run(
        [os.path.join(program_dir, "unopkg.com"), "list"],
        env=env,
        capture_output=True,
        text=True,
    )
    if "H2Orestart" in check.stdout and "is registered: yes" in check.stdout:
        print("설치 완료! 이제 HWP -> PDF 변환기를 사용할 수 있습니다.")
    else:
        print("설치가 제대로 되지 않은 것 같습니다. 위 로그를 확인해주세요.")


def main() -> None:
    program_dir = find_program_dir()
    java_home = ensure_jre()
    ensure_extension(program_dir, java_home)


if __name__ == "__main__":
    main()
