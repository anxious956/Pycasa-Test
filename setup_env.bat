@echo off
REM ===================================================================
REM  pycasa environment setup - run once per terminal session:
REM      call setup_env.bat
REM ===================================================================
REM  The data (1.2 GB) lives inside this project folder: pycasa_data\
REM  The YOLO weights, however, MUST sit in C:\pycasa-weights, because the
REM  project path contains non-ASCII Turkish characters ("Masaustu") and
REM  YOLOv5's torch.jit.load cannot open a file from such a path.
REM  Data loading, YOLO26, moving-cells and urbano all work fine from the
REM  Turkish path.
REM ===================================================================

set "PYCASA_DATA=%~dp0pycasa_data"
set "PYCASA_PROJECT_ROOT=C:\pycasa-weights"

if not exist "%PYCASA_PROJECT_ROOT%" mkdir "%PYCASA_PROJECT_ROOT%"

echo PYCASA_DATA         = %PYCASA_DATA%
echo PYCASA_PROJECT_ROOT = %PYCASA_PROJECT_ROOT%
echo.
echo Ready.  python -m IPython   or   python scripts\step1_load.py
