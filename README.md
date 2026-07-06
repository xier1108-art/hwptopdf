# HWP → PDF 변환기

아래아한글(HWP/HWPX)을 PDF로 일괄 변환하는 Windows용 데스크톱 프로그램입니다.
드래그 앤 드롭, 다중 파일 동시 변환, 이미지 EXIF 제거를 포함한 개인정보 보호 옵션을 지원합니다.

## 동작 방식

**한컴오피스가 필요 없습니다.** 대신 무료/오픈소스인 LibreOffice + HWP 가져오기 확장
([H2Orestart](https://github.com/ebandal/H2Orestart))을 이용해 완전히 로컬에서 변환합니다.

> 원래는 한컴오피스의 자동화(HwpAutomation) API로 구현했었는데, 실제로 테스트해보니
> 이 PC에 설치된 한컴오피스 2022 교육용(Edu) 에디션에는 자동화 컴포넌트 자체가 빠져 있어서
> (`HWPFrame.HwpObject` 클래스가 레지스트리에 아예 존재하지 않음) 동작하지 않았습니다.
> 에디션/라이선스에 따라 되고 안 되고가 갈리는 방식이라, 한컴오피스 설치 여부와 무관하게
> 항상 동작하는 LibreOffice 기반으로 전환했습니다.

## 설치 순서 (반드시 이 순서대로)

### 0. LibreOffice부터 먼저 설치하세요 (필수, 가장 먼저)

**➡️ [LibreOffice 공식 다운로드 페이지](https://www.libreoffice.org/download/download-libreoffice/)** 에서
Windows용 설치 파일을 받아 기본 옵션 그대로 설치해주세요. (관리자 권한 필요, 약 350MB)

이 프로그램은 한컴오피스가 아니라 LibreOffice를 이용해 변환하기 때문에, **LibreOffice 설치가 먼저 되어 있지 않으면 실행해도 변환이 되지 않습니다.**

### 1. HWP 가져오기 확장 설치 (관리자 권한 불필요)

```powershell
python setup\install_libreoffice_extension.py
```
포터블 Java(JRE)와 [H2Orestart](https://github.com/ebandal/H2Orestart) 확장을 자동으로 받아서 LibreOffice에 설치합니다.

### 2. 프로그램 실행

- **[Releases](../../releases)에서 `HWPtoPDF.exe`를 받아 바로 실행** — 파이썬 설치 불필요.
- 또는 소스로 직접 실행:
  ```powershell
  pip install -r requirements.txt
  python main.py
  ```

## 기능

- **드래그 앤 드롭**: 창에 `.hwp` / `.hwpx` 파일이나 폴더를 끌어다 놓으면 자동으로 목록에 추가됩니다 (폴더는 하위 파일까지 재귀적으로 탐색).
- **다중 파일 동시 변환**: "동시 변환 개수"를 조절해 여러 파일을 병렬로 변환합니다. 파일마다 독립된 LibreOffice 프로필을 사용해 진짜로 동시에 돌아갑니다 (실측: 4개 파일, 3동시 실행 시 5.3초).
- **이미지 EXIF 제거**: 문서에 삽입된 사진(특히 휴대폰 촬영 사진)에는 GPS 위치, 촬영 기기, 촬영 시각 등 민감한 EXIF 메타데이터가 남아있을 수 있습니다. 픽셀 데이터만 남기고 다시 인코딩해 이를 제거합니다.
- **PDF 문서 속성 제거**: 작성자, 제목, 생성 프로그램 등 PDF 자체의 메타데이터를 지웁니다.
- **원본 삭제**: 변환 후 원본 HWP 파일을 자동 삭제할 수 있습니다.
- **PDF 병합**: 변환된 여러 PDF를 하나의 파일로 합칠 수 있습니다.
- **PDF 열람 암호 설정**: 변환된 PDF에 비밀번호를 걸 수 있습니다.
- **출력 폴더 지정**: 원본과 같은 폴더 또는 별도 폴더를 선택할 수 있습니다.
- **완료 후 폴더 자동 열기**.

## 문제 해결

- "LibreOffice(soffice.exe)를 찾을 수 없습니다" → LibreOffice를 기본 경로(`C:\Program Files\LibreOffice`)에 설치했는지 확인하세요.
- "H2Orestart 확장이 설치되어 있지 않습니다" → `python setup\install_libreoffice_extension.py` 를 실행하세요.
- 변환이 실패하면 문서가 손상되었거나 극히 드문 레이아웃 요소일 수 있습니다. LibreOffice에서 직접 그 파일을 열어보면 원인을 알 수 있습니다.
- LibreOffice 렌더링은 한컴오피스 한글과 100% 동일하지는 않습니다 (레이아웃이 살짝 다를 수 있음). 완벽한 픽셀 단위 일치가 필요하면 한컴오피스에서 직접 "다른 이름으로 저장 > PDF"를 사용하세요.

## 단일 exe로 빌드하기

```powershell
pip install pyinstaller
build_exe.bat
```

빌드 결과물은 `dist\HWPtoPDF.exe` 하나입니다 (약 96MB). LibreOffice는 exe 안에 포함되지 않고
시스템에 설치된 것을 그대로 호출하므로, exe를 배포하는 PC에도 위 "최초 설치" 1~2단계는
별도로 해줘야 합니다.

두 번째 실행부터는 창이 뜨기까지 약 4~5초입니다 (최초 1회는 Windows Defender 검사로 더 오래 걸릴 수 있음).

## 비슷한 오픈소스 프로젝트 (참고용 링크)

- [ebandal/H2Orestart](https://github.com/ebandal/H2Orestart) — 이 프로그램이 실제로 사용하는 LibreOffice용 HWP/HWPX 가져오기 확장. 데비안 공식 패키지로도 배포될 만큼 검증됨.
- [pyhwpx](https://github.com/martiniifun/pyhwpx) — 한컴오피스 자동화 API가 지원되는 정품 환경이라면, pywin32로 한/글을 직접 제어하는 이 라이브러리가 더 정교한 제어(페이지 범위 등)를 제공합니다.
- [disjukr/hwpkit](https://github.com/disjukr/hwpkit) — 브라우저/Node.js에서 HWP를 캔버스나 PDF로 직접 렌더링하려는 실험적 프로젝트 (아직 개발 중, AGPL 라이선스라 재배포 시 라이선스 검토 필요).
- [mete0r/pyhwp](https://github.com/mete0r/pyhwp) — 한/글 미설치 환경에서 텍스트/구조만 추출하고 싶을 때 (PDF 렌더링용은 아님).

온라인 변환 사이트들은 문서를 외부 서버에 업로드하므로 민감 문서에는 권장하지 않습니다. 이 프로그램은 전부 로컬에서 처리되도록 만들었습니다.

## 프로젝트 구조

```
hwptopdf/
  main.py                                   # 실행 진입점
  requirements.txt
  build_exe.bat                             # 단일 exe 빌드 스크립트
  setup/install_libreoffice_extension.py    # 최초 1회 H2Orestart 확장 설치 스크립트
  hwp2pdf/
    converter.py                             # LibreOffice(soffice) 헤드리스 변환
    privacy.py                               # EXIF 제거 / 메타데이터 제거 / 병합 / 암호화
    worker.py                                # 동시 변환을 위한 백그라운드 작업 큐
    gui.py                                   # PyQt6 GUI (드래그앤드롭, 옵션, 진행률)
```
