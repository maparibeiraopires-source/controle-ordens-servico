@echo off
setlocal
cd /d "%~dp0"
if not exist app.py (
  echo ERRO: app.py nao encontrado.
  pause
  exit /b 1
)
if not exist .venv (
  echo Criando ambiente virtual...
  py -m venv .venv
  if errorlevel 1 python -m venv .venv
)
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m streamlit run app.py
pause
