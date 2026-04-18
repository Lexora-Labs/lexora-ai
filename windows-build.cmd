python -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
pip install "pyinstaller>=6.3,<7" "pillow>=10,<12"

if (Test-Path .\dist) { Remove-Item .\dist -Recurse -Force }

flet pack "src/lexora/ui/main.py" `
  --name "LexoraAI" `
  --distpath dist `
  -i "lexora-ai-icon.ico" `
  --add-data "assets;assets" `
  --add-data "lexora-ai-icon.ico;." `
  --yes
