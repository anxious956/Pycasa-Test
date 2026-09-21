# ===================================================================
#  pycasa ortam ayari (PowerShell) - her oturumda bir kez:
#      . .\setup_env.ps1
# ===================================================================
#  Veri (1.2 GB) bu proje klasorunun icinde: pycasa_data\
#  YOLO agirliklari C:\pycasa-weights icinde durmak ZORUNDA, cunku
#  klasor yolunda Turkce karakter var ve YOLOv5'in torch.jit.load
#  fonksiyonu Turkce karakterli yoldan dosya acamiyor.
# ===================================================================
$env:PYCASA_DATA         = Join-Path $PSScriptRoot "pycasa_data"
$env:PYCASA_PROJECT_ROOT = "C:\pycasa-weights"
New-Item -ItemType Directory -Force -Path $env:PYCASA_PROJECT_ROOT | Out-Null
Write-Host "PYCASA_DATA         = $env:PYCASA_DATA"
Write-Host "PYCASA_PROJECT_ROOT = $env:PYCASA_PROJECT_ROOT"
Write-Host ""
Write-Host "Hazir.  python -m IPython   veya   python scripts\step1_load.py"
