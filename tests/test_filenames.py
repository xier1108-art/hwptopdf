"""까다로운 파일명에서도 변환이 되는지 확인하는 회귀 테스트.

LibreOffice는 "보고서 .hwp"처럼 확장자 앞에 공백이 있는 파일을 아무 메시지 없이 열지 못한다.
converter가 원본 이름을 그대로 넘기지 않는지 여기서 확인한다.

실제 변환이 필요하므로 샘플 HWP 파일 경로를 환경변수로 넘겨서 실행한다:

    set HWP_SAMPLE=C:\\path\\to\\sample.hwp
    python -m unittest tests.test_filenames -v
"""

from __future__ import annotations

import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hwp2pdf.converter import HwpConverter  # noqa: E402

SAMPLE = os.environ.get("HWP_SAMPLE", "")

TRICKY_NAMES = [
    "보고서 .hwp",                      # 확장자 앞 공백 (실제 실패 사례)
    "건축 아이디어 1.2.3  .8) .hwp",     # 점/괄호/공백 혼합 (실제 실패 사례)
    "전기 아이디어1.2.3-검토의견 .hwp",   # 실제 실패 사례
    "괄호 (1) [2] {3}.hwp",
    "특수문자 #%&'+,;=@ 이름.hwp",
    "대문자.HWP",
    "점.이.많.은.이.름.hwp",
    "긴이름" + "가" * 80 + ".hwp",
]


@unittest.skipUnless(os.path.isfile(SAMPLE), "HWP_SAMPLE 환경변수에 샘플 .hwp 경로를 지정하세요")
class TrickyFilenameTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="hwp2pdf_test_")
        self.converter = HwpConverter()

    def tearDown(self):
        self.converter.close()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_tricky_names(self):
        for name in TRICKY_NAMES:
            with self.subTest(name=name):
                src = os.path.join(self.tmp, name)
                shutil.copyfile(SAMPLE, src)
                dst = os.path.splitext(src)[0] + ".pdf"
                self.converter.convert(src, dst)
                self.assertTrue(os.path.isfile(dst), f"PDF가 생성되지 않음: {name}")
                self.assertGreater(os.path.getsize(dst), 0)


if __name__ == "__main__":
    unittest.main()
