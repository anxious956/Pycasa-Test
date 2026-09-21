@echo off
REM ===================================================================
REM  pycasa ortam ayari - her terminal oturumunda bir kez:
REM      call setup_env.bat
REM ===================================================================
REM  Veri (1.2 GB) bu proje klasorunun icinde: pycasa_data\
REM  YOLO agirliklari ise C:\pycasa-weights icinde durmak ZORUNDA,
REM  cunku klasor yolunda Turkce karakter var ("Masaustu") ve YOLOv5'in
REM  torch.jit.load fonksiyonu Turkce karakterli yoldan dosya acamiyor.
REM  Veri yukleme, YOLO26, moving-cells ve urbano Turkce yoldan sorunsuz calisiyor.
REM ===================================================================

set "PYCASA_DATA=%~dp0pycasa_data"
set "PYCASA_PROJECT_ROOT=C:\pycasa-weights"

if not exist "%PYCASA_PROJECT_ROOT%" mkdir "%PYCASA_PROJECT_ROOT%"

echo PYCASA_DATA         = %PYCASA_DATA%
echo PYCASA_PROJECT_ROOT = %PYCASA_PROJECT_ROOT%
echo.
echo Hazir.  python -m IPython   veya   python scripts\step1_load.py
