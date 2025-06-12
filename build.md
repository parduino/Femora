git clone https://github.com/amnp95/Femora.git
python -m venv femoraenv
source femoraenv/bin/activate
cd Femora
pip install requirements.in
pip install pyinstaller
pip install -e .
pyinstaller --onefile --icon=icon.ico --hidden-import femora --hidden-import ipykernel --hidden-import debugpy --collect-all femora --collect-all ipykernel --collect-all debugpy main.py
