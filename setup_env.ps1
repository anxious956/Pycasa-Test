# ===================================================================
#  pycasa environment setup (PowerShell) - run once per session:
#      . .\setup_env.ps1
# ===================================================================
#  The data (1.2 GB) lives inside this project folder: pycasa_data\
#  The YOLO weights MUST sit in C:\pycasa-weights, because the project
#  path contains non-ASCII Turkish characters and YOLOv5's
#  torch.jit.load cannot open a file from such a path.
# ===================================================================
$env:PYCASA_DATA         = Join-Path $PSScriptRoot "pycasa_data"
$env:PYCASA_PROJECT_ROOT = "C:\pycasa-weights"
New-Item -ItemType Directory -Force -Path $env:PYCASA_PROJECT_ROOT | Out-Null
Write-Host "PYCASA_DATA         = $env:PYCASA_DATA"
Write-Host "PYCASA_PROJECT_ROOT = $env:PYCASA_PROJECT_ROOT"
Write-Host ""
Write-Host "Ready.  python -m IPython   or   python scripts\step1_load.py"
