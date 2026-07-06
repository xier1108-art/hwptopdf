@echo off
REM 단일 exe 빌드 스크립트. 빠른 시작을 위해 불필요한 무거운 패키지(torch/tensorflow 등)와
REM 쓰지 않는 PyQt6 모듈을 제외합니다.
REM 사용법: 이 파일이 있는 폴더(프로젝트 루트)에서 그냥 더블클릭하거나 실행하세요.

cd /d "%~dp0"

pyinstaller --onefile --windowed --noupx --clean --name HWPtoPDF ^
  --exclude-module PyQt6.QtQml --exclude-module PyQt6.QtQuick --exclude-module PyQt6.QtQuickWidgets ^
  --exclude-module PyQt6.QtQuick3D --exclude-module PyQt6.QtMultimedia --exclude-module PyQt6.QtMultimediaWidgets ^
  --exclude-module PyQt6.QtNetwork --exclude-module PyQt6.QtBluetooth --exclude-module PyQt6.QtNfc ^
  --exclude-module PyQt6.QtPositioning --exclude-module PyQt6.QtSensors --exclude-module PyQt6.QtSerialPort ^
  --exclude-module PyQt6.QtSql --exclude-module PyQt6.QtTest --exclude-module PyQt6.QtDBus ^
  --exclude-module PyQt6.QtDesigner --exclude-module PyQt6.QtHelp --exclude-module PyQt6.QtOpenGL ^
  --exclude-module PyQt6.QtOpenGLWidgets --exclude-module PyQt6.QtPdf --exclude-module PyQt6.QtPdfWidgets ^
  --exclude-module PyQt6.QtWebChannel --exclude-module PyQt6.QtWebSockets --exclude-module PyQt6.QtXml ^
  --exclude-module PyQt6.QtRemoteObjects --exclude-module PyQt6.QtTextToSpeech --exclude-module PyQt6.QtStateMachine ^
  --exclude-module pyarrow --exclude-module scipy --exclude-module torch --exclude-module torchvision ^
  --exclude-module torchaudio --exclude-module tensorflow --exclude-module sklearn --exclude-module matplotlib ^
  --exclude-module numba --exclude-module IPython --exclude-module notebook --exclude-module jupyter ^
  --exclude-module h5py --exclude-module tables --exclude-module statsmodels --exclude-module seaborn ^
  --exclude-module networkx --exclude-module sympy --exclude-module nltk --exclude-module cv2 ^
  --exclude-module onnx --exclude-module transformers --exclude-module xgboost --exclude-module lightgbm ^
  --exclude-module plotly --exclude-module dash --exclude-module streamlit --exclude-module flask ^
  --exclude-module django --exclude-module boto3 --exclude-module grpc --exclude-module tensorboard ^
  --exclude-module openpyxl --exclude-module lxml --exclude-module bs4 --exclude-module html5lib ^
  main.py

echo.
echo 빌드 완료: dist\HWPtoPDF.exe
pause
