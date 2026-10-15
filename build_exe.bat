@echo off
REM Builds dist\HWPtoPDF.exe as a single file.
REM Heavy unrelated packages (torch/tensorflow/...) and unused PyQt6 modules are
REM excluded so the exe stays small and starts fast.
REM Keep this file ASCII-only with CRLF line endings: cmd.exe misparses UTF-8 Korean text.

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
echo Build finished: dist\HWPtoPDF.exe
pause
