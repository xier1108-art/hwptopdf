"""변환된 PDF에 대한 개인정보 보호 후처리.

- 이미지 EXIF 제거: 문서에 삽입된 사진(특히 휴대폰으로 찍은 사진)에는
  GPS 위치, 촬영 기기, 촬영 시각 같은 EXIF 메타데이터가 그대로 남아있을 수 있다.
  이미지를 픽셀 단위로 다시 인코딩해 이런 메타데이터를 제거한다.
- PDF 문서 메타데이터 제거: 작성자/회사명/이전 편집기록 등 문서 속성 제거.
- 비밀번호 설정 / 여러 PDF 병합은 부가 옵션으로 함께 제공한다.
"""

from __future__ import annotations

import io
import os

import fitz  # PyMuPDF
import pikepdf
from PIL import Image


def strip_image_exif(pdf_path: str) -> int:
    """PDF 내 모든 이미지의 EXIF/메타데이터를 제거한다. 처리된 이미지 개수를 반환."""
    doc = fitz.open(pdf_path)
    cleaned = 0

    for page in doc:
        for img in page.get_images(full=True):
            xref = img[0]
            try:
                base = doc.extract_image(xref)
                pil_img = Image.open(io.BytesIO(base["image"]))
                # getdata()로 픽셀만 복사한 새 이미지를 만들면 EXIF/ICC 등 부가 정보가 빠진다.
                clean_img = Image.new(pil_img.mode, pil_img.size)
                clean_img.putdata(list(pil_img.getdata()))

                fmt = base["ext"].upper()
                fmt = "JPEG" if fmt == "JPG" else fmt
                buf = io.BytesIO()
                clean_img.save(buf, format=fmt)

                doc.update_stream(xref, buf.getvalue())
                cleaned += 1
            except Exception:  # noqa: BLE001
                continue

    if cleaned:
        tmp_path = pdf_path + ".tmp"
        doc.save(tmp_path, garbage=4, deflate=True)
        doc.close()
        os.replace(tmp_path, pdf_path)
    else:
        doc.close()

    return cleaned


def strip_document_metadata(pdf_path: str) -> None:
    """작성자, 제목, 생성 프로그램 등 PDF 문서 속성을 제거한다."""
    doc = fitz.open(pdf_path)
    doc.set_metadata({})
    try:
        doc.del_xml_metadata()
    except Exception:  # noqa: BLE001
        pass
    tmp_path = pdf_path + ".tmp"
    doc.save(tmp_path, garbage=4, deflate=True)
    doc.close()
    os.replace(tmp_path, pdf_path)


def set_password(pdf_path: str, password: str) -> None:
    """PDF 열람 암호를 설정한다."""
    with pikepdf.open(pdf_path, allow_overwriting_input=True) as pdf:
        pdf.save(
            pdf_path,
            encryption=pikepdf.Encryption(user=password, owner=password, R=6),
        )


def merge_pdfs(pdf_paths: list[str], output_path: str) -> None:
    """여러 PDF를 하나의 파일로 병합한다."""
    merged = pikepdf.Pdf.new()
    for path in pdf_paths:
        with pikepdf.open(path) as src:
            merged.pages.extend(src.pages)
    out_dir = os.path.dirname(output_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    merged.save(output_path)
    merged.close()
